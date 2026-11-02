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

"""Diálogos del sistema: QR, días especiales, país/región, puerto y contraseña de las copias."""

import qrcode
from io import BytesIO
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDateEdit, QListWidget,
                             QMessageBox, QDialog, QDialogButtonBox, QListWidgetItem, QComboBox,
                             QSpinBox, QFormLayout, QLineEdit, QCheckBox)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QPixmap, QImage

from ...idiomas import t
from ..comun import tt
from ..festivos import PROVINCIAS_ESPAÑA
from ..servidor import PUERTO_POR_DEFECTO, primer_puerto_libre, puerto_libre

class DialogoQR(QDialog):
    """QR con una dirección. Por defecto, el de vincular el móvil con el PC;
    con «titulo» y «pasos» sirve para otros (p. ej. instalar las apps)."""
    def __init__(self, url, parent=None, titulo=None, pasos=None, texto_visible=None):
        super().__init__(parent)
        self.setWindowTitle(titulo or t("title_sincronizar_movil"))
        self.resize(300, 420)
        l = QVBoxLayout()
        for paso in (pasos or [t("lbl_qr_paso1"), t("lbl_qr_paso2")]):
            lbl = QLabel(paso, alignment=Qt.AlignmentFlag.AlignCenter); lbl.setWordWrap(True)
            l.addWidget(lbl)
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        p = QPixmap.fromImage(QImage.fromData(buffer.getvalue()))
        li = QLabel()
        li.setPixmap(p.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        li.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(li)
        l.addWidget(QLabel(texto_visible or url, alignment=Qt.AlignmentFlag.AlignCenter))
        self.setLayout(l)


class DialogoDiasEspeciales(QDialog):
    def __init__(self, db, gestor_festivos, parent=None):
        super().__init__(parent)
        self.db = db
        self.gestor_festivos = gestor_festivos
        self.setWindowTitle(t("title_gestion_dias_especiales"))
        self.resize(500, 400)
        layout = QVBoxLayout()

        # Selector de Fecha y Tipo
        h_top = QHBoxLayout()
        h_top.addWidget(QLabel(t("lbl_fecha")))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        h_top.addWidget(self.date_edit)

        h_top.addWidget(QLabel(t("lbl_tipo")))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems([t("tipo_vacaciones"), t("tipo_puente"), t("tipo_dia_libre"), t("tipo_festivo_manual")])
        h_top.addWidget(self.combo_tipo)

        btn_add = QPushButton(t("btn_anadir"))
        btn_add.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_add.clicked.connect(self.add_dia)
        h_top.addWidget(btn_add)

        layout.addLayout(h_top)

        # Lista de días configurados
        self.lista = QListWidget()
        self.lista.setAlternatingRowColors(True)
        layout.addWidget(self.lista)

        # Botones inferiores
        h_bot = QHBoxLayout()
        btn_del = QPushButton(t("btn_borrar_seleccionado"))
        btn_del.setStyleSheet("background-color: #c0392b; color: white;")
        btn_del.clicked.connect(self.del_dia)
        h_bot.addWidget(btn_del)

        btn_close = QPushButton(t("btn_cerrar"))
        btn_close.clicked.connect(self.accept)
        h_bot.addWidget(btn_close)

        layout.addLayout(h_bot)

        self.setLayout(layout)
        self.refresh_lista()

    def refresh_lista(self):
        self.lista.clear()
        dias = self.db.obtener_dias_especiales()
        # Ordenamos por fecha descendente
        for fecha in sorted(dias.keys(), reverse=True):
            tipo = dias[fecha]
            item = QListWidgetItem(f"📅 {fecha}  ➔  {tipo}")
            item.setData(Qt.ItemDataRole.UserRole, fecha)
            self.lista.addItem(item)

    def add_dia(self):
        f = self.date_edit.date().toString("yyyy-MM-dd")
        t = self.combo_tipo.currentText()
        if self.db.marcar_dia_especial(f, t):
            self.refresh_lista()

    def del_dia(self):
        row = self.lista.currentRow()
        if row >= 0:
            f = self.lista.item(row).data(Qt.ItemDataRole.UserRole)
            if self.db.borrar_dia_especial(f):
                self.refresh_lista()


# ==========================================
# 3. DIÁLOGOS DE INTERFAZ
# ==========================================
class DialogoSeleccionPais(QDialog):
    def __init__(self, gestor_festivos, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(t("title_seleccionar_pais"))
        self.resize(400, 150)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(t("lbl_elige_pais")))
        layout.addWidget(QLabel(t("lbl_nota_espana")))

        self.combo = QComboBox()
        self.paises = gestor_festivos.obtener_paises_disponibles()  # lista de (nombre, iso)
        self.combo.addItems([nombre for nombre, iso in self.paises])

        actual_iso = self.db.get_config("country_iso") or "ES"
        for nombre, iso in self.paises:
            if iso == actual_iso:
                self.combo.setCurrentText(nombre)
                break

        layout.addWidget(self.combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); btns.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)

    def get_selection(self):
        nombre_sel = self.combo.currentText()
        for nombre, iso in self.paises:
            if nombre == nombre_sel:
                return nombre, iso
        return "Spain", "ES"


