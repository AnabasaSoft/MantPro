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
compras.py — Pedido sugerido y pedidos guardados.

Paso 4 de «Proveedores y punto de pedido». Solo para administradores (la
interfaz del PC lo comprueba; aquí no hay nada expuesto por la API todavía).

- **Pedido sugerido**: `lineas_sugeridas()` calcula, para cada artículo por
  debajo de su mínimo, cuánto pedir (ver pedidos.cantidad_sugerida) **descontando
  lo que ya está pedido y pendiente de llegar**, y a qué proveedor (el habitual).
- **Pedidos guardados**: `crear_pedidos()` guarda un pedido por proveedor, con su
  fecha. Mientras no llegue entero, lo que falta cuenta como «pendiente de llegar»
  y no se vuelve a sugerir.
- **Recepción**: cada **entrada de stock** del artículo va descontando lo pendiente
  de los pedidos abiertos (`recibir` / `aplicar_entrada`), el más antiguo primero. Un
  pedido pasa a «parcial» y, cuando llega todo, a «recibido». Si la entrada lleva
  precio, queda como **precio real** en la línea (media ponderada por cantidad) y se
  devuelve la diferencia con el precio del pedido, para avisar.
- **Avisos** (`avisos_pedidos`): pedidos sin enviar y pedidos **con retraso** (enviados
  hace más días que el plazo de entrega habitual del proveedor sin haber llegado enteros).
- **Envío**: `texto_pedido()`, `url_correo()`, `url_whatsapp()` y `generar_pdf()`
  preparan el pedido para mandarlo por correo, WhatsApp, impreso o teléfono. El
  texto y el PDF salen en el idioma activo y sin precios (es lo que ve el proveedor).

Vive en almacen.db. Python puro, sin Qt.
"""

import re
from datetime import date, datetime
from urllib.parse import quote

from . import almacen, pedidos, proveedores
from . import usuarios as _usuarios

ESTADO_PEDIDO = "pedido"
ESTADO_PARCIAL = "parcial"
ESTADO_RECIBIDO = "recibido"
ESTADO_CANCELADO = "cancelado"
ESTADOS_ABIERTOS = (ESTADO_PEDIDO, ESTADO_PARCIAL)

CANALES = ("correo", "whatsapp", "telefono", "impreso")


def inicializar():
    """Crea las tablas si no existen. Idempotente."""
    con = almacen._conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id     INTEGER,                 -- NULL si el proveedor se borró después
            proveedor_nombre TEXT NOT NULL DEFAULT '',  -- copia, para no perder el pedido
            fecha            TEXT NOT NULL,           -- fecha del pedido (AAAA-MM-DD)
            estado           TEXT NOT NULL DEFAULT 'pedido',
            canal            TEXT NOT NULL DEFAULT '',  -- cómo se mandó (vacío: sin enviar)
            enviado          TEXT NOT NULL DEFAULT '',  -- cuándo (AAAA-MM-DD HH:MM:SS)
            nota             TEXT NOT NULL DEFAULT '',
            usuario_nombre   TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);
        CREATE TABLE IF NOT EXISTS pedidos_lineas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id   INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
            material_id INTEGER REFERENCES materiales(id) ON DELETE SET NULL,
            codigo      TEXT NOT NULL DEFAULT '',     -- copias del artículo en el momento de pedir
            nombre      TEXT NOT NULL DEFAULT '',
            unidad      TEXT NOT NULL DEFAULT '',
            cantidad    REAL NOT NULL,
            recibido    REAL NOT NULL DEFAULT 0,
            precio      REAL,                         -- precio estimado al pedir (solo para el administrador)
            referencia  TEXT NOT NULL DEFAULT ''      -- referencia del proveedor para este artículo
        );
        CREATE INDEX IF NOT EXISTS idx_pedidos_lineas_pedido ON pedidos_lineas(pedido_id);
        CREATE INDEX IF NOT EXISTS idx_pedidos_lineas_material ON pedidos_lineas(material_id);
    """)
    # Almacén de entrega del pedido (NULL: el principal). Un pedido agrupado lleva
    # líneas de varios almacenes: agrupado = 1 y cada línea va al de su artículo.
    columnas = almacen._columnas(con, "pedidos")
    if "almacen_id" not in columnas:
        con.execute("ALTER TABLE pedidos ADD COLUMN almacen_id INTEGER")
    if "agrupado" not in columnas:
        con.execute("ALTER TABLE pedidos ADD COLUMN agrupado INTEGER NOT NULL DEFAULT 0")
    if "almacen_id" not in almacen._columnas(con, "pedidos_lineas"):
        con.execute("ALTER TABLE pedidos_lineas ADD COLUMN almacen_id INTEGER")
    # Precio real por unidad: media de las entradas con precio que se descontaron de la línea,
    # ponderada por cantidad; recibido_precio es cuánto de lo recibido llegó con precio.
    columnas = almacen._columnas(con, "pedidos_lineas")
    if "precio_real" not in columnas:
        con.execute("ALTER TABLE pedidos_lineas ADD COLUMN precio_real REAL")
    if "recibido_precio" not in columnas:
        con.execute("ALTER TABLE pedidos_lineas ADD COLUMN recibido_precio REAL NOT NULL DEFAULT 0")
    con.commit()
    con.close()


