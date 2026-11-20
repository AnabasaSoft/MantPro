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

"""Datos del Dashboard (sin Qt): los mismos para la pestaña del PC y para MantPro Web.

datos() junta todo lo que enseña el Dashboard para un usuario y una sede; la interfaz solo lo pinta."""

from datetime import date

from . import avisos as _avisos
from . import contadores, costes, maquinas, usuarios

# Tipos de la distribución, en el orden del PC, con lo que se busca en las etiquetas del trabajo (en minúsculas).
# «urgente» cuenta también las averías.
TIPOS = (("electrico", ("eléctrico", "electrico")), ("mecanico", ("mecánico", "mecanico")),
         ("preventivo", ("preventivo",)), ("urgente", ("urgente", "avería")))


def distribucion(registros):
    """[{"tipo", "cantidad", "porcentaje"}] de cada tipo sobre el total de registros (un registro puede contar en
    varios tipos). [registros]: filas de obtener_todas_cronologico (las etiquetas en la posición 3)."""
    total = len(registros)
    resultado = []
    for tipo, textos in TIPOS:
        n = sum(1 for r in registros if any(x in (r[3] or "").lower() for x in textos))
        resultado.append({"tipo": tipo, "cantidad": n, "porcentaje": int((n / total) * 100) if total else 0})
    return resultado


def registros_del_mes(registros, hoy=None):
    """Registros con fecha del mes de [hoy]."""
    mes = (hoy or date.today()).strftime("%Y-%m")
    return sum(1 for r in registros if (r[1] or "").startswith(mes))


def datos(db, usuario, sede=None, hoy=None):
    """Todo el Dashboard de [usuario] (dict de sesión) en [sede] (id, lista de ids o None = todas).
    [db]: GestorBaseDatos o LectorBD. Los costes solo para administradores (None para el resto)."""
    hoy = hoy or date.today()
    registros = db.obtener_todas_cronologico(sede=sede)
    indicadores = maquinas.indicadores_fiabilidad_global(sede=sede)
    return {
        "avisos_pendientes": _avisos.pendientes_hoy(_avisos.visibles(db.obtener_avisos(sede=sede), usuario),
                                                    contadores.estados_avisos(), hoy),
        "por_hacer": len(db.obtener_pendientes(sede=sede)),
        "registros_mes": registros_del_mes(registros, hoy),
        "mtbf_dias": indicadores["mtbf_dias"],
        "mttr_horas": indicadores["mttr_horas"],
        "ranking_trabajos": maquinas.ranking_trabajos(sede=sede),
        "averias_por_mes": maquinas.averias_por_mes(sede=sede),
        "distribucion": distribucion(registros),
        "costes": costes.resumen(sede=sede) if usuarios.es_admin(usuario) else None,
    }
