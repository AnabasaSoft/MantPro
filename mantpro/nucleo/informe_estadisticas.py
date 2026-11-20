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
"""«👥 Estadísticas por técnico» sin Qt: la tabla (columnas según el tipo, cabeceras y filas) y su exportación a
Excel y PDF. Lo usan el diálogo del PC (Dashboard) y MantPro Web. Los textos salen en el idioma activo (en MantPro
Web, el de cada petición)."""

import re
from datetime import datetime

from .. import idiomas
from . import estadisticas, usuarios

# Tipos del desplegable «Tipo», en su orden: None (todos), solo trabajos y averías, solo preventivos
TIPOS = (None, "trabajos", "preventivos")


def _tt(clave, defecto):
    valor = idiomas.t(clave)
    return defecto if valor == clave else valor


def nombre_tipo(tipo):
    return {None: _tt("filtro_todos", "Todos"), "trabajos": _tt("filtro_trabajos_averias", "Trabajos y averías"),
            "preventivos": _tt("filtro_mantenimiento_preventivo", "Mantenimiento preventivo")}[tipo]


def texto_nota():
    return _tt("msg_nota_estadisticas_tecnicos", "Las horas de parada son las de los trabajos de avería. «Pendientes» son "
               "los trabajos que cada técnico tiene asignados ahora mismo.")


def columnas(tipo):
    """Columnas tras «Técnico» y «Total»: primero los totales (lo que más se mira) y después, con un año, los meses.
    Las que no aportan nada con el tipo elegido no se muestran (en preventivos todo es preventivo y no hay averías
    ni pendientes; en trabajos no hay preventivos). Las horas trabajadas, en todos."""
    return ["horas_trabajo"] + ([] if tipo == "preventivos" else [
        c for c in ("averias", "preventivos", "horas_paro", "pendientes") if not (tipo == "trabajos" and c == "preventivos")])


def tabla(ruta_db, anio=None, tipo=None, sede=None):
    """La tabla del diálogo: {anio, tipo, columnas, cabeceras, filas (con números de verdad), con_nota}. [sede]: solo
    esa (None = todas)."""
    datos = estadisticas.por_tecnico(ruta_db, anio, tipo, sede)
    cols = columnas(tipo)
    nombres_col = {"averias": _tt("hdr_averias", "Averías"), "preventivos": _tt("hdr_preventivos", "Preventivos"),
                   "horas_paro": _tt("hdr_horas_paro", "Horas de parada"),
                   "pendientes": _tt("hdr_pendientes_asignados", "Pendientes"),
                   "horas_trabajo": _tt("hdr_horas_trabajadas", "Horas trabajadas")}
    meses = [idiomas.t(f"mes_{m:02d}_corto") for m in range(1, 13)] if anio else []
    filas = []
    for d in datos:
        nombre = _tt("lbl_tecnico_historico", "Histórico (sin usuario)") if d["nombre"] == usuarios.ETIQUETA_HISTORICO else d["nombre"]
        filas.append([nombre, d["total"]] + [round(d[c], 2) for c in cols] + (list(d["meses"]) if anio else []))
    return {"anio": anio, "tipo": tipo, "columnas": cols, "con_nota": tipo != "preventivos", "filas": filas,
            "cabeceras": [_tt("hdr_tecnico", "Técnico"), _tt("hdr_total", "Total")] + [nombres_col[c] for c in cols] + meses}


def grafico(tab):
    """Los datos del gráfico «Trabajos por técnico»: (nombre, total) de los que tienen algún trabajo."""
    return [(f[0], f[1]) for f in tab["filas"] if f[1]]


def titulo(tab):
    periodo = str(tab["anio"]) if tab["anio"] else _tt("lbl_todos_los_anos", "Todos los años")
    texto = f"{_tt('title_estadisticas_tecnicos', 'Estadísticas por técnico')} — {periodo}"
    return texto + (f" — {nombre_tipo(tab['tipo'])}" if tab["tipo"] else "")


def nombre_fichero(tab, formato):
    limpiar = lambda s: re.sub(r"[^\w-]+", "_", s).strip("_")      # noqa: E731
    base = limpiar(_tt("title_estadisticas_tecnicos", "Estadísticas por técnico"))
    periodo = tab["anio"] or limpiar(_tt("lbl_todos_los_anos", "Todos los años"))
    sufijo = "_" + limpiar(nombre_tipo(tab["tipo"])) if tab["tipo"] else ""
    return f"{base}_{periodo}{sufijo}.{formato}"


def texto_fecha():
    return _tt("txt_fecha_informe", "Fecha: {fecha}").format(
        fecha=idiomas.formato_fecha_localizada(datetime.now().strftime("%Y-%m-%d")))


