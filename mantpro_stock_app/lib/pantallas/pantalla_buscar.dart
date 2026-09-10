// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later

import 'dart:async';
import 'package:flutter/material.dart';
import '../api.dart';
import '../i18n/strings.dart';
import '../modelos.dart';
import 'pantalla_articulo.dart';

class PantallaBuscar extends StatefulWidget {
  const PantallaBuscar({super.key});
  @override
  State<PantallaBuscar> createState() => _PantallaBuscarState();
}

class _PantallaBuscarState extends State<PantallaBuscar> {
  final _controlador = TextEditingController();
  Timer? _debounce;
  bool _buscando = false;
  String? _error;
  List<Articulo> _resultados = [];
  bool _seHaBuscado = false;

  @override
  void dispose() {
    _debounce?.cancel();
    _controlador.dispose();
    super.dispose();
  }

  void _alCambiarTexto(String texto) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), () => _buscar(texto));
  }

  Future<void> _buscar(String texto) async {
    if (texto.trim().isEmpty) {
      setState(() { _resultados = []; _seHaBuscado = false; _error = null; });
      return;
    }
    setState(() { _buscando = true; _error = null; });
    try {
      final resultados = await StockApi.obtenerMateriales(q: texto.trim());
      setState(() { _resultados = resultados; _seHaBuscado = true; });
    } catch (e) {
      setState(() => _error = e.toString());
    }
    if (mounted) setState(() => _buscando = false);
  }

  Future<void> _abrirArticulo(int id) async {
    final cambiado = await Navigator.push<bool>(
        context, MaterialPageRoute(builder: (_) => PantallaArticulo(materialId: id)));
    if (cambiado == true) _buscar(_controlador.text);
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: idiomaNotifier,
      builder: (context, _, __) => _construir(context),
    );
  }

  Widget _construir(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: TextField(
            controller: _controlador,
            onChanged: _alCambiarTexto,
            decoration: InputDecoration(
              hintText: tt('ph_buscar_material', 'Buscar por nombre, código, descripción...'),
              prefixIcon: const Icon(Icons.search),
              border: const OutlineInputBorder(),
              suffixIcon: _controlador.text.isEmpty
                  ? null
                  : IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () { _controlador.clear(); _alCambiarTexto(''); },
                    ),
            ),
          ),
        ),
        if (_buscando) const LinearProgressIndicator(),
        Expanded(
          child: _error != null
              ? Center(child: Text(_error!))
              : !_seHaBuscado
                  ? Center(child: Text(tt('msg_escribe_para_buscar', 'Escribe algo para buscar')))
                  : _resultados.isEmpty
                      ? Center(child: Text(tt('msg_sin_resultados', 'Sin resultados')))
                      : ListView.builder(
                          itemCount: _resultados.length,
                          itemBuilder: (_, i) {
                            final m = _resultados[i];
                            return ListTile(
                              leading: const Icon(Icons.inventory_2_outlined),
                              title: Text(m.nombre),
                              subtitle: Text(m.ubicacion.isEmpty
                                  ? tt('lbl_sin_ubicacion', 'Sin ubicación')
                                  : m.ubicacion),
                              trailing: Text(
                                '${formatearCantidad(m.stockActual)} ${m.unidad}'.trim(),
                                style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: colorStock(m.stockActual, m.stockMinimo)),
                              ),
                              onTap: () => _abrirArticulo(m.id),
                            );
                          },
                        ),
        ),
      ],
    );
  }
}
