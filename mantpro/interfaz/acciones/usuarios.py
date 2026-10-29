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

"""Usuarios, sesiones, contraseñas, auditoría y cierre de sesión."""

import os
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
                             QAbstractItemView, QComboBox)

from ...idiomas import t
from ..comun import resource_path, tt
from ..dialogos.usuarios import (DialogoLogin, DialogoGestionUsuarios, DialogoCambioPassword,
                                 DialogoSesiones)
from ...nucleo import usuarios

class AccionesUsuarios:
    """Usuarios, sesiones, contraseñas, auditoría y cierre de sesión.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def ver_auditoria(self):
        if not usuarios.es_admin():
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(tt("menu_auditoria", "Registro de cambios"))
        dlg.resize(900, 500)
        lay = QVBoxLayout(dlg)

        fila = QHBoxLayout()
        fila.addWidget(QLabel(tt("hdr_realizado_por", "Realizado por") + ":"))
        combo_u = QComboBox()
        combo_u.addItem(tt("filtro_todos", "Todos"), "TODOS")
        for u in usuarios.listar_usuarios(incluir_inactivos=True):
            combo_u.addItem(u["nombre"], u["id"])
        fila.addWidget(combo_u)

        fila.addWidget(QLabel(tt("lbl_accion", "Acción") + ":"))
        combo_a = QComboBox()
        combo_a.addItem(tt("filtro_todos", "Todos"), "TODOS")
        combo_a.addItem(tt("accion_editar", "Editar"), "editar")
        combo_a.addItem(tt("accion_borrar", "Borrar"), "borrar")
        combo_a.addItem(tt("accion_revertir", "Revertir a pendiente"), "revertir")
        fila.addWidget(combo_a)
        lay.addLayout(fila)

        tabla = QTableWidget(0, 5)
        tabla.setHorizontalHeaderLabels([
            tt("lbl_fecha_hora", "Fecha y hora"),
            tt("hdr_realizado_por", "Realizado por"),
            tt("lbl_accion", "Acción"),
            "ID",
            tt("lbl_detalle", "Detalle"),
        ])
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setColumnWidth(0, 150)
        tabla.setColumnWidth(1, 160)
        tabla.setColumnWidth(2, 100)
        tabla.setColumnWidth(3, 45)
        tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        tabla.setAlternatingRowColors(True)
        lay.addWidget(tabla)

        def refrescar(*_):
            uid = combo_u.currentData()
            accion = combo_a.currentData()
            registros = usuarios.obtener_auditoria(
                usuario_id=uid if uid != "TODOS" else None,
                accion=accion if accion != "TODOS" else None,
                limite=500)
            tabla.setRowCount(len(registros))
            for fila_n, r in enumerate(registros):
                tabla.setItem(fila_n, 0, QTableWidgetItem(r["fecha"]))
                tabla.setItem(fila_n, 1, QTableWidgetItem(r["usuario_nombre"]))
                accion_txt = {"editar": "✏️ Editado", "borrar": "🗑️ Borrado", "revertir": "↩️ Revertido a pendiente"}.get(r["accion"], r["accion"])
                tabla.setItem(fila_n, 2, QTableWidgetItem(accion_txt))
                tabla.setItem(fila_n, 3, QTableWidgetItem(str(r["tarea_id"])))
                tabla.setItem(fila_n, 4, QTableWidgetItem(r["detalle"]))

        combo_u.currentIndexChanged.connect(refrescar)
        combo_a.currentIndexChanged.connect(refrescar)
        refrescar()

        cerrar = QPushButton(t("cerrar"))
        cerrar.clicked.connect(dlg.accept)
        lay.addWidget(cerrar)
        dlg.exec()

    def gestionar_usuarios(self):
        if not usuarios.es_admin():
            QMessageBox.warning(self, t("title_error"),
                                tt("msg_solo_admin", "Solo un administrador puede gestionar usuarios."))
            return
        DialogoGestionUsuarios(self).exec()
        if hasattr(self, 'combo_asignar'):
            self._llenar_combo_usuarios(self.combo_asignar, incluir_sin_asignar=True)
            self._llenar_combo_usuarios(self.combo_filtro_todos, incluir_todos=True, incluir_sin_asignar=True)
        if hasattr(self, 'in_av_asignar'):
            self._llenar_combo_usuarios(self.in_av_asignar, incluir_sin_asignar=True)

    def gestionar_sesiones(self):
        if not usuarios.es_admin():
            QMessageBox.warning(self, t("title_error"),
                                tt("msg_solo_admin", "Solo un administrador puede gestionar usuarios."))
            return
        DialogoSesiones(self).exec()

    def cambiar_mi_password(self):
        if not usuarios.SESION_ACTUAL:
            return
        DialogoCambioPassword(self, usuarios.SESION_ACTUAL).exec()

    def cerrar_sesion(self):
        """Cierra la sesión actual y vuelve al login sin salir de la aplicación.
        Si se cancela el login, se cierra la aplicación como al pulsar 'Salir'."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tt("title_cerrar_sesion", "Cerrar sesión"))
        msg.setText(tt("msg_confirmar_cerrar_sesion",
                        "¿Seguro que quieres cerrar la sesión actual?"))
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() != btn_si:
            return

        usuarios.SESION_ACTUAL = None
        self.hide()

        ruta_logo = resource_path(os.path.join("recursos", "AnabasaSoft.png"))
        dlg_login = DialogoLogin(ruta_logo=ruta_logo if os.path.exists(ruta_logo) else None)
        if dlg_login.exec() != QDialog.DialogCode.Accepted:
            self.close()
            return

        self._refrescar_tras_cambio_usuario()
        self.show()
        self.raise_()
        self.activateWindow()

    def _refrescar_tras_cambio_usuario(self):
        """Reconstruye el menú (permisos según rol) y el título tras un login en caliente."""
        self.menuBar().clear()
        self.crear_menu()
        titulo_base = t("title_control_mantenimiento")
        if usuarios.SESION_ACTUAL:
            titulo_base += f"  —  👤 {usuarios.SESION_ACTUAL['nombre']}"
        self.setWindowTitle(titulo_base)
        self.refresh_all()
