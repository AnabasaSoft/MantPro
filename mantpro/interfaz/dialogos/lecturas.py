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

"""Máquinas → 📈 Lecturas: cómo evolucionan las medidas de las listas de comprobación
(resistencia de tierra, aislamiento, tiempo de disparo…) de una máquina y sus submáquinas,
revisión a revisión, con su rango correcto. Gráfico y tabla, y exportación a PDF y Excel."""

import os
import re
import tempfile
from datetime import date, datetime

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..widgets.graficos import GraficoEvolucion
from ...nucleo import checklists, maquinas
from ...nucleo.rutas import DATA_DIR

ROJO = "#e74c3c"


def texto_rango(minimo, maximo, unidad=""):
    """«10 – 20 Ω», «≥ 1 MΩ», «≤ 20 Ω» o «Sin rango»."""
    u = f" {unidad}" if unidad else ""
    n = lambda v: f"{v:g}"                                       # noqa: E731
    if minimo is not None and maximo is not None:
        return f"{n(minimo)} – {n(maximo)}{u}"
    if minimo is not None:
        return f"≥ {n(minimo)}{u}"
    if maximo is not None:
        return f"≤ {n(maximo)}{u}"
    return tt("lbl_lect_sin_rango", "Sin rango")


def nombre_punto(p):
    return f"{p['texto']} ({p['unidad']})" if p["unidad"] else p["texto"]


