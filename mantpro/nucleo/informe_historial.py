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
"""Exportar el historial (CSV, Excel y el informe en PDF) y los textos de los trabajos en las exportaciones, sin Qt:
lo usan el PC («Archivo → Exportar…») y MantPro Web (la descarga del Historial).

Los costes (importes de material y de mano de obra) solo para administradores: [admin] lo dice (None = el usuario
de este PC). Los textos salen en el idioma activo (en MantPro Web, el de cada petición)."""

import csv
import html
import os
import re
from xml.sax.saxutils import escape

from .. import idiomas
from . import checklists as _checklists, consumos, mano_obra, usuarios
from .fotos import _RE_GALERIA, fotos_galeria
from .seguridad import es_video


def _tt(clave, defecto):
    """t() con texto por defecto (si la clave no existe, el literal en castellano)."""
    valor = idiomas.t(clave)
    return defecto if valor == clave else valor


def _t(clave):
    return idiomas.t(clave)


def resumen_texto(items):
    """«8 bien · 1 mal · 1 sin revisar» para el historial y las exportaciones."""
    r = _checklists.recuento(items)
    partes = []
    if r["ok"]: partes.append(_tt("chk_resumen_ok", "{n} bien").format(n=r["ok"]))
    if r["mal"]: partes.append(_tt("chk_resumen_mal", "{n} mal").format(n=r["mal"]))
    if r["na"]: partes.append(_tt("chk_resumen_na", "{n} no aplica").format(n=r["na"]))
    if r["sin"]: partes.append(_tt("chk_resumen_sin", "{n} sin revisar").format(n=r["sin"]))
    return " · ".join(partes)


def estado_plano(estado):
    """Resultado en texto sin emojis (para PDF, Excel y CSV)."""
    return {"ok": _tt("chk_txt_ok", "Bien"), "mal": _tt("chk_txt_mal", "Mal"),
            "na": _tt("chk_txt_na", "No aplica")}.get(estado, _tt("chk_txt_sin", "Sin revisar"))


def linea_export(it):
    """«Presión de trabajo: Mal — 9,1 bar (Revisar presostato)»; un separador, «── Zona 1 ──»."""
    if it.get("tipo") == _checklists.SECCION:
        return f"── {it['texto']} ──"
    texto = f"{it['texto']}: {estado_plano(it.get('estado'))}"
    if it.get("valor"):
        texto += f" — {_checklists.texto_valor(it)}"
        deseq = texto_desequilibrio(it)
        if deseq:
            texto += f" ({deseq})"
    if it.get("nota"):
        texto += f" ({it['nota']})"
    return texto


def texto_desequilibrio(it):
    """«Desequilibrio 3,2 % · se aparta más L2» de un punto trifásico con las tres fases, o «»."""
    if it.get("tipo") != "trifasica":
        return ""
    d = _checklists.desequilibrio(it.get("valor"))
    if not d:
        return ""
    texto = _tt("chk_desequilibrio", "Desequilibrio {p} % · se aparta más {fase}").format(
        p=f"{d[0]:g}", fase=_checklists.FASES[d[1]])
    if _checklists.desequilibrio_excesivo(it, it.get("valor")):
        texto += " — " + texto_deseq_max(it)
    return texto


def texto_deseq_max(punto):
    """«desequilibrio máx. 5 %» de un punto trifásico con límite, o «»."""
    limite = _checklists._deseq_max(punto) if punto.get("tipo") == "trifasica" else None
    return _tt("chk_deseq_max", "desequilibrio máx. {p} %").format(p=f"{limite:g}") if limite is not None else ""


def texto_export(lista):
    """Toda la lista en una celda (CSV y Excel)."""
    if not lista:
        return "-"
    return lista["plantilla"] + "\n" + "\n".join(
        ("" if it.get("tipo") == _checklists.SECCION else "• ") + linea_export(it) for it in lista["items"])


