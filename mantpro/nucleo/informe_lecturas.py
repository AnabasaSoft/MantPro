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

"""Máquinas → 📈 Lecturas (sin Qt): cómo evolucionan las medidas de las listas de comprobación (resistencia de tierra,
aislamiento, tiempo de disparo…) de una máquina y sus submáquinas: los textos de la tabla y del resumen, y el informe
en PDF (con el gráfico, dibujado sin Qt) y en Excel. Lo usan el diálogo del PC y MantPro Web. [destino]: una ruta o un
fichero en memoria (BytesIO)."""

import os
import re
from datetime import date, datetime

from .. import idiomas
from . import checklists, graficos_pdf, maquinas
from .rutas import DATA_DIR

ROJO = "#e74c3c"


def t(clave):
    return idiomas.t(clave)


def texto_rango(minimo, maximo, unidad=""):
    """«10 – 20 Ω», «≥ 1 MΩ», «≤ 20 Ω» o «Sin rango»."""
    u = f" {unidad}" if unidad else ""
    if minimo is not None and maximo is not None:
        return f"{minimo:g} – {maximo:g}{u}"
    if minimo is not None:
        return f"≥ {minimo:g}{u}"
    if maximo is not None:
        return f"≤ {maximo:g}{u}"
    return t("lbl_lect_sin_rango")


def nombre_punto(p):
    nombre = f"{p['texto']} ({p['unidad']})" if p["unidad"] else p["texto"]
    if p.get("tipo") == "trifasica":
        nombre += " · " + "/".join(checklists.FASES)
    return nombre


def texto_valor_lectura(l, p):
    """«9,1 bar» o, en un motor trifásico, «L1 12,1 · L2 12,3 · L3 12,0 A (Desequilibrio 1,1 % · …)»."""
    texto = f"{l['valor_texto']} {p['unidad']}".strip()
    if p.get("tipo") == "trifasica" and l.get("desequilibrio") is not None:
        texto += " (" + t("chk_desequilibrio").format(p=f"{l['desequilibrio']:g}", fase=checklists.FASES[l["fase_desviada"]]) + ")"
    return texto


def texto_rango_punto(minimo, maximo, unidad, p):
    """El rango y, en un trifásico con límite, «· desequilibrio máx. 5 %»."""
    texto = texto_rango(minimo, maximo, unidad)
    limite = checklists._deseq_max(p) if p.get("tipo") == "trifasica" else None
    if limite is not None:
        texto += " · " + t("chk_deseq_max").format(p=f"{limite:g}")
    return texto


def series_de(p):
    return checklists.FASES if p.get("tipo") == "trifasica" else None


def opciones_maquina(maquina_id):
    """Las máquinas que se pueden elegir: [(None, «Todas (con submáquinas)»)] si tiene submáquinas, y cada una por su
    ruta completa."""
    rutas = maquinas.mapa_rutas_completas()
    ids = maquinas.descendientes_ids(maquina_id)
    opciones = [(None, t("lbl_lect_todas"))] if len(ids) > 1 else []
    return opciones + [(i, rutas.get(i, str(i))) for i in sorted(ids, key=lambda i: rutas.get(i, "").casefold())]


def puntos(maquina_id, elegida=None):
    """Las medidas de la máquina (con sus submáquinas) o solo de [elegida]: checklists.evolucion_lecturas, cada una
    con «nombre» (lo que sale en el desplegable: «Tierra (Ω) · 4»)."""
    ids = maquinas.descendientes_ids(maquina_id) if elegida is None else [elegida]
    return [dict(p, nombre=f"{nombre_punto(p)} · {len(p['lecturas'])}") for p in checklists.evolucion_lecturas(ids)]


def resumen(p):
    """«4 lecturas · 1 fuera de rango · rango correcto: … · última: … (fecha)»."""
    lecturas = p["lecturas"]
    ultima = lecturas[-1]
    return t("lbl_lect_resumen").format(
        n=len(lecturas), fuera=sum(1 for l in lecturas if l["fuera"]),
        rango=texto_rango_punto(p["minimo"], p["maximo"], p["unidad"], p),
        ultima=texto_valor_lectura(ultima, p), fecha=idiomas.formato_fecha_localizada(ultima["fecha"]))


