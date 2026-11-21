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

"""«👥 Gestión de usuarios» y «Especialidades…» (sin Qt): la tabla de usuarios y lo que se hace con ellos (alta,
roles, especialidades, sedes, activar/desactivar, restablecer la contraseña y borrar) y el catálogo de
especialidades. Lo usan el diálogo del PC y MantPro Web.

Todo es solo de administradores y recibe quién lo hace (en la web no hay sesión del PC). Los errores son códigos
(ValueError), nunca texto: TEXTOS da la clave de traducción de cada uno."""

from datetime import datetime

from .. import idiomas
from . import sedes, usuarios

CLAVE_MIN = 4
ROLES = ("tecnico", "almacen", "admin")
# Código de error → clave de texto (en los 8 idiomas)
TEXTOS = {"solo_admin": "msg_solo_admin", "no_existe": "usr_err_no_existe", "obligatorios": "usr_err_obligatorios",
          "clave_corta": "usr_err_clave_corta", "login_repetido": "usr_err_login_repetido",
          "ultimo_admin": "usr_err_ultimo_admin", "propio": "usr_err_propio", "admin_todas": "usuarios_sedes_admin",
          "sede_no_existe": "usr_err_sede_no_existe", "especialidad_no_existe": "especialidades_selecciona",
          "especialidad_obligatoria": "esp_err_obligatorio", "especialidad_repetida": "esp_err_repetida"}


def texto_error(codigo):
    return idiomas.t(TEXTOS.get(codigo, "usr_err_no_existe"))


def _admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def roles_validos(roles):
    """Como las casillas del PC: administrador va solo; sin ninguno, técnico."""
    roles = [r for r in ROLES if r in set(roles or ())]
    if "admin" in roles:
        return ["admin"]
    return roles or ["tecnico"]


def texto_roles(roles):
    return ", ".join(idiomas.t(f"rol_{r}") for r in (roles or ["tecnico"]))


def fecha_hora(iso):
    """«HH:MM:SS» + la fecha corta del idioma (la del PC); «—» si no hay."""
    if not iso:
        return "—"
    try:
        d = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    return f"{d.strftime('%H:%M:%S')} {idiomas.formato_fecha_localizada(d.strftime('%Y-%m-%d'))}"


def filas():
    """La tabla del PC: [{id, login, nombre, roles, roles_txt, especialidades_txt, especialidad_ids, activo,
    estado_txt, acceso_txt, sede_ids, sedes_txt, admin}], activos primero y por nombre."""
    t = idiomas.t
    nombres_sedes = sedes.nombres()
    resultado = []
    for u in usuarios.listar_usuarios():
        roles = u.get("roles") or [u.get("rol") or "tecnico"]
        admin = usuarios.es_admin(u)
        suyas = sedes.de_usuario(u["id"])
        resultado.append({
            "id": u["id"], "login": u["login"], "nombre": u["nombre"], "roles": roles, "roles_txt": texto_roles(roles),
            "especialidad_ids": list(u.get("especialidad_ids") or []),
            "especialidades_txt": ", ".join(u.get("especialidad_nombres") or []) or "—",
            "activo": bool(u["activo"]), "estado_txt": t("activo") if u["activo"] else t("inactivo"),
            "acceso_txt": fecha_hora(u.get("ultimo_acceso")), "admin": admin, "sede_ids": [] if admin else suyas,
            "sedes_txt": t("sede_todas") if admin or not suyas
            else ", ".join(nombres_sedes.get(i, str(i)) for i in suyas)})
    return resultado


def _usuario(usuario_id):
    u = next((x for x in usuarios.listar_usuarios() if x["id"] == usuario_id), None) if usuario_id is not None else None
    if u is None:
        raise ValueError("no_existe")
    return u


def _ultimo_admin_si(usuario_id, deja_de_serlo):
    """Debe quedar al menos un administrador activo."""
    if not deja_de_serlo:
        return
    otros = [u for u in usuarios.listar_usuarios(incluir_inactivos=False) if usuarios.es_admin(u) and u["id"] != usuario_id]
    if not otros:
        raise ValueError("ultimo_admin")


def _resultado(ok_mensaje, codigo):
    ok, _ = ok_mensaje
    if not ok:
        raise ValueError(codigo)


# ---------------------------------------------------------------- usuarios

