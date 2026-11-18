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

"""
frecuencias.py — Frecuencias de los avisos recurrentes, en un solo sitio.

Cada frecuencia tiene una forma **canónica en español** (la que se guarda en la
base de datos y viaja a los móviles: «Mensual», «Cada 5 años»…), una clave de
traducción (`freq_*`) y cuánto se avanza de una vez a la siguiente. Los avisos
antiguos pueden tener guardado el texto en otro idioma («Monthly»): `canonica()`
lo entiende.

`avanzar(fecha, frecuencia)` da la siguiente fecha. Lo usan la pestaña de avisos,
el calendario, el panel y el servidor de los móviles (antes cada uno tenía su
copia). Sumar meses o años a un día que no existe en el mes de destino (31,
29 de febrero) cae en el último día de ese mes, igual que QDate.addMonths.

Python puro, sin Qt.
"""

import calendar
from datetime import date, timedelta

from .. import idiomas

# (forma canónica, clave de traducción, días, meses): uno de los dos es 0
_FRECUENCIAS = (
    ("Diario", "freq_diario", 1, 0),
    ("Semanal", "freq_semanal", 7, 0),
    ("Mensual", "freq_mensual", 0, 1),
    ("Trimestral", "freq_trimestral", 0, 3),
    ("Semestral", "freq_semestral", 0, 6),
    ("Anual", "freq_anual", 0, 12),
    ("Cada 2 años", "freq_cada_2_anios", 0, 24),
    ("Cada 3 años", "freq_cada_3_anios", 0, 36),
    ("Cada 4 años", "freq_cada_4_anios", 0, 48),
    ("Cada 5 años", "freq_cada_5_anios", 0, 60),
    ("Cada 10 años", "freq_cada_10_anios", 0, 120),
)
POR_DEFECTO = "Anual"
DIARIO = "Diario"
CLAVES = tuple(c for _, c, _, _ in _FRECUENCIAS)
CANONICAS = tuple(f for f, _, _, _ in _FRECUENCIAS)
# Las que las apps móviles antiguas no saben calcular (ver servidor: datos_para_movil)
NUEVAS = ("Cada 2 años", "Cada 3 años", "Cada 4 años", "Cada 5 años", "Cada 10 años")
# Orden del desplegable: de la más espaciada a la más frecuente
ORDEN_DESPLEGABLE = tuple(reversed(CANONICAS))

_POR_CANONICA = {f: (clave, dias, meses) for f, clave, dias, meses in _FRECUENCIAS}


def canonica(valor):
    """Forma canónica de una frecuencia guardada en cualquier idioma; vacío o
    desconocido -> POR_DEFECTO si está vacío, o el propio valor si no se reconoce."""
    if not valor:
        return POR_DEFECTO
    valor = str(valor).strip()
    if valor in _POR_CANONICA:
        return valor
    for f, clave, _, _ in _FRECUENCIAS:
        for traducciones in idiomas.TRADUCCIONES.values():
            if traducciones.get(clave) == valor:
                return f
    return valor


def conocida(valor):
    return canonica(valor) in _POR_CANONICA


def texto(valor):
    """La frecuencia en el idioma activo (o tal cual, si no se reconoce)."""
    f = canonica(valor)
    return idiomas.t(_POR_CANONICA[f][0]) if f in _POR_CANONICA else str(valor or "")


def opciones():
    """[(canónica, texto en el idioma activo)] en el orden del desplegable."""
    return [(f, texto(f)) for f in ORDEN_DESPLEGABLE]


def _sumar_meses(fecha, meses):
    total = fecha.month - 1 + meses
    anio, mes = fecha.year + total // 12, total % 12 + 1
    return date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def avanzar(fecha, valor):
    """La fecha siguiente a [fecha] (un datetime.date) con la frecuencia [valor].
    Una frecuencia desconocida devuelve la misma fecha (no avanza)."""
    f = canonica(valor)
    if f not in _POR_CANONICA:
        return fecha
    _, dias, meses = _POR_CANONICA[f]
    return fecha + timedelta(days=dias) if dias else _sumar_meses(fecha, meses)
