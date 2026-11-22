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

"""Dos ajustes de Herramientas (sin Qt), para el PC y MantPro Web:

- «🌍 País y región»: el país de los festivos de la empresa y, en España, la provincia (de la que sale la comunidad).
- «🗑️ Tiempo máximo de guardado de trabajos…»: la fecha de corte (conservar los últimos N años, meses o días) y el
  borrado de los trabajos anteriores con sus fotos (las que ya no use nada más).

Lo que cambia datos es solo de administradores y recibe quién lo hace. La copia previa al borrado la hace quien
llama (el PC en su carpeta de copias, la web en la nube). Los errores son códigos (ValueError); TEXTOS da la clave de
traducción de cada uno."""

import os
import re
from datetime import date

from .. import idiomas
from . import festivos, usuarios
from .fotos import en_uso as fotos_en_uso, fotos_galeria

TEXTOS = {"solo_admin": "msg_solo_admin", "pais_no_valido": "title_seleccionar_pais",
          "provincia_no_valida": "title_seleccionar_provincia", "cantidad": "lbl_tiempo_guardado"}
UNIDADES = ("anos", "meses", "dias")
CANTIDAD_MAXIMA = 999


def texto_error(codigo):
    return idiomas.t(TEXTOS.get(codigo, "msg_solo_admin"))


def _admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


# ------------------------------------------------------------ 🌍 País y región

def pais_region(db):
    """(país ISO, provincia ISO) de los festivos de la empresa (por defecto España/Bizkaia, como el PC)."""
    pais, provincia, _comunidad = festivos.config(db)
    return pais, provincia


def fijar_pais_region(admin, db, pais, provincia=None):
    """Guarda el país (de la lista de países con festivos) y, en España, la provincia y su comunidad; fuera de
    España, sin región (solo los festivos nacionales). Borra la caché de festivos de este año para que se bajen los
    nuevos. Devuelve (clave del mensaje del PC, valores para su format)."""
    _admin(admin)
    nombres = dict((iso, nombre) for nombre, iso in festivos.paises())
    if pais not in nombres:
        raise ValueError("pais_no_valido")
    comunidad = None
    if pais == "ES":
        nombre_provincia, comunidad = festivos.provincia_de(provincia)
        if comunidad is None:
            raise ValueError("provincia_no_valida")
    db.set_config("country_iso", pais)
    db.set_config("region_iso", provincia if pais == "ES" else "")
    db.set_config("parent_iso", comunidad if pais == "ES" else "")
    festivos.limpiar_cache(pais, date.today().year)
    if pais == "ES":
        return "msg_region_cambiada", {"zona": nombre_provincia, "parent": comunidad, "prov": provincia}
    return "msg_pais_cambiado", {"pais": nombres[pais]}


# ------------------------------------------------------------ 🗑️ Tiempo máximo de guardado

def _restar_meses(dia, meses):
    total = dia.year * 12 + dia.month - 1 - meses
    anio, mes = divmod(total, 12)
    mes += 1
    # El mismo día del mes, o el último si el mes es más corto (como QDate.addMonths)
    import calendar
    return date(anio, mes, min(dia.day, calendar.monthrange(anio, mes)[1]))


def fecha_corte(cantidad, unidad, hoy=None):
    """Primer día que se conserva (se borra todo lo anterior): hoy menos [cantidad] años, meses o días."""
    hoy = hoy or date.today()
    if not isinstance(cantidad, int) or not 1 <= cantidad <= CANTIDAD_MAXIMA or unidad not in UNIDADES:
        raise ValueError("cantidad")
    if unidad == "anos":
        return _restar_meses(hoy, 12 * cantidad)
    if unidad == "meses":
        return _restar_meses(hoy, cantidad)
    from datetime import timedelta
    return hoy - timedelta(days=cantidad)


def nombres_unidad():
    return [("anos", idiomas.t("unidad_anos")), ("meses", idiomas.t("unidad_meses")), ("dias", idiomas.t("unidad_dias"))]


def trabajos_anteriores(db, corte):
    """[(id, fecha, descripción)] de los trabajos anteriores a [corte] ('AAAA-MM-DD'), por fecha."""
    conn = db.conectar()
    try:
        return conn.execute("SELECT id, fecha, descripcion FROM tareas WHERE fecha < ? ORDER BY fecha", (corte,)).fetchall()
    finally:
        conn.close()


def resumen_borrado(db, corte):
    """Lo que borraría: {n, desde, hasta} (fechas del idioma), o None si no hay nada anterior a [corte]."""
    filas = trabajos_anteriores(db, corte)
    if not filas:
        return None
    return {"n": len(filas), "desde": idiomas.formato_fecha_localizada(filas[0][1]),
            "hasta": idiomas.formato_fecha_localizada(filas[-1][1])}


def borrar_anteriores(admin, db, corte, carpeta_fotos):
    """Borra del historial los trabajos anteriores a [corte] y, de la carpeta de fotos, las suyas que ya no use nada
    más. Lo apunta en el registro de cambios. Devuelve (trabajos borrados, fotos borradas)."""
    _admin(admin)
    filas = trabajos_anteriores(db, corte)
    if not filas:
        return 0, 0
    candidatas = set()
    for _id, _fecha, desc in filas:
        for m in re.findall(r"\[FOTO(?:_DESPUES)?:\s*(.*?)\]", desc or ""):
            candidatas.add(m.split("]")[0].strip())
        candidatas.update(fotos_galeria(desc))
    conn = db.conectar()
    try:
        borrados = conn.execute("DELETE FROM tareas WHERE fecha < ?", (corte,)).rowcount
        conn.commit()
    finally:
        conn.close()
    usuarios.registrar_auditoria(None, None, "borrar",
                                 f"Borrado por tiempo máximo de guardado: {borrados} registros del {filas[0][1]} al {filas[-1][1]}")
    usadas = fotos_en_uso(db)
    fotos_borradas = 0
    for nombre in candidatas - usadas:
        ruta = os.path.join(carpeta_fotos, nombre) if nombre and os.sep not in nombre and nombre not in (".", "..") else None
        if ruta and os.path.isfile(ruta):
            try:
                os.remove(ruta)
                fotos_borradas += 1
            except OSError:
                pass
    return borrados, fotos_borradas

