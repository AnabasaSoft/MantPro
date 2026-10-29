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

"""Asistente de importación desde Excel/CSV (la lógica está en nucleo/importar.py)."""

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTabWidget, QMessageBox, QTableWidget, QTableWidgetItem,
                             QDialog, QAbstractItemView, QComboBox, QFileDialog, QFormLayout,
                             QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

from ...idiomas import t
from ...nucleo import importar

class _PanelHojaImportar(QWidget):
    """Pestaña del paso 2 para una hoja: su tipo (solo si se importa el libro
    entero) y qué columna corresponde a cada dato."""
    def __init__(self, hoja, cabeceras, filas, tipo, elegir_tipo):
        super().__init__()
        self.hoja, self.cabeceras, self.filas = hoja, cabeceras, filas
        v = QVBoxLayout(self)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem(t("imp_no_importar"), None)
        for tp in importar.TIPOS:
            self.combo_tipo.addItem(t(f"imp_tipo_{tp}"), tp)
        self.combo_tipo.setCurrentIndex(max(0, self.combo_tipo.findData(tipo)))
        if elegir_tipo:
            f = QFormLayout(); f.addRow(t("imp_lbl_tipo_hoja"), self.combo_tipo); v.addLayout(f)
        self.form = QFormLayout(); v.addLayout(self.form)
        self.nota = QLabel(t("imp_nota_obligatorios")); v.addWidget(self.nota)
        v.addStretch()
        self.combo_tipo.currentIndexChanged.connect(self._reconstruir)
        self._reconstruir()

    @property
    def tipo(self):
        return self.combo_tipo.currentData()

    @property
    def titulo(self):
        return self.hoja or t(f"imp_tipo_{self.tipo}")

    def _reconstruir(self):
        while self.form.rowCount():
            self.form.removeRow(0)
        self.combos = {}
        self.nota.setVisible(self.tipo is not None)
        if self.tipo is None: return
        mapeo = importar.emparejar_automatico(self.tipo, self.cabeceras)
        for campo, obligatorio in importar.CAMPOS[self.tipo]:
            combo = QComboBox(); combo.addItem(t("imp_no_importar"), None)
            for j, cab in enumerate(self.cabeceras):
                combo.addItem(cab, j)
            combo.setCurrentIndex(max(0, combo.findData(mapeo.get(campo))))
            self.form.addRow(importar.etiqueta_campo(campo) + (" *" if obligatorio else "") + ":", combo)
            self.combos[campo] = combo

    def mapeo(self):
        return {campo: combo.currentData() for campo, combo in self.combos.items() if combo.currentData() is not None}

    def faltan(self):
        mapeo = self.mapeo()
        return [importar.etiqueta_campo(c) for c, obligatorio in importar.CAMPOS[self.tipo] if obligatorio and c not in mapeo]


