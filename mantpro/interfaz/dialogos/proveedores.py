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

"""Almacén → Proveedores: alta, edición y baja de los proveedores del almacén
(nombre, contacto, teléfono, correo y notas). El proveedor habitual de cada
artículo se elige en la ficha del artículo."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QDialogButtonBox, QMessageBox,
                             QTextEdit)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import proveedores


def texto_error(codigo):
    """Mensaje traducido de un código de error del núcleo de proveedores."""
    if codigo == "nombre_obligatorio":
        return tt("prov_msg_nombre_obligatorio", "El nombre del proveedor es obligatorio.")
    if codigo == "repetido":
        return tt("prov_msg_repetido", "Ya existe un proveedor con ese nombre.")
    return tt("prov_msg_no_existe", "El proveedor ya no existe.")


class DialogoEditarProveedor(QDialog):
    """Alta o edición de un proveedor."""
    def __init__(self, parent=None, proveedor=None):
        super().__init__(parent)
        self.setWindowTitle(tt("prov_title_editar", "Editar proveedor") if proveedor
                            else tt("prov_title_nuevo", "Nuevo proveedor"))
        self.resize(420, 420)
        l = QVBoxLayout()
        proveedor = proveedor or {}

        def campo(clave_texto, texto, valor):
            l.addWidget(QLabel(tt(clave_texto, texto)))
            c = QLineEdit(valor or "")
            l.addWidget(c)
            return c

        self.campo_nombre = campo("prov_lbl_nombre", "Nombre del proveedor", proveedor.get("nombre"))
        self.campo_contacto = campo("prov_lbl_contacto", "Persona de contacto", proveedor.get("contacto"))
        self.campo_telefono = campo("prov_lbl_telefono", "Teléfono", proveedor.get("telefono"))
        self.campo_correo = campo("prov_lbl_correo", "Correo electrónico", proveedor.get("correo"))
        l.addWidget(QLabel(tt("prov_lbl_nota", "Notas")))
        self.campo_nota = QTextEdit(proveedor.get("nota") or "")
        self.campo_nota.setAcceptRichText(False)
        l.addWidget(self.campo_nota)

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar); b.rejected.connect(self.reject)
        l.addWidget(b)
        self.setLayout(l)

    def _validar(self):
        if not self.campo_nombre.text().strip():
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error("nombre_obligatorio"))
            return
        self.accept()

    def get_data(self):
        return {"nombre": self.campo_nombre.text().strip(), "contacto": self.campo_contacto.text().strip(),
                "telefono": self.campo_telefono.text().strip(), "correo": self.campo_correo.text().strip(),
                "nota": self.campo_nota.toPlainText().strip()}


class DialogoProveedores(QDialog):
    """Lista de proveedores del almacén con sus botones de alta, edición y baja."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("prov_title", "Proveedores"))
        self.resize(760, 460)
        l = QVBoxLayout()

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels([
            tt("prov_hdr_nombre", "PROVEEDOR"), tt("prov_hdr_contacto", "CONTACTO"),
            tt("prov_hdr_telefono", "TELÉFONO"), tt("prov_hdr_correo", "CORREO"),
            tt("prov_hdr_articulos", "ARTÍCULOS")])
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemDoubleClicked.connect(lambda _: self.editar())
        l.addWidget(self.tabla)

        self.lbl_vacio = QLabel(tt("prov_vacio", "Aún no hay proveedores. Pulsa «Nuevo proveedor» para añadir el primero."))
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio.setWordWrap(True)
        l.addWidget(self.lbl_vacio)

        h = QHBoxLayout()
        btn_nuevo = QPushButton(tt("prov_btn_nuevo", "➕ Nuevo proveedor")); btn_nuevo.clicked.connect(self.nuevo)
        btn_editar = QPushButton(tt("prov_btn_editar", "✏️ Editar")); btn_editar.clicked.connect(self.editar)
        btn_borrar = QPushButton(tt("prov_btn_borrar", "🗑️ Borrar")); btn_borrar.clicked.connect(self.borrar)
        for b in (btn_nuevo, btn_editar, btn_borrar):
            h.addWidget(b)
        h.addStretch()
        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept)
        h.addWidget(btn_cerrar)
        l.addLayout(h)
        self.setLayout(l)
        self.refrescar()

    def refrescar(self, seleccionar_id=None):
        lista = proveedores.listar_proveedores()
        self.tabla.setRowCount(len(lista))
        for fila, p in enumerate(lista):
            for col, valor in enumerate((p["nombre"], p["contacto"], p["telefono"], p["correo"], str(p["articulos"]))):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, p["id"])
                if col == 4:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(fila, col, item)
            if p["id"] == seleccionar_id:
                self.tabla.selectRow(fila)
        self.tabla.setVisible(bool(lista))
        self.lbl_vacio.setVisible(not lista)

    def _seleccionado(self):
        fila = self.tabla.currentRow()
        item = self.tabla.item(fila, 0) if fila >= 0 else None
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _avisar_seleccion(self):
        QMessageBox.information(self, tt("aviso", "Aviso"),
                                tt("prov_msg_sin_seleccion", "Selecciona un proveedor de la lista."))

    def nuevo(self):
        dlg = DialogoEditarProveedor(self)
        if not dlg.exec():
            return
        proveedor_id, error = proveedores.crear_proveedor(**dlg.get_data())
        if error:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(error))
            return
        self.refrescar(proveedor_id)

    def editar(self):
        proveedor_id = self._seleccionado()
        if proveedor_id is None:
            self._avisar_seleccion(); return
        dlg = DialogoEditarProveedor(self, proveedores.obtener_proveedor(proveedor_id))
        if not dlg.exec():
            return
        ok, error = proveedores.editar_proveedor(proveedor_id, **dlg.get_data())
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(error))
        self.refrescar(proveedor_id)

    def borrar(self):
        proveedor_id = self._seleccionado()
        if proveedor_id is None:
            self._avisar_seleccion(); return
        p = proveedores.obtener_proveedor(proveedor_id)
        if p is None:
            self.refrescar(); return
        if p["articulos"]:
            texto = tt("prov_msg_confirmar_borrar_con_articulos",
                       "¿Borrar al proveedor «{nombre}»? Es el proveedor habitual de {n} artículos, que se quedarán sin proveedor habitual.").format(
                nombre=p["nombre"], n=p["articulos"])
        else:
            texto = tt("prov_msg_confirmar_borrar", "¿Borrar al proveedor «{nombre}»?").format(nombre=p["nombre"])
        if QMessageBox.question(self, tt("aviso", "Aviso"), texto) != QMessageBox.StandardButton.Yes:
            return
        ok, error = proveedores.borrar_proveedor(proveedor_id)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(error))
        self.refrescar()