def filas(p):
    """Las filas de la tabla en orden cronológico: [{lectura, fecha, maquina, valor, rango, fuera, tarea_id, tecnico,
    nota}] (la tabla las enseña al revés: la más reciente arriba)."""
    rutas = maquinas.mapa_rutas_completas()
    return [{"lectura": l, "fecha": idiomas.formato_fecha_localizada(l["fecha"]), "maquina": rutas.get(l["maquina_id"], ""),
             "valor": texto_valor_lectura(l, p), "fuera": l["fuera"], "tarea_id": l["tarea_id"], "tecnico": l["tecnico"],
             "nota": l["nota"], "rango": texto_rango_punto(l["minimo"], l["maximo"], p["unidad"], l | {"tipo": p.get("tipo")})}
            for l in p["lecturas"]]


def nombre_fichero(texto_maquina, p, formato):
    base = re.sub(r"[^\w-]+", "_", f"{t('title_lect_informe')}_{texto_maquina}_{p['texto']}").strip("_")[:120]
    return f"{base}.{formato}"


def cabecera(p, texto_maquina):
    return [t("title_lect_informe"), f"{t('lbl_lect_maquina')}: {texto_maquina}", f"{t('lbl_lect_punto')}: {nombre_punto(p)}",
            f"{t('lbl_lect_rango')}: {texto_rango_punto(p['minimo'], p['maximo'], p['unidad'], p)}",
            t("txt_fecha_informe").format(fecha=idiomas.formato_fecha_localizada(datetime.now().strftime("%Y-%m-%d")))]


def excel(destino, p, texto_maquina):
    import xlsxwriter
    wb = xlsxwriter.Workbook(destino, {"in_memory": True})
    ws = wb.add_worksheet(re.sub(r"[\[\]:*?/\\]", "", t("title_lect_informe"))[:31])
    f_tit = wb.add_format({"bold": True, "font_size": 14})
    f_cab = wb.add_format({"bold": True, "bg_color": "#3daee9", "color": "white", "border": 1, "align": "center"})
    f_txt = wb.add_format({"border": 1})
    f_fecha = wb.add_format({"border": 1, "num_format": idiomas.formato_fecha_excel()})
    f_num = wb.add_format({"border": 1, "num_format": "0.###"})
    f_mal = wb.add_format({"border": 1, "num_format": "0.###", "font_color": ROJO, "bold": True})
    cab = cabecera(p, texto_maquina)
    ws.write(0, 0, cab[0], f_tit)
    for i, linea in enumerate(cab[1:], start=1):
        ws.write(i, 0, linea)
    fila0 = len(cab) + 1
    trifasica = p.get("tipo") == "trifasica"
    # Columnas de valor: VALOR, o L1, L2, L3 y DESEQUILIBRIO % en un motor trifásico
    col_valor = list(checklists.FASES) + [t("hdr_lect_desequilibrio")] if trifasica else [t("hdr_lect_valor")]
    nv = len(col_valor)
    cabeceras = [t("hdr_fecha"), t("hdr_maquina").upper()] + col_valor + [
        t("hdr_lect_unidad"), t("hdr_lect_rango"), t("hdr_lect_estado"), t("hdr_tecnico").upper(), t("hdr_lect_nota")]
    for c, txt in enumerate(cabeceras):
        ws.write(fila0, c, txt, f_cab)
    lista = filas(p)
    for i, f in enumerate(lista, start=fila0 + 1):
        l = f["lectura"]
        try:
            ws.write_datetime(i, 0, datetime.combine(date.fromisoformat(l["fecha"]), datetime.min.time()), f_fecha)
        except ValueError:
            ws.write(i, 0, l["fecha"], f_txt)
        ws.write(i, 1, f["maquina"], f_txt)
        if trifasica:
            rango_fase = {"minimo": l["minimo"], "maximo": l["maximo"]}
            for k, v in enumerate(l["valores"]):
                if v is not None:
                    ws.write_number(i, 2 + k, v, f_mal if checklists.fuera_de_rango(rango_fase, v) else f_num)
                else:
                    ws.write(i, 2 + k, "", f_txt)
            if l["desequilibrio"] is not None:
                ws.write_number(i, 5, l["desequilibrio"], f_mal if l.get("desequilibrio_fuera") else f_num)
            else:
                ws.write(i, 5, "", f_txt)
        elif l["valor"] is not None:
            ws.write_number(i, 2, l["valor"], f_mal if l["fuera"] else f_num)
        else:
            ws.write(i, 2, l["valor_texto"], f_txt)
        ws.write(i, 2 + nv, p["unidad"], f_txt)
        ws.write(i, 3 + nv, f["rango"], f_txt)
        ws.write(i, 4 + nv, t("lbl_lect_fuera") if l["fuera"] else t("lbl_lect_correcta"), f_txt)
        ws.write(i, 5 + nv, l["tecnico"], f_txt)
        ws.write(i, 6 + nv, l["nota"], f_txt)
    ultima = fila0 + len(lista)
    ws.set_column(0, 0, 12)
    ws.set_column(1, 1, 28)
    ws.set_column(2, 2 + nv, 10)
    ws.set_column(3 + nv, 4 + nv, 16)
    ws.set_column(5 + nv, 5 + nv, 18)
    ws.set_column(6 + nv, 6 + nv, 40)
    ws.freeze_panes(fila0 + 1, 0)
    if lista:
        grafico = wb.add_chart({"type": "line"})
        for k, nombre in enumerate(checklists.FASES if trifasica else [nombre_punto(p)]):
            grafico.add_series({"name": nombre, "categories": [ws.name, fila0 + 1, 0, ultima, 0],
                                "values": [ws.name, fila0 + 1, 2 + k, ultima, 2 + k], "marker": {"type": "circle"}})
        grafico.set_title({"name": nombre_punto(p)})
        grafico.set_legend({"position": "bottom"} if trifasica else {"none": True})
        grafico.set_x_axis({"date_axis": True, "num_format": idiomas.formato_fecha_excel(corta=True)})
        ws.insert_chart(ultima + 2, 0, grafico, {"x_scale": 1.6, "y_scale": 1.2})
    wb.close()


