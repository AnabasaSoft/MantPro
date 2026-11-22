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

"""«🏬 Almacenes…» (sin Qt): la tabla de almacenes, sus textos (sede, ciclo de revisión) y lo que se hace con ellos
(alta, edición, activar/desactivar y borrar). Lo usan el diálogo del PC y MantPro Web; los datos están en
nucleo/almacenes.py.

Todo es solo de administradores y recibe quién lo hace (en la web no hay sesión del PC). Los errores son códigos
(ValueError); TEXTOS da la clave de traducción de cada uno."""

from .. import idiomas
from . import almacenes, sedes, usuarios

TEXTOS = {"sin_nombre": "alm_msg_sin_nombre", "nombre_repetido": "alm_msg_repetido",
          "es_principal": "alm_msg_principal", "en_uso": "alm_msg_en_uso", "mismo_almacen": "alm_msg_mismo",
          "cantidad_no_valida": "alm_msg_cantidad", "stock_insuficiente": "msg_stock_insuficiente",
          "material_no_existe": "alm_msg_no_existe", "solo_admin": "msg_solo_admin",
          "no_existe": "alm_err_no_existe", "sede_no_existe": "usr_err_sede_no_existe"}
CAMPOS = ("nombre", "sede_id", "comun", "direccion", "revision_ciclo", "revision_dia", "revision_articulos", "notas")


def texto_error(codigo):
    clave = TEXTOS.get(codigo)
    return idiomas.t(clave) if clave else codigo


def _admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def nombres_dias_semana():
    """Lunes … domingo en el idioma activo (0 = lunes)."""
    return [idiomas.t(f"dia_semana_{i}") for i in range(7)]


def nombres_ciclo():
    """[(ciclo, texto)] del desplegable «Revisión del almacén»."""
    return [(almacenes.CICLO_DIARIO, idiomas.t("alm_ciclo_diario")),
            (almacenes.CICLO_SEMANAL, idiomas.t("alm_ciclo_semanal")),
            (almacenes.CICLO_MENSUAL, idiomas.t("alm_ciclo_mensual"))]


def texto_ciclo(a):
    """Ciclo de revisión de un almacén en palabras: «Diaria», «Semanal (lunes)», «Mensual (día 15)»."""
    ciclo, dia, _n = almacenes.revision(a)
    if ciclo == almacenes.CICLO_SEMANAL:
        return idiomas.t("alm_ciclo_semanal_dia").format(dia=nombres_dias_semana()[dia].lower())
    if ciclo == almacenes.CICLO_MENSUAL:
        return idiomas.t("alm_ciclo_mensual_dia").format(dia=dia)
    return idiomas.t("alm_ciclo_diario")


def nombre_sede(a, nombres_sedes=None):
    """La sede del almacén, o «Común (todas las sedes)»."""
    if a.get("comun"):
        return idiomas.t("alm_comun")
    nombres_sedes = sedes.nombres() if nombres_sedes is None else nombres_sedes
    return nombres_sedes.get(sedes.efectiva(a.get("sede_id")), "")


def filas():
    """La tabla del PC: [{id, nombre_txt (⭐ el principal), sede_txt, estado_txt, revision_txt, activo, principal,
    ...los campos del almacén}]."""
    nombres_sedes = sedes.nombres()
    resultado = []
    for a in almacenes.listar(incluir_inactivos=True):
        revision = (texto_ciclo(a) if sedes.revision_activa(a["sede_id"])
                    else idiomas.t("alm_revision_desactivada"))
        resultado.append({**a, "nombre_txt": a["nombre"] + ("  ⭐" if a["principal"] else ""),
                          "sede_txt": nombre_sede(a, nombres_sedes), "revision_txt": revision,
                          "activo": bool(a["activo"]), "principal": bool(a["principal"]),
                          "estado_txt": idiomas.t("sede_activa") if a["activo"] else idiomas.t("sede_inactiva")})
    return resultado


def _almacen(almacen_id):
    a = almacenes.obtener(almacen_id) if almacen_id is not None else None
    if not a:
        raise ValueError("no_existe")
    return a


def _datos(datos):
    d = {c: datos.get(c) for c in CAMPOS}
    if not d.get("comun") and d.get("sede_id") is not None and not sedes.obtener(d["sede_id"]):
        raise ValueError("sede_no_existe")
    return d


def _resultado(err):
    if err:
        raise ValueError(err)


def crear(admin, datos):
    """Alta de un almacén con los campos de CAMPOS. Devuelve su id."""
    _admin(admin)
    nuevo, err = almacenes.crear(_datos(datos))
    _resultado(err)
    return nuevo


def editar(admin, almacen_id, datos):
    _admin(admin)
    _almacen(almacen_id)
    _resultado(almacenes.actualizar(almacen_id, _datos(datos)))


def alternar(admin, almacen_id):
    """✔️ Activar / 🚫 Desactivar. Devuelve si queda activo."""
    _admin(admin)
    a = _almacen(almacen_id)
    _resultado(almacenes.activar(almacen_id, not a["activo"]))
    return not a["activo"]


def borrar(admin, almacen_id):
    _admin(admin)
    _almacen(almacen_id)
    _resultado(almacenes.borrar(almacen_id))
