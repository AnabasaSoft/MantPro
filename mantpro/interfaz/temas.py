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

"""Temas visuales: oscuro, claro y clásico (Windows 98)."""

from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtCore import QSettings

from .comun import _estilo_zona_arrastre

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
