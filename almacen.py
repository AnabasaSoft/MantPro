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
almacen.py — Control de stock de material de almacén para MantPro.

Vive en una base de datos SQLite propia, independiente de la de los
trabajos de mantenimiento, para mantener ambos ámbitos desacoplados.

Modelo de ubicación (inspirado en la codificación de ubicaciones de
almacén Estantería-Balda-Sección, análogo a Aisle-Rack-Shelf-Bin):

    Estantería  -> Balda (numerada de abajo a arriba, empezando en 1;
                   la balda 0 representa el hueco en el suelo, si existe)
                -> Sección (subdivisión dentro de la balda)

Cada material se ubica en una sección concreta. El stock se modifica
únicamente a través de movimientos (entrada/salida), que quedan
registrados para trazabilidad.

Uso desde main.py:

    import almacen
    almacen.configurar_db(RUTA_DB_ALMACEN)
    almacen.inicializar()
"""

import sqlite3

RUTA_DB = "almacen.db"


def configurar_db(ruta):
    """Fija la ruta de la base de datos que usará este módulo."""
    global RUTA_DB
    RUTA_DB = ruta


def _conn():
    con = sqlite3.connect(RUTA_DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _columnas(con, tabla):
    try:
        return {fila["name"] for fila in con.execute(f"PRAGMA table_info({tabla})")}
    except sqlite3.Error:
        return set()


def inicializar():
    """Crea las tablas si no existen. Idempotente."""
    con = _conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estanterias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tiene_hueco_suelo INTEGER NOT NULL DEFAULT 0,
            estilo_baldas TEXT NOT NULL DEFAULT 'numero'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS baldas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estanteria_id INTEGER NOT NULL REFERENCES estanterias(id) ON DELETE CASCADE,
            numero INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS secciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            balda_id INTEGER NOT NULL REFERENCES baldas(id) ON DELETE CASCADE,
            nombre TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS materiales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            unidad TEXT,
            stock_actual REAL NOT NULL DEFAULT 0,
            stock_minimo REAL NOT NULL DEFAULT 0,
            seccion_id INTEGER REFERENCES secciones(id) ON DELETE SET NULL,
            foto TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL REFERENCES materiales(id) ON DELETE CASCADE,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            cantidad REAL NOT NULL,
            usuario_id INTEGER,
            usuario_nombre TEXT,
            motivo TEXT
        )
    """)

    # --- columnas nuevas en tablas existentes ---
    if "estilo_baldas" not in _columnas(con, "estanterias"):
        cur.execute("ALTER TABLE estanterias ADD COLUMN estilo_baldas TEXT NOT NULL DEFAULT 'numero'")

    con.commit()
    con.close()


# ---------------------------------------------------------------- estructura

def _letra_seccion(indice):
    """Convierte un índice (1, 2, 3...) en letras estilo columnas de hoja de
    cálculo: A, B, ..., Z, AA, AB... para no limitar a 26 secciones por balda."""
    letras = ""
    while indice > 0:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(ord('A') + resto) + letras
    return letras


def texto_balda(numero, estilo_baldas="numero"):
    """Texto identificativo de una balda (sin el prefijo "Balda"/"Suelo": eso lo
    añade cada interfaz en su propio idioma). La balda 0 (hueco de suelo) no
    tiene número visible, así que se devuelve como cadena vacía."""
    if numero == 0:
        return ""
    return _letra_seccion(numero) if estilo_baldas == "letra" else str(numero)


def crear_estanteria(nombre, num_baldas, tiene_hueco_suelo, num_secciones=0,
                      estilo_baldas="numero", estilo_secciones="letra"):
    """Crea una estantería con sus baldas (numeradas internamente de 1 a
    num_baldas, de abajo a arriba; ese número interno se usa siempre para
    ordenar, aunque en pantalla se muestre como letra si estilo_baldas="letra").
    Si tiene_hueco_suelo, añade también la balda 0.
    Si num_secciones > 0, crea esa cantidad de secciones ("Sección A"/"Sección 1"...
    según estilo_secciones) en cada balda creada."""
    con = _conn()
    cur = con.cursor()
    cur.execute("INSERT INTO estanterias (nombre, tiene_hueco_suelo, estilo_baldas) VALUES (?, ?, ?)",
                (nombre, 1 if tiene_hueco_suelo else 0, estilo_baldas))
    estanteria_id = cur.lastrowid

    def _crear_balda(numero):
        cur.execute("INSERT INTO baldas (estanteria_id, numero) VALUES (?, ?)", (estanteria_id, numero))
        balda_id = cur.lastrowid
        for i in range(1, int(num_secciones) + 1):
            etiqueta = _letra_seccion(i) if estilo_secciones == "letra" else str(i)
            cur.execute("INSERT INTO secciones (balda_id, nombre) VALUES (?, ?)",
                        (balda_id, f"Sección {etiqueta}"))

    if tiene_hueco_suelo:
        _crear_balda(0)
    for numero in range(1, int(num_baldas) + 1):
        _crear_balda(numero)
    con.commit()
    con.close()
    return estanteria_id


