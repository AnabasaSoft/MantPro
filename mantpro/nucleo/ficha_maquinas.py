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

"""La pestaña Máquinas (sin Qt): el árbol (máquinas raíz de una sede, y de cada máquina sus submáquinas, los años
de sus trabajos y los trabajos de cada año), los indicadores de fiabilidad, el gráfico de trabajos por máquina y
crear, editar y borrar máquinas. Lo usan la pestaña Máquinas del PC y MantPro Web.

En el PC los desplegables solo ofrecen lo que existe; en la web llega lo que mande el navegador: aquí se comprueba
todo (que existan la máquina superior, la zona y la sede, que el usuario vea la sede, que una máquina no cuelgue de
sí misma ni de sus submáquinas). Un nombre igual o muy parecido al de otra máquina del mismo nivel se avisa
(«nombre_parecido») salvo que se confirme. Los errores son códigos (ValueError), nunca texto."""

from .. import idiomas
from . import almacen, maquinas, sedes

MANTENER = object()        # al editar: deja la foto que tenía


# ---------------------------------------------------------------- ver

def _nodo(m):
    return {"id": m["id"], "nombre": m["nombre"], "trabajos": maquinas.contar_trabajos(m["id"]),
            "zona": m.get("zona_nombre") or "", "zona_id": m.get("zona_id"), "foto": m.get("foto") or None}


def raiz(sede=None):
    """Las máquinas raíz de [sede] (id, lista o None = todas), por nombre: [{id, nombre, trabajos (sin contar las
    submáquinas), zona, zona_id, foto}]. Las submáquinas van con su raíz."""
    return [_nodo(m) for m in maquinas.listar_maquinas() if m["padre_id"] is None and sedes.de_la_sede(m.get("sede_id"), sede)]


def hijos(maquina_id):
    """Lo que cuelga de una máquina en el árbol: {submaquinas: [nodos], anios: [(año, trabajos)]}."""
    subs = [_nodo(m) for m in maquinas.listar_maquinas() if m["padre_id"] == maquina_id]
    return {"submaquinas": subs, "anios": list(maquinas.anios_de_maquina(maquina_id))}


def trabajos_anio(maquina_id, anio):
    """Los trabajos de un año de la máquina: [{id, resumen (la primera línea), fecha (AAAA-MM-DD)}]."""
    return [{"id": t["id"], "resumen": (t["descripcion"] or "").splitlines()[0] if t["descripcion"] else "", "fecha": t["fecha"]}
            for t in maquinas.trabajos_de_maquina_anio(maquina_id, anio)]


def indicadores(maquina_id):
    """Las líneas de «Indicadores de fiabilidad» de la máquina con sus submáquinas: (título, [líneas], nota)."""
    t = idiomas.t
    ind = maquinas.indicadores_fiabilidad(maquina_id)
    lineas = [f"{t('lbl_num_averias')}: {ind['num_averias']}"]
    if ind["num_averias"] == 0 or ind["mtbf_dias"] is None:
        return t("lbl_indicadores_fiabilidad"), lineas, t("msg_sin_datos_fiabilidad")
    lineas.append(f"{t('lbl_mtbf')}: {t('fmt_dias').format(n=ind['mtbf_dias'])}")
    if ind["mttr_horas"] is not None:
        lineas.append(f"{t('lbl_mttr')}: {t('fmt_horas').format(n=ind['mttr_horas'])}")
    return t("lbl_indicadores_fiabilidad"), lineas, ""


def grafico(sede=None, anio=None, zona_id=None):
    """«Trabajos por máquina»: [(nombre, trabajos)] de las máquinas raíz de [sede] (y de [zona_id]), sumando las de
    sus submáquinas, del año [anio] o de todos (None), de más a menos."""
    raices = [m for m in maquinas.listar_maquinas() if m["padre_id"] is None and sedes.de_la_sede(m.get("sede_id"), sede)]
    if zona_id is not None:
        raices = [m for m in raices if m["zona_id"] == zona_id]

    def total(id_maquina):
        ids = maquinas.descendientes_ids(id_maquina)
        if anio is None:
            return sum(maquinas.contar_trabajos(i) for i in ids)
        return sum(maquinas.contar_trabajos_anio(i, anio) for i in ids)

    return sorted(((m["nombre"], total(m["id"])) for m in raices), key=lambda par: par[1], reverse=True)


