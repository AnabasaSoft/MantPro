# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# MantPro - Sistema de Mantenimiento Preventivo
# Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft) <anabasasoft@gmail.com>
# https://github.com/AnabasaSoft/MantPro
#
# Este programa es software libre: puedes redistribuirlo y/o modificarlo bajo
# los términos de la Licencia Pública General Affero de GNU publicada por la
# Free Software Foundation, ya sea la versión 3 de la Licencia o (a tu
# elección) cualquier versión posterior.
#
# Este programa se distribuye con la esperanza de que sea útil, pero SIN
# NINGUNA GARANTÍA; ni siquiera la garantía implícita de COMERCIABILIDAD o
# IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulta la Licencia Pública
# General Affero de GNU para más detalles.
#
# Deberías haber recibido una copia de la Licencia Pública General Affero de
# GNU junto con este programa. Si no, consulta <https://www.gnu.org/licenses/>.

"""«📋 Registro de cambios» (sin Qt): filtros, textos de cada registro (categoría, acción, campos traducidos) y la
exportación a Excel o CSV. Lo usan el diálogo del PC y MantPro Web. Solo de administradores (lo comprueba quien
lo muestra)."""

import csv
import io
from datetime import date, timedelta

from .. import idiomas
from . import usuarios

POR_PAGINA = 300
# Periodos del filtro (días hacia atrás; None = todo) y el que sale de entrada
PERIODOS = (7, 30, 365, None)
PERIODO_INICIAL = 30


def _tt(clave, defecto):
    valor = idiomas.t(clave)
    return defecto if valor == clave else valor


def nombres_categoria():
    return {
        "trabajos": _tt("aud_cat_trabajos", "📋 Trabajos (historial)"),
        "pendientes": _tt("aud_cat_pendientes", "🔨 Pendientes"),
        "avisos": _tt("aud_cat_avisos", "🔁 Avisos"),
        "checklists": _tt("aud_cat_checklists", "☑️ Listas de comprobación"),
        "maquinas": _tt("aud_cat_maquinas", "🏭 Máquinas y repuestos"),
        "almacen": _tt("aud_cat_almacen", "📦 Almacén"),
        "usuarios": _tt("aud_cat_usuarios", "👥 Usuarios"),
        "seguridad": _tt("aud_cat_seguridad", "🛡️ Seguridad"),
        "copias": _tt("aud_cat_copias", "💾 Copias e importación"),
        "configuracion": _tt("aud_cat_configuracion", "⚙️ Configuración"),
    }


def nombres_accion():
    return {
        "crear": _tt("aud_acc_crear", "➕ Creado"),
        "editar": _tt("aud_acc_editar", "✏️ Modificado"),
        "borrar": _tt("aud_acc_borrar", "🗑️ Borrado"),
        "revertir": _tt("aud_acc_revertir", "↩️ Revertido a pendiente"),
        "completar": _tt("aud_acc_completar", "✅ Completado"),
        "descompletar": _tt("aud_acc_descompletar", "↩️ Desmarcado"),
        "activar": _tt("aud_acc_activar", "✔️ Reactivado"),
        "desactivar": _tt("aud_acc_desactivar", "🚫 Desactivado"),
        "contrasena": _tt("aud_acc_contrasena", "🔑 Contraseña"),
        "configurar": _tt("aud_acc_configurar", "⚙️ Configurado"),
        "revocar": _tt("aud_acc_revocar", "🚫 Sesión revocada"),
        "bloquear": _tt("aud_acc_bloquear", "⛔ Bloqueo por intentos"),
        "restaurar": _tt("aud_acc_restaurar", "♻️ Copia restaurada"),
        "importar": _tt("aud_acc_importar", "📥 Importación"),
    }


# Acciones que se pintan en rojo
ACCIONES_ROJAS = ("borrar", "bloquear", "revocar", "desactivar")

