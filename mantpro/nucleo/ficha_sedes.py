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

"""«🏢 Sedes…» (sin Qt): la tabla de sedes, sus textos y lo que se hace con ellas (alta, edición, festivos propios,
activar/desactivar y borrar). Lo usan el diálogo del PC y MantPro Web; los datos están en nucleo/sedes.py.

Todo es solo de administradores y recibe quién lo hace (en la web no hay sesión del PC). Los errores son códigos
(ValueError); TEXTOS da la clave de traducción de cada uno."""

from .. import idiomas
from . import festivos, sedes, usuarios

TEXTOS = {"sin_nombre": "sede_msg_sin_nombre", "nombre_repetido": "sede_msg_repetido",
          "es_principal": "sede_msg_principal", "en_uso": "sede_msg_en_uso", "con_almacenes": "sede_msg_con_almacenes", "solo_admin": "msg_solo_admin",
          "no_existe": "usr_err_sede_no_existe", "pais_no_valido": "title_seleccionar_pais",
          "provincia_no_valida": "title_seleccionar_provincia"}
CAMPOS = ("nombre", "tipo", "cif", "direccion", "contacto", "telefono", "email", "notas")


def texto_error(codigo):
    return idiomas.t(TEXTOS.get(codigo, "sede_msg_sin_nombre"))


def _admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def nombre_tipo(tipo):
    return idiomas.t("sede_tipo_cliente") if tipo == sedes.TIPO_CLIENTE else idiomas.t("sede_tipo_propia")


def texto_festivos(s):
    if not s.get("pais_iso"):
        return idiomas.t("sede_festivos_generales")
    return " / ".join(x for x in (s.get("pais_iso"), s.get("region_iso")) if x)


def filas():
    """La tabla del PC: [{id, nombre, nombre_txt (⭐ la principal), tipo, tipo_txt, cif, contacto, festivos_txt,
    activa, estado_txt, principal, ...los demás campos}], en el orden de sedes.listar."""
    resultado = []
    for s in sedes.listar(incluir_inactivas=True):
        resultado.append({**s, "nombre_txt": s["nombre"] + ("  ⭐" if s["principal"] else ""),
                          "tipo_txt": nombre_tipo(s["tipo"]), "cif": s.get("cif") or "",
                          "contacto": s.get("contacto") or "", "festivos_txt": texto_festivos(s),
                          "activa": bool(s["activa"]), "principal": bool(s["principal"]),
                          "estado_txt": idiomas.t("sede_activa") if s["activa"] else idiomas.t("sede_inactiva")})
    return resultado


def _sede(sede_id):
    s = sedes.obtener(sede_id) if sede_id is not None else None
    if not s:
        raise ValueError("no_existe")
    return s


def _resultado(err):
    if err:
        raise ValueError(err)


def crear(admin, datos):
    """Alta de una sede con los campos de CAMPOS. Devuelve su id."""
    _admin(admin)
    nuevo, err = sedes.crear({c: datos.get(c) for c in CAMPOS})
    _resultado(err)
    return nuevo


def editar(admin, sede_id, datos):
    _admin(admin)
    _sede(sede_id)
    _resultado(sedes.actualizar(sede_id, {c: datos.get(c) for c in CAMPOS}))


def alternar(admin, sede_id):
    """✔️ Activar / 🚫 Desactivar. Devuelve si queda activa."""
    _admin(admin)
    s = _sede(sede_id)
    _resultado(sedes.activar(sede_id, not s["activa"]))
    return not s["activa"]


def borrar(admin, sede_id):
    _admin(admin)
    _sede(sede_id)
    _resultado(sedes.borrar(sede_id))


def fijar_festivos(admin, sede_id, pais_iso=None, region_iso=None):
    """«📅 Festivos…»: sin país, los generales de la empresa; con país, los suyos (en España, con su provincia, de la
    que sale la comunidad). El país tiene que ser de la lista de países con festivos."""
    _admin(admin)
    _sede(sede_id)
    pais_iso = (pais_iso or "").strip() or None
    comunidad = None
    if pais_iso:
        if pais_iso not in {iso for _n, iso in festivos.paises()}:
            raise ValueError("pais_no_valido")
        if pais_iso == "ES":
            _nombre, comunidad = festivos.provincia_de(region_iso)
            if comunidad is None:
                raise ValueError("provincia_no_valida")
        else:
            region_iso = None
    sedes.fijar_festivos(sede_id, pais_iso, region_iso if pais_iso else None, comunidad)
