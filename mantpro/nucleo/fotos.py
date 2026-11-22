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

"""Marcas de fotos dentro de la descripción de un trabajo ([FOTOS: ...])."""

import os
import re

# --- Colección de fotos de un trabajo -------------------------------------
# Además de la foto de antes ([FOTO: x]) y la de después ([FOTO_DESPUES: y]),
# un trabajo puede llevar una colección de fotos extra, guardada igual que
# las otras: como una marca en la propia descripción, [FOTOS: a.jpg, b.jpg].
# Así viaja sola con el trabajo (pendiente -> historial, revertir, editar,
# sincronizar con el móvil) sin cambiar el esquema de la base de datos.
_RE_GALERIA = re.compile(r"\[FOTOS:\s*(.*?)\]")


def fotos_galeria(texto):
    """Lista de nombres de fichero de la colección de fotos de [texto]."""
    m = _RE_GALERIA.search(texto or "")
    if not m: return []
    return [f.strip() for f in m.group(1).split(",") if f.strip()]


def con_fotos_galeria(texto, nombres):
    """Devuelve [texto] con la marca de colección sustituida por [nombres]
    (o quitada si la lista está vacía)."""
    texto = re.sub(r"\n?\[FOTOS:.*?\]", "", texto or "").rstrip()
    nombres = [n for n in nombres if n]
    if nombres:
        texto += ("\n" if texto else "") + f"[FOTOS: {', '.join(nombres)}]"
    return texto


def quitar_marcas_foto(texto):
    """Quita del texto todas las marcas de foto ([FOTO:], [FOTO_DESPUES:],
    [FOTOS:]) y la de referencia [REF:], para mostrarlo."""
    texto = re.sub(r"\[FOTO.*?:.*?\]", "", texto or "")
    return re.sub(r"\[REF:.*?\]", "", texto).strip()


# --- Fotos recibidas (móviles y MantPro Web) -------------------------------

def nombres_en(texto):
    """Todos los ficheros de las marcas de [texto]: la foto de antes, la de después y la colección."""
    texto = texto or ""
    nombres = [m.group(2).split("]")[0].strip() for m in re.finditer(r"\[(FOTO|FOTO_DESPUES):\s*(.*?)\]", texto)]
    return [n for n in nombres if n] + fotos_galeria(texto)


def nombre_seguro(nombre):
    """[nombre] con solo letras, números y «_» (y la extensión en minúsculas): no puede salirse de la carpeta
    de fotos (sin «/», «\\» ni «..») y cabe en los nombres que admite MantPro Cloud."""
    base, extension = os.path.splitext(os.path.basename(str(nombre or "")))
    base = re.sub(r"[^a-zA-Z0-9_]", "_", base)[:100] or "foto"
    return base + re.sub(r"[^a-zA-Z0-9.]", "", extension.lower())[:10]


def ruta_en(carpeta, nombre):
    """Ruta de [nombre] dentro de [carpeta], o None si el nombre no es sencillo o se saldría de ella."""
    if not nombre or nombre != nombre_seguro(nombre):
        return None
    carpeta = os.path.realpath(carpeta)
    ruta = os.path.realpath(os.path.join(carpeta, nombre))
    return ruta if os.path.dirname(ruta) == carpeta else None


def guardar_recibida(fichero, carpeta, nombre, solo_imagen=False):
    """Guarda una foto o un vídeo recibido ([fichero]: lo que tenga .save(ruta), como los de Flask) en [carpeta]
    con [nombre] saneado, y la comprueba (extensión, tamaño y que sea de verdad lo que dice; ver seguridad.py).
    Con [solo_imagen] (fotos de antes y de después) un vídeo no vale. Devuelve el nombre guardado, o None si no
    vale (y entonces no deja nada en la carpeta)."""
    from . import seguridad
    nombre = nombre_seguro(nombre)
    ruta = ruta_en(carpeta, nombre)
    if ruta is None or (solo_imagen and seguridad.es_video(nombre)):
        return None
    fichero.save(ruta)
    if not seguridad.foto_valida(ruta):
        try:
            os.remove(ruta)
        except OSError:
            pass
        return None
    return nombre


def en_uso(db):
    """Nombres de fichero de foto que usa cualquier dato (trabajos, pendientes, fotos de máquinas y de artículos del
    almacén, que comparten la carpeta aunque vivan en almacen.db). Para saber qué foto es basura y cuál hay que
    restaurar de una copia; sin filtrar nombres, para no borrar nunca una foto que se usa."""
    from . import almacen
    usadas = set()
    conn = db.conectar()
    try:
        c = conn.cursor()
        for sentencia in ("SELECT descripcion FROM tareas", "SELECT detalles FROM pendientes"):
            for (texto,) in c.execute(sentencia).fetchall():
                texto = texto or ""
                for patron in (r"\[FOTO:\s*(.*?)\]", r"\[FOTO_DESPUES:\s*(.*?)\]"):
                    m = re.search(patron, texto)
                    if m:
                        usadas.add(m.group(1).strip())
                usadas.update(fotos_galeria(texto))
        for (foto,) in c.execute("SELECT foto FROM maquinas WHERE foto IS NOT NULL").fetchall():
            if foto:
                usadas.add(foto.strip())
    finally:
        conn.close()
    for material in almacen.listar_materiales():
        if material.get("foto"):
            usadas.add(material["foto"].strip())
    return usadas