def eliminar_estanteria(estanteria_id):
    """Borra la estantería y su estructura. Falla si contiene material ubicado."""
    if _estanteria_tiene_material(estanteria_id):
        return False, "no_vacio"
    con = _conn()
    con.execute("DELETE FROM estanterias WHERE id=?", (estanteria_id,))
    con.commit()
    con.close()
    return True, None


def _estanteria_tiene_material(estanteria_id):
    con = _conn()
    fila = con.execute("""
        SELECT COUNT(*) AS n FROM materiales m
        JOIN secciones s ON m.seccion_id = s.id
        JOIN baldas b ON s.balda_id = b.id
        WHERE b.estanteria_id = ?
    """, (estanteria_id,)).fetchone()
    con.close()
    return fila["n"] > 0


def anadir_balda(estanteria_id):
    """Añade una balda nueva por encima de las existentes (no reinicia numeración)."""
    con = _conn()
    cur = con.cursor()
    fila = cur.execute(
        "SELECT MAX(numero) AS maximo FROM baldas WHERE estanteria_id=? AND numero > 0",
        (estanteria_id,)).fetchone()
    siguiente = (fila["maximo"] or 0) + 1
    cur.execute("INSERT INTO baldas (estanteria_id, numero) VALUES (?, ?)", (estanteria_id, siguiente))
    con.commit()
    con.close()
    return siguiente


def eliminar_balda(balda_id):
    """Borra una balda (y sus secciones). Falla si contiene material ubicado."""
    if _balda_tiene_material(balda_id):
        return False, "no_vacio"
    con = _conn()
    con.execute("DELETE FROM baldas WHERE id=?", (balda_id,))
    con.commit()
    con.close()
    return True, None


def _balda_tiene_material(balda_id):
    con = _conn()
    fila = con.execute("""
        SELECT COUNT(*) AS n FROM materiales m
        JOIN secciones s ON m.seccion_id = s.id
        WHERE s.balda_id = ?
    """, (balda_id,)).fetchone()
    con.close()
    return fila["n"] > 0


def crear_seccion(balda_id, nombre):
    con = _conn()
    cur = con.cursor()
    cur.execute("INSERT INTO secciones (balda_id, nombre) VALUES (?, ?)", (balda_id, nombre))
    seccion_id = cur.lastrowid
    con.commit()
    con.close()
    return seccion_id


def eliminar_seccion(seccion_id):
    """Borra una sección. Falla si contiene material ubicado."""
    con = _conn()
    fila = con.execute("SELECT COUNT(*) AS n FROM materiales WHERE seccion_id=?", (seccion_id,)).fetchone()
    if fila["n"] > 0:
        con.close()
        return False, "no_vacio"
    con.execute("DELETE FROM secciones WHERE id=?", (seccion_id,))
    con.commit()
    con.close()
    return True, None


def listar_estructura():
    """Devuelve la estructura completa anidada:
    [{id, nombre, tiene_hueco_suelo, baldas: [{id, numero, secciones: [{id, nombre}, ...]}, ...]}, ...]
    Las baldas se devuelven ordenadas de arriba hacia abajo (más intuitivo visualmente),
    dejando la balda 0 (hueco de suelo) siempre al final."""
    con = _conn()
    estanterias = [dict(row) for row in con.execute("SELECT * FROM estanterias ORDER BY nombre")]
    for est in estanterias:
        baldas = [dict(row) for row in con.execute(
            "SELECT * FROM baldas WHERE estanteria_id=? ORDER BY numero DESC", (est["id"],))]
        for balda in baldas:
            balda["secciones"] = [dict(row) for row in con.execute(
                "SELECT * FROM secciones WHERE balda_id=? ORDER BY nombre", (balda["id"],))]
        est["baldas"] = baldas
    con.close()
    return estanterias


def obtener_ubicacion_texto(seccion_id):
    """Devuelve una cadena tipo 'Estantería A > Balda 2 > Sección B' para una sección."""
    if not seccion_id:
        return ""
    con = _conn()
    fila = con.execute("""
        SELECT e.nombre AS estanteria, e.estilo_baldas AS estilo_baldas, b.numero AS balda, s.nombre AS seccion
        FROM secciones s
        JOIN baldas b ON s.balda_id = b.id
        JOIN estanterias e ON b.estanteria_id = e.id
        WHERE s.id = ?
    """, (seccion_id,)).fetchone()
    con.close()
    if not fila:
        return ""
    nombre_balda = "Suelo" if fila["balda"] == 0 else f"Balda {texto_balda(fila['balda'], fila['estilo_baldas'])}"
    return f"{fila['estanteria']} > {nombre_balda} > {fila['seccion']}"


# ---------------------------------------------------------------- materiales

