// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro Stock - Gestión de almacén
// Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft) <anabasasoft@gmail.com>
// https://github.com/AnabasaSoft/MantPro
//
// Este programa es software libre: puedes redistribuirlo y/o modificarlo bajo
// los términos de la Licencia Pública General Affero de GNU publicada por la
// Free Software Foundation, ya sea la versión 3 de la Licencia o (a tu
// elección) cualquier versión posterior.
//
// Este programa se distribuye con la esperanza de que sea útil, pero SIN
// NINGUNA GARANTÍA; ni siquiera la garantía implícita de COMERCIABILIDAD o
// IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la Licencia Pública
// General Affero de GNU para más detalles.
//
// Deberías haber recibido una copia de la Licencia Pública General Affero de
// GNU junto con este programa. Si no, consulta <https://www.gnu.org/licenses/>.

import 'dart:math';
import 'package:flutter/material.dart';
import '../api.dart';
import '../i18n/strings.dart';
import '../modelos.dart';

/// Pantalla que se abre al pulsar la notificación diaria de comprobación de
/// stock: elige 5 materiales al azar del almacén y deja corregir la cantidad
/// actual de cada uno sin tener que buscarlos manualmente.
class PantallaComprobarStock extends StatefulWidget {
  const PantallaComprobarStock({super.key});

  @override
  State<PantallaComprobarStock> createState() => _PantallaComprobarStockState();
}

