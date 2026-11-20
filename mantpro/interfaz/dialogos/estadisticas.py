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

"""Estadísticas por técnico: trabajos de cada persona por año y mes, averías,
preventivos, horas de parada y pendientes asignados (se abre desde el Dashboard)."""

import os
import tempfile

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ..widgets.graficos import GraficoBarrasRanking
from ...nucleo import estadisticas, informe_estadisticas
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
        # Solo la sede elegida en la ventana principal (None = todas)
        self.sede = parent.sede_filtro() if hasattr(parent, "sede_filtro") else None
        self.setWindowTitle(tt("title_estadisticas_tecnicos", "Estadísticas por técnico"))
        self.resize(1320, 640)
        l = QVBoxLayout(self)

        barra = QHBoxLayout()
        barra.addWidget(QLabel(tt("lbl_anio_grafico", "Año:")))
        self.combo_anio = QComboBox()
        self.combo_anio.addItem(tt("opcion_todos_los_anios", "TODOS"), None)
        for anio in estadisticas.anios_disponibles(ruta_db, self.sede):
            self.combo_anio.addItem(str(anio), anio)
        if self.combo_anio.count() > 1:
            self.combo_anio.setCurrentIndex(1)  # el año más reciente
        self.combo_anio.currentIndexChanged.connect(self._cargar)
        barra.addWidget(self.combo_anio)
        barra.addSpacing(16)
        barra.addWidget(QLabel(tt("hdr_tipo_historial", "Tipo") + ":"))
        self.combo_tipo = QComboBox()
        for tipo in informe_estadisticas.TIPOS:
            self.combo_tipo.addItem(informe_estadisticas.nombre_tipo(tipo), tipo)
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
        self.lbl_nota = QLabel(informe_estadisticas.texto_nota())
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
        # La tabla (columnas según el tipo, cabeceras y filas) sale del núcleo, la misma que usa MantPro Web
        self._tabla = tab = informe_estadisticas.tabla(self.ruta_db, self.combo_anio.currentData(),
                                                        self.combo_tipo.currentData(), self.sede)
        self.grafico.establecer_datos(informe_estadisticas.grafico(tab))
        self.lbl_nota.setVisible(tab["con_nota"])
        fijas = 2 + len(tab["columnas"])
        self.tabla.setSortingEnabled(False)
        self.tabla.clear()
        self.tabla.setColumnCount(len(tab["cabeceras"])); self.tabla.setHorizontalHeaderLabels(tab["cabeceras"])
        self.tabla.setRowCount(len(tab["filas"]))
        for i, fila in enumerate(tab["filas"]):
            celdas = [QTableWidgetItem(fila[0]), _ItemNumero(fila[1])]
            celdas += [_ItemNumero(v, f"{v:g}") for v in fila[2:fijas]]
            celdas += [_ItemNumero(n, str(n) if n else "·") for n in fila[fijas:]]
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
        """Cabeceras y filas tal y como se ven en la tabla, con números de verdad para que Excel pueda sumarlos."""
        return self._tabla["cabeceras"], self._tabla["filas"]

    def _exportar(self, formato):
        tab = self._tabla
        if not tab["filas"]:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_datos_estadisticas", "No hay trabajos que exportar en ese periodo."))
            return
        if formato == "xlsx":
            try: import xlsxwriter  # noqa: F401
            except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        nombre_defecto = informe_estadisticas.nombre_fichero(tab, formato)
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
        try:
            if formato == "pdf":
                self._a_pdf(archivo)
            else:
                informe_estadisticas.generar_excel(tab, archivo)
            QMessageBox.information(self, t("title_exportado"),
                tt("msg_estadisticas_exportadas", "Estadísticas exportadas en:\n{ruta}").format(ruta=archivo))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))

    def _a_pdf(self, archivo):
        # El gráfico, el mismo de la ventana (con texto negro sobre fondo claro); el resto lo hace el núcleo
        tmp = tempfile.mkdtemp(prefix="mantpro_estadisticas_")
        try:
            png = None
            pares = informe_estadisticas.grafico(self._tabla)
            if pares:
                grafico = GraficoBarrasRanking(color="#3daee9", color_texto="#000000", color_fondo="#f0f0f0")
                grafico.establecer_datos(pares)
                alto_px = max(120, 30 * len(pares) + 20)
                grafico.resize(900, alto_px)
                ruta_png = os.path.join(tmp, "grafico.png"); grafico.grab().save(ruta_png, "PNG")
                png = (ruta_png, 900, alto_px)
            informe_estadisticas.generar_pdf(self._tabla, archivo, ruta_logo=os.path.join(DATA_DIR, "Logo.jpg"), grafico_png=png)
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
