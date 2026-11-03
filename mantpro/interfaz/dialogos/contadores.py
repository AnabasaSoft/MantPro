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

"""Contadores de las máquinas (horas, ciclos, km): gestión, lecturas y los
campos «por contador» de un preventivo."""

from datetime import datetime

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox,
                             QDialogButtonBox, QComboBox, QGroupBox, QCheckBox, QWidget)
from PyQt6.QtCore import Qt

from ... import idiomas
from ..comun import tt
from ...nucleo import contadores, usuarios


def _fecha_hora(iso):
    """AAAA-MM-DDTHH:MM:SS → fecha corta del idioma + hora."""
    if not iso:
        return ""
    try:
        d = datetime.fromisoformat(iso)
        return d.strftime(idiomas.formato_fecha_corta_py()) + d.strftime(" %H:%M")
    except ValueError:
        return iso


def _fecha(iso):
    if not iso:
        return ""
    try:
        return datetime.strptime(iso[:10], "%Y-%m-%d").strftime(idiomas.formato_fecha_corta_py())
    except ValueError:
        return iso


def _botones(dialogo, ok=True):
    b = QDialogButtonBox((QDialogButtonBox.StandardButton.Ok if ok else QDialogButtonBox.StandardButton.NoButton)
                         | QDialogButtonBox.StandardButton.Cancel)
    if ok:
        b.button(QDialogButtonBox.StandardButton.Ok).setText(tt("btn_aceptar", "Aceptar"))
    b.button(QDialogButtonBox.StandardButton.Cancel).setText(tt("btn_cancelar", "Cancelar"))
    b.accepted.connect(dialogo.accept)
    b.rejected.connect(dialogo.reject)
    return b


# ------------------------------------------------------------------ lectura

class DialogoLectura(QDialog):
    """Pide una lectura de un contador mostrando la última. Si es menor que la
    última, pregunta si el contador se ha cambiado o puesto a cero."""

    def __init__(self, parent, contador, titulo=None, explicacion="", opcional=False):
        super().__init__(parent)
        self.contador = contador
        self.opcional = opcional
        self.valor = None
        self.setWindowTitle(titulo or tt("title_apuntar_lectura", "Apuntar lectura"))
        self.setMinimumWidth(420)
        v = QVBoxLayout(self)
        unidad = contador.get("unidad") or ""
        v.addWidget(QLabel(f"<b>{contador['nombre']}</b> — {contador.get('maquina', '')}"))
        if explicacion:
            lbl = QLabel(explicacion); lbl.setWordWrap(True); v.addWidget(lbl)
        if contador.get("actual") is not None:
            v.addWidget(QLabel(tt("lbl_ultima_lectura", "Última lectura: {valor} ({fecha})").format(
                valor=contadores.con_unidad(contador["actual"], unidad), fecha=_fecha_hora(contador.get("fecha_actual")))))
        fila = QHBoxLayout()
        fila.addWidget(QLabel(tt("lbl_lectura_actual", "Lectura actual:")))
        self.campo = QLineEdit()
        self.campo.setPlaceholderText(tt("ph_lectura", "p. ej. 1530"))
        fila.addWidget(self.campo, 1)
        if unidad:
            fila.addWidget(QLabel(unidad))
        v.addLayout(fila)
        if opcional:
            nota = QLabel(tt("lbl_lectura_opcional", "Déjalo en blanco si no la tienes: el siguiente se contará desde la última lectura que se apunte."))
            nota.setWordWrap(True); nota.setStyleSheet("color: gray; font-size: 11px;")
            v.addWidget(nota)
        v.addWidget(_botones(self))
        self.campo.setFocus()

    def accept(self):
        texto = self.campo.text().strip()
        if not texto and self.opcional:
            self.valor = None
            return super().accept()
        valor = contadores.numero(texto)
        if valor is None or valor < 0:
            QMessageBox.warning(self, self.windowTitle(), tt("msg_lectura_no_valida", "Escribe la lectura como un número (p. ej. 1530 o 1530,5)."))
            return
        actual = self.contador.get("actual")
        if actual is not None and valor < actual:
            r = QMessageBox.question(self, self.windowTitle(), tt(
                "msg_lectura_menor", "La lectura ({nueva}) es menor que la última ({anterior}).\n\n"
                "¿Se ha cambiado el contador o se ha puesto a cero? Si es así, se guarda y se cuenta desde ella; "
                "si no, revisa la cifra.").format(
                    nueva=contadores.con_unidad(valor, self.contador.get("unidad")),
                    anterior=contadores.con_unidad(actual, self.contador.get("unidad"))))
            if r != QMessageBox.StandardButton.Yes:
                return
        self.valor = valor
        super().accept()