def _num(valor):
    if valor is None or valor == "":
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def _hoy():
    return date.today().strftime("%Y-%m-%d")


# ----------------------------------------------------------- pendiente de llegar

def pendiente_de_llegar(material_id=None):
    """Lo que está pedido y aún no ha llegado. Con [material_id], la cantidad (float);
    sin él, un diccionario {material_id: cantidad} de todos los artículos con algo
    pendiente."""
    con = almacen._conn()
    marcas = ",".join("?" * len(ESTADOS_ABIERTOS))
    base = f"""SELECT l.material_id, SUM(MAX(l.cantidad - l.recibido, 0)) AS falta
               FROM pedidos_lineas l JOIN pedidos p ON p.id = l.pedido_id
               WHERE p.estado IN ({marcas}) AND l.material_id IS NOT NULL"""
    if material_id is not None:
        fila = con.execute(base + " AND l.material_id = ?", (*ESTADOS_ABIERTOS, material_id)).fetchone()
        con.close()
        return float(fila["falta"] or 0)
    filas = con.execute(base + " GROUP BY l.material_id", ESTADOS_ABIERTOS).fetchall()
    con.close()
    return {f["material_id"]: float(f["falta"] or 0) for f in filas if (f["falta"] or 0) > 1e-9}


# --------------------------------------------------------------- pedido sugerido

def _ultimo_precio_y_referencia(material, proveedor_id):
    """(precio, referencia) estimados de un artículo para un proveedor: el último
    precio apuntado de ese proveedor y, si no hay, el precio del artículo."""
    precio, referencia = None, ""
    if proveedor_id is not None:
        for h in proveedores.historial_precios(material["id"]):      # el más reciente primero
            if h["proveedor_id"] != proveedor_id:
                continue
            if not referencia and h["referencia"]:
                referencia = h["referencia"]
            if precio is None and h["precio"] is not None:
                precio = h["precio"]
            if precio is not None and referencia:
                break
    if precio is None:
        precio = material.get("precio")
    return precio, referencia


