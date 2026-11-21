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

"""«⚙️ Configurar almacén» (sin Qt): zonas, estanterías, baldas, huecos de suelo y secciones de un almacén, la moneda
de los precios y el objetivo por defecto del pedido sugerido. Lo usan el diálogo del PC y MantPro Web.

Todo es solo de administradores y solo sobre almacenes que se ven desde sus sedes; cada id que llega (zona,
estantería, balda, sección) se comprueba que es de ese almacén. Los errores son códigos (ValueError), nunca texto."""

from .. import idiomas
from . import almacen, almacenes, consumos, ficha_stock, pedidos, usuarios

BALDAS_MIN, BALDAS_MAX = 1, 30            # los del diálogo «Nueva estantería» del PC
SECCIONES_MAX = 30
ESTILOS_BALDAS = ("numero", "letra")
ESTILOS_SECCIONES = ("letra", "numero")
FACTOR_MIN, FACTOR_MAX = 0.1, 100.0       # «Objetivo por defecto: stock mínimo ×»
NOMBRE_MAX = 200


# ---------------------------------------------------------------- comprobaciones

def almacen_admin(usuario, almacen_id):
    """El almacén (id efectivo) si el usuario es administrador y lo ve desde sus sedes."""
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")
    almacen_id = almacenes.efectivo(almacen_id)
    if almacen_id is None or almacenes.obtener(almacen_id) is None:
        raise ValueError("almacen_no_permitido")
    return ficha_stock.almacen_visible(usuario, almacen_id)


def _nombre(nombre):
    nombre = (nombre or "").strip()[:NOMBRE_MAX]
    if not nombre:
        raise ValueError("nombre_obligatorio")
    return nombre


def zonas(almacen_id):
    """Las zonas del almacén, en orden natural: [{id, nombre}]."""
    return [{"id": z["id"], "nombre": z["nombre"]} for z in almacen.listar_zonas(almacenes.efectivo(almacen_id))]


def _zona(almacen_id, zona_id):
    if zona_id is None or zona_id not in {z["id"] for z in zonas(almacen_id)}:
        raise ValueError("zona_no_existe")
    return zona_id


def _mapa(almacen_id):
    """{estantería: dict}, {balda: (estantería, es_suelo)} y {sección: balda} de todo el almacén."""
    ests, baldas, secciones = {}, {}, {}
    for est in almacen.listar_estructura(almacen_ids=almacenes.efectivo(almacen_id)):
        ests[est["id"]] = est
        for b in est["baldas"]:
            baldas[b["id"]] = (est["id"], b["numero"] == 0)
            for s in b["secciones"]:
                secciones[s["id"]] = b["id"]
    return ests, baldas, secciones


def texto_balda(balda, estilo_baldas="numero"):
    t = idiomas.t
    if balda["numero"] == 0:
        return t("txt_hueco_suelo_corto")
    return t("txt_balda_num").format(n=almacen.texto_balda(balda["numero"], estilo_baldas or "numero"))


def arbol(almacen_id, zona_id):
    """El árbol del diálogo (estantería → balda / hueco de suelo → sección), sin las secciones implícitas (las que
    se crean solas al ubicar un artículo en la balda sin elegir sección):
    [{id, nombre, estilo_baldas, num_baldas, tiene_hueco_suelo, baldas: [{id, texto, suelo, secciones: [{id, nombre}]}]}]."""
    if zona_id is None:
        return []
    resultado = []
    for est in almacen.listar_estructura(zona_id, almacen_ids=almacenes.efectivo(almacen_id)):
        estilo = est.get("estilo_baldas") or "numero"
        baldas = [{"id": b["id"], "texto": texto_balda(b, estilo), "suelo": b["numero"] == 0,
                   "secciones": [{"id": s["id"], "nombre": s["nombre"]} for s in b["secciones"] if not s.get("implicita")]}
                  for b in est["baldas"]]
        resultado.append({"id": est["id"], "nombre": est["nombre"], "estilo_baldas": estilo,
                          "num_baldas": sum(1 for b in est["baldas"] if b["numero"] != 0),
                          "tiene_hueco_suelo": bool(est.get("tiene_hueco_suelo")), "baldas": baldas})
    return resultado


