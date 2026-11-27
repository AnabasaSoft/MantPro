# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# MantPro - Ventana de avisos (modo quiosco)
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

"""Ventana de avisos (modo quiosco): una ventana a pantalla completa que un administrador deja puesta junto al reloj
de fichar. Cada trabajador elige su nombre, rellena el aviso de pendiente (título, detalles, especialidad, prioridad
y fotos) y pulsa «Añadir»: se le pide SU contraseña y el pendiente se crea a su nombre. Después el formulario se
vacía y se deselecciona el usuario. Las fotos se suben con el móvil: «Añadir fotos» muestra un QR que abre una
página del PC (servidor.py, /subir/<token>) y las fotos aparecen en la galería al momento. Solo se cierra con la
contraseña del administrador que la abrió."""

import io
import qrcode
from PyQt6.QtCore import Qt, QEvent, QSettings, QTimer
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (QApplication, QComboBox, QDialog, QGroupBox, QHBoxLayout, QInputDialog, QLabel,
                             QLineEdit, QListWidget, QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget,
                             QAbstractItemView, QSplitter)

from ...idiomas import t
from ...nucleo import pendientes as pendientes_nucleo
from ...nucleo import subidas_temporales, usuarios
from ..widgets.fotos import GaleriaFotosWidget

SEGUNDOS_INACTIVIDAD = 120
SEGUNDOS_BLOQUEO = 30
SEGUNDOS_MENSAJE = 5
MAX_FALLOS = 5
CLAVE_DIVISOR = "quiosco_divisor"      # en QSettings: ancho de la lista de usuarios (cada PC el suyo)
EVENTOS_ACTIVIDAD = (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress, QEvent.Type.TouchBegin)


def _letra(widget, puntos, negrita=False):
    f = QFont(widget.font())
    f.setPointSize(puntos)
    f.setBold(negrita)
    widget.setFont(f)


