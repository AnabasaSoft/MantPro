// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../api.dart';
import '../i18n/strings.dart';
import '../modelos.dart';

/// Muestra (y, si el usuario puede gestionar el almacén, permite editar) un artículo.
/// - Si [materialId] es null se abre directamente en modo creación, preseleccionando
///   [seccionIdInicial] cuando el alta se lanza desde una sección concreta del árbol.
class PantallaArticulo extends StatefulWidget {
  final int? materialId;
  final int? seccionIdInicial;
  const PantallaArticulo({super.key, this.materialId, this.seccionIdInicial});

  @override
  State<PantallaArticulo> createState() => _PantallaArticuloState();
}

class _PantallaArticuloState extends State<PantallaArticulo> {
  bool _cargando = true;
  bool _guardando = false;
  bool _editando = false;
  String? _error;

  Articulo? _material;
  List<Movimiento> _movimientos = [];
  List<Estanteria> _estanterias = [];
  String? _ip;

  final _formKey = GlobalKey<FormState>();
  final _codigo = TextEditingController();
  final _nombre = TextEditingController();
  final _descripcion = TextEditingController();
  final _unidad = TextEditingController();
  final _stockMinimo = TextEditingController(text: '0');
  final _stockInicial = TextEditingController(text: '0');

  int? _estanteriaSel;
  int? _baldaSel;
  int? _seccionSel;

  File? _fotoNueva;
  bool _borrarFoto = false;

  @override
  void initState() {
    super.initState();
    _editando = widget.materialId == null;
    rolesActualizadosNotifier.addListener(_alCambiarRoles);
    datosSincronizadosNotifier.addListener(_alCambiarDatos);
    _cargar();
  }

  @override
  void dispose() {
    rolesActualizadosNotifier.removeListener(_alCambiarRoles);
    datosSincronizadosNotifier.removeListener(_alCambiarDatos);
    _codigo.dispose();
    _nombre.dispose();
    _descripcion.dispose();
    _unidad.dispose();
    _stockMinimo.dispose();
    _stockInicial.dispose();
    super.dispose();
  }

  void _alCambiarRoles() {
    if (mounted) setState(() {});
  }

  /// Refresco automático (propia sincronización o cambios hechos en el PC).
  /// Si el usuario está editando el formulario no se toca nada para no
  /// perderle lo que está escribiendo: se aplicará al salir de la edición.
  /// No usa [_cargar] porque esa muestra el spinner a pantalla completa,
  /// lo que provocaría un parpadeo cada vez que llega un refresco en segundo plano.
  Future<void> _alCambiarDatos() async {
    if (_editando || widget.materialId == null) return;
    await _refrescarMaterial();
  }

  /// Vuelve a leer solo el artículo y sus movimientos (sin el spinner a
  /// pantalla completa de [_cargar]), para reflejar cambios de stock al
  /// momento tanto si vienen de esta pantalla como de fuera.
  Future<void> _refrescarMaterial() async {
    if (widget.materialId == null) return;
    try {
      final (material, movs) = await StockApi.obtenerMaterial(widget.materialId!);
      if (mounted) setState(() { _material = material; _movimientos = movs; });
    } catch (_) {}
  }

  Future<void> _cargar() async {
    setState(() { _cargando = true; _error = null; });
    try {
      _ip = await StockApi.ipActual();
      _estanterias = await StockApi.obtenerEstructura();
      if (widget.materialId != null) {
        final (material, movs) = await StockApi.obtenerMaterial(widget.materialId!);
        _material = material;
        _movimientos = movs;
        _rellenarFormulario(material);
      } else if (widget.seccionIdInicial != null) {
        _preseleccionarSeccion(widget.seccionIdInicial!);
      }
    } catch (e) {
      _error = e.toString();
    }
    if (mounted) setState(() => _cargando = false);
  }

  void _rellenarFormulario(Articulo m) {
    _codigo.text = m.codigo;
    _nombre.text = m.nombre;
    _descripcion.text = m.descripcion;
    _unidad.text = m.unidad;
    _stockMinimo.text = formatearCantidad(m.stockMinimo);
    if (m.seccionId != null) _preseleccionarSeccion(m.seccionId!);
  }

  void _preseleccionarSeccion(int seccionId) {
    for (final est in _estanterias) {
      for (final balda in est.baldas) {
        for (final sec in balda.secciones) {
          if (sec.id == seccionId) {
            _estanteriaSel = est.id;
            _baldaSel = balda.id;
            _seccionSel = sec.id;
            return;
          }
        }
      }
    }
  }

