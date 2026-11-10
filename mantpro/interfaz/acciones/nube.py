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

"""Sincronización automática con MantPro Cloud: subir los cambios cada pocos minutos."""

from PyQt6.QtCore import QTimer

from ...nucleo import nube, sincro_nube

MINUTOS_SINCRONIZACION_NUBE = 10      # cada cuánto sube lo nuevo mientras MantPro está abierto
SEGUNDOS_PRIMERA_SINCRONIZACION = 60  # tras abrir MantPro (da tiempo a que cargue todo)


class AccionesNube:
    """Temporizador de la subida a MantPro Cloud. Solo hace algo si este PC tiene sesión
    iniciada: sin ella MantPro funciona igual que siempre. La red va en un hilo aparte,
    así que nunca bloquea la ventana, y sin conexión no pasa nada: lo no subido queda
    en la cola y se sube la siguiente vez. No avisa de errores (el diálogo
    Herramientas → MantPro Cloud muestra el estado y deja sincronizar a mano)."""

    def iniciar_sincronizacion_nube(self):
        """Se llama una vez, al crear la ventana."""
        self._hilo_nube = None
        self.temporizador_nube = QTimer(self)
        self.temporizador_nube.timeout.connect(self._tic_nube)
        self.temporizador_nube.start(MINUTOS_SINCRONIZACION_NUBE * 60 * 1000)
        QTimer.singleShot(SEGUNDOS_PRIMERA_SINCRONIZACION * 1000, self._tic_nube)

    def parar_sincronizacion_nube(self):
        temporizador = getattr(self, "temporizador_nube", None)
        if temporizador is not None:
            temporizador.stop()

    def _tic_nube(self):
        if nube.sesion() is None:
            return
        hilo = getattr(self, "_hilo_nube", None)
        if hilo is not None and hilo.is_alive():
            return
        self._hilo_nube = sincro_nube.lanzar_en_segundo_plano()
