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

"""Repuestos usados en un trabajo: la lista que se rellena al registrar,
completar o editar un trabajo, y el selector de artículos del almacén (que
propone primero los repuestos de la máquina elegida)."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QLineEdit,
                             QDoubleSpinBox, QDialogButtonBox, QGroupBox)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import almacen, consumos


def _fmt_cantidad(v):
    return f"{v:g}"


class DialogoElegirRepuesto(QDialog):
    """Buscar un artículo del almacén y la cantidad usada. Los repuestos de la
    máquina [maquina_id] salen primero (🔩), con su cantidad montada."""

    def __init__(self, parent=None, maquina_id=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_elegir_repuesto", "Añadir repuesto usado"))
        self.resize(720, 480)
        self._montados = {r["material_id"]: r for r in almacen.repuestos_de_maquina(maquina_id)} if maquina_id else {}
        materiales = almacen.listar_materiales()
        # Primero los de la máquina, luego el resto por nombre
        self._materiales = sorted(materiales, key=lambda m: (m["id"] not in self._montados, (m.get("nombre") or "").lower()))
        self.moneda = consumos.moneda()

        l = QVBoxLayout(self)
        if self._montados:
            info = QLabel("🔩 " + tt("lbl_repuestos_maquina_primero", "Los repuestos de la máquina del trabajo salen primero."))
            info.setWordWrap(True)
            l.addWidget(info)
        self.buscar = QLineEdit(); self.buscar.setPlaceholderText(tt("ph_buscar_articulo", "Buscar por código o nombre…"))
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self._filtrar)
        l.addWidget(self.buscar)
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels([tt("aud_f_codigo", "Código"), tt("lbl_material", "Artículo"),
                                              tt("lbl_stock_col", "Stock"), tt("lbl_precio_unitario", "Precio unitario")])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.currentCellChanged.connect(lambda *_: self._elegido())
        self.tabla.cellDoubleClicked.connect(lambda *_: self._aceptar())
        l.addWidget(self.tabla)
        fila = QHBoxLayout()
        fila.addWidget(QLabel(tt("lbl_cantidad_usada", "Cantidad usada") + ":"))
        self.cantidad = QDoubleSpinBox(); self.cantidad.setRange(0.01, 99999); self.cantidad.setDecimals(2); self.cantidad.setValue(1)
        fila.addWidget(self.cantidad)
        self.lbl_unidad = QLabel()
        fila.addWidget(self.lbl_unidad)
        fila.addStretch()
        l.addLayout(fila)
        caja = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        caja.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        caja.accepted.connect(self._aceptar); caja.rejected.connect(self.reject)
        l.addWidget(caja)
        self._filtrar("")
        self.buscar.setFocus()

    def _filtrar(self, texto):
        texto = (texto or "").lower().strip()
        visibles = [m for m in self._materiales
                    if not texto or texto in (m.get("nombre") or "").lower() or texto in (m.get("codigo") or "").lower()]
        self._visibles = visibles
        self.tabla.setRowCount(len(visibles))
        for fila, m in enumerate(visibles):
            montado = self._montados.get(m["id"])
            nombre = ("🔩 " if montado else "") + (m.get("nombre") or "")
            precio = m.get("precio")
            celdas = [m.get("codigo") or "", nombre, f"{m.get('stock_actual', 0):g} {m.get('unidad') or ''}".strip(),
                      consumos.formato_importe(precio, self.moneda) if precio is not None else "—"]
            for col, valor in enumerate(celdas):
                item = QTableWidgetItem(valor)
                if col == 2 and (m.get("stock_actual") or 0) <= (m.get("stock_minimo") or 0):
                    item.setForeground(Qt.GlobalColor.red)
                self.tabla.setItem(fila, col, item)
        if visibles:
            self.tabla.selectRow(0)

    def _elegido(self):
        fila = self.tabla.currentRow()
        if not (0 <= fila < len(self._visibles)):
            return
        m = self._visibles[fila]
        self.lbl_unidad.setText(m.get("unidad") or "")
        montado = self._montados.get(m["id"])
        self.cantidad.setValue(montado["cantidad"] if montado and montado.get("cantidad") else 1)

    def _aceptar(self):
        if 0 <= self.tabla.currentRow() < len(self._visibles):
            self.accept()

    def elegido(self):
        m = self._visibles[self.tabla.currentRow()]
        return m, self.cantidad.value()


class RepuestosUsadosWidget(QGroupBox):
    """Lista de repuestos usados en un trabajo, con su coste. items():
    [{material_id, cantidad}]."""

    def __init__(self, parent=None, iniciales=None):
        super().__init__(tt("lbl_repuestos_usados", "🔩 Repuestos usados"), parent)
        self._maquina_id = None
        self.moneda = consumos.moneda()
        self._filas = []   # [{material_id, codigo, nombre, unidad, cantidad, precio}]
        l = QVBoxLayout(self)
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels([tt("lbl_material", "Artículo"), tt("lbl_cantidad", "Cantidad"),
                                              tt("lbl_precio_unitario", "Precio unitario"), tt("lbl_importe", "Importe")])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in (1, 2, 3):
            cab.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setMinimumHeight(120); self.tabla.setMaximumHeight(180)
        l.addWidget(self.tabla)
        fila = QHBoxLayout()
        b_anadir = QPushButton(tt("btn_anadir_repuesto_usado", "➕ Añadir repuesto")); b_anadir.clicked.connect(self._anadir)
        b_quitar = QPushButton(tt("btn_quitar", "➖ Quitar")); b_quitar.clicked.connect(self._quitar)
        fila.addWidget(b_anadir); fila.addWidget(b_quitar); fila.addStretch()
        self.lbl_total = QLabel()
        fila.addWidget(self.lbl_total)
        l.addLayout(fila)
        for m in iniciales or []:
            self._filas.append({k: m.get(k) for k in ("material_id", "codigo", "nombre", "unidad", "cantidad", "precio")})
        self._pintar()

    def set_maquina(self, maquina_id):
        """Máquina del trabajo: sus repuestos salen primero en el selector."""
        self._maquina_id = maquina_id

    def _anadir(self):
        dlg = DialogoElegirRepuesto(self, self._maquina_id)
        if not dlg.exec():
            return
        m, cantidad = dlg.elegido()
        existente = next((f for f in self._filas if f["material_id"] == m["id"]), None)
        if existente:
            existente["cantidad"] += cantidad
        else:
            self._filas.append({"material_id": m["id"], "codigo": m.get("codigo") or "", "nombre": m.get("nombre") or "",
                                "unidad": m.get("unidad") or "", "cantidad": cantidad, "precio": m.get("precio")})
        self._pintar()

    def _quitar(self):
        fila = self.tabla.currentRow()
        if 0 <= fila < len(self._filas):
            del self._filas[fila]
            self._pintar()

    def _pintar(self):
        self.tabla.setRowCount(len(self._filas))
        total, sin_precio = 0.0, False
        for i, f in enumerate(self._filas):
            nombre = f"{f['codigo']} · {f['nombre']}" if f.get("codigo") else f["nombre"]
            importe = f["cantidad"] * f["precio"] if f.get("precio") is not None else None
            if importe is None:
                sin_precio = True
            else:
                total += importe
            celdas = [nombre, f"{_fmt_cantidad(f['cantidad'])} {f.get('unidad') or ''}".strip(),
                      consumos.formato_importe(f["precio"], self.moneda) if f.get("precio") is not None else "—",
                      consumos.formato_importe(importe, self.moneda) if importe is not None else "—"]
            for col, valor in enumerate(celdas):
                self.tabla.setItem(i, col, QTableWidgetItem(valor))
        if self._filas:
            texto = tt("lbl_coste_material", "Coste de material") + f": <b>{consumos.formato_importe(total, self.moneda)}</b>"
            if sin_precio:
                texto += " " + tt("lbl_sin_precio_algunos", "(hay artículos sin precio)")
            self.lbl_total.setText(texto)
        else:
            self.lbl_total.setText("")

    def items(self):
        return [{"material_id": f["material_id"], "cantidad": f["cantidad"]} for f in self._filas if f.get("material_id")]

    def vaciar(self):
        self._filas = []
        self._pintar()