# Nombres de campo que se guardan (en español) en el registro, con su clave de
# traducción: se traducen al mostrarlos.
_CAMPOS = {
    "Fecha": "aud_f_fecha", "Descripción": "aud_f_descripcion", "Etiquetas": "aud_f_etiquetas",
    "Realizado por": "aud_f_realizado_por", "Máquina": "aud_f_maquina", "Horas de paro": "aud_f_horas_paro",
    "Título": "aud_f_titulo", "Detalles": "aud_f_detalles", "Asignado a": "aud_f_asignado",
    "Prioridad": "aud_f_prioridad", "Especialidad": "aud_f_especialidad", "Fecha de inicio": "aud_f_inicio",
    "Frecuencia": "aud_f_frecuencia", "Días de margen": "aud_f_margen", "Nombre": "aud_f_nombre",
    "Roles": "aud_f_roles", "Activo": "aud_f_activo", "Especialidades": "aud_f_especialidades",
    "Máquina superior": "aud_f_superior", "Zona": "aud_f_zona", "Notas": "aud_f_notas", "Foto": "aud_f_foto",
    "Código": "aud_f_codigo", "Unidad": "aud_f_unidad", "Stock mínimo": "aud_f_minimo",
    "Ubicación": "aud_f_ubicacion", "Puntos": "aud_f_puntos", "Lista de comprobación": "aud_f_checklist",
    "Última vez completado": "aud_f_ultima", "Puerto de sincronización": "aud_f_puerto",
    "País (festivos)": "aud_f_pais", "Región (festivos)": "aud_f_region",
    "Región superior (festivos)": "aud_f_region_superior", "Idioma": "aud_f_idioma",
    "Precio unitario": "aud_f_precio", "Moneda": "aud_f_moneda",
    "Días sin conectar": "aud_f_dias_sin_conectar",
    "Móvil adjudicado a": "aud_f_movil_adjudicado",
    "Tiempo trabajado": "aud_f_tiempo", "Coste de la hora de trabajo": "aud_f_coste_hora",
    "Contador": "aud_f_contador", "Cada": "aud_f_cada", "Avisar antes": "aud_f_avisar_antes",
    "Primera vez a": "aud_f_primera", "Lectura": "aud_f_lectura", "Lecturas": "aud_f_lecturas",
    "Copias automáticas": "aud_f_copias_automaticas", "Copia periódica": "aud_f_copia_periodica",
    "Cada (horas)": "aud_f_cada_horas", "Copia tras recibir datos de un móvil": "aud_f_copia_tras_movil",
    "Carpeta externa de las copias": "aud_f_carpeta_externa", "Copias recientes que se guardan": "aud_f_copias_recientes",
    "Días con una copia diaria": "aud_f_dias_copia_diaria",
    "Contacto": "aud_f_contacto", "Teléfono": "aud_f_telefono", "Correo": "aud_f_correo",
    "Proveedor habitual": "aud_f_proveedor_habitual",
    "Stock objetivo": "aud_f_objetivo", "Múltiplo de pedido": "aud_f_multiplo",
    "Objetivo por defecto (× mínimo)": "aud_f_factor_objetivo",
}


def campo(texto):
    """Nombre de campo traducido (o tal cual si es un texto propio, p. ej. «Repuesto SEL-01»)."""
    clave = _CAMPOS.get(texto)
    return _tt(clave, texto) if clave else texto


def resumen(r):
    """Texto corto de la columna «Cambios»."""
    if r.get("cambios"):
        n = len(r["cambios"])
        campos = ", ".join(campo(c["campo"]) for c in r["cambios"][:3]) + ("…" if n > 3 else "")
        return _tt("aud_n_cambios", "{n} cambios: {campos}").format(n=n, campos=campos) if n > 1 else campos
    return (r.get("detalle") or "").split("\n")[0]


def textos_periodo():
    """[(días o None, texto)] en el orden del desplegable del PC."""
    nombres = {7: _tt("aud_periodo_7", "Últimos 7 días"), 30: _tt("aud_periodo_30", "Últimos 30 días"),
               365: _tt("aud_periodo_365", "Último año"), None: _tt("aud_periodo_todo", "Todo")}
    return [(d, nombres[d]) for d in PERIODOS]


def filtros(categoria=None, accion=None, usuario_id=None, dias=PERIODO_INICIAL, texto=None):
    """Los argumentos de usuarios.obtener_auditoria para lo elegido en los filtros. Lo que no es válido (una
    categoría, acción o periodo que no existen) cuenta como «Todas»."""
    if categoria not in nombres_categoria():
        categoria = None
    if accion not in nombres_accion():
        accion = None
    if dias not in PERIODOS:
        dias = None
    return dict(categoria=categoria, accion=accion, usuario_id=usuario_id, texto=(texto or "").strip() or None,
                desde=(date.today() - timedelta(days=dias)).isoformat() if dias else None)


