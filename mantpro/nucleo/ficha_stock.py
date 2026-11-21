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

"""Las pestañas «📦 Stock de almacén» y «⚠️ Stock bajo mínimo» (sin Qt): qué almacenes se ven, la tabla de
artículos, el panel del artículo elegido (se usa en, otros almacenes, movimientos), las entradas y salidas y la lista
de bajo mínimo. Lo usan las pestañas del PC y MantPro Web.

Como en el PC, cualquier usuario mueve stock de los almacenes que ve; el proveedor y el precio de una compra solo los
apunta un administrador. Los errores son códigos (ValueError), nunca texto."""

import re

from .. import idiomas
from . import almacen, almacenes, compras, maquinas, proveedores, sedes, usuarios

CANTIDAD_MIN, CANTIDAD_MAX = 0.01, 999999            # los del campo «Cantidad» del diálogo de movimiento del PC
TIPOS_MOVIMIENTO = ("entrada", "salida")


def clave_ubicacion(ubicacion, nombre=""):
    """Para ordenar por ubicación de forma natural («Estantería 2» antes que «Estantería 10»), con el nombre como
    desempate y los artículos sin ubicación al final."""
    def natural(t):
        return re.sub(r"\d+", lambda m: m.group().zfill(8), (t or "").lower())
    return ("￿" if not ubicacion else natural(ubicacion)) + "\x00" + natural(nombre)


def ubicacion(seccion_id):
    return almacen.obtener_ubicacion_texto(seccion_id, idiomas.t("txt_balda_num"), idiomas.t("txt_hueco_suelo_corto"))


def color_stock(actual, minimo):
    """«bajo» (rojo) por debajo del mínimo, «sobre» (verde) por encima, None si coincide."""
    if actual < minimo:
        return "bajo"
    if actual > minimo:
        return "sobre"
    return None


def motivo_visible(motivo):
    """Los motivos que pone la propia aplicación (guardados en forma canónica) en el idioma activo; los que escribe
    el usuario, tal cual."""
    t = idiomas.t
    motivo = motivo or ""
    if motivo == almacen.MOTIVO_ALTA_INICIAL:
        return t("motivo_alta_inicial")
    if motivo == almacen.MOTIVO_AJUSTE_IMPORTACION:
        return t("motivo_ajuste_importacion")
    if motivo.startswith(almacen.PREFIJO_MOTIVO_USADO_EN_TRABAJO):
        return t("motivo_usado_en_trabajo").format(trabajo=motivo[len(almacen.PREFIJO_MOTIVO_USADO_EN_TRABAJO):])
    if motivo.startswith(almacenes.PREFIJO_TRASPASO_A):
        return t("motivo_traspaso_a").format(almacen=motivo[len(almacenes.PREFIJO_TRASPASO_A):])
    if motivo.startswith(almacenes.PREFIJO_TRASPASO_DESDE):
        return t("motivo_traspaso_desde").format(almacen=motivo[len(almacenes.PREFIJO_TRASPASO_DESDE):])
    return motivo


# ---------------------------------------------------------------- qué se ve

def almacenes_de(sede):
    """Los almacenes que se ven desde [sede] (id, lista o None) y el que se elige de entrada (el primero propio de la
    sede; si no, el primero, común), como el desplegable del PC: (lista de dicts, id o None si no hay ninguno)."""
    lista = almacenes.listar(sede)
    elegido = next((a["id"] for a in lista if not a["comun"]), lista[0]["id"] if lista else None)
    return lista, elegido


def almacen_visible(usuario, almacen_id):
    """[almacen_id] si se ve desde las sedes del usuario; si no, ValueError("almacen_no_permitido")."""
    ids = almacenes.ids_de_sede(sedes.permitidas(usuario))
    if almacen_id is None or (ids is not None and almacenes.efectivo(almacen_id) not in ids):
        raise ValueError("almacen_no_permitido")
    return almacen_id


def material_visible(usuario, material_id):
    """El artículo (dict) si es de un almacén que se ve desde las sedes del usuario; si no, ValueError("no_encontrado")."""
    m = almacen.obtener_material(material_id) if material_id is not None else None
    ids = almacenes.ids_de_sede(sedes.permitidas(usuario))
    if not m or (ids is not None and almacenes.efectivo(m["almacen_id"]) not in ids):
        raise ValueError("no_encontrado")
    return m


def _fila(m):
    ubic = ubicacion(m.get("seccion_id"))
    return dict(m, ubicacion=ubic, color=color_stock(m["stock_actual"], m["stock_minimo"]),
                bajo_minimo=almacen.esta_bajo_minimo(m), orden_ubicacion=clave_ubicacion(ubic, m["nombre"]))


def lista(almacen_id, buscar=None, zona_id=None):
    """Los artículos del almacén (con [buscar] y [zona_id], como la barra del PC), con ubicacion, color,
    bajo_minimo y orden_ubicacion, ordenados por ubicación (como se recorre el almacén)."""
    if almacen_id is None:
        return []
    filas = [_fila(m) for m in almacen.listar_materiales((buscar or "").strip() or None, zona_id, almacen_ids=[almacen_id])]
    return sorted(filas, key=lambda f: f["orden_ubicacion"])


