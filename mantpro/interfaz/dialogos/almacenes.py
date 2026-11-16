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

"""Herramientas → Almacenes (alta, edición, activar/desactivar y borrado) y el
traspaso de stock entre almacenes. La lógica está en nucleo/almacenes.py."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QDialogButtonBox, QMessageBox,
                             QTextEdit, QComboBox, QFormLayout, QCheckBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import almacenes, sedes


def texto_error(codigo):
    """Mensaje traducido de un código de error del núcleo de almacenes."""
    return {
        "sin_nombre": tt("alm_msg_sin_nombre", "El nombre del almacén es obligatorio."),
        "nombre_repetido": tt("alm_msg_repetido", "Ya existe un almacén con ese nombre."),
        "es_principal": tt("alm_msg_principal", "El almacén principal no se puede borrar ni desactivar."),
        "en_uso": tt("alm_msg_en_uso", "El almacén tiene artículos o zonas: no se puede borrar, pero puedes desactivarlo."),
        "mismo_almacen": tt("alm_msg_mismo", "Elige un almacén distinto del de origen."),
        "cantidad_no_valida": tt("alm_msg_cantidad", "La cantidad tiene que ser mayor que cero."),
        "stock_insuficiente": tt("msg_stock_insuficiente", "No hay stock suficiente para esta salida."),
        "material_no_existe": tt("alm_msg_no_existe", "El artículo ya no existe."),
    }.get(codigo, codigo)


def _nombre_sede(a, nombres_sedes):
    if a["comun"]:
        return tt("alm_comun", "Común (todas las sedes)")
    return nombres_sedes.get(sedes.efectiva(a["sede_id"]), "")


class DialogoEditarAlmacen(QDialog):
    """Alta o edición de un almacén."""
    def __init__(self, parent=None, alm=None):
        super().__init__(parent)
        self.setWindowTitle(tt("alm_title_editar", "Editar almacén") if alm else tt("alm_title_nuevo", "Nuevo almacén"))
        self.resize(420, 320)
        alm = alm or {}
        l = QVBoxLayout()
        f = QFormLayout()
        self.campo_nombre = QLineEdit(alm.get("nombre") or "")
        f.addRow(tt("alm_lbl_nombre", "Nombre"), self.campo_nombre)
        self.combo_sede = QComboBox()
        for s in sedes.listar():
            self.combo_sede.addItem(s["nombre"], s["id"])
        self.combo_sede.setCurrentIndex(max(0, self.combo_sede.findData(sedes.efectiva(alm.get("sede_id")))))
        f.addRow(tt("alm_lbl_sede", "Sede"), self.combo_sede)
        self.chk_comun = QCheckBox(tt("alm_chk_comun", "Común: se ve desde todas las sedes"))
        self.chk_comun.setChecked(bool(alm.get("comun")))
        self.chk_comun.toggled.connect(lambda c: self.combo_sede.setEnabled(not c))
        self.combo_sede.setEnabled(not self.chk_comun.isChecked())
        f.addRow("", self.chk_comun)
        self.campo_direccion = QLineEdit(alm.get("direccion") or "")
        self.campo_direccion.setPlaceholderText(tt("alm_ph_direccion", "Vacía: la dirección de su sede"))
        self.campo_direccion.setToolTip(tt("alm_tt_direccion", "Dirección de entrega que sale en los pedidos a proveedores de este almacén."))
        f.addRow(tt("alm_lbl_direccion", "Dirección de entrega"), self.campo_direccion)
        if alm.get("principal"):   # el principal es siempre de la sede principal
            self.combo_sede.setEnabled(False); self.chk_comun.setEnabled(False)
        l.addLayout(f)
        l.addWidget(QLabel(tt("alm_lbl_notas", "Notas")))
        self.campo_notas = QTextEdit(alm.get("notas") or "")
        self.campo_notas.setAcceptRichText(False)
        l.addWidget(self.campo_notas)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar); b.rejected.connect(self.reject)
        l.addWidget(b)
        self.setLayout(l)

    def _validar(self):
        if not self.campo_nombre.text().strip():
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error("sin_nombre"))
            return
        self.accept()

    def get_data(self):
        return {"nombre": self.campo_nombre.text().strip(), "sede_id": self.combo_sede.currentData(),
                "comun": self.chk_comun.isChecked(), "notas": self.campo_notas.toPlainText().strip(),
                "direccion": self.campo_direccion.text().strip()}


class DialogoAlmacenes(QDialog):
    """Lista de almacenes con sus botones. `cambiado` dice si hay que refrescar la ventana."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cambiado = False
        self.setWindowTitle(tt("alm_title", "Almacenes"))
        self.resize(760, 420)
        l = QVBoxLayout()
        ayuda = QLabel(tt("alm_ayuda", "Cada sede puede tener uno o varios almacenes (por ejemplo, una furgoneta), y "
                                       "un almacén común se ve desde todas. El stock de un artículo se lleva en cada "
                                       "almacén; para moverlo de uno a otro, usa «Traspasar» en la pestaña de stock."))
        ayuda.setWordWrap(True)
        l.addWidget(ayuda)
        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels([tt("alm_hdr_nombre", "ALMACÉN"), tt("alm_hdr_sede", "SEDE"),
                                              tt("alm_hdr_estado", "ESTADO")])
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemDoubleClicked.connect(lambda _: self.editar())
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        l.addWidget(self.tabla)
        h = QHBoxLayout()
        self.btn_nuevo = QPushButton(tt("alm_btn_nuevo", "➕ Nuevo almacén")); self.btn_nuevo.clicked.connect(self.nuevo)
        self.btn_editar = QPushButton(tt("sede_btn_editar", "✏️ Editar")); self.btn_editar.clicked.connect(self.editar)
        self.btn_activar = QPushButton(tt("sede_btn_desactivar", "🚫 Desactivar")); self.btn_activar.clicked.connect(self.activar)
        self.btn_borrar = QPushButton(tt("sede_btn_borrar", "🗑️ Borrar")); self.btn_borrar.clicked.connect(self.borrar)
        for b in (self.btn_nuevo, self.btn_editar, self.btn_activar, self.btn_borrar):
            h.addWidget(b)
        h.addStretch()
        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept)
        h.addWidget(btn_cerrar)
        l.addLayout(h)
        self.setLayout(l)
        self.refrescar()

    def refrescar(self, seleccionar_id=None):
        lista = almacenes.listar(incluir_inactivos=True)
        nombres_sedes = sedes.nombres()
        self.tabla.setRowCount(len(lista))
        for fila, a in enumerate(lista):
            estado = tt("sede_activa", "Activa") if a["activo"] else tt("sede_inactiva", "Desactivada")
            nombre = a["nombre"] + ("  ⭐" if a["principal"] else "")
            for col, valor in enumerate((nombre, _nombre_sede(a, nombres_sedes), estado)):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, a["id"])
                self.tabla.setItem(fila, col, item)
            if a["id"] == seleccionar_id:
                self.tabla.selectRow(fila)
        self._actualizar_botones()

    def _seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0 or not self.tabla.selectedItems():
            return None
        return almacenes.obtener(self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole))

    def _actualizar_botones(self):
        a = self._seleccionado()
        self.btn_editar.setEnabled(a is not None)
        self.btn_borrar.setEnabled(a is not None and not a["principal"])
        self.btn_activar.setEnabled(a is not None and not a["principal"])
        self.btn_activar.setText(tt("sede_btn_activar", "✔️ Activar") if a and not a["activo"]
                                 else tt("sede_btn_desactivar", "🚫 Desactivar"))

    def _hecho(self, err, seleccionar_id=None):
        if err:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(err))
            return
        self.cambiado = True
        self.refrescar(seleccionar_id)

    def nuevo(self):
        d = DialogoEditarAlmacen(self)
        if d.exec():
            nuevo, err = almacenes.crear(d.get_data())
            self._hecho(err, nuevo)

    def editar(self):
        a = self._seleccionado()
        if a:
            d = DialogoEditarAlmacen(self, a)
            if d.exec():
                self._hecho(almacenes.actualizar(a["id"], d.get_data()), a["id"])

    def activar(self):
        a = self._seleccionado()
        if a:
            self._hecho(almacenes.activar(a["id"], not a["activo"]), a["id"])

    def borrar(self):
        a = self._seleccionado()
        if not a:
            return
        r = QMessageBox.question(self, tt("alm_title", "Almacenes"),
                                 tt("alm_confirmar_borrar", "¿Borrar el almacén «{nombre}»?").format(nombre=a["nombre"]))
        if r == QMessageBox.StandardButton.Yes:
            self._hecho(almacenes.borrar(a["id"]))