# ---------------------------------------------------------------- comprobaciones

def visible(usuario, maquina_id):
    """La máquina [maquina_id] (dict) si es de una sede que ve [usuario]; si no (o no existe), ValueError."""
    m = maquinas.obtener_maquina(maquina_id) if maquina_id is not None else None
    if not m or not sedes.de_la_sede(m.get("sede_id"), sedes.permitidas(usuario)):
        raise ValueError("no_encontrado")
    return m


def _superior(usuario, padre_id):
    if padre_id is None:
        return None
    try:
        return visible(usuario, padre_id)["id"]
    except ValueError:
        raise ValueError("maquina_no_existe") from None


def _zona(zona_id):
    if zona_id is not None and zona_id not in {z["id"] for z in maquinas.listar_zonas()}:
        raise ValueError("zona_no_existe")
    return zona_id


def _sede(usuario, sede_id):
    if sede_id is not None and sede_id not in {s["id"] for s in sedes.visibles(usuario)}:
        raise ValueError("sede_no_permitida")
    return sede_id


def _nombre(nombre, padre_id, excluir_id, confirmar_parecido):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("nombre_obligatorio")
    if not confirmar_parecido and maquinas.nombres_parecidos(nombre, padre_id, excluir_id=excluir_id):
        raise ValueError("nombre_parecido")
    return nombre


def parecidos(nombre, padre_id=None, excluir_id=None):
    """Los nombres parecidos al mismo nivel (para enseñarlos al avisar)."""
    return maquinas.nombres_parecidos(nombre or "", padre_id, excluir_id=excluir_id)


# ---------------------------------------------------------------- escribir

def crear(usuario, nombre, padre_id=None, notas="", foto=None, zona_id=None, sede_id=None, confirmar_parecido=False):
    """Da de alta una máquina (o una submáquina, con [padre_id]) y devuelve su id. Una raíz va a [sede_id] (None: la
    principal si el usuario la ve, si no la primera suya); una submáquina, a la sede de su superior."""
    padre_id = _superior(usuario, padre_id)
    zona_id = _zona(zona_id)
    sede_id = _sede(usuario, sede_id) if padre_id is None else None
    nombre = _nombre(nombre, padre_id, None, confirmar_parecido)
    if padre_id is None and sede_id is None:
        sede_id = sedes.para_nuevo(sedes.permitidas(usuario), usuario)
    nuevo = maquinas.agregar_maquina(nombre, padre_id, notas or "", foto, zona_id, sede_id=sede_id)
    if not nuevo:
        raise ValueError("no_guardado")
    return nuevo


def editar(usuario, maquina_id, nombre, padre_id=None, notas="", foto=MANTENER, zona_id=None, sede_id=None,
           confirmar_parecido=False):
    """Guarda los cambios de una máquina. [padre_id]: la nueva superior (no puede ser ella ni una de sus
    submáquinas). [sede_id]: solo en una raíz; si cambia, se lleva sus submáquinas y sus trabajos."""
    m = visible(usuario, maquina_id)
    if padre_id is not None and padre_id in maquinas.descendientes_ids(maquina_id):
        raise ValueError("superior_no_valida")
    padre_id = _superior(usuario, padre_id)
    zona_id = _zona(zona_id)
    sede_id = _sede(usuario, sede_id) if padre_id is None else None
    cambia = (nombre or "").strip() != m["nombre"] or padre_id != m["padre_id"]
    nombre = _nombre(nombre, padre_id, maquina_id, confirmar_parecido or not cambia)
    maquinas.actualizar_maquina(maquina_id, nombre, padre_id, notas or "", m.get("foto") if foto is MANTENER else foto, zona_id)
    if padre_id is None and sede_id is not None and sede_id != sedes.efectiva(m.get("sede_id")):
        sedes.asignar_maquina(maquina_id, sede_id)
    return True


def borrar(usuario, maquina_id):
    """Borra la máquina con sus submáquinas (y sus repuestos y contadores); sus trabajos se quedan sin máquina.
    Devuelve cuántas máquinas se han borrado."""
    visible(usuario, maquina_id)
    ids = maquinas.descendientes_ids(maquina_id)
    maquinas.borrar_maquina(maquina_id)
    almacen.borrar_repuestos_de_maquinas(ids)
    return len(ids)


def nueva_zona(nombre):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("nombre_obligatorio")
    return maquinas.agregar_zona(nombre)
