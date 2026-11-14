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

"""Almacén → Proveedores: alta, edición y baja de los proveedores del almacén
(nombre, contacto, teléfono, correo y notas). El proveedor habitual de cada
artículo se elige en la ficha del artículo."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QDialogButtonBox, QMessageBox,
                             QTextEdit)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import proveedores


def texto_error(codigo):
    """Mensaje traducido de un código de error del núcleo de proveedores."""
    if codigo == "nombre_obligatorio":
        return tt("prov_msg_nombre_obligatorio", "El nombre del proveedor es obligatorio.")
    if codigo == "repetido":
        return tt("prov_msg_repetido", "Ya existe un proveedor con ese nombre.")
    return tt("prov_msg_no_existe", "El proveedor ya no existe.")


class DialogoEditarProveedor(QDialog):
    """Alta o edición de un proveedor."""
    def __init__(self, parent=None, proveedor=None):
        super().__init__(parent)
        self.setWindowTitle(tt("prov_title_editar", "Editar proveedor") if proveedor
                            else tt("prov_title_nuevo", "Nuevo proveedor"))
        self.resize(420, 420)
        l = QVBoxLayout()
        proveedor = proveedor or {}

        def campo(clave_texto, texto, valor):
            l.addWidget(QLabel(tt(clave_texto, texto)))
            c = QLineEdit(valor or "")
            l.addWidget(c)
            return c

        self.campo_nombre = campo("prov_lbl_nombre", "Nombre del proveedor", proveedor.get("nombre"))
        self.campo_contacto = campo("prov_lbl_contacto", "Persona de contacto", proveedor.get("contacto"))
        self.campo_telefono = campo("prov_lbl_telefono", "Teléfono", proveedor.get("telefono"))
        self.campo_correo = campo("prov_lbl_correo", "Correo electrónico", proveedor.get("correo"))
        l.addWidget(QLabel(tt("prov_lbl_nota", "Notas")))
        self.campo_nota = QTextEdit(proveedor.get("nota") or "")
        self.campo_nota.setAcceptRichText(False)
        l.addWidget(self.campo_nota)

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar); b.rejected.connect(self.reject)
        l.addWidget(b)
        self.setLayout(l)

    def _validar(self):
        if not self.campo_nombre.text().strip():
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error("nombre_obligatorio"))
            return
        self.accept()

    def get_data(self):
        return {"nombre": self.campo_nombre.text().strip(), "contacto": self.campo_contacto.text().strip(),
                "telefono": self.campo_telefono.text().strip(), "correo": self.campo_correo.text().strip(),
                "nota": self.campo_nota.toPlainText().strip()}


class DialogoProveedores(QDialog):
    """Lista de proveedores del almacén con sus botones de alta, edición y baja."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("prov_title", "Proveedores"))
        self.resize(760, 460)
        l = QVBoxLayout()

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels([
            tt("prov_hdr_nombre", "PROVEEDOR"), tt("prov_hdr_contacto", "CONTACTO"),
            tt("prov_hdr_telefono", "TELÉFONO"), tt("prov_hdr_correo", "CORREO"),
            tt("prov_hdr_articulos", "ARTÍCULOS")])
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemDoubleClicked.connect(lambda _: self.editar())
        l.addWidget(self.tabla)

        self.lbl_vacio = QLabel(tt("prov_vacio", "Aún no hay proveedores. Pulsa «Nuevo proveedor» para añadir el primero."))
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vacio.setWordWrap(True)
        l.addWidget(self.lbl_vacio)

        h = QHBoxLayout()
        btn_nuevo = QPushButton(tt("prov_btn_nuevo", "➕ Nuevo proveedor")); btn_nuevo.clicked.connect(self.nuevo)
        btn_editar = QPushButton(tt("prov_btn_editar", "✏️ Editar")); btn_editar.clicked.connect(self.editar)
        btn_borrar = QPushButton(tt("prov_btn_borrar", "🗑️ Borrar")); btn_borrar.clicked.connect(self.borrar)
        for b in (btn_nuevo, btn_editar, btn_borrar):
            h.addWidget(b)
        h.addStretch()
        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept)
        h.addWidget(btn_cerrar)
        l.addLayout(h)
        self.setLayout(l)
        self.refrescar()

    def refrescar(self, seleccionar_id=None):
        lista = proveedores.listar_proveedores()
        self.tabla.setRowCount(len(lista))
        for fila, p in enumerate(lista):
            for col, valor in enumerate((p["nombre"], p["contacto"], p["telefono"], p["correo"], str(p["articulos"]))):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, p["id"])
                if col == 4:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(fila, col, item)
            if p["id"] == seleccionar_id:
                self.tabla.selectRow(fila)
        self.tabla.setVisible(bool(lista))
        self.lbl_vacio.setVisible(not lista)

    def _seleccionado(self):
        fila = self.tabla.currentRow()
        item = self.tabla.item(fila, 0) if fila >= 0 else None
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _avisar_seleccion(self):
        QMessageBox.information(self, tt("aviso", "Aviso"),
                                tt("prov_msg_sin_seleccion", "Selecciona un proveedor de la lista."))

    def nuevo(self):
        dlg = DialogoEditarProveedor(self)
        if not dlg.exec():
            return
        proveedor_id, error = proveedores.crear_proveedor(**dlg.get_data())
        if error:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(error))
            return
        self.refrescar(proveedor_id)

    def editar(self):
        proveedor_id = self._seleccionado()
        if proveedor_id is None:
            self._avisar_seleccion(); return
        dlg = DialogoEditarProveedor(self, proveedores.obtener_proveedor(proveedor_id))
        if not dlg.exec():
            return
        ok, error = proveedores.editar_proveedor(proveedor_id, **dlg.get_data())
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(error))
        self.refrescar(proveedor_id)

    def borrar(self):
        proveedor_id = self._seleccionado()
        if proveedor_id is None:
            self._avisar_seleccion(); return
        p = proveedores.obtener_proveedor(proveedor_id)
        if p is None:
            self.refrescar(); return
        if p["articulos"]:
            texto = tt("prov_msg_confirmar_borrar_con_articulos",
                       "¿Borrar al proveedor «{nombre}»? Es el proveedor habitual de {n} artículos, que se quedarán sin proveedor habitual.").format(
                nombre=p["nombre"], n=p["articulos"])
        else:
            texto = tt("prov_msg_confirmar_borrar", "¿Borrar al proveedor «{nombre}»?").format(nombre=p["nombre"])
        if QMessageBox.question(self, tt("aviso", "Aviso"), texto) != QMessageBox.StandardButton.Yes:
            return
        ok, error = proveedores.borrar_proveedor(proveedor_id)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(error))
        self.refrescar()


