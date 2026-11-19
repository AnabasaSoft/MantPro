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

/// Varias sedes en la app, 100 % sin conexión:
///
/// - El PC (o la nube) solo manda lo de las sedes que ve el técnico, y cada
///   pendiente, aviso, máquina y trabajo lleva su `sede_id`.
/// - La lista de sus sedes llega de /api/sedes y se guarda en el móvil.
/// - El selector (solo con más de una sede) filtra en el móvil lo que ya está
///   guardado; «Todas mis sedes» = sin filtro. Lo que se crea lleva la sede
///   elegida (`sede_id`), también si se envía días después.
library;

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'i18n/strings.dart';

/// Sede elegida (null = todas mis sedes). Las pestañas lo escuchan para refiltrar.
final ValueNotifier<int?> sedeElegidaNotifier = ValueNotifier(null);

/// Cambia cada vez que se carga la lista de sedes (el botón se repinta aunque
/// la sede elegida siga siendo la misma, p. ej. «todas»).
final ValueNotifier<int> sedesListaNotifier = ValueNotifier(0);

class SedesCache {
  static const _clave = 'sedes_cache';
  static const _claveElegida = 'sede_elegida';
  /// uuid de la sede elegida: el id es de cada base (PC o nube); al bajar la lista de la otra
  /// ruta, la elegida se vuelve a buscar por su uuid para que siga siendo la misma sede.
  static const _claveElegidaUuid = 'sede_elegida_uuid';

  /// Sedes del técnico: [{id, nombre, tipo, principal}].
  static List<Map<String, dynamic>> lista = [];

  /// Carga lo guardado en el móvil (al arrancar, sin conexión).
  static Future<void> cargar() async {
    final prefs = await SharedPreferences.getInstance();
    try {
      lista = List<Map<String, dynamic>>.from(
          (json.decode(prefs.getString(_clave) ?? '[]') as List).map((e) => Map<String, dynamic>.from(e)));
    } catch (_) {
      lista = [];
    }
    var elegida = prefs.getInt(_claveElegida);
    final uuidElegida = prefs.getString(_claveElegidaUuid);
    final porUuid = uuidElegida == null ? null : lista.where((s) => s['uuid'] == uuidElegida).firstOrNull;
    if (porUuid != null && porUuid['id'] != elegida) {
      elegida = porUuid['id'] as int?;
      if (elegida != null) await prefs.setInt(_claveElegida, elegida);
    }
    sedeElegidaNotifier.value = (elegida != null && lista.any((s) => s['id'] == elegida)) ? elegida : null;
    sedesListaNotifier.value++;
  }

  /// Guarda la respuesta de /api/sedes. Si la sede elegida ya no es del
  /// técnico, vuelve a «Todas mis sedes».
  static Future<void> guardarRespuesta(String cuerpo) async {
    try {
      final datos = json.decode(cuerpo);
      if (datos is! Map || datos['status'] != 'ok') return;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_clave, json.encode(datos['sedes'] ?? []));
      await cargar();
    } catch (_) {}
  }

  static Future<void> elegir(int? sedeId) async {
    final prefs = await SharedPreferences.getInstance();
    if (sedeId == null) {
      await prefs.remove(_claveElegida);
      await prefs.remove(_claveElegidaUuid);
    } else {
      await prefs.setInt(_claveElegida, sedeId);
      final u = uuid(sedeId);
      if (u != null) { await prefs.setString(_claveElegidaUuid, u); } else { await prefs.remove(_claveElegidaUuid); }
    }
    sedeElegidaNotifier.value = sedeId;
  }

  /// uuid de la sede [sedeId] (null sin MantPro Cloud o si no está en la lista).
  static String? uuid(int? sedeId) {
    if (sedeId == null) return null;
    return lista.where((x) => x['id'] == sedeId).firstOrNull?['uuid'] as String?;
  }

  static String nombre(int? sedeId) {
    if (sedeId == null) return t('sede_todas_mias');
    final s = lista.where((x) => x['id'] == sedeId);
    return s.isEmpty ? '' : '${s.first['nombre']}';
  }
}

/// ¿Se ve ahora un registro con [sedeId]? Sin sede elegida, todo; un registro
/// sin sede conocida (creado sin conexión con una versión antigua) también.
bool enSedeElegida(dynamic sedeId) {
  final elegida = sedeElegidaNotifier.value;
  return elegida == null || sedeId == null || sedeId == elegida;
}

/// Botón de la barra superior para elegir sede. Solo aparece con más de una.
class BotonSede extends StatelessWidget {
  const BotonSede({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([sedeElegidaNotifier, sedesListaNotifier]),
      builder: (context, _) {
        final elegida = sedeElegidaNotifier.value;
        if (SedesCache.lista.length < 2) return const SizedBox.shrink();
        return PopupMenuButton<int>(
          icon: Icon(Icons.apartment, color: elegida == null ? null : Colors.orangeAccent),
          tooltip: '${t('lbl_sede')}: ${SedesCache.nombre(elegida)}',
          onSelected: (v) => SedesCache.elegir(v == 0 ? null : v),
          itemBuilder: (_) => [
            CheckedPopupMenuItem<int>(value: 0, checked: elegida == null,
                child: Text(t('sede_todas_mias'))),
            ...SedesCache.lista.map((s) => CheckedPopupMenuItem<int>(
                value: s['id'] as int, checked: elegida == s['id'], child: Text('${s['nombre']}'))),
          ],
        );
      },
    );
  }
}
