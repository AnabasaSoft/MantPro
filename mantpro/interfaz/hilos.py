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

"""Tareas en segundo plano: actualizaciones, PDF, copias y restauración."""

import requests
import os
import shutil
import re
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
                                Image as PDFImage, PageBreak)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from PyQt6.QtCore import pyqtSignal, QThread

from .. import idiomas
from ..idiomas import t
from .comun import tt
from ..nucleo import usuarios
from ..nucleo import copias
from ..nucleo.fotos import _RE_GALERIA, fotos_galeria
from ..nucleo.seguridad import es_video
from ..nucleo.rutas import DATA_DIR
from ..nucleo.seguridad import anadir_bd_a_zip
from ..nucleo import cifrado_copias, checklists, consumos, mano_obra
from xml.sax.saxutils import escape
from .dialogos.checklists import linea_export, texto_repuestos_export, texto_tiempo_export
from ..version import APP_VERSION, REPO_NAME, REPO_OWNER

# ==========================================
# 1. UTILIDADES Y SERVIDORES
# ==========================================
class ChequeadorActualizaciones(QThread):
    resultado = pyqtSignal(bool, str, str, str)

    # Orden de las etiquetas de versión de pruebas; cualquier otra cuenta como "dev".
    _ORDEN_PRUEBAS = {"dev": 0, "alpha": 1, "a": 1, "beta": 2, "b": 2, "rc": 3}

    @classmethod
    def clave_version(cls, v):
        """Clave ordenable de una versión: parte numérica, luego si es final
        (va por delante de sus versiones de pruebas) y, entre versiones de
        pruebas del mismo número, su etiqueta y su número: 3.10.2-dev <
        3.10.2-dev.1 < 3.10.2-dev.3 < 3.10.2-beta < 3.10.2-rc.1 < 3.10.2."""
        numeros, _, sufijo = v.strip().lstrip("vV").partition("-")
        partes = [int(x) if x.isdigit() else 0 for x in numeros.split(".")][:3]
        partes += [0] * (3 - len(partes))
        if not sufijo:
            return partes + [1, 0, 0]
        etiqueta = re.sub(r"[^a-z]", "", sufijo.lower())
        numero = re.findall(r"\d+", sufijo)
        return partes + [0, cls._ORDEN_PRUEBAS.get(etiqueta, 0), int(numero[0]) if numero else 0]

    @classmethod
    def es_version_pruebas(cls, v):
        return "-" in v.strip()

    def comparar_versiones(self, v1, v2):
        """True si v1 es más nueva que v2 (admite el prefijo "v")."""
        return self.clave_version(v1) > self.clave_version(v2)

    def run(self):
        """Busca la release más nueva en GitHub. A quien tiene una versión
        estable solo se le ofrecen estables; a quien ya tiene instalada una
        versión de pruebas (-dev, -beta, -rc…), también las de pruebas.
        («releases/latest» de GitHub nunca devuelve pre-releases, por eso se
        pide la lista.)"""
        try:
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases?per_page=30"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                acepta_pruebas = self.es_version_pruebas(APP_VERSION)
                candidatas = [r for r in res.json()
                              if r.get("tag_name") and not r.get("draft")
                              and (acepta_pruebas or not r.get("prerelease"))]
                data = max(candidatas, key=lambda r: self.clave_version(r["tag_name"]), default={})
                tag = data.get("tag_name", "")
                html_url = data.get("html_url", "")
                body = data.get("body", "")
                if tag and self.comparar_versiones(tag, APP_VERSION):
                    self.resultado.emit(True, tag, html_url, body)
                else:
                    self.resultado.emit(False, tag, "", "")
            else:
                self.resultado.emit(False, "error", "", "")
        except:
            self.resultado.emit(False, "error", "", "")