def texto_repuestos_export(mats, moneda, admin=None):
    """Repuestos usados en una celda (CSV y Excel) o en el PDF."""
    if not mats:
        return "-"
    ver_precios = usuarios.es_admin() if admin is None else admin   # precios e importes: solo para administradores
    lineas = [f"• {m['cantidad']:g} {m.get('unidad') or ''} {m['nombre']}".replace("  ", " ") +
              (f" — {consumos.formato_importe(m['importe'], moneda)}" if ver_precios and m.get("importe") is not None else "")
              for m in mats]
    if not ver_precios:
        return "\n".join(lineas)
    importe, sin_precio = consumos.coste(mats)
    lineas.append(f"{_tt('lbl_coste_material', 'Coste de material')}: {consumos.formato_importe(importe, moneda)}" +
                  (f" ({_tt('lbl_sin_precio_algunos', '(hay artículos sin precio)').strip('()')})" if sin_precio else ""))
    return "\n".join(lineas)


def texto_tiempo_export(t, moneda, admin=None):
    """«1 h 30 min × 2 — 54,00 €» (o «-» si no hay tiempo apuntado)."""
    if not t:
        return "-"
    texto = mano_obra.texto_tiempo(t)
    if t.get("importe") is not None and (usuarios.es_admin() if admin is None else admin):   # el coste: solo administradores
        texto += f" — {consumos.formato_importe(t['importe'], moneda)}"
    return texto


# ---------------------------------------------------------------- historial: datos de cada trabajo

def _texto_limpio(desc):
    texto = re.sub(r"\[FOTO.*?:.*?\]", "", desc or "")
    return re.sub(r"\[REF:.*?\]", "", texto).strip()


def _marca(desc, marca):
    m = re.search(rf"\[{marca}:\s*(.*?)\]", desc or "")
    return m.group(1).split("]")[0].strip() if m else None


def cabeceras_csv():
    return [_tt("hdr_id", "ID"), _tt("hdr_fecha", "Fecha"), _tt("hdr_descripcion", "Descripción"), _tt("hdr_maquina", "Máquina"),
            _tt("hdr_realizado_por", "Realizado por"), _tt("hdr_foto_antes", "Foto Antes"), _tt("hdr_foto_despues", "Foto Después"),
            _tt("lbl_coleccion_fotos", "Colección de fotos"), _tt("lbl_checklist", "Lista de comprobación"),
            _tt("lbl_repuestos_usados", "🔩 Materiales usados").replace("🔩", "").strip(),
            _tt("lbl_tiempo_trabajado", "⏱️ Tiempo trabajado").replace("⏱️", "").strip()]


def generar_csv(datos, salida, mapa_maquinas, admin=None):
    """El historial en CSV («;»). [datos]: filas de obtener_todas_cronologico; [salida]: un fichero de texto abierto
    (con newline=""); [mapa_maquinas]: maquinas.mapa_rutas_completas()."""
    ids = [tarea[0] for tarea in datos]
    listas, usados, tiempos = _checklists.resultados_de(ids), consumos.materiales_de_trabajos(ids), mano_obra.tiempos_de(ids)
    moneda = consumos.moneda()
    writer = csv.writer(salida, delimiter=";")
    writer.writerow(cabeceras_csv())
    for tarea in datos:
        autor = tarea[4] if len(tarea) > 4 and tarea[4] else usuarios.ETIQUETA_HISTORICO
        maquina_nombre = mapa_maquinas.get(tarea[5], "-") if len(tarea) > 5 and tarea[5] else "-"
        writer.writerow([tarea[0], idiomas.formato_fecha_localizada(tarea[1]), _texto_limpio(tarea[2]), maquina_nombre, autor,
                         _marca(tarea[2], "FOTO") or "-", _marca(tarea[2], "FOTO_DESPUES") or "-",
                         ", ".join(fotos_galeria(tarea[2])) or "-",
                         texto_export(listas.get(tarea[0])),
                         texto_repuestos_export(usados.get(tarea[0]), moneda, admin),
                         texto_tiempo_export(tiempos.get(tarea[0]), moneda, admin)])