class DialogoSeleccionRegion(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(t("title_seleccionar_provincia"))
        self.resize(400, 150)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(t("lbl_elige_provincia")))
        layout.addWidget(QLabel(t("lbl_nota_provincia")))
        self.combo = QComboBox()
        self.nombres_ordenados = sorted(PROVINCIAS_ESPAÑA.keys())
        self.combo.addItems(self.nombres_ordenados)
        actual_iso = self.db.get_config("region_iso") or "ES-BI"
        nombre_actual = "Bizkaia"
        for nombre, datos in PROVINCIAS_ESPAÑA.items():
            if datos["iso"] == actual_iso:
                nombre_actual = nombre
                break
        self.combo.setCurrentText(nombre_actual)
        layout.addWidget(self.combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); btns.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)

    def get_selection(self):
        nombre = self.combo.currentText()
        datos = PROVINCIAS_ESPAÑA.get(nombre)
        return nombre, datos["iso"], datos["parent"]


class DialogoPuertoServidor(QDialog):
    """Elegir el puerto del servidor de sincronización con los móviles.
    Si [ocupado], explica que el actual está en uso y permite seguir sin
    sincronización."""
    def __init__(self, parent, puerto_actual, ocupado):
        super().__init__(parent)
        self.setWindowTitle(tt("title_puerto_servidor", "Puerto de sincronización"))
        self.setMinimumWidth(480)
        l = QVBoxLayout()
        if ocupado:
            texto = tt("msg_puerto_ocupado",
                "El puerto {p}, que usa MantPro para sincronizar con los móviles, está ocupado por otro programa "
                "(a menudo otro MantPro abierto).\n\nPuedes elegir otro puerto o seguir sin sincronización con los "
                "móviles hasta la próxima vez que abras MantPro.").format(p=puerto_actual)
        else:
            texto = tt("msg_elegir_puerto", "Puerto en el que MantPro espera a los móviles (por defecto, {p}).").format(p=PUERTO_POR_DEFECTO)
        lbl = QLabel(texto); lbl.setWordWrap(True); l.addWidget(lbl)
        fila = QHBoxLayout(); fila.addWidget(QLabel(tt("lbl_puerto", "Puerto") + ":"))
        self.spin = QSpinBox(); self.spin.setRange(1024, 65535)
        self.spin.setValue(primer_puerto_libre(puerto_actual + 1) if ocupado else puerto_actual)
        fila.addWidget(self.spin); fila.addStretch(); l.addLayout(fila)
        aviso = QLabel(tt("msg_aviso_cambio_puerto",
            "Al cambiar de puerto, los móviles ya vinculados tendrán que volver a escanear el QR "
            "(Herramientas > Sincronizar App)."))
        aviso.setWordWrap(True); aviso.setStyleSheet("color: #e67e22;"); l.addWidget(aviso)
        b = QDialogButtonBox()
        b.addButton(tt("btn_usar_puerto", "Usar este puerto"), QDialogButtonBox.ButtonRole.AcceptRole)
        b.addButton(tt("btn_seguir_sin_sincronizacion", "Seguir sin sincronización") if ocupado else t("btn_cancelar"),
                    QDialogButtonBox.ButtonRole.RejectRole)
        b.accepted.connect(self._validar); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)
        self.puerto_actual = puerto_actual
        self.ocupado = ocupado

    def _validar(self):
        p = self.spin.value()
        if (self.ocupado or p != self.puerto_actual) and not puerto_libre(p):
            QMessageBox.warning(self, tt("aviso", "Aviso"),
                tt("msg_puerto_tambien_ocupado", "El puerto {p} también está ocupado. Elige otro.").format(p=p))
            return
        self.accept()

    def puerto(self): return self.spin.value()