class VentanaAvisosQuiosco(QWidget):
    def __init__(self, app_principal, admin):
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.app = app_principal
        self.admin = admin
        self._puede_cerrar = False
        self._fallos = 0
        self._recibidas = 0
        self._etiqueta_recibidas = None            # la del diálogo del QR, mientras está abierto
        self._pidiendo_cierre = False
        self._servidor = getattr(app_principal, "server_thread", None)
        sede = app_principal.sede_filtro()
        self._sede = sede if isinstance(sede, int) else None
        self._token = subidas_temporales.crear()
        self.setWindowTitle(t("quiosco_titulo"))

        raiz = QVBoxLayout(self)
        cab = QHBoxLayout()
        columna = QVBoxLayout()
        titulo = QLabel(t("quiosco_titulo")); _letra(titulo, 22, True)
        ayuda = QLabel(t("quiosco_ayuda")); ayuda.setWordWrap(True); _letra(ayuda, 13)
        columna.addWidget(titulo); columna.addWidget(ayuda)
        cab.addLayout(columna, 1)
        btn_cerrar = QPushButton(t("quiosco_btn_cerrar"), clicked=self._pedir_cierre)
        btn_cerrar.setFlat(True)
        cab.addWidget(btn_cerrar, 0, Qt.AlignmentFlag.AlignTop)
        raiz.addLayout(cab)

        # Divisor entre la lista de usuarios y el formulario: se puede arrastrar y cada PC recuerda el ancho
        self.divisor = QSplitter(Qt.Orientation.Horizontal)
        self.divisor.setChildrenCollapsible(False)
        panel_izq = QWidget(); izq = QVBoxLayout(panel_izq); izq.setContentsMargins(0, 0, 6, 0)
        rotulo = QLabel(t("quiosco_elige_usuario")); _letra(rotulo, 14, True)
        izq.addWidget(rotulo)
        self.lista = QListWidget()
        self.lista.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # Columna estrecha; con muchos usuarios sale la barra (ancha, para manejarla con el dedo)
        self.lista.setMinimumWidth(180)
        self.lista.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lista.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lista.setWordWrap(True)
        self.lista.setStyleSheet("QListWidget { font-size: 13pt; } QListWidget::item { padding: 8px 10px; }"
                                 " QScrollBar:vertical { width: 22px; }")
        for u in usuarios.listar_usuarios(incluir_inactivos=False):
            if usuarios.puede_avisar_pendientes(u):
                self.lista.addItem(u["nombre"])
                self.lista.item(self.lista.count() - 1).setData(Qt.ItemDataRole.UserRole, u["id"])
        self.lista.itemSelectionChanged.connect(self._al_elegir_usuario)
        izq.addWidget(self.lista, 1)
        self.divisor.addWidget(panel_izq)

        panel_der = QWidget(); der = QVBoxLayout(panel_der); der.setContentsMargins(6, 0, 0, 0)
        self.lbl_usuario = QLabel(); _letra(self.lbl_usuario, 14, True)
        der.addWidget(self.lbl_usuario)
        self.grupo = QGroupBox(t("lbl_avisar_pendiente")); f = QVBoxLayout()
        self.in_titulo = QLineEdit(); self.in_titulo.setPlaceholderText(t("ph_titulo")); f.addWidget(self.in_titulo)
        self.in_detalles = QTextEdit(); self.in_detalles.setPlaceholderText(t("ph_detalles"))
        self.in_detalles.setMinimumHeight(160); self.in_detalles.setMaximumHeight(220); f.addWidget(self.in_detalles)
        fila = QHBoxLayout()
        fila.addWidget(QLabel(t("usuarios_col_especialidad") + ":"))
        self.combo_especialidad = QComboBox()
        app_principal._llenar_combo_especialidades(self.combo_especialidad)
        fila.addWidget(self.combo_especialidad, 1)
        f.addLayout(fila)
        fila = QHBoxLayout()
        fila.addWidget(QLabel(t("lbl_prioridad") + ":"))
        self.combo_prioridad = QComboBox()
        app_principal._llenar_combo_prioridad(self.combo_prioridad)
        fila.addWidget(self.combo_prioridad, 1)
        f.addLayout(fila)
        self.galeria = GaleriaFotosWidget(app_principal.carpeta_fotos, self, al_anadir=self._mostrar_qr)
        f.addWidget(self.galeria)
        self.btn_anadir = QPushButton(t("btn_anadir"), clicked=self._anadir)
        self.btn_anadir.setStyleSheet("QPushButton { background-color:#27ae60; color: white; font-weight: bold;"
                                      " padding: 8px 32px; }"
                                      " QPushButton:disabled { background-color: #7f8c8d; color: #dddddd; }")
        fila = QHBoxLayout(); fila.addStretch(1); fila.addWidget(self.btn_anadir)
        f.addLayout(fila)
        self.grupo.setLayout(f)
        # Todo el formulario con el mismo tamaño de letra, legible desde un paso atrás
        self.grupo.setStyleSheet("QGroupBox, QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton { font-size: 13pt; }"
                                 " QLineEdit, QComboBox { padding: 4px; }")
        der.addWidget(self.grupo)
        self.lbl_estado = QLabel(t("quiosco_aviso_anadido")); _letra(self.lbl_estado, 20, True)
        self.lbl_estado.setStyleSheet("color: #27ae60;")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.hide()
        der.addWidget(self.lbl_estado)
        der.addStretch(1)
        self.divisor.addWidget(panel_der)
        self.divisor.setStretchFactor(0, 0); self.divisor.setStretchFactor(1, 1)
        guardado = QSettings("MyCompany", "MantenimientoApp").value(CLAVE_DIVISOR)
        if not (guardado and self.divisor.restoreState(guardado)):
            self.divisor.setSizes([280, 1000])
        self.divisor.splitterMoved.connect(self._guardar_divisor)
        raiz.addWidget(self.divisor, 1)

        self._t_inactividad = QTimer(self, singleShot=True, interval=SEGUNDOS_INACTIVIDAD * 1000)
        self._t_inactividad.timeout.connect(self._por_inactividad)
        self._t_estado = QTimer(self, singleShot=True, interval=SEGUNDOS_MENSAJE * 1000)
        self._t_estado.timeout.connect(self.lbl_estado.hide)
        self._t_bloqueo = QTimer(self, singleShot=True, interval=SEGUNDOS_BLOQUEO * 1000)
        self._t_bloqueo.timeout.connect(self._fin_bloqueo)

        self._al_elegir_usuario()
        if self._servidor is not None:
            self._servidor.foto_subida_temporal.connect(self._foto_recibida)
        QApplication.instance().installEventFilter(self)
        self._t_inactividad.start()
        # La ventana principal (con la sesión del administrador) se oculta: un Alt+Tab no debe llevar a ella
        self._principal_maximizada = app_principal.isMaximized()
        app_principal.hide()
        self.showFullScreen()

    # --- usuario elegido y formulario ---------------------------------------------------------------------------
    def _id_elegido(self):
        it = self.lista.currentItem() if self.lista.selectedItems() else None
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _al_elegir_usuario(self):
        it = self.lista.selectedItems()[0] if self.lista.selectedItems() else None
        self.grupo.setEnabled(it is not None)
        if it:
            self.lbl_usuario.setText(t("quiosco_avisa").format(nombre=it.text()))
            self.lbl_usuario.setStyleSheet("")
        else:
            self.lbl_usuario.setText(t("quiosco_sin_usuario"))
            self.lbl_usuario.setStyleSheet("color: #d35400;")

    def _renovar_token(self):
        subidas_temporales.anular(self._token)
        self._token = subidas_temporales.crear()
        self._recibidas = 0

    def _reiniciar_formulario(self):
        self.in_titulo.clear(); self.in_detalles.clear()
        self.combo_prioridad.setCurrentIndex(1)
        self.combo_especialidad.setCurrentIndex(0)
        self.galeria.set_nombres([])
        self.lista.clearSelection()
        self.lista.setCurrentRow(-1)
        self._renovar_token()

    def _hay_algo(self):
        return bool(self.lista.selectedItems() or self.in_titulo.text().strip()
                    or self.in_detalles.toPlainText().strip() or self.galeria.nombres())

    def _por_inactividad(self):
        if self._puede_cerrar:
            return
        if QApplication.activeModalWidget() is not None:      # hay un diálogo abierto: no se le quita de en medio
            self._t_inactividad.start()
            return
        if self._hay_algo():
            self._reiniciar_formulario()

    def eventFilter(self, obj, ev):
        if ev.type() in EVENTOS_ACTIVIDAD and not self._puede_cerrar:
            self._t_inactividad.start()
        return False

    # --- fotos desde el móvil ----------------------------------------------------------------------------------
    def _foto_recibida(self, token, nombre):
        if token != self._token:
            return
        self.galeria.anadir_nombre(nombre)
        self._recibidas += 1
        if self._etiqueta_recibidas is not None:
            self._etiqueta_recibidas.setText(t("quiosco_fotos_recibidas").format(n=self._recibidas))
        self._t_inactividad.start()

    def _mostrar_qr(self):
        if self._servidor is None:
            QMessageBox.information(self, t("title_atencion"), t("quiosco_sin_servidor"))
            return
        # La pantalla puede llevar horas en reposo: si el código ya caducó, uno nuevo (las fotos ya recibidas
        # siguen en la galería, que guarda sus nombres)
        if not subidas_temporales.valido(self._token):
            self._token = subidas_temporales.crear()
        url = f"http://{self._servidor.obtener_ip_local()}:{self._servidor.server_port}/subir/{self._token}"
        dlg = QDialog(self)
        dlg.setModal(True)
        dlg.setWindowTitle(t("quiosco_web_titulo"))
        l = QVBoxLayout(dlg)
        texto = QLabel(t("quiosco_qr_instrucciones"), alignment=Qt.AlignmentFlag.AlignCenter)
        texto.setWordWrap(True); _letra(texto, 14)
        l.addWidget(texto)
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        buffer = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(buffer)
        pix = QPixmap.fromImage(QImage.fromData(buffer.getvalue()))
        grande = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        grande.setPixmap(pix.scaled(420, 420, Qt.AspectRatioMode.KeepAspectRatio))
        l.addWidget(grande)
        self._etiqueta_recibidas = QLabel(t("quiosco_fotos_recibidas").format(n=self._recibidas),
                                          alignment=Qt.AlignmentFlag.AlignCenter)
        _letra(self._etiqueta_recibidas, 16, True)
        l.addWidget(self._etiqueta_recibidas)
        btn = QPushButton(t("quiosco_btn_hecho"), clicked=dlg.accept)
        btn.setStyleSheet("font-size: 16pt; padding: 12px;")
        l.addWidget(btn)
        try:
            dlg.exec()
        finally:
            self._etiqueta_recibidas = None

    # --- añadir el aviso ---------------------------------------------------------------------------------------
    def _pide_contrasena(self, texto, usuario):
        """Pide la contraseña de [usuario] y la comprueba. True si es la suya."""
        pw, ok = QInputDialog.getText(self, t("title_atencion"), texto, QLineEdit.EchoMode.Password)
        if not ok:
            return None
        conocido = usuarios.autenticar(usuario["login"], pw)
        return bool(conocido and conocido["id"] == usuario["id"])

    def _usuario_elegido(self):
        uid = self._id_elegido()
        if uid is None:
            return None
        return next((u for u in usuarios.listar_usuarios(incluir_inactivos=False) if u["id"] == uid), None)

    def _hay_bloqueo(self):
        if self._t_bloqueo.isActive():
            QMessageBox.warning(self, t("title_error"), t("quiosco_demasiados_intentos").format(segundos=SEGUNDOS_BLOQUEO))
            return True
        return False

    def _fallo_contrasena(self):
        """Cuenta un fallo de contraseña (de «Añadir» o del cierre); a los MAX_FALLOS seguidos, bloquea 30 s."""
        self._fallos += 1
        if self._fallos >= MAX_FALLOS:
            self._fallos = 0
            self.btn_anadir.setEnabled(False)
            self._t_bloqueo.start()
            QMessageBox.warning(self, t("title_error"), t("quiosco_demasiados_intentos").format(segundos=SEGUNDOS_BLOQUEO))
        else:
            QMessageBox.warning(self, t("title_error"), t("quiosco_contrasena_mal"))

    def _anadir(self):
        if self._hay_bloqueo():
            return
        usuario = self._usuario_elegido()
        if usuario is None:
            QMessageBox.warning(self, t("title_atencion"), t("quiosco_sin_usuario"))
            return
        titulo = self.in_titulo.text().strip()
        if not titulo:
            QMessageBox.warning(self, t("title_atencion"), t("quiosco_falta_titulo"))
            return
        # Se lee todo ANTES de pedir la contraseña: lo que se guarde es lo que había al pulsar «Añadir»
        detalles = self.in_detalles.toPlainText().strip()
        prioridad, especialidad = self.combo_prioridad.currentData(), self.combo_especialidad.currentData()
        fotos = self.galeria.nombres()
        valida = self._pide_contrasena(t("quiosco_pide_contrasena").format(nombre=usuario["nombre"]), usuario)
        if valida is None:
            return
        if not valida:
            self._fallo_contrasena()
            return
        self._fallos = 0
        # El registro de cambios apunta al trabajador, no al administrador que tiene la sesión abierta
        usuarios.fijar_actor_peticion(usuario, origen="💻 PC")
        try:
            args = (self.app.db, usuario, titulo, detalles, None, prioridad, especialidad, None)
            try:
                try:
                    pendientes_nucleo.crear(*args, sede=self._sede, fotos=fotos)
                except ValueError as ex:
                    if str(ex) != "sede_no_permitida":
                        raise
                    pendientes_nucleo.crear(*args, sede=None, fotos=fotos)
            except ValueError as ex:
                QMessageBox.warning(self, t("title_error"),
                                    t("quiosco_sin_permiso") if str(ex) == "sin_permiso" else str(ex))
                return
        finally:
            usuarios.limpiar_actor_peticion()
        self.lbl_estado.show()
        self._t_estado.start()
        self._reiniciar_formulario()
        self.app.refresh_todos()
        if self._servidor is not None:
            self._servidor.pendiente_actualizado.emit()

    def _fin_bloqueo(self):
        self.btn_anadir.setEnabled(True)

    # --- cierre (solo con la contraseña del administrador) -------------------------------------------------------
    def _guardar_divisor(self, *_):
        QSettings("MyCompany", "MantenimientoApp").setValue(CLAVE_DIVISOR, self.divisor.saveState())

    def _liberar(self):
        subidas_temporales.anular(self._token)
        if self._servidor is not None:
            try:
                self._servidor.foto_subida_temporal.disconnect(self._foto_recibida)
            except (TypeError, RuntimeError):
                pass
        QApplication.instance().removeEventFilter(self)
        self._t_inactividad.stop()
        if self._principal_maximizada:
            self.app.showMaximized()
        else:
            self.app.show()
        self.app.raise_()
        self.app.activateWindow()

    def _pedir_cierre(self):
        if self._pidiendo_cierre or self._puede_cerrar:
            return
        if self._hay_bloqueo():
            return
        self._pidiendo_cierre = True
        try:
            valida = self._pide_contrasena(t("quiosco_pide_contrasena_admin").format(nombre=self.admin["nombre"]),
                                           self.admin)
        finally:
            self._pidiendo_cierre = False
        if valida is None:
            return
        if not valida:
            self._fallo_contrasena()
            return
        self._fallos = 0
        self._puede_cerrar = True
        self._liberar()
        self.close()

    def closeEvent(self, e):
        if not self._puede_cerrar:
            e.ignore()
            # Aplazado: un close() lanzado desde dentro de closeEvent lo ignora Qt (es reentrante)
            QTimer.singleShot(0, self._pedir_cierre)
            return
        e.accept()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            e.ignore()
            return
        super().keyPressEvent(e)
