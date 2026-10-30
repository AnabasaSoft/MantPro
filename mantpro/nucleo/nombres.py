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

"""
nombres.py — Comparación de nombres para avisar de máquinas o artículos
repetidos sin querer («Extractor de finos» / «Extracción de finos»).

La app MantPro Stock hace exactamente el mismo cálculo en Dart
(mantpro_stock_app/lib/nombres.dart): si se cambia aquí, hay que cambiarlo allí.
"""

import re
import unicodedata

# Parecido mínimo (0 a 1) para avisar. Con 0,82 «Extractor de finos» /
# «Extracción de finos» (0,84) avisa, y «Grapa 22mm una pata» / «Grapa 22mm
# dos patas» (0,80) no.
UMBRAL_PARECIDO = 0.82


def normalizar(texto):
    """Minúsculas, sin tildes y con los espacios juntados."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", (texto or "").lower())
                         if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.split())


def _distancia(a, b):
    """Distancia de Levenshtein (nº de letras a cambiar, quitar o poner)."""
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        actual = [i]
        for j, cb in enumerate(b, 1):
            actual.append(min(anterior[j] + 1, actual[j - 1] + 1, anterior[j - 1] + (ca != cb)))
        anterior = actual
    return anterior[-1]


def son_parecidos(a, b, umbral=UMBRAL_PARECIDO):
    """True si los dos nombres son iguales o muy parecidos. No cuenta como
    parecido lo que solo cambia en los números («Lora 1» / «Lora 2»,
    «Grapa 8mm» / «Grapa 16mm»)."""
    a, b = normalizar(a), normalizar(b)
    if not a or not b:
        return False
    if a == b:
        return True
    if re.findall(r"\d+", a) != re.findall(r"\d+", b):
        return False
    return 1 - _distancia(a, b) / max(len(a), len(b)) >= umbral