def seleccion(almacen_id, elegidos):
    """Clasifica lo elegido en el árbol (pares (tipo, id) con tipo «estanteria», «balda» o «seccion») como el menú del
    botón derecho del PC: {"estanterias", "baldas", "suelos", "secciones", "afectadas"} (conjuntos de ids; «afectadas»
    = estanterías elegidas o con alguna balda elegida). Lo que no es de este almacén se descarta."""
    ests, baldas, secciones = _mapa(almacen_id)
    r = {"estanterias": set(), "baldas": set(), "suelos": set(), "secciones": set(), "afectadas": set()}
    for tipo, id_ in elegidos:
        if tipo == "estanteria" and id_ in ests:
            r["estanterias"].add(id_)
            r["afectadas"].add(id_)
        elif tipo == "balda" and id_ in baldas:
            est, suelo = baldas[id_]
            r["suelos" if suelo else "baldas"].add(id_)
            r["afectadas"].add(est)
        elif tipo == "seccion" and id_ in secciones:
            r["secciones"].add(id_)
    return r


# ---------------------------------------------------------------- zonas

def crear_zona(usuario, almacen_id, nombre):
    almacen_id = almacen_admin(usuario, almacen_id)
    return almacen.crear_zona(_nombre(nombre), almacenes.guardable(almacen_id))


def renombrar_zona(usuario, almacen_id, zona_id, nombre):
    almacen_id = almacen_admin(usuario, almacen_id)
    almacen.renombrar_zona(_zona(almacen_id, zona_id), _nombre(nombre))


def estanterias_de_zona(zona_id):
    return len(almacen.zona_estanterias(zona_id))


def eliminar_zona(usuario, almacen_id, zona_id, forzar=False):
    """Sin [forzar], si la zona tiene estanterías no borra nada: ValueError("contiene_estanterias") (para preguntar
    antes, como el PC). Si alguna estantería tiene material ubicado: ValueError("no_vacio")."""
    almacen_id = almacen_admin(usuario, almacen_id)
    ok, error = almacen.eliminar_zona(_zona(almacen_id, zona_id), forzar=forzar)
    if not ok:
        raise ValueError(error or "no_vacio")


# ---------------------------------------------------------------- estanterías

def datos_estanteria(nombre, num_baldas, hueco_suelo, num_secciones, estilo_baldas, estilo_secciones):
    """Los campos del diálogo «Nueva estantería» / «Editar estantería», comprobados."""
    try:
        num_baldas, num_secciones = int(num_baldas), int(num_secciones or 0)
    except (TypeError, ValueError):
        raise ValueError("numero_no_valido") from None
    if not BALDAS_MIN <= num_baldas <= BALDAS_MAX or not 0 <= num_secciones <= SECCIONES_MAX:
        raise ValueError("numero_no_valido")
    if estilo_baldas not in ESTILOS_BALDAS or estilo_secciones not in ESTILOS_SECCIONES:
        raise ValueError("estilo_no_valido")
    return {"nombre": _nombre(nombre), "num_baldas": num_baldas, "hueco_suelo": bool(hueco_suelo),
            "num_secciones": num_secciones, "estilo_baldas": estilo_baldas, "estilo_secciones": estilo_secciones}


def _estanterias(almacen_id, ids):
    ests = _mapa(almacen_id)[0]
    ids = set(ids or ())
    if not ids or not ids <= set(ests):
        raise ValueError("estanteria_no_existe")
    return ids


def estanteria(almacen_id, estanteria_id):
    """La estantería (dict del árbol) si es de este almacén; si no, ValueError("estanteria_no_existe")."""
    for est in almacen.listar_estructura(almacen_ids=almacenes.efectivo(almacen_id)):
        if est["id"] == estanteria_id:
            return next(e for e in arbol(almacen_id, est["zona_id"]) if e["id"] == estanteria_id)
    raise ValueError("estanteria_no_existe")


def crear_estanteria(usuario, almacen_id, zona_id, datos):
    almacen_id = almacen_admin(usuario, almacen_id)
    _zona(almacen_id, zona_id)
    d = datos_estanteria(**datos)
    return almacen.crear_estanteria(d["nombre"], d["num_baldas"], d["hueco_suelo"], d["num_secciones"],
                                    d["estilo_baldas"], d["estilo_secciones"], zona_id=zona_id)


