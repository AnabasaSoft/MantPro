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
proveedores.py — Proveedores del almacén y proveedor habitual de cada artículo.

Pasos 1 y 2 de «Proveedores y punto de pedido»: un catálogo de proveedores
(nombre, contacto, teléfono, correo y notas), el proveedor habitual de cada
artículo y el historial de precios por proveedor. Más adelante colgarán de aquí
los pedidos y el pedido sugerido.

Vive en almacen.db, junto al resto del almacén. Python puro, sin Qt: lo usan
la API del servidor y la ventana del PC. Los errores se devuelven como códigos
(«nombre_obligatorio», «repetido»…) para que cada interfaz los traduzca.
"""

from . import almacen
from . import usuarios as _usuarios

_MAX_TEXTO = 200
_MAX_NOTA = 2000

_ETIQUETAS = {"nombre": "Nombre", "contacto": "Contacto", "telefono": "Teléfono",
              "correo": "Correo", "nota": "Notas"}


def inicializar():
    """Crea la tabla y la columna del proveedor habitual si no existen. Idempotente."""
    con = almacen._conn()
    con.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT NOT NULL,
            contacto TEXT NOT NULL DEFAULT '',
            telefono TEXT NOT NULL DEFAULT '',
            correo   TEXT NOT NULL DEFAULT '',
            nota     TEXT NOT NULL DEFAULT ''
        )
    """)
    # Proveedor habitual del artículo. Sin clave ajena a propósito: al borrar un
    # proveedor se sueltan los artículos a mano (borrar_proveedor), y así la
    # columna se puede añadir con ALTER TABLE sin rehacer la tabla.
    if "proveedor_id" not in almacen._columnas(con, "materiales"):
        con.execute("ALTER TABLE materiales ADD COLUMN proveedor_id INTEGER")
    con.execute("CREATE INDEX IF NOT EXISTS idx_materiales_proveedor ON materiales(proveedor_id)")
    _inicializar_precios(con)
    con.commit()
    con.close()


def _texto(valor, maximo=_MAX_TEXTO):
    return str(valor if valor is not None else "").strip()[:maximo]


def _limpiar(nombre, contacto, telefono, correo, nota):
    return {"nombre": _texto(nombre), "contacto": _texto(contacto), "telefono": _texto(telefono),
            "correo": _texto(correo), "nota": _texto(nota, _MAX_NOTA)}


def _existe_nombre(con, nombre, excluir_id=None):
    for fila in con.execute("SELECT id, nombre FROM proveedores"):
        if fila["id"] != excluir_id and fila["nombre"].casefold() == nombre.casefold():
            return True
    return False


def _foto(proveedor_id):
    p = obtener_proveedor(proveedor_id)
    return {k: (p or {}).get(k, "") for k in _ETIQUETAS}


def listar_proveedores():
    """Todos los proveedores por nombre, con `articulos`: cuántos artículos los
    tienen como proveedor habitual."""
    con = almacen._conn()
    filas = con.execute("""
        SELECT p.*, (SELECT COUNT(*) FROM materiales m WHERE m.proveedor_id = p.id) AS articulos
        FROM proveedores p
    """).fetchall()
    con.close()
    return sorted((dict(f) for f in filas), key=lambda p: p["nombre"].casefold())


def obtener_proveedor(proveedor_id):
    con = almacen._conn()
    fila = con.execute("""
        SELECT p.*, (SELECT COUNT(*) FROM materiales m WHERE m.proveedor_id = p.id) AS articulos
        FROM proveedores p WHERE p.id = ?
    """, (proveedor_id,)).fetchone()
    con.close()
    return dict(fila) if fila else None


def crear_proveedor(nombre, contacto="", telefono="", correo="", nota=""):
    """Da de alta un proveedor. Devuelve (id, None) o (None, código_de_error)."""
    datos = _limpiar(nombre, contacto, telefono, correo, nota)
    if not datos["nombre"]:
        return None, "nombre_obligatorio"
    con = almacen._conn()
    if _existe_nombre(con, datos["nombre"]):
        con.close()
        return None, "repetido"
    proveedor_id = con.execute(
        "INSERT INTO proveedores (nombre, contacto, telefono, correo, nota) VALUES (?,?,?,?,?)",
        (datos["nombre"], datos["contacto"], datos["telefono"], datos["correo"], datos["nota"])).lastrowid
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "crear", f"Proveedor «{datos['nombre']}»",
                      cambios=_usuarios.diferencias({}, datos, _ETIQUETAS))
    return proveedor_id, None


