// -*- coding: utf-8 -*-
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// MantPro Stock - Gestión de almacén
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

// ==========================================
// SISTEMA DE IDIOMAS - MantPro Stock
// ==========================================
const List<Map<String, String>> idiomasDisponibles = [
  {"codigo": "es", "nombre": "Español"},
  {"codigo": "en", "nombre": "English"},
  {"codigo": "eu", "nombre": "Euskara"},
];

const Map<String, Map<String, String>> _traducciones = {
  "es": {
    "app_titulo": "MantPro Stock",
    "dlg_idioma_titulo": "Idioma",
    "title_qr": "Escanear QR",
    "btn_si": "SÍ",
    "btn_no": "NO",
    "btn_cancelar": "Cancelar",
    "btn_guardar": "Guardar",
    "btn_editar": "Editar",
    "btn_anadir": "Añadir",

    "login_subtitulo": "Identifícate para gestionar el almacén",
    "login_usuario": "Usuario",
    "login_password": "Contraseña",
    "login_entrar": "ENTRAR",
    "login_vacio": "Introduce usuario y contraseña.",
    "login_error": "Usuario o contraseña incorrectos.",
    "login_sin_conexion": "No se pudo conectar con el PC. Comprueba la WiFi y que MantPro esté abierto.",
    "login_sin_pc": "Primero vincula el móvil con el PC escaneando el QR.",
    "login_pc_no_vinculado": "Sin PC vinculado",
    "btn_vincular_pc": "Vincular PC",
    "btn_vincular_otro_pc": "Vincular otro PC",
    "btn_cerrar_sesion": "Cerrar sesión",
    "msg_cerrar_sesion": "¿Seguro que quieres cerrar la sesión?",

    "tab_almacen": "Almacén",
    "tab_buscar": "Buscar",
    "tab_bajo_minimo": "Bajo mínimo",

    "ph_buscar_material": "Buscar por nombre, código, descripción...",
    "msg_sin_resultados": "Sin resultados",
    "msg_escribe_para_buscar": "Escribe algo para buscar",
    "msg_sin_bajo_minimo": "No hay artículos por debajo del mínimo 🎉",
    "msg_sin_estanterias": "No hay estanterías configuradas en el almacén",
    "msg_sin_articulos_seccion": "Sin artículos",
    "lbl_suelo": "Suelo",
    "lbl_balda": "Balda",

    "titulo_articulo": "Artículo",
    "titulo_nuevo_articulo": "Nuevo artículo",
    "titulo_editar_articulo": "Editar artículo",
    "lbl_nombre": "Nombre",
    "lbl_codigo": "Código",
    "lbl_descripcion": "Descripción",
    "lbl_unidad": "Unidad",
    "lbl_cantidad_actual": "Cantidad actual",
    "lbl_cantidad_minima": "Cantidad mínima",
    "lbl_cantidad_inicial": "Cantidad inicial",
    "lbl_ubicacion": "Ubicación",
    "lbl_sin_ubicacion": "Sin ubicación",
    "lbl_estanteria": "Estantería",
    "lbl_seccion": "Sección",
    "lbl_foto": "Foto",
    "lbl_sin_foto": "Sin foto",
    "btn_camara": "Cámara",
    "btn_galeria": "Galería",
    "btn_quitar_foto": "Quitar foto",
    "msg_nombre_obligatorio": "El nombre es obligatorio.",
    "msg_selecciona_seccion": "Selecciona una sección del almacén.",
    "msg_articulo_guardado": "✅ Artículo guardado",
    "msg_error_guardar": "❌ No se pudo guardar el artículo",

    "lbl_movimientos": "Últimos movimientos",
    "msg_sin_movimientos": "Sin movimientos registrados",
    "btn_entrada": "Entrada",
    "btn_salida": "Salida",
    "dlg_registrar_movimiento": "Registrar movimiento",
    "lbl_cantidad": "Cantidad",
    "lbl_motivo": "Motivo (opcional)",
    "msg_cantidad_invalida": "Introduce una cantidad mayor que 0.",
    "msg_stock_insuficiente": "No hay stock suficiente para esta salida.",
    "msg_movimiento_registrado": "✅ Movimiento registrado",
    "movimiento_entrada": "Entrada",
    "movimiento_salida": "Salida",

    "msg_sin_conexion_pc": "❌ Sin conexión con el PC",
    "msg_actualizando": "Actualizando...",
  },
  "en": {
    "app_titulo": "MantPro Stock",
    "dlg_idioma_titulo": "Language",
    "title_qr": "Scan QR",
    "btn_si": "YES",
    "btn_no": "NO",
    "btn_cancelar": "Cancel",
    "btn_guardar": "Save",
    "btn_editar": "Edit",
    "btn_anadir": "Add",

    "login_subtitulo": "Sign in to manage the warehouse",
    "login_usuario": "User",
    "login_password": "Password",
    "login_entrar": "SIGN IN",
    "login_vacio": "Enter your user and password.",
    "login_error": "Wrong user or password.",
    "login_sin_conexion": "Could not reach the PC. Check the WiFi and that MantPro is running.",
    "login_sin_pc": "Link the phone to the PC first by scanning the QR code.",
    "login_pc_no_vinculado": "No PC linked",
    "btn_vincular_pc": "Link PC",
    "btn_vincular_otro_pc": "Link another PC",
    "btn_cerrar_sesion": "Sign out",
    "msg_cerrar_sesion": "Are you sure you want to sign out?",

    "tab_almacen": "Warehouse",
    "tab_buscar": "Search",
    "tab_bajo_minimo": "Low stock",

    "ph_buscar_material": "Search by name, code, description...",
    "msg_sin_resultados": "No results",
    "msg_escribe_para_buscar": "Type something to search",
    "msg_sin_bajo_minimo": "No items below their minimum 🎉",
    "msg_sin_estanterias": "No shelving units configured in the warehouse",
    "msg_sin_articulos_seccion": "No items",
    "lbl_suelo": "Floor",
    "lbl_balda": "Shelf",

    "titulo_articulo": "Item",
    "titulo_nuevo_articulo": "New item",
    "titulo_editar_articulo": "Edit item",
    "lbl_nombre": "Name",
    "lbl_codigo": "Code",
    "lbl_descripcion": "Description",
    "lbl_unidad": "Unit",
    "lbl_cantidad_actual": "Current quantity",
    "lbl_cantidad_minima": "Minimum quantity",
    "lbl_cantidad_inicial": "Initial quantity",
    "lbl_ubicacion": "Location",
    "lbl_sin_ubicacion": "No location",
    "lbl_estanteria": "Shelving unit",
    "lbl_seccion": "Section",
    "lbl_foto": "Photo",
    "lbl_sin_foto": "No photo",
    "btn_camara": "Camera",
    "btn_galeria": "Gallery",
    "btn_quitar_foto": "Remove photo",
    "msg_nombre_obligatorio": "Name is required.",
    "msg_selecciona_seccion": "Select a section of the warehouse.",
    "msg_articulo_guardado": "✅ Item saved",
    "msg_error_guardar": "❌ Could not save the item",

    "lbl_movimientos": "Latest movements",
    "msg_sin_movimientos": "No movements recorded",
    "btn_entrada": "In",
    "btn_salida": "Out",
    "dlg_registrar_movimiento": "Record movement",
    "lbl_cantidad": "Quantity",
    "lbl_motivo": "Reason (optional)",
    "msg_cantidad_invalida": "Enter a quantity greater than 0.",
    "msg_stock_insuficiente": "Not enough stock for this outgoing movement.",
    "msg_movimiento_registrado": "✅ Movement recorded",
    "movimiento_entrada": "In",
    "movimiento_salida": "Out",

    "msg_sin_conexion_pc": "❌ No connection to the PC",
    "msg_actualizando": "Updating...",
  },
  "eu": {
    "app_titulo": "MantPro Stock",
    "dlg_idioma_titulo": "Hizkuntza",
    "title_qr": "Eskaneatu QRa",
    "btn_si": "BAI",
    "btn_no": "EZ",
    "btn_cancelar": "Utzi",
    "btn_guardar": "Gorde",
    "btn_editar": "Editatu",
    "btn_anadir": "Gehitu",

    "login_subtitulo": "Hasi saioa biltegia kudeatzeko",
    "login_usuario": "Erabiltzailea",
    "login_password": "Pasahitza",
    "login_entrar": "SARTU",
    "login_vacio": "Sartu erabiltzailea eta pasahitza.",
    "login_error": "Erabiltzailea edo pasahitza okerra.",
    "login_sin_conexion": "Ezin izan da PCarekin konektatu. Egiaztatu WiFia eta MantPro irekita dagoela.",
    "login_sin_pc": "Lehenik lotu mugikorra PCarekin QR kodea eskaneatuz.",
    "login_pc_no_vinculado": "PCrik lotu gabe",
    "btn_vincular_pc": "Estekatu PCa",
    "btn_vincular_otro_pc": "Lotu beste PC bat",
    "btn_cerrar_sesion": "Amaitu saioa",
    "msg_cerrar_sesion": "Ziur saioa amaitu nahi duzula?",

    "tab_almacen": "Biltegia",
    "tab_buscar": "Bilatu",
    "tab_bajo_minimo": "Gutxienekotik behera",

    "ph_buscar_material": "Bilatu izenez, kodez, deskribapenez...",
    "msg_sin_resultados": "Emaitzarik ez",
    "msg_escribe_para_buscar": "Idatzi zerbait bilatzeko",
    "msg_sin_bajo_minimo": "Ez dago gutxienekotik beherako artikulurik 🎉",
    "msg_sin_estanterias": "Biltegian ez dago apalategirik konfiguratuta",
    "msg_sin_articulos_seccion": "Artikulurik ez",
    "lbl_suelo": "Lurra",
    "lbl_balda": "Apala",

    "titulo_articulo": "Artikulua",
    "titulo_nuevo_articulo": "Artikulu berria",
    "titulo_editar_articulo": "Editatu artikulua",
    "lbl_nombre": "Izena",
    "lbl_codigo": "Kodea",
    "lbl_descripcion": "Deskribapena",
    "lbl_unidad": "Unitatea",
    "lbl_cantidad_actual": "Uneko kopurua",
    "lbl_cantidad_minima": "Gutxieneko kopurua",
    "lbl_cantidad_inicial": "Hasierako kopurua",
    "lbl_ubicacion": "Kokapena",
    "lbl_sin_ubicacion": "Kokapenik gabe",
    "lbl_estanteria": "Apalategia",
    "lbl_seccion": "Atala",
    "lbl_foto": "Argazkia",
    "lbl_sin_foto": "Argazkirik gabe",
    "btn_camara": "Kamera",
    "btn_galeria": "Galeria",
    "btn_quitar_foto": "Kendu argazkia",
    "msg_nombre_obligatorio": "Izena beharrezkoa da.",
    "msg_selecciona_seccion": "Hautatu biltegiko atal bat.",
    "msg_articulo_guardado": "✅ Artikulua gordeta",
    "msg_error_guardar": "❌ Ezin izan da artikulua gorde",

    "lbl_movimientos": "Azken mugimenduak",
    "msg_sin_movimientos": "Ez dago mugimendurik erregistratuta",
    "btn_entrada": "Sarrera",
    "btn_salida": "Irteera",
    "dlg_registrar_movimiento": "Erregistratu mugimendua",
    "lbl_cantidad": "Kopurua",
    "lbl_motivo": "Arrazoia (aukerakoa)",
    "msg_cantidad_invalida": "Sartu 0 baino handiagoa den kopurua.",
    "msg_stock_insuficiente": "Ez dago stock nahikorik irteera honetarako.",
    "msg_movimiento_registrado": "✅ Mugimendua erregistratuta",
    "movimiento_entrada": "Sarrera",
    "movimiento_salida": "Irteera",

    "msg_sin_conexion_pc": "❌ Ez dago konexiorik PCarekin",
    "msg_actualizando": "Eguneratzen...",
  },
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
