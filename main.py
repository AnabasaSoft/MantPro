import sys
import sqlite3
import requests
import json
import os
import shutil
import socket
import threading
import re
import csv
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as PDFImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
import zipfile
import qrcode
from io import BytesIO

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
                             QSpinBox, QRadioButton, QProgressBar, QTreeView, QMenu, QSplashScreen)

from PyQt6.QtCore import (QDate, Qt, pyqtSignal, QThread, QSettings, QDir,
                          QPropertyAnimation, QEasingCurve, QTimer)

from PyQt6.QtGui import (QAction, QIcon, QColor, QBrush, QTextCharFormat,
                         QPixmap, QImage, QTextCursor, QFileSystemModel)

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

class GeneradorPDFThread(QThread):
    resultado = pyqtSignal(bool, str)

    def __init__(self, archivo, titulo_doc, datos, carpeta_fotos, incluir_fotos):
        super().__init__()
        self.archivo = archivo
        self.titulo_doc = titulo_doc
        self.datos = datos
        self.carpeta_fotos = carpeta_fotos
        self.incluir_fotos = incluir_fotos

    def run(self):
        try:
            doc = SimpleDocTemplate(self.archivo, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
            elements = []; styles = getSampleStyleSheet()

            # --- ZONA LOGO ---
            ruta_logo = os.path.join(DATA_DIR, "Logo.jpg")
            if os.path.exists(ruta_logo):
                try:
                    logo = PDFImage(ruta_logo, width=4*cm, height=2*cm)
                    logo.hAlign = 'LEFT'
                    logo.keepAspectRatio = True
                    elements.append(logo)
                    elements.append(Spacer(1, 10))
                except Exception as e:
                    print("Error cargando logo:", e)
            # -----------------

            elements.append(Paragraph(self.titulo_doc, styles['Title'])); elements.append(Spacer(1, 12))

            data_tabla = [["FECHA", "DESCRIPCIÓN", "TAGS", "FOTO"]]
            style_cell = styles["BodyText"]; style_cell.fontSize = 9

            for fecha, desc, tags in self.datos:
                desc_visual = desc
                img_obj = "-"

                # Gestión de FOTO
                m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
                if m:
                    nombre_foto = m.group(1).split("]")[0].strip()

                    if self.incluir_fotos:
                        ruta_foto = os.path.join(self.carpeta_fotos, nombre_foto)
                        if os.path.exists(ruta_foto):
                            try:
                                img = PDFImage(ruta_foto)
                                img.drawHeight = 2.5*cm
                                img.drawWidth = 3.5*cm
                                img.keepAspectRatio = True
                                img_obj = img
                            except: img_obj = "Error Img"
                        else: img_obj = "No File"
                    else: img_obj = "SÍ"

                # LIMPIEZA DE ETIQUETAS
                desc_visual = re.sub(r"\[FOTO:.*?\]", "", desc_visual)
                desc_visual = re.sub(r"\[REF:.*?\]", "", desc_visual)
                desc_visual = desc_visual.strip()

                p_desc = Paragraph(desc_visual.replace("\n", "<br/>"), style_cell)
                p_tags = Paragraph(tags, style_cell)
                data_tabla.append([fecha, p_desc, p_tags, img_obj])

            ancho_foto = 4*cm if self.incluir_fotos else 1.5*cm
            t = Table(data_tabla, colWidths=[2.5*cm, 9*cm, 3.5*cm, ancho_foto])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))

            elements.append(t)
            doc.build(elements)
            self.resultado.emit(True, "PDF generado correctamente.")

        except Exception as e:
            self.resultado.emit(False, str(e))

class VisorFoto(QDialog):
    def __init__(self, ruta_imagen, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visor de Imagen")
        self.resize(800, 600)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.label)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)
        self.pixmap_original = QPixmap(ruta_imagen)
        if self.pixmap_original.isNull(): self.label.setText("Error al cargar la imagen")
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
        self.setWindowTitle("📸 VISOR MANUAL")
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
        self.preview_lbl = QLabel("Selecciona un archivo...")
        self.preview_lbl.setFixedWidth(500)
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setStyleSheet("border: 2px solid #555; background-color: #222; color: #aaa;")

        btn_ok = QPushButton("✅ ELEGIR ESTA FOTO")
        btn_ok.setMinimumHeight(45)
        btn_ok.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)

        btn_cancel = QPushButton("Cancelar")
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
            self.preview_lbl.setText("📁 Es una carpeta")
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
            self.preview_lbl.setText("❌ No es una imagen válida")

    def selectedFiles(self):
        if self.ruta_seleccionada: return [self.ruta_seleccionada]
        return []

