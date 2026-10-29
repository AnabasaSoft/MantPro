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

"""Diálogos del almacén: estructura, ubicaciones, materiales y movimientos."""

import os
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
                             QMessageBox, QDialog, QDialogButtonBox, QAbstractItemView, QComboBox,
                             QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QRadioButton, QMenu,
                             QTreeWidget, QTreeWidgetItem, QInputDialog, QFormLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QPixmap

from ...idiomas import t
from ... import idiomas
from ..comun import _estilo_zona_arrastre, traducir_motivo_movimiento, tt
from ..widgets.fotos import DialogoSelectorFoto, VisorFoto
from ...nucleo import almacen

# ==========================================
# DIÁLOGOS DE STOCK DE ALMACÉN
# ==========================================
class DialogoNuevaEstanteria(QDialog):
    """Alta de una estantería nueva: nombre, número de baldas y si tiene hueco de suelo.
    Si se pasa `estanteria` (el dict que devuelve almacen.listar_estructura()), se abre
    en modo edición con la misma ventana y todos los campos rellenados con los valores
    actuales: se puede cambiar el nombre, el estilo de las baldas, el hueco de suelo y
    subir o bajar el número de baldas (al subir, se añaden por arriba continuando la
    numeración, creando en cada una el número de secciones indicado; al bajar, se
    borran las de numeración más alta, deteniéndose en la primera que tenga material).
    El número de secciones y su estilo solo se aplican a las baldas nuevas que se
    añadan aquí, no a las que ya existían."""
    def __init__(self, parent=None, estanteria=None):
        super().__init__(parent)
        self._editando = estanteria is not None
        self.setWindowTitle(tt("title_editar_estanteria", "Editar estantería") if self._editando
                             else tt("title_nueva_estanteria", "Nueva estantería"))
        self.resize(380, 220)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_nombre_estanteria", "Nombre de la estantería")))
        self.campo_nombre = QLineEdit(); self.campo_nombre.setPlaceholderText(tt("ph_nombre_estanteria", "ej. Estantería A"))
        l.addWidget(self.campo_nombre)
        lbl_num_baldas = QLabel(tt("lbl_num_baldas", "Número de baldas"))
        l.addWidget(lbl_num_baldas)
        self.spin_baldas = QSpinBox(); self.spin_baldas.setRange(1, 30); self.spin_baldas.setValue(3)
        l.addWidget(self.spin_baldas)
        lbl_num_secciones = QLabel(tt("lbl_num_secciones", "Número de secciones por balda"))
        l.addWidget(lbl_num_secciones)
        self.spin_secciones = QSpinBox(); self.spin_secciones.setRange(0, 30); self.spin_secciones.setValue(0)
        self.spin_secciones.setToolTip(tt("tt_num_secciones", "0 = sin secciones predefinidas (se pueden añadir después)"))
        l.addWidget(self.spin_secciones)
        self.chk_hueco_suelo = QCheckBox(tt("txt_hueco_suelo", "Tiene hueco en el suelo (bajo la balda inferior)"))
        l.addWidget(self.chk_hueco_suelo)

        l.addWidget(QLabel(tt("lbl_estilo_baldas", "Numerar las baldas con")))
        self.combo_estilo_baldas = QComboBox()
        self.combo_estilo_baldas.addItem(tt("txt_numeros", "Números (1, 2, 3...)"), "numero")
        self.combo_estilo_baldas.addItem(tt("txt_letras", "Letras (A, B, C...)"), "letra")
        l.addWidget(self.combo_estilo_baldas)

        lbl_estilo_secciones = QLabel(tt("lbl_estilo_secciones", "Nombrar las secciones con"))
        l.addWidget(lbl_estilo_secciones)
        self.combo_estilo_secciones = QComboBox()
        self.combo_estilo_secciones.addItem(tt("txt_letras", "Letras (A, B, C...)"), "letra")
        self.combo_estilo_secciones.addItem(tt("txt_numeros", "Números (1, 2, 3...)"), "numero")
        l.addWidget(self.combo_estilo_secciones)

        if self._editando:
            self.campo_nombre.setText(estanteria["nombre"])
            num_baldas_actual = sum(1 for b in estanteria["baldas"] if b["numero"] != 0)
            self.spin_baldas.setValue(max(1, num_baldas_actual))
            self.chk_hueco_suelo.setChecked(bool(estanteria.get("tiene_hueco_suelo")))
            idx = self.combo_estilo_baldas.findData(estanteria.get("estilo_baldas", "numero"))
            if idx >= 0:
                self.combo_estilo_baldas.setCurrentIndex(idx)
            self.spin_secciones.setValue(0)
            tt_solo_nuevas = tt("tt_solo_baldas_nuevas", "Solo se aplica a las baldas nuevas que se añadan al subir el número de baldas")
            lbl_num_secciones.setToolTip(tt_solo_nuevas)
            self.spin_secciones.setToolTip(tt_solo_nuevas)
            lbl_estilo_secciones.setToolTip(tt_solo_nuevas)
            self.combo_estilo_secciones.setToolTip(tt_solo_nuevas)

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def get_data(self):
        return (self.campo_nombre.text().strip(), self.spin_baldas.value(),
                self.chk_hueco_suelo.isChecked(), self.spin_secciones.value(),
                self.combo_estilo_baldas.currentData(), self.combo_estilo_secciones.currentData())


