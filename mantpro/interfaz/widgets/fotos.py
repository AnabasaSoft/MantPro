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

"""Widgets de fotos: visor, colección, selector y zona de arrastre."""

import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
                             QMessageBox, QDialog, QAbstractItemView, QListWidgetItem, QFileDialog,
                             QSizePolicy, QTreeView)
from PyQt6.QtCore import Qt, pyqtSignal, QDir, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFileSystemModel

from ...idiomas import t
from ..comun import _estilo_zona_arrastre, tt

class VisorFoto(QDialog):
    """Muestra una foto a tamaño completo. Si se le pasa [rutas] (la colección
    entera), permite pasar de una a otra con los botones o las flechas."""
    def __init__(self, ruta_imagen, parent=None, rutas=None):
        super().__init__(parent)
        self.setWindowTitle(t("title_visor_imagen"))
        self.resize(900, 680)
        self.rutas = [r for r in (rutas or [ruta_imagen]) if r]
        self.indice = self.rutas.index(ruta_imagen) if ruta_imagen in self.rutas else 0
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.label, 1)
        barra = QHBoxLayout()
        self.btn_ant = QPushButton("◀"); self.btn_ant.clicked.connect(lambda: self.mover(-1))
        self.btn_sig = QPushButton("▶"); self.btn_sig.clicked.connect(lambda: self.mover(1))
        self.lbl_pos = QLabel(); self.lbl_pos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_cerrar = QPushButton(t("btn_cerrar"))
        btn_cerrar.clicked.connect(self.accept)
        barra.addWidget(self.btn_ant); barra.addWidget(self.lbl_pos, 1); barra.addWidget(self.btn_sig); barra.addWidget(btn_cerrar)
        layout.addLayout(barra)
        varias = len(self.rutas) > 1
        for w in (self.btn_ant, self.btn_sig, self.lbl_pos): w.setVisible(varias)
        self.cargar()

    def cargar(self):
        self.pixmap_original = QPixmap(self.rutas[self.indice]) if self.rutas else QPixmap()
        self.lbl_pos.setText(f"{self.indice + 1} / {len(self.rutas)}")
        if self.pixmap_original.isNull():
            self.label.setPixmap(QPixmap()); self.label.setText(t("msg_error_cargar_imagen"))
        else:
            self.label.setText(""); self.actualizar_imagen()

    def mover(self, paso):
        if len(self.rutas) < 2: return
        self.indice = (self.indice + paso) % len(self.rutas)
        self.cargar()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left: self.mover(-1)
        elif event.key() == Qt.Key.Key_Right: self.mover(1)
        else: super().keyPressEvent(event)

    def resizeEvent(self, event):
        self.actualizar_imagen()
        super().resizeEvent(event)

    def actualizar_imagen(self):
        if not self.pixmap_original.isNull() and self.label.width() > 0:
            pixmap_scaled = self.pixmap_original.scaled(
                self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.label.setPixmap(pixmap_scaled)


class GaleriaFotosWidget(QWidget):
    """Colección de fotos extra de un trabajo (además de la de antes y la de
    después): miniaturas en fila, añadir varias de golpe (botón o arrastrar),
    quitar la seleccionada y doble clic para verlas a tamaño completo pasando
    de una a otra. Guarda las fotos en la carpeta de fotos de la app."""
    def __init__(self, carpeta_fotos, parent=None, nombres=None):
        super().__init__(parent)
        self.carpeta_fotos = carpeta_fotos
        self.setAcceptDrops(True)
        v = QVBoxLayout(self); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(4)
        cab = QHBoxLayout()
        self.lbl_titulo = QLabel(); cab.addWidget(self.lbl_titulo, 1)
        btn_add = QPushButton(tt("btn_anadir_fotos", "➕ Añadir fotos")); btn_add.clicked.connect(self.elegir_fotos)
        self.btn_quitar = QPushButton(tt("btn_quitar_foto_coleccion", "🗑️ Quitar"))
        self.btn_quitar.setStyleSheet("background-color: #c0392b; color: white;")
        self.btn_quitar.clicked.connect(self.quitar_seleccionadas)
        cab.addWidget(btn_add); cab.addWidget(self.btn_quitar)
        v.addLayout(cab)
        self.lista = QListWidget()
        self.lista.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista.setFlow(QListWidget.Flow.LeftToRight)
        self.lista.setWrapping(False)
        self.lista.setIconSize(QSize(90, 90))
        self.lista.setFixedHeight(118)
        self.lista.setMovement(QListWidget.Movement.Static)
        self.lista.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.lista.setToolTip(tt("tt_coleccion_fotos", "Doble clic para ver a tamaño completo. Puedes arrastrar fotos aquí."))
        self.lista.itemDoubleClicked.connect(self.ver)
        self.lista.setAcceptDrops(False)
        v.addWidget(self.lista)
        self.set_nombres(nombres or [])

    def _ruta(self, nombre): return os.path.join(self.carpeta_fotos, nombre)

    def _actualizar_titulo(self):
        n = self.lista.count()
        self.lbl_titulo.setText(tt("lbl_coleccion_fotos", "Colección de fotos") + (f" ({n})" if n else ""))
        self.btn_quitar.setEnabled(n > 0)

    def set_nombres(self, nombres):
        self.lista.clear()
        for n in nombres: self._anadir_item(n)
        self._actualizar_titulo()

    def nombres(self):
        return [self.lista.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.lista.count())]

    def _anadir_item(self, nombre):
        it = QListWidgetItem()
        pix = QPixmap(self._ruta(nombre))
        if pix.isNull(): it.setText(nombre)
        else: it.setIcon(QIcon(pix.scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
        it.setData(Qt.ItemDataRole.UserRole, nombre)
        it.setToolTip(nombre)
        self.lista.addItem(it)

    def anadir_rutas(self, rutas):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        for i, origen in enumerate(rutas):
            if QPixmap(origen).isNull(): continue
            nuevo = f"pc_galeria_{ts}_{i}{os.path.splitext(origen)[1].lower()}"
            try:
                shutil.copy2(origen, self._ruta(nuevo))
                self._anadir_item(nuevo)
            except Exception as e:
                QMessageBox.critical(self, t("title_error"), str(e))
        self._actualizar_titulo()

    def elegir_fotos(self):
        dlg = QFileDialog(self, tt("btn_anadir_fotos", "➕ Añadir fotos"))
        dlg.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dlg.setNameFilter(tt("filtro_imagenes", "Imágenes") + " (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        dlg.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dlg.setDirectory(QDir.homePath())
        dlg.setLabelText(QFileDialog.DialogLabel.Accept, t("btn_elegir_foto"))
        dlg.setLabelText(QFileDialog.DialogLabel.Reject, t("btn_cancelar"))
        if dlg.exec(): self.anadir_rutas(dlg.selectedFiles())

    def quitar_seleccionadas(self):
        for it in self.lista.selectedItems() or ([self.lista.currentItem()] if self.lista.currentItem() else []):
            self.lista.takeItem(self.lista.row(it))
        self._actualizar_titulo()

    def ver(self, item):
        rutas = [self._ruta(n) for n in self.nombres()]
        VisorFoto(self._ruta(item.data(Qt.ItemDataRole.UserRole)), self, rutas=rutas).exec()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self, e):
        self.anadir_rutas([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])


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