def lineas_sugeridas(almacen_ids=None):
    """Qué pedir ahora, almacén por almacén (cada artículo de cada almacén con su
    stock y su mínimo). [almacen_ids]: un id, una lista o None (todos). Devuelve (lineas, sin_calculo):

    - lineas: una por artículo por debajo de su mínimo al que haga falta pedir,
      con material_id, codigo, nombre, unidad, stock, minimo, objetivo, pendiente
      (lo ya pedido), cantidad, proveedor_id (el habitual, o None), precio
      (estimado), referencia (del proveedor) y almacen_id (el efectivo).
    - sin_calculo: cuántos artículos por debajo del mínimo no se pueden calcular
      (sin stock mínimo ni objetivo).
    """
    factor = pedidos.factor_objetivo()
    pendiente = pendiente_de_llegar()
    lineas, sin_calculo = [], 0
    from . import almacenes
    for m in almacen.materiales_bajo_minimo(almacen_ids=almacen_ids):
        if pedidos.objetivo_efectivo(m) is None:
            sin_calculo += 1
            continue
        pend = pendiente.get(m["id"], 0.0)
        cantidad = pedidos.cantidad_sugerida(m, pend, factor=factor)
        if cantidad <= 0:
            continue
        prov = m.get("proveedor_id")
        if prov is not None and proveedores.obtener_proveedor(prov) is None:
            prov = None
        precio, referencia = _ultimo_precio_y_referencia(m, prov)
        lineas.append({"material_id": m["id"], "codigo": m.get("codigo") or "", "nombre": m["nombre"],
                       "unidad": m.get("unidad") or "", "stock": m["stock_actual"], "minimo": m["stock_minimo"],
                       "objetivo": pedidos.objetivo_efectivo(m), "pendiente": pend, "cantidad": cantidad,
                       "proveedor_id": prov, "precio": precio, "referencia": referencia,
                       "almacen_id": almacenes.efectivo(m.get("almacen_id"))})
    return lineas, sin_calculo


# ------------------------------------------------------------ pedidos guardados

