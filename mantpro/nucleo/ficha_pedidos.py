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
"""🛒 Pedidos de material (sin Qt), solo para administradores: la lista de pedidos con sus textos (estado, envío,
retraso e importe), sus líneas, el pedido sugerido (qué pedir ahora), crearlos, enviarlos (correo, WhatsApp, teléfono
o impreso), marcarlos como recibidos, cancelarlos y borrarlos. Lo usan el diálogo del PC (interfaz/dialogos/compras.py)
y MantPro Web; los datos están en nucleo/compras.py. Los errores son códigos (ValueError)."""

import re

from .. import idiomas
from . import almacen, compras, consumos, proveedores, usuarios


def _solo_admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def _resultado(par):
    ok, error = par
    if error:
        raise ValueError(error)
    return ok


def _importe(valor, moneda=None):
    return consumos.formato_importe(valor, moneda or consumos.moneda()) if valor is not None else ""


def nombre_estado(estado):
    return idiomas.t(f"cmp_est_{estado}") if estado in (compras.ESTADO_PEDIDO, compras.ESTADO_PARCIAL,
                                                        compras.ESTADO_RECIBIDO, compras.ESTADO_CANCELADO) else estado


def nombre_canal(canal):
    return idiomas.t(f"cmp_canal_{canal}") if canal in compras.CANALES else (canal or "")


def clase_estado(estado):
    """«recibido» (verde), «cancelado» (gris) o None."""
    return estado if estado in (compras.ESTADO_RECIBIDO, compras.ESTADO_CANCELADO) else None


def texto_enviado(p):
    """(«Correo · 21/11/2026 · 3 días de retraso» / «Sin enviar», clase): clase «retraso» (rojo), «sin_enviar»
    (naranja, solo si sigue abierto) o None."""
    if p["canal"]:
        texto = nombre_canal(p["canal"]) + " · " + idiomas.formato_fecha_localizada((p["enviado"] or "")[:10])
    else:
        texto = idiomas.t("cmp_sin_enviar")
    clase = "sin_enviar" if not p["canal"] and p["estado"] in compras.ESTADOS_ABIERTOS else None
    if p.get("dias_retraso"):
        texto += " · " + (idiomas.t("cmp_retraso_un_dia") if p["dias_retraso"] == 1 else
                          idiomas.t("cmp_retraso_dias").format(n=p["dias_retraso"]))
        clase = "retraso"
    return texto, clase


def filas(usuario, solo_abiertos=True, almacen_ids=None):
    """La tabla de «Pedidos de material»: [{id, fecha, proveedor, lineas, estado (código), estado_txt, clase_estado, enviado,
    clase_enviado, importe, almacen}], del más reciente al más antiguo."""
    _solo_admin(usuario)
    moneda = consumos.moneda()
    resultado = []
    for p in compras.listar_pedidos(solo_abiertos=solo_abiertos, almacen_ids=almacen_ids):
        enviado, clase = texto_enviado(p)
        resultado.append({"id": p["id"], "fecha": idiomas.formato_fecha_localizada(p["fecha"]),
                          "proveedor": p["proveedor_nombre"], "lineas": len(p["lineas"]),
                          "estado": p["estado"], "estado_txt": nombre_estado(p["estado"]), "clase_estado": clase_estado(p["estado"]),
                          "enviado": enviado, "clase_enviado": clase,
                          "importe": _importe(p["importe_estimado"], moneda) + (" *" if p["sin_precio"] else ""),
                          "almacen": p["almacen_nombre"]})
    return resultado


def pedido(usuario, pedido_id, almacen_ids=None):
    """El pedido (compras.obtener_pedido) si existe y, con [almacen_ids], si entrega en alguno de ellos."""
    _solo_admin(usuario)
    p = compras.obtener_pedido(pedido_id) if pedido_id is not None else None
    if p is None or (almacen_ids is not None and not set(almacen_ids) & set(p["almacen_ids"])):
        raise ValueError("no_existe")
    return p


def lineas(p):
    """Las líneas del pedido como las enseña el PC: [{codigo, nombre, cantidad, recibido, completo, referencia,
    precio, precio_real, clase_real («sube»/«baja»/None), almacen}]."""
    moneda = consumos.moneda()
    resultado = []
    for ln in p["lineas"]:
        unidad = f" {ln['unidad']}" if ln["unidad"] else ""
        real = ln.get("precio_real")
        clase = None
        if real is not None and ln["precio"] is not None and abs(real - ln["precio"]) >= compras.TOLERANCIA_PRECIO:
            clase = "sube" if real > ln["precio"] else "baja"
        resultado.append({"codigo": ln["codigo"], "nombre": ln["nombre"], "cantidad": f"{ln['cantidad']:g}{unidad}",
                          "recibido": f"{ln['recibido']:g}{unidad}", "completo": ln["recibido"] >= ln["cantidad"] - 1e-9,
                          "referencia": ln["referencia"], "precio": _importe(ln["precio"], moneda),
                          "precio_real": _importe(real, moneda), "clase_real": clase, "almacen": ln["almacen_nombre"]})
    return resultado


