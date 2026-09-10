// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api.dart';
import '../i18n/strings.dart';
import '../modelos.dart';
import '../sincronizador.dart';
import 'pantalla_articulo.dart';

/// Pestaña "Almacén": una pestaña por estantería, cada una con un árbol
/// balda > sección > artículos. La estructura (estanterías/baldas/secciones)
/// solo se lee del PC, nunca se modifica desde el móvil.
class PantallaAlmacen extends StatefulWidget {
  const PantallaAlmacen({super.key});
  @override
  State<PantallaAlmacen> createState() => _PantallaAlmacenState();
}

class _PantallaAlmacenState extends State<PantallaAlmacen> {
  bool _cargando = true;
  String? _error;
  List<Estanteria> _estanterias = [];
  Map<int, List<Articulo>> _materialesPorSeccion = {};

  @override
  void initState() {
    super.initState();
    rolesActualizadosNotifier.addListener(_alCambiarRolesODatos);
    datosSincronizadosNotifier.addListener(_alCambiarRolesODatos);
    _cargar();
  }

  @override
  void dispose() {
    rolesActualizadosNotifier.removeListener(_alCambiarRolesODatos);
    datosSincronizadosNotifier.removeListener(_alCambiarRolesODatos);
    super.dispose();
  }

  void _alCambiarRolesODatos() {
    // No solo repintar: la sincronización en segundo plano ya ha dejado la
    // caché al día (propia o del PC), así que hay que releer los datos para
    // que las cantidades se actualicen solas, sin pull-to-refresh manual.
    _recargarSilencioso();
  }

