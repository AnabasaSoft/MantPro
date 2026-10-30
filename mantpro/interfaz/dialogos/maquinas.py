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

"""Diálogo de alta y edición de máquinas."""

import os
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
                             QMessageBox, QDialog, QDialogButtonBox, QComboBox, QInputDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from ...idiomas import t
from ..comun import _estilo_zona_arrastre, tt
from ..widgets.fotos import DialogoSelectorFoto, VisorFoto
from ...nucleo import maquinas

class DialogoEditarMaquina(QDialog):
    """Alta/edición de una máquina del listado de maquinaria."""
    def __init__(self, parent=None, maquina=None, padre_sugerido=None, excluir_ids=None):
        super().__init__(parent)
        self.maquina = maquina
        self.es_nueva = maquina is None
        self.excluir_ids = excluir_ids or set()
        self.ruta_foto_seleccionada = ""
        self.foto_nombre_existente = maquina.get("foto") if maquina else None
        self.setWindowTitle(tt("title_nueva_maquina", "Nueva máquina") if self.es_nueva else tt("title_editar_maquina", "Editar máquina"))
        self.resize(420, 460)
        l = QVBoxLayout()

        l.addWidget(QLabel(tt("lbl_nombre_maquina", "Nombre de la máquina")))
        self.campo_nombre = QLineEdit(maquina["nombre"] if maquina else "")
        l.addWidget(self.campo_nombre)

        l.addWidget(QLabel(tt("lbl_maquina_padre", "Máquina superior (opcional)")))
        self.combo_padre = QComboBox()
        self.combo_padre.addItem(tt("txt_ninguna", "— Ninguna —"), None)
        todas = maquinas.listar_maquinas()
        por_padre = {}
        for m in todas:
            por_padre.setdefault(m["padre_id"], []).append(m)

        def anadir(padre_id, nivel):
            for m in por_padre.get(padre_id, []):
                if m["id"] in self.excluir_ids:
                    continue
                self.combo_padre.addItem(("    " * nivel) + m["nombre"], m["id"])
                anadir(m["id"], nivel + 1)

        anadir(None, 0)
        seleccion = maquina["padre_id"] if maquina else padre_sugerido
        idx = self.combo_padre.findData(seleccion)
        if idx >= 0:
            self.combo_padre.setCurrentIndex(idx)
        l.addWidget(self.combo_padre)

        l.addWidget(QLabel(tt("lbl_zona_maquina", "Zona / Ubicación (opcional)")))
        h_zona = QHBoxLayout()
        self.combo_zona = QComboBox()
        self._recargar_combo_zona(maquina.get("zona_id") if maquina else self._zona_de(seleccion))
        # Una máquina nueva toma la zona de su máquina superior, también si se
        # cambia de superior, mientras no se haya elegido otra zona a mano.
        self._zona_elegida_a_mano = False
        if self.es_nueva:
            self.combo_zona.activated.connect(lambda _: setattr(self, "_zona_elegida_a_mano", True))
            self.combo_padre.currentIndexChanged.connect(self._heredar_zona_del_padre)
        h_zona.addWidget(self.combo_zona, 1)
        btn_nueva_zona = QPushButton("➕")
        btn_nueva_zona.setFixedWidth(32)
        btn_nueva_zona.setToolTip(tt("btn_nueva_zona", "Nueva zona"))
        btn_nueva_zona.clicked.connect(self._nueva_zona)
        h_zona.addWidget(btn_nueva_zona)
        l.addLayout(h_zona)

        l.addWidget(QLabel(tt("lbl_notas", "Notas")))
        self.campo_notas = QTextEdit(maquina.get("notas") or "" if maquina else "")
        self.campo_notas.setMaximumHeight(100)
        l.addWidget(self.campo_notas)

        l.addWidget(QLabel(tt("lbl_foto_adjunta", "Foto adjunta")))
        self.lbl_preview = QLabel(tt("lbl_sin_foto", "Sin foto")); self.lbl_preview.setFixedSize(200, 150)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet(_estilo_zona_arrastre())
        self.lbl_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_preview.mousePressEvent = self._click_preview
        h_center = QHBoxLayout(); h_center.addWidget(self.lbl_preview); h_center.addStretch()
        l.addLayout(h_center)
        h_foto = QHBoxLayout()
        btn_cambiar = QPushButton(t("btn_cambiar_foto")); btn_cambiar.clicked.connect(self.seleccionar_foto)
        btn_borrar = QPushButton(t("btn_borrar_foto")); btn_borrar.clicked.connect(self.borrar_foto)
        h_foto.addWidget(btn_cambiar); h_foto.addWidget(btn_borrar)
        l.addLayout(h_foto)

        self._actualizar_preview_inicial()

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar_aceptar); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def _recargar_combo_zona(self, zona_id_seleccionada=None):
        self.combo_zona.clear()
        self.combo_zona.addItem(tt("txt_sin_zona", "— Sin zona —"), None)
        for z in maquinas.listar_zonas():
            self.combo_zona.addItem(z["nombre"], z["id"])
        idx = self.combo_zona.findData(zona_id_seleccionada)
        self.combo_zona.setCurrentIndex(idx if idx >= 0 else 0)

    @staticmethod
    def _zona_de(id_maquina):
        """Zona de la máquina indicada (None si no tiene o no hay máquina)."""
        m = maquinas.obtener_maquina(id_maquina) if id_maquina is not None else None
        return m["zona_id"] if m else None

    def _heredar_zona_del_padre(self):
        if self._zona_elegida_a_mano:
            return
        idx = self.combo_zona.findData(self._zona_de(self.combo_padre.currentData()))
        self.combo_zona.setCurrentIndex(idx if idx >= 0 else 0)

    def _nueva_zona(self):
        nombre, ok = QInputDialog.getText(self, tt("title_nueva_zona", "Nueva zona"), tt("lbl_nombre_zona", "Nombre de la zona"))
        if ok and nombre.strip():
            nuevo_id = maquinas.agregar_zona(nombre.strip())
            self._recargar_combo_zona(nuevo_id)
            self._zona_elegida_a_mano = True

    def _actualizar_preview_inicial(self):
        if self.foto_nombre_existente:
            carpeta_fotos = self.parent().carpeta_fotos if self.parent() else ""
            ruta = os.path.join(carpeta_fotos, self.foto_nombre_existente)
            if os.path.exists(ruta):
                self.ruta_foto_seleccionada = ruta
                self._refrescar_preview()

    def _refrescar_preview(self):
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada):
            pix = QPixmap(self.ruta_foto_seleccionada)
            if not pix.isNull():
                self.lbl_preview.setPixmap(pix.scaled(self.lbl_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_preview.setStyleSheet("border: 2px solid #3daee9; background-color: #000;")
        else:
            self.lbl_preview.setPixmap(QPixmap()); self.lbl_preview.setText(tt("lbl_sin_foto", "Sin foto"))
            self.lbl_preview.setStyleSheet(_estilo_zona_arrastre())

    def seleccionar_foto(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles():
            self.ruta_foto_seleccionada = dlg.selectedFiles()[0]
            self._refrescar_preview()

    def borrar_foto(self):
        self.ruta_foto_seleccionada = ""
        self.foto_nombre_existente = None
        self._refrescar_preview()

    def _click_preview(self, event):
        """Si ya hay foto la abre en grande (igual que en los trabajos); si no
        hay ninguna, abre directamente el selector de fichero."""
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada):
            VisorFoto(self.ruta_foto_seleccionada, self).exec()
        else:
            self.seleccionar_foto()

    def _validar_aceptar(self):
        if not self.campo_nombre.text().strip():
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_nombre_maquina_obligatorio", "El nombre de la máquina es obligatorio."))
            return
        # Avisar si al mismo nivel ya hay otra con un nombre igual o muy
        # parecido, para no acabar con la misma máquina dada de alta dos veces.
        # Al editar, solo si cambia el nombre o la máquina superior.
        cambia = self.es_nueva or (self.campo_nombre.text().strip() != self.maquina["nombre"]
                                   or self.combo_padre.currentData() != self.maquina["padre_id"])
        parecidos = maquinas.nombres_parecidos(self.campo_nombre.text(), self.combo_padre.currentData(),
                                               excluir_id=None if self.es_nueva else self.maquina["id"]) if cambia else []
        if parecidos:
            lista = "\n".join(f"  • {n}" for n in parecidos)
            r = QMessageBox.question(
                self, tt("title_nombre_maquina_parecido", "Nombre parecido"),
                tt("msg_nombre_maquina_parecido", "Al mismo nivel ya hay una máquina con un nombre igual o muy parecido:\n\n{lista}\n\n¿Guardar igualmente?").format(lista=lista),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if r != QMessageBox.StandardButton.Yes:
                return
        self.accept()

    def get_data(self):
        return {
            "nombre": self.campo_nombre.text().strip(),
            "padre_id": self.combo_padre.currentData(),
            "zona_id": self.combo_zona.currentData(),
            "notas": self.campo_notas.toPlainText().strip(),
            "ruta_foto_seleccionada": self.ruta_foto_seleccionada,
            "foto_nombre_existente": self.foto_nombre_existente,
        }
