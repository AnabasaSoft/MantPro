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

"""«📄 Exportar» del stock de almacén y del stock bajo mínimo (sin Qt), en PDF, Excel y CSV: lo que hacen las pestañas
del PC y MantPro Web. [destino]: una ruta o un fichero en memoria (BytesIO)."""

import csv
import io
import os
import re
from datetime import datetime

from .. import idiomas
from . import almacen, ficha_stock
from .rutas import DATA_DIR

FORMATOS = ("pdf", "xlsx", "csv")


def alcance(almacen_id, zona_id=None):
    """Lo que ofrece el diálogo «Qué exportar»: (zonas [(id, nombre)], estanterías de la zona [(id, nombre)])."""
    zonas = [(z["id"], z["nombre"]) for z in almacen.listar_zonas(almacen_id)]
    ests = [(e["id"], e["nombre"]) for e in almacen.listar_estructura(zona_id, almacen_ids=almacen_id)]
    return zonas, ests


def texto_ambito(zona_id, est_id, zonas, ests):
    """«Zona A · Estantería 3», «Zona A», «Estantería 3» o None (todo)."""
    nz, ne = dict(zonas).get(zona_id), dict(ests).get(est_id)
    if est_id is not None and ne:
        return f"{nz} · {ne}" if zona_id is not None and nz else ne
    return nz if zona_id is not None else None


def materiales(almacen_id, zona_id=None, est_id=None, solo_bajo_minimo=False, con_minimo=True):
    """Los artículos a exportar, con su ubicación, ordenados por ubicación (como se recorre el almacén)."""
    lista = almacen.listar_materiales(None, zona_id, est_id, almacen_ids=[almacen_id] if almacen_id is not None else [])
    if solo_bajo_minimo:
        lista = [m for m in lista if almacen.esta_bajo_minimo(m) or (con_minimo and almacen.esta_en_minimo(m))]
    for m in lista:
        m["ubicacion"] = ficha_stock.ubicacion(m.get("seccion_id"))
    lista.sort(key=lambda m: (not m["ubicacion"], almacen._clave_orden_natural(m["ubicacion"]),
                              almacen._clave_orden_natural(m["nombre"])))
    return lista


def titulo(solo_bajo_minimo, ambito):
    texto = idiomas.t("titulo_informe_bajo_minimo") if solo_bajo_minimo else idiomas.t("titulo_informe_stock")
    return f"{texto} — {ambito}" if ambito else texto


def nombre_fichero(solo_bajo_minimo, ambito, formato):
    sufijo = re.sub(r"[^\w-]+", "_", ambito).strip("_") if ambito else ""
    base = "Stock_bajo_minimo" if solo_bajo_minimo else "Stock"
    return f"{base}{'_' + sufijo if sufijo else ''}_{datetime.now().strftime('%Y%m%d')}.{formato}"


def _cabeceras():
    t = idiomas.t
    return [t("hdr_codigo"), t("hdr_material"), t("hdr_ubicacion"), t("hdr_stock"), t("hdr_minimo"), t("hdr_unidad")]


def _textos(lista):
    t = idiomas.t
    resumen = t("txt_resumen_stock").format(n=len(lista), b=sum(almacen.esta_bajo_minimo(m) for m in lista))
    fecha = t("txt_fecha_informe").format(fecha=idiomas.formato_fecha_localizada(datetime.now().strftime("%Y-%m-%d")))
    return fecha, resumen


def a_csv(destino, lista):
    """CSV con «;» y BOM (para que Excel lo abra bien en español)."""
    texto = io.StringIO()
    w = csv.writer(texto, delimiter=";")
    w.writerow(_cabeceras())
    for m in lista:
        w.writerow([m.get("codigo") or "", m["nombre"], m["ubicacion"] or "-", f"{m['stock_actual']:g}",
                    f"{m['stock_minimo']:g}", m.get("unidad") or ""])
    datos = ("﻿" + texto.getvalue()).encode("utf-8")
    if isinstance(destino, (str, os.PathLike)):
        with open(destino, "wb") as f:
            f.write(datos)
    else:
        destino.write(datos)


