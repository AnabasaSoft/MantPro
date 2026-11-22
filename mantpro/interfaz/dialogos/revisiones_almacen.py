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

"""Herramientas → Historial de revisiones del almacén: quién hizo cada día la
revisión de los artículos que propone MantPro Stock (los 5 al azar), si los
revisó todos, y qué cantidad contó frente a la que decía el sistema."""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
                             QFileDialog, QMessageBox, QWidget, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ...idiomas import t
from ..comun import tt
from ...nucleo import informe_revisiones as inf, registro_cambios, usuarios
from ...nucleo import revisiones_almacen as rev


# Los textos, las filas y la exportación están en el núcleo (los comparte con MantPro Web)
VENTANA_AVISO_DIAS = inf.VENTANA_AVISO_DIAS
VENTANA_MOVILES_DIAS = inf.VENTANA_MOVILES_DIAS
texto_dias_sin_revision = inf.texto_dias_sin_revision
texto_avisos = inf.texto_avisos
texto_moviles = inf.texto_moviles
nombres_estado = inf.nombres_estado


COLORES_ESTADO = {
    rev.ESTADO_COMPLETA: QColor("#2e8b57"),
    rev.ESTADO_PARCIAL: QColor("#d98a00"),
    rev.ESTADO_SIN_EMPEZAR: QColor("#c0392b"),
}


