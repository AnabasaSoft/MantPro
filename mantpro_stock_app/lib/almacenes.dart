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

/// Varios almacenes en MantPro Stock, 100 % sin conexión:
///
/// - /api/stock/almacenes da los almacenes que ve el técnico (los de sus sedes
///   y los comunes); se guardan en el móvil.
/// - El almacén elegido se recuerda. Cada almacén tiene su propia caché de
///   estructura, artículos y bajo mínimo (claves con sufijo), así que cambiar de
///   almacén sin conexión enseña lo último que se bajó de ese almacén.
/// - Las descargas piden `?almacen=<id>` y las altas llevan `almacen_id`.
///   Sin almacén elegido (un solo almacén, o PC antiguo) todo va como antes.
library;

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'i18n/strings.dart';

/// Almacén elegido (null = el principal / el de siempre). Las pantallas lo escuchan.
final ValueNotifier<int?> almacenElegidoNotifier = ValueNotifier(null);

/// Cambia cada vez que se carga la lista de almacenes (repinta el botón).
final ValueNotifier<int> almacenesListaNotifier = ValueNotifier(0);

class AlmacenesCache {
  static const _clave = 'stock_almacenes';
  static const _claveElegido = 'stock_almacen_elegido';

  /// [{id, nombre, comun, principal, sede}]
  static List<Map<String, dynamic>> lista = [];

  static Future<void> cargar() async {
    final prefs = await SharedPreferences.getInstance();
    try {
      lista = List<Map<String, dynamic>>.from(
          (json.decode(prefs.getString(_clave) ?? '[]') as List).map((e) => Map<String, dynamic>.from(e)));
    } catch (_) {
      lista = [];
    }
    final elegido = prefs.getInt(_claveElegido);
    if (elegido != null && lista.any((a) => a['id'] == elegido)) {
      almacenElegidoNotifier.value = elegido;
    } else {
      // Sin elegir: el primero que ve (el principal si es suyo); null si no hay lista (PC antiguo)
      almacenElegidoNotifier.value = lista.isEmpty ? null : lista.first['id'] as int;
    }
    almacenesListaNotifier.value++;
  }

  /// Guarda la respuesta de /api/stock/almacenes. true si el almacén elegido ha cambiado.
  static Future<bool> guardarRespuesta(String cuerpo) async {
    try {
      final datos = json.decode(cuerpo);
      if (datos is! Map || datos['status'] != 'ok') return false;
      final antes = almacenElegidoNotifier.value;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_clave, json.encode(datos['almacenes'] ?? []));
      await cargar();
      return antes != almacenElegidoNotifier.value;
    } catch (_) {
      return false;
    }
  }

  static Future<void> elegir(int id) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_claveElegido, id);
    almacenElegidoNotifier.value = id;
  }

  static String nombre(int? id) {
    final a = lista.where((x) => x['id'] == id);
    return a.isEmpty ? '' : '${a.first['nombre']}';
  }
}

/// Sufijo de las claves de caché del almacén elegido ('' = el de siempre).
String sufijoAlmacen() {
  final id = almacenElegidoNotifier.value;
  return id == null ? '' : '_alm$id';
}

/// Parámetros de consulta para pedir lo del almacén elegido.
Map<String, String> paramsAlmacen() {
  final id = almacenElegidoNotifier.value;
  return id == null ? {} : {'almacen': '$id'};
}

/// Botón de la barra superior para elegir almacén. Solo con más de uno.
class BotonAlmacen extends StatelessWidget {
  final VoidCallback alCambiar;
  const BotonAlmacen({super.key, required this.alCambiar});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([almacenElegidoNotifier, almacenesListaNotifier]),
      builder: (context, _) {
        final elegido = almacenElegidoNotifier.value;
        if (AlmacenesCache.lista.length < 2) return const SizedBox.shrink();
        return PopupMenuButton<int>(
          icon: const Icon(Icons.warehouse),
          tooltip: '${t('lbl_almacen')}: ${AlmacenesCache.nombre(elegido)}',
          onSelected: (v) async { await AlmacenesCache.elegir(v); alCambiar(); },
          itemBuilder: (_) => AlmacenesCache.lista.map((a) => CheckedPopupMenuItem<int>(
              value: a['id'] as int, checked: elegido == a['id'],
              child: Text(a['comun'] == true || (a['sede'] ?? '').toString().isEmpty
                  ? '${a['nombre']}' : '${a['nombre']} · ${a['sede']}'))).toList(),
        );
      },
    );
  }
}
