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

# ==========================================
# SISTEMA DE IDIOMAS - MantPro (Escritorio)
# ==========================================
# Los textos de cada idioma viven en un JSON aparte dentro de esta carpeta
# (es.json, en.json, eu.json...), uno por idioma.
#
# Cómo añadir un idioma nuevo:
#   1. Copia idiomas/es.json a idiomas/<codigo>.json y tradúcelo.
#   2. Añade su entrada en IDIOMAS_DISPONIBLES.
#   3. Corre `python3 verificar_idiomas.py` para comprobar que no falta ninguna clave.
#   4. Ya aparece automáticamente en el menú Herramientas > Idioma.
#
# Cómo usar una clave nueva en el código:
#   - Añade la clave en idiomas/es.json (si falta en los demás, se
#     mostrará el texto en español como respaldo automático).
#   - Donde antes tenías texto literal, usa t("tu_clave").
#   - Al terminar, corre `python3 verificar_idiomas.py` para que rellene
#     automáticamente la clave que falte en el resto de idiomas.

import json
import os

IDIOMAS_DISPONIBLES = [
    ("es", "Español"),
    ("en", "English"),
    ("eu", "Euskara"),
]

_DIR_IDIOMAS = os.path.dirname(os.path.abspath(__file__))


def _cargar_traducciones():
    datos = {}
    for codigo, _nombre in IDIOMAS_DISPONIBLES:
        ruta = os.path.join(_DIR_IDIOMAS, f"{codigo}.json")
        with open(ruta, encoding="utf-8") as f:
            datos[codigo] = json.load(f)
    return datos


TRADUCCIONES = _cargar_traducciones()

# Idioma activo en memoria (se carga desde la BD al arrancar la app)
_idioma_actual = "es"


def set_idioma(codigo):
    """Establece el idioma activo en memoria (no toca la base de datos)."""
    global _idioma_actual
    if codigo in TRADUCCIONES:
        _idioma_actual = codigo
    else:
        _idioma_actual = "es"


def get_idioma():
    return _idioma_actual


def formato_fecha_localizada(fecha_iso):
    """Convierte una fecha ISO (YYYY-MM-DD) al formato corto propio del idioma activo:
    DD/MM/AAAA en general, pero AAAA/MM/DD en euskera (donde el orden va al revés)."""
    import datetime as _dt
    try:
        fecha_obj = _dt.datetime.strptime(fecha_iso, "%Y-%m-%d")
    except (ValueError, TypeError):
        return fecha_iso or ""
    if _idioma_actual == "eu":
        return fecha_obj.strftime("%Y/%m/%d")
    return fecha_obj.strftime("%d/%m/%Y")


def formato_fecha_corta_qt():
    """Patrón día/mes (sin año) para QDate.toString(), según el idioma activo."""
    return "MM/dd" if _idioma_actual == "eu" else "dd/MM"


def formato_fecha_corta_py():
    """Patrón día/mes (sin año) para datetime.strftime(), según el idioma activo."""
    return "%m/%d" if _idioma_actual == "eu" else "%d/%m"


def t(clave):
    """Devuelve el texto traducido para 'clave' en el idioma activo.
    Si falta en el idioma activo, cae a español. Si tampoco existe, devuelve la propia clave."""
    dic_actual = TRADUCCIONES.get(_idioma_actual, TRADUCCIONES["es"])
    if clave in dic_actual:
        return dic_actual[clave]
    return TRADUCCIONES["es"].get(clave, clave)


# --------------------------------------------------------------------
# NORMALIZADOR DE FRECUENCIAS DE AVISOS RECURRENTES
# --------------------------------------------------------------------
# Las avisos recurrentes guardan en la base de datos el TEXTO que se veía
# en el combo "Frecuencia de Repetición" en el momento de crear/editar el
# aviso (p.ej. "Anual" si la interfaz estaba en español, "Yearly" si estaba
# en inglés). Toda la lógica de cálculo de recurrencia compara ese texto
# contra los literales fijos en español ("Diario", "Semanal", ...), así que
# si un aviso se guardó en otro idioma, dejaba de reconocerse.
#
# Esta función traduce CUALQUIER valor guardado, en CUALQUIER idioma
# conocido, de vuelta a su forma canónica en español, para que las
# comparaciones `freq == "Anual"` etc. sigan funcionando pase lo que pase.
_CLAVES_FRECUENCIA = ["freq_diario", "freq_semanal", "freq_mensual", "freq_trimestral", "freq_semestral", "freq_anual"]

def normalizar_frecuencia(valor):
    """Dado un valor de frecuencia guardado (en cualquier idioma soportado),
    devuelve su forma canónica en español ('Diario', 'Semanal', 'Mensual',
    'Trimestral', 'Semestral' o 'Anual'). Si no se reconoce, se devuelve tal cual."""
    if not valor:
        return valor
    for clave in _CLAVES_FRECUENCIA:
        for idioma in TRADUCCIONES:
            if TRADUCCIONES[idioma].get(clave) == valor:
                return TRADUCCIONES["es"][clave]
    return valor
