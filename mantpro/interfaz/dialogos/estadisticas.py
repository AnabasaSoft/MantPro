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

"""Estadísticas por técnico: trabajos de cada persona por año y mes, averías,
preventivos, horas de parada y pendientes asignados (se abre desde el Dashboard)."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ..widgets.graficos import GraficoBarrasRanking
from ...nucleo import estadisticas, usuarios


class _ItemNumero(QTableWidgetItem):
    """Celda numérica que ordena por su valor, no como texto."""
    def __init__(self, valor, texto=None):
        super().__init__(texto if texto is not None else str(valor))
        self._valor = valor
        self.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def __lt__(self, otro):
        return self._valor < otro._valor if isinstance(otro, _ItemNumero) else super().__lt__(otro)


class DialogoEstadisticasTecnicos(QDialog):
    def __init__(self, parent, ruta_db):
        super().__init__(parent)
        self.ruta_db = ruta_db
        self.setWindowTitle(tt("title_estadisticas_tecnicos", "Estadísticas por técnico"))
        self.resize(1320, 640)
        l = QVBoxLayout(self)

        barra = QHBoxLayout()
        barra.addWidget(QLabel(tt("lbl_anio_grafico", "Año:")))
        self.combo_anio = QComboBox()
        self.combo_anio.addItem(tt("opcion_todos_los_anios", "TODOS"), None)
        for anio in estadisticas.anios_disponibles(ruta_db):
            self.combo_anio.addItem(str(anio), anio)
        if self.combo_anio.count() > 1:
            self.combo_anio.setCurrentIndex(1)  # el año más reciente
        self.combo_anio.currentIndexChanged.connect(self._cargar)
        barra.addWidget(self.combo_anio); barra.addStretch()
        l.addLayout(barra)

        l.addWidget(QLabel(tt("lbl_trabajos_por_tecnico", "Trabajos por técnico")))
        # Texto del gráfico según el tema activo: el oscuro se aplica con hojas
        # de estilo y no cambia la paleta, así que se mira el tema elegido.
        oscuro = getattr(parent, "_tema_actual", "oscuro") == "oscuro"
        self.grafico = GraficoBarrasRanking(color="#3daee9", color_texto="#dcdcdc" if oscuro else "#202020")
        l.addWidget(self.grafico)

        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSortingEnabled(True)
        l.addWidget(self.tabla, 1)
        self.lbl_nota = QLabel(tt("msg_nota_estadisticas_tecnicos", "Las horas de parada son las de los trabajos de avería. «Pendientes» son los trabajos que cada técnico tiene asignados ahora mismo."))
        self.lbl_nota.setWordWrap(True); self.lbl_nota.setStyleSheet("color: gray;")
        l.addWidget(self.lbl_nota)

        pie = QHBoxLayout(); pie.addStretch()
        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept); pie.addWidget(btn_cerrar)
        l.addLayout(pie)
        self._cargar()

    def _cargar(self):
        anio = self.combo_anio.currentData()
        datos = estadisticas.por_tecnico(self.ruta_db, anio)
        for d in datos:
            if d["nombre"] == usuarios.ETIQUETA_HISTORICO:
                d["nombre"] = tt("lbl_tecnico_historico", "Histórico (sin usuario)")
        self.grafico.establecer_datos([(d["nombre"], d["total"]) for d in datos if d["total"]])

        meses = [t(f"mes_{m:02d}_corto") for m in range(1, 13)] if anio else []
        # Primero los totales (lo que más se mira) y después los meses, que en
        # pantallas estrechas pueden quedar a la derecha con desplazamiento.
        cabeceras = ([tt("hdr_tecnico", "Técnico"), tt("hdr_total", "Total"),
                      tt("hdr_averias", "Averías"), tt("hdr_preventivos", "Preventivos"),
                      tt("hdr_horas_paro", "Horas de parada"), tt("hdr_pendientes_asignados", "Pendientes")] + meses)
        self.tabla.setSortingEnabled(False)
        self.tabla.clear()
        self.tabla.setColumnCount(len(cabeceras)); self.tabla.setHorizontalHeaderLabels(cabeceras)
        self.tabla.setRowCount(len(datos))
        for i, d in enumerate(datos):
            celdas = [QTableWidgetItem(d["nombre"]), _ItemNumero(d["total"]),
                      _ItemNumero(d["averias"]), _ItemNumero(d["preventivos"]),
                      _ItemNumero(d["horas_paro"], f"{d['horas_paro']:g}"), _ItemNumero(d["pendientes"])]
            if anio:
                celdas += [_ItemNumero(n, str(n) if n else "·") for n in d["meses"]]
            for j, item in enumerate(celdas):
                if j == 1:
                    fuente = item.font(); fuente.setBold(True); item.setFont(fuente)
                self.tabla.setItem(i, j, item)
        self.tabla.setSortingEnabled(True)
        # Todas las columnas a su contenido (el nombre completo del técnico
        # incluido); el sobrante va a la última.
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        cab.setStretchLastSection(True)
