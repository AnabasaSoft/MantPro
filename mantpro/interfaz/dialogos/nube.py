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

"""Herramientas > MantPro Cloud: iniciar sesión con la cuenta de la nube y ver la licencia."""

import socket

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
                             QFormLayout, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices

from ...idiomas import t, formato_fecha_localizada
from ..comun import tt
from ...nucleo import nube

_ERRORES = {
    "sin_conexion": ("nube_error_sin_conexion",
                     "No se puede conectar con MantPro Cloud. Comprueba tu conexión a internet e inténtalo de nuevo."),
    "respuesta_no_valida": ("nube_error_respuesta",
                            "MantPro Cloud ha respondido algo inesperado. Inténtalo más tarde."),
    "credenciales": ("nube_error_credenciales", "Correo o contraseña incorrectos."),
    "demasiados_intentos": ("nube_error_intentos",
                            "Demasiados intentos fallidos. Espera 15 minutos antes de volver a probar."),
    "datos_incompletos": ("nube_error_datos", "Escribe el correo y la contraseña."),
    "url_no_valida": ("nube_error_url", "La dirección de MantPro Cloud no es segura (debe ser HTTPS)."),
    "sesion_caducada": ("nube_error_sesion",
                        "La sesión de MantPro Cloud ha caducado o se ha cerrado. Vuelve a iniciar sesión."),
    "sin_sesion": ("nube_error_sin_sesion", "No hay ninguna sesión iniciada."),
}

_ESTADOS = {
    "activa": ("nube_estado_activa", "Activa"),
    "gracia": ("nube_estado_gracia", "Caducada, en margen de gracia"),
    "vencida": ("nube_estado_vencida", "Caducada"),
    "suspendida": ("nube_estado_suspendida", "Suspendida"),
    "desconocida": ("nube_estado_desconocida", "Desconocido"),
}

_PLANES = {
    "prueba": ("nube_plan_prueba", "Prueba"),
    "pequena": ("nube_plan_pequena", "Pequeña empresa"),
    "empresa": ("nube_plan_empresa", "Empresa"),
}


def texto_error(codigo):
    """Traduce un código de error de la nube al idioma activo."""
    clave, defecto = _ERRORES.get(codigo, ("nube_error_otro", "No se ha podido completar la operación."))
    return tt(clave, defecto)


class _Hilo(QThread):
    """Ejecuta una función de red fuera del hilo de la ventana. Emite (resultado, código_error)."""
    terminado = pyqtSignal(object, object)

    def __init__(self, funcion, parent=None):
        super().__init__(parent)
        self._funcion = funcion

    def run(self):
        try:
            resultado, error = self._funcion()
        except Exception:
            resultado, error = None, "respuesta_no_valida"
        self.terminado.emit(resultado, error)