class DialogoRevisionesAlmacen(QDialog):
    def __init__(self, parent=None, festivos=(), festivos_de=None, sede=None):
        """[festivos]: los de la empresa; [festivos_de]: función sede_id -> festivos de esa
        sede (si no se pasa, se usan [festivos] para todas). [sede]: la que sale elegida."""
        super().__init__(parent)
        from ...nucleo import almacenes, sedes
        self._festivos = set(festivos or ())
        self._festivos_de = festivos_de or (lambda _sede: self._festivos)
        self.setWindowTitle(tt("rev_titulo", "Historial de revisiones del almacén"))
        self.resize(1050, 680)
        self._revisiones = []
        l = QVBoxLayout(self)

        # --- filtros
        f = QHBoxLayout()
        self.combo_usu = QComboBox(); self.combo_usu.addItem(tt("filtro_todos", "Todos"), None)
        for uid, nombre in rev.usuarios_con_revisiones():
            self.combo_usu.addItem(nombre, uid)
        self.combo_periodo = QComboBox()
        for dias, texto in registro_cambios.textos_periodo():
            self.combo_periodo.addItem(texto, dias)
        self.combo_periodo.setCurrentIndex(1)
        self.combo_estado = QComboBox(); self.combo_estado.addItem(tt("filtro_todas", "Todas"), None)
        for clave, (_estados, texto) in inf.FILTROS_ESTADO.items():
            self.combo_estado.addItem(tt(texto, texto), clave)
        for etiqueta, widget in ((tt("aud_usuario", "Usuario"), self.combo_usu), (tt("aud_periodo", "Periodo"), self.combo_periodo),
                                 (tt("rev_col_estado", "Estado"), self.combo_estado)):
            f.addWidget(QLabel(etiqueta + ":")); f.addWidget(widget)
        f.addStretch()
        l.addLayout(f)
        # --- sede (con su interruptor de revisión) y almacén
        f2 = QHBoxLayout()
        self.combo_sede = QComboBox(); self.combo_sede.addItem(tt("filtro_todas", "Todas"), None)
        permitidas = sedes.permitidas()
        for s_ in sedes.listar():
            if permitidas is None or s_["id"] in permitidas:
                self.combo_sede.addItem(s_["nombre"], s_["id"])
        if sede is not None and self.combo_sede.findData(sede) >= 0:
            self.combo_sede.setCurrentIndex(self.combo_sede.findData(sede))
        self.chk_revision_sede = QCheckBox(tt("rev_chk_activa_sede", "Revisión del almacén activa en esta sede"))
        self.chk_revision_sede.setToolTip(tt("rev_tt_activa_sede", "Desactivada, los almacenes de la sede no piden revisión en MantPro Stock ni salen en los avisos."))
        self.combo_almacen = QComboBox()
        self.lbl_sede, self.lbl_almacen = QLabel(tt("alm_lbl_sede", "Sede") + ":"), QLabel(tt("lbl_almacen", "Almacén") + ":")
        for w in (self.lbl_sede, self.combo_sede, self.chk_revision_sede, self.lbl_almacen, self.combo_almacen):
            f2.addWidget(w)
        f2.addStretch()
        l.addLayout(f2)
        hay_sedes = sedes.hay_varias()
        for w in (self.lbl_sede, self.combo_sede):
            w.setVisible(hay_sedes)
        self._hay_almacenes = almacenes.hay_varios()
        for w in (self.lbl_almacen, self.combo_almacen):
            w.setVisible(self._hay_almacenes)
        self.lbl_resumen = QLabel(); self.lbl_resumen.setWordWrap(True)
        l.addWidget(self.lbl_resumen)
        self.lbl_aviso = QLabel(); self.lbl_aviso.setWordWrap(True)
        self.lbl_aviso.setStyleSheet("color: #e74c3c; font-weight: bold;")
        l.addWidget(self.lbl_aviso)
        moviles = texto_moviles()
        if moviles:
            lbl_moviles = QLabel(moviles); lbl_moviles.setWordWrap(True)
            l.addWidget(lbl_moviles)

        # --- revisiones y detalle de la seleccionada
        split = QSplitter(Qt.Orientation.Vertical)
        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels([tt("lbl_fecha", "Fecha"), tt("aud_usuario", "Usuario"),
                                              tt("rev_col_movil", "Móvil"), tt("rev_col_revisados", "Revisados"),
                                              tt("rev_col_diferencias", "Con diferencias"),
                                              tt("rev_col_actividad", "Última actividad"), tt("lbl_almacen", "Almacén"),
                                              tt("alm_lbl_sede", "Sede")])
        self._preparar_tabla(self.tabla, estirar=2)
        self._hay_sedes = hay_sedes
        self.tabla.setColumnHidden(6, not self._hay_almacenes)
        self.tabla.setColumnHidden(7, not hay_sedes)
        self.tabla.currentCellChanged.connect(lambda *_: self._mostrar_detalle())
        split.addWidget(self.tabla)

        abajo = QWidget(); la = QVBoxLayout(abajo); la.setContentsMargins(0, 0, 0, 0)
        self.lbl_detalle = QLabel(); self.lbl_detalle.setWordWrap(True)
        la.addWidget(self.lbl_detalle)
        self.tabla_lineas = QTableWidget(0, 8)
        self.tabla_lineas.setHorizontalHeaderLabels([tt("rev_col_articulo", "Artículo"), tt("lbl_ubicacion", "Ubicación"),
                                                     tt("rev_col_sistema", "En el sistema"), tt("rev_col_contado", "Contado"),
                                                     tt("rev_col_diferencia", "Diferencia"), tt("rev_col_estado", "Estado"),
                                                     tt("lbl_almacen", "Almacén"), tt("alm_lbl_sede", "Sede")])
        self._preparar_tabla(self.tabla_lineas, estirar=0)
        self.tabla_lineas.setColumnHidden(6, not self._hay_almacenes)
        self.tabla_lineas.setColumnHidden(7, not hay_sedes)
        la.addWidget(self.tabla_lineas)
        split.addWidget(abajo)
        split.setSizes([360, 260])
        l.addWidget(split, 1)

        # --- botones
        b = QHBoxLayout()
        self.lbl_total = QLabel()
        b.addWidget(self.lbl_total)
        b.addStretch()
        exportar = QPushButton(tt("aud_exportar", "📤 Exportar (Excel o CSV)")); exportar.clicked.connect(self._exportar)
        cerrar = QPushButton(t("cerrar")); cerrar.clicked.connect(self.accept)
        b.addWidget(exportar); b.addWidget(cerrar)
        l.addLayout(b)

        for combo in (self.combo_usu, self.combo_periodo, self.combo_estado, self.combo_almacen):
            combo.currentIndexChanged.connect(self.recargar)
        self.combo_sede.currentIndexChanged.connect(lambda _i: self._al_cambiar_sede())
        self.chk_revision_sede.toggled.connect(self._cambiar_revision_sede)
        self._al_cambiar_sede()

    @staticmethod
    def _preparar_tabla(tabla, estirar):
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.setAlternatingRowColors(True)
        tabla.verticalHeader().setVisible(False)
        cab = tabla.horizontalHeader()
        for c in range(tabla.columnCount()):
            cab.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch if c == estirar else QHeaderView.ResizeMode.ResizeToContents)

    # ----------------------------------------------------------- datos
    def _sede(self):
        """La sede elegida o, con «Todas», las del usuario (None = todas)."""
        from ...nucleo import sedes
        elegida = self.combo_sede.currentData()
        return elegida if elegida is not None else sedes.permitidas()

    def _al_cambiar_sede(self):
        """Rellena los almacenes de la sede y pone su interruptor de revisión."""
        from ...nucleo import almacenes, sedes
        elegida = self.combo_sede.currentData()
        self.chk_revision_sede.blockSignals(True)
        self.chk_revision_sede.setChecked(sedes.revision_activa(elegida) if elegida is not None else True)
        self.chk_revision_sede.blockSignals(False)
        # Con varias sedes, el interruptor es de una sede concreta; con una sola, de la principal
        self.chk_revision_sede.setVisible(elegida is not None or not sedes.hay_varias())
        if elegida is None and not sedes.hay_varias():
            self.chk_revision_sede.blockSignals(True)
            self.chk_revision_sede.setChecked(sedes.revision_activa(None))
            self.chk_revision_sede.blockSignals(False)
        previo = self.combo_almacen.currentData()
        self.combo_almacen.blockSignals(True)
        self.combo_almacen.clear()
        self.combo_almacen.addItem(tt("filtro_todos", "Todos"), None)
        for a in almacenes.listar(self._sede()):
            self.combo_almacen.addItem(("🌐 " if a["comun"] else "") + a["nombre"], a["id"])
        if previo is not None and self.combo_almacen.findData(previo) >= 0:
            self.combo_almacen.setCurrentIndex(self.combo_almacen.findData(previo))
        self.combo_almacen.blockSignals(False)
        self.recargar()

    def _cambiar_revision_sede(self, activa):
        try:
            inf.fijar_revision_sede(usuarios.SESION_ACTUAL, self.combo_sede.currentData(), activa)
        except ValueError:
            QMessageBox.warning(self, t("title_error"), t("msg_solo_admin"))
        self.recargar()

    def _pintar_aviso(self):
        texto = texto_avisos(self._sede(), self._festivos_de, self.combo_almacen.currentData())
        self.lbl_aviso.setText(texto)
        self.lbl_aviso.setVisible(bool(texto))

    def _filtros(self):
        return inf.filtros(self.combo_periodo.currentData(), self.combo_usu.currentData(),
                           self.combo_estado.currentData(), self._sede(), self.combo_almacen.currentData())

    def recargar(self):
        self._revisiones, self._cuentas = inf.filas(self._filtros())
        self._pintar_aviso()
        self._pintar()

    def _pintar(self):
        self.tabla.setRowCount(len(self._revisiones))
        for fila, r in enumerate(self._revisiones):
            celdas = [r["fecha"], r["usuario"], r["movil"], r["revisados"], r["ajustados"], r["actividad"],
                      r["almacen"], r["sede"]]
            for col, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                if col == 3:
                    item.setForeground(COLORES_ESTADO[r["estado"]])
                self.tabla.setItem(fila, col, item)
        self.lbl_total.setText(tt("rev_total", "{n} revisiones").format(n=len(self._revisiones)))
        self.lbl_resumen.setText(inf.texto_resumen(self._cuentas))
        if self._revisiones:
            self.tabla.selectRow(0)
        self._mostrar_detalle()

    def _mostrar_detalle(self):
        fila = self.tabla.currentRow()
        r = self._revisiones[fila] if 0 <= fila < len(self._revisiones) else None
        self.tabla_lineas.setRowCount(0)
        if r is None:
            self.lbl_detalle.setText(tt("rev_sin_registros", "No hay revisiones con estos filtros."))
            self.tabla_lineas.setVisible(False)
            return
        self.tabla_lineas.setVisible(True)
        self.lbl_detalle.setText(f"<b>{r['fecha']}</b> · {r['usuario']} · {r['movil']} · {r['revisados_n']}")
        lineas = inf.lineas(r["id"])
        self.tabla_lineas.setRowCount(len(lineas))
        for i, ln in enumerate(lineas):
            celdas = [ln["articulo"], ln["ubicacion"], ln["sistema"], ln["contado"], ln["diferencia"], ln["estado"],
                      ln["almacen"], ln["sede"]]
            for col, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                if col == 4 and ln["con_diferencia"]:
                    item.setForeground(QColor("#c0392b"))
                if col == 5:
                    item.setForeground(COLORES_ESTADO[rev.ESTADO_COMPLETA if ln["revisado"] else rev.ESTADO_SIN_EMPEZAR])
                self.tabla_lineas.setItem(i, col, item)

    # ----------------------------------------------------------- exportar
    _cabecera_export = staticmethod(inf.cabecera_exportar)

    def _filas_export(self):
        return inf.filas_exportar(self._filtros())

    def _exportar(self):
        ruta, filtro = QFileDialog.getSaveFileName(self, tt("aud_exportar", "📤 Exportar (Excel o CSV)"),
                                                   inf.nombre_fichero("xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        if not ruta:
            return
        try:
            formato = "csv" if ruta.lower().endswith(".csv") or "CSV" in filtro else "xlsx"
            if not ruta.lower().endswith("." + formato):
                ruta = (os.path.splitext(ruta)[0] if formato == "csv" else ruta) + "." + formato
            n = inf.exportar(ruta, formato, self._filtros())
            QMessageBox.information(self, self.windowTitle(),
                                    tt("aud_exportado", "Exportados {n} registros a:\n{ruta}").format(n=n, ruta=ruta))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))
