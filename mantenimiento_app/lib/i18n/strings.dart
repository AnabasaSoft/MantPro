// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro - Sistema de Mantenimiento Preventivo
// Copyright (C) 2026 AnabasaSoft <anabasasoft@gmail.com>
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


import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'es.dart';
import 'en.dart';
import 'eu.dart';

// ==========================================
// SISTEMA DE IDIOMAS - MantPro (Móvil)
// ==========================================
// Los textos de cada idioma viven en su propio fichero (es.dart, en.dart,
// eu.dart), cada uno con un Map<String, String> const.
//
// Cómo añadir un idioma nuevo:
//   1. Copia es.dart a <codigo>.dart y tradúcelo.
//   2. Impórtalo aquí y añádelo a _traducciones y a idiomasDisponibles.
//   3. Corre `python3 verificar_idiomas.py` (desde la raíz del proyecto) para
//      comprobar que no falta ninguna clave.
//   4. Ya aparece automáticamente en el selector de idioma.
//
// Cómo usar una clave nueva en el código:
//   - Añade la clave en es.dart (si falta en los demás, se muestra el texto
//     en español como respaldo automático).
//   - Donde antes tenías texto literal, usa t('tu_clave').
//   - Envuelve el widget en ValueListenableBuilder(valueListenable: idiomaNotifier, ...)
//     si quieres que se actualice al vuelo sin reiniciar la app.
//   - Al terminar, corre `python3 verificar_idiomas.py` para que rellene
//     automáticamente la clave que falte en el resto de idiomas.

const List<Map<String, String>> idiomasDisponibles = [
  {"codigo": "es", "nombre": "Español"},
  {"codigo": "en", "nombre": "English"},
  {"codigo": "eu", "nombre": "Euskara"},
];

const Map<String, Map<String, String>> _traducciones = {
  "es": traduccionesEs,
  "en": traduccionesEn,
  "eu": traduccionesEu,
};

/// Idioma activo en memoria. Escúchalo con ValueListenableBuilder para que
/// los widgets se repinten solos al cambiar de idioma, sin reiniciar la app.
final ValueNotifier<String> idiomaNotifier = ValueNotifier('es');

/// Carga el idioma guardado (o 'es' por defecto). Llamar una vez en main().
Future<void> cargarIdiomaGuardado() async {
  final prefs = await SharedPreferences.getInstance();
  final codigo = prefs.getString('idioma') ?? 'es';
  idiomaNotifier.value = _traducciones.containsKey(codigo) ? codigo : 'es';
}

/// Cambia el idioma activo y lo persiste.
Future<void> cambiarIdioma(String codigo) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString('idioma', codigo);
  idiomaNotifier.value = _traducciones.containsKey(codigo) ? codigo : 'es';
}

/// Devuelve el texto traducido para [clave] en el idioma activo.
/// Si falta en el idioma activo, cae a español. Si tampoco existe, devuelve la propia clave.
String t(String clave) {
  final diccionarioActual = _traducciones[idiomaNotifier.value] ?? _traducciones['es']!;
  return diccionarioActual[clave] ?? _traducciones['es']![clave] ?? clave;
}

String traducirTagsBD(String tagsBd) {
  if (idiomaNotifier.value == 'es') return tagsBd;
  final map = {
    "Urgente": t("tag_urgente"),
    "Eléctrico": t("tag_electrico"),
    "Mecánico": t("tag_mecanico"),
    "Preventivo": t("tag_preventivo")
  };
  return tagsBd.split(', ').map((tag) => map[tag] ?? tag).join(', ');
}

/// La prioridad se guarda en la BD como código fijo en español ("Baja",
/// "Media", "Alta", "Crítica", ver maquinas.py/usuarios.py). Aquí se traduce
/// ese código al idioma activo para mostrarlo.
String traducirPrioridad(String? codigo) {
  const map = {
    "Baja": "prioridad_baja",
    "Media": "prioridad_media",
    "Alta": "prioridad_alta",
    "Crítica": "prioridad_critica",
  };
  final clave = map[codigo];
  return clave != null ? t(clave) : (codigo ?? t("prioridad_media"));
}

/// El PC devuelve el estado de un aviso como un código fijo en español
/// ("FUTURO", "PENDIENTE", "OK", ver main.py), pensado para lógica interna,
/// no para mostrarlo tal cual. Aquí se traduce ese código al idioma activo.
String traducirEstadoAviso(String estadoBd) {
  const map = {"FUTURO": "estado_futuro", "PENDIENTE": "estado_pendiente", "OK": "estado_ok"};
  final clave = map[estadoBd];
  return clave != null ? t(clave) : estadoBd;
}
