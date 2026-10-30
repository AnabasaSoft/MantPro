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

"""Pestaña «Registrar»: alta directa de trabajos."""

import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
                             QDateEdit, QMessageBox, QComboBox, QCompleter, QDoubleSpinBox,
                             QWidget, QScrollArea, QFrame)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QPixmap

from ...idiomas import t
from ..comun import (_crear_checks_etiquetas, _estilo_zona_arrastre, _poblar_combo_maquinas,
                     _tags_desde_checks, tt)
from ..widgets.fotos import DialogoSelectorFoto, GaleriaFotosWidget, LabelArrastrable, VisorFoto
from ...nucleo.fotos import con_fotos_galeria

class PestanaRegistrar:
    """Pestaña «Registrar»: alta directa de trabajos.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

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
        self.galeria_entry = GaleriaFotosWidget(self.carpeta_fotos, self)
        l.addWidget(self.galeria_entry)
        self.ire = QLineEdit(); self.ire.setPlaceholderText(t("ph_resumen")); l.addWidget(QLabel(t("lbl_resumen_tarea"))); l.addWidget(self.ire)
        l.addWidget(QLabel(t("lbl_detalles")))
        self.idet = QTextEdit(); l.addWidget(self.idet)
        fila_maquina_entry = QHBoxLayout()
        fila_maquina_entry.addWidget(QLabel(tt("lbl_maquina", "Máquina") + ":"))
        self.combo_maquina_entry = QComboBox()
        _poblar_combo_maquinas(self.combo_maquina_entry)
        fila_maquina_entry.addWidget(self.combo_maquina_entry, 1)
        l.addLayout(fila_maquina_entry)
        l.addWidget(QLabel(t("lbl_etiquetas_rapidas")))
        h_tags = QHBoxLayout()
        _crear_checks_etiquetas(self, h_tags)
        l.addLayout(h_tags)
        self.itag = QLineEdit(); self.itag.setPlaceholderText(t("ph_otras_etiquetas")); l.addWidget(self.itag)

        fila_horas_paro_entry = QHBoxLayout()
        fila_horas_paro_entry.addWidget(QLabel(tt("lbl_horas_paro", "Horas de parada (si es avería)") + ":"))
        self.spin_horas_paro_entry = QDoubleSpinBox(); self.spin_horas_paro_entry.setRange(0, 999); self.spin_horas_paro_entry.setDecimals(1)
        self.spin_horas_paro_entry.setSuffix(" h"); self.spin_horas_paro_entry.setEnabled(False)
        self.chk_averia.toggled.connect(self.spin_horas_paro_entry.setEnabled)
        fila_horas_paro_entry.addWidget(self.spin_horas_paro_entry)
        l.addLayout(fila_horas_paro_entry)

        b_save = QPushButton(t("btn_guardar_registro")); b_save.setMinimumHeight(45); b_save.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #2980b9; color: white;"); b_save.clicked.connect(self.save_entry); l.addWidget(b_save); l.addStretch()
        # Dentro de una zona con desplazamiento: en pantallas bajas (o al sacar
        # la ventana de maximizada) el formulario no cabe y, sin ella, Qt lo
        # aprieta por debajo de su tamaño mínimo y los recuadros de las fotos
        # y los botones acaban dibujados unos encima de otros.
        contenido = QWidget(); contenido.setLayout(l)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(contenido)
        l_tab = QVBoxLayout(self.tab_entry); l_tab.setContentsMargins(0, 0, 0, 0); l_tab.addWidget(scroll)

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
        full_desc = con_fotos_galeria(full_desc, self.galeria_entry.nombres())
        lista_tags = _tags_desde_checks(self)
        manuales = self.itag.text().strip()
        if manuales: lista_tags.append(manuales)
        maquina_id = self.combo_maquina_entry.currentData()
        horas_paro = self.spin_horas_paro_entry.value() if self.chk_averia.isChecked() else None
        if self.db.agregar_tarea(d, full_desc, ", ".join(lista_tags), maquina_id=maquina_id, horas_paro=horas_paro):
            self.statusBar().showMessage(t("msg_registro_guardado"), 4000)
            self.ire.clear(); self.idet.clear(); self.itag.clear()
            self.chk_urgente.setChecked(False); self.chk_electrico.setChecked(False)
            self.chk_mecanico.setChecked(False); self.chk_prev.setChecked(False); self.chk_averia.setChecked(False)
            self.combo_maquina_entry.setCurrentIndex(0)
            self.borrar_foto_entry(); self.borrar_foto_entry_d(); self.galeria_entry.set_nombres([]); self.refresh_all(); self.setup_autocompletado()

    def setup_autocompletado(self):
        d = self.db.obtener_todas_las_descripciones()
        c = QCompleter(d, self); c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); c.setFilterMode(Qt.MatchFlag.MatchContains)
        self.ire.setCompleter(c); self.in_todo_t.setCompleter(c)
