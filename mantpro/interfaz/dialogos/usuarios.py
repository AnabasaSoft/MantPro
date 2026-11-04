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

"""
dialogos_usuarios.py — Interfaz PyQt6 para login y administración de usuarios.

Depende de usuarios.py. Los textos pasan por t() para encajar con idiomas.py;
si esa función no está disponible, se usa el literal en español.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QComboBox,
    QCheckBox, QHeaderView, QAbstractItemView, QDialogButtonBox, QWidget, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

import os
from datetime import datetime
from ...nucleo import seguridad, usuarios

try:
    from ...idiomas import t as _t  # t(clave) del proyecto: devuelve la clave si falta
    from ... import idiomas as _idiomas
except Exception:  # pragma: no cover
    _t = None
    _idiomas = None


def t(clave, defecto=None):
    """t() con texto por defecto, compatible con la firma t(clave) de idiomas.py."""
    if _t is None:
        return defecto if defecto is not None else clave
    valor = _t(clave)
    if valor == clave and defecto is not None:
        return defecto
    return valor


def _formatear_fecha(iso):
    """Convierte un ISO datetime (guardado en BD) a 'HH:MM:SS' + fecha corta del idioma activo."""
    if not iso:
        return "—"
    try:
        dt_obj = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    if _idiomas is not None:
        fecha_txt = _idiomas.formato_fecha_localizada(dt_obj.strftime("%Y-%m-%d"))
    else:
        fecha_txt = dt_obj.strftime("%d/%m/%Y")
    return f"{dt_obj.strftime('%H:%M:%S')} {fecha_txt}"


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
        self.campo_login = QComboBox()
        self.campo_login.setEditable(True)
        self.campo_login.lineEdit().setPlaceholderText(t("login_usuario", "Usuario"))
        try:
            activos = usuarios.listar_usuarios(incluir_inactivos=False)
        except Exception:
            activos = []
        for u in activos:
            self.campo_login.addItem(u["login"])
        ultimo = usuarios.obtener_ultimo_usuario()
        if ultimo:
            indice = self.campo_login.findText(ultimo)
            if indice >= 0:
                self.campo_login.setCurrentIndex(indice)
            else:
                self.campo_login.setCurrentText(ultimo)
        else:
            self.campo_login.setCurrentText("")

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
        self.campo_login.lineEdit().returnPressed.connect(self.campo_password.setFocus)

        if ultimo:
            self.campo_password.setFocus()

    def _intentar(self):
        login = self.campo_login.currentText().strip()
        password = self.campo_password.text()
        if not login or not password:
            self.aviso.setText(t("login_vacio", "Introduce usuario y contraseña."))
            return

        # Tras varios fallos seguidos se bloquea ese usuario un minuto (ver
        # nucleo/seguridad.py); lo que se intente desde la red va aparte.
        clave = login.lower()
        espera = seguridad.LOGIN_LOCAL.segundos_bloqueo(clave)
        if espera:
            self.aviso.setText(t("login_bloqueado_seg", "Demasiados intentos fallidos. Espera {seg} segundos.").format(seg=espera))
            return
        usuario = usuarios.autenticar(login, password)
        if usuario is None:
            if seguridad.LOGIN_LOCAL.fallo(clave):
                usuarios.registrar_auditoria(
                    0, None, "bloquear", f"Bloqueado {seguridad.LOGIN_LOCAL.bloqueo} segundos por intentos fallidos",
                    "seguridad", objeto=f"Inicio de sesión de «{login}» en el PC", origen="💻 PC")
            self.aviso.setText(t("login_error", "Usuario o contraseña incorrectos."))
            self.campo_password.clear()
            self.campo_password.setFocus()
            return
        seguridad.LOGIN_LOCAL.acierto(clave)

        if usuario["debe_cambiar"]:
            dlg = DialogoCambioPassword(self, usuario, obligatorio=True)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                self.aviso.setText(
                    t("login_cambio_requerido", "Debes cambiar la contraseña para entrar."))
                return
            usuario["debe_cambiar"] = False

        self.usuario = usuario
        usuarios.SESION_ACTUAL = usuario
        usuarios.guardar_ultimo_usuario(usuario["login"])
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

class DialogoEspecialidades(QDialog):
    """CRUD del catálogo de especialidades (p.ej. Electricista, Mecánico...)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("especialidades_titulo", "Especialidades"))
        self.setModal(True)
        self.resize(360, 400)

        layout = QVBoxLayout(self)

        self.tabla = QTableWidget(0, 2)
        self.tabla.setHorizontalHeaderLabels([t("especialidades_col_nombre", "Nombre"), "ID"])
        self.tabla.setColumnHidden(1, True)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

        alta = QHBoxLayout()
        self.nueva_especialidad = QLineEdit()
        self.nueva_especialidad.setPlaceholderText(t("especialidades_col_nombre", "Nombre"))
        boton_alta = QPushButton(t("usuarios_anadir", "➕ Añadir"))
        alta.addWidget(self.nueva_especialidad, 1)
        alta.addWidget(boton_alta)
        layout.addLayout(alta)

        acciones = QHBoxLayout()
        boton_renombrar = QPushButton(t("especialidades_renombrar", "✏️ Renombrar"))
        boton_borrar = QPushButton(t("especialidades_borrar", "🗑️ Borrar"))
        boton_cerrar = QPushButton(t("cerrar", "Cerrar"))
        acciones.addWidget(boton_renombrar)
        acciones.addWidget(boton_borrar)
        acciones.addStretch()
        acciones.addWidget(boton_cerrar)
        layout.addLayout(acciones)

        boton_alta.clicked.connect(self._anadir)
        boton_renombrar.clicked.connect(self._renombrar)
        boton_borrar.clicked.connect(self._borrar)
        boton_cerrar.clicked.connect(self.accept)

        self.refrescar()

    def refrescar(self):
        datos = usuarios.listar_especialidades()
        self.tabla.setRowCount(len(datos))
        for fila, e in enumerate(datos):
            self.tabla.setItem(fila, 0, QTableWidgetItem(e["nombre"]))
            self.tabla.setItem(fila, 1, QTableWidgetItem(str(e["id"])))

    def _seleccionada(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.information(
                self, t("aviso", "Aviso"),
                t("especialidades_selecciona", "Selecciona una especialidad de la lista."))
            return None
        return int(self.tabla.item(fila, 1).text())

    def _anadir(self):
        ok, mensaje = usuarios.crear_especialidad(self.nueva_especialidad.text())
        if ok:
            self.nueva_especialidad.clear()
            self.refrescar()
        else:
            QMessageBox.warning(self, t("aviso", "Aviso"), mensaje)

    def _renombrar(self):
        eid = self._seleccionada()
        if eid is None:
            return
        fila = self.tabla.currentRow()
        actual = self.tabla.item(fila, 0).text()
        dlg = QDialog(self)
        dlg.setWindowTitle(t("especialidades_renombrar", "✏️ Renombrar"))
        lay = QVBoxLayout(dlg)
        campo = QLineEdit(actual)
        lay.addWidget(campo)
        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.accepted.connect(dlg.accept); caja.rejected.connect(dlg.reject)
        lay.addWidget(caja)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        ok, mensaje = usuarios.renombrar_especialidad(eid, campo.text())
        if not ok:
            QMessageBox.warning(self, t("aviso", "Aviso"), mensaje)
        self.refrescar()

    def _borrar(self):
        eid = self._seleccionada()
        if eid is None:
            return
        respuesta = QMessageBox.question(
            self, t("aviso", "Aviso"),
            t("especialidades_confirmar_borrar",
              "¿Borrar esta especialidad? Los usuarios, trabajos y avisos que la "
              "tuvieran asignada quedarán sin especialidad."))
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        usuarios.borrar_especialidad(eid)
        self.refrescar()


class DialogoSeleccionEspecialidades(QDialog):
    """Ventana con un tick por especialidad, para que un técnico pueda tener
    más de una a la vez (en vez del desplegable de selección única de antes)."""

    def __init__(self, parent=None, seleccionadas=None):
        super().__init__(parent)
        self.setWindowTitle(t("usuarios_cambiar_especialidad", "🔧 Especialidad"))
        self.setModal(True)
        self.resize(320, 320)
        seleccionadas = set(seleccionadas or [])

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(t("usuarios_col_especialidad", "Especialidad") + ":"))

        self._checks = []
        datos = usuarios.listar_especialidades()
        if not datos:
            layout.addWidget(QLabel(t("especialidades_ninguna", "Sin especialidad")))
        for e in datos:
            chk = QCheckBox(e["nombre"])
            chk.setChecked(e["id"] in seleccionadas)
            chk.setProperty("especialidad_id", e["id"])
            layout.addWidget(chk)
            self._checks.append(chk)
        layout.addStretch()

        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.accepted.connect(self.accept); caja.rejected.connect(self.reject)
        layout.addWidget(caja)

    def seleccion(self):
        """Ids de las especialidades marcadas."""
        return [chk.property("especialidad_id") for chk in self._checks if chk.isChecked()]