  Estanteria? get _estanteriaActual =>
      _estanterias.where((e) => e.id == _estanteriaSel).firstOrNull;
  Balda? get _baldaActual =>
      _estanteriaActual?.baldas.where((b) => b.id == _baldaSel).firstOrNull;

  Future<void> _elegirFoto(ImageSource origen) async {
    final picker = ImagePicker();
    final archivo = await picker.pickImage(source: origen, maxWidth: 1600, imageQuality: 85);
    if (archivo != null) {
      setState(() { _fotoNueva = File(archivo.path); _borrarFoto = false; });
    }
  }

  Future<void> _guardar() async {
    if (!_formKey.currentState!.validate()) return;
    if (_seccionSel == null) {
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(tt('msg_selecciona_seccion', 'Selecciona una sección del almacén.'))));
      return;
    }
    setState(() => _guardando = true);
    try {
      final sincronizado = await StockApi.guardarMaterial(
        id: widget.materialId,
        codigo: _codigo.text.trim(),
        nombre: _nombre.text.trim(),
        descripcion: _descripcion.text.trim(),
        unidad: _unidad.text.trim(),
        stockMinimo: double.tryParse(_stockMinimo.text.replaceAll(',', '.')) ?? 0,
        seccionId: _seccionSel!,
        stockInicial: double.tryParse(_stockInicial.text.replaceAll(',', '.')) ?? 0,
        foto: _fotoNueva,
        borrarFoto: _borrarFoto,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(sincronizado
          ? tt('msg_articulo_guardado', '✅ Artículo guardado')
          : tt('msg_articulo_pendiente', '💾 Guardado en el móvil. Se enviará al PC cuando haya conexión.'))));
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('${tt('msg_error_guardar', '❌ No se pudo guardar el artículo')}: $e')));
      }
    }
    if (mounted) setState(() => _guardando = false);
  }

  Future<void> _registrarMovimiento(String tipo) async {
    final cantidadCtrl = TextEditingController();
    final motivoCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(tt('dlg_registrar_movimiento', 'Registrar movimiento')),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(
            controller: cantidadCtrl,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            autofocus: true,
            decoration: InputDecoration(labelText: tt('lbl_cantidad', 'Cantidad')),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: motivoCtrl,
            decoration: InputDecoration(labelText: tt('lbl_motivo', 'Motivo (opcional)')),
          ),
        ]),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(t('btn_cancelar'))),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: Text(t('btn_guardar'))),
        ],
      ),
    );
    if (ok != true) return;
    final cantidad = double.tryParse(cantidadCtrl.text.replaceAll(',', '.')) ?? 0;
    if (cantidad <= 0) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(tt('msg_cantidad_invalida', 'Introduce una cantidad mayor que 0.'))));
      }
      return;
    }
    try {
      final sincronizado = await StockApi.registrarMovimiento(
          materialId: widget.materialId!, tipo: tipo, cantidad: cantidad, motivo: motivoCtrl.text.trim());
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(sincronizado
          ? tt('msg_movimiento_registrado', '✅ Movimiento registrado')
          : tt('msg_movimiento_pendiente', '💾 Guardado en el móvil. Se enviará al PC cuando haya conexión.'))));
      _refrescarMaterial();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final puedeGestionar = AuthService.puedeGestionarAlmacen;
    // Los artículos creados sin conexión tienen un id temporal negativo hasta
    // que el PC confirma el alta: no se pueden editar ni registrar
    // movimientos sobre ellos hasta entonces.
    final esTemporal = widget.materialId != null && widget.materialId! < 0;
    final titulo = widget.materialId == null
        ? tt('titulo_nuevo_articulo', 'Nuevo artículo')
        : (_editando
            ? tt('titulo_editar_articulo', 'Editar artículo')
            : (_material?.nombre ?? tt('titulo_articulo', 'Artículo')));

    return Scaffold(
      appBar: AppBar(
        title: Text(titulo),
        actions: [
          if (widget.materialId != null && !_editando && puedeGestionar && !esTemporal)
            IconButton(icon: const Icon(Icons.edit), onPressed: () => setState(() => _editando = true)),
        ],
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null && _material == null && widget.materialId != null
              ? Center(child: Text(_error!))
              : _editando
                  ? _construirFormulario()
                  : _construirVista(),
      floatingActionButton: (_editando && !_guardando)
          ? FloatingActionButton.extended(
              onPressed: _guardar,
              icon: const Icon(Icons.save),
              label: Text(t('btn_guardar')),
            )
          : (_guardando ? const FloatingActionButton(onPressed: null, child: CircularProgressIndicator()) : null),
    );
  }

  Widget _construirVista() {
    final m = _material!;
    final esTemporal = widget.materialId != null && widget.materialId! < 0;
    return RefreshIndicator(
      onRefresh: _cargar,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (m.foto != null && _ip != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.network(StockApi.urlFoto(_ip!, m.foto!),
                  height: 220, width: double.infinity, fit: BoxFit.cover),
            )
          else
            Container(
              height: 160,
              decoration: BoxDecoration(
                  color: Theme.of(context).cardColor, borderRadius: BorderRadius.circular(12)),
              child: Center(
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.inventory_2, size: 48, color: Colors.grey),
                const SizedBox(height: 8),
                Text(tt('lbl_sin_foto', 'Sin foto'), style: const TextStyle(color: Colors.grey)),
              ])),
            ),
          const SizedBox(height: 16),
          Text(m.nombre, style: Theme.of(context).textTheme.headlineSmall),
          if (m.codigo.isNotEmpty)
            Text(m.codigo, style: const TextStyle(color: Colors.grey)),
          if (esTemporal) ...[
            const SizedBox(height: 4),
            Row(children: [
              const Icon(Icons.cloud_upload, size: 16, color: Colors.orange),
              const SizedBox(width: 4),
              Text(tt('lbl_pendiente_sincronizar', 'Pendiente de enviar al PC'),
                  style: const TextStyle(color: Colors.orange)),
            ]),
          ],
          const SizedBox(height: 12),
          if (m.descripcion.isNotEmpty) ...[
            Text(m.descripcion),
            const SizedBox(height: 12),
          ],
          _filaDato(tt('lbl_cantidad_actual', 'Cantidad actual'),
              '${formatearCantidad(m.stockActual)} ${m.unidad}'.trim(),
              color: colorStock(m.stockActual, m.stockMinimo)),
          _filaDato(tt('lbl_cantidad_minima', 'Cantidad mínima'),
              '${formatearCantidad(m.stockMinimo)} ${m.unidad}'.trim()),
          _filaDato(tt('lbl_ubicacion', 'Ubicación'),
              m.ubicacion.isEmpty ? tt('lbl_sin_ubicacion', 'Sin ubicación') : m.ubicacion),
          if (AuthService.puedeGestionarAlmacen && !esTemporal) ...[
            const SizedBox(height: 16),
            Row(children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _registrarMovimiento('entrada'),
                  icon: const Icon(Icons.add_circle_outline, color: Colors.green),
                  label: Text(t('btn_entrada')),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _registrarMovimiento('salida'),
                  icon: const Icon(Icons.remove_circle_outline, color: Colors.red),
                  label: Text(t('btn_salida')),
                ),
              ),
            ]),
          ],
          const SizedBox(height: 20),
          Text(tt('lbl_movimientos', 'Últimos movimientos'), style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          if (_movimientos.isEmpty)
            Text(tt('msg_sin_movimientos', 'Sin movimientos registrados'), style: const TextStyle(color: Colors.grey))
          else
            ..._movimientos.map((mv) => mv.tipo == 'traslado'
                ? ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.swap_horiz, color: Colors.blueAccent),
                    title: Text(mv.motivo),
                    subtitle: Text([mv.fecha, mv.usuarioNombre]
                        .where((s) => s.isNotEmpty)
                        .join(' · ')),
                  )
                : ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Icon(
                      mv.tipo == 'entrada' ? Icons.add_circle : Icons.remove_circle,
                      color: mv.tipo == 'entrada' ? Colors.green : Colors.red,
                    ),
                    title: Text('${formatearCantidad(mv.cantidad)} ${m.unidad}'.trim()),
                    subtitle: Text([mv.fecha, mv.usuarioNombre, mv.motivo]
                        .where((s) => s.isNotEmpty)
                        .join(' · ')),
                  )),
        ],
      ),
    );
  }

  Widget _filaDato(String etiqueta, String valor, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(children: [
        Expanded(flex: 2, child: Text(etiqueta, style: const TextStyle(color: Colors.grey))),
        Expanded(
          flex: 3,
          child: Text(valor, style: TextStyle(fontWeight: FontWeight.bold, color: color)),
        ),
      ]),
    );
  }

  Widget _construirFormulario() {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
        children: [
          Center(
            child: Stack(children: [
              if (_fotoNueva != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.file(_fotoNueva!, height: 180, width: 260, fit: BoxFit.cover),
                )
              else if (!_borrarFoto && _material?.foto != null && _ip != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.network(StockApi.urlFoto(_ip!, _material!.foto!),
                      height: 180, width: 260, fit: BoxFit.cover),
                )
              else
                Container(
                  height: 180,
                  width: 260,
                  decoration: BoxDecoration(
                      color: Theme.of(context).cardColor, borderRadius: BorderRadius.circular(12)),
                  child: const Center(child: Icon(Icons.inventory_2, size: 48, color: Colors.grey)),
                ),
            ]),
          ),
          const SizedBox(height: 8),
          Wrap(alignment: WrapAlignment.center, spacing: 8, children: [
            TextButton.icon(
              onPressed: () => _elegirFoto(ImageSource.camera),
              icon: const Icon(Icons.camera_alt),
              label: Text(tt('btn_camara', 'Cámara')),
            ),
            TextButton.icon(
              onPressed: () => _elegirFoto(ImageSource.gallery),
              icon: const Icon(Icons.photo_library),
              label: Text(tt('btn_galeria', 'Galería')),
            ),
            if (_fotoNueva != null || (_material?.foto != null && !_borrarFoto))
              TextButton.icon(
                onPressed: () => setState(() { _fotoNueva = null; _borrarFoto = true; }),
                icon: const Icon(Icons.delete_outline, color: Colors.red),
                label: Text(tt('btn_quitar_foto', 'Quitar foto'), style: const TextStyle(color: Colors.red)),
              ),
          ]),
          const SizedBox(height: 16),
          TextFormField(
            controller: _nombre,
            decoration: InputDecoration(labelText: tt('lbl_nombre', 'Nombre'), border: const OutlineInputBorder()),
            validator: (v) => (v == null || v.trim().isEmpty)
                ? tt('msg_nombre_obligatorio', 'El nombre es obligatorio.')
                : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _codigo,
            decoration: InputDecoration(labelText: tt('lbl_codigo', 'Código'), border: const OutlineInputBorder()),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _descripcion,
            maxLines: 3,
            decoration: InputDecoration(labelText: tt('lbl_descripcion', 'Descripción'), border: const OutlineInputBorder()),
          ),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(
              child: TextFormField(
                controller: _unidad,
                decoration: InputDecoration(labelText: tt('lbl_unidad', 'Unidad'), border: const OutlineInputBorder()),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextFormField(
                controller: _stockMinimo,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(labelText: tt('lbl_cantidad_minima', 'Cantidad mínima'), border: const OutlineInputBorder()),
              ),
            ),
          ]),
          if (widget.materialId == null) ...[
            const SizedBox(height: 12),
            TextFormField(
              controller: _stockInicial,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(labelText: tt('lbl_cantidad_inicial', 'Cantidad inicial'), border: const OutlineInputBorder()),
            ),
          ],
          const SizedBox(height: 20),
          Text(tt('lbl_ubicacion', 'Ubicación'), style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          DropdownButtonFormField<int>(
            initialValue: _estanteriaSel,
            decoration: InputDecoration(labelText: tt('lbl_estanteria', 'Estantería'), border: const OutlineInputBorder()),
            items: _estanterias
                .map((e) => DropdownMenuItem(value: e.id, child: Text(e.nombre)))
                .toList(),
            onChanged: (v) {
              if (v == _estanteriaSel) return;
              setState(() { _estanteriaSel = v; _baldaSel = null; _seccionSel = null; });
            },
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            initialValue: _baldaSel,
            decoration: InputDecoration(labelText: tt('lbl_balda', 'Balda'), border: const OutlineInputBorder()),
            items: (_estanteriaActual?.baldas ?? [])
                .map((b) => DropdownMenuItem(
                    value: b.id,
                    child: Text(b.numero == 0
                        ? tt('lbl_suelo', 'Suelo')
                        : '${tt('lbl_balda', 'Balda')} ${textoBalda(b.numero, _estanteriaActual!.estiloBaldas)}')))
                .toList(),
            onChanged: _estanteriaActual == null
                ? null
                : (v) {
                    if (v == _baldaSel) return;
                    setState(() { _baldaSel = v; _seccionSel = null; });
                  },
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            initialValue: _seccionSel,
            decoration: InputDecoration(labelText: tt('lbl_seccion', 'Sección'), border: const OutlineInputBorder()),
            items: (_baldaActual?.secciones ?? [])
                .map((s) => DropdownMenuItem(value: s.id, child: Text(s.nombre)))
                .toList(),
            onChanged: _baldaActual == null ? null : (v) => setState(() => _seccionSel = v),
          ),
        ],
      ),
    );
  }
}

extension _FirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
