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

const String _kZonaSeleccionada = 'stock_zona_seleccionada';

class _PantallaAlmacenState extends State<PantallaAlmacen> {
  bool _cargando = true;
  String? _error;
  List<Estanteria> _estanterias = [];
  List<Zona> _zonas = [];
  int? _zonaSeleccionada;
  Map<int, List<Articulo>> _materialesPorSeccion = {};
  Map<int, List<Articulo>> _materialesPorBaldaPendiente = {};

  /// Estanterías de la zona seleccionada. Si no hay ninguna zona (instalación
  /// antigua sin sincronizar todavía) o la estantería no tiene zona asignada,
  /// se muestra igualmente para no dejarla "desaparecida" de la vista.
  List<Estanteria> get _estanteriasFiltradas => _zonaSeleccionada == null
      ? _estanterias
      : _estanterias.where((e) => e.zonaId == null || e.zonaId == _zonaSeleccionada).toList();

  Future<void> _elegirZona(int? zonaId) async {
    setState(() => _zonaSeleccionada = zonaId);
    final prefs = await SharedPreferences.getInstance();
    if (zonaId == null) {
      await prefs.remove(_kZonaSeleccionada);
    } else {
      await prefs.setInt(_kZonaSeleccionada, zonaId);
    }
  }

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
      final zonas = await StockApi.obtenerZonas();
      final materiales = await StockApi.obtenerMateriales();
      final (agrupados, agrupadosPorBalda) = _agrupar(materiales);
      if (mounted) {
        setState(() {
          _estanterias = estanterias;
          _zonas = zonas;
          if (_zonaSeleccionada != null && !zonas.any((z) => z.id == _zonaSeleccionada)) {
            _zonaSeleccionada = null;
          }
          _materialesPorSeccion = agrupados;
          _materialesPorBaldaPendiente = agrupadosPorBalda;
        });
      }
    } catch (_) {
      // Sin conexión ni caché legible: se deja lo que ya había en pantalla.
    }
  }

  /// Agrupa los artículos por sección para el árbol y, aparte, los dados de
  /// alta sin conexión directamente sobre una balda (todavía sin sección
  /// creada) por el id de esa balda, para poder mostrarlos sueltos.
  (Map<int, List<Articulo>>, Map<int, List<Articulo>>) _agrupar(List<Articulo> materiales) {
    final porSeccion = <int, List<Articulo>>{};
    final porBaldaPendiente = <int, List<Articulo>>{};
    for (final m in materiales) {
      if (m.seccionId != null) {
        porSeccion.putIfAbsent(m.seccionId!, () => []).add(m);
      } else if (m.baldaIdPendiente != null) {
        porBaldaPendiente.putIfAbsent(m.baldaIdPendiente!, () => []).add(m);
      }
    }
    return (porSeccion, porBaldaPendiente);
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
      final zonas = await StockApi.obtenerZonas();
      final materiales = await StockApi.obtenerMateriales();
      final (agrupados, agrupadosPorBalda) = _agrupar(materiales);
      final zonaGuardada = prefs.getInt(_kZonaSeleccionada);
      setState(() {
        _estanterias = estanterias;
        _zonas = zonas;
        _zonaSeleccionada = (zonaGuardada != null && zonas.any((z) => z.id == zonaGuardada))
            ? zonaGuardada
            : null;
        _materialesPorSeccion = agrupados;
        _materialesPorBaldaPendiente = agrupadosPorBalda;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
    if (mounted) setState(() => _cargando = false);
  }

  Future<void> _abrirArticulo({int? materialId, int? seccionId, int? baldaId}) async {
    final cambiado = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (_) => PantallaArticulo(
            materialId: materialId, seccionIdInicial: seccionId, baldaIdInicial: baldaId),
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

    final estanterias = _estanteriasFiltradas;

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
          : Column(
              children: [
                if (_zonas.length > 1) _selectorZona(context),
                Expanded(
                  child: estanterias.isEmpty
                      ? ListView(children: [
                          Padding(
                            padding: const EdgeInsets.all(24),
                            child: Center(
                                child: Text(tt('msg_sin_estanterias',
                                    'No hay estanterías configuradas en el almacén'))),
                          ),
                        ])
                      : DefaultTabController(
                          length: estanterias.length,
                          child: Column(
                            children: [
                              Material(
                                color: Theme.of(context).appBarTheme.backgroundColor,
                                child: TabBar(
                                  isScrollable: true,
                                  // La barra siempre usa el color oscuro del AppBar (igual en
                                  // modo claro y oscuro), así que el texto tiene que ser
                                  // siempre claro; si no se fija aquí, en modo claro el tema
                                  // pone letras oscuras y quedan ilegibles sobre ese fondo.
                                  labelColor: Colors.white,
                                  unselectedLabelColor: Colors.white70,
                                  tabs: estanterias
                                      .map((e) => Tab(text: e.nombre))
                                      .toList(),
                                ),
                              ),
                              Expanded(
                                child: TabBarView(
                                  children: estanterias
                                      .map((e) => _ArbolEstanteria(
                                            estanteria: e,
                                            materialesPorSeccion: _materialesPorSeccion,
                                            materialesPorBaldaPendiente: _materialesPorBaldaPendiente,
                                            onAbrirArticulo: (id) =>
                                                _abrirArticulo(materialId: id),
                                            onAnadirArticulo: (seccionId) =>
                                                _abrirArticulo(seccionId: seccionId),
                                            onAnadirArticuloBalda: (baldaId) =>
                                                _abrirArticulo(baldaId: baldaId),
                                          ))
                                      .toList(),
                                ),
                              ),
                            ],
                          ),
                        ),
                ),
              ],
            ),
    );
  }

  Widget _selectorZona(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: DropdownButtonFormField<int?>(
        initialValue: _zonaSeleccionada,
        decoration: InputDecoration(
          labelText: tt('lbl_zona', 'Zona'),
          border: const OutlineInputBorder(),
          isDense: true,
        ),
        items: [
          DropdownMenuItem<int?>(value: null, child: Text(tt('txt_todas_zonas', 'Todas las zonas'))),
          ..._zonas.map((z) => DropdownMenuItem<int?>(value: z.id, child: Text(z.nombre))),
        ],
        onChanged: _elegirZona,
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
  final Map<int, List<Articulo>> materialesPorBaldaPendiente;
  final void Function(int materialId) onAbrirArticulo;
  final void Function(int seccionId) onAnadirArticulo;
  final void Function(int baldaId) onAnadirArticuloBalda;

  const _ArbolEstanteria({
    required this.estanteria,
    required this.materialesPorSeccion,
    required this.materialesPorBaldaPendiente,
    required this.onAbrirArticulo,
    required this.onAnadirArticulo,
    required this.onAnadirArticuloBalda,
  });

  @override
  Widget build(BuildContext context) {
    final puedeGestionar = AuthService.puedeGestionarAlmacen;
    return ListView(
      padding: const EdgeInsets.symmetric(vertical: 8),
      children: estanteria.baldas.map((balda) {
        final esSuelo = balda.numero == 0;
        final tituloBalda = esSuelo
            ? tt('lbl_suelo', 'Suelo')
            : '${tt('lbl_balda', 'Balda')} ${textoBalda(balda.numero, estanteria.estiloBaldas)}';
        // El hueco de suelo se distingue con un color propio, igual que en el
        // árbol del PC, para que se note de un vistazo que no es una balda más.
        final oscuro = Theme.of(context).brightness == Brightness.dark;
        final colorSuelo = oscuro ? const Color(0xFFE0B34D) : const Color(0xFF8A6210);
        return GestureDetector(
          // Dejar pulsado sobre una balda o hueco de suelo permite añadir un
          // artículo ahí directamente, aunque todavía no tenga ninguna
          // sección creada: el servidor la crea sola de forma transparente.
          onLongPress: puedeGestionar ? () => onAnadirArticuloBalda(balda.id) : null,
          child: ExpansionTile(
            title: Text(tituloBalda,
                style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: esSuelo ? colorSuelo : null)),
            initiallyExpanded: true,
            children: [
              // Artículos ubicados directamente en la balda (dados de alta
              // dejando pulsado sobre ella, sin elegir sección): se muestran
              // sueltos, sin la sección implícita que los agrupa por dentro.
              ...balda.secciones
                  .where((s) => s.implicita)
                  .expand((s) => materialesPorSeccion[s.id] ?? const <Articulo>[])
                  .map((m) => _tileArticulo(m, onAbrirArticulo)),
              // Artículos dados de alta sin conexión directamente sobre esta
              // balda: el PC todavía no ha creado su sección (implícita o
              // no), así que se muestran sueltos igual que los anteriores
              // hasta que se sincronicen.
              ...(materialesPorBaldaPendiente[balda.id] ?? const <Articulo>[])
                  .map((m) => _tileArticulo(m, onAbrirArticulo)),
              ...balda.secciones.where((s) => !s.implicita).map((seccion) {
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
                      : materiales.map((m) => _tileArticulo(m, onAbrirArticulo)).toList(),
                );
              }),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _tileArticulo(Articulo m, void Function(int materialId) onAbrirArticulo) {
    return ListTile(
      dense: true,
      leading: const Icon(Icons.inventory_2_outlined),
      title: Text(m.nombre),
      trailing: Text(
        '${formatearCantidad(m.stockActual)} ${m.unidad}'.trim(),
        style: TextStyle(
            fontWeight: FontWeight.bold, color: colorStock(m.stockActual, m.stockMinimo)),
      ),
      onTap: () => onAbrirArticulo(m.id),
    );
  }
}