def crear(admin, login, nombre, clave, roles=("tecnico",), debe_cambiar=True, especialidad_ids=()):
    """Devuelve el id del usuario nuevo."""
    _admin(admin)
    login, nombre = (login or "").strip(), (nombre or "").strip()
    if not login or not nombre:
        raise ValueError("obligatorios")
    if len(clave or "") < CLAVE_MIN:
        raise ValueError("clave_corta")
    if any(u["login"].lower() == login.lower() for u in usuarios.listar_usuarios()):
        raise ValueError("login_repetido")
    validas = {e["id"] for e in usuarios.listar_especialidades()}
    ok, _ = usuarios.crear_usuario(login, nombre, clave, roles_validos(roles), bool(debe_cambiar),
                                   [i for i in (especialidad_ids or ()) if i in validas])
    if not ok:
        raise ValueError("login_repetido")
    return next(u["id"] for u in usuarios.listar_usuarios() if u["login"] == login)


def cambiar_roles(admin, usuario_id, roles):
    _admin(admin)
    u = _usuario(usuario_id)
    nuevos = roles_validos(roles)
    _ultimo_admin_si(usuario_id, usuarios.es_admin(u) and u["activo"] and "admin" not in nuevos)
    _resultado(usuarios.actualizar_usuario(usuario_id, roles=nuevos), "ultimo_admin")


def cambiar_especialidades(admin, usuario_id, especialidad_ids):
    _admin(admin)
    _usuario(usuario_id)
    validas = {e["id"] for e in usuarios.listar_especialidades()}
    if any(i not in validas for i in especialidad_ids or ()):
        raise ValueError("especialidad_no_existe")
    _resultado(usuarios.actualizar_usuario(usuario_id, especialidad_ids=list(especialidad_ids or ())), "no_existe")


def cambiar_sedes(admin, usuario_id, sede_ids):
    """Las sedes que ve (ninguna = todas). Un administrador las ve siempre todas."""
    _admin(admin)
    u = _usuario(usuario_id)
    if usuarios.es_admin(u):
        raise ValueError("admin_todas")
    validas = {s["id"] for s in sedes.listar()}
    if any(i not in validas for i in sede_ids or ()):
        raise ValueError("sede_no_existe")
    sedes.fijar_de_usuario(usuario_id, list(sede_ids or ()))


def alternar_estado(admin, usuario_id):
    """Activa o desactiva (al desactivar se cierran sus sesiones). Devuelve si queda activo."""
    _admin(admin)
    u = _usuario(usuario_id)
    _ultimo_admin_si(usuario_id, u["activo"] and usuarios.es_admin(u))
    _resultado(usuarios.actualizar_usuario(usuario_id, activo=not u["activo"]), "ultimo_admin")
    return not u["activo"]


def restablecer_clave(admin, usuario_id, clave):
    """Contraseña temporal: tendrá que cambiarla al entrar; se cierran sus sesiones."""
    _admin(admin)
    _usuario(usuario_id)
    if len(clave or "") < CLAVE_MIN:
        raise ValueError("clave_corta")
    _resultado(usuarios.cambiar_password(usuario_id, clave, forzar=True), "no_existe")


def borrar(admin, usuario_id):
    _admin(admin)
    u = _usuario(usuario_id)
    if usuario_id == admin.get("id"):
        raise ValueError("propio")
    _ultimo_admin_si(usuario_id, u["activo"] and usuarios.es_admin(u))
    _resultado(usuarios.borrar_usuario(usuario_id), "propio")


# ---------------------------------------------------------------- especialidades

def especialidades():
    return usuarios.listar_especialidades()


def _nombre_especialidad(nombre, excluir_id=None):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("especialidad_obligatoria")
    if any(e["nombre"].lower() == nombre.lower() and e["id"] != excluir_id for e in especialidades()):
        raise ValueError("especialidad_repetida")
    return nombre


def _especialidad(especialidad_id):
    if especialidad_id not in {e["id"] for e in especialidades()}:
        raise ValueError("especialidad_no_existe")


def crear_especialidad(admin, nombre):
    _admin(admin)
    ok, resultado = usuarios.crear_especialidad(_nombre_especialidad(nombre))
    if not ok:
        raise ValueError("especialidad_repetida")
    return resultado


def renombrar_especialidad(admin, especialidad_id, nombre):
    _admin(admin)
    _especialidad(especialidad_id)
    _resultado(usuarios.renombrar_especialidad(especialidad_id, _nombre_especialidad(nombre, especialidad_id)),
               "especialidad_repetida")


def borrar_especialidad(admin, especialidad_id):
    """Quien la tuviera (usuarios, pendientes y avisos) se queda sin ella."""
    _admin(admin)
    _especialidad(especialidad_id)
    usuarios.borrar_especialidad(especialidad_id)
