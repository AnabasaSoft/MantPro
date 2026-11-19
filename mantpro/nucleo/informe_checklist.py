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

"""
informe_checklist.py — La lista de comprobación rellenada de un trabajo, en PDF
(para imprimirla o archivarla) y en Excel.

Sin Qt: lo usa el PC y puede usarlo la API o MantPro Cloud. Los textos salen
en el idioma activo (idiomas.t) y la fecha con su formato localizado.
"""

import os

from . import checklists
from .conexion_bd import sqlite3, conectar


def _t(clave):
    from .. import idiomas
    return idiomas.t(clave)


def datos_trabajo(tarea_id, items=None):
    """{"fecha", "titulo", "tecnico", "maquina", "plantilla", "items"} o None si el
    trabajo no tiene lista de comprobación. Con [items], esos puntos en vez de los
    guardados (lo que se está viendo en pantalla, aunque aún no se haya guardado)."""
    lista = checklists.resultado_de(tarea_id)
    if not lista:
        return None
    if items is not None:
        lista = dict(lista, items=checklists.normalizar_items(items))
    con = conectar(checklists.RUTA_DB, timeout=20)
    con.row_factory = sqlite3.Row
    f = con.execute("SELECT fecha, descripcion, COALESCE(usuario_nombre, '') AS tecnico, maquina_id "
                    "FROM tareas WHERE id=?", (tarea_id,)).fetchone()
    con.close()
    maquina = ""
    if f and f["maquina_id"] is not None:
        try:
            from . import maquinas
            maquina = maquinas.mapa_rutas_completas().get(f["maquina_id"], "")
        except Exception:
            maquina = ""
    return {"fecha": (f["fecha"] if f else "") or "", "titulo": ((f["descripcion"] if f else "") or "").split("\n")[0],
            "tecnico": f["tecnico"] if f else "", "maquina": maquina,
            "plantilla": lista["plantilla"], "items": lista["items"]}


def _estado(estado):
    return {"ok": _t("chk_txt_ok"), "mal": _t("chk_txt_mal"), "na": _t("chk_txt_na")}.get(estado, _t("chk_txt_sin"))


def _rango(it):
    """«9–11 A», «≥ 1 MΩ»… y, en un trifásico con límite, «desequilibrio máx. 5 %»."""
    minimo, maximo, u = it.get("minimo"), it.get("maximo"), it.get("unidad") or ""
    n = lambda v: f"{v:g}"                                       # noqa: E731
    partes = []
    if minimo is not None and maximo is not None:
        partes.append(f"{n(minimo)}–{n(maximo)} {u}".strip())
    elif minimo is not None:
        partes.append(f"≥ {n(minimo)} {u}".strip())
    elif maximo is not None:
        partes.append(f"≤ {n(maximo)} {u}".strip())
    limite = checklists._deseq_max(it) if it.get("tipo") == "trifasica" else None
    if limite is not None:
        partes.append(_t("chk_deseq_max").format(p=f"{limite:g}"))
    return " · ".join(partes)


def _lectura(it):
    """El valor apuntado («L1 10,2 · L2 10,4 · L3 12 A») y, en un trifásico, su desequilibrio."""
    texto = checklists.texto_valor(it)
    if it.get("tipo") == "trifasica":
        d = checklists.desequilibrio(it.get("valor"))
        if d:
            texto += "\n" + _t("chk_desequilibrio").format(p=f"{d[0]:g}", fase=checklists.FASES[d[1]])
    return texto


def _resumen(items):
    r = checklists.recuento(items)
    partes = []
    for clave, n in (("chk_resumen_ok", r["ok"]), ("chk_resumen_mal", r["mal"]),
                     ("chk_resumen_na", r["na"]), ("chk_resumen_sin", r["sin"])):
        if n:
            partes.append(_t(clave).format(n=n))
    return " · ".join(partes)


