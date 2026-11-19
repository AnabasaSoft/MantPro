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
  máximo y el valor se sale, el punto queda como «mal») o «trifasica» (motor
  trifásico: tres lecturas, una por fase L1/L2/L3, guardadas en el mismo campo
  `valor` como «12,1;12,3;12,0»; el mínimo y el máximo valen para cada fase y
  se calcula el desequilibrio entre fases para ver si una consume más; si se
  pasa del «desequilibrio máximo %» del punto, el punto queda como «mal»).
  También hay «seccion»: un separador (zona o máquina) que agrupa los puntos
  que le siguen; no se marca ni cuenta en los recuentos.
- Una plantilla se asigna a avisos recurrentes y a pendientes
  (columna checklist_id).
- Al completar, lo rellenado se guarda **como copia** junto al trabajo del
  historial (checklist_resultados): si la plantilla cambia después, lo ya
  hecho no cambia.

Todo vive en mantenimiento.db.
"""

import hashlib
import json
import uuid

from .conexion_bd import sqlite3, conectar

RUTA_DB = None

TIPOS = ("estado", "lectura", "trifasica", "seccion")
SECCION = "seccion"     # separador: título de zona o máquina, sin estado ni valor
TIPOS_CON_VALOR = ("lectura", "trifasica")      # los que llevan unidad, mínimo, máximo y valor
FASES = ("L1", "L2", "L3")
SEP_FASES = ";"   # separador de las tres lecturas en `valor` (no «,», que es la coma decimal)
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
        -- Listas a medias (se dejan para seguir otro día). Locales de este PC: no se
        -- sincronizan (no están en sincronizacion.py) ni dependen de ninguna otra tabla.
        CREATE TABLE IF NOT EXISTS checklist_borradores (
            clave      TEXT PRIMARY KEY,
            plantilla  TEXT,
            fecha      TEXT,
            items      TEXT
        );
    """)
    # Desequilibrio máximo (%) entre fases de los puntos trifásicos. Columna añadida
    # después: la sincronización ignora las columnas que no conoce, así que una versión
    # anterior en otro PC o en la nube simplemente no la usa.
    for tabla in ("checklist_puntos", "checklist_resultados"):
        if "desequilibrio_max" not in _columnas(con, tabla):
            con.execute(f"ALTER TABLE {tabla} ADD COLUMN desequilibrio_max REAL")
    # Identidad fija de cada punto (punto_uid): sobrevive a renombrarlo o cambiarle el rango,
    # así la evolución de sus lecturas y las listas a medias no se parten. Se copia con cada
    # lista rellenada. Lo anterior a esta columna recibe uno calculado (plantilla + texto +
    # unidad): el mismo en todos los PC y en la nube, sin tener que ponerse de acuerdo.
    for tabla in ("checklist_puntos", "checklist_resultados"):
        if "punto_uid" not in _columnas(con, tabla):
            con.execute(f"ALTER TABLE {tabla} ADD COLUMN punto_uid TEXT")
    con.create_function("_uid_antiguo", 3, uid_antiguo)
    con.execute("""UPDATE checklist_puntos SET punto_uid = _uid_antiguo(
                       (SELECT nombre FROM checklist_plantillas pl WHERE pl.id = checklist_puntos.plantilla_id), texto, unidad)
                   WHERE punto_uid IS NULL""")
    con.execute("UPDATE checklist_resultados SET punto_uid = _uid_antiguo(plantilla, texto, unidad) "
                "WHERE punto_uid IS NULL AND tipo != 'seccion'")
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


def uid_antiguo(plantilla, texto, unidad):
    """punto_uid calculado para los puntos y resultados de antes de que existiera."""
    clave = "\n".join(" ".join(str(x or "").split()).casefold() for x in (plantilla, texto, unidad))
    return "h" + hashlib.sha1(clave.encode("utf-8")).hexdigest()[:20]


def _uid_valido(v):
    v = str(v or "").strip()
    return v[:40] if v else None


def _deseq_max(p):
    """Desequilibrio máximo (%) de un punto, o None si no tiene o no es un número positivo."""
    n = _num(p.get("desequilibrio_max"))
    return n if n is not None and n > 0 else None