class GeneradorPDFThread(QThread):
    resultado = pyqtSignal(bool, str)

    def _miniatura_pdf(self, nombre, ancho_max=2.6 * cm, alto_max=2.2 * cm):
        """Foto de la colección reducida (máx. 600 px, JPEG) para el PDF, así
        un trabajo con muchas fotos no dispara el tamaño del fichero. None si
        no existe o no se puede leer."""
        ruta = os.path.join(self.carpeta_fotos, nombre)
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

    def __init__(self, lista_trabajos, carpeta_fotos, mapa_maquinas=None):
        super().__init__()
        # Recibe una lista de diccionarios: [{"archivo": ruta, "titulo": tit,
        # "datos": [...], "rango": (ini, fin) o None, "graficos": {...} o None}].
        # "graficos" (rutas de los PNG ya renderizados en el hilo principal,
        # porque QWidget.grab() no se puede usar fuera de él, más los
        # indicadores) es específico de cada trabajo, ya que cada uno puede
        # cubrir un periodo distinto (rango de fechas o mes).
        self.lista_trabajos = lista_trabajos
        self.carpeta_fotos = carpeta_fotos
        self.mapa_maquinas = mapa_maquinas or {}

    def run(self):
        try:
            styles = getSampleStyleSheet()
            ruta_logo = os.path.join(DATA_DIR, "Logo.jpg")

            for trabajo in self.lista_trabajos:
                doc = SimpleDocTemplate(trabajo["archivo"], pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
                elements = []

                if os.path.exists(ruta_logo):
                    try:
                        logo = PDFImage(ruta_logo, width=4*cm, height=2*cm)
                        logo.hAlign = 'LEFT'
                        logo.keepAspectRatio = True
                        elements.append(logo)
                        elements.append(Spacer(1, 10))
                    except: pass

                elements.append(Paragraph(trabajo["titulo"], styles['Title']))
                elements.append(Spacer(1, 12))

                style_cell = styles["BodyText"]; style_cell.fontSize = 9
                style_header = ParagraphStyle("CabeceraTabla", parent=style_cell, textColor=colors.whitesmoke, fontName="Helvetica-Bold", fontSize=9)

                def cab(texto):
                    return Paragraph(texto, style_header)

                filas_coleccion = []
                listas = checklists.resultados_de([f[5] for f in trabajo["datos"] if len(f) > 5])
                usados = consumos.materiales_de_trabajos([f[5] for f in trabajo["datos"] if len(f) > 5])
                tiempos = mano_obra.tiempos_de([f[5] for f in trabajo["datos"] if len(f) > 5])
                moneda = consumos.moneda()
                data_tabla = [[cab(t("hdr_fecha")), cab(t("hdr_descripcion")), cab(tt("hdr_maquina", "Máquina")),
                               cab(tt("hdr_realizado_por", "Realizado por")),
                               cab(t("hdr_foto_antes")), cab(t("hdr_foto_despues"))]]

                for fila_pdf in trabajo["datos"]:
                    fecha, desc, tags = fila_pdf[0], fila_pdf[1], fila_pdf[2]
                    autor = fila_pdf[3] if len(fila_pdf) > 3 and fila_pdf[3] else usuarios.ETIQUETA_HISTORICO
                    maquina_nombre = self.mapa_maquinas.get(fila_pdf[4], "-") if len(fila_pdf) > 4 and fila_pdf[4] else "-"
                    fecha_formateada = idiomas.formato_fecha_localizada(fecha)

                    desc_visual = desc
                    img_obj = ""
                    img_obj_d = ""

                    # Fotos de antes y después: encajadas en su celda (3 cm de
                    # ancho menos el margen) sin deformarlas. Antes se fijaba
                    # el tamaño a mano y las apaisadas se salían de la celda.
                    m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
                    if m:
                        img_obj = self._miniatura_pdf(m.group(1).split("]")[0].strip(), 2.75 * cm, 2.5 * cm) or ""
                    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc)
                    if m_d:
                        img_obj_d = self._miniatura_pdf(m_d.group(1).split("]")[0].strip(), 2.75 * cm, 2.5 * cm) or ""

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
                        data_tabla.append([Paragraph(f"<b>{escape(tt('lbl_checklist', 'Lista de comprobación'))}: {escape(lista['plantilla'])}</b><br/>"
                                                     + "<br/>".join(lineas_chk), style_cell), "", "", "", "", ""])

                    # Repuestos usados: otra fila a todo el ancho, con su coste
                    mats = usados.get(fila_pdf[5]) if len(fila_pdf) > 5 else None
                    tiempo = tiempos.get(fila_pdf[5]) if len(fila_pdf) > 5 else None
                    if mats or tiempo:
                        partes = []
                        if tiempo:
                            partes.append(f"<b>{escape(tt('lbl_tiempo_trabajado', '⏱️ Tiempo trabajado').replace('⏱️', '').strip())}:</b> "
                                          + escape(texto_tiempo_export(tiempo, moneda)))
                        if mats:
                            partes.append(f"<b>{escape(tt('lbl_repuestos_usados', '🔩 Materiales usados').replace('🔩', '').strip())}</b><br/>"
                                          + escape(texto_repuestos_export(mats, moneda)).replace("\n", "<br/>"))
                        filas_coleccion.append(len(data_tabla))
                        data_tabla.append([Paragraph("<br/>".join(partes), style_cell), "", "", "", "", ""])

                    miniaturas = [m for m in (self._miniatura_pdf(n) for n in fotos_galeria(desc)) if m]
                    if miniaturas:
                        lineas = [miniaturas[i:i + 6] for i in range(0, len(miniaturas), 6)]
                        lineas[-1] += [""] * (6 - len(lineas[-1]))
                        rejilla = Table(lineas, colWidths=[2.75 * cm] * 6)
                        rejilla.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                                     ('LEFTPADDING', (0, 0), (-1, -1), 1), ('RIGHTPADDING', (0, 0), (-1, -1), 1)]))
                        filas_coleccion.append(len(data_tabla))
                        data_tabla.append([[Paragraph(f"<b>{tt('lbl_coleccion_fotos', 'Colección de fotos')}</b> ({len(miniaturas)})", style_cell), rejilla], "", "", "", "", ""])
                    # Los vídeos no caben en un PDF: se nombran, para que se sepa que existen.
                    videos = [n for n in fotos_galeria(desc) if es_video(n)]
                    if videos:
                        filas_coleccion.append(len(data_tabla))
                        data_tabla.append([Paragraph(f"<b>{escape(tt('lbl_videos_coleccion', 'Vídeos de la colección'))}</b> ({len(videos)}): "
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
                    elements.append(Paragraph(tt("titulo_estadisticas_pdf", "Estadísticas del periodo"), styles["Title"]))
                    elements.append(Spacer(1, 6))

                    ind = graficos["indicadores"]
                    if ind["num_averias"] == 0 or ind["mtbf_dias"] is None:
                        texto_ind = (
                            f"<b>{tt('lbl_indicadores_fiabilidad', 'Indicadores de fiabilidad')}</b><br/>"
                            f"{tt('lbl_num_averias', 'Averías registradas')}: {ind['num_averias']}<br/>"
                            f"<i>{tt('msg_sin_datos_fiabilidad', 'Aún no hay averías suficientes para calcular indicadores.')}</i>"
                        )
                    else:
                        mtbf_txt = tt("fmt_dias", "{n:.1f} días").format(n=ind["mtbf_dias"])
                        partes_ind = [
                            f"<b>{tt('lbl_indicadores_fiabilidad', 'Indicadores de fiabilidad')}</b>",
                            f"{tt('lbl_num_averias', 'Averías registradas')}: {ind['num_averias']}",
                            f"{tt('lbl_mtbf', 'MTBF (tiempo medio entre averías)')}: {mtbf_txt}",
                        ]
                        if ind["mttr_horas"] is not None:
                            mttr_txt = tt("fmt_horas", "{n:.1f} horas").format(n=ind["mttr_horas"])
                            partes_ind.append(f"{tt('lbl_mttr', 'MTTR (tiempo medio de reparación)')}: {mttr_txt}")
                        texto_ind = "<br/>".join(partes_ind)
                    elements.append(Paragraph(texto_ind, styles["Normal"]))
                    elements.append(Spacer(1, 14))

                    ancho_grafico = 17 * cm
                    alto_grafico = ancho_grafico * 260 / 760
                    elements.append(Paragraph(tt("titulo_ranking_averias_pdf", "Máquinas con más averías"), styles["Heading2"]))
                    elements.append(PDFImage(graficos["png_ranking"], width=ancho_grafico, height=alto_grafico))
                    elements.append(Spacer(1, 14))

                    elements.append(Paragraph(tt("titulo_averias_mes_pdf", "Averías por mes"), styles["Heading2"]))
                    elements.append(PDFImage(graficos["png_mensual"], width=ancho_grafico, height=alto_grafico))
                    elements.append(Spacer(1, 14))

                    elements.append(Paragraph(tt("titulo_distribucion_pdf", "Distribución de trabajos por tipo"), styles["Heading2"]))
                    elements.append(PDFImage(graficos["png_pie"], width=ancho_grafico, height=alto_grafico))

                doc.build(elements)

            self.resultado.emit(True, "PDF(s) generado(s) correctamente.")
        except Exception as e:
            self.resultado.emit(False, str(e))
        finally:
            for trabajo in self.lista_trabajos:
                graficos = trabajo.get("graficos")
                if graficos and graficos.get("tmp_dir"):
                    shutil.rmtree(graficos["tmp_dir"], ignore_errors=True)


class BackupThread(QThread):
    """Copia de seguridad automática en segundo plano (al cerrar, cada cierto
    tiempo, tras recibir datos de un móvil, al arrancar o a mano desde
    Archivo > Copias automáticas). Todo lo hace nucleo/copias.py; aquí solo
    se lanza en un hilo y se avisa del progreso y del resultado.

    Con [accion] = "probar" no hace copia: prueba la última (ver
    copias.probar_ultima)."""
    progreso = pyqtSignal(int, int)  # (fotos copiadas, total a copiar)
    resultado = pyqtSignal(bool, str)
    terminado = pyqtSignal(dict)     # resultado completo de copias.hacer_copia

    def __init__(self, carpeta_fotos, carpeta_backups_auto, db_name, db_almacen_name,
                 motivo="cierre", solo_si_hay_cambios=False, config=None, accion="copia"):
        super().__init__()
        self.carpeta_fotos = carpeta_fotos
        self.carpeta_backups_auto = carpeta_backups_auto
        self.rutas_bd = [db_name, db_almacen_name]
        self.motivo = motivo
        self.solo_si_hay_cambios = solo_si_hay_cambios
        self.config = config
        self.accion = accion

    def run(self):
        try:
            if self.accion == "probar":
                prueba = copias.probar_ultima(self.carpeta_backups_auto, self.rutas_bd, self.carpeta_fotos, self.config)
                r = {"hecha": False, "ok": prueba["ok"], "error": "", "integridad": [],
                     "destino_error": "", "prueba": prueba}
            else:
                r = copias.hacer_copia(self.carpeta_fotos, self.carpeta_backups_auto, self.rutas_bd,
                                       self.motivo, self.progreso.emit, self.solo_si_hay_cambios, self.config)
        except Exception as ex:   # no debería pasar: hacer_copia ya recoge los errores
            r = {"hecha": True, "ok": False, "error": str(ex), "integridad": [], "destino_error": "", "prueba": None}
        if r["integridad"]:
            print(f"Aviso: bases de datos que no pasan la comprobación de integridad: {r['integridad']}")
        self.terminado.emit(r)
        self.resultado.emit(r["ok"], r["error"] or r["destino_error"])


class BackupManualThread(QThread):
    """Backup manual (Archivo > Backup): un único ZIP con las dos bases de
    datos y todas las fotos, tal y como se ha hecho siempre. Va en un hilo
    aparte solo para poder mostrar una barra de progreso con foco mientras
    se genera, sin congelar la ventana."""
    progreso = pyqtSignal(int, int)
    resultado = pyqtSignal(bool, str, str)  # (éxito, mensaje/error, ruta_zip)

    def __init__(self, ruta_zip, carpeta_fotos, db_name, db_almacen_name):
        super().__init__()
        self.ruta_zip = ruta_zip
        self.carpeta_fotos = carpeta_fotos
        self.db_name = db_name
        self.db_almacen_name = db_almacen_name

    def run(self):
        try:
            archivos_fotos = []
            if os.path.exists(self.carpeta_fotos):
                for root, dirs, files in os.walk(self.carpeta_fotos):
                    for file in files:
                        archivos_fotos.append(os.path.join(root, file))

            total = len(archivos_fotos) + 2
            hechos = 0
            self.progreso.emit(0, total)
            # ZIP temporal que solo se renombra al final (ver BackupThread),
            # con una copia consistente de cada base de datos.
            temporal = self.ruta_zip + ".tmp"
            dañadas = []
            clave = cifrado_copias.clave_actual()
            with zipfile.ZipFile(temporal, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
                for ruta_bd in (self.db_name, self.db_almacen_name):
                    integridad = anadir_bd_a_zip(zipf, ruta_bd, clave)
                    if integridad not in (None, "ok"):
                        dañadas.append(f"{os.path.basename(ruta_bd)}: {integridad}")
                    hechos += 1; self.progreso.emit(hechos, total)
                for ruta_archivo in archivos_fotos:
                    ruta_en_zip = os.path.relpath(ruta_archivo, os.path.dirname(self.carpeta_fotos))
                    cifrado_copias.escribir_entrada(zipf, ruta_archivo, ruta_en_zip.replace(os.sep, "/"), clave)
                    hechos += 1; self.progreso.emit(hechos, total)
            os.replace(temporal, self.ruta_zip)

            # La copia se guarda igualmente, pero se avisa si alguna base de
            # datos no ha pasado la comprobación de integridad.
            self.resultado.emit(True, "\n".join(dañadas), self.ruta_zip)
        except Exception as ex:
            self.resultado.emit(False, str(ex), self.ruta_zip)


class RestoreManualThread(QThread):
    """Restauración manual de un backup (completo o automático). Extrae la BD
    y las fotos necesarias en un hilo aparte para poder mostrar una barra de
    progreso con foco mientras dura la operación."""
    progreso = pyqtSignal(int, int)
    resultado = pyqtSignal(bool, str)

    def __init__(self, archivo_zip, restore_path, carpeta_fotos, es_auto_backup, obtener_fotos_necesarias=None, claves=None):
        super().__init__()
        # Claves para descifrar ({sal: Clave}), ya comprobadas antes de empezar
        self.claves = claves or {}
        self.archivo_zip = archivo_zip
        self.restore_path = restore_path
        self.carpeta_fotos = carpeta_fotos
        # Los auto-backup solo traen la BD en el zip; sus fotos hay que sacarlas
        # de los "fotos_backup_<año>.zip" según lo que diga la BD ya restaurada
        self.es_auto_backup = es_auto_backup
        self.obtener_fotos_necesarias = obtener_fotos_necesarias

    def run(self):
        try:
            with zipfile.ZipFile(self.archivo_zip, 'r') as zipf:
                entradas = zipf.namelist()
                total = len(entradas)
                self.progreso.emit(0, total)
                # Primero se descifra y comprueba todo lo que es base de datos
                # antes de tocar nada: si la copia está dañada, no se restaura.
                bases = [n for n in entradas
                         if "/" not in n and cifrado_copias.nombre_real(n).endswith(".db")]
                hechos = 0
                for nombre in bases:
                    cifrado_copias.restaurar_bd(
                        zipf, nombre, os.path.join(self.restore_path, cifrado_copias.nombre_real(nombre)), self.claves)
                    hechos += 1; self.progreso.emit(hechos, total)
                for nombre in entradas:
                    if nombre in bases:
                        continue
                    cifrado_copias.extraer_entrada(zipf, nombre, self.restore_path, self.claves)
                    hechos += 1; self.progreso.emit(hechos, total)

            if self.es_auto_backup and self.obtener_fotos_necesarias:
                fotos_necesarias = self.obtener_fotos_necesarias()
                carpeta_backups_auto = os.path.dirname(self.archivo_zip)
                destino_fotos = os.path.join(self.restore_path, os.path.basename(self.carpeta_fotos))
                os.makedirs(destino_fotos, exist_ok=True)
                zips_fotos = [f for f in os.listdir(carpeta_backups_auto)
                              if f.startswith("fotos_backup_") and f.endswith(".zip")]
                total_f = len(zips_fotos)
                self.progreso.emit(0, total_f)
                fallidas = []
                for i, f in enumerate(zips_fotos, start=1):
                    try:
                        with zipfile.ZipFile(os.path.join(carpeta_backups_auto, f), 'r') as zf:
                            for nombre in zf.namelist():
                                if cifrado_copias.nombre_real(nombre) in fotos_necesarias:
                                    try:
                                        cifrado_copias.extraer_entrada(zf, nombre, destino_fotos, self.claves)
                                    except (cifrado_copias.ErrorCifrado, cifrado_copias.ContrasenaNecesaria):
                                        fallidas.append(cifrado_copias.nombre_real(nombre))
                    except Exception:
                        fallidas.append(f)
                    self.progreso.emit(i, total_f)
                if fallidas:
                    # La base de datos ya está restaurada: se avisa de las fotos que faltan
                    self.resultado.emit(True, "\n".join(fallidas[:20]) + ("\n…" if len(fallidas) > 20 else ""))
                    return

            self.resultado.emit(True, "")
        except cifrado_copias.ContrasenaNecesaria:
            self.resultado.emit(False, tt("msg_falta_contrasena_copia", "La copia está cifrada y la contraseña no es la suya."))
        except cifrado_copias.ErrorCifrado as ex:
            self.resultado.emit(False, tt("msg_copia_danada", "La copia está dañada o se ha modificado ({detalle}).").format(detalle=ex))
        except Exception as ex:
            self.resultado.emit(False, str(ex))


class RecifrarCopiasThread(QThread):
    """Vuelve a guardar las copias que ya hay en las carpetas de copias con la
    clave nueva (o sin cifrar, si se quita la contraseña)."""
    progreso = pyqtSignal(int, int)
    resultado = pyqtSignal(bool, str)   # (éxito, n.º de copias cambiadas / error)

    def __init__(self, carpetas, conocidas, nueva):
        super().__init__()
        self.carpetas = carpetas
        self.conocidas = conocidas
        self.nueva = nueva

    def run(self):
        try:
            zips = []
            for carpeta in self.carpetas:
                for ruta in cifrado_copias.zips_de_copias(carpeta):
                    if ruta not in zips:
                        zips.append(ruta)
            total = cifrado_copias.entradas_de(zips)
            hechos = [0]
            self.progreso.emit(0, total)

            def _paso():
                hechos[0] += 1
                self.progreso.emit(hechos[0], total)

            cambiadas = 0
            for ruta in zips:
                if cifrado_copias.recifrar_zip(ruta, self.conocidas, self.nueva, _paso):
                    cambiadas += 1
            self.resultado.emit(True, str(cambiadas))
        except Exception as ex:
            self.resultado.emit(False, str(ex))
