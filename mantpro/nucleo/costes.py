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


def _trabajos_con_coste(fecha_inicio=None, fecha_fin=None, sede=None):
    """[{id, fecha, maquina_id, importe, sin_precio}] de los trabajos que
    tienen repuestos o tiempo trabajado, dentro del rango si se indica
    ('YYYY-MM-DD'). `importe` suma repuestos y mano de obra con precio;
    `sin_precio` avisa de que a algún concepto le falta el precio."""
    from . import sedes   # [sede]: solo los de esa sede (None = todas)
    sql = "SELECT id, fecha, maquina_id FROM tareas WHERE fecha IS NOT NULL AND fecha != '' AND " + sedes.condicion(sede)
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


def resumen(n_meses=12, top_n=8, hoy=None, sede=None):
    """Datos del Dashboard:
    {"mes": importe del mes actual, "anio": importe del año actual,
     "sin_precio": hay conceptos sin precio (el total se queda corto),
     "por_mes": [('YYYY-MM', importe)] de los últimos n_meses,
     "ranking": [(máquina, importe)] de las top_n máquinas de nivel superior
                (sumando sus submáquinas) con más coste en el año actual}."""
    hoy = hoy or date.today()
    meses = _meses_hasta(hoy, n_meses)
    from . import sedes
    trabajos = _trabajos_con_coste(meses[0] + "-01", f"{hoy.year:04d}-12-31", sede)
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
        if m["padre_id"] is not None or not sedes.de_la_sede(m.get("sede_id"), sede):
            continue
        total = sum(por_maquina.get(i, 0.0) for i in maquinas.descendientes_ids(m["id"]))
        if total > 0:
            ranking.append((m["nombre"], total))
    ranking.sort(key=lambda par: par[1], reverse=True)
    return {"mes": total_mes, "anio": total_anio, "sin_precio": sin_precio,
            "por_mes": [(m, por_mes[m]) for m in meses], "ranking": ranking[:top_n]}


# ---------------------------------------------------------------- «💶 Costes» de la pestaña Máquinas (solo admin)

def por_maquina(db, sede=None, anio=None):
    """El coste de cada máquina de [sede] en [anio] ('AAAA' o None = todos), sumando el de sus submáquinas (lo que
    enseña el diálogo «Costes por máquina» del PC y MantPro Web). Devuelve {"filas", "total"}: cada fila {id, ruta,
    trabajos (con algún coste), horas, mano_obra, mano_sin_precio, repuestos, sin_precio, total, articulos:
    [{codigo, nombre, unidad, cantidad, importe, sin_precio}] de más a menos}, de la que más cuesta a la que menos;
    «total», lo de todo el periodo (sin contar dos veces las submáquinas)."""
    from . import sedes
    con = db.conectar()
    sql = "SELECT id, fecha, maquina_id FROM tareas WHERE maquina_id IS NOT NULL AND " + sedes.condicion(sede)
    filas = con.execute(sql + (" AND substr(fecha,1,4)=?" if anio else ""), (anio,) if anio else ()).fetchall()
    con.close()
    propios = consumos.consumo_por_tareas(filas)
    tiempos = mano_obra.tiempos_de([f[0] for f in filas])
    mano = {}
    for tid, _fecha, mid in filas:
        tm = tiempos.get(tid)
        if not tm:
            continue
        m = mano.setdefault(mid, {"horas": 0.0, "importe": 0.0, "sin_precio": False})
        m["horas"] += tm["horas"]
        if tm["importe"] is None:
            m["sin_precio"] = True
        else:
            m["importe"] += tm["importe"]
    con_materiales = consumos.materiales_de_trabajos([f[0] for f in filas])
    trabajos_con_coste = {}
    for tid, _fecha, mid in filas:
        if tid in tiempos or tid in con_materiales:
            trabajos_con_coste.setdefault(mid, set()).add(tid)
    rutas = maquinas.mapa_rutas_completas()
    resultado = []
    for maq in {m["id"] for m in maquinas.listar_maquinas() if sedes.de_la_sede(m.get("sede_id"), sede)}:
        acum = {"repuestos": 0.0, "sin_precio": False, "articulos": {}, "horas": 0.0, "mano_obra": 0.0, "mano_sin_precio": False}
        ids_trab = set()
        for sub in maquinas.descendientes_ids(maq):
            p = propios.get(sub)
            if p:
                acum["repuestos"] += p["importe"]
                acum["sin_precio"] |= p["sin_precio"]
                for clave, a in p["articulos"].items():
                    d = acum["articulos"].setdefault(clave, {"cantidad": 0.0, "importe": 0.0, "sin_precio": False})
                    d["cantidad"] += a["cantidad"]
                    d["importe"] += a["importe"]
                    d["sin_precio"] |= a["sin_precio"]
            mo = mano.get(sub)
            if mo:
                acum["horas"] += mo["horas"]
                acum["mano_obra"] += mo["importe"]
                acum["mano_sin_precio"] |= mo["sin_precio"]
            ids_trab |= trabajos_con_coste.get(sub, set())
        if not ids_trab:
            continue
        articulos = sorted(({"codigo": c, "nombre": n, "unidad": u, **a} for (c, n, u), a in acum["articulos"].items()),
                           key=lambda x: -x["importe"])
        resultado.append(dict(acum, id=maq, ruta=rutas.get(maq, str(maq)), trabajos=len(ids_trab), articulos=articulos,
                              total=acum["repuestos"] + acum["mano_obra"]))
    resultado.sort(key=lambda f: -f["total"])
    total = sum(p["importe"] for p in propios.values()) + sum(m["importe"] for m in mano.values())
    return {"filas": resultado, "total": total}


