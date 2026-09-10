// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later

import 'package:flutter/material.dart';
import '../api.dart';
import '../i18n/strings.dart';
import '../modelos.dart';
import 'pantalla_articulo.dart';

class PantallaBajoMinimo extends StatefulWidget {
  const PantallaBajoMinimo({super.key});
  @override
  State<PantallaBajoMinimo> createState() => _PantallaBajoMinimoState();
}

class _PantallaBajoMinimoState extends State<PantallaBajoMinimo> {
  bool _cargando = true;
  String? _error;
  List<Articulo> _materiales = [];

  @override
  void initState() {
    super.initState();
    datosSincronizadosNotifier.addListener(_recargarSilencioso);
    _cargar();
  }

  @override
  void dispose() {
    datosSincronizadosNotifier.removeListener(_recargarSilencioso);
    super.dispose();
  }

  Future<void> _cargar() async {
    setState(() { _cargando = true; _error = null; });
    try {
      final materiales = await StockApi.materialesBajoMinimo();
      setState(() => _materiales = materiales);
    } catch (e) {
      setState(() => _error = e.toString());
    }
    if (mounted) setState(() => _cargando = false);
  }

  /// Igual que [_cargar] pero sin el spinner a pantalla completa: se usa
  /// para los refrescos automáticos en segundo plano.
  Future<void> _recargarSilencioso() async {
    try {
      final materiales = await StockApi.materialesBajoMinimo();
      if (mounted) setState(() => _materiales = materiales);
    } catch (_) {}
  }

  Future<void> _abrirArticulo(int id) async {
    final cambiado = await Navigator.push<bool>(
        context, MaterialPageRoute(builder: (_) => PantallaArticulo(materialId: id)));
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
    return RefreshIndicator(
      onRefresh: _cargar,
      child: _error != null
          ? ListView(children: [Padding(padding: const EdgeInsets.all(24), child: Text(_error!))])
          : _materiales.isEmpty
              ? ListView(children: [
                  Padding(
                    padding: const EdgeInsets.all(24),
                    child: Center(child: Text(tt('msg_sin_bajo_minimo', 'No hay artículos por debajo del mínimo 🎉'))),
                  )
                ])
              : ListView.builder(
                  itemCount: _materiales.length,
                  itemBuilder: (_, i) {
                    final m = _materiales[i];
                    return ListTile(
                      leading: const Icon(Icons.warning_amber, color: Colors.redAccent),
                      title: Text(m.nombre),
                      subtitle: Text(m.ubicacion.isEmpty
                          ? tt('lbl_sin_ubicacion', 'Sin ubicación')
                          : m.ubicacion),
                      trailing: Text(
                        '${formatearCantidad(m.stockActual)} / ${formatearCantidad(m.stockMinimo)} ${m.unidad}'.trim(),
                        style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: colorStock(m.stockActual, m.stockMinimo)),
                      ),
                      onTap: () => _abrirArticulo(m.id),
                    );
                  },
                ),
    );
  }
}