def pedir_lectura(parent, contador, titulo=None, explicacion="", opcional=False):
    """(aceptado, valor): valor puede ser None si es opcional y se deja en blanco."""
    dlg = DialogoLectura(parent, contador, titulo, explicacion, opcional)
    ok = dlg.exec() == QDialog.DialogCode.Accepted
    return ok, dlg.valor


# ----------------------------------------------------------- crear / editar

class DialogoEditarContador(QDialog):
    def __init__(self, parent, nombre="", unidad="", nuevo=True):
        super().__init__(parent)
        self.setWindowTitle(tt("title_nuevo_contador", "Nuevo contador") if nuevo else tt("title_editar_contador", "Editar contador"))
        self.setMinimumWidth(400)
        g = QGridLayout(self)
        self.nombre = QLineEdit(nombre); self.nombre.setPlaceholderText(tt("ph_nombre_contador", "p. ej. Horas de motor"))
        self.unidad = QComboBox(); self.unidad.setEditable(True)
        self.unidad.addItems(["h", tt("unidad_ciclos", "ciclos"), "km", tt("unidad_piezas", "piezas"), ""])
        self.unidad.setCurrentText(unidad if not nuevo else "h")
        g.addWidget(QLabel(tt("lbl_nombre_contador", "Contador:")), 0, 0); g.addWidget(self.nombre, 0, 1)
        g.addWidget(QLabel(tt("lbl_unidad", "Unidad:")), 1, 0); g.addWidget(self.unidad, 1, 1)
        self.inicial = None
        if nuevo:
            self.inicial = QLineEdit(); self.inicial.setPlaceholderText(tt("ph_lectura", "p. ej. 1530"))
            g.addWidget(QLabel(tt("lbl_lectura_inicial", "Lectura actual (opcional):")), 2, 0); g.addWidget(self.inicial, 2, 1)
        g.addWidget(_botones(self), 3, 0, 1, 2)

    def accept(self):
        if not self.nombre.text().strip():
            self.nombre.setFocus(); return
        if self.inicial is not None and self.inicial.text().strip() and contadores.numero(self.inicial.text()) is None:
            QMessageBox.warning(self, self.windowTitle(), tt("msg_lectura_no_valida", "Escribe la lectura como un número (p. ej. 1530 o 1530,5)."))
            return
        super().accept()

    def datos(self):
        return (self.nombre.text().strip(), self.unidad.currentText().strip(),
                contadores.numero(self.inicial.text()) if self.inicial is not None else None)


# ----------------------------------------------------------------- lecturas

class DialogoLecturas(QDialog):
    """Historial de lecturas de un contador (el admin puede borrar una mal puesta)."""

    def __init__(self, parent, contador_id):
        super().__init__(parent)
        self.contador_id = contador_id
        c = contadores.obtener_contador(contador_id) or {"nombre": "", "maquina": "", "unidad": ""}
        self.unidad = c["unidad"]
        self.setWindowTitle(tt("title_lecturas", "Lecturas de {contador}").format(contador=c["nombre"]))
        self.resize(720, 460)
        v = QVBoxLayout(self)
        v.addWidget(QLabel(f"<b>{c['nombre']}</b> — {c['maquina']}"))
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels([tt("hdr_fecha", "Fecha"), tt("hdr_lectura", "Lectura"),
                                              tt("hdr_realizado_por", "Realizado por"), tt("hdr_origen", "Origen"),
                                              tt("hdr_preventivo", "Preventivo")])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        v.addWidget(self.tabla)
        fila = QHBoxLayout()
        self.btn_borrar = QPushButton(tt("btn_borrar_lectura", "🗑️ Borrar lectura"))
        self.btn_borrar.clicked.connect(self._borrar)
        self.btn_borrar.setVisible(usuarios.es_admin())
        fila.addWidget(self.btn_borrar); fila.addStretch()
        cerrar = QPushButton(tt("btn_cerrar", "Cerrar")); cerrar.clicked.connect(self.accept); fila.addWidget(cerrar)
        v.addLayout(fila)
        self._cargar()

    def _cargar(self):
        origenes = {"pc": tt("origen_pc", "PC"), "movil": tt("origen_movil", "Móvil")}
        filas = contadores.lecturas(self.contador_id)
        self.tabla.setRowCount(len(filas))
        for r, l in enumerate(filas):
            valores = [_fecha_hora(l["fecha"]), contadores.con_unidad(l["valor"], self.unidad), l["usuario_nombre"] or "",
                       origenes.get(l["origen"], l["origen"] or ""), l["aviso"] or ""]
            for c, val in enumerate(valores):
                it = QTableWidgetItem(val)
                if c == 0: it.setData(Qt.ItemDataRole.UserRole, l["id"])
                if c == 1: it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabla.setItem(r, c, it)

    def _borrar(self):
        fila = self.tabla.currentRow()
        if fila < 0: return
        lectura_id = self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, self.windowTitle(), tt("msg_borrar_lectura", "¿Borrar la lectura {valor} del {fecha}?").format(
                valor=self.tabla.item(fila, 1).text(), fecha=self.tabla.item(fila, 0).text())) != QMessageBox.StandardButton.Yes:
            return
        contadores.borrar_lectura(lectura_id)
        self._cargar()


