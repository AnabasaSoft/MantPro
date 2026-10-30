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

"""Pestaña «Dashboard»: indicadores y gráficos."""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QProgressBar, QPushButton
from PyQt6.QtCore import QDate, Qt

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..dialogos.estadisticas import DialogoEstadisticasTecnicos
from ..widgets.graficos import GraficoBarrasMensual, GraficoBarrasRanking
from ...nucleo import maquinas

class PestanaDashboard:
    """Pestaña «Dashboard»: indicadores y gráficos.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def init_dashboard_tab(self):
        l = QVBoxLayout()
        h_cards = QHBoxLayout()
        style_card = "QGroupBox { border-radius: 8px; margin-top: 10px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; } QLabel { font-size: 24px; font-weight: bold; }"
        self.card_avisos = QGroupBox(t("lbl_avisos_pendientes")); self.card_avisos.setStyleSheet(style_card)
        l_c1 = QVBoxLayout(); self.lbl_count_avisos = QLabel("0"); self.lbl_count_avisos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c1.addWidget(self.lbl_count_avisos); self.card_avisos.setLayout(l_c1); h_cards.addWidget(self.card_avisos)
        self.card_todos = QGroupBox(t("lbl_tareas_por_hacer")); self.card_todos.setStyleSheet(style_card)
        l_c2 = QVBoxLayout(); self.lbl_count_todos = QLabel("0"); self.lbl_count_todos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c2.addWidget(self.lbl_count_todos); self.card_todos.setLayout(l_c2); h_cards.addWidget(self.card_todos)
        self.card_regs = QGroupBox(t("lbl_registros_este_mes")); self.card_regs.setStyleSheet(style_card)
        l_c3 = QVBoxLayout(); self.lbl_count_regs = QLabel("0"); self.lbl_count_regs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c3.addWidget(self.lbl_count_regs); self.card_regs.setLayout(l_c3); h_cards.addWidget(self.card_regs)
        style_card_pequena = "QGroupBox { border-radius: 8px; margin-top: 10px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; } QLabel { font-size: 18px; font-weight: bold; }"
        self.card_mtbf = QGroupBox(tt("lbl_mtbf_global", "MTBF medio")); self.card_mtbf.setStyleSheet(style_card_pequena)
        l_c4 = QVBoxLayout(); self.lbl_mtbf_global = QLabel("--"); self.lbl_mtbf_global.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c4.addWidget(self.lbl_mtbf_global); self.card_mtbf.setLayout(l_c4); h_cards.addWidget(self.card_mtbf)
        self.card_mttr = QGroupBox(tt("lbl_mttr_global", "MTTR medio")); self.card_mttr.setStyleSheet(style_card_pequena)
        l_c5 = QVBoxLayout(); self.lbl_mttr_global = QLabel("--"); self.lbl_mttr_global.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c5.addWidget(self.lbl_mttr_global); self.card_mttr.setLayout(l_c5); h_cards.addWidget(self.card_mttr)
        l.addLayout(h_cards)
        h_split = QHBoxLayout()
        v_list = QVBoxLayout()
        fila_ranking = QHBoxLayout()
        fila_ranking.addWidget(QLabel(tt("lbl_ranking_maquinas_trabajos", "Máquinas con más trabajos")))
        fila_ranking.addStretch()
        btn_tecnicos = QPushButton(tt("btn_estadisticas_tecnicos", "👥 Estadísticas por técnico"))
        btn_tecnicos.clicked.connect(lambda: DialogoEstadisticasTecnicos(self, self.db.db_name).exec())
        fila_ranking.addWidget(btn_tecnicos)
        v_list.addLayout(fila_ranking)
        self.grafico_ranking_averias = GraficoBarrasRanking(color="#c0392b"); v_list.addWidget(self.grafico_ranking_averias)
        v_list.addWidget(QLabel(tt("lbl_averias_por_mes", "Averías por mes")))
        self.grafico_averias_mes = GraficoBarrasMensual(color="#e67e22"); v_list.addWidget(self.grafico_averias_mes)
        h_split.addLayout(v_list, 80)
        v_stats = QVBoxLayout(); v_stats.addWidget(QLabel(t("lbl_distribucion")))
        self.group_stats = QGroupBox(); self.group_stats.setStyleSheet("QGroupBox { border-radius: 6px; }")
        layout_stats = QVBoxLayout(); layout_stats.setSpacing(10); layout_stats.setContentsMargins(5, 10, 5, 5)
        def crear_barra(titulo, color):
            lbl = QLabel(titulo); lbl.setStyleSheet("font-size: 12px;")
            bar = QProgressBar(); bar.setStyleSheet(f"QProgressBar {{ border-radius: 4px; text-align: center; height: 18px; font-size: 11px; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}"); bar.setValue(0)
            return lbl, bar
        self.lbl_elec, self.bar_elec = crear_barra(f"⚡ {t('tag_electrico')}", "#3daee9"); layout_stats.addWidget(self.lbl_elec); layout_stats.addWidget(self.bar_elec)
        self.lbl_mec, self.bar_mec = crear_barra(f"⚙️ {t('tag_mecanico')}", "#e67e22"); layout_stats.addWidget(self.lbl_mec); layout_stats.addWidget(self.bar_mec)
        self.lbl_prev, self.bar_prev = crear_barra(f"🛡️ {t('tag_preventivo')}", "#27ae60"); layout_stats.addWidget(self.lbl_prev); layout_stats.addWidget(self.bar_prev)
        self.lbl_urg, self.bar_urg = crear_barra(f"🚨 {t('tag_urgente')}", "#c0392b"); layout_stats.addWidget(self.lbl_urg); layout_stats.addWidget(self.bar_urg)
        layout_stats.addStretch(); self.group_stats.setLayout(layout_stats); v_stats.addWidget(self.group_stats); h_split.addLayout(v_stats, 20); l.addLayout(h_split); self.tab_dashboard.setLayout(l)

    def refresh_dashboard(self):
        avisos = self._avisos_visibles(); hoy = QDate.currentDate(); pendientes_reales = 0
        for aid, tit, finicio, freq, dur, ult, *_ in avisos:
            if not finicio: continue
            fi = QDate.fromString(finicio, "yyyy-MM-dd")
            if not freq: freq = "Anual"
            freq = idiomas.normalizar_frecuencia(freq)
            # Un aviso "Diario" se resetea cada día: no le aplicamos la duración
            # configurada, porque un margen de varios días haría que el de ayer
            # siguiera contando como "hecho" hoy.
            dur_ventana = 0 if freq == "Diario" else dur
            ocurrencia = fi
            while ocurrencia.addDays(dur_ventana) < hoy:
                if freq == "Diario": ocurrencia = ocurrencia.addDays(1)
                elif freq == "Semanal": ocurrencia = ocurrencia.addDays(7)
                elif freq == "Mensual": ocurrencia = ocurrencia.addMonths(1)
                elif freq == "Trimestral": ocurrencia = ocurrencia.addMonths(3)
                elif freq == "Semestral": ocurrencia = ocurrencia.addMonths(6)
                elif freq == "Anual": ocurrencia = ocurrencia.addYears(1)
                else: break
            fin_ocurrencia = ocurrencia.addDays(dur_ventana)
            if ocurrencia <= hoy <= fin_ocurrencia and ult != ocurrencia.toString("yyyy-MM-dd"): pendientes_reales += 1
        self.lbl_count_avisos.setText(str(pendientes_reales))
        self.lbl_count_avisos.setStyleSheet("color: #e74c3c; font-size: 32px; font-weight: bold;" if pendientes_reales > 0 else "color: #2ecc71; font-size: 32px; font-weight: bold;")
        todos = self.db.obtener_pendientes(); self.lbl_count_todos.setText(str(len(todos))); self.lbl_count_todos.setStyleSheet("color: #f1c40f; font-size: 32px; font-weight: bold;")
        registros = self.db.obtener_todas_cronologico(); mes_actual = hoy.toString("yyyy-MM"); count_mes = sum(1 for r in registros if r[1].startswith(mes_actual))
        self.lbl_count_regs.setText(str(count_mes)); self.lbl_count_regs.setStyleSheet("color: #3daee9; font-size: 32px; font-weight: bold;")
        self.grafico_ranking_averias.establecer_datos(maquinas.ranking_trabajos())
        self.grafico_averias_mes.establecer_datos(maquinas.averias_por_mes())
        indicadores = maquinas.indicadores_fiabilidad_global()
        mtbf = indicadores["mtbf_dias"]
        self.lbl_mtbf_global.setText(f"{mtbf:.0f} {tt('lbl_dias_abrev', 'días')}" if mtbf is not None else "--")
        mttr = indicadores["mttr_horas"]
        self.lbl_mttr_global.setText(f"{mttr:.1f} {tt('lbl_horas_abrev', 'h')}" if mttr is not None else "--")
        total_tareas = len(registros)
        if total_tareas > 0:
            c_elec = sum(1 for r in registros if "eléctrico" in r[3].lower() or "electrico" in r[3].lower())
            c_mec = sum(1 for r in registros if "mecánico" in r[3].lower() or "mecanico" in r[3].lower())
            c_prev = sum(1 for r in registros if "preventivo" in r[3].lower())
            c_urg = sum(1 for r in registros if "urgente" in r[3].lower() or "avería" in r[3].lower())
            self.bar_elec.setValue(int((c_elec/total_tareas)*100)); self.bar_elec.setFormat(f"{int((c_elec/total_tareas)*100)}% ({c_elec})")
            self.bar_mec.setValue(int((c_mec/total_tareas)*100)); self.bar_mec.setFormat(f"{int((c_mec/total_tareas)*100)}% ({c_mec})")
            self.bar_prev.setValue(int((c_prev/total_tareas)*100)); self.bar_prev.setFormat(f"{int((c_prev/total_tareas)*100)}% ({c_prev})")
            self.bar_urg.setValue(int((c_urg/total_tareas)*100)); self.bar_urg.setFormat(f"{int((c_urg/total_tareas)*100)}% ({c_urg})")
        else:
            for b in [self.bar_elec, self.bar_mec, self.bar_prev, self.bar_urg]: b.setValue(0)
