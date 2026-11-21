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

"""Calendario (sin Qt): los días especiales (vacaciones, puentes, días libres y festivos a mano), lo que se ve al
elegir un día y el color de cada día del mes. Lo usan la pestaña Calendario del PC y MantPro Web.

Los días especiales se guardan con su forma canónica en español («Vacaciones», «Puente», «Día Libre», «Festivo
(Manual)»), que se enseña traducida. Las versiones anteriores los guardaban en el idioma del PC («Holiday (Manual)»):
tipo_canonico() los reconoce. Gestionarlos es de administradores (como el menú del PC); los errores son códigos."""

import re
from datetime import date

from .. import idiomas
from . import avisos, contadores, historial, usuarios
from .fotos import _RE_GALERIA

# (forma canónica, clave del texto, clase: el color del día)
TIPOS = (("Vacaciones", "tipo_vacaciones", "vacaciones"), ("Puente", "tipo_puente", "puente"),
         ("Día Libre", "tipo_dia_libre", "libre"), ("Festivo (Manual)", "tipo_festivo_manual", "festivo"))
FESTIVO_MANUAL = "Festivo (Manual)"
_POR_CANONICO = {c: (clave, clase) for c, clave, clase in TIPOS}
# Color de los avisos de la lista del día (los mismos que la pestaña Avisos)
COLORES_AVISO = {e: avisos.ESTADOS[e][1] for e in ("OK", "PENDIENTE", "ATRASADO")}


def tipo_canonico(valor):
    """La forma canónica de un tipo de día guardado en cualquier idioma, o el valor tal cual si no se reconoce."""
    valor = (valor or "").strip()
    if valor in _POR_CANONICO:
        return valor
    for canonico, clave, _ in TIPOS:
        if any(tr.get(clave) == valor for tr in idiomas.TRADUCCIONES.values()):
            return canonico
    return valor


def texto_tipo(valor):
    """El tipo de día en el idioma activo (o tal cual si no se reconoce)."""
    canonico = tipo_canonico(valor)
    return idiomas.t(_POR_CANONICO[canonico][0]) if canonico in _POR_CANONICO else valor


def clase_tipo(valor):
    canonico = tipo_canonico(valor)
    return _POR_CANONICO[canonico][1] if canonico in _POR_CANONICO else "otro"


def dias_especiales(db):
    """{fecha: forma canónica}."""
    return {f: tipo_canonico(tipo) for f, tipo in db.obtener_dias_especiales().items()}


def lista_dias(db):
    """Los días especiales para la lista de «Gestión de días», del más reciente al más antiguo: [{fecha, tipo, texto}]."""
    return [{"fecha": f, "tipo": tipo, "texto": texto_tipo(tipo)}
            for f, tipo in sorted(dias_especiales(db).items(), reverse=True)]


def opciones_tipo():
    """[(forma canónica, texto en el idioma activo)] en el orden del desplegable del PC."""
    return [(c, idiomas.t(clave)) for c, clave, _ in TIPOS]


def _fecha(valor):
    try:
        return date.fromisoformat((valor or "").strip()).isoformat()
    except (AttributeError, ValueError):
        raise ValueError("fecha_no_valida") from None


def marcar_dia(db, usuario, fecha, tipo):
    """Marca [fecha] como día especial de [tipo] (canónico o en cualquier idioma); si ya lo era, lo cambia."""
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")
    fecha = _fecha(fecha)
    tipo = tipo_canonico(tipo)
    if tipo not in _POR_CANONICO:
        raise ValueError("tipo_no_valido")
    if not db.marcar_dia_especial(fecha, tipo):
        raise ValueError("no_guardado")
    return True


def borrar_dia(db, usuario, fecha):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")
    fecha = _fecha(fecha)
    if fecha not in db.obtener_dias_especiales():
        raise ValueError("no_encontrado")
    if not db.borrar_dia_especial(fecha):
        raise ValueError("no_guardado")
    return True


# ---------------------------------------------------------------- lo que se ve

def festivos(db, anio, sede=None):
    """Los festivos oficiales de [anio] ('AAAA-MM-DD') para la empresa o [sede] (dict de nucleo/sedes)."""
    from . import festivos as _festivos
    return _festivos.fechas(db, anio, sede)