def editar_estanteria(usuario, almacen_id, estanteria_id, datos):
    """Devuelve cuántas baldas no se han podido quitar por tener material ubicado."""
    almacen_id = almacen_admin(usuario, almacen_id)
    _estanterias(almacen_id, [estanteria_id])
    d = datos_estanteria(**datos)
    return almacen.editar_estanteria(estanteria_id, d["nombre"], d["num_baldas"], d["hueco_suelo"], d["num_secciones"],
                                     d["estilo_baldas"], d["estilo_secciones"]) or 0


def eliminar_estanterias(usuario, almacen_id, ids):
    """Borra las estanterías (con su estructura); devuelve cuántas no se han podido borrar por tener material."""
    almacen_id = almacen_admin(usuario, almacen_id)
    return sum(1 for id_ in sorted(_estanterias(almacen_id, ids)) if not almacen.eliminar_estanteria(id_)[0])


def anadir_baldas(usuario, almacen_id, estanteria_ids):
    """Una balda más (arriba) en cada estantería."""
    almacen_id = almacen_admin(usuario, almacen_id)
    for id_ in sorted(_estanterias(almacen_id, estanteria_ids)):
        almacen.anadir_balda(id_)


def anadir_huecos_suelo(usuario, almacen_id, estanteria_ids):
    """El hueco de suelo en cada estantería que no lo tenga; devuelve cuántas ya lo tenían."""
    almacen_id = almacen_admin(usuario, almacen_id)
    ids = _estanterias(almacen_id, estanteria_ids)
    return len(ids) - sum(1 for id_ in sorted(ids) if almacen.anadir_hueco_suelo(id_))


def cambiar_estilo(usuario, almacen_id, estanteria_ids, estilo):
    almacen_id = almacen_admin(usuario, almacen_id)
    if estilo not in ESTILOS_BALDAS:
        raise ValueError("estilo_no_valido")
    for id_ in sorted(_estanterias(almacen_id, estanteria_ids)):
        almacen.cambiar_estilo_baldas(id_, estilo)


# ---------------------------------------------------------------- baldas y secciones

def eliminar_baldas(usuario, almacen_id, ids):
    """Borra baldas o huecos de suelo (con sus secciones); devuelve cuántos no se han podido borrar por tener material."""
    almacen_id = almacen_admin(usuario, almacen_id)
    baldas = _mapa(almacen_id)[1]
    ids = set(ids or ())
    if not ids or not ids <= set(baldas):
        raise ValueError("balda_no_existe")
    return sum(1 for id_ in sorted(ids) if not almacen.eliminar_balda(id_)[0])


def crear_seccion(usuario, almacen_id, balda_id, nombre):
    almacen_id = almacen_admin(usuario, almacen_id)
    if balda_id not in _mapa(almacen_id)[1]:
        raise ValueError("balda_no_existe")
    return almacen.crear_seccion(balda_id, _nombre(nombre))


def eliminar_seccion(usuario, almacen_id, seccion_id):
    almacen_id = almacen_admin(usuario, almacen_id)
    if seccion_id not in _mapa(almacen_id)[2]:
        raise ValueError("seccion_no_existe")
    ok, error = almacen.eliminar_seccion(seccion_id)
    if not ok:
        raise ValueError(error or "no_vacio")


# ---------------------------------------------------------------- ajustes

def ajustes():
    """La moneda de los precios y el factor del objetivo por defecto (texto para el campo, sin ceros de más)."""
    return {"moneda": consumos.moneda(), "factor": pedidos.factor_objetivo()}


def fijar_moneda(usuario, simbolo):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")
    consumos.fijar_moneda(simbolo)
    return consumos.moneda()


def fijar_factor(usuario, factor):
    """Admite coma o punto; entre FACTOR_MIN y FACTOR_MAX (como el campo del PC)."""
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")
    try:
        valor = round(float(str(factor).strip().replace(",", ".")), 1)
    except (TypeError, ValueError):
        raise ValueError("factor_no_valido") from None
    if not FACTOR_MIN <= valor <= FACTOR_MAX:
        raise ValueError("factor_no_valido")
    return pedidos.fijar_factor_objetivo(valor)
