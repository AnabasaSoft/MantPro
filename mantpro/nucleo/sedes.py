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
sedes.py — Varias sedes (plantas propias o empresas cliente) para MantPro (motor, sin Qt).

Fase 1 de «Varias sedes» (ROADMAP.md). Reglas:

  * Siempre hay una sede PRINCIPAL (se crea sola, con uuid fijo `sede-principal`
    para que dos PCs de la misma empresa no creen dos distintas al sincronizar).
  * `sede_id` NULL significa «sede principal». Así los datos de antes no hay que
    tocarlos (rellenarlos subiría a la nube todos los registros de cada PC a la vez).
    Para filtrar se usa siempre `condicion()`, que ya lo tiene en cuenta.
  * Máquinas: la sede se elige en las máquinas raíz; las submáquinas y los
    trabajos de una máquina llevan la sede de su máquina (disparadores y
    `asignar_maquina()` / `al_mover_maquina()`).
  * Pendientes y avisos llevan su propia sede (la que elija quien los crea).
  * Quien solo tiene una sede activa no ve nada nuevo (`hay_varias()`).

Uso (lo hace GestorBaseDatos):

    from mantpro.nucleo import sedes
    sedes.configurar_db(RUTA_DB)
    sedes.inicializar()      # tabla, columnas, disparadores y sede principal (idempotente)
"""

from .conexion_bd import sqlite3, conectar
from . import usuarios as _usuarios

RUTA_DB = "mantenimiento.db"
UUID_PRINCIPAL = "sede-principal"
TIPO_PROPIA = "propia"
TIPO_CLIENTE = "cliente"
TIPOS = (TIPO_PROPIA, TIPO_CLIENTE)
# Tablas de mantenimiento.db que llevan sede (las de las máquinas la heredan)
TABLAS_CON_SEDE = ("maquinas", "tareas", "pendientes", "avisos_recurrentes")
CAMPOS = ("nombre", "tipo", "cif", "direccion", "contacto", "telefono", "email", "notas")


def configurar_db(ruta):
    """Fija la ruta de la base de datos que usará este módulo."""
    global RUTA_DB
    RUTA_DB = ruta


def _conn():
    con = conectar(RUTA_DB, timeout=20)
    con.row_factory = sqlite3.Row
    return con


def _t(clave, defecto=None):
    """Texto traducido; si el idioma aún no lo tiene (devuelve la clave), [defecto]."""
    from .. import idiomas
    texto = idiomas.t(clave)
    return defecto if (defecto and texto == clave) else texto


def inicializar():
    """Crea la tabla, añade `sede_id` donde hace falta, (re)crea los disparadores
    que hacen heredar la sede de la máquina y se asegura de que haya sede principal.
    Idempotente. Necesita que existan ya las tablas de TABLAS_CON_SEDE."""
    con = _conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS sedes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            tipo      TEXT NOT NULL DEFAULT 'propia',
            cif       TEXT,
            direccion TEXT,
            contacto  TEXT,
            telefono  TEXT,
            email     TEXT,
            notas     TEXT,
            activa    INTEGER NOT NULL DEFAULT 1,
            principal INTEGER NOT NULL DEFAULT 0,
            uuid      TEXT
        )
    """)
    # Festivos de la sede (vacío = los generales de la empresa, en config)
    cols_sedes = {f[1] for f in con.execute("PRAGMA table_info(sedes)")}
    for col in ("pais_iso", "region_iso", "parent_iso"):
        if col not in cols_sedes:
            con.execute(f"ALTER TABLE sedes ADD COLUMN {col} TEXT")
    for tabla in TABLAS_CON_SEDE:
        cols = {f[1] for f in con.execute(f"PRAGMA table_info({tabla})")}
        if "sede_id" not in cols:
            con.execute(f"ALTER TABLE {tabla} ADD COLUMN sede_id INTEGER")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{tabla}_sede ON {tabla}(sede_id)")

    # Una submáquina nueva lleva la sede de su máquina superior (si no la trae ya,
    # como lo que llega de la nube).
    con.execute("DROP TRIGGER IF EXISTS sede_maquinas_ai")
    con.execute("""
        CREATE TRIGGER sede_maquinas_ai AFTER INSERT ON maquinas
        WHEN NEW.padre_id IS NOT NULL AND NEW.sede_id IS NULL
        BEGIN
            UPDATE maquinas SET sede_id = (SELECT sede_id FROM maquinas WHERE id = NEW.padre_id)
            WHERE id = NEW.id;
        END
    """)
    # Un trabajo con máquina lleva la sede de la máquina: al crearlo (si no la trae)
    # y cada vez que se le cambia la máquina. Sin máquina conserva la que tenga.
    con.execute("DROP TRIGGER IF EXISTS sede_tareas_ai")
    con.execute("""
        CREATE TRIGGER sede_tareas_ai AFTER INSERT ON tareas
        WHEN NEW.maquina_id IS NOT NULL AND NEW.sede_id IS NULL
        BEGIN
            UPDATE tareas SET sede_id = (SELECT sede_id FROM maquinas WHERE id = NEW.maquina_id)
            WHERE id = NEW.id;
        END
    """)
    con.execute("DROP TRIGGER IF EXISTS sede_tareas_au")
    con.execute("""
        CREATE TRIGGER sede_tareas_au AFTER UPDATE OF maquina_id ON tareas
        WHEN NEW.maquina_id IS NOT NULL AND NEW.maquina_id IS NOT OLD.maquina_id
        BEGIN
            UPDATE tareas SET sede_id = (SELECT sede_id FROM maquinas WHERE id = NEW.maquina_id)
            WHERE id = NEW.id;
        END
    """)
    # Qué sedes ve cada usuario (fase 2). Sin filas = todas; un administrador, siempre todas.
    con.execute("""
        CREATE TABLE IF NOT EXISTS usuario_sedes (
            usuario_id INTEGER NOT NULL,
            sede_id    INTEGER NOT NULL,
            PRIMARY KEY (usuario_id, sede_id)
        )
    """)
    if not con.execute("SELECT 1 FROM sedes WHERE principal = 1").fetchone():
        con.execute("INSERT INTO sedes (nombre, tipo, principal, uuid) VALUES (?, ?, 1, ?)",
                    (_t("sede_principal_nombre", "Sede principal"), TIPO_PROPIA, UUID_PRINCIPAL))
    con.execute("UPDATE sedes SET nombre = ? WHERE nombre = 'sede_principal_nombre'",
                (_t("sede_principal_nombre", "Sede principal"),))
    con.commit()
    con.close()


