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

"""Herramientas → Historial de revisiones del almacén: quién hizo cada día la
revisión de los artículos que propone MantPro Stock (los 5 al azar), si los
revisó todos, y qué cantidad contó frente a la que decía el sistema."""

import csv
import os
from datetime import date
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
                             QFileDialog, QMessageBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ...idiomas import t, formato_fecha_localizada
from ..comun import tt
from ...nucleo import revisiones_almacen as rev


def nombres_estado():
    return {
        rev.ESTADO_COMPLETA: tt("rev_estado_completa", "✅ Completa"),
        rev.ESTADO_PARCIAL: tt("rev_estado_parcial", "⚠️ Incompleta"),
        rev.ESTADO_SIN_EMPEZAR: tt("rev_estado_sin_empezar", "❌ Sin revisar"),
    }


COLORES_ESTADO = {
    rev.ESTADO_COMPLETA: QColor("#2e8b57"),
    rev.ESTADO_PARCIAL: QColor("#d98a00"),
    rev.ESTADO_SIN_EMPEZAR: QColor("#c0392b"),
}


def _numero(valor):
    if valor is None:
        return "—"
    return f"{valor:g}"


def _diferencia(valor):
    if valor is None:
        return "—"
    return f"{valor:+g}" if valor else "0"


def _actividad(texto):
    """«2026-11-04 08:15:02» → fecha del idioma + hora."""
    fecha, _, hora = (texto or "").partition(" ")
    return f"{formato_fecha_localizada(fecha)} {hora[:5]}".strip()