def bajo_minimo(sede):
    """«⚠️ Stock bajo mínimo»: los de los almacenes que se ven desde [sede] sin stock o por debajo del mínimo, y los
    que están justo en él (sin color). Devuelve (filas, cuántos están por debajo: el número de la pestaña)."""
    filas = [_fila(m) for m in almacen.materiales_bajo_minimo(incluir_en_minimo=True, almacen_ids=almacenes.ids_de_sede(sede))]
    return filas, sum(1 for f in filas if f["bajo_minimo"])


def detalle(material_id, limite=20):
    """El panel de debajo de la tabla: {nombre, usado_en (texto o ""), otros_almacenes (texto o ""), movimientos:
    [{tipo, icono, texto}]} con los [limite] últimos movimientos."""
    t = idiomas.t
    m = almacen.obtener_material(material_id) or {}
    nombre = m.get("nombre") or ""
    rutas = maquinas.mapa_rutas_completas()
    usado = sorted((f"{rutas[mid]} ({cant:g})" for mid, cant in almacen.maquinas_de_material(material_id) if mid in rutas),
                   key=str.lower)
    otros = ""
    if almacenes.hay_varios():
        lista_otros = [f"{n}: {st:g}" for n, st, mid in almacenes.stock_por_almacen(material_id) if mid != material_id]
        otros = t("lbl_en_otros_almacenes").format(lista=", ".join(lista_otros)) if lista_otros else ""
    movimientos = []
    for mov in almacen.obtener_movimientos(material_id, limite=limite):
        if mov["tipo"] == "traslado":
            texto = f"🔀 {mov['fecha']}   {nombre}: {mov.get('motivo') or ''}   —   {mov.get('usuario_nombre') or ''}"
        else:
            icono = "📥" if mov["tipo"] == "entrada" else "📤"
            texto = f"{icono} {mov['fecha']}   {mov['cantidad']:g}   —   {mov.get('usuario_nombre') or ''}"
            if mov.get("motivo"):
                texto += f"   ({motivo_visible(mov['motivo'])})"
        movimientos.append({"tipo": mov["tipo"], "texto": texto})
    return {"nombre": nombre, "titulo": t("lbl_historial_de").format(nombre=nombre),
            "usado_en": t("lbl_usado_en").format(maquinas=", ".join(usado)) if usado else "",
            "otros_almacenes": otros, "movimientos": movimientos}


# ---------------------------------------------------------------- entradas y salidas

def _cantidad(cantidad):
    try:
        valor = float(str(cantidad).replace(",", "."))
    except (TypeError, ValueError):
        raise ValueError("cantidad_no_valida") from None
    if not CANTIDAD_MIN <= valor <= CANTIDAD_MAX:
        raise ValueError("cantidad_no_valida")
    return valor


def movimiento(usuario, material_id, tipo, cantidad, motivo="", proveedor_id=None, precio=None):
    """📥 Entrada o 📤 Salida de stock (el diálogo del PC). Una salida sin stock suficiente: «stock_insuficiente». En
    una entrada, lo que llega descuenta lo pendiente de los pedidos (compras.recibir); con proveedor (solo
    administradores) queda en el historial de precios del artículo. Devuelve {"diferencias": las líneas de pedido que
    llegan a otro precio, "precio_distinto": (precio nuevo, actual) si la compra tiene un precio distinto del del
    artículo, para preguntar si se cambia (eso lo hace fijar_precio)}."""
    if tipo not in TIPOS_MOVIMIENTO:
        raise ValueError("tipo_no_valido")
    material_visible(usuario, material_id)
    cantidad = _cantidad(cantidad)
    admin = usuarios.es_admin(usuario)
    if proveedor_id is not None:
        if tipo != "entrada" or not admin:
            raise ValueError("solo_admin")
        if proveedor_id not in {pr["id"] for pr in proveedores.listar_proveedores()}:
            raise ValueError("proveedor_no_existe")
        if precio is not None and (precio < 0 or precio > 1e9):
            raise ValueError("precio_no_valido")
    else:
        precio = None
    ok, error = almacen.registrar_movimiento(material_id, tipo, cantidad, usuario["id"] if usuario else None,
                                             usuario["nombre"] if usuario else None, (motivo or "").strip()[:200])
    if not ok:
        raise ValueError(error or "no_guardado")
    resultado = {"diferencias": [], "precio_distinto": None}
    if tipo != "entrada":
        return resultado
    recepcion = compras.recibir(material_id, cantidad, proveedor_id, precio if proveedor_id is not None and admin else None)
    resultado["diferencias"] = recepcion["diferencias"]
    if proveedor_id is None:
        return resultado
    proveedores.registrar_precio(material_id, proveedor_id, precio, cantidad, usuario_nombre=usuario["nombre"] if usuario else "")
    actual = (almacen.obtener_material(material_id) or {}).get("precio")
    if precio is not None and (actual is None or abs(actual - precio) > 1e-9):
        resultado["precio_distinto"] = (precio, actual)
    return resultado


def fijar_precio(usuario, material_id, precio):
    """«¿Actualizar el precio del artículo?» tras una compra a otro precio (solo administradores)."""
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")
    material_visible(usuario, material_id)
    if precio is None or precio < 0:
        raise ValueError("precio_no_valido")
    proveedores.fijar_precio_articulo(material_id, precio, usuario["id"] if usuario else None, usuario["nombre"] if usuario else None)
    return True
