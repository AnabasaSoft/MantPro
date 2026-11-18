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

"""Almacén → Pedidos: el pedido sugerido (qué pedir ahora, editable) y la lista de
pedidos guardados, con su envío por correo, WhatsApp, teléfono o impreso y la
marca de recibido. Solo para administradores."""

import os
import re

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QDialogButtonBox, QMessageBox, QComboBox, QDoubleSpinBox,
                             QCheckBox, QTextEdit, QWidget, QApplication, QMenu)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices

from ... import idiomas
from ...idiomas import t, formato_fecha_localizada
from ..comun import tt
from ...nucleo import almacen, almacenes, compras, consumos, proveedores, usuarios
from ...nucleo.rutas import DATA_DIR


def nombres_estado():
    return {compras.ESTADO_PEDIDO: tt("cmp_est_pedido", "Pedido"), compras.ESTADO_PARCIAL: tt("cmp_est_parcial", "Parcial"),
            compras.ESTADO_RECIBIDO: tt("cmp_est_recibido", "Recibido"), compras.ESTADO_CANCELADO: tt("cmp_est_cancelado", "Cancelado")}


def nombres_canal():
    return {"correo": tt("cmp_canal_correo", "Correo"), "whatsapp": tt("cmp_canal_whatsapp", "WhatsApp"),
            "telefono": tt("cmp_canal_telefono", "Teléfono"), "impreso": tt("cmp_canal_impreso", "Impreso")}


def _abrir_url(url):
    QDesktopServices.openUrl(QUrl(url))


def _abrir_fichero(ruta):
    QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))


class _TablaSugerido(QTableWidget):
    """Tabla del pedido sugerido: la barra espaciadora avisa para marcar o desmarcar
    las filas seleccionadas."""
    espacio = pyqtSignal()

    def keyPressEvent(self, evento):
        if evento.key() == Qt.Key.Key_Space and not evento.modifiers():
            self.espacio.emit()
            return
        super().keyPressEvent(evento)


