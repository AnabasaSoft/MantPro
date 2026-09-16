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

// Traducións ao galego da app móbil MantPro Stock (mantpro_stock_app).
const Map<String, String> traduccionesGl = {
    "app_titulo": "MantPro Stock",
    "dlg_idioma_titulo": "Idioma",
    "title_qr": "Escanear QR",
    "btn_si": "SI",
    "btn_no": "NON",
    "btn_cancelar": "Cancelar",
    "btn_guardar": "Gardar",
    "btn_editar": "Editar",
    "btn_anadir": "Engadir",

    "login_subtitulo": "Identifícate para xestionar o almacén",
    "login_usuario": "Usuario",
    "login_password": "Contrasinal",
    "login_entrar": "ENTRAR",
    "login_vacio": "Introduce usuario e contrasinal.",
    "login_error": "Usuario ou contrasinal incorrectos.",
    "login_sin_conexion": "Non se puido conectar co PC. Comproba a WiFi e que MantPro estea aberto.",
    "login_sin_pc": "Primeiro vincula o móbil co PC escaneando o QR.",
    "login_pc_no_vinculado": "Sen PC vinculado",
    "btn_vincular_pc": "Vincular PC",
    "btn_vincular_otro_pc": "Vincular outro PC",
    "btn_cerrar_sesion": "Pechar sesión",
    "msg_cerrar_sesion": "Seguro que queres pechar a sesión?",

    "tab_almacen": "Almacén",
    "tab_buscar": "Buscar",
    "tab_bajo_minimo": "Por baixo do mínimo",

    "ph_buscar_material": "Buscar por nome, código, descrición...",
    "msg_sin_resultados": "Sen resultados",
    "msg_escribe_para_buscar": "Escribe algo para buscar",
    "msg_sin_bajo_minimo": "Non hai artigos por baixo do mínimo 🎉",
    "msg_sin_estanterias": "Non hai estanterías configuradas no almacén",
    "msg_sin_articulos_seccion": "Sen artigos",
    "lbl_suelo": "Chan",
    "lbl_balda": "Estante",

    "titulo_articulo": "Artigo",
    "titulo_nuevo_articulo": "Novo artigo",
    "titulo_editar_articulo": "Editar artigo",
    "lbl_nombre": "Nome",
    "lbl_codigo": "Código",
    "lbl_descripcion": "Descrición",
    "lbl_unidad": "Unidade",
    "lbl_cantidad_actual": "Cantidade actual",
    "lbl_cantidad_minima": "Cantidade mínima",
    "lbl_cantidad_inicial": "Cantidade inicial",
    "lbl_ubicacion": "Ubicación",
    "lbl_sin_ubicacion": "Sen ubicación",
    "lbl_estanteria": "Estantería",
    "lbl_seccion": "Sección",
    "lbl_foto": "Foto",
    "lbl_sin_foto": "Sen foto",
    "btn_camara": "Cámara",
    "btn_galeria": "Galería",
    "btn_quitar_foto": "Quitar foto",
    "msg_nombre_obligatorio": "O nome é obrigatorio.",
    "msg_selecciona_seccion": "Selecciona unha sección do almacén.",
    "msg_articulo_guardado": "✅ Artigo gardado",
    "msg_error_guardar": "❌ Non se puido gardar o artigo",

    "lbl_movimientos": "Últimos movementos",
    "msg_sin_movimientos": "Sen movementos rexistrados",
    "btn_entrada": "Entrada",
    "btn_salida": "Saída",
    "dlg_registrar_movimiento": "Rexistrar movemento",
    "lbl_cantidad": "Cantidade",
    "lbl_motivo": "Motivo (opcional)",
    "msg_cantidad_invalida": "Introduce unha cantidade maior que 0.",
    "msg_stock_insuficiente": "Non hai stock suficiente para esta saída.",
    "msg_movimiento_registrado": "✅ Movemento rexistrado",
    "movimiento_entrada": "Entrada",
    "movimiento_salida": "Saída",

    "msg_sin_conexion_pc": "❌ Sen conexión co PC",
    "msg_actualizando": "Actualizando...",

    "canal_notif_stock": "Comprobación de stock",
    "canal_notif_stock_desc": "Recordatorio diario ás 8:00 AM",
    "notif_stock_titulo": "📦 Comprobación de stock",
    "notif_stock_cuerpo": "Revisa o stock de 5 materiais do almacén.",
    "titulo_comprobar_stock": "Comprobar stock",
    "lbl_comprobar_stock_intro": "Comproba a cantidade real destes materiais e corríxea se fai falta.",
    "msg_sin_materiales": "Non hai materiais no almacén.",
    "motivo_comprobacion_stock": "Comprobación de stock",

    // --- Artículos, permisos y colas ---
    "lbl_articulo": "Artigo",
    "msg_borrado_articulo": "Borrado de artigo",
    "lbl_movimiento_stock": "Movemento de stock",
    "titulo_sin_permiso": "Cambios non aplicados",
    "msg_sin_permiso_almacen": "O teu usuario xa non ten permiso para xestionar o almacén, así que o PC rexeitou estes cambios pendentes:",
    "btn_aceptar": "Aceptar",
    "msg_articulo_no_encontrado": "Artigo non atopado",
    "msg_articulo_pendiente": "💾 Gardado no móbil. Enviarase ao PC cando haxa conexión.",
    "msg_movimiento_pendiente": "💾 Gardado no móbil. Enviarase ao PC cando haxa conexión.",
    "dlg_confirmar_borrado_articulo": "Eliminar artigo",
    "msg_confirmar_borrar_articulo": "Eliminar este artigo? Perderase o seu historial de movementos.",
    "btn_eliminar": "Eliminar",
    "msg_articulo_eliminado": "✅ Artigo eliminado",
    "msg_articulo_eliminado_pendiente": "💾 Eliminado no móbil. Confirmarase no PC cando haxa conexión.",
    "lbl_pendiente_sincronizar": "Pendente de enviar ao PC",

    // --- Comprobador de actualizaciones ---
    "msg_nueva_version_titulo": "🚀 Nova versión dispoñible",
    "msg_nueva_version_cuerpo": "Tes a versión {actual} instalada e en GitHub xa está a {nueva}.",
    "btn_luego": "Máis tarde",
    "btn_descargar": "Descargar",
};
