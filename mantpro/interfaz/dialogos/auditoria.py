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

"""Herramientas → Registro de cambios: quién ha cambiado qué, cuándo y desde
dónde (PC o móvil), con el detalle campo a campo (antes → después)."""

import csv
import os
from datetime import date, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
                             QFileDialog, QMessageBox, QWidget, QTextEdit)
from PyQt6.QtCore import Qt, QTimer

from ...idiomas import t
from ..comun import tt
from ...nucleo import usuarios


def nombres_categoria():
    return {
        "trabajos": tt("aud_cat_trabajos", "📋 Trabajos (historial)"),
        "pendientes": tt("aud_cat_pendientes", "🔨 Pendientes"),
        "avisos": tt("aud_cat_avisos", "🔁 Avisos"),
        "checklists": tt("aud_cat_checklists", "☑️ Listas de comprobación"),
        "maquinas": tt("aud_cat_maquinas", "🏭 Máquinas y repuestos"),
        "almacen": tt("aud_cat_almacen", "📦 Almacén"),
        "usuarios": tt("aud_cat_usuarios", "👥 Usuarios"),
        "seguridad": tt("aud_cat_seguridad", "🛡️ Seguridad"),
        "copias": tt("aud_cat_copias", "💾 Copias e importación"),
        "configuracion": tt("aud_cat_configuracion", "⚙️ Configuración"),
    }


def nombres_accion():
    return {
        "crear": tt("aud_acc_crear", "➕ Creado"),
        "editar": tt("aud_acc_editar", "✏️ Modificado"),
        "borrar": tt("aud_acc_borrar", "🗑️ Borrado"),
        "revertir": tt("aud_acc_revertir", "↩️ Revertido a pendiente"),
        "completar": tt("aud_acc_completar", "✅ Completado"),
        "descompletar": tt("aud_acc_descompletar", "↩️ Desmarcado"),
        "activar": tt("aud_acc_activar", "✔️ Reactivado"),
        "desactivar": tt("aud_acc_desactivar", "🚫 Desactivado"),
        "contrasena": tt("aud_acc_contrasena", "🔑 Contraseña"),
        "configurar": tt("aud_acc_configurar", "⚙️ Configurado"),
        "revocar": tt("aud_acc_revocar", "🚫 Sesión revocada"),
        "bloquear": tt("aud_acc_bloquear", "⛔ Bloqueo por intentos"),
        "restaurar": tt("aud_acc_restaurar", "♻️ Copia restaurada"),
        "importar": tt("aud_acc_importar", "📥 Importación"),
    }


# Nombres de campo que se guardan (en español) en el registro, con su clave de
# traducción: se traducen al mostrarlos.
_CAMPOS = {
    "Fecha": "aud_f_fecha", "Descripción": "aud_f_descripcion", "Etiquetas": "aud_f_etiquetas",
    "Realizado por": "aud_f_realizado_por", "Máquina": "aud_f_maquina", "Horas de paro": "aud_f_horas_paro",
    "Título": "aud_f_titulo", "Detalles": "aud_f_detalles", "Asignado a": "aud_f_asignado",
    "Prioridad": "aud_f_prioridad", "Especialidad": "aud_f_especialidad", "Fecha de inicio": "aud_f_inicio",
    "Frecuencia": "aud_f_frecuencia", "Días de margen": "aud_f_margen", "Nombre": "aud_f_nombre",
    "Roles": "aud_f_roles", "Activo": "aud_f_activo", "Especialidades": "aud_f_especialidades",
    "Máquina superior": "aud_f_superior", "Zona": "aud_f_zona", "Notas": "aud_f_notas", "Foto": "aud_f_foto",
    "Código": "aud_f_codigo", "Unidad": "aud_f_unidad", "Stock mínimo": "aud_f_minimo",
    "Ubicación": "aud_f_ubicacion", "Puntos": "aud_f_puntos", "Lista de comprobación": "aud_f_checklist",
    "Última vez completado": "aud_f_ultima", "Puerto de sincronización": "aud_f_puerto",
    "País (festivos)": "aud_f_pais", "Región (festivos)": "aud_f_region",
    "Región superior (festivos)": "aud_f_region_superior", "Idioma": "aud_f_idioma",
    "Precio unitario": "aud_f_precio", "Moneda": "aud_f_moneda",
    "Días sin conectar": "aud_f_dias_sin_conectar",
    "Móvil adjudicado a": "aud_f_movil_adjudicado",
    "Tiempo trabajado": "aud_f_tiempo", "Coste de la hora de trabajo": "aud_f_coste_hora",
    "Contador": "aud_f_contador", "Cada": "aud_f_cada", "Avisar antes": "aud_f_avisar_antes",
    "Primera vez a": "aud_f_primera", "Lectura": "aud_f_lectura", "Lecturas": "aud_f_lecturas",
    "Copias automáticas": "aud_f_copias_automaticas", "Copia periódica": "aud_f_copia_periodica",
    "Cada (horas)": "aud_f_cada_horas", "Copia tras recibir datos de un móvil": "aud_f_copia_tras_movil",
    "Carpeta externa de las copias": "aud_f_carpeta_externa", "Copias recientes que se guardan": "aud_f_copias_recientes",
    "Días con una copia diaria": "aud_f_dias_copia_diaria",
    "Contacto": "aud_f_contacto", "Teléfono": "aud_f_telefono", "Correo": "aud_f_correo",
    "Proveedor habitual": "aud_f_proveedor_habitual",
}


