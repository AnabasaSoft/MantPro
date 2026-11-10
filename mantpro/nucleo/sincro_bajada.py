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

"""Bajar de MantPro Cloud lo que han escrito otros (móviles, otros PCs) y aplicarlo a las bases de este PC.

Paso 4, fase B. `sincro_nube.py` pide las páginas a la nube y las pasa a `aplicar()`; aquí está
toda la lógica de aplicarlas, sin red ni Qt, para poder probarla a fondo.

Reglas (decididas con el usuario):
  * Lo que subió este mismo PC se salta (viene de vuelta en la lista).
  * Conflicto: si este PC tiene un cambio SIN SUBIR del mismo registro, gana el suyo (se subirá
    después y será el último en llegar). Si no, gana la nube. Un borrado de la nube se aplica,
    salvo con un cambio local pendiente.
  * Stock: no se baja la cantidad final. Cada movimiento NUEVO suma o resta en `stock_actual`,
    como hace MantPro al registrarlo. Un stock negativo se permite y se devuelve para avisar
    de un recuento urgente.
  * Padres antes que hijos. Una referencia a algo que no existe en este PC se deja vacía
    (se cuenta en el resultado): nunca se inventa un id.
  * Los enlaces (usuario_roles…) se combinan por su clave natural, y una fila que choca con una
    columna ÚNICA local (login, nombre de zona…) se considera el mismo registro y adopta el uuid
    de la nube (p. ej. el administrador que MantPro crea por defecto).
  * Lo que llega de fuera NO es de fiar: solo se aplican tablas y columnas que existen aquí
    (una columna que esta versión no conoce se ignora), los nombres se validan contra el esquema
    local y los valores van siempre como parámetros, nunca dentro del texto del SQL.
  * Cada registro va en su propio punto de guardado: uno que falla no estropea el resto, y toda la
    página entra o no entra (si algo grave falla, se deshace entera).
  * Un usuario que baja DESACTIVADO, BORRADO o con otra CONTRASEÑA pierde sus sesiones locales (las del
    móvil incluidas), igual que hace MantPro en local: un técnico dado de baja en un PC no puede seguir
    entrando por otro. Si el usuario no ha cambiado en nada de eso, sus sesiones no se tocan.
  * Nada de lo que se aplica se anota en `cambios` (`silenciar`): no se reenvía a la nube."""

import re

from . import conexion_bd, sincronizacion as sync

_sqlite3 = conexion_bd.sqlite3
_ID = re.compile(r"^[A-Za-z0-9_.:@ -]{1,200}$")
MAX_NEGATIVOS = 20                  # artículos que se devuelven en el aviso de recuento urgente


def resultado_vacio():
    return {"aplicados": 0, "borrados": 0, "conflictos": 0, "ignorados": 0, "rechazados": 0,
            "refs_vacias": 0, "stock_negativo": [], "sesiones_cerradas": 0}


# ---------------------------------------------------------------- esquema local

_cache = {}


def _esquema(con, tabla):
    """Columnas, clave primaria entera y columnas únicas de [tabla] en la base local."""
    clave = (id(con), tabla)
    if clave not in _cache:
        t = sync._nombre(tabla)
        cols = {f[1]: {"tipo": f[2], "notnull": bool(f[3]), "defecto": f[4], "pk": bool(f[5])}
                for f in con.execute(f"PRAGMA table_info({t})")}
        pks = [c for c, d in cols.items() if d["pk"]]
        unicos = []
        for idx in con.execute(f"PRAGMA index_list({t})").fetchall():
            if idx[2] and idx[3] != "pk":
                columnas = [x[2] for x in con.execute(f"PRAGMA index_info({idx[1]})")]
                if columnas and columnas != ["uuid"]:
                    unicos.append(columnas)
        _cache[clave] = {"cols": cols, "pk": pks[0] if len(pks) == 1 else None, "unicos": unicos}
    return _cache[clave]


def olvidar_esquemas():
    _cache.clear()


def _id_local(cons, destino, uuid):
    """id local del registro [uuid] de «base.tabla» [destino], o None si este PC no lo tiene."""
    base, tabla = destino.split(".", 1)
    con = cons[base]
    pk = _esquema(con, tabla)["pk"] or "id"
    f = con.execute(f"SELECT {pk} FROM {sync._nombre(tabla)} WHERE uuid = ?", (uuid,)).fetchone()
    return f[0] if f else None


# ---------------------------------------------------------------- aplicar un registro

