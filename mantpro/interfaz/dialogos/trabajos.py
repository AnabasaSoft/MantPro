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

"""Diálogos de trabajos, pendientes, avisos y exportación."""

import os
import shutil
import re
from datetime import datetime
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
                             QDateEdit, QMessageBox, QDialog, QDialogButtonBox, QComboBox,
                             QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QRadioButton)
from PyQt6.QtCore import QDate, Qt, QSettings
from PyQt6.QtGui import QPixmap

from ... import idiomas
from ...idiomas import t
from ..comun import (_crear_checks_etiquetas, _estilo_label_dialogo, _estilo_zona_arrastre,
                     _poblar_combo_maquinas, _tags_desde_checks, tt)
from ..widgets.fotos import DialogoSelectorFoto, GaleriaFotosWidget, LabelArrastrable, VisorFoto
from ...nucleo import usuarios
from ...nucleo.fotos import con_fotos_galeria, fotos_galeria, quitar_marcas_foto

class EditDialog(QDialog):
    def __init__(self, parent=None, fecha="", desc="", tags="", usuario_id=None, usuario_nombre="", maquina_id=None, horas_paro=None):
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
        self.galeria = GaleriaFotosWidget(self.carpeta_fotos, self, self.fotos_galeria_iniciales)
        l.addWidget(self.galeria)
        l.addWidget(QLabel(t("lbl_etiquetas")))
        h_tags = QHBoxLayout()
        _crear_checks_etiquetas(self, h_tags)
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
        l.addLayout(h_tags)
        texto_manual = ", ".join([x for x in tags.split(',') if x.strip().lower() in lista_actual])
        self.tag = QLineEdit(); self.tag.setText(texto_manual); self.tag.setPlaceholderText(t("ph_otros_tags"))
        l.addWidget(self.tag)

        # --- Horas de parada (para MTBF/MTTR) ---
        fila_horas_paro = QHBoxLayout()
        fila_horas_paro.addWidget(QLabel(tt("lbl_horas_paro", "Horas de parada (si es avería)") + ":"))
        self.spin_horas_paro = QDoubleSpinBox(); self.spin_horas_paro.setRange(0, 999); self.spin_horas_paro.setDecimals(1)
        self.spin_horas_paro.setSuffix(" h"); self.spin_horas_paro.setEnabled(self.chk_averia.isChecked())
        if horas_paro is not None: self.spin_horas_paro.setValue(horas_paro)
        self.chk_averia.toggled.connect(self.spin_horas_paro.setEnabled)
        fila_horas_paro.addWidget(self.spin_horas_paro)
        l.addLayout(fila_horas_paro)

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def separar_datos(self, texto):
        self.fotos_galeria_iniciales = fotos_galeria(texto)
        texto = con_fotos_galeria(texto, [])
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
        d = con_fotos_galeria(d, self.galeria.nombres())
        final_tags = _tags_desde_checks(self)
        manual = self.tag.text().strip()
        if manual: final_tags.append(manual)
        usuario_id = self.combo_autor.currentData()
        usuario_nombre = self.combo_autor.currentText() if usuario_id is not None else usuarios.ETIQUETA_HISTORICO
        maquina_id = self.combo_maquina.currentData()
        horas_paro = self.spin_horas_paro.value() if self.chk_averia.isChecked() else None
        return (self.de.date().toString("yyyy-MM-dd"), d, ", ".join(final_tags), usuario_id, usuario_nombre, maquina_id, horas_paro)


class DialogoEditarPendiente(QDialog):
    def __init__(self, parent=None, titulo="", detalles="", ruta_foto="", prioridad="Media", asignado_a=None, especialidad_id=None, fotos_coleccion=None):
        super().__init__(parent)
        self.setWindowTitle(t("title_editar_tarea_pendiente"))
        self.fotos_coleccion_iniciales = fotos_coleccion or []
        self.resize(550, 700)
        self.ruta_foto_seleccionada = ruta_foto
        l = QVBoxLayout()
        l.addWidget(QLabel(t("lbl_titulo"))); self.t = QLineEdit(titulo); l.addWidget(self.t)
        l.addWidget(QLabel(t("lbl_detalles"))); self.d = QTextEdit(); self.d.setText(detalles); self.d.setMaximumHeight(100); l.addWidget(self.d)
        fila_prioridad = QHBoxLayout()
        fila_prioridad.addWidget(QLabel(tt("lbl_prioridad", "Prioridad") + ":"))
        self.combo_prioridad = QComboBox()
        if parent is not None and hasattr(parent, "_llenar_combo_prioridad"):
            parent._llenar_combo_prioridad(self.combo_prioridad, prioridad)
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
        self.galeria = GaleriaFotosWidget(parent.carpeta_fotos if parent is not None else "", self, self.fotos_coleccion_iniciales)
        l.addWidget(self.galeria)
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
                self.combo_prioridad.currentData(), uid, nombre, especialidad_id, self.galeria.nombres())


