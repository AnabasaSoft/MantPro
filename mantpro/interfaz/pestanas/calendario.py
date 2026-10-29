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

"""Pestaña «Calendario» y días especiales."""

import re
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QCalendarWidget, QLabel, QPushButton,
                             QListWidget, QListWidgetItem)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon, QColor, QBrush, QTextCharFormat, QPixmap

from ... import idiomas
from ...idiomas import t
from ..comun import traducir_tags_bd
from ..dialogos.sistema import DialogoDiasEspeciales
from ...nucleo.fotos import _RE_GALERIA

class PestanaCalendario:
    """Pestaña «Calendario» y días especiales.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

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

        for aid, tit, finicio, freq, dur, ult, *_ in self._avisos_visibles():
            if not finicio: continue
            fi = QDate.fromString(finicio, "yyyy-MM-dd")
            if not freq: freq = "Anual"
            freq = idiomas.normalizar_frecuencia(freq)
            # Un aviso "Diario" no necesita ventana: un margen de varios días
            # daría un "rango" confuso para un recordatorio de todos los días.
            dur_ventana = 0 if freq == "Diario" else dur

            def _avanzar_cal(fecha):
                if freq == "Diario": return fecha.addDays(1)
                elif freq == "Semanal": return fecha.addDays(7)
                elif freq == "Mensual": return fecha.addMonths(1)
                elif freq == "Trimestral": return fecha.addMonths(3)
                elif freq == "Semestral": return fecha.addMonths(6)
                elif freq == "Anual": return fecha.addYears(1)
                else: return fecha

            # Misma lógica que en refresh_avisos: la próxima fecha se cuenta
            # desde la última vez que se completó de verdad, no desde el
            # calendario fijo, así que un aviso atrasado se sigue mostrando
            # en cualquier día desde que toca en adelante (no solo en su
            # ventana de margen original).
            if ult:
                fecha_ult = QDate.fromString(ult, "yyyy-MM-dd")
                ocurrencia = _avanzar_cal(fecha_ult) if fecha_ult.isValid() else fi
            else:
                ocurrencia = fi
            ff = ocurrencia.addDays(dur_ventana)

            if ult and sd.toString("yyyy-MM-dd") == ult:
                # El día exacto en que se completó: feedback visual en verde.
                it = QListWidgetItem(f"⚠️ AVISO: {tit} [{t('estado_ok')}]")
                it.setBackground(QColor("#27ae60")); it.setForeground(Qt.GlobalColor.white)
                self.task_list.addItem(it)
            elif sd >= ocurrencia:
                atrasado = sd > ff
                color_bg = "#cb4335" if atrasado else "#e67e22"
                clave_estado = "estado_atrasado" if atrasado else "estado_pendiente"
                it = QListWidgetItem(f"⚠️ AVISO: {tit} [{t(clave_estado)}]")
                it.setBackground(QColor(color_bg)); it.setForeground(Qt.GlobalColor.white)
                self.task_list.addItem(it)

        ts = self.db.obtener_tareas_por_fecha(sds)
        if not ts and self.task_list.count() == 0: self.task_list.addItem(t("msg_dia_no_laborable") if ets else t("msg_nada_registrado"))
        for tarea in ts:
            # --- LIMPIEZA VISUAL COMPLETA ---
            texto_limpio = re.sub(r"\[FOTO:.*?\]", "", tarea[1])
            texto_limpio = re.sub(r"\[FOTO_DESPUES:.*?\]", "", texto_limpio)
            texto_limpio = _RE_GALERIA.sub("", texto_limpio)
            texto_limpio = re.sub(r"\[REF:.*?\]", "", texto_limpio).strip()
            # --------------------------------

            it = QListWidgetItem(f"{texto_limpio} | {traducir_tags_bd(tarea[2])}")
            if self._hay_foto_disponible(tarea[1]):
                # Icono propio (no del tema del sistema): algunos temas de iconos SVG
                # provocan el warning "qt.svg: Invalid path data" con QIcon.fromTheme.
                pm_foto = QPixmap(16, 16); pm_foto.fill(QColor("#3daee9"))
                it.setIcon(QIcon(pm_foto)); it.setToolTip("Tiene foto adjunta")
            it.setData(Qt.ItemDataRole.UserRole, tarea[0])
            self.task_list.addItem(it)

    def init_calendar_tab(self):
        l = QHBoxLayout(); lp = QVBoxLayout(); th = QHBoxLayout()
        th.addWidget(QPushButton(t("btn_ir_hoy"), clicked=self.go_today)); th.addWidget(QPushButton(t("btn_gestion_dias"), clicked=lambda: self.gest_dias()))
        lp.addLayout(th); self.calendar = QCalendarWidget(); self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self.update_calendar_list); lp.addWidget(self.calendar); l.addLayout(lp, 60)
        rp = QVBoxLayout(); self.lbl_info = QLabel(t("lbl_info")); rp.addWidget(self.lbl_info)
        self.task_list = QListWidget(); self.configurar_deseleccion(self.task_list)
        self.task_list.itemDoubleClicked.connect(self.edit_cal); rp.addWidget(self.task_list); l.addLayout(rp, 40); self.tab_calendar.setLayout(l)

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
        for s, tipo_dia in self.db.obtener_dias_especiales().items(): fm = QTextCharFormat(); fm.setBackground(QBrush(QColor(cols.get(tipo_dia, "#555")))); fm.setForeground(QBrush(QColor(tcols.get(tipo_dia, "black")))); self.calendar.setDateTextFormat(QDate.fromString(s, "yyyy-MM-dd"), fm)
        ft = QTextCharFormat(); ft.setBackground(QBrush(QColor("#A5D6A7"))); ft.setForeground(QBrush(Qt.GlobalColor.black)); ft.setFontWeight(750)
        for f in self.db.obtener_fechas_con_tareas(): self.calendar.setDateTextFormat(QDate.fromString(f, "yyyy-MM-dd"), ft)
        self.calendar.setUpdatesEnabled(True)

    def edit_cal(self, i): self.proc_edit(i.data(Qt.ItemDataRole.UserRole))
