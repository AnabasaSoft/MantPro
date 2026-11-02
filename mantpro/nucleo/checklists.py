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
checklists.py — Listas de comprobación de preventivos y trabajos.

- **Plantillas** reutilizables («Revisión mensual de compresor») con sus
  puntos. Cada punto es de tipo «estado» (se marca bien / mal / no aplica) o
  «lectura» (además se apunta un valor con su unidad; si tiene mínimo o
  máximo y el valor se sale, el punto queda como «mal»).
- Una plantilla se asigna a avisos recurrentes y a pendientes
  (columna checklist_id).
- Al completar, lo rellenado se guarda **como copia** junto al trabajo del
  historial (checklist_resultados): si la plantilla cambia después, lo ya
  hecho no cambia.

Todo vive en mantenimiento.db.
"""

import json

from .conexion_bd import sqlite3, conectar

RUTA_DB = None

TIPOS = ("estado", "lectura")
ESTADOS = ("ok", "mal", "na")


def configurar_db(ruta):
    global RUTA_DB
    RUTA_DB = ruta


def _conn():
    con = conectar(RUTA_DB, timeout=20)
    con.row_factory = sqlite3.Row
    return con


def _columnas(con, tabla):
    return {f[1] for f in con.execute(f"PRAGMA table_info({tabla})")}


def inicializar():
    con = _conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS checklist_plantillas (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS checklist_puntos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            plantilla_id INTEGER NOT NULL,
            orden        INTEGER NOT NULL,
            texto        TEXT NOT NULL,
            tipo         TEXT NOT NULL DEFAULT 'estado',
            unidad       TEXT,
            minimo       REAL,
            maximo       REAL,
            FOREIGN KEY (plantilla_id) REFERENCES checklist_plantillas(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_checklist_puntos ON checklist_puntos(plantilla_id, orden);
        CREATE TABLE IF NOT EXISTS checklist_resultados (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            tarea_id  INTEGER NOT NULL,
            plantilla TEXT,
            orden     INTEGER NOT NULL,
            texto     TEXT NOT NULL,
            tipo      TEXT NOT NULL DEFAULT 'estado',
            unidad    TEXT,
            minimo    REAL,
            maximo    REAL,
            estado    TEXT,
            valor     TEXT,
            nota      TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_checklist_resultados ON checklist_resultados(tarea_id, orden);
    """)
    for tabla in ("avisos_recurrentes", "pendientes"):
        try:
            if "checklist_id" not in _columnas(con, tabla):
                con.execute(f"ALTER TABLE {tabla} ADD COLUMN checklist_id INTEGER")
        except sqlite3.OperationalError:
            pass   # la tabla aún no existe: la crea GestorBaseDatos y se añade al volver a llamar
    con.commit()
    con.close()


# ---------------------------------------------------------------- plantillas

