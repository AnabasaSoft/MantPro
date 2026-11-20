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
"""Historial y Buscador: los filtros y lo que se enseña de cada trabajo, para las pestañas del PC y MantPro Web.

Las filas son las de GestorBaseDatos.obtener_todas_cronologico / buscar_tareas_avanzado:
(id, fecha, descripcion, tags, usuario_nombre, maquina_id)."""

import os
import re

from . import checklists, consumos, mano_obra, usuarios

TODO = "TODO"            # árbol de fechas: todos los trabajos
TODOS = "TODOS"          # técnico y tipo: sin filtrar
TIPOS = ("TODOS", "TRABAJOS", "PREVENTIVOS")
MARCA_PREVENTIVO = "Aviso Recurrente"          # etiqueta de los trabajos que vienen de completar un aviso
# Filtros por etiqueta del Buscador: (lo que se busca en las etiquetas, sin la primera letra para no depender de
# mayúsculas, y sin tilde) y su clave de texto
ETIQUETAS_BUSCADOR = (("urgente", "urgente", "tag_urgente"), ("léctrico", "lectrico", "tag_electrico"),
                      ("ecánico", "ecanico", "tag_mecanico"), ("preventivo", "preventivo", "tag_preventivo"))


def es_preventivo(tags):
    return MARCA_PREVENTIVO in (tags or "")


def coincide(fila, fecha=TODO, tecnico=TODOS, tipo=TODOS):
    """True si el trabajo pasa los filtros del Historial: [fecha] «2026» o «2026-07» (TODO = todos), [tecnico]
    (nombre de quien lo hizo; TODOS = todos) y [tipo] (TRABAJOS: trabajos y averías; PREVENTIVOS: avisos)."""
    if fecha not in (None, TODO) and not (fila[1] or "").startswith(fecha):
        return False
    autor = fila[4] if len(fila) > 4 else ""
    if tecnico not in (None, TODOS) and (autor or "") != tecnico:
        return False
    if tipo == "PREVENTIVOS" and not es_preventivo(fila[3]):
        return False
    if tipo == "TRABAJOS" and es_preventivo(fila[3]):
        return False
    return True


def coincide_etiquetas(tags_visibles, filtros):
    """Buscador: True si las etiquetas (ya traducidas, como se ven) tienen todas las de [filtros] (los primeros
    valores de ETIQUETAS_BUSCADOR)."""
    texto = (tags_visibles or "").lower()
    sin_tilde = dict((con, sin) for con, sin, _ in ETIQUETAS_BUSCADOR)
    return all(f in texto or sin_tilde.get(f, f) in texto for f in filtros)


def arbol_fechas(filas):
    """[(año, [meses «MM»])] con trabajos, del más reciente al más antiguo."""
    arbol = {}
    for fila in filas:
        fecha = fila[1] or ""
        if len(fecha) >= 7:
            arbol.setdefault(fecha[:4], set()).add(fecha[5:7])
    return [(anio, sorted(arbol[anio], reverse=True)) for anio in sorted(arbol, reverse=True)]


def tecnicos(db):
    """Los nombres de quienes aparecen en el historial, por orden alfabético (el filtro «Realizado por»)."""
    con = db.conectar()
    try:
        return sorted({r[0] for r in con.execute("SELECT DISTINCT COALESCE(usuario_nombre,'') FROM tareas") if r[0]})
    finally:
        con.close()


def clase(tags):
    """El color de la fila según sus etiquetas: «averia», «preventivo», «electrico», «mecanico» o None."""
    t = (tags or "").lower()
    if any(x in t for x in ("urgente", "avería", "rotura", "fallo", "paro")):
        return "averia"
    if any(x in t for x in ("preventivo", "revisión", "ok", "limpieza")):
        return "preventivo"
    if "eléctrico" in t or "cuadro" in t:
        return "electrico"
    if "mecánico" in t:
        return "mecanico"
    return None


def texto_visible(descripcion):
    """La descripción sin las marcas de fotos ni la referencia del móvil."""
    texto = re.sub(r"\[FOTO.*?:.*?\]", "", descripcion or "")
    return re.sub(r"\[REF:.*?\]", "", texto).strip()


def hay_foto(descripcion, carpeta_fotos):
    """True si la foto de antes (o, si no está, la de después) existe en [carpeta_fotos]."""
    for marca in (r"\[FOTO:\s*(.*?)\]", r"\[FOTO_DESPUES:\s*(.*?)\]"):
        m = re.search(marca, descripcion or "")
        if m:
            nombre = m.group(1).split("]")[0].strip()
            if nombre and carpeta_fotos and os.path.exists(os.path.join(carpeta_fotos, nombre)):
                return True
    return False


def extras(ids, usuario=None):
    """{id: {"lista", "tiempo", "materiales", "coste"}} de esos trabajos: la lista de comprobación, el tiempo y los
    repuestos. El coste (del material y de la mano de obra) solo para administradores: si [usuario] no lo es, va
    a None."""
    admin = usuarios.es_admin(usuario)
    listas = checklists.resultados_de(ids)
    usados = consumos.materiales_de_trabajos(ids)
    tiempos = mano_obra.tiempos_de(ids)
    resultado = {}
    for i in ids:
        mats = usados.get(i) or []
        coste = consumos.coste(mats) if mats and admin else None
        tiempo = tiempos.get(i)
        if tiempo and not admin:
            tiempo = dict(tiempo, importe=None, coste_hora=None)
        resultado[i] = {"lista": listas.get(i), "tiempo": tiempo, "materiales": mats, "coste": coste}
    return resultado


def etiquetas_visibles(tags, traducir):
    """Las etiquetas como se enseñan: las rápidas traducidas con [traducir](clave) y las demás tal cual."""
    from .pendientes import ETIQUETAS_REGISTRAR
    claves = dict(ETIQUETAS_REGISTRAR)
    return ", ".join(traducir(claves[x.strip()]) if x.strip() in claves else x.strip()
                     for x in (tags or "").split(",") if x.strip())


def trabajo(db, usuario, tarea_id):
    """El trabajo [tarea_id] para verlo entero, si es de una sede que ve [usuario]; si no (o no existe), None.
    Dict con id, fecha, descripcion, texto (sin marcas), tags, usuario_id, autor, maquina_id, maquina (nombre),
    horas_paro, foto, foto_despues, coleccion y los extras (lista, tiempo, materiales, coste: ver extras)."""
    from . import fotos as _fotos, maquinas, sedes
    fila = db.obtener_tarea_por_id(tarea_id)
    if not fila or not sedes.de_la_sede(sedes.sede_de("tareas", tarea_id), sedes.permitidas(usuario)):
        return None
    tid, fecha, desc, tags, usuario_id, autor, maquina_id, horas_paro = fila
    marcas = {}
    for marca in ("FOTO", "FOTO_DESPUES"):
        m = re.search(rf"\[{marca}:\s*(.*?)\]", desc or "")
        marcas[marca] = m.group(1).split("]")[0].strip() if m else None
    maquina = maquinas.obtener_maquina(maquina_id) if maquina_id else None
    return dict(extras([tid], usuario)[tid], id=tid, fecha=fecha, descripcion=desc or "", texto=texto_visible(desc),
                tags=tags or "", usuario_id=usuario_id, autor=autor or usuarios.ETIQUETA_HISTORICO,
                maquina_id=maquina_id, maquina=(maquina or {}).get("nombre") if maquina else None,
                horas_paro=horas_paro, foto=marcas["FOTO"], foto_despues=marcas["FOTO_DESPUES"],
                coleccion=_fotos.fotos_galeria(desc))