class DialogoImportar(QDialog):
    """Asistente de importación desde Excel/CSV en tres pasos: fichero y tipo
    (una hoja o el libro entero), columnas de cada hoja, y vista previa. La
    lógica está en importar.py; aquí solo la interfaz. Al aceptar,
    `self.ejecutar` (de la ventana principal) hace la copia previa y la
    importación real."""
    COLORES = {"crear": "#27ae60", "actualizar": "#2980b9", "saltar": "#7f8c8d", "error": "#c0392b", "avisos": "#e67e22"}

    def __init__(self, parent, ejecutar):
        super().__init__(parent)
        self.ejecutar = ejecutar
        self.setWindowTitle(t("imp_titulo")); self.resize(1000, 660)
        self.libro, self.paneles, self.resultados = [], [], []
        l = QVBoxLayout(self)
        self.paginas = QStackedWidget(); l.addWidget(self.paginas)

        # --- Paso 1: fichero y tipo
        p1 = QWidget(); v1 = QVBoxLayout(p1)
        v1.addWidget(QLabel(t("imp_paso1"), styleSheet="font-weight: bold; font-size: 15px;"))
        f1 = QFormLayout()
        fila_fichero = QHBoxLayout()
        self.txt_fichero = QLineEdit(); self.txt_fichero.setReadOnly(True)
        btn_examinar = QPushButton(t("imp_btn_examinar")); btn_examinar.clicked.connect(self._elegir_fichero)
        fila_fichero.addWidget(self.txt_fichero); fila_fichero.addWidget(btn_examinar)
        f1.addRow(t("imp_lbl_fichero"), fila_fichero)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem(t("imp_tipo_libro"), "libro")
        for tipo in importar.TIPOS:
            self.combo_tipo.addItem(t(f"imp_tipo_{tipo}"), tipo)
        self.combo_tipo.setCurrentIndex(1)
        f1.addRow(t("imp_lbl_tipo"), self.combo_tipo)
        self.combo_hoja = QComboBox(); self.combo_hoja.setEnabled(False)
        f1.addRow(t("imp_lbl_hoja"), self.combo_hoja)
        v1.addLayout(f1); self.form_paso1 = f1
        for clave in ("imp_ayuda_paso1", "imp_ayuda_libro"):
            ayuda = QLabel(t(clave)); ayuda.setWordWrap(True); v1.addWidget(ayuda)
        btn_plantilla = QPushButton(t("imp_btn_plantilla")); btn_plantilla.clicked.connect(self._guardar_plantilla)
        fila_plantilla = QHBoxLayout(); fila_plantilla.addWidget(btn_plantilla); fila_plantilla.addStretch()
        v1.addLayout(fila_plantilla); v1.addStretch()
        self.paginas.addWidget(p1)
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_paso1)
        self.combo_hoja.currentTextChanged.connect(self._hoja_cambiada)

        # --- Paso 2: columnas de cada hoja
        p2 = QWidget(); v2 = QVBoxLayout(p2)
        v2.addWidget(QLabel(t("imp_paso2"), styleSheet="font-weight: bold; font-size: 15px;"))
        self.tabs_columnas = QTabWidget(); v2.addWidget(self.tabs_columnas)
        f2 = QFormLayout()
        self.combo_modo = QComboBox()
        self.combo_modo.addItem(t("imp_modo_saltar"), "saltar")
        self.combo_modo.addItem(t("imp_modo_actualizar"), "actualizar")
        f2.addRow(t("imp_lbl_duplicados"), self.combo_modo)
        v2.addLayout(f2)
        self.paginas.addWidget(p2)

        # --- Paso 3: vista previa
        p3 = QWidget(); v3 = QVBoxLayout(p3)
        v3.addWidget(QLabel(t("imp_paso3"), styleSheet="font-weight: bold; font-size: 15px;"))
        self.lbl_resumen = QLabel(); self.lbl_resumen.setWordWrap(True); v3.addWidget(self.lbl_resumen)
        self.tabs_previa = QTabWidget(); v3.addWidget(self.tabs_previa)
        self.paginas.addWidget(p3)

        botones = QHBoxLayout()
        self.btn_atras = QPushButton(t("imp_btn_atras")); self.btn_atras.clicked.connect(self._atras)
        self.btn_siguiente = QPushButton(t("imp_btn_siguiente")); self.btn_siguiente.clicked.connect(self._siguiente)
        self.btn_importar = QPushButton(t("imp_btn_importar")); self.btn_importar.clicked.connect(self._importar)
        btn_cancelar = QPushButton(t("btn_cancelar")); btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(self.btn_atras); botones.addStretch()
        for b in (btn_cancelar, self.btn_siguiente, self.btn_importar): botones.addWidget(b)
        l.addLayout(botones)
        self._actualizar_botones()

    # ------------------------------------------------------------ paso 1

    @property
    def tipo(self):
        return self.combo_tipo.currentData()

    def _actualizar_paso1(self):
        # La hoja solo se elige al importar una sola; con el libro entero se usan todas.
        self.form_paso1.setRowVisible(self.combo_hoja, self.tipo != "libro")
        self.combo_hoja.setEnabled(self.tipo != "libro" and self.combo_hoja.count() > 1)

    def _hoja_cambiada(self, hoja):
        if self.tipo == "libro": return
        datos = next((h for h in self.libro if h[0] == hoja), None)
        tipo = importar.detectar_tipo(hoja, datos[1]) if datos else None
        if tipo: self.combo_tipo.setCurrentIndex(self.combo_tipo.findData(tipo))

    def _avisar(self, texto):
        QMessageBox.warning(self, t("title_atencion"), texto)

    def _elegir_fichero(self):
        ruta, _ = QFileDialog.getOpenFileName(self, t("imp_titulo"), "",
                                              f"{t('imp_filtro_ficheros')} (*.xlsx *.csv *.txt)")
        if not ruta: return
        self.cargar_fichero(ruta)

    def cargar_fichero(self, ruta):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.libro = importar.leer_libro(ruta)
        except importar.ErrorLectura as e:
            QApplication.restoreOverrideCursor(); self._avisar(str(e)); return
        QApplication.restoreOverrideCursor()
        if not self.libro:
            self._avisar(t("imp_msg_sin_filas")); return
        self.txt_fichero.setText(ruta)
        self.combo_hoja.blockSignals(True)
        self.combo_hoja.clear(); self.combo_hoja.addItems([h[0] for h in self.libro if h[0]])
        self.combo_hoja.blockSignals(False)
        # "Todo el libro" solo tiene sentido con varias hojas
        self.combo_tipo.model().item(0).setEnabled(len(self.libro) > 1)
        detectadas = [(h, importar.detectar_tipo(h, cab)) for h, cab, _ in self.libro]
        con_tipo = [(h, tp) for h, tp in detectadas if tp]
        if len(con_tipo) > 1:
            self.combo_tipo.setCurrentIndex(0)
        else:
            hoja, tipo = con_tipo[0] if con_tipo else (self.libro[0][0], None)
            if hoja: self.combo_hoja.setCurrentText(hoja)
            if tipo: self.combo_tipo.setCurrentIndex(self.combo_tipo.findData(tipo))
            elif self.tipo == "libro": self.combo_tipo.setCurrentIndex(1)
        self._actualizar_paso1()

    def _guardar_plantilla(self):
        ruta, _ = QFileDialog.getSaveFileName(self, t("imp_btn_plantilla"), t("imp_nombre_plantilla") + ".xlsx", "Excel (*.xlsx)")
        if not ruta: return
        if not ruta.lower().endswith(".xlsx"): ruta += ".xlsx"
        try:
            importar.generar_plantilla(ruta)
            QMessageBox.information(self, t("title_exito"), t("imp_msg_guardado").format(ruta=ruta))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))

    # ------------------------------------------------------------ pasos 2 y 3

    def _actualizar_botones(self):
        pagina = self.paginas.currentIndex()
        self.btn_atras.setEnabled(pagina > 0)
        self.btn_siguiente.setVisible(pagina < 2)
        self.btn_importar.setVisible(pagina == 2)
        if pagina == 2:
            total = [r for res in self.resultados for r in res]
            c = importar.resumen(total)
            self.btn_importar.setEnabled(c["crear"] + c["actualizar"] > 0)

    def _cargar_paneles(self):
        self.tabs_columnas.clear()
        if self.tipo == "libro":
            hojas = [(h, cab, filas, importar.detectar_tipo(h, cab)) for h, cab, filas in self.libro]
        else:
            datos = next((x for x in self.libro if x[0] == self.combo_hoja.currentText()), self.libro[0])
            hojas = [(*datos, self.tipo)]
        self.paneles = [_PanelHojaImportar(h, cab, filas, tipo, elegir_tipo=self.tipo == "libro")
                        for h, cab, filas, tipo in hojas]
        for panel in self.paneles:
            self.tabs_columnas.addTab(panel, panel.hoja or t(f"imp_tipo_{panel.tipo}"))

    def hojas_a_importar(self):
        """[(título, tipo, cabeceras, filas, mapeo)] de las hojas con tipo."""
        return [(p.titulo, p.tipo, p.cabeceras, p.filas, p.mapeo()) for p in self.paneles if p.tipo]

    def _siguiente(self):
        pagina = self.paginas.currentIndex()
        if pagina == 0:
            if not self.libro:
                self._avisar(t("imp_msg_elige_fichero")); return
            self._cargar_paneles()
        elif pagina == 1:
            if not any(p.tipo for p in self.paneles):
                self._avisar(t("imp_msg_ninguna_hoja")); return
            for i, p in enumerate(self.paneles):
                if p.tipo and p.faltan():
                    self.tabs_columnas.setCurrentIndex(i)
                    self._avisar(t("imp_msg_falta_obligatorio_hoja").format(hoja=p.titulo, campos=", ".join(p.faltan()))); return
            hojas = self.hojas_a_importar()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                self.resultados, _ = importar.procesar_varias([(tp, filas, mapeo) for _, tp, _, filas, mapeo in hojas],
                                                              self.combo_modo.currentData(), aplicar=False)
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, t("title_error"), t("imp_msg_error").format(error=e)); return
            QApplication.restoreOverrideCursor()
            self._llenar_vista_previa(hojas)
        self.paginas.setCurrentIndex(pagina + 1)
        self._actualizar_botones()

    def _atras(self):
        self.paginas.setCurrentIndex(max(0, self.paginas.currentIndex() - 1))
        self._actualizar_botones()

    @staticmethod
    def texto_resumen(titulos, resultados):
        """Resumen de una o varias hojas: con varias, el total y una línea por hoja."""
        def una(res):
            c = importar.resumen(res)
            return t("imp_resumen").format(crear=c["crear"], actualizar=c["actualizar"], saltar=c["saltar"],
                                           error=c["error"], avisos=c["avisos"])
        if len(resultados) == 1:
            return una(resultados[0])
        lineas = [t("imp_resumen_total").format(resumen=una([r for res in resultados for r in res]))]
        lineas += [t("imp_resumen_hoja").format(hoja=tit, resumen=una(res)) for tit, res in zip(titulos, resultados)]
        return "\n".join(lineas)

    def _llenar_vista_previa(self, hojas):
        self.lbl_resumen.setText(self.texto_resumen([h[0] for h in hojas], self.resultados))
        self.tabs_previa.clear()
        for (titulo, tipo, _, _, mapeo), resultados in zip(hojas, self.resultados):
            tabla = QTableWidget(); tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tabla.verticalHeader().setVisible(False)
            # Primero a su pestaña y luego los datos: si no, los anchos de
            # columna se calculan sin el estilo (fuente) y salen recortados.
            hay_errores = any(r.estado == "error" for r in resultados)
            self.tabs_previa.addTab(tabla, titulo + (" ⚠" if hay_errores else ""))
            tabla.ensurePolished()
            campos = [c for c, _ in importar.CAMPOS[tipo] if c in mapeo]
            # Las observaciones van justo detrás del estado: son lo que explica
            # qué va a pasar con cada fila y no deben quedar escondidas al final.
            cabeceras = [t("imp_col_fila"), t("imp_col_estado"), t("imp_col_mensajes")] + [importar.etiqueta_campo(c) for c in campos]
            tabla.setColumnCount(len(cabeceras)); tabla.setHorizontalHeaderLabels(cabeceras)
            tabla.setRowCount(len(resultados)); tabla.setWordWrap(True)
            for i, r in enumerate(resultados):
                color = QColor(self.COLORES["avisos" if r.con_avisos else r.estado])
                celdas = [str(r.numero), t(f"imp_estado_{r.estado}"), "\n".join(r.mensajes)]
                celdas += [importar.texto_celda(r.valores[mapeo[c]]) for c in campos]
                for j, texto in enumerate(celdas):
                    item = QTableWidgetItem(texto)
                    if j in (1, 2):
                        item.setForeground(QBrush(color))
                    if j == 2 and texto:
                        item.setToolTip(texto)
                    tabla.setItem(i, j, item)
            tabla.resizeColumnsToContents()
            tabla.setColumnWidth(2, min(max(tabla.columnWidth(2), 200), 420))
            tabla.resizeRowsToContents()

    def _importar(self):
        if self.ejecutar(self.hojas_a_importar(), self.combo_modo.currentData(), self):
            self.accept()
