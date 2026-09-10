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
maquinas.py — Listado de maquinaria y su histórico de trabajos para MantPro.

Las máquinas forman un árbol (una máquina puede tener submáquinas, para poder
agrupar por planta/línea/equipo). Cada trabajo de la tabla "tareas" puede
vincularse opcionalmente a una máquina mediante la columna tareas.maquina_id.

Uso desde main.py:

    import maquinas
    maquinas.configurar_db(RUTA_DB)   # la misma BD que usa el resto de la app
    maquinas.inicializar()            # crea la tabla + migra la columna (idempotente)
"""

import sqlite3
from datetime import datetime

RUTA_DB = "mantenimiento.db"


def configurar_db(ruta):
    """Fija la ruta de la base de datos que usará este módulo."""
    global RUTA_DB
    RUTA_DB = ruta


def _conn():
    con = sqlite3.connect(RUTA_DB)
    con.row_factory = sqlite3.Row
    return con


def inicializar():
    """Crea la tabla de máquinas y añade la columna de vínculo en tareas.

    Es idempotente: se puede llamar en cada arranque sin efectos secundarios.
    """
    con = _conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maquinas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            padre_id  INTEGER,
            notas     TEXT,
            creado    TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_maquinas_padre ON maquinas(padre_id)")

    cols = {fila[1] for fila in cur.execute("PRAGMA table_info(tareas)")}
    if "maquina_id" not in cols:
        cur.execute("ALTER TABLE tareas ADD COLUMN maquina_id INTEGER")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tareas_maquina ON tareas(maquina_id)")

    cols_maquinas = {fila[1] for fila in cur.execute("PRAGMA table_info(maquinas)")}
    if "foto" not in cols_maquinas:
        cur.execute("ALTER TABLE maquinas ADD COLUMN foto TEXT")

    con.commit()
    con.close()


# ---------------------------------------------------------------- CRUD máquinas

def agregar_maquina(nombre, padre_id=None, notas="", foto=None):
    con = _conn()
    con.execute(
        "INSERT INTO maquinas (nombre, padre_id, notas, creado, foto) VALUES (?, ?, ?, ?, ?)",
        (nombre.strip(), padre_id, (notas or "").strip(),
         datetime.now().isoformat(timespec="seconds"), foto),
    )
    con.commit()
    con.close()


def actualizar_maquina(id_maquina, nombre, padre_id, notas, foto=None):
    con = _conn()
    con.execute(
        "UPDATE maquinas SET nombre=?, padre_id=?, notas=?, foto=? WHERE id=?",
        (nombre.strip(), padre_id, (notas or "").strip(), foto, id_maquina),
    )
    con.commit()
    con.close()


def listar_maquinas():
    """Todas las máquinas (planas, con su padre_id), ordenadas por nombre."""
    con = _conn()
    filas = con.execute(
        "SELECT id, nombre, padre_id, notas, foto FROM maquinas ORDER BY nombre COLLATE NOCASE"
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]


def obtener_maquina(id_maquina):
    con = _conn()
    fila = con.execute(
        "SELECT id, nombre, padre_id, notas, foto FROM maquinas WHERE id=?", (id_maquina,)
    ).fetchone()
    con.close()
    return dict(fila) if fila else None


def mapa_rutas_completas():
    """Devuelve {id_maquina: 'Máquina padre > Submáquina'} para todas las
    máquinas, útil para mostrar en informes y exportaciones."""
    todas = {m["id"]: m for m in listar_maquinas()}
    cache = {}

    def ruta(id_maquina):
        if id_maquina in cache:
            return cache[id_maquina]
        m = todas.get(id_maquina)
        if not m:
            return ""
        padre = ruta(m["padre_id"]) if m["padre_id"] else ""
        completo = f"{padre} > {m['nombre']}" if padre else m["nombre"]
        cache[id_maquina] = completo
        return completo

    for id_maquina in todas:
        ruta(id_maquina)
    return cache


def _descendientes(con, id_maquina):
    """IDs de una máquina y de todas sus submáquinas, recursivamente."""
    ids = [id_maquina]
    for (hijo_id,) in con.execute("SELECT id FROM maquinas WHERE padre_id=?", (id_maquina,)):
        ids.extend(_descendientes(con, hijo_id))
    return ids


def descendientes_ids(id_maquina):
    """IDs de una máquina y de todas sus submáquinas, recursivamente."""
    con = _conn()
    ids = _descendientes(con, id_maquina)
    con.close()
    return ids


def borrar_maquina(id_maquina):
    """Borra la máquina y sus submáquinas. Los trabajos ya registrados en ellas
    no se eliminan: simplemente quedan sin máquina asignada."""
    con = _conn()
    ids = _descendientes(con, id_maquina)
    marcas = ",".join("?" * len(ids))
    con.execute(f"UPDATE tareas SET maquina_id=NULL WHERE maquina_id IN ({marcas})", ids)
    con.execute(f"DELETE FROM maquinas WHERE id IN ({marcas})", ids)
    con.commit()
    con.close()


# ---------------------------------------------------------------- trabajos por máquina

def contar_trabajos(id_maquina):
    """Nº de trabajos vinculados directamente a esta máquina (sin submáquinas)."""
    con = _conn()
    fila = con.execute("SELECT COUNT(*) FROM tareas WHERE maquina_id=?", (id_maquina,)).fetchone()
    con.close()
    return fila[0] if fila else 0


def anios_de_maquina(id_maquina):
    """Años con trabajos en esta máquina y cuántos trabajos tiene cada uno."""
    con = _conn()
    filas = con.execute(
        "SELECT substr(fecha,1,4) AS anio, COUNT(*) FROM tareas "
        "WHERE maquina_id=? AND fecha IS NOT NULL AND fecha != '' "
        "GROUP BY anio ORDER BY anio DESC",
        (id_maquina,),
    ).fetchall()
    con.close()
    return [(f[0], f[1]) for f in filas]


def meses_de_maquina_anio(id_maquina, anio):
    """Meses (01-12) con trabajos de esta máquina en el año dado, con su contador."""
    con = _conn()
    filas = con.execute(
        "SELECT substr(fecha,6,2) AS mes, COUNT(*) FROM tareas "
        "WHERE maquina_id=? AND substr(fecha,1,4)=? "
        "GROUP BY mes ORDER BY mes DESC",
        (id_maquina, anio),
    ).fetchall()
    con.close()
    return [(f[0], f[1]) for f in filas if f[0]]


def trabajos_de_maquina_anio_mes(id_maquina, anio, mes):
    con = _conn()
    filas = con.execute(
        "SELECT id, fecha, descripcion, tags FROM tareas WHERE maquina_id=? "
        "AND substr(fecha,1,4)=? AND substr(fecha,6,2)=? ORDER BY fecha DESC, id DESC",
        (id_maquina, anio, mes),
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]