def _medidas(ruta_img):
    """(ancho, alto) en píxeles de una imagen, o None si no se puede leer."""
    try:
        from PIL import Image as ImagenPIL
        with ImagenPIL.open(ruta_img) as imagen:
            ancho, alto = imagen.size
        return (ancho, alto) if ancho and alto else None
    except Exception:
        return None


def _miniatura_excel(ruta_img):
    """Foto de la colección reducida (JPEG de 320 px como mucho) e insertada desde memoria: con muchas fotos,
    incrustar los originales dispara el tamaño del Excel."""
    try:
        from io import BytesIO
        from PIL import Image as ImagenPIL, ImageOps
        with ImagenPIL.open(ruta_img) as original:
            foto = ImageOps.exif_transpose(original).convert("RGB")
            foto.thumbnail((320, 320))
            buffer = BytesIO()
            foto.save(buffer, "JPEG", quality=80)
            ancho, alto = foto.size
    except Exception:
        return None
    escala = min(160.0 / ancho, 100.0 / alto)
    return {"image_data": buffer, "x_scale": escala, "y_scale": escala, "x_offset": 5, "y_offset": 5, "object_position": 1}


def generar_excel(datos, ruta, carpeta_fotos, mapa_maquinas, lineas_sede=None, admin=None):
    """El historial en Excel, con las fotos de antes y de después incrustadas y la colección en miniatura.
    [lineas_sede]: datos de la sede para el encabezado de cada página impresa."""
    import xlsxwriter
    workbook = xlsxwriter.Workbook(ruta)
    worksheet = workbook.add_worksheet("Registro")
    bold = workbook.add_format({"bold": True, "bg_color": "#3daee9", "color": "white", "border": 1, "align": "center", "valign": "vcenter"})
    wrap = workbook.add_format({"text_wrap": True, "valign": "top", "border": 1})
    center = workbook.add_format({"valign": "vcenter", "align": "center", "border": 1})
    headers = [_tt("hdr_id", "ID"), _tt("hdr_fecha", "Fecha"), _tt("hdr_descripcion", "Descripción"), _tt("hdr_maquina", "Máquina"),
               _tt("hdr_realizado_por", "Realizado por"), _tt("hdr_foto_antes", "Foto Antes"), _tt("hdr_foto_despues", "Foto Después")]
    for col, texto in enumerate(headers):
        worksheet.write(0, col, texto, bold)
    if lineas_sede:      # la sede (nombre, CIF, dirección…) en el encabezado de cada página impresa
        worksheet.set_header("&L&B" + " · ".join(lineas_sede).replace("&", "&&"))
    for columnas, ancho in (("A:A", 5), ("B:B", 12), ("C:C", 60), ("D:D", 25), ("E:E", 20), ("F:F", 25), ("G:G", 25)):
        worksheet.set_column(columnas, ancho)

    def opciones_img(ruta_img):
        medidas = _medidas(ruta_img)
        if not medidas:
            return None
        escala = min(160.0 / medidas[0], 100.0 / medidas[1])      # que quepa justo en la celda, sin deformarla
        return {"x_scale": escala, "y_scale": escala, "x_offset": 5, "y_offset": 5, "object_position": 1}

    ids = [tarea[0] for tarea in datos]
    listas, usados, tiempos = _checklists.resultados_de(ids), consumos.materiales_de_trabajos(ids), mano_obra.tiempos_de(ids)
    moneda = consumos.moneda()
    # Columnas opcionales a partir de la H: lista de comprobación, repuestos y tiempo (si algún trabajo los tiene);
    # luego la colección de fotos, una columna por foto («Colección 1», «Colección 2»…)
    col_coleccion, col_lista, col_repuestos, col_tiempo = 7, None, None, None
    for existe, clave, defecto, ancho, nombre in ((listas, "lbl_checklist", "Lista de comprobación", 45, "lista"),
                                                  (usados, "lbl_repuestos_usados", "🔩 Materiales usados", 40, "repuestos"),
                                                  (tiempos, "lbl_tiempo_trabajado", "⏱️ Tiempo trabajado", 26, "tiempo")):
        if existe:
            worksheet.write(0, col_coleccion, _tt(clave, defecto).replace("🔩", "").replace("⏱️", "").strip(), bold)
            worksheet.set_column(col_coleccion, col_coleccion, ancho)
            if nombre == "lista":
                col_lista = col_coleccion
            elif nombre == "repuestos":
                col_repuestos = col_coleccion
            else:
                col_tiempo = col_coleccion
            col_coleccion += 1
    max_coleccion = max((len(fotos_galeria(tarea[2])) for tarea in datos), default=0)
    for k in range(max_coleccion):
        worksheet.write(0, col_coleccion + k, _tt("hdr_coleccion_n", "Colección {n}").format(n=k + 1), bold)
        worksheet.set_column(col_coleccion + k, col_coleccion + k, 25)
    for row, tarea in enumerate(datos, 1):
        worksheet.write(row, 0, tarea[0], center)
        worksheet.write(row, 1, idiomas.formato_fecha_localizada(tarea[1]), center)
        worksheet.write(row, 2, _texto_limpio(tarea[2]), wrap)
        worksheet.write(row, 3, mapa_maquinas.get(tarea[5], "-") if len(tarea) > 5 and tarea[5] else "-", center)
        worksheet.write(row, 4, tarea[4] if len(tarea) > 4 and tarea[4] else usuarios.ETIQUETA_HISTORICO, center)
        for col, marca in ((5, "FOTO"), (6, "FOTO_DESPUES")):          # fotos de antes y de después, incrustadas
            nombre = _marca(tarea[2], marca)
            if not nombre:
                worksheet.write(row, col, "-", center)
                continue
            ruta_img = os.path.join(carpeta_fotos, nombre)
            if not os.path.exists(ruta_img):
                worksheet.write(row, col, "No File", center)
                continue
            opc = opciones_img(ruta_img)
            try:
                if not opc:
                    raise ValueError
                worksheet.insert_image(row, col, ruta_img, opc)
            except Exception:
                worksheet.write(row, col, "Err Img", center)
        if col_lista is not None:
            worksheet.write(row, col_lista, texto_export(listas.get(tarea[0])), wrap)
        if col_repuestos is not None:
            worksheet.write(row, col_repuestos, texto_repuestos_export(usados.get(tarea[0]), moneda, admin), wrap)
        if col_tiempo is not None:
            worksheet.write(row, col_tiempo, texto_tiempo_export(tiempos.get(tarea[0]), moneda, admin), wrap)
        for k, nombre_g in enumerate(fotos_galeria(tarea[2])):
            if es_video(nombre_g):          # un vídeo no tiene miniatura en Excel: se pone su nombre
                worksheet.write(row, col_coleccion + k, f"{_tt('lbl_video', 'Vídeo')}: {nombre_g}", wrap)
                continue
            ruta_g = os.path.join(carpeta_fotos, nombre_g)
            opc = _miniatura_excel(ruta_g) if os.path.exists(ruta_g) else None
            try:
                if not opc:
                    raise ValueError
                worksheet.insert_image(row, col_coleccion + k, nombre_g, opc)
            except Exception:
                worksheet.write(row, col_coleccion + k, "No File" if not opc else "Err Img", center)
        worksheet.set_row(row, 90)
    workbook.close()


