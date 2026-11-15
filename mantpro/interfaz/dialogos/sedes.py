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

"""Herramientas → Sedes: plantas propias o empresas cliente (alta, edición,
activar/desactivar y borrado). La lógica está en nucleo/sedes.py."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QDialogButtonBox, QMessageBox,
                             QTextEdit, QComboBox, QFormLayout)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import sedes


def texto_error(codigo):
    """Mensaje traducido de un código de error del núcleo de sedes."""
    return {
        "sin_nombre": tt("sede_msg_sin_nombre", "El nombre de la sede es obligatorio."),
        "nombre_repetido": tt("sede_msg_repetido", "Ya existe una sede con ese nombre."),
        "es_principal": tt("sede_msg_principal", "La sede principal no se puede borrar ni desactivar."),
        "en_uso": tt("sede_msg_en_uso", "La sede tiene máquinas, trabajos, pendientes o avisos: no se puede "
                                        "borrar, pero puedes desactivarla."),
    }.get(codigo, codigo)


def nombre_tipo(tipo):
    return (tt("sede_tipo_cliente", "Empresa cliente") if tipo == sedes.TIPO_CLIENTE
            else tt("sede_tipo_propia", "Planta propia"))


class DialogoEditarSede(QDialog):
    """Alta o edición de una sede."""
    def __init__(self, parent=None, sede=None):
        super().__init__(parent)
        self.setWindowTitle(tt("sede_title_editar", "Editar sede") if sede else tt("sede_title_nueva", "Nueva sede"))
        self.resize(460, 480)
        sede = sede or {}
        l = QVBoxLayout()
        f = QFormLayout()

        def campo(clave, texto, valor):
            c = QLineEdit(valor or "")
            f.addRow(tt(clave, texto), c)
            return c

        self.campo_nombre = campo("sede_lbl_nombre", "Nombre", sede.get("nombre"))
        self.combo_tipo = QComboBox()
        for tipo in sedes.TIPOS:
            self.combo_tipo.addItem(nombre_tipo(tipo), tipo)
        self.combo_tipo.setCurrentIndex(max(0, self.combo_tipo.findData(sede.get("tipo") or sedes.TIPO_PROPIA)))
        f.addRow(tt("sede_lbl_tipo", "Tipo"), self.combo_tipo)
        self.campo_cif = campo("sede_lbl_cif", "CIF / NIF", sede.get("cif"))
        self.campo_direccion = campo("sede_lbl_direccion", "Dirección", sede.get("direccion"))
        self.campo_contacto = campo("sede_lbl_contacto", "Persona de contacto", sede.get("contacto"))
        self.campo_telefono = campo("sede_lbl_telefono", "Teléfono", sede.get("telefono"))
        self.campo_email = campo("sede_lbl_email", "Correo electrónico", sede.get("email"))
        l.addLayout(f)
        l.addWidget(QLabel(tt("sede_lbl_notas", "Notas")))
        self.campo_notas = QTextEdit(sede.get("notas") or "")
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
        return {"nombre": self.campo_nombre.text().strip(), "tipo": self.combo_tipo.currentData(),
                "cif": self.campo_cif.text().strip(), "direccion": self.campo_direccion.text().strip(),
                "contacto": self.campo_contacto.text().strip(), "telefono": self.campo_telefono.text().strip(),
                "email": self.campo_email.text().strip(), "notas": self.campo_notas.toPlainText().strip()}


class DialogoSedes(QDialog):
    """Lista de sedes con sus botones. Al cerrar, `cambiado` dice si hay que refrescar la ventana."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cambiado = False
        self.setWindowTitle(tt("sede_title", "Sedes"))
        self.resize(780, 440)
        l = QVBoxLayout()
        ayuda = QLabel(tt("sede_ayuda", "Plantas propias o empresas cliente que mantienes. Con más de una sede activa "
                                        "aparece arriba a la derecha el selector de sede. Lo que ya había es de la "
                                        "sede principal."))
        ayuda.setWordWrap(True)
        l.addWidget(ayuda)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels([
            tt("sede_hdr_nombre", "SEDE"), tt("sede_hdr_tipo", "TIPO"), tt("sede_hdr_cif", "CIF / NIF"),
            tt("sede_hdr_contacto", "CONTACTO"), tt("sede_hdr_estado", "ESTADO")])
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemDoubleClicked.connect(lambda _: self.editar())
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones)
        l.addWidget(self.tabla)

        h = QHBoxLayout()
        self.btn_nueva = QPushButton(tt("sede_btn_nueva", "➕ Nueva sede")); self.btn_nueva.clicked.connect(self.nueva)
        self.btn_editar = QPushButton(tt("sede_btn_editar", "✏️ Editar")); self.btn_editar.clicked.connect(self.editar)
        self.btn_activar = QPushButton(tt("sede_btn_desactivar", "🚫 Desactivar")); self.btn_activar.clicked.connect(self.activar)
        self.btn_borrar = QPushButton(tt("sede_btn_borrar", "🗑️ Borrar")); self.btn_borrar.clicked.connect(self.borrar)
        for b in (self.btn_nueva, self.btn_editar, self.btn_activar, self.btn_borrar):
            h.addWidget(b)
        h.addStretch()
        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept)
        h.addWidget(btn_cerrar)
        l.addLayout(h)
        self.setLayout(l)
        self.refrescar()

    def refrescar(self, seleccionar_id=None):
        lista = sedes.listar(incluir_inactivas=True)
        self.tabla.setRowCount(len(lista))
        for fila, s in enumerate(lista):
            nombre = s["nombre"] + ("  ⭐" if s["principal"] else "")
            estado = tt("sede_activa", "Activa") if s["activa"] else tt("sede_inactiva", "Desactivada")
            for col, valor in enumerate((nombre, nombre_tipo(s["tipo"]), s["cif"] or "", s["contacto"] or "", estado)):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, s["id"])
                self.tabla.setItem(fila, col, item)
            if s["id"] == seleccionar_id:
                self.tabla.selectRow(fila)
        self._actualizar_botones()

    def _seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0 or not self.tabla.selectedItems():
            return None
        return sedes.obtener(self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole))

    def _actualizar_botones(self):
        s = self._seleccionada()
        self.btn_editar.setEnabled(s is not None)
        self.btn_borrar.setEnabled(s is not None and not s["principal"])
        self.btn_activar.setEnabled(s is not None and not s["principal"])
        self.btn_activar.setText(tt("sede_btn_activar", "✔️ Activar") if s and not s["activa"]
                                 else tt("sede_btn_desactivar", "🚫 Desactivar"))

    def nueva(self):
        d = DialogoEditarSede(self)
        if d.exec():
            nuevo, err = sedes.crear(d.get_data())
            if err:
                QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(err))
                return
            self.cambiado = True
            self.refrescar(nuevo)

    def editar(self):
        s = self._seleccionada()
        if not s:
            return
        d = DialogoEditarSede(self, s)
        if d.exec():
            err = sedes.actualizar(s["id"], d.get_data())
            if err:
                QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(err))
                return
            self.cambiado = True
            self.refrescar(s["id"])

    def activar(self):
        s = self._seleccionada()
        if not s:
            return
        err = sedes.activar(s["id"], not s["activa"])
        if err:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(err))
            return
        self.cambiado = True
        self.refrescar(s["id"])

    def borrar(self):
        s = self._seleccionada()
        if not s:
            return
        r = QMessageBox.question(self, tt("sede_title", "Sedes"),
                                 tt("sede_confirmar_borrar", "¿Borrar la sede «{nombre}»?").format(nombre=s["nombre"]))
        if r != QMessageBox.StandardButton.Yes:
            return
        err = sedes.borrar(s["id"])
        if err:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(err))
            return
        self.cambiado = True
        self.refrescar()


class DialogoSeleccionSedes(QDialog):
    """Un tick por sede activa: las que puede ver un técnico. Sin ninguna marcada, las ve todas."""
    def __init__(self, parent=None, seleccionadas=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QCheckBox
        self.setWindowTitle(tt("sede_title_usuario", "Sedes que ve"))
        self.setModal(True)
        self.resize(340, 320)
        seleccionadas = set(seleccionadas or [])
        l = QVBoxLayout(self)
        ayuda = QLabel(tt("sede_ayuda_usuario", "Marca las sedes que puede ver. Sin ninguna marcada, las ve todas."))
        ayuda.setWordWrap(True)
        l.addWidget(ayuda)
        self._checks = []
        for s in sedes.listar():
            chk = QCheckBox(s["nombre"])
            chk.setChecked(s["id"] in seleccionadas)
            chk.setProperty("sede_id", s["id"])
            l.addWidget(chk)
            self._checks.append(chk)
        l.addStretch()
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b)

    def seleccion(self):
        return [c.property("sede_id") for c in self._checks if c.isChecked()]
