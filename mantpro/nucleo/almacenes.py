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
almacenes.py — Varios almacenes (uno o varios por sede, y comunes) para MantPro (motor, sin Qt).

Fase 3 de «Varias sedes» (ROADMAP.md). Reglas:

  * Siempre hay un almacén PRINCIPAL (uuid fijo `almacen-principal`): es el que
    había antes, de la sede principal. `almacen_id` NULL significa «principal»
    (en `materiales` y en `zonas`), igual que `sede_id` NULL en nucleo/sedes.py.
  * Un almacén es de una sede (`sede_id`, NULL = principal) o COMÚN (se ve
    desde todas las sedes).
  * Cada artículo de cada almacén es una fila de `materiales`, con su stock, su
    mínimo y su ubicación, así todo lo que ya funcionaba sigue igual filtrando
    por almacén. «El mismo artículo» en varios almacenes son filas enlazadas por
    `articulo_id` (el id de la fila original; NULL en la original).
  * Un TRASPASO es una salida en el origen y una entrada en el destino; si el
    artículo aún no está en el destino se crea copiando sus datos.
"""

from datetime import datetime

from . import almacen
from . import usuarios as _usuarios

UUID_PRINCIPAL = "almacen-principal"

# Ciclos de la revisión del almacén
CICLO_DIARIO, CICLO_SEMANAL, CICLO_MENSUAL = "diario", "semanal", "mensual"
CICLOS = (CICLO_DIARIO, CICLO_SEMANAL, CICLO_MENSUAL)
ARTICULOS_POR_DEFECTO = 5
ARTICULOS_MAXIMO = 50          # el mismo tope que admite una revisión
# Motivos canónicos (en español; se traducen al mostrarlos, también en MantPro Stock:
# mantpro_stock_app/lib/modelos.dart)
PREFIJO_TRASPASO_A = "Traspaso a: "
PREFIJO_TRASPASO_DESDE = "Traspaso desde: "


def _t(clave, defecto=None):
    """Texto traducido; si el idioma aún no lo tiene (devuelve la clave), [defecto]."""
    from .. import idiomas
    texto = idiomas.t(clave)
    return defecto if (defecto and texto == clave) else texto


def _conn():
    return almacen._conn()


def inicializar(con):
    """Tabla de almacenes, columnas `almacen_id`/`articulo_id` y almacén principal.
    La llama almacen.inicializar() con su conexión (idempotente)."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS almacenes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            sede_id   INTEGER,
            comun     INTEGER NOT NULL DEFAULT 0,
            notas     TEXT,
            activo    INTEGER NOT NULL DEFAULT 1,
            principal INTEGER NOT NULL DEFAULT 0,
            uuid      TEXT
        )
    """)
    # Dirección de entrega propia (vacía: la de su sede)
    if "direccion" not in almacen._columnas(con, "almacenes"):
        con.execute("ALTER TABLE almacenes ADD COLUMN direccion TEXT")
    # Revisión del almacén: ciclo (diario / semanal / mensual), día del ciclo y artículos por revisión
    for columna, tipo in (("revision_ciclo", "TEXT NOT NULL DEFAULT 'diario'"),
                          ("revision_dia", "INTEGER NOT NULL DEFAULT 0"),
                          ("revision_articulos", f"INTEGER NOT NULL DEFAULT {ARTICULOS_POR_DEFECTO}")):
        if columna not in almacen._columnas(con, "almacenes"):
            con.execute(f"ALTER TABLE almacenes ADD COLUMN {columna} {tipo}")
    for tabla, columna in (("materiales", "almacen_id"), ("zonas", "almacen_id"), ("materiales", "articulo_id")):
        if columna not in almacen._columnas(con, tabla):
            con.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} INTEGER")
    con.execute("CREATE INDEX IF NOT EXISTS idx_materiales_almacen ON materiales(almacen_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_materiales_articulo ON materiales(articulo_id)")
    nombre_principal = _t("almacen_principal_nombre", "Almacén principal")
    if not con.execute("SELECT 1 FROM almacenes WHERE principal = 1").fetchone():
        con.execute("INSERT INTO almacenes (nombre, principal, uuid) VALUES (?, 1, ?)",
                    (nombre_principal, UUID_PRINCIPAL))
    # Arreglo: se llegó a crear con la clave de traducción como nombre
    con.execute("UPDATE almacenes SET nombre = ? WHERE nombre = 'almacen_principal_nombre'", (nombre_principal,))


# ---------------------------------------------------------------- consultas

def listar(sede=None, incluir_inactivos=False):
    """Almacenes como dicts (el principal primero). Con [sede], solo los que se ven
    desde ella: los suyos y los comunes. `sede`: un id de nucleo/sedes, una lista o None (todos)."""
    from . import sedes
    con = _conn()
    sql = "SELECT * FROM almacenes" + ("" if incluir_inactivos else " WHERE activo = 1")
    filas = [dict(f) for f in con.execute(sql + " ORDER BY principal DESC, comun DESC, nombre COLLATE NOCASE")]
    con.close()
    if sede is None:
        return filas
    return [a for a in filas if a["comun"] or sedes.de_la_sede(a["sede_id"], sede)]


def obtener(almacen_id):
    con = _conn()
    fila = con.execute("SELECT * FROM almacenes WHERE id = ?", (almacen_id,)).fetchone()
    con.close()
    return dict(fila) if fila else None


def principal_id():
    con = _conn()
    fila = con.execute("SELECT id FROM almacenes WHERE principal = 1 ORDER BY id LIMIT 1").fetchone()
    con.close()
    return fila[0] if fila else None


def hay_varios():
    con = _conn()
    n = con.execute("SELECT COUNT(*) FROM almacenes WHERE activo = 1").fetchone()[0]
    con.close()
    return n > 1


def efectivo(almacen_id):
    """El almacén de un registro: el suyo o, si no tiene, el principal."""
    return almacen_id if almacen_id is not None else principal_id()


def guardable(almacen_id):
    """Lo que se guarda en `almacen_id`: el principal como NULL."""
    if almacen_id is None or almacen_id == principal_id():
        return None
    return int(almacen_id)


def condicion(almacen_ids, columna="almacen_id"):
    """WHERE para los registros de [almacen_ids] (un id, una lista o None = todos).
    Solo enteros: se puede interpolar."""
    if almacen_ids is None:
        return "1=1"
    if isinstance(almacen_ids, int):
        almacen_ids = [almacen_ids]
    ids = ",".join(str(int(a)) for a in almacen_ids) or "NULL"
    pid = principal_id()
    if pid is None:
        return f"{columna} IN ({ids})"
    return f"COALESCE({columna}, {int(pid)}) IN ({ids})"


def ids_de_sede(sede):
    """Ids de los almacenes que se ven desde [sede] (None = None: todos)."""
    if sede is None:
        return None
    return [a["id"] for a in listar(sede)]


def nombres():
    return {a["id"]: a["nombre"] for a in listar(incluir_inactivos=True)}


def nombre(almacen_id):
    return nombres().get(efectivo(almacen_id), "")


def en_uso(almacen_id):
    """Artículos y zonas del almacén (sin contar lo implícito del principal)."""
    con = _conn()
    n_mat = con.execute("SELECT COUNT(*) FROM materiales WHERE almacen_id = ?", (almacen_id,)).fetchone()[0]
    n_zon = con.execute("SELECT COUNT(*) FROM zonas WHERE almacen_id = ?", (almacen_id,)).fetchone()[0]
    con.close()
    return {"materiales": n_mat, "zonas": n_zon}


def entrega(almacen_id):
    """Dónde se entrega lo pedido para un almacén (None = el principal): dict con
    `almacen` (nombre), `sede` (nombre), `direccion`, `contacto` y `telefono`. La
    dirección es la propia del almacén o, si está vacía, la de su sede (la principal
    para el almacén principal y los comunes)."""
    from . import sedes
    a = obtener(efectivo(almacen_id)) or {}
    sede = {}
    try:
        sede = sedes.obtener(sedes.efectiva(a.get("sede_id"))) or {}
    except Exception:          # sin base de datos de sedes (pruebas aisladas)
        sede = {}
    return {"almacen": a.get("nombre") or "", "sede": sede.get("nombre") or "",
            "direccion": (a.get("direccion") or "").strip() or (sede.get("direccion") or "").strip(),
            "contacto": (sede.get("contacto") or "").strip(), "telefono": (sede.get("telefono") or "").strip()}


# ---------------------------------------------------------------- altas y cambios

def revision(a):
    """Ciclo de revisión de un almacén (dict): (ciclo, dia, articulos) ya validados.
    - diario: cada día laborable (dia no se usa).
    - semanal: [dia] de la semana, 0 = lunes … 6 = domingo.
    - mensual: [dia] del mes, 1 … 31 (en meses más cortos, el último)."""
    ciclo = a.get("revision_ciclo") if a.get("revision_ciclo") in CICLOS else CICLO_DIARIO
    try:
        dia = int(a.get("revision_dia") or 0)
    except (TypeError, ValueError):
        dia = 0
    if ciclo == CICLO_SEMANAL:
        dia = min(max(dia, 0), 6)
    elif ciclo == CICLO_MENSUAL:
        dia = min(max(dia, 1), 31)
    else:
        dia = 0
    try:
        articulos = int(a.get("revision_articulos") or ARTICULOS_POR_DEFECTO)
    except (TypeError, ValueError):
        articulos = ARTICULOS_POR_DEFECTO
    return ciclo, dia, min(max(articulos, 1), ARTICULOS_MAXIMO)


def _datos(d):
    from . import sedes
    sede = d.get("sede_id")
    return {"nombre": str(d.get("nombre") or "").strip(), "comun": 1 if d.get("comun") else 0,
            "sede_id": None if d.get("comun") else sedes.guardable(sede), "notas": str(d.get("notas") or "").strip(),
            "direccion": str(d.get("direccion") or "").strip(),
            **dict(zip(("revision_ciclo", "revision_dia", "revision_articulos"), revision(d)))}


def _repetido(con, nombre, excluir_id=None):
    return con.execute("SELECT 1 FROM almacenes WHERE lower(trim(nombre)) = lower(?) AND id IS NOT ?",
                       (nombre, excluir_id)).fetchone() is not None


def crear(datos):
    """Devuelve (id, None) o (None, 'sin_nombre' | 'nombre_repetido')."""
    d = _datos(datos)
    if not d["nombre"]:
        return None, "sin_nombre"
    con = _conn()
    if _repetido(con, d["nombre"]):
        con.close()
        return None, "nombre_repetido"
    nuevo = con.execute("""INSERT INTO almacenes (nombre, sede_id, comun, notas, direccion, revision_ciclo, revision_dia,
                                                 revision_articulos) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (d["nombre"], d["sede_id"], d["comun"], d["notas"], d["direccion"], d["revision_ciclo"],
                         d["revision_dia"], d["revision_articulos"])).lastrowid
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "crear", _t("almacen_auditoria").format(nombre=d["nombre"]))
    return nuevo, None


