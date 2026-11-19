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
tarifas.py — Tarifas de proveedor (Excel/CSV) y relación fija artículo–proveedor.

Decisiones del usuario (2026-11-19):
  * Cada artículo guarda, por proveedor, su referencia (tabla `articulo_proveedor`,
    una fila por artículo y proveedor, sobre la fila ORIGINAL del artículo: la de
    `articulo_id` NULL, que representa al mismo artículo en todos los almacenes).
  * Una fila de la tarifa se enlaza por esa referencia; si no, por el «Código» del
    artículo cuando coincide con la referencia (y es único); si no, queda «sin
    enlazar» y se puede enlazar a mano (queda recordado) o crear el artículo.
  * Siempre se apunta en el historial de precios del proveedor; el precio del artículo
    (el de los costes) solo cambia en los artículos que se marquen (de serie, los que
    tienen a ese proveedor como habitual). Afecta a todas sus filas por almacén.
  * Se guarda el precio NETO = precio × (1 − descuento %). El descuento sale de la
    columna de la tarifa o, si no la trae, del descuento general del proveedor.
  * El emparejamiento de columnas se guarda por proveedor (en la base, no en el PC).
  * Los artículos nuevos se crean en el almacén principal, sin «Código» y con este
    proveedor como habitual.

Python puro, sin Qt: lo usan el asistente del PC y la API (solo administradores).
La vista previa (analizar) y la importación (aplicar) usan el mismo análisis.
"""

import json
import re
from datetime import date

from . import almacen
from . import importar
from . import usuarios as _usuarios

# (campo, obligatorio), en el orden del asistente. Etiqueta visible: t("tar_campo_<campo>").
CAMPOS = [("referencia", True), ("precio", True), ("descripcion", False), ("descuento", False),
          ("multiplo", False), ("ean", False), ("plazo", False), ("validez", False)]

# Cabeceras habituales de las tarifas (ya normalizadas con importar.normalizar: sin
# tildes, minúsculas, sin signos ni paréntesis), en los idiomas de la app.
_SINONIMOS = {
    "referencia": ["referencia", "ref", "ref proveedor", "referencia proveedor", "cod", "codigo", "codigo articulo",
                   "cod articulo", "codigo proveedor", "sku", "reference", "item", "item code", "part number",
                   "erreferentzia", "kodea", "referencia del proveedor", "codi", "referencia proveidor",
                   "codigo artigo", "reference fournisseur", "artikelnummer", "art nr", "artikel nr", "bestellnummer"],
    "precio": ["precio", "pvp", "tarifa", "precio tarifa", "precio unitario", "precio neto", "importe", "precio lista",
               "price", "list price", "unit price", "net price", "prezioa", "preu", "preco", "prix", "prix unitaire",
               "preis", "listenpreis", "einzelpreis", "nettopreis", "eur", "euros"],
    "descripcion": ["descripcion", "denominacion", "nombre", "descripcion articulo", "description", "name",
                    "deskribapena", "izena", "descripcio", "descricao", "designation", "libelle", "bezeichnung",
                    "beschreibung", "artikelbezeichnung"],
    "descuento": ["descuento", "dto", "dcto", "desc", "discount", "deskontua", "descompte", "desconto", "remise",
                  "rabatt"],
    "multiplo": ["multiplo", "unidad de venta", "uds embalaje", "embalaje", "lote", "cantidad minima", "minimo",
                 "pack", "multiple", "moq", "verpackungseinheit", "ve", "multiploa", "unitat de venda", "conditionnement"],
    "ean": ["ean", "ean13", "ean 13", "codigo de barras", "gtin", "barcode", "barra kodea", "codi de barres",
            "code barre", "strichcode"],
    "plazo": ["plazo", "plazo entrega", "plazo de entrega", "dias entrega", "lead time", "delivery time", "epea",
              "termini", "prazo", "delai", "lieferzeit"],
    "validez": ["validez", "valido hasta", "fecha validez", "valid until", "validity", "baliozkotasuna", "validesa",
                "validade", "validite", "gultig bis", "gueltig bis"],
}

MAX_FILAS_CABECERA = 30        # dónde se busca la fila de cabecera (las tarifas traen títulos encima)
MAX_CAMBIOS_REGISTRO = 300     # cambios de precio que se detallan en el registro de cambios


# ------------------------------------------------------------------ base de datos

def inicializar():
    """Relación artículo–proveedor y columnas de la tarifa en proveedores. Idempotente.
    La primera vez rellena la relación con las referencias de las compras ya apuntadas."""
    con = almacen._conn()
    try:
        nueva = con.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'articulo_proveedor'").fetchone() is None
        con.execute("""
            CREATE TABLE IF NOT EXISTS articulo_proveedor (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id  INTEGER NOT NULL REFERENCES materiales(id) ON DELETE CASCADE,
                proveedor_id INTEGER NOT NULL REFERENCES proveedores(id) ON DELETE CASCADE,
                referencia   TEXT NOT NULL DEFAULT '',   -- la del proveedor para este artículo
                descripcion  TEXT NOT NULL DEFAULT '',   -- la de la tarifa
                precio_lista REAL,                       -- el de la tarifa, antes del descuento
                descuento    REAL,                       -- % aplicado
                precio       REAL,                       -- neto (el que va al historial)
                fecha        TEXT NOT NULL DEFAULT '',   -- de la última tarifa (AAAA-MM-DD)
                multiplo     REAL,
                ean          TEXT NOT NULL DEFAULT '',
                plazo        INTEGER,
                validez      TEXT NOT NULL DEFAULT '',
                UNIQUE (material_id, proveedor_id)
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_artprov_proveedor ON articulo_proveedor(proveedor_id)")
        columnas = almacen._columnas(con, "proveedores")
        if "descuento" not in columnas:          # descuento general (%) sobre su tarifa
            con.execute("ALTER TABLE proveedores ADD COLUMN descuento REAL")
        if "tarifa_mapeo" not in columnas:       # columnas de su tarifa (JSON)
            con.execute("ALTER TABLE proveedores ADD COLUMN tarifa_mapeo TEXT")
        if nueva:
            _migrar_referencias(con)
        con.commit()
    finally:
        con.close()


def _migrar_referencias(con):
    """Al crear la tabla (una sola vez): la referencia más reciente de cada artículo y
    proveedor de las compras apuntadas pasa a la relación fija."""
    filas = con.execute("""
        SELECT COALESCE(m.articulo_id, m.id) AS raiz, pp.proveedor_id, pp.referencia, pp.precio, pp.fecha
        FROM precios_proveedor pp JOIN materiales m ON m.id = pp.material_id
        JOIN proveedores p ON p.id = pp.proveedor_id
        WHERE TRIM(COALESCE(pp.referencia, '')) != ''
        ORDER BY pp.fecha, pp.id""").fetchall()
    ultimas = {}
    for f in filas:                       # de la más antigua a la más reciente: gana la última
        ultimas[(f["raiz"], f["proveedor_id"])] = f
    for (raiz, proveedor_id), f in ultimas.items():
        con.execute("""INSERT OR IGNORE INTO articulo_proveedor (material_id, proveedor_id, referencia, precio, fecha)
                       VALUES (?,?,?,?,?)""", (raiz, proveedor_id, f["referencia"].strip(), f["precio"], f["fecha"] or ""))


def _raiz(con, material_id):
    fila = con.execute("SELECT COALESCE(articulo_id, id) AS r FROM materiales WHERE id = ?", (material_id,)).fetchone()
    return fila["r"] if fila else None


def proveedores_de_articulo(material_id):
    """Proveedores del artículo con su referencia y su último precio de tarifa (dicts),
    el habitual primero. Sirve cualquier fila del artículo (de cualquier almacén)."""
    con = almacen._conn()
    try:
        raiz = _raiz(con, material_id)
        if raiz is None:
            return []
        filas = con.execute("""
            SELECT ap.*, p.nombre AS proveedor, (m.proveedor_id = ap.proveedor_id) AS habitual
            FROM articulo_proveedor ap JOIN proveedores p ON p.id = ap.proveedor_id
            JOIN materiales m ON m.id = ap.material_id
            WHERE ap.material_id = ? ORDER BY habitual DESC, p.nombre COLLATE NOCASE""", (raiz,)).fetchall()
        return [dict(f) for f in filas]
    finally:
        con.close()


def anotar_referencia(material_id, proveedor_id, referencia):
    """La referencia de una compra apuntada pasa a la relación fija artículo–proveedor
    (si ese proveedor no la tiene ya en otro artículo). Sin registro de cambios: el
    apunte de la compra ya es el rastro."""
    referencia = " ".join(str(referencia or "").split())[:200]
    if not referencia:
        return
    con = almacen._conn()
    try:
        raiz = _raiz(con, material_id)
        otra = _buscar_por_referencia(con, proveedor_id).get(_ref(referencia))
        if raiz is None or (otra is not None and otra != raiz):
            return
        con.execute("""INSERT INTO articulo_proveedor (material_id, proveedor_id, referencia) VALUES (?,?,?)
                       ON CONFLICT(material_id, proveedor_id) DO UPDATE SET referencia = excluded.referencia""",
                    (raiz, proveedor_id, referencia))
        con.commit()
    finally:
        con.close()


def fijar_referencia(material_id, proveedor_id, referencia):
    """Pone (o quita, con texto vacío) la referencia del proveedor de un artículo.
    Devuelve (True, None) o (False, código)."""
    referencia = " ".join(str(referencia or "").split())[:200]
    con = almacen._conn()
    try:
        raiz = _raiz(con, material_id)
        if raiz is None:
            return False, "material_no_existe"
        prov = con.execute("SELECT nombre FROM proveedores WHERE id = ?", (proveedor_id,)).fetchone()
        if prov is None:
            return False, "no_existe"
        otra = _buscar_por_referencia(con, proveedor_id).get(_ref(referencia)) if referencia else None
        if otra is not None and otra != raiz:
            return False, "referencia_repetida"
        antes = con.execute("SELECT referencia FROM articulo_proveedor WHERE material_id = ? AND proveedor_id = ?",
                            (raiz, proveedor_id)).fetchone()
        if referencia:
            con.execute("""INSERT INTO articulo_proveedor (material_id, proveedor_id, referencia) VALUES (?,?,?)
                           ON CONFLICT(material_id, proveedor_id) DO UPDATE SET referencia = excluded.referencia""",
                        (raiz, proveedor_id, referencia))
        elif antes is not None:
            con.execute("DELETE FROM articulo_proveedor WHERE material_id = ? AND proveedor_id = ?", (raiz, proveedor_id))
        con.commit()
        nombre = con.execute("SELECT codigo, nombre FROM materiales WHERE id = ?", (raiz,)).fetchone()
    finally:
        con.close()
    if (antes["referencia"] if antes else "") != referencia:
        objeto = f"{nombre['codigo']} · {nombre['nombre']}" if nombre["codigo"] else nombre["nombre"]
        _usuarios.auditar("almacen", "editar", objeto, cambios=[{
            "campo": f"Referencia de {prov['nombre']}", "antes": antes["referencia"] if antes else "", "despues": referencia}])
    return True, None


# ------------------------------------------------------------------ ajustes por proveedor

def ajustes(proveedor_id):
    """{"descuento": % general o None, "mapeo": {"fila_cabecera": n, "columnas": {campo: cabecera}}}."""
    con = almacen._conn()
    try:
        f = con.execute("SELECT descuento, tarifa_mapeo FROM proveedores WHERE id = ?", (proveedor_id,)).fetchone()
    finally:
        con.close()
    if f is None:
        return {"descuento": None, "mapeo": {}}
    try:
        mapeo = json.loads(f["tarifa_mapeo"] or "{}")
    except (TypeError, ValueError):
        mapeo = {}
    return {"descuento": f["descuento"], "mapeo": mapeo if isinstance(mapeo, dict) else {}}


def guardar_ajustes(proveedor_id, descuento, mapeo_guardado):
    """Guarda el descuento general y las columnas de la tarifa del proveedor."""
    descuento = _descuento(descuento)
    con = almacen._conn()
    try:
        antes = con.execute("SELECT nombre, descuento FROM proveedores WHERE id = ?", (proveedor_id,)).fetchone()
        if antes is None:
            return False, "no_existe"
        con.execute("UPDATE proveedores SET descuento = ?, tarifa_mapeo = ? WHERE id = ?",
                    (descuento, json.dumps(mapeo_guardado or {}, ensure_ascii=False), proveedor_id))
        con.commit()
    finally:
        con.close()
    if antes["descuento"] != descuento:
        _usuarios.auditar("almacen", "editar", antes["nombre"], cambios=[{
            "campo": "Descuento sobre su tarifa (%)",
            "antes": "" if antes["descuento"] is None else f"{antes['descuento']:g}",
            "despues": "" if descuento is None else f"{descuento:g}"}])
    return True, None


def mapeo_a_guardar(cabeceras, mapeo, fila_cabecera):
    """Lo que se guarda del emparejamiento: el texto de la cabecera de cada campo
    (así sirve aunque el proveedor cambie las columnas de sitio)."""
    return {"fila_cabecera": fila_cabecera,
            "columnas": {c: cabeceras[j] for c, j in mapeo.items() if j is not None and 0 <= j < len(cabeceras)}}


def mapeo_guardado(cabeceras, guardado):
    """{campo: índice} a partir de lo guardado (por el texto de la cabecera); lo que no
    encaja se empareja solo por el nombre."""
    mapeo = emparejar_automatico(cabeceras)
    columnas = (guardado or {}).get("columnas") or {}
    norm = [importar.normalizar(c) for c in cabeceras]
    for campo, cab in columnas.items():
        if campo in dict(CAMPOS) and importar.normalizar(cab) in norm:
            j = norm.index(importar.normalizar(cab))
            for otro, k in list(mapeo.items()):     # cada columna, un solo campo
                if k == j and otro != campo:
                    del mapeo[otro]
            mapeo[campo] = j
    return mapeo


# ------------------------------------------------------------------ lectura

def _crudas(ruta, hoja=None):
    importar._comprobar_extension(ruta)
    if ruta.lower().endswith(".xlsx"):
        libro = importar._abrir_excel(ruta)
        try:
            h = libro[hoja] if hoja else libro.worksheets[0]
            return [(i, list(f)) for i, f in enumerate(h.iter_rows(values_only=True), start=1)]
        except Exception as e:
            raise importar.ErrorLectura(importar.t("imp_err_leer").format(error=e))
        finally:
            libro.close()
    return list(enumerate(importar._leer_csv(ruta), start=1))


def _puntuacion_cabecera(valores):
    """Cuántos campos distintos reconoce en esta fila (para encontrar la cabecera)."""
    norm = {importar.normalizar(importar.texto_celda(v)) for v in valores}
    return sum(1 for sin in _SINONIMOS.values() if norm & set(sin))


def leer(ruta, hoja=None, fila_cabecera=None):
    """(cabeceras, filas, fila_cabecera) de una tarifa. Las filas: [(número en el fichero,
    [valores])]. La cabecera es [fila_cabecera] o, si no se da, la fila de las
    MAX_FILAS_CABECERA primeras que más campos reconoce (o la primera no vacía)."""
    vacia = lambda valores: all(importar.texto_celda(v) == "" for v in valores)
    crudas = [(i, v) for i, v in _crudas(ruta, hoja) if not vacia(v)]
    if not crudas:
        raise importar.ErrorLectura(importar.t("imp_err_vacio"))
    pos = None
    if fila_cabecera:
        pos = next((k for k, (i, _) in enumerate(crudas) if i == int(fila_cabecera)), None)
    if pos is None:
        puntos = [(_puntuacion_cabecera(v), -k) for k, (_, v) in enumerate(crudas[:MAX_FILAS_CABECERA])]
        mejor = max(puntos)
        pos = -mejor[1] if mejor[0] >= 2 else 0
    numero_cabecera, cabecera = crudas[pos]
    resto = crudas[pos + 1:]
    ancho = max([len(cabecera)] + [len(v) for _, v in resto])
    while ancho > 0 and all(len(v) < ancho or importar.texto_celda(v[ancho - 1]) == ""
                            for _, v in [(numero_cabecera, cabecera)] + resto):
        ancho -= 1
    cabeceras = [(importar.texto_celda(cabecera[j]) if j < len(cabecera) else "")
                 or importar.t("imp_columna_n").format(n=j + 1) for j in range(ancho)]
    filas = [(i, (list(v) + [None] * ancho)[:ancho]) for i, v in resto]
    return cabeceras, filas, numero_cabecera


def emparejar_automatico(cabeceras):
    """{campo: índice de columna} adivinado por el nombre de las cabeceras. Primero las
    coincidencias exactas y, para lo que quede, que la cabecera empiece por el sinónimo."""
    from .. import idiomas
    norm = [importar.normalizar(c) for c in cabeceras]
    usadas, mapeo = set(), {}
    candidatos = {}
    for campo, _ in CAMPOS:
        c = set(_SINONIMOS.get(campo, []))
        c |= {importar.normalizar(d[f"tar_campo_{campo}"]) for d in idiomas.TRADUCCIONES.values()
              if f"tar_campo_{campo}" in d}
        c.discard("")
        candidatos[campo] = c
    for exacta in (True, False):
        for campo, _ in CAMPOS:
            if campo in mapeo:
                continue
            for j, cab in enumerate(norm):
                if j in usadas or not cab:
                    continue
                if (cab in candidatos[campo]) if exacta else \
                        any(len(s) >= 3 and (cab.startswith(s + " ") or cab.endswith(" " + s)) for s in candidatos[campo]):
                    mapeo[campo] = j
                    usadas.add(j)
                    break
    return mapeo


# ------------------------------------------------------------------ valores

def _ref(texto):
    """Referencia para comparar: sin espacios y sin distinguir mayúsculas."""
    return re.sub(r"\s+", "", str(texto or "")).casefold()


def _limpiar_numero(v):
    if isinstance(v, str):
        v = re.sub(r"(?i)(€|eur|euros?|\$|%|\s| )", "", v)
    return importar._numero(v)


def _precio(v):
    """Precio (>= 0) o None si la celda está vacía. ValueError si no se entiende."""
    n = _limpiar_numero(v)
    if n is not None and n < 0:
        raise ValueError
    return n


def _descuento(v):
    """Descuento en % (0–100) o None. «35», «35 %», «35,5» y 0,35 (un 35 % con formato de
    porcentaje en el Excel) valen. ValueError si no se entiende o se sale de 0–100."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    con_signo = isinstance(v, str) and "%" in v
    n = _limpiar_numero(v)
    if n is None:
        return None
    if not con_signo and 0 < n < 1:
        n *= 100
    if n < 0 or n > 100:
        raise ValueError
    return round(n, 4)


def _entero(v):
    n = _limpiar_numero(v)
    return None if n is None else int(round(n))


def neto(precio_lista, descuento):
    if precio_lista is None:
        return None
    return round(precio_lista * (1 - (descuento or 0) / 100), 4)


def _celda(valores, mapeo, campo):
    j = mapeo.get(campo)
    return valores[j] if j is not None and 0 <= j < len(valores) else None


# ------------------------------------------------------------------ análisis

def _buscar_por_referencia(con, proveedor_id):
    return {_ref(f["referencia"]): f["material_id"] for f in con.execute(
        "SELECT material_id, referencia FROM articulo_proveedor WHERE proveedor_id = ? AND referencia != ''",
        (proveedor_id,))}


def analizar(proveedor_id, filas, mapeo, enlaces=None):
    """Qué haría la tarifa, sin cambiar nada. [mapeo]: {campo: índice}; [enlaces]:
    {referencia: material_id} elegidos a mano. Devuelve
    {"enlazados": [...], "sin_enlazar": [...], "avisos": [{"fila", "codigo", "referencia"}],
     "descuento_general"}. Cada línea: fila, referencia, descripcion, precio_lista, descuento,
    precio (neto), multiplo, ean, plazo, validez; las enlazadas, además: material_id, codigo,
    nombre, precio_actual (el del artículo), precio_anterior (el último de este proveedor),
    variacion (% frente al precio del artículo, o None), habitual, como («referencia»,
    «codigo» o «manual») y cambiar (si de serie se cambia el precio del artículo)."""
    enlaces = {_ref(k): int(v) for k, v in (enlaces or {}).items() if v}
    con = almacen._conn()
    try:
        prov = con.execute("SELECT id, descuento FROM proveedores WHERE id = ?", (proveedor_id,)).fetchone()
        if prov is None:
            raise ValueError("no_existe")
        por_ref = _buscar_por_referencia(con, proveedor_id)
        relacion = {f["material_id"]: f for f in con.execute(
            "SELECT material_id, precio FROM articulo_proveedor WHERE proveedor_id = ?", (proveedor_id,))}
        articulos = {f["id"]: f for f in con.execute(
            "SELECT id, codigo, nombre, precio, proveedor_id FROM materiales WHERE articulo_id IS NULL")}
    finally:
        con.close()
    por_codigo, repetidos = {}, set()
    for a in articulos.values():
        c = _ref(a["codigo"])
        if c:
            if c in por_codigo:
                repetidos.add(c)
            por_codigo[c] = a["id"]
    for c in repetidos:           # un código repetido no sirve para enlazar
        del por_codigo[c]

    resultado = {"enlazados": [], "sin_enlazar": [], "avisos": [], "descuento_general": prov["descuento"]}
    vistas, usados = set(), {}
    for numero, valores in filas:
        referencia = importar.texto_celda(_celda(valores, mapeo, "referencia"))
        clave = _ref(referencia)
        if not clave:
            if any(importar.texto_celda(v) for v in valores):
                resultado["avisos"].append({"fila": numero, "codigo": "sin_referencia", "referencia": ""})
            continue
        if clave in vistas:
            resultado["avisos"].append({"fila": numero, "codigo": "referencia_repetida", "referencia": referencia})
            continue
        try:
            precio_lista = _precio(_celda(valores, mapeo, "precio"))
        except (ValueError, TypeError):
            precio_lista = None
        if precio_lista is None:
            resultado["avisos"].append({"fila": numero, "codigo": "precio_no_valido", "referencia": referencia})
            continue
        try:
            descuento = _descuento(_celda(valores, mapeo, "descuento"))
        except (ValueError, TypeError):
            resultado["avisos"].append({"fila": numero, "codigo": "descuento_no_valido", "referencia": referencia})
            continue
        if descuento is None:
            descuento = prov["descuento"]
        vistas.add(clave)
        linea = {"fila": numero, "referencia": referencia,
                 "descripcion": importar.texto_celda(_celda(valores, mapeo, "descripcion"))[:200],
                 "precio_lista": precio_lista, "descuento": descuento, "precio": neto(precio_lista, descuento),
                 "ean": importar.texto_celda(_celda(valores, mapeo, "ean"))[:40]}
        for campo, conv in (("multiplo", _precio), ("plazo", _entero)):
            try:
                linea[campo] = conv(_celda(valores, mapeo, campo))
            except (ValueError, TypeError):
                linea[campo] = None
        try:
            linea["validez"] = importar._fecha(_celda(valores, mapeo, "validez")) or ""
        except (ValueError, TypeError):
            linea["validez"] = ""

        material_id, como = None, None
        if clave in enlaces and enlaces[clave] in articulos:
            material_id, como = enlaces[clave], "manual"
        elif clave in por_ref and por_ref[clave] in articulos:
            material_id, como = por_ref[clave], "referencia"
        elif clave in por_codigo:
            material_id, como = por_codigo[clave], "codigo"
        if material_id is not None and material_id in usados:
            resultado["avisos"].append({"fila": numero, "codigo": "articulo_repetido", "referencia": referencia,
                                        "otra": usados[material_id]})
            continue
        if material_id is None:
            resultado["sin_enlazar"].append(linea)
            continue
        usados[material_id] = referencia
        a = articulos[material_id]
        actual = a["precio"]
        habitual = a["proveedor_id"] == proveedor_id
        linea.update(material_id=material_id, codigo=a["codigo"] or "", nombre=a["nombre"], precio_actual=actual,
                     precio_anterior=(relacion.get(material_id) or {"precio": None})["precio"],
                     variacion=None if not actual else round((linea["precio"] - actual) / actual * 100, 2),
                     habitual=habitual, como=como,
                     cambiar=habitual and (actual is None or abs((actual or 0) - linea["precio"]) > 1e-9))
        resultado["enlazados"].append(linea)
    return resultado


# ------------------------------------------------------------------ aplicar

def aplicar(proveedor_id, filas, mapeo, cambiar_precio=(), enlaces=None, crear=(), fichero="",
            usuario_id=None, usuario_nombre="", fecha=None):
    """Aplica la tarifa en una sola transacción:
      * historial de precios del proveedor (solo si el precio cambia frente al último suyo),
      * relación artículo–proveedor (referencia, precio y datos de la tarifa),
      * precio del artículo en todas sus filas por almacén, solo en [cambiar_precio] (material_id),
      * artículos nuevos para las referencias de [crear] que no estén enlazadas.
    Devuelve {"historial", "relaciones", "precios_cambiados", "creados", "avisos"}."""
    fecha = fecha or date.today().strftime("%Y-%m-%d")
    analisis = analizar(proveedor_id, filas, mapeo, enlaces)
    cambiar_precio = {int(i) for i in cambiar_precio}
    crear = {_ref(r) for r in crear}
    nota = f"Tarifa: {fichero}" if fichero else "Tarifa"
    usuario_nombre = usuario_nombre or (_usuarios.SESION_ACTUAL or {}).get("nombre", "")
    cuenta = {"historial": 0, "relaciones": 0, "precios_cambiados": 0, "creados": 0,
              "avisos": len(analisis["avisos"])}
    cambios = []
    con = almacen._conn()
    try:
        prov = con.execute("SELECT nombre FROM proveedores WHERE id = ?", (proveedor_id,)).fetchone()
        nuevas = []
        for linea in analisis["sin_enlazar"]:
            if _ref(linea["referencia"]) not in crear:
                continue
            nombre = linea["descripcion"] or linea["referencia"]
            material_id = con.execute(
                """INSERT INTO materiales (codigo, nombre, descripcion, unidad, stock_actual, stock_minimo, seccion_id,
                                           foto, almacen_id, proveedor_id, precio)
                   VALUES ('', ?, '', '', 0, 0, NULL, NULL, NULL, ?, ?)""",
                (nombre, proveedor_id, linea["precio"])).lastrowid
            nuevas.append({**linea, "material_id": material_id, "precio_anterior": None, "nuevo": True})
            cambios.append({"campo": f"Nuevo: {nombre}", "antes": "", "despues": f"{linea['precio']:g}"})
            cuenta["creados"] += 1
        for linea in analisis["enlazados"] + nuevas:
            mid = linea["material_id"]
            if linea["precio_anterior"] is None or abs(linea["precio_anterior"] - linea["precio"]) > 1e-9:
                con.execute("""INSERT INTO precios_proveedor (material_id, proveedor_id, proveedor_nombre, fecha, precio,
                                   cantidad, referencia, nota, usuario_nombre) VALUES (?,?,?,?,?,NULL,?,?,?)""",
                            (mid, proveedor_id, prov["nombre"], fecha, linea["precio"], linea["referencia"][:200],
                             nota[:2000], usuario_nombre[:200]))
                cuenta["historial"] += 1
            con.execute("""
                INSERT INTO articulo_proveedor (material_id, proveedor_id, referencia, descripcion, precio_lista,
                                                descuento, precio, fecha, multiplo, ean, plazo, validez)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(material_id, proveedor_id) DO UPDATE SET
                    referencia = excluded.referencia, descripcion = excluded.descripcion,
                    precio_lista = excluded.precio_lista, descuento = excluded.descuento, precio = excluded.precio,
                    fecha = excluded.fecha, multiplo = excluded.multiplo, ean = excluded.ean, plazo = excluded.plazo,
                    validez = excluded.validez""",
                (mid, proveedor_id, linea["referencia"][:200], linea["descripcion"], linea["precio_lista"],
                 linea["descuento"], linea["precio"], fecha, linea["multiplo"], linea["ean"], linea["plazo"],
                 linea["validez"]))
            cuenta["relaciones"] += 1
            if mid in cambiar_precio and not linea.get("nuevo"):
                con.execute("UPDATE materiales SET precio = ? WHERE id = ? OR articulo_id = ?",
                            (linea["precio"], mid, mid))
                cuenta["precios_cambiados"] += 1
                cambios.append({"campo": f"{linea['codigo'] + ' · ' if linea['codigo'] else ''}{linea['nombre']}",
                                "antes": "" if linea["precio_actual"] is None else f"{linea['precio_actual']:g}",
                                "despues": f"{linea['precio']:g}"})
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    detalle = (f"Proveedor: {prov['nombre']}\nPrecios de la tarifa: {cuenta['relaciones']} · "
               f"en el historial: {cuenta['historial']} · precios de artículo cambiados: {cuenta['precios_cambiados']} · "
               f"artículos nuevos: {cuenta['creados']} · filas con avisos: {cuenta['avisos']}")
    _usuarios.auditar("almacen", "importar", f"Tarifa de {prov['nombre']}" + (f" ({fichero})" if fichero else ""),
                      detalle=detalle, cambios=cambios[:MAX_CAMBIOS_REGISTRO])
    return cuenta


def articulos_para_enlazar(texto="", limite=200):
    """Artículos (la fila original de cada uno: id, codigo, nombre) cuyo código o nombre
    contienen [texto], para enlazar a mano una línea de la tarifa."""
    palabras = [w for w in importar.normalizar(texto).split() if w]
    con = almacen._conn()
    try:
        filas = con.execute("SELECT id, codigo, nombre FROM materiales WHERE articulo_id IS NULL "
                            "ORDER BY nombre COLLATE NOCASE").fetchall()
    finally:
        con.close()
    resultado = []
    for f in filas:
        llano = importar.normalizar(f"{f['codigo'] or ''} {f['nombre']}")
        if all(w in llano for w in palabras):
            resultado.append(dict(f))
            if len(resultado) >= limite:
                break
    return resultado
