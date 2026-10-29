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

"""Festivos por país y región."""

import requests
import json
import os
from datetime import datetime
from PyQt6.QtCore import QDate

from ..nucleo.rutas import DATA_DIR

# ==========================================
# DATOS GLOBALES: PROVINCIAS
# ==========================================
PROVINCIAS_ESPAÑA = {
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


class GestorFestivos:
    def __init__(self, db_instance):
        self.db = db_instance
        self.year = datetime.now().year

    def obtener_config_pais(self):
        # Por defecto España, para no romper instalaciones existentes
        return self.db.get_config("country_iso") or "ES"

    def obtener_config_region(self):
        pais = self.obtener_config_pais()
        # Si no hay región guardada y el país es España, mantenemos el valor por defecto histórico (Bizkaia)
        default_prov = "ES-BI" if pais == "ES" else ""
        default_com = "ES-PV" if pais == "ES" else ""
        iso_prov = self.db.get_config("region_iso") or default_prov
        iso_com = self.db.get_config("parent_iso") or default_com
        return iso_prov, iso_com

    def _archivo_cache(self):
        pais = self.obtener_config_pais()
        return os.path.join(DATA_DIR, f"festivos_cache_{pais}_{self.year}.json")

    def _url_api(self):
        pais = self.obtener_config_pais()
        return f"https://date.nager.at/api/v3/publicholidays/{self.year}/{pais}"

    def obtener_festivos(self):
        datos = self.cargar_cache()
        if not datos: datos = self.descargar_festivos()

        l = []
        iso_prov, iso_com = self.obtener_config_region()

        if datos:
            for i in datos:
                counties = i.get('counties')
                # Si no hay provincia/región configurada (país sin desglose), solo festivos nacionales (counties=None)
                if counties is None or (iso_com and iso_com in counties) or (iso_prov and iso_prov in counties):
                    l.append(QDate.fromString(i.get('date'),"yyyy-MM-dd"))
        return l

    def descargar_festivos(self):
        try:
            r = requests.get(self._url_api())
            if r.status_code == 200:
                with open(self._archivo_cache(), 'w') as f: json.dump(r.json(), f)
                return r.json()
        except: return []
        return []

    def cargar_cache(self):
        archivo = self._archivo_cache()
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r') as f: return json.load(f)
            except: return None

        return None

    def obtener_paises_disponibles(self):
        """Devuelve una lista de tuplas (nombre, codigo_iso) de los países soportados por la API, cacheada en disco."""
        archivo = os.path.join(DATA_DIR, "paises_cache.json")
        datos = None
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r') as f: datos = json.load(f)
            except: datos = None
        if not datos:
            try:
                r = requests.get("https://date.nager.at/api/v3/AvailableCountries")
                if r.status_code == 200:
                    datos = r.json()
                    with open(archivo, 'w') as f: json.dump(datos, f)
            except:
                datos = None
        if not datos:
            # Fallback mínimo por si no hay conexión y tampoco hay caché todavía
            datos = [{"countryCode": "ES", "name": "Spain"}]
        return sorted([(d["name"], d["countryCode"]) for d in datos], key=lambda x: x[0])

    def limpiar_cache(self):
        archivo = self._archivo_cache()
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
            except: pass