  /// Igual que [_cargar] pero sin mostrar el spinner de carga a pantalla
  /// completa: se usa para refrescos automáticos en segundo plano.
  Future<void> _recargarSilencioso() async {
    try {
      final estanterias = await StockApi.obtenerEstructura();
      final materiales = await StockApi.obtenerMateriales();
      final agrupados = <int, List<Articulo>>{};
      for (final m in materiales) {
        if (m.seccionId == null) continue;
        agrupados.putIfAbsent(m.seccionId!, () => []).add(m);
      }
      if (mounted) {
        setState(() {
          _estanterias = estanterias;
          _materialesPorSeccion = agrupados;
        });
      }
    } catch (_) {
      // Sin conexión ni caché legible: se deja lo que ya había en pantalla.
    }
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final ip = prefs.getString('pc_ip_url');
      if (ip != null) {
        // No se espera aquí: cada método de StockApi ya intenta la red y cae
        // a caché solo si hace falta, así que esta pantalla se pinta al
        // momento con lo que haya. La sincronización completa se lanza aparte
        // y esta pantalla se refresca sola cuando termina (datosSincronizadosNotifier).
        // ignore: unawaited_futures
        StockSincronizador.sincronizarTodo(ip, silencioso: true);
      }
      final estanterias = await StockApi.obtenerEstructura();
      final materiales = await StockApi.obtenerMateriales();
      final agrupados = <int, List<Articulo>>{};
      for (final m in materiales) {
        if (m.seccionId == null) continue;
        agrupados.putIfAbsent(m.seccionId!, () => []).add(m);
      }
      setState(() {
        _estanterias = estanterias;
        _materialesPorSeccion = agrupados;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
    if (mounted) setState(() => _cargando = false);
  }

  Future<void> _abrirArticulo({int? materialId, int? seccionId}) async {
    final cambiado = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => PantallaArticulo(
            materialId: materialId, seccionIdInicial: seccionId),
      ),
    );
    if (cambiado == true) _cargar();
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (context, _, __) => _construir(context),
    );
  }

  Widget _construir(BuildContext context) {
    if (_cargando) return const Center(child: CircularProgressIndicator());

    // Igual que en "Bajo mínimo": todo el contenido (error, sin estanterías o
    // el árbol en sí) va dentro de un único RefreshIndicator, para poder
    // forzar la actualización con un arrastre hacia abajo aunque todavía no
    // haya ninguna estantería configurada.
    return RefreshIndicator(
      onRefresh: _cargar,
      child: _error != null
          ? ListView(children: [
              Padding(
                padding: const EdgeInsets.all(24),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(_error!, textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  ElevatedButton(onPressed: _cargar, child: const Text('↻')),
                ]),
              ),
            ])
          : _estanterias.isEmpty
              ? ListView(children: [
                  Padding(
                    padding: const EdgeInsets.all(24),
                    child: Center(
                        child: Text(tt('msg_sin_estanterias',
                            'No hay estanterías configuradas en el almacén'))),
                  ),
                ])
              : DefaultTabController(
                  length: _estanterias.length,
                  child: Column(
                    children: [
                      Material(
                        color: Theme.of(context).appBarTheme.backgroundColor,
                        child: TabBar(
                          isScrollable: true,
                          tabs: _estanterias
                              .map((e) => Tab(text: e.nombre))
                              .toList(),
                        ),
                      ),
                      Expanded(
                        child: TabBarView(
                          children: _estanterias
                              .map((e) => _ArbolEstanteria(
                                    estanteria: e,
                                    materialesPorSeccion: _materialesPorSeccion,
                                    onAbrirArticulo: (id) =>
                                        _abrirArticulo(materialId: id),
                                    onAnadirArticulo: (seccionId) =>
                                        _abrirArticulo(seccionId: seccionId),
                                  ))
                              .toList(),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}

/// El backend genera los nombres de sección por defecto como "Sección A"
/// (letras desde la versión actual; "Sección 1" en estanterías creadas con
/// versiones antiguas, texto fijo en español, ver almacen.py). Si el nombre
/// sigue uno de esos patrones lo traducimos igual que "Balda"; si el usuario
/// le puso un nombre propio desde el escritorio, se muestra tal cual sin tocarlo.
final _reSeccionAuto = RegExp(r'^Sección ([A-Z]+|\d+)$');
String _tituloSeccion(String nombre) {
  final m = _reSeccionAuto.firstMatch(nombre);
  if (m == null) return nombre;
  return '${tt('lbl_seccion', 'Sección')} ${m.group(1)}';
}

class _ArbolEstanteria extends StatelessWidget {
  final Estanteria estanteria;
  final Map<int, List<Articulo>> materialesPorSeccion;
  final void Function(int materialId) onAbrirArticulo;
  final void Function(int seccionId) onAnadirArticulo;

  const _ArbolEstanteria({
    required this.estanteria,
    required this.materialesPorSeccion,
    required this.onAbrirArticulo,
    required this.onAnadirArticulo,
  });

  @override
  Widget build(BuildContext context) {
    final puedeGestionar = AuthService.puedeGestionarAlmacen;
    return ListView(
      padding: const EdgeInsets.symmetric(vertical: 8),
      children: estanteria.baldas.map((balda) {
        final tituloBalda = balda.numero == 0
            ? tt('lbl_suelo', 'Suelo')
            : '${tt('lbl_balda', 'Balda')} ${textoBalda(balda.numero, estanteria.estiloBaldas)}';
        return ExpansionTile(
          title: Text(tituloBalda,
              style: const TextStyle(fontWeight: FontWeight.bold)),
          initiallyExpanded: true,
          children: balda.secciones.map((seccion) {
            final materiales = materialesPorSeccion[seccion.id] ?? [];
            return ExpansionTile(
              title: Text(_tituloSeccion(seccion.nombre)),
              initiallyExpanded: true,
              trailing: puedeGestionar
                  ? IconButton(
                      icon: const Icon(Icons.add_circle_outline),
                      tooltip: tt('btn_anadir', 'Añadir'),
                      onPressed: () => onAnadirArticulo(seccion.id),
                    )
                  : const Icon(Icons.expand_more),
              children: materiales.isEmpty
                  ? [
                      ListTile(
                        dense: true,
                        title: Text(
                            tt('msg_sin_articulos_seccion', 'Sin artículos'),
                            style: const TextStyle(color: Colors.grey)),
                      )
                    ]
                  : materiales
                      .map((m) => ListTile(
                            dense: true,
                            leading: const Icon(Icons.inventory_2_outlined),
                            title: Text(m.nombre),
                            trailing: Text(
                              '${formatearCantidad(m.stockActual)} ${m.unidad}'
                                  .trim(),
                              style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color:
                                      colorStock(m.stockActual, m.stockMinimo)),
                            ),
                            onTap: () => onAbrirArticulo(m.id),
                          ))
                      .toList(),
            );
          }).toList(),
        );
      }).toList(),
    );
  }
}