# ---------------------------------------------------------------- consultas

def listar(incluir_inactivas=False):
    """Sedes como dicts, la principal primero y después por nombre."""
    con = _conn()
    sql = "SELECT * FROM sedes" + ("" if incluir_inactivas else " WHERE activa = 1")
    filas = con.execute(sql + " ORDER BY principal DESC, nombre COLLATE NOCASE").fetchall()
    con.close()
    return [dict(f) for f in filas]


def obtener(sede_id):
    con = _conn()
    fila = con.execute("SELECT * FROM sedes WHERE id = ?", (sede_id,)).fetchone()
    con.close()
    return dict(fila) if fila else None


def principal_id():
    """Id de la sede principal (la que tienen los registros sin sede)."""
    con = _conn()
    fila = con.execute("SELECT id FROM sedes WHERE principal = 1 ORDER BY id LIMIT 1").fetchone()
    con.close()
    return fila[0] if fila else None


def hay_varias():
    """True si hay más de una sede activa (solo entonces se ve el selector)."""
    con = _conn()
    n = con.execute("SELECT COUNT(*) FROM sedes WHERE activa = 1").fetchone()[0]
    con.close()
    return n > 1


def efectiva(sede_id):
    """La sede de un registro: la suya o, si no tiene, la principal."""
    return sede_id if sede_id is not None else principal_id()


def guardable(sede_id):
    """Lo que se guarda en `sede_id`: la principal como NULL (igual que lo antiguo)."""
    if sede_id is None or sede_id == principal_id():
        return None
    return int(sede_id)


