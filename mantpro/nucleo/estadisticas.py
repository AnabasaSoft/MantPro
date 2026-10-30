# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# MantPro - Sistema de Mantenimiento Preventivo
# Copyright (C) 2026 AnabasaSoft <anabasasoft@gmail.com>
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

"""Estadísticas de trabajos por técnico (Dashboard > Estadísticas por técnico).

Se calculan a partir del historial (tabla tareas, que guarda quién hizo cada
trabajo) y de los pendientes asignados. Sin Qt: solo lee la base de datos."""

import sqlite3

from . import usuarios


def _es(tags, palabra):
    return palabra in (tags or "").lower()


def es_preventivo(tags):
    """Mantenimiento preventivo: lo que viene de un aviso recurrente (el mismo
    criterio que el filtro «Tipo» del Historial) o lleva la etiqueta Preventivo."""
    return _es(tags, "aviso recurrente") or _es(tags, "preventivo")


def anios_disponibles(ruta_db):
    """Años con algún trabajo en el historial, del más reciente al más antiguo."""
    con = sqlite3.connect(ruta_db)
    filas = con.execute("SELECT DISTINCT substr(fecha, 1, 4) FROM tareas WHERE fecha GLOB '[0-9][0-9][0-9][0-9]*' ORDER BY 1 DESC").fetchall()
    con.close()
    return [int(f[0]) for f in filas]


def por_tecnico(ruta_db, anio=None, tipo=None):
    """Lista de dicts, uno por técnico, ordenada de más a menos trabajos:
    nombre, total, meses (12 contadores, solo si se pide un año), averias,
    preventivos, horas_paro y pendientes (asignados ahora mismo). Los
    trabajos anteriores al sistema de usuarios salen como "Histórico".

    tipo: None (todos), "preventivos" (solo mantenimiento preventivo) o
    "trabajos" (averías y demás trabajos). Con "preventivos" no se cuentan
    los pendientes, que son trabajos por hacer y no preventivos."""
    con = sqlite3.connect(ruta_db)
    sql = "SELECT COALESCE(NULLIF(TRIM(usuario_nombre), ''), ?), fecha, tags, horas_paro FROM tareas"
    parametros = [usuarios.ETIQUETA_HISTORICO]
    if anio:
        sql += " WHERE substr(fecha, 1, 4) = ?"
        parametros.append(str(anio))
    datos = {}
    for nombre, fecha, tags, horas in con.execute(sql, parametros):
        preventivo = es_preventivo(tags)
        if (tipo == "preventivos" and not preventivo) or (tipo == "trabajos" and preventivo):
            continue
        d = datos.setdefault(nombre, {"nombre": nombre, "total": 0, "meses": [0] * 12, "averias": 0,
                                      "preventivos": 0, "horas_paro": 0.0, "pendientes": 0})
        d["total"] += 1
        mes = (fecha or "")[5:7]
        if anio and mes.isdigit() and 1 <= int(mes) <= 12:
            d["meses"][int(mes) - 1] += 1
        if _es(tags, "avería") or _es(tags, "averia"):
            d["averias"] += 1
            d["horas_paro"] += float(horas or 0)
        if preventivo:
            d["preventivos"] += 1
    for nombre, n in [] if tipo == "preventivos" else con.execute("SELECT asignado_nombre, COUNT(*) FROM pendientes "
                                 "WHERE TRIM(COALESCE(asignado_nombre, '')) <> '' GROUP BY asignado_nombre"):
        datos.setdefault(nombre, {"nombre": nombre, "total": 0, "meses": [0] * 12, "averias": 0,
                                  "preventivos": 0, "horas_paro": 0.0, "pendientes": 0})["pendientes"] = n
    con.close()
    return sorted(datos.values(), key=lambda d: (-d["total"], d["nombre"].lower()))
