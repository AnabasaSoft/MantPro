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

// Traducciones al español de la app móvil MantPro Stock (mantpro_stock_app).
const Map<String, String> traduccionesEs = {
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
    "lbl_zona": "Zona",
    "txt_todas_zonas": "Todas las zonas",
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

    "canal_notif_stock": "Comprobación de stock",
    "canal_notif_stock_desc": "Recordatorio diario a las 8:00 AM",
    "notif_stock_titulo": "📦 Comprobación de stock",
    "notif_stock_cuerpo": "Revisa el stock de 5 materiales del almacén.",
    "titulo_comprobar_stock": "Comprobar stock",
    "lbl_comprobar_stock_intro": "Comprueba la cantidad real de estos materiales y corrígela si hace falta.",
    "msg_sin_materiales": "No hay materiales en el almacén.",
    "motivo_comprobacion_stock": "Comprobación de stock",

    // --- Artículos, permisos y colas ---
    "lbl_articulo": "Artículo",
    "msg_borrado_articulo": "Borrado de artículo",
    "lbl_movimiento_stock": "Movimiento de stock",
    "titulo_sin_permiso": "Cambios no aplicados",
    "msg_sin_permiso_almacen": "Tu usuario ya no tiene permiso para gestionar el almacén, así que el PC ha rechazado estos cambios pendientes:",
    "btn_aceptar": "Aceptar",
    "msg_articulo_no_encontrado": "Artículo no encontrado",
    "msg_articulo_pendiente": "💾 Guardado en el móvil. Se enviará al PC cuando haya conexión.",
    "msg_movimiento_pendiente": "💾 Guardado en el móvil. Se enviará al PC cuando haya conexión.",
    "dlg_confirmar_borrado_articulo": "Eliminar artículo",
    "msg_confirmar_borrar_articulo": "¿Eliminar este artículo? Se perderá su historial de movimientos.",
    "btn_eliminar": "Eliminar",
    "msg_articulo_eliminado": "✅ Artículo eliminado",
    "msg_articulo_eliminado_pendiente": "💾 Eliminado en el móvil. Se confirmará en el PC cuando haya conexión.",
    "lbl_pendiente_sincronizar": "Pendiente de enviar al PC",

    // --- Comprobador de actualizaciones ---
    "msg_nueva_version_titulo": "🚀 Nueva versión disponible",
    "msg_nueva_version_cuerpo": "Tienes la versión {actual} instalada y en GitHub ya está la {nueva}.",
    "btn_luego": "Luego",
    "btn_descargar": "Descargar",
    "msg_sin_actualizaciones_sin_conexion": "❌ No se pudo comprobar actualizaciones (sin conexión)",
    "msg_ya_ultima_version": "✅ Ya tienes la última versión",
    "tooltip_buscar_actualizaciones": "Buscar actualizaciones",
};