def texto_trabajo(descripcion, tags):
    """Un trabajo en la lista del día: la descripción sin las marcas de fotos ni la referencia del móvil, y sus
    etiquetas traducidas («Cambiar correa | Urgente, Mecánico»)."""
    texto = re.sub(r"\[FOTO:.*?\]", "", descripcion or "")
    texto = re.sub(r"\[FOTO_DESPUES:.*?\]", "", texto)
    texto = _RE_GALERIA.sub("", texto)
    texto = re.sub(r"\[REF:.*?\]", "", texto).strip()
    return f"{texto} | {historial.etiquetas_visibles(tags, idiomas.t)}"


def dia(db, usuario, fecha, sede=None, festivos=(), carpeta_fotos=None):
    """Lo que se ve al elegir [fecha] (AAAA-MM-DD): {titulo, clase (el color de la cabecera: festivo, vacaciones,
    puente, libre u otro, o None), lineas}. Cada línea: {tipo: aviso | trabajo | vacio, texto, y además estado y
    color (aviso), o id y foto (trabajo)}.

    Los avisos que ve [usuario] en [sede] salen el día en que se hicieron (OK) y, si no, desde el día en que tocan
    (Pendiente dentro del margen, Atrasado después), igual que la pestaña Avisos; los que van solo por contador no
    tienen fecha y no salen."""
    especial = db.obtener_dias_especiales().get(fecha)
    oficial = fecha in festivos
    partes = []
    if especial:
        partes.append(texto_tipo(especial))
    if oficial and tipo_canonico(especial) != FESTIVO_MANUAL:
        partes.append(idiomas.t("cal_festivo_oficial"))
    titulo = f"📅 {fecha}" + (f" ({' + '.join(partes)})" if partes else "")
    clase = "festivo" if oficial else (clase_tipo(especial) if especial else None)

    lineas = []
    solo_contador = contadores.ids_solo_contador()
    lista_avisos = [a for a in avisos.visibles(db.obtener_avisos(sede=sede), usuario) if a[2] and a[0] not in solo_contador]
    calculo = {f["id"]: f for f in avisos.filas(lista_avisos, {})}
    dia_fecha = date.fromisoformat(fecha)
    for a in lista_avisos:
        f = calculo[a[0]]
        if a[5] and fecha == a[5]:
            estado = "OK"
        elif dia_fecha >= f["ocurrencia"]:
            estado = "ATRASADO" if dia_fecha > f["fin"] else "PENDIENTE"
        else:
            continue
        lineas.append({"tipo": "aviso", "estado": estado, "color": COLORES_AVISO[estado],
                       "texto": idiomas.t("cal_aviso_linea").format(titulo=a[1], estado=idiomas.t(avisos.ESTADOS[estado][0]))})
    trabajos = db.obtener_tareas_por_fecha(fecha, sede=sede)
    for tid, descripcion, tags in trabajos:
        lineas.append({"tipo": "trabajo", "id": tid, "texto": texto_trabajo(descripcion, tags),
                       "foto": historial.hay_foto(descripcion, carpeta_fotos) if carpeta_fotos else False})
    if not lineas:
        lineas.append({"tipo": "vacio", "texto": idiomas.t("msg_dia_no_laborable" if partes else "msg_nada_registrado")})
    return {"titulo": titulo, "clase": clase, "lineas": lineas}


def marcas(db, festivos, desde, hasta, sede=None):
    """{fecha: clase} de los días entre [desde] y [hasta] (date) que llevan color, como el calendario del PC: los
    festivos oficiales, encima los días especiales y, encima de todo, los días con trabajos («tareas»)."""
    ini, fin = desde.isoformat(), hasta.isoformat()
    res = {f: "festivo" for f in festivos if ini <= f <= fin}
    for f, tipo in db.obtener_dias_especiales().items():
        if ini <= f <= fin:
            res[f] = clase_tipo(tipo)
    for f in db.obtener_fechas_con_tareas(sede=sede):
        if f and ini <= f <= fin:
            res[f] = "tareas"
    return res