def _aplicar_clave(con, tabla, espec, uuid, op, datos, res):
    """Tablas cuya identidad es su clave (config, dias_especiales)."""
    t = sync._nombre(tabla)
    identidad = espec["identidad"].format(r=t)
    if tabla == "config" and uuid not in sync.CONFIG_COMPARTIDA:
        res["ignorados"] += 1               # solo se comparten los ajustes de la empresa, nunca los de cada PC
        return
    if op == "d":
        res["borrados"] += con.execute(f"DELETE FROM {t} WHERE {identidad} = ?", (uuid,)).rowcount
        return
    esq = _esquema(con, tabla)
    valores = {c: v for c, v in (datos or {}).items() if c in esq["cols"]}
    if any(isinstance(v, (dict, list)) for v in valores.values()):
        res["rechazados"] += 1
        return
    cols = list(valores)
    con.execute(f"INSERT OR REPLACE INTO {t} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                [valores[c] for c in cols])
    res["aplicados"] += 1


def _cerrar_sesiones(con, usuario_id, res):
    """Cierra las sesiones locales (PC y móviles) de un usuario. `sesiones` es local: no se sincroniza."""
    res["sesiones_cerradas"] += con.execute("DELETE FROM sesiones WHERE usuario_id = ?", (usuario_id,)).rowcount


def _aplicar_entidad(cons, base, tabla, espec, uuid, op, datos, res, diferidas):
    con = cons[base]
    t = sync._nombre(tabla)
    if op == "d":
        if base == "mant" and tabla == "usuarios":
            f = con.execute("SELECT id FROM usuarios WHERE uuid = ?", (uuid,)).fetchone()
            if f is not None:
                _cerrar_sesiones(con, f[0], res)
        res["borrados"] += con.execute(f"DELETE FROM {t} WHERE uuid = ?", (uuid,)).rowcount
        return
    esq = _esquema(con, tabla)
    excluidas = {"uuid"} | set(espec.get("derivadas", ())) | set(espec.get("ignorar", ()))
    if esq["pk"]:
        excluidas.add(esq["pk"])
    valores = {}
    for c, v in (datos or {}).items():
        if c not in esq["cols"] or c in excluidas:
            continue                         # columna desconocida (versión distinta) o que nunca se baja
        if isinstance(v, (dict, list)):
            res["rechazados"] += 1
            return
        valores[c] = v
    # referencias: uuid -> id local; si falta el destino se deja vacía y se vuelve a intentar al final
    for c, destino in espec.get("refs", {}).items():
        if c in valores and valores[c] is not None:
            local = _id_local(cons, destino, valores[c])
            if local is None:
                diferidas.append((base, tabla, uuid, c, destino, valores[c]))
            valores[c] = local
    fila = con.execute(f"SELECT rowid, uuid FROM {t} WHERE uuid = ?", (uuid,)).fetchone()
    if fila is None:                         # ¿es el mismo registro con otro uuid? (clave natural o columna única)
        candidatos = []
        if espec["tipo"] == "enlace":
            candidatos.append(list(espec["clave_natural"]))
        candidatos += esq["unicos"]
        for columnas in candidatos:
            if all(c in valores and valores[c] is not None for c in columnas):
                donde = " AND ".join(f"{c} = ?" for c in columnas)
                fila = con.execute(f"SELECT rowid, uuid FROM {t} WHERE {donde}", [valores[c] for c in columnas]).fetchone()
                if fila is not None:
                    con.execute(f"UPDATE {t} SET uuid = ? WHERE rowid = ?", (uuid, fila[0]))
                    break
    if fila is not None:
        if espec["tipo"] == "inmutable":
            res["ignorados"] += 1            # historiales: solo se crean
            return
        antes = None
        if base == "mant" and tabla == "usuarios":
            antes = con.execute("SELECT id, activo, password_hash FROM usuarios WHERE rowid = ?", (fila[0],)).fetchone()
        if valores:
            asignar = ", ".join(f"{c} = ?" for c in valores)
            con.execute(f"UPDATE {t} SET {asignar} WHERE rowid = ?", list(valores.values()) + [fila[0]])
        if antes is not None:
            activo = valores.get("activo", antes[1])
            if not activo or valores.get("password_hash", antes[2]) != antes[2]:
                _cerrar_sesiones(con, antes[0], res)
        res["aplicados"] += 1
        return
    cols = list(valores) + ["uuid"]
    con.execute(f"INSERT INTO {t} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                list(valores.values()) + [uuid])
    res["aplicados"] += 1
    if base == "alma" and tabla == "movimientos":
        _ajustar_stock(con, valores, res)


def _ajustar_stock(con, mov, res):
    """Un movimiento nuevo de la nube suma o resta en el stock del artículo (como hace MantPro).
    NO avisa de un stock negativo aquí: los movimientos no llegan en orden y una salida puede aplicarse
    antes que la entrada que la cubre. Se anota el artículo y se mira su stock FINAL al acabar."""
    material, cantidad, tipo = mov.get("material_id"), mov.get("cantidad"), mov.get("tipo")
    if material is None or not isinstance(cantidad, (int, float)) or tipo not in ("entrada", "salida"):
        return
    delta = cantidad if tipo == "entrada" else -cantidad
    con.execute("UPDATE materiales SET stock_actual = stock_actual + ? WHERE id = ?", (delta, material))
    f = con.execute("SELECT uuid FROM materiales WHERE id = ?", (material,)).fetchone()
    if f is not None:
        res.setdefault("_tocados", set()).add(f[0])


def stock_negativo(con_almacen, uuids):
    """Artículos de [uuids] cuyo stock está ahora en negativo (como mucho MAX_NEGATIVOS), para avisar
    de un recuento urgente. Se llama con el stock FINAL, nunca a mitad de aplicar."""
    uuids = list(uuids)
    salida = []
    for i in range(0, len(uuids), 500):
        lote = uuids[i:i + 500]
        for f in con_almacen.execute(
                f"SELECT uuid, codigo, nombre, stock_actual FROM materiales WHERE stock_actual < 0 "
                f"AND uuid IN ({', '.join('?' * len(lote))}) ORDER BY nombre", lote):
            salida.append({"uuid": f[0], "codigo": f[1], "nombre": f[2], "stock": f[3]})
    return salida[:MAX_NEGATIVOS]


# ---------------------------------------------------------------- aplicar una página

def _pendientes_locales(con):
    return {(t, u) for t, u in con.execute("SELECT tabla, uuid FROM cambios WHERE subido = 0")}


def aplicar(cons, cambios, origen_propio, res=None):
    """Aplica una página de [cambios] de la nube a las dos bases. [origen_propio] es el prefijo
    de los orígenes de este PC (se saltan). Devuelve el resultado (diccionario de recuentos).
    Si algo grave falla se deshace la página entera y se relanza la excepción."""
    res = res if res is not None else resultado_vacio()
    orden = [(f"{b}.{t}", b, t, e) for b in ("mant", "alma") for t, e in sync.TABLAS[b].items()]
    por_tabla = {nombre: [] for nombre, *_ in orden}
    for c in cambios or []:
        if not isinstance(c, dict):
            res["rechazados"] += 1
            continue
        nombre, uuid, op, origen = c.get("tabla"), c.get("uuid"), c.get("op"), c.get("origen") or ""
        if nombre not in por_tabla or op not in ("u", "d") or not isinstance(uuid, str) or not _ID.match(uuid):
            res["ignorados"] += 1            # tabla que esta versión no conoce, o un registro mal formado
            continue
        if origen.startswith(origen_propio):
            continue                         # lo subió este PC: vuelve en la lista
        por_tabla[nombre].append(c)

    pendientes = {b: _pendientes_locales(cons[b]) for b in cons}
    diferidas = []
    aislamiento = {b: cons[b].isolation_level for b in cons}
    try:
        for con in cons.values():
            con.isolation_level = None       # transacciones explícitas
            con.execute("BEGIN IMMEDIATE")
            # «silenciado» se activa y se desactiva DENTRO de la transacción: si se deshace, vuelve solo
            con.execute("UPDATE sync_estado SET silenciado = 1 WHERE id = 1")
        n = 0
        for nombre, base, tabla, espec in orden:
            con = cons[base]
            for c in por_tabla[nombre]:
                if (tabla, c["uuid"]) in pendientes[base]:
                    res["conflictos"] += 1       # tiene un cambio local sin subir: gana el local
                    continue
                n += 1
                con.execute(f"SAVEPOINT r{n}")
                try:
                    if espec["tipo"] == "clave":
                        _aplicar_clave(con, tabla, espec, c["uuid"], c["op"], c.get("datos"), res)
                    else:
                        _aplicar_entidad(cons, base, tabla, espec, c["uuid"], c["op"], c.get("datos"), res, diferidas)
                    con.execute(f"RELEASE r{n}")
                except _sqlite3.Error:
                    con.execute(f"ROLLBACK TO r{n}")
                    con.execute(f"RELEASE r{n}")
                    res["rechazados"] += 1
        _resolver_diferidas(cons, diferidas, res)
        # El stock negativo se mira con TODO aplicado (y acumulando las páginas ya aplicadas de esta bajada)
        res["stock_negativo"] = stock_negativo(cons["alma"], res.get("_tocados", ()))
        for con in cons.values():
            con.execute("UPDATE sync_estado SET silenciado = 0 WHERE id = 1")
            con.execute("COMMIT")
    except BaseException:
        for con in cons.values():
            try:
                con.execute("ROLLBACK")
            except _sqlite3.Error:
                pass
        raise
    finally:
        for b, con in cons.items():
            con.isolation_level = aislamiento[b]
    return res


def _resolver_diferidas(cons, diferidas, res):
    """Referencias cuyo destino no estaba al aplicar el registro (llegó después en la misma página)."""
    for base, tabla, uuid, col, destino, uuid_destino in diferidas:
        local = _id_local(cons, destino, uuid_destino)
        if local is None:
            res["refs_vacias"] += 1
            continue
        cons[base].execute(f"UPDATE {sync._nombre(tabla)} SET {col} = ? WHERE uuid = ?", (local, uuid))
