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

"""«☑️ Listas de comprobación…» (sin Qt): las plantillas, sus textos y lo que se hace con ellas (guardar, duplicar,
borrar). Lo usan el diálogo del PC y MantPro Web; los datos están en nucleo/checklists.py.

Todo es solo de administradores y recibe quién lo hace (en la web no hay sesión del PC). Los errores son códigos
(ValueError); TEXTOS da la clave de traducción de cada uno."""

from .. import idiomas
from . import checklists, usuarios

TEXTOS = {"nombre": "msg_chk_falta_nombre", "sin_puntos": "msg_chk_sin_puntos", "solo_admin": "msg_solo_admin",
          "no_existe": "msg_chk_no_existe"}
MAX_PUNTOS = 200


def texto_error(codigo):
    return idiomas.t(TEXTOS.get(codigo, "msg_chk_no_existe"))


def _admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def nombres_tipo():
    """[(tipo, texto)] del desplegable «Tipo», en el orden del PC."""
    return [("estado", idiomas.t("chk_tipo_estado")), ("lectura", idiomas.t("chk_tipo_lectura")),
            ("trifasica", idiomas.t("chk_tipo_trifasica")), ("seccion", idiomas.t("chk_tipo_seccion"))]


def texto_lista(p):
    """«☑️ Nombre  (n)», como en la lista del PC."""
    return f"☑️ {p['nombre']}  ({len(p['puntos'])})"


def numero(n):
    """Un mínimo, máximo o desequilibrio como se escribe en la tabla («» si no hay)."""
    return "" if n is None else f"{n:g}"


def punto_vacio():
    return {"texto": "", "tipo": "estado", "unidad": "", "minimo": None, "maximo": None, "desequilibrio_max": None,
            "punto_uid": None}


def _existe(plantilla_id):
    p = checklists.obtener_plantilla(plantilla_id) if plantilla_id else None
    if p is None:
        raise ValueError("no_existe")
    return p


def guardar(admin, plantilla_id, nombre, puntos):
    """Guarda la lista (plantilla_id None: nueva) con sus puntos [{texto, tipo, unidad, minimo, maximo,
    desequilibrio_max, punto_uid}]; los puntos sin texto no cuentan. Devuelve su id."""
    _admin(admin)
    if plantilla_id is not None:
        _existe(plantilla_id)
    if not (nombre or "").strip():
        raise ValueError("nombre")
    puntos = [p for p in (puntos or [])[:MAX_PUNTOS] if (p.get("texto") or "").strip()]
    if not puntos:
        raise ValueError("sin_puntos")
    return checklists.guardar_plantilla(plantilla_id, nombre.strip(), puntos)


def duplicar(admin, plantilla_id):
    """«📄 Duplicar»: otra lista igual, «Nombre (copia)», con puntos de identidad nueva (no mezclan lecturas con la
    original). Devuelve su id."""
    _admin(admin)
    p = _existe(plantilla_id)
    return checklists.guardar_plantilla(None, f"{p['nombre']} ({idiomas.t('chk_copia')})",
                                        [dict(x, punto_uid=None) for x in p["puntos"]])


def pregunta_borrar(plantilla_id):
    """La pregunta del PC antes de borrar (con cuántos avisos y pendientes la usan)."""
    p = _existe(plantilla_id)
    texto = idiomas.t("msg_chk_borrar").format(nombre=p["nombre"])
    avisos, pendientes = checklists.usos_de_plantilla(plantilla_id)
    if avisos or pendientes:
        texto += "\n\n" + idiomas.t("msg_chk_borrar_usos").format(a=avisos, p=pendientes)
    return texto


def borrar(admin, plantilla_id):
    _admin(admin)
    _existe(plantilla_id)
    checklists.borrar_plantilla(plantilla_id)
