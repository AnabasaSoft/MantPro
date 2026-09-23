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

// Traducciones al euskera de la app móvil MantPro Stock (mantpro_stock_app).
const Map<String, String> traduccionesEu = {
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
    "lbl_zona": "Eremua",
    "txt_todas_zonas": "Eremu guztiak",
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

    "canal_notif_stock": "Stock egiaztapena",
    "canal_notif_stock_desc": "Eguneroko oroigarria 8:00etan",
    "notif_stock_titulo": "📦 Stock egiaztapena",
    "notif_stock_cuerpo": "Egiaztatu biltegiko 5 materialen stocka.",
    "titulo_comprobar_stock": "Stocka egiaztatu",
    "lbl_comprobar_stock_intro": "Egiaztatu material hauen kopuru erreala eta zuzendu behar bada.",
    "msg_sin_materiales": "Ez dago materialik biltegian.",
    "motivo_comprobacion_stock": "Stock egiaztapena",

    // --- Artículos, permisos y colas ---
    "lbl_articulo": "Artikulua",
    "msg_borrado_articulo": "Artikulua ezabatzea",
    "lbl_movimiento_stock": "Stock mugimendua",
    "titulo_sin_permiso": "Aldaketak ez dira aplikatu",
    "msg_sin_permiso_almacen": "Zure erabiltzaileak ez du jada biltegia kudeatzeko baimenik, beraz PCak zain zeuden aldaketa hauek baztertu ditu:",
    "btn_aceptar": "Ados",
    "msg_articulo_no_encontrado": "Artikulua ez da aurkitu",
    "msg_articulo_pendiente": "💾 Mugikorrean gordeta. PCra bidaliko da konexioa dagoenean.",
    "msg_movimiento_pendiente": "💾 Mugikorrean gordeta. PCra bidaliko da konexioa dagoenean.",
    "dlg_confirmar_borrado_articulo": "Artikulua ezabatu",
    "msg_confirmar_borrar_articulo": "Artikulu hau ezabatu? Bere mugimenduen historia galduko da.",
    "btn_eliminar": "Ezabatu",
    "msg_articulo_eliminado": "✅ Artikulua ezabatuta",
    "msg_articulo_eliminado_pendiente": "💾 Mugikorrean ezabatuta. PCan berretsiko da konexioa dagoenean.",
    "lbl_pendiente_sincronizar": "PCra bidaltzeko zain",

    // --- Comprobador de actualizaciones ---
    "msg_nueva_version_titulo": "🚀 Bertsio berria eskuragarri",
    "msg_nueva_version_cuerpo": "{actual} bertsioa instalatuta duzu eta GitHub-en jada {nueva} dago.",
    "btn_luego": "Geroago",
    "btn_descargar": "Deskargatu",
    "msg_sin_actualizaciones_sin_conexion": "❌ Ezin izan da eguneraketarik egiaztatu (konexiorik gabe)",
    "msg_ya_ultima_version": "✅ Dagoeneko azken bertsioa duzu",
    "tooltip_buscar_actualizaciones": "Eguneraketak bilatu",
};
