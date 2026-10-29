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

"""Pestaña «Máquinas»: árbol, fotos e indicadores."""

import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
                             QHeaderView, QComboBox, QTreeWidget)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QColor, QPixmap

from ... import idiomas
from ...idiomas import t
from ..comun import _estilo_zona_arrastre, abrir_url_externa, tt
from ..dialogos.maquinas import DialogoEditarMaquina
from ..widgets.fotos import VisorFoto
from ..widgets.graficos import GraficoCircularTrabajos
from ..widgets.ordenables import _ItemArbolOrdenable
from ...nucleo import etiquetas, maquinas

class PestanaMaquinas:
    """Pestaña «Máquinas»: árbol, fotos e indicadores.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    # ==========================================
    # MÁQUINAS
    # ==========================================
    def init_maquinas_tab(self):
        l = QVBoxLayout()
        h_tools = QHBoxLayout()
        b_nueva = QPushButton(tt("btn_nueva_maquina", "➕ Nueva máquina")); b_nueva.clicked.connect(self._maquina_nueva)
        b_nueva_sub = QPushButton(tt("btn_nueva_submaquina", "➕ Nueva submáquina")); b_nueva_sub.clicked.connect(self._maquina_nueva_sub)
        b_editar = QPushButton(tt("btn_editar_maquina", "✏️ Editar")); b_editar.clicked.connect(self._maquina_editar)
        b_eliminar = QPushButton(tt("btn_eliminar_maquina", "🗑️ Eliminar")); b_eliminar.setStyleSheet("background-color:#c0392b; color: white;"); b_eliminar.clicked.connect(self._maquina_eliminar)
        b_expandir = QPushButton(tt("btn_expandir_todo", "⬇️ Expandir todo")); b_expandir.clicked.connect(self._maquinas_expandir_todo)
        b_contraer = QPushButton(tt("btn_contraer_todo", "⬆️ Contraer todo"))
        b_qr = QPushButton(tt("btn_etiquetas_qr", "🏷️ Etiquetas QR")); b_qr.clicked.connect(self._maquinas_etiquetas_qr)
        b_qr.setToolTip(tt("tt_etiquetas_qr", "PDF con etiquetas QR para pegar en las máquinas: al escanearlas con MantPro se abre su ficha."))
        for b in [b_nueva, b_nueva_sub, b_editar, b_eliminar, b_expandir, b_contraer, b_qr]: h_tools.addWidget(b)
        h_tools.addStretch()
        l.addLayout(h_tools)

        h_cuerpo = QHBoxLayout()
        self.arbol_maquinas = QTreeWidget()
        self.arbol_maquinas.setColumnCount(4)
        self.arbol_maquinas.setHeaderLabels([tt("hdr_maquina", "Máquina"), tt("hdr_trabajos", "Trabajos"), tt("hdr_fecha_maquina", "Fecha"), tt("hdr_zona", "Zona")])
        self.arbol_maquinas.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.arbol_maquinas.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.arbol_maquinas.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.arbol_maquinas.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.arbol_maquinas.setSortingEnabled(True)
        self.arbol_maquinas.itemExpanded.connect(self._maquina_item_expandido)
        self.arbol_maquinas.itemDoubleClicked.connect(self._maquina_item_doble_click)
        self.arbol_maquinas.currentItemChanged.connect(self._maquina_mostrar_foto_seleccionada)
        h_cuerpo.addWidget(self.arbol_maquinas, 65)
        b_contraer.clicked.connect(self.arbol_maquinas.collapseAll)

        v_foto = QVBoxLayout()
        v_foto.addWidget(QLabel(tt("lbl_foto_maquina", "Foto de la máquina")))
        self.lbl_foto_maquina = QLabel(tt("lbl_sin_foto", "Sin foto"))
        self.lbl_foto_maquina.setMinimumSize(220, 220)
        self.lbl_foto_maquina.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto_maquina.setStyleSheet(_estilo_zona_arrastre())
        self.lbl_foto_maquina.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_foto_maquina.mousePressEvent = self._maquina_ver_foto_grande
        v_foto.addWidget(self.lbl_foto_maquina)

        self.lbl_indicadores_maquina = QLabel("")
        self.lbl_indicadores_maquina.setWordWrap(True)
        self.lbl_indicadores_maquina.setStyleSheet("padding: 6px; font-size: 12px;")
        v_foto.addWidget(self.lbl_indicadores_maquina)

        v_foto.addStretch(1)  # empuja el bloque de la gráfica hacia abajo
        v_foto.addWidget(QLabel(tt("lbl_grafico_trabajos_maquina", "Trabajos por máquina")))

        h_grafico = QHBoxLayout()
        self.grafico_trabajos_maquina = GraficoCircularTrabajos()
        h_grafico.addWidget(self.grafico_trabajos_maquina, 1)
        v_combo_anio = QVBoxLayout()
        v_combo_anio.addWidget(QLabel(tt("lbl_anio_grafico", "Año:")))
        self.combo_anio_grafico = QComboBox()
        self.combo_anio_grafico.currentIndexChanged.connect(self._actualizar_grafico_trabajos)
        v_combo_anio.addWidget(self.combo_anio_grafico)
        v_combo_anio.addWidget(QLabel(tt("lbl_zona_grafico", "Zona:")))
        self.combo_zona_grafico = QComboBox()
        self.combo_zona_grafico.currentIndexChanged.connect(self._actualizar_grafico_trabajos)
        v_combo_anio.addWidget(self.combo_zona_grafico)
        v_combo_anio.addStretch()
        h_grafico.addLayout(v_combo_anio)
        v_foto.addLayout(h_grafico)

        v_foto.addStretch(1)
        h_cuerpo.addLayout(v_foto, 35)

        l.addLayout(h_cuerpo)
        self.tab_maquinas.setLayout(l)
        self.refrescar_arbol_maquinas()

    def _maquina_mostrar_foto_seleccionada(self, *args):
        item = self.arbol_maquinas.currentItem()
        datos = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        ruta = None
        if datos and datos.get("tipo") == "maquina":
            maquina = maquinas.obtener_maquina(datos["id"])
            if maquina and maquina.get("foto"):
                ruta = os.path.join(self.carpeta_fotos, maquina["foto"])
        if ruta and os.path.exists(ruta):
            pix = QPixmap(ruta)
            if not pix.isNull():
                self.lbl_foto_maquina.setPixmap(pix.scaled(self.lbl_foto_maquina.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.lbl_foto_maquina.setStyleSheet("border: 2px solid #3daee9; background-color: #000;")
            else:
                self.lbl_foto_maquina.setPixmap(QPixmap()); self.lbl_foto_maquina.setText(tt("lbl_sin_foto", "Sin foto"))
                self.lbl_foto_maquina.setStyleSheet(_estilo_zona_arrastre())
        else:
            self.lbl_foto_maquina.setPixmap(QPixmap()); self.lbl_foto_maquina.setText(tt("lbl_sin_foto", "Sin foto"))
            self.lbl_foto_maquina.setStyleSheet(_estilo_zona_arrastre())
        self._actualizar_indicadores_maquina(datos["id"] if datos and datos.get("tipo") == "maquina" else None)

    def _maquina_ver_foto_grande(self, event):
        """Abre en grande la foto de la máquina seleccionada en el árbol,
        igual que al pulsar una foto de un trabajo."""
        item = self.arbol_maquinas.currentItem()
        datos = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not datos or datos.get("tipo") != "maquina": return
        maquina = maquinas.obtener_maquina(datos["id"])
        if not maquina or not maquina.get("foto"): return
        ruta = os.path.join(self.carpeta_fotos, maquina["foto"])
        if os.path.exists(ruta): VisorFoto(ruta, self).exec()

    def _actualizar_indicadores_maquina(self, id_maquina):
        """Muestra MTBF/MTTR de la máquina seleccionada (y sus submáquinas)."""
        if not hasattr(self, 'lbl_indicadores_maquina'):
            return
        if id_maquina is None:
            self.lbl_indicadores_maquina.setText("")
            return
        ind = maquinas.indicadores_fiabilidad(id_maquina)
        if ind["num_averias"] == 0 or ind["mtbf_dias"] is None:
            self.lbl_indicadores_maquina.setText(
                f"<b>{tt('lbl_indicadores_fiabilidad', 'Indicadores de fiabilidad')}</b><br>"
                f"{tt('lbl_num_averias', 'Averías registradas')}: {ind['num_averias']}<br>"
                f"<i>{tt('msg_sin_datos_fiabilidad', 'Aún no hay averías suficientes para calcular indicadores.')}</i>"
            )
            return
        mtbf_txt = tt("fmt_dias", "{n:.1f} días").format(n=ind["mtbf_dias"])
        partes = [
            f"<b>{tt('lbl_indicadores_fiabilidad', 'Indicadores de fiabilidad')}</b>",
            f"{tt('lbl_num_averias', 'Averías registradas')}: {ind['num_averias']}",
            f"{tt('lbl_mtbf', 'MTBF (tiempo medio entre averías)')}: {mtbf_txt}",
        ]
        if ind["mttr_horas"] is not None:
            mttr_txt = tt("fmt_horas", "{n:.1f} horas").format(n=ind["mttr_horas"])
            partes.append(f"{tt('lbl_mttr', 'MTTR (tiempo medio de reparación)')}: {mttr_txt}")
        self.lbl_indicadores_maquina.setText("<br>".join(partes))

    def refrescar_arbol_maquinas(self):
        item_actual = self.arbol_maquinas.currentItem()
        id_seleccionado = item_actual.data(0, Qt.ItemDataRole.UserRole)["id"] if item_actual else None
        self.arbol_maquinas.setSortingEnabled(False)
        self.arbol_maquinas.clear()
        todas = maquinas.listar_maquinas()
        por_padre = {}
        for m in todas:
            por_padre.setdefault(m["padre_id"], []).append(m)
        for m in por_padre.get(None, []):
            item = self._crear_nodo_maquina(m)
            self.arbol_maquinas.addTopLevelItem(item)
            if id_seleccionado == m["id"]:
                self.arbol_maquinas.setCurrentItem(item)
        self.arbol_maquinas.setSortingEnabled(True)

        self._refrescar_combo_anio_grafico()
        self._refrescar_combo_zona_grafico()
        self._actualizar_grafico_trabajos()

    def _colores_arbol_maquinas(self):
        """Colores para diferenciar máquinas, años y zonas en el árbol, acordes al tema activo."""
        oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
        col_maquina = QColor("#5fa8e8") if oscuro else QColor("#0d3862")
        col_anio = QColor("#e0b34d") if oscuro else QColor("#8a6210")
        col_zona = QColor("#c98be0") if oscuro else QColor("#6a2d8a")
        return col_maquina, col_anio, col_zona

    def _crear_nodo_maquina(self, maquina):
        total = maquinas.contar_trabajos(maquina["id"])
        item = _ItemArbolOrdenable([maquina["nombre"], str(total), "", maquina.get("zona_nombre") or ""])
        item.setData(1, Qt.ItemDataRole.UserRole + 1, total)
        item.setData(0, Qt.ItemDataRole.UserRole, {"tipo": "maquina", "id": maquina["id"], "cargado": False})
        col_maquina, _, col_zona = self._colores_arbol_maquinas()
        item.setForeground(0, col_maquina)
        item.setForeground(3, col_zona)
        item.addChild(_ItemArbolOrdenable([""]))  # hijo ficticio para mostrar la flecha de expandir
        return item

    def _maquina_item_expandido(self, item):
        datos = item.data(0, Qt.ItemDataRole.UserRole)
        if not datos or datos.get("cargado"):
            return
        item.takeChildren()
        tipo = datos["tipo"]
        if tipo == "maquina":
            por_padre = {}
            for m in maquinas.listar_maquinas():
                por_padre.setdefault(m["padre_id"], []).append(m)
            for sub in por_padre.get(datos["id"], []):
                item.addChild(self._crear_nodo_maquina(sub))
            _, col_anio, _ = self._colores_arbol_maquinas()
            for anio, cnt in maquinas.anios_de_maquina(datos["id"]):
                nodo = _ItemArbolOrdenable([anio, str(cnt), ""])
                nodo.setData(1, Qt.ItemDataRole.UserRole + 1, cnt)
                nodo.setData(0, Qt.ItemDataRole.UserRole, {"tipo": "anio", "id": datos["id"], "anio": anio, "cargado": False})
                nodo.setForeground(0, col_anio)
                nodo.addChild(_ItemArbolOrdenable([""]))
                item.addChild(nodo)
        elif tipo == "anio":
            for trabajo in maquinas.trabajos_de_maquina_anio(datos["id"], datos["anio"]):
                resumen = trabajo["descripcion"].splitlines()[0] if trabajo["descripcion"] else ""
                fecha_fmt = self._formatear_fecha_corta(trabajo["fecha"])
                nodo = _ItemArbolOrdenable([resumen, "", fecha_fmt])
                nodo.setData(2, Qt.ItemDataRole.UserRole + 1, trabajo["fecha"])
                nodo.setData(0, Qt.ItemDataRole.UserRole, {"tipo": "trabajo", "id": trabajo["id"], "cargado": True})
                item.addChild(nodo)
        datos["cargado"] = True
        item.setData(0, Qt.ItemDataRole.UserRole, datos)

    def _refrescar_combo_anio_grafico(self):
        """Rellena el desplegable de años del gráfico, conservando la selección actual si sigue existiendo."""
        anio_actual = self.combo_anio_grafico.currentData()
        self.combo_anio_grafico.blockSignals(True)
        self.combo_anio_grafico.clear()
        self.combo_anio_grafico.addItem(tt("opcion_todos_los_anios", "TODOS"), None)
        for anio in maquinas.anios_disponibles():
            self.combo_anio_grafico.addItem(anio, anio)
        indice = self.combo_anio_grafico.findData(anio_actual)
        self.combo_anio_grafico.setCurrentIndex(indice if indice >= 0 else 0)
        self.combo_anio_grafico.blockSignals(False)

    def _refrescar_combo_zona_grafico(self):
        """Rellena el desplegable de zonas del gráfico, conservando la selección actual si sigue existiendo."""
        zona_actual = self.combo_zona_grafico.currentData()
        self.combo_zona_grafico.blockSignals(True)
        self.combo_zona_grafico.clear()
        self.combo_zona_grafico.addItem(tt("opcion_todas_las_zonas", "TODAS"), None)
        for z in maquinas.zonas_disponibles():
            self.combo_zona_grafico.addItem(z["nombre"], z["id"])
        indice = self.combo_zona_grafico.findData(zona_actual)
        self.combo_zona_grafico.setCurrentIndex(indice if indice >= 0 else 0)
        self.combo_zona_grafico.blockSignals(False)

    def _actualizar_grafico_trabajos(self):
        """Recalcula el gráfico circular de trabajos por máquina según el año y la zona elegidos
        en los desplegables, sumando en cada máquina de nivel superior los trabajos de sus submáquinas."""
        anio = self.combo_anio_grafico.currentData()
        zona_id = self.combo_zona_grafico.currentData()
        top_level = [m for m in maquinas.listar_maquinas() if m["padre_id"] is None]
        if zona_id is not None:
            top_level = [m for m in top_level if m["zona_id"] == zona_id]

        def total_trabajos(id_maquina):
            ids = maquinas.descendientes_ids(id_maquina)
            if anio is None:
                return sum(maquinas.contar_trabajos(i) for i in ids)
            return sum(maquinas.contar_trabajos_anio(i, anio) for i in ids)

        datos_grafico = sorted(
            ((m["nombre"], total_trabajos(m["id"])) for m in top_level),
            key=lambda par: par[1], reverse=True,
        )
        self.grafico_trabajos_maquina.establecer_datos(datos_grafico)

    def _formatear_fecha_corta(self, fecha_iso):
        return idiomas.formato_fecha_localizada(fecha_iso)

    def _maquinas_expandir_todo(self):
        """Expande todas las máquinas, años y trabajos, cargando bajo demanda
        (vía _maquina_item_expandido) los niveles que aún no se hayan abierto."""
        def expandir_recursivo(item):
            self.arbol_maquinas.expandItem(item)
            for i in range(item.childCount()):
                expandir_recursivo(item.child(i))
        for i in range(self.arbol_maquinas.topLevelItemCount()):
            expandir_recursivo(self.arbol_maquinas.topLevelItem(i))

    def _maquina_item_doble_click(self, item, columna):
        datos = item.data(0, Qt.ItemDataRole.UserRole)
        if datos and datos.get("tipo") == "trabajo":
            self.proc_edit(datos["id"])
        elif datos and datos.get("tipo") == "maquina":
            self._maquina_editar()

    def _guardar_foto_maquina(self, ruta_origen):
        if not ruta_origen: return None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nuevo = f"maquina_{ts}{os.path.splitext(ruta_origen)[1]}"
        destino = os.path.join(self.carpeta_fotos, nuevo)
        try:
            shutil.copy2(ruta_origen, destino)
            return nuevo
        except Exception:
            return None

    def _resolver_foto_maquina(self, datos):
        if not datos["ruta_foto_seleccionada"]:
            return None
        if os.path.dirname(os.path.abspath(datos["ruta_foto_seleccionada"])) == os.path.abspath(self.carpeta_fotos):
            return os.path.basename(datos["ruta_foto_seleccionada"])
        return self._guardar_foto_maquina(datos["ruta_foto_seleccionada"])

    def _maquina_nueva(self):
        dlg = DialogoEditarMaquina(self)
        if dlg.exec():
            datos = dlg.get_data()
            foto = self._resolver_foto_maquina(datos)
            maquinas.agregar_maquina(datos["nombre"], datos["padre_id"], datos["notas"], foto, datos["zona_id"])
            self.refrescar_arbol_maquinas()

    def _maquina_nueva_sub(self):
        item = self.arbol_maquinas.currentItem()
        datos_item = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not datos_item or datos_item.get("tipo") != "maquina":
            QMessageBox.information(self, t("aviso"), tt("msg_selecciona_maquina_padre", "Selecciona primero la máquina superior."))
            return
        dlg = DialogoEditarMaquina(self, padre_sugerido=datos_item["id"])
        if dlg.exec():
            datos = dlg.get_data()
            foto = self._resolver_foto_maquina(datos)
            maquinas.agregar_maquina(datos["nombre"], datos["padre_id"], datos["notas"], foto, datos["zona_id"])
            self.refrescar_arbol_maquinas()

    def _maquina_editar(self):
        item = self.arbol_maquinas.currentItem()
        datos_item = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not datos_item or datos_item.get("tipo") != "maquina":
            QMessageBox.information(self, t("aviso"), tt("msg_selecciona_maquina", "Selecciona primero una máquina."))
            return
        maquina = maquinas.obtener_maquina(datos_item["id"])
        excluir = set(maquinas.descendientes_ids(datos_item["id"]))
        dlg = DialogoEditarMaquina(self, maquina=maquina, excluir_ids=excluir)
        if dlg.exec():
            datos = dlg.get_data()
            foto = self._resolver_foto_maquina(datos)
            maquinas.actualizar_maquina(datos_item["id"], datos["nombre"], datos["padre_id"], datos["notas"], foto, datos["zona_id"])
            self.refrescar_arbol_maquinas()
            self._maquina_mostrar_foto_seleccionada()

    def _maquinas_etiquetas_qr(self):
        """PDF con etiquetas QR (70 × 37 mm, 24 por folio A4) de la máquina
        seleccionada, de ella y sus submáquinas, o de todas."""
        item = self.arbol_maquinas.currentItem()
        datos_item = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        seleccionada = datos_item["id"] if datos_item and datos_item.get("tipo") == "maquina" else None
        msg = QMessageBox(self)
        msg.setWindowTitle(tt("title_etiquetas_qr", "Etiquetas QR"))
        msg.setText(tt("msg_etiquetas_qr", "¿De qué máquinas quieres las etiquetas?\n\nSe generan en un PDF de folios A4 con 24 etiquetas de 70 × 37 mm (hojas adhesivas tipo Apli 1274 / Avery 3474, o folio normal para recortar)."))
        b_una = b_rama = None
        if seleccionada is not None:
            b_una = msg.addButton(tt("btn_qr_seleccionada", "Solo la seleccionada"), QMessageBox.ButtonRole.AcceptRole)
            b_rama = msg.addButton(tt("btn_qr_con_submaquinas", "La seleccionada y sus submáquinas"), QMessageBox.ButtonRole.AcceptRole)
        b_todas = msg.addButton(tt("btn_qr_todas", "Todas las máquinas"), QMessageBox.ButtonRole.AcceptRole)
        msg.addButton(t("btn_cancelar"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        pulsado = msg.clickedButton()
        rutas = maquinas.mapa_rutas_completas()
        if pulsado is b_una and b_una is not None:
            ids = [seleccionada]
        elif pulsado is b_rama and b_rama is not None:
            ids = [seleccionada] + sorted(maquinas.descendientes_ids(seleccionada), key=lambda i: rutas.get(i, "").lower())
        elif pulsado is b_todas:
            ids = sorted(rutas, key=lambda i: rutas[i].lower())
        else:
            return
        if not ids:
            return
        nombre = tt("nombre_pdf_etiquetas", "etiquetas_qr_maquinas") + ".pdf"
        ruta = self.guardar_archivo_dialogo(tt("title_etiquetas_qr", "Etiquetas QR"), nombre, "PDF (*.pdf)")
        if not ruta:
            return
        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"
        try:
            n = etiquetas.generar_pdf(ruta, ids)
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))
            return
        abrir_url_externa("file://" + os.path.abspath(ruta))
        QMessageBox.information(self, tt("title_etiquetas_qr", "Etiquetas QR"),
                                tt("msg_etiquetas_generadas", "{n} etiquetas guardadas en:\n{ruta}").format(n=n, ruta=ruta))

    def _maquina_eliminar(self):
        item = self.arbol_maquinas.currentItem()
        datos_item = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not datos_item or datos_item.get("tipo") != "maquina":
            QMessageBox.information(self, t("aviso"), tt("msg_selecciona_maquina", "Selecciona primero una máquina."))
            return
        if QMessageBox.question(self, t("aviso"),
                tt("msg_confirmar_eliminar_maquina", "¿Eliminar esta máquina y sus submáquinas?\nLos trabajos ya registrados no se borrarán, quedarán sin máquina asignada.")
                ) == QMessageBox.StandardButton.Yes:
            maquinas.borrar_maquina(datos_item["id"])
            self.refrescar_arbol_maquinas()