def pagina(filtro, desplazamiento=0, por_pagina=POR_PAGINA):
    """(registros, hay_mas): una página del registro con [filtro] (el dict de filtros())."""
    registros = usuarios.obtener_auditoria(limite=por_pagina + 1, desplazamiento=desplazamiento, **filtro)
    return registros[:por_pagina], len(registros) > por_pagina


def fila(r):
    """Lo que se pinta de un registro: las 7 columnas de la tabla y la cabecera de su detalle."""
    cats, accs = nombres_categoria(), nombres_accion()
    accion = accs.get(r["accion"], r["accion"])
    categoria = cats.get(r["categoria"], r["categoria"])
    fecha = (r.get("fecha") or "").replace("T", " ")
    origen = r.get("origen") or "💻 PC"
    return {"id": r.get("id"), "fecha": fecha, "usuario": r.get("usuario_nombre") or "—", "origen": origen,
            "categoria": categoria, "accion": accion, "rojo": r["accion"] in ACCIONES_ROJAS,
            "objeto": campo(r.get("objeto") or "") or (f"#{r['tarea_id']}" if r.get("tarea_id") else ""),
            "objeto_crudo": r.get("objeto") or "", "resumen": resumen(r), "detalle": r.get("detalle") or "",
            "cambios": [{"campo": campo(c.get("campo", "")), "antes": c.get("antes", ""),
                         "despues": c.get("despues", "")} for c in (r.get("cambios") or [])]}


# ----------------------------------------------------------- exportar

def cabecera_exportar():
    return [_tt("lbl_fecha_hora", "Fecha y hora"), _tt("aud_usuario", "Usuario"), _tt("aud_origen", "Desde"),
            _tt("aud_categoria", "Categoría"), _tt("lbl_accion", "Acción"), _tt("aud_objeto", "Afecta a"),
            _tt("lbl_detalle", "Detalle"), _tt("aud_campo", "Campo"), _tt("aud_antes", "Antes"),
            _tt("aud_despues", "Después")]


def filas_exportar(filtro):
    """Una fila por cambio (o una por registro si no tiene cambios), con todos los registros de [filtro]."""
    cats, accs = nombres_categoria(), nombres_accion()
    for r in usuarios.obtener_auditoria(limite=100000, **filtro):
        base = [(r.get("fecha") or "").replace("T", " "), r.get("usuario_nombre") or "", r.get("origen") or "PC",
                cats.get(r["categoria"], r["categoria"]), accs.get(r["accion"], r["accion"]),
                r.get("objeto") or "", r.get("detalle") or ""]
        if r.get("cambios"):
            for c in r["cambios"]:
                yield base + [campo(c.get("campo", "")), c.get("antes", ""), c.get("despues", "")]
        else:
            yield base + ["", "", ""]


def nombre_fichero(formato):
    return f"{_tt('aud_fichero', 'Registro_de_cambios')}_{date.today().strftime('%Y%m%d')}.{formato}"


def exportar(destino, formato, filtro):
    """Escribe el registro con [filtro] en [destino] (ruta o fichero binario abierto) como «xlsx» o «csv».
    Devuelve cuántas filas ha escrito."""
    cab = cabecera_exportar()
    filas = list(filas_exportar(filtro))
    if formato == "csv":
        texto = io.StringIO(newline="")
        w = csv.writer(texto, delimiter=";")
        w.writerow(cab)
        w.writerows(filas)
        datos = texto.getvalue().encode("utf-8-sig")
        if isinstance(destino, str):
            with open(destino, "wb") as fh:
                fh.write(datos)
        else:
            destino.write(datos)
        return len(filas)
    import xlsxwriter
    libro = xlsxwriter.Workbook(destino, {"in_memory": True})
    hoja = libro.add_worksheet(_tt("aud_hoja", "Registro de cambios")[:31])
    negrita = libro.add_format({"bold": True, "bg_color": "#2c3e50", "font_color": "white"})
    ajuste = libro.add_format({"text_wrap": True, "valign": "top"})
    for col, texto in enumerate(cab):
        hoja.write(0, col, texto, negrita)
    for i, fila_ in enumerate(filas, start=1):
        for col, valor in enumerate(fila_):
            hoja.write_string(i, col, str(valor), ajuste)
    for col, ancho in enumerate((18, 18, 18, 22, 20, 35, 40, 22, 30, 30)):
        hoja.set_column(col, col, ancho)
    hoja.freeze_panes(1, 0)
    hoja.autofilter(0, 0, max(len(filas), 1), len(cab) - 1)
    libro.close()
    return len(filas)
