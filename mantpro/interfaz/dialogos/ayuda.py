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

"""Ventana de ayuda (Ayuda > Instrucciones, o F1): un índice de secciones a la
izquierda y el texto a la derecha, con buscador.

Los textos están en mantpro/idiomas/ayuda/<idioma>.html (uno por idioma, con
las mismas secciones; herramientas/verificar_idiomas.py avisa si a alguno le
falta alguna). Cada sección empieza con <h2><a name="id"></a>Título</h2>."""

import os
import re

from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
                             QTextBrowser, QLineEdit, QPushButton, QSplitter, QLabel)
from PyQt6.QtCore import Qt

from ... import idiomas
from ...idiomas import t
from ..comun import tt

CARPETA_AYUDA = os.path.join(os.path.dirname(os.path.abspath(idiomas.__file__)), "ayuda")
_RE_SECCION = re.compile(r'<h2><a name="([\w-]+)"></a>(.*?)</h2>', re.S)


def ruta_ayuda(codigo):
    """Fichero de ayuda del idioma, o el español si ese idioma no tiene."""
    ruta = os.path.join(CARPETA_AYUDA, f"{codigo}.html")
    return ruta if os.path.exists(ruta) else os.path.join(CARPETA_AYUDA, "es.html")


class DialogoAyuda(QDialog):
    def __init__(self, parent=None, seccion=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_instrucciones", "Instrucciones de MantPro"))
        self.resize(1050, 700)
        with open(ruta_ayuda(idiomas.get_idioma()), encoding="utf-8") as f:
            html = f.read()

        l = QVBoxLayout(self)
        barra = QHBoxLayout()
        self.buscar = QLineEdit(); self.buscar.setPlaceholderText(tt("ph_buscar_ayuda", "Buscar en la ayuda..."))
        self.buscar.returnPressed.connect(self._buscar_siguiente)
        self.buscar.textChanged.connect(lambda _: self.lbl_busqueda.clear())
        btn_buscar = QPushButton(tt("btn_buscar_siguiente", "🔍 Buscar")); btn_buscar.clicked.connect(self._buscar_siguiente)
        self.lbl_busqueda = QLabel()
        barra.addWidget(self.buscar, 1); barra.addWidget(btn_buscar); barra.addWidget(self.lbl_busqueda)
        l.addLayout(barra)

        split = QSplitter(Qt.Orientation.Horizontal)
        self.indice = QListWidget()
        self.indice.setMinimumWidth(290)
        self.indice.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.indice.setWordWrap(True)
        for ancla, titulo in _RE_SECCION.findall(html):
            item = QListWidgetItem(re.sub(r"<[^>]+>", "", titulo).strip())
            item.setData(Qt.ItemDataRole.UserRole, ancla)
            self.indice.addItem(item)
        self.indice.currentItemChanged.connect(self._ir_a_seccion)
        self.texto = QTextBrowser()
        self.texto.setOpenExternalLinks(True)
        self.texto.setHtml(html)
        split.addWidget(self.indice); split.addWidget(self.texto)
        split.setStretchFactor(0, 1); split.setStretchFactor(1, 4)
        split.setSizes([300, 750])
        l.addWidget(split, 1)

        pie = QHBoxLayout(); pie.addStretch()
        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept)
        pie.addWidget(btn_cerrar); l.addLayout(pie)

        if seccion:
            for i in range(self.indice.count()):
                if self.indice.item(i).data(Qt.ItemDataRole.UserRole) == seccion:
                    self.indice.setCurrentRow(i)

    def _ir_a_seccion(self, item, _anterior=None):
        if item is not None:
            self.texto.scrollToAnchor(item.data(Qt.ItemDataRole.UserRole))

    def _buscar_siguiente(self):
        texto = self.buscar.text().strip()
        if not texto:
            return
        if not self.texto.find(texto):
            # Al llegar al final, vuelve a empezar desde arriba
            cursor = self.texto.textCursor(); cursor.movePosition(cursor.MoveOperation.Start)
            self.texto.setTextCursor(cursor)
            if not self.texto.find(texto):
                self.lbl_busqueda.setText(tt("msg_ayuda_no_encontrado", "No se ha encontrado"))
                return
        self.lbl_busqueda.clear()
