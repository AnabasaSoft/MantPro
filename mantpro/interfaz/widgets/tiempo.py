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

"""Campo «Tiempo trabajado» de un trabajo: horas y minutos (se apunta
después, sin cronómetro) y cuántas personas trabajaron."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QSpinBox

from ..comun import tt
from ...nucleo import mano_obra


class CampoTiempoTrabajo(QWidget):
    def __init__(self, parent=None, minutos=None, personas=1):
        super().__init__(parent)
        h = QHBoxLayout(self); h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(QLabel(tt("lbl_tiempo_trabajado", "⏱️ Tiempo trabajado") + ":"))
        self.campo = QLineEdit(mano_obra.texto_entrada(minutos))
        self.campo.setPlaceholderText(tt("ph_tiempo_trabajado", "p. ej. 1:30 o 1,5"))
        self.campo.setMaximumWidth(120)
        self.campo.setToolTip(tt("tt_tiempo_trabajado",
            "Horas y minutos que duró el trabajo (1:30, 1,5 o 90 min). Se puede apuntar después, al volver."))
        self.campo.textChanged.connect(self._validar)
        h.addWidget(self.campo)
        h.addWidget(QLabel("×"))
        self.spin_personas = QSpinBox(); self.spin_personas.setRange(1, 50); self.spin_personas.setValue(personas or 1)
        self.spin_personas.setSuffix(" " + tt("lbl_personas", "personas"))
        h.addWidget(self.spin_personas)
        self.lbl = QLabel(); self.lbl.setStyleSheet("color: gray;")
        h.addWidget(self.lbl)
        h.addStretch()
        self._validar()

    def _validar(self, *_):
        texto = self.campo.text().strip()
        minutos = mano_obra.leer_duracion(texto)
        if texto and minutos is None:
            self.campo.setStyleSheet("color: #e74c3c;")
            self.lbl.setText(tt("msg_tiempo_no_valido", "no se entiende"))
        else:
            self.campo.setStyleSheet("")
            self.lbl.setText(mano_obra.texto_duracion(minutos) if minutos else "")

    def minutos(self):
        return mano_obra.leer_duracion(self.campo.text())

    def personas(self):
        return self.spin_personas.value()

    def vaciar(self):
        self.campo.clear(); self.spin_personas.setValue(1)
