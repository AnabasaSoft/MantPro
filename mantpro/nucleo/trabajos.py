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
"""Registrar un trabajo hecho (pestaña «📝 Registrar» del PC y la misma pantalla de MantPro Web).

El trabajo va directo al historial con su fecha, título y detalles, máquina, etiquetas (con «Avería» y sus horas
de parada), fotos de antes y de después y colección, repuestos (que salen del stock) y tiempo trabajado. Aquí se
comprueba también lo que el PC ya filtra con sus desplegables y la web tiene que comprobar en el servidor: la
máquina, los artículos y la sede tienen que ser de los que ve el usuario."""

from . import consumos, fotos as _fotos, mano_obra, maquinas, sedes, usuarios
from .pendientes import MAX_MINUTOS, MAX_PERSONAS, _fecha, _repuestos

MAX_HORAS_PARO = 999            # como el campo de horas de parada del PC


def descripcion(titulo, detalles="", foto=None, foto_despues=None, fotos=()):
    """«título\\ndetalles\\n[FOTO: a]\\n[FOTO_DESPUES: b]\\n[FOTOS: c, d]», como la guarda el PC."""
    texto = titulo + (f"\n{detalles}" if detalles else "") + (f"\n[FOTO: {foto}]" if foto else "") \
        + (f"\n[FOTO_DESPUES: {foto_despues}]" if foto_despues else "")
    return _fotos.con_fotos_galeria(texto, list(fotos or ()))


def registrar(db, usuario, fecha, titulo, detalles="", tags="", maquina_id=None, horas_paro=None, sede=None,
              repuestos=(), minutos=None, personas=1, foto=None, foto_despues=None, fotos=()):
    """Guarda un trabajo hecho y devuelve su id. [horas_paro]: solo si es una avería (None = sin parada).
    [sede]: la elegida en el selector (id, lista o None), como al crear un pendiente; con máquina, el trabajo va a
    la sede de la máquina. ValueError con un código si algo no vale."""
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValueError("titulo_obligatorio")
    fecha = _fecha(fecha)
    permitidas = sedes.permitidas(usuario)
    if maquina_id is not None:
        if maquina_id not in {m for m, _, _ in maquinas.para_elegir(permitidas)}:
            raise ValueError("maquina_no_existe")
    if horas_paro is not None and (isinstance(horas_paro, bool) or not isinstance(horas_paro, (int, float))
                                   or not 0 <= horas_paro <= MAX_HORAS_PARO):
        raise ValueError("horas_paro_no_validas")
    if minutos is not None and (isinstance(minutos, bool) or not isinstance(minutos, int) or not 0 <= minutos <= MAX_MINUTOS):
        raise ValueError("tiempo_no_valido")
    if isinstance(personas, bool) or not isinstance(personas, int) or not 1 <= personas <= MAX_PERSONAS:
        raise ValueError("personas_no_validas")
    if isinstance(sede, int) and permitidas is not None and sede not in permitidas:
        raise ValueError("sede_no_permitida")
    items = _repuestos(repuestos, usuario)
    usuario_id = usuario["id"] if usuario else usuarios.id_actual()
    usuario_nombre = usuario["nombre"] if usuario else usuarios.nombre_actual()
    tarea_id = db.agregar_tarea(fecha, descripcion(titulo, (detalles or "").strip(), foto, foto_despues, fotos),
                                tags or "", usuario_id, usuario_nombre, maquina_id=maquina_id, horas_paro=horas_paro,
                                sede_id=sedes.para_nuevo(sede if sede is not None else permitidas, usuario))
    if not tarea_id:
        raise ValueError("no_guardado")
    # Repuestos usados: salen del stock y quedan con el trabajo y su precio
    consumos.registrar_consumo(tarea_id, items, usuario_id, usuario_nombre, titulo, fecha)
    mano_obra.fijar_tiempo(tarea_id, minutos, personas, registrar=False)
    return tarea_id


def titulos_usados(db, limite=500):
    """Los títulos de los trabajos ya registrados, para autocompletar (como el PC)."""
    return db.obtener_todas_las_descripciones()[:limite]
