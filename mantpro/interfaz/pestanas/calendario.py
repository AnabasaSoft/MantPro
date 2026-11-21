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

"""Pestaña «Calendario» y días especiales."""

from datetime import date

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QCalendarWidget, QLabel, QPushButton,
                             QListWidget, QListWidgetItem)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon, QColor, QBrush, QTextCharFormat, QPixmap

from ...idiomas import t
from ..dialogos.sistema import DialogoDiasEspeciales
from ...nucleo import calendario, usuarios

# Cabecera del día elegido (tema oscuro, temas claros) y fondo y letra de cada día del mes, por clase (nucleo/calendario)
_COLORES_CABECERA = {"festivo": ("#e57373", "#c62828"), "vacaciones": ("#FFF59D", "#8a6d00"),
                     "puente": ("#42A5F5", "#1565c0"), "libre": ("#F48FB1", "#ad1457")}
_COLORES_DIA = {"festivo": ("#502828", "#ddd"), "vacaciones": ("#FFF59D", "black"), "puente": ("#1565C0", "white"),
                "libre": ("#F48FB1", "black"), "tareas": ("#A5D6A7", "black")}


class PestanaCalendario:
    """Pestaña «Calendario» y días especiales.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def update_calendar_list(self):
        """Lo que se ve del día elegido: lo calcula el núcleo (nucleo/calendario.py), igual que en MantPro Web."""
        sd = self.calendar.selectedDate(); sds = sd.toString("yyyy-MM-dd"); self.task_list.clear()
        if hasattr(self, "btn_gestion_dias"): self.btn_gestion_dias.setEnabled(usuarios.es_admin())
        festivos = {f.toString("yyyy-MM-dd") for f in self.gestor_festivos.obtener_festivos()}
        dia = calendario.dia(self.db, usuarios.SESION_ACTUAL, sds, sede=self.sede_filtro(), festivos=festivos,
                             carpeta_fotos=getattr(self, "carpeta_fotos", None))
        # Colores claros sobre el tema oscuro y oscuros sobre los temas claros.
        oscuro = getattr(self, "_tema_actual", "oscuro") == "oscuro"
        c = _COLORES_CABECERA.get(dia["clase"], ("#80DEEA", "#00727d"))[0 if oscuro else 1]
        self.lbl_info.setStyleSheet(f"font-weight:bold; font-size:16px; color:{c};"); self.lbl_info.setText(dia["titulo"])
        for linea in dia["lineas"]:
            it = QListWidgetItem(linea["texto"])
            if linea["tipo"] == "aviso":
                it.setBackground(QColor(linea["color"])); it.setForeground(Qt.GlobalColor.white)
            elif linea["tipo"] == "trabajo":
                if linea["foto"]:
                    # Icono propio (no del tema del sistema): algunos temas de iconos SVG
                    # provocan el warning "qt.svg: Invalid path data" con QIcon.fromTheme.
                    pm_foto = QPixmap(16, 16); pm_foto.fill(QColor("#3daee9"))
                    it.setIcon(QIcon(pm_foto)); it.setToolTip(t("cal_tiene_foto"))
                it.setData(Qt.ItemDataRole.UserRole, linea["id"])
            self.task_list.addItem(it)

    def init_calendar_tab(self):
        l = QHBoxLayout(); lp = QVBoxLayout(); th = QHBoxLayout()
        th.addWidget(QPushButton(t("btn_ir_hoy"), clicked=self.go_today)); self.btn_gestion_dias = QPushButton(t("btn_gestion_dias"), clicked=lambda: self.gest_dias()); th.addWidget(self.btn_gestion_dias)
        lp.addLayout(th); self.calendar = QCalendarWidget(); self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self.update_calendar_list); lp.addWidget(self.calendar); l.addLayout(lp, 60)
        rp = QVBoxLayout(); self.lbl_info = QLabel(t("lbl_info")); rp.addWidget(self.lbl_info)
        self.task_list = QListWidget(); self.configurar_deseleccion(self.task_list)
        self.task_list.itemDoubleClicked.connect(self.edit_cal); rp.addWidget(self.task_list); l.addLayout(rp, 40); self.tab_calendar.setLayout(l)

    # --- LÓGICA GENERAL ---
    def go_today(self): self.calendar.setSelectedDate(QDate.currentDate()); self.update_calendar_list()

    def gest_dias(self, c=False):
        if not usuarios.es_admin(): return          # solo administradores, como en el menú
        DialogoDiasEspeciales(self.db, self.gestor_festivos, self).exec(); self.pintar_calendario()

    def pintar_calendario(self):
        """Los colores de los días (del año pasado al que viene): los calcula el núcleo, igual que en MantPro Web."""
        self.calendar.setUpdatesEnabled(False); ac = QDate.currentDate().year(); fc = QDate(ac - 1, 1, 1); ff = QDate(ac + 1, 12, 31); fl = QTextCharFormat()
        while fc <= ff: self.calendar.setDateTextFormat(fc, fl); fc = fc.addDays(1)
        festivos = {f.toString("yyyy-MM-dd") for f in self.gestor_festivos.obtener_festivos()}
        for f, clase in calendario.marcas(self.db, festivos, date(ac - 1, 1, 1), date(ac + 1, 12, 31), sede=self.sede_filtro()).items():
            fondo, letra = _COLORES_DIA.get(clase, ("#555", "black"))
            fm = QTextCharFormat(); fm.setBackground(QBrush(QColor(fondo))); fm.setForeground(QBrush(QColor(letra)))
            if clase == "tareas": fm.setFontWeight(750)
            self.calendar.setDateTextFormat(QDate.fromString(f, "yyyy-MM-dd"), fm)
        self.calendar.setUpdatesEnabled(True)

    def edit_cal(self, i): self.proc_edit(i.data(Qt.ItemDataRole.UserRole))
