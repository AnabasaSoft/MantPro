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

// Traducciones al inglés de la app móvil MantPro Stock (mantpro_stock_app).
const Map<String, String> traduccionesEn = {
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

    "canal_notif_stock": "Stock check",
    "canal_notif_stock_desc": "Daily reminder at 8:00 AM",
    "notif_stock_titulo": "📦 Stock check",
    "notif_stock_cuerpo": "Check the stock of 5 warehouse materials.",
    "titulo_comprobar_stock": "Check stock",
    "lbl_comprobar_stock_intro": "Check the actual quantity of these materials and correct it if needed.",
    "msg_sin_materiales": "There are no materials in the warehouse.",
    "motivo_comprobacion_stock": "Stock check",

    // --- Artículos, permisos y colas ---
    "lbl_articulo": "Item",
    "msg_borrado_articulo": "Item deletion",
    "lbl_movimiento_stock": "Stock movement",
    "titulo_sin_permiso": "Changes not applied",
    "msg_sin_permiso_almacen": "Your user no longer has permission to manage the warehouse, so the PC rejected these pending changes:",
    "btn_aceptar": "OK",
    "msg_articulo_no_encontrado": "Item not found",
    "msg_articulo_pendiente": "💾 Saved on the phone. It will be sent to the PC when there is a connection.",
    "msg_movimiento_pendiente": "💾 Saved on the phone. It will be sent to the PC when there is a connection.",
    "dlg_confirmar_borrado_articulo": "Delete item",
    "msg_confirmar_borrar_articulo": "Delete this item? Its movement history will be lost.",
    "btn_eliminar": "Delete",
    "msg_articulo_eliminado": "✅ Item deleted",
    "msg_articulo_eliminado_pendiente": "💾 Deleted on the phone. It will be confirmed on the PC when there is a connection.",
    "lbl_pendiente_sincronizar": "Pending upload to the PC",

    // --- Comprobador de actualizaciones ---
    "msg_nueva_version_titulo": "🚀 New version available",
    "msg_nueva_version_cuerpo": "You have version {actual} installed and {nueva} is already on GitHub.",
    "btn_luego": "Later",
    "btn_descargar": "Download",
};
