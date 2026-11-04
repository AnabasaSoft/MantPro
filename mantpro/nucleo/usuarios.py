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

"""
usuarios.py — Gestión de usuarios, autenticación y sesiones para MantPro.

Sin dependencias externas: solo stdlib (sqlite3, hashlib, hmac, secrets).

Uso desde la interfaz (mantpro/interfaz/app.py):

    from mantpro.nucleo import usuarios
    usuarios.configurar_db(RUTA_DB)      # la misma ruta que usa el resto de la app
    usuarios.inicializar()               # crea tablas + migra columnas (idempotente)

El usuario autenticado se guarda en usuarios.SESION_ACTUAL (dict o None).
"""

from .conexion_bd import sqlite3, conectar
import hashlib
import hmac
import secrets
import base64
import json
import threading
from collections import deque
from datetime import datetime, timedelta

RUTA_DB = "mantenimiento.db"

# Usuario autenticado en la app de escritorio (proceso actual)
SESION_ACTUAL = None

ITERACIONES = 200_000
ETIQUETA_HISTORICO = "Histórico"
# Las sesiones del móvil caducan tras estos días SIN conectar con el PC; cada
# contacto las renueva (ver registrar_contacto), así que quien usa la app no
# tiene que volver a entrar. Configurable por el administrador (config
# «dias_sesion», en Sesiones de dispositivos).
DIAS_VALIDEZ_TOKEN = 60
OPCIONES_DIAS_SESION = (30, 60, 90, 180, 365)


def dias_sesion():
    try:
        con = _conn()
        fila = con.execute("SELECT valor FROM config WHERE clave='dias_sesion'").fetchone()
        con.close()
        return int(fila[0]) if fila and str(fila[0]).isdigit() else DIAS_VALIDEZ_TOKEN
    except Exception:
        return DIAS_VALIDEZ_TOKEN


def fijar_dias_sesion(dias):
    """Cambia el plazo y lo aplica ya a las sesiones abiertas (contando desde
    su último contacto): acortarlo cierra al momento las que lleven más tiempo
    sin conectar."""
    dias = int(dias)
    anterior = dias_sesion()
    con = _conn()
    con.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    con.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('dias_sesion', ?)", (str(dias),))
    for token, ultimo, creado in con.execute("SELECT token, ultimo_contacto, creado FROM sesiones").fetchall():
        base = _ULTIMO_CONTACTO.get(token) or datetime.fromisoformat(ultimo or creado)
        con.execute("UPDATE sesiones SET expira=? WHERE token=?",
                    ((base + timedelta(days=dias)).isoformat(timespec="seconds"), token))
    con.commit()
    con.close()
    if anterior != dias:
        auditar("seguridad", "configurar", "Caducidad de las sesiones del móvil",
                cambios=[{"campo": "Días sin conectar", "antes": str(anterior), "despues": str(dias)}])


# ---------------------------------------------------------------- infraestructura

def configurar_db(ruta):
    """Fija la ruta de la base de datos que usará este módulo."""
    global RUTA_DB
    RUTA_DB = ruta