class DialogoQR(QDialog):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sincronizar Móvil")
        self.resize(300, 420)
        l = QVBoxLayout()
        l.addWidget(QLabel("1. Abre la App 'MantPro' en el móvil", alignment=Qt.AlignmentFlag.AlignCenter))
        l.addWidget(QLabel("2. Dale al botón de escanear", alignment=Qt.AlignmentFlag.AlignCenter))
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

    def __init__(self, carpeta_destino, db_path):
        super().__init__()
        self.carpeta_destino = carpeta_destino
        self.db_path = db_path
        self.app = Flask(__name__)
        self.server_port = 5000

        # --- RUTAS EXISTENTES ---
        @self.app.route('/api/upload', methods=['POST'])
        def api_upload():
            try:
                titulo = request.form.get('titulo', 'Sin Título')
                detalles = request.form.get('detalles', '')
                tags = request.form.get('tags', '')
                filename, ruta = self._procesar_foto(request)
                self.registro_recibido.emit(titulo, detalles, tags, filename, ruta)
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/pendientes', methods=['GET'])
        def api_get_pendientes():
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('SELECT id, titulo, detalles FROM pendientes ORDER BY id DESC')
                datos = [{"id": r[0], "titulo": r[1], "detalles": r[2]} for r in c.fetchall()]
                conn.close()
                return jsonify(datos)
            except Exception as e: return jsonify({"error": str(e)}), 500

        @self.app.route('/api/completar_pendiente', methods=['POST'])
        def api_completar():
            try:
                id_p = request.form.get('id')
                titulo = request.form.get('titulo')
                detalles_finales = request.form.get('detalles')
                tags = request.form.get('tags', '')
                filename, ruta_foto = self._procesar_foto(request)

                fecha = datetime.now().strftime("%Y-%m-%d")

                if filename and detalles_finales:
                    detalles_finales = re.sub(r"\[FOTO:.*?\]", "", detalles_finales).strip()

                full_desc = titulo
                if detalles_finales: full_desc += f"\n{detalles_finales}"
                if filename: full_desc += f"\n[FOTO: {filename}]"

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('INSERT INTO tareas (fecha, descripcion, tags) VALUES (?,?,?)', (fecha, full_desc, tags))

                if id_p:
                    c.execute('DELETE FROM pendientes WHERE id=?', (id_p,))

                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/agregar_pendiente', methods=['POST'])
        def api_agregar_pendiente():
            try:
                titulo = request.form.get('titulo')
                detalles = request.form.get('detalles')
                filename, ruta_foto = self._procesar_foto(request)
                if filename: detalles += f"\n[FOTO: {filename}]"
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('INSERT INTO pendientes (titulo, detalles) VALUES (?,?)', (titulo, detalles))
                conn.commit()
                conn.close()
                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/eliminar_pendiente', methods=['POST'])
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
        def api_historial():
            try:
                query = request.args.get('q', '').lower()
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                sql = "SELECT id, fecha, descripcion, tags FROM tareas ORDER BY fecha DESC LIMIT 50"
                params = []

                if query:
                    sql = "SELECT id, fecha, descripcion, tags FROM tareas WHERE descripcion LIKE ? OR tags LIKE ? ORDER BY fecha DESC LIMIT 50"
                    p_query = f"%{query}%"
                    params = [p_query, p_query]

                c.execute(sql, params)
                # Procesamos para extraer nombre de foto si existe
                resultados = []
                for r in c.fetchall():
                    desc = r[2]
                    foto = None
                    m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
                    if m:
                        foto = m.group(1).split("]")[0].strip()

                    # Limpieza visual para el móvil
                    desc_limpia = re.sub(r"\[FOTO:.*?\]", "", desc)
                    desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                    resultados.append({
                        "id": r[0],
                        "fecha": r[1],
                        "descripcion": desc_limpia,
                        "tags": r[3],
                        "foto": foto,
                        "raw_desc": desc # Necesario para editar
                    })
                conn.close()
                return jsonify(resultados)
            except Exception as e: return jsonify({"error": str(e)}), 500

        # ---------------------------------------------------------
        # 1. API AVISOS (Lógica corregida: Acepta retrasos)
        # ---------------------------------------------------------
        @self.app.route('/api/avisos', methods=['GET'])
        def api_avisos():
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("SELECT id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada FROM avisos_recurrentes")
                raw_avisos = c.fetchall()
                conn.close()

                lista_procesada = []
                hoy = datetime.now().date()

                for aid, tit, finicio, freq, dur, ult in raw_avisos:
                    if not finicio: continue
                    try:
                        fi = datetime.strptime(finicio, "%Y-%m-%d").date()
                    except: continue

                    if not freq: freq = "Anual"

                    # Calcular cuándo toca (Misma lógica matemática de antes)
                    ocurrencia = fi
                    while (ocurrencia + timedelta(days=dur)) < hoy:
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

                    fin_ocurrencia = ocurrencia + timedelta(days=dur)

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
                        "rango": f"{ocurrencia.strftime('%d/%m')} - {fin_ocurrencia.strftime('%d/%m')}",
                        "estado": estado,
                        "color": color_code
                    })

                return jsonify(lista_procesada)
            except Exception as e: return jsonify({"error": str(e)}), 500

        # ---------------------------------------------------------
        # 2. API COMPLETAR (Anti-Duplicados)
        # ---------------------------------------------------------
        @self.app.route('/api/completar_aviso', methods=['POST'])
        def api_completar_aviso():
            try:
                id_aviso = request.form.get('id')
                titulo = request.form.get('titulo')
                fecha_custom = request.form.get('fecha_custom')

                fecha_final = fecha_custom if fecha_custom else datetime.now().strftime("%Y-%m-%d")

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                # 1. Actualizar aviso
                c.execute('UPDATE avisos_recurrentes SET ultima_completada=? WHERE id=?', (fecha_final, id_aviso))

                # 2. Insertar en historial SOLO SI NO EXISTE YA HOY
                desc_historial = f"Mantenimiento Preventivo: {titulo}"
                tags_historial = "Preventivo, Aviso Recurrente"

                # Check anti-duplicados
                c.execute("SELECT id FROM tareas WHERE fecha=? AND descripcion=?", (fecha_final, desc_historial))
                existe = c.fetchone()

                if not existe:
                    c.execute('INSERT INTO tareas (fecha, descripcion, tags) VALUES (?,?,?)',
                              (fecha_final, desc_historial, tags_historial))

                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/foto/<path:filename>')
        def serve_foto(filename):
            try:
                return send_from_directory(self.carpeta_destino, filename)
            except Exception as e:
                return str(e), 404

        @self.app.route('/api/editar_historial', methods=['POST'])
        def api_editar_historial():
            try:
                id_t = request.form.get('id')
                desc_final = request.form.get('detalles') # Ya viene formateada desde el móvil
                tags = request.form.get('tags')

                # Si envían foto nueva, procesarla
                filename, ruta = self._procesar_foto(request)
                if filename:
                    # Si hay foto nueva, la añadimos a la descripción
                    desc_final += f"\n[FOTO: {filename}]"

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute("UPDATE tareas SET descripcion=?, tags=? WHERE id=?", (desc_final, tags, id_t))
                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit() # Para refrescar la UI de escritorio
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/descompletar_aviso', methods=['POST'])
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

    def _procesar_foto(self, req):
        if 'foto' in req.files:
            file = req.files['foto']
            if file and file.filename != '':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = re.sub(r'[^a-zA-Z0-9.]', '_', file.filename)
                filename = f"app_{timestamp}_{safe_name}"
                ruta = os.path.join(self.carpeta_destino, filename)
                file.save(ruta)
                return filename, ruta
        return "", ""

    def obtener_ip_local(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]; s.close()
            return ip
        except: return "127.0.0.1"

    def run(self):
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

    def agregar_aviso(self, titulo, fecha_inicio, frecuencia, duracion):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('INSERT INTO avisos_recurrentes (titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada) VALUES (?,?,?,?,?)',
                      (titulo, fecha_inicio, frecuencia, duracion, ""))
            conn.commit(); conn.close(); return True
        except Exception as e: return False

    def actualizar_aviso(self, id_aviso, titulo, fecha_inicio, frecuencia, duracion):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE avisos_recurrentes SET titulo=?, fecha_inicio=?, frecuencia=?, duracion_dias=? WHERE id=?',
                      (titulo, fecha_inicio, frecuencia, duracion, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False

    def obtener_avisos(self):
        try: conn = self.conectar(); c = conn.cursor(); c.execute('SELECT id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada FROM avisos_recurrentes'); return c.fetchall()
        except: return []
    def borrar_aviso(self, i):
        try: conn = self.conectar(); c = conn.cursor(); c.execute('DELETE FROM avisos_recurrentes WHERE id=?', (i,)); conn.commit(); conn.close(); return True
        except: return False
    def marcar_aviso_completado(self, id_aviso, fecha_completada, estado):
        try:
            conn = self.conectar(); c = conn.cursor(); val = fecha_completada if estado else ""
            c.execute('UPDATE avisos_recurrentes SET ultima_completada=? WHERE id=?', (val, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False

    def agregar_tarea(self, f, d, t):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('INSERT INTO tareas (fecha,descripcion,tags) VALUES (?,?,?)',(f,d,t)); conn.commit(); conn.close(); return True
        except: return False
    def obtener_todas_cronologico(self):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT id,fecha,descripcion,tags FROM tareas ORDER BY fecha DESC'); return c.fetchall()
        except: return []
    def obtener_tareas_por_fecha(self,f):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT id,descripcion,tags FROM tareas WHERE fecha=?',(f,)); return c.fetchall()
        except: return []
    def borrar_tarea(self,i):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('DELETE FROM tareas WHERE id=?',(i,)); conn.commit(); conn.close(); return True
        except: return False
    def actualizar_tarea(self,i,f,d,t):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('UPDATE tareas SET fecha=?,descripcion=?,tags=? WHERE id=?',(f,d,t,i)); conn.commit(); conn.close(); return True
        except: return False
    def obtener_tarea_por_id(self,i):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT id,fecha,descripcion,tags FROM tareas WHERE id=?',(i,)); return c.fetchone()
        except: return None
    def buscar_tareas_avanzado(self, texto, fecha=None):
        try:
            conn = self.conectar(); c = conn.cursor(); param_texto = f"%{texto}%"
            query = "SELECT id, fecha, descripcion, tags FROM tareas WHERE (descripcion LIKE ? OR tags LIKE ?)"
            parametros = [param_texto, param_texto]
            if fecha: query += " AND fecha = ?"; parametros.append(fecha)
            query += " ORDER BY fecha DESC"; c.execute(query, parametros); return c.fetchall()
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
    def agregar_pendiente(self,t,d):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('INSERT INTO pendientes (titulo,detalles) VALUES (?,?)',(t,d)); conn.commit(); conn.close(); return True
        except: return False
    def obtener_pendientes(self):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT id,titulo,detalles FROM pendientes ORDER BY id DESC'); return c.fetchall()
        except: return []
    def borrar_pendiente(self,i):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('DELETE FROM pendientes WHERE id=?',(i,)); conn.commit(); conn.close(); return True
        except: return False
    def actualizar_pendiente(self, i, t, d):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE pendientes SET titulo=?, detalles=? WHERE id=?', (t, d, i))
            conn.commit(); conn.close(); return True
        except: return False

class GestorFestivos:
    def __init__(self, db_instance):
        self.db = db_instance
        # USAMOS DATA_DIR PARA EL CACHÉ JSON
        self.archivo_cache = os.path.join(DATA_DIR, "festivos_cache.json")
        self.year = datetime.now().year
        self.url_api = f"https://date.nager.at/api/v3/publicholidays/{self.year}/ES"

    def obtener_config_region(self):
        iso_prov = self.db.get_config("region_iso") or "ES-BI"
        iso_com = self.db.get_config("parent_iso") or "ES-PV"
        return iso_prov, iso_com

    def obtener_festivos(self):
        datos = self.cargar_cache()
        if not datos: datos = self.descargar_festivos()

        l = []
        iso_prov, iso_com = self.obtener_config_region()

        if datos:
            for i in datos:
                counties = i.get('counties')
                if counties is None or iso_com in counties or iso_prov in counties:
                    l.append(QDate.fromString(i.get('date'),"yyyy-MM-dd"))
        return l

    def descargar_festivos(self):
        try:
            r = requests.get(self.url_api)
            if r.status_code == 200:
                with open(self.archivo_cache, 'w') as f: json.dump(r.json(), f)
                return r.json()
        except: return []
        return []

    def cargar_cache(self):
        if os.path.exists(self.archivo_cache):
            try:
                with open(self.archivo_cache, 'r') as f: return json.load(f)
            except: return None
        return None

    def limpiar_cache(self):
        if os.path.exists(self.archivo_cache):
            try:
                os.remove(self.archivo_cache)
            except: pass

class LabelArrastrable(QLabel):
    archivo_soltado = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("Arrastra una foto aquí\no haz clic para buscar")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 2px dashed #666; color: #888; background: #2b2b2b;")
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): self.setStyleSheet("border: 2px dashed #3daee9; background: #333; color: #3daee9;"); event.accept()
        else: event.ignore()
    def dragLeaveEvent(self, event): self.setStyleSheet("border: 2px dashed #666; color: #888; background: #2b2b2b;")
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            ruta = urls[0].toLocalFile()
            if ruta.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')): self.archivo_soltado.emit(ruta)
            else: self.setText("Formato no válido"); self.setStyleSheet("border: 2px dashed red; color: red;")

# ==========================================
# 3. DIÁLOGOS DE INTERFAZ
# ==========================================
class DialogoSeleccionRegion(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Seleccionar Provincia")
        self.resize(400, 150)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Elige tu provincia para descargar los días festivos:"))
        layout.addWidget(QLabel("(Se descargarán festivos nacionales + comunidad + provincia)"))
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
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)

    def get_selection(self):
        nombre = self.combo.currentText()
        datos = PROVINCIAS_ESPAÑA.get(nombre)
        return nombre, datos["iso"], datos["parent"]

class EditDialog(QDialog):
    def __init__(self, parent=None, fecha="", desc="", tags=""):
        super().__init__(parent)
        self.carpeta_fotos = parent.carpeta_fotos if parent else ""
        self.foto_filename = None
        self.ref_oculta = ""
        self.setWindowTitle("Editar Registro")
        self.resize(600, 600)
        l = QVBoxLayout()
        self.de = QDateEdit(); self.de.setDate(QDate.fromString(fecha, "yyyy-MM-dd")); self.de.setCalendarPopup(True); self.de.setDisplayFormat("yyyy-MM-dd")
        l.addWidget(QLabel("Fecha:")); l.addWidget(self.de)
        texto_limpio, nombre_foto, ref_encontrada = self.separar_datos(desc)
        self.foto_filename = nombre_foto
        self.ref_oculta = ref_encontrada
        self.te = QTextEdit(); self.te.setText(texto_limpio)
        l.addWidget(QLabel("Descripción:")); l.addWidget(self.te)
        l.addWidget(QLabel("Foto Adjunta (Arrastra o Click):"))
        self.lbl_foto = LabelArrastrable()
        self.lbl_foto.setFixedHeight(200); self.lbl_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_foto.mousePressEvent = self.abrir_o_buscar
        self.lbl_foto.archivo_soltado.connect(self.procesar_nueva_foto)
        self.actualizar_vista_foto()
        l.addWidget(self.lbl_foto)
        btn_foto = QPushButton("📂 Seleccionar Foto (Botón)")
        btn_foto.clicked.connect(self.seleccionar_foto_boton)
        l.addWidget(btn_foto)
        l.addWidget(QLabel("Etiquetas:"))
        h_tags = QHBoxLayout()
        self.chk_urgente = QCheckBox("Urgente"); self.chk_electrico = QCheckBox("Eléctrico")
        self.chk_mecanico = QCheckBox("Mecánico"); self.chk_prev = QCheckBox("Preventivo")
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
        h_tags.addWidget(self.chk_urgente); h_tags.addWidget(self.chk_electrico)
        h_tags.addWidget(self.chk_mecanico); h_tags.addWidget(self.chk_prev)
        l.addLayout(h_tags)
        texto_manual = ", ".join([x for x in tags.split(',') if x.strip().lower() in lista_actual])
        self.tag = QLineEdit(); self.tag.setText(texto_manual); self.tag.setPlaceholderText("Otros tags...")
        l.addWidget(self.tag)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def separar_datos(self, texto):
        ref = ""; m_ref = re.search(r"\[REF:\s*(\d+)\]", texto)
        if m_ref: ref = m_ref.group(0); texto = re.sub(r"\[REF:.*?\]", "", texto)
        foto = None; m_foto = re.search(r"\[FOTO:\s*(.*?)\]", texto)
        if m_foto: foto = m_foto.group(1).strip().split("]")[0]; texto = re.sub(r"\[FOTO:.*?\]", "", texto)
        return texto.strip(), foto, ref
    def actualizar_vista_foto(self):
        if self.foto_filename:
            ruta = os.path.join(self.carpeta_fotos, self.foto_filename)
            if os.path.exists(ruta):
                p = QPixmap(ruta)
                self.lbl_foto.setPixmap(p.scaled(self.lbl_foto.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_foto.setStyleSheet("border: 2px solid #3daee9;")
            else: self.lbl_foto.setText(f"Error: Falta {self.foto_filename}")
        else: self.lbl_foto.setText("Arrastra una foto aquí\no haz clic para ampliar/buscar"); self.lbl_foto.setStyleSheet("border: 2px dashed #666; color: #888;")
    def abrir_o_buscar(self, event):
        if self.foto_filename:
            ruta = os.path.join(self.carpeta_fotos, self.foto_filename)
            if os.path.exists(ruta): VisorFoto(ruta, self).exec()
        else: self.seleccionar_foto_boton()
    def seleccionar_foto_boton(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles(): self.procesar_nueva_foto(dlg.selectedFiles()[0])
    def procesar_nueva_foto(self, ruta_origen):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = os.path.splitext(ruta_origen)[1]
            nuevo = f"pc_drag_{ts}{ext}"
            destino = os.path.join(self.carpeta_fotos, nuevo)
            shutil.copy2(ruta_origen, destino)
            self.foto_filename = nuevo
            self.actualizar_vista_foto()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
    def get_data(self):
        d = self.te.toPlainText().strip()
        if self.ref_oculta: d += f" {self.ref_oculta}"
        if self.foto_filename: d += f"\n[FOTO: {self.foto_filename}]"
        final_tags = []
        if self.chk_urgente.isChecked(): final_tags.append("Urgente")
        if self.chk_electrico.isChecked(): final_tags.append("Eléctrico")
        if self.chk_mecanico.isChecked(): final_tags.append("Mecánico")
        if self.chk_prev.isChecked(): final_tags.append("Preventivo")
        manual = self.tag.text().strip()
        if manual: final_tags.append(manual)
        return (self.de.date().toString("yyyy-MM-dd"), d, ", ".join(final_tags))

class DialogoEditarPendiente(QDialog):
    def __init__(self, parent=None, titulo="", detalles="", ruta_foto=""):
        super().__init__(parent)
        self.setWindowTitle("Editar Tarea Pendiente")
        self.resize(550, 650)
        self.ruta_foto_seleccionada = ruta_foto
        l = QVBoxLayout()
        l.addWidget(QLabel("Título:")); self.t = QLineEdit(titulo); l.addWidget(self.t)
        l.addWidget(QLabel("Detalles:")); self.d = QTextEdit(); self.d.setText(detalles); self.d.setMaximumHeight(100); l.addWidget(self.d)
        l.addWidget(QLabel("📸 Foto Adjunta:"))
        self.lbl_preview = QLabel("Sin foto"); self.lbl_preview.setFixedSize(400, 300)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_preview.setStyleSheet("border: 2px dashed #555; background-color: #222; color: #aaa;")
        h_center = QHBoxLayout(); h_center.addStretch(); h_center.addWidget(self.lbl_preview); h_center.addStretch(); l.addLayout(h_center)
        h_btns = QHBoxLayout(); self.lbl_nombre = QLabel(""); self.lbl_nombre.setStyleSheet("color: #777; font-size: 10px;"); h_btns.addWidget(self.lbl_nombre); h_btns.addStretch()
        btn_ver = QPushButton("🔍 Ver Grande"); btn_ver.clicked.connect(self.ver_grande); h_btns.addWidget(btn_ver)
        btn_cambiar = QPushButton("📂 Cambiar Foto"); btn_cambiar.clicked.connect(self.seleccionar_foto); h_btns.addWidget(btn_cambiar); l.addLayout(h_btns)
        self.actualizar_vista_foto()
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addWidget(b); self.setLayout(l)
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
    def ver_grande(self):
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada): VisorFoto(self.ruta_foto_seleccionada, self).exec()
    def get_data(self): return self.t.text().strip(), self.d.toPlainText().strip(), self.ruta_foto_seleccionada

class CompleteDialog(QDialog):
    def __init__(self, parent=None, titulo="", detalles=""):
        super().__init__(parent)
        self.carpeta_fotos = parent.carpeta_fotos if parent else ""
        self.foto_filename = None
        self.setWindowTitle(f"Completar: {titulo}"); self.resize(500, 550); l = QVBoxLayout()
        lbl_info = QLabel(f"<b>Trabajo:</b> {titulo}<br><i>{detalles}</i>"); lbl_info.setWordWrap(True); lbl_info.setStyleSheet("background-color: #333; padding: 10px; border-radius: 5px; color: #eee;"); l.addWidget(lbl_info)
        l.addWidget(QLabel("Fecha Finalización:")); self.de = QDateEdit(); self.de.setDate(QDate.currentDate()); self.de.setCalendarPopup(True); self.de.setDisplayFormat("yyyy-MM-dd"); l.addWidget(self.de)
        self.lbl_foto = LabelArrastrable(); self.lbl_foto.setFixedHeight(180); self.lbl_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_foto.mousePressEvent = self.click_foto; self.lbl_foto.archivo_soltado.connect(self.procesar_foto); l.addWidget(self.lbl_foto)
        btn = QPushButton("📸 Buscar Foto Manualmente"); btn.clicked.connect(self.buscar_foto); l.addWidget(btn)
        l.addWidget(QLabel("Etiquetas Rápidas:")); h_tags = QHBoxLayout()
        self.chk_urgente = QCheckBox("Urgente"); self.chk_electrico = QCheckBox("Eléctrico"); self.chk_mecanico = QCheckBox("Mecánico"); self.chk_prev = QCheckBox("Preventivo")
        for c in [self.chk_urgente, self.chk_electrico, self.chk_mecanico, self.chk_prev]: c.setStyleSheet("font-weight: bold; color: #bbb;"); h_tags.addWidget(c)
        l.addLayout(h_tags)
        l.addWidget(QLabel("Otros Tags (Opcional):")); self.tag = QLineEdit(); self.tag.setPlaceholderText("Ej: limpieza, rodamiento..."); l.addWidget(self.tag)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addWidget(b); self.setLayout(l)
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
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
    def get_data(self):
        lista_tags = []
        if self.chk_urgente.isChecked(): lista_tags.append("Urgente")
        if self.chk_electrico.isChecked(): lista_tags.append("Eléctrico")
        if self.chk_mecanico.isChecked(): lista_tags.append("Mecánico")
        if self.chk_prev.isChecked(): lista_tags.append("Preventivo")
        manual = self.tag.text().strip(); (lista_tags.append(manual) if manual else None)
        return (self.de.date().toString("yyyy-MM-dd"), ", ".join(lista_tags), self.foto_filename)

class AvisoEditDialog(QDialog):
    def __init__(self, parent=None, titulo="", inicio="", freq="", duracion=1):
        super().__init__(parent)
        self.setWindowTitle("✏️ Editar Aviso Recurrente"); self.resize(500, 450)
        l = QVBoxLayout(); l.setSpacing(15); l.setContentsMargins(20, 20, 20, 20); lbl_style = "font-weight: bold; font-size: 14px; color: #ccc;"
        l.addWidget(QLabel("Título del Aviso:", styleSheet=lbl_style)); self.titulo = QLineEdit(titulo); self.titulo.setMinimumHeight(35); l.addWidget(self.titulo)
        l.addWidget(QLabel("Fecha de Inicio:", styleSheet=lbl_style)); self.inicio = QDateEdit(); self.inicio.setCalendarPopup(True); self.inicio.setDisplayFormat("yyyy-MM-dd"); self.inicio.setMinimumHeight(35)
        if inicio: self.inicio.setDate(QDate.fromString(inicio, "yyyy-MM-dd"))
        else: self.inicio.setDate(QDate.currentDate())
        l.addWidget(self.inicio)
        l.addWidget(QLabel("Frecuencia de Repetición:", styleSheet=lbl_style)); self.freq = QComboBox(); self.freq.addItems(["Anual", "Semestral", "Trimestral", "Mensual", "Semanal", "Diario"])
        self.freq.setCurrentText(freq if freq else "Anual"); self.freq.setMinimumHeight(35); l.addWidget(self.freq)
        l.addWidget(QLabel("Días que permanece activo (margen):", styleSheet=lbl_style)); self.dur = QSpinBox(); self.dur.setRange(1, 365); self.dur.setValue(int(duracion)); self.dur.setMinimumHeight(35); l.addWidget(self.dur)
        l.addStretch()
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        for btn in b.buttons(): btn.setMinimumHeight(40); btn.setStyleSheet("font-size: 14px;")
        b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addWidget(b); self.setLayout(l)
    def get_data(self): return (self.titulo.text(), self.inicio.date().toString("yyyy-MM-dd"), self.freq.currentText(), self.dur.value())

class DialogoExportarPDF(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar a PDF"); self.resize(400, 300)
        l = QVBoxLayout()
        g = QGroupBox("Opciones de Exportación"); gl = QVBoxLayout()
        self.rb_todo = QRadioButton("Exportar TODO el historial"); self.rb_todo.setChecked(True); self.rb_todo.toggled.connect(self.toggle_fechas); gl.addWidget(self.rb_todo)
        self.rb_rango = QRadioButton("Exportar rango de fechas"); gl.addWidget(self.rb_rango)
        h = QHBoxLayout()
        self.d_inicio = QDateEdit(QDate.currentDate().addMonths(-1)); self.d_inicio.setCalendarPopup(True); self.d_inicio.setDisplayFormat("yyyy-MM-dd"); self.d_inicio.setEnabled(False)
        self.d_fin = QDateEdit(QDate.currentDate()); self.d_fin.setCalendarPopup(True); self.d_fin.setDisplayFormat("yyyy-MM-dd"); self.d_fin.setEnabled(False)
        h.addWidget(QLabel("De:")); h.addWidget(self.d_inicio); h.addWidget(QLabel("A:")); h.addWidget(self.d_fin); gl.addLayout(h); gl.addSpacing(10)
        self.chk_fotos = QCheckBox("📸 Incluir imágenes en el PDF"); self.chk_fotos.setChecked(False); gl.addWidget(self.chk_fotos); g.setLayout(gl); l.addWidget(g)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addWidget(b); self.setLayout(l)
    def toggle_fechas(self): estado = self.rb_rango.isChecked(); self.d_inicio.setEnabled(estado); self.d_fin.setEnabled(estado)
    def get_data(self):
        con_fotos = self.chk_fotos.isChecked()
        if self.rb_todo.isChecked(): return None, None, con_fotos
        else: return self.d_inicio.date().toString("yyyy-MM-dd"), self.d_fin.date().toString("yyyy-MM-dd"), con_fotos

# ==========================================
# 4. APLICACIÓN PRINCIPAL
# ==========================================

class MaintenanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = GestorBaseDatos()
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
        self.server_thread.start()
        self.setWindowTitle("Control Mantenimiento")
        self.resize(1100, 750)
        g = self.settings.value("geometry")
        if g: self.restoreGeometry(g)

        # --- FIJAR EL ICONO DE LA APLICACIÓN (WAYLAND/LINUX FIX) ---
        icon_path = resource_path("icono.png")
        if os.path.exists(icon_path):
             icon = QIcon(icon_path)
             self.setWindowIcon(icon)
             QApplication.instance().setWindowIcon(icon)

        self.crear_menu()
        self.aplicar_estilo_visual()
        cw = QWidget(); self.setCentralWidget(cw); ml = QVBoxLayout(); ml.setContentsMargins(10, 10, 10, 10); cw.setLayout(ml)
        self.tabs = QTabWidget(); ml.addWidget(self.tabs)
        self.tab_dashboard = QWidget(); self.init_dashboard_tab(); self.tabs.addTab(self.tab_dashboard, "📊 Dashboard")
        self.tab_calendar = QWidget(); self.init_calendar_tab(); self.tabs.addTab(self.tab_calendar, "📅 Calendario")
        self.tab_avisos = QWidget(); self.init_avisos_tab(); self.tabs.addTab(self.tab_avisos, "⚠️ Avisos")
        self.tab_entry = QWidget(); self.init_entry_tab(); self.tabs.addTab(self.tab_entry, "📝 Registrar")
        self.tab_history = QWidget(); self.init_history_tab(); self.tabs.addTab(self.tab_history, "🗂 Historial")
        self.tab_search = QWidget(); self.init_search_tab(); self.tabs.addTab(self.tab_search, "🔍 Buscador")
        self.tab_todo = QWidget(); self.init_todo_tab(); self.tabs.addTab(self.tab_todo, "🔨 Pendientes")
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.refresh_all(); self.pintar_calendario(); self.update_calendar_list(); self.refresh_avisos(); self.refresh_todos(); self.setup_autocompletado()

    def closeEvent(self, e):
        self.settings.setValue("geometry", self.saveGeometry())

        # 1. Limpieza de fotos antes del backup
        print("Iniciando limpieza de fotos...")
        self.limpiar_fotos_huerfanas(silencioso=True)

        # 2. Backup automático
        print("Iniciando Auto-Backup...")
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_zip = f"auto_backup_full_{timestamp}.zip"
            # Usar la nueva ruta de backups auto
            ruta_zip = os.path.join(self.carpeta_backups_auto, nombre_zip)

            with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(self.db.db_name): zipf.write(self.db.db_name, arcname=os.path.basename(self.db.db_name))
                if os.path.exists(self.carpeta_fotos):
                    for root, dirs, files in os.walk(self.carpeta_fotos):
                        for file in files:
                            ruta_archivo = os.path.join(root, file)
                            ruta_en_zip = os.path.relpath(ruta_archivo, os.path.dirname(self.carpeta_fotos))
                            zipf.write(ruta_archivo, arcname=ruta_en_zip)

            backups = []
            for f in os.listdir(self.carpeta_backups_auto):
                ruta_completa = os.path.join(self.carpeta_backups_auto, f)
                if os.path.isfile(ruta_completa) and f.startswith("auto_backup_full_") and f.endswith(".zip"): backups.append(ruta_completa)
            backups.sort(key=os.path.getmtime)
            while len(backups) > 3: archivo_a_borrar = backups.pop(0); os.remove(archivo_a_borrar)
        except Exception as ex: print(f"Error en auto-backup: {ex}")
        super().closeEvent(e)

    def on_registro_recibido(self, titulo, detalles, tags, filename, ruta_foto):
        if self.qr_dialog: self.qr_dialog.accept(); self.qr_dialog = None
        fecha = QDate.currentDate().toString("yyyy-MM-dd")
        desc_final = titulo
        if detalles: desc_final += f"\n{detalles}"
        if filename: desc_final += f"\n[FOTO: {filename}]"
        self.db.agregar_tarea(fecha, desc_final, tags)
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

        for aid, tit, finicio, freq, dur, ult in self.db.obtener_avisos():
            if not finicio: continue
            fi = QDate.fromString(finicio, "yyyy-MM-dd")
            if not freq: freq = "Anual"
            ocurrencia = fi
            while ocurrencia.addDays(dur) < sd:
                if freq == "Diario": ocurrencia = ocurrencia.addDays(1)
                elif freq == "Semanal": ocurrencia = ocurrencia.addDays(7)
                elif freq == "Mensual": ocurrencia = ocurrencia.addMonths(1)
                elif freq == "Trimestral": ocurrencia = ocurrencia.addMonths(3)
                elif freq == "Semestral": ocurrencia = ocurrencia.addMonths(6)
                elif freq == "Anual": ocurrencia = ocurrencia.addYears(1)
                else: break
            ff = ocurrencia.addDays(dur)
            if ocurrencia <= sd <= ff:
                es_completado = (ult == ocurrencia.toString("yyyy-MM-dd"))
                color_bg = "#27ae60" if es_completado else "#e74c3c"
                estado_txt = "[OK]" if es_completado else "[PENDIENTE]"
                it = QListWidgetItem(f"⚠️ AVISO: {tit} {estado_txt}")
                it.setBackground(QColor(color_bg)); it.setForeground(Qt.GlobalColor.white)
                self.task_list.addItem(it)

        ts = self.db.obtener_tareas_por_fecha(sds)
        if not ts and self.task_list.count() == 0: self.task_list.addItem("--- Día no laborable ---" if ets else "--- Nada registrado ---")
        for t in ts:
            # --- LIMPIEZA VISUAL COMPLETA ---
            texto_limpio = re.sub(r"\[FOTO:.*?\]", "", t[1])
            texto_limpio = re.sub(r"\[REF:.*?\]", "", texto_limpio).strip()
            # --------------------------------

            it = QListWidgetItem(f"{texto_limpio} | {t[2]}")
            if "[FOTO:" in t[1]: it.setIcon(QIcon.fromTheme("camera-photo")); it.setToolTip("Tiene foto adjunta")
            it.setData(Qt.ItemDataRole.UserRole, t[0])
            self.task_list.addItem(it)

    def fill_t(self, table, data):
        table.setRowCount(len(data))
        pm_foto = QPixmap(16, 16); pm_foto.fill(QColor("#3daee9")); icon_foto = QIcon(pm_foto)
        pm_vacio = QPixmap(16, 16); pm_vacio.fill(Qt.GlobalColor.transparent); icon_vacio = QIcon(pm_vacio)

        for r, (id_t, fecha, desc, tags) in enumerate(data):
            # LIMPIEZA VISUAL (FOTO Y REF)
            desc_limpia = re.sub(r"\[FOTO:.*?\]", "", desc)
            desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

            desc_visual = desc_limpia.replace("\n", "  ➜  ")

            tags_lower = tags.lower(); color_bg = None
            if any(x in tags_lower for x in ["urgente", "avería", "rotura", "fallo", "paro"]): color_bg = QColor("#5a2d2d")
            elif any(x in tags_lower for x in ["preventivo", "revisión", "ok", "limpieza"]): color_bg = QColor("#2d4a2d")
            elif "eléctrico" in tags_lower or "cuadro" in tags_lower: color_bg = QColor("#2d3b5a")
            elif "mecánico" in tags_lower: color_bg = QColor("#5a4a2d")

            item_f = QTableWidgetItem(fecha); item_f.setData(Qt.ItemDataRole.UserRole, id_t)
            item_d = QTableWidgetItem(desc_visual); item_d.setToolTip(desc_limpia)

            if "[FOTO:" in desc:
                item_d.setIcon(icon_foto)
                item_d.setToolTip(f"📸 CON FOTO ADJUNTA\n\n{desc_limpia}")
            else:
                item_d.setIcon(icon_vacio)

            item_t = QTableWidgetItem(tags)

            if color_bg:
                item_f.setBackground(color_bg); item_d.setBackground(color_bg); item_t.setBackground(color_bg)

            table.setItem(r, 0, item_f); table.setItem(r, 1, item_d); table.setItem(r, 2, item_t)

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
        self.statusBar().showMessage(f"🔍 Mostrando {filas_visibles} resultados", 3000)

    def refresh_history(self): self.fill_t(self.h_table, self.db.obtener_todas_cronologico())
    def crear_menu(self):
        mb = self.menuBar(); fm = mb.addMenu("&Archivo")
        fm.addAction(QAction("💾 Backup", self, triggered=self.realizar_backup))
        fm.addAction(QAction("♻️ Restaurar", self, triggered=self.restaurar_backup))
        fm.addSeparator()

        # --- SUBMENÚ PDF ---
        menu_pdf = fm.addMenu("📄 Opciones PDF")

        act_exportar = QAction("📄 Generar PDF Ahora", self)
        act_exportar.triggered.connect(self.exportar_pdf)
        menu_pdf.addAction(act_exportar)

        menu_pdf.addSeparator()

        act_cambiar_logo = QAction("🖼️ Añadir / Cambiar Logo", self)
        act_cambiar_logo.triggered.connect(self.cambiar_logo)
        menu_pdf.addAction(act_cambiar_logo)

        act_quitar_logo = QAction("❌ Quitar Logo", self)
        act_quitar_logo.triggered.connect(self.quitar_logo)
        menu_pdf.addAction(act_quitar_logo)
        # --------------------

        fm.addAction(QAction("📄 CSV", self, triggered=self.exportar_csv))
        fm.addAction(QAction("📊 Excel", self, triggered=self.exportar_excel))
        fm.addSeparator(); fm.addAction(QAction("Salir", self, triggered=self.close))
        tm = mb.addMenu("&Herramientas")
        act_sync = QAction("📲 Sincronizar App (QR)", self); act_sync.triggered.connect(self.mostrar_dialogo_qr); tm.addAction(act_sync)
        tm.addAction(QAction("Gestionar Días / Festivos", self, triggered=self.gest_dias));

        # --- NUEVA OPCIÓN DE PROVINCIA ---
        act_prov = QAction("🌍 Seleccionar Provincia", self)
        act_prov.triggered.connect(self.cambiar_provincia)
        tm.addAction(act_prov)
        # ---------------------------------

        fm.addSeparator()
        tm.addAction(QAction("🧹 Limpiar Fotos Basura", self, triggered=self.limpiar_fotos_huerfanas))

    def cambiar_provincia(self):
        # Abre el diálogo para seleccionar la provincia
        dlg = DialogoSeleccionRegion(self.db, self)
        if dlg.exec():
            nombre, iso_prov, iso_parent = dlg.get_selection()

            # Guardamos ambas configuraciones
            self.db.set_config("region_iso", iso_prov)
            self.db.set_config("parent_iso", iso_parent)

            # Limpiar la caché antigua
            self.gestor_festivos.limpiar_cache()

            QMessageBox.information(self, "Provincia Cambiada", f"Nueva zona: {nombre}\n(Se descargarán festivos nacionales, de {iso_parent} y de {iso_prov})")

            # Repintar el calendario
            self.pintar_calendario()
            self.update_calendar_list()

    def aplicar_estilo_visual(self):
        QApplication.setStyle(QStyleFactory.create("Fusion"))
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
        l = QVBoxLayout(); l.setSpacing(10)
        h_top = QHBoxLayout(); v_date = QVBoxLayout()
        self.ide = QDateEdit(); self.ide.setCalendarPopup(True); self.ide.setDate(QDate.currentDate()); self.ide.setDisplayFormat("yyyy-MM-dd")
        v_date.addWidget(QLabel("Fecha:")); v_date.addWidget(self.ide); v_date.addStretch(); h_top.addLayout(v_date, 40)
        v_foto = QVBoxLayout(); v_foto.setContentsMargins(0,0,0,0); v_foto.setSpacing(2)
        self.lbl_entry_foto = LabelArrastrable(); self.lbl_entry_foto.setFixedHeight(100); self.lbl_entry_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_entry_foto.archivo_soltado.connect(self.procesar_foto_entry); self.lbl_entry_foto.mousePressEvent = self.buscar_foto_entry_click
        v_foto.addWidget(self.lbl_entry_foto)
        self.btn_del_foto = QPushButton("❌ Quitar Foto"); self.btn_del_foto.setStyleSheet("background-color: #c0392b; color: white; border-radius: 4px; padding: 2px;"); self.btn_del_foto.setFixedHeight(20); self.btn_del_foto.clicked.connect(self.borrar_foto_entry); self.btn_del_foto.hide()
        v_foto.addWidget(self.btn_del_foto); h_top.addLayout(v_foto, 60); l.addLayout(h_top)
        self.ire = QLineEdit(); self.ire.setPlaceholderText("Resumen corto del trabajo..."); l.addWidget(QLabel("Resumen / Tarea:")); l.addWidget(self.ire)
        h_qr = QHBoxLayout(); h_qr.addWidget(QLabel("Detalles:")); h_qr.addStretch()
        b_qr = QPushButton("📲 Sincronizar App"); b_qr.setStyleSheet("background-color: #d35400; color: white; padding: 4px 8px;"); b_qr.clicked.connect(self.mostrar_dialogo_qr); h_qr.addWidget(b_qr); l.addLayout(h_qr)
        self.idet = QTextEdit(); l.addWidget(self.idet)
        l.addWidget(QLabel("Etiquetas Rápidas:"))
        h_tags = QHBoxLayout()
        self.chk_urgente = QCheckBox("Urgente"); self.chk_electrico = QCheckBox("Eléctrico")
        self.chk_mecanico = QCheckBox("Mecánico"); self.chk_prev = QCheckBox("Preventivo")
        for c in [self.chk_urgente, self.chk_electrico, self.chk_mecanico, self.chk_prev]: c.setStyleSheet("font-weight: bold; color: #bbb;"); h_tags.addWidget(c)
        l.addLayout(h_tags)
        self.itag = QLineEdit(); self.itag.setPlaceholderText("Otras etiquetas (separadas por comas)..."); l.addWidget(self.itag)
        b_save = QPushButton("💾 GUARDAR REGISTRO"); b_save.setMinimumHeight(45); b_save.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #2980b9; color: white;"); b_save.clicked.connect(self.save_entry); l.addWidget(b_save); l.addStretch(); self.tab_entry.setLayout(l)
    def borrar_foto_entry(self):
        self.entry_foto_filename = None; self.lbl_entry_foto.setPixmap(QPixmap()); self.lbl_entry_foto.setText("Arrastra foto aquí\no click para buscar"); self.lbl_entry_foto.setStyleSheet("border: 2px dashed #666; color: #888; background: #252525;"); self.btn_del_foto.hide()
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
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
    def save_entry(self):
        d, r = self.ide.date().toString("yyyy-MM-dd"), self.ire.text().strip()
        de = self.idet.toPlainText().strip()
        if not r: QMessageBox.warning(self, "Atención", "Falta el resumen"); return
        full_desc = r
        if de: full_desc += f"\n{de}"
        if self.entry_foto_filename: full_desc += f"\n[FOTO: {self.entry_foto_filename}]"
        lista_tags = []
        if self.chk_urgente.isChecked(): lista_tags.append("Urgente")
        if self.chk_electrico.isChecked(): lista_tags.append("Eléctrico")
        if self.chk_mecanico.isChecked(): lista_tags.append("Mecánico")
        if self.chk_prev.isChecked(): lista_tags.append("Preventivo")
        manuales = self.itag.text().strip()
        if manuales: lista_tags.append(manuales)
        if self.db.agregar_tarea(d, full_desc, ", ".join(lista_tags)):
            self.statusBar().showMessage("✅ Registro guardado correctamente", 4000)
            self.ire.clear(); self.idet.clear(); self.itag.clear()
            self.chk_urgente.setChecked(False); self.chk_electrico.setChecked(False)
            self.chk_mecanico.setChecked(False); self.chk_prev.setChecked(False)
            self.borrar_foto_entry(); self.refresh_all(); self.setup_autocompletado()
    def setup_autocompletado(self):
        d = self.db.obtener_todas_las_descripciones()
        c = QCompleter(d, self); c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); c.setFilterMode(Qt.MatchFlag.MatchContains)
        self.ire.setCompleter(c); self.in_todo_t.setCompleter(c)
    def init_calendar_tab(self):
        l = QHBoxLayout(); lp = QVBoxLayout(); th = QHBoxLayout()
        th.addWidget(QPushButton("Ir a Hoy", clicked=self.go_today)); th.addWidget(QPushButton("Gestión Días", clicked=lambda: self.gest_dias()))
        lp.addLayout(th); self.calendar = QCalendarWidget(); self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self.update_calendar_list); lp.addWidget(self.calendar); l.addLayout(lp, 60)
        rp = QVBoxLayout(); self.lbl_info = QLabel("Info"); rp.addWidget(self.lbl_info)
        self.task_list = QListWidget(); self.configurar_deseleccion(self.task_list)
        self.task_list.itemDoubleClicked.connect(self.edit_cal); rp.addWidget(self.task_list); l.addLayout(rp, 40); self.tab_calendar.setLayout(l)
    def init_avisos_tab(self):
        l = QVBoxLayout()
        self.table_avisos = QTableWidget(0, 5)
        self.configurar_deseleccion(self.table_avisos); self.table_avisos.setHorizontalHeaderLabels(["Estado", "Título", "Frecuencia", "Próxima", "Sit"])
        self.table_avisos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_avisos.cellDoubleClicked.connect(lambda r, c: self.edit_aviso())
        l.addWidget(QLabel("⚠️ GESTIÓN DE AVISOS RECURRENTES")); l.addWidget(self.table_avisos)
        g = QGroupBox("Crear Nuevo Aviso"); f = QGridLayout()
        self.in_av_t = QLineEdit(); self.in_av_t.setPlaceholderText("Título del aviso...")
        f.addWidget(QLabel("Título:"), 0, 0); f.addWidget(self.in_av_t, 0, 1)
        self.in_av_i = QDateEdit(); self.in_av_i.setCalendarPopup(True); self.in_av_i.setDate(QDate.currentDate()); self.in_av_i.setDisplayFormat("yyyy-MM-dd")
        f.addWidget(QLabel("Inicio:"), 0, 2); f.addWidget(self.in_av_i, 0, 3)
        self.in_av_freq = QComboBox(); self.in_av_freq.addItems(["Anual", "Semestral", "Trimestral", "Mensual", "Semanal", "Diario"])
        f.addWidget(QLabel("Repetir:"), 1, 0); f.addWidget(self.in_av_freq, 1, 1)
        self.in_av_dur = QSpinBox(); self.in_av_dur.setRange(1, 60); self.in_av_dur.setValue(5); self.in_av_dur.setSuffix(" días")
        f.addWidget(QLabel("Duración:"), 1, 2); f.addWidget(self.in_av_dur, 1, 3)
        b = QPushButton("Añadir Aviso"); b.clicked.connect(self.add_aviso); f.addWidget(b, 2, 0, 1, 4); g.setLayout(f); l.addWidget(g)
        bl = QHBoxLayout(); bl.addWidget(QPushButton("✏️ Editar Seleccionado", clicked=self.edit_aviso)); bl.addWidget(QPushButton("🗑️ Borrar Seleccionado", clicked=self.del_aviso)); l.addLayout(bl); self.tab_avisos.setLayout(l)
    def add_aviso(self):
        t = self.in_av_t.text().strip(); i = self.in_av_i.date().toString("yyyy-MM-dd"); f = self.in_av_freq.currentText(); d = self.in_av_dur.value()
        if t and self.db.agregar_aviso(t, i, f, d): self.in_av_t.clear(); self.refresh_avisos(); self.update_calendar_list()
    def edit_aviso(self):
        r = self.table_avisos.currentRow()
        if r < 0: return
        id_aviso = self.table_avisos.item(r, 1).data(Qt.ItemDataRole.UserRole)
        avisos = self.db.obtener_avisos(); datos = next((a for a in avisos if a[0] == id_aviso), None)
        if datos:
            dlg = AvisoEditDialog(self, datos[1], datos[2], datos[3], datos[4])
            if dlg.exec():
                new_t, new_i, new_f, new_d = dlg.get_data()
                self.db.actualizar_aviso(id_aviso, new_t, new_i, new_f, new_d); self.refresh_avisos(); self.update_calendar_list()
    def refresh_avisos(self):
        self.table_avisos.setRowCount(0); avisos = self.db.obtener_avisos(); hoy = QDate.currentDate()
        self.table_avisos.setRowCount(len(avisos))
        for r, (aid, tit, finicio, freq, dur, ult) in enumerate(avisos):
            if not finicio: finicio = f"{hoy.year()}-01-01"
            if not freq: freq = "Anual"
            fi = QDate.fromString(finicio, "yyyy-MM-dd"); ocurrencia = fi # Changed variable name from ocurrencia_actual to ocurrencia
            while ocurrencia.addDays(dur) < hoy:
                if freq == "Diario": ocurrencia = ocurrencia.addDays(1)
                elif freq == "Semanal": ocurrencia = ocurrencia.addDays(7)
                elif freq == "Mensual": ocurrencia = ocurrencia.addMonths(1)
                elif freq == "Trimestral": ocurrencia = ocurrencia.addMonths(3)
                elif freq == "Semestral": ocurrencia = ocurrencia.addMonths(6)
                elif freq == "Anual": ocurrencia = ocurrencia.addYears(1)
                else: break
            fin_ocurrencia = ocurrencia.addDays(dur)
            es_activo = (ocurrencia <= hoy <= fin_ocurrencia); completado = (ult == ocurrencia.toString("yyyy-MM-dd"))
            cw = QWidget(); cl = QHBoxLayout(cw); cl.setContentsMargins(0,0,0,0); cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox(); chk.setChecked(completado); fecha_ocu_str = ocurrencia.toString("yyyy-MM-dd") # Updated usage
            chk.toggled.connect(lambda k, x=aid, d=fecha_ocu_str, t=tit: self.tog_aviso(x, d, k, t))
            chk.setEnabled(es_activo or completado); cl.addWidget(chk); self.table_avisos.setCellWidget(r, 0, cw)
            color = QColor("#555"); estado_txt = "Futuro"
            if es_activo:
                if completado: color = QColor("#27ae60"); estado_txt = "OK"
                else: color = QColor("#e74c3c"); estado_txt = "PENDIENTE"
            item_t = QTableWidgetItem(tit); item_t.setData(Qt.ItemDataRole.UserRole, aid); item_t.setBackground(color)
            self.table_avisos.setItem(r, 1, item_t); self.table_avisos.setItem(r, 2, QTableWidgetItem(freq))
            rango = f"{ocurrencia.toString('dd/MM')} - {fin_ocurrencia.toString('dd/MM')}" # Updated usage
            self.table_avisos.setItem(r, 3, QTableWidgetItem(rango)); self.table_avisos.setItem(r, 4, QTableWidgetItem(estado_txt))
    def tog_aviso(self, id_aviso, fecha_ocurrencia, estado, titulo):
        self.db.marcar_aviso_completado(id_aviso, fecha_ocurrencia, estado)
        if estado:
            desc = f"Mantenimiento Preventivo: {titulo}"; tags = "Preventivo, Aviso Recurrente"; hoy = QDate.currentDate().toString("yyyy-MM-dd")
            self.db.agregar_tarea(hoy, desc, tags); self.statusBar().showMessage(f"✅ Guardado en historial: {titulo}", 3000)
        self.refresh_avisos(); self.update_calendar_list(); self.refresh_history()
    def del_aviso(self):
        r = self.table_avisos.currentRow()
        if r >= 0:
            # --- DIÁLOGO ESPAÑOL FORZADO ---
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setWindowTitle("Borrar Aviso")
            msg.setText("¿Estás seguro de borrar este aviso recurrente definitivamente?")

            btn_si = msg.addButton("SÍ", QMessageBox.ButtonRole.YesRole)
            btn_no = msg.addButton("NO", QMessageBox.ButtonRole.NoRole)

            msg.exec()

            if msg.clickedButton() == btn_si:
                id_aviso = self.table_avisos.item(r, 1).data(Qt.ItemDataRole.UserRole)
                self.db.borrar_aviso(id_aviso)
                self.refresh_avisos()
                self.update_calendar_list()

    def init_history_tab(self):
        l = QVBoxLayout(); self.h_table = QTableWidget(); self.configurar_deseleccion(self.h_table); self.setup_table(self.h_table)
        self.h_table.cellDoubleClicked.connect(lambda r, c: self.edit_rec(self.h_table)); l.addWidget(self.h_table)
        bl = QHBoxLayout(); bl.addWidget(QPushButton("Editar", clicked=lambda: self.edit_rec(self.h_table))); bl.addWidget(QPushButton("Borrar Seleccionado", clicked=lambda: self.del_rec(self.h_table))); l.addLayout(bl); self.tab_history.setLayout(l)
    def init_search_tab(self):
        l = QVBoxLayout(); sl = QHBoxLayout()
        self.s_in = QLineEdit(); self.s_in.setPlaceholderText("🔍 Buscar texto (Motor, Fuga, KM1)..."); self.s_in.textChanged.connect(self.search); sl.addWidget(self.s_in)
        self.s_chk_date = QCheckBox("📅 Fecha:"); self.s_chk_date.toggled.connect(lambda: self.s_date.setEnabled(self.s_chk_date.isChecked())); self.s_chk_date.toggled.connect(self.search); sl.addWidget(self.s_chk_date)
        self.s_date = QDateEdit(); self.s_date.setCalendarPopup(True); self.s_date.setDate(QDate.currentDate()); self.s_date.setDisplayFormat("yyyy-MM-dd"); self.s_date.setEnabled(False); self.s_date.dateChanged.connect(self.search); sl.addWidget(self.s_date); l.addLayout(sl)
        fl = QHBoxLayout(); fl.setSpacing(20)
        self.chk_s_urg = QCheckBox("🚨 Urgente"); self.chk_s_elec = QCheckBox("⚡ Eléctrico"); self.chk_s_mec = QCheckBox("⚙️ Mecánico"); self.chk_s_prev = QCheckBox("🛡️ Preventivo")
        for chk in [self.chk_s_urg, self.chk_s_elec, self.chk_s_mec, self.chk_s_prev]: chk.setStyleSheet("font-weight: bold; color: #ccc;"); chk.toggled.connect(self.search); fl.addWidget(chk)
        fl.addStretch(); l.addLayout(fl)
        self.s_table = QTableWidget(); self.setup_table(self.s_table); self.configurar_deseleccion(self.s_table); self.s_table.cellDoubleClicked.connect(lambda r, c: self.edit_rec(self.s_table)); l.addWidget(self.s_table)
        bl = QHBoxLayout(); bl.addWidget(QPushButton("✏️ Editar", clicked=lambda: self.edit_rec(self.s_table))); bl.addWidget(QPushButton("🗑️ Borrar Seleccionado", clicked=lambda: self.del_rec(self.s_table))); l.addLayout(bl); self.tab_search.setLayout(l)
    def init_todo_tab(self):
        l = QHBoxLayout(); ll = QVBoxLayout(); ll.addWidget(QLabel("LISTA DE PENDIENTES"))
        self.todo_list = QListWidget(); self.configurar_deseleccion(self.todo_list); self.todo_list.setAlternatingRowColors(True)
        self.todo_list.itemDoubleClicked.connect(self.edit_todo); ll.addWidget(self.todo_list); l.addLayout(ll, 60)
        rl = QVBoxLayout(); g = QGroupBox("Nuevo Trabajo"); f = QVBoxLayout()
        self.in_todo_t = QLineEdit(); self.in_todo_t.setPlaceholderText("Título"); f.addWidget(self.in_todo_t)
        self.in_todo_d = QTextEdit(); self.in_todo_d.setPlaceholderText("Detalles"); self.in_todo_d.setMaximumHeight(100); self.in_todo_d.setStyleSheet("QTextEdit { color: #e0e0e0; background-color: #1e1e1e; border: 1px solid #555; }"); f.addWidget(self.in_todo_d)
        f.addWidget(QPushButton("Añadir", clicked=self.add_todo)); g.setLayout(f); rl.addWidget(g)
        ga = QGroupBox("Acciones"); fa = QVBoxLayout()
        b_ok = QPushButton("✅ Completar", clicked=self.complete_todo); b_ok.setStyleSheet("background-color:#27ae60; color: white;"); fa.addWidget(b_ok)
        b_edit = QPushButton("✏️ Editar", clicked=self.edit_todo); b_edit.setStyleSheet("background-color:#2980b9; color: white;"); fa.addWidget(b_edit)
        b_del = QPushButton("❌ Eliminar", clicked=self.del_todo); b_del.setStyleSheet("background-color:#c0392b; color: white;"); fa.addWidget(b_del); ga.setLayout(fa); rl.addWidget(ga); l.addLayout(rl, 40); self.tab_todo.setLayout(l)

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
        for s, t in self.db.obtener_dias_especiales().items(): fm = QTextCharFormat(); fm.setBackground(QBrush(QColor(cols.get(t, "#555")))); fm.setForeground(QBrush(QColor(tcols.get(t, "black")))); self.calendar.setDateTextFormat(QDate.fromString(s, "yyyy-MM-dd"), fm)
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
        self.refresh_history(); self.search(); self.refresh_todos(); self.refresh_avisos()
    def setup_table(self, t):
        t.setColumnCount(3); t.setHorizontalHeaderLabels(["Fecha", "Descripción", "Tag"]); t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch); t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); t.setAlternatingRowColors(True)
    def configurar_deseleccion(self, widget):
        clase_base = type(widget)
        def click_inteligente(event):
            clase_base.mousePressEvent(widget, event)
            if not widget.indexAt(event.pos()).isValid(): widget.clearSelection(); widget.setCurrentItem(None)
        widget.mousePressEvent = click_inteligente

    def edit_cal(self, i): self.proc_edit(i.data(Qt.ItemDataRole.UserRole))
    def edit_rec(self, t):
        r = t.currentRow()
        if r >= 0: self.proc_edit(t.item(r, 0).data(Qt.ItemDataRole.UserRole))
    def proc_edit(self, i):
        d = self.db.obtener_tarea_por_id(i)
        if d:
            dlg = EditDialog(self, d[1], d[2], d[3])
            if dlg.exec(): nuevos_datos = dlg.get_data(); self.db.actualizar_tarea(i, *nuevos_datos); self.refresh_all()

    def del_rec(self, t):
        r = t.currentRow()
        if r >= 0:
            i = t.item(r, 0).data(Qt.ItemDataRole.UserRole)
            d = self.db.obtener_tarea_por_id(i)
            if d:
                # --- DIÁLOGO ESPAÑOL ---
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle("Confirmar Eliminación")
                msg.setText("¿Borrar registro permanentemente?\nSi tiene foto adjunta, se eliminará del disco.\n\nSi es un preventivo reciente, volverá a marcarse como PENDIENTE.")

                # Botones manuales
                btn_si = msg.addButton("SÍ", QMessageBox.ButtonRole.YesRole)
                btn_no = msg.addButton("NO", QMessageBox.ButtonRole.NoRole)

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

    def add_todo(self):
        t, d = self.in_todo_t.text().strip(), self.in_todo_d.toPlainText().strip()
        if t and self.db.agregar_pendiente(t, d): self.in_todo_t.clear(); self.in_todo_d.clear(); self.refresh_todos()

    def refresh_todos(self):
        self.todo_list.clear()
        ps = self.db.obtener_pendientes()

        if not ps:
            self.todo_list.addItem("--- Nada ---")

        for i, t, d in ps:
            # 1. LIMPIEZA TOTAL (Quitamos FOTO y REF)
            d_limpio = re.sub(r"\[FOTO:.*?\]", "", d)
            d_limpio = re.sub(r"\[REF:.*?\]", "", d_limpio).strip()

            tiene_foto = "[FOTO:" in d

            # Texto visual limpio
            texto_visual = f"⬜ {t}"
            if d_limpio:
                texto_visual += f"\n   ↳ {d_limpio}"

            if tiene_foto:
                texto_visual += "  (📸 Foto)"

            it = QListWidgetItem(texto_visual)

            # Guardamos los datos originales (sucios) por debajo para la lógica
            it.setData(Qt.ItemDataRole.UserRole, i)
            it.setData(Qt.ItemDataRole.UserRole + 1, t)
            it.setData(Qt.ItemDataRole.UserRole + 2, d)

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
                msg.setWindowTitle("Confirmar Borrado")
                msg.setText("¿Estás seguro de borrar este trabajo pendiente?")

                # Botones personalizados
                btn_si = msg.addButton("SÍ", QMessageBox.ButtonRole.YesRole)
                btn_no = msg.addButton("NO", QMessageBox.ButtonRole.NoRole)

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
            if self.db.agregar_tarea(fecha, desc_final, tags):
                self.db.borrar_pendiente(id_pendiente)
                self.refresh_todos()
                self.refresh_all()
                self.statusBar().showMessage(f"✅ Tarea '{titulo}' completada", 5000)

    # =========================================================================
    # FUNCIONES RESTAURADAS Y NUEVAS
    # =========================================================================

    def realizar_backup(self):
        self.limpiar_fotos_huerfanas(silencioso=True)
        folder_backups = "backups"
        if not os.path.exists(folder_backups): os.makedirs(folder_backups)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_zip = f"backup_completo_{timestamp}.zip"
        # Usamos self.carpeta_backups para seguir la lógica de directorios
        ruta_zip = os.path.join(self.carpeta_backups, nombre_zip)
        try:
            with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.exists(self.db.db_name): zipf.write(self.db.db_name, arcname=os.path.basename(self.db.db_name))
                if os.path.exists(self.carpeta_fotos):
                    for root, dirs, files in os.walk(self.carpeta_fotos):
                        for file in files:
                            ruta_archivo = os.path.join(root, file)
                            ruta_en_zip = os.path.relpath(ruta_archivo, os.path.dirname(self.carpeta_fotos))
                            zipf.write(ruta_archivo, arcname=ruta_en_zip)
            QMessageBox.information(self, "Backup Completo", f"Copia limpia y guardada:\n{nombre_zip}")
        except Exception as e: QMessageBox.critical(self, "Error Backup", str(e))

    def restaurar_backup(self):
        advertencia = "⚠️ ATENCIÓN ⚠️\n\nAl restaurar, se SOBRESCRIBIRÁN todos los datos.\n¿Continuar?"
        if QMessageBox.warning(self, "Restaurar Copia", advertencia, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No: return
        # Use a dialog instance to allow setting DontUseNativeDialog if needed, though getOpenFileName static usually works.
        # But to be safe with styles, we could instantiate QFileDialog.
        # For restore, let's keep it simple as it's a critical operation.
        archivo_zip, _ = QFileDialog.getOpenFileName(self, "Seleccionar Backup Completo", "backups", "Archivos ZIP (*.zip)", options=QFileDialog.Option.DontUseNativeDialog)
        if archivo_zip:
            try:
                # Restaurar en DATA_DIR o carpeta local según donde estemos
                restore_path = os.path.dirname(self.db.db_name)
                with zipfile.ZipFile(archivo_zip, 'r') as zipf: zipf.extractall(path=restore_path)
                QMessageBox.information(self, "Restauración", "✅ Sistema restaurado correctamente."); self.refresh_all()
            except Exception as e: QMessageBox.critical(self, "Error Restauración", f"ZIP corrupto:\n{str(e)}")

    def exportar_csv(self):
        nombre_defecto = f"Mantenimiento_{QDate.currentDate().toString('yyyyMMdd')}.csv"
        archivo = self.guardar_archivo_dialogo("Exportar a CSV", nombre_defecto, "CSV (*.csv)")
        if not archivo: return
        try:
            datos = self.db.obtener_todas_cronologico()
            with open(archivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';'); writer.writerow(["ID", "Fecha", "Descripción", "Tags", "Nombre Foto"])
                for tarea in datos:
                    # Limpiamos FOTO y REF también aquí para que quede perfecto
                    desc_limpia = re.sub(r"\[FOTO:.*?\]", "", tarea[2])
                    desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                    nombre_foto = "NO"
                    m = re.search(r"\[FOTO:\s*(.*?)\]", tarea[2])
                    if m: nombre_foto = m.group(1).split("]")[0].strip()
                    writer.writerow([tarea[0], tarea[1], desc_limpia, tarea[3], nombre_foto])
            QMessageBox.information(self, "Exportado", "CSV guardado correctamente.")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def exportar_excel(self):
        try: import xlsxwriter
        except ImportError: QMessageBox.warning(self, "Falta librería", "Instala: pip install xlsxwriter"); return
        nombre_defecto = f"Mantenimiento_{QDate.currentDate().toString('yyyyMMdd')}.xlsx"
        archivo = self.guardar_archivo_dialogo("Exportar a Excel", nombre_defecto, "Excel (*.xlsx)")
        if not archivo: return
        try:
            workbook = xlsxwriter.Workbook(archivo); worksheet = workbook.add_worksheet("Registro")
            bold = workbook.add_format({'bold': True, 'bg_color': '#3daee9', 'color': 'white', 'border': 1})
            wrap = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1}); center = workbook.add_format({'valign': 'top', 'align': 'center', 'border': 1})
            headers = ["ID", "Fecha", "Descripción", "Tags", "FOTO"]
            for col, text in enumerate(headers): worksheet.write(0, col, text, bold)
            worksheet.set_column('A:A', 5); worksheet.set_column('B:B', 12); worksheet.set_column('C:C', 50); worksheet.set_column('D:D', 15); worksheet.set_column('E:E', 20)
            datos = self.db.obtener_todas_cronologico(); row = 1
            for tarea in datos:
                worksheet.write(row, 0, tarea[0], center); worksheet.write(row, 1, tarea[1], center)

                # Limpieza de FOTO y REF
                desc_limpia = re.sub(r"\[FOTO:.*?\]", "", tarea[2])
                desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                worksheet.write(row, 2, desc_limpia, wrap); worksheet.write(row, 3, tarea[3], wrap)
                m = re.search(r"\[FOTO:\s*(.*?)\]", tarea[2])
                if m:
                    nombre = m.group(1).split("]")[0].strip(); ruta = os.path.join(self.carpeta_fotos, nombre)
                    if os.path.exists(ruta):
                        try: worksheet.insert_image(row, 4, ruta, {'x_scale': 0.1, 'y_scale': 0.1, 'object_position': 1}); worksheet.set_row(row, 80)
                        except: worksheet.write(row, 4, "Err Img", center)
                    else: worksheet.write(row, 4, "No File", center)
                else: worksheet.write(row, 4, "-", center)
                row += 1
            workbook.close(); QMessageBox.information(self, "Exportado", "Excel guardado correctamente.")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def init_dashboard_tab(self):
        l = QVBoxLayout()
        h_cards = QHBoxLayout()
        style_card = "QGroupBox { border: 1px solid #444; border-radius: 8px; background-color: #333; margin-top: 10px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; } QLabel { font-size: 24px; font-weight: bold; }"
        self.card_avisos = QGroupBox("Avisos Pendientes"); self.card_avisos.setStyleSheet(style_card)
        l_c1 = QVBoxLayout(); self.lbl_count_avisos = QLabel("0"); self.lbl_count_avisos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c1.addWidget(self.lbl_count_avisos); self.card_avisos.setLayout(l_c1); h_cards.addWidget(self.card_avisos)
        self.card_todos = QGroupBox("Tareas Por Hacer"); self.card_todos.setStyleSheet(style_card)
        l_c2 = QVBoxLayout(); self.lbl_count_todos = QLabel("0"); self.lbl_count_todos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c2.addWidget(self.lbl_count_todos); self.card_todos.setLayout(l_c2); h_cards.addWidget(self.card_todos)
        self.card_regs = QGroupBox("Registros este Mes"); self.card_regs.setStyleSheet(style_card)
        l_c3 = QVBoxLayout(); self.lbl_count_regs = QLabel("0"); self.lbl_count_regs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c3.addWidget(self.lbl_count_regs); self.card_regs.setLayout(l_c3); h_cards.addWidget(self.card_regs)
        l.addLayout(h_cards)
        h_split = QHBoxLayout()
        v_list = QVBoxLayout(); v_list.addWidget(QLabel("📋 Últimas Intervenciones"))
        self.dash_table = QTableWidget(); self.setup_table(self.dash_table); self.configurar_deseleccion(self.dash_table); self.dash_table.setRowCount(15); self.dash_table.cellDoubleClicked.connect(lambda r, c: self.edit_rec(self.dash_table)); v_list.addWidget(self.dash_table)
        h_split.addLayout(v_list, 80)
        v_stats = QVBoxLayout(); v_stats.addWidget(QLabel("📊 Distribución"))
        self.group_stats = QGroupBox(); self.group_stats.setStyleSheet("QGroupBox { border: 1px solid #444; background: #252525; border-radius: 6px; }")
        layout_stats = QVBoxLayout(); layout_stats.setSpacing(10); layout_stats.setContentsMargins(5, 10, 5, 5)
        def crear_barra(titulo, color):
            lbl = QLabel(titulo); lbl.setStyleSheet("font-size: 12px; color: #ccc;")
            bar = QProgressBar(); bar.setStyleSheet(f"QProgressBar {{ border: 1px solid #555; border-radius: 4px; text-align: center; background: #333; height: 18px; font-size: 11px; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}"); bar.setValue(0)
            return lbl, bar
        self.lbl_elec, self.bar_elec = crear_barra("⚡ Eléctrico", "#3daee9"); layout_stats.addWidget(self.lbl_elec); layout_stats.addWidget(self.bar_elec)
        self.lbl_mec, self.bar_mec = crear_barra("⚙️ Mecánico", "#e67e22"); layout_stats.addWidget(self.lbl_mec); layout_stats.addWidget(self.bar_mec)
        self.lbl_prev, self.bar_prev = crear_barra("🛡️ Preventivo", "#27ae60"); layout_stats.addWidget(self.lbl_prev); layout_stats.addWidget(self.bar_prev)
        self.lbl_urg, self.bar_urg = crear_barra("🚨 Urgente", "#c0392b"); layout_stats.addWidget(self.lbl_urg); layout_stats.addWidget(self.bar_urg)
        layout_stats.addStretch(); self.group_stats.setLayout(layout_stats); v_stats.addWidget(self.group_stats); h_split.addLayout(v_stats, 20); l.addLayout(h_split); self.tab_dashboard.setLayout(l)

    def refresh_dashboard(self):
        avisos = self.db.obtener_avisos(); hoy = QDate.currentDate(); pendientes_reales = 0
        for aid, tit, finicio, freq, dur, ult in avisos:
            if not finicio: continue
            fi = QDate.fromString(finicio, "yyyy-MM-dd")
            if not freq: freq = "Anual"
            ocurrencia = fi
            while ocurrencia.addDays(dur) < hoy:
                if freq == "Diario": ocurrencia = ocurrencia.addDays(1)
                elif freq == "Semanal": ocurrencia = ocurrencia.addDays(7)
                elif freq == "Mensual": ocurrencia = ocurrencia.addMonths(1)
                elif freq == "Trimestral": ocurrencia = ocurrencia.addMonths(3)
                elif freq == "Semestral": ocurrencia = ocurrencia.addMonths(6)
                elif freq == "Anual": ocurrencia = ocurrencia.addYears(1)
                else: break
            fin_ocurrencia = ocurrencia.addDays(dur)
            if ocurrencia <= hoy <= fin_ocurrencia and ult != ocurrencia.toString("yyyy-MM-dd"): pendientes_reales += 1
        self.lbl_count_avisos.setText(str(pendientes_reales))
        self.lbl_count_avisos.setStyleSheet("color: #e74c3c; font-size: 32px; font-weight: bold;" if pendientes_reales > 0 else "color: #2ecc71; font-size: 32px; font-weight: bold;")
        todos = self.db.obtener_pendientes(); self.lbl_count_todos.setText(str(len(todos))); self.lbl_count_todos.setStyleSheet("color: #f1c40f; font-size: 32px; font-weight: bold;")
        registros = self.db.obtener_todas_cronologico(); mes_actual = hoy.toString("yyyy-MM"); count_mes = sum(1 for r in registros if r[1].startswith(mes_actual))
        self.lbl_count_regs.setText(str(count_mes)); self.lbl_count_regs.setStyleSheet("color: #3daee9; font-size: 32px; font-weight: bold;")
        self.fill_t(self.dash_table, registros[:15])
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
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar Logo", "", "Imágenes (*.jpg *.png *.jpeg)", options=QFileDialog.Option.DontUseNativeDialog)
        if archivo:
            try:
                # Copiamos la imagen a la carpeta local con el nombre que busca el PDF
                # Use DATA_DIR path
                destino = os.path.join(DATA_DIR, "Logo.jpg")
                shutil.copy2(archivo, destino)
                QMessageBox.information(self, "Logo Actualizado", "✅ Logo actualizado. Aparecerá en el próximo PDF.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def quitar_logo(self):
        # Use DATA_DIR path
        destino = os.path.join(DATA_DIR, "Logo.jpg")
        if os.path.exists(destino):
            try:
                os.remove(destino)
                QMessageBox.information(self, "Logo Borrado", "🗑️ El logo ha sido eliminado del sistema.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.information(self, "Información", "No había ningún logo configurado.")

    def exportar_pdf(self):
        dlg = DialogoExportarPDF(self)
        if not dlg.exec(): return
        inicio, fin, incluir_fotos = dlg.get_data()

        nombre_defecto = f"Reporte_Mantenimiento_{datetime.now().strftime('%Y%m%d')}.pdf"
        archivo = self.guardar_archivo_dialogo("Guardar PDF", nombre_defecto, "PDF (*.pdf)")
        if not archivo: return

        # 1. Recuperar datos en el hilo principal (rápido)
        try:
            conn = self.db.conectar()
            c = conn.cursor()
            if inicio and fin:
                c.execute("SELECT fecha, descripcion, tags FROM tareas WHERE fecha BETWEEN ? AND ? ORDER BY fecha DESC", (inicio, fin))
                titulo_doc = f"Reporte de Mantenimiento ({inicio} a {fin})"
            else:
                c.execute("SELECT fecha, descripcion, tags FROM tareas ORDER BY fecha DESC")
                titulo_doc = "Reporte Histórico Completo"
            datos = c.fetchall()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Error DB", str(e))
            return

        # 2. Configurar UI de progreso
        self.progreso_pdf = QDialog(self)
        self.progreso_pdf.setWindowTitle("Generando PDF...")
        self.progreso_pdf.setFixedSize(300, 100)
        self.progreso_pdf.setWindowModality(Qt.WindowModality.ApplicationModal)
        l = QVBoxLayout()
        l.addWidget(QLabel("Procesando imágenes y generando documento...\nPor favor espera."))
        bar = QProgressBar()
        bar.setRange(0, 0) # Barra infinita
        l.addWidget(bar)
        self.progreso_pdf.setLayout(l)
        # Quitar botón de cerrar para obligar a esperar
        self.progreso_pdf.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        # 3. Iniciar Hilo
        self.hilo_pdf = GeneradorPDFThread(archivo, titulo_doc, datos, self.carpeta_fotos, incluir_fotos)
        self.hilo_pdf.resultado.connect(self.pdf_finalizado)
        self.hilo_pdf.start()

        self.progreso_pdf.exec() # Bloquea la UI hasta que se cierre con accept()

    def pdf_finalizado(self, exito, mensaje):
        self.progreso_pdf.accept() # Cierra el diálogo de progreso
        if exito:
            QMessageBox.information(self, "Éxito", mensaje)
        else:
            QMessageBox.critical(self, "Error PDF", mensaje)

    def guardar_archivo_dialogo(self, titulo, nombre_defecto, filtro):
        dialogo = QFileDialog(self, titulo); dialogo.setAcceptMode(QFileDialog.AcceptMode.AcceptSave); dialogo.setFileMode(QFileDialog.FileMode.AnyFile); dialogo.setNameFilter(filtro); dialogo.selectFile(nombre_defecto)
        dialogo.setOption(QFileDialog.Option.DontUseNativeDialog, True); dialogo.setLabelText(QFileDialog.DialogLabel.Accept, "Guardar"); dialogo.setLabelText(QFileDialog.DialogLabel.Reject, "Cancelar")
        if dialogo.exec(): return dialogo.selectedFiles()[0]
        return None

    def limpiar_fotos_huerfanas(self, silencioso=False):
        try:
            fotos_en_uso = set(); conn = self.db.conectar(); c = conn.cursor()
            c.execute("SELECT descripcion FROM tareas")
            for row in c.fetchall():
                m = re.search(r"\[FOTO:\s*(.*?)\]", row[0])
                if m: fotos_en_uso.add(m.group(1).strip())
            c.execute("SELECT detalles FROM pendientes")
            for row in c.fetchall():
                m = re.search(r"\[FOTO:\s*(.*?)\]", row[0])
                if m: fotos_en_uso.add(m.group(1).strip())
            conn.close()
            if not os.path.exists(self.carpeta_fotos): return
            basura = []
            for f in os.listdir(self.carpeta_fotos):
                if f not in fotos_en_uso and f not in ["Logo.jpg", "icono.png"] and not f.startswith("QR_"): basura.append(f)
            if not basura: return
            confirmado = True
            if not silencioso and QMessageBox.question(self, "Limpieza", f"Hay {len(basura)} fotos basura. ¿Borrar?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No: confirmado = False
            if confirmado:
                for f in basura:
                    try: os.remove(os.path.join(self.carpeta_fotos, f))
                    except: pass
        except Exception as e: print(f"Error limpieza: {e}")

    def edit_todo(self, item=None): # Añadimos argumento opcional para el doble click
        row = self.todo_list.currentRow()
        if row < 0: return

        item = self.todo_list.item(row)
        pid = item.data(Qt.ItemDataRole.UserRole)
        titulo_actual = item.data(Qt.ItemDataRole.UserRole + 1)
        detalles_raw = item.data(Qt.ItemDataRole.UserRole + 2)

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
            texto_limpio = re.sub(r"\[FOTO:.*?\]", "", detalles_raw)
            texto_limpio = re.sub(r"\[REF:.*?\]", "", texto_limpio).strip()

        # Abrimos el diálogo con el texto LIMPIO
        dlg = DialogoEditarPendiente(self, titulo_actual, texto_limpio, ruta_foto_actual)

        if dlg.exec():
            nuevo_t, nuevo_d, nueva_foto = dlg.get_data()

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

                # Guardamos en BD (con la REF oculta de nuevo)
                if self.db.actualizar_pendiente(pid, nuevo_t, desc_final):
                    self.refresh_todos()
                    self.statusBar().showMessage("✅ Pendiente actualizado", 3000)

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

    # --- 2. INSTANCIAR VENTANA PRINCIPAL ---
    # Recuerda usar el nombre real de tu clase (VentanaPrincipal o MainWindow)
    try:
        ventana = MaintenanceApp()
    except NameError:
        # Fallback por si tu clase tiene otro nombre
        # ventana = VentanaPrincipal()
        print("Error: Revisa el nombre de la clase de la ventana principal.")

    # --- 3. SPLASH SCREEN ESTÁTICO (Compatible con Wayland) ---
    if os.path.exists(ruta_logo):
        pixmap = QPixmap(ruta_logo)

        # Escalado suave si es muy grande
        if pixmap.width() > 600:
            pixmap = pixmap.scaledToWidth(600, Qt.TransformationMode.SmoothTransformation)

        # Creamos el Splash normal
        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.show() # Se muestra de golpe (sin fade-in, sin errores)

        # Función para cerrar splash y abrir app
        def iniciar_programa():
            splash.close()
            ventana.show()

        # Esperamos 2 segundos (2000 ms) y cambiamos
        QTimer.singleShot(2000, iniciar_programa)

    else:
        # Si no hay logo, arranca normal
        ventana.show()

    sys.exit(app.exec())
