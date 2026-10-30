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

"""Estadísticas por técnico: trabajos de cada persona por año y mes, averías,
preventivos, horas de parada y pendientes asignados (se abre desde el Dashboard)."""

import os
import re
import tempfile
from datetime import datetime

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..widgets.graficos import GraficoBarrasRanking
from ...nucleo import estadisticas, usuarios
from ...nucleo.rutas import DATA_DIR


class _ItemNumero(QTableWidgetItem):
    """Celda numérica que ordena por su valor, no como texto."""
    def __init__(self, valor, texto=None):
        super().__init__(texto if texto is not None else str(valor))
        self._valor = valor
        self.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def __lt__(self, otro):
        return self._valor < otro._valor if isinstance(otro, _ItemNumero) else super().__lt__(otro)


class DialogoEstadisticasTecnicos(QDialog):
    def __init__(self, parent, ruta_db):
        super().__init__(parent)
        self.ruta_db = ruta_db
        self.setWindowTitle(tt("title_estadisticas_tecnicos", "Estadísticas por técnico"))
        self.resize(1320, 640)
        l = QVBoxLayout(self)

        barra = QHBoxLayout()
        barra.addWidget(QLabel(tt("lbl_anio_grafico", "Año:")))
        self.combo_anio = QComboBox()
        self.combo_anio.addItem(tt("opcion_todos_los_anios", "TODOS"), None)
        for anio in estadisticas.anios_disponibles(ruta_db):
            self.combo_anio.addItem(str(anio), anio)
        if self.combo_anio.count() > 1:
            self.combo_anio.setCurrentIndex(1)  # el año más reciente
        self.combo_anio.currentIndexChanged.connect(self._cargar)
        barra.addWidget(self.combo_anio)
        barra.addSpacing(16)
        barra.addWidget(QLabel(tt("hdr_tipo_historial", "Tipo") + ":"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem(tt("filtro_todos", "Todos"), None)
        self.combo_tipo.addItem(tt("filtro_trabajos_averias", "Trabajos y averías"), "trabajos")
        self.combo_tipo.addItem(tt("filtro_mantenimiento_preventivo", "Mantenimiento preventivo"), "preventivos")
        self.combo_tipo.currentIndexChanged.connect(self._cargar)
        barra.addWidget(self.combo_tipo); barra.addStretch()
        l.addLayout(barra)

        l.addWidget(QLabel(tt("lbl_trabajos_por_tecnico", "Trabajos por técnico")))
        self.grafico = GraficoBarrasRanking(color="#3daee9")
        l.addWidget(self.grafico)

        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSortingEnabled(True)
        l.addWidget(self.tabla, 1)
        self.lbl_nota = QLabel(tt("msg_nota_estadisticas_tecnicos", "Las horas de parada son las de los trabajos de avería. «Pendientes» son los trabajos que cada técnico tiene asignados ahora mismo."))
        self.lbl_nota.setWordWrap(True); self.lbl_nota.setStyleSheet("color: gray;")
        l.addWidget(self.lbl_nota)

        pie = QHBoxLayout()
        btn_pdf = QPushButton(tt("btn_exportar_pdf_corto", "📄 Exportar PDF")); btn_pdf.clicked.connect(lambda: self._exportar("pdf"))
        btn_excel = QPushButton(tt("btn_exportar_excel_corto", "📊 Exportar Excel")); btn_excel.clicked.connect(lambda: self._exportar("xlsx"))
        pie.addWidget(btn_pdf); pie.addWidget(btn_excel); pie.addStretch()
        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept); pie.addWidget(btn_cerrar)
        l.addLayout(pie)
        self._cargar()

    def _cargar(self):
        anio = self.combo_anio.currentData()
        tipo = self.combo_tipo.currentData()
        datos = estadisticas.por_tecnico(self.ruta_db, anio, tipo)
        for d in datos:
            if d["nombre"] == usuarios.ETIQUETA_HISTORICO:
                d["nombre"] = tt("lbl_tecnico_historico", "Histórico (sin usuario)")
        self._datos, self._anio, self._tipo = datos, anio, tipo
        self.grafico.establecer_datos([(d["nombre"], d["total"]) for d in datos if d["total"]])

        meses = [t(f"mes_{m:02d}_corto") for m in range(1, 13)] if anio else []
        # Primero los totales (lo que más se mira) y después los meses, que en
        # pantallas estrechas pueden quedar a la derecha con desplazamiento.
        # Las columnas que no aportan nada con el tipo elegido no se muestran
        # (en preventivos todo es preventivo y no hay averías ni pendientes; en
        # trabajos no hay preventivos).
        self._columnas = [] if tipo == "preventivos" else [
            c for c in ("averias", "preventivos", "horas_paro", "pendientes") if not (tipo == "trabajos" and c == "preventivos")]
        self.lbl_nota.setVisible(bool(self._columnas))
        nombres_col = {"averias": tt("hdr_averias", "Averías"), "preventivos": tt("hdr_preventivos", "Preventivos"),
                       "horas_paro": tt("hdr_horas_paro", "Horas de parada"), "pendientes": tt("hdr_pendientes_asignados", "Pendientes")}
        cabeceras = ([tt("hdr_tecnico", "Técnico"), tt("hdr_total", "Total")]
                     + [nombres_col[c] for c in self._columnas] + meses)
        self.tabla.setSortingEnabled(False)
        self.tabla.clear()
        self.tabla.setColumnCount(len(cabeceras)); self.tabla.setHorizontalHeaderLabels(cabeceras)
        self.tabla.setRowCount(len(datos))
        for i, d in enumerate(datos):
            celdas = [QTableWidgetItem(d["nombre"]), _ItemNumero(d["total"])]
            celdas += [_ItemNumero(d[c], f"{d[c]:g}") for c in self._columnas]
            if anio:
                celdas += [_ItemNumero(n, str(n) if n else "·") for n in d["meses"]]
            for j, item in enumerate(celdas):
                if j == 1:
                    fuente = item.font(); fuente.setBold(True); item.setFont(fuente)
                self.tabla.setItem(i, j, item)
        self.tabla.setSortingEnabled(True)
        # Todas las columnas a su contenido (el nombre completo del técnico incluido).
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cab.setStretchLastSection(False)

    # ------------------------------------------------------------ exportar

    def _cabeceras_y_filas(self):
        """Cabeceras y filas tal y como se ven en la tabla (mismo orden de
        columnas), con números de verdad para que Excel pueda sumarlos."""
        cabeceras = [self.tabla.horizontalHeaderItem(c).text() for c in range(self.tabla.columnCount())]
        filas = []
        for d in self._datos:
            fila = [d["nombre"], d["total"]] + [d[c] for c in self._columnas]
            if self._anio:
                fila += d["meses"]
            filas.append(fila)
        return cabeceras, filas

    def _exportar(self, formato):
        if not self._datos:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_datos_estadisticas", "No hay trabajos que exportar en ese periodo."))
            return
        if formato == "xlsx":
            try: import xlsxwriter  # noqa: F401
            except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        periodo = str(self._anio) if self._anio else tt("lbl_todos_los_anos", "Todos los años")
        titulo = f"{tt('title_estadisticas_tecnicos', 'Estadísticas por técnico')} — {periodo}"
        if self._tipo:
            titulo += f" — {self.combo_tipo.currentText()}"
        base = re.sub(r"[^\w-]+", "_", tt("title_estadisticas_tecnicos", "Estadísticas por técnico")).strip("_")
        sufijo_tipo = "_" + re.sub(r"[^\w-]+", "_", self.combo_tipo.currentText()).strip("_") if self._tipo else ""
        nombre_defecto = f"{base}_{self._anio or re.sub(r'[^\w-]+', '_', periodo)}{sufijo_tipo}.{formato}"
        filtro = "PDF (*.pdf)" if formato == "pdf" else "Excel (*.xlsx)"
        titulo_dlg = t("title_exportar_pdf") if formato == "pdf" else t("title_exportar_excel")
        guardar = getattr(self.parent(), "guardar_archivo_dialogo", None)
        if guardar:
            archivo = guardar(titulo_dlg, nombre_defecto, filtro)
        else:
            from PyQt6.QtWidgets import QFileDialog
            archivo, _ = QFileDialog.getSaveFileName(self, titulo_dlg, nombre_defecto, filtro)
        if not archivo: return
        if not archivo.lower().endswith("." + formato): archivo += "." + formato
        fecha = tt("txt_fecha_informe", "Fecha: {fecha}").format(
            fecha=idiomas.formato_fecha_localizada(datetime.now().strftime("%Y-%m-%d")))
        try:
            if formato == "pdf":
                self._a_pdf(archivo, titulo, fecha)
            else:
                self._a_excel(archivo, titulo, fecha)
            QMessageBox.information(self, t("title_exportado"),
                tt("msg_estadisticas_exportadas", "Estadísticas exportadas en:\n{ruta}").format(ruta=archivo))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))

    def _a_excel(self, archivo, titulo, fecha):
        import xlsxwriter
        cabeceras, filas = self._cabeceras_y_filas()
        wb = xlsxwriter.Workbook(archivo)
        ws = wb.add_worksheet(re.sub(r"[\[\]:*?/\\]", "", tt("title_estadisticas_tecnicos", "Estadísticas por técnico"))[:31])
        f_tit = wb.add_format({"bold": True, "font_size": 14})
        f_nota = wb.add_format({"italic": True, "font_color": "#7f8c8d"})
        f_cab = wb.add_format({"bold": True, "bg_color": "#3daee9", "color": "white", "border": 1, "align": "center", "valign": "vcenter"})
        f_txt = wb.add_format({"border": 1})
        f_num = wb.add_format({"border": 1, "num_format": "0.##", "align": "right"})
        f_total = wb.add_format({"border": 1, "num_format": "0.##", "align": "right", "bold": True})
        ws.write(0, 0, titulo, f_tit)
        ws.write(1, 0, fecha)
        if self._columnas:
            ws.write(2, 0, self.lbl_nota.text(), f_nota)
        fila0 = 4
        for c, txt in enumerate(cabeceras): ws.write(fila0, c, txt, f_cab)
        for i, fila in enumerate(filas, start=fila0 + 1):
            ws.write(i, 0, fila[0], f_txt)
            for c, valor in enumerate(fila[1:], start=1):
                ws.write_number(i, c, valor, f_total if c == 1 else f_num)
        ws.set_column(0, 0, max(14, max(len(f[0]) for f in filas) + 2))
        fijas = 2 + len(self._columnas)
        ws.set_column(1, fijas - 1, 13)
        if len(cabeceras) > fijas: ws.set_column(fijas, len(cabeceras) - 1, 6)
        ws.freeze_panes(fila0 + 1, 1)
        ws.autofilter(fila0, 0, fila0 + len(filas), len(cabeceras) - 1)
        wb.close()

    def _a_pdf(self, archivo, titulo, fecha):
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as PDFImage
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        cabeceras, filas = self._cabeceras_y_filas()
        # Con los meses la tabla tiene 18 columnas: en apaisado caben bien.
        pagina = landscape(A4) if self._anio else A4
        doc = SimpleDocTemplate(archivo, pagesize=pagina, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        celda = ParagraphStyle("CeldaEst", parent=styles["BodyText"], fontSize=8, leading=10)
        celda_cab = ParagraphStyle("CabEst", parent=celda, textColor=colors.whitesmoke, fontName="Helvetica-Bold", alignment=1)
        nota = ParagraphStyle("NotaEst", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
        esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        elementos = []
        ruta_logo = os.path.join(DATA_DIR, "Logo.jpg")
        if os.path.exists(ruta_logo):
            try:
                logo = PDFImage(ruta_logo, width=4*cm, height=2*cm); logo.hAlign = "LEFT"; logo.keepAspectRatio = True
                elementos += [logo, Spacer(1, 8)]
            except Exception: pass
        elementos += [Paragraph(esc(titulo), styles["Title"]), Paragraph(esc(fecha), styles["Normal"]), Spacer(1, 8)]

        # Gráfico de barras (el mismo de la ventana, con texto negro sobre fondo claro).
        ancho_util = pagina[0] - 60
        tmp = tempfile.mkdtemp(prefix="mantpro_estadisticas_")
        try:
            con_trabajos = [(f[0], f[1]) for f in filas if f[1]]
            if con_trabajos:
                grafico = GraficoBarrasRanking(color="#3daee9", color_texto="#000000", color_fondo="#f0f0f0")
                grafico.establecer_datos(con_trabajos)
                alto_px = max(120, 30 * len(con_trabajos) + 20)
                grafico.resize(900, alto_px)
                png = os.path.join(tmp, "grafico.png"); grafico.grab().save(png, "PNG")
                img = PDFImage(png, width=ancho_util, height=ancho_util * alto_px / 900)
                elementos += [img, Spacer(1, 10)]

            fijas = 2 + len(self._columnas)

            def num(v):
                return f"{v:g}" if v else "·"
            datos = [[Paragraph(esc(c), celda_cab) for c in cabeceras]]
            for f in filas:
                datos.append([Paragraph(esc(f[0]), celda), f"{f[1]:g}"] + [num(v) if i >= fijas else f"{v:g}" for i, v in enumerate(f[2:], start=2)])
            ancho_nombre = 5.5*cm if self._anio else 6*cm
            resto = (ancho_util - ancho_nombre)
            if self._anio:
                # Las columnas de totales no necesitan más de 2,6 cm; el resto, para los meses.
                ancho_fija = min(2.6*cm, resto * 0.55 / (fijas - 1))
                anchos = [ancho_nombre] + [ancho_fija] * (fijas - 1) + [(resto - ancho_fija * (fijas - 1)) / 12] * 12
            else:
                anchos = [ancho_nombre] + [resto / (fijas - 1)] * (fijas - 1)
            tabla = Table(datos, colWidths=anchos, repeatRows=1)
            tabla.setStyle(TableStyle([
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
            elementos.append(tabla)
            if self._columnas:
                elementos += [Spacer(1, 8), Paragraph(esc(self.lbl_nota.text()), nota)]
            doc.build(elementos)
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
