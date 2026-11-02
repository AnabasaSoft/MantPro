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

"""Listas de comprobación: gestión de plantillas (Herramientas), rellenar
una lista al completar un preventivo o un trabajo, y verla o corregirla desde
el historial."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
                             QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
                             QHeaderView, QMessageBox, QAbstractItemView, QWidget, QButtonGroup,
                             QRadioButton, QSplitter, QDialogButtonBox)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..comun import tt
from ...nucleo import checklists


def texto_estado(estado):
    return {"ok": tt("chk_estado_ok", "✅ Bien"), "mal": tt("chk_estado_mal", "❌ Mal"),
            "na": tt("chk_estado_na", "➖ No aplica")}.get(estado, tt("chk_estado_sin", "Sin revisar"))


def texto_rango(punto):
    minimo, maximo, unidad = punto.get("minimo"), punto.get("maximo"), punto.get("unidad") or ""
    fmt = lambda n: f"{n:g}"
    if minimo is not None and maximo is not None:
        return f"{fmt(minimo)}–{fmt(maximo)} {unidad}".strip()
    if minimo is not None:
        return f"≥ {fmt(minimo)} {unidad}".strip()
    if maximo is not None:
        return f"≤ {fmt(maximo)} {unidad}".strip()
    return ""


def resumen_texto(items):
    """«8 bien · 1 mal · 1 sin revisar» para el historial y las exportaciones."""
    r = checklists.recuento(items)
    partes = []
    if r["ok"]: partes.append(tt("chk_resumen_ok", "{n} bien").format(n=r["ok"]))
    if r["mal"]: partes.append(tt("chk_resumen_mal", "{n} mal").format(n=r["mal"]))
    if r["na"]: partes.append(tt("chk_resumen_na", "{n} no aplica").format(n=r["na"]))
    if r["sin"]: partes.append(tt("chk_resumen_sin", "{n} sin revisar").format(n=r["sin"]))
    return " · ".join(partes)


def estado_plano(estado):
    """Resultado en texto sin emojis (para PDF, Excel y CSV)."""
    return {"ok": tt("chk_txt_ok", "Bien"), "mal": tt("chk_txt_mal", "Mal"),
            "na": tt("chk_txt_na", "No aplica")}.get(estado, tt("chk_txt_sin", "Sin revisar"))


def linea_export(it):
    """«Presión de trabajo: Mal — 9,1 bar (Revisar presostato)»."""
    texto = f"{it['texto']}: {estado_plano(it.get('estado'))}"
    if it.get("valor"):
        texto += f" — {it['valor']} {it.get('unidad') or ''}".rstrip()
    if it.get("nota"):
        texto += f" ({it['nota']})"
    return texto


def texto_export(lista):
    """Toda la lista en una celda (CSV y Excel)."""
    if not lista:
        return "-"
    return lista["plantilla"] + "\n" + "\n".join("• " + linea_export(it) for it in lista["items"])


def llenar_combo_plantillas(combo, seleccionada=None):
    """Combo con «Sin lista» y las plantillas; deja elegida [seleccionada]."""
    combo.clear()
    combo.addItem(tt("chk_sin_lista", "— Sin lista de comprobación —"), None)
    for p in checklists.listar_plantillas():
        combo.addItem(f"☑️ {p['nombre']} ({len(p['puntos'])})", p["id"])
    i = combo.findData(seleccionada)
    combo.setCurrentIndex(i if i >= 0 else 0)


# ------------------------------------------------------------------ rellenar

class DialogoRellenarChecklist(QDialog):
    """Rellena (o muestra, con solo_lectura) una lista de comprobación.
    items(): la lista con lo marcado."""

    COL_PUNTO, COL_ESTADO, COL_VALOR, COL_NOTA = 0, 1, 2, 3

    def __init__(self, parent, titulo, items, plantilla_nombre="", solo_lectura=False):
        super().__init__(parent)
        self._items = [dict(it) for it in items]
        self.solo_lectura = solo_lectura
        self.setWindowTitle(tt("title_checklist", "Lista de comprobación"))
        self.resize(900, 520)
        l = QVBoxLayout(self)
        cabecera = QLabel(f"<b>{titulo}</b>" + (f"<br>☑️ {plantilla_nombre}" if plantilla_nombre else ""))
        cabecera.setWordWrap(True)
        l.addWidget(cabecera)

        self.tabla = QTableWidget(len(self._items), 4)
        self.tabla.setHorizontalHeaderLabels([tt("chk_col_punto", "Punto"), tt("chk_col_resultado", "Resultado"),
                                              tt("chk_col_lectura", "Lectura"), tt("chk_col_nota", "Nota")])
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(self.COL_PUNTO, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(self.COL_ESTADO, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(self.COL_VALOR, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(self.COL_NOTA, QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._grupos, self._valores, self._notas = [], [], []
        for fila, it in enumerate(self._items):
            texto = it["texto"]
            if it["tipo"] == "lectura" and texto_rango(it):
                texto += f"\n({tt('chk_rango', 'correcto')}: {texto_rango(it)})"
            celda = QTableWidgetItem(texto)
            celda.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.tabla.setItem(fila, self.COL_PUNTO, celda)

            caja = QWidget(); h = QHBoxLayout(caja); h.setContentsMargins(4, 0, 4, 0)
            grupo = QButtonGroup(caja)
            for estado in checklists.ESTADOS:
                rb = QRadioButton(texto_estado(estado))
                rb.setProperty("estado", estado)
                rb.setChecked(it.get("estado") == estado)
                rb.setEnabled(not solo_lectura)
                grupo.addButton(rb); h.addWidget(rb)
            self.tabla.setCellWidget(fila, self.COL_ESTADO, caja)
            self._grupos.append(grupo)

            if it["tipo"] == "lectura":
                valor = QLineEdit(it.get("valor") or "")
                valor.setPlaceholderText(it.get("unidad") or tt("chk_valor", "valor"))
                valor.setMaximumWidth(120)
                valor.setReadOnly(solo_lectura)
                valor.textChanged.connect(lambda _txt, f=fila: self._lectura_cambiada(f))
                caja_v = QWidget(); hv = QHBoxLayout(caja_v); hv.setContentsMargins(4, 0, 4, 0)
                hv.addWidget(valor)
                if it.get("unidad"):
                    hv.addWidget(QLabel(it["unidad"]))
                self.tabla.setCellWidget(fila, self.COL_VALOR, caja_v)
                self._valores.append(valor)
                self._pintar_rango(fila)
            else:
                self._valores.append(None)
                vacia = QTableWidgetItem(""); vacia.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.tabla.setItem(fila, self.COL_VALOR, vacia)

            nota = QLineEdit(it.get("nota") or "")
            nota.setReadOnly(solo_lectura)
            self.tabla.setCellWidget(fila, self.COL_NOTA, nota)
            self._notas.append(nota)
        self.tabla.resizeRowsToContents()
        l.addWidget(self.tabla)

        botones = QHBoxLayout()
        if not solo_lectura:
            todo_bien = QPushButton(tt("btn_chk_todo_bien", "✅ Marcar los que faltan como bien"))
            todo_bien.clicked.connect(self._todo_bien)
            botones.addWidget(todo_bien)
        botones.addStretch()
        if solo_lectura:
            cerrar = QPushButton(tt("cerrar", "Cerrar"))
            cerrar.clicked.connect(self.reject)
            botones.addWidget(cerrar)
        else:
            caja = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            caja.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
            caja.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
            caja.accepted.connect(self._aceptar)
            caja.rejected.connect(self.reject)
            botones.addWidget(caja)
        l.addLayout(botones)

    def _estado_de(self, fila):
        b = self._grupos[fila].checkedButton()
        return b.property("estado") if b else None

    def _marcar(self, fila, estado):
        for b in self._grupos[fila].buttons():
            if b.property("estado") == estado:
                b.setChecked(True)

    def _pintar_rango(self, fila):
        campo = self._valores[fila]
        fuera = checklists.fuera_de_rango(self._items[fila], campo.text())
        campo.setStyleSheet("color: #c0392b; font-weight: bold;" if fuera else "")

    def _lectura_cambiada(self, fila):
        self._pintar_rango(fila)
        texto = self._valores[fila].text().strip()
        if not texto:
            return
        # Fuera de rango: «mal». Dentro y sin marcar todavía: «bien».
        if checklists.fuera_de_rango(self._items[fila], texto):
            self._marcar(fila, "mal")
        elif self._estado_de(fila) is None:
            self._marcar(fila, "ok")

    def _todo_bien(self):
        for fila in range(len(self._items)):
            if self._estado_de(fila) is None:
                self._marcar(fila, "ok")

    def items(self):
        resultado = []
        for fila, it in enumerate(self._items):
            nuevo = dict(it)
            nuevo["estado"] = self._estado_de(fila)
            nuevo["valor"] = self._valores[fila].text().strip() if self._valores[fila] is not None else ""
            nuevo["nota"] = self._notas[fila].text().strip()
            resultado.append(nuevo)
        return resultado

    def _aceptar(self):
        faltan = checklists.sin_marcar(self.items())
        if faltan:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle(self.windowTitle())
            msg.setText(tt("msg_chk_sin_marcar",
                "Quedan {n} puntos sin revisar. Se guardarán como «sin revisar».\n\n¿Completar igualmente?").format(n=len(faltan)))
            si = msg.addButton(tt("btn_chk_completar_igual", "Completar igualmente"), QMessageBox.ButtonRole.AcceptRole)
            msg.addButton(tt("btn_chk_volver", "Volver a la lista"), QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            if msg.clickedButton() != si:
                return
        self.accept()


def rellenar_para(parent, plantilla_id, titulo):
    """Al completar un aviso o un pendiente con lista: la pide rellenar.
    Devuelve (items, nombre de la plantilla), ([], "") si no tiene lista (o la
    plantilla ya no existe), o None si se cancela."""
    plantilla = checklists.obtener_plantilla(plantilla_id) if plantilla_id else None
    if not plantilla or not plantilla["puntos"]:
        return [], ""
    dlg = DialogoRellenarChecklist(parent, titulo, checklists.items_de_plantilla(plantilla), plantilla["nombre"])
    if not dlg.exec():
        return None
    return dlg.items(), plantilla["nombre"]


# ------------------------------------------------------------------ plantillas

class DialogoPlantillasChecklist(QDialog):
    """Herramientas → Listas de comprobación: crear, editar y borrar plantillas."""

    COL_TEXTO, COL_TIPO, COL_UNIDAD, COL_MIN, COL_MAX = range(5)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_plantillas_checklist", "Listas de comprobación"))
        self.resize(1000, 560)
        self._actual = None      # id de la plantilla en edición (None: nueva)
        self._modificada = False

        l = QVBoxLayout(self)
        ayuda = QLabel(tt("lbl_info_plantillas_checklist",
            "Crea aquí las listas de comprobación y asígnalas a los avisos recurrentes y a los pendientes. "
            "Al completarlos, se pide rellenar la lista y queda guardada con el trabajo en el historial. "
            "Los puntos de tipo «Lectura» piden además un valor (con su unidad); si se sale del mínimo o el máximo, quedan como «mal»."))
        ayuda.setWordWrap(True)
        l.addWidget(ayuda)

        split = QSplitter(Qt.Orientation.Horizontal)
        izq = QWidget(); li = QVBoxLayout(izq); li.setContentsMargins(0, 0, 0, 0)
        self.lista = QListWidget()
        self.lista.currentItemChanged.connect(self._elegida)
        li.addWidget(self.lista)
        fila = QHBoxLayout()
        b_nueva = QPushButton(tt("btn_chk_nueva", "➕ Nueva lista")); b_nueva.clicked.connect(self._nueva)
        b_dup = QPushButton(tt("btn_chk_duplicar", "📄 Duplicar")); b_dup.clicked.connect(self._duplicar)
        b_borrar = QPushButton(tt("btn_chk_borrar", "🗑️ Borrar")); b_borrar.clicked.connect(self._borrar)
        for b in (b_nueva, b_dup, b_borrar): fila.addWidget(b)
        li.addLayout(fila)
        split.addWidget(izq)

        der = QWidget(); ld = QVBoxLayout(der); ld.setContentsMargins(0, 0, 0, 0)
        fila_n = QHBoxLayout()
        fila_n.addWidget(QLabel(tt("lbl_chk_nombre", "Nombre") + ":"))
        self.nombre = QLineEdit(); self.nombre.setPlaceholderText(tt("ph_chk_nombre", "p. ej. Revisión mensual de compresor"))
        self.nombre.textEdited.connect(self._tocada)
        fila_n.addWidget(self.nombre, 1)
        ld.addLayout(fila_n)
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels([tt("chk_col_punto", "Punto"), tt("chk_col_tipo", "Tipo"),
                                              tt("chk_col_unidad", "Unidad"), tt("chk_col_minimo", "Mínimo"),
                                              tt("chk_col_maximo", "Máximo")])
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(self.COL_TEXTO, QHeaderView.ResizeMode.Stretch)
        for c in (self.COL_TIPO, self.COL_UNIDAD, self.COL_MIN, self.COL_MAX):
            cab.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.itemChanged.connect(self._tocada)
        ld.addWidget(self.tabla)
        fila_p = QHBoxLayout()
        for texto, accion in ((tt("btn_chk_anadir_punto", "➕ Añadir punto"), self._anadir_punto),
                              (tt("btn_chk_quitar_punto", "➖ Quitar"), self._quitar_punto),
                              ("⬆️", lambda: self._mover(-1)), ("⬇️", lambda: self._mover(1))):
            b = QPushButton(texto); b.clicked.connect(accion); fila_p.addWidget(b)
        fila_p.addStretch()
        self.b_guardar = QPushButton(tt("btn_guardar", "Guardar")); self.b_guardar.clicked.connect(self._guardar)
        fila_p.addWidget(self.b_guardar)
        ld.addLayout(fila_p)
        split.addWidget(der)
        split.setSizes([300, 700])
        l.addWidget(split, 1)   # que la ayuda de arriba no se estire

        cerrar = QPushButton(tt("cerrar", "Cerrar")); cerrar.clicked.connect(self.close)
        fila_c = QHBoxLayout(); fila_c.addStretch(); fila_c.addWidget(cerrar)
        l.addLayout(fila_c)

        self._recargar()
        if self.lista.count():
            self.lista.setCurrentRow(0)
        else:
            self._nueva()

    # --- lista de plantillas
    def _recargar(self, elegir=None):
        self.lista.blockSignals(True)
        self.lista.clear()
        for p in checklists.listar_plantillas():
            item = QListWidgetItem(f"☑️ {p['nombre']}  ({len(p['puntos'])})")
            item.setData(Qt.ItemDataRole.UserRole, p["id"])
            self.lista.addItem(item)
            if p["id"] == elegir:
                self.lista.setCurrentItem(item)
        self.lista.blockSignals(False)

    def _preguntar_guardar(self):
        """Si hay cambios sin guardar, pregunta. False si se cancela."""
        if not self._modificada:
            return True
        r = QMessageBox.question(self, self.windowTitle(),
            tt("msg_chk_guardar_cambios", "¿Guardar los cambios de la lista «{nombre}»?").format(nombre=self.nombre.text() or "…"),
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        if r == QMessageBox.StandardButton.Cancel:
            return False
        if r == QMessageBox.StandardButton.Save:
            return self._guardar()
        return True

    def _elegida(self, item, anterior=None):
        if item is None:
            return
        if not self._preguntar_guardar():
            self.lista.blockSignals(True); self.lista.setCurrentItem(anterior); self.lista.blockSignals(False)
            return
        self._cargar(checklists.obtener_plantilla(item.data(Qt.ItemDataRole.UserRole)))

    def _cargar(self, plantilla):
        self.tabla.blockSignals(True)
        self._actual = plantilla["id"] if plantilla else None
        self.nombre.setText(plantilla["nombre"] if plantilla else "")
        self.tabla.setRowCount(0)
        for p in (plantilla["puntos"] if plantilla else []):
            self._fila_punto(p)
        self.tabla.blockSignals(False)
        self._modificada = False

    def _fila_punto(self, p=None):
        p = p or {"texto": "", "tipo": "estado", "unidad": "", "minimo": None, "maximo": None}
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        self.tabla.setItem(fila, self.COL_TEXTO, QTableWidgetItem(p["texto"]))
        combo = QComboBox()
        combo.addItem(tt("chk_tipo_estado", "Bien / Mal"), "estado")
        combo.addItem(tt("chk_tipo_lectura", "Lectura"), "lectura")
        combo.setCurrentIndex(1 if p["tipo"] == "lectura" else 0)
        combo.currentIndexChanged.connect(lambda _i, c=combo: self._tipo_cambiado(c))
        self.tabla.setCellWidget(fila, self.COL_TIPO, combo)
        fmt = lambda n: "" if n is None else f"{n:g}"
        for col, valor in ((self.COL_UNIDAD, p.get("unidad") or ""), (self.COL_MIN, fmt(p.get("minimo"))),
                           (self.COL_MAX, fmt(p.get("maximo")))):
            self.tabla.setItem(fila, col, QTableWidgetItem(valor))
        self._activar_lectura(fila, p["tipo"] == "lectura")

    def _activar_lectura(self, fila, lectura):
        for col in (self.COL_UNIDAD, self.COL_MIN, self.COL_MAX):
            item = self.tabla.item(fila, col)
            if item is None:
                continue
            if lectura:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setText("")
                item.setFlags(Qt.ItemFlag.NoItemFlags)

    def _tipo_cambiado(self, combo):
        for fila in range(self.tabla.rowCount()):
            if self.tabla.cellWidget(fila, self.COL_TIPO) is combo:
                self.tabla.blockSignals(True)
                self._activar_lectura(fila, combo.currentData() == "lectura")
                self.tabla.blockSignals(False)
        self._tocada()

    def _tocada(self, *_):
        self._modificada = True

    def _puntos(self):
        puntos = []
        for fila in range(self.tabla.rowCount()):
            texto = (self.tabla.item(fila, self.COL_TEXTO).text() if self.tabla.item(fila, self.COL_TEXTO) else "").strip()
            if not texto:
                continue
            leer = lambda col: self.tabla.item(fila, col).text() if self.tabla.item(fila, col) else ""
            puntos.append({"texto": texto, "tipo": self.tabla.cellWidget(fila, self.COL_TIPO).currentData(),
                           "unidad": leer(self.COL_UNIDAD), "minimo": leer(self.COL_MIN), "maximo": leer(self.COL_MAX)})
        return puntos

    def _anadir_punto(self):
        self._fila_punto()
        fila = self.tabla.rowCount() - 1
        self.tabla.setCurrentCell(fila, self.COL_TEXTO)
        self.tabla.editItem(self.tabla.item(fila, self.COL_TEXTO))
        self._tocada()

    def _quitar_punto(self):
        fila = self.tabla.currentRow()
        if fila >= 0:
            self.tabla.removeRow(fila)
            self._tocada()

    def _mover(self, paso):
        fila = self.tabla.currentRow()
        destino = fila + paso
        if fila < 0 or not (0 <= destino < self.tabla.rowCount()):
            return
        puntos = []
        for f in range(self.tabla.rowCount()):
            leer = lambda col: self.tabla.item(f, col).text() if self.tabla.item(f, col) else ""
            puntos.append({"texto": leer(self.COL_TEXTO), "tipo": self.tabla.cellWidget(f, self.COL_TIPO).currentData(),
                           "unidad": leer(self.COL_UNIDAD), "minimo": checklists._num(leer(self.COL_MIN)),
                           "maximo": checklists._num(leer(self.COL_MAX))})
        puntos[fila], puntos[destino] = puntos[destino], puntos[fila]
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)
        for p in puntos:
            self._fila_punto(p)
        self.tabla.blockSignals(False)
        self.tabla.setCurrentCell(destino, self.COL_TEXTO)
        self._tocada()

    def _guardar(self):
        nombre = self.nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, self.windowTitle(), tt("msg_chk_falta_nombre", "Ponle un nombre a la lista."))
            return False
        puntos = self._puntos()
        if not puntos:
            QMessageBox.warning(self, self.windowTitle(), tt("msg_chk_sin_puntos", "Añade al menos un punto a la lista."))
            return False
        self._actual = checklists.guardar_plantilla(self._actual, nombre, puntos)
        self._modificada = False
        self.lista.blockSignals(True)
        self._recargar(elegir=self._actual)
        self.lista.blockSignals(False)
        return True

    def _nueva(self):
        if not self._preguntar_guardar():
            return
        self.lista.blockSignals(True); self.lista.clearSelection(); self.lista.setCurrentRow(-1); self.lista.blockSignals(False)
        self._cargar(None)
        self._anadir_punto()
        self._modificada = False
        self.nombre.setFocus()

    def _duplicar(self):
        if self._actual is None or not self._preguntar_guardar():
            return
        p = checklists.obtener_plantilla(self._actual)
        nuevo = checklists.guardar_plantilla(None, f"{p['nombre']} ({tt('chk_copia', 'copia')})", p["puntos"])
        self._recargar(elegir=nuevo)
        self._cargar(checklists.obtener_plantilla(nuevo))

    def _borrar(self):
        if self._actual is None:
            return
        avisos, pendientes = checklists.usos_de_plantilla(self._actual)
        texto = tt("msg_chk_borrar", "¿Borrar la lista «{nombre}»?").format(nombre=self.nombre.text())
        if avisos or pendientes:
            texto += "\n\n" + tt("msg_chk_borrar_usos",
                "La usan {a} avisos y {p} pendientes, que se quedarán sin lista. Lo ya rellenado en el historial se conserva.").format(a=avisos, p=pendientes)
        if QMessageBox.question(self, self.windowTitle(), texto) != QMessageBox.StandardButton.Yes:
            return
        checklists.borrar_plantilla(self._actual)
        self._modificada = False
        self._recargar()
        if self.lista.count():
            self.lista.setCurrentRow(0)
        else:
            self._cargar(None)

    def closeEvent(self, e):
        if not self._preguntar_guardar():
            e.ignore()
            return
        super().closeEvent(e)

    def reject(self):
        if self._preguntar_guardar():
            super().reject()



def texto_repuestos_export(mats, moneda):
    """Repuestos usados en una celda (CSV y Excel) o en el PDF."""
    if not mats:
        return "-"
    from ...nucleo import consumos
    lineas = [f"• {m['cantidad']:g} {m.get('unidad') or ''} {m['nombre']}".replace("  ", " ") +
              (f" — {consumos.formato_importe(m['importe'], moneda)}" if m.get("importe") is not None else "")
              for m in mats]
    importe, sin_precio = consumos.coste(mats)
    lineas.append(f"{tt('lbl_coste_material', 'Coste de material')}: {consumos.formato_importe(importe, moneda)}" +
                  (f" ({tt('lbl_sin_precio_algunos', '(hay artículos sin precio)').strip('()')})" if sin_precio else ""))
    return "\n".join(lineas)



def texto_tiempo_export(t, moneda):
    """«1 h 30 min × 2 — 54,00 €» (o «-» si no hay tiempo apuntado)."""
    if not t:
        return "-"
    from ...nucleo import consumos, mano_obra
    texto = mano_obra.texto_tiempo(t)
    if t.get("importe") is not None:
        texto += f" — {consumos.formato_importe(t['importe'], moneda)}"
    return texto