def crear_material(codigo, nombre, descripcion, unidad, stock_minimo, seccion_id, foto,
                    stock_inicial=0, usuario_id=None, usuario_nombre=None):
    con = _conn()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO materiales (codigo, nombre, descripcion, unidad, stock_actual, stock_minimo, seccion_id, foto)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (codigo, nombre, descripcion, unidad, 0, stock_minimo, seccion_id, foto))
    material_id = cur.lastrowid
    con.commit()
    con.close()
    if stock_inicial and float(stock_inicial) > 0:
        registrar_movimiento(material_id, "entrada", float(stock_inicial),
                              usuario_id, usuario_nombre, motivo="Alta inicial")
    return material_id


def actualizar_material(material_id, codigo, nombre, descripcion, unidad, stock_minimo, seccion_id, foto,
                         usuario_id=None, usuario_nombre=None):
    con = _conn()
    seccion_anterior = con.execute(
        "SELECT seccion_id FROM materiales WHERE id=?", (material_id,)).fetchone()["seccion_id"]
    con.execute("""
        UPDATE materiales SET codigo=?, nombre=?, descripcion=?, unidad=?, stock_minimo=?, seccion_id=?, foto=?
        WHERE id=?
    """, (codigo, nombre, descripcion, unidad, stock_minimo, seccion_id, foto, material_id))
    con.commit()
    con.close()
    if seccion_id != seccion_anterior:
        origen = obtener_ubicacion_texto(seccion_anterior) or "Sin ubicación"
        destino = obtener_ubicacion_texto(seccion_id) or "Sin ubicación"
        _registrar_traslado(material_id, origen, destino, usuario_id, usuario_nombre)


def _registrar_traslado(material_id, origen, destino, usuario_id, usuario_nombre):
    from datetime import datetime
    con = _conn()
    con.execute("""
        INSERT INTO movimientos (material_id, fecha, tipo, cantidad, usuario_id, usuario_nombre, motivo)
        VALUES (?, ?, 'traslado', 0, ?, ?, ?)
    """, (material_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario_id, usuario_nombre,
          f"De {origen} a {destino}"))
    con.commit()
    con.close()


def borrar_material(material_id):
    con = _conn()
    con.execute("DELETE FROM materiales WHERE id=?", (material_id,))
    con.commit()
    con.close()


def obtener_material(material_id):
    con = _conn()
    fila = con.execute("SELECT * FROM materiales WHERE id=?", (material_id,)).fetchone()
    con.close()
    return dict(fila) if fila else None


def listar_materiales(filtro_texto=None):
    con = _conn()
    if filtro_texto:
        patron = f"%{filtro_texto}%"
        filas = con.execute("""
            SELECT DISTINCT m.* FROM materiales m
            LEFT JOIN secciones s ON m.seccion_id = s.id
            LEFT JOIN baldas b ON s.balda_id = b.id
            LEFT JOIN estanterias e ON b.estanteria_id = e.id
            WHERE m.nombre LIKE ? OR m.codigo LIKE ? OR m.descripcion LIKE ?
               OR e.nombre LIKE ? OR s.nombre LIKE ?
            ORDER BY m.nombre
        """, (patron, patron, patron, patron, patron)).fetchall()
    else:
        filas = con.execute("SELECT * FROM materiales ORDER BY nombre").fetchall()
    con.close()
    return [dict(f) for f in filas]


def materiales_bajo_minimo():
    """Materiales sin stock (aunque no tengan mínimo configurado) o por debajo de su mínimo."""
    con = _conn()
    filas = con.execute(
        "SELECT * FROM materiales WHERE stock_actual <= 0 OR stock_actual < stock_minimo ORDER BY nombre").fetchall()
    con.close()
    return [dict(f) for f in filas]


# ---------------------------------------------------------------- movimientos

def registrar_movimiento(material_id, tipo, cantidad, usuario_id, usuario_nombre, motivo=""):
    """tipo: 'entrada' o 'salida'. Actualiza el stock y deja constancia del movimiento.
    Devuelve (True, None) o (False, "stock_insuficiente")."""
    from datetime import datetime
    con = _conn()
    cur = con.cursor()
    fila = cur.execute("SELECT stock_actual FROM materiales WHERE id=?", (material_id,)).fetchone()
    if fila is None:
        con.close()
        return False, "material_no_existe"
    stock_actual = fila["stock_actual"]
    if tipo == "salida" and cantidad > stock_actual:
        con.close()
        return False, "stock_insuficiente"
    nuevo_stock = stock_actual + cantidad if tipo == "entrada" else stock_actual - cantidad
    cur.execute("UPDATE materiales SET stock_actual=? WHERE id=?", (nuevo_stock, material_id))
    cur.execute("""
        INSERT INTO movimientos (material_id, fecha, tipo, cantidad, usuario_id, usuario_nombre, motivo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (material_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tipo, cantidad,
          usuario_id, usuario_nombre, motivo))
    con.commit()
    con.close()
    return True, None


def obtener_movimientos(material_id, limite=20):
    con = _conn()
    filas = con.execute(
        "SELECT * FROM movimientos WHERE material_id=? ORDER BY id DESC LIMIT ?",
        (material_id, limite)).fetchall()
    con.close()
    return [dict(f) for f in filas]
