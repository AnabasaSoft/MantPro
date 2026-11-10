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

"""Sincronización automática con MantPro Cloud: subir y bajar los cambios cada pocos minutos."""

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox

from ..comun import tt
from ...nucleo import nube, sincro_nube

MINUTOS_SINCRONIZACION_NUBE = 10      # cada cuánto sube lo nuevo mientras MantPro está abierto
SEGUNDOS_PRIMERA_SINCRONIZACION = 60  # tras abrir MantPro (da tiempo a que cargue todo)
SEGUNDOS_REVISAR_RESULTADO = 3        # cada cuánto mira la ventana si ha terminado la sincronización de fondo


class AccionesNube:
    """Temporizador de la sincronización con MantPro Cloud (sube lo nuevo y baja lo de otros). Solo hace
    algo si este PC tiene sesión iniciada: sin ella MantPro funciona igual que siempre. La red va en un
    hilo aparte, así que nunca bloquea la ventana, y sin conexión no pasa nada: lo no subido queda en
    la cola y se sube la siguiente vez. No avisa de errores (el diálogo Herramientas → MantPro Cloud
    muestra el estado y deja sincronizar a mano), salvo de dos cosas: un stock que ha quedado negativo
    tras bajar movimientos de otros (recuento urgente) y que hace falta una decisión del usuario.
    El hilo de fondo nunca toca la interfaz: deja el resultado y es la ventana quien lo recoge."""

    def iniciar_sincronizacion_nube(self):
        """Se llama una vez, al crear la ventana."""
        self._hilo_nube = None
        self._resultado_nube = None
        self._aviso_decision_mostrado = False
        self.temporizador_resultado_nube = QTimer(self)
        self.temporizador_resultado_nube.timeout.connect(self._revisar_resultado_nube)
        self.temporizador_resultado_nube.start(SEGUNDOS_REVISAR_RESULTADO * 1000)
        self.temporizador_nube = QTimer(self)
        self.temporizador_nube.timeout.connect(self._tic_nube)
        self.temporizador_nube.start(MINUTOS_SINCRONIZACION_NUBE * 60 * 1000)
        QTimer.singleShot(SEGUNDOS_PRIMERA_SINCRONIZACION * 1000, self._tic_nube)

    def parar_sincronizacion_nube(self):
        for nombre in ("temporizador_nube", "temporizador_resultado_nube"):
            temporizador = getattr(self, nombre, None)
            if temporizador is not None:
                temporizador.stop()

    def _tic_nube(self):
        if nube.sesion() is None:
            return
        hilo = getattr(self, "_hilo_nube", None)
        if hilo is not None and hilo.is_alive():
            return
        self._hilo_nube = sincro_nube.lanzar_en_segundo_plano(al_terminar=self._guardar_resultado_nube)

    def _guardar_resultado_nube(self, resultado, error):
        """Lo llama el hilo de fondo: solo guarda el resultado (nada de tocar la interfaz desde aquí)."""
        self._resultado_nube = (resultado, error)

    def _revisar_resultado_nube(self):
        """En el hilo de la ventana: recoge el resultado de la sincronización de fondo."""
        recogido, self._resultado_nube = self._resultado_nube, None
        if recogido is None:
            return
        resultado, error = recogido
        if error in (sincro_nube.NUBE_CON_DATOS, sincro_nube.COPIA_RESTAURADA):
            if not self._aviso_decision_mostrado:        # una vez por sesión: no insistir cada 10 minutos
                self._aviso_decision_mostrado = True
                self.statusBar().showMessage(tt("msg_nube_necesita_decision",
                                                "MantPro Cloud necesita tu decisión: Herramientas → MantPro Cloud…"), 20000)
            return
        if not resultado:
            return
        if resultado.get("aplicados") or resultado.get("borrados"):
            self.refrescar_tras_nube()
        negativos = resultado.get("stock_negativo") or []
        if negativos:
            lista = "\n".join(f"• {x.get('nombre') or x.get('codigo')}: {x.get('stock'):g}" for x in negativos[:10])
            QMessageBox.warning(self, tt("title_nube", "MantPro Cloud"),
                                tt("msg_nube_stock_negativo", "Tras sincronizar, estos artículos han quedado con stock NEGATIVO. "
                                   "Haz un recuento urgente:\n\n{lista}").format(lista=lista))

    def refrescar_tras_nube(self):
        """Repinta la ventana con lo que ha llegado de la nube."""
        for nombre in ("refresh_all", "pintar_calendario", "update_calendar_list", "refresh_avisos", "refresh_todos", "refresh_stock"):
            funcion = getattr(self, nombre, None)
            if funcion is not None:
                try:
                    funcion()
                except Exception as ex:      # noqa: BLE001  (un repintado que falla no debe romper la sincronización)
                    print(f"Sincronización con la nube: no se pudo repintar ({nombre}: {ex})")