class DialogoPedidoSugerido(QDialog):
    """Qué pedir ahora: una fila por artículo por debajo del mínimo, con la cantidad
    calculada (objetivo − stock − lo ya pedido), el proveedor y el importe estimado.
    Todo es editable; «Crear pedidos» guarda un pedido por proveedor y almacén (o,
    con «Agrupar», uno por proveedor con las líneas de cada almacén).

    [almacenes_visibles]: los almacenes que se pueden elegir (dicts de
    nucleo/almacenes; None = todos). [almacen_inicial]: el que sale elegido (None = todos)."""
    def __init__(self, parent=None, almacenes_visibles=None, almacen_inicial=None):
        super().__init__(parent)
        self.setWindowTitle(tt("cmp_title_sugerido", "Pedido sugerido"))
        self.resize(1080, 560)
        self.pedidos_creados = []
        self.moneda = consumos.moneda()
        self._proveedores = proveedores.listar_proveedores()
        self._almacenes = almacenes_visibles if almacenes_visibles is not None else almacenes.listar()
        self._varios = len(self._almacenes) > 1
        self._nombres_almacen = almacenes.nombres()
        self._lineas = []
        l = QVBoxLayout()
        info = QLabel(tt("cmp_sug_info", "Artículos por debajo del mínimo. La cantidad sale del stock objetivo, lo que hay y lo que ya está pedido y pendiente de llegar."))
        info.setWordWrap(True)
        l.addWidget(info)
        # Almacén: el pedido sugerido se calcula almacén por almacén
        fila_alm = QHBoxLayout()
        fila_alm.addWidget(QLabel(tt("lbl_almacen", "Almacén") + ":"))
        self.combo_almacen = QComboBox()
        if self._varios:
            self.combo_almacen.addItem(tt("cmp_sug_todos_almacenes", "Todos los almacenes"), None)
        for a in self._almacenes:
            self.combo_almacen.addItem(("🌐 " if a["comun"] else "") + a["nombre"], a["id"])
        if almacen_inicial is not None and self.combo_almacen.findData(almacen_inicial) >= 0:
            self.combo_almacen.setCurrentIndex(self.combo_almacen.findData(almacen_inicial))
        self.combo_almacen.currentIndexChanged.connect(lambda _i: self._recargar())
        fila_alm.addWidget(self.combo_almacen)
        fila_alm.addStretch()
        l.addLayout(fila_alm)
        for w in (fila_alm.itemAt(i).widget() for i in range(fila_alm.count())):
            if w is not None:
                w.setVisible(self._varios)
        self.lbl_sin_calculo = QLabel()
        self.lbl_sin_calculo.setWordWrap(True); self.lbl_sin_calculo.setStyleSheet("color:#d98a00;")
        l.addWidget(self.lbl_sin_calculo)
        self._aplicando = False   # evita rebotes al marcar varias casillas a la vez
        barra_marcas = QHBoxLayout()
        for clave, texto, accion in (("cmp_btn_marcar_sel", "☑️ Marcar selección", lambda: self._marcar_seleccion(True)),
                                     ("cmp_btn_desmarcar_sel", "☐ Desmarcar selección", lambda: self._marcar_seleccion(False)),
                                     ("cmp_btn_marcar_todo", "Marcar todo", lambda: self._marcar_todo(True)),
                                     ("cmp_btn_desmarcar_todo", "Desmarcar todo", lambda: self._marcar_todo(False))):
            b = QPushButton(tt(clave, texto)); b.clicked.connect(accion)
            b.setToolTip(tt("cmp_tt_seleccion", "Selecciona varias filas (Ctrl o Mayús) y márcalas o desmárcalas a la vez; también con la barra espaciadora."))
            barra_marcas.addWidget(b)
        barra_marcas.addStretch()
        l.addLayout(barra_marcas)
        self.tabla = _TablaSugerido(0, 10)
        self.tabla.setHorizontalHeaderLabels([
            tt("cmp_sug_hdr_pedir", "PEDIR"), tt("hdr_codigo", "CÓDIGO"), tt("hdr_material", "MATERIAL"), tt("hdr_stock", "STOCK"),
            tt("cmp_sug_hdr_pendiente", "YA PEDIDO"), tt("prov_hdr_cantidad", "CANTIDAD"), tt("prov_lbl_proveedor", "Proveedor").upper(),
            tt("cmp_sug_hdr_precio", "PRECIO EST."), tt("lbl_importe", "Importe").upper(), tt("lbl_almacen", "Almacén").upper()])
        self.tabla.setColumnHidden(9, not self._varios)
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.espacio.connect(self._alternar_seleccion)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self._menu_marcas)
        l.addWidget(self.tabla, 1)
        self.lbl_vacio = QLabel(tt("cmp_sug_vacio", "No hace falta pedir nada ahora."))
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.lbl_vacio)
        self.lbl_total = QLabel(); self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        l.addWidget(self.lbl_total)
        self.chk_agrupar = QCheckBox(tt("cmp_sug_agrupar", "Agrupar los almacenes en un solo pedido por proveedor"))
        self.chk_agrupar.setToolTip(tt("cmp_sug_agrupar_tt", "Un pedido por proveedor con las líneas separadas por almacén; cada una se entrega en la dirección de su almacén. Sin marcar, un pedido por proveedor y almacén."))
        self.chk_agrupar.setVisible(self._varios)
        l.addWidget(self.chk_agrupar)
        self.botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.boton_crear = self.botones.button(QDialogButtonBox.StandardButton.Ok)
        self.boton_crear.setText(tt("cmp_btn_crear", "Crear pedidos"))
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        self.botones.accepted.connect(self.crear); self.botones.rejected.connect(self.reject)
        l.addWidget(self.botones)
        self.setLayout(l)
        self._recargar()

    def _recargar(self):
        """Calcula las líneas del almacén elegido (o de todos los visibles)."""
        elegido = self.combo_almacen.currentData()
        ids = [elegido] if elegido is not None else [a["id"] for a in self._almacenes]
        self._lineas, sin_calculo = compras.lineas_sugeridas(almacen_ids=ids)
        self.lbl_sin_calculo.setText(tt("cmp_sug_sin_calculo", "{n} artículos por debajo del mínimo no se pueden calcular: no tienen stock mínimo ni objetivo.").format(n=sin_calculo))
        self.lbl_sin_calculo.setVisible(bool(sin_calculo))
        self.chk_agrupar.setEnabled(len({ln["almacen_id"] for ln in self._lineas}) > 1)
        self._pintar()

    def _pintar(self):
        self.tabla.setRowCount(len(self._lineas))
        for fila, ln in enumerate(self._lineas):
            casilla = QCheckBox(); casilla.setChecked(True)
            casilla.stateChanged.connect(lambda estado, f=fila: self._casilla_cambiada(f, estado))
            contenedor = QWidget(); hc = QHBoxLayout(contenedor); hc.setContentsMargins(0, 0, 0, 0)
            hc.setAlignment(Qt.AlignmentFlag.AlignCenter); hc.addWidget(casilla)
            self.tabla.setCellWidget(fila, 0, contenedor)
            for col, valor in ((1, ln["codigo"]), (2, ln["nombre"]),
                               (3, f"{ln['stock']:g} {ln['unidad']}".strip()),
                               (4, f"{ln['pendiente']:g}" if ln["pendiente"] else "")):
                item = QTableWidgetItem(valor)
                if col == 3:
                    item.setForeground(QColor("#c0392b"))
                self.tabla.setItem(fila, col, item)
            spin = QDoubleSpinBox(); spin.setRange(0, 999999); spin.setDecimals(2); spin.setValue(ln["cantidad"])
            spin.valueChanged.connect(self._actualizar_total)
            self.tabla.setCellWidget(fila, 5, spin)
            combo = QComboBox()
            combo.addItem(tt("prov_sin_proveedor", "— Sin proveedor —"), None)
            for p in self._proveedores:
                combo.addItem(p["nombre"], p["id"])
            if ln["proveedor_id"] is not None and combo.findData(ln["proveedor_id"]) >= 0:
                combo.setCurrentIndex(combo.findData(ln["proveedor_id"]))
            combo.currentIndexChanged.connect(lambda _i, f=fila: self._cambio_proveedor(f))
            self.tabla.setCellWidget(fila, 6, combo)
            self.tabla.setItem(fila, 7, QTableWidgetItem(""))
            self.tabla.setItem(fila, 8, QTableWidgetItem(""))
            self.tabla.setItem(fila, 9, QTableWidgetItem(self._nombres_almacen.get(ln["almacen_id"], "")))
        self.tabla.setVisible(bool(self._lineas))
        self.lbl_vacio.setVisible(not self._lineas)
        self.boton_crear.setEnabled(bool(self._lineas))
        self._actualizar_total()

    def _cambio_proveedor(self, fila):
        """Al cambiar de proveedor, el precio estimado es el de ese proveedor."""
        ln = self._lineas[fila]
        prov = self.tabla.cellWidget(fila, 6).currentData()
        material = almacen.obtener_material(ln["material_id"])
        ln["precio"], ln["referencia"] = compras._ultimo_precio_y_referencia(material, prov)
        self._actualizar_total()

    def _fila_marcada(self, fila):
        return self.tabla.cellWidget(fila, 0).findChild(QCheckBox).isChecked()

    def _filas_seleccionadas(self):
        return sorted({i.row() for i in self.tabla.selectionModel().selectedRows()})

    def _poner_marcas(self, filas, marcado):
        """Marca o desmarca varias filas de una vez (y recalcula el total una sola vez)."""
        self._aplicando = True
        try:
            for f in filas:
                self.tabla.cellWidget(f, 0).findChild(QCheckBox).setChecked(marcado)
        finally:
            self._aplicando = False
        self._actualizar_total()

    def _casilla_cambiada(self, fila, estado):
        """Si se toca la casilla de una fila que forma parte de una selección de varias,
        el cambio se aplica a todas las seleccionadas."""
        if self._aplicando:
            return
        seleccion = self._filas_seleccionadas()
        if len(seleccion) > 1 and fila in seleccion:
            self._poner_marcas(seleccion, bool(estado))
        else:
            self._actualizar_total()

    def _marcar_seleccion(self, marcado):
        self._poner_marcas(self._filas_seleccionadas(), marcado)

    def _marcar_todo(self, marcado):
        self._poner_marcas(range(len(self._lineas)), marcado)

    def _alternar_seleccion(self):
        """Barra espaciadora: si todas las filas seleccionadas están marcadas, las desmarca;
        si no, las marca."""
        filas = self._filas_seleccionadas()
        if filas:
            self._poner_marcas(filas, not all(self._fila_marcada(f) for f in filas))

    def _menu_marcas(self, pos):
        menu = QMenu(self)
        a1 = menu.addAction(tt("cmp_btn_marcar_sel", "☑️ Marcar selección"))
        a2 = menu.addAction(tt("cmp_btn_desmarcar_sel", "☐ Desmarcar selección"))
        menu.addSeparator()
        a3 = menu.addAction(tt("cmp_btn_marcar_todo", "Marcar todo"))
        a4 = menu.addAction(tt("cmp_btn_desmarcar_todo", "Desmarcar todo"))
        hay = bool(self._filas_seleccionadas())
        a1.setEnabled(hay); a2.setEnabled(hay)
        elegida = menu.exec(self.tabla.viewport().mapToGlobal(pos))
        if elegida == a1: self._marcar_seleccion(True)
        elif elegida == a2: self._marcar_seleccion(False)
        elif elegida == a3: self._marcar_todo(True)
        elif elegida == a4: self._marcar_todo(False)

    def _actualizar_total(self, *_):
        total, sin_precio = 0.0, False
        for fila, ln in enumerate(self._lineas):
            cantidad = self.tabla.cellWidget(fila, 5).value()
            precio = ln["precio"]
            self.tabla.item(fila, 7).setText(consumos.formato_importe(precio, self.moneda) if precio is not None else "—")
            importe = cantidad * precio if precio is not None else None
            self.tabla.item(fila, 8).setText(consumos.formato_importe(importe, self.moneda) if importe is not None else "—")
            if self._fila_marcada(fila):
                if importe is None:
                    sin_precio = True
                else:
                    total += importe
        texto = tt("cmp_sug_total", "Total estimado: {importe}").format(importe=consumos.formato_importe(total, self.moneda))
        if sin_precio:
            texto += " " + tt("lbl_sin_precio_algunos", "(hay artículos sin precio)")
        self.lbl_total.setText("<b>" + texto + "</b>" if self._lineas else "")

    def crear(self):
        elegidas = []
        for fila, ln in enumerate(self._lineas):
            if not self._fila_marcada(fila):
                continue
            cantidad = self.tabla.cellWidget(fila, 5).value()
            if cantidad <= 0:
                continue
            elegidas.append({"material_id": ln["material_id"], "cantidad": cantidad, "proveedor_id": self.tabla.cellWidget(fila, 6).currentData(),
                             "precio": ln["precio"], "referencia": ln["referencia"]})
        if not elegidas:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("cmp_msg_nada_marcado", "No hay ninguna línea marcada para pedir."))
            return
        if any(e["proveedor_id"] is None for e in elegidas):
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("cmp_msg_sin_proveedor", "Hay artículos marcados sin proveedor: elige uno para cada uno o desmárcalos."))
            return
        ids, errores = compras.crear_pedidos(elegidas, usuarios.nombre_actual(),
                                             agrupar=not self.chk_agrupar.isHidden() and self.chk_agrupar.isEnabled()
                                             and self.chk_agrupar.isChecked())
        self.pedidos_creados = ids
        if errores and not ids:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("cmp_msg_no_creado", "No se ha podido crear el pedido."))
            return
        self.accept()