def _conn():
    # timeout=20: igual que en main.py, para no dar "database is locked" cuando
    # el hilo del servidor Flask comprueba la sesión de un móvil justo mientras
    # el PC está escribiendo mucho seguido (p. ej. al crear un almacén entero).
    con = conectar(RUTA_DB, timeout=20)
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
    # Último contacto del móvil con el servidor, para saber en "Sesiones de
    # dispositivos" si está en línea (ver registrar_contacto).
    if "ultimo_contacto" not in _columnas(con, "sesiones"):
        cur.execute("ALTER TABLE sesiones ADD COLUMN ultimo_contacto TEXT")
    # Si el móvil se conectó la última vez por la conexión cifrada (1), sin
    # cifrar (0, app antigua) o no se sabe aún (NULL). Ver sesiones_sin_cifrar.
    if "cifrada" not in _columnas(con, "sesiones"):
        cur.execute("ALTER TABLE sesiones ADD COLUMN cifrada INTEGER")
    # Identificador propio del móvil (el mismo para MantPro y MantPro Stock en
    # el mismo teléfono) y los móviles adjudicados a un técnico.
    if "dispositivo_id" not in _columnas(con, "sesiones"):
        cur.execute("ALTER TABLE sesiones ADD COLUMN dispositivo_id TEXT")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS moviles (
            dispositivo_id TEXT PRIMARY KEY,
            modelo         TEXT NOT NULL DEFAULT '',
            usuario_id     INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
            visto          TEXT NOT NULL
        )
    """)

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
    # Ampliación del registro de cambios: de qué tipo es (categoría), sobre
    # qué (objeto), qué ha cambiado campo a campo (cambios, JSON
    # [{campo, antes, despues}]) y desde dónde (origen: «PC» o el móvil).
    for columna in ("categoria", "objeto", "cambios", "origen"):
        if columna not in _columnas(con, "auditoria"):
            cur.execute(f"ALTER TABLE auditoria ADD COLUMN {columna} TEXT")
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS especialidades (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT    NOT NULL UNIQUE COLLATE NOCASE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuario_especialidades (
            usuario_id      INTEGER NOT NULL,
            especialidad_id INTEGER NOT NULL,
            PRIMARY KEY (usuario_id, especialidad_id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
            FOREIGN KEY (especialidad_id) REFERENCES especialidades(id) ON DELETE CASCADE
        )
    """)
    # Migración: un técnico podía tener antes una única especialidad, guardada
    # en la columna especialidad_id de usuarios. Se traslada ese valor a la
    # nueva tabla muchos-a-muchos (usuario_especialidades) la primera vez que
    # se detecta, para no perder la asignación ya existente.
    if "especialidad_id" in _columnas(con, "usuarios"):
        cur.execute("""
            INSERT OR IGNORE INTO usuario_especialidades (usuario_id, especialidad_id)
            SELECT id, especialidad_id FROM usuarios WHERE especialidad_id IS NOT NULL
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
        if "prioridad" not in cols:
            cur.execute("ALTER TABLE pendientes ADD COLUMN prioridad TEXT DEFAULT 'Media'")
        if "especialidad_id" not in cols:
            cur.execute("ALTER TABLE pendientes ADD COLUMN especialidad_id INTEGER")

    if _tabla_existe(con, "avisos_recurrentes"):
        cols = _columnas(con, "avisos_recurrentes")
        if "asignado_a" not in cols:
            cur.execute("ALTER TABLE avisos_recurrentes ADD COLUMN asignado_a INTEGER")
        if "asignado_nombre" not in cols:
            cur.execute("ALTER TABLE avisos_recurrentes ADD COLUMN asignado_nombre TEXT")
        if "especialidad_id" not in cols:
            cur.execute("ALTER TABLE avisos_recurrentes ADD COLUMN especialidad_id INTEGER")

    cols_usuarios = _columnas(con, "usuarios")
    if "especialidad_id" not in cols_usuarios:
        cur.execute("ALTER TABLE usuarios ADD COLUMN especialidad_id INTEGER")

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
    especialidades = _especialidades_de_usuario(con, fila["id"]) if con is not None else []
    return {
        "id": fila["id"],
        "login": fila["login"],
        "nombre": fila["nombre"],
        "rol": fila["rol"],  # compat: rol principal (el primero usado antes del sistema multi-rol)
        "roles": roles,
        "activo": bool(fila["activo"]),
        "debe_cambiar": bool(fila["debe_cambiar"]),
        # Un técnico puede tener varias especialidades a la vez.
        "especialidad_ids": [e["id"] for e in especialidades],
        "especialidad_nombres": [e["nombre"] for e in especialidades],
    }


def _especialidades_de_usuario(con, usuario_id):
    filas = con.execute(
        "SELECT e.id, e.nombre FROM especialidades e "
        "JOIN usuario_especialidades ue ON ue.especialidad_id = e.id "
        "WHERE ue.usuario_id = ? ORDER BY e.nombre COLLATE NOCASE",
        (usuario_id,),
    ).fetchall()
    return [dict(f) for f in filas]


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


def puede_hacer_trabajos(usuario=None):
    """True para admin y para el rol técnico: son quienes pueden crear, editar,
    completar o borrar trabajos y avisos desde la app móvil de mantenimiento."""
    u = usuario or SESION_ACTUAL
    roles = u.get("roles") or [u.get("rol")] if u else []
    return bool(u) and ("admin" in roles or "tecnico" in roles)


def nombre_actual():
    """Nombre a estampar en los registros creados desde el escritorio."""
    return SESION_ACTUAL["nombre"] if SESION_ACTUAL else ETIQUETA_HISTORICO


def id_actual():
    return SESION_ACTUAL["id"] if SESION_ACTUAL else None


def especialidades_actuales():
    """Ids de las especialidades del usuario en sesión (lista vacía si no tiene)."""
    return SESION_ACTUAL.get("especialidad_ids") or [] if SESION_ACTUAL else []


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


def crear_usuario(login, nombre, password, roles=("tecnico",), debe_cambiar=True, especialidad_ids=None):
    """Devuelve (ok, mensaje). `roles` acepta uno o varios valores de ROLES
    (p.ej. un usuario puede ser a la vez "tecnico" y "almacen"). `especialidad_ids`
    acepta cero, una o varias especialidades a la vez."""
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
        establecer_especialidades_usuario(usuario_id, especialidad_ids, con=con)
        con.commit()
        return True, "Usuario creado."
    except sqlite3.IntegrityError:
        return False, "Ya existe un usuario con ese login."
    finally:
        con.close()


def actualizar_usuario(usuario_id, nombre=None, roles=None, activo=None, especialidad_ids=None):
    """Si se indica `roles` (lista de valores de ROLES), sustituye por completo
    el conjunto de roles del usuario. `especialidad_ids` solo se toca si se pasa
    explícitamente (None es el valor por defecto que significa "no tocar"; pasa
    una lista, vacía o no, para sustituir el conjunto de especialidades)."""
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
    if not campos and especialidad_ids is None:
        return False, "Nada que actualizar."

    con = _conn()
    # No permitir quedarse sin ningún admin activo
    deja_de_ser_admin = roles_validos is not None and "admin" not in roles_validos
    if (deja_de_ser_admin or activo is False) and _es_ultimo_admin(con, usuario_id):
        con.close()
        return False, "Debe quedar al menos un administrador activo."

    if campos:
        valores.append(usuario_id)
        con.execute(f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?", valores)
    if roles_validos is not None:
        con.execute("DELETE FROM usuario_roles WHERE usuario_id = ?", (usuario_id,))
        con.executemany(
            "INSERT INTO usuario_roles (usuario_id, rol) VALUES (?, ?)",
            [(usuario_id, r) for r in roles_validos],
        )
    if especialidad_ids is not None:
        establecer_especialidades_usuario(usuario_id, especialidad_ids, con=con)
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


# ---------------------------------------------------------------- especialidades

def listar_especialidades():
    con = _conn()
    filas = con.execute("SELECT id, nombre FROM especialidades ORDER BY nombre COLLATE NOCASE").fetchall()
    con.close()
    return [dict(f) for f in filas]


def crear_especialidad(nombre):
    """Devuelve (ok, mensaje_o_id)."""
    nombre = (nombre or "").strip()
    if not nombre:
        return False, "El nombre de la especialidad es obligatorio."
    con = _conn()
    try:
        cur = con.cursor()
        cur.execute("INSERT INTO especialidades (nombre) VALUES (?)", (nombre,))
        con.commit()
        return True, cur.lastrowid
    except sqlite3.IntegrityError:
        return False, "Ya existe una especialidad con ese nombre."
    finally:
        con.close()


def renombrar_especialidad(especialidad_id, nombre_nuevo):
    nombre_nuevo = (nombre_nuevo or "").strip()
    if not nombre_nuevo:
        return False, "El nombre de la especialidad es obligatorio."
    con = _conn()
    try:
        con.execute("UPDATE especialidades SET nombre = ? WHERE id = ?", (nombre_nuevo, especialidad_id))
        con.commit()
        return True, "Especialidad actualizada."
    except sqlite3.IntegrityError:
        return False, "Ya existe una especialidad con ese nombre."
    finally:
        con.close()


def especialidades_de_usuario(usuario_id):
    """Especialidades (lista de dicts id/nombre) asignadas a un usuario."""
    con = _conn()
    resultado = _especialidades_de_usuario(con, usuario_id)
    con.close()
    return resultado


def establecer_especialidades_usuario(usuario_id, especialidad_ids, con=None):
    """Sustituye por completo el conjunto de especialidades de un usuario.
    Un técnico puede tener cero, una o varias a la vez."""
    cerrar = con is None
    if con is None:
        con = _conn()
    ids = sorted({int(e) for e in (especialidad_ids or [])})
    con.execute("DELETE FROM usuario_especialidades WHERE usuario_id = ?", (usuario_id,))
    if ids:
        con.executemany(
            "INSERT INTO usuario_especialidades (usuario_id, especialidad_id) VALUES (?, ?)",
            [(usuario_id, eid) for eid in ids],
        )
    if cerrar:
        con.commit()
        con.close()


def borrar_especialidad(especialidad_id):
    """Borra la especialidad y desvincula a quien la tuviera asignada (usuarios,
    pendientes/trabajos y avisos recurrentes), en vez de dejar referencias rotas."""
    con = _conn()
    con.execute("DELETE FROM usuario_especialidades WHERE especialidad_id = ?", (especialidad_id,))
    if _tabla_existe(con, "pendientes"):
        con.execute("UPDATE pendientes SET especialidad_id = NULL WHERE especialidad_id = ?", (especialidad_id,))
    if _tabla_existe(con, "avisos_recurrentes"):
        con.execute("UPDATE avisos_recurrentes SET especialidad_id = NULL WHERE especialidad_id = ?", (especialidad_id,))
    con.execute("DELETE FROM especialidades WHERE id = ?", (especialidad_id,))
    con.commit()
    con.close()
    return True, "Especialidad eliminada."


# ---------------------------------------------------------------- sesiones (móvil)

def crear_token(usuario_id, dispositivo=None, dispositivo_id=None):
    token = secrets.token_urlsafe(32)
    dispositivo_id = limpiar_dispositivo_id(dispositivo_id)
    if dispositivo_id:
        registrar_movil(dispositivo_id, dispositivo)
    ahora = datetime.now()
    con = _conn()
    if dispositivo:
        # Si ese mismo usuario ya tenía una sesión abierta desde el mismo
        # dispositivo (p. ej. reconecta el móvil tras cerrar/reinstalar la
        # app), la sustituimos en vez de dejarla acumulada como sesión suelta.
        con.execute(
            "DELETE FROM sesiones WHERE usuario_id = ? AND dispositivo = ?",
            (usuario_id, dispositivo),
        )
    con.execute(
        "INSERT INTO sesiones (token, usuario_id, dispositivo, creado, expira, dispositivo_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (token, usuario_id, dispositivo or "",
         ahora.isoformat(timespec="seconds"),
         (ahora + timedelta(days=dias_sesion())).isoformat(timespec="seconds"),
         dispositivo_id),
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
        "SELECT s.token, s.dispositivo, s.creado, s.expira, s.ultimo_contacto, s.cifrada, s.dispositivo_id, "
        "u.id AS usuario_id, u.login, u.nombre, "
        "m.usuario_id AS adjudicado_id, ua.nombre AS adjudicado_nombre "
        "FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id "
        "LEFT JOIN moviles m ON m.dispositivo_id = s.dispositivo_id AND s.dispositivo_id != '' "
        "LEFT JOIN usuarios ua ON ua.id = m.usuario_id "
        "ORDER BY s.creado DESC"
    ).fetchall()
    con.close()
    ahora = datetime.now().isoformat(timespec="seconds")
    sesiones = []
    for f in filas:
        d = dict(f)
        d["activa"] = d["expira"] >= ahora
        # La hora en memoria es la más reciente (la de la BD se guarda como
        # mucho una vez por minuto); la de la BD sirve tras reiniciar el PC.
        en_memoria = _ULTIMO_CONTACTO.get(d["token"])
        if en_memoria and (not d["ultimo_contacto"] or en_memoria.isoformat(timespec="seconds") > d["ultimo_contacto"]):
            d["ultimo_contacto"] = en_memoria.isoformat(timespec="seconds")
        d["en_linea"] = en_linea(d["token"], d["activa"])
        if d["token"] in _CIFRADA:
            d["cifrada"] = _CIFRADA[d["token"]]
        d["cifrada"] = None if d["cifrada"] is None else bool(d["cifrada"])
        sesiones.append(d)
    return sesiones


# El PC no puede preguntar a un móvil si está conectado (es el móvil quien
# llama al PC), así que se deduce del tiempo sin contacto. MantPro llama cada
# 5 s mientras está abierta y MantPro Stock cada 25 s, de modo que el margen se
# adapta al ritmo de cada sesión: el doble de su intervalo más largo reciente
# más 5 s de cortesía (MantPro ~15 s, MantPro Stock ~55 s), entre 15 y 90 s.
# Mientras no hay intervalos conocidos se usa SEGUNDOS_EN_LINEA. Además, las
# apps avisan al cerrarse o pasar a segundo plano (registrar_desconexion).
SEGUNDOS_EN_LINEA = 60
_MARGEN_MINIMO, _MARGEN_MAXIMO = 15, 90

# token -> datetime del último contacto. En memoria porque lo actualiza cada
# petición de los móviles; en la BD se guarda como mucho una vez por minuto.
_ULTIMO_CONTACTO = {}
_ULTIMA_ESCRITURA_CONTACTO = {}
_INTERVALOS = {}       # token -> últimos intervalos entre contactos (s)
_DESCONECTADO = {}     # token -> hora del aviso "me desconecto" de la app
_CIFRADA = {}          # token -> True/False: si su último contacto fue por HTTPS


def margen_en_linea(token):
    """Segundos sin contacto a partir de los cuales una sesión pasa a "Sin conexión"."""
    intervalos = _INTERVALOS.get(token)
    if not intervalos:
        return SEGUNDOS_EN_LINEA
    return min(_MARGEN_MAXIMO, max(_MARGEN_MINIMO, 2 * max(intervalos) + 5))


def en_linea(token, activa=True):
    """True si el móvil de esta sesión está conectado ahora mismo."""
    ultimo = _ULTIMO_CONTACTO.get(token)
    if not (activa and ultimo) or token in _DESCONECTADO:
        return False
    return (datetime.now() - ultimo).total_seconds() <= margen_en_linea(token)


def registrar_desconexion(token):
    """La app avisa de que se cierra o pasa a segundo plano: deja de estar en
    línea al momento, sin esperar al margen. Su siguiente contacto la vuelve
    a poner en línea."""
    if token:
        _DESCONECTADO[token] = datetime.now()


def registrar_contacto(token, cifrada=None):
    """Anota que el móvil de esta sesión acaba de hablar con el servidor, y si
    lo ha hecho por la conexión cifrada. Lo llama el servidor de
    sincronización en cada petición con un token válido."""
    if not token:
        return
    ahora = datetime.now()
    cambio_conexion = cifrada is not None and _CIFRADA.get(token) != cifrada
    if cifrada is not None:
        _CIFRADA[token] = cifrada
    anterior = _ULTIMO_CONTACTO.get(token)
    if anterior is not None:
        hueco = (ahora - anterior).total_seconds()
        # Huecos largos = la app estuvo cerrada; no cuentan para su ritmo.
        if hueco <= 120:
            _INTERVALOS.setdefault(token, deque(maxlen=8)).append(hueco)
    _ULTIMO_CONTACTO[token] = ahora
    _DESCONECTADO.pop(token, None)
    ultima = _ULTIMA_ESCRITURA_CONTACTO.get(token)
    if ultima and (ahora - ultima).total_seconds() < 60 and not cambio_conexion:
        return
    _ULTIMA_ESCRITURA_CONTACTO[token] = ahora
    try:
        con = _conn()
        # Cada contacto renueva la sesión: caduca tras X días SIN conectar
        con.execute("UPDATE sesiones SET ultimo_contacto = ?, cifrada = COALESCE(?, cifrada), expira = ? WHERE token = ?",
                    (ahora.isoformat(timespec="seconds"), None if cifrada is None else int(cifrada),
                     (ahora + timedelta(days=dias_sesion())).isoformat(timespec="seconds"), token))
        con.commit()
        con.close()
    except sqlite3.Error:
        pass  # no es crítico: la hora en memoria sigue valiendo para "en línea"


def sesiones_sin_cifrar():
    """Sesiones activas cuyo móvil se conectó la última vez sin cifrar (una
    app anterior a la conexión cifrada): mientras haya alguna, conviene no
    desactivar la conexión sin cifrar."""
    return [s for s in listar_sesiones() if s["activa"] and s.get("cifrada") is False]


# Conexión sin cifrar (HTTP) desactivada: el PC solo atiende por HTTPS. Se
# guarda en la tabla config; en memoria para no leer la BD en cada petición.
_HTTP_DESACTIVADO = None


def http_desactivado():
    global _HTTP_DESACTIVADO
    if _HTTP_DESACTIVADO is None:
        try:
            con = _conn()
            fila = con.execute("SELECT valor FROM config WHERE clave = 'http_desactivado'").fetchone()
            con.close()
            _HTTP_DESACTIVADO = bool(fila) and fila[0] == "1"
        except sqlite3.Error:
            return False
    return _HTTP_DESACTIVADO


def fijar_http_desactivado(desactivado):
    global _HTTP_DESACTIVADO
    con = _conn()
    con.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    con.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('http_desactivado', ?)",
                ("1" if desactivado else "0",))
    con.commit()
    con.close()
    _HTTP_DESACTIVADO = bool(desactivado)


# ---------------------------------------------------------------- auditoría

# Quién hace la petición en el servidor de los móviles (cada petición va en
# su propio hilo): el servidor lo fija al validar el token, y así las
# funciones del núcleo apuntan en el registro al usuario y al móvil correctos
# en vez de al usuario con la sesión abierta en el PC.
_actor = threading.local()


def fijar_actor_peticion(usuario, dispositivo=None):
    _actor.usuario = usuario
    _actor.origen = f"📱 {dispositivo}" if dispositivo else "📱"


def limpiar_actor_peticion():
    _actor.usuario = None
    _actor.origen = None


def _actor_actual():
    """(usuario_id, origen) de quien hace el cambio ahora mismo."""
    u = getattr(_actor, "usuario", None)
    if u:
        return u.get("id"), getattr(_actor, "origen", None) or "📱"
    return id_actual(), "💻 PC"


def _texto(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, (list, tuple, set)):
        return ", ".join(str(x) for x in v)
    return str(v)


def diferencias(antes, despues, etiquetas=None):
    """Cambios campo a campo entre dos dicts: [{campo, antes, despues}].
    [etiquetas] da el nombre legible de cada campo (y solo esos se miran)."""
    etiquetas = etiquetas or {k: k for k in set(antes or {}) | set(despues or {})}
    cambios = []
    for clave, nombre in etiquetas.items():
        a, d = _texto((antes or {}).get(clave)), _texto((despues or {}).get(clave))
        if a.strip() != d.strip():
            cambios.append({"campo": nombre, "antes": a[:2000], "despues": d[:2000]})
    return cambios


def registrar_auditoria(usuario_id, tarea_id, accion, detalle="", categoria="trabajos",
                        objeto="", cambios=None, origen=None):
    """Apunta un cambio en el registro (Herramientas → Registro de cambios).

    - accion: crear, editar, borrar, revertir, completar, descompletar,
      restaurar, importar, configurar…
    - categoria: trabajos, pendientes, avisos, usuarios, seguridad, almacen,
      maquinas, checklists, copias, configuracion.
    - objeto: a qué afecta, en texto («Compresor GA30», «usuario jperez»…).
    - cambios: [{campo, antes, despues}] (ver diferencias()).
    Si usuario_id u origen no se dan, se toman de quien hace la petición (el
    móvil, en el servidor) o del usuario con la sesión abierta en el PC."""
    try:
        actor_id, actor_origen = _actor_actual()
        if usuario_id is None:
            usuario_id = actor_id
        origen = origen or actor_origen
        con = _conn()
        nombre = ""
        if usuario_id:
            fila = con.execute("SELECT nombre FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
            nombre = fila["nombre"] if fila else ""
        con.execute(
            "INSERT INTO auditoria (fecha, usuario_id, usuario_nombre, tarea_id, accion, detalle, "
            "categoria, objeto, cambios, origen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), usuario_id, nombre,
             tarea_id, accion, (detalle or "")[:2000], categoria, (objeto or "")[:300],
             json.dumps(cambios, ensure_ascii=False) if cambios else None, origen),
        )
        con.commit()
        con.close()
    except Exception as e:
        print(f"Error registrar_auditoria: {e}")


def auditar(categoria, accion, objeto="", detalle="", cambios=None, objeto_id=None):
    """Atajo para apuntar un cambio de quien lo hace ahora (PC o móvil). Si es
    una edición sin cambios reales, no apunta nada."""
    if accion == "editar" and cambios is not None and not cambios and not detalle:
        return
    registrar_auditoria(None, objeto_id, accion, detalle, categoria, objeto, cambios)


def obtener_auditoria(usuario_id=None, accion=None, tarea_id=None, limite=200, categoria=None,
                      texto=None, desde=None, hasta=None, desplazamiento=0):
    """Registros del registro de cambios, los más recientes primero. [desde] y
    [hasta] son fechas AAAA-MM-DD (incluidas); [texto] busca en el objeto, el
    detalle, los cambios y el usuario."""
    con = _conn()
    sql = "SELECT * FROM auditoria WHERE 1=1"
    params = []
    if usuario_id is not None:
        sql += " AND usuario_id = ?"; params.append(usuario_id)
    if accion is not None:
        sql += " AND accion = ?"; params.append(accion)
    if tarea_id is not None:
        sql += " AND tarea_id = ?"; params.append(tarea_id)
    if categoria is not None:
        # Los registros antiguos no tienen categoría: eran todos de trabajos
        sql += " AND COALESCE(categoria, 'trabajos') = ?"; params.append(categoria)
    if desde:
        sql += " AND fecha >= ?"; params.append(desde)
    if hasta:
        sql += " AND fecha < ?"; params.append(hasta + "T99")
    if texto:
        sql += (" AND (COALESCE(objeto,'') || ' ' || COALESCE(detalle,'') || ' ' || COALESCE(cambios,'')"
                " || ' ' || COALESCE(usuario_nombre,'')) LIKE ?")
        params.append(f"%{texto}%")
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params += [limite, desplazamiento]
    filas = con.execute(sql, params).fetchall()
    con.close()
    resultado = []
    for f in filas:
        d = dict(f)
        d["categoria"] = d.get("categoria") or "trabajos"
        try:
            d["cambios"] = json.loads(d["cambios"]) if d.get("cambios") else []
        except ValueError:
            d["cambios"] = []
        resultado.append(d)
    return resultado

# ------------------------------------------- registro de cambios de usuarios
# Las funciones de gestión de usuarios y especialidades apuntan lo que cambian
# (sirven igual desde el PC que desde el servidor de los móviles).

_NOMBRES_ROL = {"admin": "Administrador", "tecnico": "Técnico", "almacen": "Almacén"}
_ETIQUETAS_USUARIO = {"nombre": "Nombre", "roles": "Roles", "activo": "Activo", "especialidades": "Especialidades"}


def _foto_usuario(usuario_id):
    """Estado de un usuario para comparar antes y después de un cambio."""
    u = next((x for x in listar_usuarios() if x["id"] == usuario_id), None)
    if not u:
        return {}
    return {"login": u.get("login"), "nombre": u.get("nombre"),
            "roles": sorted(_NOMBRES_ROL.get(r, r) for r in (u.get("roles") or [])),
            "activo": "Sí" if u.get("activo") else "No",
            "especialidades": sorted(e["nombre"] for e in especialidades_de_usuario(usuario_id))}


def _objeto_usuario(foto):
    return f"{foto.get('nombre', '')} ({foto.get('login', '')})" if foto else ""


_crear_usuario_sin_registro = crear_usuario
_actualizar_usuario_sin_registro = actualizar_usuario
_cambiar_password_sin_registro = cambiar_password
_crear_especialidad_sin_registro = crear_especialidad
_renombrar_especialidad_sin_registro = renombrar_especialidad
_borrar_especialidad_sin_registro = borrar_especialidad


def crear_usuario(login, nombre, password, roles=("tecnico",), debe_cambiar=True, especialidad_ids=None):
    ok, mensaje = _crear_usuario_sin_registro(login, nombre, password, roles, debe_cambiar, especialidad_ids)
    if ok:
        u = next((x for x in listar_usuarios() if x["login"] == (login or "").strip()), None)
        foto = _foto_usuario(u["id"]) if u else {}
        auditar("usuarios", "crear", _objeto_usuario(foto),
                cambios=diferencias({}, foto, _ETIQUETAS_USUARIO), objeto_id=u["id"] if u else None)
    return ok, mensaje


def actualizar_usuario(usuario_id, nombre=None, roles=None, activo=None, especialidad_ids=None):
    antes = _foto_usuario(usuario_id)
    ok, mensaje = _actualizar_usuario_sin_registro(usuario_id, nombre, roles, activo, especialidad_ids)
    if ok:
        despues = _foto_usuario(usuario_id)
        accion = "desactivar" if antes.get("activo") == "Sí" and despues.get("activo") == "No" else \
                 "activar" if antes.get("activo") == "No" and despues.get("activo") == "Sí" else "editar"
        auditar("usuarios", accion, _objeto_usuario(despues),
                cambios=diferencias(antes, despues, _ETIQUETAS_USUARIO), objeto_id=usuario_id)
    return ok, mensaje


def cambiar_password(usuario_id, password_nueva, password_actual=None, forzar=False):
    ok, mensaje = _cambiar_password_sin_registro(usuario_id, password_nueva, password_actual, forzar)
    if ok:
        foto = _foto_usuario(usuario_id)
        auditar("usuarios", "contrasena", _objeto_usuario(foto),
                detalle=("Contraseña restablecida por un administrador (deberá cambiarla al entrar); se cierran sus sesiones"
                         if forzar else "Contraseña cambiada por el propio usuario; se cierran sus sesiones"),
                objeto_id=usuario_id)
    return ok, mensaje


def crear_especialidad(nombre):
    ok, resultado = _crear_especialidad_sin_registro(nombre)
    if ok:
        auditar("usuarios", "crear", f"Especialidad «{(nombre or '').strip()}»")
    return ok, resultado


def renombrar_especialidad(especialidad_id, nombre_nuevo):
    anterior = next((e["nombre"] for e in listar_especialidades() if e["id"] == especialidad_id), "")
    ok, mensaje = _renombrar_especialidad_sin_registro(especialidad_id, nombre_nuevo)
    if ok:
        auditar("usuarios", "editar", f"Especialidad «{(nombre_nuevo or '').strip()}»",
                cambios=diferencias({"n": anterior}, {"n": (nombre_nuevo or "").strip()}, {"n": "Nombre"}))
    return ok, mensaje


def borrar_especialidad(especialidad_id):
    anterior = next((e["nombre"] for e in listar_especialidades() if e["id"] == especialidad_id), "")
    resultado = _borrar_especialidad_sin_registro(especialidad_id)
    auditar("usuarios", "borrar", f"Especialidad «{anterior}»",
            detalle="Se quita a los usuarios, pendientes y avisos que la tenían")
    return resultado


def limpiar_dispositivo_id(valor):
    """Identificador del móvil tal como lo manda la app (letras, cifras y
    «-_.:»; hasta 64), o None si falta o no vale."""
    valor = (valor or "").strip() if isinstance(valor, str) else ""
    if not valor or len(valor) > 64 or not all(c.isalnum() or c in "-_.:" for c in valor):
        return None
    return valor


def registrar_movil(dispositivo_id, modelo=None):
    """Anota (o actualiza) que este móvil ha conectado. El modelo se guarda sin
    el « (Stock)» que MantPro Stock añade a su nombre, para que las dos apps del
    mismo teléfono lo llamen igual."""
    modelo = (modelo or "").replace(" (Stock)", "").strip()[:120]
    con = _conn()
    con.execute(
        "INSERT INTO moviles (dispositivo_id, modelo, visto) VALUES (?, ?, ?) "
        "ON CONFLICT(dispositivo_id) DO UPDATE SET modelo = CASE WHEN excluded.modelo != '' "
        "THEN excluded.modelo ELSE moviles.modelo END, visto = excluded.visto",
        (dispositivo_id, modelo, datetime.now().isoformat(timespec="seconds")))
    con.commit()
    con.close()


def movil_adjudicado(dispositivo_id):
    """{id, login, nombre} del técnico al que está adjudicado el móvil, o None
    si no lo está (o su usuario está dado de baja)."""
    dispositivo_id = limpiar_dispositivo_id(dispositivo_id)
    if not dispositivo_id:
        return None
    con = _conn()
    fila = con.execute(
        "SELECT u.id, u.login, u.nombre FROM moviles m JOIN usuarios u ON u.id = m.usuario_id "
        "WHERE m.dispositivo_id = ? AND u.activo = 1", (dispositivo_id,)).fetchone()
    con.close()
    return dict(fila) if fila else None


def movil_permite_a(usuario, dispositivo_id):
    """(True, None) si [usuario] puede iniciar sesión en ese móvil, o
    (False, adjudicado) si está adjudicado a otro técnico. Los administradores
    pueden entrar en cualquiera (para probar o ayudar); un móvil sin
    adjudicar o que no manda identificador no restringe a nadie."""
    adjudicado = movil_adjudicado(dispositivo_id)
    if adjudicado is None or adjudicado["id"] == usuario["id"] or es_admin(usuario):
        return True, None
    return False, adjudicado


def adjudicar_movil(dispositivo_id, usuario_id):
    """Adjudica el móvil a un técnico (usuario_id None: lo deja libre). Queda
    en el registro de cambios. Las sesiones abiertas no se tocan."""
    dispositivo_id = limpiar_dispositivo_id(dispositivo_id)
    if not dispositivo_id:
        return False
    con = _conn()
    fila = con.execute("SELECT modelo, usuario_id FROM moviles WHERE dispositivo_id = ?", (dispositivo_id,)).fetchone()
    if fila is None:
        con.close()
        return False
    def nombre(uid):
        u = con.execute("SELECT nombre FROM usuarios WHERE id = ?", (uid,)).fetchone() if uid else None
        return u[0] if u else ""
    antes, despues = nombre(fila["usuario_id"]), nombre(usuario_id)
    con.execute("UPDATE moviles SET usuario_id = ? WHERE dispositivo_id = ?", (usuario_id, dispositivo_id))
    con.commit()
    con.close()
    if antes != despues:
        auditar("seguridad", "configurar", fila["modelo"] or dispositivo_id,
                cambios=[{"campo": "Móvil adjudicado a", "antes": antes, "despues": despues}])
    return True


def dispositivo_id_de_token(token):
    try:
        con = _conn()
        fila = con.execute("SELECT dispositivo_id FROM sesiones WHERE token = ?", (token,)).fetchone()
        con.close()
        return (fila[0] or None) if fila else None
    except sqlite3.Error:
        return None


def dispositivo_de_token(token):
    """Modelo del móvil de una sesión («OPPO CPH2781»), o None."""
    try:
        con = _conn()
        fila = con.execute("SELECT dispositivo FROM sesiones WHERE token = ?", (token,)).fetchone()
        con.close()
        return fila[0] if fila else None
    except sqlite3.Error:
        return None