class _PantallaComprobarStockState extends State<PantallaComprobarStock> {
  bool _cargando = true;
  String? _error;
  List<Articulo> _seleccionados = [];
  final Map<int, TextEditingController> _controladores = {};
  final Set<int> _guardando = {};
  final Set<int> _confirmados = {};
  // Revisión de hoy (quién, qué artículos y cuáles lleva revisados): se guarda
  // en el móvil y se envía al PC cada vez que avanza.
  Map<String, dynamic> _revision = {};

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    for (final c in _controladores.values) {
      c.dispose();
    }
    super.dispose();
  }

  String _fechaDeHoy() {
    final h = DateTime.now();
    return '${h.year.toString().padLeft(4, '0')}-${h.month.toString().padLeft(2, '0')}-${h.day.toString().padLeft(2, '0')}';
  }

  Map<String, dynamic> _lineaNueva(Articulo a) => {
        'material_id': a.id,
        'codigo': a.codigo,
        'nombre': a.nombre,
        'ubicacion': a.ubicacion,
        'unidad': a.unidad,
        'cantidad_sistema': a.stockActual,
        'cantidad_contada': null,
        'revisado': false,
        'fecha_revision': '',
      };

  Map<String, dynamic>? _lineaDe(int materialId) {
    for (final l in (_revision['lineas'] as List)) {
      if (l['material_id'] == materialId) return l as Map<String, dynamic>;
    }
    return null;
  }

  Future<void> _cargar() async {
    setState(() { _cargando = true; _error = null; });
    try {
      final materiales = await StockApi.obtenerMateriales();
      final previa = await StockApi.revisionDeHoy();
      if (previa != null) {
        // Ya se había empezado hoy: se sigue con los mismos artículos y lo
        // ya revisado (los que se hayan borrado desde entonces se quitan).
        final porId = {for (final m in materiales) m.id: m};
        final lineas = (previa['lineas'] as List).where((l) => porId.containsKey(l['material_id'])).toList();
        previa['lineas'] = lineas;
        _revision = previa;
        _seleccionados = [for (final l in lineas) porId[l['material_id']]!];
        for (final l in lineas) {
          if (l['revisado'] == true) _confirmados.add(l['material_id'] as int);
        }
      }
      if (previa == null || (_revision['lineas'] as List).isEmpty) {
        // Semilla basada en el día de hoy: la selección es al azar, pero se
        // mantiene igual si se entra varias veces el mismo día y cambia sola
        // al día siguiente, sin tener que guardar nada en el servidor.
        final hoy = DateTime.now();
        final semilla = hoy.year * 10000 + hoy.month * 100 + hoy.day;
        final lista = List<Articulo>.from(materiales)..shuffle(Random(semilla));
        _seleccionados = lista.take(5).toList();
        _confirmados.clear();
        _revision = {
          'uid': '${_fechaDeHoy()}-${DateTime.now().microsecondsSinceEpoch}',
          'fecha': _fechaDeHoy(),
          'lineas': [for (final a in _seleccionados) _lineaNueva(a)],
        };
        // Queda constancia de que se ha abierto la revisión aunque luego no
        // se llegue a revisar nada (0 de 5).
        if (_seleccionados.isNotEmpty) await StockApi.guardarRevision(_revision);
      }
      for (final a in _seleccionados) {
        final linea = _lineaDe(a.id);
        final contada = (linea != null && linea['revisado'] == true) ? linea['cantidad_contada'] as num? : null;
        _controladores[a.id] = TextEditingController(
            text: formatearCantidad(contada?.toDouble() ?? a.stockActual));
      }
    } catch (e) {
      _error = e.toString();
    }
    if (mounted) setState(() => _cargando = false);
  }

  /// Apunta en la revisión que [a] está revisado con [contada] y la guarda
  /// (y la manda al PC si hay conexión).
  Future<void> _marcarRevisado(Articulo a, double contada) async {
    final linea = _lineaDe(a.id);
    if (linea != null) {
      final h = DateTime.now();
      String dos(int n) => n.toString().padLeft(2, '0');
      linea['cantidad_contada'] = contada;
      linea['revisado'] = true;
      linea['fecha_revision'] =
          '${h.year}-${dos(h.month)}-${dos(h.day)} ${dos(h.hour)}:${dos(h.minute)}:${dos(h.second)}';
    }
    try {
      await StockApi.guardarRevision(_revision);
    } catch (_) {}
  }

  Future<void> _confirmar(Articulo a) async {
    final controlador = _controladores[a.id]!;
    final nuevaCantidad = double.tryParse(controlador.text.replaceAll(',', '.'));
    if (nuevaCantidad == null || nuevaCantidad < 0) {
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(tt('msg_cantidad_invalida', 'Introduce una cantidad válida.'))));
      return;
    }
    final delta = nuevaCantidad - a.stockActual;
    if (delta == 0) {
      await _marcarRevisado(a, nuevaCantidad);
      if (mounted) setState(() => _confirmados.add(a.id));
      return;
    }
    setState(() => _guardando.add(a.id));
    try {
      await StockApi.registrarMovimiento(
        materialId: a.id,
        tipo: delta > 0 ? 'entrada' : 'salida',
        cantidad: delta.abs(),
        motivo: tt('motivo_comprobacion_stock', 'Comprobación de stock'),
      );
      await _marcarRevisado(a, nuevaCantidad);
      if (!mounted) return;
      setState(() => _confirmados.add(a.id));
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    }
    if (mounted) setState(() => _guardando.remove(a.id));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(tt('titulo_comprobar_stock', 'Comprobar stock'))),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _seleccionados.isEmpty
                  ? Center(child: Text(tt('msg_sin_materiales', 'No hay materiales en el almacén.')))
                  : ListView(
                      padding: const EdgeInsets.all(16),
                      children: [
                        Text(
                          tt('lbl_comprobar_stock_intro',
                              'Comprueba la cantidad real de estos materiales y corrígela si hace falta.'),
                          style: const TextStyle(color: Colors.grey),
                        ),
                        const SizedBox(height: 12),
                        _construirProgreso(),
                        const SizedBox(height: 12),
                        ..._seleccionados.map(_construirFila),
                      ],
                    ),
    );
  }

  /// «2 de 5 revisados» y, al llegar al total, el aviso de revisión completa.
  Widget _construirProgreso() {
    final total = _seleccionados.length;
    final hechos = _confirmados.length;
    final completa = total > 0 && hechos >= total;
    return Card(
      color: completa ? Colors.green.withOpacity(0.15) : null,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(
            tt('lbl_revision_progreso', '{n} de {total} revisados')
                .replaceAll('{n}', '$hechos')
                .replaceAll('{total}', '$total'),
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(value: total == 0 ? 0 : hechos / total),
          if (completa) ...[
            const SizedBox(height: 8),
            Text(tt('msg_revision_completa', '✅ Revisión completa: has comprobado los {total} artículos.')
                .replaceAll('{total}', '$total')),
          ],
        ]),
      ),
    );
  }

  Widget _construirFila(Articulo a) {
    final confirmado = _confirmados.contains(a.id);
    final guardando = _guardando.contains(a.id);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(a.nombre, style: const TextStyle(fontWeight: FontWeight.bold)),
              if (a.ubicacion.isNotEmpty)
                Text(a.ubicacion, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ]),
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 90,
            child: TextField(
              controller: _controladores[a.id],
              enabled: !confirmado,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              textAlign: TextAlign.center,
              decoration: InputDecoration(
                isDense: true,
                border: const OutlineInputBorder(),
                suffixText: a.unidad,
              ),
            ),
          ),
          const SizedBox(width: 8),
          confirmado
              ? const Icon(Icons.check_circle, color: Colors.green)
              : guardando
                  ? const SizedBox(
                      width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2))
                  : IconButton(
                      icon: const Icon(Icons.check),
                      tooltip: t('btn_guardar'),
                      onPressed: () => _confirmar(a),
                    ),
        ]),
      ),
    );
  }
}