class DialogoContrasenaCopias(QDialog):
    """Archivo > Contraseña de las copias: poner, cambiar o quitar la
    contraseña con la que se cifran las copias de seguridad. Al aceptar deja
    en self.accion "fijar" (con self.contrasena) o "quitar", y en
    self.aplicar_existentes si hay que rehacer las copias que ya existen."""
    LONGITUD_MINIMA = 8

    def __init__(self, parent=None, activada=False):
        super().__init__(parent)
        self.accion = None
        self.contrasena = ""
        self.setWindowTitle(tt("title_contrasena_copias", "Contraseña de las copias de seguridad"))
        self.setModal(True)
        self.setMinimumWidth(460)
        l = QVBoxLayout(self)

        estado = QLabel("🔒 " + tt("lbl_copias_cifradas", "Las copias de seguridad se guardan cifradas.") if activada
                        else "🔓 " + tt("lbl_copias_sin_cifrar", "Las copias de seguridad se guardan sin cifrar."))
        estado.setStyleSheet("font-weight: bold;")
        l.addWidget(estado)
        info = QLabel(tt("lbl_info_contrasena_copias",
            "Con contraseña, las copias (la manual, la automática al cerrar y las previas a borrar o importar) "
            "se guardan cifradas: si alguien se lleva el USB o entra en el NAS o la nube donde las guardas, "
            "no puede abrirlas. En este equipo se restauran sin pedirla; en otro equipo, sí.\n\n"
            "Si la olvidas, no hay forma de recuperar las copias cifradas: apúntala en un sitio seguro."))
        info.setWordWrap(True)
        l.addWidget(info)

        formulario = QFormLayout()
        self.nueva = QLineEdit(); self.nueva.setEchoMode(QLineEdit.EchoMode.Password)
        self.repetir = QLineEdit(); self.repetir.setEchoMode(QLineEdit.EchoMode.Password)
        formulario.addRow(t("password_nueva") + ":", self.nueva)
        formulario.addRow(t("password_repetir") + ":", self.repetir)
        l.addLayout(formulario)

        self.chk_existentes = QCheckBox(tt("chk_aplicar_copias_existentes",
            "Aplicar también a las copias que ya hay en las carpetas de copias de MantPro"))
        self.chk_existentes.setChecked(True)
        l.addWidget(self.chk_existentes)

        caja = QDialogButtonBox()
        caja.addButton(tt("btn_guardar", "Guardar"),
                       QDialogButtonBox.ButtonRole.AcceptRole).clicked.connect(self._fijar)
        if activada:
            caja.addButton(tt("btn_quitar_contrasena", "Quitar contraseña"),
                           QDialogButtonBox.ButtonRole.DestructiveRole).clicked.connect(self._quitar)
        caja.addButton(t("btn_cancelar"), QDialogButtonBox.ButtonRole.RejectRole).clicked.connect(self.reject)
        l.addWidget(caja)

    @property
    def aplicar_existentes(self):
        return self.chk_existentes.isChecked()

    def _fijar(self):
        if len(self.nueva.text()) < self.LONGITUD_MINIMA:
            QMessageBox.warning(self, self.windowTitle(), tt("msg_contrasena_copias_corta",
                "La contraseña tiene que tener al menos {n} caracteres.").format(n=self.LONGITUD_MINIMA))
            return
        if self.nueva.text() != self.repetir.text():
            QMessageBox.warning(self, self.windowTitle(), t("password_no_coincide"))
            return
        self.accion = "fijar"
        self.contrasena = self.nueva.text()
        self.accept()

    def _quitar(self):
        self.accion = "quitar"
        self.accept()
