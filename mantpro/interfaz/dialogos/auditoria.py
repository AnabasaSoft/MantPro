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

"""Herramientas → Registro de cambios: quién ha cambiado qué, cuándo y desde
dónde (PC o móvil), con el detalle campo a campo (antes → después)."""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
                             QFileDialog, QMessageBox, QWidget, QTextEdit)
from PyQt6.QtCore import Qt, QTimer

from ...idiomas import t
from ..comun import tt
from ...nucleo import registro_cambios, usuarios


# Los textos, los filtros y la exportación están en el núcleo (los comparte con MantPro Web)
nombres_categoria = registro_cambios.nombres_categoria
nombres_accion = registro_cambios.nombres_accion
campo = registro_cambios.campo
_resumen = registro_cambios.resumen


class DialogoRegistroCambios(QDialog):
    POR_PAGINA = registro_cambios.POR_PAGINA

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("menu_auditoria", "Registro de cambios").lstrip("📋 "))
        self.resize(1200, 700)
        self._registros = []
        self._hay_mas = False
        l = QVBoxLayout(self)

        # --- filtros
        f = QHBoxLayout()
        self.combo_cat = QComboBox(); self.combo_cat.addItem(tt("filtro_todas", "Todas"), None)
        for clave, nombre in nombres_categoria().items():
            self.combo_cat.addItem(nombre, clave)
        self.combo_acc = QComboBox(); self.combo_acc.addItem(tt("filtro_todas", "Todas"), None)
        for clave, nombre in nombres_accion().items():
            self.combo_acc.addItem(nombre, clave)
        self.combo_usu = QComboBox(); self.combo_usu.addItem(tt("filtro_todos", "Todos"), None)
        for u in usuarios.listar_usuarios(incluir_inactivos=True):
            self.combo_usu.addItem(u["nombre"], u["id"])
        self.combo_periodo = QComboBox()
        for dias, texto in registro_cambios.textos_periodo():
            self.combo_periodo.addItem(texto, dias)
        self.combo_periodo.setCurrentIndex(registro_cambios.PERIODOS.index(registro_cambios.PERIODO_INICIAL))
        self.buscar = QLineEdit(); self.buscar.setPlaceholderText(tt("aud_buscar", "Buscar (máquina, artículo, usuario, texto…)"))
        self.buscar.setClearButtonEnabled(True)
        for etiqueta, widget in ((tt("aud_categoria", "Categoría"), self.combo_cat), (tt("lbl_accion", "Acción"), self.combo_acc),
                                 (tt("aud_usuario", "Usuario"), self.combo_usu), (tt("aud_periodo", "Periodo"), self.combo_periodo)):
            f.addWidget(QLabel(etiqueta + ":")); f.addWidget(widget)
        l.addLayout(f)
        l.addWidget(self.buscar)

        # --- tabla y detalle
        split = QSplitter(Qt.Orientation.Vertical)
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels([tt("lbl_fecha_hora", "Fecha y hora"), tt("aud_usuario", "Usuario"),
                                              tt("aud_origen", "Desde"), tt("aud_categoria", "Categoría"),
                                              tt("lbl_accion", "Acción"), tt("aud_objeto", "Afecta a"),
                                              tt("aud_cambios", "Cambios")])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        cab = self.tabla.horizontalHeader()
        for c in range(5):
            cab.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive); self.tabla.setColumnWidth(5, 260)
        cab.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.tabla.currentCellChanged.connect(lambda *_: self._mostrar_detalle())
        split.addWidget(self.tabla)

        abajo = QWidget(); la = QVBoxLayout(abajo); la.setContentsMargins(0, 0, 0, 0)
        self.lbl_detalle = QLabel(); self.lbl_detalle.setWordWrap(True)
        self.lbl_detalle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        la.addWidget(self.lbl_detalle)
        self.tabla_cambios = QTableWidget(0, 3)
        self.tabla_cambios.setHorizontalHeaderLabels([tt("aud_campo", "Campo"), tt("aud_antes", "Antes"), tt("aud_despues", "Después")])
        self.tabla_cambios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_cambios.verticalHeader().setVisible(False)
        self.tabla_cambios.setWordWrap(True)
        cc = self.tabla_cambios.horizontalHeader()
        cc.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cc.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cc.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        la.addWidget(self.tabla_cambios)
        self.texto_detalle = QTextEdit(); self.texto_detalle.setReadOnly(True); self.texto_detalle.setMaximumHeight(110)
        la.addWidget(self.texto_detalle)
        split.addWidget(abajo)
        split.setSizes([420, 260])
        l.addWidget(split, 1)

        # --- botones
        b = QHBoxLayout()
        self.lbl_total = QLabel()
        b.addWidget(self.lbl_total)
        b.addStretch()
        self.btn_mas = QPushButton(tt("aud_cargar_mas", "Cargar más")); self.btn_mas.clicked.connect(self._cargar_mas)
        exportar = QPushButton(tt("aud_exportar", "📤 Exportar (Excel o CSV)")); exportar.clicked.connect(self._exportar)
        cerrar = QPushButton(t("cerrar")); cerrar.clicked.connect(self.accept)
        for w in (self.btn_mas, exportar, cerrar):
            b.addWidget(w)
        l.addLayout(b)

        for combo in (self.combo_cat, self.combo_acc, self.combo_usu, self.combo_periodo):
            combo.currentIndexChanged.connect(self.recargar)
        self._espera = QTimer(self, singleShot=True, interval=350, timeout=self.recargar)
        self.buscar.textChanged.connect(lambda _t: self._espera.start())
        self.recargar()

    # ----------------------------------------------------------- datos
    def _filtros(self):
        return registro_cambios.filtros(self.combo_cat.currentData(), self.combo_acc.currentData(),
                                        self.combo_usu.currentData(), self.combo_periodo.currentData(), self.buscar.text())

    def recargar(self):
        self._registros, self._hay_mas = registro_cambios.pagina(self._filtros())
        self._pintar()

    def _cargar_mas(self):
        mas, self._hay_mas = registro_cambios.pagina(self._filtros(), len(self._registros))
        self._registros += mas
        self._pintar()

    def _pintar(self):
        self.tabla.setRowCount(len(self._registros))
        for fila, r in enumerate(self._registros):
            d = registro_cambios.fila(r)
            celdas = [d["fecha"], d["usuario"], d["origen"], d["categoria"], d["accion"], d["objeto"], d["resumen"]]
            for col, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                if col == 6 and d["detalle"]:
                    item.setToolTip(d["detalle"])
                if d["rojo"]:
                    item.setForeground(Qt.GlobalColor.red)
                self.tabla.setItem(fila, col, item)
        self.btn_mas.setVisible(self._hay_mas)
        self.lbl_total.setText(tt("aud_total", "{n} registros").format(n=len(self._registros)) + ("+" if self._hay_mas else ""))
        if self._registros:
            self.tabla.selectRow(0)
        self._mostrar_detalle()

    def _mostrar_detalle(self):
        fila = self.tabla.currentRow()
        r = self._registros[fila] if 0 <= fila < len(self._registros) else None
        self.tabla_cambios.setRowCount(0)
        if r is None:
            self.lbl_detalle.setText(tt("aud_sin_registros", "No hay cambios con estos filtros."))
            self.texto_detalle.clear(); self.tabla_cambios.setVisible(False); self.texto_detalle.setVisible(False)
            return
        cats, accs = nombres_categoria(), nombres_accion()
        self.lbl_detalle.setText(f"<b>{accs.get(r['accion'], r['accion'])}</b> · {cats.get(r['categoria'], r['categoria'])}"
                                 f" · {r.get('objeto') or ''}<br>{(r.get('fecha') or '').replace('T', ' ')} · "
                                 f"{r.get('usuario_nombre') or '—'} · {r.get('origen') or '💻 PC'}")
        cambios = r.get("cambios") or []
        self.tabla_cambios.setVisible(bool(cambios))
        self.tabla_cambios.setRowCount(len(cambios))
        for i, c in enumerate(cambios):
            for col, texto in enumerate((campo(c.get("campo", "")), c.get("antes", ""), c.get("despues", ""))):
                item = QTableWidgetItem(texto if texto != "" else "—")
                if col == 1 and texto:
                    item.setForeground(Qt.GlobalColor.darkRed)
                if col == 2 and texto:
                    item.setForeground(Qt.GlobalColor.darkGreen)
                self.tabla_cambios.setItem(i, col, item)
        self.tabla_cambios.resizeRowsToContents()
        self.texto_detalle.setVisible(bool(r.get("detalle")))
        self.texto_detalle.setPlainText(r.get("detalle") or "")

    # ----------------------------------------------------------- exportar
    def _exportar(self):
        nombre = registro_cambios.nombre_fichero("xlsx")
        ruta, filtro = QFileDialog.getSaveFileName(self, tt("aud_exportar", "📤 Exportar (Excel o CSV)"), nombre,
                                                   "Excel (*.xlsx);;CSV (*.csv)")
        if not ruta:
            return
        try:
            formato = "csv" if ruta.lower().endswith(".csv") or "CSV" in filtro else "xlsx"
            if not ruta.lower().endswith("." + formato):
                ruta = (os.path.splitext(ruta)[0] if formato == "csv" else ruta) + "." + formato
            n = registro_cambios.exportar(ruta, formato, self._filtros())
            QMessageBox.information(self, self.windowTitle(),
                                    tt("aud_exportado", "Exportados {n} registros a:\n{ruta}").format(n=n, ruta=ruta))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))
