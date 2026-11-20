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

"""Avisos recurrentes: qué avisos ve cada usuario y cuáles tocan hoy (sin Qt).

Lo usan la pestaña Avisos y el Dashboard del PC y MantPro Web, para que todos cuenten igual.
Cada aviso es una fila de GestorBaseDatos.obtener_avisos:
(id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, asignado_a, asignado_nombre, especialidad_id)."""

from datetime import date, timedelta

from .. import idiomas
from . import frecuencias, usuarios


def visibles(avisos, usuario):
    """Igual que en el móvil: el administrador ve todos los avisos; cada trabajador ve los suyos más los que
    no están asignados a nadie (y, si no lo están, coinciden con alguna de sus especialidades o no tienen
    ninguna), pero no los asignados a otro técnico ni los de una especialidad que no tiene.
    [usuario]: dict de sesión (el del PC o el de la petición web)."""
    if usuarios.es_admin(usuario):
        return list(avisos)
    uid = (usuario or {}).get("id")
    especialidades = (usuario or {}).get("especialidad_ids") or []
    return [a for a in avisos if a[6] == uid or (a[6] is None and (a[8] is None or a[8] in especialidades))]


def pendientes_hoy(avisos, por_contador, hoy=None):
    """Cuántos de [avisos] tocan hoy y no están hechos (la tarjeta «Avisos pendientes» del Dashboard).
    [por_contador]: contadores.estados_avisos(). Un aviso por contador cuenta si toca por contador (y no se ha
    hecho hoy); si además tiene fecha, también si toca por fecha. Por fecha: la ocurrencia de hoy y los días de
    margen siguientes, salvo los diarios, que no usan margen (el de ayer no cuenta como hecho hoy)."""
    hoy = hoy or date.today()
    hoy_iso = hoy.isoformat()
    total = 0
    for aid, _titulo, finicio, freq, dur, ult, *_ in avisos:
        info = por_contador.get(aid)
        if info and ult != hoy_iso and info["estado"] in ("PENDIENTE", "ATRASADO"):
            total += 1
            continue
        if info and info["solo_contador"]:
            continue
        if not finicio:
            continue
        try:
            ocurrencia = date.fromisoformat(finicio)
        except (TypeError, ValueError):
            continue
        freq = idiomas.normalizar_frecuencia(freq or "Anual")
        margen = timedelta(days=0 if freq == "Diario" else int(dur or 0))
        while ocurrencia + margen < hoy:
            siguiente = frecuencias.avanzar(ocurrencia, freq)
            if siguiente <= ocurrencia:           # frecuencia desconocida: no avanza
                break
            ocurrencia = siguiente
        if ocurrencia <= hoy <= ocurrencia + margen and ult != ocurrencia.isoformat():
            total += 1
    return total
