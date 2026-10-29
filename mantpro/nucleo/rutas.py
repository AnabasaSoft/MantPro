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

"""Carpeta de datos de la aplicación (bases de datos, fotos, copias)."""

import sys
import os

def obtener_ruta_datos():
    """
    Determina dónde leer/escribir datos.
    PRIORIDAD 1: Carpeta actual (Modo desarrollo/Portable). Si existe 'mantenimiento.db' aquí, se usa esta.
    PRIORIDAD 2: Carpeta de sistema (Modo Instalación/AUR). ~/.local/share/MantPro
    """
    cwd = os.path.abspath(".")
    db_local = os.path.join(cwd, "mantenimiento.db")

    # Si ya existe la BD en la carpeta actual, nos quedamos aquí (tu caso actual)
    if os.path.exists(db_local):
        return cwd

    # Si no, usamos la ruta estándar del sistema operativo
    nombre_app = "MantPro"
    if sys.platform == "win32":
        base_dir = os.getenv("APPDATA")
    else:
        # Linux estándar (XDG_DATA_HOME)
        base_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    ruta_sistema = os.path.join(base_dir, nombre_app)

    # Crear la carpeta de sistema si no existe (importante para la primera ejecución)
    if not os.path.exists(ruta_sistema):
        try:
            os.makedirs(ruta_sistema)
        except OSError as e:
            print(f"Error creando directorio de datos: {e}")
            # Fallback al directorio local si falla (ej. portable)
            return os.path.abspath(".")

    return ruta_sistema


# Variable global que decide dónde se guarda TODO
DATA_DIR = obtener_ruta_datos()