def editar_proveedor(proveedor_id, nombre, contacto="", telefono="", correo="", nota=""):
    """Cambia los datos de un proveedor. Devuelve (True, None) o (False, código)."""
    antes = _foto(proveedor_id)
    if obtener_proveedor(proveedor_id) is None:
        return False, "no_existe"
    datos = _limpiar(nombre, contacto, telefono, correo, nota)
    if not datos["nombre"]:
        return False, "nombre_obligatorio"
    con = almacen._conn()
    if _existe_nombre(con, datos["nombre"], excluir_id=proveedor_id):
        con.close()
        return False, "repetido"
    con.execute("UPDATE proveedores SET nombre=?, contacto=?, telefono=?, correo=?, nota=? WHERE id=?",
                (datos["nombre"], datos["contacto"], datos["telefono"], datos["correo"], datos["nota"],
                 proveedor_id))
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "editar", f"Proveedor «{datos['nombre']}»",
                      cambios=_usuarios.diferencias(antes, datos, _ETIQUETAS))
    return True, None


def borrar_proveedor(proveedor_id):
    """Borra un proveedor y deja sin proveedor habitual a los artículos que lo
    tenían. Devuelve (True, None) o (False, "no_existe")."""
    proveedor = obtener_proveedor(proveedor_id)
    if proveedor is None:
        return False, "no_existe"
    con = almacen._conn()
    con.execute("UPDATE materiales SET proveedor_id = NULL WHERE proveedor_id = ?", (proveedor_id,))
    con.execute("UPDATE precios_proveedor SET proveedor_id = NULL WHERE proveedor_id = ?", (proveedor_id,))
    try:   # los pedidos guardados conservan el nombre del proveedor (tabla de compras.py)
        con.execute("UPDATE pedidos SET proveedor_id = NULL WHERE proveedor_id = ?", (proveedor_id,))
    except Exception:
        pass
    con.execute("DELETE FROM proveedores WHERE id = ?", (proveedor_id,))
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "borrar", f"Proveedor «{proveedor['nombre']}»",
                      detalle=f"Artículos que lo tenían como proveedor habitual: {proveedor['articulos']}")
    return True, None


# ------------------------------------------------------- proveedor habitual

def proveedor_habitual(material_id):
    """Proveedor habitual del artículo (diccionario) o None."""
    con = almacen._conn()
    fila = con.execute("""
        SELECT p.* FROM proveedores p JOIN materiales m ON m.proveedor_id = p.id WHERE m.id = ?
    """, (material_id,)).fetchone()
    con.close()
    return dict(fila) if fila else None


def fijar_proveedor_habitual(material_id, proveedor_id):
    """Pone (o quita, con None) el proveedor habitual de un artículo. Devuelve
    (True, None) o (False, código). Apunta el cambio en el registro solo si cambia."""
    material = almacen.obtener_material(material_id)
    if material is None:
        return False, "material_no_existe"
    if proveedor_id in ("", 0):
        proveedor_id = None
    nuevo = None
    if proveedor_id is not None:
        try:
            nuevo = obtener_proveedor(int(proveedor_id))
        except (TypeError, ValueError):
            nuevo = None
        if nuevo is None:
            return False, "no_existe"
    anterior = proveedor_habitual(material_id)
    id_anterior = anterior["id"] if anterior else None
    id_nuevo = nuevo["id"] if nuevo else None
    if id_anterior == id_nuevo:
        return True, None
    con = almacen._conn()
    con.execute("UPDATE materiales SET proveedor_id = ? WHERE id = ?", (id_nuevo, material_id))
    con.commit()
    con.close()
    objeto = f"{material['codigo']} · {material['nombre']}" if material.get("codigo") else material["nombre"]
    _usuarios.auditar("almacen", "editar", objeto, cambios=[{
        "campo": "Proveedor habitual",
        "antes": anterior["nombre"] if anterior else "",
        "despues": nuevo["nombre"] if nuevo else ""}])
    return True, None


def materiales_de_proveedor(proveedor_id):
    """Artículos (id, código, nombre) que tienen a este proveedor como habitual."""
    con = almacen._conn()
    filas = con.execute("SELECT id, codigo, nombre FROM materiales WHERE proveedor_id = ? ORDER BY nombre",
                        (proveedor_id,)).fetchall()
    con.close()
    return [dict(f) for f in filas]


# ------------------------------------------------- historial de precios
# Cada fila es una compra o una oferta: cuándo, a qué proveedor y a cuánto. El
# `precio` del artículo (el que usan los costes) NO cambia solo: ver
# fijar_precio_articulo(), que se usa siempre tras una confirmación.

