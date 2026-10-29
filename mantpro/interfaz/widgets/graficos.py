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

"""Gráficos del dashboard, dibujados con QPainter."""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QBrush, QPainter, QPen, QFont

from ..comun import tt

class _GraficoBase(QWidget):
    """Base común de las gráficas dibujadas a mano con QPainter (sin depender
    de ninguna librería de gráficos externa): centraliza el guardado de
    datos, el color de texto/fondo y el estado "sin datos", dejando en cada
    subclase solo la parte de dibujo (_dibujar) que de verdad cambia entre
    ellas."""

    def __init__(self, parent=None, color_texto="#dcdcdc", color_fondo=None, altura_minima=160):
        super().__init__(parent)
        self._datos = []
        self._color_texto = QColor(color_texto)
        self._color_fondo = QColor(color_fondo) if color_fondo else None
        self.setMinimumHeight(altura_minima)

    def establecer_datos(self, datos):
        """datos: lista de tuplas (etiqueta, valor)."""
        self._datos = datos
        self.update()

    def _hay_datos(self):
        """Las subclases lo sobrescriben si su criterio de "vacío" no es
        simplemente que la lista de datos esté vacía."""
        return bool(self._datos)

    def _texto_vacio(self):
        return tt("lbl_sin_datos_grafico", "Sin datos")

    def paintEvent(self, evento):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._color_fondo:
            painter.fillRect(self.rect(), self._color_fondo)
        if not self._hay_datos():
            painter.setPen(QColor("#888888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._texto_vacio())
            return
        self._dibujar(painter)


class GraficoCircularTrabajos(_GraficoBase):
    """Gráfica circular dibujada a mano con QPainter (sin depender de ninguna
    librería de gráficos externa) que reparte un total de trabajos entre un
    conjunto de etiquetas, con su leyenda de colores al lado."""

    _COLORES = [
        QColor("#3daee9"), QColor("#e67e22"), QColor("#2ecc71"), QColor("#e74c3c"),
        QColor("#9b59b6"), QColor("#f1c40f"), QColor("#1abc9c"), QColor("#95a5a6"),
    ]

    def __init__(self, parent=None, color_texto="#dcdcdc", color_fondo=None):
        super().__init__(parent, color_texto, color_fondo, altura_minima=180)

    def establecer_datos(self, datos):
        """datos: lista de tuplas (etiqueta, valor)."""
        super().establecer_datos([(etiqueta, valor) for etiqueta, valor in datos if valor > 0])

    def _texto_vacio(self):
        return tt("lbl_sin_trabajos_grafico", "Sin trabajos registrados")

    def _dibujar(self, painter):
        total = sum(valor for _, valor in self._datos)
        ancho, alto = self.width(), self.height()
        ancho_leyenda = 120
        lado = min(alto - 20, ancho - ancho_leyenda - 20)
        lado = max(lado, 30)
        x_tarta = 10
        y_tarta = (alto - lado) // 2
        rect_tarta = QRectF(x_tarta, y_tarta, lado, lado)

        angulo_inicio = 90 * 16  # las 12h en punto, QPainter mide en 1/16 de grado
        for i, (etiqueta, valor) in enumerate(self._datos):
            color = self._COLORES[i % len(self._COLORES)]
            angulo_extension = -round(valor / total * 360 * 16)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#1e1e1e"), 1))
            painter.drawPie(rect_tarta, angulo_inicio, angulo_extension)
            angulo_inicio += angulo_extension

        x_leyenda = x_tarta + lado + 15
        painter.setFont(QFont(painter.font().family(), 8))
        for i, (etiqueta, valor) in enumerate(self._datos):
            y = 10 + i * 16
            if y > alto - 10:
                painter.setPen(self._color_texto)
                painter.drawText(x_leyenda, y, "…")
                break
            color = self._COLORES[i % len(self._COLORES)]
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawRect(x_leyenda, y, 10, 10)
            painter.setPen(self._color_texto)
            painter.drawText(x_leyenda + 15, y + 9, f"{etiqueta} ({valor})")


class GraficoBarrasRanking(_GraficoBase):
    """Gráfica de barras horizontales dibujada a mano con QPainter (sin
    depender de ninguna librería de gráficos externa), para un ranking ya
    ordenado de mayor a menor."""

    def __init__(self, parent=None, color="#c0392b", color_texto="#dcdcdc", color_fondo=None):
        super().__init__(parent, color_texto, color_fondo, altura_minima=160)
        self._color = QColor(color)

    def _dibujar(self, painter):
        maximo = max(valor for _, valor in self._datos) or 1
        ancho, alto = self.width(), self.height()
        alto_fila = alto / len(self._datos)
        ancho_etiqueta = 130
        ancho_valor = 30
        painter.setFont(QFont(painter.font().family(), 9))
        metrica = painter.fontMetrics()
        for i, (etiqueta, valor) in enumerate(self._datos):
            y = i * alto_fila
            painter.setPen(self._color_texto)
            etiqueta_elidida = metrica.elidedText(etiqueta, Qt.TextElideMode.ElideRight, ancho_etiqueta - 6)
            painter.drawText(QRectF(4, y, ancho_etiqueta, alto_fila),
                              Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, etiqueta_elidida)

            x_barra = ancho_etiqueta + 8
            ancho_disponible = max(ancho - x_barra - ancho_valor - 8, 10)
            ancho_barra = max(ancho_disponible * (valor / maximo), 2)
            alto_barra = min(alto_fila * 0.6, 22)
            y_barra = y + (alto_fila - alto_barra) / 2
            painter.setBrush(QBrush(self._color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x_barra, y_barra, ancho_barra, alto_barra), 3, 3)

            painter.setPen(self._color_texto)
            painter.drawText(QRectF(x_barra + ancho_disponible + 4, y, ancho_valor, alto_fila),
                              Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, str(valor))


class GraficoBarrasMensual(_GraficoBase):
    """Gráfica de barras verticales (evolución mes a mes) dibujada a mano con
    QPainter, sin depender de ninguna librería de gráficos externa."""

    def __init__(self, parent=None, color="#c0392b", color_texto="#dcdcdc", color_fondo=None):
        super().__init__(parent, color_texto, color_fondo, altura_minima=160)
        self._color = QColor(color)

    def establecer_datos(self, datos):
        """datos: lista de tuplas ('YYYY-MM', valor), en orden cronológico."""
        super().establecer_datos(datos)

    def _hay_datos(self):
        return bool(self._datos) and any(valor != 0 for _, valor in self._datos)

    def _dibujar(self, painter):
        maximo = max(valor for _, valor in self._datos) or 1
        ancho, alto = self.width(), self.height()
        alto_util = alto - 22
        ancho_col = ancho / len(self._datos)
        painter.setFont(QFont(painter.font().family(), 8))
        for i, (mes, valor) in enumerate(self._datos):
            x = i * ancho_col
            alto_barra = max((valor / maximo) * (alto_util - 16), 1) if valor > 0 else 0
            y_barra = alto_util - alto_barra
            if valor > 0:
                painter.setBrush(QBrush(self._color))
                painter.setPen(Qt.PenStyle.NoPen)
                ancho_barra = max(ancho_col * 0.5, 4)
                painter.drawRoundedRect(QRectF(x + (ancho_col - ancho_barra) / 2, y_barra, ancho_barra, alto_barra), 2, 2)
                painter.setPen(self._color_texto)
                painter.drawText(QRectF(x, y_barra - 14, ancho_col, 14), Qt.AlignmentFlag.AlignCenter, str(valor))
            painter.setPen(self._color_texto)
            etiqueta_mes = f"{mes[5:7]}/{mes[2:4]}"
            painter.drawText(QRectF(x, alto_util + 2, ancho_col, 18), Qt.AlignmentFlag.AlignCenter, etiqueta_mes)
