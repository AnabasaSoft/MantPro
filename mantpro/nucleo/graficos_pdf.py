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
"""Gráficos para los PDF dibujados con reportlab, sin Qt: los mismos que pinta el PC con QPainter
(interfaz/widgets/graficos.py), con texto negro sobre fondo claro. Los usan los informes del núcleo cuando no reciben
los PNG del PC (MantPro Web, que no tiene Qt). Cada función devuelve un Drawing de [ancho] × [alto] puntos."""

from .. import idiomas

FONDO = "#f0f0f0"
TEXTO = "#000000"
COLORES_CIRCULAR = ("#3daee9", "#e67e22", "#2ecc71", "#e74c3c", "#9b59b6", "#f1c40f", "#1abc9c", "#95a5a6")


def _tt(clave, defecto):
    valor = idiomas.t(clave)
    return defecto if valor == clave else valor


def _lienzo(ancho, alto):
    from reportlab.graphics.shapes import Drawing, Rect
    from reportlab.lib import colors
    d = Drawing(ancho, alto)
    d.add(Rect(0, 0, ancho, alto, fillColor=colors.HexColor(FONDO), strokeColor=None))
    return d


def _vacio(d, ancho, alto, texto):
    from reportlab.graphics.shapes import String
    from reportlab.lib import colors
    d.add(String(ancho / 2, alto / 2 - 4, texto, fontSize=10, textAnchor="middle", fillColor=colors.HexColor("#888888")))
    return d


def _recortar(texto, ancho_pt, tam):
    """Corta [texto] con «…» para que quepa en [ancho_pt] (como elidedText del PC)."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    texto = str(texto)
    if stringWidth(texto, "Helvetica", tam) <= ancho_pt:
        return texto
    while texto and stringWidth(texto + "…", "Helvetica", tam) > ancho_pt:
        texto = texto[:-1]
    return texto + "…"


def ranking(pares, ancho, alto, color, formato=str, alto_fila_max=None):
    """Barras horizontales de [(etiqueta, valor)], de arriba abajo: etiqueta, barra y valor (GraficoBarrasRanking)."""
    from reportlab.graphics.shapes import Rect, String
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.lib import colors
    d = _lienzo(ancho, alto)
    if not pares:
        return _vacio(d, ancho, alto, _tt("lbl_sin_datos_grafico", "Sin datos"))
    tam = 8
    maximo = max(v for _, v in pares) or 1
    alto_fila = alto / len(pares)
    if alto_fila_max:
        alto_fila = min(alto_fila, alto_fila_max)
    ancho_etiqueta = min(130, ancho * 0.3)
    ancho_valor = max(24, max(stringWidth(formato(v), "Helvetica", tam) for _, v in pares) + 6)
    x_barra = ancho_etiqueta + 6
    disponible = max(ancho - x_barra - ancho_valor - 6, 10)
    for i, (etiqueta, valor) in enumerate(pares):
        centro = alto - alto_fila * (i + 0.5)
        d.add(String(4, centro - 3, _recortar(etiqueta, ancho_etiqueta - 6, tam), fontSize=tam, fillColor=colors.HexColor(TEXTO)))
        largo = max(disponible * valor / maximo, 2)
        grueso = min(alto_fila * 0.6, 16)
        d.add(Rect(x_barra, centro - grueso / 2, largo, grueso, rx=2, ry=2, fillColor=colors.HexColor(color), strokeColor=None))
        d.add(String(x_barra + disponible + 4, centro - 3, formato(valor), fontSize=tam, fillColor=colors.HexColor(TEXTO)))
    return d


def mensual(pares, ancho, alto, color, formato=str):
    """Barras verticales de [('AAAA-MM', valor)] en orden, con «MM/AA» debajo y el valor encima (GraficoBarrasMensual)."""
    from reportlab.graphics.shapes import Rect, String
    from reportlab.lib import colors
    d = _lienzo(ancho, alto)
    if not pares or not any(v for _, v in pares):
        return _vacio(d, ancho, alto, _tt("lbl_sin_datos_grafico", "Sin datos"))
    tam = 7 if len(pares) > 14 else 8
    maximo = max(v for _, v in pares) or 1
    abajo = 16                       # hueco de las etiquetas de los meses
    util = alto - abajo - 14         # y el del valor encima de la barra más alta
    ancho_col = ancho / len(pares)
    for i, (mes, valor) in enumerate(pares):
        x = i * ancho_col
        if valor > 0:
            alto_barra = max(valor / maximo * util, 1)
            ancho_barra = max(ancho_col * 0.5, 3)
            d.add(Rect(x + (ancho_col - ancho_barra) / 2, abajo, ancho_barra, alto_barra, rx=1.5, ry=1.5,
                       fillColor=colors.HexColor(color), strokeColor=None))
            d.add(String(x + ancho_col / 2, abajo + alto_barra + 3, formato(valor), fontSize=tam, textAnchor="middle",
                         fillColor=colors.HexColor(TEXTO)))
        d.add(String(x + ancho_col / 2, 4, f"{mes[5:7]}/{mes[2:4]}", fontSize=tam, textAnchor="middle",
                     fillColor=colors.HexColor(TEXTO)))
    return d


def circular(pares, ancho, alto):
    """Tarta de [(etiqueta, valor)] (solo los que tienen algo) con la leyenda «etiqueta (valor)» al lado
    (GraficoCircularTrabajos)."""
    from reportlab.graphics.shapes import Rect, String, Wedge
    from reportlab.lib import colors
    pares = [(e, v) for e, v in pares if v > 0]
    d = _lienzo(ancho, alto)
    if not pares:
        return _vacio(d, ancho, alto, _tt("lbl_sin_trabajos_grafico", "Sin trabajos registrados"))
    total = sum(v for _, v in pares)
    lado = max(min(alto - 16, ancho - 120 - 16), 24)
    cx, cy, radio = 8 + lado / 2, alto / 2, lado / 2
    inicio = 90.0                    # las 12 en punto, en el sentido de las agujas del reloj, como el PC
    for i, (_, valor) in enumerate(pares):
        extension = valor / total * 360
        color = colors.HexColor(COLORES_CIRCULAR[i % len(COLORES_CIRCULAR)])
        if extension >= 359.99:
            from reportlab.graphics.shapes import Circle
            d.add(Circle(cx, cy, radio, fillColor=color, strokeColor=colors.HexColor("#1e1e1e"), strokeWidth=0.6))
        else:
            d.add(Wedge(cx, cy, radio, inicio - extension, inicio, fillColor=color,
                        strokeColor=colors.HexColor("#1e1e1e"), strokeWidth=0.6))
        inicio -= extension
    x = 8 + lado + 12
    for i, (etiqueta, valor) in enumerate(pares):
        y = alto - 14 - i * 13
        if y < 4:
            d.add(String(x, y + 2, "…", fontSize=8, fillColor=colors.HexColor(TEXTO)))
            break
        d.add(Rect(x, y, 8, 8, fillColor=colors.HexColor(COLORES_CIRCULAR[i % len(COLORES_CIRCULAR)]), strokeColor=None))
        d.add(String(x + 12, y + 1, _recortar(f"{etiqueta} ({valor})", ancho - x - 16, 8), fontSize=8,
                     fillColor=colors.HexColor(TEXTO)))
    return d
