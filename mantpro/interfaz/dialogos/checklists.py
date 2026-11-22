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

import os
import re
import tempfile

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
                             QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
                             QHeaderView, QMessageBox, QAbstractItemView, QWidget, QButtonGroup,
                             QRadioButton, QSplitter, QDialogButtonBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QColor

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ...nucleo import checklists, ficha_checklists, usuarios
# Los textos de las listas en exportaciones e informes están en el núcleo (también los usa MantPro Web)
from ...nucleo.informe_historial import (resumen_texto, estado_plano, linea_export, texto_desequilibrio,  # noqa: F401
                                          texto_deseq_max, texto_export, texto_repuestos_export, texto_tiempo_export)


def texto_estado(estado):
    return {"ok": tt("chk_estado_ok", "✅ Bien"), "mal": tt("chk_estado_mal", "❌ Mal"),
            "na": tt("chk_estado_na", "➖ No aplica")}.get(estado, tt("chk_estado_sin", "Sin revisar"))


texto_rango = checklists.texto_rango     # en el núcleo: lo usa también MantPro Web


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

    def __init__(self, parent, titulo, items, plantilla_nombre="", solo_lectura=False, al_cambiar=None, tarea_id=None):
        super().__init__(parent)
        self.tarea_id = tarea_id          # con él (lista ya guardada con un trabajo): imprimir y exportar
        self._items = [dict(it) for it in items]
        self.solo_lectura = solo_lectura
        # al_cambiar(items): se llama (con un pequeño retraso) cada vez que se apunta algo,
        # para guardar el borrador de una lista que se deja a medias.
        self._al_cambiar = None if solo_lectura else al_cambiar
        self._espera = QTimer(self); self._espera.setSingleShot(True); self._espera.setInterval(400)
        # Si cada punto tiene ahora su lectura fuera de rango: así se sabe si un «mal» lo
        # puso la lectura (y al corregirla vuelve a «bien») o el técnico a propósito.
        self._fuera = [checklists.fuera_de_rango(it, it.get("valor")) for it in self._items]
        self._espera.timeout.connect(self._guardar_borrador)
        self.setWindowTitle(tt("title_checklist", "Lista de comprobación"))
        self.resize(900, 520)
        l = QVBoxLayout(self)
        self._titulo = titulo
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
        # _valores[fila]: QLineEdit (lectura), lista de tres QLineEdit (trifásica) o None
        self._grupos, self._valores, self._notas, self._desequilibrios = [], [], [], {}
        for fila, it in enumerate(self._items):
            if it["tipo"] == checklists.SECCION:
                # Separador: título de zona o máquina a lo ancho de la tabla, sin estado ni campos
                celda = QTableWidgetItem(f"▸ {it['texto']}")
                celda.setFlags(Qt.ItemFlag.ItemIsEnabled)
                letra = celda.font(); letra.setBold(True); letra.setPointSizeF(letra.pointSizeF() * 1.1); celda.setFont(letra)
                celda.setBackground(QColor(61, 174, 233, 60))
                self.tabla.setItem(fila, self.COL_PUNTO, celda)
                self.tabla.setSpan(fila, 0, 1, 4)
                self._grupos.append(QButtonGroup(self)); self._valores.append(None); self._notas.append(None)
                continue
            texto = it["texto"]
            if it["tipo"] in checklists.TIPOS_CON_VALOR and texto_rango(it):
                texto += f"\n({tt('chk_rango', 'correcto')}: {texto_rango(it)})"
            if texto_deseq_max(it):
                texto += f"\n({texto_deseq_max(it)})"
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

            if it["tipo"] == "trifasica":
                campos = []
                caja_v = QWidget(); vv = QVBoxLayout(caja_v); vv.setContentsMargins(4, 0, 4, 0); vv.setSpacing(2)
                hv = QHBoxLayout(); hv.setSpacing(4)
                for fase, texto_fase in zip(checklists.FASES, checklists.fases(it.get("valor"))):
                    hv.addWidget(QLabel(fase))
                    campo = QLineEdit(texto_fase)
                    campo.setPlaceholderText(it.get("unidad") or tt("chk_valor", "valor"))
                    campo.setMaximumWidth(70)
                    campo.setReadOnly(solo_lectura)
                    campo.textChanged.connect(lambda _txt, f=fila: self._lectura_cambiada(f))
                    hv.addWidget(campo)
                    campos.append(campo)
                if it.get("unidad"):
                    hv.addWidget(QLabel(it["unidad"]))
                vv.addLayout(hv)
                lbl = QLabel(); lbl.setStyleSheet("color: gray; font-size: 11px;")
                vv.addWidget(lbl)
                self._desequilibrios[fila] = lbl
                self.tabla.setCellWidget(fila, self.COL_VALOR, caja_v)
                self._valores.append(campos)
                self._pintar_rango(fila)
            elif it["tipo"] == "lectura":
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
        if self._al_cambiar:
            for grupo in self._grupos:
                grupo.buttonToggled.connect(lambda *_: self._espera.start())
            for campo in self._valores:
                for c in (campo if isinstance(campo, list) else [campo] if campo is not None else []):
                    c.textChanged.connect(lambda *_: self._espera.start())
            for nota in filter(None, self._notas):
                nota.textChanged.connect(lambda *_: self._espera.start())

        botones = QHBoxLayout()
        if tarea_id is not None:
            for texto, clave, accion in (("🖨️ Imprimir", "btn_chk_imprimir", self._imprimir),
                                         ("📄 Exportar PDF", "btn_exportar_pdf_corto", lambda: self._exportar("pdf")),
                                         ("📊 Exportar Excel", "btn_exportar_excel_corto", lambda: self._exportar("xlsx"))):
                b = QPushButton(tt(clave, texto))
                b.clicked.connect(accion)
                botones.addWidget(b)
        if not solo_lectura and tarea_id is None:
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

    # ------------------------------------------------------------- imprimir / exportar
    def _logo(self):
        from ...nucleo.rutas import DATA_DIR
        return os.path.join(DATA_DIR, "Logo.jpg")

    def _imprimir(self):
        """PDF en una carpeta temporal, abierto con el visor del sistema para imprimirlo
        (igual que los pedidos a proveedor)."""
        from ...nucleo import informe_checklist
        carpeta = tempfile.mkdtemp(prefix="mantpro_lista_")
        ruta = os.path.join(carpeta, self._nombre_fichero() + ".pdf")
        try:
            informe_checklist.generar_pdf(self.tarea_id, ruta, self._logo(), self.items())
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))

    def _nombre_fichero(self):
        titulo = tt("title_checklist", "Lista de comprobación")
        return re.sub(r"[^\w-]+", "_", f"{titulo}_{self._titulo}").strip("_")[:120] or "lista"

    def _exportar(self, formato):
        from ...nucleo import informe_checklist
        if formato == "xlsx":
            try: import xlsxwriter  # noqa: F401
            except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        filtro = "PDF (*.pdf)" if formato == "pdf" else "Excel (*.xlsx)"
        titulo_dlg = t("title_exportar_pdf") if formato == "pdf" else t("title_exportar_excel")
        propuesto = f"{self._nombre_fichero()}.{formato}"
        guardar = getattr(self.parent(), "guardar_archivo_dialogo", None)
        if guardar:
            archivo = guardar(titulo_dlg, propuesto, filtro)
        else:
            archivo, _ = QFileDialog.getSaveFileName(self, titulo_dlg, propuesto, filtro)
        if not archivo:
            return
        if not archivo.lower().endswith("." + formato):
            archivo += "." + formato
        try:
            if formato == "pdf":
                informe_checklist.generar_pdf(self.tarea_id, archivo, self._logo(), self.items())
            else:
                informe_checklist.generar_excel(self.tarea_id, archivo, self.items())
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))
            return
        QMessageBox.information(self, t("title_exportado"),
                                tt("msg_chk_exportada", "Lista de comprobación exportada en:\n{ruta}").format(ruta=archivo))

    def _guardar_borrador(self):
        self._espera.stop()
        if self._al_cambiar:
            self._al_cambiar(self.items())

    def done(self, r):
        if self._espera.isActive():          # lo último escrito antes de cerrar
            self._guardar_borrador()
        super().done(r)

    def _estado_de(self, fila):
        b = self._grupos[fila].checkedButton()
        return b.property("estado") if b else None

    def _marcar(self, fila, estado):
        for b in self._grupos[fila].buttons():
            if b.property("estado") == estado:
                b.setChecked(True)

    def _valor_de(self, fila):
        """Lo escrito en la fila: «9,1», «12,1;12,3;12,0» (trifásica) o «»."""
        campo = self._valores[fila]
        if campo is None:
            return ""
        if isinstance(campo, list):
            return checklists.unir_fases(c.text() for c in campo)
        return campo.text().strip()

    def _pintar_rango(self, fila):
        campo = self._valores[fila]
        rojo = "color: #c0392b; font-weight: bold;"
        if isinstance(campo, list):
            punto = dict(self._items[fila], tipo="lectura")      # cada fase con el mismo rango
            for c in campo:
                c.setStyleSheet(rojo if checklists.fuera_de_rango(punto, c.text()) else "")
            lbl = self._desequilibrios.get(fila)
            if lbl is not None:
                valor = self._valor_de(fila)
                lbl.setText(texto_desequilibrio(dict(self._items[fila], valor=valor)))
                lbl.setVisible(bool(lbl.text()))
                excesivo = checklists.desequilibrio_excesivo(self._items[fila], valor)
                lbl.setStyleSheet("color: #c0392b; font-weight: bold; font-size: 11px;" if excesivo
                                  else "color: gray; font-size: 11px;")
            return
        fuera = checklists.fuera_de_rango(self._items[fila], campo.text())
        campo.setStyleSheet(rojo if fuera else "")

    def _lectura_cambiada(self, fila):
        self._pintar_rango(fila)
        texto = self._valor_de(fila)
        if not texto:
            return
        # Fuera de rango: «mal». Dentro: «bien» si aún no tenía estado o si el «mal» venía de
        # una lectura fuera de rango que se acaba de corregir (un «mal» puesto a mano con una
        # lectura correcta se respeta).
        fuera = checklists.fuera_de_rango(self._items[fila], texto)
        if fuera:
            self._marcar(fila, "mal")
        elif self._estado_de(fila) is None or (self._fuera[fila] and self._estado_de(fila) == "mal"):
            self._marcar(fila, "ok")
        self._fuera[fila] = fuera

    def _todo_bien(self):
        for fila in range(len(self._items)):
            if self._estado_de(fila) is None:
                self._marcar(fila, "ok")

    def items(self):
        resultado = []
        for fila, it in enumerate(self._items):
            nuevo = dict(it)
            nuevo["estado"] = self._estado_de(fila)
            nuevo["valor"] = self._valor_de(fila)
            nuevo["nota"] = self._notas[fila].text().strip() if self._notas[fila] is not None else ""
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


