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
consumos.py — Repuestos y materiales consumidos en cada trabajo.

- Cada artículo del almacén puede tener un **precio unitario**
  (materiales.precio).
- Al apuntar los repuestos usados en un trabajo se descuentan del stock
  (movimiento de salida) y se guarda una **copia** en trabajo_materiales: código,
  nombre, unidad, cantidad y el precio de ese momento. Si el artículo cambia de
  precio, o se borra, el coste de lo ya hecho no cambia.
- Corregir los repuestos de un trabajo ya hecho ajusta el stock con un
  movimiento por la diferencia.
- Con eso se calcula el coste de material de cada trabajo y de cada máquina.

Vive en almacen.db (junto al stock); el trabajo se identifica por el id de
tareas de mantenimiento.db.
"""

from collections import OrderedDict

from . import almacen
from . import usuarios as _usuarios

PREFIJO_CORRECCION = "Corrección del trabajo: "


def _conn():
    return almacen._conn()


def inicializar():
    con = _conn()
    if "precio" not in almacen._columnas(con, "materiales"):
        con.execute("ALTER TABLE materiales ADD COLUMN precio REAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS trabajo_materiales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            tarea_id    INTEGER NOT NULL,
            material_id INTEGER,
            codigo      TEXT,
            nombre      TEXT NOT NULL,
            unidad      TEXT,
            cantidad    REAL NOT NULL,
            precio      REAL,
            fecha       TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_trabajo_materiales ON trabajo_materiales(tarea_id)")
    con.commit()
    con.close()


# ---------------------------------------------------------------- precios

def fijar_precio(material_id, precio):
    """Precio unitario del artículo (None: sin precio)."""
    con = _conn()
    con.execute("UPDATE materiales SET precio=? WHERE id=?", (precio, material_id))
    con.commit()
    con.close()


def numero(v):
    """Número o None a partir de lo que escriba el usuario («12,50», «», None)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    texto = str(v).strip().replace(" ", "").replace(",", ".")
    try:
        return float(texto) if texto else None
    except ValueError:
        return None


def _agrupar(items):
    """{material_id: cantidad} sumando duplicados y quitando cantidades <= 0."""
    total = OrderedDict()
    for it in items or []:
        try:
            mid = int(it.get("material_id"))
            cantidad = float(numero(it.get("cantidad")) or 0)
        except (TypeError, ValueError, AttributeError):
            continue
        if cantidad > 0:
            total[mid] = total.get(mid, 0) + cantidad
    return total


# ---------------------------------------------------------------- consumir

def registrar_consumo(tarea_id, items, usuario_id, usuario_nombre, referencia="", fecha=None):
    """Descuenta del stock los repuestos usados en el trabajo [tarea_id]
    ([{material_id, cantidad}]) y los guarda con su precio. El material ya se
    ha usado, así que se descuenta aunque el stock quede en negativo (eso
    dispara el aviso de bajo mínimo). Devuelve cuántos artículos se han
    apuntado."""
    agrupados = _agrupar(items)
    if not agrupados:
        return 0
    from datetime import datetime
    fecha = fecha or datetime.now().strftime("%Y-%m-%d")
    filas = []
    for mid, cantidad in agrupados.items():
        m = almacen.obtener_material(mid)
        if not m:
            continue
        ok, _ = almacen.registrar_movimiento(mid, "salida", cantidad, usuario_id, usuario_nombre,
                                             motivo=f"{almacen.PREFIJO_MOTIVO_USADO_EN_TRABAJO}{referencia}",
                                             permitir_negativo=True)
        if ok:
            filas.append((tarea_id, mid, m.get("codigo") or "", m["nombre"], m.get("unidad") or "",
                          cantidad, m.get("precio"), fecha))
    if filas:
        con = _conn()
        con.executemany("INSERT INTO trabajo_materiales (tarea_id, material_id, codigo, nombre, unidad, cantidad, precio, fecha) "
                        "VALUES (?,?,?,?,?,?,?,?)", filas)
        con.commit()
        con.close()
    return len(filas)


def materiales_de_trabajos(tarea_ids):
    """{tarea_id: [{material_id, codigo, nombre, unidad, cantidad, precio, importe}]}."""
    ids = [int(i) for i in tarea_ids if i is not None]
    resultado = {}
    if not ids:
        return resultado
    con = _conn()
    for trozo in range(0, len(ids), 500):
        parte = ids[trozo:trozo + 500]
        marcas = ",".join("?" * len(parte))
        for f in con.execute(f"SELECT * FROM trabajo_materiales WHERE tarea_id IN ({marcas}) ORDER BY tarea_id, id", parte):
            d = dict(f)
            d["importe"] = d["cantidad"] * d["precio"] if d["precio"] is not None else None
            resultado.setdefault(d["tarea_id"], []).append(d)
    con.close()
    return resultado


def materiales_de_trabajo(tarea_id):
    return materiales_de_trabajos([tarea_id]).get(int(tarea_id), []) if tarea_id is not None else []


def coste(materiales):
    """(importe total, hay artículos sin precio)."""
    total = sum(m["importe"] for m in materiales if m.get("importe") is not None)
    return total, any(m.get("precio") is None for m in materiales)