def _num(v):
    """Número o None a partir de lo que escriba el usuario («6,5», «», None)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    texto = str(v).strip().replace(",", ".")
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def _punto(fila):
    return {"texto": fila["texto"], "tipo": fila["tipo"] or "estado", "unidad": fila["unidad"] or "",
            "minimo": fila["minimo"], "maximo": fila["maximo"]}


def listar_plantillas():
    """[{id, nombre, puntos: [...]}] ordenadas por nombre."""
    con = _conn()
    plantillas = [dict(f) for f in con.execute(
        "SELECT id, nombre FROM checklist_plantillas ORDER BY nombre COLLATE NOCASE")]
    puntos = {}
    for f in con.execute("SELECT * FROM checklist_puntos ORDER BY plantilla_id, orden"):
        puntos.setdefault(f["plantilla_id"], []).append(_punto(f))
    con.close()
    for p in plantillas:
        p["puntos"] = puntos.get(p["id"], [])
    return plantillas


def obtener_plantilla(plantilla_id):
    if not plantilla_id:
        return None
    return next((p for p in listar_plantillas() if p["id"] == plantilla_id), None)


def guardar_plantilla(plantilla_id, nombre, puntos):
    """Crea (plantilla_id None) o actualiza una plantilla con sus puntos
    [{texto, tipo, unidad, minimo, maximo}]. Devuelve su id."""
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("nombre")
    limpios = []
    for p in puntos:
        texto = (p.get("texto") or "").strip()
        if not texto:
            continue
        tipo = p.get("tipo") if p.get("tipo") in TIPOS else "estado"
        limpios.append((texto, tipo,
                        (p.get("unidad") or "").strip() if tipo == "lectura" else None,
                        _num(p.get("minimo")) if tipo == "lectura" else None,
                        _num(p.get("maximo")) if tipo == "lectura" else None))
    con = _conn()
    try:
        if plantilla_id:
            con.execute("UPDATE checklist_plantillas SET nombre=? WHERE id=?", (nombre, plantilla_id))
            con.execute("DELETE FROM checklist_puntos WHERE plantilla_id=?", (plantilla_id,))
        else:
            plantilla_id = con.execute("INSERT INTO checklist_plantillas (nombre) VALUES (?)", (nombre,)).lastrowid
        con.executemany(
            "INSERT INTO checklist_puntos (plantilla_id, orden, texto, tipo, unidad, minimo, maximo) "
            "VALUES (?,?,?,?,?,?,?)",
            [(plantilla_id, i, *p) for i, p in enumerate(limpios)])
        con.commit()
    finally:
        con.close()
    return plantilla_id


def borrar_plantilla(plantilla_id):
    """Borra la plantilla y la quita de los avisos y pendientes que la usaban.
    Lo ya rellenado en el historial se conserva."""
    con = _conn()
    con.execute("DELETE FROM checklist_puntos WHERE plantilla_id=?", (plantilla_id,))
    con.execute("DELETE FROM checklist_plantillas WHERE id=?", (plantilla_id,))
    for tabla in ("avisos_recurrentes", "pendientes"):
        con.execute(f"UPDATE {tabla} SET checklist_id=NULL WHERE checklist_id=?", (plantilla_id,))
    con.commit()
    con.close()


def usos_de_plantilla(plantilla_id):
    """(avisos, pendientes) que usan la plantilla."""
    con = _conn()
    a = con.execute("SELECT COUNT(*) FROM avisos_recurrentes WHERE checklist_id=?", (plantilla_id,)).fetchone()[0]
    p = con.execute("SELECT COUNT(*) FROM pendientes WHERE checklist_id=?", (plantilla_id,)).fetchone()[0]
    con.close()
    return a, p


# ------------------------------------------------- asignación a avisos/pendientes

def _tabla(tipo):
    return {"aviso": "avisos_recurrentes", "pendiente": "pendientes"}[tipo]


def checklist_de(tipo, item_id):
    """id de la plantilla asignada a un aviso o pendiente, o None."""
    con = _conn()
    fila = con.execute(f"SELECT checklist_id FROM {_tabla(tipo)} WHERE id=?", (item_id,)).fetchone()
    con.close()
    return fila[0] if fila else None


def checklists_de(tipo):
    """{id del aviso o pendiente: id de la plantilla} de todos los que tienen una."""
    con = _conn()
    filas = con.execute(f"SELECT id, checklist_id FROM {_tabla(tipo)} WHERE checklist_id IS NOT NULL").fetchall()
    con.close()
    return {f[0]: f[1] for f in filas}


def asignar(tipo, item_id, plantilla_id):
    con = _conn()
    con.execute(f"UPDATE {_tabla(tipo)} SET checklist_id=? WHERE id=?", (plantilla_id or None, item_id))
    con.commit()
    con.close()


# ---------------------------------------------------------------- resultados

def fuera_de_rango(punto, valor):
    """True si una lectura se sale del mínimo o el máximo del punto."""
    n = _num(valor)
    if n is None:
        return False
    minimo, maximo = _num(punto.get("minimo")), _num(punto.get("maximo"))
    return (minimo is not None and n < minimo) or (maximo is not None and n > maximo)


def items_de_plantilla(plantilla):
    """Puntos de una plantilla listos para rellenar (sin estado ni valor)."""
    return [dict(p, estado=None, valor="", nota="") for p in plantilla["puntos"]]


def normalizar_items(items):
    """Limpia lo que llega del PC o del móvil (lista de dicts o JSON)."""
    if isinstance(items, str):
        try:
            items = json.loads(items) if items.strip() else []
        except ValueError:
            items = []
    limpios = []
    for it in items or []:
        if not isinstance(it, dict) or not str(it.get("texto") or "").strip():
            continue
        tipo = it.get("tipo") if it.get("tipo") in TIPOS else "estado"
        estado = it.get("estado") if it.get("estado") in ESTADOS else None
        valor = str(it.get("valor") or "").strip() if tipo == "lectura" else ""
        limpios.append({
            "texto": str(it["texto"]).strip()[:500], "tipo": tipo,
            "unidad": str(it.get("unidad") or "").strip()[:30] if tipo == "lectura" else "",
            "minimo": _num(it.get("minimo")), "maximo": _num(it.get("maximo")),
            "estado": estado, "valor": valor[:60], "nota": str(it.get("nota") or "").strip()[:1000]})
    return limpios


def guardar_resultado(tarea_id, items, plantilla_nombre="", con=None):
    """Guarda lo rellenado junto al trabajo [tarea_id] (sustituye lo que hubiera)."""
    items = normalizar_items(items)
    propia = con is None
    if propia:
        con = _conn()
    con.execute("DELETE FROM checklist_resultados WHERE tarea_id=?", (tarea_id,))
    con.executemany(
        "INSERT INTO checklist_resultados (tarea_id, plantilla, orden, texto, tipo, unidad, minimo, maximo, estado, valor, nota) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [(tarea_id, plantilla_nombre or "", i, it["texto"], it["tipo"], it["unidad"], it["minimo"], it["maximo"],
          it["estado"], it["valor"], it["nota"]) for i, it in enumerate(items)])
    if propia:
        con.commit()
        con.close()


def resultados_de(tarea_ids):
    """{tarea_id: {"plantilla": nombre, "items": [...]}} de esos trabajos."""
    ids = [int(i) for i in tarea_ids if i is not None]
    if not ids:
        return {}
    con = _conn()
    resultado = {}
    for trozo in range(0, len(ids), 500):
        parte = ids[trozo:trozo + 500]
        marcas = ",".join("?" * len(parte))
        for f in con.execute(f"SELECT * FROM checklist_resultados WHERE tarea_id IN ({marcas}) "
                             f"ORDER BY tarea_id, orden", parte):
            r = resultado.setdefault(f["tarea_id"], {"plantilla": f["plantilla"] or "", "items": []})
            r["items"].append({"texto": f["texto"], "tipo": f["tipo"], "unidad": f["unidad"] or "",
                               "minimo": f["minimo"], "maximo": f["maximo"], "estado": f["estado"],
                               "valor": f["valor"] or "", "nota": f["nota"] or ""})
    con.close()
    return resultado


def resultado_de(tarea_id):
    return resultados_de([tarea_id]).get(int(tarea_id)) if tarea_id is not None else None


def borrar_resultado(tarea_id, con=None):
    propia = con is None
    if propia:
        con = _conn()
    con.execute("DELETE FROM checklist_resultados WHERE tarea_id=?", (tarea_id,))
    if propia:
        con.commit()
        con.close()


def recuento(items):
    """{"ok", "mal", "na", "sin"} de una lista rellenada."""
    r = {"ok": 0, "mal": 0, "na": 0, "sin": 0}
    for it in items:
        r[it.get("estado") if it.get("estado") in ESTADOS else "sin"] += 1
    return r


def sin_marcar(items):
    return [it for it in items if it.get("estado") not in ESTADOS]