class DialogoTraspaso(QDialog):
    """Elegir el almacén de destino y la cantidad para traspasar un artículo."""
    def __init__(self, parent, material):
        super().__init__(parent)
        self.setWindowTitle(tt("alm_title_traspaso", "Traspasar a otro almacén"))
        self.resize(420, 200)
        l = QVBoxLayout()
        origen = almacenes.nombre(material["almacen_id"])
        l.addWidget(QLabel(tt("alm_lbl_traspaso", "{articulo} — en «{origen}» hay {stock:g} {unidad}").format(
            articulo=material["nombre"], origen=origen, stock=material["stock_actual"], unidad=material.get("unidad") or "")))
        f = QFormLayout()
        self.combo_destino = QComboBox()
        actual = almacenes.efectivo(material["almacen_id"])
        nombres_sedes = sedes.nombres()
        for a in almacenes.listar():
            if a["id"] != actual:
                self.combo_destino.addItem(f"{a['nombre']}  ({_nombre_sede(a, nombres_sedes)})", a["id"])
        f.addRow(tt("alm_lbl_destino", "Almacén de destino"), self.combo_destino)
        self.cantidad = QDoubleSpinBox()
        self.cantidad.setDecimals(2)
        self.cantidad.setRange(0, max(0.0, float(material["stock_actual"])))
        self.cantidad.setValue(min(1.0, max(0.0, float(material["stock_actual"]))))
        f.addRow(tt("alm_lbl_cantidad", "Cantidad"), self.cantidad)
        l.addLayout(f)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.button(QDialogButtonBox.StandardButton.Ok).setEnabled(self.combo_destino.count() > 0 and material["stock_actual"] > 0)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b)
        self.setLayout(l)

    def get_data(self):
        return self.combo_destino.currentData(), self.cantidad.value()
