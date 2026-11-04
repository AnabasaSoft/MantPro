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

"""
revisiones_almacen.py — Control de las revisiones diarias del almacén.

Cada día MantPro Stock propone revisar 5 artículos al azar. Aquí queda
constancia de **quién** hizo la revisión, **cuándo** y **si revisó los 5**:

- Una *revisión* es lo que hace una persona un día (fecha, usuario, móvil).
- Cada revisión tiene sus *líneas*: los artículos propuestos, con la cantidad
  que decía el sistema, la que se contó y si se llegó a revisar.

El móvil manda la revisión entera cada vez que avanza (se identifica con un
`uid` propio, así reenviarla no la duplica), también si la hizo sin conexión.
Si llega una versión más antigua que la ya guardada, se ignora.

Vive en almacen.db, junto al resto del almacén. Python puro, sin Qt: lo usan
la API del servidor y la ventana del PC.
"""

from datetime import datetime, timedelta

from . import almacen

ESTADO_COMPLETA = "completa"
ESTADO_PARCIAL = "parcial"
ESTADO_SIN_EMPEZAR = "sin_empezar"

_MAX_LINEAS = 50  # tope razonable: lo normal son 5 por revisión


def inicializar():
    """Crea las tablas si no existen. Idempotente."""
    con = almacen._conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS revisiones_stock (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            uid            TEXT NOT NULL UNIQUE,
            fecha          TEXT NOT NULL,          -- día de la revisión (AAAA-MM-DD)
            usuario_id     INTEGER,
            usuario_nombre TEXT NOT NULL DEFAULT '',
            dispositivo    TEXT NOT NULL DEFAULT '',
            creada         TEXT NOT NULL,
            actualizada    TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_revisiones_stock_fecha ON revisiones_stock(fecha);
        CREATE TABLE IF NOT EXISTS revisiones_stock_lineas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            revision_id      INTEGER NOT NULL REFERENCES revisiones_stock(id) ON DELETE CASCADE,
            material_id      INTEGER,               -- NULL si el artículo aún no existía en el PC
            codigo           TEXT NOT NULL DEFAULT '',
            nombre           TEXT NOT NULL DEFAULT '',
            ubicacion        TEXT NOT NULL DEFAULT '',
            unidad           TEXT NOT NULL DEFAULT '',
            cantidad_sistema REAL,                  -- lo que decía el sistema al empezar
            cantidad_contada REAL,                  -- lo que se contó (NULL si no se revisó)
            revisado         INTEGER NOT NULL DEFAULT 0,
            fecha_revision   TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_revisiones_lineas_rev ON revisiones_stock_lineas(revision_id);
    """)
    con.commit()
    con.close()


def _numero(valor):
    """float o None (vacío, texto raro…)."""
    if valor is None or valor == "":
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def _texto(valor, maximo=200):
    return str(valor if valor is not None else "").strip()[:maximo]


def _fecha_valida(texto):
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def guardar_revision(datos, usuario_id, usuario_nombre):
    """Guarda (o actualiza) una revisión que manda un móvil.

    [datos] es un diccionario: `uid`, `fecha` (AAAA-MM-DD), `dispositivo`
    (opcional), `actualizada` (AAAA-MM-DD HH:MM:SS) y `lineas`: lista de
    diccionarios con `material_id` (o None), `codigo`, `nombre`, `ubicacion`,
    `unidad`, `cantidad_sistema`, `cantidad_contada`, `revisado`,
    `fecha_revision`.

    Devuelve (True, id) si se guardó, (True, id) también si se ignoró por
    llegar una versión más antigua que la guardada, o (False, motivo) si los
    datos no valen. El usuario es siempre el de la sesión, no el que diga el
    móvil: así nadie puede firmar una revisión como otro."""
    uid = _texto(datos.get("uid"), 80)
    fecha = _texto(datos.get("fecha"), 10)
    lineas = datos.get("lineas")
    if not uid:
        return False, "falta_uid"
    if not _fecha_valida(fecha):
        return False, "fecha_no_valida"
    if not isinstance(lineas, list) or not lineas or len(lineas) > _MAX_LINEAS:
        return False, "lineas_no_validas"
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    actualizada = _texto(datos.get("actualizada"), 19) or ahora

    con = almacen._conn()
    try:
        existente = con.execute("SELECT id, actualizada, usuario_id FROM revisiones_stock WHERE uid=?", (uid,)).fetchone()
        if existente is not None:
            if existente["usuario_id"] != usuario_id:
                return False, "revision_de_otro_usuario"
            if actualizada < existente["actualizada"]:
                return True, existente["id"]   # llegó una versión vieja: ya hay una más nueva
            revision_id = existente["id"]
            con.execute("UPDATE revisiones_stock SET actualizada=?, dispositivo=? WHERE id=?",
                        (actualizada, _texto(datos.get("dispositivo"), 120), revision_id))
            con.execute("DELETE FROM revisiones_stock_lineas WHERE revision_id=?", (revision_id,))
        else:
            revision_id = con.execute("""
                INSERT INTO revisiones_stock (uid, fecha, usuario_id, usuario_nombre, dispositivo, creada, actualizada)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (uid, fecha, usuario_id, _texto(usuario_nombre, 120), _texto(datos.get("dispositivo"), 120),
                 ahora, actualizada)).lastrowid
        for linea in lineas:
            if not isinstance(linea, dict):
                continue
            material_id = linea.get("material_id")
            material_id = int(material_id) if isinstance(material_id, (int, float)) and material_id > 0 else None
            revisado = 1 if linea.get("revisado") in (True, 1, "1", "true", "True") else 0
            contada = _numero(linea.get("cantidad_contada")) if revisado else None
            con.execute("""
                INSERT INTO revisiones_stock_lineas
                    (revision_id, material_id, codigo, nombre, ubicacion, unidad,
                     cantidad_sistema, cantidad_contada, revisado, fecha_revision)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (revision_id, material_id, _texto(linea.get("codigo"), 60), _texto(linea.get("nombre")),
                 _texto(linea.get("ubicacion")), _texto(linea.get("unidad"), 20),
                 _numero(linea.get("cantidad_sistema")), contada, revisado,
                 _texto(linea.get("fecha_revision"), 19) if revisado else ""))
        con.commit()
        return True, revision_id
    finally:
        con.close()


def estado_de(total, revisados):
    if total and revisados >= total:
        return ESTADO_COMPLETA
    return ESTADO_PARCIAL if revisados else ESTADO_SIN_EMPEZAR


def listar_revisiones(dias=None, usuario_id=None, estado=None, limite=500, desplazamiento=0):
    """Revisiones, de la más reciente a la más antigua, cada una con `total`
    (artículos propuestos), `revisados`, `ajustados` (con diferencia entre lo
    contado y lo que decía el sistema) y `estado`.

    [dias]: solo las de los últimos N días. [usuario_id]: solo de esa persona.
    [estado]: "completa", "parcial", "sin_empezar" o una lista de ellos."""
    condiciones, parametros = [], []
    if dias:
        condiciones.append("r.fecha >= ?")
        parametros.append((datetime.now() - timedelta(days=int(dias))).strftime("%Y-%m-%d"))
    if usuario_id:
        condiciones.append("r.usuario_id = ?")
        parametros.append(usuario_id)
    donde = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    con = almacen._conn()
    filas = con.execute(f"""
        SELECT r.*,
               COUNT(l.id) AS total,
               COALESCE(SUM(l.revisado), 0) AS revisados,
               COALESCE(SUM(CASE WHEN l.revisado = 1 AND l.cantidad_sistema IS NOT NULL
                                  AND l.cantidad_contada IS NOT NULL
                                  AND ABS(l.cantidad_contada - l.cantidad_sistema) > 0.0000001
                                 THEN 1 ELSE 0 END), 0) AS ajustados
        FROM revisiones_stock r LEFT JOIN revisiones_stock_lineas l ON l.revision_id = r.id
        {donde}
        GROUP BY r.id
        ORDER BY r.fecha DESC, r.actualizada DESC, r.id DESC""", parametros).fetchall()
    con.close()
    resultado = []
    permitidos = {estado} if isinstance(estado, str) else set(estado or [])
    for f in filas:
        d = dict(f)
        d["estado"] = estado_de(d["total"], d["revisados"])
        if permitidos and d["estado"] not in permitidos:
            continue
        resultado.append(d)
    return resultado[desplazamiento:desplazamiento + limite]


def lineas_de_revision(revision_id):
    """Líneas de una revisión, con la `diferencia` (contada − sistema) cuando
    se revisó."""
    con = almacen._conn()
    filas = con.execute("SELECT * FROM revisiones_stock_lineas WHERE revision_id=? ORDER BY id", (revision_id,)).fetchall()
    con.close()
    lineas = []
    for f in filas:
        d = dict(f)
        if d["revisado"] and d["cantidad_sistema"] is not None and d["cantidad_contada"] is not None:
            d["diferencia"] = d["cantidad_contada"] - d["cantidad_sistema"]
        else:
            d["diferencia"] = None
        lineas.append(d)
    return lineas


def usuarios_con_revisiones():
    """[(usuario_id, nombre)] de quien ha hecho alguna revisión, para el filtro."""
    con = almacen._conn()
    filas = con.execute("""
        SELECT usuario_id, MAX(usuario_nombre) AS nombre FROM revisiones_stock
        WHERE usuario_id IS NOT NULL GROUP BY usuario_id ORDER BY nombre COLLATE NOCASE""").fetchall()
    con.close()
    return [(f["usuario_id"], f["nombre"]) for f in filas]