class DialogoGestionUsuarios(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("usuarios_titulo", "Gestión de usuarios"))
        self.setModal(True)
        self.resize(820, 420)

        layout = QVBoxLayout(self)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels([
            t("usuarios_col_login", "Usuario"),
            t("usuarios_col_nombre", "Nombre"),
            t("usuarios_col_rol", "Rol"),
            t("usuarios_col_especialidad", "Especialidad"),
            t("usuarios_col_estado", "Estado"),
            t("usuarios_col_acceso", "Último acceso"),
            "ID",
        ])
        self.tabla.setColumnHidden(6, True)
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
        self.selector_roles, self.chk_rol_tecnico, self.chk_rol_almacen, self.chk_rol_admin = \
            self._crear_selector_roles()
        self._especialidades_alta_ids = []
        self.boton_especialidad_alta = QPushButton()
        self.boton_especialidad_alta.clicked.connect(self._elegir_especialidades_alta)
        self._actualizar_boton_especialidades_alta()
        self.chk_cambiar = QCheckBox(t("usuarios_forzar_cambio", "Pedir cambio al entrar"))
        self.chk_cambiar.setChecked(True)
        boton_alta = QPushButton(t("usuarios_anadir", "➕ Añadir"))
        for w in (self.nuevo_login, self.nuevo_nombre, self.nueva_password,
                  self.selector_roles, self.boton_especialidad_alta, self.chk_cambiar, boton_alta):
            alta.addWidget(w)
        layout.addLayout(alta)

        # --- acciones sobre el seleccionado ---
        acciones = QHBoxLayout()
        boton_reset = QPushButton(t("usuarios_reset", "🔑 Restablecer contraseña"))
        boton_rol = QPushButton(t("usuarios_cambiar_rol", "🎚 Cambiar rol"))
        boton_especialidad = QPushButton(t("usuarios_cambiar_especialidad", "🔧 Especialidad"))
        boton_estado = QPushButton(t("usuarios_activar", "🚫 Activar / Desactivar"))
        boton_gestionar_especialidades = QPushButton(t("especialidades_titulo", "Especialidades") + "...")
        boton_cerrar = QPushButton(t("cerrar", "Cerrar"))
        acciones.addWidget(boton_reset)
        acciones.addWidget(boton_rol)
        acciones.addWidget(boton_especialidad)
        acciones.addWidget(boton_estado)
        acciones.addStretch()
        acciones.addWidget(boton_gestionar_especialidades)
        acciones.addWidget(boton_cerrar)
        layout.addLayout(acciones)

        boton_alta.clicked.connect(self._anadir)
        boton_reset.clicked.connect(self._reset)
        boton_rol.clicked.connect(self._cambiar_rol)
        boton_especialidad.clicked.connect(self._cambiar_especialidad)
        boton_estado.clicked.connect(self._alternar_estado)
        boton_gestionar_especialidades.clicked.connect(self._gestionar_especialidades)
        boton_cerrar.clicked.connect(self.accept)

        self.refrescar()

    # -------------------------------------------------- helpers

    @staticmethod
    def _texto_roles(roles):
        etiquetas = {
            "admin": t("rol_admin", "Administrador"),
            "almacen": t("rol_almacen", "Almacén"),
            "tecnico": t("rol_tecnico", "Técnico"),
        }
        return ", ".join(etiquetas.get(r, r) for r in (roles or ["tecnico"]))

    def _crear_selector_roles(self, roles_iniciales=("tecnico",)):
        """Casillas para elegir uno o varios roles (técnico y/o almacén).
        Administrador es exclusivo: al marcarlo se desmarcan y bloquean los otros."""
        chk_tecnico = QCheckBox(t("rol_tecnico", "Técnico"))
        chk_almacen = QCheckBox(t("rol_almacen", "Almacén"))
        chk_admin = QCheckBox(t("rol_admin", "Administrador"))
        chk_tecnico.setChecked("tecnico" in roles_iniciales)
        chk_almacen.setChecked("almacen" in roles_iniciales)
        chk_admin.setChecked("admin" in roles_iniciales)

        def _al_marcar_admin(marcado):
            if marcado:
                chk_tecnico.setChecked(False)
                chk_almacen.setChecked(False)
            chk_tecnico.setEnabled(not marcado)
            chk_almacen.setEnabled(not marcado)

        def _al_marcar_otro(_marcado):
            if chk_tecnico.isChecked() or chk_almacen.isChecked():
                chk_admin.setChecked(False)

        chk_admin.toggled.connect(_al_marcar_admin)
        chk_tecnico.toggled.connect(_al_marcar_otro)
        chk_almacen.toggled.connect(_al_marcar_otro)
        _al_marcar_admin(chk_admin.isChecked())

        contenedor = QWidget()
        lay = QHBoxLayout(contenedor)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(chk_tecnico)
        lay.addWidget(chk_almacen)
        lay.addWidget(chk_admin)
        return contenedor, chk_tecnico, chk_almacen, chk_admin

    @staticmethod
    def _roles_marcados(chk_tecnico, chk_almacen, chk_admin):
        return [r for chk, r in (
            (chk_tecnico, "tecnico"), (chk_almacen, "almacen"), (chk_admin, "admin")
        ) if chk.isChecked()]

    @staticmethod
    def _llenar_combo_especialidades(combo, incluir_ninguna=True):
        combo.clear()
        if incluir_ninguna:
            combo.addItem(t("especialidades_ninguna", "Sin especialidad"), None)
        for e in usuarios.listar_especialidades():
            combo.addItem(e["nombre"], e["id"])

    def _actualizar_boton_especialidades_alta(self):
        nombres = [e["nombre"] for e in usuarios.listar_especialidades()
                   if e["id"] in self._especialidades_alta_ids]
        texto = ", ".join(nombres) if nombres else t("especialidades_ninguna", "Sin especialidad")
        self.boton_especialidad_alta.setText("🔧 " + texto)

    def _elegir_especialidades_alta(self):
        dlg = DialogoSeleccionEspecialidades(self, self._especialidades_alta_ids)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._especialidades_alta_ids = dlg.seleccion()
        self._actualizar_boton_especialidades_alta()

    def refrescar(self):
        datos = usuarios.listar_usuarios()
        self.tabla.setRowCount(len(datos))
        for fila, u in enumerate(datos):
            valores = [
                u["login"],
                u["nombre"],
                self._texto_roles(u.get("roles")),
                ", ".join(u.get("especialidad_nombres") or []) or "—",
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
        return int(self.tabla.item(fila, 6).text())

    # -------------------------------------------------- acciones

    def _anadir(self):
        roles = self._roles_marcados(self.chk_rol_tecnico, self.chk_rol_almacen, self.chk_rol_admin)
        ok, mensaje = usuarios.crear_usuario(
            self.nuevo_login.text(),
            self.nuevo_nombre.text(),
            self.nueva_password.text(),
            roles,
            self.chk_cambiar.isChecked(),
            self._especialidades_alta_ids,
        )
        if ok:
            self.nuevo_login.clear(); self.nuevo_nombre.clear(); self.nueva_password.clear()
            self.chk_rol_tecnico.setChecked(True)
            self.chk_rol_almacen.setChecked(False)
            self.chk_rol_admin.setChecked(False)
            self._especialidades_alta_ids = []
            self._actualizar_boton_especialidades_alta()
            self.refrescar()
        else:
            QMessageBox.warning(self, t("aviso", "Aviso"), mensaje)

    def _cambiar_especialidad(self):
        uid = self._seleccionado()
        if uid is None:
            return
        actual = next((u for u in usuarios.listar_usuarios() if u["id"] == uid), None)

        dlg = DialogoSeleccionEspecialidades(self, actual.get("especialidad_ids"))
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        ok, mensaje = usuarios.actualizar_usuario(uid, especialidad_ids=dlg.seleccion())
        if not ok:
            QMessageBox.warning(self, t("aviso", "Aviso"), mensaje)
        self.refrescar()

    def _gestionar_especialidades(self):
        DialogoEspecialidades(self).exec()
        ids_validos = {e["id"] for e in usuarios.listar_especialidades()}
        self._especialidades_alta_ids = [i for i in self._especialidades_alta_ids if i in ids_validos]
        self._actualizar_boton_especialidades_alta()
        self.refrescar()

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
        roles_actuales = actual.get("roles") or [actual["rol"]]

        dlg = QDialog(self)
        dlg.setWindowTitle(t("usuarios_cambiar_rol", "🎚 Cambiar rol"))
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(t("usuarios_col_rol", "Rol") + ":"))
        selector, chk_tecnico, chk_almacen, chk_admin = self._crear_selector_roles(roles_actuales)
        lay.addWidget(selector)
        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.accepted.connect(dlg.accept); caja.rejected.connect(dlg.reject)
        lay.addWidget(caja)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        roles = self._roles_marcados(chk_tecnico, chk_almacen, chk_admin)
        ok, mensaje = usuarios.actualizar_usuario(uid, roles=roles)
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


