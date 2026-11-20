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

"""Pestañas «Historial» y «Buscador»: consulta, edición, borrado y reasignación de trabajos."""

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QDateEdit, QMessageBox, QTableWidget, QTableWidgetItem,
                             QDialog, QDialogButtonBox, QAbstractItemView, QComboBox, QCheckBox,
                             QProgressDialog, QMenu, QTreeWidget, QTreeWidgetItem, QSplitter)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QIcon, QColor, QPixmap

from ...idiomas import t
from ..comun import _estilo_check_etiqueta, traducir_tags_bd, tt
from ..dialogos.trabajos import EditDialog
from ...nucleo import usuarios, checklists, consumos, mano_obra, historial, trabajos
from ..dialogos.checklists import DialogoRellenarChecklist, resumen_texto, texto_tiempo_export

# Colores de las filas por tipo (historial.clase): ((fondo, letra) en tema oscuro, (fondo, letra) en claro)
COLORES_FILA = {"averia": (("#4a2424", "#ffffff"), ("#f2b8bd", "#58151c")),
                "preventivo": (("#213c21", "#ffffff"), ("#a3d9ac", "#1e4620")),
                "electrico": (("#555", "#ffffff"), ("#e0e0e0", "#333333")),
                "mecanico": (("#5a4a2d", "#ffffff"), ("#fff3cd", "#5c4813"))}