class DialogoConfigurarAlmacen(QDialog):
    """Gestión de la estructura del almacén: estanterías > baldas > secciones. Solo admin."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_configurar_almacen", "Configurar almacén"))
        self.resize(560, 520)
        l = QVBoxLayout()

        hz = QHBoxLayout()
        hz.addWidget(QLabel(tt("lbl_zona", "Zona")))
        self.combo_zona = QComboBox()
        self.combo_zona.currentIndexChanged.connect(self._cambiar_zona)
        hz.addWidget(self.combo_zona, 1)
        btn_nueva_zona = QPushButton(tt("btn_nueva_zona_almacen", "➕ Nueva zona")); btn_nueva_zona.clicked.connect(self.nueva_zona)
        btn_renombrar_zona = QPushButton(tt("btn_renombrar_zona", "✏️ Renombrar zona")); btn_renombrar_zona.clicked.connect(self.renombrar_zona)
        btn_eliminar_zona = QPushButton(tt("btn_eliminar_zona", "🗑️ Eliminar zona")); btn_eliminar_zona.clicked.connect(self.eliminar_zona)
        hz.addWidget(btn_nueva_zona); hz.addWidget(btn_renombrar_zona); hz.addWidget(btn_eliminar_zona)
        l.addLayout(hz)

        self.arbol = QTreeWidget(); self.arbol.setHeaderHidden(True)
        self.arbol.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.arbol.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.arbol.customContextMenuRequested.connect(self._mostrar_menu_contextual)
        l.addWidget(self.arbol)

        h0 = QHBoxLayout()
        btn_expandir = QPushButton(tt("btn_expandir_todo", "⬇️ Expandir todo")); btn_expandir.clicked.connect(self.arbol.expandAll)
        btn_contraer = QPushButton(tt("btn_contraer_todo", "⬆️ Contraer todo")); btn_contraer.clicked.connect(self.arbol.collapseAll)
        h0.addWidget(btn_expandir); h0.addWidget(btn_contraer)
        l.addLayout(h0)

        h1 = QHBoxLayout()
        btn_add_est = QPushButton(tt("btn_anadir_estanteria", "➕ Añadir estantería")); btn_add_est.clicked.connect(self.anadir_estanteria)
        btn_del_est = QPushButton(tt("btn_eliminar_estanteria", "🗑️ Eliminar estantería")); btn_del_est.clicked.connect(self.eliminar_estanteria)
        h1.addWidget(btn_add_est); h1.addWidget(btn_del_est)
        l.addLayout(h1)

        h2 = QHBoxLayout()
        btn_add_balda = QPushButton(tt("btn_anadir_balda", "➕ Añadir balda")); btn_add_balda.clicked.connect(self.anadir_balda)
        btn_del_balda = QPushButton(tt("btn_eliminar_balda", "🗑️ Eliminar balda")); btn_del_balda.clicked.connect(self.eliminar_balda)
        h2.addWidget(btn_add_balda); h2.addWidget(btn_del_balda)
        l.addLayout(h2)

        h3 = QHBoxLayout()
        btn_add_sec = QPushButton(tt("btn_anadir_seccion", "➕ Añadir sección")); btn_add_sec.clicked.connect(self.anadir_seccion)
        btn_del_sec = QPushButton(tt("btn_eliminar_seccion", "🗑️ Eliminar sección")); btn_del_sec.clicked.connect(self.eliminar_seccion)
        h3.addWidget(btn_add_sec); h3.addWidget(btn_del_sec)
        l.addLayout(h3)

        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept)
        l.addWidget(btn_cerrar)
        self.setLayout(l)
        self._cargar_zonas()

    def _cargar_zonas(self, preferir_id=None):
        """Rellena el desplegable de zonas conservando (o forzando con
        preferir_id) la selección actual, y refresca el árbol para la zona
        que quede seleccionada."""
        zona_previa = preferir_id if preferir_id is not None else self.combo_zona.currentData()
        self._zonas = almacen.listar_zonas()
        self.combo_zona.blockSignals(True)
        self.combo_zona.clear()
        for zona in self._zonas:
            self.combo_zona.addItem(zona["nombre"], zona["id"])
        idx = self.combo_zona.findData(zona_previa)
        self.combo_zona.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_zona.blockSignals(False)
        self.refrescar()

    def _cambiar_zona(self, _idx):
        self.refrescar()

    def nueva_zona(self):
        nombre, ok = QInputDialog.getText(self, tt("title_nueva_zona_almacen", "Nueva zona"), tt("lbl_nombre_zona_almacen", "Nombre de la zona"))
        if ok and nombre.strip():
            zona_id = almacen.crear_zona(nombre.strip())
            self._cargar_zonas(preferir_id=zona_id)

    def renombrar_zona(self):
        zona_id = self.combo_zona.currentData()
        if zona_id is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_zona_requerida", "Selecciona una zona.")); return
        nombre, ok = QInputDialog.getText(self, tt("title_renombrar_zona", "Renombrar zona"),
                                           tt("lbl_nombre_zona_almacen", "Nombre de la zona"), text=self.combo_zona.currentText())
        if ok and nombre.strip():
            almacen.renombrar_zona(zona_id, nombre.strip())
            self._cargar_zonas(preferir_id=zona_id)

    def eliminar_zona(self):
        zona_id = self.combo_zona.currentData()
        if zona_id is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_zona_requerida", "Selecciona una zona.")); return
        nombre_zona = self.combo_zona.currentText()
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "msg_confirmar_eliminar_zona", "¿Eliminar la zona «{nombre}»?").format(nombre=nombre_zona)) != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen.eliminar_zona(zona_id)
        if not ok and error == "contiene_estanterias":
            n = len(almacen.zona_estanterias(zona_id))
            if QMessageBox.warning(self, tt("aviso", "Aviso"), tt(
                    "msg_zona_contiene_estanterias",
                    "Esta zona contiene {n} estantería(s). Si continúas, se eliminarán también esas estanterías y toda su estructura. ¿Continuar?").format(n=n),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            ok, error = almacen.eliminar_zona(zona_id, forzar=True)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_elemento_no_vacio", "No se puede eliminar: todavía contiene material ubicado."))
        self._cargar_zonas()

    def refrescar(self):
        self.arbol.clear()
        # Un color de texto distinto por nivel (estantería/balda/hueco de suelo/sección)
        # para que la jerarquía se distinga de un vistazo, ajustado según el tema activo.
        oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
        col_est = QColor("#5fa8e8") if oscuro else QColor("#0d3862")
        col_balda = QColor("#6fcf7a") if oscuro else QColor("#1e6620")
        col_suelo = QColor("#e0b34d") if oscuro else QColor("#8a6210")
        col_sec = QColor("#c98be0") if oscuro else QColor("#6a2d8a")
        self._estructura = almacen.listar_estructura(self.combo_zona.currentData())
        for est in self._estructura:
            item_est = QTreeWidgetItem([f"🗄️ {est['nombre']}"])
            item_est.setData(0, Qt.ItemDataRole.UserRole, ("estanteria", est["id"]))
            item_est.setForeground(0, col_est)
            for balda in est["baldas"]:
                es_suelo = balda["numero"] == 0
                nombre_balda = tt("txt_hueco_suelo_corto", "Hueco de suelo") if es_suelo else tt(
                    "txt_balda_num", "Balda {n}").format(n=almacen.texto_balda(balda["numero"], est.get("estilo_baldas", "numero")))
                item_balda = QTreeWidgetItem([f"📚 {nombre_balda}"])
                item_balda.setData(0, Qt.ItemDataRole.UserRole, ("balda", balda["id"]))
                item_balda.setForeground(0, col_suelo if es_suelo else col_balda)
                for sec in balda["secciones"]:
                    # Las secciones implícitas (creadas solas al ubicar un
                    # material directamente en la balda, sin elegir sección)
                    # no se muestran aquí: para el usuario ese material está
                    # "en la balda", no en una sección que él haya creado.
                    if sec.get("implicita"):
                        continue
                    item_sec = QTreeWidgetItem([f"📦 {sec['nombre']}"])
                    item_sec.setData(0, Qt.ItemDataRole.UserRole, ("seccion", sec["id"]))
                    item_sec.setForeground(0, col_sec)
                    item_balda.addChild(item_sec)
                item_est.addChild(item_balda)
            self.arbol.addTopLevelItem(item_est)
        self.arbol.expandAll()

    def _seleccion(self):
        item = self.arbol.currentItem()
        if not item: return None, None
        return item.data(0, Qt.ItemDataRole.UserRole)

    def anadir_estanteria(self):
        zona_id = self.combo_zona.currentData()
        if zona_id is None:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_crea_zona_primero", "Crea antes una zona para poder añadir estanterías.")); return
        dlg = DialogoNuevaEstanteria(self)
        if dlg.exec():
            nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones = dlg.get_data()
            if not nombre:
                QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_nombre_obligatorio", "El nombre es obligatorio.")); return
            almacen.crear_estanteria(nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones, zona_id=zona_id)
            self.refrescar()

    def eliminar_estanteria(self):
        tipo, id_ = self._seleccion()
        if tipo != "estanteria":
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_estanteria_requerida", "Selecciona una estantería.")); return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt("msg_confirmar_eliminar_estanteria", "¿Eliminar esta estantería y toda su estructura?")) != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen.eliminar_estanteria(id_)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_elemento_no_vacio", "No se puede eliminar: todavía contiene material ubicado."))
        self.refrescar()

    def anadir_balda(self):
        tipo, id_ = self._seleccion()
        estanteria_id = None
        item = self.arbol.currentItem()
        if tipo == "estanteria":
            estanteria_id = id_
        elif tipo == "balda":
            estanteria_id = item.parent().data(0, Qt.ItemDataRole.UserRole)[1]
        else:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_estanteria_requerida", "Selecciona una estantería.")); return
        almacen.anadir_balda(estanteria_id)
        self.refrescar()

    def eliminar_balda(self):
        tipo, id_ = self._seleccion()
        if tipo != "balda":
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_balda_requerida", "Selecciona una balda.")); return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt("msg_confirmar_eliminar_balda", "¿Eliminar esta balda y sus secciones?")) != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen.eliminar_balda(id_)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_elemento_no_vacio", "No se puede eliminar: todavía contiene material ubicado."))
        self.refrescar()

    def anadir_seccion(self):
        tipo, id_ = self._seleccion()
        if tipo != "balda":
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_balda_requerida", "Selecciona una balda.")); return
        nombre, ok = QInputDialog.getText(self, tt("title_nueva_seccion", "Nueva sección"), tt("lbl_nombre_seccion", "Nombre de la sección"))
        if ok and nombre.strip():
            almacen.crear_seccion(id_, nombre.strip())
            self.refrescar()

    def eliminar_seccion(self):
        tipo, id_ = self._seleccion()
        if tipo != "seccion":
            QMessageBox.information(self, tt("aviso", "Aviso"), tt("msg_seleccion_seccion_requerida", "Selecciona una sección.")); return
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt("msg_confirmar_eliminar_seccion", "¿Eliminar esta sección?")) != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen.eliminar_seccion(id_)
        if not ok:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_elemento_no_vacio", "No se puede eliminar: todavía contiene material ubicado."))
        self.refrescar()

    def _mapa_baldas(self):
        """A partir de self._estructura (rellenada en refrescar), devuelve dos diccionarios:
        {balda_id: estanteria_id} y {balda_id: es_hueco_suelo}, para poder clasificar la
        selección múltiple del árbol sin volver a consultar la base de datos."""
        est_de_balda, es_suelo = {}, {}
        for est in self._estructura:
            for balda in est["baldas"]:
                est_de_balda[balda["id"]] = est["id"]
                es_suelo[balda["id"]] = balda["numero"] == 0
        return est_de_balda, es_suelo

    def _mostrar_menu_contextual(self, pos):
        items = self.arbol.selectedItems()
        if not items:
            return
        est_de_balda, es_suelo = self._mapa_baldas()
        ids_est, ids_balda, ids_suelo = set(), set(), set()
        estanterias_afectadas = set()
        for item in items:
            tipo, id_ = item.data(0, Qt.ItemDataRole.UserRole)
            if tipo == "estanteria":
                ids_est.add(id_)
                estanterias_afectadas.add(id_)
            elif tipo == "balda":
                estanterias_afectadas.add(est_de_balda.get(id_))
                (ids_suelo if es_suelo.get(id_) else ids_balda).add(id_)

        menu = QMenu(self)
        if len(ids_est) == 1:
            id_est = next(iter(ids_est))
            a = menu.addAction(tt("menu_editar_estanteria", "✏️ Editar estantería"))
            a.triggered.connect(lambda: self._editar_estanteria(id_est))
            menu.addSeparator()
        if ids_est:
            a = menu.addAction(tt("menu_borrar_estanterias", "🗑️ Borrar estanterías seleccionadas"))
            a.triggered.connect(lambda: self._borrar_estanterias_multiple(ids_est))
        if ids_balda:
            a = menu.addAction(tt("menu_borrar_baldas", "🗑️ Borrar baldas seleccionadas"))
            a.triggered.connect(lambda: self._borrar_baldas_multiple(ids_balda))
        if ids_suelo:
            a = menu.addAction(tt("menu_borrar_huecos_suelo", "🗑️ Borrar huecos de suelo seleccionados"))
            a.triggered.connect(lambda: self._borrar_baldas_multiple(ids_suelo))
        if estanterias_afectadas:
            if not menu.isEmpty():
                menu.addSeparator()
            a = menu.addAction(tt("menu_cambiar_a_numeros", "🔢 Cambiar baldas a números"))
            a.triggered.connect(lambda: self._cambiar_estilo_multiple(estanterias_afectadas, "numero"))
            a = menu.addAction(tt("menu_cambiar_a_letras", "🔤 Cambiar baldas a letras"))
            a.triggered.connect(lambda: self._cambiar_estilo_multiple(estanterias_afectadas, "letra"))
            menu.addSeparator()
            a = menu.addAction(tt("menu_anadir_baldas", "➕ Añadir balda a cada estantería seleccionada"))
            a.triggered.connect(lambda: self._anadir_baldas_multiple(estanterias_afectadas))
            a = menu.addAction(tt("menu_anadir_huecos_suelo", "➕ Añadir hueco de suelo a cada estantería seleccionada"))
            a.triggered.connect(lambda: self._anadir_huecos_suelo_multiple(estanterias_afectadas))
        if not menu.isEmpty():
            menu.exec(self.arbol.viewport().mapToGlobal(pos))

    def _editar_estanteria(self, estanteria_id):
        est = next((e for e in self._estructura if e["id"] == estanteria_id), None)
        if est is None:
            return
        dlg = DialogoNuevaEstanteria(self, estanteria=est)
        if dlg.exec():
            nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones = dlg.get_data()
            if not nombre:
                QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_nombre_obligatorio", "El nombre es obligatorio.")); return
            no_borradas = almacen.editar_estanteria(
                estanteria_id, nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones)
            if no_borradas:
                QMessageBox.warning(self, tt("aviso", "Aviso"), tt(
                    "msg_baldas_no_borradas", "No se han podido quitar {n} balda(s): todavía contienen material ubicado.").format(n=no_borradas))
            self.refrescar()

    def _borrar_estanterias_multiple(self, ids):
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "msg_confirmar_eliminar_estanterias", "¿Eliminar {n} estantería(s) y toda su estructura?").format(n=len(ids))) != QMessageBox.StandardButton.Yes:
            return
        fallidas = sum(1 for id_ in ids if not almacen.eliminar_estanteria(id_)[0])
        if fallidas:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt(
                "msg_algunas_no_vacias", "{n} elemento(s) no se han podido borrar porque todavía contienen material ubicado.").format(n=fallidas))
        self.refrescar()

    def _borrar_baldas_multiple(self, ids):
        if QMessageBox.question(self, tt("aviso", "Aviso"), tt(
                "msg_confirmar_eliminar_baldas", "¿Eliminar {n} elemento(s) seleccionado(s) y sus secciones?").format(n=len(ids))) != QMessageBox.StandardButton.Yes:
            return
        fallidas = sum(1 for id_ in ids if not almacen.eliminar_balda(id_)[0])
        if fallidas:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt(
                "msg_algunas_no_vacias", "{n} elemento(s) no se han podido borrar porque todavía contienen material ubicado.").format(n=fallidas))
        self.refrescar()

    def _cambiar_estilo_multiple(self, estanteria_ids, estilo):
        for id_ in estanteria_ids:
            almacen.cambiar_estilo_baldas(id_, estilo)
        self.refrescar()

    def _anadir_baldas_multiple(self, estanteria_ids):
        for id_ in estanteria_ids:
            almacen.anadir_balda(id_)
        self.refrescar()

    def _anadir_huecos_suelo_multiple(self, estanteria_ids):
        creados = sum(1 for id_ in estanteria_ids if almacen.anadir_hueco_suelo(id_))
        ya_existian = len(estanteria_ids) - creados
        if ya_existian:
            QMessageBox.information(self, tt("aviso", "Aviso"), tt(
                "msg_huecos_suelo_ya_existian", "{n} estantería(s) ya tenían hueco de suelo y no se han modificado.").format(n=ya_existian))
        self.refrescar()


def _seccion_destino(seccion_id, balda_id):
    """Sección donde se ubica un material: la elegida o, si se deja "Sin
    sección", la implícita de la balda (se crea si hace falta, igual que desde
    el móvil). Así la sección siempre es opcional."""
    if seccion_id is not None: return seccion_id
    return almacen.seccion_para_balda(balda_id) if balda_id is not None else None


class DialogoSeleccionarUbicacion(QDialog):
    """Elige estantería/balda/sección de destino, sin más datos, para mover uno o varios materiales a la vez."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_mover_material", "Mover a..."))
        self.resize(360, 200)
        l = QVBoxLayout()
        self.combo_estanteria = QComboBox(); self.combo_balda = QComboBox(); self.combo_seccion = QComboBox()
        l.addWidget(QLabel(tt("lbl_estanteria", "Estantería"))); l.addWidget(self.combo_estanteria)
        l.addWidget(QLabel(tt("lbl_balda", "Balda"))); l.addWidget(self.combo_balda)
        l.addWidget(QLabel(tt("lbl_seccion", "Sección"))); l.addWidget(self.combo_seccion)
        self._estructura = almacen.listar_estructura()
        for est in self._estructura:
            self.combo_estanteria.addItem(est["nombre"], est["id"])
        self.combo_estanteria.currentIndexChanged.connect(self._actualizar_baldas)
        self.combo_balda.currentIndexChanged.connect(self._actualizar_secciones)
        self._actualizar_baldas()
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar_aceptar); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def _actualizar_baldas(self):
        self.combo_balda.clear()
        est_id = self.combo_estanteria.currentData()
        est = next((e for e in self._estructura if e["id"] == est_id), None)
        if est:
            for balda in est["baldas"]:
                nombre = tt("txt_hueco_suelo_corto", "Hueco de suelo") if balda["numero"] == 0 else tt(
                    "txt_balda_num", "Balda {n}").format(n=almacen.texto_balda(balda["numero"], est.get("estilo_baldas", "numero")))
                self.combo_balda.addItem(nombre, balda["id"])
        self._actualizar_secciones()

    def _actualizar_secciones(self):
        self.combo_seccion.clear()
        est_id = self.combo_estanteria.currentData()
        balda_id = self.combo_balda.currentData()
        est = next((e for e in self._estructura if e["id"] == est_id), None)
        if est:
            balda = next((b for b in est["baldas"] if b["id"] == balda_id), None)
            if balda:
                # La sección es opcional: "Sin sección" ubica el material en la
                # balda (ver _seccion_destino). Las implícitas, creadas solas
                # para eso, no se ofrecen como una sección más.
                self.combo_seccion.addItem(tt("lbl_sin_seccion", "Sin sección"), None)
                for sec in balda["secciones"]:
                    if sec.get("implicita"): continue
                    self.combo_seccion.addItem(sec["nombre"], sec["id"])

    def _validar_aceptar(self):
        if self.combo_balda.currentData() is None:
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_selecciona_balda", "Selecciona una estantería y una balda.")); return
        self.accept()

    def get_seccion_id(self):
        return _seccion_destino(self.combo_seccion.currentData(), self.combo_balda.currentData())


