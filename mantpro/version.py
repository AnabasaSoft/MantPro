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

"""Versión de la app de escritorio. Al compilar en GitHub, APP_VERSION se sustituye
por la del tag (ver .github/workflows/build_desktop.yml); ejecutando "python main.py"
se queda como "Dev Version"."""

# Al compilar en GitHub se sustituye por la versión del tag (ver build_desktop.yml);
# ejecutando "python main.py" se queda así.
APP_VERSION = "Dev Version"

# Si la app la ha instalado el gestor de paquetes de la distribución (p. ej.
# el paquete de OBS para openSUSE, ver empaquetado/obs/mantpro.spec), su
# nombre: entonces las actualizaciones llegan por él y no se buscan en GitHub.
GESTOR_PAQUETES = None


REPO_OWNER = "AnabasaSoft"


REPO_NAME = "MantPro"