def actualizar(almacen_id, datos):
    """Devuelve None o el código de error. El principal no puede ser común ni de otra sede.
    Lo que no venga en [datos] (dirección, ciclo de revisión) se queda como estaba."""
    a = obtener(almacen_id)
    if not a:
        return None
    d = _datos({**{k: a.get(k) for k in ("direccion", "revision_ciclo", "revision_dia", "revision_articulos")}, **datos})
    if not d["nombre"]:
        return "sin_nombre"
    if a["principal"]:
        d["comun"], d["sede_id"] = 0, None
    con = _conn()
    if _repetido(con, d["nombre"], almacen_id):
        con.close()
        return "nombre_repetido"
    con.execute("""UPDATE almacenes SET nombre = ?, sede_id = ?, comun = ?, notas = ?, direccion = ?, revision_ciclo = ?,
                   revision_dia = ?, revision_articulos = ? WHERE id = ?""",
                (d["nombre"], d["sede_id"], d["comun"], d["notas"], d["direccion"], d["revision_ciclo"],
                 d["revision_dia"], d["revision_articulos"], almacen_id))
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "editar", _t("almacen_auditoria").format(nombre=d["nombre"]))
    return None


def activar(almacen_id, activo):
    a = obtener(almacen_id)
    if not a:
        return None
    if a["principal"] and not activo:
        return "es_principal"
    con = _conn()
    con.execute("UPDATE almacenes SET activo = ? WHERE id = ?", (1 if activo else 0, almacen_id))
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "activar" if activo else "desactivar", _t("almacen_auditoria").format(nombre=a["nombre"]))
    return None