class DialogoEditarMaterial(QDialog):
    """Alta/edición de un material del almacén, con ubicación y foto opcional."""
    def __init__(self, parent=None, material=None):
        super().__init__(parent)
        self.material = material
        self.es_nuevo = material is None
        self.ruta_foto_seleccionada = ""
        self.foto_nombre_existente = material.get("foto") if material else None
        self.setWindowTitle(tt("title_nuevo_material", "Nuevo material") if self.es_nuevo else tt("title_editar_material", "Editar material"))
        self.resize(480, 620)
        l = QVBoxLayout()

        l.addWidget(QLabel(tt("lbl_codigo", "Código (opcional)")))
        self.campo_codigo = QLineEdit(material.get("codigo") or "" if material else "")
        l.addWidget(self.campo_codigo)

        l.addWidget(QLabel(tt("lbl_nombre_material", "Nombre del material")))
        self.campo_nombre = QLineEdit(material.get("nombre") or "" if material else "")
        l.addWidget(self.campo_nombre)

        l.addWidget(QLabel(tt("lbl_descripcion", "Descripción")))
        self.campo_desc = QTextEdit(material.get("descripcion") or "" if material else "")
        self.campo_desc.setMaximumHeight(70)
        l.addWidget(self.campo_desc)

        h_um = QHBoxLayout()
        v1 = QVBoxLayout(); v1.addWidget(QLabel(tt("lbl_unidad", "Unidad")))
        self.campo_unidad = QLineEdit(material.get("unidad") or "" if material else "")
        self.campo_unidad.setPlaceholderText(tt("ph_unidad", "ej. uds, m, kg..."))
        v1.addWidget(self.campo_unidad); h_um.addLayout(v1)
        v2 = QVBoxLayout(); v2.addWidget(QLabel(tt("lbl_stock_minimo", "Stock mínimo")))
        self.spin_minimo = QDoubleSpinBox(); self.spin_minimo.setRange(0, 999999); self.spin_minimo.setDecimals(2)
        self.spin_minimo.setValue(material.get("stock_minimo") or 0 if material else 0)
        v2.addWidget(self.spin_minimo); h_um.addLayout(v2)
        l.addLayout(h_um)

        if self.es_nuevo:
            l.addWidget(QLabel(tt("lbl_stock_inicial", "Stock inicial")))
            self.spin_inicial = QDoubleSpinBox(); self.spin_inicial.setRange(0, 999999); self.spin_inicial.setDecimals(2)
            l.addWidget(self.spin_inicial)

        l.addWidget(QLabel(tt("lbl_ubicacion", "Ubicación")))
        self.combo_estanteria = QComboBox(); self.combo_balda = QComboBox(); self.combo_seccion = QComboBox()
        l.addWidget(QLabel(tt("lbl_estanteria", "Estantería"))); l.addWidget(self.combo_estanteria)
        l.addWidget(QLabel(tt("lbl_balda", "Balda"))); l.addWidget(self.combo_balda)
        l.addWidget(QLabel(tt("lbl_seccion", "Sección"))); l.addWidget(self.combo_seccion)
        self._estructura = almacen.listar_estructura()
        self.combo_estanteria.addItem(tt("txt_sin_ubicacion", "— Sin ubicación —"), None)
        for est in self._estructura:
            self.combo_estanteria.addItem(est["nombre"], est["id"])
        self.combo_estanteria.currentIndexChanged.connect(self._actualizar_baldas)
        self.combo_balda.currentIndexChanged.connect(self._actualizar_secciones)
        self._actualizar_baldas()

        l.addWidget(QLabel(tt("lbl_foto_adjunta", "Foto adjunta")))
        self.lbl_preview = QLabel(tt("lbl_sin_foto", "Sin foto")); self.lbl_preview.setFixedSize(200, 150)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet(_estilo_zona_arrastre())
        self.lbl_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_preview.mousePressEvent = self._click_preview
        h_center = QHBoxLayout(); h_center.addWidget(self.lbl_preview); h_center.addStretch()
        l.addLayout(h_center)
        h_foto = QHBoxLayout()
        btn_cambiar = QPushButton(t("btn_cambiar_foto")); btn_cambiar.clicked.connect(self.seleccionar_foto)
        btn_borrar = QPushButton(t("btn_borrar_foto")); btn_borrar.clicked.connect(self.borrar_foto)
        h_foto.addWidget(btn_cambiar); h_foto.addWidget(btn_borrar)
        l.addLayout(h_foto)

        # Preselección de ubicación si estamos editando
        if material and material.get("seccion_id"):
            self._preseleccionar_ubicacion(material["seccion_id"])

        self._actualizar_preview_inicial()

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self._validar_aceptar); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def _actualizar_baldas(self):
        self.combo_balda.clear()
        est_id = self.combo_estanteria.currentData()
        est = next((e for e in self._estructura if e["id"] == est_id), None)
        if est:
            for balda in est["baldas"]:
                nombre = tt("txt_hueco_suelo_corto", "Hueco de suelo") if balda["numero"] == 0 else tt(
                    "txt_balda_num", "Balda {n}").format(n=almacen.texto_balda(balda["numero"], est.get("estilo_baldas", "numero")))
                self.combo_balda.addItem(nombre, balda["id"])
        self._actualizar_secciones()

    def _actualizar_secciones(self):
        self.combo_seccion.clear()
        est_id = self.combo_estanteria.currentData()
        balda_id = self.combo_balda.currentData()
        est = next((e for e in self._estructura if e["id"] == est_id), None)
        if est:
            balda = next((b for b in est["baldas"] if b["id"] == balda_id), None)
            if balda:
                # La sección es opcional: "Sin sección" ubica el material en la
                # balda (ver _seccion_destino). Las implícitas, creadas solas
                # para eso, no se ofrecen como una sección más.
                self.combo_seccion.addItem(tt("lbl_sin_seccion", "Sin sección"), None)
                for sec in balda["secciones"]:
                    if sec.get("implicita"): continue
                    self.combo_seccion.addItem(sec["nombre"], sec["id"])

    def _preseleccionar_ubicacion(self, seccion_id):
        for est in self._estructura:
            for balda in est["baldas"]:
                for sec in balda["secciones"]:
                    if sec["id"] == seccion_id:
                        idx_est = self.combo_estanteria.findData(est["id"])
                        if idx_est >= 0: self.combo_estanteria.setCurrentIndex(idx_est)
                        idx_balda = self.combo_balda.findData(balda["id"])
                        if idx_balda >= 0: self.combo_balda.setCurrentIndex(idx_balda)
                        idx_sec = self.combo_seccion.findData(sec["id"])
                        if idx_sec >= 0: self.combo_seccion.setCurrentIndex(idx_sec)
                        return

    def _actualizar_preview_inicial(self):
        if self.foto_nombre_existente:
            carpeta_fotos = self.parent().carpeta_fotos if self.parent() else ""
            ruta = os.path.join(carpeta_fotos, self.foto_nombre_existente)
            if os.path.exists(ruta):
                self.ruta_foto_seleccionada = ruta
                self._refrescar_preview()

    def _refrescar_preview(self):
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada):
            pix = QPixmap(self.ruta_foto_seleccionada)
            if not pix.isNull():
                self.lbl_preview.setPixmap(pix.scaled(self.lbl_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_preview.setStyleSheet("border: 2px solid #3daee9; background-color: #000;")
        else:
            self.lbl_preview.setPixmap(QPixmap()); self.lbl_preview.setText(tt("lbl_sin_foto", "Sin foto"))
            self.lbl_preview.setStyleSheet(_estilo_zona_arrastre())

    def seleccionar_foto(self):
        dlg = DialogoSelectorFoto(self)
        if dlg.exec() and dlg.selectedFiles():
            self.ruta_foto_seleccionada = dlg.selectedFiles()[0]
            self._refrescar_preview()

    def borrar_foto(self):
        self.ruta_foto_seleccionada = ""
        self.foto_nombre_existente = None
        self._refrescar_preview()

    def _click_preview(self, event):
        """Si ya hay foto la abre en grande (igual que en los trabajos); si no
        hay ninguna, abre directamente el selector de fichero."""
        if self.ruta_foto_seleccionada and os.path.exists(self.ruta_foto_seleccionada):
            VisorFoto(self.ruta_foto_seleccionada, self).exec()
        else:
            self.seleccionar_foto()

    def _validar_aceptar(self):
        if not self.campo_nombre.text().strip():
            QMessageBox.warning(self, tt("aviso", "Aviso"), tt("msg_nombre_material_obligatorio", "El nombre del material es obligatorio."))
            return
        self.accept()

    def get_data(self):
        return {
            "codigo": self.campo_codigo.text().strip(),
            "nombre": self.campo_nombre.text().strip(),
            "descripcion": self.campo_desc.toPlainText().strip(),
            "unidad": self.campo_unidad.text().strip(),
            "stock_minimo": self.spin_minimo.value(),
            "stock_inicial": self.spin_inicial.value() if self.es_nuevo else 0,
            "seccion_id": _seccion_destino(self.combo_seccion.currentData(), self.combo_balda.currentData()),
            "ruta_foto_seleccionada": self.ruta_foto_seleccionada,
            "foto_nombre_existente": self.foto_nombre_existente,
        }


class DialogoMovimientoStock(QDialog):
    """Registro rápido de una entrada o salida de stock para un material."""
    def __init__(self, parent=None, material=None, tipo="entrada"):
        super().__init__(parent)
        self.tipo = tipo
        titulo = tt("title_entrada_stock", "Entrada de stock") if tipo == "entrada" else tt("title_salida_stock", "Salida de stock")
        self.setWindowTitle(titulo)
        self.resize(380, 260)
        l = QVBoxLayout()
        info = QLabel(f"<b>{material['nombre']}</b><br>{tt('lbl_stock_actual', 'Stock actual')}: {material['stock_actual']} {material.get('unidad') or ''}")
        info.setWordWrap(True)
        l.addWidget(info)
        l.addWidget(QLabel(tt("lbl_cantidad", "Cantidad")))
        self.spin_cantidad = QDoubleSpinBox(); self.spin_cantidad.setRange(0.01, 999999); self.spin_cantidad.setDecimals(2); self.spin_cantidad.setValue(1)
        l.addWidget(self.spin_cantidad)
        l.addWidget(QLabel(tt("lbl_motivo", "Motivo (opcional)")))
        self.campo_motivo = QLineEdit()
        ph = tt("ph_motivo_entrada", "ej. Compra, devolución...") if tipo == "entrada" else tt("ph_motivo_salida", "ej. Usado en trabajo...")
        self.campo_motivo.setPlaceholderText(ph)
        l.addWidget(self.campo_motivo)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar")); b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def get_data(self):
        return self.spin_cantidad.value(), self.campo_motivo.text().strip()


class DialogoHistorialAlmacen(QDialog):
    """Todos los movimientos del almacén seguidos, del más reciente al más
    antiguo (entradas, salidas y traslados), sin tener que ir artículo por
    artículo. Con filtro por tipo y búsqueda por artículo, usuario o motivo.
    Doble clic en una fila: `al_elegir_material(material_id)`."""
    COLUMNAS = ("hdr_fecha", "hdr_codigo", "hdr_material", "hdr_movimiento", "hdr_cantidad", "hdr_detalle", "hdr_usuario")

    def __init__(self, parent=None, al_elegir_material=None):
        super().__init__(parent)
        self.al_elegir_material = al_elegir_material
        self.setWindowTitle(tt("title_historial_almacen", "Historial de movimientos del almacén"))
        self.resize(1100, 620)
        l = QVBoxLayout(self)
        filtros = QHBoxLayout()
        self.buscar = QLineEdit(); self.buscar.setPlaceholderText(tt("ph_buscar_movimientos", "Buscar artículo, usuario o motivo..."))
        self.buscar.textChanged.connect(self._filtrar)
        self.combo_tipo = QComboBox()
        for clave, defecto, tipo in (("filtro_todos", "Todos", None), ("txt_entradas", "Entradas", "entrada"),
                                     ("txt_salidas", "Salidas", "salida"), ("txt_traslados", "Traslados", "traslado")):
            self.combo_tipo.addItem(tt(clave, defecto), tipo)
        self.combo_tipo.currentIndexChanged.connect(self._filtrar)
        filtros.addWidget(self.buscar, 1); filtros.addWidget(QLabel(tt("lbl_tipo_movimiento", "Tipo") + ":")); filtros.addWidget(self.combo_tipo)
        l.addLayout(filtros)

        self.tabla = QTableWidget(0, len(self.COLUMNAS))
        self.tabla.setHorizontalHeaderLabels([tt(c, c) for c in self.COLUMNAS])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.itemDoubleClicked.connect(self._doble_clic)
        l.addWidget(self.tabla)

        pie = QHBoxLayout()
        self.lbl_total = QLabel(); pie.addWidget(self.lbl_total); pie.addStretch()
        btn_cerrar = QPushButton(t("btn_cerrar")); btn_cerrar.clicked.connect(self.accept); pie.addWidget(btn_cerrar)
        l.addLayout(pie)

        self.movimientos = almacen.listar_movimientos()
        self._filtrar()

    @staticmethod
    def _fecha(iso):
        """'2026-10-29 08:15:02' -> fecha corta del idioma activo + hora."""
        fecha, _, hora = (iso or "").partition(" ")
        return f"{idiomas.formato_fecha_localizada(fecha)} {hora[:5]}".strip()

    def _textos(self, mv):
        tipo = mv["tipo"]
        if tipo == "traslado":
            movimiento, cantidad, detalle = tt("mov_traslado", "🔀 Traslado"), "", mv.get("motivo") or ""
        else:
            movimiento = tt("btn_entrada_stock", "📥 Entrada") if tipo == "entrada" else tt("btn_salida_stock", "📤 Salida")
            cantidad = f"{'+' if tipo == 'entrada' else '−'}{mv['cantidad']:g}"
            detalle = traducir_motivo_movimiento(mv.get("motivo") or "")
        return [self._fecha(mv["fecha"]), mv.get("material_codigo") or "", mv.get("material_nombre") or "",
                movimiento, cantidad, detalle, mv.get("usuario_nombre") or ""]

    def _filtrar(self):
        tipo = self.combo_tipo.currentData()
        texto = self.buscar.text().strip().lower()
        filas = []
        for mv in self.movimientos:
            if tipo and mv["tipo"] != tipo:
                continue
            celdas = self._textos(mv)
            if texto and texto not in " ".join(celdas).lower():
                continue
            filas.append((mv, celdas))
        self.tabla.setRowCount(len(filas))
        colores = {"entrada": QColor("#27ae60"), "salida": QColor("#d35400")}
        for i, (mv, celdas) in enumerate(filas):
            for j, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                item.setData(Qt.ItemDataRole.UserRole, mv["material_id"])
                if texto and j in (2, 5):
                    item.setToolTip(texto)  # nombre o traslado largos, completos al pasar el ratón
                if j == 4 and mv["tipo"] in colores:
                    item.setForeground(colores[mv["tipo"]])
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabla.setItem(i, j, item)
        self.tabla.resizeColumnsToContents()
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        cab.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.lbl_total.setText(tt("msg_n_movimientos", "{n} movimientos").format(n=len(filas)))

    def _doble_clic(self, item):
        if self.al_elegir_material:
            self.al_elegir_material(item.data(Qt.ItemDataRole.UserRole))
            self.accept()


class DialogoExportarStock(QDialog):
    """Elige formato (PDF/CSV/Excel) y alcance (todo, una zona o una estantería)
    para exportar el stock de almacén."""
    def __init__(self, parent=None, zona_inicial=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_exportar_stock", "Exportar stock de almacén"))
        l = QVBoxLayout()

        g_formato = QGroupBox(tt("lbl_formato", "Formato"))
        h = QHBoxLayout(g_formato)
        self.rb_pdf = QRadioButton("PDF"); self.rb_csv = QRadioButton("CSV"); self.rb_excel = QRadioButton("Excel")
        self.rb_pdf.setChecked(True)
        for rb in (self.rb_pdf, self.rb_csv, self.rb_excel): h.addWidget(rb)
        l.addWidget(g_formato)

        g_alcance = QGroupBox(tt("lbl_que_exportar", "Qué exportar"))
        f = QFormLayout(g_alcance)
        self.combo_zona = QComboBox()
        self.combo_zona.addItem(tt("txt_todas_zonas", "Todas las zonas"), None)
        for zona in almacen.listar_zonas():
            self.combo_zona.addItem(zona["nombre"], zona["id"])
        idx = self.combo_zona.findData(zona_inicial)
        self.combo_zona.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_estanteria = QComboBox()
        self.combo_zona.currentIndexChanged.connect(self._cargar_estanterias)
        f.addRow(tt("lbl_zona", "Zona") + ":", self.combo_zona)
        f.addRow(tt("lbl_estanteria", "Estantería") + ":", self.combo_estanteria)
        l.addWidget(g_alcance)
        self._cargar_estanterias()

        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        b.button(QDialogButtonBox.StandardButton.Ok).setText(tt("btn_exportar", "Exportar"))
        b.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        b.accepted.connect(self.accept); b.rejected.connect(self.reject)
        l.addWidget(b); self.setLayout(l)

    def _cargar_estanterias(self):
        self.combo_estanteria.clear()
        self.combo_estanteria.addItem(tt("txt_todas_estanterias", "Todas las estanterías"), None)
        for est in almacen.listar_estructura(self.combo_zona.currentData()):
            self.combo_estanteria.addItem(est["nombre"], est["id"])

    def get_data(self):
        formato = "pdf" if self.rb_pdf.isChecked() else ("csv" if self.rb_csv.isChecked() else "xlsx")
        zona_id = self.combo_zona.currentData()
        est_id = self.combo_estanteria.currentData()
        if est_id is not None:
            ambito = self.combo_estanteria.currentText()
            if zona_id is not None:
                ambito = f"{self.combo_zona.currentText()} · {ambito}"
        elif zona_id is not None:
            ambito = self.combo_zona.currentText()
        else:
            ambito = None
        return formato, zona_id, est_id, ambito