class DialogoLecturasChecklist(QDialog):
    def __init__(self, parent, maquina_id, nombre_maquina):
        super().__init__(parent)
        self.maquina_id = maquina_id
        self.nombre_maquina = nombre_maquina
        self.setWindowTitle(tt("title_lecturas_checklist", "📈 Lecturas de {maquina}").format(maquina=nombre_maquina))
        self.resize(900, 640)
        self._rutas = maquinas.mapa_rutas_completas()
        self._ids = maquinas.descendientes_ids(maquina_id)
        self._puntos = []
        v = QVBoxLayout(self)

        fila = QHBoxLayout()
        fila.addWidget(QLabel(tt("lbl_lect_maquina", "Máquina") + ":"))
        self.combo_maquina = QComboBox()
        if len(self._ids) > 1:
            self.combo_maquina.addItem(tt("lbl_lect_todas", "Todas (con submáquinas)"), None)
        for i in sorted(self._ids, key=lambda i: self._rutas.get(i, "").casefold()):
            self.combo_maquina.addItem(self._rutas.get(i, str(i)), i)
        fila.addWidget(self.combo_maquina, 1)
        fila.addWidget(QLabel(tt("lbl_lect_punto", "Medida") + ":"))
        self.combo_punto = QComboBox()
        fila.addWidget(self.combo_punto, 2)
        v.addLayout(fila)

        self.lbl_resumen = QLabel()
        self.lbl_resumen.setWordWrap(True)
        v.addWidget(self.lbl_resumen)
        self.grafico = GraficoEvolucion(formato_fecha=idiomas.formato_fecha_localizada)
        v.addWidget(self.grafico, 3)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels([t("hdr_fecha"), tt("hdr_maquina", "Máquina").upper(), tt("hdr_lect_valor", "VALOR"),
                                              tt("hdr_lect_rango", "RANGO"), tt("hdr_tecnico", "Técnico").upper(), tt("hdr_lect_nota", "NOTA")])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setToolTip(tt("tt_lect_doble_clic", "Doble clic: abrir el trabajo de esa revisión."))
        self.tabla.itemDoubleClicked.connect(self._abrir_trabajo)
        v.addWidget(self.tabla, 2)

        self.lbl_vacio = QLabel(tt("msg_lect_sin_lecturas",
            "No hay lecturas guardadas. Salen de las listas de comprobación con puntos de tipo «Lectura» "
            "al completar los trabajos de esta máquina."))
        self.lbl_vacio.setWordWrap(True)
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.lbl_vacio)

        pie = QHBoxLayout()
        self.btn_pdf = QPushButton(tt("btn_exportar_pdf_corto", "📄 Exportar PDF")); self.btn_pdf.clicked.connect(lambda: self._exportar("pdf"))
        self.btn_excel = QPushButton(tt("btn_exportar_excel_corto", "📊 Exportar Excel")); self.btn_excel.clicked.connect(lambda: self._exportar("xlsx"))
        pie.addWidget(self.btn_pdf); pie.addWidget(self.btn_excel); pie.addStretch()
        b = QPushButton(t("btn_cerrar")); b.clicked.connect(self.accept); pie.addWidget(b)
        v.addLayout(pie)

        self.combo_maquina.currentIndexChanged.connect(lambda _i: self._cargar())
        self.combo_punto.currentIndexChanged.connect(lambda _i: self._pintar())
        self._cargar()

    # ------------------------------------------------------------------ datos
    def _ids_elegidos(self):
        elegida = self.combo_maquina.currentData()
        return self._ids if elegida is None else [elegida]

    def _cargar(self):
        anterior = self.combo_punto.currentText()
        self._puntos = checklists.evolucion_lecturas(self._ids_elegidos())
        self.combo_punto.blockSignals(True)
        self.combo_punto.clear()
        for p in self._puntos:
            self.combo_punto.addItem(f"{nombre_punto(p)} · {len(p['lecturas'])}")
        i = next((k for k, p in enumerate(self._puntos) if self.combo_punto.itemText(k) == anterior), 0)
        self.combo_punto.setCurrentIndex(i if self._puntos else -1)
        self.combo_punto.blockSignals(False)
        self._pintar()

    def punto(self):
        i = self.combo_punto.currentIndex()
        return self._puntos[i] if 0 <= i < len(self._puntos) else None

    def _pintar(self):
        p = self.punto()
        hay = p is not None
        for w in (self.grafico, self.tabla, self.lbl_resumen, self.btn_pdf, self.btn_excel):
            w.setVisible(hay) if w in (self.grafico, self.tabla, self.lbl_resumen) else w.setEnabled(hay)
        self.lbl_vacio.setVisible(not hay)
        self.combo_punto.setEnabled(hay)
        if not hay:
            self.tabla.setRowCount(0)
            return
        lecturas = p["lecturas"]
        self.grafico.establecer_datos(lecturas, p["minimo"], p["maximo"], p["unidad"])
        fuera = sum(1 for l in lecturas if l["fuera"])
        ultima = lecturas[-1]
        self.lbl_resumen.setText(tt("lbl_lect_resumen", "{n} lecturas · {fuera} fuera de rango · rango correcto: {rango} · última: {ultima} ({fecha})").format(
            n=len(lecturas), fuera=fuera, rango=texto_rango(p["minimo"], p["maximo"], p["unidad"]),
            ultima=f"{ultima['valor_texto']} {p['unidad']}".strip(), fecha=idiomas.formato_fecha_localizada(ultima["fecha"])))
        self.tabla.setRowCount(len(lecturas))
        for fila, l in enumerate(reversed(lecturas)):           # la más reciente arriba
            valores = (idiomas.formato_fecha_localizada(l["fecha"]), self._rutas.get(l["maquina_id"], ""),
                       f"{l['valor_texto']} {p['unidad']}".strip(), texto_rango(l["minimo"], l["maximo"], p["unidad"]),
                       l["tecnico"], l["nota"])
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, l["tarea_id"])
                if col == 2 and l["fuera"]:
                    item.setForeground(QColor(ROJO))
                self.tabla.setItem(fila, col, item)

    def _abrir_trabajo(self, item):
        tarea_id = self.tabla.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        abrir = getattr(self.parent(), "proc_edit", None)
        if tarea_id is not None and abrir:
            abrir(tarea_id)
            self._cargar()

    # ------------------------------------------------------------------ exportar
    def _filas(self, p):
        """Filas de la tabla en orden cronológico (para el PDF y el Excel)."""
        return [(l, idiomas.formato_fecha_localizada(l["fecha"]), self._rutas.get(l["maquina_id"], ""),
                 texto_rango(l["minimo"], l["maximo"], p["unidad"])) for l in p["lecturas"]]

    def _exportar(self, formato):
        p = self.punto()
        if p is None:
            return
        if formato == "xlsx":
            try: import xlsxwriter  # noqa: F401
            except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        titulo = tt("title_lect_informe", "Evolución de lecturas")
        base = re.sub(r"[^\w-]+", "_", f"{titulo}_{self.combo_maquina.currentText()}_{p['texto']}").strip("_")[:120]
        filtro = "PDF (*.pdf)" if formato == "pdf" else "Excel (*.xlsx)"
        titulo_dlg = t("title_exportar_pdf") if formato == "pdf" else t("title_exportar_excel")
        guardar = getattr(self.parent(), "guardar_archivo_dialogo", None)
        if guardar:
            archivo = guardar(titulo_dlg, f"{base}.{formato}", filtro)
        else:
            from PyQt6.QtWidgets import QFileDialog
            archivo, _ = QFileDialog.getSaveFileName(self, titulo_dlg, f"{base}.{formato}", filtro)
        if not archivo:
            return
        if not archivo.lower().endswith("." + formato):
            archivo += "." + formato
        try:
            if formato == "pdf":
                self.a_pdf(archivo, p)
            else:
                self.a_excel(archivo, p)
            QMessageBox.information(self, t("title_exportado"),
                                    tt("msg_lect_exportado", "Lecturas exportadas en:\n{ruta}").format(ruta=archivo))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))

    def _cabecera_informe(self, p):
        return [tt("title_lect_informe", "Evolución de lecturas"),
                f"{tt('lbl_lect_maquina', 'Máquina')}: {self.combo_maquina.currentText()}",
                f"{tt('lbl_lect_punto', 'Medida')}: {nombre_punto(p)}",
                f"{tt('lbl_lect_rango', 'Rango correcto')}: {texto_rango(p['minimo'], p['maximo'], p['unidad'])}",
                tt("txt_fecha_informe", "Fecha: {fecha}").format(fecha=idiomas.formato_fecha_localizada(datetime.now().strftime("%Y-%m-%d")))]

    def a_excel(self, archivo, p):
        import xlsxwriter
        wb = xlsxwriter.Workbook(archivo)
        ws = wb.add_worksheet(re.sub(r"[\[\]:*?/\\]", "", tt("title_lect_informe", "Evolución de lecturas"))[:31])
        f_tit = wb.add_format({"bold": True, "font_size": 14})
        f_cab = wb.add_format({"bold": True, "bg_color": "#3daee9", "color": "white", "border": 1, "align": "center"})
        f_txt = wb.add_format({"border": 1})
        f_fecha = wb.add_format({"border": 1, "num_format": idiomas.formato_fecha_excel()})
        f_num = wb.add_format({"border": 1, "num_format": "0.###"})
        f_mal = wb.add_format({"border": 1, "num_format": "0.###", "font_color": ROJO, "bold": True})
        cab = self._cabecera_informe(p)
        ws.write(0, 0, cab[0], f_tit)
        for i, linea in enumerate(cab[1:], start=1):
            ws.write(i, 0, linea)
        fila0 = len(cab) + 1
        cabeceras = [t("hdr_fecha"), tt("hdr_maquina", "Máquina").upper(), tt("hdr_lect_valor", "VALOR"),
                     tt("hdr_lect_unidad", "UNIDAD"), tt("hdr_lect_rango", "RANGO"), tt("hdr_lect_estado", "ESTADO"),
                     tt("hdr_tecnico", "Técnico").upper(), tt("hdr_lect_nota", "NOTA")]
        for c, txt in enumerate(cabeceras):
            ws.write(fila0, c, txt, f_cab)
        filas = self._filas(p)
        for i, (l, _fecha, maquina, rango) in enumerate(filas, start=fila0 + 1):
            try:
                ws.write_datetime(i, 0, datetime.combine(date.fromisoformat(l["fecha"]), datetime.min.time()), f_fecha)
            except ValueError:
                ws.write(i, 0, l["fecha"], f_txt)
            ws.write(i, 1, maquina, f_txt)
            if l["valor"] is not None:
                ws.write_number(i, 2, l["valor"], f_mal if l["fuera"] else f_num)
            else:
                ws.write(i, 2, l["valor_texto"], f_txt)
            ws.write(i, 3, p["unidad"], f_txt)
            ws.write(i, 4, rango, f_txt)
            ws.write(i, 5, tt("lbl_lect_fuera", "Fuera de rango") if l["fuera"] else tt("lbl_lect_correcta", "Correcta"), f_txt)
            ws.write(i, 6, l["tecnico"], f_txt)
            ws.write(i, 7, l["nota"], f_txt)
        ultima = fila0 + len(filas)
        ws.set_column(0, 0, 12); ws.set_column(1, 1, 28); ws.set_column(2, 3, 10); ws.set_column(4, 5, 16); ws.set_column(6, 6, 18); ws.set_column(7, 7, 40)
        ws.freeze_panes(fila0 + 1, 0)
        if filas:
            grafico = wb.add_chart({"type": "line"})
            grafico.add_series({"name": nombre_punto(p), "categories": [ws.name, fila0 + 1, 0, ultima, 0],
                                "values": [ws.name, fila0 + 1, 2, ultima, 2], "marker": {"type": "circle"}})
            grafico.set_title({"name": nombre_punto(p)})
            grafico.set_legend({"none": True})
            grafico.set_x_axis({"date_axis": True, "num_format": idiomas.formato_fecha_excel(corta=True)})
            ws.insert_chart(ultima + 2, 0, grafico, {"x_scale": 1.6, "y_scale": 1.2})
        wb.close()

    def a_pdf(self, archivo, p):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage

        doc = SimpleDocTemplate(archivo, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        celda = ParagraphStyle("CeldaLect", parent=styles["BodyText"], fontSize=8, leading=10)
        celda_mal = ParagraphStyle("CeldaLectMal", parent=celda, textColor=colors.HexColor(ROJO), fontName="Helvetica-Bold")
        celda_cab = ParagraphStyle("CabLect", parent=celda, textColor=colors.whitesmoke, fontName="Helvetica-Bold")
        esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")   # noqa: E731
        elementos = []
        ruta_logo = os.path.join(DATA_DIR, "Logo.jpg")
        if os.path.exists(ruta_logo):
            try:
                logo = PDFImage(ruta_logo, width=4*cm, height=2*cm); logo.hAlign = "LEFT"; logo.keepAspectRatio = True
                elementos += [logo, Spacer(1, 8)]
            except Exception:
                pass
        cab = self._cabecera_informe(p)
        elementos.append(Paragraph(esc(cab[0]), styles["Title"]))
        elementos += [Paragraph(esc(linea), styles["Normal"]) for linea in cab[1:]]
        elementos.append(Spacer(1, 10))
        ancho_util = A4[0] - 60
        tmp = tempfile.mkdtemp(prefix="mantpro_lecturas_")
        try:
            grafico = GraficoEvolucion(color_texto="#000000", color_fondo="#ffffff", formato_fecha=idiomas.formato_fecha_localizada)
            grafico.establecer_datos(p["lecturas"], p["minimo"], p["maximo"], p["unidad"])
            grafico.resize(900, 340)
            png = os.path.join(tmp, "grafico.png")
            grafico.grab().save(png, "PNG")
            elementos += [PDFImage(png, width=ancho_util, height=ancho_util * 340 / 900), Spacer(1, 10)]
            datos = [[Paragraph(esc(c), celda_cab) for c in (t("hdr_fecha"), tt("hdr_maquina", "Máquina").upper(), tt("hdr_lect_valor", "VALOR"),
                                                             tt("hdr_lect_rango", "RANGO"), tt("hdr_tecnico", "Técnico").upper(), tt("hdr_lect_nota", "NOTA"))]]
            for l, fecha, maquina, rango in reversed(self._filas(p)):
                valor = f"{l['valor_texto']} {p['unidad']}".strip()
                datos.append([Paragraph(esc(fecha), celda), Paragraph(esc(maquina), celda),
                              Paragraph(esc(valor), celda_mal if l["fuera"] else celda), Paragraph(esc(rango), celda),
                              Paragraph(esc(l["tecnico"]), celda), Paragraph(esc(l["nota"]), celda)])
            anchos = [2.2*cm, 4.5*cm, 2.4*cm, 2.8*cm, 3*cm]
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
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
