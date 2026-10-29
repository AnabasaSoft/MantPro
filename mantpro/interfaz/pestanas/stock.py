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

"""Pestañas «Stock de almacén» y «Stock bajo mínimo»."""

import os
import shutil
import re
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
                                Image as PDFImage)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QListWidget, QMessageBox, QTableWidget, QHeaderView, QAbstractItemView,
                             QComboBox, QMenu, QSplitter)
from PyQt6.QtCore import QDate, Qt, QItemSelection, QItemSelectionModel
from PyQt6.QtGui import QColor, QBrush

from ... import idiomas
from ...idiomas import t
from ..comun import traducir_motivo_movimiento, tt
from ..dialogos.almacen import (DialogoHistorialAlmacen, DialogoConfigurarAlmacen, DialogoEditarMaterial,
                                DialogoExportarStock, DialogoMovimientoStock,
                                DialogoSeleccionarUbicacion)
from ..widgets.ordenables import _ItemTablaOrdenable, _clave_orden_ubicacion
from ...nucleo import usuarios, almacen
from ...nucleo.rutas import DATA_DIR

class PestanaStock:
    """Pestañas «Stock de almacén» y «Stock bajo mínimo».

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    # ==========================================
    # STOCK DE ALMACÉN
    # ==========================================
    def init_stock_tab(self):
        l = QVBoxLayout()

        barra = QHBoxLayout()
        self.stock_buscar = QLineEdit(); self.stock_buscar.setPlaceholderText(tt("ph_buscar_material", "Buscar material..."))
        self.stock_buscar.setMinimumWidth(170)
        self.stock_buscar.textChanged.connect(self.refresh_stock)
        barra.addWidget(self.stock_buscar, 1)
        barra.addWidget(QLabel(tt("lbl_zona", "Zona")))
        self.combo_zona_stock = QComboBox()
        self.combo_zona_stock.currentIndexChanged.connect(self.refresh_stock)
        barra.addWidget(self.combo_zona_stock)
        btn_add = QPushButton(tt("btn_add_material", "➕ Añadir material")); btn_add.clicked.connect(self.stock_anadir_material)
        btn_edit = QPushButton(tt("btn_editar_material", "✏️ Editar")); btn_edit.clicked.connect(self.stock_editar_material)
        btn_del = QPushButton(tt("btn_borrar_material", "🗑️ Eliminar")); btn_del.setStyleSheet("background-color:#c0392b; color:white;"); btn_del.clicked.connect(lambda: self.stock_borrar_material())
        btn_entrada = QPushButton(tt("btn_entrada_stock", "📥 Entrada")); btn_entrada.setStyleSheet("background-color:#27ae60; color:white;"); btn_entrada.clicked.connect(lambda: self.stock_registrar_movimiento("entrada"))
        btn_salida = QPushButton(tt("btn_salida_stock", "📤 Salida")); btn_salida.setStyleSheet("background-color:#d35400; color:white;"); btn_salida.clicked.connect(lambda: self.stock_registrar_movimiento("salida"))
        btn_exportar = QPushButton(tt("btn_exportar_stock", "📄 Exportar")); btn_exportar.clicked.connect(lambda: self.stock_exportar())
        btn_historial = QPushButton(tt("btn_historial_almacen", "📜 Historial")); btn_historial.clicked.connect(self.stock_ver_historial)
        for b in (btn_add, btn_edit, btn_del, btn_entrada, btn_salida, btn_exportar, btn_historial): barra.addWidget(b)
        self.btn_configurar_almacen = QPushButton(tt("btn_configurar_almacen", "⚙️ Configurar almacén"))
        self.btn_configurar_almacen.clicked.connect(self.stock_configurar_almacen)
        barra.addWidget(self.btn_configurar_almacen)
        l.addLayout(barra)

        split = QSplitter(Qt.Orientation.Vertical)
        self.tabla_stock = QTableWidget(0, 6)
        self.tabla_stock.setHorizontalHeaderLabels([
            tt("hdr_codigo", "CÓDIGO"), tt("hdr_material", "MATERIAL"), tt("hdr_ubicacion", "UBICACIÓN"),
            tt("hdr_stock", "STOCK"), tt("hdr_minimo", "MÍNIMO"), tt("hdr_unidad", "UNIDAD")])
        self.tabla_stock.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_stock.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # Por defecto, ordenada por ubicación (como se recorre el almacén); si
        # el usuario pulsa otra cabecera, se respeta su elección al recargar.
        self.tabla_stock.horizontalHeader().setSortIndicator(2, Qt.SortOrder.AscendingOrder)
        self.tabla_stock.setSortingEnabled(True)
        self.tabla_stock.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_stock.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tabla_stock.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_stock.setAlternatingRowColors(True)
        self.tabla_stock.itemSelectionChanged.connect(self.refresh_historial_stock)
        self.tabla_stock.itemDoubleClicked.connect(lambda _: self.stock_editar_material())
        self.tabla_stock.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_stock.customContextMenuRequested.connect(self._menu_contextual_stock)
        split.addWidget(self.tabla_stock)

        panel_hist = QWidget(); vh = QVBoxLayout(panel_hist)
        self.lbl_historial_stock = QLabel(tt("lbl_historial_movimientos", "Historial de movimientos"))
        vh.addWidget(self.lbl_historial_stock)
        self.lista_historial_stock = QListWidget()
        vh.addWidget(self.lista_historial_stock)
        split.addWidget(panel_hist)
        split.setStretchFactor(0, 3); split.setStretchFactor(1, 1)
        l.addWidget(split)

        self.tab_stock.setLayout(l)
        self._cargar_zonas_stock()

    def _cargar_zonas_stock(self):
        """Rellena el desplegable de zonas de la pestaña de stock, conservando
        la zona seleccionada si sigue existiendo (o "Todas las zonas" si no)."""
        if not hasattr(self, "combo_zona_stock"): return
        zona_previa = self.combo_zona_stock.currentData()
        self.combo_zona_stock.blockSignals(True)
        self.combo_zona_stock.clear()
        self.combo_zona_stock.addItem(tt("txt_todas_zonas", "Todas las zonas"), None)
        for zona in almacen.listar_zonas():
            self.combo_zona_stock.addItem(zona["nombre"], zona["id"])
        idx = self.combo_zona_stock.findData(zona_previa)
        self.combo_zona_stock.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_zona_stock.blockSignals(False)

    def init_stock_alertas_tab(self):
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_stock_bajo_minimo", "Materiales sin stock o por debajo del mínimo establecido")))
        self.tabla_stock_alertas = QTableWidget(0, 6)
        self.tabla_stock_alertas.setHorizontalHeaderLabels([
            tt("hdr_codigo", "CÓDIGO"), tt("hdr_material", "MATERIAL"), tt("hdr_ubicacion", "UBICACIÓN"),
            tt("hdr_stock", "STOCK"), tt("hdr_minimo", "MÍNIMO"), tt("hdr_unidad", "UNIDAD")])
        self.tabla_stock_alertas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_stock_alertas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla_stock_alertas.setSortingEnabled(True)
        self.tabla_stock_alertas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_stock_alertas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_stock_alertas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_stock_alertas.setAlternatingRowColors(True)
        self.tabla_stock_alertas.itemDoubleClicked.connect(lambda _: self.stock_alerta_ir_a_material())
        l.addWidget(self.tabla_stock_alertas)

        barra = QHBoxLayout()
        btn_ir = QPushButton(tt("btn_ir_a_material", "🔎 Ver en Stock de almacén")); btn_ir.clicked.connect(self.stock_alerta_ir_a_material)
        btn_entrada = QPushButton(tt("btn_entrada_stock", "📥 Entrada")); btn_entrada.setStyleSheet("background-color:#27ae60; color:white;")
        btn_entrada.clicked.connect(self.stock_alerta_entrada)
        btn_exportar = QPushButton(tt("btn_exportar_stock", "📄 Exportar"))
        btn_exportar.clicked.connect(lambda: self.stock_exportar(solo_bajo_minimo=True))
        barra.addWidget(btn_ir); barra.addWidget(btn_entrada); barra.addWidget(btn_exportar)
        l.addLayout(barra)

        self.tab_stock_alertas.setLayout(l)

    @staticmethod
    def _color_stock(actual, minimo):
        """Rojo por debajo del mínimo, verde por encima, color por defecto si coincide."""
        if actual < minimo:
            return QColor("#e74c3c")
        if actual > minimo:
            return QColor("#27ae60")
        return None

    def _texto_ubicacion(self, seccion_id):
        return almacen.obtener_ubicacion_texto(
            seccion_id, tt("txt_balda_num", "Balda {n}"), tt("txt_hueco_suelo_corto", "Hueco de suelo"))

    def _material_seleccionado_alerta(self):
        fila = self.tabla_stock_alertas.currentRow()
        if fila < 0: return None
        return self.tabla_stock_alertas.item(fila, 0).data(Qt.ItemDataRole.UserRole)

    def refresh_stock_alertas(self):
        if not hasattr(self, "tabla_stock_alertas"): return
        materiales = almacen.materiales_bajo_minimo()
        header = self.tabla_stock_alertas.horizontalHeader()
        # Al pulsar una cabecera para ordenar, Qt guarda esa columna y sentido en
        # el propio header; los recuperamos para que el orden elegido por el
        # usuario sobreviva a los refrescos automáticos de la tabla en vez de
        # volver siempre al orden natural de la base de datos.
        col_orden, orden = header.sortIndicatorSection(), header.sortIndicatorOrder()
        self.tabla_stock_alertas.setSortingEnabled(False)
        self.tabla_stock_alertas.setRowCount(len(materiales))
        for fila, m in enumerate(materiales):
            ubicacion = self._texto_ubicacion(m.get("seccion_id"))
            valores = [m.get("codigo") or "", m["nombre"], ubicacion,
                       f"{m['stock_actual']:g}", f"{m['stock_minimo']:g}", m.get("unidad") or ""]
            claves = {2: _clave_orden_ubicacion(ubicacion, m["nombre"]), 3: m["stock_actual"], 4: m["stock_minimo"]}
            color = self._color_stock(m["stock_actual"], m["stock_minimo"])
            for col, val in enumerate(valores):
                item = _ItemTablaOrdenable(val)
                if col in claves: item.setData(Qt.ItemDataRole.UserRole + 1, claves[col])
                if col == 0: item.setData(Qt.ItemDataRole.UserRole, m["id"])
                if col == 3 and color is not None: item.setForeground(QBrush(color))
                self.tabla_stock_alertas.setItem(fila, col, item)
        self.tabla_stock_alertas.setSortingEnabled(True)
        if col_orden >= 0: self.tabla_stock_alertas.sortItems(col_orden, orden)
        if hasattr(self, "tabs") and hasattr(self, "tab_stock_alertas"):
            idx = self.tabs.indexOf(self.tab_stock_alertas)
            if idx >= 0:
                sufijo = f" ({len(materiales)})" if materiales else ""
                self.tabs.setTabText(idx, tt("tab_stock_alertas", "⚠️ Stock bajo mínimo") + sufijo)

    def stock_alerta_ir_a_material(self):
        material_id = self._material_seleccionado_alerta()
        if not material_id: return
        m = almacen.obtener_material(material_id)
        if not m: return
        self.tabs.setCurrentWidget(self.tab_stock)
        self.stock_buscar.setText(m.get("codigo") or m["nombre"])
        self.refresh_stock()
        for fila in range(self.tabla_stock.rowCount()):
            if self.tabla_stock.item(fila, 0).data(Qt.ItemDataRole.UserRole) == material_id:
                self.tabla_stock.selectRow(fila); break

    def stock_alerta_entrada(self):
        material_id = self._material_seleccionado_alerta()
        if not material_id: return
        m = almacen.obtener_material(material_id)
        if not m: return
        dlg = DialogoMovimientoStock(self, m, "entrada")
        if dlg.exec():
            cantidad, motivo = dlg.get_data()
            almacen.registrar_movimiento(material_id, "entrada", cantidad,
                                          usuarios.id_actual(), usuarios.nombre_actual(), motivo)
            self.refresh_stock(); self.refresh_stock_alertas()

    def _material_seleccionado(self):
        fila = self.tabla_stock.currentRow()
        if fila < 0: return None
        return self.tabla_stock.item(fila, 0).data(Qt.ItemDataRole.UserRole)

    def _materiales_seleccionados(self):
        filas = {i.row() for i in self.tabla_stock.selectedIndexes()}
        return [self.tabla_stock.item(f, 0).data(Qt.ItemDataRole.UserRole) for f in sorted(filas)]

    def _menu_contextual_stock(self, pos):
        ids = self._materiales_seleccionados()
        if not ids: return
        menu = QMenu(self)
        if len(ids) == 1:
            accion_editar = menu.addAction(tt("btn_editar_material", "✏️ Editar"))
            accion_entrada = menu.addAction(tt("btn_entrada_stock", "📥 Entrada"))
            accion_salida = menu.addAction(tt("btn_salida_stock", "📤 Salida"))
            menu.addSeparator()
        accion_mover = menu.addAction(tt("btn_mover_material", "📦 Mover a..."))
        accion_borrar = menu.addAction(tt("btn_borrar_material", "🗑️ Eliminar"))
        elegida = menu.exec(self.tabla_stock.viewport().mapToGlobal(pos))
        if elegida is None: return
        if len(ids) == 1:
            if elegida == accion_editar: self.stock_editar_material()
            elif elegida == accion_entrada: self.stock_registrar_movimiento("entrada")
            elif elegida == accion_salida: self.stock_registrar_movimiento("salida")
        if elegida == accion_mover: self.stock_mover_materiales(ids)
        elif elegida == accion_borrar: self.stock_borrar_material(ids)

    def refresh_stock(self):
        if not hasattr(self, "tabla_stock"): return
        texto = self.stock_buscar.text().strip() if hasattr(self, "stock_buscar") else ""
        zona_id = self.combo_zona_stock.currentData() if hasattr(self, "combo_zona_stock") else None
        materiales = almacen.listar_materiales(texto or None, zona_id)
        # La selección se guarda por id de material, no por número de fila:
        # al reescribir y reordenar la tabla, la misma fila pasa a ser otro
        # material y la barra de selección saltaba a uno cualquiera.
        id_actual = self._material_seleccionado()
        ids_sel = set(self._materiales_seleccionados())
        self.tabla_stock.blockSignals(True)
        header = self.tabla_stock.horizontalHeader()
        col_orden, orden = header.sortIndicatorSection(), header.sortIndicatorOrder()
        self.tabla_stock.setSortingEnabled(False)
        self.tabla_stock.setRowCount(len(materiales))
        for fila, m in enumerate(materiales):
            ubicacion = self._texto_ubicacion(m.get("seccion_id"))
            valores = [m.get("codigo") or "", m["nombre"], ubicacion,
                       f"{m['stock_actual']:g}", f"{m['stock_minimo']:g}", m.get("unidad") or ""]
            claves = {2: _clave_orden_ubicacion(ubicacion, m["nombre"]), 3: m["stock_actual"], 4: m["stock_minimo"]}
            color = self._color_stock(m["stock_actual"], m["stock_minimo"])
            for col, val in enumerate(valores):
                item = _ItemTablaOrdenable(val)
                if col in claves: item.setData(Qt.ItemDataRole.UserRole + 1, claves[col])
                if col == 0: item.setData(Qt.ItemDataRole.UserRole, m["id"])
                if col == 3 and color is not None: item.setForeground(QBrush(color))
                self.tabla_stock.setItem(fila, col, item)
        self.tabla_stock.setSortingEnabled(True)
        if col_orden >= 0: self.tabla_stock.sortItems(col_orden, orden)
        self._restaurar_seleccion_stock(id_actual, ids_sel)
        self.tabla_stock.blockSignals(False)
        if hasattr(self, "btn_configurar_almacen"):
            self.btn_configurar_almacen.setVisible(usuarios.es_admin())
        self.refresh_historial_stock()
        self.refresh_stock_alertas()

    def _restaurar_seleccion_stock(self, id_actual, ids_sel):
        tabla = self.tabla_stock
        tabla.clearSelection()
        tabla.setCurrentItem(None)
        if not ids_sel and id_actual is None:
            return
        modelo, sel = tabla.selectionModel(), QItemSelection()
        fila_actual = -1
        for fila in range(tabla.rowCount()):
            mid = tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)
            if mid in ids_sel:
                sel.select(tabla.model().index(fila, 0), tabla.model().index(fila, tabla.columnCount() - 1))
            if mid == id_actual:
                fila_actual = fila
        if fila_actual >= 0:
            modelo.setCurrentIndex(tabla.model().index(fila_actual, 0), QItemSelectionModel.SelectionFlag.NoUpdate)
            tabla.scrollToItem(tabla.item(fila_actual, 0))
        modelo.select(sel, QItemSelectionModel.SelectionFlag.Select)

    def refresh_historial_stock(self):
        if not hasattr(self, "lista_historial_stock"): return
        self.lista_historial_stock.clear()
        self.lbl_historial_stock.setText(tt("lbl_historial_movimientos", "Historial de movimientos"))
        material_id = self._material_seleccionado()
        if not material_id: return
        # El nombre del artículo, a la vista: sin él, un traslado ("De Estantería
        # 11 > Balda B a Estantería 12 > Balda C") no dice qué se ha movido.
        material = almacen.obtener_material(material_id) or {}
        nombre = material.get("nombre") or ""
        self.lbl_historial_stock.setText(tt("lbl_historial_de", "Historial de movimientos: {nombre}").format(nombre=nombre))
        for mov in almacen.obtener_movimientos(material_id, limite=20):
            if mov["tipo"] == "traslado":
                texto = f"🔀 {mov['fecha']}   {nombre}: {mov.get('motivo') or ''}   —   {mov.get('usuario_nombre') or ''}"
            else:
                icono = "📥" if mov["tipo"] == "entrada" else "📤"
                texto = f"{icono} {mov['fecha']}   {mov['cantidad']:g}   —   {mov.get('usuario_nombre') or ''}"
                if mov.get("motivo"): texto += f"   ({traducir_motivo_movimiento(mov['motivo'])})"
            self.lista_historial_stock.addItem(texto)

    def stock_ver_historial(self):
        DialogoHistorialAlmacen(self, al_elegir_material=self._ir_a_material_stock).exec()

    def _ir_a_material_stock(self, material_id):
        """Selecciona el artículo en la tabla (quitando filtros si no está a la vista)."""
        for _ in range(2):
            for fila in range(self.tabla_stock.rowCount()):
                item = self.tabla_stock.item(fila, 0)
                if item is not None and item.data(Qt.ItemDataRole.UserRole) == material_id:
                    self.tabla_stock.selectRow(fila)
                    self.tabla_stock.scrollToItem(item)
                    return
            self.stock_buscar.clear(); self.combo_zona_stock.setCurrentIndex(0); self.refresh_stock()

    # ------------------------------------------------------- exportar stock
    @staticmethod
    def _bajo_minimo(m):
        # Mismo criterio que almacen.materiales_bajo_minimo()
        return m["stock_actual"] <= 0 or m["stock_actual"] < m["stock_minimo"]

    def stock_exportar(self, solo_bajo_minimo=False):
        zona_actual = self.combo_zona_stock.currentData() if hasattr(self, "combo_zona_stock") else None
        dlg = DialogoExportarStock(self, zona_actual)
        if solo_bajo_minimo:
            dlg.setWindowTitle(tt("title_exportar_bajo_minimo", "Exportar stock bajo mínimo"))
        if not dlg.exec(): return
        formato, zona_id, est_id, ambito = dlg.get_data()

        materiales = almacen.listar_materiales(None, zona_id, est_id)
        if solo_bajo_minimo:
            materiales = [m for m in materiales if self._bajo_minimo(m)]
        if not materiales:
            QMessageBox.information(self, tt("aviso", "Aviso"),
                tt("msg_stock_sin_materiales", "No hay materiales que exportar con ese filtro.")); return
        for m in materiales:
            m["ubicacion"] = self._texto_ubicacion(m.get("seccion_id"))
        # Ordenados por ubicación (como se recorre el almacén); sin ubicación al final
        materiales.sort(key=lambda m: (not m["ubicacion"], almacen._clave_orden_natural(m["ubicacion"]),
                                       almacen._clave_orden_natural(m["nombre"])))

        titulo = (tt("titulo_informe_bajo_minimo", "Stock bajo mínimo") if solo_bajo_minimo
                  else tt("titulo_informe_stock", "Stock de almacén"))
        if ambito: titulo += f" — {ambito}"
        sufijo = re.sub(r'[^\w-]+', '_', ambito).strip('_') if ambito else ""
        base = "Stock_bajo_minimo" if solo_bajo_minimo else "Stock"
        nombre_defecto = f"{base}{'_' + sufijo if sufijo else ''}_{QDate.currentDate().toString('yyyyMMdd')}.{formato}"
        filtros = {"pdf": "PDF (*.pdf)", "csv": "CSV (*.csv)", "xlsx": "Excel (*.xlsx)"}
        archivo = self.guardar_archivo_dialogo(tt("title_exportar_stock", "Exportar stock de almacén"),
                                               nombre_defecto, filtros[formato])
        if not archivo: return
        if not archivo.lower().endswith("." + formato): archivo += "." + formato

        cabeceras = [tt("hdr_codigo", "CÓDIGO"), tt("hdr_material", "MATERIAL"), tt("hdr_ubicacion", "UBICACIÓN"),
                     tt("hdr_stock", "STOCK"), tt("hdr_minimo", "MÍNIMO"), tt("hdr_unidad", "UNIDAD")]
        n_bajo = sum(self._bajo_minimo(m) for m in materiales)
        resumen = tt("txt_resumen_stock", "{n} materiales · {b} bajo el mínimo").format(n=len(materiales), b=n_bajo)
        fecha = tt("txt_fecha_informe", "Fecha: {fecha}").format(
            fecha=idiomas.formato_fecha_localizada(datetime.now().strftime("%Y-%m-%d")))
        try:
            if formato == "csv":
                self._stock_a_csv(archivo, cabeceras, materiales)
            elif formato == "xlsx":
                try: import xlsxwriter  # noqa: F401
                except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
                self._stock_a_excel(archivo, titulo, fecha, resumen, cabeceras, materiales)
            else:
                self._stock_a_pdf(archivo, titulo, fecha, resumen, cabeceras, materiales)
            QMessageBox.information(self, t("title_exportado"),
                tt("msg_stock_exportado", "Stock exportado en:\n{ruta}").format(ruta=archivo))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))

    def _stock_a_csv(self, archivo, cabeceras, materiales):
        with open(archivo, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(cabeceras)
            for m in materiales:
                w.writerow([m.get("codigo") or "", m["nombre"], m["ubicacion"] or "-",
                            f"{m['stock_actual']:g}", f"{m['stock_minimo']:g}", m.get("unidad") or ""])

    def _stock_a_excel(self, archivo, titulo, fecha, resumen, cabeceras, materiales):
        import xlsxwriter
        wb = xlsxwriter.Workbook(archivo)
        ws = wb.add_worksheet(re.sub(r'[\[\]:*?/\\]', '', tt("titulo_informe_stock", "Stock de almacén"))[:31])
        f_tit = wb.add_format({'bold': True, 'font_size': 14})
        f_cab = wb.add_format({'bold': True, 'bg_color': '#3daee9', 'color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        f_txt = wb.add_format({'border': 1, 'valign': 'top'})
        f_num = wb.add_format({'border': 1, 'num_format': '0.##', 'align': 'right'})
        f_num_rojo = wb.add_format({'border': 1, 'num_format': '0.##', 'align': 'right', 'bold': True, 'font_color': '#c0392b'})
        ws.write(0, 0, titulo, f_tit)
        ws.write(1, 0, fecha); ws.write(2, 0, resumen)
        fila0 = 4
        for col, txt in enumerate(cabeceras): ws.write(fila0, col, txt, f_cab)
        for i, m in enumerate(materiales, start=fila0 + 1):
            ws.write(i, 0, m.get("codigo") or "", f_txt)
            ws.write(i, 1, m["nombre"], f_txt)
            ws.write(i, 2, m["ubicacion"] or "-", f_txt)
            ws.write_number(i, 3, m["stock_actual"], f_num_rojo if self._bajo_minimo(m) else f_num)
            ws.write_number(i, 4, m["stock_minimo"], f_num)
            ws.write(i, 5, m.get("unidad") or "", f_txt)
        for col, ancho in enumerate((12, 40, 38, 10, 10, 10)): ws.set_column(col, col, ancho)
        ws.freeze_panes(fila0 + 1, 0)
        ws.autofilter(fila0, 0, fila0 + len(materiales), len(cabeceras) - 1)
        wb.close()

    def _stock_a_pdf(self, archivo, titulo, fecha, resumen, cabeceras, materiales):
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(archivo, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        celda = ParagraphStyle("CeldaStock", parent=styles["BodyText"], fontSize=9, leading=11)
        celda_cab = ParagraphStyle("CabStock", parent=celda, textColor=colors.whitesmoke, fontName="Helvetica-Bold", fontSize=8)
        celda_num = ParagraphStyle("NumStock", parent=celda, alignment=2)
        celda_rojo = ParagraphStyle("RojoStock", parent=celda_num, textColor=colors.HexColor("#c0392b"), fontName="Helvetica-Bold")
        esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        elementos = []
        ruta_logo = os.path.join(DATA_DIR, "Logo.jpg")
        if os.path.exists(ruta_logo):
            try:
                logo = PDFImage(ruta_logo, width=4*cm, height=2*cm); logo.hAlign = 'LEFT'; logo.keepAspectRatio = True
                elementos += [logo, Spacer(1, 8)]
            except Exception: pass
        elementos += [Paragraph(esc(titulo), styles["Title"]),
                      Paragraph(esc(fecha) + " &nbsp;·&nbsp; " + esc(resumen), styles["Normal"]), Spacer(1, 10)]
        datos = [[Paragraph(esc(c), celda_cab) for c in cabeceras]]
        for m in materiales:
            datos.append([Paragraph(esc(m.get("codigo") or ""), celda), Paragraph(esc(m["nombre"]), celda),
                          Paragraph(esc(m["ubicacion"] or "-"), celda),
                          Paragraph(f"{m['stock_actual']:g}", celda_rojo if self._bajo_minimo(m) else celda_num),
                          Paragraph(f"{m['stock_minimo']:g}", celda_num), Paragraph(esc(m.get("unidad") or ""), celda)])
        tabla = Table(datos, colWidths=[1.9*cm, 5.0*cm, 4.6*cm, 1.7*cm, 2.6*cm, 2.2*cm], repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3daee9")),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6f9")]),
        ]))
        elementos.append(tabla)
        doc.build(elementos)

    def _guardar_foto_material(self, ruta_origen):
        if not ruta_origen: return None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nuevo = f"almacen_{ts}{os.path.splitext(ruta_origen)[1]}"
        destino = os.path.join(self.carpeta_fotos, nuevo)
        try:
            shutil.copy2(ruta_origen, destino)
            return nuevo
        except Exception:
            return None

    def stock_anadir_material(self):
        dlg = DialogoEditarMaterial(self)
        if dlg.exec():
            d = dlg.get_data()
            if not d["nombre"]: return
            foto_guardada = self._guardar_foto_material(d["ruta_foto_seleccionada"])
            almacen.crear_material(d["codigo"], d["nombre"], d["descripcion"], d["unidad"], d["stock_minimo"],
                                    d["seccion_id"], foto_guardada, d["stock_inicial"],
                                    usuarios.id_actual(), usuarios.nombre_actual())
            self.refresh_stock()

    def stock_editar_material(self):
        material_id = self._material_seleccionado()
        if not material_id:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_material_seleccionado", "Selecciona un material de la lista.")); return
        material = almacen.obtener_material(material_id)
        dlg = DialogoEditarMaterial(self, material)
        if dlg.exec():
            d = dlg.get_data()
            if not d["nombre"]: return
            if not d["ruta_foto_seleccionada"]:
                foto_final = None
            elif os.path.dirname(os.path.abspath(d["ruta_foto_seleccionada"])) == os.path.abspath(self.carpeta_fotos):
                foto_final = os.path.basename(d["ruta_foto_seleccionada"])
            else:
                foto_final = self._guardar_foto_material(d["ruta_foto_seleccionada"])
            almacen.actualizar_material(material_id, d["codigo"], d["nombre"], d["descripcion"], d["unidad"],
                                         d["stock_minimo"], d["seccion_id"], foto_final,
                                         usuarios.id_actual(), usuarios.nombre_actual())
            self.refresh_stock()

    def stock_borrar_material(self, ids=None):
        ids = ids if ids is not None else self._materiales_seleccionados()
        if not ids:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_material_seleccionado", "Selecciona un material de la lista.")); return
        mensaje = (tt("msg_confirmar_borrar_material", "¿Eliminar este material del almacén? Se perderá su historial de movimientos.")
                   if len(ids) == 1 else
                   tt("msg_confirmar_borrar_materiales", "¿Eliminar estos {n} materiales del almacén? Se perderá su historial de movimientos.").format(n=len(ids)))
        if QMessageBox.question(self, tt("aviso", "Aviso"), mensaje) != QMessageBox.StandardButton.Yes:
            return
        for material_id in ids:
            almacen.borrar_material(material_id)
        self.refresh_stock()

    def stock_mover_materiales(self, ids=None):
        ids = ids if ids is not None else self._materiales_seleccionados()
        if not ids:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_material_seleccionado", "Selecciona un material de la lista.")); return
        dlg = DialogoSeleccionarUbicacion(self)
        if not dlg.exec(): return
        seccion_id = dlg.get_seccion_id()
        for material_id in ids:
            m = almacen.obtener_material(material_id)
            if not m: continue
            almacen.actualizar_material(material_id, m.get("codigo") or "", m["nombre"], m.get("descripcion") or "",
                                         m.get("unidad") or "", m.get("stock_minimo") or 0, seccion_id, m.get("foto"),
                                         usuarios.id_actual(), usuarios.nombre_actual())
        self.refresh_stock()

    def stock_registrar_movimiento(self, tipo):
        material_id = self._material_seleccionado()
        if not material_id:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_sin_material_seleccionado", "Selecciona un material de la lista.")); return
        material = almacen.obtener_material(material_id)
        dlg = DialogoMovimientoStock(self, material, tipo)
        if dlg.exec():
            cantidad, motivo = dlg.get_data()
            ok, error = almacen.registrar_movimiento(material_id, tipo, cantidad, usuarios.id_actual(), usuarios.nombre_actual(), motivo)
            if not ok:
                QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_stock_insuficiente", "No hay stock suficiente para esta salida."))
            self.refresh_stock()

    def stock_configurar_almacen(self):
        if not usuarios.es_admin(): return
        DialogoConfigurarAlmacen(self).exec()
        self._cargar_zonas_stock()
        self.refresh_stock()