# ------------------------------------------------- precios por proveedor

def _qdate_formato():
    from ... import idiomas
    return {"eu": "yyyy/MM/dd", "de": "dd.MM.yyyy"}.get(idiomas.get_idioma(), "dd/MM/yyyy")


class DialogoApuntarPrecio(QDialog):
    """Apunta a mano un precio (una oferta o una compra) de un artículo a un proveedor."""
    def __init__(self, parent=None, proveedor_id=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QComboBox, QDateEdit
        from PyQt6.QtCore import QDate
        self.setWindowTitle(tt("prov_precio_title_nuevo", "Apuntar precio"))
        self.resize(380, 300)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("prov_lbl_proveedor", "Proveedor")))
        self.combo = QComboBox()
        for p in proveedores.listar_proveedores():
            self.combo.addItem(p["nombre"], p["id"])
        if proveedor_id is not None and self.combo.findData(proveedor_id) >= 0:
            self.combo.setCurrentIndex(self.combo.findData(proveedor_id))
        l.addWidget(self.combo)
        l.addWidget(QLabel(tt("prov_lbl_precio", "Precio unitario")))
        self.campo_precio = QLineEdit()
        l.addWidget(self.campo_precio)
        l.addWidget(QLabel(tt("prov_lbl_fecha", "Fecha")))
        self.campo_fecha = QDateEdit(QDate.currentDate())
        self.campo_fecha.setCalendarPopup(True)
        self.campo_fecha.setDisplayFormat(_qdate_formato())
        l.addWidget(self.campo_fecha)
        l.addWidget(QLabel(tt("prov_lbl_referencia", "Referencia del proveedor (opcional)")))
        self.campo_ref = QLineEdit()
        l.addWidget(self.campo_ref)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar); b.rejected.connect(self.reject)
        l.addWidget(b)
        self.setLayout(l)

    def _validar(self):
        from ...nucleo import consumos
        if consumos.numero(self.campo_precio.text()) is None:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("prov_msg_precio_obligatorio", "Escribe el precio."))
            return
        self.accept()

    def get_data(self):
        from ...nucleo import consumos
        return {"proveedor_id": self.combo.currentData(), "precio": consumos.numero(self.campo_precio.text()),
                "fecha": self.campo_fecha.date().toString("yyyy-MM-dd"), "referencia": self.campo_ref.text().strip()}