class DialogoRevisionesAlmacen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("rev_titulo", "Historial de revisiones del almacén"))
        self.resize(1050, 680)
        self._revisiones = []
        l = QVBoxLayout(self)

        # --- filtros
        f = QHBoxLayout()
        self.combo_usu = QComboBox(); self.combo_usu.addItem(tt("filtro_todos", "Todos"), None)
        for uid, nombre in rev.usuarios_con_revisiones():
            self.combo_usu.addItem(nombre, uid)
        self.combo_periodo = QComboBox()
        for texto, dias in ((tt("aud_periodo_7", "Últimos 7 días"), 7), (tt("aud_periodo_30", "Últimos 30 días"), 30),
                            (tt("aud_periodo_365", "Último año"), 365), (tt("aud_periodo_todo", "Todo"), None)):
            self.combo_periodo.addItem(texto, dias)
        self.combo_periodo.setCurrentIndex(1)
        self.combo_estado = QComboBox(); self.combo_estado.addItem(tt("filtro_todas", "Todas"), None)
        self.combo_estado.addItem(tt("rev_filtro_completas", "Completas"), [rev.ESTADO_COMPLETA])
        self.combo_estado.addItem(tt("rev_filtro_incompletas", "Incompletas o sin revisar"),
                                  [rev.ESTADO_PARCIAL, rev.ESTADO_SIN_EMPEZAR])
        for etiqueta, widget in ((tt("aud_usuario", "Usuario"), self.combo_usu), (tt("aud_periodo", "Periodo"), self.combo_periodo),
                                 (tt("rev_col_estado", "Estado"), self.combo_estado)):
            f.addWidget(QLabel(etiqueta + ":")); f.addWidget(widget)
        f.addStretch()
        l.addLayout(f)
        self.lbl_resumen = QLabel(); self.lbl_resumen.setWordWrap(True)
        l.addWidget(self.lbl_resumen)

        # --- revisiones y detalle de la seleccionada
        split = QSplitter(Qt.Orientation.Vertical)
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels([tt("lbl_fecha", "Fecha"), tt("aud_usuario", "Usuario"),
                                              tt("rev_col_movil", "Móvil"), tt("rev_col_revisados", "Revisados"),
                                              tt("rev_col_diferencias", "Con diferencias"),
                                              tt("rev_col_actividad", "Última actividad")])
        self._preparar_tabla(self.tabla, estirar=2)
        self.tabla.currentCellChanged.connect(lambda *_: self._mostrar_detalle())
        split.addWidget(self.tabla)

        abajo = QWidget(); la = QVBoxLayout(abajo); la.setContentsMargins(0, 0, 0, 0)
        self.lbl_detalle = QLabel(); self.lbl_detalle.setWordWrap(True)
        la.addWidget(self.lbl_detalle)
        self.tabla_lineas = QTableWidget(0, 6)
        self.tabla_lineas.setHorizontalHeaderLabels([tt("rev_col_articulo", "Artículo"), tt("lbl_ubicacion", "Ubicación"),
                                                     tt("rev_col_sistema", "En el sistema"), tt("rev_col_contado", "Contado"),
                                                     tt("rev_col_diferencia", "Diferencia"), tt("rev_col_estado", "Estado")])
        self._preparar_tabla(self.tabla_lineas, estirar=0)
        la.addWidget(self.tabla_lineas)
        split.addWidget(abajo)
        split.setSizes([360, 260])
        l.addWidget(split, 1)

        # --- botones
        b = QHBoxLayout()
        self.lbl_total = QLabel()
        b.addWidget(self.lbl_total)
        b.addStretch()
        exportar = QPushButton(tt("aud_exportar", "📤 Exportar (Excel o CSV)")); exportar.clicked.connect(self._exportar)
        cerrar = QPushButton(t("cerrar")); cerrar.clicked.connect(self.accept)
        b.addWidget(exportar); b.addWidget(cerrar)
        l.addLayout(b)

        for combo in (self.combo_usu, self.combo_periodo, self.combo_estado):
            combo.currentIndexChanged.connect(self.recargar)
        self.recargar()

    @staticmethod
    def _preparar_tabla(tabla, estirar):
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setAlternatingRowColors(True)
        tabla.verticalHeader().setVisible(False)
        cab = tabla.horizontalHeader()
        for c in range(tabla.columnCount()):
            cab.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch if c == estirar else QHeaderView.ResizeMode.ResizeToContents)

    # ----------------------------------------------------------- datos
    def _filtros(self):
        return dict(dias=self.combo_periodo.currentData(), usuario_id=self.combo_usu.currentData(),
                    estado=self.combo_estado.currentData())

    def recargar(self):
        self._revisiones = rev.listar_revisiones(limite=5000, **self._filtros())
        self._pintar()

    def _pintar(self):
        estados = nombres_estado()
        self.tabla.setRowCount(len(self._revisiones))
        cuentas = {rev.ESTADO_COMPLETA: 0, rev.ESTADO_PARCIAL: 0, rev.ESTADO_SIN_EMPEZAR: 0}
        for fila, r in enumerate(self._revisiones):
            cuentas[r["estado"]] += 1
            celdas = [formato_fecha_localizada(r["fecha"]), r["usuario_nombre"] or "—", r["dispositivo"] or "—",
                      f"{r['revisados']}/{r['total']}  {estados[r['estado']]}",
                      str(r["ajustados"]) if r["revisados"] else "—", _actividad(r["actualizada"])]
            for col, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                if col == 3:
                    item.setForeground(COLORES_ESTADO[r["estado"]])
                self.tabla.setItem(fila, col, item)
        self.lbl_total.setText(tt("rev_total", "{n} revisiones").format(n=len(self._revisiones)))
        self.lbl_resumen.setText(tt("rev_resumen", "Completas: {c} · Incompletas: {i} · Sin revisar: {s}").format(
            c=cuentas[rev.ESTADO_COMPLETA], i=cuentas[rev.ESTADO_PARCIAL], s=cuentas[rev.ESTADO_SIN_EMPEZAR]))
        if self._revisiones:
            self.tabla.selectRow(0)
        self._mostrar_detalle()

    def _mostrar_detalle(self):
        fila = self.tabla.currentRow()
        r = self._revisiones[fila] if 0 <= fila < len(self._revisiones) else None
        self.tabla_lineas.setRowCount(0)
        if r is None:
            self.lbl_detalle.setText(tt("rev_sin_registros", "No hay revisiones con estos filtros."))
            self.tabla_lineas.setVisible(False)
            return
        self.tabla_lineas.setVisible(True)
        self.lbl_detalle.setText(f"<b>{formato_fecha_localizada(r['fecha'])}</b> · {r['usuario_nombre'] or '—'}"
                                 f" · {r['dispositivo'] or '—'} · {r['revisados']}/{r['total']}")
        lineas = rev.lineas_de_revision(r["id"])
        self.tabla_lineas.setRowCount(len(lineas))
        for i, ln in enumerate(lineas):
            articulo = f"{ln['codigo']} · {ln['nombre']}" if ln["codigo"] else ln["nombre"]
            unidad = f" {ln['unidad']}" if ln["unidad"] else ""
            estado = tt("rev_linea_revisada", "✅ Revisado") + (f" {ln['fecha_revision'][11:16]}" if ln["fecha_revision"] else "") \
                if ln["revisado"] else tt("rev_linea_pendiente", "❌ Sin revisar")
            celdas = [articulo, ln["ubicacion"] or "—", _numero(ln["cantidad_sistema"]) + unidad,
                      (_numero(ln["cantidad_contada"]) + unidad) if ln["revisado"] else "—",
                      _diferencia(ln["diferencia"]), estado]
            for col, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                if col == 4 and ln["diferencia"]:
                    item.setForeground(QColor("#c0392b"))
                if col == 5:
                    item.setForeground(COLORES_ESTADO[rev.ESTADO_COMPLETA if ln["revisado"] else rev.ESTADO_SIN_EMPEZAR])
                self.tabla_lineas.setItem(i, col, item)

    # ----------------------------------------------------------- exportar
    def _cabecera_export(self):
        return [tt("lbl_fecha", "Fecha"), tt("aud_usuario", "Usuario"), tt("rev_col_movil", "Móvil"),
                tt("rev_col_estado", "Estado"), tt("rev_col_revisados", "Revisados"), tt("rev_col_articulo", "Artículo"),
                tt("lbl_ubicacion", "Ubicación"), tt("rev_col_sistema", "En el sistema"), tt("rev_col_contado", "Contado"),
                tt("rev_col_diferencia", "Diferencia"), tt("rev_linea_estado", "Revisado")]

    def _filas_export(self):
        """Una fila por artículo propuesto."""
        estados = nombres_estado()
        si, no = tt("rev_si", "Sí"), tt("rev_no", "No")
        for r in rev.listar_revisiones(limite=100000, **self._filtros()):
            for ln in rev.lineas_de_revision(r["id"]):
                articulo = f"{ln['codigo']} · {ln['nombre']}" if ln["codigo"] else ln["nombre"]
                yield [formato_fecha_localizada(r["fecha"]), r["usuario_nombre"], r["dispositivo"],
                       estados[r["estado"]], f"{r['revisados']}/{r['total']}", articulo, ln["ubicacion"],
                       ln["cantidad_sistema"] if ln["cantidad_sistema"] is not None else "",
                       ln["cantidad_contada"] if ln["revisado"] and ln["cantidad_contada"] is not None else "",
                       ln["diferencia"] if ln["diferencia"] is not None else "", si if ln["revisado"] else no]

    def _exportar(self):
        cab = self._cabecera_export()
        nombre = f"{tt('rev_fichero', 'Revisiones_del_almacen')}_{date.today().strftime('%Y%m%d')}.xlsx"
        ruta, filtro = QFileDialog.getSaveFileName(self, tt("aud_exportar", "📤 Exportar (Excel o CSV)"), nombre,
                                                   "Excel (*.xlsx);;CSV (*.csv)")
        if not ruta:
            return
        filas = list(self._filas_export())
        try:
            if ruta.lower().endswith(".csv") or "CSV" in filtro:
                if not ruta.lower().endswith(".csv"):
                    ruta = os.path.splitext(ruta)[0] + ".csv"
                with open(ruta, "w", newline="", encoding="utf-8-sig") as fh:
                    w = csv.writer(fh, delimiter=";")
                    w.writerow(cab); w.writerows(filas)
            else:
                import xlsxwriter
                if not ruta.lower().endswith(".xlsx"):
                    ruta += ".xlsx"
                libro = xlsxwriter.Workbook(ruta)
                hoja = libro.add_worksheet(tt("rev_hoja", "Revisiones del almacén")[:31])
                negrita = libro.add_format({"bold": True, "bg_color": "#2c3e50", "font_color": "white"})
                for col, texto in enumerate(cab):
                    hoja.write(0, col, texto, negrita)
                for i, fila in enumerate(filas, start=1):
                    for col, valor in enumerate(fila):
                        hoja.write(i, col, valor)
                for col, ancho in enumerate((12, 18, 20, 16, 11, 36, 24, 14, 12, 12, 11)):
                    hoja.set_column(col, col, ancho)
                hoja.freeze_panes(1, 0)
                hoja.autofilter(0, 0, max(len(filas), 1), len(cab) - 1)
                libro.close()
            QMessageBox.information(self, self.windowTitle(),
                                    tt("aud_exportado", "Exportados {n} registros a:\n{ruta}").format(n=len(filas), ruta=ruta))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))