# --------------------------------------------------------- contadores de una máquina

class DialogoContadores(QDialog):
    """Contadores de una máquina: crear/editar/borrar (admin), apuntar lectura
    y ver el historial de lecturas (quien pueda hacer trabajos)."""

    def __init__(self, parent, maquina_id, nombre_maquina):
        super().__init__(parent)
        self.maquina_id = maquina_id
        self.cambiado = False
        self.setWindowTitle(tt("title_contadores", "📟 Contadores de {maquina}").format(maquina=nombre_maquina))
        self.resize(760, 380)
        v = QVBoxLayout(self)
        ayuda = QLabel(tt("lbl_ayuda_contadores",
            "Horas de uso, ciclos, km… de esta máquina. Sus lecturas se apuntan aquí, en la ficha de la máquina "
            "en el móvil (al escanear su QR) y al completar sus preventivos por contador."))
        ayuda.setWordWrap(True); v.addWidget(ayuda)
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels([tt("hdr_contador", "Contador"), tt("hdr_lectura", "Lectura"),
                                              tt("hdr_ultima_lectura", "Última lectura"), tt("hdr_uso_diario", "Uso medio/día"),
                                              tt("hdr_preventivos", "Preventivos")])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.itemDoubleClicked.connect(lambda *_: self._lectura())
        v.addWidget(self.tabla)
        fila = QHBoxLayout()
        admin = usuarios.es_admin()
        self.btn_lectura = QPushButton(tt("btn_apuntar_lectura", "📟 Apuntar lectura")); self.btn_lectura.clicked.connect(self._lectura)
        self.btn_lectura.setEnabled(usuarios.puede_hacer_trabajos())
        self.btn_historial = QPushButton(tt("btn_ver_lecturas", "📋 Lecturas")); self.btn_historial.clicked.connect(self._historial)
        b_nuevo = QPushButton(tt("btn_nuevo_contador", "➕ Nuevo contador")); b_nuevo.clicked.connect(self._nuevo)
        b_editar = QPushButton(tt("btn_editar_maquina", "✏️ Editar")); b_editar.clicked.connect(self._editar)
        b_borrar = QPushButton(tt("btn_eliminar_maquina", "🗑️ Eliminar")); b_borrar.clicked.connect(self._borrar)
        for b in (b_nuevo, b_editar, b_borrar):
            b.setVisible(admin)
        for b in (self.btn_lectura, self.btn_historial, b_nuevo, b_editar, b_borrar):
            fila.addWidget(b)
        fila.addStretch()
        cerrar = QPushButton(tt("btn_cerrar", "Cerrar")); cerrar.clicked.connect(self.accept); fila.addWidget(cerrar)
        v.addLayout(fila)
        self._cargar()

    def _cargar(self):
        self.lista = contadores.listar_contadores(self.maquina_id)
        self.tabla.setRowCount(len(self.lista))
        for r, c in enumerate(self.lista):
            ritmo = contadores.ritmo_diario(c["id"])
            valores = [c["nombre"], contadores.con_unidad(c["actual"], c["unidad"]) if c["actual"] is not None else "—",
                       _fecha_hora(c["fecha_actual"]),
                       contadores.con_unidad(round(ritmo, 1), c["unidad"]) if ritmo else "—", str(c["n_avisos"])]
            for col, val in enumerate(valores):
                it = QTableWidgetItem(val)
                if col == 0: it.setData(Qt.ItemDataRole.UserRole, c["id"])
                if col in (1, 3, 4): it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabla.setItem(r, col, it)
        if self.lista and self.tabla.currentRow() < 0:
            self.tabla.selectRow(0)

    def _seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self.lista):
            return None
        return self.lista[fila]

    def _nuevo(self):
        dlg = DialogoEditarContador(self)
        if dlg.exec():
            nombre, unidad, inicial = dlg.datos()
            contadores.crear_contador(self.maquina_id, nombre, unidad, inicial)
            self.cambiado = True; self._cargar()

    def _editar(self):
        c = self._seleccionado()
        if not c: return
        dlg = DialogoEditarContador(self, c["nombre"], c["unidad"], nuevo=False)
        if dlg.exec():
            nombre, unidad, _ = dlg.datos()
            contadores.editar_contador(c["id"], nombre, unidad)
            self.cambiado = True; self._cargar()

    def _borrar(self):
        c = self._seleccionado()
        if not c: return
        if c["n_avisos"]:
            QMessageBox.information(self, self.windowTitle(), tt(
                "msg_contador_en_uso", "«{contador}» lo usan {n} preventivos. Cámbialos a otro contador o a solo por fecha "
                "(en Avisos) antes de borrarlo.").format(contador=c["nombre"], n=c["n_avisos"]))
            return
        if QMessageBox.question(self, self.windowTitle(), tt(
                "msg_borrar_contador", "¿Borrar el contador «{contador}» y todas sus lecturas?").format(contador=c["nombre"])) \
                != QMessageBox.StandardButton.Yes:
            return
        contadores.borrar_contador(c["id"])
        self.cambiado = True; self._cargar()

    def _lectura(self):
        c = self._seleccionado()
        if not c or not usuarios.puede_hacer_trabajos(): return
        ok, valor = pedir_lectura(self, c)
        if ok and valor is not None:
            contadores.registrar_lectura(c["id"], valor, origen="pc")
            self.cambiado = True; self._cargar()

    def _historial(self):
        c = self._seleccionado()
        if not c: return
        DialogoLecturas(self, c["id"]).exec()
        self.cambiado = True; self._cargar()