def borrar(almacen_id):
    """Solo un almacén vacío (sin artículos ni zonas) que no sea el principal."""
    a = obtener(almacen_id)
    if not a:
        return None
    if a["principal"]:
        return "es_principal"
    if any(en_uso(almacen_id).values()):
        return "en_uso"
    con = _conn()
    con.execute("DELETE FROM almacenes WHERE id = ?", (almacen_id,))
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "borrar", _t("almacen_auditoria").format(nombre=a["nombre"]))
    return None


# ---------------------------------------------------------------- el mismo artículo en varios almacenes

def raiz_articulo(material):
    """Id que identifica «el mismo artículo» en todos los almacenes."""
    return material["articulo_id"] or material["id"]


def mismo_articulo(material_id):
    """Filas del mismo artículo en todos los almacenes (dicts, con su `almacen_id` efectivo)."""
    m = almacen.obtener_material(material_id)
    if not m:
        return []
    raiz = raiz_articulo(m)
    con = _conn()
    filas = [dict(f) for f in con.execute("SELECT * FROM materiales WHERE id = ? OR articulo_id = ? ORDER BY id",
                                          (raiz, raiz))]
    con.close()
    for f in filas:
        f["almacen_id"] = efectivo(f["almacen_id"])
    return filas


def en_almacen(material_id, almacen_id):
    """La fila del mismo artículo en [almacen_id], o None si allí no está."""
    almacen_id = efectivo(almacen_id)
    return next((f for f in mismo_articulo(material_id) if f["almacen_id"] == almacen_id), None)


