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

"""Temas visuales: oscuro, claro y clásico (Windows 98)."""

from PyQt6.QtWidgets import QApplication, QStyleFactory, QWidget
from PyQt6.QtCore import QSettings

import os
import tempfile

from .comun import _estilo_zona_arrastre

def _iconos_del_tema(oscuro):
    """Pone los iconos de Qt (los botones de los selectores de ficheros y
    carpetas: atrás, subir, nueva carpeta, vista…) a juego con el tema de
    MantPro y no con el del sistema: con un tema de iconos oscuro en el
    sistema (iconos blancos), los temas claro y retro los dejaban blanco
    sobre blanco, y al revés. Sirve para los iconos de carpetas y ficheros;
    los de los botones los dibuja MantPro (ver _estilo_con_iconos), porque
    sin estos temas de iconos (Windows) no habría forma de elegir su color.
    Devuelve True si ha encontrado el tema de iconos."""
    from PyQt6.QtGui import QIcon
    if not hasattr(_iconos_del_tema, "original"):
        _iconos_del_tema.original = QIcon.themeName()
    # Según la plataforma (offscreen, ejecutable empaquetado…), Qt no siempre
    # busca en las carpetas de iconos estándar: se añaden las que falten
    rutas = list(QIcon.themeSearchPaths())
    datos = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    for carpeta in [os.path.expanduser("~/.local/share/icons"), os.path.expanduser("~/.icons")] + \
            [os.path.join(d, "icons") for d in datos.split(os.pathsep) if d]:
        if carpeta not in rutas and os.path.isdir(carpeta):
            rutas.append(carpeta)
    candidatos = ("breeze-dark",) if oscuro else ("breeze", "Adwaita")
    for nombre in candidatos:
        for carpeta in rutas:
            if os.path.isfile(os.path.join(carpeta, nombre, "index.theme")):
                if rutas != QIcon.themeSearchPaths():
                    QIcon.setThemeSearchPaths(rutas)
                QIcon.setThemeName(nombre)
                return True
    # Sin el tema que toca: el del sistema, tal cual (Qt usa los suyos si no hay)
    QIcon.setThemeName(_iconos_del_tema.original)
    return False


def _dibujar_icono(clave, color):
    """Icono de los botones de los selectores de ficheros, dibujado aquí en
    [color] (no depende de los iconos del sistema: en Windows, o con un tema
    de iconos oscuro en Linux, salían blancos sobre fondo claro). Se dibuja
    en una rejilla de 24 × 24 y se guarda a varios tamaños."""
    from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPainterPath
    from PyQt6.QtCore import Qt, QPointF, QRectF
    icono = QIcon()
    for lado in (16, 22, 24, 32, 48, 64):
        pixmap = QPixmap(lado, lado)
        pixmap.fill(Qt.GlobalColor.transparent)
        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.scale(lado / 24, lado / 24)
        pluma = QPen(QColor(color), 2)
        pluma.setCapStyle(Qt.PenCapStyle.RoundCap); pluma.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pluma)

        def linea(*puntos):
            camino = QPainterPath(QPointF(*puntos[0]))
            for punto in puntos[1:]:
                camino.lineTo(QPointF(*punto))
            p.drawPath(camino)

        if clave == "atras":
            linea((19, 12), (5, 12)); linea((11, 6), (5, 12), (11, 18))
        elif clave == "adelante":
            linea((5, 12), (19, 12)); linea((13, 6), (19, 12), (13, 18))
        elif clave == "subir":
            linea((12, 19), (12, 5)); linea((6, 11), (12, 5), (18, 11))
        elif clave == "nueva_carpeta":
            linea((3, 19), (3, 6), (9, 6), (11, 8), (21, 8), (21, 19), (3, 19))
            linea((12, 11), (12, 17)); linea((9, 14), (15, 14))
        elif clave == "vista_lista":     # iconos en cuadrícula
            for x, y in ((4, 4), (14, 4), (4, 14), (14, 14)):
                p.drawRoundedRect(QRectF(x, y, 6, 6), 1, 1)
        elif clave == "vista_detalle":   # filas con detalle
            for y in (6, 12, 18):
                p.drawPoint(QPointF(4, y)); linea((8, y), (20, y))
        p.end()
        icono.addPixmap(pixmap)
    return icono