def _cabecera(d):
    from .. import idiomas
    lineas = [f"{_t('hdr_fecha').capitalize()}: {idiomas.formato_fecha_localizada(d['fecha'][:10])}"]
    if d["maquina"]:
        lineas.append(f"{_t('lbl_lect_maquina')}: {d['maquina']}")
    if d["tecnico"]:
        lineas.append(f"{_t('hdr_tecnico')}: {d['tecnico']}")
    lineas.append(_resumen(d["items"]))
    return lineas


def generar_pdf(tarea_id, ruta, ruta_logo=None, items=None):
    """Escribe la lista rellenada del trabajo en un PDF (A4) en [ruta].
    Devuelve True, o False si el trabajo no tiene lista."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from xml.sax.saxutils import escape

    d = datos_trabajo(tarea_id, items)
    if not d:
        return False
    estilos = getSampleStyleSheet()
    celda = ParagraphStyle("CeldaChk", parent=estilos["BodyText"], fontSize=8.5, leading=10.5)
    celda_mal = ParagraphStyle("CeldaChkMal", parent=celda, textColor=colors.HexColor("#c0392b"), fontName="Helvetica-Bold")
    celda_cab = ParagraphStyle("CabChk", parent=celda, textColor=colors.whitesmoke, fontName="Helvetica-Bold")
    celda_sec = ParagraphStyle("SecChk", parent=celda, fontSize=10, leading=13, textColor=colors.HexColor("#1d5f86"))
    esc = lambda s: escape(str(s or "")).replace("\n", "<br/>")   # noqa: E731

    elementos = []
    if ruta_logo and os.path.exists(ruta_logo):
        try:
            logo = Image(ruta_logo, width=4 * cm, height=2 * cm)
            logo.hAlign = "LEFT"
            logo.keepAspectRatio = True
            elementos += [logo, Spacer(1, 6)]
        except Exception:
            pass
    elementos.append(Paragraph(esc(f"{_t('title_checklist')}: {d['plantilla']}"), estilos["Title"]))
    elementos.append(Paragraph(f"<b>{esc(d['titulo'])}</b>", estilos["Heading3"]))
    elementos += [Paragraph(esc(linea), estilos["Normal"]) for linea in _cabecera(d)]
    elementos.append(Spacer(1, 10))

    filas = [[Paragraph(esc(c), celda_cab) for c in
              ("#", _t("chk_col_punto"), _t("chk_col_resultado"), _t("chk_col_lectura"), _t("chk_col_nota"))]]
    secciones = []                      # filas de los separadores, para darles su estilo
    n = 0
    for it in d["items"]:
        if it.get("tipo") == checklists.SECCION:
            secciones.append(len(filas))
            filas.append([Paragraph(f"<b>{esc(it['texto'])}</b>", celda_sec), "", "", "", ""])
            continue
        n += 1
        i = n
        punto = it["texto"] + (f"\n({_t('chk_rango')}: {_rango(it)})" if _rango(it) else "")
        mal = it.get("estado") == "mal"
        filas.append([Paragraph(str(i), celda), Paragraph(esc(punto), celda),
                      Paragraph(esc(_estado(it.get("estado"))), celda_mal if mal else celda),
                      Paragraph(esc(_lectura(it)), celda_mal if checklists.fuera_de_rango(it, it.get("valor")) else celda),
                      Paragraph(esc(it.get("nota")), celda)])
    ancho = A4[0] - 3 * cm
    anchos = [0.8 * cm, 6.2 * cm, 2.2 * cm, 4.2 * cm]
    anchos.append(ancho - sum(anchos))
    tabla = Table(filas, colWidths=anchos, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3daee9")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
    ]
    for f in secciones:
        estilo += [("SPAN", (0, f), (-1, f)), ("BACKGROUND", (0, f), (-1, f), colors.HexColor("#d4ebf8"))]
    tabla.setStyle(TableStyle(estilo))
    elementos.append(tabla)
    SimpleDocTemplate(ruta, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.5 * cm,
                      bottomMargin=1.5 * cm, title=f"{_t('title_checklist')} - {d['titulo']}").build(elementos)
    return True


def generar_excel(tarea_id, ruta, items=None):
    """Escribe la lista rellenada del trabajo en un Excel en [ruta]. En los motores
    trifásicos, una columna por fase y otra con el desequilibrio, para poder operar
    con los números. Devuelve True, o False si el trabajo no tiene lista."""
    import re
    import xlsxwriter

    d = datos_trabajo(tarea_id, items)
    if not d:
        return False
    wb = xlsxwriter.Workbook(ruta)
    ws = wb.add_worksheet(re.sub(r"[\[\]:*?/\\]", "", _t("title_checklist"))[:31])
    f_tit = wb.add_format({"bold": True, "font_size": 14})
    f_cab = wb.add_format({"bold": True, "bg_color": "#3daee9", "color": "white", "border": 1, "align": "center",
                           "text_wrap": True})
    f_txt = wb.add_format({"border": 1, "text_wrap": True, "valign": "top"})
    f_sec = wb.add_format({"border": 1, "bold": True, "font_size": 11, "bg_color": "#d4ebf8", "font_color": "#1d5f86"})
    f_mal = wb.add_format({"border": 1, "text_wrap": True, "valign": "top", "font_color": "#c0392b", "bold": True})
    f_num = wb.add_format({"border": 1, "num_format": "0.###", "valign": "top"})
    f_num_mal = wb.add_format({"border": 1, "num_format": "0.###", "valign": "top", "font_color": "#c0392b", "bold": True})

    ws.write(0, 0, f"{_t('title_checklist')}: {d['plantilla']}", f_tit)
    ws.write(1, 0, d["titulo"])
    cab = _cabecera(d)
    for i, linea in enumerate(cab, start=2):
        ws.write(i, 0, linea)
    fila0 = len(cab) + 3
    cabeceras = ["#", _t("chk_col_punto"), _t("chk_col_resultado"), _t("chk_col_lectura"),
                 *checklists.FASES, _t("hdr_lect_desequilibrio"), _t("chk_rango").capitalize(), _t("chk_col_nota")]
    for c, txt in enumerate(cabeceras):
        ws.write(fila0, c, txt, f_cab)
    n = 0
    for f, it in enumerate(d["items"], start=fila0 + 1):
        if it.get("tipo") == checklists.SECCION:
            ws.merge_range(f, 0, f, 9, it["texto"], f_sec)
            continue
        n += 1
        mal = it.get("estado") == "mal"
        ws.write_number(f, 0, n, f_txt)
        ws.write(f, 1, it["texto"], f_txt)
        ws.write(f, 2, _estado(it.get("estado")), f_mal if mal else f_txt)
        ws.write(f, 3, checklists.texto_valor(it), f_mal if checklists.fuera_de_rango(it, it.get("valor")) else f_txt)
        if it.get("tipo") == "trifasica":
            rango = {"minimo": it.get("minimo"), "maximo": it.get("maximo")}
            for k, v in enumerate(checklists.fases(it.get("valor"))):
                n = checklists._num(v)
                if n is None:
                    ws.write(f, 4 + k, "", f_txt)
                else:
                    ws.write_number(f, 4 + k, n, f_num_mal if checklists.fuera_de_rango(rango, n) else f_num)
            de = checklists.desequilibrio(it.get("valor"))
            if de:
                ws.write_number(f, 7, de[0], f_num_mal if checklists.desequilibrio_excesivo(it, it.get("valor")) else f_num)
            else:
                ws.write(f, 7, "", f_txt)
        else:
            for c in range(4, 8):
                ws.write(f, c, "", f_txt)
        ws.write(f, 8, _rango(it), f_txt)
        ws.write(f, 9, it.get("nota") or "", f_txt)
    ws.set_column(0, 0, 4); ws.set_column(1, 1, 40); ws.set_column(2, 2, 12); ws.set_column(3, 3, 26)
    ws.set_column(4, 7, 9); ws.set_column(8, 8, 22); ws.set_column(9, 9, 40)
    ws.freeze_panes(fila0 + 1, 0)
    wb.close()
    return True