def a_excel(destino, titulo_txt, lista):
    import xlsxwriter
    fecha, resumen = _textos(lista)
    cabeceras = _cabeceras()
    wb = xlsxwriter.Workbook(destino, {"in_memory": True})
    ws = wb.add_worksheet(re.sub(r"[\[\]:*?/\\]", "", idiomas.t("titulo_informe_stock"))[:31])
    f_tit = wb.add_format({"bold": True, "font_size": 14})
    f_cab = wb.add_format({"bold": True, "bg_color": "#3daee9", "color": "white", "border": 1, "align": "center", "valign": "vcenter"})
    f_txt = wb.add_format({"border": 1, "valign": "top"})
    f_num = wb.add_format({"border": 1, "num_format": "0.##", "align": "right"})
    f_num_rojo = wb.add_format({"border": 1, "num_format": "0.##", "align": "right", "bold": True, "font_color": "#c0392b"})
    ws.write(0, 0, titulo_txt, f_tit)
    ws.write(1, 0, fecha)
    ws.write(2, 0, resumen)
    fila0 = 4
    for col, txt in enumerate(cabeceras):
        ws.write(fila0, col, txt, f_cab)
    for i, m in enumerate(lista, start=fila0 + 1):
        ws.write(i, 0, m.get("codigo") or "", f_txt)
        ws.write(i, 1, m["nombre"], f_txt)
        ws.write(i, 2, m["ubicacion"] or "-", f_txt)
        ws.write_number(i, 3, m["stock_actual"], f_num_rojo if almacen.esta_bajo_minimo(m) else f_num)
        ws.write_number(i, 4, m["stock_minimo"], f_num)
        ws.write(i, 5, m.get("unidad") or "", f_txt)
    for col, ancho in enumerate((12, 40, 38, 10, 10, 10)):
        ws.set_column(col, col, ancho)
    ws.freeze_panes(fila0 + 1, 0)
    ws.autofilter(fila0, 0, fila0 + len(lista), len(cabeceras) - 1)
    wb.close()


def a_pdf(destino, titulo_txt, lista):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image as PDFImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    fecha, resumen = _textos(lista)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(destino, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30, title=titulo_txt)
    celda = ParagraphStyle("CeldaStock", parent=styles["BodyText"], fontSize=9, leading=11)
    celda_cab = ParagraphStyle("CabStock", parent=celda, textColor=colors.whitesmoke, fontName="Helvetica-Bold", fontSize=8)
    celda_num = ParagraphStyle("NumStock", parent=celda, alignment=2)
    celda_rojo = ParagraphStyle("RojoStock", parent=celda_num, textColor=colors.HexColor("#c0392b"), fontName="Helvetica-Bold")

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    elementos = []
    ruta_logo = os.path.join(DATA_DIR, "Logo.jpg")
    if os.path.exists(ruta_logo):
        try:
            logo = PDFImage(ruta_logo, width=4 * cm, height=2 * cm)
            logo.hAlign = "LEFT"
            logo.keepAspectRatio = True
            elementos += [logo, Spacer(1, 8)]
        except Exception:                # noqa: BLE001  (un logo que no se puede leer no impide el informe)
            pass
    elementos += [Paragraph(esc(titulo_txt), styles["Title"]),
                  Paragraph(esc(fecha) + " &nbsp;·&nbsp; " + esc(resumen), styles["Normal"]), Spacer(1, 10)]
    datos = [[Paragraph(esc(c), celda_cab) for c in _cabeceras()]]
    for m in lista:
        datos.append([Paragraph(esc(m.get("codigo") or ""), celda), Paragraph(esc(m["nombre"]), celda),
                      Paragraph(esc(m["ubicacion"] or "-"), celda),
                      Paragraph(f"{m['stock_actual']:g}", celda_rojo if almacen.esta_bajo_minimo(m) else celda_num),
                      Paragraph(f"{m['stock_minimo']:g}", celda_num), Paragraph(esc(m.get("unidad") or ""), celda)])
    tabla = Table(datos, colWidths=[1.9 * cm, 5.0 * cm, 4.6 * cm, 1.7 * cm, 2.6 * cm, 2.2 * cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3daee9")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
    ]))
    elementos.append(tabla)
    doc.build(elementos)


def generar(destino, formato, titulo_txt, lista):
    if formato not in FORMATOS:
        raise ValueError("formato_no_valido")
    if formato == "csv":
        a_csv(destino, lista)
    elif formato == "xlsx":
        a_excel(destino, titulo_txt, lista)
    else:
        a_pdf(destino, titulo_txt, lista)