def generar_excel(tab, salida):
    """[salida]: ruta o fichero abierto en binario."""
    import xlsxwriter
    cabeceras, filas = tab["cabeceras"], tab["filas"]
    wb = xlsxwriter.Workbook(salida, {"in_memory": True})
    ws = wb.add_worksheet(re.sub(r"[\[\]:*?/\\]", "", _tt("title_estadisticas_tecnicos", "Estadísticas por técnico"))[:31])
    f_tit = wb.add_format({"bold": True, "font_size": 14})
    f_nota = wb.add_format({"italic": True, "font_color": "#7f8c8d"})
    f_cab = wb.add_format({"bold": True, "bg_color": "#3daee9", "color": "white", "border": 1, "align": "center", "valign": "vcenter"})
    f_txt = wb.add_format({"border": 1})
    f_num = wb.add_format({"border": 1, "num_format": "0.##", "align": "right"})
    f_total = wb.add_format({"border": 1, "num_format": "0.##", "align": "right", "bold": True})
    ws.write(0, 0, titulo(tab), f_tit)
    ws.write(1, 0, texto_fecha())
    if tab["con_nota"]:
        ws.write(2, 0, texto_nota(), f_nota)
    fila0 = 4
    for c, txt in enumerate(cabeceras):
        ws.write(fila0, c, txt, f_cab)
    for i, fila in enumerate(filas, start=fila0 + 1):
        ws.write(i, 0, fila[0], f_txt)
        for c, valor in enumerate(fila[1:], start=1):
            ws.write_number(i, c, valor, f_total if c == 1 else f_num)
    ws.set_column(0, 0, max(14, max(len(f[0]) for f in filas) + 2))
    fijas = 2 + len(tab["columnas"])
    ws.set_column(1, fijas - 1, 13)
    if len(cabeceras) > fijas:
        ws.set_column(fijas, len(cabeceras) - 1, 6)
    ws.freeze_panes(fila0 + 1, 1)
    ws.autofilter(fila0, 0, fila0 + len(filas), len(cabeceras) - 1)
    wb.close()


def _grafico_pdf(pares, ancho):
    """El gráfico de barras dibujado con reportlab (sin Qt), como el del PC: nombre a la izquierda, barra y valor."""
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.lib import colors
    alto_fila, margen = 22, 6
    alto = margen * 2 + alto_fila * len(pares)
    d = Drawing(ancho, alto)
    d.add(Rect(0, 0, ancho, alto, fillColor=colors.HexColor("#f0f0f0"), strokeColor=None))
    ancho_nombre = min(ancho * 0.3, 170)
    hueco = ancho - ancho_nombre - 50
    maximo = max(v for _, v in pares) or 1
    for i, (nombre, valor) in enumerate(pares):
        y = alto - margen - alto_fila * (i + 1) + 5
        texto = nombre if len(nombre) <= 28 else nombre[:27] + "…"
        d.add(String(ancho_nombre - 6, y + 4, texto, fontSize=9, textAnchor="end"))
        largo = max(2, hueco * valor / maximo)
        d.add(Rect(ancho_nombre, y, largo, alto_fila - 8, fillColor=colors.HexColor("#3daee9"), strokeColor=None))
        d.add(String(ancho_nombre + largo + 5, y + 4, f"{valor:g}", fontSize=9))
    return d


def generar_pdf(tab, salida, ruta_logo=None, grafico_png=None):
    """[salida]: ruta o fichero abierto en binario. [grafico_png]: (ruta, ancho_px, alto_px) del gráfico ya dibujado
    (el PC usa el mismo de la ventana); sin él se dibuja con reportlab."""
    import os
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image as PDFImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    cabeceras, filas = tab["cabeceras"], tab["filas"]
    # Con los meses la tabla tiene 18 columnas: en apaisado caben bien.
    pagina = landscape(A4) if tab["anio"] else A4
    doc = SimpleDocTemplate(salida, pagesize=pagina, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    celda = ParagraphStyle("CeldaEst", parent=styles["BodyText"], fontSize=8, leading=10)
    celda_cab = ParagraphStyle("CabEst", parent=celda, textColor=colors.whitesmoke, fontName="Helvetica-Bold", alignment=1)
    nota = ParagraphStyle("NotaEst", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")      # noqa: E731
    elementos = []
    if ruta_logo and os.path.exists(ruta_logo):
        try:
            logo = PDFImage(ruta_logo, width=4*cm, height=2*cm)
            logo.hAlign = "LEFT"
            logo.keepAspectRatio = True
            elementos += [logo, Spacer(1, 8)]
        except Exception:
            pass
    elementos += [Paragraph(esc(titulo(tab)), styles["Title"]), Paragraph(esc(texto_fecha()), styles["Normal"]), Spacer(1, 8)]

    ancho_util = pagina[0] - 60
    pares = grafico(tab)
    if grafico_png:
        ruta, ancho_px, alto_px = grafico_png
        elementos += [PDFImage(ruta, width=ancho_util, height=ancho_util * alto_px / ancho_px), Spacer(1, 10)]
    elif pares:
        elementos += [_grafico_pdf(pares, ancho_util), Spacer(1, 10)]

    fijas = 2 + len(tab["columnas"])

    def num(v):
        return f"{v:g}" if v else "·"
    datos = [[Paragraph(esc(c), celda_cab) for c in cabeceras]]
    for f in filas:
        datos.append([Paragraph(esc(f[0]), celda), f"{f[1]:g}"] + [num(v) if i >= fijas else f"{v:g}" for i, v in enumerate(f[2:], start=2)])
    ancho_nombre = 5.5*cm if tab["anio"] else 6*cm
    resto = ancho_util - ancho_nombre
    if tab["anio"]:
        # Las columnas de totales no necesitan más de 2,6 cm; el resto, para los meses.
        ancho_fija = min(2.6*cm, resto * 0.55 / (fijas - 1))
        anchos = [ancho_nombre] + [ancho_fija] * (fijas - 1) + [(resto - ancho_fija * (fijas - 1)) / 12] * 12
    else:
        anchos = [ancho_nombre] + [resto / (fijas - 1)] * (fijas - 1)
    t = Table(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3daee9")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (1, 1), (-1, -1), 8),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
        # Meses: poco margen para que quepan abreviaturas de 4 letras («Janv»).
        ("LEFTPADDING", (fijas, 0), (-1, -1), 1), ("RIGHTPADDING", (fijas, 0), (-1, -1), 2),
    ]))
    elementos.append(t)
    if tab["con_nota"]:
        elementos += [Spacer(1, 8), Paragraph(esc(texto_nota()), nota)]
    doc.build(elementos)