def texto_precio_real(p):
    """«Recibido a precio real: … · diferencia con lo estimado: +…», o «» si no hay precios reales."""
    if not p or not p.get("con_precio_real"):
        return ""
    texto = idiomas.t("cmp_lbl_importe_real").format(real=_importe(p["importe_real"]))
    if abs(p["diferencia_precio"]) >= compras.TOLERANCIA_PRECIO:
        signo = "+" if p["diferencia_precio"] > 0 else "−"
        texto += " · " + idiomas.t("cmp_lbl_diferencia").format(dif=signo + _importe(abs(p["diferencia_precio"])))
    return texto


def avisos(usuario, almacen_ids=None):
    """El botón «🛒 Pedidos» de Stock de almacén: {"texto", "detalle", "n"} (n = pedidos sin enviar o con retraso
    de esos almacenes). Para quien no es administrador, solo el texto."""
    texto = idiomas.t("cmp_btn_pedidos")
    if not usuarios.es_admin(usuario):
        return {"texto": texto, "detalle": "", "n": 0}
    try:
        a = compras.avisos_pedidos(almacen_ids)
    except Exception:                      # noqa: BLE001  (un fallo al leer los pedidos no puede tumbar la pestaña)
        a = {"sin_enviar": [], "retrasados": []}
    n_sin, n_tarde = len(a["sin_enviar"]), len(a["retrasados"])
    partes = []
    if n_sin:
        partes.append(idiomas.t("cmp_aviso_sin_enviar").format(n=n_sin))
    if n_tarde:
        partes.append(idiomas.t("cmp_aviso_retrasados").format(n=n_tarde))
    if not partes:
        return {"texto": texto, "detalle": "", "n": 0}
    return {"texto": f"{texto} (⚠️ {n_sin + n_tarde})", "n": n_sin + n_tarde,
            "detalle": idiomas.t("cmp_aviso_tooltip") + ": " + " · ".join(partes)}


# ---------------------------------------------------------------- pedido sugerido

def sugerido(usuario, almacen_ids):
    """(líneas, sin_calculo) de compras.lineas_sugeridas para esos almacenes."""
    _solo_admin(usuario)
    return compras.lineas_sugeridas(almacen_ids=almacen_ids)


def precio_estimado(material_id, proveedor_id):
    """(precio, referencia) de un artículo con ese proveedor: su último precio apuntado o el del artículo."""
    material = almacen.obtener_material(material_id)
    if material is None:
        return None, ""
    return compras._ultimo_precio_y_referencia(material, proveedor_id)


def texto_total(importes):
    """«Total estimado: …» de los importes de las líneas marcadas (None = sin precio), con «(hay artículos sin
    precio)» si falta alguno."""
    total = sum(i for i in importes if i is not None)
    texto = idiomas.t("cmp_sug_total").format(importe=_importe(total))
    if any(i is None for i in importes):
        texto += " " + idiomas.t("lbl_sin_precio_algunos")
    return texto


def crear(usuario, elegidas, agrupar=False):
    """«Crear pedidos» del pedido sugerido. [elegidas]: las líneas marcadas ({material_id, cantidad, proveedor_id,
    precio, referencia}); las de cantidad 0 no cuentan. Errores: nada_marcado, sin_proveedor, no_creado.
    Devuelve los ids de los pedidos creados."""
    _solo_admin(usuario)
    elegidas = [e for e in elegidas if (compras._num(e.get("cantidad")) or 0) > 0]
    if not elegidas:
        raise ValueError("nada_marcado")
    if any(e.get("proveedor_id") in (None, "", 0) for e in elegidas):
        raise ValueError("sin_proveedor")
    ids, errores = compras.crear_pedidos(elegidas, usuario.get("nombre") or "", agrupar=agrupar)
    if errores and not ids:
        raise ValueError("no_creado")
    return ids


# ---------------------------------------------------------------- acciones sobre un pedido

def marcar_enviado(usuario, pedido_id, canal):
    _solo_admin(usuario)
    return _resultado(compras.marcar_enviado(pedido_id, canal))


def marcar_recibido(usuario, pedido_id):
    _solo_admin(usuario)
    return _resultado(compras.marcar_recibido(pedido_id))


def cancelar(usuario, pedido_id):
    _solo_admin(usuario)
    return _resultado(compras.cancelar_pedido(pedido_id))


def borrar(usuario, pedido_id):
    _solo_admin(usuario)
    return _resultado(compras.borrar_pedido(pedido_id))


def nombre_pdf(p):
    """«pedido_12_Saltoki.pdf»."""
    nombre = re.sub(r"[^A-Za-z0-9_-]+", "_", p["proveedor_nombre"]).strip("_") or "proveedor"
    return f"pedido_{p['id']}_{nombre}.pdf"


def proveedor_de(p):
    """El proveedor del pedido (para el teléfono, el contacto o el correo), o None."""
    return proveedores.obtener_proveedor(p["proveedor_id"]) if p.get("proveedor_id") is not None else None