class PestanaHistorial:
    """Pestañas «Historial» y «Buscador»: consulta, edición, borrado y reasignación de trabajos.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def _hay_foto_disponible(self, desc):
        # La foto de ANTES o, si no existe físicamente, la de DESPUÉS (lo decide el núcleo, igual que en MantPro Web)
        return historial.hay_foto(desc, self.carpeta_fotos)

    def fill_t(self, table, data):
        table.setRowCount(len(data))
        listas = checklists.resultados_de([f[0] for f in data])
        usados = consumos.materiales_de_trabajos([f[0] for f in data])
        tiempos = mano_obra.tiempos_de([f[0] for f in data])
        moneda = consumos.moneda()
        pm_foto = QPixmap(16, 16); pm_foto.fill(QColor("#3daee9")); icon_foto = QIcon(pm_foto)
        pm_vacio = QPixmap(16, 16); pm_vacio.fill(Qt.GlobalColor.transparent); icon_vacio = QIcon(pm_vacio)

        for r, fila in enumerate(data):
            id_t, fecha, desc, tags = fila[0], fila[1], fila[2], fila[3]
            autor = fila[4] if len(fila) > 4 else ""
            if not autor: autor = usuarios.ETIQUETA_HISTORICO
            # LIMPIEZA VISUAL (FOTO Y REF)
            desc_limpia = historial.texto_visible(desc)

            desc_visual = desc_limpia.replace("\n", "  ➜  ")
            lista = listas.get(id_t)
            if lista:
                r_lista = checklists.recuento(lista["items"])
                desc_visual = ("☑️❌ " if r_lista["mal"] else "☑️ ") + desc_visual
                desc_limpia += f"\n\n☑️ {lista['plantilla']}: {resumen_texto(lista['items'])}"
            tiempo = tiempos.get(id_t)
            if tiempo:
                desc_visual = "⏱️ " + desc_visual
                desc_limpia += "\n\n⏱️ " + tt("lbl_tiempo_trabajado", "⏱️ Tiempo trabajado").replace("⏱️", "").strip() + \
                    ": " + texto_tiempo_export(tiempo, moneda)
            mats = usados.get(id_t)
            if mats:
                importe, sin_precio = consumos.coste(mats)
                desc_visual = "🔩 " + desc_visual
                desc_limpia += "\n\n🔩 " + tt("lbl_repuestos_usados", "🔩 Materiales usados").replace("🔩", "").strip() + ":\n" + "\n".join(
                    f"• {m['cantidad']:g} {m['unidad'] or ''} {m['nombre']}".replace("  ", " ") for m in mats)
                if usuarios.es_admin():
                    desc_limpia += f"\n{tt('lbl_coste_material', 'Coste de material')}: {consumos.formato_importe(importe, moneda)}" + \
                    (" *" if sin_precio else "")

            oscuro = self._tema_actual == "oscuro"
            color_bg = color_fg = None
            colores = COLORES_FILA.get(historial.clase(tags))      # el tipo de fila lo decide el núcleo (también la web)
            if colores:
                fondo, letra = colores[0 if oscuro else 1]
                color_bg, color_fg = QColor(fondo), QColor(letra)

            item_f = QTableWidgetItem(fecha); item_f.setData(Qt.ItemDataRole.UserRole, id_t)
            item_d = QTableWidgetItem(desc_visual); item_d.setToolTip(desc_limpia)

            if self._hay_foto_disponible(desc):
                item_d.setIcon(icon_foto)
                item_d.setToolTip(f"📸 CON FOTO(S) ADJUNTA(S)\n\n{desc_limpia}")
            else:
                item_d.setIcon(icon_vacio)

            item_t = QTableWidgetItem(traducir_tags_bd(tags))
            item_t.setData(Qt.ItemDataRole.UserRole, tags)
            item_u = QTableWidgetItem(autor)

            if color_bg:
                item_f.setBackground(color_bg); item_d.setBackground(color_bg)
                item_t.setBackground(color_bg); item_u.setBackground(color_bg)
                item_f.setForeground(color_fg); item_d.setForeground(color_fg)
                item_t.setForeground(color_fg); item_u.setForeground(color_fg)

            table.setItem(r, 0, item_f); table.setItem(r, 1, item_d); table.setItem(r, 2, item_t)
            if table.columnCount() > 3:
                table.setItem(r, 3, item_u)

    def search(self):
        texto = self.s_in.text().strip(); fecha = None
        if self.s_chk_date.isChecked(): fecha = self.s_date.date().toString("yyyy-MM-dd")
        resultados = self.db.buscar_tareas_avanzado(texto, fecha, sede=self.sede_filtro())
        self.fill_t(self.s_table, resultados)
        marcadas = (self.chk_s_urg, self.chk_s_elec, self.chk_s_mec, self.chk_s_prev)
        filtros_activos = [et[0] for et, chk in zip(historial.ETIQUETAS_BUSCADOR, marcadas) if chk.isChecked()]
        filas_visibles = 0
        for row in range(self.s_table.rowCount()):
            mostrar = historial.coincide_etiquetas(self.s_table.item(row, 2).text(), filtros_activos)
            self.s_table.setRowHidden(row, not mostrar)
            if mostrar: filas_visibles += 1
        self.statusBar().showMessage(t("msg_mostrando_resultados").format(n=filas_visibles), 3000)

    def refresh_history(self):
        datos = self.db.obtener_todas_cronologico(sede=self.sede_filtro())
        self.fill_t(self.h_table, datos)
        self.recargar_combo_historial()
        self.aplicar_filtros_historial()

        # Construir árbol de fechas dinámico
        self.tree_history.clear()


        meses = {"01":t("mes_01"), "02":t("mes_02"), "03":t("mes_03"), "04":t("mes_04"), "05":t("mes_05"), "06":t("mes_06"), "07":t("mes_07"), "08":t("mes_08"), "09":t("mes_09"), "10":t("mes_10"), "11":t("mes_11"), "12":t("mes_12")}

        item_todo = QTreeWidgetItem([t("lbl_todos_trabajos")])
        item_todo.setData(0, Qt.ItemDataRole.UserRole, "TODO")
        self.tree_history.addTopLevelItem(item_todo)

        for year, meses_anio in historial.arbol_fechas(datos):
            item_year = QTreeWidgetItem([f"📅 {year}"])
            item_year.setData(0, Qt.ItemDataRole.UserRole, year)
            self.tree_history.addTopLevelItem(item_year)

            for month in meses_anio:
                item_month = QTreeWidgetItem([meses.get(month, month)])
                item_month.setData(0, Qt.ItemDataRole.UserRole, f"{year}-{month}")
                item_year.addChild(item_month)

        self.tree_history.setCurrentItem(item_todo)

        # Desocultar todas las filas al refrescar la tabla por defecto
        for row in range(self.h_table.rowCount()):
            self.h_table.setRowHidden(row, False)

    def init_history_tab(self):
        l = QHBoxLayout() # Layout contenedor principal

        # Crear el separador arrastrable horizontal
        self.splitter_history = QSplitter(Qt.Orientation.Horizontal)

        # PANEL IZQUIERDO: Árbol de fechas
        left_widget = QWidget()
        left_panel = QVBoxLayout(left_widget)
        left_panel.setContentsMargins(0, 0, 0, 0)

        btn_layout = QHBoxLayout()
        btn_expand = QPushButton("🠇")
        btn_expand.setToolTip("Desplegar todas las ramas")
        btn_expand.setFixedWidth(35)
        btn_collapse = QPushButton("🠅")
        btn_collapse.setToolTip("Plegar todas las ramas")
        btn_collapse.setFixedWidth(35)

        btn_expand.clicked.connect(lambda: self.tree_history.expandAll())
        btn_collapse.clicked.connect(lambda: self.tree_history.collapseAll())

        btn_layout.addWidget(btn_expand)
        btn_layout.addWidget(btn_collapse)
        btn_layout.addStretch()  # Empuja los botones compactos a la izquierda
        left_panel.addLayout(btn_layout)

        self.tree_history = QTreeWidget()
        self.tree_history.setHeaderHidden(True)
        self.tree_history.itemClicked.connect(self.on_tree_history_clicked)
        left_panel.addWidget(self.tree_history)

        # PANEL DERECHO: Tabla
        right_widget = QWidget()
        right_panel = QVBoxLayout(right_widget)
        right_panel.setContentsMargins(0, 0, 0, 0)

        fila_usuario = QHBoxLayout()
        fila_usuario.addWidget(QLabel(tt("hdr_realizado_por", "Realizado por") + ":"))
        self.combo_filtro_historial = QComboBox()
        self.combo_filtro_historial.currentIndexChanged.connect(self.aplicar_filtros_historial)
        fila_usuario.addWidget(self.combo_filtro_historial, 1)

        fila_usuario.addWidget(QLabel(tt("hdr_tipo_historial", "Tipo") + ":"))
        self.combo_filtro_tipo_historial = QComboBox()
        self.combo_filtro_tipo_historial.addItem(tt("filtro_todos", "Todos"), "TODOS")
        self.combo_filtro_tipo_historial.addItem(tt("filtro_trabajos_averias", "Trabajos y averías"), "TRABAJOS")
        self.combo_filtro_tipo_historial.addItem(tt("filtro_avisos_preventivos", "Avisos preventivos"), "PREVENTIVOS")
        self.combo_filtro_tipo_historial.currentIndexChanged.connect(self.aplicar_filtros_historial)
        fila_usuario.addWidget(self.combo_filtro_tipo_historial, 1)

        right_panel.addLayout(fila_usuario)

        self.h_table = QTableWidget()
        self.configurar_deseleccion(self.h_table)
        self.setup_table(self.h_table)
        # La columna TAGS se sigue guardando y coloreando las filas, pero no se muestra
        self.h_table.setColumnHidden(2, True)
        # Selección múltiple (Ctrl+Click, Shift+Click) + menú contextual
        self.h_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.h_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.h_table.customContextMenuRequested.connect(self._menu_contextual_historial)
        self.h_table.cellDoubleClicked.connect(lambda r, c: self.edit_rec(self.h_table))
        right_panel.addWidget(self.h_table)

        bl = QHBoxLayout()
        bl.addWidget(QPushButton(t("btn_editar"), clicked=lambda: self.edit_rec(self.h_table)))
        bl.addWidget(QPushButton(t("btn_borrar_seleccionado"), clicked=lambda: self.del_rec(self.h_table)))
        right_panel.addLayout(bl)

        # Añadir paneles al splitter arrastrable
        self.splitter_history.addWidget(left_widget)
        self.splitter_history.addWidget(right_widget)

        # Proporción inicial orientativa (se ajusta al arrastrar con el ratón)
        self.splitter_history.setSizes([100,900])

        l.addWidget(self.splitter_history)
        self.tab_history.setLayout(l)

    def on_tree_history_clicked(self, item, column):
        self._filtro_fecha_historial = item.data(0, Qt.ItemDataRole.UserRole)
        self.aplicar_filtros_historial()

    def aplicar_filtros_historial(self, *_):
        """Combina el filtro de fecha (árbol), el de técnico (combo) y el de tipo (trabajos/averías vs. avisos preventivos)."""
        filtro_fecha = getattr(self, '_filtro_fecha_historial', "TODO") or "TODO"
        filtro_usuario = self.combo_filtro_historial.currentData() if hasattr(self, 'combo_filtro_historial') else "TODOS"
        filtro_tipo = self.combo_filtro_tipo_historial.currentData() if hasattr(self, 'combo_filtro_tipo_historial') else "TODOS"
        visibles = 0

        for row in range(self.h_table.rowCount()):
            item_fecha = self.h_table.item(row, 0)
            if not item_fecha: continue
            # El filtro de fecha puede ser "2026" (año) o "2026-07" (año-mes); los tres los aplica el núcleo
            item_usuario, item_tags = self.h_table.item(row, 3), self.h_table.item(row, 2)
            fila = (None, item_fecha.text(), None, item_tags.data(Qt.ItemDataRole.UserRole) if item_tags else "",
                    item_usuario.text() if item_usuario else "")
            mostrar = historial.coincide(fila, filtro_fecha, filtro_usuario, filtro_tipo)

            self.h_table.setRowHidden(row, not mostrar)
            if mostrar: visibles += 1

        if filtro_usuario not in (None, "TODOS") or filtro_tipo not in (None, "TODOS"):
            self.statusBar().showMessage(t("msg_mostrando_resultados").format(n=visibles), 3000)

    def recargar_combo_historial(self):
        """Rellena el combo con los autores que aparecen realmente en el histórico."""
        if not hasattr(self, 'combo_filtro_historial'): return
        anterior = self.combo_filtro_historial.currentData()
        try:
            nombres = historial.tecnicos(self.db)
        except Exception:
            nombres = []
        self.combo_filtro_historial.blockSignals(True)
        self.combo_filtro_historial.clear()
        self.combo_filtro_historial.addItem(tt("filtro_todos", "Todos"), "TODOS")
        for n in sorted(nombres):
            self.combo_filtro_historial.addItem(n, n)
        idx = self.combo_filtro_historial.findData(anterior)
        self.combo_filtro_historial.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_filtro_historial.blockSignals(False)

    def init_search_tab(self):
        l = QVBoxLayout(); sl = QHBoxLayout()
        self.s_in = QLineEdit(); self.s_in.setPlaceholderText(t("ph_buscar_texto")); self.s_in.textChanged.connect(self.search); sl.addWidget(self.s_in)
        self.s_chk_date = QCheckBox("📅 Fecha:"); self.s_chk_date.toggled.connect(lambda: self.s_date.setEnabled(self.s_chk_date.isChecked())); self.s_chk_date.toggled.connect(self.search); sl.addWidget(self.s_chk_date)
        self.s_date = QDateEdit(); self.s_date.setCalendarPopup(True); self.s_date.setDate(QDate.currentDate()); self.s_date.setDisplayFormat("yyyy-MM-dd"); self.s_date.setEnabled(False); self.s_date.dateChanged.connect(self.search); sl.addWidget(self.s_date); l.addLayout(sl)
        fl = QHBoxLayout(); fl.setSpacing(20)
        self.chk_s_urg = QCheckBox(f"🚨 {t('tag_urgente')}"); self.chk_s_elec = QCheckBox(f"⚡ {t('tag_electrico')}"); self.chk_s_mec = QCheckBox(f"⚙️ {t('tag_mecanico')}"); self.chk_s_prev = QCheckBox(f"🛡️ {t('tag_preventivo')}")
        for chk in [self.chk_s_urg, self.chk_s_elec, self.chk_s_mec, self.chk_s_prev]: chk.setStyleSheet(_estilo_check_etiqueta()); chk.toggled.connect(self.search); fl.addWidget(chk)
        fl.addStretch(); l.addLayout(fl)
        self.s_table = QTableWidget(); self.setup_table(self.s_table); self.configurar_deseleccion(self.s_table); self.s_table.cellDoubleClicked.connect(lambda r, c: self.edit_rec(self.s_table)); l.addWidget(self.s_table)
        bl = QHBoxLayout(); bl.addWidget(QPushButton(t("btn_editar"), clicked=lambda: self.edit_rec(self.s_table))); bl.addWidget(QPushButton(t("btn_borrar_seleccionado"), clicked=lambda: self.del_rec(self.s_table))); l.addLayout(bl); self.tab_search.setLayout(l)

    def _es_mi_registro(self, tarea_id):
        """Comprueba si el registro pertenece al usuario actual."""
        d = self.db.obtener_tarea_por_id(tarea_id)
        if not d:
            return False
        uid_registro = d[4] if len(d) > 4 else None
        return uid_registro == usuarios.id_actual()

    def _puede_modificar(self, tarea_id):
        """Admin puede todo; técnico solo sus registros (lo decide el núcleo, igual que en MantPro Web)."""
        return trabajos.puede_modificar(usuarios.SESION_ACTUAL, self.db.obtener_tarea_por_id(tarea_id))

    def edit_rec(self, tabla_widget):
        r = tabla_widget.currentRow()
        if r >= 0: self.proc_edit(tabla_widget.item(r, 0).data(Qt.ItemDataRole.UserRole))

    def proc_edit(self, i):
        d = self.db.obtener_tarea_por_id(i)
        if d:
            if not self._puede_modificar(i):
                QMessageBox.information(self, t("aviso"),
                    tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))
                return
            uid = d[4] if len(d) > 4 else None
            unombre = d[5] if len(d) > 5 else ""
            maquina_id = d[6] if len(d) > 6 else None
            horas_paro = d[7] if len(d) > 7 else None
            dlg = EditDialog(self, d[1], d[2], d[3], usuario_id=uid, usuario_nombre=unombre, maquina_id=maquina_id, horas_paro=horas_paro,
                             repuestos=consumos.materiales_de_trabajo(i), tiempo=mano_obra.tiempo_de(i),
                             ver_lista=(lambda: self.ver_checklist(i)) if checklists.resultado_de(i) else None)
            if dlg.exec():
                fecha, desc, tags, nuevo_uid, nuevo_nombre, nueva_maquina_id, nuevas_horas_paro = dlg.get_data()
                # Lo guarda el núcleo, igual que MantPro Web: tiempo y repuestos (el stock se ajusta por la diferencia)
                try:
                    trabajos.guardar_editado(self.db, i, fecha, desc, tags, nuevo_uid, nuevo_nombre, nueva_maquina_id,
                                             nuevas_horas_paro, dlg.repuestos.items(), dlg.tiempo.minutos(), dlg.tiempo.personas())
                except ValueError:
                    return
                self.refresh_all()
                if hasattr(self, 'arbol_maquinas'):
                    self.refrescar_arbol_maquinas()

    def del_rec(self, tabla_widget):
        filas = sorted({ix.row() for ix in tabla_widget.selectionModel().selectedRows()})
        if not filas and tabla_widget.currentRow() >= 0:
            filas = [tabla_widget.currentRow()]
        ids = [tabla_widget.item(r, 0).data(Qt.ItemDataRole.UserRole) for r in filas]
        ids = [i for i in ids if i is not None]
        if not ids:
            return
        permitidos = [i for i in ids if self._puede_modificar(i)]
        if not permitidos:
            QMessageBox.information(self, t("aviso"),
                tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))
            return

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(t("title_confirmar_eliminacion"))
        if len(permitidos) == 1:
            msg.setText(t("msg_confirmar_eliminacion_registro"))
        else:
            msg.setText(t("msg_confirmar_eliminacion_registros").format(n=len(permitidos)))
        if len(permitidos) < len(ids):
            msg.setInformativeText(t("msg_registros_ajenos_omitidos").format(n=len(ids) - len(permitidos)))
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() != btn_si:
            return

        # Lo hace el núcleo, igual que MantPro Web: el aviso del que venía queda sin completar y la foto se borra
        trabajos.borrar(self.db, usuarios.SESION_ACTUAL, permitidos, carpeta_fotos=self.carpeta_fotos)
        self.refresh_all()
        if hasattr(self, 'servidor') and self.servidor:
            self.servidor.pendiente_actualizado.emit()

    def revertir_a_pendiente(self, tabla_widget):
        """Deshace la finalización de un trabajo: lo saca del historial y lo
        vuelve a poner en Pendientes, por si se completó por error."""
        r = tabla_widget.currentRow()
        if r < 0: return
        i = tabla_widget.item(r, 0).data(Qt.ItemDataRole.UserRole)
        if not self._puede_modificar(i):
            QMessageBox.information(self, t("aviso"),
                tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))
            return

        d = self.db.obtener_tarea_por_id(i)
        if not d: return
        maquina_id = d[6] if len(d) > 6 else None

        texto_aviso = tt("msg_confirmar_revertir_pendiente",
            "El trabajo volverá a la pestaña Pendientes y desaparecerá del historial. ¿Continuar?")
        if maquina_id:
            texto_aviso += "\n\n" + tt("msg_revertir_pierde_maquina",
                "Las tareas pendientes no admiten máquina vinculada, así que se perderá ese dato.")

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tt("title_revertir_pendiente", "Revertir a pendiente"))
        msg.setText(texto_aviso)
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() != btn_si: return

        # Lo hace el núcleo, igual que MantPro Web y la app: el aviso del que venía queda sin completar, y el
        # pendiente vuelve con su técnico, su sede y su lista de comprobación
        try:
            trabajos.revertir(self.db, usuarios.SESION_ACTUAL, i)
        except ValueError:
            QMessageBox.critical(self, t("aviso"), tt("msg_error_revertir", "No se ha podido revertir el trabajo a pendiente."))
            return
        self.refresh_todos()
        self.refresh_all()
        if hasattr(self, 'servidor') and self.servidor:
            self.servidor.pendiente_actualizado.emit()
        self.statusBar().showMessage(tt("msg_revertido_pendiente", "Trabajo movido de nuevo a Pendientes."), 4000)

    def ver_checklist(self, tarea_id):
        """Muestra la lista rellenada de un trabajo; quien puede modificar el
        registro puede también corregirla."""
        lista = checklists.resultado_de(tarea_id)
        if not lista:
            return
        fila = self.db.obtener_tarea_por_id(tarea_id)
        titulo = (fila[2] if fila else "").split("\n")[0]
        puede = self._puede_modificar(tarea_id)
        dlg = DialogoRellenarChecklist(self, titulo, lista["items"], lista["plantilla"], solo_lectura=not puede,
                                       tarea_id=tarea_id)
        if dlg.exec() and puede:
            nuevos = dlg.items()
            checklists.guardar_resultado(tarea_id, nuevos, lista["plantilla"])
            usuarios.auditar("trabajos", "editar", titulo, detalle=f"Lista de comprobación «{lista['plantilla']}» corregida",
                             cambios=checklists.cambios_resultado(lista["items"], nuevos), objeto_id=tarea_id)
            self.refresh_history()

    def _menu_contextual_historial(self, pos):
        """Menú con clic derecho sobre la tabla del historial."""
        seleccion = self.h_table.selectionModel().selectedRows()
        if not seleccion:
            return

        menu = QMenu(self)
        n = len(seleccion)

        if n == 1:
            tarea_id = self.h_table.item(seleccion[0].row(), 0).data(Qt.ItemDataRole.UserRole)
            puede = self._puede_modificar(tarea_id)
            act_editar = menu.addAction(t("btn_editar"), lambda: self.edit_rec(self.h_table))
            act_editar.setEnabled(puede)
            if not puede:
                act_editar.setToolTip(tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))

        # Cambiar autor (admin)
        if usuarios.es_admin():
            texto = tt("ctx_cambiar_autor", "👤 Cambiar autor") if n == 1 else \
                    tt("ctx_cambiar_autor_n", "👤 Cambiar autor ({n} registros)").format(n=n)
            menu.addAction(texto, lambda: self._reasignar_masivo(seleccion))

        if n == 1 and checklists.resultado_de(tarea_id):
            menu.addAction(tt("ctx_ver_checklist", "☑️ Ver lista de comprobación"),
                           lambda: self.ver_checklist(tarea_id))

        if n == 1:
            act_revertir = menu.addAction(tt("ctx_revertir_pendiente", "↩️ Revertir a pendiente"),
                                           lambda: self.revertir_a_pendiente(self.h_table))
            act_revertir.setEnabled(puede)
            if not puede:
                act_revertir.setToolTip(tt("msg_solo_tus_registros", "Solo puedes modificar tus propios trabajos."))

            menu.addSeparator()
            act_borrar = menu.addAction(t("btn_borrar_seleccionado"), lambda: self.del_rec(self.h_table))
            act_borrar.setEnabled(puede)
        else:
            menu.addSeparator()
            menu.addAction(t("ctx_borrar_n_registros").format(n=n), lambda: self.del_rec(self.h_table))

        menu.exec(self.h_table.viewport().mapToGlobal(pos))

    def _reasignar_masivo(self, seleccion):
        """Cambia el autor de uno o varios registros del historial."""
        if not usuarios.es_admin():
            return

        ids = []
        for idx in seleccion:
            item = self.h_table.item(idx.row(), 0)
            if item:
                ids.append(item.data(Qt.ItemDataRole.UserRole))
        if not ids:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tt("ctx_cambiar_autor", "Cambiar autor"))
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(
            tt("lbl_nuevo_autor", "Nuevo autor para {n} registro(s):").format(n=len(ids))))

        combo = QComboBox()
        combo.addItem(usuarios.ETIQUETA_HISTORICO, None)
        for u in usuarios.listar_usuarios(incluir_inactivos=True):
            combo.addItem(u["nombre"], u["id"])
        lay.addWidget(combo)

        caja = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        caja.button(QDialogButtonBox.StandardButton.Ok).setText(t("btn_aceptar"))
        caja.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_cancelar"))
        caja.accepted.connect(dlg.accept)
        caja.rejected.connect(dlg.reject)
        lay.addWidget(caja)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        nuevo_uid = combo.currentData()
        nuevo_nombre = combo.currentText() if nuevo_uid is not None else usuarios.ETIQUETA_HISTORICO

        # --- Diálogo de progreso modal (bloquea la ventana principal) ---
        progreso = QProgressDialog(
            tt("msg_reasignando", "Reasignando registros…"), None, 0, len(ids), self)
        progreso.setWindowTitle(tt("ctx_cambiar_autor", "Cambiar autor"))
        progreso.setWindowModality(Qt.WindowModality.ApplicationModal)
        progreso.setMinimumDuration(0)
        progreso.setCancelButton(None)  # Sin botón de cancelar
        progreso.setAutoClose(False)
        progreso.setValue(0)
        QApplication.processEvents()

        def _avance(hechos, total):
            progreso.setValue(hechos)
            progreso.setLabelText(tt("msg_reasignando_n", "Reasignando {i} de {n}…").format(i=hechos, n=total))
            QApplication.processEvents()

        try:
            # Lo hace el núcleo, igual que MantPro Web (y apunta cada cambio en el registro de cambios)
            trabajos.reasignar_autor(self.db, usuarios.SESION_ACTUAL, ids, nuevo_uid, progreso=_avance)
        except Exception as e:
            progreso.close()
            QMessageBox.critical(self, t("title_error"), str(e))
            return

        progreso.close()
        self.refresh_all()
        self.statusBar().showMessage(
            tt("msg_autor_cambiado", "{n} registro(s) reasignado(s) a {nombre}").format(
                n=len(ids), nombre=nuevo_nombre), 4000)
