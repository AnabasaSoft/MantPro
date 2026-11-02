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

"""Barra de pestañas que «subraya» con una barra de progreso animada el
título de las pestañas que están recibiendo datos de un móvil (Historial,
Pendientes, Avisos, Stock de almacén…)."""

import time

from PyQt6.QtWidgets import QTabBar
from PyQt6.QtCore import QTimer, QRectF, Qt
from PyQt6.QtGui import QPainter, QColor


class BarraPestanasActividad(QTabBar):
    # Para que se vea aunque el envío sea instantáneo
    SEGUNDOS_MINIMOS = 1.0
    COLOR = QColor("#3daee9")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._activos = {}      # widget de la pestaña -> envíos en curso
        self._hasta = {}        # widget -> hora (monotonic) hasta la que se sigue mostrando
        self._fase = 0.0
        self._temporizador = QTimer(self)
        self._temporizador.setInterval(30)
        self._temporizador.timeout.connect(self._avanzar)
        self._tab_widget = None

    def set_tab_widget(self, tab_widget):
        self._tab_widget = tab_widget

    # ---------------------------------------------------------------- estado
    def empezar(self, widget):
        self._activos[widget] = self._activos.get(widget, 0) + 1
        self._hasta[widget] = time.monotonic() + self.SEGUNDOS_MINIMOS
        if not self._temporizador.isActive():
            self._temporizador.start()
        self.update()

    def terminar(self, widget):
        if self._activos.get(widget, 0) > 0:
            self._activos[widget] -= 1
        self._hasta[widget] = max(self._hasta.get(widget, 0), time.monotonic() + 0.4)

    def _ocupados(self):
        ahora = time.monotonic()
        return [w for w in set(self._activos) | set(self._hasta)
                if self._activos.get(w, 0) > 0 or self._hasta.get(w, 0) > ahora]

    def _avanzar(self):
        self._fase = (self._fase + 0.018) % 1.0
        if not self._ocupados():
            self._temporizador.stop()
            self._activos.clear(); self._hasta.clear()
        self.update()

    # ---------------------------------------------------------------- dibujo
    def paintEvent(self, evento):
        super().paintEvent(evento)
        if self._tab_widget is None:
            return
        ocupados = self._ocupados()
        if not ocupados:
            return
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
        fm = self.fontMetrics()
        from PyQt6.QtCore import QSettings
        clasico = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "retro"
        for widget in ocupados:
            i = self._tab_widget.indexOf(widget)
            if i < 0:
                continue
            caja = self.tabRect(i)
            ancho_texto = min(fm.horizontalAdvance(self.tabText(i)), caja.width() - 8)
            x = caja.center().x() - ancho_texto / 2
            y = caja.center().y() + fm.height() / 2 + 1
            pista = QRectF(x, y, ancho_texto, 3)
            # La pestaña activa tiene fondo azul en los temas claro y oscuro:
            # ahí, en blanco. En el clásico es gris claro: el azul de siempre.
            color = QColor("white") if i == self.currentIndex() and not clasico else self.COLOR
            fondo = QColor(color); fondo.setAlpha(70)
            pintor.setPen(Qt.PenStyle.NoPen)
            pintor.setBrush(fondo)
            pintor.drawRoundedRect(pista, 1.5, 1.5)
            # Tramo que se desliza de un lado a otro (progreso sin final conocido)
            tramo = ancho_texto * 0.35
            inicio = x - tramo + (ancho_texto + tramo) * self._fase
            visible = QRectF(max(inicio, x), y, min(inicio + tramo, x + ancho_texto) - max(inicio, x), 3)
            if visible.width() > 0:
                pintor.setBrush(color)
                pintor.drawRoundedRect(visible, 1.5, 1.5)
        pintor.end()
