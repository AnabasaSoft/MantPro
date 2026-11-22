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

"""«🔐 Sesiones de dispositivos» (sin Qt): la tabla de sesiones, revocarlas, adjudicar un móvil a un técnico y la
caducidad por días sin conectar. Lo usan el diálogo del PC y MantPro Web.

Cada sesión se identifica con su «ref» (un trozo de la huella SHA-256 del token), nunca con el token: el token es la
llave de la sesión y no debe salir hacia un navegador. Todo es solo de administradores y recibe quién lo hace. Los
errores son códigos (ValueError); TEXTOS da la clave de traducción de cada uno."""

from .. import idiomas
from . import ficha_usuarios, usuarios

TEXTOS = {"solo_admin": "msg_solo_admin", "elige": "sesiones_selecciona", "elige_movil": "msg_adjudicar_elige",
          "sin_id": "msg_adjudicar_sin_id", "es_web": "msg_adjudicar_web", "no_existe": "usr_err_no_existe"}


def texto_error(codigo):
    return idiomas.t(TEXTOS.get(codigo, "usr_err_no_existe"))


def _admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def ref(token):
    """Identificador de la sesión que puede salir de MantPro (no deja sacar el token)."""
    return usuarios.huella_token(token)[:20]


def texto_conexion(s):
    return idiomas.t("sesiones_en_linea") if s.get("en_linea") else idiomas.t("sesiones_sin_conexion")


def texto_cifrado(s):
    if s.get("cifrada") is True:
        return idiomas.t("sesiones_cifrada")
    if s.get("cifrada") is False:
        return idiomas.t("sesiones_sin_cifrar")
    return "—"


def filas():
    """La tabla del PC, las más recientes primero: [{ref, token, usuario_txt, dispositivo, iniciada, expira,
    activa, estado_txt, en_linea, conexion_txt, contacto, cifrado_txt, sin_cifrar, adjudicado_txt,
    dispositivo_id, adjudicado_id, iniciada_iso, expira_iso, contacto_iso}]."""
    resultado = []
    for s in usuarios.listar_sesiones():
        resultado.append({
            "ref": ref(s["token"]), "token": s["token"],
            "usuario_txt": f"{s['nombre']} ({s['login']})" if s.get("nombre") else s["login"],
            "dispositivo": s.get("dispositivo") or "—",
            "iniciada": ficha_usuarios.fecha_hora(s.get("creado")), "iniciada_iso": s.get("creado") or "",
            "expira": ficha_usuarios.fecha_hora(s.get("expira")), "expira_iso": s.get("expira") or "",
            "activa": bool(s["activa"]),
            "estado_txt": idiomas.t("sesiones_activa") if s["activa"] else idiomas.t("sesiones_expirada"),
            "en_linea": bool(s.get("en_linea")), "conexion_txt": texto_conexion(s),
            "contacto": ficha_usuarios.fecha_hora(s.get("ultimo_contacto")),
            "contacto_iso": s.get("ultimo_contacto") or "",
            "cifrado_txt": texto_cifrado(s), "sin_cifrar": bool(s["activa"] and s.get("cifrada") is False),
            "adjudicado_txt": s.get("adjudicado_nombre") or "—", "adjudicado_id": s.get("adjudicado_id"),
            "dispositivo_id": s.get("dispositivo_id") or "", "login": s["login"], "nombre": s.get("nombre") or ""})
    return resultado


def _por_ref(refs):
    por_ref = {f["ref"]: f for f in filas()}
    return [por_ref[r] for r in refs if r in por_ref]


def revocar(admin, refs):
    """Revoca las sesiones elegidas (tendrán que volver a iniciar sesión) y lo apunta en el registro de cambios.
    Devuelve cuántas ha revocado."""
    _admin(admin)
    elegidas = _por_ref(dict.fromkeys(refs or ()))
    if not elegidas:
        raise ValueError("elige")
    for s in elegidas:
        usuarios.revocar_token(s["token"])
        usuarios.auditar("seguridad", "revocar", f"{s['nombre'] or s['login']} — {s['dispositivo']}",
                         detalle="Sesión del móvil revocada: tendrá que volver a iniciar sesión")
    return len(elegidas)


def para_adjudicar(admin, ref_sesion):
    """(sesión, técnicos activos) para el diálogo «📲 Adjudicar móvil a un técnico…»."""
    _admin(admin)
    s = next(iter(_por_ref([ref_sesion])), None) if ref_sesion else None
    if s is None:
        raise ValueError("elige_movil")
    if usuarios.es_sesion_web(s):
        raise ValueError("es_web")
    if not s["dispositivo_id"]:
        raise ValueError("sin_id")
    return s, usuarios.listar_usuarios(incluir_inactivos=False)


def adjudicar(admin, ref_sesion, usuario_id):
    """Adjudica el móvil de la sesión a un técnico activo (None: lo deja libre). Vale para las dos apps."""
    s, tecnicos = para_adjudicar(admin, ref_sesion)
    if usuario_id is not None and usuario_id not in {u["id"] for u in tecnicos}:
        raise ValueError("no_existe")
    if not usuarios.adjudicar_movil(s["dispositivo_id"], usuario_id):
        raise ValueError("sin_id")


def opciones_dias():
    """[(días, texto)] del desplegable de caducidad, con el valor actual aunque no sea de los de serie."""
    dias = list(usuarios.OPCIONES_DIAS_SESION)
    actual = usuarios.dias_sesion()
    if actual not in dias:
        dias.append(actual)
    return [(d, idiomas.t("sesiones_dias").format(n=d)) for d in dias]


def fijar_dias(admin, dias):
    _admin(admin)
    if dias not in usuarios.OPCIONES_DIAS_SESION and dias != usuarios.dias_sesion():
        raise ValueError("dias")
    usuarios.fijar_dias_sesion(dias)
