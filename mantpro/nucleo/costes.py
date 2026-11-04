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

"""Coste de mantenimiento acumulado (repuestos + mano de obra) para el
Dashboard: total del mes y del año, evolución mensual y ranking de máquinas.

Lógica pura (sin Qt): la interfaz solo dibuja lo que devuelven estas
funciones, y la API de MantPro Cloud podrá ofrecerlas tal cual."""

from datetime import date

from . import consumos, mano_obra, maquinas


def _trabajos_con_coste(fecha_inicio=None, fecha_fin=None):
    """[{id, fecha, maquina_id, importe, sin_precio}] de los trabajos que
    tienen repuestos o tiempo trabajado, dentro del rango si se indica
    ('YYYY-MM-DD'). `importe` suma repuestos y mano de obra con precio;
    `sin_precio` avisa de que a algún concepto le falta el precio."""
    sql = "SELECT id, fecha, maquina_id FROM tareas WHERE fecha IS NOT NULL AND fecha != ''"
    parametros = []
    if fecha_inicio and fecha_fin:
        sql += " AND fecha BETWEEN ? AND ?"
        parametros = [fecha_inicio, fecha_fin]
    con = maquinas._conn()
    filas = [(f[0], f[1], f[2]) for f in con.execute(sql, parametros).fetchall()]
    con.close()
    ids = [f[0] for f in filas]
    materiales = consumos.materiales_de_trabajos(ids)
    tiempos = mano_obra.tiempos_de(ids)
    resultado = []
    for tid, fecha, mid in filas:
        mats = materiales.get(tid)
        tm = tiempos.get(tid)
        if not mats and not tm:
            continue
        importe, sin_precio = (0.0, False)
        if mats:
            importe, sin_precio = consumos.coste(mats)
        if tm:
            if tm["importe"] is None:
                sin_precio = True
            else:
                importe += tm["importe"]
        resultado.append({"id": tid, "fecha": fecha, "maquina_id": mid,
                          "importe": importe, "sin_precio": sin_precio})
    return resultado


def _meses_hasta(hoy, n_meses):
    """['YYYY-MM', ...] de los últimos n_meses (incluido el de `hoy`), en orden."""
    anio, mes = hoy.year, hoy.month
    meses = []
    for _ in range(n_meses):
        meses.append(f"{anio:04d}-{mes:02d}")
        mes -= 1
        if mes == 0:
            mes, anio = 12, anio - 1
    return meses[::-1]


def resumen(n_meses=12, top_n=8, hoy=None):
    """Datos del Dashboard:
    {"mes": importe del mes actual, "anio": importe del año actual,
     "sin_precio": hay conceptos sin precio (el total se queda corto),
     "por_mes": [('YYYY-MM', importe)] de los últimos n_meses,
     "ranking": [(máquina, importe)] de las top_n máquinas de nivel superior
                (sumando sus submáquinas) con más coste en el año actual}."""
    hoy = hoy or date.today()
    meses = _meses_hasta(hoy, n_meses)
    trabajos = _trabajos_con_coste(meses[0] + "-01", f"{hoy.year:04d}-12-31")
    clave_mes = f"{hoy.year:04d}-{hoy.month:02d}"
    prefijo_anio = f"{hoy.year:04d}-"
    por_mes = {m: 0.0 for m in meses}
    total_mes = total_anio = 0.0
    sin_precio = False
    por_maquina = {}
    for t in trabajos:
        mes = t["fecha"][:7]
        if mes in por_mes:
            por_mes[mes] += t["importe"]
        if mes == clave_mes:
            total_mes += t["importe"]
            sin_precio |= t["sin_precio"]
        if t["fecha"].startswith(prefijo_anio):
            total_anio += t["importe"]
            sin_precio |= t["sin_precio"]
            if t["maquina_id"] is not None:
                por_maquina[t["maquina_id"]] = por_maquina.get(t["maquina_id"], 0.0) + t["importe"]
    ranking = []
    for m in maquinas.listar_maquinas():
        if m["padre_id"] is not None:
            continue
        total = sum(por_maquina.get(i, 0.0) for i in maquinas.descendientes_ids(m["id"]))
        if total > 0:
            ranking.append((m["nombre"], total))
    ranking.sort(key=lambda par: par[1], reverse=True)
    return {"mes": total_mes, "anio": total_anio, "sin_precio": sin_precio,
            "por_mes": [(m, por_mes[m]) for m in meses], "ranking": ranking[:top_n]}
