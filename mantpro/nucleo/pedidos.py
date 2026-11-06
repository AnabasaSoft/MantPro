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
pedidos.py — Punto de pedido: stock objetivo y múltiplo de pedido de cada artículo.

Paso 3 de «Proveedores y punto de pedido». Cada artículo puede llevar:

- **Stock objetivo**: hasta cuánto se quiere llenar al pedir. Si está vacío se
  usa un múltiplo del stock mínimo (el factor se configura en el almacén; por
  defecto, el doble).
- **Múltiplo de pedido**: hay artículos que solo se compran en cajas de 10; la
  cantidad sugerida se redondea hacia arriba a ese múltiplo.

`cantidad_sugerida()` calcula cuánto pedir de un artículo. En el paso siguiente
(pedido sugerido) se le pasará además lo que ya está pedido y pendiente de
llegar, para no sugerir lo mismo cada día.

Vive en almacen.db (columnas nuevas de `materiales`). Python puro, sin Qt: lo
usan la API del servidor y la ventana del PC.
"""

import math

from . import almacen
from . import usuarios as _usuarios

FACTOR_POR_DEFECTO = 2.0     # objetivo = mínimo × 2 si el artículo no tiene objetivo propio
_MAX_NUMERO = 999999.0


def inicializar():
    """Añade las columnas si no existen. Idempotente."""
    con = almacen._conn()
    columnas = almacen._columnas(con, "materiales")
    if "stock_objetivo" not in columnas:
        con.execute("ALTER TABLE materiales ADD COLUMN stock_objetivo REAL")
    if "multiplo_pedido" not in columnas:
        con.execute("ALTER TABLE materiales ADD COLUMN multiplo_pedido REAL")
    con.commit()
    con.close()


def _numero(valor):
    """float positivo, o None si está vacío, es texto raro, cero o negativo."""
    if valor is None or valor == "":
        return None
    try:
        n = float(str(valor).replace(",", "."))
    except ValueError:
        return None
    if math.isnan(n) or math.isinf(n) or n <= 0:
        return None
    return min(n, _MAX_NUMERO)


def _g(n):
    return "" if n is None else f"{n:g}"


# --------------------------------------------------------------- configuración

def factor_objetivo():
    """Por cuánto se multiplica el stock mínimo para obtener el objetivo de los
    artículos que no tienen uno propio (configurable; 2 por defecto)."""
    try:
        con = _usuarios._conn()
        fila = con.execute("SELECT valor FROM config WHERE clave='factor_objetivo'").fetchone()
        con.close()
        n = _numero(fila[0]) if fila else None
        return n if n is not None else FACTOR_POR_DEFECTO
    except Exception:
        return FACTOR_POR_DEFECTO


def fijar_factor_objetivo(factor):
    """Guarda el factor (debe ser mayor que 0; si no, vuelve al de por defecto)
    y apunta el cambio en el registro. Devuelve el valor que ha quedado."""
    nuevo = _numero(factor) or FACTOR_POR_DEFECTO
    anterior = factor_objetivo()
    con = _usuarios._conn()
    con.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    con.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('factor_objetivo', ?)", (_g(nuevo),))
    con.commit()
    con.close()
    if anterior != nuevo:
        _usuarios.auditar("configuracion", "configurar", "Almacén",
                          cambios=[{"campo": "Objetivo por defecto (× mínimo)",
                                    "antes": _g(anterior), "despues": _g(nuevo)}])
    return nuevo


# ------------------------------------------------------------- por artículo

def parametros(material_id):
    """(stock_objetivo, multiplo_pedido) propios del artículo (None si no tiene)."""
    m = almacen.obtener_material(material_id)
    if m is None:
        return None, None
    return m.get("stock_objetivo"), m.get("multiplo_pedido")


def fijar_parametros(material_id, stock_objetivo, multiplo_pedido):
    """Guarda el stock objetivo y el múltiplo de pedido del artículo (vacío o 0
    los quita). Apunta en el registro solo lo que cambia. Devuelve (True, None)
    o (False, código)."""
    m = almacen.obtener_material(material_id)
    if m is None:
        return False, "material_no_existe"
    objetivo, multiplo = _numero(stock_objetivo), _numero(multiplo_pedido)
    antes = (m.get("stock_objetivo"), m.get("multiplo_pedido"))
    if antes == (objetivo, multiplo):
        return True, None
    con = almacen._conn()
    con.execute("UPDATE materiales SET stock_objetivo=?, multiplo_pedido=? WHERE id=?",
                (objetivo, multiplo, material_id))
    con.commit()
    con.close()
    cambios = []
    if antes[0] != objetivo:
        cambios.append({"campo": "Stock objetivo", "antes": _g(antes[0]), "despues": _g(objetivo)})
    if antes[1] != multiplo:
        cambios.append({"campo": "Múltiplo de pedido", "antes": _g(antes[1]), "despues": _g(multiplo)})
    nombre = f"{m['codigo']} · {m['nombre']}" if m.get("codigo") else m["nombre"]
    _usuarios.auditar("almacen", "editar", nombre, cambios=cambios)
    return True, None


def objetivo_efectivo(material):
    """Stock hasta el que se quiere llenar el artículo: el suyo propio o, si no
    lo tiene, su mínimo × el factor. None si no hay ni objetivo ni mínimo (no se
    puede calcular un pedido)."""
    propio = _numero(material.get("stock_objetivo"))
    if propio is not None:
        return propio
    minimo = material.get("stock_minimo") or 0
    return minimo * factor_objetivo() if minimo > 0 else None


def cantidad_sugerida(material, pendiente_de_llegar=0.0, factor=None):
    """Cantidad a pedir de un artículo: objetivo − stock actual − lo ya pedido y
    pendiente de llegar, redondeada hacia arriba al múltiplo de pedido. Es 0 si no
    hace falta pedir (o no se puede calcular). [factor] evita releer la
    configuración al calcular muchos artículos seguidos."""
    propio = _numero(material.get("stock_objetivo"))
    if propio is not None:
        objetivo = propio
    else:
        minimo = material.get("stock_minimo") or 0
        if minimo <= 0:
            return 0.0
        objetivo = minimo * (factor if factor is not None else factor_objetivo())
    falta = objetivo - (material.get("stock_actual") or 0) - (pendiente_de_llegar or 0)
    if falta <= 1e-9:
        return 0.0
    multiplo = _numero(material.get("multiplo_pedido"))
    if multiplo is not None:
        falta = math.ceil(falta / multiplo - 1e-9) * multiplo
    return round(falta, 6)
