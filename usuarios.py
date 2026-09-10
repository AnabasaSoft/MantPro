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

"""
usuarios.py — Gestión de usuarios, autenticación y sesiones para MantPro.

Sin dependencias externas: solo stdlib (sqlite3, hashlib, hmac, secrets).

Uso desde main.py:

    import usuarios
    usuarios.configurar_db(RUTA_DB)      # la misma ruta que usa el resto de la app
    usuarios.inicializar()               # crea tablas + migra columnas (idempotente)

El usuario autenticado se guarda en usuarios.SESION_ACTUAL (dict o None).
"""

import sqlite3
import hashlib
import hmac
import secrets
import base64
from datetime import datetime, timedelta

RUTA_DB = "mantenimiento.db"

# Usuario autenticado en la app de escritorio (proceso actual)
SESION_ACTUAL = None

ITERACIONES = 200_000
ETIQUETA_HISTORICO = "Histórico"
DIAS_VALIDEZ_TOKEN = 365  # los tokens del móvil son de larga duración


# ---------------------------------------------------------------- infraestructura

def configurar_db(ruta):
    """Fija la ruta de la base de datos que usará este módulo."""
    global RUTA_DB
    RUTA_DB = ruta


def _conn():
    con = sqlite3.connect(RUTA_DB)
    con.row_factory = sqlite3.Row
    return con


def _columnas(con, tabla):
    try:
        return {fila["name"] for fila in con.execute(f"PRAGMA table_info({tabla})")}
    except sqlite3.Error:
        return set()


def _tabla_existe(con, tabla):
    fila = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,)
    ).fetchone()
    return fila is not None


# ---------------------------------------------------------------- hashing

def hash_password(password, salt=None):
    """Devuelve 'pbkdf2_sha256$iteraciones$salt_b64$hash_b64'."""
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERACIONES)
    return "pbkdf2_sha256${}${}${}".format(
        ITERACIONES,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verificar_password(password, almacenado):
    """Comparación en tiempo constante contra el hash guardado."""
    try:
        algoritmo, iteraciones, salt_b64, hash_b64 = almacenado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        esperado = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iteraciones)
        )
        return hmac.compare_digest(dk, esperado)
    except (ValueError, TypeError, AttributeError):
        return False


# ---------------------------------------------------------------- esquema y migración