def _inicializar_precios(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS precios_proveedor (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id      INTEGER NOT NULL REFERENCES materiales(id) ON DELETE CASCADE,
            proveedor_id     INTEGER,               -- NULL si el proveedor se borró después
            proveedor_nombre TEXT NOT NULL DEFAULT '',  -- copia, para no perder el historial
            fecha            TEXT NOT NULL,         -- AAAA-MM-DD
            precio           REAL,                  -- NULL: se compró sin apuntar el precio
            cantidad         REAL,
            referencia       TEXT NOT NULL DEFAULT '',  -- referencia del proveedor para este artículo
            nota             TEXT NOT NULL DEFAULT '',
            usuario_nombre   TEXT NOT NULL DEFAULT ''
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_precios_material ON precios_proveedor(material_id, fecha)")


def _numero(valor):
    if valor is None or valor == "":
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def _fecha_valida(texto):
    from datetime import datetime
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def registrar_precio(material_id, proveedor_id, precio=None, cantidad=None, fecha=None,
                     referencia="", nota="", usuario_nombre=""):
    """Apunta una compra u oferta de un artículo a un proveedor. [precio] puede
    ser None (se compró sin apuntar el precio). Devuelve (id, None) o (None, código)."""
    from datetime import date
    if almacen.obtener_material(material_id) is None:
        return None, "material_no_existe"
    try:
        proveedor = obtener_proveedor(int(proveedor_id))
    except (TypeError, ValueError):
        proveedor = None
    if proveedor is None:
        return None, "no_existe"
    precio, cantidad = _numero(precio), _numero(cantidad)
    if (precio is not None and precio < 0) or (cantidad is not None and cantidad < 0):
        return None, "negativo"
    fecha = fecha if _fecha_valida(fecha) else date.today().strftime("%Y-%m-%d")
    con = almacen._conn()
    nuevo = con.execute("""
        INSERT INTO precios_proveedor (material_id, proveedor_id, proveedor_nombre, fecha, precio, cantidad,
                                       referencia, nota, usuario_nombre)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (material_id, proveedor["id"], proveedor["nombre"], fecha, precio, cantidad,
         _texto(referencia), _texto(nota, _MAX_NOTA), _texto(usuario_nombre))).lastrowid
    con.commit()
    con.close()
    return nuevo, None


def historial_precios(material_id, limite=500):
    """Apuntes de precio del artículo, del más reciente al más antiguo."""
    con = almacen._conn()
    filas = con.execute("""
        SELECT pp.*, COALESCE(p.nombre, pp.proveedor_nombre) AS proveedor
        FROM precios_proveedor pp LEFT JOIN proveedores p ON p.id = pp.proveedor_id
        WHERE pp.material_id = ? ORDER BY pp.fecha DESC, pp.id DESC LIMIT ?""",
        (material_id, limite)).fetchall()
    con.close()
    return [dict(f) for f in filas]


def resumen_precios(material_id):
    """Último precio de cada proveedor (solo apuntes con precio), del más barato
    al más caro. Cada fila: proveedor_id, proveedor, precio, fecha, referencia,
    anterior (el precio anterior de ese mismo proveedor, o None) y `mas_barato`."""
    ultimos, anteriores = {}, {}
    for h in historial_precios(material_id):       # del más reciente al más antiguo
        if h["precio"] is None:
            continue
        clave = h["proveedor_id"] if h["proveedor_id"] is not None else ("borrado", h["proveedor"])
        if clave not in ultimos:
            ultimos[clave] = h
        elif clave not in anteriores:
            anteriores[clave] = h["precio"]
    filas = [{"proveedor_id": h["proveedor_id"], "proveedor": h["proveedor"], "precio": h["precio"],
              "fecha": h["fecha"], "referencia": h["referencia"], "anterior": anteriores.get(clave)}
             for clave, h in ultimos.items()]
    filas.sort(key=lambda f: (f["precio"], f["proveedor"].casefold()))
    for f in filas:
        f["mas_barato"] = bool(filas) and f["precio"] == filas[0]["precio"] and len(filas) > 1
    return filas


def borrar_precio(precio_id):
    """Borra un apunte del historial (p. ej. uno mal tecleado)."""
    con = almacen._conn()
    n = con.execute("DELETE FROM precios_proveedor WHERE id = ?", (precio_id,)).rowcount
    con.commit()
    con.close()
    return (True, None) if n else (False, "no_existe")


def fijar_precio_articulo(material_id, precio, usuario_id=None, usuario_nombre=None):
    """Cambia el precio unitario del artículo (el de los costes), dejándolo en el
    registro de cambios. Se llama solo tras confirmar o si lo pide un administrador."""
    m = almacen.obtener_material(material_id)
    if m is None:
        return False, "material_no_existe"
    almacen.actualizar_material(
        material_id, m.get("codigo") or "", m["nombre"], m.get("descripcion") or "", m.get("unidad") or "",
        m.get("stock_minimo") or 0, m.get("seccion_id"), m.get("foto"), usuario_id, usuario_nombre,
        precio=_numero(precio), cambiar_precio=True)
    return True, None