class DialogoPreciosProveedor(QDialog):
    """Precios de un artículo por proveedor: el último de cada uno (con el más
    barato resaltado y cómo ha variado) y todo el historial. Solo administradores."""
    def __init__(self, parent=None, material=None):
        super().__init__(parent)
        from ...nucleo import consumos
        self.material = material
        self.moneda = consumos.moneda()
        self.setWindowTitle(tt("prov_precios_title", "Precios por proveedor") + f" — {material['nombre']}")
        self.resize(820, 560)
        l = QVBoxLayout()

        l.addWidget(QLabel("<b>" + tt("prov_precios_resumen", "Último precio de cada proveedor") + "</b>"))
        self.tabla_resumen = self._tabla([tt("prov_hdr_nombre", "PROVEEDOR"), tt("prov_hdr_precio", "PRECIO"),
                                          tt("prov_hdr_fecha", "FECHA"), tt("prov_hdr_referencia", "REFERENCIA"),
                                          tt("prov_hdr_variacion", "VARIACIÓN")])
        self.tabla_resumen.setMaximumHeight(160)
        l.addWidget(self.tabla_resumen)
        self.lbl_leyenda = QLabel(tt("prov_precios_leyenda", "En verde, el proveedor más barato."))
        l.addWidget(self.lbl_leyenda)

        l.addWidget(QLabel("<b>" + tt("prov_precios_historial", "Historial de precios") + "</b>"))
        self.tabla = self._tabla([tt("prov_hdr_fecha", "FECHA"), tt("prov_hdr_nombre", "PROVEEDOR"),
                                  tt("prov_hdr_precio", "PRECIO"), tt("prov_hdr_cantidad", "CANTIDAD"),
                                  tt("prov_hdr_referencia", "REFERENCIA"), tt("prov_hdr_nota", "NOTA")])
        l.addWidget(self.tabla, 1)
        self.lbl_vacio = QLabel(tt("prov_msg_sin_precios", "Aún no hay precios apuntados para este artículo."))
        self.lbl_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.lbl_vacio)

        h = QHBoxLayout()
        b1 = QPushButton(tt("prov_btn_apuntar_precio", "➕ Apuntar precio")); b1.clicked.connect(self.apuntar)
        b2 = QPushButton(tt("prov_btn_usar_precio", "💲 Usar como precio del artículo")); b2.clicked.connect(self.usar_precio)
        b3 = QPushButton(tt("prov_btn_borrar_apunte", "🗑️ Borrar apunte")); b3.clicked.connect(self.borrar_apunte)
        for b in (b1, b2, b3):
            h.addWidget(b)
        h.addStretch()
        bc = QPushButton(t("btn_cerrar")); bc.clicked.connect(self.accept)
        h.addWidget(bc)
        l.addLayout(h)
        self.setLayout(l)
        self.refrescar()

    def _tabla(self, cabeceras):
        tb = QTableWidget(0, len(cabeceras))
        tb.setHorizontalHeaderLabels(cabeceras)
        tb.horizontalHeader().setStretchLastSection(True)
        tb.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tb.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tb.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tb.setAlternatingRowColors(True)
        return tb

    def _importe(self, valor):
        from ...nucleo import consumos
        return consumos.formato_importe(valor, self.moneda) if valor is not None else "—"

    @staticmethod
    def _variacion(precio, anterior):
        if anterior is None or anterior == 0:
            return "", None
        pct = (precio - anterior) / anterior * 100
        if abs(pct) < 0.05:
            return "=", None
        from ... import idiomas
        texto = f"{abs(pct):.1f}"
        if idiomas.get_idioma() != "en":
            texto = texto.replace(".", ",")
        return (f"▲ {texto} %", "#c0392b") if pct > 0 else (f"▼ {texto} %", "#2e8b57")

    def refrescar(self):
        from PyQt6.QtGui import QColor, QFont
        from ...idiomas import formato_fecha_localizada
        resumen = proveedores.resumen_precios(self.material["id"])
        self.tabla_resumen.setRowCount(len(resumen))
        for fila, r in enumerate(resumen):
            texto_var, color_var = self._variacion(r["precio"], r["anterior"])
            for col, valor in enumerate((r["proveedor"], self._importe(r["precio"]), formato_fecha_localizada(r["fecha"]),
                                         r["referencia"], texto_var)):
                item = QTableWidgetItem(valor)
                if r["mas_barato"]:
                    item.setForeground(QColor("#2e8b57")); f = QFont(item.font()); f.setBold(True); item.setFont(f)
                elif col == 4 and color_var:
                    item.setForeground(QColor(color_var))
                self.tabla_resumen.setItem(fila, col, item)
        self.tabla_resumen.setVisible(bool(resumen))
        self.lbl_leyenda.setVisible(any(r["mas_barato"] for r in resumen))

        hist = proveedores.historial_precios(self.material["id"])
        self.tabla.setRowCount(len(hist))
        for fila, h in enumerate(hist):
            cantidad = "" if h["cantidad"] is None else f"{h['cantidad']:g}"
            for col, valor in enumerate((formato_fecha_localizada(h["fecha"]), h["proveedor"], self._importe(h["precio"]),
                                         cantidad, h["referencia"], h["nota"])):
                item = QTableWidgetItem(valor)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, h["id"])
                    item.setData(Qt.ItemDataRole.UserRole + 1, h["precio"])
                self.tabla.setItem(fila, col, item)
        self.tabla.setVisible(bool(hist))
        self.lbl_vacio.setVisible(not hist)

    def _apunte_seleccionado(self):
        fila = self.tabla.currentRow()
        item = self.tabla.item(fila, 0) if fila >= 0 else None
        if item is None:
            QMessageBox.information(self, tt("aviso", "Aviso"),
                                    tt("prov_msg_sin_apunte", "Selecciona un apunte del historial."))
            return None
        return item

    def apuntar(self):
        if not proveedores.listar_proveedores():
            QMessageBox.information(self, tt("aviso", "Aviso"), tt(
                "prov_msg_sin_proveedores", "Primero da de alta algún proveedor (botón «🏭 Proveedores» de la pestaña de stock)."))
            return
        dlg = DialogoApuntarPrecio(self, self.material.get("proveedor_id"))
        if not dlg.exec():
            return
        from ...nucleo import usuarios
        d = dlg.get_data()
        _id, error = proveedores.registrar_precio(self.material["id"], d["proveedor_id"], d["precio"], None, d["fecha"],
                                                  d["referencia"], "", usuarios.nombre_actual())
        if error:
            QMessageBox.warning(self, tt("aviso", "Aviso"), texto_error(error))
        self.refrescar()

    def borrar_apunte(self):
        item = self._apunte_seleccionado()
        if item is None:
            return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "prov_msg_confirmar_borrar_apunte", "¿Borrar este apunte del historial de precios?")) != QMessageBox.StandardButton.Yes:
            return
        proveedores.borrar_precio(item.data(Qt.ItemDataRole.UserRole))
        self.refrescar()

    def usar_precio(self):
        """Pone el precio del apunte seleccionado como precio del artículo (con confirmación)."""
        item = self._apunte_seleccionado()
        if item is None:
            return
        precio = item.data(Qt.ItemDataRole.UserRole + 1)
        if precio is None:
            QMessageBox.information(self, tt("aviso", "Aviso"),
                                    tt("prov_msg_sin_precio_sel", "El apunte seleccionado no tiene precio."))
            return
        if QMessageBox.question(self, tt("prov_title_actualizar_precio", "Actualizar precio"), tt(
                "prov_msg_confirmar_usar_precio",
                "¿Poner {precio} como precio del artículo? Cambiará el coste de los trabajos a partir de ahora.").format(
                precio=self._importe(precio))) != QMessageBox.StandardButton.Yes:
            return
        from ...nucleo import usuarios
        proveedores.fijar_precio_articulo(self.material["id"], precio, usuarios.id_actual(), usuarios.nombre_actual())
        self.precio_cambiado = True
