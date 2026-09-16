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

// MantPro Stock - Gestión de almacén

// Traduccions al català de l'app mòbil MantPro Stock (mantpro_stock_app).
const Map<String, String> traduccionesCa = {
    "app_titulo": "MantPro Stock",
    "dlg_idioma_titulo": "Idioma",
    "title_qr": "Escanejar QR",
    "btn_si": "SÍ",
    "btn_no": "NO",
    "btn_cancelar": "Cancel·lar",
    "btn_guardar": "Desar",
    "btn_editar": "Editar",
    "btn_anadir": "Afegir",

    "login_subtitulo": "Identifica't per gestionar el magatzem",
    "login_usuario": "Usuari",
    "login_password": "Contrasenya",
    "login_entrar": "ENTRAR",
    "login_vacio": "Introdueix usuari i contrasenya.",
    "login_error": "Usuari o contrasenya incorrectes.",
    "login_sin_conexion": "No s'ha pogut connectar amb el PC. Comprova la WiFi i que MantPro estigui obert.",
    "login_sin_pc": "Primer vincula el mòbil amb el PC escanejant el QR.",
    "login_pc_no_vinculado": "Sense PC vinculat",
    "btn_vincular_pc": "Vincular PC",
    "btn_vincular_otro_pc": "Vincular un altre PC",
    "btn_cerrar_sesion": "Tancar sessió",
    "msg_cerrar_sesion": "Segur que vols tancar la sessió?",

    "tab_almacen": "Magatzem",
    "tab_buscar": "Cercar",
    "tab_bajo_minimo": "Per sota del mínim",

    "ph_buscar_material": "Cercar per nom, codi, descripció...",
    "msg_sin_resultados": "Sense resultats",
    "msg_escribe_para_buscar": "Escriu alguna cosa per cercar",
    "msg_sin_bajo_minimo": "No hi ha articles per sota del mínim 🎉",
    "msg_sin_estanterias": "No hi ha prestatgeries configurades al magatzem",
    "msg_sin_articulos_seccion": "Sense articles",
    "lbl_suelo": "Terra",
    "lbl_balda": "Prestatge",

    "titulo_articulo": "Article",
    "titulo_nuevo_articulo": "Nou article",
    "titulo_editar_articulo": "Editar article",
    "lbl_nombre": "Nom",
    "lbl_codigo": "Codi",
    "lbl_descripcion": "Descripció",
    "lbl_unidad": "Unitat",
    "lbl_cantidad_actual": "Quantitat actual",
    "lbl_cantidad_minima": "Quantitat mínima",
    "lbl_cantidad_inicial": "Quantitat inicial",
    "lbl_ubicacion": "Ubicació",
    "lbl_sin_ubicacion": "Sense ubicació",
    "lbl_estanteria": "Prestatgeria",
    "lbl_seccion": "Secció",
    "lbl_foto": "Foto",
    "lbl_sin_foto": "Sense foto",
    "btn_camara": "Càmera",
    "btn_galeria": "Galeria",
    "btn_quitar_foto": "Treure foto",
    "msg_nombre_obligatorio": "El nom és obligatori.",
    "msg_selecciona_seccion": "Selecciona una secció del magatzem.",
    "msg_articulo_guardado": "✅ Article desat",
    "msg_error_guardar": "❌ No s'ha pogut desar l'article",

    "lbl_movimientos": "Últims moviments",
    "msg_sin_movimientos": "Sense moviments registrats",
    "btn_entrada": "Entrada",
    "btn_salida": "Sortida",
    "dlg_registrar_movimiento": "Registrar moviment",
    "lbl_cantidad": "Quantitat",
    "lbl_motivo": "Motiu (opcional)",
    "msg_cantidad_invalida": "Introdueix una quantitat més gran que 0.",
    "msg_stock_insuficiente": "No hi ha estoc suficient per a aquesta sortida.",
    "msg_movimiento_registrado": "✅ Moviment registrat",
    "movimiento_entrada": "Entrada",
    "movimiento_salida": "Sortida",

    "msg_sin_conexion_pc": "❌ Sense connexió amb el PC",
    "msg_actualizando": "Actualitzant...",

    "canal_notif_stock": "Comprovació d'estoc",
    "canal_notif_stock_desc": "Recordatori diari a les 8:00 AM",
    "notif_stock_titulo": "📦 Comprovació d'estoc",
    "notif_stock_cuerpo": "Revisa l'estoc de 5 materials del magatzem.",
    "titulo_comprobar_stock": "Comprovar estoc",
    "lbl_comprobar_stock_intro": "Comprova la quantitat real d'aquests materials i corregeix-la si cal.",
    "msg_sin_materiales": "No hi ha materials al magatzem.",
    "motivo_comprobacion_stock": "Comprovació d'estoc",

    // --- Artículos, permisos y colas ---
    "lbl_articulo": "Article",
    "msg_borrado_articulo": "Esborrat d'article",
    "lbl_movimiento_stock": "Moviment d'estoc",
    "titulo_sin_permiso": "Canvis no aplicats",
    "msg_sin_permiso_almacen": "El teu usuari ja no té permís per gestionar el magatzem, per això el PC ha rebutjat aquests canvis pendents:",
    "btn_aceptar": "D'acord",
    "msg_articulo_no_encontrado": "Article no trobat",
    "msg_articulo_pendiente": "💾 Desat al mòbil. S'enviarà al PC quan hi hagi connexió.",
    "msg_movimiento_pendiente": "💾 Desat al mòbil. S'enviarà al PC quan hi hagi connexió.",
    "dlg_confirmar_borrado_articulo": "Eliminar article",
    "msg_confirmar_borrar_articulo": "Eliminar aquest article? Es perdrà el seu historial de moviments.",
    "btn_eliminar": "Eliminar",
    "msg_articulo_eliminado": "✅ Article eliminat",
    "msg_articulo_eliminado_pendiente": "💾 Eliminat al mòbil. Es confirmarà al PC quan hi hagi connexió.",
    "lbl_pendiente_sincronizar": "Pendent d'enviar al PC",

    // --- Comprobador de actualizaciones ---
    "msg_nueva_version_titulo": "🚀 Nova versió disponible",
    "msg_nueva_version_cuerpo": "Tens la versió {actual} instal·lada i a GitHub ja hi ha la {nueva}.",
    "btn_luego": "Més tard",
    "btn_descargar": "Descarregar",
};
