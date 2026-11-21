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
"""Proveedores → «📥 Importar tarifa…»: asistente para cargar la tarifa de un proveedor
(Excel/CSV) en dos pasos: fichero y columnas, y el resumen antes de aplicar (enlazados con
la casilla de cambiar el precio del artículo, sin enlazar para enlazar a mano o crear, y
avisos). La lógica está en nucleo/tarifas.py. Solo administradores."""

import os

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QComboBox, QSpinBox,
                             QDoubleSpinBox, QFormLayout, QStackedWidget, QTabWidget, QWidget, QFileDialog,
                             QApplication, QListWidget, QListWidgetItem, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ...idiomas import t
from ..comun import tt
from ...nucleo import tarifas, proveedores, importar, consumos, usuarios

FILAS_VISTA = tarifas.FILAS_VISTA
COLOR_SUBE, COLOR_BAJA = "#c0392b", "#2e8b57"
_pct = tarifas.texto_pct
texto_aviso = tarifas.texto_aviso


class DialogoElegirArticulo(QDialog):
    """Buscador de artículos para enlazar a mano una línea de la tarifa."""
    def __init__(self, parent, referencia, descripcion):
        super().__init__(parent)
        self.setWindowTitle(tt("tar_enlazar_title", "Enlazar con un artículo"))
        self.resize(560, 460)
        self.material_id = None
        l = QVBoxLayout(self)
        l.addWidget(QLabel(tt("tar_enlazar_linea", "Línea de la tarifa: {ref} · {desc}").format(ref=referencia, desc=descripcion)))
        self.txt = QLineEdit()
        self.txt.setPlaceholderText(tt("tar_buscar_articulo", "Buscar por código o nombre…"))
        self.txt.setClearButtonEnabled(True)
        self.txt.textChanged.connect(self._buscar)
        l.addWidget(self.txt)
        self.lista = QListWidget()
        self.lista.itemDoubleClicked.connect(lambda _: self._aceptar())
        l.addWidget(self.lista, 1)
        h = QHBoxLayout()
        h.addStretch()
        bc = QPushButton(t("btn_cancelar")); bc.clicked.connect(self.reject)
        ba = QPushButton(tt("tar_btn_enlazar", "🔗 Enlazar")); ba.clicked.connect(self._aceptar)
        h.addWidget(bc); h.addWidget(ba)
        l.addLayout(h)
        self.txt.setText(descripcion.split(" ")[0] if descripcion else "")
        self._buscar()

    def _buscar(self):
        self.lista.clear()
        for a in tarifas.articulos_para_enlazar(self.txt.text()):
            item = QListWidgetItem(f"{a['codigo']} · {a['nombre']}" if a["codigo"] else a["nombre"])
            item.setData(Qt.ItemDataRole.UserRole, a["id"])
            self.lista.addItem(item)

    def _aceptar(self):
        item = self.lista.currentItem()
        if item is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("tar_msg_elige_articulo", "Elige un artículo de la lista."))
            return
        self.material_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