def pdf(destino, p, texto_maquina):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image as PDFImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    doc = SimpleDocTemplate(destino, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30,
                            title=t("title_lect_informe"))
    styles = getSampleStyleSheet()
    celda = ParagraphStyle("CeldaLect", parent=styles["BodyText"], fontSize=8, leading=10)
    celda_mal = ParagraphStyle("CeldaLectMal", parent=celda, textColor=colors.HexColor(ROJO), fontName="Helvetica-Bold")
    celda_cab = ParagraphStyle("CabLect", parent=celda, textColor=colors.whitesmoke, fontName="Helvetica-Bold")

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
    cab = cabecera(p, texto_maquina)
    elementos.append(Paragraph(esc(cab[0]), styles["Title"]))
    elementos += [Paragraph(esc(linea), styles["Normal"]) for linea in cab[1:]]
    elementos.append(Spacer(1, 10))
    ancho_util = A4[0] - 60
    elementos += [graficos_pdf.evolucion(p["lecturas"], p["minimo"], p["maximo"], series_de(p), ancho_util, ancho_util * 340 / 900,
                                         idiomas.formato_fecha_localizada), Spacer(1, 10)]
    datos = [[Paragraph(esc(c), celda_cab) for c in (t("hdr_fecha"), t("hdr_maquina").upper(), t("hdr_lect_valor"),
                                                     t("hdr_lect_rango"), t("hdr_tecnico").upper(), t("hdr_lect_nota"))]]
    for f in reversed(filas(p)):
        datos.append([Paragraph(esc(f["fecha"]), celda), Paragraph(esc(f["maquina"]), celda),
                      Paragraph(esc(f["valor"]), celda_mal if f["fuera"] else celda), Paragraph(esc(f["rango"]), celda),
                      Paragraph(esc(f["tecnico"]), celda), Paragraph(esc(f["nota"]), celda)])
    anchos = [2.2 * cm, 3.6 * cm, 4.6 * cm, 2.4 * cm, 2.6 * cm] if p.get("tipo") == "trifasica" \
        else [2.2 * cm, 4.5 * cm, 2.4 * cm, 2.8 * cm, 3 * cm]
    anchos.append(ancho_util - sum(anchos))
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3daee9")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
    ]))
    elementos.append(tabla)
    doc.build(elementos)


def generar(destino, p, texto_maquina, formato):
    if formato not in ("pdf", "xlsx"):
        raise ValueError("formato_no_valido")
    (pdf if formato == "pdf" else excel)(destino, p, texto_maquina)
