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

Primer paso de «Proveedores y punto de pedido»: un catálogo de proveedores
(nombre, contacto, teléfono, correo y notas) y, para cada artículo, cuál es su
proveedor habitual. Más adelante colgarán de aquí el historial de precios, los
pedidos y el pedido sugerido.

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
