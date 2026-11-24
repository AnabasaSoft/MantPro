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

"""Usuarios, sesiones, contraseñas, auditoría y cierre de sesión."""

import os
from PyQt6.QtWidgets import QMessageBox, QDialog

from ...idiomas import t
from ..comun import resource_path, tt
from ..dialogos.usuarios import (DialogoLogin, DialogoGestionUsuarios, DialogoCambioPassword,
                                 DialogoSesiones)
from ...nucleo import usuarios

class AccionesUsuarios:
    """Usuarios, sesiones, contraseñas, auditoría y cierre de sesión.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def gestionar_nube(self):
        """Herramientas → MantPro Cloud (solo administradores): iniciar sesión con la
        cuenta de la nube y ver la licencia. Sin sesión, MantPro funciona igual en local."""
        if not usuarios.es_admin():
            return
        from ..dialogos.nube import DialogoNube
        DialogoNube(self).exec()

    def ver_auditoria(self):
        """Herramientas → Registro de cambios (solo administradores)."""
        if not usuarios.es_admin():
            return
        from ..dialogos.auditoria import DialogoRegistroCambios
        DialogoRegistroCambios(self).exec()

    def ver_revisiones_almacen(self):
        """Herramientas → Historial de revisiones del almacén (solo administradores):
        quién hizo cada día la revisión de los 5 artículos y si los revisó todos."""
        if not usuarios.es_admin():
            return
        from ..dialogos.revisiones_almacen import DialogoRevisionesAlmacen
        elegida = self.sede_filtro() if hasattr(self, "sede_filtro") else None
        DialogoRevisionesAlmacen(self, self._festivos_iso(), festivos_de=self._festivos_iso_de_sede,
                                 sede=elegida if isinstance(elegida, int) else None).exec()

    def _festivos_iso_de_sede(self, sede_id):
        """Festivos ya descargados de una sede (los suyos si tiene región propia)."""
        from ...nucleo import sedes
        gestor = getattr(self, "gestor_festivos", None)
        if gestor is None:
            return set()
        anterior = gestor.sede
        try:
            gestor.sede = sedes.obtener(sede_id)
            return self._festivos_iso()
        finally:
            gestor.sede = anterior

    def _festivos_iso(self):
        """Festivos del año ya descargados ('AAAA-MM-DD'), sin ir a internet:
        solo se usa la caché, para no bloquear la ventana si no hay conexión."""
        try:
            if not self.gestor_festivos.cargar_cache():
                return set()
            return {d.toString("yyyy-MM-dd") for d in self.gestor_festivos.obtener_festivos()}
        except Exception:
            return set()

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

    def gestionar_checklists(self):
        """Herramientas → Listas de comprobación (plantillas)."""
        if not usuarios.es_admin(): return
        from ..dialogos.checklists import DialogoPlantillasChecklist
        DialogoPlantillasChecklist(self).exec()
        # Los combos y los iconos ☑️ de avisos y pendientes
        self.refresh_avisos(); self.refresh_todos()

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

        ruta_logo = resource_path(os.path.join("recursos", "icono.png"))
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
        if getattr(self, "_modo_operario", False) != usuarios.es_operario():
            self.recargar_interfaz_completa()       # de operario a otro rol o al revés: otras pestañas
            return
        self.refresh_all()
