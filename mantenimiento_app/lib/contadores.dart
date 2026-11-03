// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro - Sistema de Mantenimiento Preventivo
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

/// Contadores de las máquinas (horas de uso, ciclos, km) y preventivos por
/// contador, 100 % sin conexión:
///
/// - Los contadores llegan con las máquinas (/api/maquinas, campo
///   «contadores» con la última lectura) y se guardan en el móvil.
/// - Las lecturas apuntadas en la ficha de la máquina van a la cola
///   «cola_lecturas» (cada una con su uid, para que el PC no la duplique si
///   se reenvía) y se envían a /api/lectura cuando hay conexión.
/// - La lectura apuntada al completar un preventivo viaja con el completado
///   (campos «lectura», «lectura_uid», «lectura_fecha»), no por esa cola: así
///   el PC la liga al preventivo y cuenta desde ella el siguiente ciclo.
/// - El estado de un preventivo por contador se recalcula en el móvil con la
///   lectura más reciente que conozca (la del PC o una propia sin enviar).
library;

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'i18n/strings.dart';

const claveColaLecturas = 'cola_lecturas';

/// Número escrito por el usuario («1530», «1530,5», «1.530»).
double? leerNumero(String texto) {
  var s = texto.trim().replaceAll(' ', '');
  if (s.isEmpty) return null;
  if (s.contains(',')) {
    s = s.replaceAll('.', '').replaceAll(',', '.');
  } else if (RegExp(r'^\d{1,3}(\.\d{3})+$').hasMatch(s)) {
    s = s.replaceAll('.', '');
  }
  final v = double.tryParse(s);
  return (v == null || v < 0) ? null : v;
}

/// «1530», «1530,5» (sin decimales si es entero).
String cifraLectura(num? v) {
  if (v == null) return '—';
  final d = v.toDouble();
  if ((d - d.roundToDouble()).abs() < 1e-9) return d.round().toString();
  return d.toStringAsFixed(2).replaceAll(RegExp(r'0+$'), '').replaceAll(RegExp(r'\.$'), '').replaceAll('.', ',');
}

String conUnidad(num? v, String? unidad) =>
    (unidad == null || unidad.isEmpty) ? cifraLectura(v) : '${cifraLectura(v)} $unidad';

String _ahoraIso() => DateTime.now().toIso8601String().substring(0, 19);

String nuevoUidLectura() => 'm${DateTime.now().microsecondsSinceEpoch}';

// ------------------------------------------------------------------ cola

Future<List<Map<String, dynamic>>> colaLecturas() async {
  final prefs = await SharedPreferences.getInstance();
  try {
    return List<Map<String, dynamic>>.from(
        (json.decode(prefs.getString(claveColaLecturas) ?? '[]') as List).map((e) => Map<String, dynamic>.from(e)));
  } catch (_) {
    return [];
  }
}

Future<void> _guardarCola(List<Map<String, dynamic>> cola) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString(claveColaLecturas, json.encode(cola));
}

/// Apunta una lectura en la cola local (se ve al instante en el móvil).
Future<void> apuntarLectura(int contadorId, double valor) async {
  final cola = await colaLecturas();
  cola.add({'uid': nuevoUidLectura(), 'contador_id': contadorId, 'valor': valor, 'fecha': _ahoraIso()});
  await _guardarCola(cola);
}

/// Quita de la cola una lectura aún no enviada (si se apuntó mal).
Future<void> quitarLecturaPendiente(String uid) async {
  final cola = await colaLecturas();
  cola.removeWhere((l) => l['uid'] == uid);
  await _guardarCola(cola);
}

/// Envía la cola al PC; [enviar] hace el POST (/api/lectura) y devuelve el
/// código HTTP (o null si no hay conexión). Lo aceptado (200) se retira; un
/// 400 (lectura rechazada) también, para no atascar la cola.
Future<int> enviarColaLecturas(Future<int?> Function(Map<String, String> campos) enviar) async {
  final cola = await colaLecturas();
  if (cola.isEmpty) return 0;
  final enviadas = <String>{};
  for (final l in cola) {
    final codigo = await enviar({
      'contador_id': '${l['contador_id']}', 'valor': '${l['valor']}', 'fecha': '${l['fecha']}', 'uid': '${l['uid']}'});
    if (codigo == 200 || codigo == 400) enviadas.add('${l['uid']}');
    if (codigo == null) break;   // sin conexión: lo demás, luego
  }
  if (enviadas.isNotEmpty) {
    final actual = await colaLecturas();   // por si se apuntó otra mientras tanto
    actual.removeWhere((l) => enviadas.contains('${l['uid']}'));
    await _guardarCola(actual);
  }
  return enviadas.length;
}

/// Lectura más reciente que conoce el móvil de cada contador sin enviar: las
/// de la cola y las apuntadas al completar preventivos aún en su cola
/// («avisos_cola_completados»). {contador_id: {valor, fecha, uid}}
Future<Map<int, Map<String, dynamic>>> lecturasLocales() async {
  final prefs = await SharedPreferences.getInstance();
  final resultado = <int, Map<String, dynamic>>{};
  void considerar(int? id, dynamic valor, String? fecha, String? uid) {
    // Guardado por la app en formato de máquina («1530.5»)
    final v = valor is num ? valor.toDouble() : double.tryParse('${valor ?? ''}');
    if (id == null || v == null || fecha == null) return;
    final previa = resultado[id];
    if (previa == null || fecha.compareTo(previa['fecha'] as String) >= 0) {
      resultado[id] = {'valor': v, 'fecha': fecha, 'uid': uid};
    }
  }
  for (final l in await colaLecturas()) {
    considerar(l['contador_id'] is int ? l['contador_id'] : int.tryParse('${l['contador_id']}'), l['valor'], l['fecha'], l['uid']);
  }
  try {
    for (final c in json.decode(prefs.getString('avisos_cola_completados') ?? '[]') as List) {
      if (c['lectura'] != null && c['lectura_contador'] != null) {
        considerar(int.tryParse('${c['lectura_contador']}'), c['lectura'], c['lectura_fecha'], c['lectura_uid']);
      }
    }
  } catch (_) {}
  return resultado;
}

