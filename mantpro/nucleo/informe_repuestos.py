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

"""El informe de los repuestos de una máquina (sin Qt), en PDF y en Excel: lo que hace «📄 Exportar» del panel
«🔩 Repuestos» del PC y de MantPro Web. [destino]: una ruta o un fichero en memoria (BytesIO)."""

import os
import re
from datetime import datetime

from .. import idiomas
from . import ficha_maquinas, maquinas
from .rutas import DATA_DIR

FORMATOS = ("pdf", "xlsx")


def titulo(maquina_id):
    """«Repuestos de Prensa > Motor» (la ruta completa de la máquina)."""
    return idiomas.t("titulo_informe_repuestos").format(maquina=maquinas.mapa_rutas_completas().get(maquina_id, ""))


def nombre_fichero(maquina_id, formato):
    return re.sub(r"[^\w-]+", "_", titulo(maquina_id)).strip("_") + "." + formato


def cabeceras():
    """Las de la tabla del panel (CÓDIGO, MATERIAL, LLEVA, STOCK, UBICACIÓN, NOTAS)."""
    t = idiomas.t
    return [t("hdr_codigo"), t("hdr_material"), t("hdr_cantidad_montada"), t("hdr_stock"), t("hdr_ubicacion"), t("hdr_notas")]


def _fecha():
    return idiomas.t("txt_fecha_informe").format(fecha=idiomas.formato_fecha_localizada(datetime.now().strftime("%Y-%m-%d")))


def excel(destino, maquina_id):
    import xlsxwriter
    t = idiomas.t
    lista = ficha_maquinas.repuestos(maquina_id)
    wb = xlsxwriter.Workbook(destino, {"in_memory": True})
    ws = wb.add_worksheet(t("lbl_repuestos").replace("🔩", "").strip()[:31])
    f_tit = wb.add_format({"bold": True, "font_size": 14})
    f_cab = wb.add_format({"bold": True, "bg_color": "#3daee9", "color": "white", "border": 1, "align": "center"})
    f_txt = wb.add_format({"border": 1})
    f_num = wb.add_format({"border": 1, "num_format": "0.##"})
    f_rojo = wb.add_format({"border": 1, "num_format": "0.##", "bold": True, "font_color": "#c0392b"})
    ws.write(0, 0, titulo(maquina_id), f_tit)
    ws.write(1, 0, _fecha())
    cab = cabeceras()
    cab = cab[:4] + [t("hdr_unidad")] + cab[4:]
    for c, txt in enumerate(cab):
        ws.write(3, c, txt, f_cab)
    for i, r in enumerate(lista, start=4):
        fila = [r.get("codigo") or "", r["nombre"], r["cantidad"], r["stock_actual"], r.get("unidad") or "",
                r["ubicacion"], r.get("notas") or ""]
        for c, v in enumerate(fila):
            if c == 3 and r["bajo_minimo"]:
                ws.write_number(i, c, v, f_rojo)
            elif c in (2, 3):
                ws.write_number(i, c, v, f_num)
            else:
                ws.write(i, c, v, f_txt)
    for c, ancho in enumerate((12, 40, 8, 8, 9, 36, 24)):
        ws.set_column(c, c, ancho)
    ws.freeze_panes(4, 0)
    wb.close()


def pdf(destino, maquina_id):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image as PDFImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    lista = ficha_maquinas.repuestos(maquina_id)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(destino, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30,
                            title=titulo(maquina_id))
    celda = ParagraphStyle("CeldaRep", parent=styles["BodyText"], fontSize=9, leading=11)
    celda_cab = ParagraphStyle("CabRep", parent=celda, textColor=colors.whitesmoke, fontName="Helvetica-Bold", fontSize=8)
    celda_num = ParagraphStyle("NumRep", parent=celda, alignment=2)
    celda_rojo = ParagraphStyle("RojoRep", parent=celda_num, textColor=colors.HexColor("#c0392b"), fontName="Helvetica-Bold")

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
    elementos += [Paragraph(esc(titulo(maquina_id)), styles["Title"]), Paragraph(esc(_fecha()), styles["Normal"]), Spacer(1, 10)]
    datos = [[Paragraph(esc(c), celda_cab) for c in cabeceras()]]
    for r in lista:
        unidad = f" {r['unidad']}" if r.get("unidad") else ""
        datos.append([Paragraph(esc(r.get("codigo") or ""), celda), Paragraph(esc(r["nombre"]), celda),
                      Paragraph(f"{r['cantidad']:g}{esc(unidad)}", celda_num),
                      Paragraph(f"{r['stock_actual']:g}{esc(unidad)}", celda_rojo if r["bajo_minimo"] else celda_num),
                      Paragraph(esc(r["ubicacion"]), celda), Paragraph(esc(r.get("notas") or ""), celda)])
    tabla = Table(datos, colWidths=[1.9 * cm, 5.2 * cm, 1.7 * cm, 1.7 * cm, 4.4 * cm, 3.0 * cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3daee9")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
    ]))
    elementos.append(tabla)
    doc.build(elementos)


def generar(destino, maquina_id, formato):
    """[formato]: «pdf» o «xlsx»."""
    if formato not in FORMATOS:
        raise ValueError("formato_no_valido")
    (pdf if formato == "pdf" else excel)(destino, maquina_id)
