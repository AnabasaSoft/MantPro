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

"""Pestaña «Dashboard»: indicadores y gráficos."""

from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QProgressBar, QPushButton
from PyQt6.QtCore import QDate, Qt

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..dialogos.estadisticas import DialogoEstadisticasTecnicos
from ..widgets.graficos import GraficoBarrasMensual, GraficoBarrasRanking
from ...nucleo import maquinas, consumos, costes, usuarios

def _importe_corto(valor):
    """Importe abreviado para las barras del gráfico mensual: «850», «1,2k»."""
    if valor >= 1000:
        texto = f"{valor / 1000:.1f}k"
        return texto if idiomas.get_idioma() == "en" else texto.replace(".", ",")
    return f"{valor:.0f}"


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
        self.card_coste_mes = QGroupBox(tt("lbl_coste_mes", "Coste del mes")); self.card_coste_mes.setStyleSheet(style_card_pequena)
        l_c6 = QVBoxLayout(); self.lbl_coste_mes = QLabel("--"); self.lbl_coste_mes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c6.addWidget(self.lbl_coste_mes); self.card_coste_mes.setLayout(l_c6); h_cards.addWidget(self.card_coste_mes)
        self.card_coste_anio = QGroupBox(tt("lbl_coste_anio", "Coste del año")); self.card_coste_anio.setStyleSheet(style_card_pequena)
        l_c7 = QVBoxLayout(); self.lbl_coste_anio = QLabel("--"); self.lbl_coste_anio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_c7.addWidget(self.lbl_coste_anio); self.card_coste_anio.setLayout(l_c7); h_cards.addWidget(self.card_coste_anio)
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
        layout_stats.addStretch(); self.group_stats.setLayout(layout_stats); v_stats.addWidget(self.group_stats); h_split.addLayout(v_stats, 20); l.addLayout(h_split)
        h_costes = QHBoxLayout()
        v_rank_coste = QVBoxLayout()
        self.lbl_titulo_ranking_coste = QLabel(tt("lbl_ranking_maquinas_coste", "Máquinas con más coste (año actual)"))
        v_rank_coste.addWidget(self.lbl_titulo_ranking_coste)
        self.grafico_ranking_coste = GraficoBarrasRanking(color="#8e44ad", formato_valor=self._importe_largo); v_rank_coste.addWidget(self.grafico_ranking_coste)
        h_costes.addLayout(v_rank_coste, 50)
        v_mes_coste = QVBoxLayout()
        self.lbl_titulo_coste_mes = QLabel(tt("lbl_coste_por_mes", "Coste de mantenimiento por mes"))
        v_mes_coste.addWidget(self.lbl_titulo_coste_mes)
        self.grafico_coste_mes = GraficoBarrasMensual(color="#16a085", formato_valor=_importe_corto); v_mes_coste.addWidget(self.grafico_coste_mes)
        h_costes.addLayout(v_mes_coste, 50)
        l.addLayout(h_costes); self.tab_dashboard.setLayout(l)

    @staticmethod
    def _importe_largo(valor):
        return consumos.formato_importe(valor, consumos.moneda())

    def _refrescar_costes(self):
        # Los costes (repuestos y mano de obra) solo los ve un administrador
        ver = usuarios.es_admin()
        for w in (self.card_coste_mes, self.card_coste_anio, self.lbl_titulo_ranking_coste, self.grafico_ranking_coste,
                  self.lbl_titulo_coste_mes, self.grafico_coste_mes):
            w.setVisible(ver)
        if not ver:
            return
        r = costes.resumen()
        # «≥» avisa de que a algún repuesto u hora le falta el precio y el total se queda corto
        marca = "≥ " if r["sin_precio"] else ""
        self.lbl_coste_mes.setText(marca + self._importe_largo(r["mes"]))
        self.lbl_coste_anio.setText(marca + self._importe_largo(r["anio"]))
        self.grafico_ranking_coste.establecer_datos(r["ranking"])
        self.grafico_coste_mes.establecer_datos(r["por_mes"])

    def refresh_dashboard(self):
        avisos = self._avisos_visibles(); hoy = QDate.currentDate(); pendientes_reales = 0
        from ...nucleo import contadores
        por_contador = contadores.estados_avisos()
        for aid, tit, finicio, freq, dur, ult, *_ in avisos:
            info = por_contador.get(aid)
            # Por contador: cuenta si toca por contador (y no se ha hecho hoy);
            # si además tiene fecha, también si toca por fecha (abajo)
            if info and ult != hoy.toString("yyyy-MM-dd") and info["estado"] in ("PENDIENTE", "ATRASADO"):
                pendientes_reales += 1; continue
            if info and info["solo_contador"]: continue
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
        self._refrescar_costes()
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
