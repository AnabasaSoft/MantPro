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

"""Máquinas → 💶 Costes por máquina: cuánto ha costado el mantenimiento de cada
máquina (con sus submáquinas), en mano de obra (horas × coste de la hora) y en
repuestos (qué artículos y cuántos), por año."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QLineEdit,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import consumos, costes, maquinas, mano_obra, usuarios


class _ItemNumero(QTableWidgetItem):
    def __init__(self, texto, valor):
        super().__init__(texto)
        self.valor = valor
        self.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def __lt__(self, otro):
        return self.valor < getattr(otro, "valor", 0)


class DialogoCosteRepuestos(QDialog):
    def __init__(self, parent, db, maquina_inicial=None):
        super().__init__(parent)
        self.db = db
        # Solo la sede elegida en la ventana principal (None = todas)
        from ...nucleo import sedes as _sedes
        self._sedes = _sedes
        self.sede = parent.sede_filtro() if hasattr(parent, "sede_filtro") else None
        self.moneda = consumos.moneda()
        self.setWindowTitle(tt("title_costes_maquina", "Costes por máquina"))
        self.resize(1050, 620)
        l = QVBoxLayout(self)
        f = QHBoxLayout()
        f.addWidget(QLabel(tt("lbl_anio", "Año") + ":"))
        self.combo_anio = QComboBox(); self.combo_anio.addItem(tt("filtro_todos", "Todos"), None)
        for anio in maquinas.anios_disponibles(self.sede):
            self.combo_anio.addItem(anio, anio)
        if self.combo_anio.count() > 1:
            self.combo_anio.setCurrentIndex(1)
        self.combo_anio.currentIndexChanged.connect(self.recargar)
        f.addWidget(self.combo_anio)
        # Coste de la hora de trabajo (interno, igual para todos): solo el administrador
        f.addSpacing(20)
        f.addWidget(QLabel(tt("lbl_coste_hora", "Coste de la hora de trabajo") + f" ({self.moneda}):"))
        tarifa = mano_obra.coste_hora()
        self.campo_hora = QLineEdit("" if tarifa is None else f"{tarifa:g}".replace(".", ","))
        self.campo_hora.setPlaceholderText(tt("ph_precio", "sin precio")); self.campo_hora.setMaximumWidth(90)
        self.campo_hora.setEnabled(usuarios.es_admin())
        self.campo_hora.setToolTip(tt("tt_coste_hora", "Se aplica a los trabajos cuyo tiempo se apunte a partir de ahora; "
                                                       "los ya apuntados conservan su tarifa. Solo lo cambia un administrador."))
        self.campo_hora.editingFinished.connect(lambda: mano_obra.fijar_coste_hora(consumos.numero(self.campo_hora.text())))
        f.addWidget(self.campo_hora)
        f.addStretch()
        self.lbl_total = QLabel(); f.addWidget(self.lbl_total)
        l.addLayout(f)

        split = QSplitter(Qt.Orientation.Horizontal)
        self.tabla_maq = QTableWidget(0, 6)
        self.tabla_maq.setHorizontalHeaderLabels([tt("hdr_maquina", "Máquina"), tt("hdr_trabajos", "Trabajos"),
                                                  tt("lbl_horas", "Horas"), tt("lbl_mano_obra", "Mano de obra"),
                                                  tt("lbl_repuestos_corto", "Repuestos"), tt("lbl_total", "Total")])
        self._configurar(self.tabla_maq, estirar=0)
        self.tabla_maq.currentCellChanged.connect(lambda *_: self._mostrar_detalle())
        split.addWidget(self.tabla_maq)
        self.tabla_art = QTableWidget(0, 4)
        self.tabla_art.setHorizontalHeaderLabels([tt("lbl_material", "Artículo"), tt("lbl_cantidad", "Cantidad"),
                                                  tt("lbl_importe", "Importe"), tt("aud_f_codigo", "Código")])
        self._configurar(self.tabla_art, estirar=0)
        split.addWidget(self.tabla_art)
        split.setSizes([500, 550])
        l.addWidget(split, 1)
        nota = QLabel(tt("lbl_nota_costes", "Incluye los trabajos de las submáquinas. Horas = tiempo trabajado × personas. "
                                            "*: falta algún precio (de un artículo o de la hora) al apuntarlo."))
        nota.setWordWrap(True); nota.setStyleSheet("color: gray;")
        l.addWidget(nota)
        b = QHBoxLayout(); b.addStretch()
        exportar = QPushButton(tt("btn_exportar_excel_coste", "📊 Exportar a Excel")); exportar.clicked.connect(self._exportar)
        cerrar = QPushButton(t("cerrar")); cerrar.clicked.connect(self.accept)
        b.addWidget(exportar); b.addWidget(cerrar)
        l.addLayout(b)
        self._maquina_inicial = maquina_inicial
        self.recargar()

    @staticmethod
    def _configurar(tabla, estirar):
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.verticalHeader().setVisible(False)
        tabla.setSortingEnabled(True)
        cab = tabla.horizontalHeader()
        for c in range(tabla.columnCount()):
            cab.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch if c == estirar else QHeaderView.ResizeMode.ResizeToContents)

    def _importe(self, valor, sin_precio):
        return consumos.formato_importe(valor, self.moneda) + (" *" if sin_precio else "")

    def recargar(self):
        """Los costes los calcula el núcleo (costes.por_maquina), igual que en MantPro Web."""
        self._resultado = costes.por_maquina(self.db, self.sede, self.combo_anio.currentData())
        self._por_id = {d["id"]: d for d in self._resultado["filas"]}
        self.tabla_maq.setSortingEnabled(False)
        self.tabla_maq.setRowCount(len(self._resultado["filas"]))
        for fila, d in enumerate(self._resultado["filas"]):
            item = QTableWidgetItem(d["ruta"]); item.setData(Qt.ItemDataRole.UserRole, d["id"])
            self.tabla_maq.setItem(fila, 0, item)
            self.tabla_maq.setItem(fila, 1, _ItemNumero(str(d["trabajos"]), d["trabajos"]))
            self.tabla_maq.setItem(fila, 2, _ItemNumero(f"{d['horas']:.1f}".replace(".", ",") if d["horas"] else "", d["horas"]))
            self.tabla_maq.setItem(fila, 3, _ItemNumero(self._importe(d["mano_obra"], d["mano_sin_precio"]) if d["horas"] else "", d["mano_obra"]))
            self.tabla_maq.setItem(fila, 4, _ItemNumero(self._importe(d["repuestos"], d["sin_precio"]) if d["articulos"] else "", d["repuestos"]))
            self.tabla_maq.setItem(fila, 5, _ItemNumero(self._importe(d["total"], d["sin_precio"] or d["mano_sin_precio"]), d["total"]))
        self.tabla_maq.setSortingEnabled(True)
        self.tabla_maq.sortItems(5, Qt.SortOrder.DescendingOrder)   # las que más cuestan, arriba
        self.lbl_total.setText(tt("lbl_total_periodo", "Total del periodo") + f": <b>{consumos.formato_importe(self._resultado['total'], self.moneda)}</b>")
        fila = next((f for f in range(self.tabla_maq.rowCount())
                     if self.tabla_maq.item(f, 0).data(Qt.ItemDataRole.UserRole) == self._maquina_inicial), 0)
        if self._resultado["filas"]:
            self.tabla_maq.selectRow(fila)
        self._mostrar_detalle()

    def _mostrar_detalle(self):
        item = self.tabla_maq.item(self.tabla_maq.currentRow(), 0) if self.tabla_maq.currentRow() >= 0 else None
        d = self._por_id.get(item.data(Qt.ItemDataRole.UserRole)) if item else None
        articulos = (d or {}).get("articulos", [])
        self.tabla_art.setSortingEnabled(False)
        self.tabla_art.setRowCount(len(articulos))
        for fila, a in enumerate(articulos):
            self.tabla_art.setItem(fila, 0, QTableWidgetItem(a["nombre"]))
            self.tabla_art.setItem(fila, 1, _ItemNumero(f"{a['cantidad']:g} {a['unidad'] or ''}".strip(), a["cantidad"]))
            self.tabla_art.setItem(fila, 2, _ItemNumero(self._importe(a["importe"], a["sin_precio"]), a["importe"]))
            self.tabla_art.setItem(fila, 3, QTableWidgetItem(a["codigo"] or ""))
        self.tabla_art.setSortingEnabled(True)
        self.tabla_art.sortItems(2, Qt.SortOrder.DescendingOrder)

    def _exportar(self):
        try:
            import xlsxwriter  # noqa: F401
        except ImportError:
            QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        anio = self.combo_anio.currentData()
        ruta, _ = QFileDialog.getSaveFileName(self, self.windowTitle(), costes.nombre_fichero_maquinas(anio), "Excel (*.xlsx)")
        if not ruta:
            return
        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"
        costes.excel_por_maquina(ruta, self._resultado, anio)       # el mismo Excel que descarga MantPro Web
        QMessageBox.information(self, t("title_exportado"), tt("msg_coste_exportado", "Exportado en:\n{ruta}").format(ruta=ruta))
