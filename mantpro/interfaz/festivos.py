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

"""Festivos por país y región."""

import os
from datetime import datetime
from PyQt6.QtCore import QDate

from ..nucleo import festivos as _festivos
from ..nucleo.rutas import DATA_DIR

# ==========================================
# DATOS GLOBALES: PROVINCIAS
# ==========================================
# La lista está en el núcleo (la comparte con MantPro Web)
PROVINCIAS_ESPAÑA = _festivos.PROVINCIAS


class GestorFestivos:
    def __init__(self, db_instance):
        self.db = db_instance
        self.year = datetime.now().year
        # Sede elegida en la ventana (dict de nucleo/sedes): si tiene región propia, manda la suya
        self.sede = None

    def _de_sede(self):
        return self.sede if self.sede and self.sede.get("pais_iso") else None

    def obtener_config_pais(self):
        s = self._de_sede()
        if s:
            return s["pais_iso"]
        # Por defecto España, para no romper instalaciones existentes
        return self.db.get_config("country_iso") or "ES"

    def obtener_config_region(self):
        s = self._de_sede()
        if s:
            return s.get("region_iso") or "", s.get("parent_iso") or ""
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
        """Los festivos de este año para el país y la región configurados (lo hace nucleo/festivos.py, igual que
        MantPro Web)."""
        provincia, comunidad = self.obtener_config_region()
        datos = self.cargar_cache() or self.descargar_festivos()
        return [QDate.fromString(f, "yyyy-MM-dd") for f in sorted(_festivos.de_la_region(datos, provincia, comunidad))]

    def descargar_festivos(self):
        return _festivos.descargar(self.obtener_config_pais(), self.year)

    def cargar_cache(self):
        return _festivos.cargar_cache(self.obtener_config_pais(), self.year)

    def obtener_paises_disponibles(self):
        """Lista de tuplas (nombre, código ISO) de los países con festivos (nucleo/festivos.py, igual que la web)."""
        return _festivos.paises()

    def limpiar_cache(self):
        archivo = self._archivo_cache()
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
            except: pass
