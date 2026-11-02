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

"""Máquinas → 💶 Coste de repuestos: cuánto se ha gastado en repuestos en cada
máquina (con sus submáquinas), qué artículos y en cuántos trabajos, por año."""

from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import consumos, maquinas


class _ItemNumero(QTableWidgetItem):
    def __init__(self, texto, valor):
        super().__init__(texto)
        self.valor = valor
        self.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def __lt__(self, otro):
        return self.valor < getattr(otro, "valor", 0)


class DialogoCosteRepuestos(QDialog):
    def __init__(self, parent, db, maquina_inicial=None):
        super().__init__(parent)
        self.db = db
        self.moneda = consumos.moneda()
        self.setWindowTitle(tt("title_coste_repuestos", "Coste de repuestos por máquina"))
        self.resize(1050, 620)
        l = QVBoxLayout(self)
        f = QHBoxLayout()
        f.addWidget(QLabel(tt("lbl_anio", "Año") + ":"))
        self.combo_anio = QComboBox(); self.combo_anio.addItem(tt("filtro_todos", "Todos"), None)
        for anio in maquinas.anios_disponibles():
            self.combo_anio.addItem(anio, anio)
        if self.combo_anio.count() > 1:
            self.combo_anio.setCurrentIndex(1)
        self.combo_anio.currentIndexChanged.connect(self.recargar)
        f.addWidget(self.combo_anio); f.addStretch()
        self.lbl_total = QLabel(); f.addWidget(self.lbl_total)
        l.addLayout(f)

        split = QSplitter(Qt.Orientation.Horizontal)
        self.tabla_maq = QTableWidget(0, 3)
        self.tabla_maq.setHorizontalHeaderLabels([tt("hdr_maquina", "Máquina"), tt("hdr_trabajos", "Trabajos"),
                                                  tt("lbl_coste_material", "Coste de material")])
        self._configurar(self.tabla_maq, estirar=0)
        self.tabla_maq.currentCellChanged.connect(lambda *_: self._mostrar_detalle())
        split.addWidget(self.tabla_maq)
        self.tabla_art = QTableWidget(0, 4)
        self.tabla_art.setHorizontalHeaderLabels([tt("lbl_material", "Artículo"), tt("lbl_cantidad", "Cantidad"),
                                                  tt("lbl_importe", "Importe"), tt("aud_f_codigo", "Código")])
        self._configurar(self.tabla_art, estirar=0)
        split.addWidget(self.tabla_art)
        split.setSizes([500, 550])
        l.addWidget(split, 1)
        nota = QLabel(tt("lbl_nota_coste", "Incluye los trabajos de las submáquinas. *: algún artículo no tenía precio al usarse."))
        nota.setWordWrap(True); nota.setStyleSheet("color: gray;")
        l.addWidget(nota)
        b = QHBoxLayout(); b.addStretch()
        exportar = QPushButton(tt("btn_exportar_excel_coste", "📊 Exportar a Excel")); exportar.clicked.connect(self._exportar)
        cerrar = QPushButton(t("cerrar")); cerrar.clicked.connect(self.accept)
        b.addWidget(exportar); b.addWidget(cerrar)
        l.addLayout(b)
        self._maquina_inicial = maquina_inicial
        self.recargar()

    @staticmethod
    def _configurar(tabla, estirar):
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.verticalHeader().setVisible(False)
        tabla.setSortingEnabled(True)
        cab = tabla.horizontalHeader()
        for c in range(tabla.columnCount()):
            cab.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch if c == estirar else QHeaderView.ResizeMode.ResizeToContents)

    def _importe(self, valor, sin_precio):
        return consumos.formato_importe(valor, self.moneda) + (" *" if sin_precio else "")

    def _datos(self):
        """{maquina_id: datos} sumando a cada máquina lo de sus submáquinas."""
        anio = self.combo_anio.currentData()
        con = self.db.conectar()
        sql = "SELECT id, fecha, maquina_id FROM tareas WHERE maquina_id IS NOT NULL"
        filas = con.execute(sql + (" AND substr(fecha,1,4)=?" if anio else ""), (anio,) if anio else ()).fetchall()
        con.close()
        propios = consumos.consumo_por_tareas(filas)
        totales = {}
        for mid in {m["id"] for m in maquinas.listar_maquinas()}:
            ids = maquinas.descendientes_ids(mid)
            acum = {"importe": 0.0, "sin_precio": False, "trabajos": 0, "articulos": {}}
            for sub in ids:
                p = propios.get(sub)
                if not p:
                    continue
                acum["importe"] += p["importe"]; acum["sin_precio"] |= p["sin_precio"]; acum["trabajos"] += p["trabajos"]
                for clave, a in p["articulos"].items():
                    d = acum["articulos"].setdefault(clave, {"cantidad": 0.0, "importe": 0.0, "sin_precio": False})
                    d["cantidad"] += a["cantidad"]; d["importe"] += a["importe"]; d["sin_precio"] |= a["sin_precio"]
            if acum["trabajos"]:
                totales[mid] = acum
        return totales, propios

    def recargar(self):
        self._totales, propios = self._datos()
        rutas = maquinas.mapa_rutas_completas()
        self._orden = sorted(self._totales, key=lambda m: -self._totales[m]["importe"])
        self.tabla_maq.setSortingEnabled(False)
        self.tabla_maq.setRowCount(len(self._orden))
        for fila, mid in enumerate(self._orden):
            d = self._totales[mid]
            item = QTableWidgetItem(rutas.get(mid, str(mid))); item.setData(Qt.ItemDataRole.UserRole, mid)
            self.tabla_maq.setItem(fila, 0, item)
            self.tabla_maq.setItem(fila, 1, _ItemNumero(str(d["trabajos"]), d["trabajos"]))
            self.tabla_maq.setItem(fila, 2, _ItemNumero(self._importe(d["importe"], d["sin_precio"]), d["importe"]))
        self.tabla_maq.setSortingEnabled(True)
        self.tabla_maq.sortItems(2, Qt.SortOrder.DescendingOrder)   # las que más cuestan, arriba
        total = sum(p["importe"] for p in propios.values())
        self.lbl_total.setText(tt("lbl_total_periodo", "Total del periodo") + f": <b>{consumos.formato_importe(total, self.moneda)}</b>")
        fila = next((f for f in range(self.tabla_maq.rowCount())
                     if self.tabla_maq.item(f, 0).data(Qt.ItemDataRole.UserRole) == self._maquina_inicial), 0)
        if self._orden:
            self.tabla_maq.selectRow(fila)
        self._mostrar_detalle()

    def _mostrar_detalle(self):
        item = self.tabla_maq.item(self.tabla_maq.currentRow(), 0) if self.tabla_maq.currentRow() >= 0 else None
        d = self._totales.get(item.data(Qt.ItemDataRole.UserRole)) if item else None
        articulos = sorted((d or {}).get("articulos", {}).items(), key=lambda x: -x[1]["importe"])
        self.tabla_art.setSortingEnabled(False)
        self.tabla_art.setRowCount(len(articulos))
        for fila, ((codigo, nombre, unidad), a) in enumerate(articulos):
            self.tabla_art.setItem(fila, 0, QTableWidgetItem(nombre))
            self.tabla_art.setItem(fila, 1, _ItemNumero(f"{a['cantidad']:g} {unidad or ''}".strip(), a["cantidad"]))
            self.tabla_art.setItem(fila, 2, _ItemNumero(self._importe(a["importe"], a["sin_precio"]), a["importe"]))
            self.tabla_art.setItem(fila, 3, QTableWidgetItem(codigo or ""))
        self.tabla_art.setSortingEnabled(True)
        self.tabla_art.sortItems(2, Qt.SortOrder.DescendingOrder)

    def _exportar(self):
        try:
            import xlsxwriter
        except ImportError:
            QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        anio = self.combo_anio.currentData() or tt("filtro_todos", "Todos")
        ruta, _ = QFileDialog.getSaveFileName(self, self.windowTitle(),
                                              f"{tt('fichero_coste_repuestos', 'Coste_repuestos')}_{anio}.xlsx", "Excel (*.xlsx)")
        if not ruta:
            return
        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"
        rutas = maquinas.mapa_rutas_completas()
        libro = xlsxwriter.Workbook(ruta)
        negrita = libro.add_format({"bold": True, "bg_color": "#2c3e50", "font_color": "white"})
        dinero = libro.add_format({"num_format": "#,##0.00"})
        h1 = libro.add_worksheet(tt("hoja_coste_maquinas", "Por máquina")[:31])
        cab = [tt("hdr_maquina", "Máquina"), tt("hdr_trabajos", "Trabajos"), f"{tt('lbl_coste_material', 'Coste de material')} ({self.moneda})"]
        for c, txt in enumerate(cab): h1.write(0, c, txt, negrita)
        for f, mid in enumerate(self._orden, start=1):
            d = self._totales[mid]
            h1.write(f, 0, rutas.get(mid, str(mid))); h1.write(f, 1, d["trabajos"]); h1.write(f, 2, d["importe"], dinero)
        h1.set_column(0, 0, 45); h1.set_column(1, 2, 18)
        h2 = libro.add_worksheet(tt("hoja_coste_articulos", "Por artículo")[:31])
        cab2 = [tt("hdr_maquina", "Máquina"), tt("aud_f_codigo", "Código"), tt("lbl_material", "Artículo"),
                tt("lbl_cantidad", "Cantidad"), tt("lbl_unidad", "Unidad"), f"{tt('lbl_importe', 'Importe')} ({self.moneda})"]
        for c, txt in enumerate(cab2): h2.write(0, c, txt, negrita)
        f = 1
        for mid in self._orden:
            for (codigo, nombre, unidad), a in self._totales[mid]["articulos"].items():
                for c, v in enumerate((rutas.get(mid, str(mid)), codigo or "", nombre, a["cantidad"], unidad or "")):
                    h2.write(f, c, v)
                h2.write(f, 5, a["importe"], dinero); f += 1
        h2.set_column(0, 0, 40); h2.set_column(1, 1, 14); h2.set_column(2, 2, 40); h2.set_column(3, 5, 14)
        h1.write(len(self._orden) + 2, 0, f"{tt('lbl_anio', 'Año')}: {anio} · {datetime.now().strftime('%Y-%m-%d')}")
        libro.close()
        QMessageBox.information(self, t("title_exportado"), tt("msg_coste_exportado", "Exportado en:\n{ruta}").format(ruta=ruta))