def campo(texto):
    """Nombre de campo traducido (o tal cual si es un texto propio, p. ej.
    «Repuesto SEL-01»)."""
    clave = _CAMPOS.get(texto)
    return tt(clave, texto) if clave else texto


def _resumen(r):
    """Texto corto de la columna «Cambios»."""
    if r.get("cambios"):
        n = len(r["cambios"])
        campos = ", ".join(campo(c["campo"]) for c in r["cambios"][:3]) + ("…" if n > 3 else "")
        return tt("aud_n_cambios", "{n} cambios: {campos}").format(n=n, campos=campos) if n > 1 else campos
    return (r.get("detalle") or "").split("\n")[0]


class DialogoRegistroCambios(QDialog):
    POR_PAGINA = 300

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("menu_auditoria", "Registro de cambios").lstrip("📋 "))
        self.resize(1200, 700)
        self._registros = []
        self._hay_mas = False
        l = QVBoxLayout(self)

        # --- filtros
        f = QHBoxLayout()
        self.combo_cat = QComboBox(); self.combo_cat.addItem(tt("filtro_todas", "Todas"), None)
        for clave, nombre in nombres_categoria().items():
            self.combo_cat.addItem(nombre, clave)
        self.combo_acc = QComboBox(); self.combo_acc.addItem(tt("filtro_todas", "Todas"), None)
        for clave, nombre in nombres_accion().items():
            self.combo_acc.addItem(nombre, clave)
        self.combo_usu = QComboBox(); self.combo_usu.addItem(tt("filtro_todos", "Todos"), None)
        for u in usuarios.listar_usuarios(incluir_inactivos=True):
            self.combo_usu.addItem(u["nombre"], u["id"])
        self.combo_periodo = QComboBox()
        for texto, dias in ((tt("aud_periodo_7", "Últimos 7 días"), 7), (tt("aud_periodo_30", "Últimos 30 días"), 30),
                            (tt("aud_periodo_365", "Último año"), 365), (tt("aud_periodo_todo", "Todo"), None)):
            self.combo_periodo.addItem(texto, dias)
        self.combo_periodo.setCurrentIndex(1)
        self.buscar = QLineEdit(); self.buscar.setPlaceholderText(tt("aud_buscar", "Buscar (máquina, artículo, usuario, texto…)"))
        self.buscar.setClearButtonEnabled(True)
        for etiqueta, widget in ((tt("aud_categoria", "Categoría"), self.combo_cat), (tt("lbl_accion", "Acción"), self.combo_acc),
                                 (tt("aud_usuario", "Usuario"), self.combo_usu), (tt("aud_periodo", "Periodo"), self.combo_periodo)):
            f.addWidget(QLabel(etiqueta + ":")); f.addWidget(widget)
        l.addLayout(f)
        l.addWidget(self.buscar)

        # --- tabla y detalle
        split = QSplitter(Qt.Orientation.Vertical)
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels([tt("lbl_fecha_hora", "Fecha y hora"), tt("aud_usuario", "Usuario"),
                                              tt("aud_origen", "Desde"), tt("aud_categoria", "Categoría"),
                                              tt("lbl_accion", "Acción"), tt("aud_objeto", "Afecta a"),
                                              tt("aud_cambios", "Cambios")])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        cab = self.tabla.horizontalHeader()
        for c in range(5):
            cab.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive); self.tabla.setColumnWidth(5, 260)
        cab.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.tabla.currentCellChanged.connect(lambda *_: self._mostrar_detalle())
        split.addWidget(self.tabla)

        abajo = QWidget(); la = QVBoxLayout(abajo); la.setContentsMargins(0, 0, 0, 0)
        self.lbl_detalle = QLabel(); self.lbl_detalle.setWordWrap(True)
        self.lbl_detalle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        la.addWidget(self.lbl_detalle)
        self.tabla_cambios = QTableWidget(0, 3)
        self.tabla_cambios.setHorizontalHeaderLabels([tt("aud_campo", "Campo"), tt("aud_antes", "Antes"), tt("aud_despues", "Después")])
        self.tabla_cambios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_cambios.verticalHeader().setVisible(False)
        self.tabla_cambios.setWordWrap(True)
        cc = self.tabla_cambios.horizontalHeader()
        cc.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cc.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        cc.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        la.addWidget(self.tabla_cambios)
        self.texto_detalle = QTextEdit(); self.texto_detalle.setReadOnly(True); self.texto_detalle.setMaximumHeight(110)
        la.addWidget(self.texto_detalle)
        split.addWidget(abajo)
        split.setSizes([420, 260])
        l.addWidget(split, 1)

        # --- botones
        b = QHBoxLayout()
        self.lbl_total = QLabel()
        b.addWidget(self.lbl_total)
        b.addStretch()
        self.btn_mas = QPushButton(tt("aud_cargar_mas", "Cargar más")); self.btn_mas.clicked.connect(self._cargar_mas)
        exportar = QPushButton(tt("aud_exportar", "📤 Exportar (Excel o CSV)")); exportar.clicked.connect(self._exportar)
        cerrar = QPushButton(t("cerrar")); cerrar.clicked.connect(self.accept)
        for w in (self.btn_mas, exportar, cerrar):
            b.addWidget(w)
        l.addLayout(b)

        for combo in (self.combo_cat, self.combo_acc, self.combo_usu, self.combo_periodo):
            combo.currentIndexChanged.connect(self.recargar)
        self._espera = QTimer(self, singleShot=True, interval=350, timeout=self.recargar)
        self.buscar.textChanged.connect(lambda _t: self._espera.start())
        self.recargar()

    # ----------------------------------------------------------- datos
    def _filtros(self):
        dias = self.combo_periodo.currentData()
        return dict(categoria=self.combo_cat.currentData(), accion=self.combo_acc.currentData(),
                    usuario_id=self.combo_usu.currentData(), texto=self.buscar.text().strip() or None,
                    desde=(date.today() - timedelta(days=dias)).isoformat() if dias else None)

    def recargar(self):
        self._registros = usuarios.obtener_auditoria(limite=self.POR_PAGINA + 1, **self._filtros())
        self._hay_mas = len(self._registros) > self.POR_PAGINA
        self._registros = self._registros[:self.POR_PAGINA]
        self._pintar()

    def _cargar_mas(self):
        mas = usuarios.obtener_auditoria(limite=self.POR_PAGINA + 1, desplazamiento=len(self._registros), **self._filtros())
        self._hay_mas = len(mas) > self.POR_PAGINA
        self._registros += mas[:self.POR_PAGINA]
        self._pintar()

    def _pintar(self):
        cats, accs = nombres_categoria(), nombres_accion()
        self.tabla.setRowCount(len(self._registros))
        for fila, r in enumerate(self._registros):
            fecha = (r.get("fecha") or "").replace("T", " ")
            celdas = [fecha, r.get("usuario_nombre") or "—", r.get("origen") or "💻 PC",
                      cats.get(r["categoria"], r["categoria"]), accs.get(r["accion"], r["accion"]),
                      campo(r.get("objeto") or "") or (f"#{r['tarea_id']}" if r.get("tarea_id") else ""), _resumen(r)]
            for col, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                if col == 6 and r.get("detalle"):
                    item.setToolTip(r["detalle"])
                if r["accion"] in ("borrar", "bloquear", "revocar", "desactivar"):
                    item.setForeground(Qt.GlobalColor.red)
                self.tabla.setItem(fila, col, item)
        self.btn_mas.setVisible(self._hay_mas)
        self.lbl_total.setText(tt("aud_total", "{n} registros").format(n=len(self._registros)) + ("+" if self._hay_mas else ""))
        if self._registros:
            self.tabla.selectRow(0)
        self._mostrar_detalle()

    def _mostrar_detalle(self):
        fila = self.tabla.currentRow()
        r = self._registros[fila] if 0 <= fila < len(self._registros) else None
        self.tabla_cambios.setRowCount(0)
        if r is None:
            self.lbl_detalle.setText(tt("aud_sin_registros", "No hay cambios con estos filtros."))
            self.texto_detalle.clear(); self.tabla_cambios.setVisible(False); self.texto_detalle.setVisible(False)
            return
        cats, accs = nombres_categoria(), nombres_accion()
        self.lbl_detalle.setText(f"<b>{accs.get(r['accion'], r['accion'])}</b> · {cats.get(r['categoria'], r['categoria'])}"
                                 f" · {r.get('objeto') or ''}<br>{(r.get('fecha') or '').replace('T', ' ')} · "
                                 f"{r.get('usuario_nombre') or '—'} · {r.get('origen') or '💻 PC'}")
        cambios = r.get("cambios") or []
        self.tabla_cambios.setVisible(bool(cambios))
        self.tabla_cambios.setRowCount(len(cambios))
        for i, c in enumerate(cambios):
            for col, texto in enumerate((campo(c.get("campo", "")), c.get("antes", ""), c.get("despues", ""))):
                item = QTableWidgetItem(texto if texto != "" else "—")
                if col == 1 and texto:
                    item.setForeground(Qt.GlobalColor.darkRed)
                if col == 2 and texto:
                    item.setForeground(Qt.GlobalColor.darkGreen)
                self.tabla_cambios.setItem(i, col, item)
        self.tabla_cambios.resizeRowsToContents()
        self.texto_detalle.setVisible(bool(r.get("detalle")))
        self.texto_detalle.setPlainText(r.get("detalle") or "")

    # ----------------------------------------------------------- exportar
    def _filas_export(self):
        """Una fila por cambio (o una por registro si no tiene cambios)."""
        cats, accs = nombres_categoria(), nombres_accion()
        todos = usuarios.obtener_auditoria(limite=100000, **self._filtros())
        for r in todos:
            base = [(r.get("fecha") or "").replace("T", " "), r.get("usuario_nombre") or "", r.get("origen") or "PC",
                    cats.get(r["categoria"], r["categoria"]), accs.get(r["accion"], r["accion"]),
                    r.get("objeto") or "", r.get("detalle") or ""]
            if r.get("cambios"):
                for c in r["cambios"]:
                    yield base + [campo(c.get("campo", "")), c.get("antes", ""), c.get("despues", "")]
            else:
                yield base + ["", "", ""]

    def _exportar(self):
        cab = [tt("lbl_fecha_hora", "Fecha y hora"), tt("aud_usuario", "Usuario"), tt("aud_origen", "Desde"),
               tt("aud_categoria", "Categoría"), tt("lbl_accion", "Acción"), tt("aud_objeto", "Afecta a"),
               tt("lbl_detalle", "Detalle"), tt("aud_campo", "Campo"), tt("aud_antes", "Antes"), tt("aud_despues", "Después")]
        nombre = f"{tt('aud_fichero', 'Registro_de_cambios')}_{date.today().strftime('%Y%m%d')}.xlsx"
        ruta, filtro = QFileDialog.getSaveFileName(self, tt("aud_exportar", "📤 Exportar (Excel o CSV)"), nombre,
                                                   "Excel (*.xlsx);;CSV (*.csv)")
        if not ruta:
            return
        filas = list(self._filas_export())
        try:
            if ruta.lower().endswith(".csv") or "CSV" in filtro:
                if not ruta.lower().endswith(".csv"):
                    ruta = os.path.splitext(ruta)[0] + ".csv"
                with open(ruta, "w", newline="", encoding="utf-8-sig") as fh:
                    w = csv.writer(fh, delimiter=";")
                    w.writerow(cab); w.writerows(filas)
            else:
                import xlsxwriter
                if not ruta.lower().endswith(".xlsx"):
                    ruta += ".xlsx"
                libro = xlsxwriter.Workbook(ruta)
                hoja = libro.add_worksheet(tt("aud_hoja", "Registro de cambios")[:31])
                negrita = libro.add_format({"bold": True, "bg_color": "#2c3e50", "font_color": "white"})
                ajuste = libro.add_format({"text_wrap": True, "valign": "top"})
                for col, texto in enumerate(cab):
                    hoja.write(0, col, texto, negrita)
                for i, fila in enumerate(filas, start=1):
                    for col, valor in enumerate(fila):
                        hoja.write(i, col, valor, ajuste)
                for col, ancho in enumerate((18, 18, 18, 22, 20, 35, 40, 22, 30, 30)):
                    hoja.set_column(col, col, ancho)
                hoja.freeze_panes(1, 0)
                hoja.autofilter(0, 0, max(len(filas), 1), len(cab) - 1)
                libro.close()
            QMessageBox.information(self, self.windowTitle(),
                                    tt("aud_exportado", "Exportados {n} registros a:\n{ruta}").format(n=len(filas), ruta=ruta))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))
