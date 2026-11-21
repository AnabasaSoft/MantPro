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

"""🏭 Proveedores y 💶 Precios por proveedor (sin Qt), solo para administradores: la lista, alta, edición y baja de
proveedores, y los precios de un artículo por proveedor (el último de cada uno con su variación, la referencia en
cada proveedor y el historial). Lo usan los diálogos del PC y MantPro Web; los datos y su registro de cambios están en
nucleo/proveedores.py y nucleo/tarifas.py. Los errores son códigos (ValueError)."""

from .. import idiomas
from . import almacen, consumos, proveedores, tarifas, usuarios

COLOR_BARATO, COLOR_SUBE, COLOR_BAJA = "#2e8b57", "#c0392b", "#2e8b57"


def _solo_admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def _resultado(par):
    ok, error = par
    if error:
        raise ValueError(error)
    return ok


# ---------------------------------------------------------------- 🏭 Proveedores

def lista():
    """[{id, nombre, contacto, telefono, correo, nota, plazo_entrega, articulos}] por nombre."""
    return proveedores.listar_proveedores()


def guardar(usuario, proveedor_id, datos):
    """Alta (proveedor_id None) o edición: nombre (obligatorio y sin repetir), contacto, telefono, correo, nota y
    plazo_entrega (días, 0 o vacío = sin plazo). Devuelve el id."""
    _solo_admin(usuario)
    d = {k: (datos.get(k) or "").strip() if isinstance(datos.get(k), str) else datos.get(k)
         for k in ("nombre", "contacto", "telefono", "correo", "nota")}
    plazo = datos.get("plazo_entrega")
    if plazo not in (None, "", 0):
        try:
            plazo = int(str(plazo).strip())
        except ValueError:
            raise ValueError("plazo_no_valido") from None
        if not 0 <= plazo <= proveedores.PLAZO_MAX:
            raise ValueError("plazo_no_valido")
    d["plazo_entrega"] = plazo or None
    if not d["nombre"]:
        raise ValueError("nombre_obligatorio")
    if proveedor_id is None:
        nuevo, error = proveedores.crear_proveedor(**d)
        if error:
            raise ValueError(error)
        return nuevo
    if proveedores.obtener_proveedor(proveedor_id) is None:
        raise ValueError("no_existe")
    _resultado(proveedores.editar_proveedor(proveedor_id, **d))
    return proveedor_id


def borrar(usuario, proveedor_id):
    _solo_admin(usuario)
    return _resultado(proveedores.borrar_proveedor(proveedor_id))


# ---------------------------------------------------------------- 💶 Precios por proveedor

def variacion(precio, anterior):
    """(«▲ 25,0 %» / «▼ 3,1 %» / «=» / «», color o None) de un precio respecto al anterior del mismo proveedor."""
    if anterior is None or anterior == 0:
        return "", None
    pct = (precio - anterior) / anterior * 100
    if abs(pct) < 0.05:
        return "=", None
    texto = f"{abs(pct):.1f}"
    if idiomas.get_idioma() != "en":
        texto = texto.replace(".", ",")
    return (f"▲ {texto} %", COLOR_SUBE) if pct > 0 else (f"▼ {texto} %", COLOR_BAJA)


def precios(material_id):
    """Lo que enseña «Precios por proveedor» de un artículo: {resumen, referencias, historial}, con los textos ya
    hechos (importes en la moneda, fechas en el idioma, variación y su color)."""
    moneda = consumos.moneda()

    def importe(v):
        return consumos.formato_importe(v, moneda) if v is not None else "—"

    def fecha(f):
        return idiomas.formato_fecha_localizada(f) if f else ""

    resumen = []
    for r in proveedores.resumen_precios(material_id):
        texto_var, color_var = variacion(r["precio"], r["anterior"])
        resumen.append(dict(r, precio_txt=importe(r["precio"]), fecha_txt=fecha(r["fecha"]), variacion=texto_var,
                            color_variacion=color_var))
    referencias = [dict(r, tarifa_txt=importe(r["precio_lista"]) if r["precio_lista"] is not None else "",
                        dto_txt="" if r["descuento"] is None else f"{r['descuento']:g}",
                        neto_txt=importe(r["precio"]) if r["precio"] is not None else "", fecha_txt=fecha(r["fecha"]))
                   for r in tarifas.proveedores_de_articulo(material_id)]
    historial = [dict(h, fecha_txt=fecha(h["fecha"]), precio_txt=importe(h["precio"]),
                      cantidad_txt="" if h["cantidad"] is None else f"{h['cantidad']:g}")
                 for h in proveedores.historial_precios(material_id)]
    return {"resumen": resumen, "referencias": referencias, "historial": historial}


def _material(material_id):
    m = almacen.obtener_material(material_id) if material_id is not None else None
    if m is None:
        raise ValueError("material_no_existe")
    return m


def apuntar_precio(usuario, material_id, proveedor_id, precio, fecha=None, referencia=""):
    """➕ Apuntar precio (una oferta o una compra) de un artículo a un proveedor."""
    _solo_admin(usuario)
    _material(material_id)
    if proveedores.obtener_proveedor(proveedor_id) is None:
        raise ValueError("no_existe")
    n = consumos.numero(precio)
    if n is None or n < 0:
        raise ValueError("precio_obligatorio")
    nuevo, error = proveedores.registrar_precio(material_id, proveedor_id, n, None, fecha, (referencia or "").strip(), "",
                                                usuario["nombre"] if usuario else "")
    if error:
        raise ValueError(error)
    return nuevo


def _apunte(material_id, apunte_id):
    a = next((h for h in proveedores.historial_precios(material_id) if h["id"] == apunte_id), None)
    if a is None:
        raise ValueError("apunte_no_existe")
    return a


def usar_precio(usuario, material_id, apunte_id):
    """💲 Usar como precio del artículo el del apunte (cambia el coste de los trabajos a partir de ahora)."""
    _solo_admin(usuario)
    a = _apunte(material_id, apunte_id)
    if a["precio"] is None:
        raise ValueError("sin_precio")
    return _resultado(proveedores.fijar_precio_articulo(material_id, a["precio"], usuario["id"] if usuario else None,
                                                        usuario["nombre"] if usuario else None))


def borrar_apunte(usuario, material_id, apunte_id):
    _solo_admin(usuario)
    _apunte(material_id, apunte_id)
    return _resultado(proveedores.borrar_precio(apunte_id))


def fijar_referencia(usuario, material_id, proveedor_id, referencia):
    """🔖 Referencia del proveedor para este artículo (vacía: quitarla)."""
    _solo_admin(usuario)
    _material(material_id)
    return _resultado(tarifas.fijar_referencia(material_id, proveedor_id, referencia))
