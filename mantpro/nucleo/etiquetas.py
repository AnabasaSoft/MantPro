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

"""Etiquetas con código QR para las máquinas, en PDF listo para imprimir.

Hoja A4 de 3 × 8 etiquetas de 70 × 37 mm (el formato de las hojas adhesivas
más comunes: Apli 1274, Avery 3474...; también vale en folio normal y
recortando). Cada etiqueta lleva un QR con el texto "mantpro:maquina:<id>",
que la app MantPro reconoce al escanearlo y abre la ficha de esa máquina (sin
necesitar conexión: la app ya tiene la lista de máquinas guardada).
"""

from io import BytesIO

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

from . import maquinas

PREFIJO_QR = "mantpro:maquina:"
COLUMNAS, FILAS = 3, 8
ANCHO, ALTO = 70 * mm, 37 * mm


def contenido_qr(maquina_id):
    return f"{PREFIJO_QR}{int(maquina_id)}"


def _imagen_qr(texto):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=1)
    qr.add_data(texto)
    qr.make(fit=True)
    buf = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def generar_pdf(ruta, ids_maquinas, marco=True):
    """Crea el PDF con una etiqueta por máquina, en el orden dado. Con
    `marco`, dibuja un borde fino para recortar (en hojas adhesivas
    precortadas se puede quitar). Devuelve el número de etiquetas."""
    todas = {m["id"]: m for m in maquinas.listar_maquinas()}
    rutas = maquinas.mapa_rutas_completas()
    lista = [todas[i] for i in ids_maquinas if i in todas]
    ancho_pag, alto_pag = A4
    margen_x = (ancho_pag - COLUMNAS * ANCHO) / 2
    margen_y = (alto_pag - FILAS * ALTO) / 2
    c = canvas.Canvas(ruta, pagesize=A4)
    c.setTitle("MantPro - QR")
    for n, m in enumerate(lista):
        pos = n % (COLUMNAS * FILAS)
        if n and pos == 0:
            c.showPage()
        x = margen_x + (pos % COLUMNAS) * ANCHO
        y = alto_pag - margen_y - (pos // COLUMNAS + 1) * ALTO
        if marco:
            c.setStrokeGray(0.8)
            c.setLineWidth(0.3)
            c.rect(x, y, ANCHO, ALTO)
        lado = ALTO - 6 * mm
        c.drawImage(_imagen_qr(contenido_qr(m["id"])), x + 3 * mm, y + 3 * mm, lado, lado)

        # Texto a la derecha del QR: nombre (en negrita, hasta 3 líneas),
        # la máquina superior y la zona, si las tiene.
        tx = x + 3 * mm + lado + 2.5 * mm
        ancho_txt = x + ANCHO - 2.5 * mm - tx
        cy = y + ALTO - 6.5 * mm
        c.setFillGray(0)
        c.setFont("Helvetica-Bold", 10)
        for linea in simpleSplit(m["nombre"], "Helvetica-Bold", 10, ancho_txt)[:3]:
            c.drawString(tx, cy, linea)
            cy -= 11.5
        c.setFont("Helvetica", 7)
        c.setFillGray(0.3)
        ruta_txt = rutas.get(m["id"], "")
        superior = ruta_txt.rsplit(" > ", 1)[0] if " > " in ruta_txt else ""
        for extra in (superior, m.get("zona_nombre") or ""):
            for linea in simpleSplit(extra, "Helvetica", 7, ancho_txt)[:2]:
                if cy < y + 7 * mm:
                    break
                c.drawString(tx, cy, linea)
                cy -= 8.5
        c.setFont("Helvetica", 6)
        c.drawString(tx, y + 3.5 * mm, f"MantPro · #{m['id']}")
    c.save()
    return len(lista)