def _estilo_con_iconos(color):
    """Estilo Fusion con los iconos de los botones de los selectores de
    ficheros (atrás, adelante, subir, nueva carpeta y las dos vistas)
    dibujados por MantPro en [color], a juego con el tema."""
    from PyQt6.QtWidgets import QProxyStyle, QStyle

    claves = {QStyle.StandardPixmap.SP_ArrowBack: "atras", QStyle.StandardPixmap.SP_ArrowLeft: "atras",
              QStyle.StandardPixmap.SP_ArrowForward: "adelante", QStyle.StandardPixmap.SP_ArrowRight: "adelante",
              QStyle.StandardPixmap.SP_FileDialogToParent: "subir", QStyle.StandardPixmap.SP_ArrowUp: "subir",
              QStyle.StandardPixmap.SP_FileDialogNewFolder: "nueva_carpeta",
              QStyle.StandardPixmap.SP_FileDialogListView: "vista_lista",
              QStyle.StandardPixmap.SP_FileDialogDetailedView: "vista_detalle"}

    class EstiloMantPro(QProxyStyle):
        _cache = {}

        def standardIcon(self, icono, opcion=None, widget=None):
            clave = claves.get(icono)
            if clave is None:
                return super().standardIcon(icono, opcion, widget)
            if (clave, color) not in self._cache:
                self._cache[(clave, color)] = _dibujar_icono(clave, color)
            return self._cache[(clave, color)]

    estilo = EstiloMantPro(QStyleFactory.create("Fusion"))
    _estilo_con_iconos.actual = estilo   # que Python no lo libere mientras Qt lo usa
    return estilo


def _flechas(color):
    """Rutas de dos PNG pequeños (flecha abajo y arriba) del color indicado,
    para los desplegables y los campos numéricos de los temas claro y
    clásico: al darles estilo con hoja de estilos, Qt deja de dibujar sus
    flechas y hay que ponérselas como imagen. Se generan una vez en la
    carpeta temporal."""
    from PyQt6.QtGui import QImage, QPainter, QColor, QPolygonF
    from PyQt6.QtCore import QPointF, Qt
    carpeta = os.path.join(tempfile.gettempdir(), "mantpro_flechas")
    os.makedirs(carpeta, exist_ok=True)
    rutas = []
    for nombre, puntos in (("abajo", [(1, 3), (9, 3), (5, 8)]), ("arriba", [(1, 7), (9, 7), (5, 2)])):
        ruta = os.path.join(carpeta, f"{nombre}_{color.lstrip('#')}.png")
        if not os.path.exists(ruta):
            img = QImage(10, 10, QImage.Format.Format_ARGB32); img.fill(Qt.GlobalColor.transparent)
            pintor = QPainter(img); pintor.setRenderHint(QPainter.RenderHint.Antialiasing)
            pintor.setPen(Qt.PenStyle.NoPen); pintor.setBrush(QColor(color))
            pintor.drawPolygon(QPolygonF([QPointF(x, y) for x, y in puntos])); pintor.end()
            img.save(ruta, "PNG")
        rutas.append(ruta.replace("\\", "/"))
    return rutas


def _estilo_flechas(color, fondo, borde_boton):
    """Reglas de hoja de estilos para las flechas de desplegables, campos de
    fecha y campos numéricos."""
    abajo, arriba = _flechas(color)
    return f"""
        QComboBox::drop-down, QDateEdit::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 18px; background: {fondo}; {borde_boton} }}
        QComboBox::down-arrow, QDateEdit::down-arrow {{ image: url("{abajo}"); width: 10px; height: 10px; }}
        QAbstractSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 16px; background: {fondo}; {borde_boton} }}
        QAbstractSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 16px; background: {fondo}; {borde_boton} }}
        QAbstractSpinBox::up-arrow {{ image: url("{arriba}"); width: 8px; height: 8px; }}
        QAbstractSpinBox::down-arrow {{ image: url("{abajo}"); width: 8px; height: 8px; }}
        """