# ---------------------------------------------------------------- historial: el informe en PDF

def _miniatura_pdf(carpeta_fotos, nombre, ancho_max=None, alto_max=None):
    """Foto de la colección reducida (máx. 600 px, JPEG) para el PDF, así
    un trabajo con muchas fotos no dispara el tamaño del fichero. None si
    no existe o no se puede leer."""
    from reportlab.lib.units import cm
    from reportlab.platypus import Image as PDFImage
    ancho_max, alto_max = ancho_max or 2.6 * cm, alto_max or 2.2 * cm
    ruta = os.path.join(carpeta_fotos, nombre)
    if not os.path.exists(ruta):
        return None
    try:
        from io import BytesIO
        from PIL import Image as ImagenPIL, ImageOps
        with ImagenPIL.open(ruta) as original:
            foto = ImageOps.exif_transpose(original).convert("RGB")
            foto.thumbnail((600, 600))
            buffer = BytesIO(); foto.save(buffer, "JPEG", quality=80); buffer.seek(0)
            ancho, alto = foto.size
        escala = min(ancho_max / ancho, alto_max / alto)
        return PDFImage(buffer, width=ancho * escala, height=alto * escala)
    except Exception:
        return None


def generar_pdf(lista_trabajos, carpeta_fotos, mapa_maquinas=None, ruta_logo=None, admin=None):
    """El informe del historial en PDF (uno por elemento de [lista_trabajos]: {"archivo": ruta o fichero abierto en
    binario, "titulo", "datos": filas (fecha, descripcion, tags, autor, maquina_id, id), "sede": líneas bajo el
    título, "graficos": {png_ranking, png_mensual, png_pie, indicadores} o None}). Con fotos en miniatura, lista de
    comprobación, tiempo, repuestos y colección de cada trabajo. Lo usan el PC (en un hilo) y MantPro Web."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (Image as PDFImage, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                    TableStyle)
    mapa_maquinas = mapa_maquinas or {}
    styles = getSampleStyleSheet()

    for trabajo in lista_trabajos:
        doc = SimpleDocTemplate(trabajo["archivo"], pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []

        if ruta_logo and os.path.exists(ruta_logo):
            try:
                logo = PDFImage(ruta_logo, width=4*cm, height=2*cm)
                logo.hAlign = 'LEFT'
                logo.keepAspectRatio = True
                elements.append(logo)
                elements.append(Spacer(1, 10))
            except Exception:
                pass

        elements.append(Paragraph(trabajo["titulo"], styles['Title']))
        for linea in trabajo.get("sede") or []:   # datos de la sede (CIF, dirección, contacto)
            elements.append(Paragraph(html.escape(linea), styles['Normal']))
        elements.append(Spacer(1, 12))

        style_cell = styles["BodyText"]; style_cell.fontSize = 9
        style_header = ParagraphStyle("CabeceraTabla", parent=style_cell, textColor=colors.whitesmoke, fontName="Helvetica-Bold", fontSize=9)

        def cab(texto):
            return Paragraph(texto, style_header)

        filas_coleccion = []
        listas = _checklists.resultados_de([f[5] for f in trabajo["datos"] if len(f) > 5])
        usados = consumos.materiales_de_trabajos([f[5] for f in trabajo["datos"] if len(f) > 5])
        tiempos = mano_obra.tiempos_de([f[5] for f in trabajo["datos"] if len(f) > 5])
        moneda = consumos.moneda()
        data_tabla = [[cab(_t("hdr_fecha")), cab(_t("hdr_descripcion")), cab(_tt("hdr_maquina", "Máquina")),
                       cab(_tt("hdr_realizado_por", "Realizado por")),
                       cab(_t("hdr_foto_antes")), cab(_t("hdr_foto_despues"))]]

        for fila_pdf in trabajo["datos"]:
            fecha, desc, tags = fila_pdf[0], fila_pdf[1], fila_pdf[2]
            autor = fila_pdf[3] if len(fila_pdf) > 3 and fila_pdf[3] else usuarios.ETIQUETA_HISTORICO
            maquina_nombre = mapa_maquinas.get(fila_pdf[4], "-") if len(fila_pdf) > 4 and fila_pdf[4] else "-"
            fecha_formateada = idiomas.formato_fecha_localizada(fecha)

            desc_visual = desc
            img_obj = ""
            img_obj_d = ""

            # Fotos de antes y después: encajadas en su celda (3 cm de
            # ancho menos el margen) sin deformarlas. Antes se fijaba
            # el tamaño a mano y las apaisadas se salían de la celda.
            m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
            if m:
                img_obj = _miniatura_pdf(carpeta_fotos, m.group(1).split("]")[0].strip(), 2.75 * cm, 2.5 * cm) or ""
            m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc)
            if m_d:
                img_obj_d = _miniatura_pdf(carpeta_fotos, m_d.group(1).split("]")[0].strip(), 2.75 * cm, 2.5 * cm) or ""

            desc_visual = re.sub(r"\[FOTO:.*?\]", "", desc_visual)
            desc_visual = re.sub(r"\[FOTO_DESPUES:.*?\]", "", desc_visual)
            desc_visual = _RE_GALERIA.sub("", desc_visual)
            desc_visual = re.sub(r"\[REF:.*?\]", "", desc_visual).strip()

            p_desc = Paragraph(desc_visual.replace("\n", "<br/>"), style_cell)
            data_tabla.append([Paragraph(fecha_formateada, style_cell), p_desc, Paragraph(maquina_nombre, style_cell), Paragraph(autor, style_cell), img_obj, img_obj_d])

            # Colección de fotos: una fila debajo del trabajo, a todo el
            # ancho, con las fotos en miniatura (6 por línea).
            # Lista de comprobación: otra fila a todo el ancho, con los
            # puntos «mal» en rojo.
            lista = listas.get(fila_pdf[5]) if len(fila_pdf) > 5 else None
            if lista:
                lineas_chk = []
                for it in lista["items"]:
                    linea = escape(linea_export(it))
                    if it.get("estado") == "mal":
                        linea = f'<font color="#c0392b"><b>{linea}</b></font>'
                    lineas_chk.append("• " + linea)
                filas_coleccion.append(len(data_tabla))
                data_tabla.append([Paragraph(f"<b>{escape(_tt('lbl_checklist', 'Lista de comprobación'))}: {escape(lista['plantilla'])}</b><br/>"
                                             + "<br/>".join(lineas_chk), style_cell), "", "", "", "", ""])

            # Repuestos usados: otra fila a todo el ancho, con su coste
            mats = usados.get(fila_pdf[5]) if len(fila_pdf) > 5 else None
            tiempo = tiempos.get(fila_pdf[5]) if len(fila_pdf) > 5 else None
            if mats or tiempo:
                partes = []
                if tiempo:
                    partes.append(f"<b>{escape(_tt('lbl_tiempo_trabajado', '⏱️ Tiempo trabajado').replace('⏱️', '').strip())}:</b> "
                                  + escape(texto_tiempo_export(tiempo, moneda, admin)))
                if mats:
                    partes.append(f"<b>{escape(_tt('lbl_repuestos_usados', '🔩 Materiales usados').replace('🔩', '').strip())}</b><br/>"
                                  + escape(texto_repuestos_export(mats, moneda, admin)).replace("\n", "<br/>"))
                filas_coleccion.append(len(data_tabla))
                data_tabla.append([Paragraph("<br/>".join(partes), style_cell), "", "", "", "", ""])

            miniaturas = [m for m in (_miniatura_pdf(carpeta_fotos, n) for n in fotos_galeria(desc)) if m]
            if miniaturas:
                lineas = [miniaturas[i:i + 6] for i in range(0, len(miniaturas), 6)]
                lineas[-1] += [""] * (6 - len(lineas[-1]))
                rejilla = Table(lineas, colWidths=[2.75 * cm] * 6)
                rejilla.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                             ('LEFTPADDING', (0, 0), (-1, -1), 1), ('RIGHTPADDING', (0, 0), (-1, -1), 1)]))
                filas_coleccion.append(len(data_tabla))
                data_tabla.append([[Paragraph(f"<b>{_tt('lbl_coleccion_fotos', 'Colección de fotos')}</b> ({len(miniaturas)})", style_cell), rejilla], "", "", "", "", ""])
            # Los vídeos no caben en un PDF: se nombran, para que se sepa que existen.
            videos = [n for n in fotos_galeria(desc) if es_video(n)]
            if videos:
                filas_coleccion.append(len(data_tabla))
                data_tabla.append([Paragraph(f"<b>{escape(_tt('lbl_videos_coleccion', 'Vídeos de la colección'))}</b> ({len(videos)}): "
                                             + escape(", ".join(videos)), style_cell), "", "", "", "", ""])

        ancho_foto = 3.0 * cm
        tabla_pdf = Table(data_tabla, colWidths=[2.0*cm, 4.5*cm, 2.4*cm, 2.6*cm, ancho_foto, ancho_foto])
        tabla_pdf.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ] + [estilo for fila in filas_coleccion for estilo in (
            ('SPAN', (0, fila), (-1, fila)), ('BACKGROUND', (0, fila), (-1, fila), colors.HexColor("#f7f3e6")))]))

        elements.append(tabla_pdf)

        graficos = trabajo.get("graficos")
        if graficos:
            elements.append(PageBreak())
            elements.append(Paragraph(_tt("titulo_estadisticas_pdf", "Estadísticas del periodo"), styles["Title"]))
            elements.append(Spacer(1, 6))

            ind = graficos["indicadores"]
            if ind["num_averias"] == 0 or ind["mtbf_dias"] is None:
                texto_ind = (
                    f"<b>{_tt('lbl_indicadores_fiabilidad', 'Indicadores de fiabilidad')}</b><br/>"
                    f"{_tt('lbl_num_averias', 'Averías registradas')}: {ind['num_averias']}<br/>"
                    f"<i>{_tt('msg_sin_datos_fiabilidad', 'Aún no hay averías suficientes para calcular indicadores.')}</i>"
                )
            else:
                mtbf_txt = _tt("fmt_dias", "{n:.1f} días").format(n=ind["mtbf_dias"])
                partes_ind = [
                    f"<b>{_tt('lbl_indicadores_fiabilidad', 'Indicadores de fiabilidad')}</b>",
                    f"{_tt('lbl_num_averias', 'Averías registradas')}: {ind['num_averias']}",
                    f"{_tt('lbl_mtbf', 'MTBF (tiempo medio entre averías)')}: {mtbf_txt}",
                ]
                if ind["mttr_horas"] is not None:
                    mttr_txt = _tt("fmt_horas", "{n:.1f} horas").format(n=ind["mttr_horas"])
                    partes_ind.append(f"{_tt('lbl_mttr', 'MTTR (tiempo medio de reparación)')}: {mttr_txt}")
                texto_ind = "<br/>".join(partes_ind)
            elements.append(Paragraph(texto_ind, styles["Normal"]))
            elements.append(Spacer(1, 14))

            ancho_grafico = 17 * cm
            alto_grafico = ancho_grafico * 260 / 760
            elements.append(Paragraph(_tt("titulo_ranking_averias_pdf", "Máquinas con más averías"), styles["Heading2"]))
            elements.append(PDFImage(graficos["png_ranking"], width=ancho_grafico, height=alto_grafico))
            elements.append(Spacer(1, 14))

            elements.append(Paragraph(_tt("titulo_averias_mes_pdf", "Averías por mes"), styles["Heading2"]))
            elements.append(PDFImage(graficos["png_mensual"], width=ancho_grafico, height=alto_grafico))
            elements.append(Spacer(1, 14))

            elements.append(Paragraph(_tt("titulo_distribucion_pdf", "Distribución de trabajos por tipo"), styles["Heading2"]))
            elements.append(PDFImage(graficos["png_pie"], width=ancho_grafico, height=alto_grafico))

        doc.build(elements)