def nombre_fichero_maquinas(anio):
    from .. import idiomas
    return f"{idiomas.t('fichero_coste_repuestos')}_{anio or idiomas.t('filtro_todos')}.xlsx"


def excel_por_maquina(destino, datos, anio):
    """El Excel de «Costes por máquina»: hoja «Por máquina» y hoja «Por artículo». [datos]: los de por_maquina."""
    import xlsxwriter
    from datetime import datetime

    from .. import idiomas
    t = idiomas.t
    mon = consumos.moneda()
    libro = xlsxwriter.Workbook(destino, {"in_memory": True})
    negrita = libro.add_format({"bold": True, "bg_color": "#2c3e50", "font_color": "white"})
    dinero = libro.add_format({"num_format": "#,##0.00"})
    h1 = libro.add_worksheet(t("hoja_coste_maquinas")[:31])
    cab = [t("hdr_maquina"), t("hdr_trabajos"), t("lbl_horas"), f"{t('lbl_mano_obra')} ({mon})",
           f"{t('lbl_repuestos_corto')} ({mon})", f"{t('lbl_total')} ({mon})"]
    for c, txt in enumerate(cab):
        h1.write(0, c, txt, negrita)
    for f, d in enumerate(datos["filas"], start=1):
        h1.write(f, 0, d["ruta"])
        h1.write(f, 1, d["trabajos"])
        h1.write(f, 2, round(d["horas"], 2))
        h1.write(f, 3, d["mano_obra"], dinero)
        h1.write(f, 4, d["repuestos"], dinero)
        h1.write(f, 5, d["total"], dinero)
    h1.set_column(0, 0, 45)
    h1.set_column(1, 5, 16)
    h2 = libro.add_worksheet(t("hoja_coste_articulos")[:31])
    cab2 = [t("hdr_maquina"), t("aud_f_codigo"), t("lbl_material"), t("lbl_cantidad"), t("lbl_unidad"), f"{t('lbl_importe')} ({mon})"]
    for c, txt in enumerate(cab2):
        h2.write(0, c, txt, negrita)
    f = 1
    for d in datos["filas"]:
        for a in d["articulos"]:
            for c, v in enumerate((d["ruta"], a["codigo"] or "", a["nombre"], a["cantidad"], a["unidad"] or "")):
                h2.write(f, c, v)
            h2.write(f, 5, a["importe"], dinero)
            f += 1
    h2.set_column(0, 0, 40)
    h2.set_column(1, 1, 14)
    h2.set_column(2, 2, 40)
    h2.set_column(3, 5, 14)
    h1.write(len(datos["filas"]) + 2, 0, f"{t('lbl_anio')}: {anio or t('filtro_todos')} · {datetime.now().strftime('%Y-%m-%d')}")
    libro.close()