def inicializar():
    """Crea las tablas de usuarios/sesiones y migra las tablas existentes.

    Es idempotente: se puede llamar en cada arranque sin efectos secundarios.
    Devuelve True si ha creado el admin inicial (para avisar al usuario).
    """
    con = _conn()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            login          TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            nombre         TEXT    NOT NULL,
            password_hash  TEXT    NOT NULL,
            rol            TEXT    NOT NULL DEFAULT 'tecnico',
            activo         INTEGER NOT NULL DEFAULT 1,
            debe_cambiar   INTEGER NOT NULL DEFAULT 0,
            creado         TEXT    NOT NULL,
            ultimo_acceso  TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sesiones (
            token       TEXT PRIMARY KEY,
            usuario_id  INTEGER NOT NULL,
            dispositivo TEXT,
            creado      TEXT NOT NULL,
            expira      TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones(usuario_id)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha       TEXT    NOT NULL,
            usuario_id  INTEGER,
            usuario_nombre TEXT,
            tarea_id    INTEGER,
            accion      TEXT    NOT NULL,
            detalle     TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_tarea ON auditoria(tarea_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha DESC)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuario_roles (
            usuario_id  INTEGER NOT NULL,
            rol         TEXT    NOT NULL,
            PRIMARY KEY (usuario_id, rol),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)
    # Migración: cada usuario que aún no tenga fila en usuario_roles recibe
    # su rol único de siempre como primer rol (así los usuarios ya existentes
    # no pierden permisos al pasar al modelo de varios roles por usuario).
    cur.execute("""
        INSERT OR IGNORE INTO usuario_roles (usuario_id, rol)
        SELECT id, rol FROM usuarios
        WHERE id NOT IN (SELECT usuario_id FROM usuario_roles)
    """)

    # --- columnas nuevas en tablas existentes ---
    if _tabla_existe(con, "tareas"):
        cols = _columnas(con, "tareas")
        if "usuario_id" not in cols:
            cur.execute("ALTER TABLE tareas ADD COLUMN usuario_id INTEGER")
        if "usuario_nombre" not in cols:
            cur.execute("ALTER TABLE tareas ADD COLUMN usuario_nombre TEXT")
        # Registros anteriores al sistema de usuarios
        cur.execute(
            "UPDATE tareas SET usuario_nombre = ? "
            "WHERE usuario_nombre IS NULL OR TRIM(usuario_nombre) = ''",
            (ETIQUETA_HISTORICO,),
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_tareas_usuario ON tareas(usuario_id)"
        )

    if _tabla_existe(con, "pendientes"):
        cols = _columnas(con, "pendientes")
        if "asignado_a" not in cols:
            cur.execute("ALTER TABLE pendientes ADD COLUMN asignado_a INTEGER")
        if "asignado_nombre" not in cols:
            cur.execute("ALTER TABLE pendientes ADD COLUMN asignado_nombre TEXT")

    # --- admin inicial ---
    creado_admin = False
    total = cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if total == 0:
        cur.execute(
            "INSERT INTO usuarios (login, nombre, password_hash, rol, activo, "
            "debe_cambiar, creado) VALUES (?, ?, ?, 'admin', 1, 1, ?)",
            ("admin", "Administrador", hash_password("admin"),
             datetime.now().isoformat(timespec="seconds")),
        )
        cur.execute("INSERT INTO usuario_roles (usuario_id, rol) VALUES (?, 'admin')", (cur.lastrowid,))
        creado_admin = True

    con.commit()
    con.close()
    return creado_admin


# ---------------------------------------------------------------- autenticación

def autenticar(login, password):
    """Devuelve dict del usuario si las credenciales son válidas, si no None."""
    con = _conn()
    fila = con.execute(
        "SELECT * FROM usuarios WHERE login = ? COLLATE NOCASE", (login.strip(),)
    ).fetchone()

    if fila is None or not fila["activo"]:
        con.close()
        return None
    if not verificar_password(password, fila["password_hash"]):
        con.close()
        return None

    ahora = datetime.now().isoformat(timespec="seconds")
    con.execute("UPDATE usuarios SET ultimo_acceso = ? WHERE id = ?", (ahora, fila["id"]))
    con.commit()
    usuario = _a_dict(fila, con)
    con.close()
    return usuario


def obtener_roles(con, usuario_id):
    """Lista de roles asignados a un usuario (puede tener varios, p.ej. técnico y almacén)."""
    filas = con.execute(
        "SELECT rol FROM usuario_roles WHERE usuario_id = ? ORDER BY rol", (usuario_id,)
    ).fetchall()
    return [f["rol"] for f in filas]


def _a_dict(fila, con=None):
    roles = obtener_roles(con, fila["id"]) if con is not None else [fila["rol"]]
    return {
        "id": fila["id"],
        "login": fila["login"],
        "nombre": fila["nombre"],
        "rol": fila["rol"],  # compat: rol principal (el primero usado antes del sistema multi-rol)
        "roles": roles,
        "activo": bool(fila["activo"]),
        "debe_cambiar": bool(fila["debe_cambiar"]),
    }


ROLES = ("admin", "tecnico", "almacen")


def es_admin(usuario=None):
    u = usuario or SESION_ACTUAL
    return bool(u) and "admin" in (u.get("roles") or [u.get("rol")])


def puede_gestionar_almacen(usuario=None):
    """True para admin y para el rol almacén: son quienes pueden dar de alta o
    editar artículos y registrar entradas/salidas de stock desde la app móvil."""
    u = usuario or SESION_ACTUAL
    roles = u.get("roles") or [u.get("rol")] if u else []
    return bool(u) and ("admin" in roles or "almacen" in roles)


def nombre_actual():
    """Nombre a estampar en los registros creados desde el escritorio."""
    return SESION_ACTUAL["nombre"] if SESION_ACTUAL else ETIQUETA_HISTORICO


def id_actual():
    return SESION_ACTUAL["id"] if SESION_ACTUAL else None


# ---------------------------------------------------------------- CRUD

def listar_usuarios(incluir_inactivos=True):
    con = _conn()
    sql = "SELECT * FROM usuarios"
    if not incluir_inactivos:
        sql += " WHERE activo = 1"
    sql += " ORDER BY activo DESC, nombre COLLATE NOCASE"
    filas = con.execute(sql).fetchall()
    resultado = [
        dict(_a_dict(f, con), ultimo_acceso=f["ultimo_acceso"], creado=f["creado"])
        for f in filas
    ]
    con.close()
    return resultado


def guardar_ultimo_usuario(login):
    """Recuerda el último login usado, para preseleccionarlo en el desplegable de acceso."""
    try:
        con = _conn()
        con.execute(
            "CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
        con.execute(
            "INSERT OR REPLACE INTO config (clave, valor) VALUES ('ultimo_usuario', ?)",
            (login,))
        con.commit()
        con.close()
    except sqlite3.Error:
        pass


def obtener_ultimo_usuario():
    """Devuelve el login recordado de la última sesión, o None si no hay ninguno."""
    try:
        con = _conn()
        fila = con.execute(
            "SELECT valor FROM config WHERE clave = 'ultimo_usuario'").fetchone()
        con.close()
        return fila["valor"] if fila else None
    except sqlite3.Error:
        return None


def crear_usuario(login, nombre, password, roles=("tecnico",), debe_cambiar=True):
    """Devuelve (ok, mensaje). `roles` acepta uno o varios valores de ROLES
    (p.ej. un usuario puede ser a la vez "tecnico" y "almacen")."""
    login = (login or "").strip()
    nombre = (nombre or "").strip()
    if not login or not nombre:
        return False, "El usuario y el nombre son obligatorios."
    if len(password or "") < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."
    roles = [r for r in (roles or []) if r in ROLES] or ["tecnico"]
    rol_principal = "admin" if "admin" in roles else roles[0]

    con = _conn()
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO usuarios (login, nombre, password_hash, rol, activo, "
            "debe_cambiar, creado) VALUES (?, ?, ?, ?, 1, ?, ?)",
            (login, nombre, hash_password(password), rol_principal, int(debe_cambiar),
             datetime.now().isoformat(timespec="seconds")),
        )
        usuario_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO usuario_roles (usuario_id, rol) VALUES (?, ?)",
            [(usuario_id, r) for r in roles],
        )
        con.commit()
        return True, "Usuario creado."
    except sqlite3.IntegrityError:
        return False, "Ya existe un usuario con ese login."
    finally:
        con.close()


def actualizar_usuario(usuario_id, nombre=None, roles=None, activo=None):
    """Si se indica `roles` (lista de valores de ROLES), sustituye por completo
    el conjunto de roles del usuario."""
    campos, valores = [], []
    if nombre is not None:
        campos.append("nombre = ?"); valores.append(nombre.strip())
    roles_validos = None
    if roles is not None:
        roles_validos = [r for r in roles if r in ROLES] or ["tecnico"]
        rol_principal = "admin" if "admin" in roles_validos else roles_validos[0]
        campos.append("rol = ?"); valores.append(rol_principal)
    if activo is not None:
        campos.append("activo = ?"); valores.append(int(bool(activo)))
    if not campos:
        return False, "Nada que actualizar."

    con = _conn()
    # No permitir quedarse sin ningún admin activo
    deja_de_ser_admin = roles_validos is not None and "admin" not in roles_validos
    if (deja_de_ser_admin or activo is False) and _es_ultimo_admin(con, usuario_id):
        con.close()
        return False, "Debe quedar al menos un administrador activo."

    valores.append(usuario_id)
    con.execute(f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?", valores)
    if roles_validos is not None:
        con.execute("DELETE FROM usuario_roles WHERE usuario_id = ?", (usuario_id,))
        con.executemany(
            "INSERT INTO usuario_roles (usuario_id, rol) VALUES (?, ?)",
            [(usuario_id, r) for r in roles_validos],
        )
    if activo is False:
        con.execute("DELETE FROM sesiones WHERE usuario_id = ?", (usuario_id,))
    con.commit()
    con.close()
    return True, "Usuario actualizado."


def _es_ultimo_admin(con, usuario_id):
    fila = con.execute("SELECT activo FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if not fila or not fila["activo"]:
        return False
    es_admin_actual = con.execute(
        "SELECT 1 FROM usuario_roles WHERE usuario_id = ? AND rol = 'admin'", (usuario_id,)
    ).fetchone()
    if not es_admin_actual:
        return False
    otros = con.execute(
        "SELECT COUNT(*) FROM usuario_roles ur JOIN usuarios u ON u.id = ur.usuario_id "
        "WHERE ur.rol = 'admin' AND u.activo = 1 AND u.id != ?",
        (usuario_id,),
    ).fetchone()[0]
    return otros == 0


def cambiar_password(usuario_id, password_nueva, password_actual=None, forzar=False):
    """Si forzar=False exige la contraseña actual (cambio por el propio usuario)."""
    if len(password_nueva or "") < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."

    con = _conn()
    fila = con.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if fila is None:
        con.close()
        return False, "Usuario no encontrado."
    if not forzar and not verificar_password(password_actual or "", fila["password_hash"]):
        con.close()
        return False, "La contraseña actual no es correcta."

    con.execute(
        "UPDATE usuarios SET password_hash = ?, debe_cambiar = ? WHERE id = ?",
        (hash_password(password_nueva), 1 if forzar else 0, usuario_id),
    )
    # Un cambio de contraseña invalida las sesiones móviles de ese usuario
    con.execute("DELETE FROM sesiones WHERE usuario_id = ?", (usuario_id,))
    con.commit()
    con.close()
    if SESION_ACTUAL and SESION_ACTUAL.get("id") == usuario_id:
        SESION_ACTUAL["debe_cambiar"] = bool(forzar)
    return True, "Contraseña actualizada."


def desactivar_usuario(usuario_id):
    """Baja lógica: nunca se borra, para no romper el histórico."""
    return actualizar_usuario(usuario_id, activo=False)


# ---------------------------------------------------------------- sesiones (móvil)

def crear_token(usuario_id, dispositivo=None):
    token = secrets.token_urlsafe(32)
    ahora = datetime.now()
    con = _conn()
    con.execute(
        "INSERT INTO sesiones (token, usuario_id, dispositivo, creado, expira) "
        "VALUES (?, ?, ?, ?, ?)",
        (token, usuario_id, dispositivo or "",
         ahora.isoformat(timespec="seconds"),
         (ahora + timedelta(days=DIAS_VALIDEZ_TOKEN)).isoformat(timespec="seconds")),
    )
    con.commit()
    con.close()
    return token


def usuario_por_token(token):
    """Devuelve el usuario asociado al token, o None si no existe/expiró/está inactivo."""
    if not token:
        return None
    con = _conn()
    fila = con.execute(
        "SELECT u.*, s.expira FROM sesiones s "
        "JOIN usuarios u ON u.id = s.usuario_id WHERE s.token = ?",
        (token,),
    ).fetchone()
    if fila is None:
        con.close()
        return None
    if not fila["activo"] or fila["expira"] < datetime.now().isoformat(timespec="seconds"):
        con.execute("DELETE FROM sesiones WHERE token = ?", (token,))
        con.commit()
        con.close()
        return None
    usuario = _a_dict(fila, con)
    con.close()
    return usuario


def revocar_token(token):
    con = _conn()
    con.execute("DELETE FROM sesiones WHERE token = ?", (token,))
    con.commit()
    con.close()


def sesiones_de(usuario_id):
    con = _conn()
    filas = con.execute(
        "SELECT dispositivo, creado, expira FROM sesiones WHERE usuario_id = ? "
        "ORDER BY creado DESC", (usuario_id,)
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]


def listar_sesiones():
    """Todas las sesiones de dispositivos de todos los usuarios, con el estado calculado."""
    con = _conn()
    filas = con.execute(
        "SELECT s.token, s.dispositivo, s.creado, s.expira, "
        "u.id AS usuario_id, u.login, u.nombre "
        "FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id "
        "ORDER BY s.creado DESC"
    ).fetchall()
    con.close()
    ahora = datetime.now().isoformat(timespec="seconds")
    sesiones = []
    for f in filas:
        d = dict(f)
        d["activa"] = d["expira"] >= ahora
        sesiones.append(d)
    return sesiones


# ---------------------------------------------------------------- auditoría

def registrar_auditoria(usuario_id, tarea_id, accion, detalle=""):
    """Apunta una acción (editar/borrar) sobre un registro del historial."""
    try:
        con = _conn()
        nombre = ""
        if usuario_id:
            fila = con.execute("SELECT nombre FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
            nombre = fila["nombre"] if fila else ""
        con.execute(
            "INSERT INTO auditoria (fecha, usuario_id, usuario_nombre, tarea_id, accion, detalle) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), usuario_id, nombre,
             tarea_id, accion, (detalle or "")[:500]),
        )
        con.commit()
        con.close()
    except Exception as e:
        print(f"Error registrar_auditoria: {e}")


def obtener_auditoria(usuario_id=None, accion=None, tarea_id=None, limite=200):
    """Devuelve los registros de auditoría, los más recientes primero."""
    con = _conn()
    sql = "SELECT * FROM auditoria WHERE 1=1"
    params = []
    if usuario_id is not None:
        sql += " AND usuario_id = ?"; params.append(usuario_id)
    if accion is not None:
        sql += " AND accion = ?"; params.append(accion)
    if tarea_id is not None:
        sql += " AND tarea_id = ?"; params.append(tarea_id)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limite)
    filas = con.execute(sql, params).fetchall()
    con.close()
    return [dict(f) for f in filas]