def _lista(sede):
    """[sede] como lista de ids (un id, una lista) o None (todas)."""
    if sede is None:
        return None
    if isinstance(sede, (list, tuple, set)):
        return [int(x) for x in sede]
    return [int(sede)]


def condicion(sede, columna="sede_id"):
    """Trozo de WHERE que deja solo los registros de [sede]: un id, una lista de ids
    (las sedes de un técnico) o None (todas). Los registros sin sede cuentan como de
    la principal. Solo enteros: se puede interpolar sin riesgo."""
    ids = _lista(sede)
    if ids is None:
        return "1=1"
    texto = ",".join(str(i) for i in ids) or "NULL"
    pid = principal_id()
    if pid is None:
        return f"{columna} IN ({texto})"
    return f"COALESCE({columna}, {int(pid)}) IN ({texto})"


def de_la_sede(registro_sede_id, sede):
    """Para filtrar en Python: ¿un registro con [registro_sede_id] es de [sede]
    (un id, una lista o None = todas)?"""
    ids = _lista(sede)
    return ids is None or efectiva(registro_sede_id) in ids


# ---------------------------------------------------------------- qué sedes ve cada usuario

def de_usuario(usuario_id):
    """Ids de las sedes marcadas a un usuario ([] si ninguna = las ve todas)."""
    con = _conn()
    ids = [f[0] for f in con.execute("SELECT sede_id FROM usuario_sedes WHERE usuario_id = ? ORDER BY sede_id",
                                     (usuario_id,))]
    con.close()
    return ids


def permitidas(usuario=None):
    """Sedes que puede ver [usuario] (dict de sesión; por defecto el de este PC):
    None = todas (administrador, o sin ninguna marcada), o la lista de ids."""
    u = usuario if usuario is not None else _usuarios.SESION_ACTUAL
    if not u or _usuarios.es_admin(u):
        return None
    ids = de_usuario(u.get("id"))
    return ids or None