class CompleteDialog(QDialog):
    def __init__(self, parent=None, titulo="", detalles=""):
        super().__init__(parent)
        self.carpeta_fotos = parent.carpeta_fotos if parent else ""
        self.foto_filename = None
        self.setWindowTitle(f"Completar: {titulo}"); self.resize(500, 550); l = QVBoxLayout()
        oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
        lbl_info = QLabel(f"<b>Trabajo:</b> {titulo}<br><i>{quitar_marcas_foto(detalles)}</i>"); lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("background-color: #333; padding: 10px; border-radius: 5px; color: #eee;" if oscuro
                                else "background-color: #eee; padding: 10px; border-radius: 5px; color: #333;")
        l.addWidget(lbl_info)
        l.addWidget(QLabel(t("lbl_fecha_finalizacion"))); self.de = QDateEdit(); self.de.setDate(QDate.currentDate()); self.de.setCalendarPopup(True); self.de.setDisplayFormat("yyyy-MM-dd"); l.addWidget(self.de)
        self.lbl_foto = LabelArrastrable(); self.lbl_foto.setFixedHeight(180); self.lbl_foto.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_foto.mousePressEvent = self.click_foto; self.lbl_foto.archivo_soltado.connect(self.procesar_foto); l.addWidget(self.lbl_foto)
        btn = QPushButton(t("btn_buscar_foto_manual")); btn.clicked.connect(self.buscar_foto); l.addWidget(btn)
        l.addWidget(QLabel(t("lbl_etiquetas_rapidas"))); h_tags = QHBoxLayout()
        _crear_checks_etiquetas(self, h_tags, incluir_averia=False)
        l.addLayout(h_tags)
        l.addWidget(QLabel(t("lbl_otros_tags"))); self.tag = QLineEdit(); self.tag.setPlaceholderText(t("ph_ejemplo_tags")); l.addWidget(self.tag)
        self.galeria = GaleriaFotosWidget(self.carpeta_fotos, self, fotos_galeria(detalles))
        l.addWidget(self.galeria)
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
        lista_tags = _tags_desde_checks(self, incluir_averia=False)
        manual = self.tag.text().strip(); (lista_tags.append(manual) if manual else None)
        return (self.de.date().toString("yyyy-MM-dd"), ", ".join(lista_tags), self.foto_filename, self.galeria.nombres())


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


class DialogoTiempoGuardado(QDialog):
    """Pide cuánto tiempo hacia atrás (desde hoy) se conservan los trabajos
    del historial: un número y una unidad (años, meses o días)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_tiempo_guardado", "Tiempo máximo de guardado de trabajos"))
        l = QVBoxLayout()
        lbl = QLabel(tt("lbl_tiempo_guardado", "Conservar los trabajos de los últimos:"))
        lbl.setWordWrap(True); l.addWidget(lbl)
        fila = QHBoxLayout()
        self.spin = QSpinBox(); self.spin.setRange(1, 999); self.spin.setValue(5)
        self.combo = QComboBox()
        self.combo.addItem(tt("unidad_anos", "años"), "anos")
        self.combo.addItem(tt("unidad_meses", "meses"), "meses")
        self.combo.addItem(tt("unidad_dias", "días"), "dias")
        fila.addWidget(self.spin); fila.addWidget(self.combo, 1)
        l.addLayout(fila)
        self.lbl_corte = QLabel(); self.lbl_corte.setWordWrap(True); self.lbl_corte.setStyleSheet("color: #c0392b;")
        l.addWidget(self.lbl_corte)
        self.spin.valueChanged.connect(self._actualizar); self.combo.currentIndexChanged.connect(self._actualizar)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)
        self._actualizar()

    def fecha_corte(self):
        """Primer día que se conserva: se borra todo lo anterior a esta fecha."""
        n, hoy = self.spin.value(), QDate.currentDate()
        unidad = self.combo.currentData()
        if unidad == "anos": return hoy.addYears(-n)
        if unidad == "meses": return hoy.addMonths(-n)
        return hoy.addDays(-n)

    def _actualizar(self):
        corte = idiomas.formato_fecha_localizada(self.fecha_corte().toString("yyyy-MM-dd"))
        self.lbl_corte.setText(tt("lbl_se_borrara_antes_de", "Se borrarán los trabajos anteriores al {fecha}.").format(fecha=corte))
