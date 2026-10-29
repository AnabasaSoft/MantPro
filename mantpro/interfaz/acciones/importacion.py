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

"""Importación desde Excel/CSV."""

from PyQt6.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
                             QAbstractItemView, QFileDialog)
from PyQt6.QtCore import Qt

from ...idiomas import t
from ..dialogos.importacion import DialogoImportar
from ...nucleo import usuarios, importar

class AccionesImportacion:
    """Importación desde Excel/CSV.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def importar_datos(self):
        if not usuarios.es_admin(): return
        DialogoImportar(self, self._ejecutar_importacion).exec()

    def _ejecutar_importacion(self, hojas, modo, dialogo):
        """Importación real, llamada desde el último paso del asistente con
        [(título, tipo, cabeceras, filas, mapeo)] de cada hoja. Devuelve True
        si se ha hecho (el asistente se cierra)."""
        c = importar.resumen([r for res in dialogo.resultados for r in res])
        respuesta = QMessageBox.question(dialogo, t("imp_titulo"),
                                         t("imp_msg_confirmar").format(n=c["crear"] + c["actualizar"]))
        if respuesta != QMessageBox.StandardButton.Yes: return False
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            ruta_copia = self._copia_previa_bases("antes_importacion")
            resultados, extra = importar.procesar_varias([(tipo, filas, mapeo) for _, tipo, _, filas, mapeo in hojas],
                                                         modo, aplicar=True, usuario_id=usuarios.id_actual(),
                                                         usuario_nombre=usuarios.nombre_actual())
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(dialogo, t("title_error"), t("imp_msg_error").format(error=e))
            return False
        QApplication.restoreOverrideCursor()
        self.refresh_all()

        titulos = [h[0] for h in hojas]
        msg = QMessageBox(dialogo)
        msg.setWindowTitle(t("imp_titulo")); msg.setIcon(QMessageBox.Icon.Information)
        # Más ancho solo para el texto (no para el icono): con varias hojas
        # hay una línea de resumen por hoja.
        msg.setStyleSheet("QLabel#qt_msgbox_label { min-width: 620px; }")
        msg.setText(t("imp_msg_terminado").format(resumen=dialogo.texto_resumen(titulos, resultados), ruta=ruta_copia))
        hay_errores = any(r.estado == "error" for res in resultados for r in res)
        btn_errores = msg.addButton(t("imp_btn_guardar_errores"), QMessageBox.ButtonRole.ActionRole) if hay_errores else None
        msg.addButton(t("btn_aceptar"), QMessageBox.ButtonRole.AcceptRole)
        msg.exec()
        if btn_errores is not None and msg.clickedButton() == btn_errores:
            ruta, _ = QFileDialog.getSaveFileName(dialogo, t("imp_btn_guardar_errores"),
                                                  t("imp_nombre_errores") + ".xlsx", "Excel (*.xlsx)")
            if ruta:
                if not ruta.lower().endswith(".xlsx"): ruta += ".xlsx"
                importar.exportar_errores(ruta, [(titulo, h[2], res) for titulo, h, res in zip(titulos, hojas, resultados)])
        if extra["passwords"]:
            self._mostrar_passwords_temporales(extra["passwords"], dialogo)
        return True

    def _mostrar_passwords_temporales(self, passwords, padre):
        """Contraseñas temporales de los usuarios importados: solo se pueden ver
        ahora (en la BD solo queda el hash), así que se ofrece guardarlas."""
        dlg = QDialog(padre); dlg.setWindowTitle(t("imp_title_passwords")); dlg.resize(560, 420)
        v = QVBoxLayout(dlg)
        aviso = QLabel(t("imp_msg_passwords")); aviso.setWordWrap(True); v.addWidget(aviso)
        tabla = QTableWidget(len(passwords), 3)
        tabla.setHorizontalHeaderLabels([importar.etiqueta_campo("login"), importar.etiqueta_campo("nombre"), t("imp_col_password")])
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); tabla.verticalHeader().setVisible(False)
        for i, fila in enumerate(passwords):
            for j, texto in enumerate(fila):
                tabla.setItem(i, j, QTableWidgetItem(texto))
        cabecera = tabla.horizontalHeader()
        cabecera.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        cabecera.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        v.addWidget(tabla)
        botones = QHBoxLayout()
        btn_guardar = QPushButton(t("imp_btn_guardar_passwords")); btn_cerrar = QPushButton(t("btn_cerrar"))
        def guardar():
            ruta, _ = QFileDialog.getSaveFileName(dlg, t("imp_btn_guardar_passwords"),
                                                  t("imp_nombre_passwords") + ".xlsx", "Excel (*.xlsx)")
            if ruta:
                if not ruta.lower().endswith(".xlsx"): ruta += ".xlsx"
                importar.exportar_passwords(ruta, passwords)
                QMessageBox.information(dlg, t("title_exito"), t("imp_msg_guardado").format(ruta=ruta))
        btn_guardar.clicked.connect(guardar); btn_cerrar.clicked.connect(dlg.accept)
        botones.addWidget(btn_guardar); botones.addStretch(); botones.addWidget(btn_cerrar)
        v.addLayout(botones)
        dlg.exec()