class DialogoTelefonoPedido(QDialog):
    """Para pedir por teléfono: enseña el teléfono y el contacto del proveedor y el
    pedido en texto, listo para leerlo o copiarlo."""
    def __init__(self, parent, pedido, texto, proveedor):
        super().__init__(parent)
        self.setWindowTitle(tt("cmp_title_telefono", "Pedir por teléfono"))
        self.resize(460, 420)
        l = QVBoxLayout()
        nombre = pedido["proveedor_nombre"]
        telefono = (proveedor or {}).get("telefono") or tt("cmp_sin_telefono", "(sin teléfono)")
        contacto = (proveedor or {}).get("contacto")
        cab = f"<b>{nombre}</b><br>📞 {telefono}" + (f"<br>👤 {contacto}" if contacto else "")
        etiqueta = QLabel(cab); etiqueta.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        l.addWidget(etiqueta)
        self.caja = QTextEdit(texto); self.caja.setReadOnly(True)
        l.addWidget(self.caja, 1)
        h = QHBoxLayout()
        b_copiar = QPushButton(tt("cmp_btn_copiar", "📋 Copiar texto")); b_copiar.clicked.connect(
            lambda: QApplication.clipboard().setText(self.caja.toPlainText()))
        h.addWidget(b_copiar); h.addStretch()
        l.addLayout(h)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(tt("cmp_btn_ya_pedido", "Ya lo he pedido"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cerrar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b)
        self.setLayout(l)


class DialogoPedidos(QDialog):
    """Pedidos guardados: pendientes de llegar o todos, con sus líneas y las acciones
    de enviar, marcar como recibido, cancelar y borrar. [almacenes_visibles]: solo los
    pedidos que entregan en esos almacenes (dicts de nucleo/almacenes; None = todos)."""
    def __init__(self, parent=None, seleccionar_id=None, almacenes_visibles=None, almacen_inicial=None):
        super().__init__(parent)
        self._almacenes = almacenes_visibles
        self._almacen_inicial = almacen_inicial
        self._varios = almacenes.hay_varios()
        self.setWindowTitle(tt("cmp_title_pedidos", "Pedidos de material"))
        self.resize(900, 600)
        self.moneda = consumos.moneda()
        self.abrir_url = _abrir_url
        self.abrir_fichero = _abrir_fichero
        self._pedidos = []
        l = QVBoxLayout()
        h = QHBoxLayout()
        h.addWidget(QLabel(tt("cmp_lbl_mostrar", "Mostrar") + ":"))
        self.combo_filtro = QComboBox()
        self.combo_filtro.addItem(tt("cmp_filtro_abiertos", "Pendientes de llegar"), True)
        self.combo_filtro.addItem(tt("cmp_filtro_todos", "Todos"), False)
        self.combo_filtro.currentIndexChanged.connect(lambda _i: self.refrescar())
        h.addWidget(self.combo_filtro)
        h.addStretch()
        b_sugerido = QPushButton(tt("cmp_btn_sugerido", "🛒 Pedido sugerido…")); b_sugerido.clicked.connect(self.pedido_sugerido)
        h.addWidget(b_sugerido)
        l.addLayout(h)

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels([
            tt("cmp_hdr_n", "N.º"), tt("prov_hdr_fecha", "FECHA"), tt("prov_hdr_nombre", "PROVEEDOR"), tt("cmp_hdr_lineas", "LÍNEAS"),
            tt("cmp_hdr_estado", "ESTADO"), tt("cmp_hdr_enviado", "ENVIADO"), tt("cmp_hdr_importe", "IMPORTE EST."),
            tt("lbl_almacen", "Almacén").upper()])
        self.tabla.setColumnHidden(7, not self._varios)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemSelectionChanged.connect(self._pintar_lineas)
        l.addWidget(self.tabla, 3)
        self.lbl_vacio = QLabel(tt("cmp_msg_sin_pedidos", "No hay pedidos."))
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.lbl_vacio)

        l.addWidget(QLabel("<b>" + tt("cmp_lbl_lineas", "Líneas del pedido") + "</b>"))
        self.tabla_lineas = QTableWidget(0, 8)
        self.tabla_lineas.setHorizontalHeaderLabels([tt("hdr_codigo", "CÓDIGO"), tt("cmp_hdr_articulo", "ARTÍCULO"),
                                                     tt("prov_hdr_cantidad", "CANTIDAD"), tt("cmp_hdr_recibido", "RECIBIDO"),
                                                     tt("cmp_hdr_ref", "REF."), tt("cmp_hdr_precio_est", "PRECIO EST."),
                                                     tt("cmp_hdr_precio_real", "PRECIO REAL"), tt("lbl_almacen", "Almacén").upper()])
        self.tabla_lineas.setColumnHidden(7, not self._varios)
        self.tabla_lineas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_lineas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_lineas.setAlternatingRowColors(True)
        l.addWidget(self.tabla_lineas, 2)
        self.lbl_precio_real = QLabel()
        self.lbl_precio_real.setWordWrap(True)
        l.addWidget(self.lbl_precio_real)

        h2 = QHBoxLayout()
        for texto, clave, accion in (("✉️ Correo", "cmp_btn_correo", self.enviar_correo), ("💬 WhatsApp", "cmp_btn_whatsapp", self.enviar_whatsapp),
                                     ("📞 Teléfono", "cmp_btn_telefono", self.enviar_telefono), ("🖨️ Imprimir / PDF", "cmp_btn_imprimir", self.imprimir)):
            b = QPushButton(tt(clave, texto)); b.clicked.connect(accion); h2.addWidget(b)
        l.addLayout(h2)
        h3 = QHBoxLayout()
        for texto, clave, accion in (("✅ Marcar recibido", "cmp_btn_recibido", self.marcar_recibido), ("🚫 Cancelar pedido", "cmp_btn_cancelar", self.cancelar),
                                     ("🗑️ Borrar", "prov_btn_borrar", self.borrar)):
            b = QPushButton(tt(clave, texto)); b.clicked.connect(accion); h3.addWidget(b)
        h3.addStretch()
        bc = QPushButton(t("btn_cerrar")); bc.clicked.connect(self.accept)
        h3.addWidget(bc)
        l.addLayout(h3)
        self.setLayout(l)
        self.refrescar(seleccionar_id)

    # ------------------------------------------------------------------ tabla
    def refrescar(self, seleccionar_id=None):
        previo = seleccionar_id if seleccionar_id is not None else self._pedido_id()
        ids = [a["id"] for a in self._almacenes] if self._almacenes is not None else None
        self._pedidos = compras.listar_pedidos(solo_abiertos=bool(self.combo_filtro.currentData()), almacen_ids=ids)
        estados, canales = nombres_estado(), nombres_canal()
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(self._pedidos))
        for fila, p in enumerate(self._pedidos):
            if p["canal"]:
                enviado = canales.get(p["canal"], p["canal"]) + " · " + formato_fecha_localizada(p["enviado"][:10])
            else:
                enviado = tt("cmp_sin_enviar", "Sin enviar")
            if p.get("dias_retraso"):
                enviado += " · " + (tt("cmp_retraso_un_dia", "1 día de retraso") if p["dias_retraso"] == 1 else
                                    tt("cmp_retraso_dias", "{n} días de retraso").format(n=p["dias_retraso"]))
            importe = consumos.formato_importe(p["importe_estimado"], self.moneda) + (" *" if p["sin_precio"] else "")
            for col, valor in enumerate((str(p["id"]), formato_fecha_localizada(p["fecha"]), p["proveedor_nombre"], str(len(p["lineas"])),
                                         estados.get(p["estado"], p["estado"]), enviado, importe,
                                         p["almacen_nombre"])):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, p["id"])
                if col == 5 and not p["canal"] and p["estado"] in compras.ESTADOS_ABIERTOS:
                    item.setForeground(QColor("#d98a00"))
                if col == 5 and p.get("dias_retraso"):
                    item.setForeground(QColor("#c0392b"))
                if col == 4 and p["estado"] == compras.ESTADO_RECIBIDO:
                    item.setForeground(QColor("#2e8b57"))
                if col == 4 and p["estado"] == compras.ESTADO_CANCELADO:
                    item.setForeground(QColor("#888888"))
                self.tabla.setItem(fila, col, item)
            if p["id"] == previo:
                self.tabla.selectRow(fila)
        self.tabla.blockSignals(False)
        self.tabla.setVisible(bool(self._pedidos))
        self.lbl_vacio.setVisible(not self._pedidos)
        self._pintar_lineas()

    def _pedido_id(self):
        fila = self.tabla.currentRow()
        item = self.tabla.item(fila, 0) if fila >= 0 else None
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _pedido(self):
        pid = self._pedido_id()
        if pid is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("cmp_msg_sin_pedido_sel", "Selecciona un pedido de la lista."))
            return None
        return compras.obtener_pedido(pid)

    def _pintar_lineas(self):
        pid = self._pedido_id()
        p = compras.obtener_pedido(pid) if pid is not None else None
        lineas = p["lineas"] if p else []
        self.tabla_lineas.setRowCount(len(lineas))
        importe = lambda v: consumos.formato_importe(v, self.moneda) if v is not None else ""
        for fila, ln in enumerate(lineas):
            unidad = f" {ln['unidad']}" if ln["unidad"] else ""
            real = ln.get("precio_real")
            for col, valor in enumerate((ln["codigo"], ln["nombre"], f"{ln['cantidad']:g}{unidad}", f"{ln['recibido']:g}{unidad}",
                                         ln["referencia"], importe(ln["precio"]), importe(real), ln["almacen_nombre"])):
                item = QTableWidgetItem(valor)
                if col == 3 and ln["recibido"] >= ln["cantidad"] - 1e-9:
                    item.setForeground(QColor("#2e8b57"))
                if col == 6 and real is not None and ln["precio"] is not None \
                        and abs(real - ln["precio"]) >= compras.TOLERANCIA_PRECIO:
                    item.setForeground(QColor("#c0392b" if real > ln["precio"] else "#2e8b57"))
                self.tabla_lineas.setItem(fila, col, item)
        texto = ""
        if p and p.get("con_precio_real"):
            texto = tt("cmp_lbl_importe_real", "Recibido a precio real: {real}").format(real=importe(p["importe_real"]))
            if abs(p["diferencia_precio"]) >= compras.TOLERANCIA_PRECIO:
                signo = "+" if p["diferencia_precio"] > 0 else "−"
                texto += " · " + tt("cmp_lbl_diferencia", "diferencia con lo estimado: {dif}").format(
                    dif=signo + importe(abs(p["diferencia_precio"])))
        self.lbl_precio_real.setText(texto)
        self.lbl_precio_real.setVisible(bool(texto))

    # ---------------------------------------------------------------- acciones
    def pedido_sugerido(self):
        dlg = DialogoPedidoSugerido(self, self._almacenes, self._almacen_inicial)
        if dlg.exec() and dlg.pedidos_creados:
            self.combo_filtro.setCurrentIndex(0)
            self.refrescar(dlg.pedidos_creados[0])

    def _firma(self):
        return usuarios.nombre_actual() or ""

    def _ruta_pdf(self, pedido):
        carpeta = os.path.join(DATA_DIR, "pedidos")
        os.makedirs(carpeta, exist_ok=True)
        nombre = re.sub(r"[^A-Za-z0-9_-]+", "_", pedido["proveedor_nombre"]).strip("_") or "proveedor"
        return os.path.join(carpeta, f"pedido_{pedido['id']}_{nombre}.pdf")

    def _marcar(self, pedido, canal):
        compras.marcar_enviado(pedido["id"], canal)
        self.refrescar(pedido["id"])

    def enviar_correo(self):
        p = self._pedido()
        if p is None:
            return
        prov = proveedores.obtener_proveedor(p["proveedor_id"]) if p["proveedor_id"] is not None else None
        if not (prov or {}).get("correo"):
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("cmp_msg_sin_correo", "Este proveedor no tiene correo: se abrirá el correo sin destinatario."))
        ruta = self._ruta_pdf(p)
        ok, _e = compras.generar_pdf(p["id"], ruta, self._firma())
        if ok:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt(
                "cmp_msg_correo_adjunto", "Se ha guardado el PDF del pedido en:\n{ruta}\n\nAdjúntalo al correo que se va a abrir.").format(ruta=ruta))
            self.abrir_fichero(os.path.dirname(ruta))
        self.abrir_url(compras.url_correo(p, self._firma()))
        self._marcar(p, "correo")

    def enviar_whatsapp(self):
        p = self._pedido()
        if p is None:
            return
        url, con_prefijo = compras.url_whatsapp(p, self._firma())
        if not con_prefijo:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt(
                "cmp_msg_prefijo", "El teléfono del proveedor no lleva prefijo internacional (p. ej. +34): WhatsApp puede no reconocerlo. Corrígelo en Proveedores."))
        self.abrir_url(url)
        self._marcar(p, "whatsapp")

    def enviar_telefono(self):
        p = self._pedido()
        if p is None:
            return
        prov = proveedores.obtener_proveedor(p["proveedor_id"]) if p["proveedor_id"] is not None else None
        if DialogoTelefonoPedido(self, p, compras.texto_pedido(p, self._firma()), prov).exec():
            self._marcar(p, "telefono")

    def imprimir(self):
        p = self._pedido()
        if p is None:
            return
        ruta = self._ruta_pdf(p)
        ok, _e = compras.generar_pdf(p["id"], ruta, self._firma())
        if ok:
            self.abrir_fichero(ruta)
            self._marcar(p, "impreso")

    def marcar_recibido(self):
        p = self._pedido()
        if p is None:
            return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "cmp_msg_confirmar_recibido", "¿Marcar todo el pedido como recibido? No cambia el stock: las entradas se registran con «📥 Entrada».")) != QMessageBox.StandardButton.Yes:
            return
        compras.marcar_recibido(p["id"])
        self.refrescar(p["id"])

    def cancelar(self):
        p = self._pedido()
        if p is None:
            return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "cmp_msg_confirmar_cancelar", "¿Cancelar este pedido? Lo que faltaba por llegar dejará de contar como pendiente.")) != QMessageBox.StandardButton.Yes:
            return
        compras.cancelar_pedido(p["id"])
        self.refrescar(p["id"])

    def borrar(self):
        p = self._pedido()
        if p is None:
            return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "cmp_msg_confirmar_borrar", "¿Borrar este pedido? Desaparece de la lista y deja de contar como pendiente.")) != QMessageBox.StandardButton.Yes:
            return
        compras.borrar_pedido(p["id"])
        self.refrescar()
