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


# ---------------------------------------------------------------- evolución de una lectura (📈 Lecturas)

COLORES_SERIES = ("#3daee9", "#e67e22", "#8e44ad")          # los de GraficoEvolucion del PC (L1, L2, L3)
COLOR_FUERA = "#e74c3c"


def datos_evolucion(lecturas, series=None):
    """Las lecturas que se dibujan, cada una con «valores» (uno por serie), como GraficoEvolucion.establecer_datos."""
    if series:
        return [dict(d, valores=list(d.get("valores") or [])) for d in lecturas
                if d.get("fecha") and any(v is not None for v in (d.get("valores") or []))]
    return [dict(d, valores=[d.get("valor")]) for d in lecturas if d.get("valor") is not None and d.get("fecha")]


def escala_evolucion(datos, minimo, maximo):
    """(bajo, alto, días de la primera y la última, etiquetas del eje Y) para dibujar [datos] con su rango."""
    from datetime import date
    valores = [v for d in datos for v in d["valores"] if v is not None]
    limites = [v for v in (minimo, maximo) if v is not None]
    bajo, alto = min(valores + limites), max(valores + limites)
    if alto == bajo:
        bajo, alto = bajo - 1, alto + 1
    margen = (alto - bajo) * 0.08
    etiquetas = sorted({round(v, 6) for v in [bajo, alto] + limites})
    dias = []
    for d in datos:
        try:
            dias.append(date.fromisoformat(d["fecha"][:10]).toordinal())
        except ValueError:
            dias.append(0)
    return bajo - margen, alto + margen, dias, etiquetas


def fuera_de_rango(v, minimo, maximo):
    return (minimo is not None and v < minimo) or (maximo is not None and v > maximo)


def evolucion(lecturas, minimo, maximo, series, ancho, alto, formato_fecha=lambda f: f):
    """El gráfico de GraficoEvolucion para el PDF: la banda del rango correcto en verde, una línea por serie y los
    puntos fuera de rango en rojo; las fechas a su distancia real."""
    from reportlab.graphics.shapes import Circle, Line, PolyLine, Rect, String
    from reportlab.lib import colors
    d = _lienzo(ancho, alto)
    datos = datos_evolucion(lecturas, series)
    if not datos:
        return _vacio(d, ancho, alto, _tt("lbl_sin_datos_grafico", "Sin datos"))
    bajo, tope, dias, etiquetas = escala_evolucion(datos, minimo, maximo)
    d0, d1 = min(dias), max(dias)
    izq, der, arriba, abajo = 40, 10, 10, 18                  # (en el PDF, y crece hacia arriba)
    w, h = ancho - izq - der, alto - arriba - abajo

    def x_de(dia):
        return izq + (w / 2 if d1 == d0 else (dia - d0) / (d1 - d0) * w)

    def y_de(v):
        return abajo + (v - bajo) / (tope - bajo) * h

    negro = colors.HexColor(TEXTO)
    if minimo is not None or maximo is not None:
        y_inf = y_de(minimo) if minimo is not None else abajo
        y_sup = y_de(maximo) if maximo is not None else abajo + h
        d.add(Rect(izq, y_inf, w, y_sup - y_inf, fillColor=colors.Color(0.18, 0.8, 0.44, alpha=0.18), strokeColor=None))
        for v in (minimo, maximo):
            if v is not None:
                d.add(Line(izq, y_de(v), izq + w, y_de(v), strokeColor=colors.HexColor("#27ae60"), strokeDashArray=[3, 2]))
    d.add(Line(izq, abajo, izq, abajo + h, strokeColor=negro))
    d.add(Line(izq, abajo, izq + w, abajo, strokeColor=negro))
    for v in etiquetas:
        d.add(String(izq - 4, y_de(v) - 3, f"{v:g}", fontSize=7, textAnchor="end", fillColor=negro))
    d.add(String(izq, 4, formato_fecha(datos[0]["fecha"]), fontSize=7, fillColor=negro))
    if datos[-1]["fecha"] != datos[0]["fecha"]:
        d.add(String(izq + w, 4, formato_fecha(datos[-1]["fecha"]), fontSize=7, textAnchor="end", fillColor=negro))
    n = len(series) if series else 1
    for k in range(n):
        color = colors.HexColor(COLORES_SERIES[k % len(COLORES_SERIES)])
        puntos = [(x_de(dias[i]), y_de(dd["valores"][k]),
                   fuera_de_rango(dd["valores"][k], minimo, maximo) if series else dd.get("fuera"))
                  for i, dd in enumerate(datos) if k < len(dd["valores"]) and dd["valores"][k] is not None]
        if len(puntos) > 1:
            d.add(PolyLine([c for x, y, _ in puntos for c in (x, y)], strokeColor=color, strokeWidth=1.5))
        for x, y, es_fuera in puntos:
            c = colors.HexColor(COLOR_FUERA) if es_fuera else color
            d.add(Circle(x, y, 2.5, fillColor=c, strokeColor=c))
    if series:
        x = izq + w
        for k in reversed(range(n)):
            x -= 26
            d.add(Line(x, abajo + h - 3, x + 8, abajo + h - 3, strokeColor=colors.HexColor(COLORES_SERIES[k]), strokeWidth=2.5))
            d.add(String(x + 10, abajo + h - 5, series[k], fontSize=7, fillColor=negro))
    return d
