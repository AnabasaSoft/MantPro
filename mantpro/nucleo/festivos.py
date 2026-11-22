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


# Provincias de España (para los festivos de comunidad y provincia): nombre -> ISO de la provincia y de su comunidad
PROVINCIAS = {
    "A Coruña": {"iso": "ES-C", "parent": "ES-GA"},
    "Álava/Araba": {"iso": "ES-VI", "parent": "ES-PV"},
    "Albacete": {"iso": "ES-AB", "parent": "ES-CM"},
    "Alicante": {"iso": "ES-A", "parent": "ES-VC"},
    "Almería": {"iso": "ES-AL", "parent": "ES-AN"},
    "Asturias": {"iso": "ES-O", "parent": "ES-AS"},
    "Ávila": {"iso": "ES-AV", "parent": "ES-CL"},
    "Badajoz": {"iso": "ES-BA", "parent": "ES-EX"},
    "Baleares": {"iso": "ES-PM", "parent": "ES-IB"},
    "Barcelona": {"iso": "ES-B", "parent": "ES-CT"},
    "Bizkaia": {"iso": "ES-BI", "parent": "ES-PV"},
    "Burgos": {"iso": "ES-BU", "parent": "ES-CL"},
    "Cáceres": {"iso": "ES-CC", "parent": "ES-EX"},
    "Cádiz": {"iso": "ES-CA", "parent": "ES-AN"},
    "Cantabria": {"iso": "ES-S", "parent": "ES-CB"},
    "Castellón": {"iso": "ES-CS", "parent": "ES-VC"},
    "Ceuta": {"iso": "ES-CE", "parent": "ES-CE"},
    "Ciudad Real": {"iso": "ES-CR", "parent": "ES-CM"},
    "Córdoba": {"iso": "ES-CO", "parent": "ES-AN"},
    "Cuenca": {"iso": "ES-CU", "parent": "ES-CM"},
    "Gipuzkoa": {"iso": "ES-SS", "parent": "ES-PV"},
    "Girona": {"iso": "ES-GI", "parent": "ES-CT"},
    "Granada": {"iso": "ES-GR", "parent": "ES-AN"},
    "Guadalajara": {"iso": "ES-GU", "parent": "ES-CM"},
    "Huelva": {"iso": "ES-H", "parent": "ES-AN"},
    "Huesca": {"iso": "ES-HU", "parent": "ES-AR"},
    "Jaén": {"iso": "ES-J", "parent": "ES-AN"},
    "La Rioja": {"iso": "ES-LO", "parent": "ES-RI"},
    "Las Palmas": {"iso": "ES-GC", "parent": "ES-CN"},
    "León": {"iso": "ES-LE", "parent": "ES-CL"},
    "Lleida": {"iso": "ES-L", "parent": "ES-CT"},
    "Lugo": {"iso": "ES-LU", "parent": "ES-GA"},
    "Madrid": {"iso": "ES-M", "parent": "ES-MD"},
    "Málaga": {"iso": "ES-MA", "parent": "ES-AN"},
    "Melilla": {"iso": "ES-ML", "parent": "ES-ML"},
    "Murcia": {"iso": "ES-MU", "parent": "ES-MC"},
    "Navarra": {"iso": "ES-NA", "parent": "ES-NC"},
    "Ourense": {"iso": "ES-OR", "parent": "ES-GA"},
    "Palencia": {"iso": "ES-P", "parent": "ES-CL"},
    "Pontevedra": {"iso": "ES-PO", "parent": "ES-GA"},
    "Salamanca": {"iso": "ES-SA", "parent": "ES-CL"},
    "Santa Cruz de Tenerife": {"iso": "ES-TF", "parent": "ES-CN"},
    "Segovia": {"iso": "ES-SG", "parent": "ES-CL"},
    "Sevilla": {"iso": "ES-SE", "parent": "ES-AN"},
    "Soria": {"iso": "ES-SO", "parent": "ES-CL"},
    "Tarragona": {"iso": "ES-T", "parent": "ES-CT"},
    "Teruel": {"iso": "ES-TE", "parent": "ES-AR"},
    "Toledo": {"iso": "ES-TO", "parent": "ES-CM"},
    "Valencia": {"iso": "ES-V", "parent": "ES-VC"},
    "Valladolid": {"iso": "ES-VA", "parent": "ES-CL"},
    "Zamora": {"iso": "ES-ZA", "parent": "ES-CL"},
    "Zaragoza": {"iso": "ES-Z", "parent": "ES-AR"}
}

API_PAISES = "https://date.nager.at/api/v3/AvailableCountries"


def paises():
    """[(nombre, ISO)] de los países con festivos, por nombre. Se descargan una vez y se guardan en la caché; sin
    conexión ni caché, solo España."""
    archivo = os.path.join(DATA_DIR, "paises_cache.json")
    datos = None
    try:
        with open(archivo, "r") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        datos = None
    if not datos and time.monotonic() - _fallos.get("paises", -REINTENTO) >= REINTENTO:
        try:
            import requests
            r = requests.get(API_PAISES, timeout=ESPERA)
            if r.status_code == 200:
                datos = r.json()
                escribir_atomico(archivo, json.dumps(datos))
        except Exception:                # noqa: BLE001  (sin conexión: la lista mínima)
            datos = None
        if not datos:
            _fallos["paises"] = time.monotonic()
    if not datos:
        datos = [{"countryCode": "ES", "name": "Spain"}]
    return sorted(((d["name"], d["countryCode"]) for d in datos if d.get("name") and d.get("countryCode")),
                  key=lambda x: x[0])


def provincia_de(region_iso):
    """(nombre, ISO de la comunidad) de una provincia por su ISO, o (None, None)."""
    for nombre, datos in PROVINCIAS.items():
        if datos["iso"] == region_iso:
            return nombre, datos["parent"]
    return None, None


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


def fechas(db, anio, sede=None, descargar_si_falta=True):
    """Conjunto de fechas 'AAAA-MM-DD' festivas de [anio] para la empresa o [sede] (de la caché o descargadas;
    con [descargar_si_falta] False, solo de la caché, sin ir a internet)."""
    pais, provincia, comunidad = config(db, sede)
    datos = cargar_cache(pais, anio)
    if not datos and descargar_si_falta:
        datos = descargar(pais, anio)
    return de_la_region(datos, provincia, comunidad)
