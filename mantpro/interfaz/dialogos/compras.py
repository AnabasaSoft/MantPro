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
from ...nucleo import almacen, compras, consumos, proveedores, usuarios
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
    Todo es editable; «Crear pedidos» guarda un pedido por proveedor."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("cmp_title_sugerido", "Pedido sugerido"))
        self.resize(980, 540)
        self.pedidos_creados = []
        self.moneda = consumos.moneda()
        self._proveedores = proveedores.listar_proveedores()
        self._lineas, sin_calculo = compras.lineas_sugeridas()
        l = QVBoxLayout()
        info = QLabel(tt("cmp_sug_info", "Artículos por debajo del mínimo. La cantidad sale del stock objetivo, lo que hay y lo que ya está pedido y pendiente de llegar."))
        info.setWordWrap(True)
        l.addWidget(info)
        if sin_calculo:
            aviso = QLabel(tt("cmp_sug_sin_calculo", "{n} artículos por debajo del mínimo no se pueden calcular: no tienen stock mínimo ni objetivo.").format(n=sin_calculo))
            aviso.setWordWrap(True); aviso.setStyleSheet("color:#d98a00;")
            l.addWidget(aviso)
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
        self.tabla = _TablaSugerido(0, 9)
        self.tabla.setHorizontalHeaderLabels([
            tt("cmp_sug_hdr_pedir", "PEDIR"), tt("hdr_codigo", "CÓDIGO"), tt("hdr_material", "MATERIAL"), tt("hdr_stock", "STOCK"),
            tt("cmp_sug_hdr_pendiente", "YA PEDIDO"), tt("prov_hdr_cantidad", "CANTIDAD"), tt("prov_lbl_proveedor", "Proveedor").upper(),
            tt("cmp_sug_hdr_precio", "PRECIO EST."), tt("lbl_importe", "Importe").upper()])
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
        self.botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.boton_crear = self.botones.button(QDialogButtonBox.StandardButton.Ok)
        self.boton_crear.setText(tt("cmp_btn_crear", "Crear pedidos"))
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        self.botones.accepted.connect(self.crear); self.botones.rejected.connect(self.reject)
        l.addWidget(self.botones)
        self.setLayout(l)
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
        ids, errores = compras.crear_pedidos(elegidas, usuarios.nombre_actual())
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
    de enviar, marcar como recibido, cancelar y borrar."""
    def __init__(self, parent=None, seleccionar_id=None):
        super().__init__(parent)
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

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels([
            tt("cmp_hdr_n", "N.º"), tt("prov_hdr_fecha", "FECHA"), tt("prov_hdr_nombre", "PROVEEDOR"), tt("cmp_hdr_lineas", "LÍNEAS"),
            tt("cmp_hdr_estado", "ESTADO"), tt("cmp_hdr_enviado", "ENVIADO"), tt("cmp_hdr_importe", "IMPORTE EST.")])
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
        self.tabla_lineas = QTableWidget(0, 5)
        self.tabla_lineas.setHorizontalHeaderLabels([tt("hdr_codigo", "CÓDIGO"), tt("cmp_hdr_articulo", "ARTÍCULO"),
                                                     tt("prov_hdr_cantidad", "CANTIDAD"), tt("cmp_hdr_recibido", "RECIBIDO"),
                                                     tt("cmp_hdr_ref", "REF.")])
        self.tabla_lineas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_lineas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_lineas.setAlternatingRowColors(True)
        l.addWidget(self.tabla_lineas, 2)

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
        self._pedidos = compras.listar_pedidos(solo_abiertos=bool(self.combo_filtro.currentData()))
        estados, canales = nombres_estado(), nombres_canal()
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(len(self._pedidos))
        for fila, p in enumerate(self._pedidos):
            if p["canal"]:
                enviado = canales.get(p["canal"], p["canal"]) + " · " + formato_fecha_localizada(p["enviado"][:10])
            else:
                enviado = tt("cmp_sin_enviar", "Sin enviar")
            importe = consumos.formato_importe(p["importe_estimado"], self.moneda) + (" *" if p["sin_precio"] else "")
            for col, valor in enumerate((str(p["id"]), formato_fecha_localizada(p["fecha"]), p["proveedor_nombre"], str(len(p["lineas"])),
                                         estados.get(p["estado"], p["estado"]), enviado, importe)):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, p["id"])
                if col == 5 and not p["canal"] and p["estado"] in compras.ESTADOS_ABIERTOS:
                    item.setForeground(QColor("#d98a00"))
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
        for fila, ln in enumerate(lineas):
            unidad = f" {ln['unidad']}" if ln["unidad"] else ""
            for col, valor in enumerate((ln["codigo"], ln["nombre"], f"{ln['cantidad']:g}{unidad}", f"{ln['recibido']:g}{unidad}", ln["referencia"])):
                item = QTableWidgetItem(valor)
                if col == 3 and ln["recibido"] >= ln["cantidad"] - 1e-9:
                    item.setForeground(QColor("#2e8b57"))
                self.tabla_lineas.setItem(fila, col, item)

    # ---------------------------------------------------------------- acciones
    def pedido_sugerido(self):
        dlg = DialogoPedidoSugerido(self)
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