class Temas:
    """Temas visuales: oscuro, claro y clásico (Windows 98).

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

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
        if hasattr(self, 'lbl_info') and hasattr(self, 'calendar'):
            self.update_calendar_list()
        # Los gráficos toman el color de texto del tema al pintarse.
        for grafico in self.findChildren(QWidget):
            if hasattr(grafico, "_color_texto_fijo"):
                grafico.update()

        # Repintar las zonas de "arrastra una foto aquí" si no tienen foto puesta
        if hasattr(self, 'lbl_entry_foto') and not getattr(self, 'entry_foto_filename', None):
            self.lbl_entry_foto.setStyleSheet(_estilo_zona_arrastre())
        if hasattr(self, 'lbl_entry_foto_d') and not getattr(self, 'entry_foto_despues_filename', None):
            self.lbl_entry_foto_d.setStyleSheet(_estilo_zona_arrastre())

    def _aplicar_tema_retro(self):
        """Estilo clásico inspirado en Windows 98 / 2000."""
        QApplication.setStyle(_estilo_con_iconos("#000000"))
        _iconos_del_tema(oscuro=False)
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
        QMenu { background-color: #d4d0c8; border-width: 2px; border-style: solid; border-color: #ffffff #404040 #404040 #ffffff; }
        QMenu::item:selected { background-color: #000080; color: white; }
        QTabWidget::pane { border-width: 2px; border-style: solid; border-color: #ffffff #404040 #404040 #ffffff; background: #d4d0c8; }
        QTabBar::tab { background: #d4d0c8; border-width: 1px 2px 0 1px; border-style: solid; border-color: #ffffff #404040 #404040 #ffffff; padding: 4px 14px; margin-right: 1px; margin-top: 2px; }
        QTabBar::tab:selected { background: #d4d0c8; font-weight: bold; margin-top: 0; padding-bottom: 6px; }
        QPushButton { background-color: #d4d0c8; border-width: 2px; border-style: solid; border-color: #ffffff #404040 #404040 #ffffff; padding: 4px 12px; min-height: 20px; color: black; }
        QPushButton:pressed { border-width: 2px; border-style: solid; border-color: #808080 #ffffff #ffffff #808080; }
        QPushButton:disabled { color: #808080; }
        QPushButton:hover { background-color: #e4e0d8; }
        QLineEdit, QTextEdit, QDateEdit, QAbstractSpinBox { background-color: white; border-width: 2px; border-style: solid; border-color: #808080 #ffffff #ffffff #808080; padding: 2px; color: black; }
        QTableWidget, QTreeView, QListWidget, QListView { background-color: white; border-width: 2px; border-style: solid; border-color: #808080 #ffffff #ffffff #808080; gridline-color: #c0c0c0; color: black; }
        QHeaderView::section { background-color: #d4d0c8; border-width: 1px; border-style: solid; border-color: #ffffff #808080 #808080 #ffffff; padding: 4px; font-weight: bold; color: black; }
        QGroupBox { border: 1px solid #808080; margin-top: 8px; padding-top: 12px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
        QComboBox { background-color: white; border-width: 2px; border-style: solid; border-color: #808080 #ffffff #ffffff #808080; padding: 2px; color: black; }
        QCheckBox::indicator, QRadioButton::indicator { width: 13px; height: 13px; }
        QProgressBar { border-width: 2px; border-style: solid; border-color: #808080 #ffffff #ffffff #808080; background: white; text-align: center; color: black; }
        QProgressBar::chunk { background-color: #000080; }
        QScrollBar:vertical { background: #d4d0c8; width: 16px; border: 1px solid #808080; }
        QScrollBar::handle:vertical { background: #d4d0c8; border-width: 1px; border-style: solid; border-color: #ffffff #404040 #404040 #ffffff; min-height: 20px; }
        QScrollBar:horizontal { background: #d4d0c8; height: 16px; border: 1px solid #808080; }
        QScrollBar::handle:horizontal { background: #d4d0c8; border-width: 1px; border-style: solid; border-color: #ffffff #404040 #404040 #ffffff; min-width: 20px; }
        QStatusBar { background: #d4d0c8; border-top: 1px solid #808080; }
        QCalendarWidget QAbstractItemView:enabled { background-color: white; color: black; selection-background-color: #000080; selection-color: white; }
        QSplitter::handle { background: #d4d0c8; }
        QDialog { background-color: #d4d0c8; }
        """ + _estilo_flechas("#000000", "#d4d0c8", "border-width: 1px; border-style: solid; border-color: #ffffff #404040 #404040 #ffffff;"))

    def _aplicar_tema_claro(self):
        """Tema claro moderno."""
        QApplication.setStyle(_estilo_con_iconos("#333333"))
        _iconos_del_tema(oscuro=False)
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
        QLineEdit, QTextEdit, QDateEdit, QAbstractSpinBox { background-color: white; border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px; }
        QLineEdit:focus, QTextEdit:focus { border-color: #0078d4; }
        QTableWidget, QTreeView, QListWidget, QListView { background-color: white; border: 1px solid #c0c0c0; border-radius: 4px; gridline-color: #e0e0e0; selection-background-color: #0078d4; selection-color: white; }
        QHeaderView::section { background-color: #e6e6e6; border: none; border-right: 1px solid #d0d0d0; border-bottom: 1px solid #d0d0d0; padding: 6px; font-weight: bold; color: #333; }
        QGroupBox { border: 1px solid #d0d0d0; border-radius: 6px; margin-top: 8px; padding-top: 14px; }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; color: #0078d4; }
        QComboBox { background-color: white; border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px; }
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
        """ + _estilo_flechas("#444444", "#e6e6e6", "border-left: 1px solid #d0d0d0;"))

    def _aplicar_tema_oscuro(self):
        """Tema oscuro original de MantPro."""
        QApplication.setStyle(_estilo_con_iconos("#e0e0e0"))
        # Limpiar la paleta retro si venimos de ella
        QApplication.instance().setPalette(QApplication.style().standardPalette())
        # Botones de los selectores de ficheros: gris medio, con sus iconos
        # dibujados en claro (ver _estilo_con_iconos)
        _iconos_del_tema(oscuro=True)
        boton_fichero = ("#555555", "#e0e0e0", "#6a6a6a", "#666666", "#3c3c3c", "#4a4a4a")
        self.setStyleSheet("""
        QMainWindow, QWidget { background-color: #2b2b2b; color: #e0e0e0; font-family: "Segoe UI", sans-serif; font-size: 14px; }
        QTabWidget::pane { border: 1px solid #444; background: #2b2b2b; border-radius: 4px; }
        QTabBar::tab { background: #3c3c3c; color: #b0b0b0; padding: 8px 20px; border-top-left-radius: 4px; margin-right: 2px; }
        QTabBar::tab:selected { background: #3daee9; color: white; font-weight: bold; }
        QPushButton { background-color: #3c3c3c; border: 1px solid #555; border-radius: 6px; padding: 6px 12px; color: #e0e0e0; }
        QPushButton:hover { background-color: #505050; border: 1px solid #3daee9; }
        QPushButton:pressed { background-color: #3daee9; color: white; }
        QLineEdit, QTextEdit, QDateEdit, QListWidget, QTableWidget, QTreeView, QListView { background-color: #1e1e1e; border: 1px solid #555; border-radius: 4px; color: #e0e0e0; padding: 4px; selection-background-color: #3daee9; selection-color: white; alternate-background-color: #262626; }
        QHeaderView::section { background-color: #3c3c3c; padding: 6px; border: none; color: #e0e0e0; font-weight: bold; }
        QCalendarWidget QAbstractItemView:enabled { color: #e0e0e0; background-color: #1e1e1e; selection-background-color: #80DEEA; selection-color: black; }
        QMenu { background-color: #2b2b2b; color: #e0e0e0; border: 1px solid #555; }
        QMenu::item { padding: 5px 20px; }
        QMenu::item:selected { background-color: #3daee9; color: white; }
        QMenu::separator { height: 1px; background: #7a7a7a; margin: 5px 8px; }

        /* ESTILO ESPECÍFICO PARA DIÁLOGOS DE ARCHIVOS (QFileDialog) */
        QFileDialog QToolButton {
            background-color: %s;
            color: %s;
            border: 1px solid %s;
            border-radius: 4px;
            margin: 2px;
        }
        QFileDialog QToolButton:hover {
            background-color: %s;
            border: 1px solid #3daee9;
        }
        QFileDialog QToolButton:disabled {
            background-color: %s;
            border: 1px solid %s;
        }
        QFileDialog QListView, QFileDialog QTreeView {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        """ % boton_fichero)
