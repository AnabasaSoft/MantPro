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
from ..comun import tt
from ..dialogos.trabajos import CompleteDialog, DialogoEditarPendiente
from ..widgets.fotos import GaleriaFotosWidget
from ...nucleo import usuarios, checklists, sedes
from ...nucleo import pendientes as pendientes_nucleo
from ..dialogos.checklists import llenar_combo_plantillas, rellenar_para
from ...nucleo.fotos import fotos_galeria

class PestanaPendientes:
    """Pestaña «Pendientes»: trabajos por hacer.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def init_todo_tab(self):
        operario = usuarios.es_operario()
        l = QHBoxLayout(); ll = QVBoxLayout()
        ll.addWidget(QLabel(t("lbl_pendientes_avisados") if operario else t("lbl_lista_pendientes")))
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
        fila_checklist_todo = QHBoxLayout()
        fila_checklist_todo.addWidget(QLabel(tt("lbl_checklist", "Lista de comprobación") + ":"))
        self.combo_checklist_todo = QComboBox()
        llenar_combo_plantillas(self.combo_checklist_todo)
        fila_checklist_todo.addWidget(self.combo_checklist_todo, 1)
        f.addLayout(fila_checklist_todo)
        self.galeria_todo = GaleriaFotosWidget(self.carpeta_fotos, self)
        f.addWidget(self.galeria_todo)
        f.addWidget(QPushButton(t("btn_anadir"), clicked=self.add_todo)); g.setLayout(f); rl.addWidget(g)
        self.grupo_nuevo_todo = g          # sin él para un usuario solo de almacén (no crea pendientes)
        ga = QGroupBox(t("lbl_acciones")); fa = QVBoxLayout()
        b_ok = QPushButton(t("btn_completar"), clicked=self.complete_todo); b_ok.setStyleSheet("background-color:#27ae60; color: white;"); fa.addWidget(b_ok)
        b_edit = QPushButton(t("btn_editar"), clicked=self.edit_todo); b_edit.setStyleSheet("background-color:#2980b9; color: white;"); fa.addWidget(b_edit)
        b_del = QPushButton(t("btn_eliminar"), clicked=self.del_todo); b_del.setStyleSheet("background-color:#c0392b; color: white;"); fa.addWidget(b_del)
        self.b_asig_todo = QPushButton(tt("btn_reasignar", "👤 Reasignar"), clicked=self.reasignar_todo)
        self.b_asig_todo.setStyleSheet("background-color:#8e44ad; color: white;"); fa.addWidget(self.b_asig_todo)
        ga.setLayout(fa); rl.addWidget(ga); l.addLayout(rl, 40); self.tab_todo.setLayout(l)
        if operario:
            # Un operario solo avisa: sin filtro, sin asignar técnico ni lista, y sin acciones sobre la lista
            # (ve los que ha avisado él; los gestiona un técnico o un administrador)
            for fila in (fila_filtro, fila_asig, fila_checklist_todo):
                for i in range(fila.count()):
                    if fila.itemAt(i).widget():
                        fila.itemAt(i).widget().hide()
            ga.hide()
            g.setTitle(t("lbl_avisar_pendiente"))
            self.todo_list.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            self.todo_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

    def add_todo(self):
        tit, d = self.in_todo_t.text().strip(), self.in_todo_d.toPlainText().strip()
        try:
            # Lo mismo que hace MantPro Web (nucleo/pendientes.py)
            nuevo_id = pendientes_nucleo.crear(self.db, usuarios.SESION_ACTUAL, tit, d, self.combo_asignar.currentData(),
                                               self.combo_prioridad_todo.currentData(), self.combo_especialidad_todo.currentData(),
                                               self.combo_checklist_todo.currentData(), sede=self.sede_filtro(),
                                               fotos=self.galeria_todo.nombres())
        except ValueError:
            nuevo_id = None
        if nuevo_id:
            self.combo_checklist_todo.setCurrentIndex(0)
            self.in_todo_t.clear(); self.in_todo_d.clear(); self.galeria_todo.set_nombres([]); self.combo_prioridad_todo.setCurrentIndex(1); self.refresh_todos()
            if hasattr(self, 'servidor') and self.servidor:
                self.servidor.pendiente_actualizado.emit()

    def reasignar_todo(self):
        """Cambia el técnico asignado y/o la especialidad del pendiente seleccionado.
        Solo un admin puede modificar la asignación/especialidad de un trabajo ya
        existente; un técnico solo puede fijarlas al crear el trabajo."""
        if usuarios.es_operario():
            return
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

        try:
            ok = pendientes_nucleo.reasignar(self.db, usuarios.SESION_ACTUAL, [pid], asignado_id=combo.currentData(),
                                             especialidad_id=combo_esp.currentData())
        except ValueError:
            ok = False
        if ok:
            self.refresh_todos()
            if hasattr(self, 'servidor') and self.servidor:
                self.servidor.pendiente_actualizado.emit()

    def _menu_contextual_todos(self, pos):
        """Menú con clic derecho sobre la lista de trabajos: eliminar o asignar
        técnico/especialidad a varios trabajos a la vez."""
        if usuarios.es_operario():
            return
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
            try:
                pendientes_nucleo.borrar(self.db, usuarios.SESION_ACTUAL, ids)
            except ValueError:
                pass
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

        mantener = pendientes_nucleo.MANTENER
        try:
            pendientes_nucleo.reasignar(self.db, usuarios.SESION_ACTUAL, ids,
                                        asignado_id=combo.currentData() if chk_tecnico.isChecked() else mantener,
                                        especialidad_id=combo_esp.currentData() if chk_especialidad.isChecked() else mantener)
        except ValueError:
            return
        self.refresh_todos()
        if hasattr(self, 'servidor') and self.servidor:
            self.servidor.pendiente_actualizado.emit()

    def refresh_todos(self, *_):
        self.todo_list.clear()
        if hasattr(self, 'grupo_nuevo_todo'):
            self.grupo_nuevo_todo.setVisible(usuarios.puede_avisar_pendientes())
        if usuarios.es_operario():
            # Lo único que ve un operario: los pendientes que ha avisado él y siguen sin hacer
            filas = pendientes_nucleo.avisados_por(self.db, usuarios.SESION_ACTUAL)
            if not filas:
                self.todo_list.addItem(t("msg_sin_pendientes_avisados"))
            for fila in filas:
                texto = f"{pendientes_nucleo.ICONOS.get(fila['prioridad'], '⬜')} {fila['titulo']}"
                if fila["detalles"]:
                    texto += f"\n   ↳ {fila['detalles']}"
                if fila["especialidad"]:
                    texto += f"\n   🔧 {fila['especialidad']}"
                self.todo_list.addItem(QListWidgetItem(texto))
            return
        if hasattr(self, 'b_asig_todo'):
            self.b_asig_todo.setEnabled(usuarios.es_admin())
        # Lo que se lista, su orden y su texto salen del núcleo (lo mismo que enseña MantPro Web)
        filtro = self.combo_filtro_todos.currentData() if hasattr(self, 'combo_filtro_todos') else pendientes_nucleo.TODOS
        filas = pendientes_nucleo.lista(self.db, sede=self.sede_filtro(), asignado=filtro, carpeta_fotos=self.carpeta_fotos)
        if not filas:
            self.todo_list.addItem(t("msg_nada"))
        if hasattr(self, 'combo_checklist_todo'):
            llenar_combo_plantillas(self.combo_checklist_todo, self.combo_checklist_todo.currentData())
        for fila in filas:
            it = QListWidgetItem(pendientes_nucleo.texto(fila))
            # Los datos originales (con las marcas de foto y referencia) van por debajo, para la lógica
            it.setData(Qt.ItemDataRole.UserRole, fila["id"])
            it.setData(Qt.ItemDataRole.UserRole + 1, fila["titulo"])
            it.setData(Qt.ItemDataRole.UserRole + 2, fila["descripcion"])
            it.setData(Qt.ItemDataRole.UserRole + 3, fila["asignado_id"])
            it.setData(Qt.ItemDataRole.UserRole + 4, fila["prioridad"])
            it.setData(Qt.ItemDataRole.UserRole + 5, fila["especialidad_id"])
            if fila["tiene_foto"]:
                it.setToolTip("📸 Tiene foto adjunta")
            self.todo_list.addItem(it)

    def del_todo(self):
        if usuarios.es_operario():
            return
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
                    try:
                        pendientes_nucleo.borrar(self.db, usuarios.SESION_ACTUAL, [i])
                    except ValueError:
                        pass
                    self.refresh_todos()

    def complete_todo(self):
        if usuarios.es_operario():
            return
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
            # Con lista de comprobación: se rellena antes de pasarlo al
            # historial; si se cancela, el pendiente sigue como estaba.
            clave_borrador = checklists.clave_borrador("pendiente", id_pendiente)
            lista = rellenar_para(self, checklists.checklist_de("pendiente", id_pendiente), titulo, clave_borrador)
            if lista is None:
                self.refresh_todos()       # la marca 📝 de la lista a medias
                return

            # Pasarlo al historial lo hace el núcleo, igual que en MantPro Web: la foto nueva sustituye
            # a la anterior y la colección del diálogo (que ya incluye la que traía) a la marca de antes
            try:
                tarea_id = pendientes_nucleo.completar(
                    self.db, usuarios.SESION_ACTUAL, id_pendiente, fecha, tags, repuestos=dialogo.repuestos.items(),
                    minutos=dialogo.tiempo.minutos(), personas=dialogo.tiempo.personas(), lista=lista,
                    foto=os.path.basename(foto_nueva) if foto_nueva else None, fotos=fotos_coleccion)
            except ValueError:
                tarea_id = None
            if tarea_id:
                self.refresh_todos()
                self.refresh_all()
                self.statusBar().showMessage(t("msg_tarea_completada").format(titulo=titulo), 5000)

    def edit_todo(self, item=None): # Añadimos argumento opcional para el doble click
        if usuarios.es_operario():
            return
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

        if detalles_raw:
            # 1. Detectar FOTO
            m = re.search(r"\[FOTO:\s*(.*?)\]", detalles_raw)
            if m:
                nombre_fichero = m.group(1).split("]")[0].strip()
                ruta_posible = os.path.join(self.carpeta_fotos, nombre_fichero)
                if os.path.exists(ruta_posible):
                    ruta_foto_actual = ruta_posible

            # 2. El texto sin las marcas (la referencia del móvil y las fotos las conserva el núcleo al guardar)
            texto_limpio = pendientes_nucleo.detalles_visibles(detalles_raw)

        # Abrimos el diálogo con el texto LIMPIO
        dlg = DialogoEditarPendiente(self, titulo_actual, texto_limpio, ruta_foto_actual, prioridad_actual, asignado_actual_id, especialidad_actual_id,
                                     fotos_coleccion=fotos_galeria(detalles_raw),
                                     checklist_id=checklists.checklist_de("pendiente", pid),
                                     sede_id=sedes.sede_de("pendientes", pid))

        if dlg.exec():
            nuevo_t, nuevo_d, nueva_foto, nueva_prioridad, nuevo_asignado_id, nuevo_asignado_nombre, nueva_especialidad_id, fotos_coleccion = dlg.get_data()

            # La foto nueva se copia a la carpeta de fotos; el resto (conservar la referencia y la foto de
            # después, quién puede reasignar, comprobar lo elegido) lo hace el núcleo, igual que en MantPro Web
            nombre_final = None
            if nueva_foto:
                nombre_final = os.path.basename(nueva_foto)
                if nueva_foto != ruta_foto_actual:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    nombre_final = f"pc_edit_{ts}_{nombre_final}"
                    destino = os.path.join(self.carpeta_fotos, nombre_final)
                    try: shutil.copy2(nueva_foto, destino)
                    except: pass
            try:
                guardado = pendientes_nucleo.editar(
                    self.db, usuarios.SESION_ACTUAL, pid, nuevo_t, nuevo_d, nueva_prioridad,
                    asignado_id=nuevo_asignado_id, especialidad_id=nueva_especialidad_id, checklist_id=dlg.checklist_id(),
                    sede_id=dlg.sede_elegida(), foto=nombre_final, fotos=fotos_coleccion)
            except ValueError:
                guardado = False
            if guardado:
                self.refresh_todos()
                self.statusBar().showMessage(t("msg_pendiente_actualizado"), 3000)
