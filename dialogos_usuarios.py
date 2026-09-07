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

"""
dialogos_usuarios.py — Interfaz PyQt6 para login y administración de usuarios.

Depende de usuarios.py. Los textos pasan por t() para encajar con idiomas.py;
si esa función no está disponible, se usa el literal en español.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QComboBox,
    QCheckBox, QHeaderView, QAbstractItemView, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

import os
import usuarios

try:
    from idiomas import t as _t  # t(clave) del proyecto: devuelve la clave si falta
except Exception:  # pragma: no cover
    _t = None


def t(clave, defecto=None):
    """t() con texto por defecto, compatible con la firma t(clave) de idiomas.py."""
    if _t is None:
        return defecto if defecto is not None else clave
    valor = _t(clave)
    if valor == clave and defecto is not None:
        return defecto
    return valor


# --------------------------------------------------------------------- login

class DialogoLogin(QDialog):
    """Diálogo modal de acceso. exec() == Accepted => usuarios.SESION_ACTUAL fijado."""

    def __init__(self, parent=None, ruta_logo="logo.png"):
        super().__init__(parent)
        self.setWindowTitle(t("login_titulo", "MantPro — Acceso"))
        self.setModal(True)
        self.setFixedWidth(360)
        self.usuario = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        if ruta_logo and os.path.exists(ruta_logo):
            logo = QLabel()
            pix = QPixmap(ruta_logo).scaledToWidth(
                180, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pix)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo)

        formulario = QFormLayout()
        self.campo_login = QLineEdit()
        self.campo_login.setPlaceholderText(t("login_usuario", "Usuario"))
        self.campo_password = QLineEdit()
        self.campo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_password.setPlaceholderText(t("login_password", "Contraseña"))
        formulario.addRow(t("login_usuario", "Usuario") + ":", self.campo_login)
        formulario.addRow(t("login_password", "Contraseña") + ":", self.campo_password)
        layout.addLayout(formulario)

        self.aviso = QLabel("")
        self.aviso.setStyleSheet("color: #c62828;")
        self.aviso.setWordWrap(True)
        layout.addWidget(self.aviso)

        botones = QHBoxLayout()
        self.boton_salir = QPushButton(t("salir", "Salir"))
        self.boton_entrar = QPushButton(t("login_entrar", "Entrar"))
        self.boton_entrar.setDefault(True)
        botones.addWidget(self.boton_salir)
        botones.addStretch()
        botones.addWidget(self.boton_entrar)
        layout.addLayout(botones)

        self.boton_entrar.clicked.connect(self._intentar)
        self.boton_salir.clicked.connect(self.reject)
        self.campo_password.returnPressed.connect(self._intentar)
        self.campo_login.returnPressed.connect(self.campo_password.setFocus)

    def _intentar(self):
        login = self.campo_login.text().strip()
        password = self.campo_password.text()
        if not login or not password:
            self.aviso.setText(t("login_vacio", "Introduce usuario y contraseña."))
            return

        usuario = usuarios.autenticar(login, password)
        if usuario is None:
            self.aviso.setText(t("login_error", "Usuario o contraseña incorrectos."))
            self.campo_password.clear()
            self.campo_password.setFocus()
            return

        if usuario["debe_cambiar"]:
            dlg = DialogoCambioPassword(self, usuario, obligatorio=True)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                self.aviso.setText(
                    t("login_cambio_requerido", "Debes cambiar la contraseña para entrar."))
                return
            usuario["debe_cambiar"] = False

        self.usuario = usuario
        usuarios.SESION_ACTUAL = usuario
        self.accept()


# --------------------------------------------------------- cambio de contraseña

class DialogoCambioPassword(QDialog):
    def __init__(self, parent, usuario, obligatorio=False):
        super().__init__(parent)
        self.usuario = usuario
        self.obligatorio = obligatorio
        self.setWindowTitle(t("password_titulo", "Cambiar contraseña"))
        self.setModal(True)
        self.setFixedWidth(360)

        layout = QVBoxLayout(self)
        if obligatorio:
            aviso = QLabel(t(
                "password_obligatorio",
                "Es tu primer acceso: define una contraseña nueva."))
            aviso.setWordWrap(True)
            layout.addWidget(aviso)

        formulario = QFormLayout()
        self.actual = QLineEdit(); self.actual.setEchoMode(QLineEdit.EchoMode.Password)
        self.nueva = QLineEdit(); self.nueva.setEchoMode(QLineEdit.EchoMode.Password)
        self.repetir = QLineEdit(); self.repetir.setEchoMode(QLineEdit.EchoMode.Password)
        formulario.addRow(t("password_actual", "Contraseña actual") + ":", self.actual)
        formulario.addRow(t("password_nueva", "Contraseña nueva") + ":", self.nueva)
        formulario.addRow(t("password_repetir", "Repetir") + ":", self.repetir)
        layout.addLayout(formulario)

        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.accepted.connect(self._guardar)
        caja.rejected.connect(self.reject)
        layout.addWidget(caja)

    def _guardar(self):
        if self.nueva.text() != self.repetir.text():
            QMessageBox.warning(self, t("aviso", "Aviso"),
                                t("password_no_coincide", "Las contraseñas no coinciden."))
            return
        ok, mensaje = usuarios.cambiar_password(
            self.usuario["id"], self.nueva.text(), self.actual.text())
        if not ok:
            QMessageBox.warning(self, t("aviso", "Aviso"), mensaje)
            return
        QMessageBox.information(self, t("ok", "Hecho"), mensaje)
        self.accept()


# --------------------------------------------------------- gestión (solo admin)

class DialogoGestionUsuarios(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("usuarios_titulo", "Gestión de usuarios"))
        self.setModal(True)
        self.resize(720, 420)

        layout = QVBoxLayout(self)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels([
            t("usuarios_col_login", "Usuario"),
            t("usuarios_col_nombre", "Nombre"),
            t("usuarios_col_rol", "Rol"),
            t("usuarios_col_estado", "Estado"),
            t("usuarios_col_acceso", "Último acceso"),
            "ID",
        ])
        self.tabla.setColumnHidden(5, True)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

        # --- alta ---
        alta = QHBoxLayout()
        self.nuevo_login = QLineEdit(); self.nuevo_login.setPlaceholderText(
            t("usuarios_col_login", "Usuario"))
        self.nuevo_nombre = QLineEdit(); self.nuevo_nombre.setPlaceholderText(
            t("usuarios_col_nombre", "Nombre completo"))
        self.nueva_password = QLineEdit()
        self.nueva_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.nueva_password.setPlaceholderText(t("login_password", "Contraseña"))
        self.combo_rol = QComboBox()
        self.combo_rol.addItem(t("rol_tecnico", "Técnico"), "tecnico")
        self.combo_rol.addItem(t("rol_admin", "Administrador"), "admin")
        self.chk_cambiar = QCheckBox(t("usuarios_forzar_cambio", "Pedir cambio al entrar"))
        self.chk_cambiar.setChecked(True)
        boton_alta = QPushButton(t("usuarios_anadir", "➕ Añadir"))
        for w in (self.nuevo_login, self.nuevo_nombre, self.nueva_password,
                  self.combo_rol, self.chk_cambiar, boton_alta):
            alta.addWidget(w)
        layout.addLayout(alta)

        # --- acciones sobre el seleccionado ---
        acciones = QHBoxLayout()
        boton_reset = QPushButton(t("usuarios_reset", "🔑 Restablecer contraseña"))
        boton_rol = QPushButton(t("usuarios_cambiar_rol", "🎚 Cambiar rol"))
        boton_estado = QPushButton(t("usuarios_activar", "🚫 Activar / Desactivar"))
        boton_cerrar = QPushButton(t("cerrar", "Cerrar"))
        acciones.addWidget(boton_reset)
        acciones.addWidget(boton_rol)
        acciones.addWidget(boton_estado)
        acciones.addStretch()
        acciones.addWidget(boton_cerrar)
        layout.addLayout(acciones)

        boton_alta.clicked.connect(self._anadir)
        boton_reset.clicked.connect(self._reset)
        boton_rol.clicked.connect(self._cambiar_rol)
        boton_estado.clicked.connect(self._alternar_estado)
        boton_cerrar.clicked.connect(self.accept)

        self.refrescar()

    # -------------------------------------------------- helpers

    def refrescar(self):
        datos = usuarios.listar_usuarios()
        self.tabla.setRowCount(len(datos))
        for fila, u in enumerate(datos):
            valores = [
                u["login"],
                u["nombre"],
                t("rol_admin", "Administrador") if u["rol"] == "admin"
                else t("rol_tecnico", "Técnico"),
                t("activo", "Activo") if u["activo"] else t("inactivo", "Inactivo"),
                u.get("ultimo_acceso") or "—",
                str(u["id"]),
            ]
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                if not u["activo"]:
                    item.setForeground(Qt.GlobalColor.gray)
                self.tabla.setItem(fila, col, item)

    def _seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(
                self, t("aviso", "Aviso"),
                t("usuarios_selecciona", "Selecciona un usuario de la lista."))
            return None
        return int(self.tabla.item(fila, 5).text())

    # -------------------------------------------------- acciones

    def _anadir(self):
        ok, mensaje = usuarios.crear_usuario(
            self.nuevo_login.text(),
            self.nuevo_nombre.text(),
            self.nueva_password.text(),
            self.combo_rol.currentData(),
            self.chk_cambiar.isChecked(),
        )
        if ok:
            self.nuevo_login.clear(); self.nuevo_nombre.clear(); self.nueva_password.clear()
            self.refrescar()
        else:
            QMessageBox.warning(self, t("aviso", "Aviso"), mensaje)

    def _reset(self):
        uid = self._seleccionado()
        if uid is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(t("usuarios_reset", "Restablecer contraseña"))
        lay = QVBoxLayout(dlg)
        campo = QLineEdit(); campo.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(QLabel(t("password_nueva", "Contraseña nueva") + ":"))
        lay.addWidget(campo)
        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.accepted.connect(dlg.accept); caja.rejected.connect(dlg.reject)
        lay.addWidget(caja)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        ok, mensaje = usuarios.cambiar_password(uid, campo.text(), forzar=True)
        QMessageBox.information(self, t("aviso", "Aviso"), mensaje)
        self.refrescar()

    def _cambiar_rol(self):
        uid = self._seleccionado()
        if uid is None:
            return
        actual = next((u for u in usuarios.listar_usuarios() if u["id"] == uid), None)
        nuevo = "tecnico" if actual["rol"] == "admin" else "admin"
        ok, mensaje = usuarios.actualizar_usuario(uid, rol=nuevo)
        if not ok:
            QMessageBox.warning(self, t("aviso", "Aviso"), mensaje)
        self.refrescar()

    def _alternar_estado(self):
        uid = self._seleccionado()
        if uid is None:
            return
        actual = next((u for u in usuarios.listar_usuarios() if u["id"] == uid), None)
        ok, mensaje = usuarios.actualizar_usuario(uid, activo=not actual["activo"])
        if not ok:
            QMessageBox.warning(self, t("aviso", "Aviso"), mensaje)
        self.refrescar()
