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

"""Sustitutos mínimos de `QThread` y `pyqtSignal` para ejecutar el servidor de móviles SIN Qt.

MantPro Cloud usa el mismo código del servidor de móviles del PC (`interfaz/servidor.py`) en un
servidor sin escritorio, donde PyQt6 no está instalado. Allí solo se usa la aplicación Flask
(`servidor.app`): las señales no tienen a nadie que las escuche, así que `emit` no hace nada."""


class pyqtSignal:
    """Señal que no avisa a nadie (en la nube no hay ventana que la reciba)."""

    def __init__(self, *tipos):
        self.tipos = tipos

    def emit(self, *args):
        pass

    def connect(self, *args):
        pass

    def disconnect(self, *args):
        pass


class QThread:
    """Base vacía: el servidor en la nube no arranca el hilo, solo usa `app`."""

    def __init__(self, *args, **kwargs):
        pass

    def start(self, *args, **kwargs):
        raise RuntimeError("Sin Qt no se puede arrancar el hilo del servidor: usa su atributo «app» con un servidor WSGI.")