/// Lectura actual de un contador: la más reciente entre la del PC y la local.
/// {valor, fecha, local: bool}
Map<String, dynamic>? lecturaActual(Map<String, dynamic> contador, Map<int, Map<String, dynamic>> locales) {
  final local = locales[contador['contador_id'] ?? contador['id']];
  final valorPc = (contador['actual'] as num?)?.toDouble();
  final fechaPc = contador['fecha_actual'] as String?;
  if (local != null && (fechaPc == null || (local['fecha'] as String).compareTo(fechaPc) >= 0)) {
    return {'valor': local['valor'], 'fecha': local['fecha'], 'local': true};
  }
  if (valorPc == null) return null;
  return {'valor': valorPc, 'fecha': fechaPc, 'local': false};
}

// --------------------------------------------------------- estado preventivo

const _gravedad = {'OK': -1, 'FUTURO': 0, 'PENDIENTE': 1, 'ATRASADO': 2};

String peorEstado(String a, String b) => (_gravedad[a] ?? 0) >= (_gravedad[b] ?? 0) ? a : b;

/// Estado del preventivo según el contador: FUTURO / PENDIENTE (dentro de la
/// antelación) / ATRASADO (pasado).
String estadoPorContador(Map<String, dynamic> c, double? actual) {
  final proximo = (c['proximo'] as num?)?.toDouble();
  final antelacion = (c['antelacion'] as num?)?.toDouble() ?? 0;
  if (actual == null || proximo == null) return 'FUTURO';
  if (actual > proximo) return 'ATRASADO';
  if (actual >= proximo - antelacion) return 'PENDIENTE';
  return 'FUTURO';
}

/// «1500 h (ahora 1440 h)».
String textoProximoContador(Map<String, dynamic> c, double? actual) {
  final u = c['unidad'] as String?;
  final ahora = actual == null ? t('lbl_sin_lecturas') : conUnidad(actual, u);
  return '${conUnidad(c['proximo'] as num?, u)} (${t('lbl_ahora')} $ahora)';
}

String textoCadaContador(Map<String, dynamic> c) => '${t('lbl_cada_corto')} ${conUnidad(c['cada'] as num?, c['unidad'] as String?)}';

// ------------------------------------------------------------------ widgets

/// Campo «Lectura del contador» para el diálogo de completar un preventivo.
class CampoLecturaContador extends StatelessWidget {
  final TextEditingController controlador;
  final Map<String, dynamic> contador;
  final double? actual;
  const CampoLecturaContador({super.key, required this.controlador, required this.contador, this.actual});

  @override
  Widget build(BuildContext context) {
    final u = contador['unidad'] as String? ?? '';
    return TextField(
      controller: controlador,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: '📟 ${contador['contador']} (${t('lbl_opcional')})',
        helperText: actual != null ? '${t('lbl_ultima')}: ${conUnidad(actual, u)}' : null,
        suffixText: u.isEmpty ? null : u,
        isDense: true,
      ),
    );
  }
}

/// Diálogo para apuntar una lectura. Devuelve el valor o null si se cancela.
/// Si es menor que la última, pide confirmar (contador cambiado o a cero).
Future<double?> pedirLecturaContador(BuildContext context, Map<String, dynamic> contador, double? actual) async {
  final ctrl = TextEditingController();
  final u = contador['unidad'] as String? ?? '';
  String? error;
  final valor = await showDialog<double>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, setSt) => AlertDialog(
    title: Text('📟 ${contador['nombre']}'),
    content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (actual != null) Text('${t('lbl_ultima')}: ${conUnidad(actual, u)}'),
      TextField(controller: ctrl, autofocus: true, keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(labelText: t('lbl_lectura_actual'), suffixText: u.isEmpty ? null : u, errorText: error)),
    ]),
    actions: [
      TextButton(onPressed: () => Navigator.pop(ctx), child: Text(t('btn_cancelar'))),
      ElevatedButton(onPressed: () async {
        final v = leerNumero(ctrl.text);
        if (v == null) { setSt(() => error = t('msg_lectura_no_valida')); return; }
        if (actual != null && v < actual) {
          final seguir = await showDialog<bool>(context: ctx, builder: (c2) => AlertDialog(
            content: Text(t('msg_lectura_menor').replaceAll('{nueva}', conUnidad(v, u)).replaceAll('{anterior}', conUnidad(actual, u))),
            actions: [
              TextButton(onPressed: () => Navigator.pop(c2, false), child: Text(t('btn_no'))),
              ElevatedButton(onPressed: () => Navigator.pop(c2, true), child: Text(t('btn_si'))),
            ]));
          if (seguir != true) return;
        }
        if (ctx.mounted) Navigator.pop(ctx, v);
      }, child: Text(t('btn_guardar'))),
    ],
  )));
  return valor;
}
