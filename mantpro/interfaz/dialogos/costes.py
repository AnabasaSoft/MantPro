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

"""Máquinas → 💶 Costes por máquina: cuánto ha costado el mantenimiento de cada
máquina (con sus submáquinas), en mano de obra (horas × coste de la hora) y en
repuestos (qué artículos y cuántos), por año."""

from datetime import datetime
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QLineEdit,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import consumos, maquinas, mano_obra, usuarios


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
        self.setWindowTitle(tt("title_costes_maquina", "Costes por máquina"))
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
        f.addWidget(self.combo_anio)
        # Coste de la hora de trabajo (interno, igual para todos): solo el administrador
        f.addSpacing(20)
        f.addWidget(QLabel(tt("lbl_coste_hora", "Coste de la hora de trabajo") + f" ({self.moneda}):"))
        tarifa = mano_obra.coste_hora()
        self.campo_hora = QLineEdit("" if tarifa is None else f"{tarifa:g}".replace(".", ","))
        self.campo_hora.setPlaceholderText(tt("ph_precio", "sin precio")); self.campo_hora.setMaximumWidth(90)
        self.campo_hora.setEnabled(usuarios.es_admin())
        self.campo_hora.setToolTip(tt("tt_coste_hora", "Se aplica a los trabajos cuyo tiempo se apunte a partir de ahora; "
                                                       "los ya apuntados conservan su tarifa. Solo lo cambia un administrador."))
        self.campo_hora.editingFinished.connect(lambda: mano_obra.fijar_coste_hora(consumos.numero(self.campo_hora.text())))
        f.addWidget(self.campo_hora)
        f.addStretch()
        self.lbl_total = QLabel(); f.addWidget(self.lbl_total)
        l.addLayout(f)

        split = QSplitter(Qt.Orientation.Horizontal)
        self.tabla_maq = QTableWidget(0, 6)
        self.tabla_maq.setHorizontalHeaderLabels([tt("hdr_maquina", "Máquina"), tt("hdr_trabajos", "Trabajos"),
                                                  tt("lbl_horas", "Horas"), tt("lbl_mano_obra", "Mano de obra"),
                                                  tt("lbl_repuestos_corto", "Repuestos"), tt("lbl_total", "Total")])
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
        nota = QLabel(tt("lbl_nota_costes", "Incluye los trabajos de las submáquinas. Horas = tiempo trabajado × personas. "
                                            "*: falta algún precio (de un artículo o de la hora) al apuntarlo."))
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
        tiempos = mano_obra.tiempos_de([f[0] for f in filas])
        mano = {}
        for tid, _fecha, mid in filas:
            tm = tiempos.get(tid)
            if not tm:
                continue
            m = mano.setdefault(mid, {"horas": 0.0, "importe": 0.0, "sin_precio": False, "trabajos": set()})
            m["horas"] += tm["horas"]; m["trabajos"].add(tid)
            if tm["importe"] is None:
                m["sin_precio"] = True
            else:
                m["importe"] += tm["importe"]
        con_materiales = consumos.materiales_de_trabajos([f[0] for f in filas])
        trabajos_con_coste = {}
        for tid, _fecha, mid in filas:
            if tid in tiempos or tid in con_materiales:
                trabajos_con_coste.setdefault(mid, set()).add(tid)
        totales = {}
        for maq in {m["id"] for m in maquinas.listar_maquinas()}:
            acum = {"importe": 0.0, "sin_precio": False, "trabajos": 0, "articulos": {},
                    "horas": 0.0, "mano_obra": 0.0, "mano_sin_precio": False}
            ids_trab = set()
            for sub in maquinas.descendientes_ids(maq):
                p = propios.get(sub)
                if p:
                    acum["importe"] += p["importe"]; acum["sin_precio"] |= p["sin_precio"]
                    for clave, a in p["articulos"].items():
                        d = acum["articulos"].setdefault(clave, {"cantidad": 0.0, "importe": 0.0, "sin_precio": False})
                        d["cantidad"] += a["cantidad"]; d["importe"] += a["importe"]; d["sin_precio"] |= a["sin_precio"]
                mo = mano.get(sub)
                if mo:
                    acum["horas"] += mo["horas"]; acum["mano_obra"] += mo["importe"]; acum["mano_sin_precio"] |= mo["sin_precio"]
                ids_trab |= trabajos_con_coste.get(sub, set())
            acum["trabajos"] = len(ids_trab)
            if acum["trabajos"]:
                totales[maq] = acum
        return totales, propios, mano

    def recargar(self):
        self._totales, propios, mano = self._datos()
        rutas = maquinas.mapa_rutas_completas()
        self._orden = sorted(self._totales, key=lambda m: -(self._totales[m]["importe"] + self._totales[m]["mano_obra"]))
        self.tabla_maq.setSortingEnabled(False)
        self.tabla_maq.setRowCount(len(self._orden))
        for fila, mid in enumerate(self._orden):
            d = self._totales[mid]
            item = QTableWidgetItem(rutas.get(mid, str(mid))); item.setData(Qt.ItemDataRole.UserRole, mid)
            self.tabla_maq.setItem(fila, 0, item)
            self.tabla_maq.setItem(fila, 1, _ItemNumero(str(d["trabajos"]), d["trabajos"]))
            self.tabla_maq.setItem(fila, 2, _ItemNumero(f"{d['horas']:.1f}".replace(".", ",") if d["horas"] else "", d["horas"]))
            self.tabla_maq.setItem(fila, 3, _ItemNumero(self._importe(d["mano_obra"], d["mano_sin_precio"]) if d["horas"] else "", d["mano_obra"]))
            self.tabla_maq.setItem(fila, 4, _ItemNumero(self._importe(d["importe"], d["sin_precio"]) if d["articulos"] else "", d["importe"]))
            total = d["importe"] + d["mano_obra"]
            self.tabla_maq.setItem(fila, 5, _ItemNumero(self._importe(total, d["sin_precio"] or d["mano_sin_precio"]), total))
        self.tabla_maq.setSortingEnabled(True)
        self.tabla_maq.sortItems(5, Qt.SortOrder.DescendingOrder)   # las que más cuestan, arriba
        total = sum(p["importe"] for p in propios.values()) + sum(m["importe"] for m in mano.values())
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
        cab = [tt("hdr_maquina", "Máquina"), tt("hdr_trabajos", "Trabajos"), tt("lbl_horas", "Horas"),
               f"{tt('lbl_mano_obra', 'Mano de obra')} ({self.moneda})", f"{tt('lbl_repuestos_corto', 'Repuestos')} ({self.moneda})",
               f"{tt('lbl_total', 'Total')} ({self.moneda})"]
        for c, txt in enumerate(cab): h1.write(0, c, txt, negrita)
        for f, mid in enumerate(self._orden, start=1):
            d = self._totales[mid]
            h1.write(f, 0, rutas.get(mid, str(mid))); h1.write(f, 1, d["trabajos"]); h1.write(f, 2, round(d["horas"], 2))
            h1.write(f, 3, d["mano_obra"], dinero); h1.write(f, 4, d["importe"], dinero)
            h1.write(f, 5, d["mano_obra"] + d["importe"], dinero)
        h1.set_column(0, 0, 45); h1.set_column(1, 5, 16)
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
