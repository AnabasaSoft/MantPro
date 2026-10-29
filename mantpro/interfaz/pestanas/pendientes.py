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

"""Pestaña «Pendientes»: trabajos por hacer."""

import os
import shutil
import re
from datetime import datetime
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
                             QListWidget, QMessageBox, QDialog, QDialogButtonBox, QAbstractItemView,
                             QListWidgetItem, QComboBox, QGroupBox, QCheckBox, QMenu)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import traducir_prioridad, tt
from ..dialogos.trabajos import CompleteDialog, DialogoEditarPendiente
from ..widgets.fotos import GaleriaFotosWidget
from ...nucleo import usuarios
from ...nucleo.fotos import con_fotos_galeria, fotos_galeria

class PestanaPendientes:
    """Pestaña «Pendientes»: trabajos por hacer.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

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
        self._llenar_combo_prioridad(self.combo_prioridad_todo)
        fila_prioridad_todo.addWidget(self.combo_prioridad_todo, 1)
        f.addLayout(fila_prioridad_todo)
        self.galeria_todo = GaleriaFotosWidget(self.carpeta_fotos, self)
        f.addWidget(self.galeria_todo)
        f.addWidget(QPushButton(t("btn_anadir"), clicked=self.add_todo)); g.setLayout(f); rl.addWidget(g)
        ga = QGroupBox(t("lbl_acciones")); fa = QVBoxLayout()
        b_ok = QPushButton(t("btn_completar"), clicked=self.complete_todo); b_ok.setStyleSheet("background-color:#27ae60; color: white;"); fa.addWidget(b_ok)
        b_edit = QPushButton(t("btn_editar"), clicked=self.edit_todo); b_edit.setStyleSheet("background-color:#2980b9; color: white;"); fa.addWidget(b_edit)
        b_del = QPushButton(t("btn_eliminar"), clicked=self.del_todo); b_del.setStyleSheet("background-color:#c0392b; color: white;"); fa.addWidget(b_del)
        self.b_asig_todo = QPushButton(tt("btn_reasignar", "👤 Reasignar"), clicked=self.reasignar_todo)
        self.b_asig_todo.setStyleSheet("background-color:#8e44ad; color: white;"); fa.addWidget(self.b_asig_todo)
        ga.setLayout(fa); rl.addWidget(ga); l.addLayout(rl, 40); self.tab_todo.setLayout(l)

    def add_todo(self):
        tit, d = self.in_todo_t.text().strip(), self.in_todo_d.toPlainText().strip()
        d = con_fotos_galeria(d, self.galeria_todo.nombres())
        uid = self.combo_asignar.currentData()
        nombre = self.combo_asignar.currentText() if uid is not None else None
        prioridad = self.combo_prioridad_todo.currentData()
        especialidad_id = self.combo_especialidad_todo.currentData()
        if tit and self.db.agregar_pendiente(tit, d, uid, nombre, prioridad, especialidad_id):
            self.in_todo_t.clear(); self.in_todo_d.clear(); self.galeria_todo.set_nombres([]); self.combo_prioridad_todo.setCurrentIndex(1); self.refresh_todos()
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

        # Usamos la nueva clase de diálogo
        dialogo = CompleteDialog(self, titulo, detalles_originales)

        if dialogo.exec():
            fecha, tags, foto_nueva, fotos_coleccion = dialogo.get_data()

            # --- MEJORA: LIMPIEZA INTELIGENTE ---
            detalles_limpios = detalles_originales
            # Si el usuario ha elegido una FOTO NUEVA, borramos la etiqueta de la vieja del texto
            if foto_nueva and detalles_originales:
                 detalles_limpios = re.sub(r"\[FOTO:.*?\]", "", detalles_originales).strip()
            # ------------------------------------

            desc_final = titulo
            if detalles_limpios: desc_final += f"\n{detalles_limpios}"
            if foto_nueva: desc_final += f"\n[FOTO: {os.path.basename(foto_nueva)}]"
            # La colección del diálogo ya incluye la que traía el pendiente (si
            # venía de revertir un trabajo): sustituye a la marca anterior.
            desc_final = con_fotos_galeria(desc_final, fotos_coleccion)

            # Guardar en Historial y borrar de Pendientes
            if self.db.agregar_tarea(fecha, desc_final, tags):
                self.db.borrar_pendiente(id_pendiente)
                self.refresh_todos()
                self.refresh_all()
                self.statusBar().showMessage(t("msg_tarea_completada").format(titulo=titulo), 5000)

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
        dlg = DialogoEditarPendiente(self, titulo_actual, texto_limpio, ruta_foto_actual, prioridad_actual, asignado_actual_id, especialidad_actual_id,
                                     fotos_coleccion=fotos_galeria(detalles_raw))

        if dlg.exec():
            nuevo_t, nuevo_d, nueva_foto, nueva_prioridad, nuevo_asignado_id, nuevo_asignado_nombre, nueva_especialidad_id, fotos_coleccion = dlg.get_data()

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
                # La foto de después (p. ej. de un trabajo revertido) no se edita
                # aquí, pero no se debe perder.
                m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", detalles_raw or "")
                if m_d: desc_final += f"\n[FOTO_DESPUES: {m_d.group(1).strip()}]"
                desc_final = con_fotos_galeria(desc_final, fotos_coleccion)

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