def fijar_de_usuario(usuario_id, sede_ids):
    """Marca las sedes que ve un usuario (lista vacía = todas)."""
    sede_ids = sorted({int(i) for i in (sede_ids or [])})
    antes = de_usuario(usuario_id)
    if antes == sede_ids:
        return
    con = _conn()
    if sede_ids:
        con.execute("DELETE FROM usuario_sedes WHERE usuario_id = ? AND sede_id NOT IN (%s)"
                    % ",".join("?" * len(sede_ids)), [usuario_id, *sede_ids])
    else:   # ninguna marcada = todas (ojo: «NOT IN (NULL)» no borraría nada)
        con.execute("DELETE FROM usuario_sedes WHERE usuario_id = ?", (usuario_id,))
    for sid in sede_ids:
        con.execute("INSERT OR IGNORE INTO usuario_sedes (usuario_id, sede_id) VALUES (?, ?)", (usuario_id, sid))
    con.commit()
    nombre = con.execute("SELECT nombre FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    con.close()
    todas = nombres()
    _usuarios.auditar("usuarios", "editar", nombre[0] if nombre else str(usuario_id),
                      detalle=_t("sede_aud_usuario").format(
                          sedes=", ".join(todas.get(i, str(i)) for i in sede_ids) or _t("sede_todas")))


def visibles(usuario=None):
    """Sedes activas que puede ver [usuario] (dicts)."""
    ids = permitidas(usuario)
    return [s for s in listar() if ids is None or s["id"] in ids]


def para_nuevo(sede, usuario=None):
    """Sede de algo nuevo cuando lo elegido es [sede] (un id, una lista o None): ese id; con
    varias, la principal si se puede, si no la primera permitida."""
    ids = _lista(sede)
    if ids is None:
        return None
    if len(ids) == 1:
        return ids[0]
    pid = principal_id()
    return pid if pid in ids else (ids[0] if ids else None)


def sede_de(tabla, registro_id):
    """Sede guardada de un trabajo, pendiente o aviso (NULL = principal, tal cual)."""
    if tabla not in TABLAS_CON_SEDE:
        raise ValueError(tabla)
    con = _conn()
    fila = con.execute(f"SELECT sede_id FROM {tabla} WHERE id = ?", (registro_id,)).fetchone()
    con.close()
    return fila[0] if fila else None


def sede_de_maquina(maquina_id):
    """Sede efectiva de una máquina (None si la máquina no existe)."""
    con = _conn()
    fila = con.execute("SELECT sede_id FROM maquinas WHERE id = ?", (maquina_id,)).fetchone()
    con.close()
    return efectiva(fila[0]) if fila else None


def nombres():
    """{id: nombre} de todas las sedes (también las inactivas, para el historial)."""
    return {s["id"]: s["nombre"] for s in listar(incluir_inactivas=True)}


def en_uso(sede_id):
    """Cuántos registros de cada tabla son de la sede (sin contar la principal implícita)."""
    con = _conn()
    usos = {t: con.execute(f"SELECT COUNT(*) FROM {t} WHERE sede_id = ?", (sede_id,)).fetchone()[0]
            for t in TABLAS_CON_SEDE}
    con.close()
    return usos


# ---------------------------------------------------------------- altas y cambios

def _limpiar(datos):
    d = {c: (str(datos.get(c) or "").strip()) for c in CAMPOS}
    if d["tipo"] not in TIPOS:
        d["tipo"] = TIPO_PROPIA
    return d


def _nombre_repetido(con, nombre, excluir_id=None):
    fila = con.execute("SELECT id FROM sedes WHERE lower(trim(nombre)) = lower(?) AND id IS NOT ?",
                       (nombre, excluir_id)).fetchone()
    return fila is not None


def crear(datos):
    """Da de alta una sede. Devuelve (id, None) o (None, código de error):
    'sin_nombre' o 'nombre_repetido'."""
    d = _limpiar(datos)
    if not d["nombre"]:
        return None, "sin_nombre"
    con = _conn()
    if _nombre_repetido(con, d["nombre"]):
        con.close()
        return None, "nombre_repetido"
    cur = con.execute(f"INSERT INTO sedes ({', '.join(CAMPOS)}) VALUES ({', '.join('?' * len(CAMPOS))})",
                      [d[c] for c in CAMPOS])
    nuevo = cur.lastrowid
    con.commit()
    con.close()
    _usuarios.auditar("configuracion", "crear", _t("sede_auditoria").format(nombre=d["nombre"]))
    return nuevo, None


def actualizar(sede_id, datos):
    """Cambia los datos de una sede. Devuelve None o el código de error."""
    d = _limpiar(datos)
    if not d["nombre"]:
        return "sin_nombre"
    con = _conn()
    if _nombre_repetido(con, d["nombre"], sede_id):
        con.close()
        return "nombre_repetido"
    con.execute(f"UPDATE sedes SET {', '.join(c + ' = ?' for c in CAMPOS)} WHERE id = ?",
                [d[c] for c in CAMPOS] + [sede_id])
    con.commit()
    con.close()
    _usuarios.auditar("configuracion", "editar", _t("sede_auditoria").format(nombre=d["nombre"]))
    return None


def activar(sede_id, activa):
    """Activa o desactiva una sede (la principal no se puede desactivar).
    Devuelve None o 'es_principal'."""
    s = obtener(sede_id)
    if not s:
        return None
    if s["principal"] and not activa:
        return "es_principal"
    con = _conn()
    con.execute("UPDATE sedes SET activa = ? WHERE id = ?", (1 if activa else 0, sede_id))
    con.commit()
    con.close()
    _usuarios.auditar("configuracion", "activar" if activa else "desactivar",
                      _t("sede_auditoria").format(nombre=s["nombre"]))
    return None


def borrar(sede_id):
    """Borra una sede sin datos. Devuelve None o el código de error:
    'es_principal' o 'en_uso' (entonces se puede desactivar)."""
    s = obtener(sede_id)
    if not s:
        return None
    if s["principal"]:
        return "es_principal"
    if any(en_uso(sede_id).values()):
        return "en_uso"
    con = _conn()
    con.execute("DELETE FROM usuario_sedes WHERE sede_id = ?", (sede_id,))
    con.execute("DELETE FROM sedes WHERE id = ?", (sede_id,))
    con.commit()
    con.close()
    _usuarios.auditar("configuracion", "borrar", _t("sede_auditoria").format(nombre=s["nombre"]))
    return None


def _raiz(con, maquina_id):
    vistos = set()
    actual = maquina_id
    while actual is not None and actual not in vistos:
        vistos.add(actual)
        fila = con.execute("SELECT padre_id FROM maquinas WHERE id = ?", (actual,)).fetchone()
        if not fila or fila[0] is None:
            return actual
        actual = fila[0]
    return actual


def _arbol(con, raiz):
    ids, pila = [], [raiz]
    while pila:
        m = pila.pop()
        if m in ids:
            continue
        ids.append(m)
        pila.extend(f[0] for f in con.execute("SELECT id FROM maquinas WHERE padre_id = ?", (m,)))
    return ids


def _poner_sede_arbol(con, raiz, sede_id):
    """Pone [sede_id] a la máquina [raiz], sus submáquinas y sus trabajos.
    Solo toca las filas que cambian (cada cambio se sincroniza)."""
    sede_id = guardable(sede_id)
    ids = _arbol(con, raiz)
    marcas = ",".join("?" * len(ids))
    con.execute(f"UPDATE maquinas SET sede_id = ? WHERE id IN ({marcas}) AND sede_id IS NOT ?",
                [sede_id, *ids, sede_id])
    con.execute(f"UPDATE tareas SET sede_id = ? WHERE maquina_id IN ({marcas}) AND sede_id IS NOT ?",
                [sede_id, *ids, sede_id])
    return ids


def asignar_maquina(maquina_id, sede_id):
    """Cambia la sede de una máquina: se aplica a toda su máquina raíz (las
    submáquinas siempre van con su raíz) y a los trabajos de todas ellas.
    Devuelve cuántas máquinas cambian de árbol (las del árbol completo)."""
    con = _conn()
    raiz = _raiz(con, maquina_id)
    ids = _poner_sede_arbol(con, raiz, sede_id)
    con.commit()
    con.close()
    return len(ids)


def al_mover_maquina(maquina_id):
    """Tras cambiar la máquina superior de [maquina_id]: ella, sus submáquinas y
    sus trabajos pasan a la sede de su nueva raíz."""
    con = _conn()
    raiz = _raiz(con, maquina_id)
    fila = con.execute("SELECT sede_id FROM maquinas WHERE id = ?", (raiz,)).fetchone()
    if fila is not None and raiz != maquina_id:
        _poner_sede_arbol(con, maquina_id, efectiva(fila[0]))
        con.commit()
    con.close()


def fijar_festivos(sede_id, pais_iso=None, region_iso=None, parent_iso=None):
    """Región de festivos propia de la sede. Sin país = los generales de la empresa."""
    s = obtener(sede_id)
    if not s:
        return
    pais_iso = (pais_iso or "").strip() or None
    valores = (pais_iso, (region_iso or None) if pais_iso else None, (parent_iso or None) if pais_iso else None)
    con = _conn()
    con.execute("UPDATE sedes SET pais_iso = ?, region_iso = ?, parent_iso = ? WHERE id = ?", (*valores, sede_id))
    con.commit()
    con.close()
    _usuarios.auditar("configuracion", "editar", _t("sede_auditoria").format(nombre=s["nombre"]),
                      detalle=_t("sede_aud_festivos").format(region=" / ".join(v for v in valores if v) or "—"))


def poner_sede(tabla, registro_id, sede_id):
    """Fija la sede de un pendiente o aviso (la principal se guarda como NULL)."""
    if tabla not in ("pendientes", "avisos_recurrentes"):
        raise ValueError(tabla)
    sede_id = guardable(sede_id)
    con = _conn()
    con.execute(f"UPDATE {tabla} SET sede_id = ? WHERE id = ? AND sede_id IS NOT ?", (sede_id, registro_id, sede_id))
    con.commit()
    con.close()