class _ItemFecha(QTableWidgetItem):
    """Muestra la fecha formateada pero ordena por el valor ISO real subyacente."""

    def __init__(self, iso):
        super().__init__(_formatear_fecha(iso))
        self._iso = iso or ""

    def __lt__(self, otro):
        if isinstance(otro, _ItemFecha):
            return self._iso < otro._iso
        return super().__lt__(otro)


class DialogoSesiones(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("sesiones_titulo", "Sesiones de dispositivos"))
        self.setModal(True)
        self.resize(980, 420)

        layout = QVBoxLayout(self)

        self.tabla = QTableWidget(0, 10)
        self.tabla.setHorizontalHeaderLabels([
            t("sesiones_col_usuario", "Usuario"),
            t("sesiones_col_dispositivo", "Dispositivo"),
            t("sesiones_col_iniciada", "Iniciada"),
            t("sesiones_col_expira", "Expira"),
            t("sesiones_col_estado", "Estado"),
            t("sesiones_col_conexion", "Conexión"),
            t("sesiones_col_ultimo_contacto", "Último contacto"),
            t("sesiones_col_cifrado", "Cifrado"),
            t("sesiones_col_adjudicado", "Móvil de"),
            "token",
        ])
        self.tabla.setColumnHidden(self.COL_TOKEN, True)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tabla.setSortingEnabled(True)
        cabecera = self.tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cabecera.setStretchLastSection(False)
        layout.addWidget(self.tabla)

        # Conexión sin cifrar (HTTP), que se mantiene para las apps antiguas
        fila_http = QHBoxLayout()
        self.lbl_http = QLabel()
        self.lbl_http.setWordWrap(True)
        self.boton_http = QPushButton()
        self.boton_http.clicked.connect(self._cambiar_http)
        fila_http.addWidget(self.lbl_http, 1)
        fila_http.addWidget(self.boton_http)
        layout.addLayout(fila_http)

        # Caducidad de las sesiones por inactividad (cada conexión las renueva)
        fila_dias = QHBoxLayout()
        fila_dias.addWidget(QLabel(t("sesiones_caducidad",
            "🕒 Cerrar las sesiones de los móviles que lleven sin conectar con el PC:")))
        self.combo_dias = QComboBox()
        for dias in usuarios.OPCIONES_DIAS_SESION:
            self.combo_dias.addItem(t("sesiones_dias", "{n} días").format(n=dias), dias)
        actual = usuarios.dias_sesion()
        if self.combo_dias.findData(actual) < 0:
            self.combo_dias.addItem(t("sesiones_dias", "{n} días").format(n=actual), actual)
        self.combo_dias.setCurrentIndex(self.combo_dias.findData(actual))
        self.combo_dias.setToolTip(t("tt_sesiones_caducidad",
            "Cada vez que el móvil conecta, su sesión se renueva: quien usa la app no tiene que volver a entrar. "
            "Una sesión que pase este tiempo sin conectar (un móvil perdido o de alguien que ya no está) se cierra sola; "
            "lo que tuviera sin enviar no se pierde y se envía al volver a iniciar sesión."))
        self.combo_dias.currentIndexChanged.connect(self._cambiar_dias)
        fila_dias.addWidget(self.combo_dias); fila_dias.addStretch()
        layout.addLayout(fila_dias)

        acciones = QHBoxLayout()
        boton_actualizar = QPushButton(t("sesiones_actualizar", "🔄 Actualizar"))
        boton_revocar = QPushButton(t("sesiones_revocar", "🚫 Revocar sesión"))
        boton_adjudicar = QPushButton(t("sesiones_adjudicar", "📲 Adjudicar móvil a un técnico…"))
        boton_adjudicar.setToolTip(t("tt_sesiones_adjudicar",
            "El móvil solo deja iniciar sesión a su técnico (también en MantPro Stock) y la app le rellena el usuario. "
            "Los administradores pueden entrar siempre."))
        boton_cerrar = QPushButton(t("cerrar", "Cerrar"))
        acciones.addWidget(boton_actualizar)
        acciones.addWidget(boton_revocar)
        acciones.addWidget(boton_adjudicar)
        acciones.addStretch()
        acciones.addWidget(boton_cerrar)
        layout.addLayout(acciones)

        boton_actualizar.clicked.connect(self.refrescar)
        boton_revocar.clicked.connect(self._revocar)
        boton_adjudicar.clicked.connect(self._adjudicar)
        boton_cerrar.clicked.connect(self.accept)

        self.refrescar()

        # Mientras la ventana está abierta, la conexión de cada móvil se
        # actualiza sola (solo esas columnas, para no perder la selección).
        self._temporizador = QTimer(self)
        self._temporizador.timeout.connect(self._actualizar_conexion)
        self._temporizador.start(5000)

    COL_CONEXION, COL_ULTIMO_CONTACTO, COL_CIFRADO, COL_ADJUDICADO, COL_TOKEN = 5, 6, 7, 8, 9

    @staticmethod
    def _texto_cifrado(s):
        if s.get("cifrada") is True:
            return t("sesiones_cifrada", "🔒 Cifrada")
        if s.get("cifrada") is False:
            return t("sesiones_sin_cifrar", "⚠️ Sin cifrar (app antigua)")
        return "—"

    @staticmethod
    def _texto_conexion(s):
        if s.get("en_linea"):
            return t("sesiones_en_linea", "🟢 En línea")
        return t("sesiones_sin_conexion", "⚫ Sin conexión")

    def _pintar_conexion(self, fila, s):
        item = self.tabla.item(fila, self.COL_CONEXION)
        item.setText(self._texto_conexion(s))
        if s.get("en_linea"):
            item.setForeground(Qt.GlobalColor.darkGreen)
        elif s["activa"]:
            item.setForeground(self.tabla.palette().text())
        contacto = self.tabla.item(fila, self.COL_ULTIMO_CONTACTO)
        contacto.setText(_formatear_fecha(s.get("ultimo_contacto")))
        contacto._iso = s.get("ultimo_contacto") or ""
        cifrado = self.tabla.item(fila, self.COL_CIFRADO)
        cifrado.setText(self._texto_cifrado(s))
        if s["activa"] and s.get("cifrada") is False:
            cifrado.setForeground(Qt.GlobalColor.darkYellow)

    def _actualizar_conexion(self):
        por_token = {s["token"]: s for s in usuarios.listar_sesiones()}
        # Sin reordenar a mitad del recorrido si se ordenó por esta columna
        self.tabla.setSortingEnabled(False)
        for fila in range(self.tabla.rowCount()):
            s = por_token.get(self.tabla.item(fila, self.COL_TOKEN).text())
            if s is not None:
                self._pintar_conexion(fila, s)
        self.tabla.setSortingEnabled(True)
        self._pintar_http()

    def refrescar(self):
        datos = usuarios.listar_sesiones()
        self.tabla.setSortingEnabled(False)
        self.tabla.setRowCount(len(datos))
        for fila, s in enumerate(datos):
            usuario_txt = f"{s['nombre']} ({s['login']})" if s.get("nombre") else s["login"]
            columnas = [
                QTableWidgetItem(usuario_txt),
                QTableWidgetItem(s.get("dispositivo") or "—"),
                _ItemFecha(s.get("creado")),
                _ItemFecha(s.get("expira")),
                QTableWidgetItem(t("sesiones_activa", "Activa") if s["activa"] else t("sesiones_expirada", "Expirada")),
                QTableWidgetItem(self._texto_conexion(s)),
                _ItemFecha(s.get("ultimo_contacto")),
                QTableWidgetItem(self._texto_cifrado(s)),
                QTableWidgetItem(s.get("adjudicado_nombre") or "—"),
                QTableWidgetItem(s["token"]),
            ]
            for col, item in enumerate(columnas):
                if not s["activa"]:
                    item.setForeground(Qt.GlobalColor.gray)
                self.tabla.setItem(fila, col, item)
            self._pintar_conexion(fila, s)
        self.tabla.setSortingEnabled(True)
        self._pintar_http()

    def _cambiar_dias(self, _i):
        usuarios.fijar_dias_sesion(self.combo_dias.currentData())
        self.refrescar()

    def _pintar_http(self):
        if usuarios.http_desactivado():
            self.lbl_http.setText(t("sesiones_http_desactivado",
                "🔒 Conexión sin cifrar desactivada: el PC solo atiende a los móviles por la conexión cifrada."))
            self.boton_http.setText(t("btn_activar_http", "Volver a permitir la conexión sin cifrar"))
            return
        pendientes = len(usuarios.sesiones_sin_cifrar())
        if pendientes:
            texto = t("sesiones_http_pendientes",
                "⚠️ {n} móviles se conectan todavía sin cifrar (con una app anterior a la 3.10.3). "
                "Actualiza su app antes de desactivar la conexión sin cifrar.").format(n=pendientes)
        else:
            texto = t("sesiones_http_listo",
                "Ningún móvil usa ya la conexión sin cifrar: puedes desactivarla.")
        self.lbl_http.setText(texto)
        self.boton_http.setText(t("btn_desactivar_http", "Desactivar la conexión sin cifrar"))

    def _cambiar_http(self):
        titulo = t("sesiones_titulo", "Sesiones de dispositivos")
        if usuarios.http_desactivado():
            usuarios.fijar_http_desactivado(False)
            usuarios.auditar("seguridad", "configurar", "Conexión sin cifrar (HTTP) permitida otra vez")
            self._pintar_http()
            return
        pendientes = usuarios.sesiones_sin_cifrar()
        texto = t("msg_confirmar_desactivar_http",
            "Los móviles con una app anterior a la 3.10.3 dejarán de sincronizar hasta que se actualice. "
            "Los vinculados con el QR antiguo y la app ya actualizada pasan solos a la conexión cifrada.\n\n¿Desactivar la conexión sin cifrar?")
        if pendientes:
            nombres = "\n".join(f"• {s.get('nombre') or s['login']} — {s.get('dispositivo') or '—'}" for s in pendientes[:10])
            texto = t("msg_desactivar_http_pendientes",
                "Estos móviles se conectan todavía sin cifrar y dejarán de sincronizar hasta que se actualice su app:") + "\n\n" + nombres + "\n\n" + texto
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning if pendientes else QMessageBox.Icon.Question)
        msg.setWindowTitle(titulo)
        msg.setText(texto)
        btn_si = msg.addButton(t("btn_desactivar_http", "Desactivar la conexión sin cifrar"), QMessageBox.ButtonRole.AcceptRole)
        msg.addButton(t("btn_cancelar", "Cancelar"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() != btn_si:
            return
        usuarios.fijar_http_desactivado(True)
        usuarios.auditar("seguridad", "configurar", "Conexión sin cifrar (HTTP) desactivada")
        self._pintar_http()

    def _tokens_seleccionados(self):
        filas = {i.row() for i in self.tabla.selectedIndexes()}
        if not filas:
            QMessageBox.information(
                self, t("aviso", "Aviso"),
                t("sesiones_selecciona", "Selecciona una sesión de la lista."))
            return []
        return [self.tabla.item(fila, self.COL_TOKEN).text() for fila in filas]

    def _adjudicar(self):
        """Adjudica el móvil de la fila seleccionada a un técnico (o lo deja
        libre). Vale para las dos apps: comparten el identificador del móvil."""
        filas = sorted({i.row() for i in self.tabla.selectedItems()})
        if not filas:
            QMessageBox.information(self, t("sesiones_titulo", "Sesiones de dispositivos"),
                                    t("msg_adjudicar_elige", "Selecciona primero una sesión del móvil."))
            return
        token = self.tabla.item(filas[0], self.COL_TOKEN).text()
        s = next((x for x in usuarios.listar_sesiones() if x["token"] == token), None)
        if s is None:
            return
        if not s.get("dispositivo_id"):
            QMessageBox.information(self, t("sesiones_titulo", "Sesiones de dispositivos"),
                                    t("msg_adjudicar_sin_id",
                                      "Este móvil aún no manda su identificador: actualiza la app y que vuelva a iniciar sesión."))
            return
        nadie = t("adjudicar_nadie", "— Nadie (móvil libre) —")
        tecnicos = usuarios.listar_usuarios(incluir_inactivos=False)
        opciones = [nadie] + [f"{u['nombre']} ({u['login']})" for u in tecnicos]
        actual = 0
        for i, u in enumerate(tecnicos, 1):
            if u["id"] == s.get("adjudicado_id"):
                actual = i
        elegido, ok = QInputDialog.getItem(
            self, t("sesiones_adjudicar_titulo", "Adjudicar móvil"),
            t("sesiones_adjudicar_texto", "Técnico al que se adjudica «{movil}»:").format(movil=s.get("dispositivo") or "—"),
            opciones, actual, False)
        if not ok:
            return
        indice = opciones.index(elegido)
        usuarios.adjudicar_movil(s["dispositivo_id"], tecnicos[indice - 1]["id"] if indice else None)
        self.refrescar()

    def _revocar(self):
        tokens = self._tokens_seleccionados()
        if not tokens:
            return
        por_token = {s["token"]: s for s in usuarios.listar_sesiones()}
        for token in tokens:
            s = por_token.get(token, {})
            usuarios.revocar_token(token)
            usuarios.auditar("seguridad", "revocar", f"{s.get('nombre') or s.get('login', '')} — {s.get('dispositivo') or '?'}",
                             detalle="Sesión del móvil revocada: tendrá que volver a iniciar sesión")
        self.refrescar()
