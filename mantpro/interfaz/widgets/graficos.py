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

"""Gráficos del dashboard, dibujados con QPainter."""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QSettings
from PyQt6.QtGui import QColor, QBrush, QPainter, QPen, QFont

from ..comun import tt

class _GraficoBase(QWidget):
    """Base común de las gráficas dibujadas a mano con QPainter (sin depender
    de ninguna librería de gráficos externa): centraliza el guardado de
    datos, el color de texto/fondo y el estado "sin datos", dejando en cada
    subclase solo la parte de dibujo (_dibujar) que de verdad cambia entre
    ellas."""

    def __init__(self, parent=None, color_texto=None, color_fondo=None, altura_minima=160):
        super().__init__(parent)
        self._datos = []
        # Sin color de texto fijo (el caso normal en pantalla), se toma el del
        # tema activo al pintar; los PDF pasan uno fijo (negro sobre blanco).
        self._color_texto_fijo = QColor(color_texto) if color_texto else None
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

    @property
    def _color_texto(self):
        if self._color_texto_fijo is not None:
            return self._color_texto_fijo
        oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
        return QColor("#dcdcdc" if oscuro else "#202020")

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

    def __init__(self, parent=None, color_texto=None, color_fondo=None):
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

    def __init__(self, parent=None, color="#c0392b", color_texto=None, color_fondo=None, formato_valor=None):
        super().__init__(parent, color_texto, color_fondo, altura_minima=160)
        self._color = QColor(color)
        # Función valor → texto (p. ej. para importes); sin ella, str(valor)
        self._formato_valor = formato_valor or str

    def _dibujar(self, painter):
        maximo = max(valor for _, valor in self._datos) or 1
        ancho, alto = self.width(), self.height()
        alto_fila = alto / len(self._datos)
        ancho_etiqueta = 130
        painter.setFont(QFont(painter.font().family(), 9))
        metrica = painter.fontMetrics()
        ancho_valor = max(30, max(metrica.horizontalAdvance(self._formato_valor(v)) for _, v in self._datos) + 8)
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
                              Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self._formato_valor(valor))


class GraficoBarrasMensual(_GraficoBase):
    """Gráfica de barras verticales (evolución mes a mes) dibujada a mano con
    QPainter, sin depender de ninguna librería de gráficos externa."""

    def __init__(self, parent=None, color="#c0392b", color_texto=None, color_fondo=None, formato_valor=None):
        super().__init__(parent, color_texto, color_fondo, altura_minima=160)
        self._color = QColor(color)
        self._formato_valor = formato_valor or str

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
                painter.drawText(QRectF(x, y_barra - 14, ancho_col, 14), Qt.AlignmentFlag.AlignCenter, self._formato_valor(valor))
            painter.setPen(self._color_texto)
            etiqueta_mes = f"{mes[5:7]}/{mes[2:4]}"
            painter.drawText(QRectF(x, alto_util + 2, ancho_col, 18), Qt.AlignmentFlag.AlignCenter, etiqueta_mes)