def _punto(fila):
    return {"texto": fila["texto"], "tipo": fila["tipo"] or "estado", "unidad": fila["unidad"] or "",
            "minimo": fila["minimo"], "maximo": fila["maximo"], "desequilibrio_max": fila["desequilibrio_max"],
            "punto_uid": fila["punto_uid"]}


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
    [{texto, tipo, unidad, minimo, maximo, desequilibrio_max, punto_uid}]. Devuelve su id.
    Cada punto conserva su punto_uid (el editor lo arrastra aunque se renombre o se mueva);
    los nuevos reciben uno."""
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("nombre")
    limpios, usados = [], set()
    for p in puntos:
        texto = (p.get("texto") or "").strip()
        if not texto:
            continue
        tipo = p.get("tipo") if p.get("tipo") in TIPOS else "estado"
        uid = _uid_valido(p.get("punto_uid"))
        if uid is None or uid in usados:
            uid = uuid.uuid4().hex
        usados.add(uid)
        limpios.append((uid, texto, tipo,
                        (p.get("unidad") or "").strip() if tipo in TIPOS_CON_VALOR else None,
                        _num(p.get("minimo")) if tipo in TIPOS_CON_VALOR else None,
                        _num(p.get("maximo")) if tipo in TIPOS_CON_VALOR else None,
                        _deseq_max(p) if tipo == "trifasica" else None))
    con = _conn()
    try:
        if plantilla_id:
            con.execute("UPDATE checklist_plantillas SET nombre=? WHERE id=?", (nombre, plantilla_id))
            con.execute("DELETE FROM checklist_puntos WHERE plantilla_id=?", (plantilla_id,))
        else:
            plantilla_id = con.execute("INSERT INTO checklist_plantillas (nombre) VALUES (?)", (nombre,)).lastrowid
        con.executemany(
            "INSERT INTO checklist_puntos (plantilla_id, orden, punto_uid, texto, tipo, unidad, minimo, maximo, desequilibrio_max) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
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

def fases(valor):
    """Las tres lecturas (textos, «» si falta alguna) de un punto trifásico: «12,1;12,3;12,0»."""
    partes = [x.strip() for x in str(valor or "").split(SEP_FASES)][:len(FASES)]
    return partes + [""] * (len(FASES) - len(partes))


def unir_fases(lecturas):
    """Al revés que fases(): «12,1;12,3;12,0», o «» si no hay ninguna."""
    partes = [str(x or "").strip().replace(SEP_FASES, "")[:18] for x in list(lecturas)[:len(FASES)]]
    partes += [""] * (len(FASES) - len(partes))
    return SEP_FASES.join(partes) if any(partes) else ""


def desequilibrio(valor):
    """(porcentaje, índice de la fase que más se aparta) de un punto trifásico, o None si
    faltan lecturas o la media es 0. Es el desequilibrio habitual (NEMA): la mayor
    diferencia con la media, en % de la media."""
    nums = [_num(x) for x in fases(valor)]
    if any(n is None for n in nums):
        return None
    media = sum(nums) / len(nums)
    if media <= 0:
        return None
    desvios = [abs(n - media) for n in nums]
    mayor = max(range(len(nums)), key=lambda i: desvios[i])
    return round(desvios[mayor] / media * 100, 1), mayor


def _fuera_uno(punto, valor):
    n = _num(valor)
    if n is None:
        return False
    minimo, maximo = _num(punto.get("minimo")), _num(punto.get("maximo"))
    return (minimo is not None and n < minimo) or (maximo is not None and n > maximo)


def desequilibrio_excesivo(punto, valor):
    """True si el desequilibrio entre fases pasa del máximo del punto trifásico."""
    limite = _deseq_max(punto)
    d = desequilibrio(valor) if limite is not None and punto.get("tipo") == "trifasica" else None
    return d is not None and d[0] > limite


def fuera_de_rango(punto, valor):
    """True si una lectura se sale del mínimo o el máximo del punto (en un punto
    trifásico, si se sale cualquiera de las tres fases o el desequilibrio pasa del máximo)."""
    if punto.get("tipo") == "trifasica":
        return any(_fuera_uno(punto, x) for x in fases(valor)) or desequilibrio_excesivo(punto, valor)
    return _fuera_uno(punto, valor)


def texto_valor(it):
    """El valor rellenado para enseñarlo: «9,1 bar» o «L1 12,1 · L2 12,3 · L3 12,0 A»."""
    unidad = it.get("unidad") or ""
    if it.get("tipo") == "trifasica":
        if not it.get("valor"):
            return ""
        texto = " · ".join(f"{f} {v or '-'}" for f, v in zip(FASES, fases(it["valor"])))
    else:
        texto = str(it.get("valor") or "")
    return f"{texto} {unidad}".strip() if texto else ""


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
        # Un tipo que esta versión no conoce (de una versión más nueva del móvil o del PC)
        # se conserva tal cual con su valor, en vez de convertirlo en «estado» y perder las
        # lecturas: así llegan enteras al PC o a la nube que sí lo entiende.
        desconocido = bool(it.get("tipo")) and tipo == "estado" and it.get("tipo") != "estado"
        if desconocido:
            tipo = str(it["tipo"]).strip()[:20] or "estado"
        estado = it.get("estado") if it.get("estado") in ESTADOS and tipo != SECCION else None
        valor = str(it.get("valor") or "").strip() if tipo == "lectura" or desconocido else ""
        if tipo == "trifasica":
            valor = unir_fases(fases(it.get("valor")))
        limpios.append({
            "texto": str(it["texto"]).strip()[:500], "tipo": tipo,
            "unidad": str(it.get("unidad") or "").strip()[:30] if tipo in TIPOS_CON_VALOR or desconocido else "",
            "minimo": _num(it.get("minimo")), "maximo": _num(it.get("maximo")),
            "desequilibrio_max": _deseq_max(it) if tipo == "trifasica" or desconocido else None,
            "estado": estado, "valor": valor[:60], "nota": str(it.get("nota") or "").strip()[:1000],
            "punto_uid": _uid_valido(it.get("punto_uid")) if tipo != SECCION else None})
    return limpios


def guardar_resultado(tarea_id, items, plantilla_nombre="", con=None):
    """Guarda lo rellenado junto al trabajo [tarea_id] (sustituye lo que hubiera)."""
    items = normalizar_items(items)
    _completar_uids(items, plantilla_nombre)
    propia = con is None
    if propia:
        con = _conn()
    con.execute("DELETE FROM checklist_resultados WHERE tarea_id=?", (tarea_id,))
    con.executemany(
        "INSERT INTO checklist_resultados (tarea_id, plantilla, orden, punto_uid, texto, tipo, unidad, minimo, maximo, "
        "desequilibrio_max, estado, valor, nota) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(tarea_id, plantilla_nombre or "", i, it["punto_uid"], it["texto"], it["tipo"], it["unidad"], it["minimo"],
          it["maximo"], it["desequilibrio_max"], it["estado"], it["valor"], it["nota"]) for i, it in enumerate(items)])
    if propia:
        con.commit()
        con.close()


def _completar_uids(items, plantilla_nombre):
    """Pone punto_uid a los puntos que llegan sin él (de una versión anterior del móvil o
    de la nube): el del punto de la plantilla con ese nombre que tenga el mismo texto y tipo
    y, si no lo hay, el calculado."""
    faltan = [it for it in items if not it.get("punto_uid") and it["tipo"] != SECCION]
    if not faltan:
        return
    plantilla = next((p for p in listar_plantillas() if p["nombre"] == plantilla_nombre), None)
    actuales = {(" ".join(p["texto"].split()).casefold(), p["tipo"]): p["punto_uid"]
                for p in (plantilla or {}).get("puntos", []) if p.get("punto_uid")}
    for it in faltan:
        it["punto_uid"] = actuales.get((" ".join(it["texto"].split()).casefold(), it["tipo"])) \
            or uid_antiguo(plantilla_nombre, it["texto"], it["unidad"])


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
                               "minimo": f["minimo"], "maximo": f["maximo"],
                               "desequilibrio_max": f["desequilibrio_max"], "punto_uid": f["punto_uid"],
                               "estado": f["estado"],
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
    for it in puntos_reales(items):
        r[it.get("estado") if it.get("estado") in ESTADOS else "sin"] += 1
    return r


def puntos_reales(items):
    """Los puntos que se revisan (sin los separadores)."""
    return [it for it in items if it.get("tipo") != SECCION]


def sin_marcar(items):
    return [it for it in puntos_reales(items) if it.get("estado") not in ESTADOS]


# ---------------------------------------------------------------- borradores
# Una lista larga se puede dejar a medias (fin del turno) y seguir otro día: lo
# apuntado se guarda al momento por aviso o pendiente y se recupera al volver a
# abrirla. Solo en este PC (el móvil tiene los suyos); se borra al completar.

def clave_borrador(tipo, item_id):
    """«aviso:12» / «pendiente:7»."""
    return f"{tipo}:{item_id}"


def _hay_algo(items):
    return any(it.get("estado") in ESTADOS or str(it.get("valor") or "").strip() or str(it.get("nota") or "").strip()
               for it in items)


def guardar_borrador(clave, plantilla_nombre, items):
    """Guarda lo apuntado hasta ahora (o lo borra si no hay nada apuntado)."""
    from datetime import datetime
    limpios = normalizar_items(items)
    con = _conn()
    if _hay_algo(limpios):
        con.execute("INSERT OR REPLACE INTO checklist_borradores (clave, plantilla, fecha, items) VALUES (?,?,?,?)",
                    (clave, plantilla_nombre or "", datetime.now().isoformat(timespec="seconds"),
                     json.dumps(limpios, ensure_ascii=False)))
    else:
        con.execute("DELETE FROM checklist_borradores WHERE clave=?", (clave,))
    con.commit()
    con.close()


def borrador_de(clave):
    """{"plantilla", "fecha", "items"} o None."""
    con = _conn()
    f = con.execute("SELECT plantilla, fecha, items FROM checklist_borradores WHERE clave=?", (clave,)).fetchone()
    con.close()
    if not f:
        return None
    return {"plantilla": f["plantilla"] or "", "fecha": f["fecha"] or "", "items": normalizar_items(f["items"] or "")}


def borrar_borrador(clave):
    con = _conn()
    con.execute("DELETE FROM checklist_borradores WHERE clave=?", (clave,))
    con.commit()
    con.close()


def resumen_borradores(tipo):
    """{item_id: (hechos, total)} de los avisos o pendientes con la lista a medias."""
    con = _conn()
    filas = con.execute("SELECT clave, items FROM checklist_borradores WHERE clave LIKE ?", (f"{tipo}:%",)).fetchall()
    con.close()
    resultado = {}
    for f in filas:
        try:
            item_id = int(f["clave"].split(":", 1)[1])
        except ValueError:
            continue
        items = normalizar_items(f["items"] or "")
        total = len(puntos_reales(items))
        resultado[item_id] = (total - recuento(items)["sin"], total)
    return resultado


def aplicar_borrador(items, borrador):
    """Pasa lo apuntado del borrador a los puntos actuales, punto a punto, solo si
    coincide el texto y el tipo (por si la plantilla ha cambiado entretanto)."""
    viejos = (borrador or {}).get("items", [])
    por_uid = {v["punto_uid"]: v for v in viejos if v.get("punto_uid")}
    for i, it in enumerate(items):
        viejo = por_uid.get(it.get("punto_uid")) if it.get("punto_uid") else None
        if viejo is None and i < len(viejos) and it.get("texto") == viejos[i].get("texto"):
            viejo = viejos[i]                 # borradores de antes del punto_uid: por posición y texto
        if viejo is not None and it.get("tipo") == viejo.get("tipo") and it.get("tipo") != SECCION:
            it.update(estado=viejo.get("estado"), valor=viejo.get("valor") or "", nota=viejo.get("nota") or "")
    return items


# ---------------------------------------------------------------- registro de cambios
from . import usuarios as _usuarios


def _texto_punto(p):
    if p.get("tipo") == SECCION:
        return f"── {p['texto']} ──"
    texto = p["texto"]
    if p.get("tipo") in TIPOS_CON_VALOR:
        rango = []
        if p.get("minimo") is not None: rango.append(f"mín. {_num(p['minimo']):g}")
        if p.get("maximo") is not None: rango.append(f"máx. {_num(p['maximo']):g}")
        if p.get("tipo") == "trifasica" and _deseq_max(p) is not None:
            rango.append(f"desequilibrio máx. {_deseq_max(p):g} %")
        nombre = "motor trifásico" if p.get("tipo") == "trifasica" else "lectura"
        texto += f" [{nombre}{(' ' + p['unidad']) if p.get('unidad') else ''}{(', ' + ', '.join(rango)) if rango else ''}]"
    return texto


def _foto_plantilla(plantilla_id):
    p = obtener_plantilla(plantilla_id)
    if not p:
        return {}
    return {"nombre": p["nombre"], "puntos": "\n".join(f"{i + 1}. {_texto_punto(x)}" for i, x in enumerate(p["puntos"]))}


_ETIQ_PLANTILLA = {"nombre": "Nombre", "puntos": "Puntos"}

_guardar_plantilla_sin_registro = guardar_plantilla
_borrar_plantilla_sin_registro = borrar_plantilla
_asignar_sin_registro = asignar


def guardar_plantilla(plantilla_id, nombre, puntos):
    antes = _foto_plantilla(plantilla_id) if plantilla_id else {}
    nuevo_id = _guardar_plantilla_sin_registro(plantilla_id, nombre, puntos)
    despues = _foto_plantilla(nuevo_id)
    _usuarios.auditar("checklists", "editar" if plantilla_id else "crear", despues.get("nombre", ""),
                      cambios=_usuarios.diferencias(antes, despues, _ETIQ_PLANTILLA))
    return nuevo_id


def borrar_plantilla(plantilla_id):
    antes = _foto_plantilla(plantilla_id)
    avisos, pendientes = usos_de_plantilla(plantilla_id)
    _borrar_plantilla_sin_registro(plantilla_id)
    _usuarios.auditar("checklists", "borrar", antes.get("nombre", ""),
                      detalle=f"Se quita de {avisos} avisos y {pendientes} pendientes\n{antes.get('puntos', '')}")


def asignar(tipo, item_id, plantilla_id):
    anterior = checklist_de(tipo, item_id)
    _asignar_sin_registro(tipo, item_id, plantilla_id)
    if (anterior or None) == (plantilla_id or None):
        return
    nombres = {p["id"]: p["nombre"] for p in listar_plantillas()}
    con = _conn()
    fila = con.execute(f"SELECT titulo FROM {_tabla(tipo)} WHERE id=?", (item_id,)).fetchone()
    con.close()
    _usuarios.auditar("avisos" if tipo == "aviso" else "pendientes", "editar", fila[0] if fila else "",
                      cambios=[{"campo": "Lista de comprobación", "antes": nombres.get(anterior, ""),
                                "despues": nombres.get(plantilla_id, "")}])


def cambios_resultado(antes_items, despues_items):
    """Diferencias entre dos listas rellenadas, punto a punto (para el
    registro de cambios al corregir una lista desde el historial)."""
    def linea(it):
        estado = {"ok": "Bien", "mal": "Mal", "na": "No aplica"}.get(it.get("estado"), "Sin revisar")
        partes = [estado]
        if it.get("valor"): partes.append(texto_valor(it))
        if it.get("nota"): partes.append(f"«{it['nota']}»")
        return " · ".join(partes)
    cambios = []
    for a, d in zip(antes_items, despues_items):
        if a.get("tipo") == SECCION:
            continue
        if linea(a) != linea(d):
            cambios.append({"campo": a.get("texto", ""), "antes": linea(a), "despues": linea(d)})
    return cambios


# ---------------------------------------------------------------- evolución de las lecturas

def _clave_punto(texto, unidad, tipo="lectura"):
    """El «mismo punto» en revisiones distintas: mismo texto, misma unidad (sin distinguir
    mayúsculas ni espacios de más) y mismo tipo (una lectura y un motor trifásico no se
    mezclan). Es lo que da de sí cómo se guardan las lecturas: con el trabajo, copiadas de
    la plantilla en ese momento."""
    return (" ".join(str(texto or "").split()).casefold(), " ".join(str(unidad or "").split()).casefold(),
            tipo if tipo == "trifasica" else "lectura")


def evolucion_lecturas(maquina_ids):
    """Lecturas de las listas de comprobación de los trabajos de esas máquinas, agrupadas por
    punto (texto + unidad) y de la más antigua a la más reciente:
    [{"texto", "unidad", "tipo", "minimo", "maximo" (los de la lectura más reciente), "lecturas": [{"fecha",
    "valor" (número o None si no se entiende), "valor_texto", "fuera" (de su propio rango),
    "minimo", "maximo", "tarea_id", "maquina_id", "tecnico", "nota"}]}], los puntos por su texto.
    En los motores trifásicos (tipo «trifasica») cada lectura lleva además "valores" (las tres
    fases, número o None), "desequilibrio" (% o None), "fase_desviada" (índice o None),
    "desequilibrio_max" y "desequilibrio_fuera" (si pasa de ese máximo); el punto, "desequilibrio_max";
    su "valor" es el de la fase más alta y "valor_texto", las tres («L1 12,1 · L2 …»)."""
    ids = [int(i) for i in (maquina_ids or []) if i is not None]
    if not ids:
        return []
    con = _conn()
    filas = []
    for trozo in range(0, len(ids), 500):
        parte = ids[trozo:trozo + 500]
        filas += con.execute(
            f"""SELECT r.punto_uid, r.texto, r.unidad, r.tipo, r.minimo, r.maximo, r.desequilibrio_max, r.valor, r.nota, r.tarea_id,
                       t.fecha, t.maquina_id, COALESCE(t.usuario_nombre, '') AS tecnico
                FROM checklist_resultados r JOIN tareas t ON t.id = r.tarea_id
                WHERE r.tipo IN ('lectura', 'trifasica') AND COALESCE(r.valor, '') != ''
                  AND t.maquina_id IN ({','.join('?' * len(parte))})""", parte).fetchall()
    con.close()
    puntos = {}
    for f in sorted(filas, key=lambda f: (f["fecha"] or "", f["tarea_id"])):
        tipo = "trifasica" if f["tipo"] == "trifasica" else "lectura"
        # El mismo punto en revisiones distintas: por su punto_uid (aunque se haya renombrado o
        # cambiado de unidad); sin él, por texto y unidad.
        clave = (f["punto_uid"], tipo) if f["punto_uid"] else _clave_punto(f["texto"], f["unidad"], tipo)
        p = puntos.setdefault(clave, {"tipo": tipo, "lecturas": []})
        p["texto"], p["unidad"] = " ".join(f["texto"].split()), f["unidad"] or ""   # los de la más reciente
        p["minimo"], p["maximo"] = f["minimo"], f["maximo"]        # los de la más reciente (van en orden)
        p["desequilibrio_max"] = f["desequilibrio_max"]
        rango = {"minimo": f["minimo"], "maximo": f["maximo"], "tipo": tipo, "desequilibrio_max": f["desequilibrio_max"]}
        lectura = {
            "fecha": (f["fecha"] or "")[:10], "valor": _num(f["valor"]), "valor_texto": f["valor"],
            "fuera": fuera_de_rango(rango, f["valor"]), "minimo": f["minimo"], "maximo": f["maximo"],
            "tarea_id": f["tarea_id"], "maquina_id": f["maquina_id"], "tecnico": f["tecnico"], "nota": f["nota"] or ""}
        if tipo == "trifasica":
            valores = [_num(x) for x in fases(f["valor"])]
            deseq = desequilibrio(f["valor"])
            lectura.update(valores=valores, valor=max((v for v in valores if v is not None), default=None),
                           valor_texto=" · ".join(f"{n} {v or '-'}" for n, v in zip(FASES, fases(f["valor"]))),
                           desequilibrio=deseq[0] if deseq else None, fase_desviada=deseq[1] if deseq else None,
                           desequilibrio_max=f["desequilibrio_max"],
                           desequilibrio_fuera=desequilibrio_excesivo(rango, f["valor"]))
        p["lecturas"].append(lectura)
    return sorted(puntos.values(), key=lambda p: (p["texto"].casefold(), p["unidad"].casefold(), p["tipo"]))
