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

"""Arranque de la aplicación de escritorio: instancia única, login y ventana principal."""

import sys
import sqlite3
import os
import getpass
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog, QSplashScreen
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap

from .. import idiomas
from ..idiomas import t
from .app import MaintenanceApp
from .comun import instalar_traductor_qt, resource_path, tt
from .dialogos.usuarios import DialogoLogin
from ..nucleo import usuarios
from ..nucleo.basedatos import reparar_base_datos
from ..nucleo.rutas import DATA_DIR

NOMBRE_INSTANCIA = "MantPro-" + getpass.getuser()


_ventana_principal = None


def traer_al_frente():
    """Muestra y pone delante la ventana de esta instancia (la principal o,
    si aún no existe, la que esté abierta, p. ej. el login)."""
    ventanas = [_ventana_principal] if _ventana_principal is not None else \
        [w for w in QApplication.topLevelWidgets() if w.isVisible()]
    for w in ventanas:
        if w.isMinimized(): w.showNormal()
        w.show(); w.raise_(); w.activateWindow()


def hay_otra_instancia():
    s = QLocalSocket(); s.connectToServer(NOMBRE_INSTANCIA)
    ok = s.waitForConnected(500)
    s.abort()
    return ok


def pedir_mostrar_otra_instancia():
    s = QLocalSocket(); s.connectToServer(NOMBRE_INSTANCIA)
    if s.waitForConnected(500):
        s.write(b"mostrar"); s.flush(); s.waitForBytesWritten(500)
        s.disconnectFromServer()


def escuchar_otras_instancias(app):
    """Queda atenta a que otra instancia que se abra le pida ponerse delante."""
    QLocalServer.removeServer(NOMBRE_INSTANCIA)  # restos de un cierre brusco
    srv = QLocalServer(app)
    if not srv.listen(NOMBRE_INSTANCIA): return None
    def nueva_conexion():
        c = srv.nextPendingConnection()
        if c is None: return
        def leer():
            if bytes(c.readAll()).startswith(b"mostrar"): traer_al_frente()
        c.readyRead.connect(leer)
    srv.newConnection.connect(nueva_conexion)
    return srv


def manejador_excepciones(exc_type, exc_value, exc_tb):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(error_msg) # Por si lo ejecutas en terminal
    try:
        # Intentamos mostrar el error en una ventanita antes de morir
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(t("title_error_fatal"))
        msg.setText(t("msg_error_fatal"))
        msg.setDetailedText(error_msg)
        msg.exec()
    except:
        pass


sys.excepthook = manejador_excepciones


def main():
    """Arranque de la aplicación de escritorio (lo llama main.py, en la raíz)."""
    global _ventana_principal
    # YA NO forzamos "xcb", dejamos que Wayland gestione la ventana nativamente

    app = QApplication(sys.argv)

    # --- 1. CONFIGURACIÓN DE IDENTIDAD ---
    app.setDesktopFileName("MantPro")
    app.setApplicationName("MantPro")
    app.setOrganizationName("AnabasaSoft")

    ruta_icono = resource_path(os.path.join("recursos", "icono.png"))
    ruta_logo = resource_path(os.path.join("recursos", "AnabasaSoft.png"))

    if os.path.exists(ruta_icono):
        app_icon = QIcon(ruta_icono)
        app.setWindowIcon(app_icon)

    # --- 2. REPARACIÓN DE BASE DE DATOS (CRÍTICO) ---
    # Esto es lo que faltaba. Sin esto, no se crea la columna 'raw_desc' y falla el sync.
    try:
        ruta_db = os.path.join(DATA_DIR, "mantenimiento.db")
        reparar_base_datos(ruta_db)
        print(f"✅ Base de datos verificada en: {ruta_db}")
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")

    # --- 2b. SISTEMA DE USUARIOS + LOGIN OBLIGATORIO ---
    try:
        usuarios.configurar_db(ruta_db)
        primer_arranque = usuarios.inicializar()
        if primer_arranque:
            QMessageBox.information(
                None, "MantPro",
                "Se ha creado el usuario administrador inicial.\n\n"
                "Usuario: admin\nContraseña: admin\n\n"
                "Se te pedirá cambiarla al entrar.")
    except Exception as e:
        print(f"❌ Error inicializando usuarios: {e}")

    # --- 2c. IDIOMA GUARDADO + TRADUCCIÓN DE LOS TEXTOS PROPIOS DE QT ---
    # Se lee ya aquí (antes del login) para que el menú contextual de cortar/
    # copiar/pegar y los botones de los QMessageBox salgan en el idioma correcto
    # desde la primera pantalla, no solo tras abrir la ventana principal.
    try:
        conn_idioma = sqlite3.connect(ruta_db)
        fila_idioma = conn_idioma.execute(
            "SELECT valor FROM config WHERE clave = 'idioma'").fetchone()
        conn_idioma.close()
        idioma_guardado = fila_idioma[0] if fila_idioma else "es"
    except Exception:
        idioma_guardado = "es"
    idiomas.set_idioma(idioma_guardado)
    instalar_traductor_qt(app, idiomas.get_idioma())

    # --- 2d. ¿YA HAY OTRO MANTPRO ABIERTO? ---
    servidor_instancia = None
    if hay_otra_instancia():
        msg = QMessageBox(QMessageBox.Icon.Information, "MantPro",
            tt("msg_ya_abierto", "MantPro ya está abierto en este equipo.\n\n"
               "Abrir otro a la vez no es habitual: los dos compartirían los mismos datos y solo uno podría "
               "sincronizar con los móviles."))
        btn_mostrar = msg.addButton(tt("btn_mostrar_abierto", "Mostrar el que está abierto"), QMessageBox.ButtonRole.AcceptRole)
        msg.addButton(tt("btn_abrir_otro", "Abrir otro igualmente"), QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(btn_mostrar)
        msg.exec()
        if msg.clickedButton() == btn_mostrar:
            pedir_mostrar_otra_instancia()
            sys.exit(0)
    else:
        servidor_instancia = escuchar_otras_instancias(app)

    dlg_login = DialogoLogin(ruta_logo=ruta_logo if os.path.exists(ruta_logo) else None)
    if dlg_login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    # --- 3. INSTANCIAR VENTANA PRINCIPAL ---
    try:
        ventana = MaintenanceApp()
        _ventana_principal = ventana
    except Exception as e:
        print(f"Error crítico al arrancar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # --- 4. SPLASH SCREEN ESTÁTICO (Compatible con Wayland) ---
    if os.path.exists(ruta_logo):
        pixmap = QPixmap(ruta_logo)

        # Escalado suave si es muy grande
        if pixmap.width() > 600:
            pixmap = pixmap.scaledToWidth(600, Qt.TransformationMode.SmoothTransformation)

        # Creamos el Splash normal
        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()

        # Función para cerrar splash y abrir app
        def iniciar_programa():
            splash.close()
            ventana.show()
            ventana.raise_()
            ventana.activateWindow()
            # Comprobamos actualizaciones solo AHORA, con la ventana ya visible y
            # con el foco, para que el diálogo modal de "nueva versión" no compita
            # con el propio arranque de la ventana principal.
            QTimer.singleShot(500, lambda: ventana.comprobar_actualizaciones(manual=False))

        # Esperamos 2 segundos (2000 ms) y cambiamos
        QTimer.singleShot(2000, iniciar_programa)

    else:
        # Si no hay logo, arranca normal
        ventana.show()
        ventana.raise_()
        ventana.activateWindow()
        QTimer.singleShot(500, lambda: ventana.comprobar_actualizaciones(manual=False))

    sys.exit(app.exec())