def crear_pedidos(lineas, usuario_nombre="", fecha=None, nota="", agrupar=False):
    """Guarda un pedido por proveedor y almacén (el del artículo de cada línea) o,
    con [agrupar], uno por proveedor con las líneas de todos sus almacenes (cada
    una se entrega en el suyo). Las [lineas] son ({material_id, cantidad,
    proveedor_id, y opcionalmente precio y referencia}). Devuelve (ids, errores):
    la lista de ids de los pedidos creados y, por cada línea que no se ha podido
    guardar, un código («sin_proveedor», «proveedor_no_existe»,
    «material_no_existe», «cantidad_no_valida»). Si una línea falla, el resto se guarda."""
    from . import almacenes
    fecha = fecha if _fecha_valida(fecha) else _hoy()
    grupos, errores = {}, []
    for l in lineas:
        cantidad = _num(l.get("cantidad"))
        material = almacen.obtener_material(l.get("material_id"))
        if material is None:
            errores.append((l.get("material_id"), "material_no_existe")); continue
        if cantidad is None or cantidad <= 0:
            errores.append((l["material_id"], "cantidad_no_valida")); continue
        prov_id = l.get("proveedor_id")
        if prov_id in (None, "", 0):
            errores.append((l["material_id"], "sin_proveedor")); continue
        proveedor = proveedores.obtener_proveedor(int(prov_id))
        if proveedor is None:
            errores.append((l["material_id"], "proveedor_no_existe")); continue
        precio, referencia = _ultimo_precio_y_referencia(material, proveedor["id"])
        if _num(l.get("precio")) is not None:
            precio = _num(l.get("precio"))
        if (l.get("referencia") or "").strip():
            referencia = l["referencia"].strip()
        alm = almacenes.guardable(almacenes.efectivo(material.get("almacen_id")))
        clave = proveedor["id"] if agrupar else (proveedor["id"], alm)
        grupos.setdefault(clave, (proveedor, []))[1].append((material, cantidad, precio, referencia, alm))
    ids = []
    for proveedor, items in grupos.values():
        destinos = {i[4] for i in items}
        alm_pedido = next(iter(destinos)) if len(destinos) == 1 else None
        con = almacen._conn()
        pedido_id = con.execute(
            """INSERT INTO pedidos (proveedor_id, proveedor_nombre, fecha, usuario_nombre, nota, almacen_id, agrupado)
               VALUES (?,?,?,?,?,?,?)""",
            (proveedor["id"], proveedor["nombre"], fecha, (usuario_nombre or "")[:200], (nota or "")[:2000],
             alm_pedido, 1 if len(destinos) > 1 else 0)).lastrowid
        for material, cantidad, precio, referencia, _alm in items:
            con.execute("""INSERT INTO pedidos_lineas (pedido_id, material_id, codigo, nombre, unidad, cantidad, precio,
                                                        referencia, almacen_id)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (pedido_id, material["id"], material.get("codigo") or "", material["nombre"],
                         material.get("unidad") or "", cantidad, precio, referencia, _alm))
        con.commit()
        con.close()
        ids.append(pedido_id)
        _usuarios.auditar("almacen", "crear", f"Pedido {pedido_id} a {proveedor['nombre']}",
                          detalle="\n".join(f"{c:g} {m.get('unidad') or ''} {m['nombre']}".replace("  ", " ")
                                            for m, c, _p, _r, _a in items))
    return ids, errores


def _fecha_valida(texto):
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def _lineas(con, pedido_id):
    return [dict(f) for f in con.execute("SELECT * FROM pedidos_lineas WHERE pedido_id = ? ORDER BY id", (pedido_id,))]


def _resumen(con, p):
    from . import almacenes
    d = dict(p)
    d["lineas"] = _lineas(con, d["id"])
    nombres = almacenes.nombres()
    for l in d["lineas"]:
        # Las líneas antiguas no tienen almacén: el del pedido
        l["almacen_id"] = almacenes.efectivo(l.get("almacen_id") if l.get("almacen_id") is not None
                                             else d.get("almacen_id"))
        l["almacen_nombre"] = nombres.get(l["almacen_id"], "")
    d["almacen_ids"] = sorted({l["almacen_id"] for l in d["lineas"] if l["almacen_id"] is not None}) or \
        [almacenes.efectivo(d.get("almacen_id"))]
    d["almacen_nombre"] = ", ".join(nombres.get(a, "") for a in d["almacen_ids"])
    total, sin_precio = 0.0, False
    real, diferencia = 0.0, 0.0
    for l in d["lineas"]:
        if l["precio"] is None:
            sin_precio = True
        else:
            total += l["cantidad"] * l["precio"]
        if l.get("precio_real") is not None:
            con_precio = l.get("recibido_precio") or 0
            real += con_precio * l["precio_real"]
            if l["precio"] is not None:
                diferencia += con_precio * (l["precio_real"] - l["precio"])
    d["importe_estimado"], d["sin_precio"] = total, sin_precio
    # Lo recibido con precio real y cuánto se desvía de lo estimado (la diferencia, solo en líneas con los dos)
    d["importe_real"] = round(real, 6)
    d["diferencia_precio"] = round(diferencia, 6)
    d["con_precio_real"] = any(l.get("precio_real") is not None for l in d["lineas"])
    d["pendiente"] = sum(max(l["cantidad"] - l["recibido"], 0) for l in d["lineas"]) if d["estado"] in ESTADOS_ABIERTOS else 0.0
    fila = con.execute("SELECT plazo_entrega FROM proveedores WHERE id = ?", (d["proveedor_id"],)).fetchone() \
        if d.get("proveedor_id") is not None else None
    d["plazo_entrega"] = fila["plazo_entrega"] if fila else None
    d["dias_retraso"] = dias_retraso(d)
    return d


def dias_retraso(pedido, hoy=None):
    """Días que lleva de retraso un pedido abierto y enviado: los que han pasado desde
    que se envió más allá del plazo de entrega de su proveedor. 0 si va en plazo, no se
    ha enviado, ya llegó o el proveedor no tiene plazo."""
    if pedido.get("estado") not in ESTADOS_ABIERTOS or not pedido.get("canal") or not pedido.get("plazo_entrega"):
        return 0
    try:
        enviado = datetime.strptime((pedido.get("enviado") or "")[:10], "%Y-%m-%d").date()
    except ValueError:
        return 0
    hoy = hoy or date.today()
    return max((hoy - enviado).days - int(pedido["plazo_entrega"]), 0)


def obtener_pedido(pedido_id):
    """El pedido con sus líneas, importe estimado y lo que falta por llegar; o None."""
    con = almacen._conn()
    p = con.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    resultado = _resumen(con, p) if p else None
    con.close()
    return resultado


def listar_pedidos(solo_abiertos=False, almacen_ids=None):
    """Pedidos del más reciente al más antiguo (con sus líneas). [solo_abiertos]:
    solo los que aún no han llegado enteros ni están cancelados. [almacen_ids]: solo
    los que entregan algo en esos almacenes (un id, una lista o None = todos)."""
    con = almacen._conn()
    sql = "SELECT * FROM pedidos"
    parametros = ()
    if solo_abiertos:
        sql += f" WHERE estado IN ({','.join('?' * len(ESTADOS_ABIERTOS))})"
        parametros = ESTADOS_ABIERTOS
    filas = con.execute(sql + " ORDER BY fecha DESC, id DESC", parametros).fetchall()
    lista = [_resumen(con, f) for f in filas]
    con.close()
    if almacen_ids is not None:
        ids = {almacen_ids} if isinstance(almacen_ids, int) else set(almacen_ids)
        lista = [p for p in lista if ids & set(p["almacen_ids"])]
    return lista


def _recalcular_estado(con, pedido_id):
    p = con.execute("SELECT estado FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    if p is None or p["estado"] == ESTADO_CANCELADO:
        return
    lineas = _lineas(con, pedido_id)
    if lineas and all(l["recibido"] >= l["cantidad"] - 1e-9 for l in lineas):
        estado = ESTADO_RECIBIDO
    elif any(l["recibido"] > 1e-9 for l in lineas):
        estado = ESTADO_PARCIAL
    else:
        estado = ESTADO_PEDIDO
    con.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (estado, pedido_id))


TOLERANCIA_PRECIO = 0.005      # diferencias de precio por debajo de medio céntimo no se avisan


def recibir(material_id, cantidad, proveedor_id=None, precio=None):
    """Una entrada de stock de [cantidad] del artículo llega y se descuenta de lo
    pendiente de los pedidos abiertos: primero los del [proveedor_id] (si se
    indica) y, dentro de cada grupo, el pedido más antiguo. Lo que sobre se
    ignora. Con [precio] (por unidad), entra en el precio real de las líneas que
    reciben algo (media ponderada por cantidad), y las que se pidieron a otro
    precio se devuelven para avisar.
    Devuelve {"aplicado": cantidad dada por recibida, "diferencias": [{pedido_id,
    fecha, proveedor_nombre, precio_pedido, precio_real, porcentaje}]}."""
    restante = _num(cantidad) or 0.0
    precio = _num(precio)
    if precio is not None and precio < 0:
        precio = None
    resultado = {"aplicado": 0.0, "diferencias": []}
    if restante <= 0:
        return resultado
    con = almacen._conn()
    marcas = ",".join("?" * len(ESTADOS_ABIERTOS))
    filas = con.execute(f"""
        SELECT l.id, l.cantidad, l.recibido, l.pedido_id, l.precio, l.precio_real, l.recibido_precio,
               p.fecha, p.proveedor_nombre
        FROM pedidos_lineas l JOIN pedidos p ON p.id = l.pedido_id
        WHERE l.material_id = ? AND p.estado IN ({marcas}) AND l.recibido < l.cantidad - 1e-9
        ORDER BY (CASE WHEN p.proveedor_id = ? THEN 0 ELSE 1 END), p.fecha, p.id""",
        (material_id, *ESTADOS_ABIERTOS, proveedor_id)).fetchall()
    aplicado, tocados = 0.0, set()
    for f in filas:
        if restante <= 1e-9:
            break
        toma = min(restante, f["cantidad"] - f["recibido"])
        if precio is None:
            con.execute("UPDATE pedidos_lineas SET recibido = ? WHERE id = ?", (round(f["recibido"] + toma, 6), f["id"]))
        else:
            previo = f["recibido_precio"] or 0
            media = precio if f["precio_real"] is None or previo <= 0 else \
                (f["precio_real"] * previo + precio * toma) / (previo + toma)
            con.execute("UPDATE pedidos_lineas SET recibido = ?, precio_real = ?, recibido_precio = ? WHERE id = ?",
                        (round(f["recibido"] + toma, 6), round(media, 6), round(previo + toma, 6), f["id"]))
            if f["precio"] is not None and abs(precio - f["precio"]) >= TOLERANCIA_PRECIO:
                resultado["diferencias"].append({
                    "pedido_id": f["pedido_id"], "fecha": f["fecha"], "proveedor_nombre": f["proveedor_nombre"],
                    "precio_pedido": f["precio"], "precio_real": precio,
                    "porcentaje": round((precio - f["precio"]) / f["precio"] * 100, 1) if f["precio"] else None})
        restante -= toma
        aplicado += toma
        tocados.add(f["pedido_id"])
    for pedido_id in tocados:
        _recalcular_estado(con, pedido_id)
    con.commit()
    con.close()
    resultado["aplicado"] = round(aplicado, 6)
    return resultado


def aplicar_entrada(material_id, cantidad, proveedor_id=None, precio=None):
    """Como recibir(), pero devuelve solo la cantidad dada por recibida."""
    return recibir(material_id, cantidad, proveedor_id, precio)["aplicado"]


def _cambiar(pedido_id, detalle, sql, parametros=()):
    p = obtener_pedido(pedido_id)
    if p is None:
        return False, "no_existe"
    con = almacen._conn()
    con.execute(sql, (*parametros, pedido_id))
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "editar", f"Pedido {pedido_id} a {p['proveedor_nombre']}", detalle=detalle)
    return True, None


def marcar_enviado(pedido_id, canal):
    """Apunta cómo se mandó el pedido (correo, whatsapp, telefono o impreso) y cuándo."""
    if canal not in CANALES:
        return False, "canal_no_valido"
    return _cambiar(pedido_id, f"Enviado por {canal}",
                    "UPDATE pedidos SET canal = ?, enviado = ? WHERE id = ?",
                    (canal, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def marcar_recibido(pedido_id):
    """Da por recibido todo lo pendiente del pedido. NO cambia el stock: las
    entradas se registran aparte (así no se cuentan dos veces)."""
    p = obtener_pedido(pedido_id)
    if p is None:
        return False, "no_existe"
    if p["estado"] == ESTADO_CANCELADO:
        return False, "cancelado"
    con = almacen._conn()
    con.execute("UPDATE pedidos_lineas SET recibido = cantidad WHERE pedido_id = ?", (pedido_id,))
    _recalcular_estado(con, pedido_id)
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "editar", f"Pedido {pedido_id} a {p['proveedor_nombre']}", detalle="Marcado como recibido")
    return True, None


def cancelar_pedido(pedido_id):
    """Cancela un pedido: lo que faltaba por llegar deja de contar como pendiente."""
    return _cambiar(pedido_id, "Cancelado", "UPDATE pedidos SET estado = 'cancelado' WHERE id = ?")


def borrar_pedido(pedido_id):
    p = obtener_pedido(pedido_id)
    if p is None:
        return False, "no_existe"
    con = almacen._conn()
    con.execute("DELETE FROM pedidos_lineas WHERE pedido_id = ?", (pedido_id,))
    con.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
    con.commit()
    con.close()
    _usuarios.auditar("almacen", "borrar", f"Pedido {pedido_id} a {p['proveedor_nombre']}",
                      detalle=f"Estado: {p['estado']}")
    return True, None


def pedidos_sin_enviar(almacen_ids=None):
    """Pedidos abiertos que nadie ha mandado todavía (para avisar)."""
    return [p for p in listar_pedidos(solo_abiertos=True, almacen_ids=almacen_ids) if not p["canal"]]


def pedidos_retrasados(almacen_ids=None, hoy=None):
    """Pedidos enviados que llevan más días que el plazo de entrega de su proveedor sin llegar enteros."""
    lista = []
    for p in listar_pedidos(solo_abiertos=True, almacen_ids=almacen_ids):
        p["dias_retraso"] = dias_retraso(p, hoy)
        if p["dias_retraso"] > 0:
            lista.append(p)
    return lista


def avisos_pedidos(almacen_ids=None, hoy=None):
    """Lo que hay que mirar de los pedidos: {"sin_enviar": [...], "retrasados": [...]}."""
    return {"sin_enviar": pedidos_sin_enviar(almacen_ids), "retrasados": pedidos_retrasados(almacen_ids, hoy)}


# --------------------------------------------------------------- envío del pedido

def _t(clave, **datos):
    from .. import idiomas
    texto = idiomas.t(clave)
    return texto.format(**datos) if datos else texto


def _cantidad_texto(valor):
    return f"{valor:g}"


def asunto_pedido(pedido):
    from .. import idiomas
    return _t("cmp_asunto", n=pedido["id"], fecha=idiomas.formato_fecha_localizada(pedido["fecha"]))


def lugar_entrega(entrega):
    """Texto de un lugar de entrega: «Almacén (Sede) — dirección, contacto, teléfono»."""
    nombre = entrega["almacen"] + (f" ({entrega['sede']})" if entrega["sede"] and entrega["sede"] != entrega["almacen"] else "")
    resto = ", ".join(x for x in (entrega["direccion"], entrega["contacto"], entrega["telefono"]) if x)
    return f"{nombre} — {resto}" if resto else nombre


def entregas(pedido):
    """Las líneas del pedido por lugar de entrega: lista de (entrega, lineas), con
    entrega como la da almacenes.entrega(). Vacía si no hace falta decir dónde
    (un solo almacén y sin dirección de entrega)."""
    from . import almacenes
    grupos = {}
    for l in pedido["lineas"]:
        grupos.setdefault(l["almacen_id"], []).append(l)
    lista = [(almacenes.entrega(a), ls) for a, ls in grupos.items()]
    if len(lista) == 1 and not lista[0][0]["direccion"] and not almacenes.hay_varios():
        return []
    return lista


def texto_pedido(pedido, firma=""):
    """Texto del pedido listo para pegar en un correo o mensaje, en el idioma activo.
    Sin precios: es lo que ve el proveedor. Con varios almacenes, las líneas van
    agrupadas por lugar de entrega."""
    def linea_texto(l):
        resto = f"{_cantidad_texto(l['cantidad'])} {l['unidad']}".strip()
        linea = f"• {resto} — {l['nombre']}"
        if l["referencia"]:
            linea += f" ({_t('cmp_txt_ref', ref=l['referencia'])})"
        return linea

    lugares = entregas(pedido)
    if len(lugares) > 1:
        lineas = []
        for entrega, ls in lugares:
            lineas += [_t("cmp_txt_entrega", lugar=lugar_entrega(entrega)), *[linea_texto(l) for l in ls], ""]
        lineas = lineas[:-1]
    else:
        lineas = [linea_texto(l) for l in pedido["lineas"]]
        if lugares:
            lineas += ["", _t("cmp_txt_entrega", lugar=lugar_entrega(lugares[0][0]))]
    cuerpo = [_t("cmp_txt_saludo"), "", _t("cmp_txt_intro"), "", *lineas, "", _t("cmp_txt_cierre")]
    if firma:
        cuerpo.append(firma)
    return "\n".join(cuerpo)


def url_correo(pedido, firma=""):
    """Enlace mailto: con destinatario, asunto y texto ya puestos (el PDF, si se
    quiere, lo adjunta quien lo manda: mailto no permite adjuntar)."""
    prov = proveedores.obtener_proveedor(pedido["proveedor_id"]) if pedido["proveedor_id"] is not None else None
    destino = quote((prov or {}).get("correo", "").strip(), safe="@,")
    return f"mailto:{destino}?subject={quote(asunto_pedido(pedido), safe='')}&body={quote(texto_pedido(pedido, firma), safe='')}"


def telefono_internacional(telefono):
    """(dígitos, con_prefijo): el teléfono solo con cifras para wa.me y si lleva
    prefijo internacional (+34… o 0034…). Sin prefijo, WhatsApp puede no reconocerlo."""
    texto = (telefono or "").strip()
    digitos = re.sub(r"\D", "", texto)
    if texto.startswith("00"):
        return digitos[2:], True
    return digitos, texto.startswith("+")


def url_whatsapp(pedido, firma=""):
    """Enlace wa.me con el texto del pedido (y el teléfono del proveedor si lo hay).
    Devuelve (url, con_prefijo); con_prefijo es True también si no hay teléfono."""
    prov = proveedores.obtener_proveedor(pedido["proveedor_id"]) if pedido["proveedor_id"] is not None else None
    digitos, con_prefijo = telefono_internacional((prov or {}).get("telefono", ""))
    texto = quote(texto_pedido(pedido, firma), safe="")
    if not digitos:
        return f"https://wa.me/?text={texto}", True
    return f"https://wa.me/{digitos}?text={texto}", con_prefijo


def generar_pdf(pedido_id, ruta, firma=""):
    """Escribe el pedido en un PDF (A4) en [ruta], en el idioma activo y sin precios.
    Devuelve (True, None) o (False, código)."""
    from .. import idiomas
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    pedido = obtener_pedido(pedido_id)
    if pedido is None:
        return False, "no_existe"
    prov = proveedores.obtener_proveedor(pedido["proveedor_id"]) if pedido["proveedor_id"] is not None else None
    estilos = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=estilos["Normal"], fontSize=10, leading=13)
    celda = ParagraphStyle("c", parent=normal, fontSize=9.5, leading=12)
    historia = [Paragraph(f"<b>{escape(_t('cmp_pdf_titulo', n=pedido['id']))}</b>", estilos["Title"]), Spacer(1, 0.3 * cm)]
    datos = [f"<b>{escape(_t('cmp_pdf_proveedor'))}:</b> {escape(pedido['proveedor_nombre'])}",
             f"<b>{escape(_t('cmp_pdf_fecha'))}:</b> {escape(idiomas.formato_fecha_localizada(pedido['fecha']))}"]
    if prov and prov.get("contacto"):
        datos.append(f"<b>{escape(_t('prov_lbl_contacto'))}:</b> {escape(prov['contacto'])}")
    lugares = entregas(pedido)
    if len(lugares) == 1:
        datos.append(f"<b>{escape(_t('cmp_pdf_entrega'))}:</b> {escape(lugar_entrega(lugares[0][0]))}")
    for d in datos:
        historia.append(Paragraph(d, normal))

    def tabla_de(lineas):
        filas = [[Paragraph(f"<b>{escape(_t('cmp_hdr_ref'))}</b>", celda), Paragraph(f"<b>{escape(_t('cmp_hdr_articulo'))}</b>", celda),
                  Paragraph(f"<b>{escape(_t('prov_hdr_cantidad'))}</b>", celda)]]
        for l in lineas:
            filas.append([Paragraph(escape(l["referencia"] or l["codigo"]), celda), Paragraph(escape(l["nombre"]), celda),
                          Paragraph(escape(f"{_cantidad_texto(l['cantidad'])} {l['unidad']}".strip()), celda)])
        tabla = Table(filas, colWidths=[3.5 * cm, 10 * cm, 3.5 * cm], repeatRows=1)
        tabla.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                                   ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return tabla

    if len(lugares) > 1:
        # Pedido agrupado: una tabla por lugar de entrega
        for entrega, ls in lugares:
            historia += [Spacer(1, 0.5 * cm),
                         Paragraph(f"<b>{escape(_t('cmp_pdf_entrega'))}:</b> {escape(lugar_entrega(entrega))}", normal),
                         Spacer(1, 0.15 * cm), tabla_de(ls)]
    else:
        historia += [Spacer(1, 0.5 * cm), tabla_de(pedido["lineas"])]
    if pedido["nota"]:
        historia += [Spacer(1, 0.4 * cm), Paragraph(escape(pedido["nota"]), normal)]
    historia += [Spacer(1, 0.8 * cm), Paragraph(escape(_t("cmp_txt_cierre")), normal)]
    if firma:
        historia.append(Paragraph(escape(firma), normal))
    SimpleDocTemplate(ruta, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                      title=_t("cmp_pdf_titulo", n=pedido["id"])).build(historia)
    return True, None
