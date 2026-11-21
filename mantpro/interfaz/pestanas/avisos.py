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

"""Pestaña «Avisos»: mantenimientos recurrentes."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QDateEdit, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QDialogButtonBox, QAbstractItemView, QComboBox, QGroupBox,
                             QCheckBox, QGridLayout, QSpinBox, QMenu)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor

from ...idiomas import t
from ..comun import tt, combo_frecuencias
from ..dialogos.trabajos import AvisoEditDialog
from ...nucleo import usuarios, checklists, contadores, sedes
from ...nucleo import avisos as avisos_nucleo
from ..dialogos.contadores import CamposContadorAviso, pedir_lectura
from ..dialogos.checklists import llenar_combo_plantillas, rellenar_para

class PestanaAvisos:
    """Pestaña «Avisos»: mantenimientos recurrentes.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def init_avisos_tab(self):
        l = QVBoxLayout()
        self.table_avisos = QTableWidget(0, 6)
        self.configurar_deseleccion(self.table_avisos); self.table_avisos.setHorizontalHeaderLabels([t("hdr_estado"), t("hdr_titulo"), t("hdr_frecuencia"), t("hdr_proxima"), t("hdr_sit"), t("hdr_asignado")])
        self.table_avisos.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_avisos.setColumnWidth(3, 140)
        # Los preventivos por contador llevan más texto («Cada 500 h · Anual»)
        for col in (2, 3): self.table_avisos.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
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
        self.in_av_freq = QComboBox(); combo_frecuencias(self.in_av_freq)   # se guarda la forma canónica (en español)
        f.addWidget(QLabel(t("lbl_repetir")), 1, 0); f.addWidget(self.in_av_freq, 1, 1)
        self.in_av_dur = QSpinBox(); self.in_av_dur.setRange(1, 60); self.in_av_dur.setValue(5); self.in_av_dur.setSuffix(" " + t("lbl_dias_abrev"))
        f.addWidget(QLabel(t("lbl_duracion")), 1, 2); f.addWidget(self.in_av_dur, 1, 3)
        self.in_av_asignar = QComboBox(); self._llenar_combo_usuarios(self.in_av_asignar, incluir_sin_asignar=True)
        f.addWidget(QLabel(tt("lbl_asignar_a", "Asignar a") + ":"), 2, 0); f.addWidget(self.in_av_asignar, 2, 1, 1, 3)
        self.in_av_especialidad = QComboBox(); self._llenar_combo_especialidades(self.in_av_especialidad)
        f.addWidget(QLabel(tt("usuarios_col_especialidad", "Especialidad") + ":"), 3, 0); f.addWidget(self.in_av_especialidad, 3, 1, 1, 3)
        self.in_av_checklist = QComboBox(); llenar_combo_plantillas(self.in_av_checklist)
        f.addWidget(QLabel(tt("lbl_checklist", "Lista de comprobación") + ":"), 4, 0); f.addWidget(self.in_av_checklist, 4, 1, 1, 3)
        self.in_av_contador = CamposContadorAviso(g)
        f.addWidget(self.in_av_contador, 5, 0, 1, 4)
        b = QPushButton(t("btn_anadir_aviso")); b.clicked.connect(self.add_aviso); f.addWidget(b, 6, 0, 1, 4); g.setLayout(f); l.addWidget(g)
        self.grupo_crear_aviso = g
        bl = QHBoxLayout()
        self.btn_editar_aviso = QPushButton(t("btn_editar_seleccionado"), clicked=self.edit_aviso); bl.addWidget(self.btn_editar_aviso)
        self.btn_borrar_aviso = QPushButton(t("btn_borrar_seleccionado"), clicked=self.del_aviso); bl.addWidget(self.btn_borrar_aviso)
        l.addLayout(bl); self.tab_avisos.setLayout(l)

    def add_aviso(self):
        if not usuarios.es_admin(): return
        tit = self.in_av_t.text().strip(); i = self.in_av_i.date().toString("yyyy-MM-dd"); f = self.in_av_freq.currentData(); dur = self.in_av_dur.value()
        uid = self.in_av_asignar.currentData()
        especialidad_id = self.in_av_especialidad.currentData()
        error = self.in_av_contador.validar(self)
        if tit and error:
            QMessageBox.warning(self, t("lbl_crear_nuevo_aviso"), error); return
        try:
            # Lo mismo que hace MantPro Web (nucleo/avisos.py)
            nuevo_id = avisos_nucleo.crear(self.db, usuarios.SESION_ACTUAL, tit, i, f, dur, uid, especialidad_id,
                                           self.in_av_checklist.currentData(), contador=self.in_av_contador.config(),
                                           sede=self.sede_filtro()) if tit else None
        except ValueError:
            nuevo_id = None
        if nuevo_id:
            self.in_av_t.clear(); self.in_av_contador.setChecked(False)
            self.refresh_avisos(); self.update_calendar_list()

    def edit_aviso(self):
        if not usuarios.es_admin(): return
        r = self.table_avisos.currentRow()
        if r < 0: return
        id_aviso = self.table_avisos.item(r, 1).data(Qt.ItemDataRole.UserRole)
        avisos = self.db.obtener_avisos(); datos = next((a for a in avisos if a[0] == id_aviso), None)
        if datos:
            dlg = AvisoEditDialog(self, datos[1], datos[2], datos[3], datos[4], datos[6], datos[8],
                                  checklist_id=checklists.checklist_de("aviso", id_aviso),
                                  contador=contadores.config_aviso(id_aviso),
                                  sede_id=sedes.sede_de("avisos_recurrentes", id_aviso))
            if dlg.exec():
                new_t, new_i, new_f, new_d, new_uid, _nombre, new_especialidad = dlg.get_data()
                try:
                    avisos_nucleo.editar(self.db, usuarios.SESION_ACTUAL, id_aviso, new_t, new_i, new_f, new_d, new_uid,
                                         new_especialidad, checklist_id=dlg.checklist_id(), contador=dlg.contador(),
                                         sede_id=dlg.sede_elegida())
                except ValueError:
                    return
                self.refresh_avisos(); self.update_calendar_list()

    def _avisos_visibles(self):
        """Los avisos de la sede elegida que ve el usuario (el calendario también los usa)."""
        return avisos_nucleo.visibles(self.db.obtener_avisos(sede=self.sede_filtro()), usuarios.SESION_ACTUAL)

    def refresh_avisos(self):
        """La tabla la calcula el núcleo (nucleo/avisos.py), igual que en MantPro Web: el admin ve todos los
        avisos; cada trabajador, los suyos y los sin asignar de sus especialidades (o sin ninguna)."""
        self.table_avisos.setRowCount(0)
        es_admin = usuarios.es_admin()
        if hasattr(self, 'grupo_crear_aviso'): self.grupo_crear_aviso.setEnabled(es_admin)
        if hasattr(self, 'btn_editar_aviso'): self.btn_editar_aviso.setEnabled(es_admin)
        if hasattr(self, 'btn_borrar_aviso'): self.btn_borrar_aviso.setEnabled(es_admin)
        if hasattr(self, 'in_av_checklist'):
            llenar_combo_plantillas(self.in_av_checklist, self.in_av_checklist.currentData())
        if hasattr(self, 'in_av_contador') and not self.in_av_contador.isChecked():
            self.in_av_contador._llenar(None)   # por si hay contadores nuevos
        filas = avisos_nucleo.lista(self.db, usuarios.SESION_ACTUAL, sede=self.sede_filtro())
        self.table_avisos.setRowCount(len(filas))
        for r, f in enumerate(filas):
            aid, tit = f["id"], f["titulo"]
            clave, color, _ = avisos_nucleo.ESTADOS[f["estado"]]
            cw = QWidget()
            cl = QHBoxLayout(cw); cl.setContentsMargins(0,0,0,0); cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(f["completado"])
            chk.toggled.connect(lambda k, x=aid, t=tit: self.tog_aviso(x, k, t))
            chk.setEnabled(f["activo"] or f["completado"])
            cl.addWidget(chk)
            self.table_avisos.setCellWidget(r, 0, cw)

            item_t = QTableWidgetItem(avisos_nucleo.titulo_en_tabla(f))
            item_t.setData(Qt.ItemDataRole.UserRole, aid)
            if f["lista"]: item_t.setToolTip("☑️ " + f["lista"])
            self.table_avisos.setItem(r, 1, item_t)
            item_f = QTableWidgetItem(f["texto_frecuencia"])
            if f["consejo"]: item_f.setToolTip(f["consejo"])
            self.table_avisos.setItem(r, 2, item_f)
            item_r = QTableWidgetItem(f["rango"])
            if f["consejo"]: item_r.setToolTip(f["consejo"])
            self.table_avisos.setItem(r, 3, item_r)
            item_estado = QTableWidgetItem(t(clave))
            item_estado.setForeground(QColor(color))
            self.table_avisos.setItem(r, 4, item_estado)
            self.table_avisos.setItem(r, 5, QTableWidgetItem(f["asignado_nombre"] or tt("lbl_sin_asignar", "Sin asignar")))

    def tog_aviso(self, id_aviso, estado, titulo):
        """La casilla de la tabla: marcarla apunta el preventivo de hoy en el historial (antes, la lista de
        comprobación y la lectura del contador, si tiene); desmarcarla lo deshace. Lo hace el núcleo
        (nucleo/avisos.py), igual que MantPro Web y la app MantPro."""
        if estado:
            # Con lista de comprobación: se rellena antes de completarlo; si se cancela, el aviso queda como estaba.
            clave_borrador = checklists.clave_borrador("aviso", id_aviso)
            lista = rellenar_para(self, checklists.checklist_de("aviso", id_aviso), titulo, clave_borrador)
            if lista is None:
                self.refresh_avisos()
                return
            # Por contador: lectura en el momento de hacerlo (de ella se cuenta el siguiente). Opcional; cancelar
            # deja el aviso como estaba.
            info = contadores.config_aviso(id_aviso)
            lectura = None
            if info:
                contador = {"nombre": info["contador"], "maquina": info["maquina"], "unidad": info["unidad"],
                            "actual": info["actual"], "fecha_actual": info["fecha_actual"]}
                ok, lectura = pedir_lectura(self, contador, titulo, tt(
                    "lbl_lectura_al_completar", "Lectura del contador al hacer el preventivo:"), opcional=True)
                if not ok:
                    self.refresh_avisos()
                    return
            # Con la fecha real de HOY (no la que tocaba): el siguiente ciclo se cuenta desde cuándo se ha hecho
            try:
                avisos_nucleo.completar(self.db, usuarios.SESION_ACTUAL, id_aviso, lista=lista if lista[0] else None,
                                        valor_lectura=lectura)
                self.statusBar().showMessage(t("msg_guardado_historial").format(titulo=titulo), 3000)
            except ValueError as e:
                print(f"No se ha podido completar el aviso: {e}")
        else:
            try:
                avisos_nucleo.descompletar(self.db, usuarios.SESION_ACTUAL, id_aviso)
                self.statusBar().showMessage(t("msg_eliminado_historial").format(titulo=titulo), 3000)
            except ValueError as e:
                print(f"No se ha podido deshacer el aviso: {e}")

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
            try:
                avisos_nucleo.borrar(self.db, usuarios.SESION_ACTUAL, ids)
            except ValueError:
                pass
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

        mantener = avisos_nucleo.MANTENER
        try:
            avisos_nucleo.reasignar(self.db, usuarios.SESION_ACTUAL, ids,
                                    asignado_id=combo.currentData() if chk_tecnico.isChecked() else mantener,
                                    especialidad_id=combo_esp.currentData() if chk_especialidad.isChecked() else mantener)
        except ValueError:
            pass
        self.refresh_avisos()
