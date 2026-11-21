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

"""Festivos oficiales (sin Qt): los de date.nager.at para el país y la región de la empresa o de una sede, guardados
en una caché por país y año en la carpeta de datos. Lo usan el calendario del PC (interfaz/festivos.GestorFestivos)
y MantPro Web. Sin conexión y sin caché, no hay festivos (nunca falla)."""

import json
import os
import time

from .rutas import DATA_DIR
from .seguridad import escribir_atomico

API = "https://date.nager.at/api/v3/publicholidays/{anio}/{pais}"
ESPERA = 10                    # segundos como mucho para descargarlos (la web no se puede quedar colgada)
REINTENTO = 3600               # tras un fallo, no se vuelve a intentar en este tiempo (segundos)
_fallos = {}                   # (país, año) -> cuándo falló la última descarga


def config(db, sede=None):
    """(país, provincia, comunidad) ISO: los de [sede] (dict de nucleo/sedes) si tiene país propio; si no, los de la
    configuración (por defecto España/Bizkaia, para no romper instalaciones antiguas)."""
    if sede and sede.get("pais_iso"):
        return sede["pais_iso"], sede.get("region_iso") or "", sede.get("parent_iso") or ""
    pais = db.get_config("country_iso") or "ES"
    por_defecto = ("ES-BI", "ES-PV") if pais == "ES" else ("", "")
    return pais, db.get_config("region_iso") or por_defecto[0], db.get_config("parent_iso") or por_defecto[1]


def archivo_cache(pais, anio):
    return os.path.join(DATA_DIR, f"festivos_cache_{pais}_{anio}.json")


def cargar_cache(pais, anio):
    try:
        with open(archivo_cache(pais, anio), "r") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def descargar(pais, anio):
    """Los descarga y los guarda en la caché; [] si no se puede (y durante REINTENTO no se vuelve a probar)."""
    if time.monotonic() - _fallos.get((pais, anio), -REINTENTO) < REINTENTO:
        return []
    try:
        import requests
        r = requests.get(API.format(anio=anio, pais=pais), timeout=ESPERA)
        if r.status_code == 200:
            datos = r.json()
            escribir_atomico(archivo_cache(pais, anio), json.dumps(datos))
            return datos
    except Exception:                    # noqa: BLE001  (sin conexión: sin festivos)
        pass
    _fallos[(pais, anio)] = time.monotonic()
    return []


def limpiar_cache(pais, anio):
    try:
        os.remove(archivo_cache(pais, anio))
    except OSError:
        pass


def de_la_region(datos, provincia, comunidad):
    """Las fechas 'AAAA-MM-DD' de [datos] que valen para la región: las nacionales y las de la provincia o la
    comunidad (un país sin desglose: solo las nacionales)."""
    fechas = set()
    for i in datos or []:
        condados = i.get("counties")
        if condados is None or (comunidad and comunidad in condados) or (provincia and provincia in condados):
            if i.get("date"):
                fechas.add(i["date"])
    return fechas


def fechas(db, anio, sede=None):
    """Conjunto de fechas 'AAAA-MM-DD' festivas de [anio] para la empresa o [sede] (de la caché o descargadas)."""
    pais, provincia, comunidad = config(db, sede)
    datos = cargar_cache(pais, anio)
    if not datos:
        datos = descargar(pais, anio)
    return de_la_region(datos, provincia, comunidad)
