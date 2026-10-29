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

"""Pestaña «Avisos»: mantenimientos recurrentes."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QDateEdit, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QDialogButtonBox, QAbstractItemView, QComboBox, QGroupBox,
                             QCheckBox, QGridLayout, QSpinBox, QMenu)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..dialogos.trabajos import AvisoEditDialog
from ...nucleo import usuarios
from ...nucleo.basedatos import get_db_connection

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
        self.in_av_dur = QSpinBox(); self.in_av_dur.setRange(1, 60); self.in_av_dur.setValue(5); self.in_av_dur.setSuffix(" " + t("lbl_dias_abrev"))
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

            # Un aviso "Diario" no necesita ventana: un margen de varios días
            # daría un "rango" confuso para un recordatorio que es de todos
            # los días.
            dur_ventana = 0 if freq == "Diario" else dur

            def _avanzar(fecha):
                if freq == "Diario": return fecha.addDays(1)
                elif freq == "Semanal": return fecha.addDays(7)
                elif freq == "Mensual": return fecha.addMonths(1)
                elif freq == "Trimestral": return fecha.addMonths(3)
                elif freq == "Semestral": return fecha.addMonths(6)
                elif freq == "Anual": return fecha.addYears(1)
                else: return fecha

            # La fecha en que toca la próxima vez se cuenta desde la ÚLTIMA VEZ
            # QUE SE HIZO DE VERDAD (ult), no desde el calendario fijo original.
            # Así, si te retrasas, el aviso se queda en "Pendiente" (no salta al
            # ciclo siguiente sin más) hasta que lo completas, y en cuanto lo
            # haces, el siguiente se cuenta a partir de ese día real.
            if ult:
                fecha_ult = QDate.fromString(ult, "yyyy-MM-dd")
                ocurrencia = _avanzar(fecha_ult) if fecha_ult.isValid() else fi
            else:
                ocurrencia = fi

            fin_ocurrencia = ocurrencia.addDays(dur_ventana)
            s_inicio = ocurrencia.toString("yyyy-MM-dd")

            # Completado "para hoy" solo si se hizo justo hoy: evita que un
            # aviso quede marcado en verde permanentemente por una fecha
            # antigua, ya que ahora esa fecha es la que decide cuándo toca el
            # siguiente, no si el ciclo actual está "hecho".
            completado = (ult == hoy.toString("yyyy-MM-dd"))
            es_activo = hoy >= ocurrencia
            # Distinguimos "toca ahora" (dentro del margen configurado) de
            # "se ha pasado ese margen sin hacerlo" (atrasado).
            es_atrasado = hoy > fin_ocurrencia

            if completado:
                color = QColor("#27ae60") # Verde
                estado_txt = t("estado_ok")
                prioridad = 3
            elif es_atrasado:
                color = QColor("#cb4335") # Rojo (atrasado)
                estado_txt = t("estado_atrasado")
                prioridad = 0  # Atrasado: lo más urgente, va primero
            elif es_activo:
                color = QColor("#e67e22") # Naranja (toca ahora, dentro del margen)
                estado_txt = t("estado_pendiente")
                prioridad = 1
            else:
                color = QColor("#2e86c1") # Azul (futuro)
                estado_txt = t("estado_futuro")
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
            chk.toggled.connect(lambda k, x=aid, t=tit: self.tog_aviso(x, k, t))
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

    def tog_aviso(self, id_aviso, estado, titulo):
        desc_historial = f"Mantenimiento Preventivo: {titulo}"

        if estado:
            # MARCADO -> se completa con la fecha real de HOY (no la fecha que
            # tocaba): así el siguiente ciclo se cuenta a partir de cuándo se
            # ha hecho el trabajo de verdad, no de cuándo estaba programado.
            hoy = QDate.currentDate().toString("yyyy-MM-dd")
            self.db.marcar_aviso_completado(id_aviso, hoy, True)
            tags = "Preventivo, Aviso Recurrente"
            self.db.agregar_tarea(hoy, desc_historial, tags)
            self.statusBar().showMessage(t("msg_guardado_historial").format(titulo=titulo), 3000)
        else:
            # DESMARCADO -> averiguamos qué fecha tenía registrada para borrar
            # justo esa entrada del historial, y restauramos como "última
            # completada" la vez anterior a esa (si la hay) en vez de dejarlo
            # siempre en "nunca", igual que ya hace la API para el móvil.
            avisos = self.db.obtener_avisos()
            datos = next((a for a in avisos if a[0] == id_aviso), None)
            fecha_actual = datos[5] if datos else None
            try:
                with get_db_connection(self.db.db_name) as conn:
                    c = conn.cursor()
                    if fecha_actual:
                        c.execute("DELETE FROM tareas WHERE fecha=? AND descripcion=?", (fecha_actual, desc_historial))
                    c.execute("SELECT MAX(fecha) FROM tareas WHERE descripcion=?", (desc_historial,))
                    prev_fecha = c.fetchone()[0]
                    conn.commit()
                self.db.marcar_aviso_completado(id_aviso, prev_fecha, prev_fecha is not None)
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
