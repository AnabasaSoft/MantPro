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

import sys
import sqlite3
import requests
import json
import os
import shutil
import tempfile
import socket
import threading
import re
import csv
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, g
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as PDFImage, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import zipfile
import qrcode
from io import BytesIO
import idiomas
from idiomas import t

# --- Sistema de usuarios (login, roles, atribución de trabajos) ---
import usuarios
from dialogos_usuarios import (DialogoLogin, DialogoGestionUsuarios,
                               DialogoCambioPassword, DialogoSesiones)

# --- Control de stock de almacén (BD propia, independiente de los trabajos) ---
import almacen

# --- Listado de maquinaria y su histórico de trabajos ---
import maquinas


def tt(clave, defecto):
    """t() con texto por defecto: si la clave aún no está en idiomas.py,
    devuelve el literal en castellano en vez del nombre de la clave."""
    valor = t(clave)
    return defecto if valor == clave else valor

# ==========================================
# IMPORTS CORREGIDOS (PyQt6)
# ==========================================
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QCalendarWidget, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QTabWidget, QDateEdit,
                             QListWidget, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog, QDialogButtonBox, QAbstractItemView,
                             QListWidgetItem, QStyleFactory, QComboBox, QGroupBox, QCheckBox,
                             QCompleter, QFileDialog, QScrollArea, QSizePolicy, QGridLayout,
                             QSpinBox, QDoubleSpinBox, QRadioButton, QProgressBar, QProgressDialog, QTreeView, QMenu, QSplashScreen,
                             QTreeWidget, QTreeWidgetItem, QSplitter, QInputDialog)

from PyQt6.QtCore import (QDate, Qt, pyqtSignal, QThread, QSettings, QDir,
                          QPropertyAnimation, QEasingCurve, QTimer,
                          QTranslator, QLibraryInfo, QRectF)

from PyQt6.QtGui import (QAction, QActionGroup, QIcon, QColor, QBrush, QTextCharFormat,
                         QPixmap, QImage, QTextCursor, QFileSystemModel, QPainter, QPen, QFont)

# Función auxiliar para conectar de forma SEGURA
def get_db_connection(db_path):
    conn = sqlite3.connect(db_path, timeout=20) # 20 segundos de espera antes de dar error
    conn.row_factory = sqlite3.Row
    # ACTIVAR MODO WAL: Esto es vital para evitar lo que te ha pasado
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

# --- FUNCIÓN PARA REPARAR LA BASE DE DATOS AUTOMÁTICAMENTE ---
def reparar_base_datos(db_path):
    print(f"Verificando estructura de BD en: {db_path}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. Intentar añadir columna 'raw_desc' si falta
    try:
        c.execute("ALTER TABLE tareas ADD COLUMN raw_desc TEXT")
        print("🔧 REPARACIÓN: Columna 'raw_desc' añadida con éxito.")
    except sqlite3.OperationalError:
        pass # La columna ya existe, no hacemos nada

    # 2. Intentar añadir columna 'foto' si falta (por seguridad)
    try:
        c.execute("ALTER TABLE tareas ADD COLUMN foto TEXT")
        print("🔧 REPARACIÓN: Columna 'foto' añadida con éxito.")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

# ==========================================
# GESTIÓN DE RUTAS (INTELIGENTE)
# ==========================================

def resource_path(relative_path):
    """ Para recursos ESTÁTICOS (solo lectura) empaquetados (icono.png) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def instalar_traductor_qt(app, codigo_idioma):
    """Traduce los textos propios de Qt (menú contextual de cortar/copiar/pegar,
    botones de QMessageBox, etc.) al idioma de la app. Sin esto, esos textos
    siempre salen en inglés aunque el resto de la interfaz esté en español.
    El euskara no tiene traducción oficial en Qt, así que se queda en inglés."""
    traductor = QTranslator(app)
    ruta_traducciones = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if traductor.load(f"qtbase_{codigo_idioma}", ruta_traducciones):
        app.installTranslator(traductor)
        app._traductor_qt = traductor  # evitar que el GC lo destruya

def obtener_ruta_datos():
    """
    Determina dónde leer/escribir datos.
    PRIORIDAD 1: Carpeta actual (Modo desarrollo/Portable). Si existe 'mantenimiento.db' aquí, se usa esta.
    PRIORIDAD 2: Carpeta de sistema (Modo Instalación/AUR). ~/.local/share/MantPro
    """
    cwd = os.path.abspath(".")
    db_local = os.path.join(cwd, "mantenimiento.db")

    # Si ya existe la BD en la carpeta actual, nos quedamos aquí (tu caso actual)
    if os.path.exists(db_local):
        return cwd

    # Si no, usamos la ruta estándar del sistema operativo
    nombre_app = "MantPro"
    if sys.platform == "win32":
        base_dir = os.getenv("APPDATA")
    else:
        # Linux estándar (XDG_DATA_HOME)
        base_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    ruta_sistema = os.path.join(base_dir, nombre_app)

    # Crear la carpeta de sistema si no existe (importante para la primera ejecución)
    if not os.path.exists(ruta_sistema):
        try:
            os.makedirs(ruta_sistema)
        except OSError as e:
            print(f"Error creando directorio de datos: {e}")
            # Fallback al directorio local si falla (ej. portable)
            return os.path.abspath(".")

    return ruta_sistema

# Variable global que decide dónde se guarda TODO
DATA_DIR = obtener_ruta_datos()
APP_VERSION = "3.9.4"
REPO_OWNER = "AnabasaSoft"
REPO_NAME = "MantPro"

# ==========================================
# DATOS GLOBALES: PROVINCIAS
# ==========================================
PROVINCIAS_ESPAÑA = {
    "A Coruña": {"iso": "ES-C", "parent": "ES-GA"},
    "Álava/Araba": {"iso": "ES-VI", "parent": "ES-PV"},
    "Albacete": {"iso": "ES-AB", "parent": "ES-CM"},
    "Alicante": {"iso": "ES-A", "parent": "ES-VC"},
    "Almería": {"iso": "ES-AL", "parent": "ES-AN"},
    "Asturias": {"iso": "ES-O", "parent": "ES-AS"},
    "Ávila": {"iso": "ES-AV", "parent": "ES-CL"},
    "Badajoz": {"iso": "ES-BA", "parent": "ES-EX"},
    "Baleares": {"iso": "ES-PM", "parent": "ES-IB"},
    "Barcelona": {"iso": "ES-B", "parent": "ES-CT"},
    "Bizkaia": {"iso": "ES-BI", "parent": "ES-PV"},
    "Burgos": {"iso": "ES-BU", "parent": "ES-CL"},
    "Cáceres": {"iso": "ES-CC", "parent": "ES-EX"},
    "Cádiz": {"iso": "ES-CA", "parent": "ES-AN"},
    "Cantabria": {"iso": "ES-S", "parent": "ES-CB"},
    "Castellón": {"iso": "ES-CS", "parent": "ES-VC"},
    "Ceuta": {"iso": "ES-CE", "parent": "ES-CE"},
    "Ciudad Real": {"iso": "ES-CR", "parent": "ES-CM"},
    "Córdoba": {"iso": "ES-CO", "parent": "ES-AN"},
    "Cuenca": {"iso": "ES-CU", "parent": "ES-CM"},
    "Gipuzkoa": {"iso": "ES-SS", "parent": "ES-PV"},
    "Girona": {"iso": "ES-GI", "parent": "ES-CT"},
    "Granada": {"iso": "ES-GR", "parent": "ES-AN"},
    "Guadalajara": {"iso": "ES-GU", "parent": "ES-CM"},
    "Huelva": {"iso": "ES-H", "parent": "ES-AN"},
    "Huesca": {"iso": "ES-HU", "parent": "ES-AR"},
    "Jaén": {"iso": "ES-J", "parent": "ES-AN"},
    "La Rioja": {"iso": "ES-LO", "parent": "ES-RI"},
    "Las Palmas": {"iso": "ES-GC", "parent": "ES-CN"},
    "León": {"iso": "ES-LE", "parent": "ES-CL"},
    "Lleida": {"iso": "ES-L", "parent": "ES-CT"},
    "Lugo": {"iso": "ES-LU", "parent": "ES-GA"},
    "Madrid": {"iso": "ES-M", "parent": "ES-MD"},
    "Málaga": {"iso": "ES-MA", "parent": "ES-AN"},
    "Melilla": {"iso": "ES-ML", "parent": "ES-ML"},
    "Murcia": {"iso": "ES-MU", "parent": "ES-MC"},
    "Navarra": {"iso": "ES-NA", "parent": "ES-NC"},
    "Ourense": {"iso": "ES-OR", "parent": "ES-GA"},
    "Palencia": {"iso": "ES-P", "parent": "ES-CL"},
    "Pontevedra": {"iso": "ES-PO", "parent": "ES-GA"},
    "Salamanca": {"iso": "ES-SA", "parent": "ES-CL"},
    "Santa Cruz de Tenerife": {"iso": "ES-TF", "parent": "ES-CN"},
    "Segovia": {"iso": "ES-SG", "parent": "ES-CL"},
    "Sevilla": {"iso": "ES-SE", "parent": "ES-AN"},
    "Soria": {"iso": "ES-SO", "parent": "ES-CL"},
    "Tarragona": {"iso": "ES-T", "parent": "ES-CT"},
    "Teruel": {"iso": "ES-TE", "parent": "ES-AR"},
    "Toledo": {"iso": "ES-TO", "parent": "ES-CM"},
    "Valencia": {"iso": "ES-V", "parent": "ES-VC"},
    "Valladolid": {"iso": "ES-VA", "parent": "ES-CL"},
    "Zamora": {"iso": "ES-ZA", "parent": "ES-CL"},
    "Zaragoza": {"iso": "ES-Z", "parent": "ES-AR"}
}

# ==========================================
# 1. UTILIDADES Y SERVIDORES
# ==========================================
class ChequeadorActualizaciones(QThread):
    resultado = pyqtSignal(bool, str, str, str)

    def comparar_versiones(self, v1, v2):
        def parse(v): return [int(x) for x in re.sub(r'[^\d.]', '', v).split('.') if x.strip()]
        p1, p2 = parse(v1), parse(v2)
        for i in range(max(len(p1), len(p2))):
            va = p1[i] if i < len(p1) else 0
            vb = p2[i] if i < len(p2) else 0
            if va != vb: return va > vb
        return False

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
                               cab(tt("hdr_realizado_por", "Realizado por")), cab(tt("hdr_prioridad", "Prioridad")),
                               cab(t("hdr_foto_antes")), cab(t("hdr_foto_despues"))]]

                for fila_pdf in trabajo["datos"]:
                    fecha, desc, tags = fila_pdf[0], fila_pdf[1], fila_pdf[2]
                    autor = fila_pdf[3] if len(fila_pdf) > 3 and fila_pdf[3] else usuarios.ETIQUETA_HISTORICO
                    maquina_nombre = self.mapa_maquinas.get(fila_pdf[4], "-") if len(fila_pdf) > 4 and fila_pdf[4] else "-"
                    prioridad_txt = traducir_prioridad(fila_pdf[5]) if len(fila_pdf) > 5 else traducir_prioridad("Media")
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
                    desc_visual = re.sub(r"\[REF:.*?\]", "", desc_visual).strip()

                    p_desc = Paragraph(desc_visual.replace("\n", "<br/>"), style_cell)
                    data_tabla.append([Paragraph(fecha_formateada, style_cell), p_desc, Paragraph(maquina_nombre, style_cell), Paragraph(autor, style_cell), Paragraph(prioridad_txt, style_cell), img_obj, img_obj_d])

                ancho_foto = 3.0 * cm
                tabla_pdf = Table(data_tabla, colWidths=[2.0*cm, 4.2*cm, 2.2*cm, 2.4*cm, 1.8*cm, ancho_foto, ancho_foto])
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


class VisorFoto(QDialog):
    def __init__(self, ruta_imagen, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("title_visor_imagen"))
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.label)
        btn_cerrar = QPushButton(t("btn_cerrar"))
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)
        self.pixmap_original = QPixmap(ruta_imagen)
        if self.pixmap_original.isNull(): self.label.setText(t("msg_error_cargar_imagen"))
        else: self.actualizar_imagen()

    def resizeEvent(self, event):
        self.actualizar_imagen()
        super().resizeEvent(event)

    def actualizar_imagen(self):
        if not self.pixmap_original.isNull() and self.label.width() > 0:
            pixmap_scaled = self.pixmap_original.scaled(
                self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.label.setPixmap(pixmap_scaled)

class DialogoSelectorFoto(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("title_visor_manual"))
        self.resize(1100, 600)
        self.ruta_seleccionada = None

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.model = QFileSystemModel()
        ruta_inicial = QDir.homePath()
        self.model.setRootPath(ruta_inicial)
        self.model.setNameFilters(["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"])
        self.model.setNameFilterDisables(False)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(ruta_inicial))
        self.tree.setColumnWidth(0, 400)
        self.tree.hideColumn(1); self.tree.hideColumn(2); self.tree.hideColumn(3)
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)

        self.tree.clicked.connect(self.on_click)
        self.tree.doubleClicked.connect(self.on_double_click)

        right_layout = QVBoxLayout()
        self.preview_lbl = QLabel(t("lbl_seleccionar_archivo"))
        self.preview_lbl.setFixedWidth(500)
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setStyleSheet(_estilo_zona_arrastre())

        btn_ok = QPushButton(t("btn_elegir_foto"))
        btn_ok.setMinimumHeight(45)
        btn_ok.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton(t("btn_cancelar"))
        btn_cancel.clicked.connect(self.reject)

        right_layout.addWidget(self.preview_lbl)
        right_layout.addWidget(btn_ok)
        right_layout.addWidget(btn_cancel)

        layout.addWidget(self.tree, 1)
        layout.addLayout(right_layout, 0)

    def on_click(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.mostrar_preview(path)
            self.ruta_seleccionada = path
        else:
            self.ruta_seleccionada = None
            self.preview_lbl.setText(t("msg_es_carpeta"))
            self.preview_lbl.setPixmap(QPixmap())

    def on_double_click(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self.ruta_seleccionada = path
            self.accept()

    def mostrar_preview(self, path):
        pix = QPixmap(path)
        if not pix.isNull():
            self.preview_lbl.setPixmap(pix.scaled(
                self.preview_lbl.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.preview_lbl.setText(t("msg_no_imagen_valida"))

    def selectedFiles(self):
        if self.ruta_seleccionada: return [self.ruta_seleccionada]
        return []

class DialogoQR(QDialog):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("title_sincronizar_movil"))
        self.resize(300, 420)
        l = QVBoxLayout()
        l.addWidget(QLabel(t("lbl_qr_paso1"), alignment=Qt.AlignmentFlag.AlignCenter))
        l.addWidget(QLabel(t("lbl_qr_paso2"), alignment=Qt.AlignmentFlag.AlignCenter))
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        p = QPixmap.fromImage(QImage.fromData(buffer.getvalue()))
        li = QLabel()
        li.setPixmap(p.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        li.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(li)
        l.addWidget(QLabel(url, alignment=Qt.AlignmentFlag.AlignCenter))
        self.setLayout(l)

class ServidorSincronizacion(QThread):
    registro_recibido = pyqtSignal(str, str, str, str, str)
    pendiente_actualizado = pyqtSignal()
    stock_actualizado = pyqtSignal()

    def __init__(self, carpeta_destino, db_path):
        super().__init__()
        self.carpeta_destino = carpeta_destino
        self.db_path = db_path
        self.app = Flask(__name__)
        self.server_port = 5000
        usuarios.configurar_db(db_path)

        # --- AUTENTICACIÓN POR TOKEN ---------------------------------------
        def _token_peticion():
            cabecera = request.headers.get('Authorization', '')
            if cabecera.startswith('Bearer '):
                return cabecera[7:].strip()
            return request.headers.get('X-MantPro-Token', '')

        def _usuario_peticion():
            """Devuelve el usuario del token, o None si no es válido."""
            return usuarios.usuario_por_token(_token_peticion())

        def requiere_token(func):
            from functools import wraps

            @wraps(func)
            def envoltorio(*args, **kwargs):
                u = _usuario_peticion()
                if u is None:
                    return jsonify({
                        "status": "error",
                        "error": "token_invalido",
                        "message": "Sesión no válida. Vuelve a iniciar sesión."
                    }), 401
                g.usuario_mantpro = u
                return func(*args, **kwargs)
            return envoltorio

        self._usuario_peticion = _usuario_peticion

        # --- API DE TRABAJOS (app MantPro) ----------------------------------
        # Lectura: cualquier usuario autenticado. Alta/edición/completar/borrar
        # trabajos y avisos: solo admin o rol "técnico" (usuarios.puede_hacer_trabajos).
        def requiere_tecnico(func):
            from functools import wraps

            @wraps(func)
            def envoltorio(*args, **kwargs):
                if not usuarios.puede_hacer_trabajos(g.usuario_mantpro):
                    return jsonify({
                        "status": "error", "error": "sin_permiso",
                        "message": "Tu usuario no puede gestionar trabajos."
                    }), 403
                return func(*args, **kwargs)
            return envoltorio

        @self.app.route('/api/login', methods=['POST'])
        def api_login():
            datos = request.get_json(silent=True) or request.form
            login_usuario = (datos.get('login') or '').strip()
            password = datos.get('password') or ''
            dispositivo = (datos.get('dispositivo') or '')[:120]
            if not login_usuario or not password:
                return jsonify({"status": "error", "message": "Faltan datos"}), 400
            usuario = usuarios.autenticar(login_usuario, password)
            if usuario is None:
                return jsonify({"status": "error", "error": "credenciales",
                                "message": "Usuario o contraseña incorrectos."}), 401
            token = usuarios.crear_token(usuario['id'], dispositivo)
            return jsonify({"status": "ok", "token": token, "usuario": {
                "id": usuario['id'], "login": usuario['login'],
                "nombre": usuario['nombre'], "rol": usuario['rol'],
                "roles": usuario['roles']}})

        @self.app.route('/api/logout', methods=['POST'])
        @requiere_token
        def api_logout():
            usuarios.revocar_token(_token_peticion())
            return jsonify({"status": "ok"})

        @self.app.route('/api/yo', methods=['GET'])
        @requiere_token
        def api_yo():
            return jsonify({"status": "ok", "usuario": g.usuario_mantpro})

        @self.app.route('/api/ping', methods=['GET'])
        def api_ping():
            # Sin token: sirve para comprobar conectividad y si el PC ya pide login
            return jsonify({"status": "ok", "auth": True, "version_api": 2})
        # -------------------------------------------------------------------

        # --- RUTAS EXISTENTES ---
        @self.app.route('/api/upload', methods=['POST'])
        @requiere_token
        def api_upload():
            try:
                usuario = g.usuario_mantpro
                titulo = request.form.get('titulo', 'Sin Título')
                detalles = request.form.get('detalles', '')
                tags = request.form.get('tags', 'General')

                # --- LEER FECHA DEL MÓVIL ---
                fecha_movil = request.form.get('fecha')
                if fecha_movil:
                    fecha_final = fecha_movil
                else:
                    fecha_final = datetime.now().strftime("%Y-%m-%d")
                # -----------------------------

                filename, ruta_local = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')
                raw_desc = ruta_local if ruta_local else detalles

                # --- Máquina vinculada (opcional, enviada por la app móvil) ---
                maquina_id_raw = request.form.get('maquina_id')
                try:
                    maquina_id = int(maquina_id_raw) if maquina_id_raw else None
                except (TypeError, ValueError):
                    maquina_id = None

                # --- FIX: CREAR LA DESCRIPCIÓN COMPLETA CON TÍTULO Y FOTO ---
                desc_final = titulo
                if detalles:
                    desc_final += f"\n{detalles}"
                if filename:
                    desc_final += f"\n[FOTO: {filename}]"
                if filename_d:
                    desc_final += f"\n[FOTO_DESPUES: {filename_d}]"

                # Usamos el bloque with para asegurar el guardado
                with get_db_connection(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO tareas (fecha, descripcion, tags, raw_desc, foto, usuario_id, usuario_nombre, maquina_id) VALUES (?,?,?,?,?,?,?,?)',
                                   (fecha_final, desc_final, tags, raw_desc, filename,
                                    usuario['id'], usuario['nombre'], maquina_id))
                    conn.commit()

                self._descontar_materiales_trabajo(request, usuario, titulo)

                # Emitimos la señal pasando el título correcto para la notificación
                self.registro_recibido.emit(titulo, detalles, tags, raw_desc if raw_desc else "", filename if filename else "")
                return jsonify({"status": "ok"})
            except Exception as e:
                print(f"Error api_upload: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/maquinas', methods=['GET'])
        @requiere_token
        def api_maquinas():
            try:
                return jsonify(maquinas.listar_maquinas())
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/pendientes', methods=['GET'])
        @requiere_token
        def api_get_pendientes():
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                u = g.usuario_mantpro
                solo_mios = request.args.get('solo_mios', '') in ('1', 'true', 'True')
                columnas = ("SELECT id, titulo, detalles, asignado_a, COALESCE(asignado_nombre,''), "
                            "COALESCE(prioridad,'Media'), especialidad_id FROM pendientes")
                if solo_mios:
                    c.execute(columnas + " WHERE asignado_a = ? ORDER BY id DESC", (u['id'],))
                elif usuarios.es_admin(u):
                    c.execute(columnas + " ORDER BY id DESC")
                else:
                    # Igual que en los avisos: cada técnico ve los suyos más los
                    # que no están asignados a nadie y coinciden con alguna de
                    # sus especialidades (o no tienen ninguna); no ve los
                    # asignados a otro técnico ni los restringidos a una
                    # especialidad que no tiene.
                    especialidades_u = u.get('especialidad_ids') or []
                    interrogantes = ", ".join("?" * len(especialidades_u))
                    condicion_especialidad = (
                        f"especialidad_id IS NULL OR especialidad_id IN ({interrogantes})"
                        if especialidades_u else "especialidad_id IS NULL")
                    c.execute(columnas + " WHERE asignado_a = ? OR (asignado_a IS NULL AND "
                              f"({condicion_especialidad})) ORDER BY id DESC",
                              (u['id'], *especialidades_u))
                filas = c.fetchall()
                conn.close()
                especialidades_por_id = {e['id']: e['nombre'] for e in usuarios.listar_especialidades()}
                datos = [{"id": r[0], "titulo": r[1], "detalles": r[2],
                          "asignado_a": r[3], "asignado": r[4], "prioridad": r[5],
                          "especialidad_id": r[6], "especialidad": especialidades_por_id.get(r[6])} for r in filas]
                return jsonify(datos)
            except Exception as e: return jsonify({"error": str(e)}), 500

        @self.app.route('/api/especialidades', methods=['GET'])
        @requiere_token
        def api_get_especialidades():
            try:
                return jsonify(usuarios.listar_especialidades())
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/completar_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_completar_pendiente():
            try:
                usuario = g.usuario_mantpro
                id_pend = request.form.get('id')
                titulo = request.form.get('titulo') or "Sin Título"
                detalles = request.form.get('detalles', '')
                tags = request.form.get('tags', '')
                prioridad = request.form.get('prioridad') or 'Media'

                # --- LEER FECHA DEL MÓVIL ---
                fecha_movil = request.form.get('fecha')
                fecha_final = fecha_movil if fecha_movil else datetime.now().strftime("%Y-%m-%d")
                # ----------------------------

                filename, ruta_local = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')
                raw_desc = ruta_local if ruta_local else detalles

                # --- FIX: CREAR LA DESCRIPCIÓN COMPLETA CON TÍTULO Y FOTO ---
                desc_final = titulo
                if detalles:
                    desc_final += f"\n{detalles}"
                if filename:
                    desc_final += f"\n[FOTO: {filename}]"
                if filename_d:
                    desc_final += f"\n[FOTO_DESPUES: {filename_d}]"

                with get_db_connection(self.db_path) as conn:
                    c = conn.cursor()
                    c.execute('DELETE FROM pendientes WHERE id=?', (id_pend,))
                    if c.rowcount == 0:
                        # El pendiente no existe (id inválido, ya completado o aún no
                        # sincronizado desde el móvil): no creamos nada en el historial
                        # para no duplicar el trabajo.
                        return jsonify({"status": "error", "message": "El pendiente ya no existe."}), 404
                    # Usamos el INSERT completo para alimentar todas las columnas
                    c.execute('INSERT INTO tareas (fecha, descripcion, tags, raw_desc, foto, usuario_id, usuario_nombre, prioridad) VALUES (?,?,?,?,?,?,?,?)',
                              (fecha_final, desc_final, tags, raw_desc, filename,
                               usuario['id'], usuario['nombre'], prioridad))
                    conn.commit()

                self._descontar_materiales_trabajo(request, usuario, titulo)

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                print(f"Error completar_pendiente: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/agregar_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_agregar_pendiente():
            print(">>> PETICIÓN: AGREGAR PENDIENTE")
            try:
                titulo = request.form.get('titulo')
                detalles = request.form.get('detalles')
                prioridad = request.form.get('prioridad') or 'Media'
                especialidad_id = request.form.get('especialidad_id') or None
                if especialidad_id is not None:
                    especialidad_id = int(especialidad_id)
                filename, ruta_foto = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')
                if filename: detalles += f"\n[FOTO: {filename}]"
                if filename_d: detalles += f"\n[FOTO_DESPUES: {filename_d}]"

                # Timeout de 10s para esperar si la BD está ocupada
                conn = sqlite3.connect(self.db_path, timeout=10)
                c = conn.cursor()
                # Un pendiente creado desde el móvil queda asignado a quien lo crea
                usuario = g.usuario_mantpro
                c.execute('INSERT INTO pendientes (titulo, detalles, asignado_a, asignado_nombre, prioridad, especialidad_id) VALUES (?,?,?,?,?,?)',
                          (titulo, detalles, usuario['id'], usuario['nombre'], prioridad, especialidad_id))
                conn.commit()
                conn.close()

                print("✅ Pendiente guardado OK")
                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                print(f"!!! ERROR AGREGAR PENDIENTE: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/editar_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_editar_pendiente():
            try:
                id_p = request.form.get('id')
                titulo = request.form.get('titulo')
                detalles = request.form.get('detalles')
                prioridad = request.form.get('prioridad')

                # Gestión de foto nueva si la hubiera
                filename, ruta = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')
                if filename:
                    detalles += f"\n[FOTO: {filename}]"
                if filename_d:
                    detalles += f"\n[FOTO_DESPUES: {filename_d}]"

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                # Actualizamos título y detalles (y prioridad si el móvil la ha enviado)
                if prioridad:
                    c.execute('UPDATE pendientes SET titulo=?, detalles=?, prioridad=? WHERE id=?', (titulo, detalles, prioridad, id_p))
                else:
                    c.execute('UPDATE pendientes SET titulo=?, detalles=? WHERE id=?', (titulo, detalles, id_p))
                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/eliminar_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_eliminar_pendiente():
            # (Mantener código original)
            try:
                id_p = request.form.get('id')
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('DELETE FROM pendientes WHERE id=?', (id_p,))
                conn.commit()
                conn.close()
                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        # ==========================================
        # --- NUEVAS RUTAS PARA EL MÓVIL ---
        # ==========================================

        @self.app.route('/api/dashboard', methods=['GET'])
        @requiere_token
        def api_dashboard():
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                # 1. Contar pendientes
                c.execute("SELECT COUNT(*) FROM pendientes")
                n_pendientes = c.fetchone()[0]

                # 2. Contar registros del mes actual
                mes_actual = datetime.now().strftime("%Y-%m")
                c.execute("SELECT COUNT(*) FROM tareas WHERE fecha LIKE ?", (f"{mes_actual}%",))
                n_mes = c.fetchone()[0]

                # 3. Contar avisos activos (lógica simplificada para SQL)
                c.execute("SELECT titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada FROM avisos_recurrentes")
                avisos = c.fetchall()
                n_avisos = 0
                hoy = datetime.now().date() # Usamos objeto date de Python para calcular rápido aquí

                # (Nota: Replicar lógica exacta de recurrencia en SQL puro es complejo,
                # enviamos el total de avisos configurados como dato simple o hacemos un cálculo aproximado)
                n_avisos_total = len(avisos)

                conn.close()
                return jsonify({
                    "pendientes": n_pendientes,
                    "registros_mes": n_mes,
                    "avisos_total": n_avisos_total
                })
            except Exception as e: return jsonify({"error": str(e)}), 500

        @self.app.route('/api/historial', methods=['GET'])
        @requiere_token
        def api_historial():
            try:
                query = request.args.get('q', '').lower()
                # Paginación: 'page' empieza en 0, 'limit' registros por página (por defecto 50)
                try:
                    page = max(0, int(request.args.get('page', 0)))
                except (TypeError, ValueError):
                    page = 0
                try:
                    limit = int(request.args.get('limit', 50))
                except (TypeError, ValueError):
                    limit = 50
                limit = max(1, min(limit, 200))
                offset = page * limit

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                mes = request.args.get('mes', '')
                sql = "SELECT id, fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id FROM tareas WHERE 1=1"
                params = []

                if query:
                    sql += " AND (descripcion LIKE ? OR tags LIKE ?)"
                    p_query = f"%{query}%"
                    params.extend([p_query, p_query])

                if mes:
                    sql += " AND fecha LIKE ?"
                    params.append(f"{mes}%")

                sql += " ORDER BY fecha DESC, id DESC LIMIT ? OFFSET ?"
                params.extend([limit + 1, offset])

                c.execute(sql, params)
                filas = c.fetchall()
                hay_mas = len(filas) > limit
                filas = filas[:limit]
                nombres_maquinas = {m["id"]: m["nombre"] for m in maquinas.listar_maquinas()}
                # Procesamos para extraer nombre de foto si existe
                resultados = []
                for r in filas:
                    desc = r[2]
                    foto = None
                    m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
                    if m: foto = m.group(1).split("]")[0].strip()

                    foto_d = None
                    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc)
                    if m_d: foto_d = m_d.group(1).split("]")[0].strip()

                    # Limpieza visual para el móvil
                    desc_limpia = re.sub(r"\[FOTO.*?:.*?\]", "", desc)
                    desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                    maquina_id = r[5] if len(r) > 5 else None
                    resultados.append({
                        "id": r[0],
                        "fecha": r[1],
                        "descripcion": desc_limpia,
                        "tags": r[3],
                        "foto": foto,
                        "foto_d": foto_d,
                        "raw_desc": desc, # Necesario para editar
                        "usuario": r[4] if len(r) > 4 else "",
                        "maquina_id": maquina_id,
                        "maquina_nombre": nombres_maquinas.get(maquina_id, "") if maquina_id else ""
                    })
                conn.close()
                return jsonify({"items": resultados, "has_more": hay_mas, "page": page})
            except Exception as e: return jsonify({"error": str(e)}), 500

        # ---------------------------------------------------------
        # 1. API AVISOS (Lógica corregida: Acepta retrasos)
        # ---------------------------------------------------------
        @self.app.route('/api/avisos', methods=['GET'])
        @requiere_token
        def api_avisos():
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                u = g.usuario_mantpro
                # Cada trabajador ve sus avisos asignados más los que todavía
                # no están asignados a nadie y, de esos, solo los que no
                # tienen especialidad o coinciden con la suya. Los asignados
                # a otro técnico, o restringidos a otra especialidad, no se
                # le muestran. El admin los ve todos.
                if usuarios.es_admin(u):
                    c.execute("SELECT id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, "
                              "asignado_a, COALESCE(asignado_nombre,''), especialidad_id FROM avisos_recurrentes")
                    raw_avisos = c.fetchall()
                else:
                    especialidades_u = u.get('especialidad_ids') or []
                    interrogantes = ", ".join("?" * len(especialidades_u))
                    condicion_especialidad = (
                        f"especialidad_id IS NULL OR especialidad_id IN ({interrogantes})"
                        if especialidades_u else "especialidad_id IS NULL")
                    c.execute("SELECT id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, "
                              "asignado_a, COALESCE(asignado_nombre,''), especialidad_id FROM avisos_recurrentes "
                              f"WHERE asignado_a = ? OR (asignado_a IS NULL AND ({condicion_especialidad}))",
                              (u['id'], *especialidades_u))
                    raw_avisos = c.fetchall()
                conn.close()

                lista_procesada = []
                hoy = datetime.now().date()

                for aid, tit, finicio, freq, dur, ult, asignado_a, asignado_nombre, especialidad_id in raw_avisos:
                    if not finicio: continue
                    try:
                        fi = datetime.strptime(finicio, "%Y-%m-%d").date()
                    except: continue

                    if not freq: freq = "Anual"
                    freq = idiomas.normalizar_frecuencia(freq)

                    # Un aviso "Diario" se resetea cada día: no le aplicamos la duración
                    # configurada, porque un margen de varios días haría que el de ayer
                    # siguiera contando como "hecho" hoy.
                    dur_ventana = 0 if freq == "Diario" else dur

                    # Calcular cuándo toca (Misma lógica matemática de antes)
                    ocurrencia = fi
                    while (ocurrencia + timedelta(days=dur_ventana)) < hoy:
                        if freq == "Diario": ocurrencia += timedelta(days=1)
                        elif freq == "Semanal": ocurrencia += timedelta(days=7)
                        elif freq == "Mensual":
                            ny = ocurrencia.year + (ocurrencia.month // 12)
                            nm = (ocurrencia.month % 12) + 1
                            try: ocurrencia = ocurrencia.replace(year=ny, month=nm)
                            except: ocurrencia = ocurrencia.replace(year=ny, month=nm, day=28)
                        elif freq == "Trimestral":
                             m_add = ocurrencia.month + 3
                             ny = ocurrencia.year + (m_add - 1) // 12
                             nm = (m_add - 1) % 12 + 1
                             try: ocurrencia = ocurrencia.replace(year=ny, month=nm)
                             except: ocurrencia = ocurrencia.replace(year=ny, month=nm, day=28)
                        elif freq == "Semestral":
                             m_add = ocurrencia.month + 6
                             ny = ocurrencia.year + (m_add - 1) // 12
                             nm = (m_add - 1) % 12 + 1
                             try: ocurrencia = ocurrencia.replace(year=ny, month=nm)
                             except: ocurrencia = ocurrencia.replace(year=ny, month=nm, day=28)
                        elif freq == "Anual": ocurrencia = ocurrencia.replace(year=ocurrencia.year + 1)
                        else: break

                    fin_ocurrencia = ocurrencia + timedelta(days=dur_ventana)

                    # --- CORRECCIÓN DE ESTADO ---
                    estado = "FUTURO"
                    color_code = "blue"

                    es_activo = (ocurrencia <= hoy <= fin_ocurrencia)

                    # Lógica corregida: Si la última completada (ult) es posterior o igual a la fecha de ocurrencia, está OK.
                    # Antes solo miraba si era EXACTAMENTE igual.
                    es_completado = False
                    if ult:
                        fecha_ult = datetime.strptime(ult, "%Y-%m-%d").date()
                        if fecha_ult >= ocurrencia:
                            es_completado = True

                    if es_activo:
                        if es_completado:
                            estado = "OK"
                            color_code = "green"
                        else:
                            estado = "PENDIENTE"
                            color_code = "red"
                    elif hoy < ocurrencia:
                        estado = "FUTURO"
                        color_code = "blue"

                    # Caso especial: Si ya lo completé hoy (aunque fuera futuro), que salga verde
                    if ult == hoy.strftime("%Y-%m-%d"):
                         estado = "OK"
                         color_code = "green"

                    lista_procesada.append({
                        "id": aid,
                        "titulo": tit,
                        "frecuencia": freq,
                        "rango": f"{ocurrencia.strftime(idiomas.formato_fecha_corta_py())} - {fin_ocurrencia.strftime(idiomas.formato_fecha_corta_py())}",
                        "estado": estado,
                        "color": color_code,
                        "raw_inicio": ocurrencia.strftime("%Y-%m-%d"),
                        "raw_fin": fin_ocurrencia.strftime("%Y-%m-%d"),
                        # Datos "crudos" del aviso (fecha de inicio original, duración y última
                        # completada) para que el móvil pueda recalcular el ciclo por su cuenta
                        # con la fecha del propio teléfono, aunque lleve meses sin sincronizar.
                        "fecha_inicio_raw": finicio,
                        "duracion_dias": dur,
                        "ultima_completada": ult or "",
                        "asignado_a": asignado_a,
                        "asignado": asignado_nombre or ""
                    })

                return jsonify(lista_procesada)
            except Exception as e: return jsonify({"error": str(e)}), 500

        # ---------------------------------------------------------
        # 2. API COMPLETAR (Anti-Duplicados)
        # ---------------------------------------------------------
        @self.app.route('/api/completar_aviso', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_completar_aviso():
            print("\n" + "="*40)
            print(">>> RECIBIDA PETICIÓN: COMPLETAR AVISO")

            try:
                # 1. IMPRIMIR QUÉ NOS LLEGA EXACTAMENTE
                print(f"Datos recibidos (RAW): {request.form}")

                id_aviso_str = request.form.get('id')
                titulo = request.form.get('titulo') or "Sin Título"
                fecha_custom = request.form.get('fecha_custom')

                # 2. VALIDACIÓN DE ID
                if not id_aviso_str:
                    print("!!! ERROR: No ha llegado el ID")
                    return jsonify({"status": "error", "message": "Falta ID"}), 400

                try:
                    id_aviso = int(id_aviso_str)
                    print(f"ID convertido a entero: {id_aviso}")
                except ValueError:
                    print(f"!!! ERROR: El ID '{id_aviso_str}' no es un número")
                    return jsonify({"status": "error", "message": "ID no numérico"}), 400

                # 3. FECHA
                fecha_final = fecha_custom if fecha_custom else datetime.now().strftime("%Y-%m-%d")
                print(f"Fecha a guardar: {fecha_final}")

                # 4. CONEXIÓN BASE DE DATOS
                print("Intentando conectar a BD...")
                conn = sqlite3.connect(self.db_path, timeout=10) # Timeout alto para evitar bloqueos
                c = conn.cursor()

                # 5. ACTUALIZAR AVISO
                print("Ejecutando UPDATE en avisos_recurrentes...")
                c.execute('UPDATE avisos_recurrentes SET ultima_completada=? WHERE id=?', (fecha_final, id_aviso))
                if c.rowcount == 0:
                    print("⚠️ AVISO: No se actualizó ninguna fila. ¿Existe el ID?")
                else:
                    print("✅ UPDATE correcto.")

                # 6. INSERTAR HISTORIAL
                print("Verificando historial para evitar duplicados...")
                desc_historial = f"Mantenimiento Preventivo: {titulo}"
                tags_historial = "Preventivo, Aviso Recurrente"

                c.execute("SELECT id FROM tareas WHERE fecha=? AND descripcion=?", (fecha_final, desc_historial))
                existe = c.fetchone()

                if not existe:
                    print("Insertando nueva tarea en historial...")
                    usuario_aviso = g.usuario_mantpro
                    c.execute('INSERT INTO tareas (fecha, descripcion, tags, usuario_id, usuario_nombre) VALUES (?,?,?,?,?)',
                              (fecha_final, desc_historial, tags_historial,
                               usuario_aviso['id'], usuario_aviso['nombre']))
                else:
                    print("La tarea ya existe en el historial. Saltando insert.")

                conn.commit()
                conn.close()
                print("✅ BD CERRADA Y COMMIT REALIZADO")

                # 7. AVISAR INTERFAZ PC
                self.pendiente_actualizado.emit()

                print(">>> PROCESO TERMINADO CON ÉXITO")
                print("="*40 + "\n")
                return jsonify({"status": "ok"})

            except Exception as e:
                print("\n!!! EXCEPCIÓN CRÍTICA EN EL SERVIDOR !!!")
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
                print("="*40 + "\n")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/foto/<path:filename>')
        def serve_foto(filename):
            try:
                return send_from_directory(self.carpeta_destino, filename)
            except Exception as e:
                return str(e), 404

        @self.app.route('/api/historial_todo', methods=['GET'])
        @requiere_token
        def api_historial_todo():
            # Versión ligera y SIN LIMIT, usada solo por la herramienta de "reenviar fotos"
            # del móvil para poder revisar TODO el histórico, no solo los últimos 50.
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT id, descripcion FROM tareas ORDER BY fecha DESC, id DESC")
                resultados = []
                for id_t, desc in c.fetchall():
                    foto = None
                    m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
                    if m: foto = m.group(1).split("]")[0].strip()
                    foto_d = None
                    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc)
                    if m_d: foto_d = m_d.group(1).split("]")[0].strip()
                    resultados.append({"id": id_t, "foto": foto, "foto_d": foto_d})
                conn.close()
                return jsonify(resultados)
            except Exception as e: return jsonify({"error": str(e)}), 500

        @self.app.route('/api/editar_historial', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_editar_historial():
            try:
                id_t = request.form.get('id')
                desc_final = request.form.get('detalles') # Ya viene formateada desde el móvil (sin tags FOTO)
                tags = request.form.get('tags')

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                # Recuperamos la descripción actual para no perder fotos que no se reenvían en esta edición
                c.execute("SELECT descripcion FROM tareas WHERE id=?", (id_t,))
                row = c.fetchone()
                desc_actual = row[0] if row else ""

                m_actual = re.search(r"\[FOTO:\s*(.*?)\]", desc_actual)
                foto_actual = m_actual.group(1).strip() if m_actual else None
                m_actual_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc_actual)
                foto_actual_d = m_actual_d.group(1).strip() if m_actual_d else None

                # Si envían foto nueva, procesarla; si no, mantenemos la que ya había en BD
                filename, ruta = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')

                foto_final = filename if filename else foto_actual
                foto_final_d = filename_d if filename_d else foto_actual_d

                if foto_final:
                    desc_final += f"\n[FOTO: {foto_final}]"
                if foto_final_d:
                    desc_final += f"\n[FOTO_DESPUES: {foto_final_d}]"

                if 'maquina_id' in request.form:
                    maquina_id_raw = request.form.get('maquina_id')
                    try:
                        maquina_id = int(maquina_id_raw) if maquina_id_raw else None
                    except (TypeError, ValueError):
                        maquina_id = None
                    c.execute("UPDATE tareas SET descripcion=?, tags=?, maquina_id=? WHERE id=?", (desc_final, tags, maquina_id, id_t))
                else:
                    c.execute("UPDATE tareas SET descripcion=?, tags=? WHERE id=?", (desc_final, tags, id_t))
                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit() # Para refrescar la UI de escritorio
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/restaurar_foto', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_restaurar_foto():
            # Endpoint de reparación manual: sube una foto (antes o después) para un registro
            # existente SIN tocar el resto de la descripción ni la otra foto.
            try:
                id_t = request.form.get('id')
                tipo = request.form.get('tipo')  # 'antes' o 'despues'
                key = 'foto' if tipo == 'antes' else 'foto_despues'

                filename, ruta = self._procesar_foto(request, key)
                if not filename:
                    return jsonify({"status": "error", "message": "No se recibió ningún archivo"}), 400

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT descripcion FROM tareas WHERE id=?", (id_t,))
                row = c.fetchone()
                if not row:
                    conn.close()
                    return jsonify({"status": "error", "message": "Registro no encontrado"}), 404
                desc = row[0]

                if tipo == 'antes':
                    if re.search(r"\[FOTO:\s*.*?\]", desc):
                        desc = re.sub(r"\[FOTO:\s*.*?\]", f"[FOTO: {filename}]", desc, count=1)
                    else:
                        desc += f"\n[FOTO: {filename}]"
                else:
                    if re.search(r"\[FOTO_DESPUES:\s*.*?\]", desc):
                        desc = re.sub(r"\[FOTO_DESPUES:\s*.*?\]", f"[FOTO_DESPUES: {filename}]", desc, count=1)
                    else:
                        desc += f"\n[FOTO_DESPUES: {filename}]"

                c.execute("UPDATE tareas SET descripcion=? WHERE id=?", (desc, id_t))
                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok", "filename": filename})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/descompletar_aviso', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_descompletar_aviso():
            try:
                id_aviso = request.form.get('id')

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                # 1. Obtener datos actuales del aviso
                c.execute("SELECT titulo, ultima_completada FROM avisos_recurrentes WHERE id=?", (id_aviso,))
                row = c.fetchone()

                if row:
                    titulo, ult_fecha = row

                    # 2. Intentar borrar del historial la entrada generada para esa fecha
                    # La descripción debe coincidir con la que generamos automáticamente
                    desc = f"Mantenimiento Preventivo: {titulo}"
                    if ult_fecha:
                        c.execute("DELETE FROM tareas WHERE descripcion=? AND fecha=?", (desc, ult_fecha))

                    # 3. Buscar cuál es la NUEVA última fecha real (la anterior a la borrada)
                    # Esto evita que se quede en NULL si ya se había hecho el mes pasado
                    c.execute("SELECT MAX(fecha) FROM tareas WHERE descripcion=?", (desc,))
                    resultado = c.fetchone()
                    prev_fecha = resultado[0] if resultado else None # Puede ser None si nunca se hizo antes

                    # 4. Actualizar el aviso con la fecha histórica correcta
                    c.execute("UPDATE avisos_recurrentes SET ultima_completada=? WHERE id=?", (prev_fecha, id_aviso))

                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/revertir_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_revertir_pendiente():
            # Deshace la finalización de un trabajo: lo saca del historial y lo
            # vuelve a poner en Pendientes. Mismo comportamiento que el PC.
            try:
                usuario = g.usuario_mantpro
                id_t = request.form.get('id')

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT id, fecha, descripcion, tags, usuario_id, COALESCE(usuario_nombre,''), maquina_id FROM tareas WHERE id=?", (id_t,))
                d = c.fetchone()
                if not d:
                    conn.close()
                    return jsonify({"status": "error", "message": "Registro no encontrado"}), 404

                fecha_tarea, desc_tarea = d[1], d[2]
                uid_original = d[4] if len(d) > 4 else None
                unombre_original = d[5] if len(d) > 5 else ""

                if not usuarios.es_admin(usuario) and uid_original != usuario['id']:
                    conn.close()
                    return jsonify({"status": "error", "message": "Solo puedes modificar tus propios trabajos."}), 403

                # Si el trabajo venía de un aviso recurrente, lo "descompletamos" igual
                # que se hace al borrar un registro del historial.
                prefijo = "Mantenimiento Preventivo: "
                if desc_tarea.startswith(prefijo):
                    titulo_aviso = desc_tarea.replace(prefijo, "").strip()
                    try:
                        c.execute("SELECT id FROM avisos_recurrentes WHERE titulo=? AND ultima_completada=?", (titulo_aviso, fecha_tarea))
                        aviso = c.fetchone()
                        if aviso:
                            c.execute("UPDATE avisos_recurrentes SET ultima_completada=NULL WHERE id=?", (aviso[0],))
                            conn.commit()
                    except Exception as e:
                        print(f"Error intentando restaurar aviso: {e}")

                lineas = desc_tarea.split("\n")
                titulo = lineas[0].strip()
                detalles = "\n".join(lineas[1:]).strip()

                try:
                    c.execute('INSERT INTO pendientes (titulo,detalles,asignado_a,asignado_nombre) VALUES (?,?,?,?)',
                              (titulo, detalles, uid_original, unombre_original or None))
                    conn.commit()
                except Exception as e:
                    conn.close()
                    print(f"Error revirtiendo a pendiente: {e}")
                    return jsonify({"status": "error", "message": "No se ha podido revertir el trabajo a pendiente."}), 500

                detalle_auditoria = f"Registro del {fecha_tarea}: {titulo[:80]} (autor original: {unombre_original or usuarios.ETIQUETA_HISTORICO})"
                c.execute("DELETE FROM tareas WHERE id=?", (id_t,))
                conn.commit(); conn.close()
                usuarios.registrar_auditoria(usuario['id'], id_t, "revertir", detalle_auditoria)

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        # --- API DE STOCK (app MantPro Stock) ------------------------------
        # Lectura: cualquier usuario autenticado. Alta/edición/movimientos:
        # solo admin o rol "almacen" (usuarios.puede_gestionar_almacen).
        def requiere_almacen(func):
            from functools import wraps

            @wraps(func)
            def envoltorio(*args, **kwargs):
                if not usuarios.puede_gestionar_almacen(g.usuario_mantpro):
                    return jsonify({
                        "status": "error", "error": "sin_permiso",
                        "message": "Tu usuario no puede gestionar el almacén."
                    }), 403
                return func(*args, **kwargs)
            return envoltorio

        @self.app.route('/api/stock/estructura', methods=['GET'])
        @requiere_token
        def api_stock_estructura():
            return jsonify({"status": "ok", "estanterias": almacen.listar_estructura()})

        @self.app.route('/api/stock/zonas', methods=['GET'])
        @requiere_token
        def api_stock_zonas():
            return jsonify({"status": "ok", "zonas": almacen.listar_zonas()})

        @self.app.route('/api/stock/materiales', methods=['GET'])
        @requiere_token
        def api_stock_materiales():
            filtro = request.args.get('q') or None
            materiales = almacen.listar_materiales(filtro)
            for m in materiales:
                m["ubicacion"] = almacen.obtener_ubicacion_texto(m.get("seccion_id"))
            return jsonify({"status": "ok", "materiales": materiales})

        @self.app.route('/api/stock/bajo_minimo', methods=['GET'])
        @requiere_token
        def api_stock_bajo_minimo():
            materiales = almacen.materiales_bajo_minimo()
            for m in materiales:
                m["ubicacion"] = almacen.obtener_ubicacion_texto(m.get("seccion_id"))
            return jsonify({"status": "ok", "materiales": materiales})

        @self.app.route('/api/stock/material/<int:material_id>', methods=['GET'])
        @requiere_token
        def api_stock_material(material_id):
            material = almacen.obtener_material(material_id)
            if material is None:
                return jsonify({"status": "error", "message": "Material no encontrado"}), 404
            material["ubicacion"] = almacen.obtener_ubicacion_texto(material.get("seccion_id"))
            material["movimientos"] = almacen.obtener_movimientos(material_id, limite=20)
            return jsonify({"status": "ok", "material": material})

        @self.app.route('/api/stock/material', methods=['POST'])
        @requiere_token
        @requiere_almacen
        def api_stock_crear_material():
            try:
                usuario = g.usuario_mantpro
                datos = request.form
                nombre = (datos.get('nombre') or '').strip()
                if not nombre:
                    return jsonify({"status": "error", "message": "El nombre del material es obligatorio."}), 400
                seccion_id = datos.get('seccion_id')
                seccion_id = int(seccion_id) if seccion_id else None
                if seccion_id is None:
                    balda_id = datos.get('balda_id')
                    if balda_id:
                        seccion_id = almacen.seccion_para_balda(int(balda_id))
                filename, _ = self._procesar_foto(request, 'foto')
                material_id = almacen.crear_material(
                    datos.get('codigo', ''), nombre, datos.get('descripcion', ''),
                    datos.get('unidad', ''), float(datos.get('stock_minimo') or 0),
                    seccion_id, filename or None, float(datos.get('stock_inicial') or 0),
                    usuario['id'], usuario['nombre'])
                self.stock_actualizado.emit()
                return jsonify({"status": "ok", "id": material_id})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/stock/material/<int:material_id>', methods=['POST'])
        @requiere_token
        @requiere_almacen
        def api_stock_editar_material(material_id):
            try:
                material = almacen.obtener_material(material_id)
                if material is None:
                    return jsonify({"status": "error", "message": "Material no encontrado"}), 404
                datos = request.form
                nombre = (datos.get('nombre') or '').strip()
                if not nombre:
                    return jsonify({"status": "error", "message": "El nombre del material es obligatorio."}), 400
                seccion_id = datos.get('seccion_id')
                seccion_id = int(seccion_id) if seccion_id else None
                if seccion_id is None:
                    balda_id = datos.get('balda_id')
                    if balda_id:
                        seccion_id = almacen.seccion_para_balda(int(balda_id))

                foto_final = material.get('foto')
                filename, _ = self._procesar_foto(request, 'foto')
                if filename:
                    foto_final = filename
                elif datos.get('borrar_foto') == '1':
                    foto_final = None

                usuario = g.usuario_mantpro
                almacen.actualizar_material(
                    material_id, datos.get('codigo', ''), nombre, datos.get('descripcion', ''),
                    datos.get('unidad', ''), float(datos.get('stock_minimo') or 0),
                    seccion_id, foto_final, usuario['id'], usuario['nombre'])
                self.stock_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/stock/material/<int:material_id>', methods=['DELETE'])
        @requiere_token
        @requiere_almacen
        def api_stock_borrar_material(material_id):
            try:
                material = almacen.obtener_material(material_id)
                if material is None:
                    return jsonify({"status": "error", "message": "Material no encontrado"}), 404
                almacen.borrar_material(material_id)
                self.stock_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/stock/material/<int:material_id>/movimiento', methods=['POST'])
        @requiere_token
        @requiere_almacen
        def api_stock_movimiento(material_id):
            try:
                usuario = g.usuario_mantpro
                datos = request.form
                tipo = datos.get('tipo')
                if tipo not in ('entrada', 'salida'):
                    return jsonify({"status": "error", "message": "Tipo de movimiento no válido."}), 400
                try:
                    cantidad = float(datos.get('cantidad') or 0)
                except ValueError:
                    cantidad = 0
                if cantidad <= 0:
                    return jsonify({"status": "error", "message": "La cantidad debe ser mayor que 0."}), 400
                ok, error = almacen.registrar_movimiento(
                    material_id, tipo, cantidad, usuario['id'], usuario['nombre'],
                    datos.get('motivo', ''))
                if not ok:
                    mensaje = ("No hay stock suficiente para esta salida."
                               if error == "stock_insuficiente" else "Material no encontrado")
                    return jsonify({"status": "error", "error": error, "message": mensaje}), 400
                self.stock_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        # -------------------------------------------------------------------

    def _procesar_foto(self, req, key='foto'):
        if key in req.files:
            file = req.files[key]
            if file and file.filename != '':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = re.sub(r'[^a-zA-Z0-9.]', '_', file.filename)
                filename = f"app_{timestamp}_{safe_name}"
                ruta = os.path.join(self.carpeta_destino, filename)
                file.save(ruta)
                return filename, ruta
        return "", ""

    def _descontar_materiales_trabajo(self, req, usuario, referencia):
        """Lee el campo 'materiales' (JSON: [{"material_id":.., "cantidad":..}, ...])
        del formulario de un trabajo y descuenta cada cantidad del almacén. El
        material ya se ha usado en la realidad, así que el descuento se aplica
        aunque deje el stock en negativo: eso es lo que dispara el aviso de
        "bajo mínimo" en la app para que se verifique y se reponga."""
        materiales_raw = req.form.get('materiales')
        if not materiales_raw:
            return
        try:
            materiales = json.loads(materiales_raw)
        except (ValueError, TypeError):
            return
        hubo_algo = False
        for item in materiales:
            try:
                material_id = int(item.get('material_id'))
                cantidad = float(item.get('cantidad') or 0)
            except (TypeError, ValueError):
                continue
            if cantidad <= 0:
                continue
            ok, _ = almacen.registrar_movimiento(
                material_id, "salida", cantidad, usuario['id'], usuario['nombre'],
                motivo=f"Usado en trabajo: {referencia}", permitir_negativo=True)
            if ok:
                hubo_algo = True
        if hubo_algo:
            self.stock_actualizado.emit()

    def obtener_ip_local(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]; s.close()
            return ip
        except: return "127.0.0.1"

    def run(self):
        # Silencia el log de peticiones HTTP de Werkzeug (una línea por cada
        # sincronización del móvil): con la app ya probada no aporta nada y
        # solo llena la consola.
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        self.app.run(host='0.0.0.0', port=self.server_port, debug=False, use_reloader=False)

# ==========================================
# 2. GESTORES DE DATOS
# ==========================================

class GestorBaseDatos:
    def __init__(self):
        # USAMOS DATA_DIR PARA UBICAR LA DB
        # La lógica de DATA_DIR se calcula arriba globalmente
        self.db_name = os.path.join(DATA_DIR, "mantenimiento.db")
        self.inicializar_tablas()
        # Tablas de usuarios/sesiones + columnas de autoría (idempotente)
        usuarios.configurar_db(self.db_name)
        usuarios.inicializar()
        # Stock de almacén: base de datos propia, separada de la de trabajos
        self.db_almacen_name = os.path.join(DATA_DIR, "almacen.db")
        almacen.configurar_db(self.db_almacen_name)
        almacen.inicializar()
        # Listado de maquinaria + vínculo de cada trabajo con su máquina (idempotente)
        maquinas.configurar_db(self.db_name)
        maquinas.inicializar()

    def conectar(self):
        return sqlite3.connect(self.db_name)

    def inicializar_tablas(self):
        try:
            conn = self.conectar()
            c = conn.cursor()
            c.execute('CREATE TABLE IF NOT EXISTS tareas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, descripcion TEXT, tags TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS dias_especiales (fecha TEXT PRIMARY KEY, tipo TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS pendientes (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, detalles TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)')

            necesita_recrear = False
            try:
                c.execute("PRAGMA table_info(avisos_recurrentes)")
                cols = [info[1] for info in c.fetchall()]
                if 'mes' in cols: necesita_recrear = True
            except: pass

            if necesita_recrear:
                c.execute("DROP TABLE IF EXISTS avisos_recurrentes")

            c.execute('''CREATE TABLE IF NOT EXISTS avisos_recurrentes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        titulo TEXT, fecha_inicio TEXT, frecuencia TEXT, duracion_dias INTEGER, ultima_completada TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e: print(f"Error crítico inicializando BD: {e}")

    def set_config(self, clave, valor):
        try:
            conn = self.conectar()
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO config (clave, valor) VALUES (?, ?)', (clave, valor))
            conn.commit()
            conn.close()
            return True
        except: return False

    def get_config(self, clave):
        try:
            conn = self.conectar()
            c = conn.cursor()
            c.execute('SELECT valor FROM config WHERE clave = ?', (clave,))
            res = c.fetchone()
            conn.close()
            return res[0] if res else None
        except: return None

    def agregar_aviso(self, titulo, fecha_inicio, frecuencia, duracion, asignado_a=None, asignado_nombre=None, especialidad_id=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('INSERT INTO avisos_recurrentes (titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, asignado_a, asignado_nombre, especialidad_id) VALUES (?,?,?,?,?,?,?,?)',
                      (titulo, fecha_inicio, frecuencia, duracion, "", asignado_a, asignado_nombre, especialidad_id))
            conn.commit(); conn.close(); return True
        except Exception as e: return False

    def actualizar_aviso(self, id_aviso, titulo, fecha_inicio, frecuencia, duracion, asignado_a=None, asignado_nombre=None, especialidad_id=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE avisos_recurrentes SET titulo=?, fecha_inicio=?, frecuencia=?, duracion_dias=?, asignado_a=?, asignado_nombre=?, especialidad_id=? WHERE id=?',
                      (titulo, fecha_inicio, frecuencia, duracion, asignado_a, asignado_nombre, especialidad_id, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False

    def obtener_avisos(self):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('SELECT id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, '
                      'asignado_a, COALESCE(asignado_nombre,\'\'), especialidad_id FROM avisos_recurrentes')
            return c.fetchall()
        except: return []
    def borrar_aviso(self, i):
        try: conn = self.conectar(); c = conn.cursor(); c.execute('DELETE FROM avisos_recurrentes WHERE id=?', (i,)); conn.commit(); conn.close(); return True
        except: return False
    def asignar_aviso(self, id_aviso, asignado_a, asignado_nombre):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE avisos_recurrentes SET asignado_a=?, asignado_nombre=? WHERE id=?',
                      (asignado_a, asignado_nombre, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False
    def asignar_especialidad_aviso(self, id_aviso, especialidad_id):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE avisos_recurrentes SET especialidad_id=? WHERE id=?',
                      (especialidad_id, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False
    def marcar_aviso_completado(self, id_aviso, fecha_completada, estado):
        try:
            conn = self.conectar(); c = conn.cursor(); val = fecha_completada if estado else ""
            c.execute('UPDATE avisos_recurrentes SET ultima_completada=? WHERE id=?', (val, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False

    def agregar_tarea(self, f, d, t, usuario_id=None, usuario_nombre=None, maquina_id=None, prioridad="Media", horas_paro=None):
        """Guarda un registro atribuido al usuario que ha iniciado sesión."""
        if usuario_id is None: usuario_id = usuarios.id_actual()
        if usuario_nombre is None: usuario_nombre = usuarios.nombre_actual()
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('INSERT INTO tareas (fecha,descripcion,tags,usuario_id,usuario_nombre,maquina_id,prioridad,horas_paro) VALUES (?,?,?,?,?,?,?,?)',
                      (f, d, t, usuario_id, usuario_nombre, maquina_id, prioridad, horas_paro))
            conn.commit(); conn.close(); return True
        except Exception as e:
            print(f"Error agregar_tarea: {e}"); return False
    def obtener_todas_cronologico(self, filtro_usuario=None):
        try:
            conn=self.conectar(); c=conn.cursor()
            sql = "SELECT id,fecha,descripcion,tags,COALESCE(usuario_nombre,''),maquina_id,COALESCE(prioridad,'Media') FROM tareas"
            params = []
            if filtro_usuario:
                sql += " WHERE usuario_nombre = ?"
                params.append(filtro_usuario)
            sql += " ORDER BY fecha DESC, id DESC"
            c.execute(sql, params)
            return c.fetchall()
        except: return []
    def obtener_tareas_por_fecha(self,f):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT id,descripcion,tags FROM tareas WHERE fecha=?',(f,)); return c.fetchall()
        except: return []
    def borrar_tarea(self, i):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute("SELECT fecha, descripcion, COALESCE(usuario_nombre,'') FROM tareas WHERE id=?", (i,))
            fila = c.fetchone()
            detalle = ""
            if fila:
                desc_corta = fila[1][:80].split("\n")[0]
                detalle = f"Registro del {fila[0]}: {desc_corta} (autor original: {fila[2] or 'Histórico'})"
            c.execute('DELETE FROM tareas WHERE id=?', (i,))
            conn.commit(); conn.close()
            usuarios.registrar_auditoria(usuarios.id_actual(), i, "borrar", detalle)
            return True
        except Exception as e:
            print(f"Error borrar_tarea: {e}"); return False
    def actualizar_tarea(self, i, f, d, t, usuario_id=None, usuario_nombre=None, maquina_id=None, prioridad="Media", horas_paro=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            if usuario_id is not None:
                c.execute('UPDATE tareas SET fecha=?, descripcion=?, tags=?, usuario_id=?, usuario_nombre=?, maquina_id=?, prioridad=?, horas_paro=? WHERE id=?',
                          (f, d, t, usuario_id, usuario_nombre, maquina_id, prioridad, horas_paro, i))
            else:
                c.execute('UPDATE tareas SET fecha=?, descripcion=?, tags=?, maquina_id=?, prioridad=?, horas_paro=? WHERE id=?', (f, d, t, maquina_id, prioridad, horas_paro, i))
            conn.commit(); conn.close(); return True
        except: return False
    def obtener_tarea_por_id(self, i):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute("SELECT id, fecha, descripcion, tags, usuario_id, COALESCE(usuario_nombre,''), maquina_id, COALESCE(prioridad,'Media'), horas_paro FROM tareas WHERE id=?", (i,))
            return c.fetchone()
        except: return None
    def buscar_tareas_avanzado(self, texto, fecha=None):
        try:
            conn = self.conectar(); c = conn.cursor(); param_texto = f"%{texto}%"
            query = "SELECT id, fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id, COALESCE(prioridad,'Media') FROM tareas WHERE (descripcion LIKE ? OR tags LIKE ?)"
            parametros = [param_texto, param_texto]
            if fecha: query += " AND fecha = ?"; parametros.append(fecha)
            query += " ORDER BY fecha DESC, id DESC"; c.execute(query, parametros); return c.fetchall()
        except: return []
    def obtener_fechas_con_tareas(self):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT DISTINCT fecha FROM tareas'); return [x[0] for x in c.fetchall()]
        except: return []
    def obtener_todas_las_descripciones(self):
        try:
            conn=self.conectar(); c=conn.cursor(); c.execute('SELECT DISTINCT descripcion FROM tareas'); l=[]
            for r in c.fetchall(): t=re.sub(r"\[FOTO:.*?\]","",r[0]).strip().split('\n')[0].replace("[DESDE PENDIENTES] ","").strip(); (l.append(t) if t else None)
            conn.close(); return sorted(list(set(l)))
        except: return []
    def marcar_dia_especial(self,f,t):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('INSERT OR REPLACE INTO dias_especiales (fecha,tipo) VALUES (?,?)',(f,t)); conn.commit(); conn.close(); return True
        except: return False
    def borrar_dia_especial(self,f):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('DELETE FROM dias_especiales WHERE fecha=?',(f,)); conn.commit(); conn.close(); return True
        except: return False
    def obtener_dias_especiales(self):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT fecha,tipo FROM dias_especiales'); return {r[0]:r[1] for r in c.fetchall()}
        except: return {}
    def agregar_pendiente(self, t, d, asignado_a=None, asignado_nombre=None, prioridad="Media", especialidad_id=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('INSERT INTO pendientes (titulo,detalles,asignado_a,asignado_nombre,prioridad,especialidad_id) VALUES (?,?,?,?,?,?)',
                      (t, d, asignado_a, asignado_nombre, prioridad, especialidad_id))
            conn.commit(); conn.close(); return True
        except Exception as e:
            print(f"Error agregar_pendiente: {e}"); return False
    def obtener_pendientes(self):
        """Devuelve (id, titulo, detalles, asignado_a, asignado_nombre, prioridad, especialidad_id)."""
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute("SELECT id,titulo,detalles,asignado_a,COALESCE(asignado_nombre,''),COALESCE(prioridad,'Media'),especialidad_id FROM pendientes ORDER BY id DESC")
            return c.fetchall()
        except: return []
    def asignar_pendiente(self, id_p, asignado_a, asignado_nombre):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE pendientes SET asignado_a=?, asignado_nombre=? WHERE id=?',
                      (asignado_a, asignado_nombre, id_p))
            conn.commit(); conn.close(); return True
        except: return False
    def asignar_especialidad_pendiente(self, id_p, especialidad_id):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE pendientes SET especialidad_id=? WHERE id=?',
                      (especialidad_id, id_p))
            conn.commit(); conn.close(); return True
        except: return False
    def borrar_pendiente(self,i):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('DELETE FROM pendientes WHERE id=?',(i,)); conn.commit(); conn.close(); return True
        except: return False
    def actualizar_pendiente(self, i, t, d, prioridad="Media", especialidad_id=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE pendientes SET titulo=?, detalles=?, prioridad=?, especialidad_id=? WHERE id=?', (t, d, prioridad, especialidad_id, i))
            conn.commit(); conn.close(); return True
        except: return False

class GestorFestivos:
    def __init__(self, db_instance):
        self.db = db_instance
        self.year = datetime.now().year

    def obtener_config_pais(self):
        # Por defecto España, para no romper instalaciones existentes
        return self.db.get_config("country_iso") or "ES"

    def obtener_config_region(self):
        pais = self.obtener_config_pais()
        # Si no hay región guardada y el país es España, mantenemos el valor por defecto histórico (Bizkaia)
        default_prov = "ES-BI" if pais == "ES" else ""
        default_com = "ES-PV" if pais == "ES" else ""
        iso_prov = self.db.get_config("region_iso") or default_prov
        iso_com = self.db.get_config("parent_iso") or default_com
        return iso_prov, iso_com

    def _archivo_cache(self):
        pais = self.obtener_config_pais()
        return os.path.join(DATA_DIR, f"festivos_cache_{pais}_{self.year}.json")

    def _url_api(self):
        pais = self.obtener_config_pais()
        return f"https://date.nager.at/api/v3/publicholidays/{self.year}/{pais}"

    def obtener_festivos(self):
        datos = self.cargar_cache()
        if not datos: datos = self.descargar_festivos()

        l = []
        iso_prov, iso_com = self.obtener_config_region()

        if datos:
            for i in datos:
                counties = i.get('counties')
                # Si no hay provincia/región configurada (país sin desglose), solo festivos nacionales (counties=None)
                if counties is None or (iso_com and iso_com in counties) or (iso_prov and iso_prov in counties):
                    l.append(QDate.fromString(i.get('date'),"yyyy-MM-dd"))
        return l

    def descargar_festivos(self):
        try:
            r = requests.get(self._url_api())
            if r.status_code == 200:
                with open(self._archivo_cache(), 'w') as f: json.dump(r.json(), f)
                return r.json()
        except: return []
        return []

    def cargar_cache(self):
        archivo = self._archivo_cache()
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r') as f: return json.load(f)
            except: return None

        return None

    def obtener_paises_disponibles(self):
        """Devuelve una lista de tuplas (nombre, codigo_iso) de los países soportados por la API, cacheada en disco."""
        archivo = os.path.join(DATA_DIR, "paises_cache.json")
        datos = None
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r') as f: datos = json.load(f)
            except: datos = None
        if not datos:
            try:
                r = requests.get("https://date.nager.at/api/v3/AvailableCountries")
                if r.status_code == 200:
                    datos = r.json()
                    with open(archivo, 'w') as f: json.dump(datos, f)
            except:
                datos = None
        if not datos:
            # Fallback mínimo por si no hay conexión y tampoco hay caché todavía
            datos = [{"countryCode": "ES", "name": "Spain"}]
        return sorted([(d["name"], d["countryCode"]) for d in datos], key=lambda x: x[0])

    def limpiar_cache(self):
        archivo = self._archivo_cache()
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
            except: pass

def _estilo_zona_arrastre(activo=False):
    """Estilo de las zonas de 'arrastra una foto aquí', adaptado al tema actual
    (oscuro/claro/retro), para no quedar siempre en negro en temas claros."""
    oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
    if activo:
        return ("border: 2px dashed #3daee9; background: #333; color: #3daee9;" if oscuro
                else "border: 2px dashed #0078d4; background: #eaf3fb; color: #0078d4;")
    return ("border: 2px dashed #666; color: #888; background: #2b2b2b;" if oscuro
            else "border: 2px dashed #999; color: #666; background: #f0f0f0;")


def _estilo_check_etiqueta():
    """Estilo de los checkboxes de 'Etiquetas rápidas' (Urgente/Eléctrico/...),
    adaptado al tema actual para que el texto no quede gris clarito sobre fondo claro."""
    oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
    return "font-weight: bold; color: #bbb;" if oscuro else "font-weight: bold; color: #555;"


def _estilo_label_dialogo():
    """Estilo de las etiquetas de campo de formularios de diálogo (p.ej. AvisoEditDialog),
    adaptado al tema para que no queden en gris clarito sobre fondo claro."""
    oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
    return f"font-weight: bold; font-size: 14px; color: {'#ccc' if oscuro else '#444'};"


def _poblar_combo_maquinas(combo, seleccion_id=None):
    """Rellena un QComboBox con el árbol de máquinas (indentado por nivel) y una
    primera opción de 'sin máquina', dejando seleccionada la máquina indicada."""
    combo.clear()
    combo.addItem(tt("lbl_sin_maquina", "— Sin máquina —"), None)
    todas = maquinas.listar_maquinas()
    por_padre = {}
    for m in todas:
        por_padre.setdefault(m["padre_id"], []).append(m)

    def anadir(padre_id, nivel):
        for m in por_padre.get(padre_id, []):
            combo.addItem(("    " * nivel) + m["nombre"], m["id"])
            anadir(m["id"], nivel + 1)

    anadir(None, 0)
    idx = combo.findData(seleccion_id)
    if idx >= 0:
        combo.setCurrentIndex(idx)


class LabelArrastrable(QLabel):
    archivo_soltado = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText(t("lbl_arrastra_foto"))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(_estilo_zona_arrastre())
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): self.setStyleSheet(_estilo_zona_arrastre(activo=True)); event.accept()
        else: event.ignore()
    def dragLeaveEvent(self, event): self.setStyleSheet(_estilo_zona_arrastre())
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            ruta = urls[0].toLocalFile()
            if ruta.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')): self.archivo_soltado.emit(ruta)
            else: self.setText(t("lbl_formato_invalido")); self.setStyleSheet("border: 2px dashed red; color: red;")

class DialogoDiasEspeciales(QDialog):
    def __init__(self, db, gestor_festivos, parent=None):
        super().__init__(parent)
        self.db = db
        self.gestor_festivos = gestor_festivos
        self.setWindowTitle(t("title_gestion_dias_especiales"))
        self.resize(500, 400)
        layout = QVBoxLayout()

        # Selector de Fecha y Tipo
        h_top = QHBoxLayout()
        h_top.addWidget(QLabel(t("lbl_fecha")))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        h_top.addWidget(self.date_edit)

        h_top.addWidget(QLabel(t("lbl_tipo")))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems([t("tipo_vacaciones"), t("tipo_puente"), t("tipo_dia_libre"), t("tipo_festivo_manual")])
        h_top.addWidget(self.combo_tipo)

        btn_add = QPushButton(t("btn_anadir"))
        btn_add.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_add.clicked.connect(self.add_dia)
        h_top.addWidget(btn_add)

        layout.addLayout(h_top)

        # Lista de días configurados
        self.lista = QListWidget()
        self.lista.setAlternatingRowColors(True)
        layout.addWidget(self.lista)

        # Botones inferiores
        h_bot = QHBoxLayout()
        btn_del = QPushButton(t("btn_borrar_seleccionado"))
        btn_del.setStyleSheet("background-color: #c0392b; color: white;")
        btn_del.clicked.connect(self.del_dia)
        h_bot.addWidget(btn_del)

        btn_close = QPushButton(t("btn_cerrar"))
        btn_close.clicked.connect(self.accept)
        h_bot.addWidget(btn_close)

        layout.addLayout(h_bot)

        self.setLayout(layout)
        self.refresh_lista()

    def refresh_lista(self):
        self.lista.clear()
        dias = self.db.obtener_dias_especiales()
        # Ordenamos por fecha descendente
        for fecha in sorted(dias.keys(), reverse=True):
            tipo = dias[fecha]
            item = QListWidgetItem(f"📅 {fecha}  ➔  {tipo}")
            item.setData(Qt.ItemDataRole.UserRole, fecha)
            self.lista.addItem(item)

    def add_dia(self):
        f = self.date_edit.date().toString("yyyy-MM-dd")
        t = self.combo_tipo.currentText()
        if self.db.marcar_dia_especial(f, t):
            self.refresh_lista()

    def del_dia(self):
        row = self.lista.currentRow()
        if row >= 0:
            f = self.lista.item(row).data(Qt.ItemDataRole.UserRole)
            if self.db.borrar_dia_especial(f):
                self.refresh_lista()

# ==========================================
# 3. DIÁLOGOS DE INTERFAZ
# ==========================================
class DialogoSeleccionPais(QDialog):
    def __init__(self, gestor_festivos, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(t("title_seleccionar_pais"))
        self.resize(400, 150)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(t("lbl_elige_pais")))
        layout.addWidget(QLabel(t("lbl_nota_espana")))

        self.combo = QComboBox()
        self.paises = gestor_festivos.obtener_paises_disponibles()  # lista de (nombre, iso)
        self.combo.addItems([nombre for nombre, iso in self.paises])

        actual_iso = self.db.get_config("country_iso") or "ES"
        for nombre, iso in self.paises:
            if iso == actual_iso:
                self.combo.setCurrentText(nombre)
                break

        layout.addWidget(self.combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); btns.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)

    def get_selection(self):
        nombre_sel = self.combo.currentText()
        for nombre, iso in self.paises:
            if nombre == nombre_sel:
                return nombre, iso
        return "Spain", "ES"

class DialogoSeleccionRegion(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle(t("title_seleccionar_provincia"))
        self.resize(400, 150)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(t("lbl_elige_provincia")))
        layout.addWidget(QLabel(t("lbl_nota_provincia")))
        self.combo = QComboBox()
        self.nombres_ordenados = sorted(PROVINCIAS_ESPAÑA.keys())
        self.combo.addItems(self.nombres_ordenados)
        actual_iso = self.db.get_config("region_iso") or "ES-BI"
        nombre_actual = "Bizkaia"
        for nombre, datos in PROVINCIAS_ESPAÑA.items():
            if datos["iso"] == actual_iso:
                nombre_actual = nombre
                break
        self.combo.setCurrentText(nombre_actual)
        layout.addWidget(self.combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); btns.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)

    def get_selection(self):
        nombre = self.combo.currentText()
        datos = PROVINCIAS_ESPAÑA.get(nombre)
        return nombre, datos["iso"], datos["parent"]

# ==========================================
# DIÁLOGOS DE STOCK DE ALMACÉN
# ==========================================
class DialogoNuevaEstanteria(QDialog):
    """Alta de una estantería nueva: nombre, número de baldas y si tiene hueco de suelo.
    Si se pasa `estanteria` (el dict que devuelve almacen.listar_estructura()), se abre
    en modo edición con la misma ventana y todos los campos rellenados con los valores
    actuales: se puede cambiar el nombre, el estilo de las baldas, el hueco de suelo y
    subir o bajar el número de baldas (al subir, se añaden por arriba continuando la
    numeración, creando en cada una el número de secciones indicado; al bajar, se
    borran las de numeración más alta, deteniéndose en la primera que tenga material).
    El número de secciones y su estilo solo se aplican a las baldas nuevas que se
    añadan aquí, no a las que ya existían."""
    def __init__(self, parent=None, estanteria=None):
        super().__init__(parent)
        self._editando = estanteria is not None
        self.setWindowTitle(tt("title_editar_estanteria", "Editar estantería") if self._editando
                             else tt("title_nueva_estanteria", "Nueva estantería"))
        self.resize(380, 220)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_nombre_estanteria", "Nombre de la estantería")))
        self.campo_nombre = QLineEdit(); self.campo_nombre.setPlaceholderText(tt("ph_nombre_estanteria", "ej. Estantería A"))
        l.addWidget(self.campo_nombre)
        lbl_num_baldas = QLabel(tt("lbl_num_baldas", "Número de baldas"))
        l.addWidget(lbl_num_baldas)
        self.spin_baldas = QSpinBox(); self.spin_baldas.setRange(1, 30); self.spin_baldas.setValue(3)
        l.addWidget(self.spin_baldas)
        lbl_num_secciones = QLabel(tt("lbl_num_secciones", "Número de secciones por balda"))
        l.addWidget(lbl_num_secciones)
        self.spin_secciones = QSpinBox(); self.spin_secciones.setRange(0, 30); self.spin_secciones.setValue(0)
        self.spin_secciones.setToolTip(tt("tt_num_secciones", "0 = sin secciones predefinidas (se pueden añadir después)"))
        l.addWidget(self.spin_secciones)
        self.chk_hueco_suelo = QCheckBox(tt("txt_hueco_suelo", "Tiene hueco en el suelo (bajo la balda inferior)"))
        l.addWidget(self.chk_hueco_suelo)

        l.addWidget(QLabel(tt("lbl_estilo_baldas", "Numerar las baldas con")))
        self.combo_estilo_baldas = QComboBox()
        self.combo_estilo_baldas.addItem(tt("txt_numeros", "Números (1, 2, 3...)"), "numero")
        self.combo_estilo_baldas.addItem(tt("txt_letras", "Letras (A, B, C...)"), "letra")
        l.addWidget(self.combo_estilo_baldas)

        lbl_estilo_secciones = QLabel(tt("lbl_estilo_secciones", "Nombrar las secciones con"))
        l.addWidget(lbl_estilo_secciones)
        self.combo_estilo_secciones = QComboBox()
        self.combo_estilo_secciones.addItem(tt("txt_letras", "Letras (A, B, C...)"), "letra")
        self.combo_estilo_secciones.addItem(tt("txt_numeros", "Números (1, 2, 3...)"), "numero")
        l.addWidget(self.combo_estilo_secciones)

        if self._editando:
            self.campo_nombre.setText(estanteria["nombre"])
            num_baldas_actual = sum(1 for b in estanteria["baldas"] if b["numero"] != 0)
            self.spin_baldas.setValue(max(1, num_baldas_actual))
            self.chk_hueco_suelo.setChecked(bool(estanteria.get("tiene_hueco_suelo")))
            idx = self.combo_estilo_baldas.findData(estanteria.get("estilo_baldas", "numero"))
            if idx >= 0:
                self.combo_estilo_baldas.setCurrentIndex(idx)
            self.spin_secciones.setValue(0)
            tt_solo_nuevas = tt("tt_solo_baldas_nuevas", "Solo se aplica a las baldas nuevas que se añadan al subir el número de baldas")
            lbl_num_secciones.setToolTip(tt_solo_nuevas)
            self.spin_secciones.setToolTip(tt_solo_nuevas)
            lbl_estilo_secciones.setToolTip(tt_solo_nuevas)
            self.combo_estilo_secciones.setToolTip(tt_solo_nuevas)

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def get_data(self):
        return (self.campo_nombre.text().strip(), self.spin_baldas.value(),
                self.chk_hueco_suelo.isChecked(), self.spin_secciones.value(),
                self.combo_estilo_baldas.currentData(), self.combo_estilo_secciones.currentData())


class DialogoConfigurarAlmacen(QDialog):
    """Gestión de la estructura del almacén: estanterías > baldas > secciones. Solo admin."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_configurar_almacen", "Configurar almacén"))
        self.resize(560, 520)
        l = QVBoxLayout()

        hz = QHBoxLayout()
        hz.addWidget(QLabel(tt("lbl_zona", "Zona")))
        self.combo_zona = QComboBox()
        self.combo_zona.currentIndexChanged.connect(self._cambiar_zona)
        hz.addWidget(self.combo_zona, 1)
        btn_nueva_zona = QPushButton(tt("btn_nueva_zona_almacen", "➕ Nueva zona")); btn_nueva_zona.clicked.connect(self.nueva_zona)
        btn_renombrar_zona = QPushButton(tt("btn_renombrar_zona", "✏️ Renombrar zona")); btn_renombrar_zona.clicked.connect(self.renombrar_zona)
        btn_eliminar_zona = QPushButton(tt("btn_eliminar_zona", "🗑️ Eliminar zona")); btn_eliminar_zona.clicked.connect(self.eliminar_zona)
        hz.addWidget(btn_nueva_zona); hz.addWidget(btn_renombrar_zona); hz.addWidget(btn_eliminar_zona)
        l.addLayout(hz)

        self.arbol = QTreeWidget(); self.arbol.setHeaderHidden(True)
        self.arbol.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.arbol.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.arbol.customContextMenuRequested.connect(self._mostrar_menu_contextual)
        l.addWidget(self.arbol)

        h0 = QHBoxLayout()
        btn_expandir = QPushButton(tt("btn_expandir_todo", "⬇️ Expandir todo")); btn_expandir.clicked.connect(self.arbol.expandAll)
        btn_contraer = QPushButton(tt("btn_contraer_todo", "⬆️ Contraer todo")); btn_contraer.clicked.connect(self.arbol.collapseAll)
        h0.addWidget(btn_expandir); h0.addWidget(btn_contraer)
        l.addLayout(h0)

        h1 = QHBoxLayout()
        btn_add_est = QPushButton(tt("btn_anadir_estanteria", "➕ Añadir estantería")); btn_add_est.clicked.connect(self.anadir_estanteria)
        btn_del_est = QPushButton(tt("btn_eliminar_estanteria", "🗑️ Eliminar estantería")); btn_del_est.clicked.connect(self.eliminar_estanteria)
        h1.addWidget(btn_add_est); h1.addWidget(btn_del_est)
        l.addLayout(h1)

        h2 = QHBoxLayout()
        btn_add_balda = QPushButton(tt("btn_anadir_balda", "➕ Añadir balda")); btn_add_balda.clicked.connect(self.anadir_balda)
        btn_del_balda = QPushButton(tt("btn_eliminar_balda", "🗑️ Eliminar balda")); btn_del_balda.clicked.connect(self.eliminar_balda)
        h2.addWidget(btn_add_balda); h2.addWidget(btn_del_balda)
        l.addLayout(h2)

        h3 = QHBoxLayout()
        btn_add_sec = QPushButton(tt("btn_anadir_seccion", "➕ Añadir sección")); btn_add_sec.clicked.connect(self.anadir_seccion)
        btn_del_sec = QPushButton(tt("btn_eliminar_seccion", "🗑️ Eliminar sección")); btn_del_sec.clicked.connect(self.eliminar_seccion)
        h3.addWidget(btn_add_sec); h3.addWidget(btn_del_sec)
        l.addLayout(h3)

        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept)
        l.addWidget(btn_cerrar)
        self.setLayout(l)
        self._cargar_zonas()

    def _cargar_zonas(self, preferir_id=None):
        """Rellena el desplegable de zonas conservando (o forzando con
        preferir_id) la selección actual, y refresca el árbol para la zona
        que quede seleccionada."""
        zona_previa = preferir_id if preferir_id is not None else self.combo_zona.currentData()
        self._zonas = almacen.listar_zonas()
        self.combo_zona.blockSignals(True)
        self.combo_zona.clear()
        for zona in self._zonas:
            self.combo_zona.addItem(zona["nombre"], zona["id"])
        idx = self.combo_zona.findData(zona_previa)
        self.combo_zona.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_zona.blockSignals(False)
        self.refrescar()

    def _cambiar_zona(self, _idx):
        self.refrescar()

    def nueva_zona(self):
        nombre, ok = QInputDialog.getText(self, tt("title_nueva_zona_almacen", "Nueva zona"), tt("lbl_nombre_zona_almacen", "Nombre de la zona"))
        if ok and nombre.strip():
            zona_id = almacen.crear_zona(nombre.strip())
            self._cargar_zonas(preferir_id=zona_id)

    def renombrar_zona(self):
        zona_id = self.combo_zona.currentData()
        if zona_id is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_zona_requerida", "Selecciona una zona.")); return
        nombre, ok = QInputDialog.getText(self, tt("title_renombrar_zona", "Renombrar zona"),
                                           tt("lbl_nombre_zona_almacen", "Nombre de la zona"), text=self.combo_zona.currentText())
        if ok and nombre.strip():
            almacen.renombrar_zona(zona_id, nombre.strip())
            self._cargar_zonas(preferir_id=zona_id)

    def eliminar_zona(self):
        zona_id = self.combo_zona.currentData()
        if zona_id is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_zona_requerida", "Selecciona una zona.")); return
        nombre_zona = self.combo_zona.currentText()
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "msg_confirmar_eliminar_zona", "¿Eliminar la zona «{nombre}»?").format(nombre=nombre_zona)) != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen.eliminar_zona(zona_id)
        if not ok and error == "contiene_estanterias":
            n = len(almacen.zona_estanterias(zona_id))
            if QMessageBox.warning(self, tt("aviso", "Aviso"), tt(
                    "msg_zona_contiene_estanterias",
                    "Esta zona contiene {n} estantería(s). Si continúas, se eliminarán también esas estanterías y toda su estructura. ¿Continuar?").format(n=n),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            ok, error = almacen.eliminar_zona(zona_id, forzar=True)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_elemento_no_vacio", "No se puede eliminar: todavía contiene material ubicado."))
        self._cargar_zonas()

    def refrescar(self):
        self.arbol.clear()
        # Un color de texto distinto por nivel (estantería/balda/hueco de suelo/sección)
        # para que la jerarquía se distinga de un vistazo, ajustado según el tema activo.
        oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
        col_est = QColor("#5fa8e8") if oscuro else QColor("#0d3862")
        col_balda = QColor("#6fcf7a") if oscuro else QColor("#1e6620")
        col_suelo = QColor("#e0b34d") if oscuro else QColor("#8a6210")
        col_sec = QColor("#c98be0") if oscuro else QColor("#6a2d8a")
        self._estructura = almacen.listar_estructura(self.combo_zona.currentData())
        for est in self._estructura:
            item_est = QTreeWidgetItem([f"🗄️ {est['nombre']}"])
            item_est.setData(0, Qt.ItemDataRole.UserRole, ("estanteria", est["id"]))
            item_est.setForeground(0, col_est)
            for balda in est["baldas"]:
                es_suelo = balda["numero"] == 0
                nombre_balda = tt("txt_hueco_suelo_corto", "Hueco de suelo") if es_suelo else tt(
                    "txt_balda_num", "Balda {n}").format(n=almacen.texto_balda(balda["numero"], est.get("estilo_baldas", "numero")))
                item_balda = QTreeWidgetItem([f"📚 {nombre_balda}"])
                item_balda.setData(0, Qt.ItemDataRole.UserRole, ("balda", balda["id"]))
                item_balda.setForeground(0, col_suelo if es_suelo else col_balda)
                for sec in balda["secciones"]:
                    # Las secciones implícitas (creadas solas al ubicar un
                    # material directamente en la balda, sin elegir sección)
                    # no se muestran aquí: para el usuario ese material está
                    # "en la balda", no en una sección que él haya creado.
                    if sec.get("implicita"):
                        continue
                    item_sec = QTreeWidgetItem([f"📦 {sec['nombre']}"])
                    item_sec.setData(0, Qt.ItemDataRole.UserRole, ("seccion", sec["id"]))
                    item_sec.setForeground(0, col_sec)
                    item_balda.addChild(item_sec)
                item_est.addChild(item_balda)
            self.arbol.addTopLevelItem(item_est)
        self.arbol.expandAll()

    def _seleccion(self):
        item = self.arbol.currentItem()
        if not item: return None, None
        return item.data(0, Qt.ItemDataRole.UserRole)

    def anadir_estanteria(self):
        zona_id = self.combo_zona.currentData()
        if zona_id is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_crea_zona_primero", "Crea antes una zona para poder añadir estanterías.")); return
        dlg = DialogoNuevaEstanteria(self)
        if dlg.exec():
            nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones = dlg.get_data()
            if not nombre:
                QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_nombre_obligatorio", "El nombre es obligatorio.")); return
            almacen.crear_estanteria(nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones, zona_id=zona_id)
            self.refrescar()

    def eliminar_estanteria(self):
        tipo, id_ = self._seleccion()
        if tipo != "estanteria":
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_estanteria_requerida", "Selecciona una estantería.")); return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt("msg_confirmar_eliminar_estanteria", "¿Eliminar esta estantería y toda su estructura?")) != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen.eliminar_estanteria(id_)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_elemento_no_vacio", "No se puede eliminar: todavía contiene material ubicado."))
        self.refrescar()

    def anadir_balda(self):
        tipo, id_ = self._seleccion()
        estanteria_id = None
        item = self.arbol.currentItem()
        if tipo == "estanteria":
            estanteria_id = id_
        elif tipo == "balda":
            estanteria_id = item.parent().data(0, Qt.ItemDataRole.UserRole)[1]
        else:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_estanteria_requerida", "Selecciona una estantería.")); return
        almacen.anadir_balda(estanteria_id)
        self.refrescar()

    def eliminar_balda(self):
        tipo, id_ = self._seleccion()
        if tipo != "balda":
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_balda_requerida", "Selecciona una balda.")); return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt("msg_confirmar_eliminar_balda", "¿Eliminar esta balda y sus secciones?")) != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen.eliminar_balda(id_)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_elemento_no_vacio", "No se puede eliminar: todavía contiene material ubicado."))
        self.refrescar()

    def anadir_seccion(self):
        tipo, id_ = self._seleccion()
        if tipo != "balda":
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_balda_requerida", "Selecciona una balda.")); return
        nombre, ok = QInputDialog.getText(self, tt("title_nueva_seccion", "Nueva sección"), tt("lbl_nombre_seccion", "Nombre de la sección"))
        if ok and nombre.strip():
            almacen.crear_seccion(id_, nombre.strip())
            self.refrescar()

    def eliminar_seccion(self):
        tipo, id_ = self._seleccion()
        if tipo != "seccion":
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_seccion_requerida", "Selecciona una sección.")); return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt("msg_confirmar_eliminar_seccion", "¿Eliminar esta sección?")) != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen.eliminar_seccion(id_)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_elemento_no_vacio", "No se puede eliminar: todavía contiene material ubicado."))
        self.refrescar()

    def _mapa_baldas(self):
        """A partir de self._estructura (rellenada en refrescar), devuelve dos diccionarios:
        {balda_id: estanteria_id} y {balda_id: es_hueco_suelo}, para poder clasificar la
        selección múltiple del árbol sin volver a consultar la base de datos."""
        est_de_balda, es_suelo = {}, {}
        for est in self._estructura:
            for balda in est["baldas"]:
                est_de_balda[balda["id"]] = est["id"]
                es_suelo[balda["id"]] = balda["numero"] == 0
        return est_de_balda, es_suelo

    def _mostrar_menu_contextual(self, pos):
        items = self.arbol.selectedItems()
        if not items:
            return
        est_de_balda, es_suelo = self._mapa_baldas()
        ids_est, ids_balda, ids_suelo = set(), set(), set()
        estanterias_afectadas = set()
        for item in items:
            tipo, id_ = item.data(0, Qt.ItemDataRole.UserRole)
            if tipo == "estanteria":
                ids_est.add(id_)
                estanterias_afectadas.add(id_)
            elif tipo == "balda":
                estanterias_afectadas.add(est_de_balda.get(id_))
                (ids_suelo if es_suelo.get(id_) else ids_balda).add(id_)

        menu = QMenu(self)
        if len(ids_est) == 1:
            id_est = next(iter(ids_est))
            a = menu.addAction(tt("menu_editar_estanteria", "✏️ Editar estantería"))
            a.triggered.connect(lambda: self._editar_estanteria(id_est))
            menu.addSeparator()
        if ids_est:
            a = menu.addAction(tt("menu_borrar_estanterias", "🗑️ Borrar estanterías seleccionadas"))
            a.triggered.connect(lambda: self._borrar_estanterias_multiple(ids_est))
        if ids_balda:
            a = menu.addAction(tt("menu_borrar_baldas", "🗑️ Borrar baldas seleccionadas"))
            a.triggered.connect(lambda: self._borrar_baldas_multiple(ids_balda))
        if ids_suelo:
            a = menu.addAction(tt("menu_borrar_huecos_suelo", "🗑️ Borrar huecos de suelo seleccionados"))
            a.triggered.connect(lambda: self._borrar_baldas_multiple(ids_suelo))
        if estanterias_afectadas:
            if not menu.isEmpty():
                menu.addSeparator()
            a = menu.addAction(tt("menu_cambiar_a_numeros", "🔢 Cambiar baldas a números"))
            a.triggered.connect(lambda: self._cambiar_estilo_multiple(estanterias_afectadas, "numero"))
            a = menu.addAction(tt("menu_cambiar_a_letras", "🔤 Cambiar baldas a letras"))
            a.triggered.connect(lambda: self._cambiar_estilo_multiple(estanterias_afectadas, "letra"))
            menu.addSeparator()
            a = menu.addAction(tt("menu_anadir_baldas", "➕ Añadir balda a cada estantería seleccionada"))
            a.triggered.connect(lambda: self._anadir_baldas_multiple(estanterias_afectadas))
            a = menu.addAction(tt("menu_anadir_huecos_suelo", "➕ Añadir hueco de suelo a cada estantería seleccionada"))
            a.triggered.connect(lambda: self._anadir_huecos_suelo_multiple(estanterias_afectadas))
        if not menu.isEmpty():
            menu.exec(self.arbol.viewport().mapToGlobal(pos))

    def _editar_estanteria(self, estanteria_id):
        est = next((e for e in self._estructura if e["id"] == estanteria_id), None)
        if est is None:
            return
        dlg = DialogoNuevaEstanteria(self, estanteria=est)
        if dlg.exec():
            nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones = dlg.get_data()
            if not nombre:
                QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_nombre_obligatorio", "El nombre es obligatorio.")); return
            no_borradas = almacen.editar_estanteria(
                estanteria_id, nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones)
            if no_borradas:
                QMessageBox.warning(self, tt("aviso", "Aviso"), tt(
                    "msg_baldas_no_borradas", "No se han podido quitar {n} balda(s): todavía contienen material ubicado.").format(n=no_borradas))
            self.refrescar()

    def _borrar_estanterias_multiple(self, ids):
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "msg_confirmar_eliminar_estanterias", "¿Eliminar {n} estantería(s) y toda su estructura?").format(n=len(ids))) != QMessageBox.StandardButton.Yes:
            return
        fallidas = sum(1 for id_ in ids if not almacen.eliminar_estanteria(id_)[0])
        if fallidas:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt(
                "msg_algunas_no_vacias", "{n} elemento(s) no se han podido borrar porque todavía contienen material ubicado.").format(n=fallidas))
        self.refrescar()

    def _borrar_baldas_multiple(self, ids):
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "msg_confirmar_eliminar_baldas", "¿Eliminar {n} elemento(s) seleccionado(s) y sus secciones?").format(n=len(ids))) != QMessageBox.StandardButton.Yes:
            return
        fallidas = sum(1 for id_ in ids if not almacen.eliminar_balda(id_)[0])
        if fallidas:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt(
                "msg_algunas_no_vacias", "{n} elemento(s) no se han podido borrar porque todavía contienen material ubicado.").format(n=fallidas))
        self.refrescar()

    def _cambiar_estilo_multiple(self, estanteria_ids, estilo):
        for id_ in estanteria_ids:
            almacen.cambiar_estilo_baldas(id_, estilo)
        self.refrescar()

    def _anadir_baldas_multiple(self, estanteria_ids):
        for id_ in estanteria_ids:
            almacen.anadir_balda(id_)
        self.refrescar()

    def _anadir_huecos_suelo_multiple(self, estanteria_ids):
        creados = sum(1 for id_ in estanteria_ids if almacen.anadir_hueco_suelo(id_))
        ya_existian = len(estanteria_ids) - creados
        if ya_existian:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt(
                "msg_huecos_suelo_ya_existian", "{n} estantería(s) ya tenían hueco de suelo y no se han modificado.").format(n=ya_existian))
        self.refrescar()


class DialogoSeleccionarUbicacion(QDialog):
    """Elige estantería/balda/sección de destino, sin más datos, para mover uno o varios materiales a la vez."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_mover_material", "Mover a..."))
        self.resize(360, 200)
        l = QVBoxLayout()
        self.combo_estanteria = QComboBox(); self.combo_balda = QComboBox(); self.combo_seccion = QComboBox()
        l.addWidget(QLabel(tt("lbl_estanteria", "Estantería"))); l.addWidget(self.combo_estanteria)
        l.addWidget(QLabel(tt("lbl_balda", "Balda"))); l.addWidget(self.combo_balda)
        l.addWidget(QLabel(tt("lbl_seccion", "Sección"))); l.addWidget(self.combo_seccion)
        self._estructura = almacen.listar_estructura()
        for est in self._estructura:
            self.combo_estanteria.addItem(est["nombre"], est["id"])
        self.combo_estanteria.currentIndexChanged.connect(self._actualizar_baldas)
        self.combo_balda.currentIndexChanged.connect(self._actualizar_secciones)
        self._actualizar_baldas()
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar_aceptar); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def _actualizar_baldas(self):
        self.combo_balda.clear()
        est_id = self.combo_estanteria.currentData()
        est = next((e for e in self._estructura if e["id"] == est_id), None)
        if est:
            for balda in est["baldas"]:
                nombre = tt("txt_hueco_suelo_corto", "Hueco de suelo") if balda["numero"] == 0 else tt(
                    "txt_balda_num", "Balda {n}").format(n=almacen.texto_balda(balda["numero"], est.get("estilo_baldas", "numero")))
                self.combo_balda.addItem(nombre, balda["id"])
        self._actualizar_secciones()

    def _actualizar_secciones(self):
        self.combo_seccion.clear()
        est_id = self.combo_estanteria.currentData()
        balda_id = self.combo_balda.currentData()
        est = next((e for e in self._estructura if e["id"] == est_id), None)
        if est:
            balda = next((b for b in est["baldas"] if b["id"] == balda_id), None)
            if balda:
                for sec in balda["secciones"]:
                    self.combo_seccion.addItem(sec["nombre"], sec["id"])

    def _validar_aceptar(self):
        if self.combo_seccion.currentData() is None:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_selecciona_seccion", "Selecciona una sección del almacén.")); return
        self.accept()

    def get_seccion_id(self):
        return self.combo_seccion.currentData()


class _ItemArbolOrdenable(QTreeWidgetItem):
    """QTreeWidgetItem que, si la columna tiene una clave de orden guardada en
    UserRole+1 (un número o una fecha ISO), la usa para comparar en vez del
    texto mostrado. Así "10" no queda antes que "2" y las fechas se ordenan
    cronológicamente y no alfabéticamente al pulsar la cabecera del árbol."""
    def __lt__(self, otro):
        arbol = self.treeWidget()
        columna = arbol.sortColumn() if arbol else 0
        clave_propia = self.data(columna, Qt.ItemDataRole.UserRole + 1)
        clave_otro = otro.data(columna, Qt.ItemDataRole.UserRole + 1)
        if clave_propia is not None and clave_otro is not None:
            return clave_propia < clave_otro
        return super().__lt__(otro)


class GraficoCircularTrabajos(QWidget):
    """Gráfica circular dibujada a mano con QPainter (sin depender de ninguna
    librería de gráficos externa) que reparte un total de trabajos entre un
    conjunto de etiquetas, con su leyenda de colores al lado."""

    _COLORES = [
        QColor("#3daee9"), QColor("#e67e22"), QColor("#2ecc71"), QColor("#e74c3c"),
        QColor("#9b59b6"), QColor("#f1c40f"), QColor("#1abc9c"), QColor("#95a5a6"),
    ]

    def __init__(self, parent=None, color_texto="#dcdcdc", color_fondo=None):
        super().__init__(parent)
        self._datos = []
        self._color_texto = QColor(color_texto)
        self._color_fondo = QColor(color_fondo) if color_fondo else None
        self.setMinimumHeight(180)

    def establecer_datos(self, datos):
        """datos: lista de tuplas (etiqueta, valor)."""
        self._datos = [(etiqueta, valor) for etiqueta, valor in datos if valor > 0]
        self.update()

    def paintEvent(self, evento):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._color_fondo:
            painter.fillRect(self.rect(), self._color_fondo)
        total = sum(valor for _, valor in self._datos)
        ancho, alto = self.width(), self.height()

        if total == 0:
            painter.setPen(QColor("#888888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                              tt("lbl_sin_trabajos_grafico", "Sin trabajos registrados"))
            return

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


class GraficoBarrasRanking(QWidget):
    """Gráfica de barras horizontales dibujada a mano con QPainter (sin
    depender de ninguna librería de gráficos externa), para un ranking ya
    ordenado de mayor a menor."""

    def __init__(self, parent=None, color="#c0392b", color_texto="#dcdcdc", color_fondo=None):
        super().__init__(parent)
        self._datos = []
        self._color = QColor(color)
        self._color_texto = QColor(color_texto)
        self._color_fondo = QColor(color_fondo) if color_fondo else None
        self.setMinimumHeight(160)

    def establecer_datos(self, datos):
        """datos: lista de tuplas (etiqueta, valor), ya ordenada de mayor a menor."""
        self._datos = datos
        self.update()

    def paintEvent(self, evento):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._color_fondo:
            painter.fillRect(self.rect(), self._color_fondo)
        if not self._datos:
            painter.setPen(QColor("#888888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                              tt("lbl_sin_datos_grafico", "Sin datos"))
            return

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


class GraficoBarrasMensual(QWidget):
    """Gráfica de barras verticales (evolución mes a mes) dibujada a mano con
    QPainter, sin depender de ninguna librería de gráficos externa."""

    def __init__(self, parent=None, color="#c0392b", color_texto="#dcdcdc", color_fondo=None):
        super().__init__(parent)
        self._datos = []
        self._color = QColor(color)
        self._color_texto = QColor(color_texto)
        self._color_fondo = QColor(color_fondo) if color_fondo else None
        self.setMinimumHeight(160)

    def establecer_datos(self, datos):
        """datos: lista de tuplas ('YYYY-MM', valor), en orden cronológico."""
        self._datos = datos
        self.update()

    def paintEvent(self, evento):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._color_fondo:
            painter.fillRect(self.rect(), self._color_fondo)
        if not self._datos or all(valor == 0 for _, valor in self._datos):
            painter.setPen(QColor("#888888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                              tt("lbl_sin_datos_grafico", "Sin datos"))
            return

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


class DialogoEditarMaquina(QDialog):
    """Alta/edición de una máquina del listado de maquinaria."""
    def __init__(self, parent=None, maquina=None, padre_sugerido=None, excluir_ids=None):
        super().__init__(parent)
        self.maquina = maquina
        self.es_nueva = maquina is None
        self.excluir_ids = excluir_ids or set()
        self.ruta_foto_seleccionada = ""
        self.foto_nombre_existente = maquina.get("foto") if maquina else None
        self.setWindowTitle(tt("title_nueva_maquina", "Nueva máquina") if self.es_nueva else tt("title_editar_maquina", "Editar máquina"))
        self.resize(420, 460)
        l = QVBoxLayout()

        l.addWidget(QLabel(tt("lbl_nombre_maquina", "Nombre de la máquina")))
        self.campo_nombre = QLineEdit(maquina["nombre"] if maquina else "")
        l.addWidget(self.campo_nombre)

        l.addWidget(QLabel(tt("lbl_maquina_padre", "Máquina superior (opcional)")))
        self.combo_padre = QComboBox()
        self.combo_padre.addItem(tt("txt_ninguna", "— Ninguna —"), None)
        todas = maquinas.listar_maquinas()
        por_padre = {}
        for m in todas:
            por_padre.setdefault(m["padre_id"], []).append(m)

        def anadir(padre_id, nivel):
            for m in por_padre.get(padre_id, []):
                if m["id"] in self.excluir_ids:
                    continue
                self.combo_padre.addItem(("    " * nivel) + m["nombre"], m["id"])
                anadir(m["id"], nivel + 1)

        anadir(None, 0)
        seleccion = maquina["padre_id"] if maquina else padre_sugerido
        idx = self.combo_padre.findData(seleccion)
        if idx >= 0:
            self.combo_padre.setCurrentIndex(idx)
        l.addWidget(self.combo_padre)

        l.addWidget(QLabel(tt("lbl_zona_maquina", "Zona / Ubicación (opcional)")))
        h_zona = QHBoxLayout()
        self.combo_zona = QComboBox()
        self._recargar_combo_zona(maquina.get("zona_id") if maquina else None)
        h_zona.addWidget(self.combo_zona, 1)
        btn_nueva_zona = QPushButton("➕")
        btn_nueva_zona.setFixedWidth(32)
        btn_nueva_zona.setToolTip(tt("btn_nueva_zona", "Nueva zona"))
        btn_nueva_zona.clicked.connect(self._nueva_zona)
        h_zona.addWidget(btn_nueva_zona)
        l.addLayout(h_zona)

        l.addWidget(QLabel(tt("lbl_notas", "Notas")))
        self.campo_notas = QTextEdit(maquina.get("notas") or "" if maquina else "")
        self.campo_notas.setMaximumHeight(100)
        l.addWidget(self.campo_notas)

        l.addWidget(QLabel(tt("lbl_foto_adjunta", "Foto adjunta")))
        self.lbl_preview = QLabel(tt("lbl_sin_foto", "Sin foto")); self.lbl_preview.setFixedSize(200, 150)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet(_estilo_zona_arrastre())
        h_center = QHBoxLayout(); h_center.addWidget(self.lbl_preview); h_center.addStretch()
        l.addLayout(h_center)
        h_foto = QHBoxLayout()
        btn_cambiar = QPushButton(t("btn_cambiar_foto")); btn_cambiar.clicked.connect(self.seleccionar_foto)
        btn_borrar = QPushButton(t("btn_borrar_foto")); btn_borrar.clicked.connect(self.borrar_foto)
        h_foto.addWidget(btn_cambiar); h_foto.addWidget(btn_borrar)
        l.addLayout(h_foto)

        self._actualizar_preview_inicial()

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar_aceptar); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def _recargar_combo_zona(self, zona_id_seleccionada=None):
        self.combo_zona.clear()
        self.combo_zona.addItem(tt("txt_sin_zona", "— Sin zona —"), None)
        for z in maquinas.listar_zonas():
            self.combo_zona.addItem(z["nombre"], z["id"])
        idx = self.combo_zona.findData(zona_id_seleccionada)
        self.combo_zona.setCurrentIndex(idx if idx >= 0 else 0)

    def _nueva_zona(self):
        nombre, ok = QInputDialog.getText(self, tt("title_nueva_zona", "Nueva zona"), tt("lbl_nombre_zona", "Nombre de la zona"))
        if ok and nombre.strip():
            nuevo_id = maquinas.agregar_zona(nombre.strip())
            self._recargar_combo_zona(nuevo_id)

    def _actualizar_preview_inicial(self):
        if self.foto_nombre_existente:
            carpeta_fotos = self.parent().carpeta_fotos if self.parent() else ""
            ruta = os.path.join(carpeta_fotos, self.foto_nombre_existente)
            if os.path.exists(ruta):
                self.ruta_foto_seleccionada = ruta
                self._refrescar_preview()

    def _refrescar_preview(self):
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada):
            pix = QPixmap(self.ruta_foto_seleccionada)
            if not pix.isNull():
                self.lbl_preview.setPixmap(pix.scaled(self.lbl_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_preview.setStyleSheet("border: 2px solid #3daee9; background-color: #000;")
        else:
            self.lbl_preview.setPixmap(QPixmap()); self.lbl_preview.setText(tt("lbl_sin_foto", "Sin foto"))
            self.lbl_preview.setStyleSheet(_estilo_zona_arrastre())

    def seleccionar_foto(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles():
            self.ruta_foto_seleccionada = dlg.selectedFiles()[0]
            self._refrescar_preview()

    def borrar_foto(self):
        self.ruta_foto_seleccionada = ""
        self.foto_nombre_existente = None
        self._refrescar_preview()

    def _validar_aceptar(self):
        if not self.campo_nombre.text().strip():
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_nombre_maquina_obligatorio", "El nombre de la máquina es obligatorio."))
            return
        self.accept()

    def get_data(self):
        return {
            "nombre": self.campo_nombre.text().strip(),
            "padre_id": self.combo_padre.currentData(),
            "zona_id": self.combo_zona.currentData(),
            "notas": self.campo_notas.toPlainText().strip(),
            "ruta_foto_seleccionada": self.ruta_foto_seleccionada,
            "foto_nombre_existente": self.foto_nombre_existente,
        }


class DialogoEditarMaterial(QDialog):
    """Alta/edición de un material del almacén, con ubicación y foto opcional."""
    def __init__(self, parent=None, material=None):
        super().__init__(parent)
        self.material = material
        self.es_nuevo = material is None
        self.ruta_foto_seleccionada = ""
        self.foto_nombre_existente = material.get("foto") if material else None
        self.setWindowTitle(tt("title_nuevo_material", "Nuevo material") if self.es_nuevo else tt("title_editar_material", "Editar material"))
        self.resize(480, 620)
        l = QVBoxLayout()

        l.addWidget(QLabel(tt("lbl_codigo", "Código (opcional)")))
        self.campo_codigo = QLineEdit(material.get("codigo") or "" if material else "")
        l.addWidget(self.campo_codigo)

        l.addWidget(QLabel(tt("lbl_nombre_material", "Nombre del material")))
        self.campo_nombre = QLineEdit(material.get("nombre") or "" if material else "")
        l.addWidget(self.campo_nombre)

        l.addWidget(QLabel(tt("lbl_descripcion", "Descripción")))
        self.campo_desc = QTextEdit(material.get("descripcion") or "" if material else "")
        self.campo_desc.setMaximumHeight(70)
        l.addWidget(self.campo_desc)

        h_um = QHBoxLayout()
        v1 = QVBoxLayout(); v1.addWidget(QLabel(tt("lbl_unidad", "Unidad")))
        self.campo_unidad = QLineEdit(material.get("unidad") or "" if material else "")
        self.campo_unidad.setPlaceholderText(tt("ph_unidad", "ej. uds, m, kg..."))
        v1.addWidget(self.campo_unidad); h_um.addLayout(v1)
        v2 = QVBoxLayout(); v2.addWidget(QLabel(tt("lbl_stock_minimo", "Stock mínimo")))
        self.spin_minimo = QDoubleSpinBox(); self.spin_minimo.setRange(0, 999999); self.spin_minimo.setDecimals(2)
        self.spin_minimo.setValue(material.get("stock_minimo") or 0 if material else 0)
        v2.addWidget(self.spin_minimo); h_um.addLayout(v2)
        l.addLayout(h_um)

        if self.es_nuevo:
            l.addWidget(QLabel(tt("lbl_stock_inicial", "Stock inicial")))
            self.spin_inicial = QDoubleSpinBox(); self.spin_inicial.setRange(0, 999999); self.spin_inicial.setDecimals(2)
            l.addWidget(self.spin_inicial)

        l.addWidget(QLabel(tt("lbl_ubicacion", "Ubicación")))
        self.combo_estanteria = QComboBox(); self.combo_balda = QComboBox(); self.combo_seccion = QComboBox()
        l.addWidget(QLabel(tt("lbl_estanteria", "Estantería"))); l.addWidget(self.combo_estanteria)
        l.addWidget(QLabel(tt("lbl_balda", "Balda"))); l.addWidget(self.combo_balda)
        l.addWidget(QLabel(tt("lbl_seccion", "Sección"))); l.addWidget(self.combo_seccion)
        self._estructura = almacen.listar_estructura()
        self.combo_estanteria.addItem(tt("txt_sin_ubicacion", "— Sin ubicación —"), None)
        for est in self._estructura:
            self.combo_estanteria.addItem(est["nombre"], est["id"])
        self.combo_estanteria.currentIndexChanged.connect(self._actualizar_baldas)
        self.combo_balda.currentIndexChanged.connect(self._actualizar_secciones)
        self._actualizar_baldas()

        l.addWidget(QLabel(tt("lbl_foto_adjunta", "Foto adjunta")))
        self.lbl_preview = QLabel(tt("lbl_sin_foto", "Sin foto")); self.lbl_preview.setFixedSize(200, 150)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet(_estilo_zona_arrastre())
        h_center = QHBoxLayout(); h_center.addWidget(self.lbl_preview); h_center.addStretch()
        l.addLayout(h_center)
        h_foto = QHBoxLayout()
        btn_cambiar = QPushButton(t("btn_cambiar_foto")); btn_cambiar.clicked.connect(self.seleccionar_foto)
        btn_borrar = QPushButton(t("btn_borrar_foto")); btn_borrar.clicked.connect(self.borrar_foto)
        h_foto.addWidget(btn_cambiar); h_foto.addWidget(btn_borrar)
        l.addLayout(h_foto)

        # Preselección de ubicación si estamos editando
        if material and material.get("seccion_id"):
            self._preseleccionar_ubicacion(material["seccion_id"])

        self._actualizar_preview_inicial()

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar_aceptar); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def _actualizar_baldas(self):
        self.combo_balda.clear()
        est_id = self.combo_estanteria.currentData()
        est = next((e for e in self._estructura if e["id"] == est_id), None)
        if est:
            for balda in est["baldas"]:
                nombre = tt("txt_hueco_suelo_corto", "Hueco de suelo") if balda["numero"] == 0 else tt(
                    "txt_balda_num", "Balda {n}").format(n=almacen.texto_balda(balda["numero"], est.get("estilo_baldas", "numero")))
                self.combo_balda.addItem(nombre, balda["id"])
        self._actualizar_secciones()

    def _actualizar_secciones(self):
        self.combo_seccion.clear()
        est_id = self.combo_estanteria.currentData()
        balda_id = self.combo_balda.currentData()
        est = next((e for e in self._estructura if e["id"] == est_id), None)
        if est:
            balda = next((b for b in est["baldas"] if b["id"] == balda_id), None)
            if balda:
                for sec in balda["secciones"]:
                    self.combo_seccion.addItem(sec["nombre"], sec["id"])

    def _preseleccionar_ubicacion(self, seccion_id):
        for est in self._estructura:
            for balda in est["baldas"]:
                for sec in balda["secciones"]:
                    if sec["id"] == seccion_id:
                        idx_est = self.combo_estanteria.findData(est["id"])
                        if idx_est >= 0: self.combo_estanteria.setCurrentIndex(idx_est)
                        idx_balda = self.combo_balda.findData(balda["id"])
                        if idx_balda >= 0: self.combo_balda.setCurrentIndex(idx_balda)
                        idx_sec = self.combo_seccion.findData(sec["id"])
                        if idx_sec >= 0: self.combo_seccion.setCurrentIndex(idx_sec)
                        return

    def _actualizar_preview_inicial(self):
        if self.foto_nombre_existente:
            carpeta_fotos = self.parent().carpeta_fotos if self.parent() else ""
            ruta = os.path.join(carpeta_fotos, self.foto_nombre_existente)
            if os.path.exists(ruta):
                self.ruta_foto_seleccionada = ruta
                self._refrescar_preview()

    def _refrescar_preview(self):
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada):
            pix = QPixmap(self.ruta_foto_seleccionada)
            if not pix.isNull():
                self.lbl_preview.setPixmap(pix.scaled(self.lbl_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_preview.setStyleSheet("border: 2px solid #3daee9; background-color: #000;")
        else:
            self.lbl_preview.setPixmap(QPixmap()); self.lbl_preview.setText(tt("lbl_sin_foto", "Sin foto"))
            self.lbl_preview.setStyleSheet(_estilo_zona_arrastre())

    def seleccionar_foto(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles():
            self.ruta_foto_seleccionada = dlg.selectedFiles()[0]
            self._refrescar_preview()

    def borrar_foto(self):
        self.ruta_foto_seleccionada = ""
        self.foto_nombre_existente = None
        self._refrescar_preview()

    def _validar_aceptar(self):
        if not self.campo_nombre.text().strip():
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_nombre_material_obligatorio", "El nombre del material es obligatorio."))
            return
        self.accept()

    def get_data(self):
        return {
            "codigo": self.campo_codigo.text().strip(),
            "nombre": self.campo_nombre.text().strip(),
            "descripcion": self.campo_desc.toPlainText().strip(),
            "unidad": self.campo_unidad.text().strip(),
            "stock_minimo": self.spin_minimo.value(),
            "stock_inicial": self.spin_inicial.value() if self.es_nuevo else 0,
            "seccion_id": self.combo_seccion.currentData(),
            "ruta_foto_seleccionada": self.ruta_foto_seleccionada,
            "foto_nombre_existente": self.foto_nombre_existente,
        }


class DialogoMovimientoStock(QDialog):
    """Registro rápido de una entrada o salida de stock para un material."""
    def __init__(self, parent=None, material=None, tipo="entrada"):
        super().__init__(parent)
        self.tipo = tipo
        titulo = tt("title_entrada_stock", "Entrada de stock") if tipo == "entrada" else tt("title_salida_stock", "Salida de stock")
        self.setWindowTitle(titulo)
        self.resize(380, 260)
        l = QVBoxLayout()
        info = QLabel(f"<b>{material['nombre']}</b><br>{tt('lbl_stock_actual', 'Stock actual')}: {material['stock_actual']} {material.get('unidad') or ''}")
        info.setWordWrap(True)
        l.addWidget(info)
        l.addWidget(QLabel(tt("lbl_cantidad", "Cantidad")))
        self.spin_cantidad = QDoubleSpinBox(); self.spin_cantidad.setRange(0.01, 999999); self.spin_cantidad.setDecimals(2); self.spin_cantidad.setValue(1)
        l.addWidget(self.spin_cantidad)
        l.addWidget(QLabel(tt("lbl_motivo", "Motivo (opcional)")))
        self.campo_motivo = QLineEdit()
        ph = tt("ph_motivo_entrada", "ej. Compra, devolución...") if tipo == "entrada" else tt("ph_motivo_salida", "ej. Usado en trabajo...")
        self.campo_motivo.setPlaceholderText(ph)
        l.addWidget(self.campo_motivo)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def get_data(self):
        return self.spin_cantidad.value(), self.campo_motivo.text().strip()


class EditDialog(QDialog):
    def __init__(self, parent=None, fecha="", desc="", tags="", usuario_id=None, usuario_nombre="", maquina_id=None, prioridad="Media", horas_paro=None):
        super().__init__(parent)
        self.carpeta_fotos = parent.carpeta_fotos if parent else ""
        self.foto_filename = None
        self.ref_oculta = ""
        self._usuario_id_original = usuario_id
        self._usuario_nombre_original = usuario_nombre
        self.setWindowTitle(t("title_editar_registro"))
        self.resize(600, 650)
        l = QVBoxLayout()
        self.de = QDateEdit(); self.de.setDate(QDate.fromString(fecha, "yyyy-MM-dd")); self.de.setCalendarPopup(True); self.de.setDisplayFormat("yyyy-MM-dd")
        l.addWidget(QLabel(t("lbl_fecha"))); l.addWidget(self.de)

        # --- Combo de técnico (solo editable por admin) ---
        fila_autor = QHBoxLayout()
        fila_autor.addWidget(QLabel(tt("hdr_realizado_por", "Realizado por") + ":"))
        self.combo_autor = QComboBox()
        self.combo_autor.addItem(usuarios.ETIQUETA_HISTORICO, None)
        for u in usuarios.listar_usuarios(incluir_inactivos=True):
            self.combo_autor.addItem(u["nombre"], u["id"])
        idx = self.combo_autor.findData(usuario_id)
        if idx >= 0:
            self.combo_autor.setCurrentIndex(idx)
        elif usuario_nombre:
            idx_nombre = self.combo_autor.findText(usuario_nombre)
            if idx_nombre >= 0: self.combo_autor.setCurrentIndex(idx_nombre)
        if not usuarios.es_admin():
            self.combo_autor.setEnabled(False)
            self.combo_autor.setToolTip(tt("msg_solo_admin_autor", "Solo un administrador puede cambiar el autor"))
        fila_autor.addWidget(self.combo_autor, 1)
        l.addLayout(fila_autor)

        # --- Combo de máquina vinculada ---
        fila_maquina = QHBoxLayout()
        fila_maquina.addWidget(QLabel(tt("lbl_maquina", "Máquina") + ":"))
        self.combo_maquina = QComboBox()
        _poblar_combo_maquinas(self.combo_maquina, maquina_id)
        fila_maquina.addWidget(self.combo_maquina, 1)
        l.addLayout(fila_maquina)

        texto_limpio, nombre_foto, nombre_foto_d, ref_encontrada = self.separar_datos(desc)
        self.foto_filename = nombre_foto
        self.foto_despues_filename = nombre_foto_d
        self.ref_oculta = ref_encontrada
        self.te = QTextEdit(); self.te.setText(texto_limpio)
        l.addWidget(QLabel(t("lbl_descripcion"))); l.addWidget(self.te)

        l.addWidget(QLabel(t("lbl_fotos_antes_despues")))
        h_fotos = QHBoxLayout()
        v_antes = QVBoxLayout(); v_antes.addWidget(QLabel(t("lbl_antes")))
        self.lbl_foto = LabelArrastrable(); self.lbl_foto.setFixedHeight(150); self.lbl_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_foto.mousePressEvent = self.abrir_o_buscar; self.lbl_foto.archivo_soltado.connect(self.procesar_nueva_foto)
        v_antes.addWidget(self.lbl_foto)
        h_btns_a = QHBoxLayout()
        btn_foto = QPushButton(t("btn_cambiar_foto")); btn_foto.clicked.connect(self.seleccionar_foto_boton); h_btns_a.addWidget(btn_foto)
        btn_borrar_a = QPushButton(t("btn_borrar_foto")); btn_borrar_a.setStyleSheet("background-color: #c0392b; color: white;"); btn_borrar_a.clicked.connect(self.borrar_foto_antes); h_btns_a.addWidget(btn_borrar_a)
        v_antes.addLayout(h_btns_a)
        h_fotos.addLayout(v_antes)

        v_despues = QVBoxLayout(); v_despues.addWidget(QLabel(t("lbl_despues")))
        self.lbl_foto_d = LabelArrastrable(); self.lbl_foto_d.setFixedHeight(150); self.lbl_foto_d.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_foto_d.mousePressEvent = self.abrir_o_buscar_d; self.lbl_foto_d.archivo_soltado.connect(self.procesar_nueva_foto_d)
        v_despues.addWidget(self.lbl_foto_d)
        h_btns_d = QHBoxLayout()
        btn_foto_d = QPushButton(t("btn_cambiar_foto")); btn_foto_d.clicked.connect(self.seleccionar_foto_boton_d); h_btns_d.addWidget(btn_foto_d)
        btn_borrar_d = QPushButton(t("btn_borrar_foto")); btn_borrar_d.setStyleSheet("background-color: #c0392b; color: white;"); btn_borrar_d.clicked.connect(self.borrar_foto_despues); h_btns_d.addWidget(btn_borrar_d)
        v_despues.addLayout(h_btns_d)
        h_fotos.addLayout(v_despues)

        l.addLayout(h_fotos)
        self.actualizar_vista_foto()
        l.addWidget(QLabel(t("lbl_etiquetas")))
        h_tags = QHBoxLayout()
        self.chk_urgente = QCheckBox(t("tag_urgente")); self.chk_electrico = QCheckBox(t("tag_electrico"))
        self.chk_mecanico = QCheckBox(t("tag_mecanico")); self.chk_prev = QCheckBox(t("tag_preventivo"))
        self.chk_averia = QCheckBox(tt("tag_averia", "Avería"))
        lista_actual = [t.strip().lower() for t in tags.split(',')]
        def check_and_clean(texto_check, chk_box):
            if texto_check.lower() in lista_actual:
                chk_box.setChecked(True)
                while texto_check.lower() in lista_actual: lista_actual.remove(texto_check.lower())
        check_and_clean("urgente", self.chk_urgente); check_and_clean("eléctrico", self.chk_electrico)
        if "electrico" in lista_actual: self.chk_electrico.setChecked(True); lista_actual.remove("electrico")
        check_and_clean("mecánico", self.chk_mecanico)
        if "mecanico" in lista_actual: self.chk_mecanico.setChecked(True); lista_actual.remove("mecanico")
        check_and_clean("preventivo", self.chk_prev)
        check_and_clean("avería", self.chk_averia)
        if "averia" in lista_actual: self.chk_averia.setChecked(True); lista_actual.remove("averia")
        h_tags.addWidget(self.chk_urgente); h_tags.addWidget(self.chk_electrico)
        h_tags.addWidget(self.chk_mecanico); h_tags.addWidget(self.chk_prev); h_tags.addWidget(self.chk_averia)
        l.addLayout(h_tags)
        texto_manual = ", ".join([x for x in tags.split(',') if x.strip().lower() in lista_actual])
        self.tag = QLineEdit(); self.tag.setText(texto_manual); self.tag.setPlaceholderText(t("ph_otros_tags"))
        l.addWidget(self.tag)

        # --- Prioridad y horas de parada (para MTBF/MTTR) ---
        fila_prioridad = QHBoxLayout()
        fila_prioridad.addWidget(QLabel(tt("lbl_prioridad", "Prioridad") + ":"))
        self.combo_prioridad = QComboBox()
        for cod, clave in (("Baja", "prioridad_baja"), ("Media", "prioridad_media"), ("Alta", "prioridad_alta"), ("Crítica", "prioridad_critica")):
            self.combo_prioridad.addItem(tt(clave, cod), cod)
        idx_prio = self.combo_prioridad.findData(prioridad or "Media")
        self.combo_prioridad.setCurrentIndex(idx_prio if idx_prio >= 0 else 1)
        fila_prioridad.addWidget(self.combo_prioridad, 1)
        fila_prioridad.addWidget(QLabel(tt("lbl_horas_paro", "Horas de parada (si es avería)") + ":"))
        self.spin_horas_paro = QDoubleSpinBox(); self.spin_horas_paro.setRange(0, 999); self.spin_horas_paro.setDecimals(1)
        self.spin_horas_paro.setSuffix(" h"); self.spin_horas_paro.setEnabled(self.chk_averia.isChecked())
        if horas_paro is not None: self.spin_horas_paro.setValue(horas_paro)
        self.chk_averia.toggled.connect(self.spin_horas_paro.setEnabled)
        fila_prioridad.addWidget(self.spin_horas_paro)
        l.addLayout(fila_prioridad)

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def separar_datos(self, texto):
        ref = ""; m_ref = re.search(r"\[REF:\s*(\d+)\]", texto)
        if m_ref: ref = m_ref.group(0); texto = re.sub(r"\[REF:.*?\]", "", texto)
        foto = None; m_foto = re.search(r"\[FOTO:\s*(.*?)\]", texto)
        if m_foto: foto = m_foto.group(1).strip().split("]")[0]; texto = re.sub(r"\[FOTO:.*?\]", "", texto)
        foto_d = None; m_foto_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", texto)
        if m_foto_d: foto_d = m_foto_d.group(1).strip().split("]")[0]; texto = re.sub(r"\[FOTO_DESPUES:.*?\]", "", texto)
        return texto.strip(), foto, foto_d, ref
    def actualizar_vista_foto(self):
        if self.foto_filename:
            ruta = os.path.join(self.carpeta_fotos, self.foto_filename)
            if os.path.exists(ruta):
                self.lbl_foto.setPixmap(QPixmap(ruta).scaled(self.lbl_foto.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_foto.setStyleSheet("border: 2px solid #3daee9;")
            else: self.lbl_foto.setText(f"Error: {self.foto_filename}")
        else: self.lbl_foto.setText(t("lbl_arrastra_click")); self.lbl_foto.setStyleSheet(_estilo_zona_arrastre())

        if hasattr(self, 'foto_despues_filename') and self.foto_despues_filename:
            ruta_d = os.path.join(self.carpeta_fotos, self.foto_despues_filename)
            if os.path.exists(ruta_d):
                self.lbl_foto_d.setPixmap(QPixmap(ruta_d).scaled(self.lbl_foto_d.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_foto_d.setStyleSheet("border: 2px solid #2ecc71;")
            else: self.lbl_foto_d.setText(f"Error: {self.foto_despues_filename}")
        else: self.lbl_foto_d.setText(t("lbl_arrastra_click")); self.lbl_foto_d.setStyleSheet(_estilo_zona_arrastre())

    def abrir_o_buscar(self, event):
        if self.foto_filename and os.path.exists(os.path.join(self.carpeta_fotos, self.foto_filename)): VisorFoto(os.path.join(self.carpeta_fotos, self.foto_filename), self).exec()
        else: self.seleccionar_foto_boton()
    def seleccionar_foto_boton(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles(): self.procesar_nueva_foto(dlg.selectedFiles()[0])
    def procesar_nueva_foto(self, ruta_origen):
        try:
            nuevo = f"pc_drag_{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(ruta_origen)[1]}"; destino = os.path.join(self.carpeta_fotos, nuevo)
            shutil.copy2(ruta_origen, destino); self.foto_filename = nuevo; self.actualizar_vista_foto()
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))

    def abrir_o_buscar_d(self, event):
        if hasattr(self, 'foto_despues_filename') and self.foto_despues_filename and os.path.exists(os.path.join(self.carpeta_fotos, self.foto_despues_filename)): VisorFoto(os.path.join(self.carpeta_fotos, self.foto_despues_filename), self).exec()
        else: self.seleccionar_foto_boton_d()
    def seleccionar_foto_boton_d(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles(): self.procesar_nueva_foto_d(dlg.selectedFiles()[0])
    def procesar_nueva_foto_d(self, ruta_origen):
        try:
            nuevo = f"pc_drag_d_{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(ruta_origen)[1]}"; destino = os.path.join(self.carpeta_fotos, nuevo)
            shutil.copy2(ruta_origen, destino); self.foto_despues_filename = nuevo; self.actualizar_vista_foto()
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))
    def borrar_foto_antes(self):
        self.foto_filename = None; self.actualizar_vista_foto()
    def borrar_foto_despues(self):
        self.foto_despues_filename = None; self.actualizar_vista_foto()
    def get_data(self):
        d = self.te.toPlainText().strip()
        if self.ref_oculta: d += f" {self.ref_oculta}"
        if self.foto_filename: d += f"\n[FOTO: {self.foto_filename}]"
        if hasattr(self, 'foto_despues_filename') and self.foto_despues_filename: d += f"\n[FOTO_DESPUES: {self.foto_despues_filename}]"
        final_tags = []
        if self.chk_urgente.isChecked(): final_tags.append("Urgente")
        if self.chk_electrico.isChecked(): final_tags.append("Eléctrico")
        if self.chk_mecanico.isChecked(): final_tags.append("Mecánico")
        if self.chk_prev.isChecked(): final_tags.append("Preventivo")
        if self.chk_averia.isChecked(): final_tags.append("Avería")
        manual = self.tag.text().strip()
        if manual: final_tags.append(manual)
        usuario_id = self.combo_autor.currentData()
        usuario_nombre = self.combo_autor.currentText() if usuario_id is not None else usuarios.ETIQUETA_HISTORICO
        maquina_id = self.combo_maquina.currentData()
        prioridad = self.combo_prioridad.currentData()
        horas_paro = self.spin_horas_paro.value() if self.chk_averia.isChecked() else None
        return (self.de.date().toString("yyyy-MM-dd"), d, ", ".join(final_tags), usuario_id, usuario_nombre, maquina_id, prioridad, horas_paro)

class DialogoEditarPendiente(QDialog):
    def __init__(self, parent=None, titulo="", detalles="", ruta_foto="", prioridad="Media", asignado_a=None, especialidad_id=None):
        super().__init__(parent)
        self.setWindowTitle(t("title_editar_tarea_pendiente"))
        self.resize(550, 700)
        self.ruta_foto_seleccionada = ruta_foto
        l = QVBoxLayout()
        l.addWidget(QLabel(t("lbl_titulo"))); self.t = QLineEdit(titulo); l.addWidget(self.t)
        l.addWidget(QLabel(t("lbl_detalles"))); self.d = QTextEdit(); self.d.setText(detalles); self.d.setMaximumHeight(100); l.addWidget(self.d)
        fila_prioridad = QHBoxLayout()
        fila_prioridad.addWidget(QLabel(tt("lbl_prioridad", "Prioridad") + ":"))
        self.combo_prioridad = QComboBox()
        for cod, clave in (("Baja", "prioridad_baja"), ("Media", "prioridad_media"), ("Alta", "prioridad_alta"), ("Crítica", "prioridad_critica")):
            self.combo_prioridad.addItem(tt(clave, cod), cod)
        idx_prio = self.combo_prioridad.findData(prioridad or "Media")
        self.combo_prioridad.setCurrentIndex(idx_prio if idx_prio >= 0 else 1)
        fila_prioridad.addWidget(self.combo_prioridad, 1)
        l.addLayout(fila_prioridad)
        fila_asig = QHBoxLayout()
        fila_asig.addWidget(QLabel(tt("lbl_asignar_a", "Asignar a") + ":"))
        self.combo_asignar = QComboBox()
        if parent is not None and hasattr(parent, "_llenar_combo_usuarios"):
            parent._llenar_combo_usuarios(self.combo_asignar, incluir_sin_asignar=True)
        idx_asig = self.combo_asignar.findData(asignado_a)
        self.combo_asignar.setCurrentIndex(idx_asig if idx_asig >= 0 else 0)
        fila_asig.addWidget(self.combo_asignar, 1)
        l.addLayout(fila_asig)
        fila_especialidad = QHBoxLayout()
        fila_especialidad.addWidget(QLabel(tt("usuarios_col_especialidad", "Especialidad") + ":"))
        self.combo_especialidad = QComboBox()
        if parent is not None and hasattr(parent, "_llenar_combo_especialidades"):
            parent._llenar_combo_especialidades(self.combo_especialidad)
        idx_esp = self.combo_especialidad.findData(especialidad_id)
        self.combo_especialidad.setCurrentIndex(idx_esp if idx_esp >= 0 else 0)
        fila_especialidad.addWidget(self.combo_especialidad, 1)
        l.addLayout(fila_especialidad)
        # Un técnico solo puede fijar la asignación/especialidad al CREAR un
        # trabajo; modificarlas en uno ya existente es cosa exclusiva de admin.
        if not usuarios.es_admin():
            self.combo_asignar.setEnabled(False)
            self.combo_especialidad.setEnabled(False)
        l.addWidget(QLabel(t("lbl_foto_adjunta")))
        self.lbl_preview = LabelArrastrable(); self.lbl_preview.setFixedSize(400, 300)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.archivo_soltado.connect(self.procesar_foto_arrastrada)
        h_center = QHBoxLayout(); h_center.addStretch(); h_center.addWidget(self.lbl_preview); h_center.addStretch(); l.addLayout(h_center)
        h_btns = QHBoxLayout(); self.lbl_nombre = QLabel(""); self.lbl_nombre.setStyleSheet("color: #777; font-size: 10px;"); h_btns.addWidget(self.lbl_nombre); h_btns.addStretch()
        btn_ver = QPushButton(t("btn_ver_grande")); btn_ver.clicked.connect(self.ver_grande); h_btns.addWidget(btn_ver)
        btn_cambiar = QPushButton(t("btn_cambiar_foto")); btn_cambiar.clicked.connect(self.seleccionar_foto); h_btns.addWidget(btn_cambiar)
        btn_borrar = QPushButton(t("btn_borrar_foto")); btn_borrar.setStyleSheet("background-color: #c0392b; color: white;"); btn_borrar.clicked.connect(self.borrar_foto); h_btns.addWidget(btn_borrar)
        l.addLayout(h_btns)
        self.actualizar_vista_foto()
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar")); b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addWidget(b); self.setLayout(l)
    def actualizar_vista_foto(self):
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada):
            pix = QPixmap(self.ruta_foto_seleccionada)
            if not pix.isNull():
                self.lbl_preview.setPixmap(pix.scaled(self.lbl_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_preview.setStyleSheet("border: 2px solid #3daee9; background-color: #000;")
                self.lbl_nombre.setText(os.path.basename(self.ruta_foto_seleccionada))
            else: self.lbl_preview.setText("❌ Error de imagen"); self.lbl_preview.setStyleSheet("border: 2px dashed red;")
        else: self.lbl_preview.setPixmap(QPixmap()); self.lbl_preview.setText("Sin Foto Asignada"); self.lbl_preview.setStyleSheet("border: 2px dashed #555; color: #777;"); self.lbl_nombre.setText("")
    def seleccionar_foto(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles(): self.ruta_foto_seleccionada = dlg.selectedFiles()[0]; self.actualizar_vista_foto()
    def procesar_foto_arrastrada(self, ruta):
        self.ruta_foto_seleccionada = ruta; self.actualizar_vista_foto()
    def ver_grande(self):
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada): VisorFoto(self.ruta_foto_seleccionada, self).exec()
    def borrar_foto(self):
        self.ruta_foto_seleccionada = ""; self.actualizar_vista_foto()
    def get_data(self):
        uid = self.combo_asignar.currentData()
        nombre = self.combo_asignar.currentText() if uid is not None else None
        especialidad_id = self.combo_especialidad.currentData()
        return (self.t.text().strip(), self.d.toPlainText().strip(), self.ruta_foto_seleccionada,
                self.combo_prioridad.currentData(), uid, nombre, especialidad_id)

class CompleteDialog(QDialog):
    def __init__(self, parent=None, titulo="", detalles=""):
        super().__init__(parent)
        self.carpeta_fotos = parent.carpeta_fotos if parent else ""
        self.foto_filename = None
        self.setWindowTitle(f"Completar: {titulo}"); self.resize(500, 550); l = QVBoxLayout()
        oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
        lbl_info = QLabel(f"<b>Trabajo:</b> {titulo}<br><i>{detalles}</i>"); lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("background-color: #333; padding: 10px; border-radius: 5px; color: #eee;" if oscuro
                                else "background-color: #eee; padding: 10px; border-radius: 5px; color: #333;")
        l.addWidget(lbl_info)
        l.addWidget(QLabel(t("lbl_fecha_finalizacion"))); self.de = QDateEdit(); self.de.setDate(QDate.currentDate()); self.de.setCalendarPopup(True); self.de.setDisplayFormat("yyyy-MM-dd"); l.addWidget(self.de)
        self.lbl_foto = LabelArrastrable(); self.lbl_foto.setFixedHeight(180); self.lbl_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_foto.mousePressEvent = self.click_foto; self.lbl_foto.archivo_soltado.connect(self.procesar_foto); l.addWidget(self.lbl_foto)
        btn = QPushButton(t("btn_buscar_foto_manual")); btn.clicked.connect(self.buscar_foto); l.addWidget(btn)
        l.addWidget(QLabel(t("lbl_etiquetas_rapidas"))); h_tags = QHBoxLayout()
        self.chk_urgente = QCheckBox(t("tag_urgente")); self.chk_electrico = QCheckBox(t("tag_electrico"))
        self.chk_mecanico = QCheckBox(t("tag_mecanico")); self.chk_prev = QCheckBox(t("tag_preventivo"))
        for c in [self.chk_urgente, self.chk_electrico, self.chk_mecanico, self.chk_prev]: c.setStyleSheet(_estilo_check_etiqueta()); h_tags.addWidget(c)
        l.addLayout(h_tags)
        l.addWidget(QLabel(t("lbl_otros_tags"))); self.tag = QLineEdit(); self.tag.setPlaceholderText(t("ph_ejemplo_tags")); l.addWidget(self.tag)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar")); b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addWidget(b); self.setLayout(l)
    def click_foto(self, e):
        if self.foto_filename:
            ruta = os.path.join(self.carpeta_fotos, self.foto_filename)
            if os.path.exists(ruta): VisorFoto(ruta, self).exec()
        else: self.buscar_foto()
    def buscar_foto(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles(): self.procesar_foto(dlg.selectedFiles()[0])
    def procesar_foto(self, ruta):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S"); ext = os.path.splitext(ruta)[1]
            nuevo = f"pc_complete_{ts}{ext}"; dest = os.path.join(self.carpeta_fotos, nuevo)
            shutil.copy2(ruta, dest); self.foto_filename = nuevo
            self.lbl_foto.setPixmap(QPixmap(dest).scaled(self.lbl_foto.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_foto.setStyleSheet("border: 2px solid #3daee9;")
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))
    def get_data(self):
        lista_tags = []
        if self.chk_urgente.isChecked(): lista_tags.append("Urgente")
        if self.chk_electrico.isChecked(): lista_tags.append("Eléctrico")
        if self.chk_mecanico.isChecked(): lista_tags.append("Mecánico")
        if self.chk_prev.isChecked(): lista_tags.append("Preventivo")
        manual = self.tag.text().strip(); (lista_tags.append(manual) if manual else None)
        return (self.de.date().toString("yyyy-MM-dd"), ", ".join(lista_tags), self.foto_filename)

class AvisoEditDialog(QDialog):
    def __init__(self, parent=None, titulo="", inicio="", freq="", duracion=1, asignado_a=None, especialidad_id=None):
        super().__init__(parent)
        self.setWindowTitle(t("title_editar_aviso")); self.resize(500, 500)
        l = QVBoxLayout(); l.setSpacing(15); l.setContentsMargins(20, 20, 20, 20); lbl_style = _estilo_label_dialogo()
        l.addWidget(QLabel(t("lbl_titulo_aviso"), styleSheet=lbl_style)); self.titulo = QLineEdit(titulo); self.titulo.setMinimumHeight(35); l.addWidget(self.titulo)
        l.addWidget(QLabel(t("lbl_fecha_inicio"), styleSheet=lbl_style)); self.inicio = QDateEdit(); self.inicio.setCalendarPopup(True); self.inicio.setDisplayFormat("yyyy-MM-dd"); self.inicio.setMinimumHeight(35)
        if inicio: self.inicio.setDate(QDate.fromString(inicio, "yyyy-MM-dd"))
        else: self.inicio.setDate(QDate.currentDate())
        l.addWidget(self.inicio)
        l.addWidget(QLabel(t("lbl_frecuencia_repeticion"), styleSheet=lbl_style)); self.freq = QComboBox(); self.freq.addItems([t("freq_anual"), t("freq_semestral"), t("freq_trimestral"), t("freq_mensual"), t("freq_semanal"), t("freq_diario")])
        self.freq.setCurrentText(freq if freq else "Anual"); self.freq.setMinimumHeight(35); l.addWidget(self.freq)
        l.addWidget(QLabel(t("lbl_dias_margen"), styleSheet=lbl_style)); self.dur = QSpinBox(); self.dur.setRange(1, 365); self.dur.setValue(int(duracion)); self.dur.setMinimumHeight(35); l.addWidget(self.dur)
        l.addWidget(QLabel(tt("lbl_asignar_a", "Asignar a") + ":", styleSheet=lbl_style)); self.combo_asignar = QComboBox(); self.combo_asignar.setMinimumHeight(35)
        if parent is not None and hasattr(parent, "_llenar_combo_usuarios"):
            parent._llenar_combo_usuarios(self.combo_asignar, incluir_sin_asignar=True)
        idx = self.combo_asignar.findData(asignado_a)
        self.combo_asignar.setCurrentIndex(idx if idx >= 0 else 0)
        l.addWidget(self.combo_asignar)
        l.addWidget(QLabel(tt("usuarios_col_especialidad", "Especialidad") + ":", styleSheet=lbl_style)); self.combo_especialidad = QComboBox(); self.combo_especialidad.setMinimumHeight(35)
        if parent is not None and hasattr(parent, "_llenar_combo_especialidades"):
            parent._llenar_combo_especialidades(self.combo_especialidad)
        idx_e = self.combo_especialidad.findData(especialidad_id)
        self.combo_especialidad.setCurrentIndex(idx_e if idx_e >= 0 else 0)
        l.addWidget(self.combo_especialidad)
        l.addStretch()
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        for btn in b.buttons(): btn.setMinimumHeight(40); btn.setStyleSheet("font-size: 14px;")
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addWidget(b); self.setLayout(l)
    def get_data(self):
        uid = self.combo_asignar.currentData()
        nombre = self.combo_asignar.currentText() if uid is not None else None
        especialidad_id = self.combo_especialidad.currentData()
        return (self.titulo.text(), self.inicio.date().toString("yyyy-MM-dd"), self.freq.currentText(), self.dur.value(), uid, nombre, especialidad_id)

class DialogoExportarPDF(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("title_exportar_pdf"))
        self.resize(400, 270)
        l = QVBoxLayout()
        g = QGroupBox(t("lbl_opciones_exportacion")); gl = QVBoxLayout()

        self.rb_todo = QRadioButton(t("lbl_exportar_todo")); self.rb_todo.setChecked(True); self.rb_todo.toggled.connect(self.toggle_fechas); gl.addWidget(self.rb_todo)

        # Nueva opción por meses
        texto_meses = t("lbl_exportar_por_mes") if t("lbl_exportar_por_mes") != "lbl_exportar_por_mes" else "Exportar un PDF por mes"
        self.rb_meses = QRadioButton(texto_meses); self.rb_meses.toggled.connect(self.toggle_fechas); gl.addWidget(self.rb_meses)

        self.rb_rango = QRadioButton(t("lbl_exportar_rango")); gl.addWidget(self.rb_rango)

        h = QHBoxLayout()
        self.d_inicio = QDateEdit(QDate.currentDate().addMonths(-1)); self.d_inicio.setCalendarPopup(True); self.d_inicio.setDisplayFormat("yyyy-MM-dd"); self.d_inicio.setEnabled(False)
        self.d_fin = QDateEdit(QDate.currentDate()); self.d_fin.setCalendarPopup(True); self.d_fin.setDisplayFormat("yyyy-MM-dd"); self.d_fin.setEnabled(False)

        h.addWidget(QLabel(t("lbl_de"))); h.addWidget(self.d_inicio); h.addWidget(QLabel(t("lbl_a"))); h.addWidget(self.d_fin)
        gl.addLayout(h); gl.addSpacing(10)

        fila_u = QHBoxLayout()
        fila_u.addWidget(QLabel(tt("hdr_realizado_por", "Realizado por") + ":"))
        self.combo_usuario = QComboBox()
        self.combo_usuario.addItem(tt("filtro_todos", "Todos"), "TODOS")
        try:
            for u in usuarios.listar_usuarios():
                self.combo_usuario.addItem(u["nombre"], u["nombre"])
            self.combo_usuario.addItem(usuarios.ETIQUETA_HISTORICO, usuarios.ETIQUETA_HISTORICO)
        except Exception:
            pass
        fila_u.addWidget(self.combo_usuario, 1)
        gl.addLayout(fila_u)

        self.chk_graficos = QCheckBox(tt("chk_incluir_graficos_pdf", "Incluir página de gráficos y estadísticas"))
        self.chk_graficos.setChecked(True)
        gl.addWidget(self.chk_graficos)

        g.setLayout(gl); l.addWidget(g)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def toggle_fechas(self):
        estado = self.rb_rango.isChecked()
        self.d_inicio.setEnabled(estado)
        self.d_fin.setEnabled(estado)

    def get_data(self):
        usuario = self.combo_usuario.currentData()
        if usuario == "TODOS": usuario = None
        incluir_graficos = self.chk_graficos.isChecked()
        if self.rb_todo.isChecked():
            return "TODO", None, None, usuario, incluir_graficos
        elif self.rb_meses.isChecked():
            return "MESES", None, None, usuario, incluir_graficos
        else:
            return ("RANGO", self.d_inicio.date().toString("yyyy-MM-dd"),
                    self.d_fin.date().toString("yyyy-MM-dd"), usuario, incluir_graficos)

class DialogoFiltroTecnico(QDialog):
    def __init__(self, parent=None, titulo=None):
        super().__init__(parent)
        self.setWindowTitle(titulo or tt("title_filtrar_tecnico", "Filtrar por Técnico"))
        l = QVBoxLayout()
        fila = QHBoxLayout()
        fila.addWidget(QLabel(tt("hdr_realizado_por", "Realizado por") + ":"))
        self.combo_usuario = QComboBox()
        self.combo_usuario.addItem(tt("filtro_todos", "Todos"), "TODOS")
        try:
            for u in usuarios.listar_usuarios():
                self.combo_usuario.addItem(u["nombre"], u["nombre"])
            self.combo_usuario.addItem(usuarios.ETIQUETA_HISTORICO, usuarios.ETIQUETA_HISTORICO)
        except Exception:
            pass
        fila.addWidget(self.combo_usuario, 1)
        l.addLayout(fila)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def get_filtro(self):
        usuario = self.combo_usuario.currentData()
        return None if usuario == "TODOS" else usuario

def traducir_tags_bd(tags_bd):
    traducciones = {
        "Urgente": t("tag_urgente"),
        "Eléctrico": t("tag_electrico"),
        "Mecánico": t("tag_mecanico"),
        "Preventivo": t("tag_preventivo"),
        "Avería": tt("tag_averia", "Avería"),
    }
    return ", ".join([traducciones.get(x.strip(), x.strip()) for x in tags_bd.split(",") if x.strip()])

def traducir_prioridad(codigo):
    claves = {"Baja": "prioridad_baja", "Media": "prioridad_media", "Alta": "prioridad_alta", "Crítica": "prioridad_critica"}
    return tt(claves.get(codigo, "prioridad_media"), codigo or "Media")

# ==========================================
# 4. APLICACIÓN PRINCIPAL
# ==========================================

class MaintenanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = GestorBaseDatos()
        # Cargamos el idioma guardado (por defecto español) antes de construir nada de la UI
        idiomas.set_idioma(self.db.get_config("idioma") or "es")
        # GestorFestivos ahora necesita la BD para saber qué región usar
        self.gestor_festivos = GestorFestivos(self.db)

        # --- USAR DATA_DIR PARA FOTOS Y BACKUPS ---
        # Pero si existen localmente, usar la ruta local (Mantener compatibilidad)
        cwd = os.path.abspath(".")

        # Lógica para fotos:
        local_fotos = os.path.join(cwd, "fotos_recibidas")
        if os.path.exists(local_fotos):
             self.carpeta_fotos = local_fotos
        else:
             self.carpeta_fotos = os.path.join(DATA_DIR, "fotos_recibidas")

        if not os.path.exists(self.carpeta_fotos): os.makedirs(self.carpeta_fotos)

        # Lógica para backups:
        local_backups = os.path.join(cwd, "backups")
        if os.path.exists(local_backups):
             self.carpeta_backups = local_backups
        else:
             self.carpeta_backups = os.path.join(DATA_DIR, "backups")

        if not os.path.exists(self.carpeta_backups): os.makedirs(self.carpeta_backups)

        # Lógica para backups auto:
        local_backups_auto = os.path.join(cwd, "backups_auto")
        if os.path.exists(local_backups_auto):
             self.carpeta_backups_auto = local_backups_auto
        else:
             self.carpeta_backups_auto = os.path.join(DATA_DIR, "backups_auto")

        if not os.path.exists(self.carpeta_backups_auto): os.makedirs(self.carpeta_backups_auto)
        # ------------------------------------------

        self.qr_dialog = None
        self.settings = QSettings("MyCompany", "MantenimientoApp")
        self.server_thread = ServidorSincronizacion(self.carpeta_fotos, self.db.db_name)
        self.server_thread.registro_recibido.connect(self.on_registro_recibido)
        self.server_thread.pendiente_actualizado.connect(self.refresh_all)
        self.server_thread.stock_actualizado.connect(self.refresh_stock)
        self.server_thread.stock_actualizado.connect(self.refresh_stock_alertas)
        self.server_thread.start()
        self.setWindowTitle(t("title_control_mantenimiento"))
        self.resize(1100, 750)
        g = self.settings.value("geometry")
        if g: self.restoreGeometry(g)

        # --- FIJAR EL ICONO DE LA APLICACIÓN (WAYLAND/LINUX FIX) ---
        icon_path = resource_path("icono.png")
        if os.path.exists(icon_path):
             icon = QIcon(icon_path)
             self.setWindowIcon(icon)
             QApplication.instance().setWindowIcon(icon)
        try:
            if usuarios.SESION_ACTUAL:
                self.setWindowTitle(f"{self.windowTitle()}  —  👤 {usuarios.SESION_ACTUAL['nombre']}")
        except Exception:
            pass

        self._tema_actual = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro")
        self.crear_menu()
        self.aplicar_estilo_visual()
        cw = QWidget(); self.setCentralWidget(cw); ml = QVBoxLayout(); ml.setContentsMargins(10, 10, 10, 10); cw.setLayout(ml)
        self.tabs = QTabWidget(); ml.addWidget(self.tabs)
        self._poblar_tabs()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.refresh_all(); self.pintar_calendario(); self.update_calendar_list(); self.refresh_avisos(); self.refresh_todos(); self.setup_autocompletado()
        # NOTA: La comprobación automática de actualizaciones YA NO se lanza aquí.
        # Se dispara desde el punto de entrada (bloque __main__), una vez que la
        # ventana principal ya está visible y el splash se ha cerrado del todo,
        # para evitar la carrera de foco/apilamiento entre el splash, la ventana
        # principal y el diálogo modal de "nueva versión disponible".

    def _poblar_tabs(self):
        """Crea (o recrea) todas las pestañas dentro de self.tabs, ya existente."""
        self.tab_dashboard = QWidget(); self.init_dashboard_tab(); self.tabs.addTab(self.tab_dashboard, t("tab_dashboard"))
        self.tab_calendar = QWidget(); self.init_calendar_tab(); self.tabs.addTab(self.tab_calendar, t("tab_calendario"))
        self.tab_avisos = QWidget(); self.init_avisos_tab(); self.tabs.addTab(self.tab_avisos, t("tab_avisos"))
        self.tab_entry = QWidget(); self.init_entry_tab(); self.tabs.addTab(self.tab_entry, t("tab_registrar"))
        self.tab_history = QWidget(); self.init_history_tab(); self.tabs.addTab(self.tab_history, t("tab_historial"))
        self.tab_search = QWidget(); self.init_search_tab(); self.tabs.addTab(self.tab_search, t("tab_buscador"))
        self.tab_todo = QWidget(); self.init_todo_tab(); self.tabs.addTab(self.tab_todo, t("tab_pendientes"))
        self.tab_maquinas = QWidget(); self.init_maquinas_tab(); self.tabs.addTab(self.tab_maquinas, tt("tab_maquinas", "🏭 Máquinas"))
        self.tab_stock = QWidget(); self.init_stock_tab(); self.tabs.addTab(self.tab_stock, tt("tab_stock", "📦 Stock de almacén"))
        self.tab_stock_alertas = QWidget(); self.init_stock_alertas_tab(); self.tabs.addTab(self.tab_stock_alertas, tt("tab_stock_alertas", "⚠️ Stock bajo mínimo"))

    def recargar_interfaz_completa(self):
        """Reconstruye el menú y todas las pestañas en caliente (p.ej. tras un
        cambio de idioma), sin tener que cerrar y volver a abrir la aplicación."""
        self.menuBar().clear()
        self.crear_menu()

        titulo_base = t("title_control_mantenimiento")
        if usuarios.SESION_ACTUAL:
            titulo_base += f"  —  👤 {usuarios.SESION_ACTUAL['nombre']}"
        self.setWindowTitle(titulo_base)

        indice_actual = self.tabs.currentIndex()
        self.tabs.blockSignals(True)
        while self.tabs.count():
            viejo = self.tabs.widget(0)
            self.tabs.removeTab(0)
            viejo.deleteLater()
        self._poblar_tabs()
        if 0 <= indice_actual < self.tabs.count():
            self.tabs.setCurrentIndex(indice_actual)
        self.tabs.blockSignals(False)

        self.refresh_all(); self.pintar_calendario(); self.update_calendar_list(); self.refresh_avisos(); self.refresh_todos(); self.setup_autocompletado()

    def closeEvent(self, e):
        # Posponemos el cierre real (aceptando el evento al final de esta misma
        # llamada, no volviendo a invocar self.close(): Qt ignora los close()
        # reentrantes mientras ya se está procesando uno, así que llamarlo aquí
        # dejaría la ventana abierta y obligaría a pulsar "Salir" dos veces).
        e.ignore()

        print("Iniciando limpieza de fotos...")
        self.limpiar_fotos_huerfanas(silencioso=True)

        print("Iniciando Auto-Backup...")
        dlg = QDialog(self)
        dlg.setWindowTitle(tt("title_cerrando", "Cerrando MantPro"))
        dlg.setFixedSize(420, 110)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_haciendo_backup", "Haciendo copia de seguridad antes de cerrar...")))
        barra = QProgressBar(); barra.setRange(0, 0)
        l.addWidget(barra)
        dlg.setLayout(l)

        def _actualizar_progreso(actual, total):
            if total:
                barra.setRange(0, total)
                barra.setValue(actual)

        def _backup_terminado(exito, mensaje):
            if not exito:
                print(f"Error en auto-backup: {mensaje}")
            dlg.accept()

        self.hilo_backup = BackupThread(self.carpeta_fotos, self.carpeta_backups_auto, self.db.db_name, self.db.db_almacen_name)
        self.hilo_backup.progreso.connect(_actualizar_progreso)
        self.hilo_backup.resultado.connect(_backup_terminado)
        self.hilo_backup.start()

        dlg.exec()

        self.settings.setValue("geometry", self.saveGeometry())
        e.accept()

    def on_registro_recibido(self, titulo, detalles, tags, filename, ruta_foto):
        if self.qr_dialog: self.qr_dialog.accept(); self.qr_dialog = None

        # ELIMINADO EL GUARDADO DUPLICADO (self.db.agregar_tarea).
        # La BD ya se actualizó en la API, así que solo refrescamos la vista:
        self.refresh_all()
        self.statusBar().showMessage(f"📲 Recibido: {titulo}", 4000)

    def mostrar_dialogo_qr(self):
        url = f"http://{self.server_thread.obtener_ip_local()}:{self.server_thread.server_port}"
        self.qr_dialog = DialogoQR(url, self)
        self.qr_dialog.exec(); self.qr_dialog = None

    def update_calendar_list(self):
        sd = self.calendar.selectedDate(); sds = sd.toString("yyyy-MM-dd"); self.task_list.clear()
        tdb = self.db.obtener_dias_especiales().get(sds)
        ef = sd in self.gestor_festivos.obtener_festivos()
        ets = []
        if tdb: ets.append(tdb)
        if ef and tdb != "Festivo (Manual)": ets.append("Festivo Oficial")
        ti = f"📅 {sds}" + (f" ({' + '.join(ets)})" if ets else "")
        c = "#80DEEA"
        if "Festivo" in ti: c = "#e57373"
        elif "Vacaciones" in ti: c = "#FFF59D"
        elif "Puente" in ti: c = "#42A5F5"
        elif "Día Libre" in ti: c = "#F48FB1"
        self.lbl_info.setStyleSheet(f"font-weight:bold; font-size:16px; color:{c};"); self.lbl_info.setText(ti)

        for aid, tit, finicio, freq, dur, ult, *_ in self._avisos_visibles():
            if not finicio: continue
            fi = QDate.fromString(finicio, "yyyy-MM-dd")
            if not freq: freq = "Anual"
            freq = idiomas.normalizar_frecuencia(freq)
            # Un aviso "Diario" se resetea cada día: no le aplicamos la duración
            # configurada, porque un margen de varios días haría que el de ayer
            # siguiera contando como "hecho" hoy.
            dur_ventana = 0 if freq == "Diario" else dur
            ocurrencia = fi
            while ocurrencia.addDays(dur_ventana) < sd:
                if freq == "Diario": ocurrencia = ocurrencia.addDays(1)
                elif freq == "Semanal": ocurrencia = ocurrencia.addDays(7)
                elif freq == "Mensual": ocurrencia = ocurrencia.addMonths(1)
                elif freq == "Trimestral": ocurrencia = ocurrencia.addMonths(3)
                elif freq == "Semestral": ocurrencia = ocurrencia.addMonths(6)
                elif freq == "Anual": ocurrencia = ocurrencia.addYears(1)
                else: break
            ff = ocurrencia.addDays(dur_ventana)
            if ocurrencia <= sd <= ff:
                es_completado = (ult == ocurrencia.toString("yyyy-MM-dd"))
                color_bg = "#27ae60" if es_completado else "#e74c3c"
                estado_txt = f"[{t('estado_ok')}]" if es_completado else f"[{t('estado_pendiente')}]"
                it = QListWidgetItem(f"⚠️ AVISO: {tit} {estado_txt}")
                it.setBackground(QColor(color_bg)); it.setForeground(Qt.GlobalColor.white)
                self.task_list.addItem(it)

        ts = self.db.obtener_tareas_por_fecha(sds)
        if not ts and self.task_list.count() == 0: self.task_list.addItem(t("msg_dia_no_laborable") if ets else t("msg_nada_registrado"))
        for tarea in ts:
            # --- LIMPIEZA VISUAL COMPLETA ---
            texto_limpio = re.sub(r"\[FOTO:.*?\]", "", tarea[1])
            texto_limpio = re.sub(r"\[FOTO_DESPUES:.*?\]", "", texto_limpio)
            texto_limpio = re.sub(r"\[REF:.*?\]", "", texto_limpio).strip()
            # --------------------------------

            it = QListWidgetItem(f"{texto_limpio} | {traducir_tags_bd(tarea[2])}")
            if self._hay_foto_disponible(tarea[1]):
                # Icono propio (no del tema del sistema): algunos temas de iconos SVG
                # provocan el warning "qt.svg: Invalid path data" con QIcon.fromTheme.
                pm_foto = QPixmap(16, 16); pm_foto.fill(QColor("#3daee9"))
                it.setIcon(QIcon(pm_foto)); it.setToolTip("Tiene foto adjunta")
            it.setData(Qt.ItemDataRole.UserRole, tarea[0])
            self.task_list.addItem(it)

    def _hay_foto_disponible(self, desc):
        # Busca primero la foto de ANTES; si no existe físicamente, prueba la de DESPUÉS.
        m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
        if m:
            nombre = m.group(1).split("]")[0].strip()
            if nombre and os.path.exists(os.path.join(self.carpeta_fotos, nombre)):
                return True
        m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc)
        if m_d:
            nombre_d = m_d.group(1).split("]")[0].strip()
            if nombre_d and os.path.exists(os.path.join(self.carpeta_fotos, nombre_d)):
                return True
        return False

    def fill_t(self, table, data):
        table.setRowCount(len(data))
        pm_foto = QPixmap(16, 16); pm_foto.fill(QColor("#3daee9")); icon_foto = QIcon(pm_foto)
        pm_vacio = QPixmap(16, 16); pm_vacio.fill(Qt.GlobalColor.transparent); icon_vacio = QIcon(pm_vacio)

        for r, fila in enumerate(data):
            id_t, fecha, desc, tags = fila[0], fila[1], fila[2], fila[3]
            autor = fila[4] if len(fila) > 4 else ""
            if not autor: autor = usuarios.ETIQUETA_HISTORICO
            prioridad = fila[6] if len(fila) > 6 else "Media"
            # LIMPIEZA VISUAL (FOTO Y REF)
            desc_limpia = re.sub(r"\[FOTO.*?:.*?\]", "", desc)
            desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

            desc_visual = desc_limpia.replace("\n", "  ➜  ")

            oscuro = self._tema_actual == "oscuro"
            tags_lower = tags.lower(); color_bg = None; color_fg = None
            if any(x in tags_lower for x in ["urgente", "avería", "rotura", "fallo", "paro"]):
                color_bg = QColor("#4a2424" if oscuro else "#f2b8bd"); color_fg = QColor("#ffffff" if oscuro else "#58151c")
            elif any(x in tags_lower for x in ["preventivo", "revisión", "ok", "limpieza"]):
                color_bg = QColor("#213c21" if oscuro else "#a3d9ac"); color_fg = QColor("#ffffff" if oscuro else "#1e4620")
            elif "eléctrico" in tags_lower or "cuadro" in tags_lower:
                color_bg = QColor("#555" if oscuro else "#e0e0e0"); color_fg = QColor("#ffffff" if oscuro else "#333333")
            elif "mecánico" in tags_lower:
                color_bg = QColor("#5a4a2d" if oscuro else "#fff3cd"); color_fg = QColor("#ffffff" if oscuro else "#5c4813")

            item_f = QTableWidgetItem(fecha); item_f.setData(Qt.ItemDataRole.UserRole, id_t)
            item_d = QTableWidgetItem(desc_visual); item_d.setToolTip(desc_limpia)

            if self._hay_foto_disponible(desc):
                item_d.setIcon(icon_foto)
                item_d.setToolTip(f"📸 CON FOTO(S) ADJUNTA(S)\n\n{desc_limpia}")
            else:
                item_d.setIcon(icon_vacio)

            item_t = QTableWidgetItem(traducir_tags_bd(tags))
            item_t.setData(Qt.ItemDataRole.UserRole, tags)
            item_u = QTableWidgetItem(autor)
            item_p = QTableWidgetItem(traducir_prioridad(prioridad))
            colores_prioridad = {
                "Crítica": QColor("#8e1616"), "Alta": QColor("#c0392b" if not oscuro else "#a94442"),
            }
            if prioridad in colores_prioridad:
                item_p.setBackground(colores_prioridad[prioridad]); item_p.setForeground(QColor("#ffffff"))

            if color_bg:
                item_f.setBackground(color_bg); item_d.setBackground(color_bg)
                item_t.setBackground(color_bg); item_u.setBackground(color_bg)
                item_f.setForeground(color_fg); item_d.setForeground(color_fg)
                item_t.setForeground(color_fg); item_u.setForeground(color_fg)

            table.setItem(r, 0, item_f); table.setItem(r, 1, item_d); table.setItem(r, 2, item_t)
            if table.columnCount() > 3:
                table.setItem(r, 3, item_u)
            if table.columnCount() > 4:
                table.setItem(r, 4, item_p)

    def search(self):
        texto = self.s_in.text().strip(); fecha = None
        if self.s_chk_date.isChecked(): fecha = self.s_date.date().toString("yyyy-MM-dd")
        resultados = self.db.buscar_tareas_avanzado(texto, fecha)
        self.fill_t(self.s_table, resultados)
        filtros_activos = []
        if self.chk_s_urg.isChecked(): filtros_activos.append("urgente")
        if self.chk_s_elec.isChecked(): filtros_activos.append("léctrico")
        if self.chk_s_mec.isChecked(): filtros_activos.append("ecánico")
        if self.chk_s_prev.isChecked(): filtros_activos.append("preventivo")
        filas_visibles = 0
        for row in range(self.s_table.rowCount()):
            item_tags = self.s_table.item(row, 2).text().lower()
            mostrar = True
            for f in filtros_activos:
                if f not in item_tags:
                    sin_tilde = f.replace("léctrico", "lectrico").replace("ecánico", "ecanico")
                    if sin_tilde not in item_tags: mostrar = False; break
            self.s_table.setRowHidden(row, not mostrar)
            if mostrar: filas_visibles += 1
        self.statusBar().showMessage(t("msg_mostrando_resultados").format(n=filas_visibles), 3000)

    def refresh_history(self):
        datos = self.db.obtener_todas_cronologico()
        self.fill_t(self.h_table, datos)
        self.recargar_combo_historial()
        self.aplicar_filtros_historial()

        # Construir árbol de fechas dinámico
        self.tree_history.clear()
        arbol_datos = {}
        for row in datos:
            fecha = row[1]
            if not fecha or len(fecha) < 7: continue
            year, month = fecha[:4], fecha[5:7]
            if year not in arbol_datos: arbol_datos[year] = set()
            arbol_datos[year].add(month)

        meses = {"01":t("mes_01"), "02":t("mes_02"), "03":t("mes_03"), "04":t("mes_04"), "05":t("mes_05"), "06":t("mes_06"), "07":t("mes_07"), "08":t("mes_08"), "09":t("mes_09"), "10":t("mes_10"), "11":t("mes_11"), "12":t("mes_12")}

        item_todo = QTreeWidgetItem([t("lbl_todos_trabajos")])
        item_todo.setData(0, Qt.ItemDataRole.UserRole, "TODO")
        self.tree_history.addTopLevelItem(item_todo)

        for year in sorted(arbol_datos.keys(), reverse=True):
            item_year = QTreeWidgetItem([f"📅 {year}"])
            item_year.setData(0, Qt.ItemDataRole.UserRole, year)
            self.tree_history.addTopLevelItem(item_year)

            for month in sorted(arbol_datos[year], reverse=True):
                item_month = QTreeWidgetItem([meses.get(month, month)])
                item_month.setData(0, Qt.ItemDataRole.UserRole, f"{year}-{month}")
                item_year.addChild(item_month)

        self.tree_history.setCurrentItem(item_todo)

        # Desocultar todas las filas al refrescar la tabla por defecto
        for row in range(self.h_table.rowCount()):
            self.h_table.setRowHidden(row, False)
    def mostrar_about(self):
        import webbrowser
        texto = f"""
        <h2>MantPro v{APP_VERSION}</h2>
        <p><b>AnabasaSoft</b></p>
        <p>📧 Email: <a href="mailto:anabasasoft@gmail.com">anabasasoft@gmail.com</a></p>
        <p>🌐 GitHub: <a href="https://github.com/AnabasaSoft">github.com/AnabasaSoft</a></p>
        <p>💼 Proyecto: <a href="https://github.com/AnabasaSoft/MantPro">github.com/AnabasaSoft/MantPro</a></p>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle(t("title_acerca_de"))
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(texto)
        # Esto permite que los enlaces abran el navegador de KDE (o el por defecto del SO)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        msg.exec()

    def comprobar_actualizaciones(self, manual=False):
        self._check_manual = manual
        if manual: self.statusBar().showMessage("🔄 Buscando actualizaciones en GitHub...", 3000)
        self.hilo_updates = ChequeadorActualizaciones()
        self.hilo_updates.resultado.connect(self.on_actualizacion_comprobada)
        self.hilo_updates.start()

    def on_actualizacion_comprobada(self, hay_nueva, version, url, notas):
        if hay_nueva:
            msg = QMessageBox(self)
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg.setWindowTitle(t("title_nueva_version"))
            msg.setText(t("msg_nueva_version_disponible").format(actual=APP_VERSION, nueva=version))
            msg.setInformativeText(t("msg_quieres_descargar"))
            if notas: msg.setDetailedText(notas)

            btn_si = msg.addButton(t("btn_descargar"), QMessageBox.ButtonRole.YesRole)
            msg.addButton(t("btn_luego"), QMessageBox.ButtonRole.NoRole)

            msg.setWindowState(msg.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
            msg.raise_()
            msg.activateWindow()

            msg.exec()

            if msg.clickedButton() == btn_si:
                # Forzar apertura externa limpia ignorando librerías empaquetadas del entorno virtual/rpm
                try:
                    if sys.platform.startswith('linux'):
                        os.system(f"xdg-open '{url}' &")
                    else:
                        import webbrowser
                        webbrowser.open(url)
                except Exception as e:
                    import webbrowser
                    webbrowser.open(url)
        elif self._check_manual:
            if version == "error":
                QMessageBox.warning(self, t("title_error"), t("msg_error_conexion_github"))
            else:
                QMessageBox.information(self, t("title_actualizado"), t("msg_ya_actualizado").format(v=APP_VERSION))

    def crear_menu(self):
        mb = self.menuBar()

        # --- MENÚ SESIÓN (delante de Archivo) ---
        sm = mb.addMenu(tt("menu_sesion", "&Sesión"))
        sm.addAction(QAction(tt("menu_cambiar_usuario", "🔁 Cambiar de usuario"),
                             self, triggered=self.cerrar_sesion))
        sm.addAction(QAction(tt("menu_cerrar_sesion", "🚪 Cerrar sesión"),
                             self, triggered=self.cerrar_sesion))
        sm.addSeparator()
        sm.addAction(QAction(t("menu_salir"), self, triggered=self.close))
        # ------------------------------------------

        fm = mb.addMenu(t("menu_archivo"))
        if usuarios.es_admin():
            fm.addAction(QAction(t("menu_backup"), self, triggered=self.realizar_backup))
            menu_restaurar = fm.addMenu(t("menu_restaurar"))
            menu_restaurar.addAction(QAction(tt("menu_restaurar_manual", "Restaurar..."), self, triggered=self.restaurar_backup))
            menu_restaurar.addAction(QAction(tt("menu_restaurar_auto", "Restaurar desde copia automática..."), self, triggered=self.restaurar_backup_auto))
            fm.addSeparator()

        # --- SUBMENÚ PDF ---
        menu_pdf = fm.addMenu(t("menu_opciones_pdf"))

        act_exportar = QAction(t("menu_generar_pdf"), self)
        act_exportar.triggered.connect(self.exportar_pdf)
        menu_pdf.addAction(act_exportar)

        menu_pdf.addSeparator()

        act_cambiar_logo = QAction(t("menu_add_logo"), self)
        act_cambiar_logo.triggered.connect(self.cambiar_logo)
        menu_pdf.addAction(act_cambiar_logo)

        act_quitar_logo = QAction(t("menu_quitar_logo"), self)
        act_quitar_logo.triggered.connect(self.quitar_logo)
        menu_pdf.addAction(act_quitar_logo)
        # --------------------

        fm.addAction(QAction(t("menu_csv"), self, triggered=self.exportar_csv))
        fm.addAction(QAction(t("menu_excel"), self, triggered=self.exportar_excel))
        tm = mb.addMenu(t("menu_herramientas"))
        act_sync = QAction(t("menu_sync_qr"), self); act_sync.triggered.connect(self.mostrar_dialogo_qr); tm.addAction(act_sync)
        if usuarios.es_admin():
            tm.addAction(QAction(t("menu_gestionar_dias"), self, triggered=self.gest_dias));

            # --- OPCIÓN DE PAÍS / PROVINCIA ---
            act_prov = QAction(t("menu_pais_region"), self)
            act_prov.triggered.connect(self.cambiar_pais_region)
            tm.addAction(act_prov)
            # ---------------------------------

        # --- SUBMENÚ DE IDIOMA ---
        menu_idioma = tm.addMenu(t("menu_idioma"))
        self.acciones_idioma = []
        for codigo, nombre in idiomas.IDIOMAS_DISPONIBLES:
            act_idioma = QAction(nombre, self)
            act_idioma.setCheckable(True)
            act_idioma.setChecked(codigo == idiomas.get_idioma())
            act_idioma.triggered.connect(lambda checked, c=codigo: self.cambiar_idioma(c))
            menu_idioma.addAction(act_idioma)
            self.acciones_idioma.append((codigo, act_idioma))
        # -------------------------

        fm.addSeparator()
        if usuarios.es_admin():
            tm.addAction(QAction(t("menu_limpiar_fotos"), self, triggered=lambda: self.limpiar_fotos_huerfanas(limpiar_backups=True)))
            tm.addSeparator()
        tm.addAction(QAction(tt("menu_cambiar_password", "🔑 Cambiar mi contraseña"),
                             self, triggered=self.cambiar_mi_password))
        if usuarios.es_admin():
            tm.addAction(QAction(tt("menu_usuarios", "👥 Gestión de usuarios"),
                                 self, triggered=self.gestionar_usuarios))
            tm.addAction(QAction(tt("menu_sesiones", "🔐 Sesiones de dispositivos"),
                                 self, triggered=self.gestionar_sesiones))
            tm.addAction(QAction(tt("menu_auditoria", "📋 Registro de cambios"),
                                 self, triggered=self.ver_auditoria))
        # --- Menú de tema visual ---
        vm = mb.addMenu(tt("menu_tema", "Apariencia"))
        self._acciones_tema = {}
        grupo_tema = QActionGroup(self)
        for nombre, etiqueta in [("oscuro", tt("tema_oscuro", "🌙 Oscuro (por defecto)")),
                                  ("claro", tt("tema_claro", "☀️ Claro")),
                                  ("retro", tt("tema_retro", "🖥️ Clásico (Windows 98)"))]:
            act = QAction(etiqueta, self, checkable=True)
            act.setData(nombre)
            act.triggered.connect(lambda checked, n=nombre: self.aplicar_estilo_visual(n))
            grupo_tema.addAction(act)
            vm.addAction(act)
            self._acciones_tema[nombre] = act
            if nombre == self._tema_actual:
                act.setChecked(True)

        hm = mb.addMenu(t("menu_ayuda"))
        hm.addAction(QAction(t("menu_buscar_actualizaciones"), self, triggered=lambda: self.comprobar_actualizaciones(manual=True)))
        hm.addAction(QAction(t("menu_acerca_de"), self, triggered=self.mostrar_about))

    def cambiar_idioma(self, codigo):
        if codigo == idiomas.get_idioma():
            return
        idiomas.set_idioma(codigo)
        self.db.set_config("idioma", codigo)
        self.recargar_interfaz_completa()

    def cambiar_pais_region(self):
        # PASO 1: Elegir país
        dlg_pais = DialogoSeleccionPais(self.gestor_festivos, self.db, self)
        if not dlg_pais.exec():
            return  # Cancelado

        nombre_pais, iso_pais = dlg_pais.get_selection()
        self.db.set_config("country_iso", iso_pais)

        if iso_pais == "ES":
            # PASO 2 (solo España): Elegir provincia, igual que antes
            dlg = DialogoSeleccionRegion(self.db, self)
            if dlg.exec():
                nombre, iso_prov, iso_parent = dlg.get_selection()
                self.db.set_config("region_iso", iso_prov)
                self.db.set_config("parent_iso", iso_parent)
                self.gestor_festivos.limpiar_cache()
                QMessageBox.information(self, t("title_region_cambiada"), t("msg_region_cambiada").format(zona=nombre, parent=iso_parent, prov=iso_prov))
            else:
                # Canceló la provincia, pero el país ya quedó guardado como España
                self.gestor_festivos.limpiar_cache()
        else:
            # Otro país: sin desglose regional, solo festivos nacionales
            self.db.set_config("region_iso", "")
            self.db.set_config("parent_iso", "")
            self.gestor_festivos.limpiar_cache()
            QMessageBox.information(self, t("title_pais_cambiado"), t("msg_pais_cambiado").format(pais=nombre_pais))

        # Repintar el calendario
        self.pintar_calendario()
        self.update_calendar_list()

    def aplicar_estilo_visual(self, tema=None):
        if tema is None:
            tema = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro")
        self._tema_actual = tema

        QSettings("MyCompany", "MantenimientoApp").setValue("tema", tema)

        if tema == "retro":
            self._aplicar_tema_retro()
        elif tema == "claro":
            self._aplicar_tema_claro()
        else:
            self._aplicar_tema_oscuro()

        # Actualizar checks del menú si existe
        if hasattr(self, '_acciones_tema'):
            for nombre, act in self._acciones_tema.items():
                act.setChecked(nombre == tema)

        # Repintar las tablas con colores por etiqueta/estado, ya que sus celdas
        # se colorean con QColor fijos en el momento de rellenarlas y no se
        # actualizan solas al cambiar de tema.
        if hasattr(self, 'grafico_ranking_averias'):
            self.refresh_dashboard()
        if hasattr(self, 'h_table'):
            self.refresh_history()
        if hasattr(self, 's_table'):
            self.search()
        if hasattr(self, 'table_avisos'):
            self.refresh_avisos()

        # Repintar las zonas de "arrastra una foto aquí" si no tienen foto puesta
        if hasattr(self, 'lbl_entry_foto') and not getattr(self, 'entry_foto_filename', None):
            self.lbl_entry_foto.setStyleSheet(_estilo_zona_arrastre())
        if hasattr(self, 'lbl_entry_foto_d') and not getattr(self, 'entry_foto_despues_filename', None):
            self.lbl_entry_foto_d.setStyleSheet(_estilo_zona_arrastre())

    def _aplicar_tema_retro(self):
        """Estilo clásico inspirado en Windows 98 / 2000."""
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        from PyQt6.QtGui import QPalette, QColor
        pal = QPalette()
        # Fondo gris clásico
        pal.setColor(QPalette.ColorRole.Window, QColor(212, 208, 200))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        pal.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(230, 228, 224))
        pal.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        pal.setColor(QPalette.ColorRole.Button, QColor(212, 208, 200))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        # Selección azul oscuro
        pal.setColor(QPalette.ColorRole.Highlight, QColor(0, 0, 128))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        # Bordes
        pal.setColor(QPalette.ColorRole.Light, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorRole.Dark, QColor(128, 128, 128))
        pal.setColor(QPalette.ColorRole.Mid, QColor(160, 160, 160))
        pal.setColor(QPalette.ColorRole.Shadow, QColor(64, 64, 64))
        # Tooltips
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 225))
        pal.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        # Disabled
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(128, 128, 128))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(128, 128, 128))

        QApplication.instance().setPalette(pal)
        self.setStyleSheet("""
        QMainWindow, QWidget { font-family: "Tahoma", "MS Sans Serif", sans-serif; font-size: 13px; }
        QMenuBar { background-color: #d4d0c8; border-bottom: 1px solid #808080; }
        QMenuBar::item:selected { background-color: #000080; color: white; }
        QMenu { background-color: #d4d0c8; border: 2px outset #d4d0c8; }
        QMenu::item:selected { background-color: #000080; color: white; }
        QTabWidget::pane { border: 2px inset #808080; background: #d4d0c8; }
        QTabBar::tab { background: #d4d0c8; border: 1px outset #d4d0c8; padding: 4px 14px; margin-right: 1px; }
        QTabBar::tab:selected { background: #d4d0c8; border-bottom: none; font-weight: bold; }
        QPushButton { background-color: #d4d0c8; border: 2px outset #d4d0c8; padding: 4px 12px; min-height: 20px; }
        QPushButton:pressed { border-style: inset; }
        QPushButton:hover { background-color: #e4e0d8; }
        QLineEdit, QTextEdit, QDateEdit, QSpinBox { background-color: white; border: 2px inset #808080; padding: 2px; }
        QTableWidget, QTreeView, QListWidget, QListView { background-color: white; border: 2px inset #808080; gridline-color: #c0c0c0; }
        QHeaderView::section { background-color: #d4d0c8; border: 1px outset #d4d0c8; padding: 4px; font-weight: bold; }
        QGroupBox { border: 2px groove #d4d0c8; margin-top: 8px; padding-top: 12px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
        QComboBox { background-color: white; border: 2px inset #808080; padding: 2px; }
        QComboBox::drop-down { border-left: 1px solid #808080; background: #d4d0c8; width: 18px; }
        QCheckBox::indicator, QRadioButton::indicator { width: 13px; height: 13px; }
        QProgressBar { border: 2px inset #808080; background: white; text-align: center; }
        QProgressBar::chunk { background-color: #000080; }
        QScrollBar:vertical { background: #d4d0c8; width: 16px; border: 1px solid #808080; }
        QScrollBar::handle:vertical { background: #d4d0c8; border: 1px outset #d4d0c8; min-height: 20px; }
        QScrollBar:horizontal { background: #d4d0c8; height: 16px; border: 1px solid #808080; }
        QScrollBar::handle:horizontal { background: #d4d0c8; border: 1px outset #d4d0c8; min-width: 20px; }
        QStatusBar { background: #d4d0c8; border-top: 1px solid #808080; }
        QCalendarWidget QAbstractItemView:enabled { background-color: white; color: black; selection-background-color: #000080; selection-color: white; }
        QSplitter::handle { background: #d4d0c8; }
        QDialog { background-color: #d4d0c8; }
        """)

    def _aplicar_tema_claro(self):
        """Tema claro moderno."""
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        from PyQt6.QtGui import QPalette, QColor
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, QColor(243, 243, 243))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(238, 238, 238))
        pal.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.Button, QColor(230, 230, 230))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 212))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorRole.Light, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorRole.Dark, QColor(180, 180, 180))
        pal.setColor(QPalette.ColorRole.Mid, QColor(200, 200, 200))
        pal.setColor(QPalette.ColorRole.Shadow, QColor(120, 120, 120))
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        pal.setColor(QPalette.ColorRole.ToolTipText, QColor(30, 30, 30))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(160, 160, 160))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(160, 160, 160))
        pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(160, 160, 160))
        QApplication.instance().setPalette(pal)
        self.setStyleSheet("""
        QMainWindow, QWidget { font-family: "Segoe UI", sans-serif; font-size: 14px; }
        QMenuBar { background-color: #f3f3f3; border-bottom: 1px solid #d0d0d0; }
        QMenuBar::item:selected { background-color: #0078d4; color: white; border-radius: 3px; }
        QMenu { background-color: #ffffff; border: 1px solid #d0d0d0; }
        QMenu::item { padding: 6px 24px; }
        QMenu::item:selected { background-color: #0078d4; color: white; border-radius: 3px; }
        QTabWidget::pane { border: 1px solid #d0d0d0; background: #f3f3f3; border-radius: 4px; }
        QTabBar::tab { background: #e6e6e6; color: #444; padding: 8px 20px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
        QTabBar::tab:selected { background: #0078d4; color: white; font-weight: bold; }
        QTabBar::tab:hover:!selected { background: #d4d4d4; }
        QPushButton { background-color: #e6e6e6; border: 1px solid #c0c0c0; border-radius: 5px; padding: 6px 14px; }
        QPushButton:hover { background-color: #d4d4d4; border-color: #0078d4; }
        QPushButton:pressed { background-color: #0078d4; color: white; }
        QLineEdit, QTextEdit, QDateEdit, QSpinBox { background-color: white; border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px; }
        QLineEdit:focus, QTextEdit:focus { border-color: #0078d4; }
        QTableWidget, QTreeView, QListWidget, QListView { background-color: white; border: 1px solid #c0c0c0; border-radius: 4px; gridline-color: #e0e0e0; selection-background-color: #0078d4; selection-color: white; }
        QHeaderView::section { background-color: #e6e6e6; border: none; border-right: 1px solid #d0d0d0; border-bottom: 1px solid #d0d0d0; padding: 6px; font-weight: bold; color: #333; }
        QGroupBox { border: 1px solid #d0d0d0; border-radius: 6px; margin-top: 8px; padding-top: 14px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #0078d4; }
        QComboBox { background-color: white; border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px; }
        QComboBox::drop-down { border-left: 1px solid #d0d0d0; background: #e6e6e6; width: 20px; border-radius: 0 4px 4px 0; }
        QProgressBar { border: 1px solid #c0c0c0; border-radius: 4px; background: white; text-align: center; }
        QProgressBar::chunk { background-color: #0078d4; border-radius: 3px; }
        QScrollBar:vertical { background: #f3f3f3; width: 12px; border: none; }
        QScrollBar::handle:vertical { background: #c0c0c0; border-radius: 6px; min-height: 24px; }
        QScrollBar::handle:vertical:hover { background: #a0a0a0; }
        QScrollBar:horizontal { background: #f3f3f3; height: 12px; border: none; }
        QScrollBar::handle:horizontal { background: #c0c0c0; border-radius: 6px; min-width: 24px; }
        QScrollBar::handle:horizontal:hover { background: #a0a0a0; }
        QStatusBar { background: #f3f3f3; border-top: 1px solid #d0d0d0; color: #555; }
        QCalendarWidget QAbstractItemView:enabled { background-color: white; color: #1e1e1e; selection-background-color: #0078d4; selection-color: white; }
        QSplitter::handle { background: #d0d0d0; }
        QDialog { background-color: #f3f3f3; }
        QCheckBox::indicator:unchecked { border: 1px solid #999; background: white; border-radius: 2px; }
        QCheckBox::indicator:checked { background: #0078d4; border: 1px solid #0078d4; border-radius: 2px; }
        """)

    def _aplicar_tema_oscuro(self):
        """Tema oscuro original de MantPro."""
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        # Limpiar la paleta retro si venimos de ella
        QApplication.instance().setPalette(QApplication.style().standardPalette())
        self.setStyleSheet("""
        QMainWindow, QWidget { background-color: #2b2b2b; color: #e0e0e0; font-family: "Segoe UI", sans-serif; font-size: 14px; }
        QTabWidget::pane { border: 1px solid #444; background: #2b2b2b; border-radius: 4px; }
        QTabBar::tab { background: #3c3c3c; color: #b0b0b0; padding: 8px 20px; border-top-left-radius: 4px; margin-right: 2px; }
        QTabBar::tab:selected { background: #3daee9; color: white; font-weight: bold; }
        QPushButton { background-color: #3c3c3c; border: 1px solid #555; border-radius: 6px; padding: 6px 12px; color: #e0e0e0; }
        QPushButton:hover { background-color: #505050; border: 1px solid #3daee9; }
        QPushButton:pressed { background-color: #3daee9; color: white; }
        QLineEdit, QTextEdit, QDateEdit, QListWidget, QTableWidget, QTreeView, QListView { background-color: #1e1e1e; border: 1px solid #555; border-radius: 4px; color: #e0e0e0; padding: 4px; selection-background-color: #3daee9; selection-color: white; }
        QHeaderView::section { background-color: #3c3c3c; padding: 6px; border: none; color: #e0e0e0; font-weight: bold; }
        QCalendarWidget QAbstractItemView:enabled { color: #e0e0e0; background-color: #1e1e1e; selection-background-color: #80DEEA; selection-color: black; }
        QMenu { background-color: #2b2b2b; color: #e0e0e0; border: 1px solid #555; }
        QMenu::item { padding: 5px 20px; }
        QMenu::item:selected { background-color: #3daee9; color: white; }

        /* ESTILO ESPECÍFICO PARA DIÁLOGOS DE ARCHIVOS (QFileDialog) */
        QFileDialog QToolButton {
            background-color: #cccccc;
            color: black;
            border: 1px solid #999;
            border-radius: 4px;
            margin: 2px;
        }
        QFileDialog QToolButton:hover {
            background-color: #ffffff;
        }
        QFileDialog QListView, QFileDialog QTreeView {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        """)

    def init_entry_tab(self):
        self.entry_foto_filename = None
        self.entry_foto_despues_filename = None
        l = QVBoxLayout(); l.setSpacing(10)
        h_top = QHBoxLayout(); v_date = QVBoxLayout()
        self.ide = QDateEdit(); self.ide.setCalendarPopup(True); self.ide.setDate(QDate.currentDate()); self.ide.setDisplayFormat("yyyy-MM-dd")
        v_date.addWidget(QLabel(t("lbl_fecha"))); v_date.addWidget(self.ide); v_date.addStretch(); h_top.addLayout(v_date, 40)
        v_foto = QVBoxLayout(); v_foto.setContentsMargins(0,0,0,0); v_foto.setSpacing(2)
        self.lbl_entry_foto = LabelArrastrable(); self.lbl_entry_foto.setFixedHeight(100); self.lbl_entry_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_entry_foto.archivo_soltado.connect(self.procesar_foto_entry); self.lbl_entry_foto.mousePressEvent = self.buscar_foto_entry_click
        v_foto.addWidget(self.lbl_entry_foto)
        self.btn_del_foto = QPushButton(t("btn_quitar_foto")); self.btn_del_foto.setStyleSheet("background-color: #c0392b; color: white; border-radius: 4px; padding: 2px;"); self.btn_del_foto.setFixedHeight(20); self.btn_del_foto.clicked.connect(self.borrar_foto_entry); self.btn_del_foto.hide()
        v_foto.addWidget(self.btn_del_foto)

        self.lbl_entry_foto_d = LabelArrastrable(); self.lbl_entry_foto_d.setFixedHeight(100); self.lbl_entry_foto_d.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_entry_foto_d.setText(t("lbl_arrastra_despues"))
        self.lbl_entry_foto_d.archivo_soltado.connect(self.procesar_foto_entry_d); self.lbl_entry_foto_d.mousePressEvent = self.buscar_foto_entry_click_d
        v_foto.addWidget(self.lbl_entry_foto_d)

        self.btn_del_foto_d = QPushButton(t("btn_quitar_foto_despues")); self.btn_del_foto_d.setStyleSheet("background-color: #c0392b; color: white; border-radius: 4px; padding: 2px;"); self.btn_del_foto_d.setFixedHeight(20); self.btn_del_foto_d.clicked.connect(self.borrar_foto_entry_d); self.btn_del_foto_d.hide()
        v_foto.addWidget(self.btn_del_foto_d)

        h_top.addLayout(v_foto, 60); l.addLayout(h_top)
        self.ire = QLineEdit(); self.ire.setPlaceholderText(t("ph_resumen")); l.addWidget(QLabel(t("lbl_resumen_tarea"))); l.addWidget(self.ire)
        h_qr = QHBoxLayout(); h_qr.addWidget(QLabel(t("lbl_detalles"))); h_qr.addStretch()
        b_qr = QPushButton(t("btn_sincronizar_app")); b_qr.setStyleSheet("background-color: #d35400; color: white; padding: 4px 8px;"); b_qr.clicked.connect(self.mostrar_dialogo_qr); h_qr.addWidget(b_qr); l.addLayout(h_qr)
        self.idet = QTextEdit(); l.addWidget(self.idet)
        fila_maquina_entry = QHBoxLayout()
        fila_maquina_entry.addWidget(QLabel(tt("lbl_maquina", "Máquina") + ":"))
        self.combo_maquina_entry = QComboBox()
        _poblar_combo_maquinas(self.combo_maquina_entry)
        fila_maquina_entry.addWidget(self.combo_maquina_entry, 1)
        l.addLayout(fila_maquina_entry)
        l.addWidget(QLabel(t("lbl_etiquetas_rapidas")))
        h_tags = QHBoxLayout()
        self.chk_urgente = QCheckBox(t("tag_urgente")); self.chk_electrico = QCheckBox(t("tag_electrico"))
        self.chk_mecanico = QCheckBox(t("tag_mecanico")); self.chk_prev = QCheckBox(t("tag_preventivo"))
        self.chk_averia = QCheckBox(tt("tag_averia", "Avería"))
        for c in [self.chk_urgente, self.chk_electrico, self.chk_mecanico, self.chk_prev, self.chk_averia]: c.setStyleSheet(_estilo_check_etiqueta()); h_tags.addWidget(c)
        l.addLayout(h_tags)
        self.itag = QLineEdit(); self.itag.setPlaceholderText(t("ph_otras_etiquetas")); l.addWidget(self.itag)

        fila_prioridad_entry = QHBoxLayout()
        fila_prioridad_entry.addWidget(QLabel(tt("lbl_prioridad", "Prioridad") + ":"))
        self.combo_prioridad_entry = QComboBox()
        for cod, clave in (("Baja", "prioridad_baja"), ("Media", "prioridad_media"), ("Alta", "prioridad_alta"), ("Crítica", "prioridad_critica")):
            self.combo_prioridad_entry.addItem(tt(clave, cod), cod)
        self.combo_prioridad_entry.setCurrentIndex(1)
        fila_prioridad_entry.addWidget(self.combo_prioridad_entry, 1)
        fila_prioridad_entry.addWidget(QLabel(tt("lbl_horas_paro", "Horas de parada (si es avería)") + ":"))
        self.spin_horas_paro_entry = QDoubleSpinBox(); self.spin_horas_paro_entry.setRange(0, 999); self.spin_horas_paro_entry.setDecimals(1)
        self.spin_horas_paro_entry.setSuffix(" h"); self.spin_horas_paro_entry.setEnabled(False)
        self.chk_averia.toggled.connect(self.spin_horas_paro_entry.setEnabled)
        fila_prioridad_entry.addWidget(self.spin_horas_paro_entry)
        l.addLayout(fila_prioridad_entry)

        b_save = QPushButton(t("btn_guardar_registro")); b_save.setMinimumHeight(45); b_save.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #2980b9; color: white;"); b_save.clicked.connect(self.save_entry); l.addWidget(b_save); l.addStretch(); self.tab_entry.setLayout(l)
    def borrar_foto_entry(self):
        self.entry_foto_filename = None; self.lbl_entry_foto.setPixmap(QPixmap()); self.lbl_entry_foto.setText(t("lbl_arrastra_foto")); self.lbl_entry_foto.setStyleSheet(_estilo_zona_arrastre()); self.btn_del_foto.hide()
    def borrar_foto_entry_d(self):
        self.entry_foto_despues_filename = None; self.lbl_entry_foto_d.setPixmap(QPixmap()); self.lbl_entry_foto_d.setText(t("lbl_arrastra_despues")); self.lbl_entry_foto_d.setStyleSheet(_estilo_zona_arrastre()); self.btn_del_foto_d.hide()

    def buscar_foto_entry_click_d(self, e):
        if self.entry_foto_despues_filename:
            ruta = os.path.join(self.carpeta_fotos, self.entry_foto_despues_filename)
            if os.path.exists(ruta): VisorFoto(ruta, self).exec()
        else:
            dlg = DialogoSelectorFoto(self)
            if dlg.exec() and dlg.selectedFiles(): self.procesar_foto_entry_d(dlg.selectedFiles()[0])

    def procesar_foto_entry_d(self, ruta_origen):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S"); ext = os.path.splitext(ruta_origen)[1]
            nuevo = f"pc_entry_d_{ts}{ext}"; destino = os.path.join(self.carpeta_fotos, nuevo)
            shutil.copy2(ruta_origen, destino); self.entry_foto_despues_filename = nuevo
            pix = QPixmap(destino); self.lbl_entry_foto_d.setPixmap(pix.scaled(self.lbl_entry_foto_d.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_entry_foto_d.setStyleSheet("border: 2px solid #2ecc71;"); self.lbl_entry_foto_d.setText(""); self.btn_del_foto_d.show()
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))
    def buscar_foto_entry_click(self, e):
        if self.entry_foto_filename:
            ruta = os.path.join(self.carpeta_fotos, self.entry_foto_filename)
            if os.path.exists(ruta): VisorFoto(ruta, self).exec()
        else:
            dlg = DialogoSelectorFoto(self)
            if dlg.exec() and dlg.selectedFiles(): self.procesar_foto_entry(dlg.selectedFiles()[0])
    def procesar_foto_entry(self, ruta_origen):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S"); ext = os.path.splitext(ruta_origen)[1]
            nuevo = f"pc_entry_{ts}{ext}"; destino = os.path.join(self.carpeta_fotos, nuevo)
            shutil.copy2(ruta_origen, destino); self.entry_foto_filename = nuevo
            pix = QPixmap(destino); self.lbl_entry_foto.setPixmap(pix.scaled(self.lbl_entry_foto.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.lbl_entry_foto.setStyleSheet("border: 2px solid #2ecc71;"); self.lbl_entry_foto.setText(""); self.btn_del_foto.show()
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))
    def save_entry(self):
        d, r = self.ide.date().toString("yyyy-MM-dd"), self.ire.text().strip()
        de = self.idet.toPlainText().strip()
        if not r: QMessageBox.warning(self, t("title_atencion"), t("msg_falta_resumen")); return
        full_desc = r
        if de: full_desc += f"\n{de}"
        if self.entry_foto_filename: full_desc += f"\n[FOTO: {self.entry_foto_filename}]"
        if self.entry_foto_despues_filename: full_desc += f"\n[FOTO_DESPUES: {self.entry_foto_despues_filename}]"
        lista_tags = []
        if self.chk_urgente.isChecked(): lista_tags.append("Urgente")
        if self.chk_electrico.isChecked(): lista_tags.append("Eléctrico")
        if self.chk_mecanico.isChecked(): lista_tags.append("Mecánico")
        if self.chk_prev.isChecked(): lista_tags.append("Preventivo")
        if self.chk_averia.isChecked(): lista_tags.append("Avería")
        manuales = self.itag.text().strip()
        if manuales: lista_tags.append(manuales)
        maquina_id = self.combo_maquina_entry.currentData()
        prioridad = self.combo_prioridad_entry.currentData()
        horas_paro = self.spin_horas_paro_entry.value() if self.chk_averia.isChecked() else None
        if self.db.agregar_tarea(d, full_desc, ", ".join(lista_tags), maquina_id=maquina_id, prioridad=prioridad, horas_paro=horas_paro):
            self.statusBar().showMessage(t("msg_registro_guardado"), 4000)
            self.ire.clear(); self.idet.clear(); self.itag.clear()
            self.chk_urgente.setChecked(False); self.chk_electrico.setChecked(False)
            self.chk_mecanico.setChecked(False); self.chk_prev.setChecked(False); self.chk_averia.setChecked(False)
            self.combo_maquina_entry.setCurrentIndex(0); self.combo_prioridad_entry.setCurrentIndex(1)
            self.borrar_foto_entry(); self.borrar_foto_entry_d(); self.refresh_all(); self.setup_autocompletado()
    def setup_autocompletado(self):
        d = self.db.obtener_todas_las_descripciones()
        c = QCompleter(d, self); c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); c.setFilterMode(Qt.MatchFlag.MatchContains)
        self.ire.setCompleter(c); self.in_todo_t.setCompleter(c)
    def init_calendar_tab(self):
        l = QHBoxLayout(); lp = QVBoxLayout(); th = QHBoxLayout()
        th.addWidget(QPushButton(t("btn_ir_hoy"), clicked=self.go_today)); th.addWidget(QPushButton(t("btn_gestion_dias"), clicked=lambda: self.gest_dias()))
        lp.addLayout(th); self.calendar = QCalendarWidget(); self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self.update_calendar_list); lp.addWidget(self.calendar); l.addLayout(lp, 60)
        rp = QVBoxLayout(); self.lbl_info = QLabel(t("lbl_info")); rp.addWidget(self.lbl_info)
        self.task_list = QListWidget(); self.configurar_deseleccion(self.task_list)
        self.task_list.itemDoubleClicked.connect(self.edit_cal); rp.addWidget(self.task_list); l.addLayout(rp, 40); self.tab_calendar.setLayout(l)
    def init_avisos_tab(self):
        l = QVBoxLayout()
        self.table_avisos = QTableWidget(0, 6)
        self.configurar_deseleccion(self.table_avisos); self.table_avisos.setHorizontalHeaderLabels([t("hdr_estado"), t("hdr_titulo"), t("hdr_frecuencia"), t("hdr_proxima"), t("hdr_sit"), t("hdr_asignado")])
        self.table_avisos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_avisos.setColumnWidth(3, 140)
        self.table_avisos.setColumnWidth(5, 160)
        self.table_avisos.cellDoubleClicked.connect(lambda r, c: self.edit_aviso())
        # Selección múltiple (Ctrl+Click, Shift+Click) + menú contextual para
        # eliminar o asignar varios avisos a la vez a un trabajador.
        # SelectRows es imprescindible: sin él, cada clic solo marca la celda
        # bajo el cursor y selectedRows() (que mira la columna 0, la del
        # checkbox) no ve como "seleccionadas" las filas donde se hizo clic
        # en otra columna (título, frecuencia...), así que el menú contextual
        # solo actuaría sobre la fila bajo el clic derecho.
        self.table_avisos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_avisos.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_avisos.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_avisos.customContextMenuRequested.connect(self._menu_contextual_avisos)
        l.addWidget(QLabel(t("lbl_gestion_avisos"))); l.addWidget(self.table_avisos)
        g = QGroupBox(t("lbl_crear_nuevo_aviso")); f = QGridLayout()
        self.in_av_t = QLineEdit(); self.in_av_t.setPlaceholderText(t("ph_titulo_aviso"))
        f.addWidget(QLabel(t("lbl_titulo")), 0, 0); f.addWidget(self.in_av_t, 0, 1)
        self.in_av_i = QDateEdit(); self.in_av_i.setCalendarPopup(True); self.in_av_i.setDate(QDate.currentDate()); self.in_av_i.setDisplayFormat("yyyy-MM-dd")
        f.addWidget(QLabel(t("lbl_inicio")), 0, 2); f.addWidget(self.in_av_i, 0, 3)
        self.in_av_freq = QComboBox(); self.in_av_freq.addItems([t("freq_anual"), t("freq_semestral"), t("freq_trimestral"), t("freq_mensual"), t("freq_semanal"), t("freq_diario")])
        f.addWidget(QLabel(t("lbl_repetir")), 1, 0); f.addWidget(self.in_av_freq, 1, 1)
        self.in_av_dur = QSpinBox(); self.in_av_dur.setRange(1, 60); self.in_av_dur.setValue(5); self.in_av_dur.setSuffix(" días")
        f.addWidget(QLabel(t("lbl_duracion")), 1, 2); f.addWidget(self.in_av_dur, 1, 3)
        self.in_av_asignar = QComboBox(); self._llenar_combo_usuarios(self.in_av_asignar, incluir_sin_asignar=True)
        f.addWidget(QLabel(tt("lbl_asignar_a", "Asignar a") + ":"), 2, 0); f.addWidget(self.in_av_asignar, 2, 1, 1, 3)
        self.in_av_especialidad = QComboBox(); self._llenar_combo_especialidades(self.in_av_especialidad)
        f.addWidget(QLabel(tt("usuarios_col_especialidad", "Especialidad") + ":"), 3, 0); f.addWidget(self.in_av_especialidad, 3, 1, 1, 3)
        b = QPushButton(t("btn_anadir_aviso")); b.clicked.connect(self.add_aviso); f.addWidget(b, 4, 0, 1, 4); g.setLayout(f); l.addWidget(g)
        self.grupo_crear_aviso = g
        bl = QHBoxLayout()
        self.btn_editar_aviso = QPushButton(t("btn_editar_seleccionado"), clicked=self.edit_aviso); bl.addWidget(self.btn_editar_aviso)
        self.btn_borrar_aviso = QPushButton(t("btn_borrar_seleccionado"), clicked=self.del_aviso); bl.addWidget(self.btn_borrar_aviso)
        l.addLayout(bl); self.tab_avisos.setLayout(l)
    def add_aviso(self):
        if not usuarios.es_admin(): return
        tit = self.in_av_t.text().strip(); i = self.in_av_i.date().toString("yyyy-MM-dd"); f = self.in_av_freq.currentText(); dur = self.in_av_dur.value()
        uid = self.in_av_asignar.currentData(); nombre = self.in_av_asignar.currentText() if uid is not None else None
        especialidad_id = self.in_av_especialidad.currentData()
        if tit and self.db.agregar_aviso(tit, i, f, dur, uid, nombre, especialidad_id): self.in_av_t.clear(); self.refresh_avisos(); self.update_calendar_list()
    def edit_aviso(self):
        if not usuarios.es_admin(): return
        r = self.table_avisos.currentRow()
        if r < 0: return
        id_aviso = self.table_avisos.item(r, 1).data(Qt.ItemDataRole.UserRole)
        avisos = self.db.obtener_avisos(); datos = next((a for a in avisos if a[0] == id_aviso), None)
        if datos:
            dlg = AvisoEditDialog(self, datos[1], datos[2], datos[3], datos[4], datos[6], datos[8])
            if dlg.exec():
                new_t, new_i, new_f, new_d, new_uid, new_nombre, new_especialidad = dlg.get_data()
                self.db.actualizar_aviso(id_aviso, new_t, new_i, new_f, new_d, new_uid, new_nombre, new_especialidad); self.refresh_avisos(); self.update_calendar_list()
    def _avisos_visibles(self):
        """Igual que en el móvil: el admin ve todos los avisos; cada
        trabajador ve los suyos más los que no están asignados a nadie
        (y, si no están asignados, coinciden con alguna de sus especialidades
        o no tienen ninguna), pero no los asignados a otro técnico ni los
        restringidos a una especialidad que no tiene."""
        avisos = self.db.obtener_avisos()
        if usuarios.es_admin():
            return avisos
        uid = usuarios.id_actual()
        especialidades = usuarios.especialidades_actuales()
        return [a for a in avisos if a[6] == uid or (a[6] is None and (a[8] is None or a[8] in especialidades))]

    def refresh_avisos(self):
        self.table_avisos.setRowCount(0)
        avisos = self._avisos_visibles()
        hoy = QDate.currentDate()
        es_admin = usuarios.es_admin()
        if hasattr(self, 'grupo_crear_aviso'): self.grupo_crear_aviso.setEnabled(es_admin)
        if hasattr(self, 'btn_editar_aviso'): self.btn_editar_aviso.setEnabled(es_admin)
        if hasattr(self, 'btn_borrar_aviso'): self.btn_borrar_aviso.setEnabled(es_admin)

        filas_calculadas = []
        for (aid, tit, finicio, freq, dur, ult, asignado_a, asignado_nombre, especialidad_id) in avisos:
            if not finicio: finicio = f"{hoy.year()}-01-01"
            if not freq: freq = "Anual"
            freq = idiomas.normalizar_frecuencia(freq)

            fi = QDate.fromString(finicio, "yyyy-MM-dd")
            ocurrencia = fi

            # Un aviso "Diario" se resetea cada día: no le aplicamos la duración
            # configurada, porque un margen de varios días haría que el de ayer
            # siguiera contando como "hecho" hoy.
            dur_ventana = 0 if freq == "Diario" else dur

            # Avanzamos la fecha hasta el ciclo actual
            while ocurrencia.addDays(dur_ventana) < hoy:
                if freq == "Diario": ocurrencia = ocurrencia.addDays(1)
                elif freq == "Semanal": ocurrencia = ocurrencia.addDays(7)
                elif freq == "Mensual": ocurrencia = ocurrencia.addMonths(1)
                elif freq == "Trimestral": ocurrencia = ocurrencia.addMonths(3)
                elif freq == "Semestral": ocurrencia = ocurrencia.addMonths(6)
                elif freq == "Anual": ocurrencia = ocurrencia.addYears(1)
                else: break

            fin_ocurrencia = ocurrencia.addDays(dur_ventana)

            # --- CORRECCIÓN CLAVE: RANGO FLEXIBLE ---
            s_inicio = ocurrencia.toString("yyyy-MM-dd")
            s_fin = fin_ocurrencia.toString("yyyy-MM-dd")

            es_activo = (ocurrencia <= hoy <= fin_ocurrencia)
            completado = False

            # Si hay fecha de última completada (ult), comprobamos si cae DENTRO del rango
            # Antes comprobábamos si era EXACTAMENTE igual al inicio (ult == s_inicio)
            if ult:
                if ult >= s_inicio and ult <= s_fin:
                    completado = True

            # Colores de estado: azul=futuro, rojo=pendiente, verde=realizado
            color = QColor("#2e86c1")  # Azul (futuro)
            estado_txt = t("estado_futuro")
            prioridad = 1  # Futuro

            if es_activo:
                if completado:
                    color = QColor("#27ae60") # Verde
                    estado_txt = t("estado_ok")
                    prioridad = 2
                else:
                    color = QColor("#cb4335") # Rojo (un poco más oscuro)
                    estado_txt = t("estado_pendiente")
                    prioridad = 0  # Pendiente/sin hacer: va primero
            elif completado:
                 color = QColor("#27ae60")
                 estado_txt = t("estado_ok")
                 prioridad = 2

            filas_calculadas.append({
                "aid": aid, "tit": tit, "freq": freq, "ocurrencia": ocurrencia,
                "fin_ocurrencia": fin_ocurrencia, "s_inicio": s_inicio,
                "es_activo": es_activo, "completado": completado,
                "color": color, "estado_txt": estado_txt, "prioridad": prioridad,
                "asignado_nombre": asignado_nombre,
            })

        # Pendientes/sin hacer primero; dentro de cada grupo, por fecha de ocurrencia
        filas_calculadas.sort(key=lambda f: (f["prioridad"], f["ocurrencia"]))

        self.table_avisos.setRowCount(len(filas_calculadas))
        patron_qt = idiomas.formato_fecha_corta_qt()
        for r, f in enumerate(filas_calculadas):
            aid, tit, freq = f["aid"], f["tit"], f["freq"]
            ocurrencia, fin_ocurrencia = f["ocurrencia"], f["fin_ocurrencia"]
            s_inicio, es_activo, completado = f["s_inicio"], f["es_activo"], f["completado"]
            color, estado_txt = f["color"], f["estado_txt"]
            asignado_nombre = f["asignado_nombre"]

            # Configurar celda
            cw = QWidget()
            cl = QHBoxLayout(cw); cl.setContentsMargins(0,0,0,0); cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(completado)
            # Al marcar manual en PC, seguimos usando el inicio para mantener el orden
            chk.toggled.connect(lambda k, x=aid, d=s_inicio, t=tit: self.tog_aviso(x, d, k, t))
            chk.setEnabled(es_activo or completado)
            cl.addWidget(chk)
            self.table_avisos.setCellWidget(r, 0, cw)

            # Rellenar fila
            item_t = QTableWidgetItem(tit)
            item_t.setData(Qt.ItemDataRole.UserRole, aid)

            self.table_avisos.setItem(r, 1, item_t)
            self.table_avisos.setItem(r, 2, QTableWidgetItem(freq))

            rango = f"{ocurrencia.toString(patron_qt)} - {fin_ocurrencia.toString(patron_qt)}"
            self.table_avisos.setItem(r, 3, QTableWidgetItem(rango))

            item_estado = QTableWidgetItem(estado_txt)
            item_estado.setForeground(color)
            self.table_avisos.setItem(r, 4, item_estado)

            texto_asignado = asignado_nombre if asignado_nombre else tt("lbl_sin_asignar", "Sin asignar")
            self.table_avisos.setItem(r, 5, QTableWidgetItem(texto_asignado))

    def tog_aviso(self, id_aviso, fecha_ocurrencia, estado, titulo):
        # Actualizar fecha última completada
        self.db.marcar_aviso_completado(id_aviso, fecha_ocurrencia, estado)

        desc_historial = f"Mantenimiento Preventivo: {titulo}"

        if estado:
            # MARCADO -> Añadir al historial
            tags = "Preventivo, Aviso Recurrente"
            self.db.agregar_tarea(fecha_ocurrencia, desc_historial, tags)
            self.statusBar().showMessage(t("msg_guardado_historial").format(titulo=titulo), 3000)
            self.statusBar().showMessage(f"🗑️ Eliminado del historial: {titulo}", 3000)
        else:
            # DESMARCADO -> Borrar del historial
            try:
                with get_db_connection(self.db.db_name) as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM tareas WHERE fecha=? AND descripcion=?", (fecha_ocurrencia, desc_historial))
                    conn.commit()
                self.statusBar().showMessage(t("msg_eliminado_historial").format(titulo=titulo), 3000)
            except Exception as e:
                print(f"Error borrando historial: {e}")

        self.refresh_avisos()
        self.update_calendar_list()
        self.refresh_history()
        self.refresh_dashboard()

    def del_aviso(self):
        if not usuarios.es_admin(): return
        seleccion = self.table_avisos.selectionModel().selectedRows()
        if not seleccion:
            return
        ids = [self.table_avisos.item(idx.row(), 1).data(Qt.ItemDataRole.UserRole) for idx in seleccion]
        self._borrar_avisos_masivo(ids)

    def _menu_contextual_avisos(self, pos):
        """Menú con clic derecho sobre la tabla de avisos: eliminar o asignar a un trabajador."""
        if not usuarios.es_admin(): return
        # Si se hace clic derecho directamente (sin haber seleccionado antes con
        # el izquierdo), seleccionamos la fila bajo el cursor para no dejar el
        # menú sin acciones sobre las que actuar.
        if not self.table_avisos.selectionModel().selectedRows():
            fila = self.table_avisos.rowAt(pos.y())
            if fila >= 0:
                self.table_avisos.selectRow(fila)
        seleccion = self.table_avisos.selectionModel().selectedRows()
        if not seleccion:
            return
        ids = [self.table_avisos.item(idx.row(), 1).data(Qt.ItemDataRole.UserRole) for idx in seleccion]
        n = len(ids)

        menu = QMenu(self)
        texto_asignar = tt("ctx_asignar_avisos", "👤 Asignar a...") if n == 1 else \
                         tt("ctx_asignar_avisos_n", "👤 Asignar a... ({n} avisos)").format(n=n)
        menu.addAction(texto_asignar, lambda: self._asignar_avisos_masivo(ids))

        menu.addSeparator()

        texto_borrar = tt("ctx_eliminar_avisos", "🗑️ Eliminar") if n == 1 else \
                        tt("ctx_eliminar_avisos_n", "🗑️ Eliminar ({n} avisos)").format(n=n)
        menu.addAction(texto_borrar, lambda: self._borrar_avisos_masivo(ids))

        menu.exec(self.table_avisos.viewport().mapToGlobal(pos))

    def _borrar_avisos_masivo(self, ids):
        """Borra uno o varios avisos recurrentes, previa confirmación."""
        if not usuarios.es_admin(): return
        if not ids:
            return
        n = len(ids)
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(t("title_borrar_aviso"))
        msg.setText(t("msg_confirmar_borrar_aviso") if n == 1 else
                    tt("msg_confirmar_borrar_avisos_n", "¿Estás seguro de borrar estos {n} avisos recurrentes definitivamente?").format(n=n))

        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)

        msg.exec()

        if msg.clickedButton() == btn_si:
            for id_aviso in ids:
                self.db.borrar_aviso(id_aviso)
            self.refresh_avisos()
            self.update_calendar_list()

    def _asignar_avisos_masivo(self, ids):
        """Asigna uno o varios avisos recurrentes a un trabajador y/o a una
        especialidad (o los deja sin asignar), de forma independiente: si solo
        se marca la especialidad, el técnico ya asignado no se toca, y viceversa."""
        if not usuarios.es_admin(): return
        if not ids:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tt("lbl_asignar_a", "Asignar a"))
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(
            tt("lbl_asignar_avisos_a", "Asignar {n} aviso(s) a:").format(n=len(ids))))

        chk_tecnico = QCheckBox(tt("chk_cambiar_tecnico", "Cambiar técnico asignado"))
        lay.addWidget(chk_tecnico)
        combo = QComboBox()
        self._llenar_combo_usuarios(combo, incluir_sin_asignar=True)
        combo.setEnabled(False)
        chk_tecnico.toggled.connect(combo.setEnabled)
        lay.addWidget(combo)

        chk_especialidad = QCheckBox(tt("chk_cambiar_especialidad", "Cambiar especialidad"))
        lay.addWidget(chk_especialidad)
        combo_esp = QComboBox()
        self._llenar_combo_especialidades(combo_esp)
        combo_esp.setEnabled(False)
        chk_especialidad.toggled.connect(combo_esp.setEnabled)
        lay.addWidget(combo_esp)

        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        caja.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        caja.accepted.connect(dlg.accept)
        caja.rejected.connect(dlg.reject)
        lay.addWidget(caja)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        if not chk_tecnico.isChecked() and not chk_especialidad.isChecked():
            return

        uid = combo.currentData()
        nombre = combo.currentText() if uid is not None else None
        especialidad_id = combo_esp.currentData()
        for id_aviso in ids:
            if chk_tecnico.isChecked():
                self.db.asignar_aviso(id_aviso, uid, nombre)
            if chk_especialidad.isChecked():
                self.db.asignar_especialidad_aviso(id_aviso, especialidad_id)
        self.refresh_avisos()

    def init_history_tab(self):
        l = QHBoxLayout() # Layout contenedor principal

        # Crear el separador arrastrable horizontal
        self.splitter_history = QSplitter(Qt.Orientation.Horizontal)

        # PANEL IZQUIERDO: Árbol de fechas
        left_widget = QWidget()
        left_panel = QVBoxLayout(left_widget)
        left_panel.setContentsMargins(0, 0, 0, 0)

        btn_layout = QHBoxLayout()
        btn_expand = QPushButton("🠇")
        btn_expand.setToolTip("Desplegar todas las ramas")
        btn_expand.setFixedWidth(35)
        btn_collapse = QPushButton("🠅")
        btn_collapse.setToolTip("Plegar todas las ramas")
        btn_collapse.setFixedWidth(35)

        btn_expand.clicked.connect(lambda: self.tree_history.expandAll())
        btn_collapse.clicked.connect(lambda: self.tree_history.collapseAll())

        btn_layout.addWidget(btn_expand)
        btn_layout.addWidget(btn_collapse)
        btn_layout.addStretch()  # Empuja los botones compactos a la izquierda
        left_panel.addLayout(btn_layout)

        self.tree_history = QTreeWidget()
        self.tree_history.setHeaderHidden(True)
        self.tree_history.itemClicked.connect(self.on_tree_history_clicked)
        left_panel.addWidget(self.tree_history)

        # PANEL DERECHO: Tabla
        right_widget = QWidget()
        right_panel = QVBoxLayout(right_widget)
        right_panel.setContentsMargins(0, 0, 0, 0)

        fila_usuario = QHBoxLayout()
        fila_usuario.addWidget(QLabel(tt("hdr_realizado_por", "Realizado por") + ":"))
        self.combo_filtro_historial = QComboBox()
        self.combo_filtro_historial.currentIndexChanged.connect(self.aplicar_filtros_historial)
        fila_usuario.addWidget(self.combo_filtro_historial, 1)

        fila_usuario.addWidget(QLabel(tt("hdr_tipo_historial", "Tipo") + ":"))
        self.combo_filtro_tipo_historial = QComboBox()
        self.combo_filtro_tipo_historial.addItem(tt("filtro_todos", "Todos"), "TODOS")
        self.combo_filtro_tipo_historial.addItem(tt("filtro_trabajos_averias", "Trabajos y averías"), "TRABAJOS")
        self.combo_filtro_tipo_historial.addItem(tt("filtro_avisos_preventivos", "Avisos preventivos"), "PREVENTIVOS")
        self.combo_filtro_tipo_historial.currentIndexChanged.connect(self.aplicar_filtros_historial)
        fila_usuario.addWidget(self.combo_filtro_tipo_historial, 1)

        right_panel.addLayout(fila_usuario)

        self.h_table = QTableWidget()
        self.configurar_deseleccion(self.h_table)
        self.setup_table(self.h_table)
        # La columna TAGS se sigue guardando y coloreando las filas, pero no se muestra
        self.h_table.setColumnHidden(2, True)
        # Selección múltiple (Ctrl+Click, Shift+Click) + menú contextual
        self.h_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.h_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.h_table.customContextMenuRequested.connect(self._menu_contextual_historial)
        self.h_table.cellDoubleClicked.connect(lambda r, c: self.edit_rec(self.h_table))
        right_panel.addWidget(self.h_table)

        bl = QHBoxLayout()
        bl.addWidget(QPushButton(t("btn_editar"), clicked=lambda: self.edit_rec(self.h_table)))
        bl.addWidget(QPushButton(t("btn_borrar_seleccionado"), clicked=lambda: self.del_rec(self.h_table)))
        right_panel.addLayout(bl)

        # Añadir paneles al splitter arrastrable
        self.splitter_history.addWidget(left_widget)
        self.splitter_history.addWidget(right_widget)

        # Proporción inicial orientativa (se ajusta al arrastrar con el ratón)
        self.splitter_history.setSizes([100,900])

        l.addWidget(self.splitter_history)
        self.tab_history.setLayout(l)

    def on_tree_history_clicked(self, item, column):
        self._filtro_fecha_historial = item.data(0, Qt.ItemDataRole.UserRole)
        self.aplicar_filtros_historial()

    def aplicar_filtros_historial(self, *_):
        """Combina el filtro de fecha (árbol), el de técnico (combo) y el de tipo (trabajos/averías vs. avisos preventivos)."""
        filtro_fecha = getattr(self, '_filtro_fecha_historial', "TODO") or "TODO"
        filtro_usuario = self.combo_filtro_historial.currentData() if hasattr(self, 'combo_filtro_historial') else "TODOS"
        filtro_tipo = self.combo_filtro_tipo_historial.currentData() if hasattr(self, 'combo_filtro_tipo_historial') else "TODOS"
        visibles = 0

        for row in range(self.h_table.rowCount()):
            item_fecha = self.h_table.item(row, 0)
            if not item_fecha: continue
            mostrar = True

            # El filtro puede ser "2026" (año) o "2026-07" (año-mes)
            if filtro_fecha != "TODO" and not item_fecha.text().startswith(filtro_fecha):
                mostrar = False

            if mostrar and filtro_usuario not in (None, "TODOS"):
                item_usuario = self.h_table.item(row, 3)
                if not item_usuario or item_usuario.text() != filtro_usuario:
                    mostrar = False

            if mostrar and filtro_tipo not in (None, "TODOS"):
                item_tags = self.h_table.item(row, 2)
                tags_crudas = item_tags.data(Qt.ItemDataRole.UserRole) if item_tags else ""
                es_preventivo = "Aviso Recurrente" in (tags_crudas or "")
                if filtro_tipo == "PREVENTIVOS" and not es_preventivo:
                    mostrar = False
                elif filtro_tipo == "TRABAJOS" and es_preventivo:
                    mostrar = False

            self.h_table.setRowHidden(row, not mostrar)
            if mostrar: visibles += 1

        if filtro_usuario not in (None, "TODOS") or filtro_tipo not in (None, "TODOS"):
            self.statusBar().showMessage(t("msg_mostrando_resultados").format(n=visibles), 3000)

    def recargar_combo_historial(self):
        """Rellena el combo con los autores que aparecen realmente en el histórico."""
        if not hasattr(self, 'combo_filtro_historial'): return
        anterior = self.combo_filtro_historial.currentData()
        nombres = set()
        try:
            conn = self.db.conectar(); c = conn.cursor()
            c.execute("SELECT DISTINCT COALESCE(usuario_nombre,'') FROM tareas")
            nombres = {r[0] for r in c.fetchall() if r[0]}
            conn.close()
        except Exception:
            pass
        self.combo_filtro_historial.blockSignals(True)
        self.combo_filtro_historial.clear()
        self.combo_filtro_historial.addItem(tt("filtro_todos", "Todos"), "TODOS")
        for n in sorted(nombres):
            self.combo_filtro_historial.addItem(n, n)
        idx = self.combo_filtro_historial.findData(anterior)
        self.combo_filtro_historial.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_filtro_historial.blockSignals(False)
    def init_search_tab(self):
        l = QVBoxLayout(); sl = QHBoxLayout()
        self.s_in = QLineEdit(); self.s_in.setPlaceholderText(t("ph_buscar_texto")); self.s_in.textChanged.connect(self.search); sl.addWidget(self.s_in)
        self.s_chk_date = QCheckBox("📅 Fecha:"); self.s_chk_date.toggled.connect(lambda: self.s_date.setEnabled(self.s_chk_date.isChecked())); self.s_chk_date.toggled.connect(self.search); sl.addWidget(self.s_chk_date)
        self.s_date = QDateEdit(); self.s_date.setCalendarPopup(True); self.s_date.setDate(QDate.currentDate()); self.s_date.setDisplayFormat("yyyy-MM-dd"); self.s_date.setEnabled(False); self.s_date.dateChanged.connect(self.search); sl.addWidget(self.s_date); l.addLayout(sl)
        fl = QHBoxLayout(); fl.setSpacing(20)
        self.chk_s_urg = QCheckBox(f"🚨 {t('tag_urgente')}"); self.chk_s_elec = QCheckBox(f"⚡ {t('tag_electrico')}"); self.chk_s_mec = QCheckBox(f"⚙️ {t('tag_mecanico')}"); self.chk_s_prev = QCheckBox(f"🛡️ {t('tag_preventivo')}")
        for chk in [self.chk_s_urg, self.chk_s_elec, self.chk_s_mec, self.chk_s_prev]: chk.setStyleSheet(_estilo_check_etiqueta()); chk.toggled.connect(self.search); fl.addWidget(chk)
        fl.addStretch(); l.addLayout(fl)
        self.s_table = QTableWidget(); self.setup_table(self.s_table); self.configurar_deseleccion(self.s_table); self.s_table.cellDoubleClicked.connect(lambda r, c: self.edit_rec(self.s_table)); l.addWidget(self.s_table)
        bl = QHBoxLayout(); bl.addWidget(QPushButton(t("btn_editar"), clicked=lambda: self.edit_rec(self.s_table))); bl.addWidget(QPushButton(t("btn_borrar_seleccionado"), clicked=lambda: self.del_rec(self.s_table))); l.addLayout(bl); self.tab_search.setLayout(l)
    def _llenar_combo_especialidades(self, combo, incluir_ninguna=True):
        """Rellena un combo con el catálogo de especialidades, conservando la selección."""
        anterior = combo.currentData() if combo.count() > 0 else "__SIN_SELECCION_PREVIA__"
        combo.blockSignals(True)
        combo.clear()
        if incluir_ninguna:
            combo.addItem(tt("especialidades_ninguna", "Sin especialidad"), None)
        for e in usuarios.listar_especialidades():
            combo.addItem(e["nombre"], e["id"])
        idx = combo.findData(anterior)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def _llenar_combo_usuarios(self, combo, incluir_todos=False, incluir_sin_asignar=False):
        """Rellena un combo con los usuarios activos, conservando la selección."""
        # Si el combo aún no tenía nada cargado (primer llenado), no hay
        # selección previa real que conservar: usamos un centinela que no
        # coincide con ningún dato, para no confundir "sin selección" con
        # "Sin asignar" (ambos usan None como dato) y así caer en el índice 0.
        anterior = combo.currentData() if combo.count() > 0 else "__SIN_SELECCION_PREVIA__"
        combo.blockSignals(True)
        combo.clear()
        if incluir_todos:
            combo.addItem(tt("filtro_todos", "Todos"), "TODOS")
        if incluir_sin_asignar:
            combo.addItem(tt("lbl_sin_asignar", "Sin asignar"), None)
        for u in usuarios.listar_usuarios(incluir_inactivos=False):
            combo.addItem(u["nombre"], u["id"])
        idx = combo.findData(anterior)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def init_todo_tab(self):
        l = QHBoxLayout(); ll = QVBoxLayout(); ll.addWidget(QLabel(t("lbl_lista_pendientes")))
        fila_filtro = QHBoxLayout()
        fila_filtro.addWidget(QLabel(tt("lbl_ver_de", "Ver los de") + ":"))
        self.combo_filtro_todos = QComboBox()
        self._llenar_combo_usuarios(self.combo_filtro_todos, incluir_todos=True, incluir_sin_asignar=True)
        self.combo_filtro_todos.currentIndexChanged.connect(self.refresh_todos)
        fila_filtro.addWidget(self.combo_filtro_todos, 1)
        ll.addLayout(fila_filtro)
        self.todo_list = QListWidget(); self.configurar_deseleccion(self.todo_list); self.todo_list.setAlternatingRowColors(True)
        self.todo_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.todo_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.todo_list.customContextMenuRequested.connect(self._menu_contextual_todos)
        self.todo_list.itemDoubleClicked.connect(self.edit_todo); ll.addWidget(self.todo_list); l.addLayout(ll, 60)
        rl = QVBoxLayout(); g = QGroupBox(t("lbl_nuevo_trabajo")); f = QVBoxLayout()
        self.in_todo_t = QLineEdit(); self.in_todo_t.setPlaceholderText(t("ph_titulo")); f.addWidget(self.in_todo_t)
        self.in_todo_d = QTextEdit(); self.in_todo_d.setPlaceholderText(t("ph_detalles")); self.in_todo_d.setMaximumHeight(100); f.addWidget(self.in_todo_d)
        fila_asig = QHBoxLayout()
        fila_asig.addWidget(QLabel(tt("lbl_asignar_a", "Asignar a") + ":"))
        self.combo_asignar = QComboBox()
        self._llenar_combo_usuarios(self.combo_asignar, incluir_sin_asignar=True)
        fila_asig.addWidget(self.combo_asignar, 1)
        f.addLayout(fila_asig)
        fila_especialidad_todo = QHBoxLayout()
        fila_especialidad_todo.addWidget(QLabel(tt("usuarios_col_especialidad", "Especialidad") + ":"))
        self.combo_especialidad_todo = QComboBox()
        self._llenar_combo_especialidades(self.combo_especialidad_todo)
        fila_especialidad_todo.addWidget(self.combo_especialidad_todo, 1)
        f.addLayout(fila_especialidad_todo)
        fila_prioridad_todo = QHBoxLayout()
        fila_prioridad_todo.addWidget(QLabel(tt("lbl_prioridad", "Prioridad") + ":"))
        self.combo_prioridad_todo = QComboBox()
        for cod, clave in (("Baja", "prioridad_baja"), ("Media", "prioridad_media"), ("Alta", "prioridad_alta"), ("Crítica", "prioridad_critica")):
            self.combo_prioridad_todo.addItem(tt(clave, cod), cod)
        self.combo_prioridad_todo.setCurrentIndex(1)
        fila_prioridad_todo.addWidget(self.combo_prioridad_todo, 1)
        f.addLayout(fila_prioridad_todo)
        f.addWidget(QPushButton(t("btn_anadir"), clicked=self.add_todo)); g.setLayout(f); rl.addWidget(g)
        ga = QGroupBox(t("lbl_acciones")); fa = QVBoxLayout()
        b_ok = QPushButton(t("btn_completar"), clicked=self.complete_todo); b_ok.setStyleSheet("background-color:#27ae60; color: white;"); fa.addWidget(b_ok)
        b_edit = QPushButton(t("btn_editar"), clicked=self.edit_todo); b_edit.setStyleSheet("background-color:#2980b9; color: white;"); fa.addWidget(b_edit)
        b_del = QPushButton(t("btn_eliminar"), clicked=self.del_todo); b_del.setStyleSheet("background-color:#c0392b; color: white;"); fa.addWidget(b_del)
        self.b_asig_todo = QPushButton(tt("btn_reasignar", "👤 Reasignar"), clicked=self.reasignar_todo)
        self.b_asig_todo.setStyleSheet("background-color:#8e44ad; color: white;"); fa.addWidget(self.b_asig_todo)
        ga.setLayout(fa); rl.addWidget(ga); l.addLayout(rl, 40); self.tab_todo.setLayout(l)

    # ==========================================
    # MÁQUINAS
    # ==========================================
    def init_maquinas_tab(self):
        l = QVBoxLayout()
        h_tools = QHBoxLayout()
        b_nueva = QPushButton(tt("btn_nueva_maquina", "➕ Nueva máquina")); b_nueva.clicked.connect(self._maquina_nueva)
        b_nueva_sub = QPushButton(tt("btn_nueva_submaquina", "➕ Nueva submáquina")); b_nueva_sub.clicked.connect(self._maquina_nueva_sub)
        b_editar = QPushButton(tt("btn_editar_maquina", "✏️ Editar")); b_editar.clicked.connect(self._maquina_editar)
        b_eliminar = QPushButton(tt("btn_eliminar_maquina", "🗑️ Eliminar")); b_eliminar.setStyleSheet("background-color:#c0392b; color: white;"); b_eliminar.clicked.connect(self._maquina_eliminar)
        b_expandir = QPushButton(tt("btn_expandir_todo", "⬇️ Expandir todo")); b_expandir.clicked.connect(self._maquinas_expandir_todo)
        b_contraer = QPushButton(tt("btn_contraer_todo", "⬆️ Contraer todo"))
        for b in [b_nueva, b_nueva_sub, b_editar, b_eliminar, b_expandir, b_contraer]: h_tools.addWidget(b)
        h_tools.addStretch()
        l.addLayout(h_tools)

        h_cuerpo = QHBoxLayout()
        self.arbol_maquinas = QTreeWidget()
        self.arbol_maquinas.setColumnCount(4)
        self.arbol_maquinas.setHeaderLabels([tt("hdr_maquina", "Máquina"), tt("hdr_trabajos", "Trabajos"), tt("hdr_fecha_maquina", "Fecha"), tt("hdr_zona", "Zona")])
        self.arbol_maquinas.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.arbol_maquinas.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.arbol_maquinas.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.arbol_maquinas.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.arbol_maquinas.setSortingEnabled(True)
        self.arbol_maquinas.itemExpanded.connect(self._maquina_item_expandido)
        self.arbol_maquinas.itemDoubleClicked.connect(self._maquina_item_doble_click)
        self.arbol_maquinas.currentItemChanged.connect(self._maquina_mostrar_foto_seleccionada)
        h_cuerpo.addWidget(self.arbol_maquinas, 65)
        b_contraer.clicked.connect(self.arbol_maquinas.collapseAll)

        v_foto = QVBoxLayout()
        v_foto.addWidget(QLabel(tt("lbl_foto_maquina", "Foto de la máquina")))
        self.lbl_foto_maquina = QLabel(tt("lbl_sin_foto", "Sin foto"))
        self.lbl_foto_maquina.setMinimumSize(220, 220)
        self.lbl_foto_maquina.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto_maquina.setStyleSheet(_estilo_zona_arrastre())
        v_foto.addWidget(self.lbl_foto_maquina)

        self.lbl_indicadores_maquina = QLabel("")
        self.lbl_indicadores_maquina.setWordWrap(True)
        self.lbl_indicadores_maquina.setStyleSheet("padding: 6px; font-size: 12px;")
        v_foto.addWidget(self.lbl_indicadores_maquina)

        v_foto.addStretch(1)  # empuja el bloque de la gráfica hacia abajo
        v_foto.addWidget(QLabel(tt("lbl_grafico_trabajos_maquina", "Trabajos por máquina")))

        h_grafico = QHBoxLayout()
        self.grafico_trabajos_maquina = GraficoCircularTrabajos()
        h_grafico.addWidget(self.grafico_trabajos_maquina, 1)
        v_combo_anio = QVBoxLayout()
        v_combo_anio.addWidget(QLabel(tt("lbl_anio_grafico", "Año:")))
        self.combo_anio_grafico = QComboBox()
        self.combo_anio_grafico.currentIndexChanged.connect(self._actualizar_grafico_trabajos)
        v_combo_anio.addWidget(self.combo_anio_grafico)
        v_combo_anio.addWidget(QLabel(tt("lbl_zona_grafico", "Zona:")))
        self.combo_zona_grafico = QComboBox()
        self.combo_zona_grafico.currentIndexChanged.connect(self._actualizar_grafico_trabajos)
        v_combo_anio.addWidget(self.combo_zona_grafico)
        v_combo_anio.addStretch()
        h_grafico.addLayout(v_combo_anio)
        v_foto.addLayout(h_grafico)

        v_foto.addStretch(1)
        h_cuerpo.addLayout(v_foto, 35)

        l.addLayout(h_cuerpo)
        self.tab_maquinas.setLayout(l)
        self.refrescar_arbol_maquinas()

    def _maquina_mostrar_foto_seleccionada(self, *args):
        item = self.arbol_maquinas.currentItem()
        datos = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        ruta = None
        if datos and datos.get("tipo") == "maquina":
            maquina = maquinas.obtener_maquina(datos["id"])
            if maquina and maquina.get("foto"):
                ruta = os.path.join(self.carpeta_fotos, maquina["foto"])
        if ruta and os.path.exists(ruta):
            pix = QPixmap(ruta)
            if not pix.isNull():
                self.lbl_foto_maquina.setPixmap(pix.scaled(self.lbl_foto_maquina.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_foto_maquina.setStyleSheet("border: 2px solid #3daee9; background-color: #000;")
            else:
                self.lbl_foto_maquina.setPixmap(QPixmap()); self.lbl_foto_maquina.setText(tt("lbl_sin_foto", "Sin foto"))
                self.lbl_foto_maquina.setStyleSheet(_estilo_zona_arrastre())
        else:
            self.lbl_foto_maquina.setPixmap(QPixmap()); self.lbl_foto_maquina.setText(tt("lbl_sin_foto", "Sin foto"))
            self.lbl_foto_maquina.setStyleSheet(_estilo_zona_arrastre())
        self._actualizar_indicadores_maquina(datos["id"] if datos and datos.get("tipo") == "maquina" else None)

    def _actualizar_indicadores_maquina(self, id_maquina):
        """Muestra MTBF/MTTR de la máquina seleccionada (y sus submáquinas)."""
        if not hasattr(self, 'lbl_indicadores_maquina'):
            return
        if id_maquina is None:
            self.lbl_indicadores_maquina.setText("")
            return
        ind = maquinas.indicadores_fiabilidad(id_maquina)
        if ind["num_averias"] == 0 or ind["mtbf_dias"] is None:
            self.lbl_indicadores_maquina.setText(
                f"<b>{tt('lbl_indicadores_fiabilidad', 'Indicadores de fiabilidad')}</b><br>"
                f"{tt('lbl_num_averias', 'Averías registradas')}: {ind['num_averias']}<br>"
                f"<i>{tt('msg_sin_datos_fiabilidad', 'Aún no hay averías suficientes para calcular indicadores.')}</i>"
            )
            return
        mtbf_txt = tt("fmt_dias", "{n:.1f} días").format(n=ind["mtbf_dias"])
        partes = [
            f"<b>{tt('lbl_indicadores_fiabilidad', 'Indicadores de fiabilidad')}</b>",
            f"{tt('lbl_num_averias', 'Averías registradas')}: {ind['num_averias']}",
            f"{tt('lbl_mtbf', 'MTBF (tiempo medio entre averías)')}: {mtbf_txt}",
        ]
        if ind["mttr_horas"] is not None:
            mttr_txt = tt("fmt_horas", "{n:.1f} horas").format(n=ind["mttr_horas"])
            partes.append(f"{tt('lbl_mttr', 'MTTR (tiempo medio de reparación)')}: {mttr_txt}")
        self.lbl_indicadores_maquina.setText("<br>".join(partes))

    def refrescar_arbol_maquinas(self):
        item_actual = self.arbol_maquinas.currentItem()
        id_seleccionado = item_actual.data(0, Qt.ItemDataRole.UserRole)["id"] if item_actual else None
        self.arbol_maquinas.setSortingEnabled(False)
        self.arbol_maquinas.clear()
        todas = maquinas.listar_maquinas()
        por_padre = {}
        for m in todas:
            por_padre.setdefault(m["padre_id"], []).append(m)
        for m in por_padre.get(None, []):
            item = self._crear_nodo_maquina(m)
            self.arbol_maquinas.addTopLevelItem(item)
            if id_seleccionado == m["id"]:
                self.arbol_maquinas.setCurrentItem(item)
        self.arbol_maquinas.setSortingEnabled(True)

        self._refrescar_combo_anio_grafico()
        self._refrescar_combo_zona_grafico()
        self._actualizar_grafico_trabajos()

    def _colores_arbol_maquinas(self):
        """Colores para diferenciar máquinas, años y zonas en el árbol, acordes al tema activo."""
        oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
        col_maquina = QColor("#5fa8e8") if oscuro else QColor("#0d3862")
        col_anio = QColor("#e0b34d") if oscuro else QColor("#8a6210")
        col_zona = QColor("#c98be0") if oscuro else QColor("#6a2d8a")
        return col_maquina, col_anio, col_zona

    def _crear_nodo_maquina(self, maquina):
        total = maquinas.contar_trabajos(maquina["id"])
        item = _ItemArbolOrdenable([maquina["nombre"], str(total), "", maquina.get("zona_nombre") or ""])
        item.setData(1, Qt.ItemDataRole.UserRole + 1, total)
        item.setData(0, Qt.ItemDataRole.UserRole, {"tipo": "maquina", "id": maquina["id"], "cargado": False})
        col_maquina, _, col_zona = self._colores_arbol_maquinas()
        item.setForeground(0, col_maquina)
        item.setForeground(3, col_zona)
        item.addChild(_ItemArbolOrdenable([""]))  # hijo ficticio para mostrar la flecha de expandir
        return item

    def _maquina_item_expandido(self, item):
        datos = item.data(0, Qt.ItemDataRole.UserRole)
        if not datos or datos.get("cargado"):
            return
        item.takeChildren()
        tipo = datos["tipo"]
        if tipo == "maquina":
            por_padre = {}
            for m in maquinas.listar_maquinas():
                por_padre.setdefault(m["padre_id"], []).append(m)
            for sub in por_padre.get(datos["id"], []):
                item.addChild(self._crear_nodo_maquina(sub))
            _, col_anio, _ = self._colores_arbol_maquinas()
            for anio, cnt in maquinas.anios_de_maquina(datos["id"]):
                nodo = _ItemArbolOrdenable([anio, str(cnt), ""])
                nodo.setData(1, Qt.ItemDataRole.UserRole + 1, cnt)
                nodo.setData(0, Qt.ItemDataRole.UserRole, {"tipo": "anio", "id": datos["id"], "anio": anio, "cargado": False})
                nodo.setForeground(0, col_anio)
                nodo.addChild(_ItemArbolOrdenable([""]))
                item.addChild(nodo)
        elif tipo == "anio":
            for trabajo in maquinas.trabajos_de_maquina_anio(datos["id"], datos["anio"]):
                resumen = trabajo["descripcion"].splitlines()[0] if trabajo["descripcion"] else ""
                fecha_fmt = self._formatear_fecha_corta(trabajo["fecha"])
                nodo = _ItemArbolOrdenable([resumen, "", fecha_fmt])
                nodo.setData(2, Qt.ItemDataRole.UserRole + 1, trabajo["fecha"])
                nodo.setData(0, Qt.ItemDataRole.UserRole, {"tipo": "trabajo", "id": trabajo["id"], "cargado": True})
                item.addChild(nodo)
        datos["cargado"] = True
        item.setData(0, Qt.ItemDataRole.UserRole, datos)

    def _refrescar_combo_anio_grafico(self):
        """Rellena el desplegable de años del gráfico, conservando la selección actual si sigue existiendo."""
        anio_actual = self.combo_anio_grafico.currentData()
        self.combo_anio_grafico.blockSignals(True)
        self.combo_anio_grafico.clear()
        self.combo_anio_grafico.addItem(tt("opcion_todos_los_anios", "TODOS"), None)
        for anio in maquinas.anios_disponibles():
            self.combo_anio_grafico.addItem(anio, anio)
        indice = self.combo_anio_grafico.findData(anio_actual)
        self.combo_anio_grafico.setCurrentIndex(indice if indice >= 0 else 0)
        self.combo_anio_grafico.blockSignals(False)

    def _refrescar_combo_zona_grafico(self):
        """Rellena el desplegable de zonas del gráfico, conservando la selección actual si sigue existiendo."""
        zona_actual = self.combo_zona_grafico.currentData()
        self.combo_zona_grafico.blockSignals(True)
        self.combo_zona_grafico.clear()
        self.combo_zona_grafico.addItem(tt("opcion_todas_las_zonas", "TODAS"), None)
        for z in maquinas.zonas_disponibles():
            self.combo_zona_grafico.addItem(z["nombre"], z["id"])
        indice = self.combo_zona_grafico.findData(zona_actual)
        self.combo_zona_grafico.setCurrentIndex(indice if indice >= 0 else 0)
        self.combo_zona_grafico.blockSignals(False)

    def _actualizar_grafico_trabajos(self):
        """Recalcula el gráfico circular de trabajos por máquina según el año y la zona elegidos
        en los desplegables, sumando en cada máquina de nivel superior los trabajos de sus submáquinas."""
        anio = self.combo_anio_grafico.currentData()
        zona_id = self.combo_zona_grafico.currentData()
        top_level = [m for m in maquinas.listar_maquinas() if m["padre_id"] is None]
        if zona_id is not None:
            top_level = [m for m in top_level if m["zona_id"] == zona_id]

        def total_trabajos(id_maquina):
            ids = maquinas.descendientes_ids(id_maquina)
            if anio is None:
                return sum(maquinas.contar_trabajos(i) for i in ids)
            return sum(maquinas.contar_trabajos_anio(i, anio) for i in ids)

        datos_grafico = sorted(
            ((m["nombre"], total_trabajos(m["id"])) for m in top_level),
            key=lambda par: par[1], reverse=True,
        )
        self.grafico_trabajos_maquina.establecer_datos(datos_grafico)

    def _formatear_fecha_corta(self, fecha_iso):
        return idiomas.formato_fecha_localizada(fecha_iso)

    def _maquinas_expandir_todo(self):
        """Expande todas las máquinas, años y trabajos, cargando bajo demanda
        (vía _maquina_item_expandido) los niveles que aún no se hayan abierto."""
        def expandir_recursivo(item):
            self.arbol_maquinas.expandItem(item)
            for i in range(item.childCount()):
                expandir_recursivo(item.child(i))
        for i in range(self.arbol_maquinas.topLevelItemCount()):
            expandir_recursivo(self.arbol_maquinas.topLevelItem(i))

    def _maquina_item_doble_click(self, item, columna):
        datos = item.data(0, Qt.ItemDataRole.UserRole)
        if datos and datos.get("tipo") == "trabajo":
            self.proc_edit(datos["id"])
        elif datos and datos.get("tipo") == "maquina":
            self._maquina_editar()

    def _guardar_foto_maquina(self, ruta_origen):
        if not ruta_origen: return None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nuevo = f"maquina_{ts}{os.path.splitext(ruta_origen)[1]}"
        destino = os.path.join(self.carpeta_fotos, nuevo)
        try:
            shutil.copy2(ruta_origen, destino)
            return nuevo
        except Exception:
            return None

    def _resolver_foto_maquina(self, datos):
        if not datos["ruta_foto_seleccionada"]:
            return None
        if os.path.dirname(os.path.abspath(datos["ruta_foto_seleccionada"])) == os.path.abspath(self.carpeta_fotos):
            return os.path.basename(datos["ruta_foto_seleccionada"])
        return self._guardar_foto_maquina(datos["ruta_foto_seleccionada"])

    def _maquina_nueva(self):
        dlg = DialogoEditarMaquina(self)
        if dlg.exec():
            datos = dlg.get_data()
            foto = self._resolver_foto_maquina(datos)
            maquinas.agregar_maquina(datos["nombre"], datos["padre_id"], datos["notas"], foto, datos["zona_id"])
            self.refrescar_arbol_maquinas()

    def _maquina_nueva_sub(self):
        item = self.arbol_maquinas.currentItem()
        datos_item = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not datos_item or datos_item.get("tipo") != "maquina":
            QMessageBox.information(self, t("aviso"), tt("msg_selecciona_maquina_padre", "Selecciona primero la máquina superior."))
            return
        dlg = DialogoEditarMaquina(self, padre_sugerido=datos_item["id"])
        if dlg.exec():
            datos = dlg.get_data()
            foto = self._resolver_foto_maquina(datos)
            maquinas.agregar_maquina(datos["nombre"], datos["padre_id"], datos["notas"], foto, datos["zona_id"])
            self.refrescar_arbol_maquinas()

    def _maquina_editar(self):
        item = self.arbol_maquinas.currentItem()
        datos_item = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not datos_item or datos_item.get("tipo") != "maquina":
            QMessageBox.information(self, t("aviso"), tt("msg_selecciona_maquina", "Selecciona primero una máquina."))
            return
        maquina = maquinas.obtener_maquina(datos_item["id"])
        excluir = set(maquinas.descendientes_ids(datos_item["id"]))
        dlg = DialogoEditarMaquina(self, maquina=maquina, excluir_ids=excluir)
        if dlg.exec():
            datos = dlg.get_data()
            foto = self._resolver_foto_maquina(datos)
            maquinas.actualizar_maquina(datos_item["id"], datos["nombre"], datos["padre_id"], datos["notas"], foto, datos["zona_id"])
            self.refrescar_arbol_maquinas()
            self._maquina_mostrar_foto_seleccionada()

    def _maquina_eliminar(self):
        item = self.arbol_maquinas.currentItem()
        datos_item = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not datos_item or datos_item.get("tipo") != "maquina":
            QMessageBox.information(self, t("aviso"), tt("msg_selecciona_maquina", "Selecciona primero una máquina."))
            return
        if QMessageBox.question(self, t("aviso"),
                tt("msg_confirmar_eliminar_maquina", "¿Eliminar esta máquina y sus submáquinas?\nLos trabajos ya registrados no se borrarán, quedarán sin máquina asignada.")
                ) == QMessageBox.StandardButton.Yes:
            maquinas.borrar_maquina(datos_item["id"])
            self.refrescar_arbol_maquinas()

    # ==========================================
    # STOCK DE ALMACÉN
    # ==========================================
    def init_stock_tab(self):
        l = QVBoxLayout()

        barra = QHBoxLayout()
        self.stock_buscar = QLineEdit(); self.stock_buscar.setPlaceholderText(tt("ph_buscar_material", "Buscar material..."))
        self.stock_buscar.textChanged.connect(self.refresh_stock)
        barra.addWidget(self.stock_buscar, 1)
        barra.addWidget(QLabel(tt("lbl_zona", "Zona")))
        self.combo_zona_stock = QComboBox()
        self.combo_zona_stock.currentIndexChanged.connect(self.refresh_stock)
        barra.addWidget(self.combo_zona_stock)
        btn_add = QPushButton(tt("btn_add_material", "➕ Añadir material")); btn_add.clicked.connect(self.stock_anadir_material)
        btn_edit = QPushButton(tt("btn_editar_material", "✏️ Editar")); btn_edit.clicked.connect(self.stock_editar_material)
        btn_del = QPushButton(tt("btn_borrar_material", "🗑️ Eliminar")); btn_del.setStyleSheet("background-color:#c0392b; color:white;"); btn_del.clicked.connect(lambda: self.stock_borrar_material())
        btn_entrada = QPushButton(tt("btn_entrada_stock", "📥 Entrada")); btn_entrada.setStyleSheet("background-color:#27ae60; color:white;"); btn_entrada.clicked.connect(lambda: self.stock_registrar_movimiento("entrada"))
        btn_salida = QPushButton(tt("btn_salida_stock", "📤 Salida")); btn_salida.setStyleSheet("background-color:#d35400; color:white;"); btn_salida.clicked.connect(lambda: self.stock_registrar_movimiento("salida"))
        for b in (btn_add, btn_edit, btn_del, btn_entrada, btn_salida): barra.addWidget(b)
        self.btn_configurar_almacen = QPushButton(tt("btn_configurar_almacen", "⚙️ Configurar almacén"))
        self.btn_configurar_almacen.clicked.connect(self.stock_configurar_almacen)
        barra.addWidget(self.btn_configurar_almacen)
        l.addLayout(barra)

        split = QSplitter(Qt.Orientation.Vertical)
        self.tabla_stock = QTableWidget(0, 6)
        self.tabla_stock.setHorizontalHeaderLabels([
            tt("hdr_codigo", "CÓDIGO"), tt("hdr_material", "MATERIAL"), tt("hdr_ubicacion", "UBICACIÓN"),
            tt("hdr_stock", "STOCK"), tt("hdr_minimo", "MÍNIMO"), tt("hdr_unidad", "UNIDAD")])
        self.tabla_stock.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_stock.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_stock.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_stock.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tabla_stock.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_stock.setAlternatingRowColors(True)
        self.tabla_stock.itemSelectionChanged.connect(self.refresh_historial_stock)
        self.tabla_stock.itemDoubleClicked.connect(lambda _: self.stock_editar_material())
        self.tabla_stock.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_stock.customContextMenuRequested.connect(self._menu_contextual_stock)
        split.addWidget(self.tabla_stock)

        panel_hist = QWidget(); vh = QVBoxLayout(panel_hist)
        vh.addWidget(QLabel(tt("lbl_historial_movimientos", "Historial de movimientos")))
        self.lista_historial_stock = QListWidget()
        vh.addWidget(self.lista_historial_stock)
        split.addWidget(panel_hist)
        split.setStretchFactor(0, 3); split.setStretchFactor(1, 1)
        l.addWidget(split)

        self.tab_stock.setLayout(l)
        self._cargar_zonas_stock()

    def _cargar_zonas_stock(self):
        """Rellena el desplegable de zonas de la pestaña de stock, conservando
        la zona seleccionada si sigue existiendo (o "Todas las zonas" si no)."""
        if not hasattr(self, "combo_zona_stock"): return
        zona_previa = self.combo_zona_stock.currentData()
        self.combo_zona_stock.blockSignals(True)
        self.combo_zona_stock.clear()
        self.combo_zona_stock.addItem(tt("txt_todas_zonas", "Todas las zonas"), None)
        for zona in almacen.listar_zonas():
            self.combo_zona_stock.addItem(zona["nombre"], zona["id"])
        idx = self.combo_zona_stock.findData(zona_previa)
        self.combo_zona_stock.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_zona_stock.blockSignals(False)

    def init_stock_alertas_tab(self):
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_stock_bajo_minimo", "Materiales sin stock o por debajo del mínimo establecido")))
        self.tabla_stock_alertas = QTableWidget(0, 6)
        self.tabla_stock_alertas.setHorizontalHeaderLabels([
            tt("hdr_codigo", "CÓDIGO"), tt("hdr_material", "MATERIAL"), tt("hdr_ubicacion", "UBICACIÓN"),
            tt("hdr_stock", "STOCK"), tt("hdr_minimo", "MÍNIMO"), tt("hdr_unidad", "UNIDAD")])
        self.tabla_stock_alertas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_stock_alertas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_stock_alertas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_stock_alertas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_stock_alertas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_stock_alertas.setAlternatingRowColors(True)
        self.tabla_stock_alertas.itemDoubleClicked.connect(lambda _: self.stock_alerta_ir_a_material())
        l.addWidget(self.tabla_stock_alertas)

        barra = QHBoxLayout()
        btn_ir = QPushButton(tt("btn_ir_a_material", "🔎 Ver en Stock de almacén")); btn_ir.clicked.connect(self.stock_alerta_ir_a_material)
        btn_entrada = QPushButton(tt("btn_entrada_stock", "📥 Entrada")); btn_entrada.setStyleSheet("background-color:#27ae60; color:white;")
        btn_entrada.clicked.connect(self.stock_alerta_entrada)
        barra.addWidget(btn_ir); barra.addWidget(btn_entrada)
        l.addLayout(barra)

        self.tab_stock_alertas.setLayout(l)

    @staticmethod
    def _color_stock(actual, minimo):
        """Rojo por debajo del mínimo, verde por encima, color por defecto si coincide."""
        if actual < minimo:
            return QColor("#e74c3c")
        if actual > minimo:
            return QColor("#27ae60")
        return None

    def _material_seleccionado_alerta(self):
        fila = self.tabla_stock_alertas.currentRow()
        if fila < 0: return None
        return self.tabla_stock_alertas.item(fila, 0).data(Qt.ItemDataRole.UserRole)

    def refresh_stock_alertas(self):
        if not hasattr(self, "tabla_stock_alertas"): return
        materiales = almacen.materiales_bajo_minimo()
        self.tabla_stock_alertas.setRowCount(len(materiales))
        for fila, m in enumerate(materiales):
            ubicacion = almacen.obtener_ubicacion_texto(m.get("seccion_id"))
            valores = [m.get("codigo") or "", m["nombre"], ubicacion,
                       f"{m['stock_actual']:g}", f"{m['stock_minimo']:g}", m.get("unidad") or ""]
            color = self._color_stock(m["stock_actual"], m["stock_minimo"])
            for col, val in enumerate(valores):
                item = QTableWidgetItem(val)
                if col == 0: item.setData(Qt.ItemDataRole.UserRole, m["id"])
                if col == 3 and color is not None: item.setForeground(QBrush(color))
                self.tabla_stock_alertas.setItem(fila, col, item)
        if hasattr(self, "tabs") and hasattr(self, "tab_stock_alertas"):
            idx = self.tabs.indexOf(self.tab_stock_alertas)
            if idx >= 0:
                sufijo = f" ({len(materiales)})" if materiales else ""
                self.tabs.setTabText(idx, tt("tab_stock_alertas", "⚠️ Stock bajo mínimo") + sufijo)

    def stock_alerta_ir_a_material(self):
        material_id = self._material_seleccionado_alerta()
        if not material_id: return
        m = almacen.obtener_material(material_id)
        if not m: return
        self.tabs.setCurrentWidget(self.tab_stock)
        self.stock_buscar.setText(m.get("codigo") or m["nombre"])
        self.refresh_stock()
        for fila in range(self.tabla_stock.rowCount()):
            if self.tabla_stock.item(fila, 0).data(Qt.ItemDataRole.UserRole) == material_id:
                self.tabla_stock.selectRow(fila); break

    def stock_alerta_entrada(self):
        material_id = self._material_seleccionado_alerta()
        if not material_id: return
        m = almacen.obtener_material(material_id)
        if not m: return
        dlg = DialogoMovimientoStock(self, m, "entrada")
        if dlg.exec():
            cantidad, motivo = dlg.get_data()
            almacen.registrar_movimiento(material_id, "entrada", cantidad,
                                          usuarios.id_actual(), usuarios.nombre_actual(), motivo)
            self.refresh_stock(); self.refresh_stock_alertas()

    def _material_seleccionado(self):
        fila = self.tabla_stock.currentRow()
        if fila < 0: return None
        return self.tabla_stock.item(fila, 0).data(Qt.ItemDataRole.UserRole)

    def _materiales_seleccionados(self):
        filas = {i.row() for i in self.tabla_stock.selectedIndexes()}
        return [self.tabla_stock.item(f, 0).data(Qt.ItemDataRole.UserRole) for f in sorted(filas)]

    def _menu_contextual_stock(self, pos):
        ids = self._materiales_seleccionados()
        if not ids: return
        menu = QMenu(self)
        if len(ids) == 1:
            accion_editar = menu.addAction(tt("btn_editar_material", "✏️ Editar"))
            accion_entrada = menu.addAction(tt("btn_entrada_stock", "📥 Entrada"))
            accion_salida = menu.addAction(tt("btn_salida_stock", "📤 Salida"))
            menu.addSeparator()
        accion_mover = menu.addAction(tt("btn_mover_material", "📦 Mover a..."))
        accion_borrar = menu.addAction(tt("btn_borrar_material", "🗑️ Eliminar"))
        elegida = menu.exec(self.tabla_stock.viewport().mapToGlobal(pos))
        if elegida is None: return
        if len(ids) == 1:
            if elegida == accion_editar: self.stock_editar_material()
            elif elegida == accion_entrada: self.stock_registrar_movimiento("entrada")
            elif elegida == accion_salida: self.stock_registrar_movimiento("salida")
        if elegida == accion_mover: self.stock_mover_materiales(ids)
        elif elegida == accion_borrar: self.stock_borrar_material(ids)

    def refresh_stock(self):
        if not hasattr(self, "tabla_stock"): return
        texto = self.stock_buscar.text().strip() if hasattr(self, "stock_buscar") else ""
        zona_id = self.combo_zona_stock.currentData() if hasattr(self, "combo_zona_stock") else None
        materiales = almacen.listar_materiales(texto or None, zona_id)
        self.tabla_stock.setRowCount(len(materiales))
        for fila, m in enumerate(materiales):
            ubicacion = almacen.obtener_ubicacion_texto(m.get("seccion_id"))
            valores = [m.get("codigo") or "", m["nombre"], ubicacion,
                       f"{m['stock_actual']:g}", f"{m['stock_minimo']:g}", m.get("unidad") or ""]
            color = self._color_stock(m["stock_actual"], m["stock_minimo"])
            for col, val in enumerate(valores):
                item = QTableWidgetItem(val)
                if col == 0: item.setData(Qt.ItemDataRole.UserRole, m["id"])
                if col == 3 and color is not None: item.setForeground(QBrush(color))
                self.tabla_stock.setItem(fila, col, item)
        if hasattr(self, "btn_configurar_almacen"):
            self.btn_configurar_almacen.setVisible(usuarios.es_admin())
        self.refresh_historial_stock()
        self.refresh_stock_alertas()

    def refresh_historial_stock(self):
        if not hasattr(self, "lista_historial_stock"): return
        self.lista_historial_stock.clear()
        material_id = self._material_seleccionado()
        if not material_id: return
        for mov in almacen.obtener_movimientos(material_id, limite=20):
            if mov["tipo"] == "traslado":
                texto = f"🔀 {mov['fecha']}   {mov.get('motivo') or ''}   —   {mov.get('usuario_nombre') or ''}"
            else:
                icono = "📥" if mov["tipo"] == "entrada" else "📤"
                texto = f"{icono} {mov['fecha']}   {mov['cantidad']:g}   —   {mov.get('usuario_nombre') or ''}"
                if mov.get("motivo"): texto += f"   ({mov['motivo']})"
            self.lista_historial_stock.addItem(texto)

    def _guardar_foto_material(self, ruta_origen):
        if not ruta_origen: return None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nuevo = f"almacen_{ts}{os.path.splitext(ruta_origen)[1]}"
        destino = os.path.join(self.carpeta_fotos, nuevo)
        try:
            shutil.copy2(ruta_origen, destino)
            return nuevo
        except Exception:
            return None

    def stock_anadir_material(self):
        dlg = DialogoEditarMaterial(self)
        if dlg.exec():
            d = dlg.get_data()
            if not d["nombre"]: return
            foto_guardada = self._guardar_foto_material(d["ruta_foto_seleccionada"])
            almacen.crear_material(d["codigo"], d["nombre"], d["descripcion"], d["unidad"], d["stock_minimo"],
                                    d["seccion_id"], foto_guardada, d["stock_inicial"],
                                    usuarios.id_actual(), usuarios.nombre_actual())
            self.refresh_stock()

    def stock_editar_material(self):
        material_id = self._material_seleccionado()
        if not material_id:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_material_seleccionado", "Selecciona un material de la lista.")); return
        material = almacen.obtener_material(material_id)
        dlg = DialogoEditarMaterial(self, material)
        if dlg.exec():
            d = dlg.get_data()
            if not d["nombre"]: return
            if not d["ruta_foto_seleccionada"]:
                foto_final = None
            elif os.path.dirname(os.path.abspath(d["ruta_foto_seleccionada"])) == os.path.abspath(self.carpeta_fotos):
                foto_final = os.path.basename(d["ruta_foto_seleccionada"])
            else:
                foto_final = self._guardar_foto_material(d["ruta_foto_seleccionada"])
            almacen.actualizar_material(material_id, d["codigo"], d["nombre"], d["descripcion"], d["unidad"],
                                         d["stock_minimo"], d["seccion_id"], foto_final,
                                         usuarios.id_actual(), usuarios.nombre_actual())
            self.refresh_stock()

    def stock_borrar_material(self, ids=None):
        ids = ids if ids is not None else self._materiales_seleccionados()
        if not ids:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_material_seleccionado", "Selecciona un material de la lista.")); return
        mensaje = (tt("msg_confirmar_borrar_material", "¿Eliminar este material del almacén? Se perderá su historial de movimientos.")
                   if len(ids) == 1 else
                   tt("msg_confirmar_borrar_materiales", "¿Eliminar estos {n} materiales del almacén? Se perderá su historial de movimientos.").format(n=len(ids)))
        if QMessageBox.question(self, tt("aviso", "Aviso"), mensaje) != QMessageBox.StandardButton.Yes:
            return
        for material_id in ids:
            almacen.borrar_material(material_id)
        self.refresh_stock()

    def stock_mover_materiales(self, ids=None):
        ids = ids if ids is not None else self._materiales_seleccionados()
        if not ids:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_material_seleccionado", "Selecciona un material de la lista.")); return
        dlg = DialogoSeleccionarUbicacion(self)
        if not dlg.exec(): return
        seccion_id = dlg.get_seccion_id()
        for material_id in ids:
            m = almacen.obtener_material(material_id)
            if not m: continue
            almacen.actualizar_material(material_id, m.get("codigo") or "", m["nombre"], m.get("descripcion") or "",
                                         m.get("unidad") or "", m.get("stock_minimo") or 0, seccion_id, m.get("foto"),
                                         usuarios.id_actual(), usuarios.nombre_actual())
        self.refresh_stock()

    def stock_registrar_movimiento(self, tipo):
        material_id = self._material_seleccionado()
        if not material_id:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_material_seleccionado", "Selecciona un material de la lista.")); return
        material = almacen.obtener_material(material_id)
        dlg = DialogoMovimientoStock(self, material, tipo)
        if dlg.exec():
            cantidad, motivo = dlg.get_data()
            ok, error = almacen.registrar_movimiento(material_id, tipo, cantidad, usuarios.id_actual(), usuarios.nombre_actual(), motivo)
            if not ok:
                QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_stock_insuficiente", "No hay stock suficiente para esta salida."))
            self.refresh_stock()

    def stock_configurar_almacen(self):
        if not usuarios.es_admin(): return
        DialogoConfigurarAlmacen(self).exec()
        self._cargar_zonas_stock()
        self.refresh_stock()

    # --- LÓGICA GENERAL ---
    def go_today(self): self.calendar.setSelectedDate(QDate.currentDate()); self.update_calendar_list()
    def gest_dias(self, c=False): DialogoDiasEspeciales(self.db, self.gestor_festivos, self).exec(); self.pintar_calendario()
    def pintar_calendario(self):
        self.calendar.setUpdatesEnabled(False); ac = QDate.currentDate().year(); fc = QDate(ac - 1, 1, 1); ff = QDate(ac + 1, 12, 31); fl = QTextCharFormat()
        while fc <= ff: self.calendar.setDateTextFormat(fc, fl); fc = fc.addDays(1)
        ffst = QTextCharFormat(); ffst.setBackground(QBrush(QColor("#502828"))); ffst.setForeground(QBrush(QColor("#ddd")))
        for f in self.gestor_festivos.obtener_festivos(): self.calendar.setDateTextFormat(f, ffst)
        cols = {"Vacaciones": "#FFF59D", "Puente": "#1565C0", "Día Libre": "#F48FB1", "Festivo (Manual)": "#502828"}
        tcols = {"Vacaciones": "black", "Puente": "white", "Día Libre": "black", "Festivo (Manual)": "ddd"}
        for s, tipo_dia in self.db.obtener_dias_especiales().items(): fm = QTextCharFormat(); fm.setBackground(QBrush(QColor(cols.get(tipo_dia, "#555")))); fm.setForeground(QBrush(QColor(tcols.get(tipo_dia, "black")))); self.calendar.setDateTextFormat(QDate.fromString(s, "yyyy-MM-dd"), fm)
        ft = QTextCharFormat(); ft.setBackground(QBrush(QColor("#A5D6A7"))); ft.setForeground(QBrush(Qt.GlobalColor.black)); ft.setFontWeight(750)
        for f in self.db.obtener_fechas_con_tareas(): self.calendar.setDateTextFormat(QDate.fromString(f, "yyyy-MM-dd"), ft)
        self.calendar.setUpdatesEnabled(True)

    def on_tab_changed(self, i):
        if i == 0: self.refresh_dashboard()
        elif i == 1: self.pintar_calendario(); self.update_calendar_list()
        elif i == 2: self.refresh_avisos()
        elif i == 4: self.refresh_history()
        self.refresh_todos()

    def refresh_all(self):
        self.refresh_dashboard(); self.pintar_calendario(); self.update_calendar_list()
        self.refresh_history(); self.search(); self.refresh_todos(); self.refresh_avisos(); self.refresh_stock()
        if hasattr(self, 'arbol_maquinas'):
            self.refrescar_arbol_maquinas()
    def setup_table(self, tabla_widget):
        tabla_widget.setColumnCount(5); tabla_widget.setHorizontalHeaderLabels([t("hdr_fecha"), t("hdr_descripcion"), t("hdr_tags"), tt("hdr_realizado_por", "Realizado por"), tt("hdr_prioridad", "PRIORIDAD")]); tabla_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch); # La columna del técnico se ajusta al contenido (cabecera o nombre, lo que sea más ancho)
        tabla_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents); tabla_widget.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents); tabla_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); tabla_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); tabla_widget.setAlternatingRowColors(True); tabla_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    def configurar_deseleccion(self, widget):
        clase_base = type(widget)
        def click_inteligente(event):
            clase_base.mousePressEvent(widget, event)
            if not widget.indexAt(event.pos()).isValid(): widget.clearSelection(); widget.setCurrentItem(None)
        widget.mousePressEvent = click_inteligente

    def edit_cal(self, i): self.proc_edit(i.data(Qt.ItemDataRole.UserRole))
    def _es_mi_registro(self, tarea_id):
        """Comprueba si el registro pertenece al usuario actual."""
        d = self.db.obtener_tarea_por_id(tarea_id)
        if not d:
            return False
        uid_registro = d[4] if len(d) > 4 else None
        return uid_registro == usuarios.id_actual()

    def _puede_modificar(self, tarea_id):
        """Admin puede todo; técnico solo sus registros."""
        if usuarios.es_admin():
            return True
        return self._es_mi_registro(tarea_id)

    def edit_rec(self, tabla_widget):
        r = tabla_widget.currentRow()
        if r >= 0: self.proc_edit(tabla_widget.item(r, 0).data(Qt.ItemDataRole.UserRole))
    def proc_edit(self, i):
        d = self.db.obtener_tarea_por_id(i)
        if d:
            if not self._puede_modificar(i):
                QMessageBox.information(self, t("aviso"),
                    tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))
                return
            uid = d[4] if len(d) > 4 else None
            unombre = d[5] if len(d) > 5 else ""
            maquina_id = d[6] if len(d) > 6 else None
            prioridad = d[7] if len(d) > 7 else "Media"
            horas_paro = d[8] if len(d) > 8 else None
            dlg = EditDialog(self, d[1], d[2], d[3], usuario_id=uid, usuario_nombre=unombre, maquina_id=maquina_id, prioridad=prioridad, horas_paro=horas_paro)
            if dlg.exec():
                fecha, desc, tags, nuevo_uid, nuevo_nombre, nueva_maquina_id, nueva_prioridad, nuevas_horas_paro = dlg.get_data()
                self.db.actualizar_tarea(i, fecha, desc, tags, nuevo_uid, nuevo_nombre, nueva_maquina_id, nueva_prioridad, nuevas_horas_paro)
                self.refresh_all()
                if hasattr(self, 'arbol_maquinas'):
                    self.refrescar_arbol_maquinas()

    def del_rec(self, tabla_widget):
        r = tabla_widget.currentRow()
        if r >= 0:
            i = tabla_widget.item(r, 0).data(Qt.ItemDataRole.UserRole)
            if not self._puede_modificar(i):
                QMessageBox.information(self, t("aviso"),
                    tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))
                return
            d = self.db.obtener_tarea_por_id(i)
            if d:
                # --- DIÁLOGO ESPAÑOL ---
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle(t("title_confirmar_eliminacion"))
                msg.setText(t("msg_confirmar_eliminacion_registro"))

                # Botones manuales
                btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
                btn_no = msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)

                msg.exec()

                if msg.clickedButton() == btn_si:
                    # -------------------------------------------------------
                    # 1. LÓGICA DE RESTAURACIÓN DE AVISO (NUEVO)
                    # -------------------------------------------------------
                    try:
                        desc_tarea = d[2]  # Descripción
                        fecha_tarea = d[1] # Fecha (YYYY-MM-DD)

                        prefijo = "Mantenimiento Preventivo: "
                        if desc_tarea.startswith(prefijo):
                            titulo_aviso = desc_tarea.replace(prefijo, "").strip()

                            # Abrimos conexión manual segura usando el método de tu clase DB
                            conn = self.db.conectar()
                            c = conn.cursor()

                            # Buscamos si hay un aviso con ese título Y esa fecha de 'ultima_completada'
                            c.execute("SELECT id FROM avisos_recurrentes WHERE titulo=? AND ultima_completada=?", (titulo_aviso, fecha_tarea))
                            aviso = c.fetchone()

                            if aviso:
                                # Lo "descompletamos" poniendo NULL
                                c.execute("UPDATE avisos_recurrentes SET ultima_completada=NULL WHERE id=?", (aviso[0],))
                                conn.commit()
                                print(f"Aviso '{titulo_aviso}' restaurado a pendiente.")

                            conn.close()
                    except Exception as e:
                        print(f"Error intentando restaurar aviso: {e}")

                    # -------------------------------------------------------
                    # 2. BORRADO DE FOTO (Lógica original que ya tenías)
                    # -------------------------------------------------------
                    m = re.search(r"\[FOTO:\s*(.*?)\]", d[2])
                    if m:
                        nombre = m.group(1).split("]")[0].strip()
                        ruta = os.path.join(self.carpeta_fotos, nombre)
                        if os.path.exists(ruta):
                            try: os.remove(ruta)
                            except: pass

                    # -------------------------------------------------------
                    # 3. BORRADO DE BASE DE DATOS
                    # -------------------------------------------------------
                    self.db.borrar_tarea(i)
                    self.refresh_all()

                    # Avisar al móvil (Servidor) si está activo
                    if hasattr(self, 'servidor') and self.servidor:
                        self.servidor.pendiente_actualizado.emit()

    def revertir_a_pendiente(self, tabla_widget):
        """Deshace la finalización de un trabajo: lo saca del historial y lo
        vuelve a poner en Pendientes, por si se completó por error."""
        r = tabla_widget.currentRow()
        if r < 0: return
        i = tabla_widget.item(r, 0).data(Qt.ItemDataRole.UserRole)
        if not self._puede_modificar(i):
            QMessageBox.information(self, t("aviso"),
                tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))
            return

        d = self.db.obtener_tarea_por_id(i)
        if not d: return
        fecha_tarea, desc_tarea, tags_tarea = d[1], d[2], d[3]
        uid_original = d[4] if len(d) > 4 else None
        unombre_original = d[5] if len(d) > 5 else ""
        maquina_id = d[6] if len(d) > 6 else None
        prioridad_original = d[7] if len(d) > 7 else "Media"

        texto_aviso = tt("msg_confirmar_revertir_pendiente",
            "El trabajo volverá a la pestaña Pendientes y desaparecerá del historial. ¿Continuar?")
        if maquina_id:
            texto_aviso += "\n\n" + tt("msg_revertir_pierde_maquina",
                "Las tareas pendientes no admiten máquina vinculada, así que se perderá ese dato.")

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tt("title_revertir_pendiente", "Revertir a pendiente"))
        msg.setText(texto_aviso)
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() != btn_si: return

        # Si el trabajo venía de un aviso recurrente, lo "descompletamos" igual
        # que ya se hace al borrar un registro del historial.
        prefijo = "Mantenimiento Preventivo: "
        if desc_tarea.startswith(prefijo):
            titulo_aviso = desc_tarea.replace(prefijo, "").strip()
            try:
                conn = self.db.conectar(); c = conn.cursor()
                c.execute("SELECT id FROM avisos_recurrentes WHERE titulo=? AND ultima_completada=?", (titulo_aviso, fecha_tarea))
                aviso = c.fetchone()
                if aviso:
                    c.execute("UPDATE avisos_recurrentes SET ultima_completada=NULL WHERE id=?", (aviso[0],))
                    conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error intentando restaurar aviso: {e}")

        lineas = desc_tarea.split("\n")
        titulo = lineas[0].strip()
        detalles = "\n".join(lineas[1:]).strip()

        if not self.db.agregar_pendiente(titulo, detalles, uid_original, unombre_original or None, prioridad_original):
            QMessageBox.critical(self, t("aviso"), tt("msg_error_revertir", "No se ha podido revertir el trabajo a pendiente."))
            return

        detalle_auditoria = f"Registro del {fecha_tarea}: {titulo[:80]} (autor original: {unombre_original or usuarios.ETIQUETA_HISTORICO})"
        try:
            conn = self.db.conectar(); c = conn.cursor()
            c.execute("DELETE FROM tareas WHERE id=?", (i,))
            conn.commit(); conn.close()
        except Exception as e:
            print(f"Error eliminando tarea al revertir: {e}")
        usuarios.registrar_auditoria(usuarios.id_actual(), i, "revertir", detalle_auditoria)
        self.refresh_todos()
        self.refresh_all()
        if hasattr(self, 'servidor') and self.servidor:
            self.servidor.pendiente_actualizado.emit()
        self.statusBar().showMessage(tt("msg_revertido_pendiente", "Trabajo movido de nuevo a Pendientes."), 4000)

    def add_todo(self):
        tit, d = self.in_todo_t.text().strip(), self.in_todo_d.toPlainText().strip()
        uid = self.combo_asignar.currentData()
        nombre = self.combo_asignar.currentText() if uid is not None else None
        prioridad = self.combo_prioridad_todo.currentData()
        especialidad_id = self.combo_especialidad_todo.currentData()
        if tit and self.db.agregar_pendiente(tit, d, uid, nombre, prioridad, especialidad_id):
            self.in_todo_t.clear(); self.in_todo_d.clear(); self.combo_prioridad_todo.setCurrentIndex(1); self.refresh_todos()
            if hasattr(self, 'servidor') and self.servidor:
                self.servidor.pendiente_actualizado.emit()

    def reasignar_todo(self):
        """Cambia el técnico asignado y/o la especialidad del pendiente seleccionado.
        Solo un admin puede modificar la asignación/especialidad de un trabajo ya
        existente; un técnico solo puede fijarlas al crear el trabajo."""
        if not usuarios.es_admin():
            return
        row = self.todo_list.currentRow()
        if row < 0: return
        item = self.todo_list.item(row)
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid is None: return

        dlg = QDialog(self)
        dlg.setWindowTitle(tt("btn_reasignar", "Reasignar"))
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(tt("lbl_asignar_a", "Asignar a") + ":"))
        combo = QComboBox()
        self._llenar_combo_usuarios(combo, incluir_sin_asignar=True)
        idx = combo.findData(item.data(Qt.ItemDataRole.UserRole + 3))
        if idx >= 0: combo.setCurrentIndex(idx)
        lay.addWidget(combo)
        lay.addWidget(QLabel(tt("usuarios_col_especialidad", "Especialidad") + ":"))
        combo_esp = QComboBox()
        self._llenar_combo_especialidades(combo_esp)
        idx_esp = combo_esp.findData(item.data(Qt.ItemDataRole.UserRole + 5))
        if idx_esp >= 0: combo_esp.setCurrentIndex(idx_esp)
        lay.addWidget(combo_esp)
        caja = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.accepted.connect(dlg.accept); caja.rejected.connect(dlg.reject)
        lay.addWidget(caja)
        if dlg.exec() != QDialog.DialogCode.Accepted: return

        uid = combo.currentData()
        nombre = combo.currentText() if uid is not None else None
        especialidad_id = combo_esp.currentData()
        ok = self.db.asignar_pendiente(pid, uid, nombre)
        ok = self.db.asignar_especialidad_pendiente(pid, especialidad_id) and ok
        if ok:
            self.refresh_todos()
            if hasattr(self, 'servidor') and self.servidor:
                self.servidor.pendiente_actualizado.emit()

    def _menu_contextual_todos(self, pos):
        """Menú con clic derecho sobre la lista de trabajos: eliminar o asignar
        técnico/especialidad a varios trabajos a la vez."""
        if not self.todo_list.selectedItems():
            item = self.todo_list.itemAt(pos)
            if item is not None:
                item.setSelected(True)
        seleccion = [it for it in self.todo_list.selectedItems() if it.data(Qt.ItemDataRole.UserRole) is not None]
        if not seleccion:
            return
        ids = [it.data(Qt.ItemDataRole.UserRole) for it in seleccion]
        n = len(ids)

        menu = QMenu(self)
        if usuarios.es_admin():
            texto_asignar = tt("ctx_asignar_avisos", "👤 Asignar a...") if n == 1 else \
                             tt("ctx_asignar_trabajos_n", "👤 Asignar a... ({n} trabajos)").format(n=n)
            menu.addAction(texto_asignar, lambda: self._asignar_todos_masivo(ids))
            menu.addSeparator()

        texto_borrar = tt("ctx_eliminar_trabajos", "🗑️ Eliminar") if n == 1 else \
                        tt("ctx_eliminar_trabajos_n", "🗑️ Eliminar ({n} trabajos)").format(n=n)
        menu.addAction(texto_borrar, lambda: self._borrar_todos_masivo(ids))

        menu.exec(self.todo_list.viewport().mapToGlobal(pos))

    def _borrar_todos_masivo(self, ids):
        """Borra uno o varios trabajos pendientes, previa confirmación."""
        if not ids:
            return
        n = len(ids)
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(t("title_confirmar_borrado"))
        msg.setText(t("msg_confirmar_borrar_pendiente") if n == 1 else
                    tt("msg_confirmar_borrar_pendientes_n", "¿Estás seguro de borrar estos {n} trabajos pendientes definitivamente?").format(n=n))

        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)

        msg.exec()

        if msg.clickedButton() == btn_si:
            for id_p in ids:
                self.db.borrar_pendiente(id_p)
            self.refresh_todos()
            if hasattr(self, 'servidor') and self.servidor:
                self.servidor.pendiente_actualizado.emit()

    def _asignar_todos_masivo(self, ids):
        """Asigna uno o varios trabajos pendientes a un técnico y/o a una
        especialidad (o los deja sin asignar), de forma independiente: si solo
        se marca la especialidad, el técnico ya asignado no se toca, y viceversa.
        Solo un admin puede modificar la asignación/especialidad de trabajos ya
        existentes; un técnico solo puede fijarlas al crear el trabajo."""
        if not usuarios.es_admin():
            return
        if not ids:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tt("lbl_asignar_a", "Asignar a"))
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(
            tt("lbl_asignar_trabajos_a", "Asignar {n} trabajo(s) a:").format(n=len(ids))))

        chk_tecnico = QCheckBox(tt("chk_cambiar_tecnico", "Cambiar técnico asignado"))
        lay.addWidget(chk_tecnico)
        combo = QComboBox()
        self._llenar_combo_usuarios(combo, incluir_sin_asignar=True)
        combo.setEnabled(False)
        chk_tecnico.toggled.connect(combo.setEnabled)
        lay.addWidget(combo)

        chk_especialidad = QCheckBox(tt("chk_cambiar_especialidad", "Cambiar especialidad"))
        lay.addWidget(chk_especialidad)
        combo_esp = QComboBox()
        self._llenar_combo_especialidades(combo_esp)
        combo_esp.setEnabled(False)
        chk_especialidad.toggled.connect(combo_esp.setEnabled)
        lay.addWidget(combo_esp)

        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        caja.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        caja.accepted.connect(dlg.accept)
        caja.rejected.connect(dlg.reject)
        lay.addWidget(caja)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        if not chk_tecnico.isChecked() and not chk_especialidad.isChecked():
            return

        uid = combo.currentData()
        nombre = combo.currentText() if uid is not None else None
        especialidad_id = combo_esp.currentData()
        for id_p in ids:
            if chk_tecnico.isChecked():
                self.db.asignar_pendiente(id_p, uid, nombre)
            if chk_especialidad.isChecked():
                self.db.asignar_especialidad_pendiente(id_p, especialidad_id)
        self.refresh_todos()
        if hasattr(self, 'servidor') and self.servidor:
            self.servidor.pendiente_actualizado.emit()

    def refresh_todos(self, *_):
        self.todo_list.clear()
        if hasattr(self, 'b_asig_todo'):
            self.b_asig_todo.setEnabled(usuarios.es_admin())
        ps = self.db.obtener_pendientes()

        # Filtro por técnico asignado
        filtro = self.combo_filtro_todos.currentData() if hasattr(self, 'combo_filtro_todos') else "TODOS"
        if filtro != "TODOS":
            ps = [p for p in ps if p[3] == filtro]

        if not ps:
            self.todo_list.addItem(t("msg_nada"))

        orden_prioridad = {"Crítica": 0, "Alta": 1, "Media": 2, "Baja": 3}
        ps = sorted(ps, key=lambda p: orden_prioridad.get(p[5], 2))

        iconos_prioridad = {"Crítica": "🔴", "Alta": "🟠", "Media": "⬜", "Baja": "🟢"}
        for i, tit, d, asig_id, asig_nombre, prioridad, especialidad_id in ps:
            # 1. LIMPIEZA TOTAL (Quitamos FOTO y REF)
            d_limpio = re.sub(r"\[FOTO.*?:.*?\]", "", d)
            d_limpio = re.sub(r"\[REF:.*?\]", "", d_limpio).strip()

            tiene_foto = self._hay_foto_disponible(d)

            # Texto visual limpio
            icono = iconos_prioridad.get(prioridad, "⬜")
            texto_visual = f"{icono} {tit}"
            if prioridad in ("Crítica", "Alta"):
                texto_visual += f"  [{traducir_prioridad(prioridad)}]"
            if d_limpio:
                texto_visual += f"\n   ↳ {d_limpio}"

            if tiene_foto:
                texto_visual += "  (📸 Foto)"

            if asig_nombre:
                texto_visual += f"\n   👤 {asig_nombre}"

            it = QListWidgetItem(texto_visual)

            # Guardamos los datos originales (sucios) por debajo para la lógica
            it.setData(Qt.ItemDataRole.UserRole, i)
            it.setData(Qt.ItemDataRole.UserRole + 1, tit)
            it.setData(Qt.ItemDataRole.UserRole + 2, d)
            it.setData(Qt.ItemDataRole.UserRole + 3, asig_id)
            it.setData(Qt.ItemDataRole.UserRole + 4, prioridad)
            it.setData(Qt.ItemDataRole.UserRole + 5, especialidad_id)

            if tiene_foto:
                it.setToolTip("📸 Tiene foto adjunta")

            self.todo_list.addItem(it)

    def del_todo(self):
        r = self.todo_list.currentRow()
        if r >= 0:
            i = self.todo_list.item(r).data(Qt.ItemDataRole.UserRole)
            if i:
                # --- DIÁLOGO PERSONALIZADO EN ESPAÑOL ---
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle(t("title_confirmar_borrado"))
                msg.setText(t("msg_confirmar_borrar_pendiente"))

                # Botones personalizados
                btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
                btn_no = msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)

                msg.exec()

                if msg.clickedButton() == btn_si:
                    self.db.borrar_pendiente(i)
                    self.refresh_todos()

    def complete_todo(self):
        row = self.todo_list.currentRow()
        if row < 0: return

        item = self.todo_list.item(row)
        id_pendiente = item.data(Qt.ItemDataRole.UserRole)
        titulo = item.data(Qt.ItemDataRole.UserRole + 1)
        detalles_originales = item.data(Qt.ItemDataRole.UserRole + 2)
        prioridad_pendiente = item.data(Qt.ItemDataRole.UserRole + 4) or "Media"

        # Usamos la nueva clase de diálogo
        dialogo = CompleteDialog(self, titulo, detalles_originales)

        if dialogo.exec():
            fecha, tags, foto_nueva = dialogo.get_data()

            # --- MEJORA: LIMPIEZA INTELIGENTE ---
            detalles_limpios = detalles_originales
            # Si el usuario ha elegido una FOTO NUEVA, borramos la etiqueta de la vieja del texto
            if foto_nueva and detalles_originales:
                 detalles_limpios = re.sub(r"\[FOTO:.*?\]", "", detalles_originales).strip()
            # ------------------------------------

            desc_final = titulo
            if detalles_limpios: desc_final += f"\n{detalles_limpios}"
            if foto_nueva: desc_final += f"\n[FOTO: {os.path.basename(foto_nueva)}]"

            # Guardar en Historial y borrar de Pendientes
            if self.db.agregar_tarea(fecha, desc_final, tags, prioridad=prioridad_pendiente):
                self.db.borrar_pendiente(id_pendiente)
                self.refresh_todos()
                self.refresh_all()
                self.statusBar().showMessage(t("msg_tarea_completada").format(titulo=titulo), 5000)

    # =========================================================================
    # FUNCIONES RESTAURADAS Y NUEVAS
    # =========================================================================

    def realizar_backup(self):
        self.limpiar_fotos_huerfanas(silencioso=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_zip = f"backup_completo_{timestamp}.zip"
        # Sugerimos la carpeta de backups habitual, pero el usuario puede elegir otra ubicación
        ruta_sugerida = os.path.join(self.carpeta_backups, nombre_zip)
        ruta_zip = self.guardar_archivo_dialogo(t("title_guardar_backup"), ruta_sugerida, "Archivos ZIP (*.zip)")
        if not ruta_zip: return

        dlg = QDialog(self)
        dlg.setWindowTitle(t("title_guardar_backup"))
        dlg.setFixedSize(420, 110)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_haciendo_backup", "Haciendo copia de seguridad...")))
        barra = QProgressBar(); barra.setRange(0, 0)
        l.addWidget(barra)
        dlg.setLayout(l)

        def _actualizar_progreso(actual, total):
            if total:
                barra.setRange(0, total)
                barra.setValue(actual)

        def _terminado(exito, mensaje, ruta):
            dlg.accept()
            if exito:
                QMessageBox.information(self, t("title_backup_completo"), t("msg_backup_guardado").format(archivo=os.path.basename(ruta)))
            else:
                QMessageBox.critical(self, t("title_error_backup"), mensaje)

        self.hilo_backup_manual = BackupManualThread(ruta_zip, self.carpeta_fotos, self.db.db_name, self.db.db_almacen_name)
        self.hilo_backup_manual.progreso.connect(_actualizar_progreso)
        self.hilo_backup_manual.resultado.connect(_terminado)
        self.hilo_backup_manual.start()

        dlg.exec()

    def _confirmar_restaurar(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(t("title_restaurar_copia"))
        msg.setText(t("msg_advertencia_restaurar"))
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        return msg.clickedButton() == btn_si

    def restaurar_backup(self):
        if not self._confirmar_restaurar(): return
        # Use a dialog instance to allow setting DontUseNativeDialog if needed, though getOpenFileName static usually works.
        # But to be safe with styles, we could instantiate QFileDialog.
        # For restore, let's keep it simple as it's a critical operation.
        archivo_zip, _ = QFileDialog.getOpenFileName(self, t("title_seleccionar_backup"), "backups", "Archivos ZIP (*.zip)", options=QFileDialog.Option.DontUseNativeDialog)
        if not archivo_zip: return
        self._ejecutar_restauracion(archivo_zip)

    def restaurar_backup_auto(self):
        if not self._confirmar_restaurar(): return
        carpeta_inicial = self.carpeta_backups_auto if os.path.isdir(self.carpeta_backups_auto) else "backups"
        archivo_zip, _ = QFileDialog.getOpenFileName(
            self, tt("title_seleccionar_backup_auto", "Seleccionar copia automática"), carpeta_inicial,
            tt("filtro_backup_auto", "Copias automáticas") + " (auto_backup_db_*.zip)",
            options=QFileDialog.Option.DontUseNativeDialog)
        if not archivo_zip: return
        self._ejecutar_restauracion(archivo_zip)

    def _ejecutar_restauracion(self, archivo_zip):
        # Restaurar en DATA_DIR o carpeta local según donde estemos
        restore_path = os.path.dirname(self.db.db_name)
        es_auto_backup = os.path.basename(archivo_zip).startswith("auto_backup_db_")

        dlg = QDialog(self)
        dlg.setWindowTitle(t("title_restaurar_copia"))
        dlg.setFixedSize(420, 110)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_restaurando_backup", "Restaurando copia de seguridad...")))
        barra = QProgressBar(); barra.setRange(0, 0)
        l.addWidget(barra)
        dlg.setLayout(l)

        def _actualizar_progreso(actual, total):
            if total:
                barra.setRange(0, total)
                barra.setValue(actual)

        def _terminado(exito, mensaje):
            dlg.accept()
            if exito:
                QMessageBox.information(self, t("title_restauracion"), t("msg_sistema_restaurado")); self.refresh_all()
            else:
                QMessageBox.critical(self, t("title_error_restauracion"), t("msg_zip_corrupto").format(error=mensaje))

        self.hilo_restore = RestoreManualThread(archivo_zip, restore_path, self.carpeta_fotos, es_auto_backup, self._fotos_en_uso)
        self.hilo_restore.progreso.connect(_actualizar_progreso)
        self.hilo_restore.resultado.connect(_terminado)
        self.hilo_restore.start()

        dlg.exec()

    def exportar_csv(self):
        dlg = DialogoFiltroTecnico(self, t("title_exportar_csv"))
        if not dlg.exec(): return
        filtro_usuario = dlg.get_filtro()
        nombre_limpio = re.sub(r'[<>:\"/\\\\|?*]', '', filtro_usuario) if filtro_usuario else ""
        sufijo = f"_{nombre_limpio}" if nombre_limpio else ""
        nombre_defecto = f"Mantenimiento_{QDate.currentDate().toString('yyyyMMdd')}{sufijo}.csv"
        archivo = self.guardar_archivo_dialogo(t("title_exportar_csv"), nombre_defecto, "CSV (*.csv)")
        if not archivo: return
        try:
            datos = self.db.obtener_todas_cronologico(filtro_usuario)
            mapa_maquinas = maquinas.mapa_rutas_completas()
            with open(archivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                # Nuevos encabezados sin Tags, añadiendo Máquina, Foto Antes y Foto Después
                writer.writerow([tt("hdr_id", "ID"), tt("hdr_fecha", "Fecha"), tt("hdr_descripcion", "Descripción"), tt("hdr_maquina", "Máquina"), tt("hdr_realizado_por", "Realizado por"), tt("hdr_prioridad", "Prioridad"), tt("hdr_foto_antes", "Foto Antes"), tt("hdr_foto_despues", "Foto Después")])
                for tarea in datos:
                    # Convertir formato de fecha de YYYY-MM-DD al formato corto del idioma activo
                    fecha_formateada = idiomas.formato_fecha_localizada(tarea[1])

                    # Limpiamos FOTO y REF de la descripción
                    desc_limpia = re.sub(r"\[FOTO.*?:.*?\]", "", tarea[2])
                    desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                    # Extraer nombres de fotos
                    foto_antes = "-"
                    m = re.search(r"\[FOTO:\s*(.*?)\]", tarea[2])
                    if m: foto_antes = m.group(1).split("]")[0].strip()

                    foto_despues = "-"
                    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", tarea[2])
                    if m_d: foto_despues = m_d.group(1).split("]")[0].strip()

                    autor = tarea[4] if len(tarea) > 4 and tarea[4] else usuarios.ETIQUETA_HISTORICO
                    maquina_nombre = mapa_maquinas.get(tarea[5], "-") if len(tarea) > 5 and tarea[5] else "-"
                    prioridad_txt = traducir_prioridad(tarea[6]) if len(tarea) > 6 else traducir_prioridad("Media")
                    writer.writerow([tarea[0], fecha_formateada, desc_limpia, maquina_nombre, autor, prioridad_txt, foto_antes, foto_despues])
            QMessageBox.information(self, t("title_exportado"), t("msg_csv_guardado"))
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))

    def exportar_excel(self):
        try: import xlsxwriter
        except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        dlg = DialogoFiltroTecnico(self, t("title_exportar_excel"))
        if not dlg.exec(): return
        filtro_usuario = dlg.get_filtro()
        nombre_limpio = re.sub(r'[<>:\"/\\\\|?*]', '', filtro_usuario) if filtro_usuario else ""
        sufijo = f"_{nombre_limpio}" if nombre_limpio else ""
        nombre_defecto = f"Mantenimiento_{QDate.currentDate().toString('yyyyMMdd')}{sufijo}.xlsx"
        archivo = self.guardar_archivo_dialogo(t("title_exportar_excel"), nombre_defecto, "Excel (*.xlsx)")
        if not archivo: return
        try:
            workbook = xlsxwriter.Workbook(archivo)
            worksheet = workbook.add_worksheet("Registro")

            # Estilos profesionales
            bold = workbook.add_format({'bold': True, 'bg_color': '#3daee9', 'color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            wrap = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
            center = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'border': 1})

            # Nuevos encabezados
            headers = [tt("hdr_id", "ID"), tt("hdr_fecha", "Fecha"), tt("hdr_descripcion", "Descripción"), tt("hdr_maquina", "Máquina"), tt("hdr_realizado_por", "Realizado por"), tt("hdr_prioridad", "Prioridad"), tt("hdr_foto_antes", "Foto Antes"), tt("hdr_foto_despues", "Foto Después")]
            for col, text in enumerate(headers): worksheet.write(0, col, text, bold)

            # Ajuste de anchura de columnas
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 12)
            worksheet.set_column('C:C', 60) # Descripción ancha
            worksheet.set_column('D:D', 25) # Máquina
            worksheet.set_column('E:E', 20) # Realizado por
            worksheet.set_column('F:F', 12) # Prioridad
            worksheet.set_column('G:G', 25) # Foto Antes
            worksheet.set_column('H:H', 25) # Foto Después

            # --- FUNCIÓN INTERNA PARA CALCULAR LA ESCALA PERFECTA ---
            def obtener_opciones_img(ruta_img):
                pix = QPixmap(ruta_img)
                if pix.isNull() or pix.width() == 0 or pix.height() == 0:
                    return None

                # Tamaño máximo deseado en píxeles (para que quepa justo en la celda)
                max_w = 160.0
                max_h = 100.0

                # Calcular escala manteniendo la proporción real de la foto
                scale = min(max_w / pix.width(), max_h / pix.height())

                return {
                    'x_scale': scale,
                    'y_scale': scale,
                    'x_offset': 5,
                    'y_offset': 5,
                    'object_position': 1
                }

            datos = self.db.obtener_todas_cronologico(filtro_usuario)
            mapa_maquinas = maquinas.mapa_rutas_completas()
            row = 1
            for tarea in datos:
                # Convertir formato de fecha al formato corto del idioma activo
                fecha_formateada = idiomas.formato_fecha_localizada(tarea[1])

                worksheet.write(row, 0, tarea[0], center)
                worksheet.write(row, 1, fecha_formateada, center)

                # Limpieza de texto
                desc_limpia = re.sub(r"\[FOTO.*?:.*?\]", "", tarea[2])
                desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                worksheet.write(row, 2, desc_limpia, wrap)

                maquina_nombre = mapa_maquinas.get(tarea[5], "-") if len(tarea) > 5 and tarea[5] else "-"
                worksheet.write(row, 3, maquina_nombre, center)

                autor = tarea[4] if len(tarea) > 4 and tarea[4] else usuarios.ETIQUETA_HISTORICO
                worksheet.write(row, 4, autor, center)

                prioridad_txt = traducir_prioridad(tarea[6]) if len(tarea) > 6 else traducir_prioridad("Media")
                worksheet.write(row, 5, prioridad_txt, center)

                # Incrustar FOTO ANTES
                m = re.search(r"\[FOTO:\s*(.*?)\]", tarea[2])
                if m:
                    nombre = m.group(1).split("]")[0].strip()
                    ruta = os.path.join(self.carpeta_fotos, nombre)
                    if os.path.exists(ruta):
                        opc = obtener_opciones_img(ruta)
                        if opc:
                            try: worksheet.insert_image(row, 6, ruta, opc)
                            except: worksheet.write(row, 6, "Err Img", center)
                        else:
                            worksheet.write(row, 6, "Err Img", center)
                    else: worksheet.write(row, 6, "No File", center)
                else: worksheet.write(row, 6, "-", center)

                # Incrustar FOTO DESPUÉS
                m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", tarea[2])
                if m_d:
                    nombre_d = m_d.group(1).split("]")[0].strip()
                    ruta_d = os.path.join(self.carpeta_fotos, nombre_d)
                    if os.path.exists(ruta_d):
                        opc = obtener_opciones_img(ruta_d)
                        if opc:
                            try: worksheet.insert_image(row, 7, ruta_d, opc)
                            except: worksheet.write(row, 7, "Err Img", center)
                        else:
                            worksheet.write(row, 7, "Err Img", center)
                    else: worksheet.write(row, 7, "No File", center)
                else: worksheet.write(row, 7, "-", center)

                worksheet.set_row(row, 90) # Altura de fila fija
                row += 1

            workbook.close()
            QMessageBox.information(self, t("title_exportado"), t("msg_excel_guardado"))
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))

    def init_dashboard_tab(self):
        l = QVBoxLayout()
        h_cards = QHBoxLayout()
        style_card = "QGroupBox { border-radius: 8px; margin-top: 10px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; } QLabel { font-size: 24px; font-weight: bold; }"
        self.card_avisos = QGroupBox(t("lbl_avisos_pendientes")); self.card_avisos.setStyleSheet(style_card)
        l_c1 = QVBoxLayout(); self.lbl_count_avisos = QLabel("0"); self.lbl_count_avisos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c1.addWidget(self.lbl_count_avisos); self.card_avisos.setLayout(l_c1); h_cards.addWidget(self.card_avisos)
        self.card_todos = QGroupBox(t("lbl_tareas_por_hacer")); self.card_todos.setStyleSheet(style_card)
        l_c2 = QVBoxLayout(); self.lbl_count_todos = QLabel("0"); self.lbl_count_todos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c2.addWidget(self.lbl_count_todos); self.card_todos.setLayout(l_c2); h_cards.addWidget(self.card_todos)
        self.card_regs = QGroupBox(t("lbl_registros_este_mes")); self.card_regs.setStyleSheet(style_card)
        l_c3 = QVBoxLayout(); self.lbl_count_regs = QLabel("0"); self.lbl_count_regs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c3.addWidget(self.lbl_count_regs); self.card_regs.setLayout(l_c3); h_cards.addWidget(self.card_regs)
        style_card_pequena = "QGroupBox { border-radius: 8px; margin-top: 10px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; } QLabel { font-size: 18px; font-weight: bold; }"
        self.card_mtbf = QGroupBox(tt("lbl_mtbf_global", "MTBF medio")); self.card_mtbf.setStyleSheet(style_card_pequena)
        l_c4 = QVBoxLayout(); self.lbl_mtbf_global = QLabel("--"); self.lbl_mtbf_global.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c4.addWidget(self.lbl_mtbf_global); self.card_mtbf.setLayout(l_c4); h_cards.addWidget(self.card_mtbf)
        self.card_mttr = QGroupBox(tt("lbl_mttr_global", "MTTR medio")); self.card_mttr.setStyleSheet(style_card_pequena)
        l_c5 = QVBoxLayout(); self.lbl_mttr_global = QLabel("--"); self.lbl_mttr_global.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c5.addWidget(self.lbl_mttr_global); self.card_mttr.setLayout(l_c5); h_cards.addWidget(self.card_mttr)
        l.addLayout(h_cards)
        h_split = QHBoxLayout()
        v_list = QVBoxLayout()
        v_list.addWidget(QLabel(tt("lbl_ranking_maquinas_averias", "Máquinas con más averías")))
        self.grafico_ranking_averias = GraficoBarrasRanking(color="#c0392b"); v_list.addWidget(self.grafico_ranking_averias)
        v_list.addWidget(QLabel(tt("lbl_averias_por_mes", "Averías por mes")))
        self.grafico_averias_mes = GraficoBarrasMensual(color="#e67e22"); v_list.addWidget(self.grafico_averias_mes)
        h_split.addLayout(v_list, 80)
        v_stats = QVBoxLayout(); v_stats.addWidget(QLabel(t("lbl_distribucion")))
        self.group_stats = QGroupBox(); self.group_stats.setStyleSheet("QGroupBox { border-radius: 6px; }")
        layout_stats = QVBoxLayout(); layout_stats.setSpacing(10); layout_stats.setContentsMargins(5, 10, 5, 5)
        def crear_barra(titulo, color):
            lbl = QLabel(titulo); lbl.setStyleSheet("font-size: 12px;")
            bar = QProgressBar(); bar.setStyleSheet(f"QProgressBar {{ border-radius: 4px; text-align: center; height: 18px; font-size: 11px; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}"); bar.setValue(0)
            return lbl, bar
        self.lbl_elec, self.bar_elec = crear_barra(f"⚡ {t('tag_electrico')}", "#3daee9"); layout_stats.addWidget(self.lbl_elec); layout_stats.addWidget(self.bar_elec)
        self.lbl_mec, self.bar_mec = crear_barra(f"⚙️ {t('tag_mecanico')}", "#e67e22"); layout_stats.addWidget(self.lbl_mec); layout_stats.addWidget(self.bar_mec)
        self.lbl_prev, self.bar_prev = crear_barra(f"🛡️ {t('tag_preventivo')}", "#27ae60"); layout_stats.addWidget(self.lbl_prev); layout_stats.addWidget(self.bar_prev)
        self.lbl_urg, self.bar_urg = crear_barra(f"🚨 {t('tag_urgente')}", "#c0392b"); layout_stats.addWidget(self.lbl_urg); layout_stats.addWidget(self.bar_urg)
        layout_stats.addStretch(); self.group_stats.setLayout(layout_stats); v_stats.addWidget(self.group_stats); h_split.addLayout(v_stats, 20); l.addLayout(h_split); self.tab_dashboard.setLayout(l)

    def refresh_dashboard(self):
        avisos = self._avisos_visibles(); hoy = QDate.currentDate(); pendientes_reales = 0
        for aid, tit, finicio, freq, dur, ult, *_ in avisos:
            if not finicio: continue
            fi = QDate.fromString(finicio, "yyyy-MM-dd")
            if not freq: freq = "Anual"
            freq = idiomas.normalizar_frecuencia(freq)
            # Un aviso "Diario" se resetea cada día: no le aplicamos la duración
            # configurada, porque un margen de varios días haría que el de ayer
            # siguiera contando como "hecho" hoy.
            dur_ventana = 0 if freq == "Diario" else dur
            ocurrencia = fi
            while ocurrencia.addDays(dur_ventana) < hoy:
                if freq == "Diario": ocurrencia = ocurrencia.addDays(1)
                elif freq == "Semanal": ocurrencia = ocurrencia.addDays(7)
                elif freq == "Mensual": ocurrencia = ocurrencia.addMonths(1)
                elif freq == "Trimestral": ocurrencia = ocurrencia.addMonths(3)
                elif freq == "Semestral": ocurrencia = ocurrencia.addMonths(6)
                elif freq == "Anual": ocurrencia = ocurrencia.addYears(1)
                else: break
            fin_ocurrencia = ocurrencia.addDays(dur_ventana)
            if ocurrencia <= hoy <= fin_ocurrencia and ult != ocurrencia.toString("yyyy-MM-dd"): pendientes_reales += 1
        self.lbl_count_avisos.setText(str(pendientes_reales))
        self.lbl_count_avisos.setStyleSheet("color: #e74c3c; font-size: 32px; font-weight: bold;" if pendientes_reales > 0 else "color: #2ecc71; font-size: 32px; font-weight: bold;")
        todos = self.db.obtener_pendientes(); self.lbl_count_todos.setText(str(len(todos))); self.lbl_count_todos.setStyleSheet("color: #f1c40f; font-size: 32px; font-weight: bold;")
        registros = self.db.obtener_todas_cronologico(); mes_actual = hoy.toString("yyyy-MM"); count_mes = sum(1 for r in registros if r[1].startswith(mes_actual))
        self.lbl_count_regs.setText(str(count_mes)); self.lbl_count_regs.setStyleSheet("color: #3daee9; font-size: 32px; font-weight: bold;")
        self.grafico_ranking_averias.establecer_datos(maquinas.ranking_averias())
        self.grafico_averias_mes.establecer_datos(maquinas.averias_por_mes())
        indicadores = maquinas.indicadores_fiabilidad_global()
        mtbf = indicadores["mtbf_dias"]
        self.lbl_mtbf_global.setText(f"{mtbf:.0f} {tt('lbl_dias_abrev', 'días')}" if mtbf is not None else "--")
        mttr = indicadores["mttr_horas"]
        self.lbl_mttr_global.setText(f"{mttr:.1f} {tt('lbl_horas_abrev', 'h')}" if mttr is not None else "--")
        total_tareas = len(registros)
        if total_tareas > 0:
            c_elec = sum(1 for r in registros if "eléctrico" in r[3].lower() or "electrico" in r[3].lower())
            c_mec = sum(1 for r in registros if "mecánico" in r[3].lower() or "mecanico" in r[3].lower())
            c_prev = sum(1 for r in registros if "preventivo" in r[3].lower())
            c_urg = sum(1 for r in registros if "urgente" in r[3].lower() or "avería" in r[3].lower())
            self.bar_elec.setValue(int((c_elec/total_tareas)*100)); self.bar_elec.setFormat(f"{int((c_elec/total_tareas)*100)}% ({c_elec})")
            self.bar_mec.setValue(int((c_mec/total_tareas)*100)); self.bar_mec.setFormat(f"{int((c_mec/total_tareas)*100)}% ({c_mec})")
            self.bar_prev.setValue(int((c_prev/total_tareas)*100)); self.bar_prev.setFormat(f"{int((c_prev/total_tareas)*100)}% ({c_prev})")
            self.bar_urg.setValue(int((c_urg/total_tareas)*100)); self.bar_urg.setFormat(f"{int((c_urg/total_tareas)*100)}% ({c_urg})")
        else:
            for b in [self.bar_elec, self.bar_mec, self.bar_prev, self.bar_urg]: b.setValue(0)

    # ========================================================
    #  NUEVAS FUNCIONES PARA GESTIÓN DE LOGO PDF
    # ========================================================
    def cambiar_logo(self):
        # Use DontUseNativeDialog to ensure stylesheets apply
        archivo, _ = QFileDialog.getOpenFileName(self, t("title_seleccionar_logo"), "", "Imágenes (*.jpg *.png *.jpeg)", options=QFileDialog.Option.DontUseNativeDialog)
        if archivo:
            try:
                # Copiamos la imagen a la carpeta local con el nombre que busca el PDF
                # Use DATA_DIR path
                destino = os.path.join(DATA_DIR, "Logo.jpg")
                shutil.copy2(archivo, destino)
                QMessageBox.information(self, t("title_logo_actualizado"), t("msg_logo_actualizado"))
            except Exception as e:
                QMessageBox.critical(self, t("title_error"), str(e))

    def quitar_logo(self):
        # Use DATA_DIR path
        destino = os.path.join(DATA_DIR, "Logo.jpg")
        if os.path.exists(destino):
            try:
                os.remove(destino)
                QMessageBox.information(self, t("title_logo_borrado"), t("msg_logo_borrado"))
            except Exception as e:
                QMessageBox.critical(self, t("title_error"), str(e))
        else:
            QMessageBox.information(self, t("title_informacion"), t("msg_sin_logo"))

    def exportar_pdf(self):
        dlg = DialogoExportarPDF(self)
        if not dlg.exec(): return
        modo, inicio, fin, filtro_usuario, incluir_graficos = dlg.get_data()
        sufijo_u = f" — {filtro_usuario}" if filtro_usuario else ""
        cond_u = " AND usuario_nombre = ?" if filtro_usuario else ""
        param_u = [filtro_usuario] if filtro_usuario else []

        try:
            conn = self.db.conectar()
            c = conn.cursor()
            lista_trabajos = []

            if modo == "RANGO" and inicio and fin:
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id, COALESCE(prioridad,'Media') FROM tareas "
                          "WHERE fecha BETWEEN ? AND ?" + cond_u + " ORDER BY fecha DESC, id DESC",
                          [inicio, fin] + param_u)
                datos = c.fetchall()
                if not datos: return
                nombre_defecto = f"Reporte_Mantenimiento_{inicio}_a_{fin}.pdf"
                archivo = self.guardar_archivo_dialogo(t("title_guardar_pdf"), nombre_defecto, "PDF (*.pdf)")
                if not archivo: return
                titulo_pdf = t("titulo_reporte_rango").format(inicio=inicio, fin=fin) + sufijo_u
                lista_trabajos.append({"archivo": archivo, "titulo": titulo_pdf, "datos": datos, "rango": (inicio, fin)})

            elif modo == "TODO":
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id, COALESCE(prioridad,'Media') FROM tareas "
                          "WHERE 1=1" + cond_u + " ORDER BY fecha DESC, id DESC", param_u)
                datos = c.fetchall()
                if not datos: return
                nombre_defecto = f"Reporte_Histórico_Completo_{datetime.now().strftime('%Y%m%d')}.pdf"
                archivo = self.guardar_archivo_dialogo(t("title_guardar_pdf"), nombre_defecto, "PDF (*.pdf)")
                if not archivo: return
                lista_trabajos.append({"archivo": archivo, "titulo": t("titulo_reporte_historico") + sufijo_u, "datos": datos, "rango": None})

            elif modo == "MESES":
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id, COALESCE(prioridad,'Media') FROM tareas "
                          "WHERE 1=1" + cond_u + " ORDER BY fecha DESC, id DESC", param_u)
                datos = c.fetchall()
                if not datos: return

                # Pedir carpeta en vez de archivo
                carpeta_destino = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta para Guardar los PDFs", "", options=QFileDialog.Option.DontUseNativeDialog)
                if not carpeta_destino: return

                # Agrupar por mes (YYYY-MM)
                datos_por_mes = {}
                for row in datos:
                    fecha_str = row[0]
                    if not fecha_str or len(fecha_str) < 7: continue
                    mes_str = fecha_str[:7]
                    if mes_str not in datos_por_mes:
                        datos_por_mes[mes_str] = []
                    datos_por_mes[mes_str].append(row)

                for mes, datos_mes in datos_por_mes.items():
                    archivo = os.path.join(carpeta_destino, f"Reporte_Mantenimiento_{mes}.pdf")
                    titulo_mes = t("titulo_reporte_mes").format(mes=mes) + sufijo_u
                    lista_trabajos.append({"archivo": archivo, "titulo": titulo_mes, "datos": datos_mes, "rango": (f"{mes}-01", f"{mes}-31")})

            conn.close()
        except Exception as e:
            QMessageBox.critical(self, t("title_error_db"), str(e))
            return

        if not lista_trabajos: return

        if incluir_graficos:
            for trabajo in lista_trabajos:
                ini_rango, fin_rango = trabajo["rango"] if trabajo["rango"] else (None, None)
                trabajo["graficos"] = self._generar_graficos_pdf(ini_rango, fin_rango)

        # Configurar UI de progreso
        self.progreso_pdf = QDialog(self)
        self.progreso_pdf.setWindowTitle(t("title_generando_pdf"))
        self.progreso_pdf.setFixedSize(450, 120)
        self.progreso_pdf.setWindowModality(Qt.WindowModality.ApplicationModal)
        l = QVBoxLayout()
        l.addWidget(QLabel(t("lbl_procesando_pdf")))
        bar = QProgressBar()
        bar.setRange(0, 0)
        l.addWidget(bar)
        self.progreso_pdf.setLayout(l)
        self.progreso_pdf.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        # Iniciar Hilo
        self.hilo_pdf = GeneradorPDFThread(lista_trabajos, self.carpeta_fotos, maquinas.mapa_rutas_completas())
        self.hilo_pdf.resultado.connect(self.pdf_finalizado)
        self.hilo_pdf.start()

        self.progreso_pdf.exec()

    def _generar_graficos_pdf(self, fecha_inicio=None, fecha_fin=None):
        """Renderiza a PNG (en el hilo principal, porque QWidget.grab() no se
        puede usar desde el QThread que genera el PDF) los mismos gráficos del
        dashboard, con el texto en negro para que se lean sobre fondo blanco,
        y los guarda en una carpeta temporal que el hilo del PDF borra al
        terminar. Si se indican fecha_inicio/fecha_fin ('YYYY-MM-DD'), los
        gráficos y los indicadores solo tienen en cuenta ese periodo, para
        que un PDF exportado por rango o por mes muestre sus propias
        estadísticas y no las de todo el histórico. Si no hay ninguna avería
        registrada en el periodo, no genera nada."""
        indicadores = maquinas.indicadores_fiabilidad_global(fecha_inicio, fecha_fin)
        if indicadores["num_averias"] == 0:
            return None

        registros = self.db.obtener_todas_cronologico()
        if fecha_inicio and fecha_fin:
            registros = [r for r in registros if r[1] and fecha_inicio <= r[1] <= fecha_fin]
        total = len(registros)
        c_elec = sum(1 for r in registros if "eléctrico" in r[3].lower() or "electrico" in r[3].lower())
        c_mec = sum(1 for r in registros if "mecánico" in r[3].lower() or "mecanico" in r[3].lower())
        c_prev = sum(1 for r in registros if "preventivo" in r[3].lower())
        c_urg = sum(1 for r in registros if "urgente" in r[3].lower() or "avería" in r[3].lower())
        datos_pie = [
            (tt("tag_electrico", "Eléctrico"), c_elec), (tt("tag_mecanico", "Mecánico"), c_mec),
            (tt("tag_preventivo", "Preventivo"), c_prev), (tt("tag_urgente", "Urgente"), c_urg),
        ] if total else []

        ancho, alto = 760, 260
        color_fondo_pdf = "#f0f0f0"
        grafico_ranking = GraficoBarrasRanking(color="#c0392b", color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_ranking.establecer_datos(maquinas.ranking_averias(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin))
        grafico_ranking.resize(ancho, alto)

        grafico_mensual = GraficoBarrasMensual(color="#e67e22", color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_mensual.establecer_datos(maquinas.averias_por_mes(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin))
        grafico_mensual.resize(ancho, alto)

        grafico_pie = GraficoCircularTrabajos(color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_pie.establecer_datos(datos_pie)
        grafico_pie.resize(ancho, alto)

        tmp_dir = tempfile.mkdtemp(prefix="mantpro_pdf_graficos_")
        png_ranking = os.path.join(tmp_dir, "ranking.png")
        png_mensual = os.path.join(tmp_dir, "mensual.png")
        png_pie = os.path.join(tmp_dir, "pie.png")
        grafico_ranking.grab().save(png_ranking, "PNG")
        grafico_mensual.grab().save(png_mensual, "PNG")
        grafico_pie.grab().save(png_pie, "PNG")

        return {
            "png_ranking": png_ranking, "png_mensual": png_mensual, "png_pie": png_pie,
            "indicadores": indicadores, "tmp_dir": tmp_dir,
        }

    def pdf_finalizado(self, exito, mensaje):
        self.progreso_pdf.accept() # Cierra el diálogo de progreso
        if exito:
            QMessageBox.information(self, t("title_exito"), mensaje)
        else:
            QMessageBox.critical(self, t("title_error_pdf"), mensaje)

    def _menu_contextual_historial(self, pos):
        """Menú con clic derecho sobre la tabla del historial."""
        seleccion = self.h_table.selectionModel().selectedRows()
        if not seleccion:
            return

        menu = QMenu(self)
        n = len(seleccion)

        if n == 1:
            tarea_id = self.h_table.item(seleccion[0].row(), 0).data(Qt.ItemDataRole.UserRole)
            puede = self._puede_modificar(tarea_id)
            act_editar = menu.addAction(t("btn_editar"), lambda: self.edit_rec(self.h_table))
            act_editar.setEnabled(puede)
            if not puede:
                act_editar.setToolTip(tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))

        # Cambiar autor (admin)
        if usuarios.es_admin():
            texto = tt("ctx_cambiar_autor", "👤 Cambiar autor") if n == 1 else \
                    tt("ctx_cambiar_autor_n", "👤 Cambiar autor ({n} registros)").format(n=n)
            menu.addAction(texto, lambda: self._reasignar_masivo(seleccion))

        if n == 1:
            act_revertir = menu.addAction(tt("ctx_revertir_pendiente", "↩️ Revertir a pendiente"),
                                           lambda: self.revertir_a_pendiente(self.h_table))
            act_revertir.setEnabled(puede)
            if not puede:
                act_revertir.setToolTip(tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))

            menu.addSeparator()
            act_borrar = menu.addAction(t("btn_borrar_seleccionado"), lambda: self.del_rec(self.h_table))
            act_borrar.setEnabled(puede)

        menu.exec(self.h_table.viewport().mapToGlobal(pos))

    def _reasignar_masivo(self, seleccion):
        """Cambia el autor de uno o varios registros del historial."""
        if not usuarios.es_admin():
            return

        ids = []
        for idx in seleccion:
            item = self.h_table.item(idx.row(), 0)
            if item:
                ids.append(item.data(Qt.ItemDataRole.UserRole))
        if not ids:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tt("ctx_cambiar_autor", "Cambiar autor"))
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(
            tt("lbl_nuevo_autor", "Nuevo autor para {n} registro(s):").format(n=len(ids))))

        combo = QComboBox()
        combo.addItem(usuarios.ETIQUETA_HISTORICO, None)
        for u in usuarios.listar_usuarios(incluir_inactivos=True):
            combo.addItem(u["nombre"], u["id"])
        lay.addWidget(combo)

        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        caja.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        caja.accepted.connect(dlg.accept)
        caja.rejected.connect(dlg.reject)
        lay.addWidget(caja)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        nuevo_uid = combo.currentData()
        nuevo_nombre = combo.currentText() if nuevo_uid is not None else usuarios.ETIQUETA_HISTORICO

        # --- Diálogo de progreso modal (bloquea la ventana principal) ---
        progreso = QProgressDialog(
            tt("msg_reasignando", "Reasignando registros…"), None, 0, len(ids), self)
        progreso.setWindowTitle(tt("ctx_cambiar_autor", "Cambiar autor"))
        progreso.setWindowModality(Qt.WindowModality.ApplicationModal)
        progreso.setMinimumDuration(0)
        progreso.setCancelButton(None)  # Sin botón de cancelar
        progreso.setAutoClose(False)
        progreso.setValue(0)
        QApplication.processEvents()

        try:
            conn = self.db.conectar()
            c = conn.cursor()
            auditorias = []
            for i, tarea_id in enumerate(ids):
                c.execute("SELECT COALESCE(usuario_nombre,'') FROM tareas WHERE id=?", (tarea_id,))
                fila = c.fetchone()
                anterior = fila[0] if fila and fila[0] else usuarios.ETIQUETA_HISTORICO
                if anterior != nuevo_nombre:
                    c.execute("UPDATE tareas SET usuario_id=?, usuario_nombre=? WHERE id=?",
                              (nuevo_uid, nuevo_nombre, tarea_id))
                    auditorias.append((tarea_id, f"autor: {anterior} → {nuevo_nombre}"))
                progreso.setValue(i + 1)
                progreso.setLabelText(
                    tt("msg_reasignando_n", "Reasignando {i} de {n}…").format(i=i + 1, n=len(ids)))
                QApplication.processEvents()
            conn.commit()
            conn.close()

            # Auditoría DESPUÉS de cerrar la conexión (evita deadlock en SQLite)
            progreso.setLabelText(tt("msg_guardando_auditoria", "Guardando registro de cambios…"))
            progreso.setMaximum(len(auditorias))
            progreso.setValue(0)
            QApplication.processEvents()
            for i, (tarea_id, detalle) in enumerate(auditorias):
                usuarios.registrar_auditoria(usuarios.id_actual(), tarea_id, "editar", detalle)
                progreso.setValue(i + 1)
                if i % 10 == 0:
                    QApplication.processEvents()
        except Exception as e:
            progreso.close()
            QMessageBox.critical(self, t("title_error"), str(e))
            return

        progreso.close()
        self.refresh_all()
        self.statusBar().showMessage(
            tt("msg_autor_cambiado", "{n} registro(s) reasignado(s) a {nombre}").format(
                n=len(ids), nombre=nuevo_nombre), 4000)

    def ver_auditoria(self):
        if not usuarios.es_admin():
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(tt("menu_auditoria", "Registro de cambios"))
        dlg.resize(900, 500)
        lay = QVBoxLayout(dlg)

        fila = QHBoxLayout()
        fila.addWidget(QLabel(tt("hdr_realizado_por", "Realizado por") + ":"))
        combo_u = QComboBox()
        combo_u.addItem(tt("filtro_todos", "Todos"), "TODOS")
        for u in usuarios.listar_usuarios(incluir_inactivos=True):
            combo_u.addItem(u["nombre"], u["id"])
        fila.addWidget(combo_u)

        fila.addWidget(QLabel(tt("lbl_accion", "Acción") + ":"))
        combo_a = QComboBox()
        combo_a.addItem(tt("filtro_todos", "Todos"), "TODOS")
        combo_a.addItem(tt("accion_editar", "Editar"), "editar")
        combo_a.addItem(tt("accion_borrar", "Borrar"), "borrar")
        combo_a.addItem(tt("accion_revertir", "Revertir a pendiente"), "revertir")
        fila.addWidget(combo_a)
        lay.addLayout(fila)

        tabla = QTableWidget(0, 5)
        tabla.setHorizontalHeaderLabels([
            tt("lbl_fecha_hora", "Fecha y hora"),
            tt("hdr_realizado_por", "Realizado por"),
            tt("lbl_accion", "Acción"),
            "ID",
            tt("lbl_detalle", "Detalle"),
        ])
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setColumnWidth(0, 150)
        tabla.setColumnWidth(1, 160)
        tabla.setColumnWidth(2, 100)
        tabla.setColumnWidth(3, 45)
        tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        tabla.setAlternatingRowColors(True)
        lay.addWidget(tabla)

        def refrescar(*_):
            uid = combo_u.currentData()
            accion = combo_a.currentData()
            registros = usuarios.obtener_auditoria(
                usuario_id=uid if uid != "TODOS" else None,
                accion=accion if accion != "TODOS" else None,
                limite=500)
            tabla.setRowCount(len(registros))
            for fila_n, r in enumerate(registros):
                tabla.setItem(fila_n, 0, QTableWidgetItem(r["fecha"]))
                tabla.setItem(fila_n, 1, QTableWidgetItem(r["usuario_nombre"]))
                accion_txt = {"editar": "✏️ Editado", "borrar": "🗑️ Borrado", "revertir": "↩️ Revertido a pendiente"}.get(r["accion"], r["accion"])
                tabla.setItem(fila_n, 2, QTableWidgetItem(accion_txt))
                tabla.setItem(fila_n, 3, QTableWidgetItem(str(r["tarea_id"])))
                tabla.setItem(fila_n, 4, QTableWidgetItem(r["detalle"]))

        combo_u.currentIndexChanged.connect(refrescar)
        combo_a.currentIndexChanged.connect(refrescar)
        refrescar()

        cerrar = QPushButton(t("cerrar"))
        cerrar.clicked.connect(dlg.accept)
        lay.addWidget(cerrar)
        dlg.exec()

    def gestionar_usuarios(self):
        if not usuarios.es_admin():
            QMessageBox.warning(self, t("title_error"),
                                tt("msg_solo_admin", "Solo un administrador puede gestionar usuarios."))
            return
        DialogoGestionUsuarios(self).exec()
        if hasattr(self, 'combo_asignar'):
            self._llenar_combo_usuarios(self.combo_asignar, incluir_sin_asignar=True)
            self._llenar_combo_usuarios(self.combo_filtro_todos, incluir_todos=True, incluir_sin_asignar=True)
        if hasattr(self, 'in_av_asignar'):
            self._llenar_combo_usuarios(self.in_av_asignar, incluir_sin_asignar=True)

    def gestionar_sesiones(self):
        if not usuarios.es_admin():
            QMessageBox.warning(self, t("title_error"),
                                tt("msg_solo_admin", "Solo un administrador puede gestionar usuarios."))
            return
        DialogoSesiones(self).exec()

    def cambiar_mi_password(self):
        if not usuarios.SESION_ACTUAL:
            return
        DialogoCambioPassword(self, usuarios.SESION_ACTUAL).exec()

    def cerrar_sesion(self):
        """Cierra la sesión actual y vuelve al login sin salir de la aplicación.
        Si se cancela el login, se cierra la aplicación como al pulsar 'Salir'."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tt("title_cerrar_sesion", "Cerrar sesión"))
        msg.setText(tt("msg_confirmar_cerrar_sesion",
                        "¿Seguro que quieres cerrar la sesión actual?"))
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() != btn_si:
            return

        usuarios.SESION_ACTUAL = None
        self.hide()

        ruta_logo = resource_path("AnabasaSoft.png")
        dlg_login = DialogoLogin(ruta_logo=ruta_logo if os.path.exists(ruta_logo) else None)
        if dlg_login.exec() != QDialog.DialogCode.Accepted:
            self.close()
            return

        self._refrescar_tras_cambio_usuario()
        self.show()
        self.raise_()
        self.activateWindow()

    def _refrescar_tras_cambio_usuario(self):
        """Reconstruye el menú (permisos según rol) y el título tras un login en caliente."""
        self.menuBar().clear()
        self.crear_menu()
        titulo_base = t("title_control_mantenimiento")
        if usuarios.SESION_ACTUAL:
            titulo_base += f"  —  👤 {usuarios.SESION_ACTUAL['nombre']}"
        self.setWindowTitle(titulo_base)
        self.refresh_all()

    def guardar_archivo_dialogo(self, titulo, nombre_defecto, filtro):
        dialogo = QFileDialog(self, titulo); dialogo.setAcceptMode(QFileDialog.AcceptMode.AcceptSave); dialogo.setFileMode(QFileDialog.FileMode.AnyFile); dialogo.setNameFilter(filtro); dialogo.selectFile(nombre_defecto)
        dialogo.setOption(QFileDialog.Option.DontUseNativeDialog, True); dialogo.setLabelText(QFileDialog.DialogLabel.Accept, t("btn_guardar_form")); dialogo.setLabelText(QFileDialog.DialogLabel.Reject, t("btn_cancelar"))
        if dialogo.exec(): return dialogo.selectedFiles()[0]
        return None

    def _fotos_en_uso(self):
        """Nombres de fichero de foto referenciados desde cualquier sitio de la
        BD (trabajos, pendientes y fotos de máquinas). Se usa tanto para saber
        qué es basura como para saber qué hace falta restaurar de un backup."""
        fotos_en_uso = set(); conn = self.db.conectar(); c = conn.cursor()
        c.execute("SELECT descripcion FROM tareas")
        for row in c.fetchall():
            m = re.search(r"\[FOTO:\s*(.*?)\]", row[0])
            if m: fotos_en_uso.add(m.group(1).strip())
            m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", row[0])
            if m_d: fotos_en_uso.add(m_d.group(1).strip())
        c.execute("SELECT detalles FROM pendientes")
        for row in c.fetchall():
            m = re.search(r"\[FOTO:\s*(.*?)\]", row[0])
            if m: fotos_en_uso.add(m.group(1).strip())
            m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", row[0])
            if m_d: fotos_en_uso.add(m_d.group(1).strip())
        c.execute("SELECT foto FROM maquinas WHERE foto IS NOT NULL")
        for row in c.fetchall():
            if row[0]: fotos_en_uso.add(row[0].strip())
        conn.close()
        return fotos_en_uso

    def limpiar_fotos_huerfanas(self, silencioso=False, limpiar_backups=False):
        try:
            fotos_en_uso = self._fotos_en_uso()

            basura = []
            if os.path.exists(self.carpeta_fotos):
                for f in os.listdir(self.carpeta_fotos):
                    if f not in fotos_en_uso and f not in ["Logo.jpg", "icono.png"] and not f.startswith("QR_"):
                        basura.append(f)

            # Los ZIP de fotos del backup automático solo se revisan cuando se pide
            # explícitamente desde el menú Herramientas, nunca al cerrar el programa
            # ni antes de un backup manual, para no alargar esas operaciones.
            zips_con_huerfanas = {}
            if limpiar_backups and os.path.isdir(self.carpeta_backups_auto):
                for f in os.listdir(self.carpeta_backups_auto):
                    if f.startswith("fotos_backup_") and f.endswith(".zip"):
                        ruta_zip = os.path.join(self.carpeta_backups_auto, f)
                        try:
                            with zipfile.ZipFile(ruta_zip, 'r') as zf:
                                huerfanas = [n for n in zf.namelist() if n not in fotos_en_uso]
                            if huerfanas: zips_con_huerfanas[ruta_zip] = huerfanas
                        except Exception:
                            pass

            total_huerfanas = len(basura) + sum(len(v) for v in zips_con_huerfanas.values())
            if total_huerfanas == 0: return

            confirmado = True
            if not silencioso:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle(t("title_limpieza"))
                msg.setText(t("msg_fotos_basura").format(n=total_huerfanas))
                btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
                msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
                msg.exec()
                if msg.clickedButton() != btn_si: confirmado = False
            if not confirmado: return

            for f in basura:
                try: os.remove(os.path.join(self.carpeta_fotos, f))
                except: pass

            for ruta_zip, huerfanas in zips_con_huerfanas.items():
                try:
                    huerfanas_set = set(huerfanas)
                    ruta_tmp = ruta_zip + ".tmp"
                    with zipfile.ZipFile(ruta_zip, 'r') as origen, \
                         zipfile.ZipFile(ruta_tmp, 'w', zipfile.ZIP_DEFLATED) as nuevo:
                        for n in origen.namelist():
                            if n not in huerfanas_set:
                                nuevo.writestr(n, origen.read(n))
                    os.replace(ruta_tmp, ruta_zip)
                except Exception:
                    pass
        except Exception as e: print(f"Error limpieza: {e}")

    def edit_todo(self, item=None): # Añadimos argumento opcional para el doble click
        row = self.todo_list.currentRow()
        if row < 0: return

        item = self.todo_list.item(row)
        pid = item.data(Qt.ItemDataRole.UserRole)
        titulo_actual = item.data(Qt.ItemDataRole.UserRole + 1)
        detalles_raw = item.data(Qt.ItemDataRole.UserRole + 2)
        prioridad_actual = item.data(Qt.ItemDataRole.UserRole + 4) or "Media"
        especialidad_actual_id = item.data(Qt.ItemDataRole.UserRole + 5)
        asignado_actual_id = item.data(Qt.ItemDataRole.UserRole + 3)

        # --- LÓGICA DE LIMPIEZA VISUAL ---
        ruta_foto_actual = ""
        texto_limpio = detalles_raw
        ref_oculta = "" # Aquí guardaremos la matrícula para no perderla

        if detalles_raw:
            # 1. Detectar FOTO
            m = re.search(r"\[FOTO:\s*(.*?)\]", detalles_raw)
            if m:
                nombre_fichero = m.group(1).split("]")[0].strip()
                ruta_posible = os.path.join(self.carpeta_fotos, nombre_fichero)
                if os.path.exists(ruta_posible):
                    ruta_foto_actual = ruta_posible

            # 2. Detectar y Guardar REF (Matrícula)
            m_ref = re.search(r"\[REF:\s*(\d+)\]", detalles_raw)
            if m_ref:
                ref_oculta = m_ref.group(0) # Guardamos "[REF:12345]" entero

            # 3. Limpiar el texto para que tú lo veas bonito
            texto_limpio = re.sub(r"\[FOTO.*?:.*?\]", "", detalles_raw)
            texto_limpio = re.sub(r"\[REF:.*?\]", "", texto_limpio).strip()

        # Abrimos el diálogo con el texto LIMPIO
        dlg = DialogoEditarPendiente(self, titulo_actual, texto_limpio, ruta_foto_actual, prioridad_actual, asignado_actual_id, especialidad_actual_id)

        if dlg.exec():
            nuevo_t, nuevo_d, nueva_foto, nueva_prioridad, nuevo_asignado_id, nuevo_asignado_nombre, nueva_especialidad_id = dlg.get_data()

            if nuevo_t:
                desc_final = nuevo_d

                # --- RECONSTRUCCIÓN INVISIBLE ---
                # 1. Volvemos a pegar la REF oculta para que el móvil no pierda la foto
                if ref_oculta:
                    desc_final += f" {ref_oculta}"

                # 2. Gestionar Foto nueva
                if nueva_foto:
                    nombre_final = os.path.basename(nueva_foto)
                    if nueva_foto != ruta_foto_actual:
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        nombre_final = f"pc_edit_{ts}_{nombre_final}"
                        destino = os.path.join(self.carpeta_fotos, nombre_final)
                        try: shutil.copy2(nueva_foto, destino)
                        except: pass

                    desc_final += f"\n[FOTO: {nombre_final}]"

                # La asignación/especialidad de un trabajo ya existente solo la
                # puede tocar un admin; un técnico solo las fija al crearlo.
                if not usuarios.es_admin():
                    nueva_especialidad_id = especialidad_actual_id
                    nuevo_asignado_id, nuevo_asignado_nombre = None, None

                # Guardamos en BD (con la REF oculta de nuevo)
                if self.db.actualizar_pendiente(pid, nuevo_t, desc_final, nueva_prioridad, nueva_especialidad_id):
                    if usuarios.es_admin():
                        self.db.asignar_pendiente(pid, nuevo_asignado_id, nuevo_asignado_nombre)
                    self.refresh_todos()
                    self.statusBar().showMessage(t("msg_pendiente_actualizado"), 3000)

import traceback

def manejador_excepciones(exc_type, exc_value, exc_tb):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(error_msg) # Por si lo ejecutas en terminal
    try:
        # Intentamos mostrar el error en una ventanita antes de morir
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(t("title_error_fatal"))
        msg.setText(t("msg_error_fatal"))
        msg.setDetailedText(error_msg)
        msg.exec()
    except:
        pass

sys.excepthook = manejador_excepciones

if __name__ == "__main__":
    # YA NO forzamos "xcb", dejamos que Wayland gestione la ventana nativamente

    app = QApplication(sys.argv)

    # --- 1. CONFIGURACIÓN DE IDENTIDAD ---
    app.setDesktopFileName("MantPro")
    app.setApplicationName("MantPro")
    app.setOrganizationName("AnabasaSoft")

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    ruta_icono = os.path.join(base_path, "icono.png")
    ruta_logo = os.path.join(base_path, "AnabasaSoft.png")

    if os.path.exists(ruta_icono):
        app_icon = QIcon(ruta_icono)
        app.setWindowIcon(app_icon)

    # --- 2. REPARACIÓN DE BASE DE DATOS (CRÍTICO) ---
    # Esto es lo que faltaba. Sin esto, no se crea la columna 'raw_desc' y falla el sync.
    try:
        ruta_db = os.path.join(DATA_DIR, "mantenimiento.db")
        reparar_base_datos(ruta_db)
        print(f"✅ Base de datos verificada en: {ruta_db}")
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")

    # --- 2b. SISTEMA DE USUARIOS + LOGIN OBLIGATORIO ---
    try:
        usuarios.configurar_db(ruta_db)
        primer_arranque = usuarios.inicializar()
        if primer_arranque:
            QMessageBox.information(
                None, "MantPro",
                "Se ha creado el usuario administrador inicial.\n\n"
                "Usuario: admin\nContraseña: admin\n\n"
                "Se te pedirá cambiarla al entrar.")
    except Exception as e:
        print(f"❌ Error inicializando usuarios: {e}")

    # --- 2c. IDIOMA GUARDADO + TRADUCCIÓN DE LOS TEXTOS PROPIOS DE QT ---
    # Se lee ya aquí (antes del login) para que el menú contextual de cortar/
    # copiar/pegar y los botones de los QMessageBox salgan en el idioma correcto
    # desde la primera pantalla, no solo tras abrir la ventana principal.
    try:
        conn_idioma = sqlite3.connect(ruta_db)
        fila_idioma = conn_idioma.execute(
            "SELECT valor FROM config WHERE clave = 'idioma'").fetchone()
        conn_idioma.close()
        idioma_guardado = fila_idioma[0] if fila_idioma else "es"
    except Exception:
        idioma_guardado = "es"
    idiomas.set_idioma(idioma_guardado)
    instalar_traductor_qt(app, idiomas.get_idioma())

    dlg_login = DialogoLogin(ruta_logo=ruta_logo if os.path.exists(ruta_logo) else None)
    if dlg_login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    # --- 3. INSTANCIAR VENTANA PRINCIPAL ---
    try:
        ventana = MaintenanceApp()
    except Exception as e:
        print(f"Error crítico al arrancar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # --- 4. SPLASH SCREEN ESTÁTICO (Compatible con Wayland) ---
    if os.path.exists(ruta_logo):
        pixmap = QPixmap(ruta_logo)

        # Escalado suave si es muy grande
        if pixmap.width() > 600:
            pixmap = pixmap.scaledToWidth(600, Qt.TransformationMode.SmoothTransformation)

        # Creamos el Splash normal
        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()

        # Función para cerrar splash y abrir app
        def iniciar_programa():
            splash.close()
            ventana.show()
            ventana.raise_()
            ventana.activateWindow()
            # Comprobamos actualizaciones solo AHORA, con la ventana ya visible y
            # con el foco, para que el diálogo modal de "nueva versión" no compita
            # con el propio arranque de la ventana principal.
            QTimer.singleShot(500, lambda: ventana.comprobar_actualizaciones(manual=False))

        # Esperamos 2 segundos (2000 ms) y cambiamos
        QTimer.singleShot(2000, iniciar_programa)

    else:
        # Si no hay logo, arranca normal
        ventana.show()
        ventana.raise_()
        ventana.activateWindow()
        QTimer.singleShot(500, lambda: ventana.comprobar_actualizaciones(manual=False))

    sys.exit(app.exec())