class DialogoImportarTarifa(QDialog):
    def __init__(self, parent=None, proveedor_id=None):
        super().__init__(parent)
        self.proveedor = proveedores.obtener_proveedor(proveedor_id)
        self.moneda = consumos.moneda()
        self.ruta = None
        self.cabeceras, self.filas, self.fila_cab = [], [], None
        self.enlaces = {}            # referencia -> material_id (a mano)
        self.crear = set()           # referencias normalizadas que se crearán
        self.cambiar = {}            # material_id -> marcado (lo que el usuario cambia)
        self.analisis = None
        self.aplicado = False
        self.setWindowTitle(tt("tar_title", "Importar tarifa de {proveedor}").format(proveedor=self.proveedor["nombre"]))
        self.resize(1000, 680)
        l = QVBoxLayout(self)
        self.pila = QStackedWidget()
        self.pila.addWidget(self._pagina_fichero())
        self.pila.addWidget(self._pagina_resumen())
        l.addWidget(self.pila, 1)

    # ------------------------------------------------------------ paso 1: fichero y columnas
    def _pagina_fichero(self):
        w = QWidget()
        l = QVBoxLayout(w)
        ayuda = QLabel(tt("tar_ayuda", "Elige el fichero de la tarifa (Excel .xlsx o CSV) y di qué columna es la referencia del "
                                       "proveedor y cuál el precio. MantPro recuerda las columnas de cada proveedor para la próxima vez."))
        ayuda.setWordWrap(True)
        l.addWidget(ayuda)
        h = QHBoxLayout()
        self.txt_fichero = QLineEdit(); self.txt_fichero.setReadOnly(True)
        b = QPushButton(tt("tar_btn_fichero", "📂 Elegir fichero…")); b.clicked.connect(self._elegir_fichero)
        h.addWidget(self.txt_fichero, 1); h.addWidget(b)
        l.addLayout(h)

        form = QFormLayout()
        self.combo_hoja = QComboBox(); self.combo_hoja.currentIndexChanged.connect(lambda _: self._leer(auto=True))
        self.lbl_hoja = QLabel(tt("tar_lbl_hoja", "Hoja:"))
        form.addRow(self.lbl_hoja, self.combo_hoja)
        self.spin_cabecera = QSpinBox(); self.spin_cabecera.setRange(1, 100000)
        self.spin_cabecera.setToolTip(tt("tar_tt_cabecera", "Fila del fichero con los nombres de las columnas (las tarifas suelen traer títulos encima)."))
        self.spin_cabecera.editingFinished.connect(lambda: self._leer(auto=False))
        form.addRow(tt("tar_lbl_cabecera", "Fila de cabecera:"), self.spin_cabecera)
        self.spin_descuento = QDoubleSpinBox(); self.spin_descuento.setRange(0, 100); self.spin_descuento.setDecimals(2)
        self.spin_descuento.setSuffix(" %")
        self.spin_descuento.setToolTip(tt("tar_tt_descuento", "Vuestro descuento sobre la tarifa de este proveedor. Se usa en las "
                                                              "líneas que no traen descuento propio. Se guarda en el proveedor."))
        ajustes = tarifas.ajustes(self.proveedor["id"])
        self.spin_descuento.setValue(ajustes["descuento"] or 0)
        form.addRow(tt("tar_lbl_descuento", "Descuento general del proveedor:"), self.spin_descuento)
        l.addLayout(form)

        grupo = QGroupBox(tt("tar_grupo_columnas", "Columnas de la tarifa"))
        rejilla = QGridLayout(grupo)
        self.combos = {}
        for k, (campo, obligatorio) in enumerate(tarifas.CAMPOS):
            etiqueta = tt(f"tar_campo_{campo}", campo) + (" *" if obligatorio else "")
            c = QComboBox()
            self.combos[campo] = c
            rejilla.addWidget(QLabel(etiqueta), k // 2, (k % 2) * 2)
            rejilla.addWidget(c, k // 2, (k % 2) * 2 + 1)
        l.addWidget(grupo)
        nota = QLabel(tt("tar_nota_obligatorios", "* Obligatorias. El precio puede llevar «€» y coma decimal; el descuento, «%»."))
        nota.setWordWrap(True)
        l.addWidget(nota)

        l.addWidget(QLabel("<b>" + tt("tar_vista_previa", "Primeras filas") + "</b>"))
        self.tabla_vista = QTableWidget(0, 0)
        self.tabla_vista.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        l.addWidget(self.tabla_vista, 1)

        h = QHBoxLayout()
        h.addStretch()
        bc = QPushButton(t("btn_cancelar")); bc.clicked.connect(self.reject)
        self.btn_siguiente = QPushButton(tt("tar_btn_siguiente", "Siguiente ▶")); self.btn_siguiente.clicked.connect(self._analizar)
        self.btn_siguiente.setEnabled(False)
        h.addWidget(bc); h.addWidget(self.btn_siguiente)
        l.addLayout(h)
        self.lbl_hoja.setVisible(False); self.combo_hoja.setVisible(False)
        return w

    def _elegir_fichero(self):
        ruta, _ = QFileDialog.getOpenFileName(self, tt("tar_btn_fichero", "📂 Elegir fichero…"), "",
                                              f"{t('imp_filtro_ficheros')} (*.xlsx *.csv *.txt)")
        if ruta:
            self.cargar_fichero(ruta)

    def cargar_fichero(self, ruta):
        """Carga el fichero (también lo usan las pruebas, sin el diálogo de abrir)."""
        try:
            hojas = importar.hojas(ruta)
        except importar.ErrorLectura as e:
            QMessageBox.warning(self, tt("aviso", "Aviso"), str(e))
            return False
        self.ruta = ruta
        self.txt_fichero.setText(ruta)
        self.combo_hoja.blockSignals(True)
        self.combo_hoja.clear()
        self.combo_hoja.addItems(hojas)
        self.combo_hoja.blockSignals(False)
        self.lbl_hoja.setVisible(len(hojas) > 1); self.combo_hoja.setVisible(len(hojas) > 1)
        return self._leer(auto=True)

    def _leer(self, auto):
        """Lee el fichero. [auto]: la fila de cabecera la busca MantPro (la guardada del
        proveedor o la que más columnas reconoce); si no, la del recuadro."""
        if not self.ruta:
            return False
        fila = None if auto else self.spin_cabecera.value()
        hoja = self.combo_hoja.currentText() or None
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            try:
                self.cabeceras, self.filas, self.fila_cab, mapeo = tarifas.leer_para(self.proveedor["id"], self.ruta,
                                                                                     hoja, fila)
            except importar.ErrorLectura as e:
                QMessageBox.warning(self, tt("aviso", "Aviso"), str(e))
                return False
        finally:
            QApplication.restoreOverrideCursor()
        self.spin_cabecera.blockSignals(True)
        self.spin_cabecera.setValue(self.fila_cab)
        self.spin_cabecera.blockSignals(False)
        for campo, c in self.combos.items():
            c.clear()
            c.addItem(tt("tar_ninguna", "— ninguna —"), None)
            for j, cab in enumerate(self.cabeceras):
                c.addItem(cab, j)
            if campo in mapeo:
                c.setCurrentIndex(c.findData(mapeo[campo]))
        self.tabla_vista.setColumnCount(len(self.cabeceras))
        self.tabla_vista.setHorizontalHeaderLabels(self.cabeceras)
        self.tabla_vista.setRowCount(min(8, len(self.filas)))
        for i, (_, valores) in enumerate(self.filas[:8]):
            for j, v in enumerate(valores):
                self.tabla_vista.setItem(i, j, QTableWidgetItem(importar.texto_celda(v)))
        self.btn_siguiente.setEnabled(True)
        return True

    def mapeo(self):
        return {campo: c.currentData() for campo, c in self.combos.items() if c.currentData() is not None}

    def _descuento_general(self):
        return self.spin_descuento.value() or None

    def _analizar(self):
        mapeo = self.mapeo()
        faltan = [tt(f"tar_campo_{c}", c) for c in tarifas.faltan_columnas(mapeo)]
        if faltan:
            QMessageBox.warning(self, tt("aviso", "Aviso"),
                                tt("tar_msg_faltan_columnas", "Falta elegir la columna de: {campos}.").format(campos=", ".join(faltan)))
            return
        if tarifas.columna_repetida(mapeo):
            QMessageBox.warning(self, tt("aviso", "Aviso"),
                                tt("tar_msg_columna_repetida", "Una misma columna está elegida para dos datos distintos."))
            return
        # El descuento general se guarda antes de analizar: el análisis lo lee del proveedor
        tarifas.guardar_ajustes(self.proveedor["id"], self._descuento_general(),
                                tarifas.mapeo_a_guardar(self.cabeceras, mapeo, self.fila_cab))
        self.refrescar_resumen()
        self.pila.setCurrentIndex(1)

    # ------------------------------------------------------------ paso 2: resumen
    def _pagina_resumen(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setWordWrap(True)
        l.addWidget(self.lbl_resumen)
        self.pestanas = QTabWidget()

        # Enlazados
        we = QWidget(); le = QVBoxLayout(we)
        self.tabla_enl = self._tabla([tt("tar_hdr_cambiar", "CAMBIAR PRECIO"), tt("tar_hdr_referencia", "REFERENCIA"),
                                      tt("tar_hdr_articulo", "ARTÍCULO"), tt("tar_hdr_precio_actual", "PRECIO ACTUAL"),
                                      tt("tar_hdr_tarifa", "TARIFA"), tt("tar_hdr_dto", "DTO. %"), tt("tar_hdr_neto", "NETO"),
                                      tt("tar_hdr_variacion", "VARIACIÓN"), tt("tar_hdr_enlace", "ENLACE")])
        self.tabla_enl.itemChanged.connect(self._marca_cambiar)
        le.addWidget(self.tabla_enl, 1)
        h = QHBoxLayout()
        b1 = QPushButton(tt("tar_btn_marcar_todos", "☑ Marcar todos")); b1.clicked.connect(lambda: self._marcar_todos(True))
        b2 = QPushButton(tt("tar_btn_desmarcar_todos", "☐ Desmarcar todos")); b2.clicked.connect(lambda: self._marcar_todos(False))
        h.addWidget(b1); h.addWidget(b2); h.addStretch()
        nota = QLabel(tt("tar_nota_cambiar", "Marcado: el precio del artículo (el de los costes) pasa a ser el neto. "
                                             "Todos quedan en el historial de precios del proveedor."))
        nota.setWordWrap(True)
        le.addLayout(h); le.addWidget(nota)
        self.pestanas.addTab(we, "")

        # Sin enlazar
        ws = QWidget(); ls = QVBoxLayout(ws)
        self.txt_buscar = QLineEdit(); self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.setPlaceholderText(tt("tar_buscar_tarifa", "Buscar en la tarifa por referencia o descripción…"))
        self.txt_buscar.textChanged.connect(lambda _: self._pintar_sin_enlazar())
        ls.addWidget(self.txt_buscar)
        self.tabla_sin = self._tabla([tt("tar_hdr_crear", "CREAR"), tt("tar_hdr_referencia", "REFERENCIA"),
                                      tt("tar_hdr_descripcion", "DESCRIPCIÓN"), tt("tar_hdr_neto", "NETO")])
        self.tabla_sin.itemChanged.connect(self._marca_crear)
        ls.addWidget(self.tabla_sin, 1)
        self.lbl_sin = QLabel(); self.lbl_sin.setWordWrap(True)
        ls.addWidget(self.lbl_sin)
        h = QHBoxLayout()
        b = QPushButton(tt("tar_btn_enlazar_articulo", "🔗 Enlazar con un artículo…")); b.clicked.connect(self._enlazar)
        h.addWidget(b); h.addStretch()
        ls.addLayout(h)
        self.pestanas.addTab(ws, "")

        # Avisos
        self.tabla_avisos = self._tabla([tt("tar_hdr_fila", "FILA"), tt("tar_hdr_referencia", "REFERENCIA"),
                                         tt("tar_hdr_aviso", "AVISO")])
        self.pestanas.addTab(self.tabla_avisos, "")
        l.addWidget(self.pestanas, 1)

        h = QHBoxLayout()
        ba = QPushButton(tt("tar_btn_atras", "◀ Atrás")); ba.clicked.connect(lambda: self.pila.setCurrentIndex(0))
        h.addWidget(ba); h.addStretch()
        bc = QPushButton(t("btn_cancelar")); bc.clicked.connect(self.reject)
        self.btn_aplicar = QPushButton(tt("tar_btn_aplicar", "✅ Aplicar tarifa")); self.btn_aplicar.clicked.connect(self.aplicar)
        h.addWidget(bc); h.addWidget(self.btn_aplicar)
        l.addLayout(h)
        return w

    def _tabla(self, cabeceras):
        tb = QTableWidget(0, len(cabeceras))
        tb.setHorizontalHeaderLabels(cabeceras)
        tb.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tb.horizontalHeader().setStretchLastSection(True)
        tb.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tb.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tb.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tb.setAlternatingRowColors(True)
        return tb

    def _importe(self, valor):
        return consumos.formato_importe(valor, self.moneda) if valor is not None else "—"

    def refrescar_resumen(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.analisis = tarifas.analizar(self.proveedor["id"], self.filas, self.mapeo(), self.enlaces)
        finally:
            QApplication.restoreOverrideCursor()
        a = self.analisis
        tb = self.tabla_enl
        tb.blockSignals(True)
        tb.setRowCount(len(a["enlazados"]))
        for i, x in enumerate(a["enlazados"]):
            marcado = self.cambiar.get(x["material_id"], x["cambiar"])
            caja = QTableWidgetItem()
            caja.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            caja.setCheckState(Qt.CheckState.Checked if marcado else Qt.CheckState.Unchecked)
            caja.setData(Qt.ItemDataRole.UserRole, x["material_id"])
            tb.setItem(i, 0, caja)
            var = x["variacion"]
            texto_var, sentido = tarifas.texto_variacion(var)
            nombre = f"{x['codigo']} · {x['nombre']}" if x["codigo"] else x["nombre"]
            valores = (x["referencia"], nombre, self._importe(x["precio_actual"]), self._importe(x["precio_lista"]),
                       _pct(x["descuento"]), self._importe(x["precio"]), texto_var, tarifas.texto_enlace(x["como"]))
            for j, v in enumerate(valores, start=1):
                item = QTableWidgetItem(v)
                if j == 7 and sentido:
                    item.setForeground(QColor(COLOR_SUBE if sentido == "sube" else COLOR_BAJA))
                tb.setItem(i, j, item)
        tb.blockSignals(False)
        self._pintar_sin_enlazar()
        self.tabla_avisos.setRowCount(len(a["avisos"]))
        for i, x in enumerate(a["avisos"]):
            for j, v in enumerate((str(x["fila"]), x["referencia"], texto_aviso(x))):
                self.tabla_avisos.setItem(i, j, QTableWidgetItem(v))
        self.pestanas.setTabText(0, tt("tar_tab_enlazados", "✅ Enlazados ({n})").format(n=len(a["enlazados"])))
        self.pestanas.setTabText(1, tt("tar_tab_sin_enlazar", "❔ Sin enlazar ({n})").format(n=len(a["sin_enlazar"])))
        self.pestanas.setTabText(2, tt("tar_tab_avisos", "⚠️ Avisos ({n})").format(n=len(a["avisos"])))
        self._actualizar_resumen()

    def _actualizar_resumen(self):
        a = self.analisis
        n = tarifas.cuentas(a, self.cambiar, self.crear)
        self.lbl_resumen.setText(tt("tar_resumen", "{enl} artículos de la tarifa están en el almacén ({cambiar} con el precio "
                                                   "marcado para cambiar), {sin} no están ({crear} marcados para crear) y {avisos} "
                                                   "filas tienen avisos.").format(**n))

    def _pintar_sin_enlazar(self):
        if self.analisis is None:
            return
        vista, total = tarifas.buscar_sin_enlazar(self.analisis, self.txt_buscar.text())
        tb = self.tabla_sin
        tb.blockSignals(True)
        tb.setRowCount(len(vista))
        for i, x in enumerate(vista):
            caja = QTableWidgetItem()
            caja.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            caja.setCheckState(Qt.CheckState.Checked if tarifas._ref(x["referencia"]) in self.crear else Qt.CheckState.Unchecked)
            caja.setData(Qt.ItemDataRole.UserRole, x["referencia"])
            caja.setData(Qt.ItemDataRole.UserRole + 1, x["descripcion"])
            tb.setItem(i, 0, caja)
            for j, v in enumerate((x["referencia"], x["descripcion"], self._importe(x["precio"])), start=1):
                tb.setItem(i, j, QTableWidgetItem(v))
        tb.blockSignals(False)
        if total > len(vista):
            self.lbl_sin.setText(tt("tar_mostrando", "Se ven {n} de {total}: usa el buscador para encontrar el resto.").format(
                n=len(vista), total=total))
        else:
            self.lbl_sin.setText(tt("tar_nota_sin_enlazar", "Marca «Crear» para dar de alta el artículo en el almacén principal "
                                                            "(sin stock, con este proveedor como habitual), o enlázalo con uno que ya tengáis."))

    def _marca_cambiar(self, item):
        if item.column() == 0:
            self.cambiar[item.data(Qt.ItemDataRole.UserRole)] = item.checkState() == Qt.CheckState.Checked
            self._actualizar_resumen()

    def _marca_crear(self, item):
        if item.column() == 0:
            ref = tarifas._ref(item.data(Qt.ItemDataRole.UserRole))
            if item.checkState() == Qt.CheckState.Checked:
                self.crear.add(ref)
            else:
                self.crear.discard(ref)
            self._actualizar_resumen()

    def _marcar_todos(self, marcar):
        for x in self.analisis["enlazados"]:
            self.cambiar[x["material_id"]] = marcar
        self.refrescar_resumen()

    def _enlazar(self):
        fila = self.tabla_sin.currentRow()
        item = self.tabla_sin.item(fila, 0) if fila >= 0 else None
        if item is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("tar_msg_elige_linea", "Elige una línea de la tarifa."))
            return
        dlg = DialogoElegirArticulo(self, item.data(Qt.ItemDataRole.UserRole), item.data(Qt.ItemDataRole.UserRole + 1))
        if dlg.exec() and dlg.material_id:
            self.enlazar(item.data(Qt.ItemDataRole.UserRole), dlg.material_id)

    def enlazar(self, referencia, material_id):
        self.enlaces[referencia] = material_id
        self.crear.discard(tarifas._ref(referencia))
        self.refrescar_resumen()

    # ------------------------------------------------------------ aplicar
    def aplicar(self, confirmar=True):
        a = self.analisis
        cambiar, crear = tarifas.a_cambiar(a, self.cambiar), tarifas.a_crear(a, self.crear)
        if not a["enlazados"] and not crear:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt(
                "tar_msg_nada", "Ningún artículo de la tarifa está en el almacén ni se ha marcado para crear: no hay nada que aplicar."))
            return
        if confirmar and QMessageBox.question(self, tt("tar_btn_aplicar", "✅ Aplicar tarifa"), tt(
                "tar_msg_confirmar", "Se guardarán {enl} precios en el historial del proveedor, se cambiará el precio de {cambiar} "
                                     "artículos y se crearán {crear} artículos nuevos. ¿Seguir?").format(
                enl=len(a["enlazados"]) + len(crear), cambiar=len(cambiar), crear=len(crear))) != QMessageBox.StandardButton.Yes:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            r = tarifas.aplicar(self.proveedor["id"], self.filas, self.mapeo(), cambiar_precio=cambiar, enlaces=self.enlaces,
                                crear=crear, fichero=os.path.basename(self.ruta or ""), usuario_id=usuarios.id_actual(),
                                usuario_nombre=usuarios.nombre_actual())
        finally:
            QApplication.restoreOverrideCursor()
        self.aplicado = True
        self.resultado = r
        if confirmar:
            QMessageBox.information(self, tt("tar_btn_aplicar", "✅ Aplicar tarifa"), tt(
                "tar_msg_hecho", "Tarifa aplicada: {rel} artículos con su precio de este proveedor ({hist} precios nuevos en el "
                                 "historial), {cambiados} precios de artículo cambiados y {creados} artículos nuevos.").format(
                rel=r["relaciones"], hist=r["historial"], cambiados=r["precios_cambiados"], creados=r["creados"]))
        self.accept()