def _copiar_a(material, almacen_id):
    """Crea el artículo en otro almacén (sin stock, sin mínimo y sin ubicación)."""
    con = _conn()
    columnas = {c for c in almacen._columnas(con, "materiales")}
    copiar = [c for c in ("codigo", "nombre", "descripcion", "unidad", "foto", "proveedor_id", "precio")
              if c in columnas]
    valores = [material[c] for c in copiar]
    nuevo = con.execute(
        f"INSERT INTO materiales ({', '.join(copiar)}, stock_actual, stock_minimo, seccion_id, almacen_id, articulo_id) "
        f"VALUES ({', '.join('?' * len(copiar))}, 0, 0, NULL, ?, ?)",
        valores + [guardable(almacen_id), raiz_articulo(material)]).lastrowid
    con.commit()
    con.close()
    return nuevo


def traspasar(material_id, almacen_destino, cantidad, usuario_id=None, usuario_nombre=None):
    """Lleva [cantidad] del artículo [material_id] a [almacen_destino]. Devuelve
    (id del artículo en el destino, None) o (None, error): 'mismo_almacen',
    'cantidad_no_valida', 'material_no_existe', 'stock_insuficiente'."""
    origen = almacen.obtener_material(material_id)
    if not origen:
        return None, "material_no_existe"
    try:
        cantidad = float(cantidad)
    except (TypeError, ValueError):
        return None, "cantidad_no_valida"
    if cantidad <= 0:
        return None, "cantidad_no_valida"
    if efectivo(origen["almacen_id"]) == efectivo(almacen_destino):
        return None, "mismo_almacen"
    if cantidad > origen["stock_actual"]:
        return None, "stock_insuficiente"
    destino = en_almacen(material_id, almacen_destino)
    destino_id = destino["id"] if destino else _copiar_a(origen, almacen_destino)
    ok, err = almacen.registrar_movimiento(material_id, "salida", cantidad, usuario_id, usuario_nombre,
                                           motivo=PREFIJO_TRASPASO_A + nombre(almacen_destino))
    if not ok:
        return None, err
    almacen.registrar_movimiento(destino_id, "entrada", cantidad, usuario_id, usuario_nombre,
                                 motivo=PREFIJO_TRASPASO_DESDE + nombre(origen["almacen_id"]))
    return destino_id, None


def stock_por_almacen(material_id):
    """[(nombre del almacén, stock, id del artículo allí)] del mismo artículo en cada almacén activo."""
    activos = {a["id"]: a["nombre"] for a in listar()}
    return [(activos[f["almacen_id"]], f["stock_actual"], f["id"])
            for f in mismo_articulo(material_id) if f["almacen_id"] in activos]