def rellenar_para(parent, plantilla_id, titulo, clave_borrador=None):
    """Al completar un aviso o un pendiente con lista: la pide rellenar.
    Devuelve (items, nombre de la plantilla), ([], "") si no tiene lista (o la
    plantilla ya no existe), o None si se cancela.
    Con [clave_borrador] (checklists.clave_borrador), lo apuntado se guarda al
    momento y, si se deja a medias, se ofrece seguir donde se quedó. El borrador
    lo borra quien completa el trabajo (checklists.borrar_borrador)."""
    plantilla = checklists.obtener_plantilla(plantilla_id) if plantilla_id else None
    if not plantilla or not plantilla["puntos"]:
        return [], ""
    items = checklists.items_de_plantilla(plantilla)
    borrador = checklists.borrador_de(clave_borrador) if clave_borrador else None
    if borrador:
        r = checklists.recuento(borrador["items"])
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tt("title_chk_borrador", "Lista a medias"))
        msg.setText(tt("msg_chk_borrador",
            "Esta lista se empezó el {fecha} y se dejó a medias ({hechos} puntos revisados).\n\n¿Seguir donde se quedó?").format(
            fecha=idiomas.formato_fecha_localizada(borrador["fecha"][:10]) + " " + borrador["fecha"][11:16],
            hechos=f"{len(checklists.puntos_reales(borrador['items'])) - r['sin']}/{len(checklists.puntos_reales(borrador['items']))}"))
        seguir = msg.addButton(tt("btn_chk_continuar", "Continuar"), QMessageBox.ButtonRole.AcceptRole)
        nueva = msg.addButton(tt("btn_chk_empezar_nuevo", "Empezar de nuevo"), QMessageBox.ButtonRole.DestructiveRole)
        msg.addButton(t("btn_cancelar"), QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(seguir)
        msg.exec()
        if msg.clickedButton() == seguir:
            checklists.aplicar_borrador(items, borrador)
        elif msg.clickedButton() == nueva:
            checklists.borrar_borrador(clave_borrador)
        else:
            return None
    al_cambiar = (lambda actual: checklists.guardar_borrador(clave_borrador, plantilla["nombre"], actual)) \
        if clave_borrador else None
    dlg = DialogoRellenarChecklist(parent, titulo, items, plantilla["nombre"], al_cambiar=al_cambiar)
    if not dlg.exec():
        return None
    return dlg.items(), plantilla["nombre"]


# ------------------------------------------------------------------ plantillas

class DialogoPlantillasChecklist(QDialog):
    """Herramientas → Listas de comprobación: crear, editar y borrar plantillas."""

    COL_TEXTO, COL_TIPO, COL_UNIDAD, COL_MIN, COL_MAX, COL_DESEQ = range(6)

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
            "Los puntos de tipo «Lectura» piden además un valor (con su unidad); si se sale del mínimo o el máximo, quedan como «mal». "
            "Los de tipo «Motor trifásico» piden tres lecturas (L1, L2, L3), con el mismo rango para cada fase, y además "
            "quedan como «mal» si el desequilibrio entre fases pasa del «Deseq. máx. %». "
            "Los de tipo «Separador» no se revisan: son un título (una zona o una máquina) que agrupa los puntos de debajo."))
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
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels([tt("chk_col_punto", "Punto"), tt("chk_col_tipo", "Tipo"),
                                              tt("chk_col_unidad", "Unidad"), tt("chk_col_minimo", "Mínimo"),
                                              tt("chk_col_maximo", "Máximo"), tt("chk_col_deseq_max", "Deseq. máx. %")])
        self.tabla.horizontalHeaderItem(self.COL_DESEQ).setToolTip(tt("tt_chk_deseq_max",
            "Solo en los motores trifásicos: si la fase que más se aparta de la media de las tres "
            "lo hace más de este porcentaje, el punto queda como «mal». Vacío: sin límite."))
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(self.COL_TEXTO, QHeaderView.ResizeMode.Stretch)
        for c in (self.COL_TIPO, self.COL_UNIDAD, self.COL_MIN, self.COL_MAX, self.COL_DESEQ):
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
            item = QListWidgetItem(ficha_checklists.texto_lista(p))
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
        self._modificada = False          # descartado: no volver a preguntar
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
        p = p or ficha_checklists.punto_vacio()
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)
        celda_texto = QTableWidgetItem(p["texto"])
        # Identidad fija del punto: viaja con la fila aunque se renombre o se mueva
        celda_texto.setData(Qt.ItemDataRole.UserRole, p.get("punto_uid"))
        self.tabla.setItem(fila, self.COL_TEXTO, celda_texto)
        combo = QComboBox()
        for tipo, texto in ficha_checklists.nombres_tipo():
            combo.addItem(texto, tipo)
        combo.setCurrentIndex(max(0, combo.findData(p["tipo"])))
        combo.currentIndexChanged.connect(lambda _i, c=combo: self._tipo_cambiado(c))
        self.tabla.setCellWidget(fila, self.COL_TIPO, combo)
        fmt = ficha_checklists.numero
        for col, valor in ((self.COL_UNIDAD, p.get("unidad") or ""), (self.COL_MIN, fmt(p.get("minimo"))),
                           (self.COL_MAX, fmt(p.get("maximo"))), (self.COL_DESEQ, fmt(p.get("desequilibrio_max")))):
            self.tabla.setItem(fila, col, QTableWidgetItem(valor))
        self._activar_lectura(fila, p["tipo"])

    def _activar_lectura(self, fila, tipo):
        """Unidad, mínimo y máximo solo en las lecturas; el desequilibrio máximo, solo en los trifásicos."""
        for col in (self.COL_UNIDAD, self.COL_MIN, self.COL_MAX, self.COL_DESEQ):
            item = self.tabla.item(fila, col)
            if item is None:
                continue
            activa = tipo == "trifasica" if col == self.COL_DESEQ else tipo in checklists.TIPOS_CON_VALOR
            if activa:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setText("")
                item.setFlags(Qt.ItemFlag.NoItemFlags)

    def _tipo_cambiado(self, combo):
        for fila in range(self.tabla.rowCount()):
            if self.tabla.cellWidget(fila, self.COL_TIPO) is combo:
                self.tabla.blockSignals(True)
                self._activar_lectura(fila, combo.currentData())
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
                           "punto_uid": self.tabla.item(fila, self.COL_TEXTO).data(Qt.ItemDataRole.UserRole),
                           "unidad": leer(self.COL_UNIDAD), "minimo": leer(self.COL_MIN), "maximo": leer(self.COL_MAX),
                           "desequilibrio_max": leer(self.COL_DESEQ)})
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
                           "punto_uid": self.tabla.item(f, self.COL_TEXTO).data(Qt.ItemDataRole.UserRole)
                           if self.tabla.item(f, self.COL_TEXTO) else None,
                           "unidad": leer(self.COL_UNIDAD), "minimo": checklists._num(leer(self.COL_MIN)),
                           "maximo": checklists._num(leer(self.COL_MAX)),
                           "desequilibrio_max": checklists._num(leer(self.COL_DESEQ))})
        puntos[fila], puntos[destino] = puntos[destino], puntos[fila]
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)
        for p in puntos:
            self._fila_punto(p)
        self.tabla.blockSignals(False)
        self.tabla.setCurrentCell(destino, self.COL_TEXTO)
        self._tocada()

    def _guardar(self):
        try:
            self._actual = ficha_checklists.guardar(usuarios.SESION_ACTUAL, self._actual, self.nombre.text(), self._puntos())
        except ValueError as e:
            QMessageBox.warning(self, self.windowTitle(), ficha_checklists.texto_error(str(e)))
            return False
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
        try:
            nuevo = ficha_checklists.duplicar(usuarios.SESION_ACTUAL, self._actual)
        except ValueError as e:
            QMessageBox.warning(self, self.windowTitle(), ficha_checklists.texto_error(str(e)))
            return
        self._recargar(elegir=nuevo)
        self._cargar(checklists.obtener_plantilla(nuevo))

    def _borrar(self):
        if self._actual is None:
            return
        try:
            if QMessageBox.question(self, self.windowTitle(), ficha_checklists.pregunta_borrar(self._actual)) \
                    != QMessageBox.StandardButton.Yes:
                return
            ficha_checklists.borrar(usuarios.SESION_ACTUAL, self._actual)
        except ValueError as e:
            QMessageBox.warning(self, self.windowTitle(), ficha_checklists.texto_error(str(e)))
            return
        self._modificada = False
        self._recargar()
        if self.lista.count():
            self.lista.setCurrentRow(0)
        else:
            self._cargar(None)

    # Sin closeEvent propio: QDialog.closeEvent ya llama a reject(), y preguntar en los dos
    # sacaba la confirmación dos veces y dejaba el diálogo abierto (con su exec() vivo, el
    # programa no terminaba al salir).
    def reject(self):
        if self._preguntar_guardar():
            super().reject()


