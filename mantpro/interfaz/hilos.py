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

"""Tareas en segundo plano: actualizaciones, PDF, copias y restauración."""

import requests
import os
import shutil
import re
import zipfile
from datetime import datetime
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
from ..nucleo.fotos import _RE_GALERIA
from ..nucleo.rutas import DATA_DIR
from ..version import APP_VERSION, REPO_NAME, REPO_OWNER

# ==========================================
# 1. UTILIDADES Y SERVIDORES
# ==========================================
class ChequeadorActualizaciones(QThread):
    resultado = pyqtSignal(bool, str, str, str)

    def comparar_versiones(self, v1, v2):
        """True si v1 es más nueva que v2. Admite el prefijo "v" y sufijos de
        versión de pruebas ("3.10.2-dev1", "3.10.2-rc.1"): se compara la parte
        numérica y, si es igual, la versión final va por delante de sus
        versiones de pruebas. Antes, "3.10.2-dev1" se leía como 3.10.21."""
        def parse(v):
            numeros, _, sufijo = v.strip().lstrip("vV").partition("-")
            partes = [int(x) if x.isdigit() else 0 for x in numeros.split(".")]
            return partes + [0] * (3 - len(partes)), bool(sufijo)
        (p1, pruebas1), (p2, pruebas2) = parse(v1), parse(v2)
        if p1 != p2:
            return p1 > p2
        return pruebas2 and not pruebas1

    def run(self):
        try:
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
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

                    m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
                    if m:
                        nombre_foto = m.group(1).split("]")[0].strip()
                        ruta_foto = os.path.join(self.carpeta_fotos, nombre_foto)
                        if os.path.exists(ruta_foto):
                            try:
                                img = PDFImage(ruta_foto)
                                img.drawHeight = 2.5 * cm
                                img.drawWidth = 3.0 * cm
                                img.keepAspectRatio = True
                                img_obj = img
                            except: img_obj = "Error Img"

                    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc)
                    if m_d:
                        nombre_foto_d = m_d.group(1).split("]")[0].strip()
                        ruta_foto_d = os.path.join(self.carpeta_fotos, nombre_foto_d)
                        if os.path.exists(ruta_foto_d):
                            try:
                                img_d = PDFImage(ruta_foto_d)
                                img_d.drawHeight = 2.5 * cm
                                img_d.drawWidth = 3.0 * cm
                                img_d.keepAspectRatio = True
                                img_obj_d = img_d
                            except: img_obj_d = "Error Img"

                    desc_visual = re.sub(r"\[FOTO:.*?\]", "", desc_visual)
                    desc_visual = re.sub(r"\[FOTO_DESPUES:.*?\]", "", desc_visual)
                    desc_visual = _RE_GALERIA.sub("", desc_visual)
                    desc_visual = re.sub(r"\[REF:.*?\]", "", desc_visual).strip()

                    p_desc = Paragraph(desc_visual.replace("\n", "<br/>"), style_cell)
                    data_tabla.append([Paragraph(fecha_formateada, style_cell), p_desc, Paragraph(maquina_nombre, style_cell), Paragraph(autor, style_cell), img_obj, img_obj_d])

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
                ]))

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
    """Backup automático al cerrar la aplicación.

    Las fotos son inmutables una vez guardadas (solo se añaden o se borran las
    huérfanas), así que en vez de reempaquetar todo el histórico cada vez que
    se cierra la app, se mantienen unos ZIP incrementales por año (nombrados
    "fotos_backup_<año>.zip"): cada cierre solo añade a su ZIP del año las
    fotos que todavía no estén dentro, sin tocar ni recomprimir las que ya
    estaban. Así el ZIP de años anteriores no vuelve a abrirse salvo que
    aparezca una foto nueva de ese año, y el peso total queda repartido y
    comprimido en vez de duplicado sin comprimir en una carpeta espejo.

    La base de datos sí cambia en cada sesión, pero pesa poco, así que esa
    parte se sigue empaquetando entera en un ZIP rotativo (sin comprimir,
    para no gastar tiempo de CPU en algo que ya es rápido de por sí).
    """
    progreso = pyqtSignal(int, int)  # (archivos copiados, total a copiar)
    resultado = pyqtSignal(bool, str)

    _RE_TIMESTAMP = re.compile(r"(\d{8})_\d{6}")

    def __init__(self, carpeta_fotos, carpeta_backups_auto, db_name, db_almacen_name):
        super().__init__()
        self.carpeta_fotos = carpeta_fotos
        self.carpeta_backups_auto = carpeta_backups_auto
        self.db_name = db_name
        self.db_almacen_name = db_almacen_name

    def _anio_de_foto(self, nombre, ruta):
        """El nombre de fichero lleva casi siempre una marca de tiempo
        (pc_drag_20260115_..., app_20260115_..., maquina_20260115_...); si no
        la lleva (fotos muy antiguas), se recurre a la fecha de modificación."""
        m = self._RE_TIMESTAMP.search(nombre)
        if m:
            return m.group(1)[:4]
        try:
            return str(datetime.fromtimestamp(os.path.getmtime(ruta)).year)
        except Exception:
            return str(datetime.now().year)

    def run(self):
        try:
            os.makedirs(self.carpeta_backups_auto, exist_ok=True)
            origen_archivos = os.listdir(self.carpeta_fotos) if os.path.exists(self.carpeta_fotos) else []

            ya_respaldadas = set()
            zips_existentes = {}
            for f in os.listdir(self.carpeta_backups_auto):
                if f.startswith("fotos_backup_") and f.endswith(".zip"):
                    anio = f[len("fotos_backup_"):-len(".zip")]
                    zips_existentes[anio] = os.path.join(self.carpeta_backups_auto, f)
                    try:
                        with zipfile.ZipFile(zips_existentes[anio], 'r') as zf:
                            ya_respaldadas.update(zf.namelist())
                    except Exception:
                        pass

            pendientes_por_anio = {}
            for nombre in origen_archivos:
                if nombre in ya_respaldadas:
                    continue
                ruta_origen = os.path.join(self.carpeta_fotos, nombre)
                if not os.path.isfile(ruta_origen):
                    continue
                anio = self._anio_de_foto(nombre, ruta_origen)
                pendientes_por_anio.setdefault(anio, []).append(nombre)

            total = sum(len(v) for v in pendientes_por_anio.values())
            copiadas = 0
            self.progreso.emit(0, total)
            for anio, nombres in pendientes_por_anio.items():
                ruta_zip = zips_existentes.get(anio, os.path.join(self.carpeta_backups_auto, f"fotos_backup_{anio}.zip"))
                with zipfile.ZipFile(ruta_zip, 'a', zipfile.ZIP_DEFLATED) as zipf:
                    existentes_zip = set(zipf.namelist())
                    for nombre in nombres:
                        if nombre not in existentes_zip:
                            zipf.write(os.path.join(self.carpeta_fotos, nombre), arcname=nombre)
                        copiadas += 1
                        self.progreso.emit(copiadas, total)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_zip = f"auto_backup_db_{timestamp}.zip"
            ruta_zip = os.path.join(self.carpeta_backups_auto, nombre_zip)
            with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_STORED) as zipf:
                if os.path.exists(self.db_name):
                    zipf.write(self.db_name, arcname=os.path.basename(self.db_name))
                if os.path.exists(self.db_almacen_name):
                    zipf.write(self.db_almacen_name, arcname=os.path.basename(self.db_almacen_name))

            backups = []
            for f in os.listdir(self.carpeta_backups_auto):
                ruta_completa = os.path.join(self.carpeta_backups_auto, f)
                if os.path.isfile(ruta_completa) and f.startswith("auto_backup_db_") and f.endswith(".zip"):
                    backups.append(ruta_completa)
            backups.sort(key=os.path.getmtime)
            while len(backups) > 3:
                os.remove(backups.pop(0))

            self.resultado.emit(True, "Auto-backup completado.")
        except Exception as ex:
            self.resultado.emit(False, str(ex))


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
            with zipfile.ZipFile(self.ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(self.db_name):
                    zipf.write(self.db_name, arcname=os.path.basename(self.db_name))
                hechos += 1; self.progreso.emit(hechos, total)
                if os.path.exists(self.db_almacen_name):
                    zipf.write(self.db_almacen_name, arcname=os.path.basename(self.db_almacen_name))
                hechos += 1; self.progreso.emit(hechos, total)
                for ruta_archivo in archivos_fotos:
                    ruta_en_zip = os.path.relpath(ruta_archivo, os.path.dirname(self.carpeta_fotos))
                    zipf.write(ruta_archivo, arcname=ruta_en_zip)
                    hechos += 1; self.progreso.emit(hechos, total)

            self.resultado.emit(True, "", self.ruta_zip)
        except Exception as ex:
            self.resultado.emit(False, str(ex), self.ruta_zip)


class RestoreManualThread(QThread):
    """Restauración manual de un backup (completo o automático). Extrae la BD
    y las fotos necesarias en un hilo aparte para poder mostrar una barra de
    progreso con foco mientras dura la operación."""
    progreso = pyqtSignal(int, int)
    resultado = pyqtSignal(bool, str)

    def __init__(self, archivo_zip, restore_path, carpeta_fotos, es_auto_backup, obtener_fotos_necesarias=None):
        super().__init__()
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
                for i, nombre in enumerate(entradas, start=1):
                    zipf.extract(nombre, path=self.restore_path)
                    self.progreso.emit(i, total)

            if self.es_auto_backup and self.obtener_fotos_necesarias:
                fotos_necesarias = self.obtener_fotos_necesarias()
                carpeta_backups_auto = os.path.dirname(self.archivo_zip)
                destino_fotos = os.path.join(self.restore_path, os.path.basename(self.carpeta_fotos))
                os.makedirs(destino_fotos, exist_ok=True)
                zips_fotos = [f for f in os.listdir(carpeta_backups_auto)
                              if f.startswith("fotos_backup_") and f.endswith(".zip")]
                total_f = len(zips_fotos)
                self.progreso.emit(0, total_f)
                for i, f in enumerate(zips_fotos, start=1):
                    try:
                        with zipfile.ZipFile(os.path.join(carpeta_backups_auto, f), 'r') as zf:
                            for nombre in zf.namelist():
                                if nombre in fotos_necesarias:
                                    zf.extract(nombre, path=destino_fotos)
                    except Exception:
                        pass
                    self.progreso.emit(i, total_f)

            self.resultado.emit(True, "")
        except Exception as ex:
            self.resultado.emit(False, str(ex))
