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

"""Varias sedes en la ventana principal: el selector «Sede» (a la derecha de la barra de menús,
solo con más de una sede activa), la sede con la que se filtran las pestañas y
la que llevan los registros nuevos, y Herramientas → Sedes."""

from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import QSettings, Qt

from ..comun import tt
from ...nucleo import sedes, usuarios

CLAVE_AJUSTE = "sede_actual"     # en QSettings: cada PC (y usuario del sistema) recuerda la suya


class AccionesSedes:
    """Mixin de MaintenanceApp (usa self.tabs, self.refresh_all...)."""

    def crear_selector_sede(self):
        """Crea el selector y lo pone en la esquina de las pestañas. Se llama una vez."""
        caja = QWidget()
        h = QHBoxLayout(caja)
        h.setContentsMargins(0, 0, 4, 0)
        self.lbl_sede = QLabel()
        self.combo_sede = QComboBox()
        self.combo_sede.setMinimumWidth(180)
        h.addWidget(self.lbl_sede)
        h.addWidget(self.combo_sede)
        self.caja_sede = caja
        # En la esquina de la barra de menús: en la de pestañas quitaba sitio y las pestañas no cabían
        self.menuBar().setCornerWidget(caja, Qt.Corner.TopRightCorner)
        self.combo_sede.currentIndexChanged.connect(self._al_elegir_sede)
        self.refrescar_selector_sede()

    def refrescar_selector_sede(self):
        """Rellena el selector (tras crear/cambiar sedes o cambiar de idioma) y lo oculta
        si solo hay una sede activa. Conserva la elegida si sigue activa."""
        if not hasattr(self, "combo_sede"):
            return
        self.lbl_sede.setText(tt("sede_lbl_selector", "🏢 Sede:"))
        guardada = QSettings("MyCompany", "MantenimientoApp").value(CLAVE_AJUSTE, "")
        self.combo_sede.blockSignals(True)
        self.combo_sede.clear()
        self.combo_sede.addItem(tt("sede_todas", "Todas las sedes"), None)
        for s in sedes.listar():
            self.combo_sede.addItem(s["nombre"], s["id"])
        indice = 0
        if guardada not in ("", None):
            try:
                encontrado = self.combo_sede.findData(int(guardada))
                indice = max(0, encontrado)
            except (TypeError, ValueError):
                indice = 0
        self.combo_sede.setCurrentIndex(indice)
        self.combo_sede.blockSignals(False)
        self.caja_sede.setVisible(sedes.hay_varias())

    def _al_elegir_sede(self, _indice):
        valor = self.combo_sede.currentData()
        QSettings("MyCompany", "MantenimientoApp").setValue(CLAVE_AJUSTE, "" if valor is None else str(valor))
        self.refrescar_por_sede()

    def refrescar_por_sede(self):
        """Vuelve a pintar todo lo que depende de la sede elegida."""
        if hasattr(self, "_cargar_almacenes_stock"):   # Stock: los almacenes que se ven desde la sede
            self._cargar_almacenes_stock(cambio_de_sede=True)
        self.refresh_all()
        if hasattr(self, "combo_maquina_entry"):     # Registrar: solo las máquinas de la sede
            from ..comun import _poblar_combo_maquinas
            _poblar_combo_maquinas(self.combo_maquina_entry, self.combo_maquina_entry.currentData(),
                                   sede=self.sede_filtro())

    def sede_filtro(self):
        """Sede con la que se filtran las pestañas (None = todas). Con una sola sede, None."""
        if not hasattr(self, "combo_sede") or not sedes.hay_varias():
            return None
        return self.combo_sede.currentData()

    def sede_para_nuevo(self):
        """Sede de lo que se crea ahora sin máquina (pendientes, avisos, trabajos):
        la elegida en el selector o, con «Todas», la principal (None)."""
        return self.sede_filtro()

    def gestionar_almacenes(self):
        """Herramientas → Almacenes (solo administradores)."""
        if not usuarios.es_admin():
            return
        from ..dialogos.almacenes import DialogoAlmacenes
        d = DialogoAlmacenes(self)
        d.exec()
        if d.cambiado:
            self.refrescar_por_sede()

    def gestionar_sedes(self):
        """Herramientas → Sedes (solo administradores)."""
        if not usuarios.es_admin():
            return
        from ..dialogos.sedes import DialogoSedes
        d = DialogoSedes(self)
        d.exec()
        if d.cambiado:
            self.refrescar_selector_sede()
            self.refrescar_por_sede()