class DialogoNube(QDialog):
    """Sin sesión: formulario de acceso. Con sesión: cuenta, empresa y licencia."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_nube", "MantPro Cloud"))
        self.setModal(True)
        self.setMinimumWidth(460)
        self._hilo = None
        self.boton_entrar = self.boton_comprobar = self.boton_salir_sesion = self.aviso = None
        self._layout = QVBoxLayout(self)
        self._construir()

    # ------------------------------------------------------------ construcción
    def _vaciar(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            elif item.layout() is not None:
                self._vaciar_layout(item.layout())

    def _vaciar_layout(self, lay):
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            elif item.layout() is not None:
                self._vaciar_layout(item.layout())

    def _construir(self):
        self._vaciar()
        # Los botones y el aviso de la vista anterior ya no existen
        self.boton_entrar = self.boton_comprobar = self.boton_salir_sesion = self.aviso = None
        datos = nube.sesion()
        if datos:
            self._construir_con_sesion(datos)
        else:
            self._construir_sin_sesion()

    def _boton_web(self):
        """Botón que abre la web de MantPro Cloud en el navegador (contratar, renovar, información)."""
        b = QPushButton("🌐 " + tt("btn_nube_web", "Abrir la web"))
        b.setAutoDefault(False)
        b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(nube.URL_WEB)))
        return b

    def _etiqueta(self, texto, negrita=False):
        lbl = QLabel(texto)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        if negrita:
            lbl.setStyleSheet("font-weight: bold;")
        return lbl

    def _construir_sin_sesion(self):
        l = self._layout
        l.addWidget(self._etiqueta("☁️ " + tt("lbl_nube_sin_sesion", "Este PC no está conectado a MantPro Cloud."), True))
        l.addWidget(self._etiqueta(tt("lbl_nube_info",
            "MantPro Cloud guarda tus datos en la nube y los mantiene al día entre varios PCs y los móviles, "
            "aunque no estén en la misma red. Inicia sesión con la cuenta que te dimos al contratarlo.\n\n"
            "MantPro sigue funcionando igual en este PC sin la nube: si no inicias sesión, no cambia nada.")))
        form = QFormLayout()
        self.campo_correo = QLineEdit()
        self.campo_correo.setPlaceholderText(tt("nube_correo", "Correo"))
        self.campo_password = QLineEdit()
        self.campo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_password.setPlaceholderText(tt("nube_password", "Contraseña"))
        form.addRow(tt("nube_correo", "Correo") + ":", self.campo_correo)
        form.addRow(tt("nube_password", "Contraseña") + ":", self.campo_password)
        l.addLayout(form)
        self.aviso = self._etiqueta("")
        self.aviso.setStyleSheet("color: #c62828;")
        l.addWidget(self.aviso)

        botones = QHBoxLayout()
        self.boton_cerrar = QPushButton(t("btn_cerrar"))
        self.boton_cerrar.clicked.connect(self.reject)
        self.boton_entrar = QPushButton(tt("btn_nube_iniciar", "Iniciar sesión"))
        self.boton_entrar.setDefault(True)
        self.boton_entrar.clicked.connect(self._iniciar)
        self.campo_password.returnPressed.connect(self._iniciar)
        self.campo_correo.returnPressed.connect(self.campo_password.setFocus)
        botones.addWidget(self.boton_cerrar)
        botones.addWidget(self._boton_web())
        botones.addStretch()
        botones.addWidget(self.boton_entrar)
        l.addLayout(botones)
        self.campo_correo.setFocus()

    def _construir_con_sesion(self, datos):
        l = self._layout
        lic = datos.get("licencia") or {}
        efectivo = nube.estado_efectivo(lic)
        icono = {"activa": "✅", "gracia": "⚠️", "vencida": "⛔", "suspendida": "⛔"}.get(efectivo, "❔")
        l.addWidget(self._etiqueta("☁️ " + tt("lbl_nube_conectado", "Este PC está conectado a MantPro Cloud."), True))

        form = QFormLayout()
        empresa = datos.get("empresa") or {}
        cuenta = datos.get("cuenta") or {}
        form.addRow(tt("nube_empresa", "Empresa") + ":", self._etiqueta(empresa.get("nombre", "")))
        form.addRow(tt("nube_cuenta", "Cuenta") + ":",
                    self._etiqueta(f"{cuenta.get('nombre', '')} ({cuenta.get('correo', '')})"))
        plan = lic.get("plan")
        clave_plan, defecto_plan = _PLANES.get(plan, ("", plan or ""))
        form.addRow(tt("nube_plan", "Plan") + ":", self._etiqueta(tt(clave_plan, defecto_plan) if clave_plan else defecto_plan))
        clave_e, defecto_e = _ESTADOS[efectivo]
        form.addRow(tt("nube_licencia", "Licencia") + ":", self._etiqueta(f"{icono} {tt(clave_e, defecto_e)}"))
        hasta = lic.get("valida_hasta")
        if hasta:
            dias = nube.dias_restantes(lic)
            texto = formato_fecha_localizada(hasta)
            if dias is not None and dias >= 0:
                texto += " (" + tt("nube_dias_restantes", "{n} días restantes").format(n=dias) + ")"
            form.addRow(tt("nube_valida_hasta", "Válida hasta") + ":", self._etiqueta(texto))
        comprobada = (datos.get("comprobada") or "")[:10]
        if comprobada:
            form.addRow(tt("nube_comprobada", "Última comprobación") + ":",
                        self._etiqueta(formato_fecha_localizada(comprobada)))
        l.addLayout(form)

        mensaje = {
            "gracia": tt("lbl_nube_gracia",
                "La licencia ha caducado. Renuévala antes de que termine el margen de gracia para no perder la sincronización."),
            "vencida": tt("lbl_nube_vencida",
                "La licencia ha caducado y este PC ya no sincroniza con la nube. MantPro sigue funcionando en local con tus "
                "datos y puedes exportarlos cuando quieras. Renueva la licencia para volver a sincronizar."),
            "suspendida": tt("lbl_nube_suspendida",
                "La cuenta está suspendida. MantPro sigue funcionando en local con tus datos. Contacta con MantPro Cloud."),
        }.get(efectivo)
        if mensaje:
            aviso_lic = self._etiqueta(mensaje)
            aviso_lic.setStyleSheet("color: #b26a00;")
            l.addWidget(aviso_lic)

        self.aviso = self._etiqueta("")
        l.addWidget(self.aviso)

        botones = QHBoxLayout()
        self.boton_salir_sesion = QPushButton(tt("btn_nube_cerrar_sesion", "Cerrar sesión"))
        self.boton_salir_sesion.clicked.connect(self._cerrar_sesion)
        self.boton_comprobar = QPushButton(tt("btn_nube_comprobar", "Comprobar ahora"))
        self.boton_comprobar.clicked.connect(self._comprobar)
        self.boton_cerrar = QPushButton(t("btn_cerrar"))
        self.boton_cerrar.setDefault(True)
        self.boton_cerrar.clicked.connect(self.accept)
        botones.addWidget(self.boton_salir_sesion)
        botones.addWidget(self._boton_web())
        botones.addStretch()
        botones.addWidget(self.boton_comprobar)
        botones.addWidget(self.boton_cerrar)
        l.addLayout(botones)

    # ------------------------------------------------------------ acciones
    def _ocupado(self, ocupado, mensaje=""):
        for nombre in ("boton_entrar", "boton_comprobar", "boton_salir_sesion"):
            w = getattr(self, nombre, None)
            if w is not None:
                w.setEnabled(not ocupado)
        if self.aviso is not None:
            self.aviso.setStyleSheet("")
            self.aviso.setText(mensaje)

    def _lanzar(self, funcion, al_terminar, mensaje):
        if self._hilo is not None and self._hilo.isRunning():
            return
        self._ocupado(True, mensaje)
        self._hilo = _Hilo(funcion, self)
        self._hilo.terminado.connect(al_terminar)
        self._hilo.start()

    def _iniciar(self):
        correo = self.campo_correo.text()
        password = self.campo_password.text()
        self._lanzar(lambda: nube.iniciar_sesion(correo, password, dispositivo=socket.gethostname()),
                     self._tras_iniciar, tt("lbl_nube_conectando", "Conectando…"))

    def _tras_iniciar(self, datos, error):
        if error:
            self._ocupado(False)
            self.aviso.setStyleSheet("color: #c62828;")
            self.aviso.setText(texto_error(error))
            self.campo_password.clear()
            self.campo_password.setFocus()
            return
        self._construir()

    def _comprobar(self):
        self._lanzar(nube.comprobar_licencia, self._tras_comprobar,
                     tt("lbl_nube_comprobando", "Comprobando…"))

    def _tras_comprobar(self, datos, error):
        if error == "sesion_caducada":
            self._construir()
            QMessageBox.information(self, tt("title_nube", "MantPro Cloud"), texto_error(error))
            return
        if error:
            self._ocupado(False)
            self.aviso.setStyleSheet("color: #c62828;")
            self.aviso.setText(texto_error(error))
            return
        self._construir()

    def _cerrar_sesion(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tt("title_nube", "MantPro Cloud"))
        msg.setText(tt("msg_nube_confirmar_cerrar",
            "¿Cerrar la sesión de MantPro Cloud en este PC?\n\nTus datos de mantenimiento no se tocan: "
            "MantPro sigue funcionando en local."))
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() != btn_si:
            return
        self._lanzar(lambda: (nube.cerrar_sesion(), None), lambda *_: self._construir(),
                     tt("lbl_nube_cerrando", "Cerrando sesión…"))

    def done(self, resultado):
        # No cerrar mientras hay una petición en curso (el hilo seguiría tocando la ventana)
        if self._hilo is not None and self._hilo.isRunning():
            self._hilo.wait(nube.TIMEOUT * 1000 + 2000)
        super().done(resultado)