# --------------------------------------------------- campos «por contador» de un aviso

class CamposContadorAviso(QGroupBox):
    """Grupo marcable «📟 Por contador» para el formulario de un preventivo:
    contador (de cualquier máquina), cada cuánto, con cuánta antelación
    avisar, a qué lectura toca la primera vez y si además tiene límite por
    fecha (lo que antes llegue) o va solo por contador."""

    def __init__(self, parent=None, config=None):
        super().__init__(tt("lbl_por_contador", "📟 Por contador (horas de uso, ciclos, km…)"), parent)
        self.setCheckable(True)
        exterior = QVBoxLayout(self); exterior.setContentsMargins(6, 4, 6, 4)
        # Desmarcado se pliega para no quitar sitio a la lista de avisos
        self.cuerpo = QWidget(); exterior.addWidget(self.cuerpo)
        g = QGridLayout(self.cuerpo); g.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.lbl_sin = QLabel(tt("msg_sin_contadores", "Ninguna máquina tiene contadores todavía: créalos en Máquinas → 📟 Contadores."))
        self.lbl_sin.setWordWrap(True)
        self.cada = QLineEdit(); self.cada.setPlaceholderText("500")
        self.antelacion = QLineEdit(); self.antelacion.setPlaceholderText("50")
        self.primera = QLineEdit()
        self.lbl_u1, self.lbl_u2, self.lbl_u3 = QLabel(), QLabel(), QLabel()
        self.con_fecha = QCheckBox(tt("lbl_tambien_por_fecha", "Además, como máximo con la frecuencia por fecha (lo que antes llegue)"))
        self.con_fecha.setToolTip(tt("tt_tambien_por_fecha",
            "Marcado: toca al llegar al contador o al cumplirse la frecuencia por fecha, lo primero que ocurra "
            "(«cada 500 h o cada año»). Sin marcar: solo por contador; no sale en el calendario."))
        for campo in (self.cada, self.antelacion, self.primera):
            campo.setMinimumWidth(90)
        self.primera.setPlaceholderText(tt("ph_primera_auto", "automático"))
        self.primera.setToolTip(tt("tt_primera_vez",
            "Lectura a la que toca la primera vez. Vacío: la lectura actual del contador más «Cada»."))
        g.addWidget(self.lbl_sin, 0, 0, 1, 9)
        g.addWidget(QLabel(tt("lbl_contador", "Contador:")), 1, 0); g.addWidget(self.combo, 1, 1, 1, 8)
        fila = 2
        for col, (etiqueta, campo, unidad) in enumerate((
                (tt("lbl_cada", "Cada:"), self.cada, self.lbl_u1),
                (tt("lbl_avisar_antes", "Avisar antes:"), self.antelacion, self.lbl_u2),
                (tt("lbl_primera_vez_a", "Primera vez a:"), self.primera, self.lbl_u3))):
            g.addWidget(QLabel(etiqueta), fila, col * 3); g.addWidget(campo, fila, col * 3 + 1); g.addWidget(unidad, fila, col * 3 + 2)
        g.addWidget(self.con_fecha, 3, 0, 1, 9)
        for c in (1, 4, 7):
            g.setColumnStretch(c, 1)
        self.combo.currentIndexChanged.connect(self._al_cambiar_contador)
        self._llenar(config)
        self.toggled.connect(self._al_marcar)
        self._al_marcar(self.isChecked())

    def _llenar(self, config):
        self._lista = contadores.listar_contadores()
        self._lista.sort(key=lambda c: (c["maquina"].lower(), c["nombre"].lower()))
        self.combo.blockSignals(True); self.combo.clear()
        for c in self._lista:
            self.combo.addItem(f"{c['maquina']} — {c['nombre']}" + (f" ({c['unidad']})" if c["unidad"] else ""), c["id"])
        self.combo.blockSignals(False)
        self.lbl_sin.setVisible(not self._lista)
        if config:
            i = self.combo.findData(config["contador_id"])
            if i >= 0: self.combo.setCurrentIndex(i)
            self.cada.setText(contadores.cifra(config["cada"]))
            self.antelacion.setText(contadores.cifra(config["antelacion"]))
            self.primera.setText(contadores.cifra(config["primera"]) if config.get("primera") is not None else "")
            self.con_fecha.setChecked(not config["solo_contador"])
            self.setChecked(True)
        else:
            self.con_fecha.setChecked(True)
            self.setChecked(False)
        self._al_cambiar_contador()

    def _contador(self):
        cid = self.combo.currentData()
        return next((c for c in self._lista if c["id"] == cid), None)

    def _al_cambiar_contador(self, *_):
        c = self._contador()
        u = c["unidad"] if c else ""
        for l in (self.lbl_u1, self.lbl_u2, self.lbl_u3):
            l.setText(u)

    def _al_marcar(self, marcado):
        self.cuerpo.setVisible(marcado)
        if marcado and not self._lista:   # no hay nada que elegir
            self.combo.setEnabled(False)

    def solo_contador(self):
        return self.isChecked() and not self.con_fecha.isChecked()

    def validar(self, parent):
        """Mensaje de error, o "" si está bien (o desmarcado)."""
        if not self.isChecked():
            return ""
        if not self._lista or self.combo.currentData() is None:
            return tt("msg_sin_contadores", "Ninguna máquina tiene contadores todavía: créalos en Máquinas → 📟 Contadores.")
        cada = contadores.numero(self.cada.text())
        if cada is None or cada <= 0:
            return tt("msg_cada_no_valido", "Indica cada cuánto toca (un número mayor que cero).")
        for campo in (self.antelacion, self.primera):
            if campo.text().strip() and contadores.numero(campo.text()) is None:
                return tt("msg_lectura_no_valida", "Escribe la lectura como un número (p. ej. 1530 o 1530,5).")
        return ""

    def config(self):
        """dict para contadores.fijar_aviso, o None si no es por contador."""
        if not self.isChecked() or self.combo.currentData() is None:
            return None
        primera = contadores.numero(self.primera.text())
        if primera is None:
            c = self._contador()
            primera = ((c["actual"] or 0) if c else 0) + (contadores.numero(self.cada.text()) or 0)
        return {"contador_id": self.combo.currentData(), "cada": contadores.numero(self.cada.text()),
                "antelacion": contadores.numero(self.antelacion.text()) or 0, "primera": primera,
                "solo_contador": not self.con_fecha.isChecked()}
