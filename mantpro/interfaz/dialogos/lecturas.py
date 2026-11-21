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

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..widgets.graficos import GraficoEvolucion
from ...nucleo import informe_lecturas, maquinas

# Los textos y el informe los hace el núcleo (nucleo/informe_lecturas.py), igual que MantPro Web
from ...nucleo.informe_lecturas import (ROJO, nombre_punto, series_de, texto_rango, texto_rango_punto,  # noqa: E402
                                        texto_valor_lectura)

__all__ = ["DialogoLecturasChecklist", "nombre_punto", "texto_rango", "texto_rango_punto", "texto_valor_lectura"]


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
        self._puntos = informe_lecturas.puntos(self.maquina_id, self.combo_maquina.currentData())
        self.combo_punto.blockSignals(True)
        self.combo_punto.clear()
        for p in self._puntos:
            self.combo_punto.addItem(p["nombre"])
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
        self.grafico.establecer_datos(lecturas, p["minimo"], p["maximo"], p["unidad"], series_de(p))
        self.lbl_resumen.setText(informe_lecturas.resumen(p))
        lista = informe_lecturas.filas(p)
        self.tabla.setRowCount(len(lista))
        for fila, f in enumerate(reversed(lista)):           # la más reciente arriba
            valores = (f["fecha"], f["maquina"], f["valor"], f["rango"], f["tecnico"], f["nota"])
            for col, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, f["tarea_id"])
                if col == 2 and f["fuera"]:
                    item.setForeground(QColor(ROJO))
                self.tabla.setItem(fila, col, item)

    def _abrir_trabajo(self, item):
        tarea_id = self.tabla.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        abrir = getattr(self.parent(), "proc_edit", None)
        if tarea_id is not None and abrir:
            abrir(tarea_id)
            self._cargar()

    # ------------------------------------------------------------------ exportar
    def _exportar(self, formato):
        p = self.punto()
        if p is None:
            return
        if formato == "xlsx":
            try: import xlsxwriter  # noqa: F401
            except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        nombre = informe_lecturas.nombre_fichero(self.combo_maquina.currentText(), p, formato)
        filtro = "PDF (*.pdf)" if formato == "pdf" else "Excel (*.xlsx)"
        titulo_dlg = t("title_exportar_pdf") if formato == "pdf" else t("title_exportar_excel")
        guardar = getattr(self.parent(), "guardar_archivo_dialogo", None)
        if guardar:
            archivo = guardar(titulo_dlg, nombre, filtro)
        else:
            from PyQt6.QtWidgets import QFileDialog
            archivo, _ = QFileDialog.getSaveFileName(self, titulo_dlg, nombre, filtro)
        if not archivo:
            return
        if not archivo.lower().endswith("." + formato):
            archivo += "." + formato
        try:
            informe_lecturas.generar(archivo, p, self.combo_maquina.currentText(), formato)
            QMessageBox.information(self, t("title_exportado"),
                                    tt("msg_lect_exportado", "Lecturas exportadas en:\n{ruta}").format(ruta=archivo))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))

    def a_excel(self, archivo, p):
        informe_lecturas.excel(archivo, p, self.combo_maquina.currentText())

    def a_pdf(self, archivo, p):
        informe_lecturas.pdf(archivo, p, self.combo_maquina.currentText())