class GraficoEvolucion(_GraficoBase):
    """Evolución de una lectura en el tiempo (p. ej. la resistencia de tierra de cada revisión):
    una línea con un punto por lectura, la banda del rango correcto sombreada en verde y los
    puntos fuera de rango en rojo. Las fechas van en el eje X a su distancia real.
    Con [series] (p. ej. las fases L1, L2, L3 de un motor trifásico) dibuja una línea por
    serie, cada una de su color y con leyenda, a partir de "valores" de cada dato."""

    COLORES_SERIES = ("#3daee9", "#e67e22", "#8e44ad")

    def __init__(self, parent=None, color="#3daee9", color_texto=None, color_fondo=None, formato_fecha=None):
        super().__init__(parent, color_texto, color_fondo, altura_minima=200)
        self._color = QColor(color)
        self._minimo = self._maximo = None
        self._unidad = ""
        self._series = None
        self._formato_fecha = formato_fecha or (lambda f: f)

    def establecer_datos(self, datos, minimo=None, maximo=None, unidad="", series=None):
        """datos: lista de dicts {"fecha": 'AAAA-MM-DD', "valor": número o None, "fuera": bool}, en orden.
        Con [series] (nombres), cada dato trae "valores": un número o None por serie."""
        self._minimo, self._maximo, self._unidad = minimo, maximo, unidad or ""
        self._series = list(series) if series else None
        if self._series:
            datos = [dict(d, valores=list(d.get("valores") or [])) for d in datos
                     if d.get("fecha") and any(v is not None for v in (d.get("valores") or []))]
        else:
            datos = [dict(d, valores=[d.get("valor")]) for d in datos if d.get("valor") is not None and d.get("fecha")]
        super().establecer_datos(datos)

    @staticmethod
    def _dia(fecha):
        from datetime import date
        try:
            return date.fromisoformat(fecha[:10]).toordinal()
        except ValueError:
            return 0

    @staticmethod
    def _numero(v):
        return f"{v:g}"

    def _dibujar(self, painter):
        valores = [v for d in self._datos for v in d["valores"] if v is not None]
        limites = [v for v in (self._minimo, self._maximo) if v is not None]
        bajo, alto_v = min(valores + limites), max(valores + limites)
        if alto_v == bajo:
            bajo, alto_v = bajo - 1, alto_v + 1
        margen_v = (alto_v - bajo) * 0.08
        bajo, alto_v = bajo - margen_v, alto_v + margen_v
        dias = [self._dia(d["fecha"]) for d in self._datos]
        d0, d1 = min(dias), max(dias)
        painter.setFont(QFont(painter.font().family(), 8))
        metricas = painter.fontMetrics()
        izq = max(metricas.horizontalAdvance(self._numero(v)) for v in (bajo, alto_v)) + 10
        der, arriba, abajo = 14, 10, 22
        ancho, alto = self.width() - izq - der, self.height() - arriba - abajo
        if ancho <= 10 or alto <= 10:
            return

        def x_de(dia):
            return izq + (ancho / 2 if d1 == d0 else (dia - d0) / (d1 - d0) * ancho)

        def y_de(v):
            return arriba + (alto_v - v) / (alto_v - bajo) * alto

        texto = self._color_texto
        # Banda del rango correcto (con solo mínimo o solo máximo, hasta el borde)
        if limites:
            y_sup = y_de(self._maximo) if self._maximo is not None else arriba
            y_inf = y_de(self._minimo) if self._minimo is not None else arriba + alto
            verde = QColor("#2ecc71"); verde.setAlpha(45)
            painter.fillRect(QRectF(izq, y_sup, ancho, y_inf - y_sup), verde)
            painter.setPen(QPen(QColor("#27ae60"), 1, Qt.PenStyle.DashLine))
            for v in (self._minimo, self._maximo):
                if v is not None:
                    painter.drawLine(int(izq), int(y_de(v)), int(izq + ancho), int(y_de(v)))
        # Ejes y etiquetas
        painter.setPen(QPen(texto, 1))
        painter.drawLine(int(izq), int(arriba), int(izq), int(arriba + alto))
        painter.drawLine(int(izq), int(arriba + alto), int(izq + ancho), int(arriba + alto))
        etiquetas = sorted({round(v, 6) for v in [bajo + margen_v, alto_v - margen_v] + limites})
        for v in etiquetas:
            painter.drawText(QRectF(0, y_de(v) - 8, izq - 5, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, self._numero(v))
        primera, ultima = self._datos[0]["fecha"], self._datos[-1]["fecha"]
        painter.drawText(QRectF(izq, arriba + alto + 4, ancho, 16), Qt.AlignmentFlag.AlignLeft, self._formato_fecha(primera))
        if ultima != primera:
            painter.drawText(QRectF(izq, arriba + alto + 4, ancho, 16), Qt.AlignmentFlag.AlignRight, self._formato_fecha(ultima))
        # Líneas y puntos (una por serie; en rojo los que se salen del rango)
        def fuera(v):
            return (self._minimo is not None and v < self._minimo) or (self._maximo is not None and v > self._maximo)
        n_series = len(self._series) if self._series else 1
        for k in range(n_series):
            color = QColor(self.COLORES_SERIES[k % len(self.COLORES_SERIES)]) if self._series else self._color
            puntos = [(x_de(dias[i]), y_de(d["valores"][k]),
                       fuera(d["valores"][k]) if self._series else d.get("fuera"))
                      for i, d in enumerate(self._datos) if k < len(d["valores"]) and d["valores"][k] is not None]
            painter.setPen(QPen(color, 2))
            for (xa, ya, _), (xb, yb, _) in zip(puntos, puntos[1:]):
                painter.drawLine(int(xa), int(ya), int(xb), int(yb))
            for x, y, es_fuera in puntos:
                c = QColor("#e74c3c") if es_fuera else color
                painter.setPen(QPen(c, 1))
                painter.setBrush(QBrush(c))
                painter.drawEllipse(QRectF(x - 4, y - 4, 8, 8))
        # Leyenda arriba a la derecha
        if self._series:
            x = izq + ancho
            for k in reversed(range(n_series)):
                nombre = self._series[k]
                w = metricas.horizontalAdvance(nombre)
                x -= w + 4
                painter.setPen(QPen(texto, 1))
                painter.drawText(QRectF(x, arriba, w + 4, 14), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, nombre)
                x -= 16
                color = QColor(self.COLORES_SERIES[k % len(self.COLORES_SERIES)])
                painter.setPen(QPen(color, 3))
                painter.drawLine(int(x), int(arriba + 7), int(x + 12), int(arriba + 7))
                x -= 10