def corregir_consumo(tarea_id, items, usuario_id, usuario_nombre, referencia=""):
    """Deja los repuestos del trabajo como [items] ([{material_id, cantidad}])
    y ajusta el stock por la diferencia: si ahora hay más, sale lo que falta;
    si hay menos, vuelve al almacén. Lo que ya estaba conserva su precio de
    entonces. Devuelve la lista de cambios [{campo, antes, despues}]."""
    anteriores = materiales_de_trabajo(tarea_id)
    antes = OrderedDict()
    for m in anteriores:
        clave = m["material_id"] if m["material_id"] is not None else f"borrado-{m['id']}"
        if clave in antes:
            antes[clave]["cantidad"] += m["cantidad"]
        else:
            antes[clave] = dict(m)
    despues = _agrupar(items)
    motivo = f"{PREFIJO_CORRECCION}{referencia}"
    cambios = []
    from datetime import datetime
    fecha = anteriores[0]["fecha"] if anteriores else datetime.now().strftime("%Y-%m-%d")
    nuevas = []
    for clave in list(antes) + [k for k in despues if k not in antes]:
        previo = antes.get(clave)
        cantidad_antes = previo["cantidad"] if previo else 0
        cantidad_despues = despues.get(clave, 0) if not isinstance(clave, str) else cantidad_antes
        m = almacen.obtener_material(clave) if not isinstance(clave, str) else None
        nombre = (previo or m or {}).get("nombre", "?")
        codigo = (previo or m or {}).get("codigo") or ""
        diferencia = cantidad_despues - cantidad_antes
        if abs(diferencia) > 1e-9 and m:
            almacen.registrar_movimiento(clave, "salida" if diferencia > 0 else "entrada", abs(diferencia),
                                         usuario_id, usuario_nombre, motivo=motivo, permitir_negativo=True)
            cambios.append({"campo": f"{codigo} · {nombre}" if codigo else nombre,
                            "antes": f"{cantidad_antes:g}" if cantidad_antes else "",
                            "despues": f"{cantidad_despues:g}" if cantidad_despues else ""})
        if cantidad_despues > 0:
            base = previo or {"material_id": clave, "codigo": codigo, "nombre": nombre,
                              "unidad": (m or {}).get("unidad") or "", "precio": (m or {}).get("precio")}
            nuevas.append((tarea_id, base["material_id"], base["codigo"], base["nombre"], base["unidad"],
                           cantidad_despues, base["precio"], fecha))
    con = _conn()
    con.execute("DELETE FROM trabajo_materiales WHERE tarea_id=?", (tarea_id,))
    con.executemany("INSERT INTO trabajo_materiales (tarea_id, material_id, codigo, nombre, unidad, cantidad, precio, fecha) "
                    "VALUES (?,?,?,?,?,?,?,?)", nuevas)
    con.commit()
    con.close()
    if cambios:
        _usuarios.auditar("trabajos", "editar", referencia, detalle="Repuestos usados corregidos (stock ajustado)",
                          cambios=cambios, objeto_id=tarea_id)
    return cambios


def olvidar_trabajo(tarea_id):
    """El trabajo se ha borrado o ha vuelto a pendientes: se quitan sus
    repuestos de los costes (el stock no se toca: el material ya se usó)."""
    con = _conn()
    con.execute("DELETE FROM trabajo_materiales WHERE tarea_id=?", (tarea_id,))
    con.commit()
    con.close()
    # La lectura de contador apuntada al completarlo deja de marcar el inicio
    # del ciclo de su preventivo (la lectura en sí sigue siendo válida)
    from . import contadores
    try:
        contadores.olvidar_trabajo(tarea_id)
    except Exception:
        pass


# ---------------------------------------------------------------- costes

def consumo_por_tareas(tareas):
    """[(tarea_id, fecha, maquina_id)] → {maquina_id: {"importe", "sin_precio",
    "articulos": {nombre: cantidad}, "trabajos": n}} sumando sus repuestos."""
    por_tarea = materiales_de_trabajos([t[0] for t in tareas])
    resultado = {}
    for tarea_id, _fecha, maquina_id in tareas:
        mats = por_tarea.get(tarea_id)
        if not mats:
            continue
        r = resultado.setdefault(maquina_id, {"importe": 0.0, "sin_precio": False, "articulos": OrderedDict(), "trabajos": 0})
        importe, sin_precio = coste(mats)
        r["importe"] += importe
        r["sin_precio"] = r["sin_precio"] or sin_precio
        r["trabajos"] += 1
        for m in mats:
            clave = (m["codigo"], m["nombre"], m["unidad"])
            a = r["articulos"].setdefault(clave, {"cantidad": 0.0, "importe": 0.0, "sin_precio": False})
            a["cantidad"] += m["cantidad"]
            if m["importe"] is None:
                a["sin_precio"] = True
            else:
                a["importe"] += m["importe"]
    return resultado


def formato_importe(valor, moneda="€"):
    """«1.234,50 €» (en inglés, «1,234.50 €»); la moneda es la configurada."""
    from .. import idiomas
    texto = f"{valor:,.2f}"
    if idiomas.get_idioma() != "en":
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} {moneda}".strip()


# ---------------------------------------------------------------- moneda

def moneda():
    """Símbolo de moneda configurado (en mantenimiento.db; «€» por defecto)."""
    try:
        con = _usuarios._conn()
        fila = con.execute("SELECT valor FROM config WHERE clave='moneda'").fetchone()
        con.close()
        return (fila[0] if fila and fila[0] else "€")
    except Exception:
        return "€"


def fijar_moneda(simbolo):
    simbolo = (simbolo or "").strip()[:8] or "€"
    anterior = moneda()
    con = _usuarios._conn()
    con.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    con.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('moneda', ?)", (simbolo,))
    con.commit()
    con.close()
    if anterior != simbolo:
        _usuarios.auditar("configuracion", "configurar", "Moneda",
                          cambios=[{"campo": "Moneda", "antes": anterior, "despues": simbolo}])
