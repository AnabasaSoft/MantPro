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

/// Sedes que ve el técnico (de /api/sedes), para agrupar los almacenes en el menú.
class SedesStock {
  static const _clave = 'stock_sedes';
  static List<Map<String, dynamic>> lista = [];

  static Future<void> cargar() async {
    final prefs = await SharedPreferences.getInstance();
    try {
      lista = List<Map<String, dynamic>>.from(
          (json.decode(prefs.getString(_clave) ?? '[]') as List).map((e) => Map<String, dynamic>.from(e)));
    } catch (_) {
      lista = [];
    }
    almacenesListaNotifier.value++;
  }

  static Future<void> guardarRespuesta(String cuerpo) async {
    try {
      final datos = json.decode(cuerpo);
      if (datos is! Map || datos['status'] != 'ok') return;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_clave, json.encode(datos['sedes'] ?? []));
      await cargar();
    } catch (_) {}
  }
}

/// Botón de la barra superior (edificio) para elegir almacén, agrupados por sede.
/// Aparece con más de un almacén o más de una sede; una sede sin almacén sale
/// como «sin almacén» (no se puede elegir).
class BotonAlmacen extends StatelessWidget {
  final VoidCallback alCambiar;
  const BotonAlmacen({super.key, required this.alCambiar});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([almacenElegidoNotifier, almacenesListaNotifier]),
      builder: (context, _) {
        final elegido = almacenElegidoNotifier.value;
        final almacenes = AlmacenesCache.lista;
        final sedes = SedesStock.lista;
        if (almacenes.length < 2 && sedes.length < 2) return const SizedBox.shrink();
        final entradas = <PopupMenuEntry<int>>[];
        PopupMenuItem<int> item(Map a) => CheckedPopupMenuItem<int>(
            value: a['id'] as int, checked: elegido == a['id'], child: Text('${a['nombre']}'));
        PopupMenuItem<int> cabecera(String texto) => PopupMenuItem<int>(
            enabled: false, height: 32,
            child: Text(texto, style: const TextStyle(fontWeight: FontWeight.bold)));
        if (sedes.isEmpty) {
          entradas.addAll(almacenes.map(item));
        } else {
          for (final s in sedes) {
            entradas.add(cabecera('🏢 ${s['nombre']}'));
            final suyos = almacenes.where((a) => a['comun'] != true && a['sede_id'] == s['id']).toList();
            if (suyos.isEmpty) {
              entradas.add(PopupMenuItem<int>(enabled: false, height: 32,
                  child: Text('   ${t('sin_almacen')}', style: const TextStyle(fontStyle: FontStyle.italic))));
            } else {
              entradas.addAll(suyos.map(item));
            }
          }
          final comunes = almacenes.where((a) => a['comun'] == true).toList();
          if (comunes.isNotEmpty) {
            entradas.add(cabecera('🌐 ${t('alm_comunes')}'));
            entradas.addAll(comunes.map(item));
          }
        }
        return PopupMenuButton<int>(
          icon: const Icon(Icons.apartment),
          tooltip: '${t('lbl_almacen')}: ${AlmacenesCache.nombre(elegido)}',
          onSelected: (v) async { await AlmacenesCache.elegir(v); alCambiar(); },
          itemBuilder: (_) => entradas,
        );
      },
    );
  }
}

/// Ciclo de la revisión del almacén (lo manda el PC con la lista de almacenes,
/// así que funciona sin conexión con lo último que se sincronizó).
/// - diario: cada día laborable.
/// - semanal: [dia] de la semana (0 = lunes … 6 = domingo).
/// - mensual: [dia] del mes (en meses más cortos, el último).
class RevisionAlmacen {
  final bool activa;
  final String ciclo;
  final int dia;
  final int articulos;
  /// Última revisión del almacén con algo revisado (AAAA-MM-DD) que conocía el PC.
  final String ultima;

  const RevisionAlmacen({this.activa = true, this.ciclo = 'diario', this.dia = 0, this.articulos = 5, this.ultima = ''});

  /// La del almacén elegido. Con un PC antiguo (sin datos de revisión): diaria de 5 artículos.
  static RevisionAlmacen delElegido() => deAlmacen(almacenElegidoNotifier.value);

  static RevisionAlmacen deAlmacen(int? id) {
    final a = AlmacenesCache.lista.where((x) => x['id'] == id);
    final r = a.isEmpty ? null : a.first['revision'];
    if (r is! Map) return const RevisionAlmacen();
    final ciclo = (r['ciclo'] == 'semanal' || r['ciclo'] == 'mensual') ? r['ciclo'] as String : 'diario';
    return RevisionAlmacen(
      activa: r['activa'] != false,
      ciclo: ciclo,
      dia: (r['dia'] as num?)?.toInt() ?? 0,
      articulos: ((r['articulos'] as num?)?.toInt() ?? 5).clamp(1, 50),
      ultima: '${r['ultima'] ?? ''}',
    );
  }

  static DateTime _soloDia(DateTime d) => DateTime(d.year, d.month, d.day);

  static DateTime _diaDelMes(int anio, int mes, int dia) {
    final ultimo = DateTime(anio, mes + 1, 0).day;   // día 0 del mes siguiente = último de este
    return DateTime(anio, mes, dia < ultimo ? dia : ultimo);
  }

  /// Primer día del periodo que contiene [fecha].
  DateTime inicioPeriodo(DateTime fecha) {
    final d = _soloDia(fecha);
    if (ciclo == 'semanal') {
      return d.subtract(Duration(days: ((d.weekday - 1) - dia) % 7));
    }
    if (ciclo == 'mensual') {
      final este = _diaDelMes(d.year, d.month, dia);
      return este.isAfter(d) ? _diaDelMes(d.year, d.month - 1, dia) : este;
    }
    return d;
  }

  /// Primer día del periodo siguiente al que contiene [fecha].
  DateTime siguientePeriodo(DateTime fecha) {
    final inicio = inicioPeriodo(fecha);
    if (ciclo == 'semanal') return inicio.add(const Duration(days: 7));
    if (ciclo == 'mensual') return _diaDelMes(inicio.year, inicio.month + 1, dia);
    return inicio.add(const Duration(days: 1));
  }

  static String texto(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  /// 'AAAA-MM-DD' del inicio del periodo actual.
  String periodoActual() => texto(inicioPeriodo(DateTime.now()));
}
