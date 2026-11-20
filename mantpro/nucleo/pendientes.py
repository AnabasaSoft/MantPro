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

"""Trabajos pendientes (sin Qt): listar, crear, editar, borrar y reasignar. Lo usan la pestaña Pendientes del PC
y MantPro Web, para que hagan exactamente lo mismo.

En el PC los desplegables solo ofrecen lo que existe; en la web llega lo que mande el navegador. Por eso aquí se
comprueba todo: que existan el usuario, la especialidad, la lista y la sede, que el usuario vea la sede del
pendiente (un técnico con sedes marcadas no toca las demás) y que solo un administrador cambie la asignación de
un pendiente que ya existe. Los errores son códigos (ValueError), nunca texto.

La descripción guarda marcas que no se enseñan: [REF:n] (la del móvil), [FOTO: x], [FOTO_DESPUES: y] y la colección
[FOTOS: a, b]; al editar se conservan."""

import os
import re
from datetime import datetime

from .. import idiomas
from . import checklists, consumos, fotos as _fotos, mano_obra, sedes, usuarios

PRIORIDADES = ("Baja", "Media", "Alta", "Crítica")          # en el orden de los desplegables
_ORDEN = {"Crítica": 0, "Alta": 1, "Media": 2, "Baja": 3}
ICONOS = {"Crítica": "🔴", "Alta": "🟠", "Media": "⬜", "Baja": "🟢"}
CLAVES_PRIORIDAD = {"Baja": "prioridad_baja", "Media": "prioridad_media", "Alta": "prioridad_alta",
                    "Crítica": "prioridad_critica"}
TODOS = "TODOS"            # filtro «Ver los de: Todos» (None es «Sin asignar»)
MANTENER = object()        # al editar o reasignar: deja el valor que tenía


def hay_foto(descripcion, carpeta_fotos):
    """True si la foto de antes (o, si no está, la de después) de [descripcion] existe en [carpeta_fotos]."""
    for marca in (r"\[FOTO:\s*(.*?)\]", r"\[FOTO_DESPUES:\s*(.*?)\]"):
        m = re.search(marca, descripcion or "")
        if m:
            nombre = m.group(1).split("]")[0].strip()
            if nombre and carpeta_fotos and os.path.exists(os.path.join(carpeta_fotos, nombre)):
                return True
    return False


def detalles_visibles(descripcion):
    """La descripción sin las marcas de fotos ni la referencia del móvil."""
    texto = re.sub(r"\[FOTO.*?:.*?\]", "", descripcion or "")
    return re.sub(r"\[REF:.*?\]", "", texto).strip()


def lista(db, sede=None, asignado=TODOS, carpeta_fotos=None):
    """Pendientes de [sede] (id, lista de ids o None = todas) ordenados por prioridad, como los enseña el PC.
    [asignado]: TODOS, None (sin asignar) o el id de un usuario. Cada uno es un dict con id, titulo, detalles
    (sin marcas), descripcion (con ellas), asignado_id, asignado_nombre, prioridad, especialidad_id, tiene_foto,
    lista (nombre de su lista de comprobación o None) y a_medias ((hechos, total) o None)."""
    filas = db.obtener_pendientes(sede=sede)
    if asignado != TODOS:
        filas = [f for f in filas if f[3] == asignado]
    filas = sorted(filas, key=lambda f: _ORDEN.get(f[5], 2))
    con_lista = checklists.checklists_de("pendiente")
    a_medias = checklists.resumen_borradores("pendiente")
    plantillas = {pl["id"]: pl["nombre"] for pl in checklists.listar_plantillas()}
    resultado = []
    for pid, titulo, desc, asig_id, asig_nombre, prioridad, especialidad_id in filas:
        nombre_lista = plantillas.get(con_lista.get(pid))
        resultado.append({"id": pid, "titulo": titulo, "detalles": detalles_visibles(desc), "descripcion": desc or "",
                          "asignado_id": asig_id, "asignado_nombre": asig_nombre or "", "prioridad": prioridad,
                          "especialidad_id": especialidad_id, "tiene_foto": hay_foto(desc, carpeta_fotos),
                          "lista": nombre_lista, "a_medias": a_medias.get(pid) if nombre_lista else None})
    return resultado


def texto(fila):
    """El texto de un pendiente en la lista del PC (varias líneas), en el idioma activo."""
    t = idiomas.t
    linea = f"{ICONOS.get(fila['prioridad'], '⬜')} {fila['titulo']}"
    if fila["prioridad"] in ("Crítica", "Alta"):
        linea += f"  [{t(CLAVES_PRIORIDAD[fila['prioridad']])}]"
    if fila["detalles"]:
        linea += f"\n   ↳ {fila['detalles']}"
    if fila["tiene_foto"]:
        linea += "  (📸 Foto)"
    if fila["asignado_nombre"]:
        linea += f"\n   👤 {fila['asignado_nombre']}"
    if fila["lista"]:
        linea += f"\n   ☑️ {fila['lista']}"
        if fila["a_medias"]:
            linea += "  " + t("chk_borrador_lista").format(hechos=f"{fila['a_medias'][0]}/{fila['a_medias'][1]}")
    return linea


# ---------------------------------------------------------------- comprobaciones

def _usuario_asignable(usuario_id):
    """(id, nombre) de un usuario activo, o (None, None) para «Sin asignar». El nombre sale de la base."""
    if usuario_id is None:
        return None, None
    u = next((x for x in usuarios.listar_usuarios(incluir_inactivos=False) if x["id"] == usuario_id), None)
    if u is None:
        raise ValueError("usuario_no_existe")
    return u["id"], u["nombre"]


def _especialidad(especialidad_id):
    if especialidad_id is not None and especialidad_id not in {e["id"] for e in usuarios.listar_especialidades()}:
        raise ValueError("especialidad_no_existe")
    return especialidad_id


def _lista(checklist_id):
    if checklist_id and checklist_id not in {pl["id"] for pl in checklists.listar_plantillas()}:
        raise ValueError("lista_no_existe")
    return checklist_id or None


def _prioridad(prioridad):
    if prioridad not in PRIORIDADES:
        raise ValueError("prioridad_no_valida")
    return prioridad


def _accesibles(db, usuario, ids):
    """Las filas de [ids] si [usuario] puede verlas todas (las de las sedes que ve); si no, ValueError."""
    vistas = {f[0]: f for f in db.obtener_pendientes(sede=sedes.permitidas(usuario))}
    if not ids or any(i not in vistas for i in ids):
        raise ValueError("no_encontrado")
    return [vistas[i] for i in ids]


# ---------------------------------------------------------------- escribir

def crear(db, usuario, titulo, detalles, asignado_id=None, prioridad="Media", especialidad_id=None,
          checklist_id=None, sede=None):
    """Da de alta un pendiente y devuelve su id. [sede]: la elegida en el selector (id, lista o None); el
    pendiente va a esa sede o, con varias, a la principal si el usuario la ve (como en el PC)."""
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValueError("titulo_obligatorio")
    asignado_id, asignado_nombre = _usuario_asignable(asignado_id)
    prioridad, especialidad_id = _prioridad(prioridad), _especialidad(especialidad_id)
    checklist_id = _lista(checklist_id)
    permitidas = sedes.permitidas(usuario)
    if isinstance(sede, int) and permitidas is not None and sede not in permitidas:
        raise ValueError("sede_no_permitida")
    nuevo = db.agregar_pendiente(titulo, (detalles or "").strip(), asignado_id, asignado_nombre, prioridad,
                                 especialidad_id, sede_id=sedes.para_nuevo(sede if sede is not None else permitidas, usuario))
    if not nuevo:
        raise ValueError("no_guardado")
    if checklist_id:
        checklists.asignar("pendiente", nuevo, checklist_id)
    return nuevo


def descripcion_editada(original, detalles, foto=MANTENER, fotos=MANTENER, carpeta_fotos=None):
    """La descripción nueva de un pendiente editado: el texto escrito más las marcas que no se ven, que se
    conservan (la referencia del móvil, la foto de después). [foto]: MANTENER (la que tenía, si el fichero existe),
    None (quitarla) o el nombre de la nueva. [fotos]: MANTENER o la lista de la colección."""
    original = original or ""
    texto_final = (detalles or "").strip()
    m_ref = re.search(r"\[REF:\s*(\d+)\]", original)
    if m_ref:
        texto_final += f" {m_ref.group(0)}"
    if foto is MANTENER:
        m = re.search(r"\[FOTO:\s*(.*?)\]", original)
        nombre = m.group(1).split("]")[0].strip() if m else ""
        foto = nombre if nombre and (carpeta_fotos is None or os.path.exists(os.path.join(carpeta_fotos, nombre))) else None
    if foto:
        texto_final += f"\n[FOTO: {foto}]"
    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", original)
    if m_d:
        texto_final += f"\n[FOTO_DESPUES: {m_d.group(1).strip()}]"
    return _fotos.con_fotos_galeria(texto_final, _fotos.fotos_galeria(original) if fotos is MANTENER else fotos)


def editar(db, usuario, pendiente_id, titulo, detalles, prioridad="Media", asignado_id=MANTENER,
           especialidad_id=MANTENER, checklist_id=MANTENER, sede_id=None, foto=MANTENER, fotos=MANTENER,
           carpeta_fotos=None):
    """Guarda los cambios de un pendiente. La asignación y la especialidad de un pendiente que ya existe solo
    las cambia un administrador (un técnico las fija al crearlo). [sede_id]: la sede nueva (None = no cambia)."""
    fila = _accesibles(db, usuario, [pendiente_id])[0]
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValueError("titulo_obligatorio")
    prioridad = _prioridad(prioridad)
    admin = usuarios.es_admin(usuario)
    if not admin or especialidad_id is MANTENER:
        especialidad_id = fila[6]
    especialidad_id = _especialidad(especialidad_id)
    asignar = admin and asignado_id is not MANTENER
    if asignar:
        asignado_id, asignado_nombre = _usuario_asignable(asignado_id)
    if checklist_id is not MANTENER:
        checklist_id = _lista(checklist_id)
    if sede_id is not None and sede_id not in {s["id"] for s in sedes.visibles(usuario)}:
        raise ValueError("sede_no_permitida")
    descripcion = descripcion_editada(fila[2], detalles, foto, fotos, carpeta_fotos)
    if not db.actualizar_pendiente(pendiente_id, titulo, descripcion, prioridad, especialidad_id):
        raise ValueError("no_guardado")
    if checklist_id is not MANTENER:
        checklists.asignar("pendiente", pendiente_id, checklist_id)
    if sede_id is not None:
        sedes.poner_sede("pendientes", pendiente_id, sede_id)
    if asignar:
        db.asignar_pendiente(pendiente_id, asignado_id, asignado_nombre)
    return True


def borrar(db, usuario, ids):
    """Borra los pendientes [ids] (todos o ninguno, si alguno no lo ve). Devuelve cuántos."""
    _accesibles(db, usuario, list(ids))
    return sum(1 for i in ids if db.borrar_pendiente(i))


def reasignar(db, usuario, ids, asignado_id=MANTENER, especialidad_id=MANTENER):
    """Cambia el técnico y/o la especialidad de varios pendientes (solo administradores). Lo que se deja en
    MANTENER no se toca. Devuelve cuántos."""
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")
    _accesibles(db, usuario, list(ids))
    if asignado_id is not MANTENER:
        asignado_id, asignado_nombre = _usuario_asignable(asignado_id)
    if especialidad_id is not MANTENER:
        especialidad_id = _especialidad(especialidad_id)
    for i in ids:
        if asignado_id is not MANTENER:
            db.asignar_pendiente(i, asignado_id, asignado_nombre)
        if especialidad_id is not MANTENER:
            db.asignar_especialidad_pendiente(i, especialidad_id)
    return len(ids)


# ---------------------------------------------------------------- completar

# Etiquetas rápidas al completar: (lo que se guarda, clave del texto), en el orden en que se guardan
ETIQUETAS_RAPIDAS = (("Urgente", "tag_urgente"), ("Eléctrico", "tag_electrico"),
                     ("Mecánico", "tag_mecanico"), ("Preventivo", "tag_preventivo"))
# Al registrar un trabajo también se puede marcar «Avería» (con sus horas de parada), siempre la última
ETIQUETAS_REGISTRAR = ETIQUETAS_RAPIDAS + (("Avería", "tag_averia"),)
MAX_PERSONAS = 50                 # como el campo de personas del PC
MAX_MINUTOS = 60 * 24 * 366


def etiquetas(rapidas=(), otras="", opciones=ETIQUETAS_RAPIDAS):
    """El texto de etiquetas de un trabajo: las rápidas marcadas (de [opciones]), en su orden de siempre, y las
    escritas a mano."""
    marcadas = set(rapidas or ())
    lista = [valor for valor, _ in opciones if valor in marcadas]
    otras = (otras or "").strip()
    if otras:
        lista.append(otras)
    return ", ".join(lista)


def _fecha(fecha):
    try:
        dia = datetime.strptime((fecha or "").strip(), "%Y-%m-%d")
    except ValueError:
        raise ValueError("fecha_no_valida") from None
    if not 2000 <= dia.year <= 2100:
        raise ValueError("fecha_no_valida")
    return dia.strftime("%Y-%m-%d")


def _repuestos(repuestos, usuario):
    """Los repuestos usados, comprobados: artículos de los almacenes que ve el usuario y cantidades mayores que cero."""
    items = [r for r in (repuestos or []) if r.get("material_id") is not None]
    if not items:
        return []
    elegibles = {m["id"] for m in consumos.materiales_elegibles(sedes.permitidas(usuario))}
    limpios = []
    for r in items:
        if r["material_id"] not in elegibles:
            raise ValueError("material_no_existe")
        cantidad = consumos.numero(r.get("cantidad"))
        if cantidad is None or not 0 < cantidad < 1e9:
            raise ValueError("cantidad_no_valida")
        limpios.append({"material_id": r["material_id"], "cantidad": cantidad})
    return limpios


def lista_pendiente(pendiente_id):
    """La plantilla de la lista de comprobación que hay que rellenar al completar el pendiente, o None."""
    plantilla_id = checklists.checklist_de("pendiente", pendiente_id)
    plantilla = checklists.obtener_plantilla(plantilla_id) if plantilla_id else None
    return plantilla if plantilla and plantilla["puntos"] else None


def _tolerante(fecha, minutos, personas, repuestos):
    """Lo que llega de la cola de un móvil no se rechaza (se quedaría atascado reintentándose para siempre):
    una fecha que no vale es hoy, el tiempo y las personas se recortan y los repuestos se pasan tal cual
    (registrar_consumo se salta los artículos que ya no existen)."""
    try:
        fecha = _fecha(fecha)
    except ValueError:
        fecha = datetime.now().strftime("%Y-%m-%d")
    if isinstance(minutos, bool) or not isinstance(minutos, int) or not 0 < minutos <= MAX_MINUTOS:
        minutos = None
    personas = personas if isinstance(personas, int) and not isinstance(personas, bool) else 1
    personas = min(max(personas, 1), MAX_PERSONAS)
    items = [r for r in (repuestos or []) if isinstance(r, dict) and r.get("material_id") is not None]
    return fecha, minutos, personas, items


def completar(db, usuario, pendiente_id, fecha, tags="", repuestos=(), minutos=None, personas=1, lista=None,
              foto=None, fotos=MANTENER, foto_despues=None, texto=None, estricto=True):
    """Pasa un pendiente al historial (lo que hace «✅ Completar» en el PC, en MantPro Web y en la app MantPro)
    y devuelve el id del trabajo nuevo.
    [fecha]: AAAA-MM-DD. [repuestos]: [{material_id, cantidad}], que se descuentan del stock. [minutos] y
    [personas]: tiempo trabajado (None = sin tiempo). [lista]: (items, nombre de la plantilla) de la lista de
    comprobación rellenada; obligatoria si el pendiente tiene una. [foto] y [foto_despues]: nombres de fotos nuevas,
    que sustituyen a las que tenía (None = las de siempre). [fotos]: la colección (MANTENER = la que traía).
    [texto]: (título, detalles) escritos al completar (la app deja cambiarlos; los detalles ya traen la referencia
    y la colección); None = los del pendiente. [estricto]=False: lo que llega de la cola de un móvil (ver
    _tolerante; la lista tampoco es obligatoria)."""
    fila = _accesibles(db, usuario, [pendiente_id])[0]
    if estricto:
        fecha = _fecha(fecha)
        if minutos is not None and (isinstance(minutos, bool) or not isinstance(minutos, int) or not 0 <= minutos <= MAX_MINUTOS):
            raise ValueError("tiempo_no_valido")
        if isinstance(personas, bool) or not isinstance(personas, int) or not 1 <= personas <= MAX_PERSONAS:
            raise ValueError("personas_no_validas")
        items = _repuestos(repuestos, usuario)
        if lista_pendiente(pendiente_id) is not None and not (lista and lista[0]):
            raise ValueError("lista_sin_rellenar")
    else:
        fecha, minutos, personas, items = _tolerante(fecha, minutos, personas, repuestos)
    if texto is None:
        titulo, detalles = fila[1], fila[2] or ""
        if foto:            # la foto nueva sustituye a la anterior (con su salto de línea)
            detalles = re.sub(r"\n?\[FOTO:.*?\]", "", detalles).strip()
        if foto_despues:
            detalles = re.sub(r"\n?\[FOTO_DESPUES:.*?\]", "", detalles).strip()
    else:
        titulo, detalles = texto[0] or fila[1], texto[1] or ""
    descripcion = (titulo + (f"\n{detalles}" if detalles else "") + (f"\n[FOTO: {foto}]" if foto else "")
                   + (f"\n[FOTO_DESPUES: {foto_despues}]" if foto_despues else ""))
    descripcion = _fotos.con_fotos_galeria(descripcion, _fotos.fotos_galeria(detalles) if fotos is MANTENER else fotos)
    usuario_id = usuario["id"] if usuario else usuarios.id_actual()
    usuario_nombre = usuario["nombre"] if usuario else usuarios.nombre_actual()
    tarea_id = db.agregar_tarea(fecha, descripcion, tags or "", usuario_id, usuario_nombre,
                                sede_id=sedes.sede_de("pendientes", pendiente_id))
    if not tarea_id:
        raise ValueError("no_guardado")
    consumos.registrar_consumo(tarea_id, items, usuario_id, usuario_nombre, titulo, fecha)
    mano_obra.fijar_tiempo(tarea_id, minutos, personas, registrar=False)
    detalle = ""
    if lista and lista[0]:
        checklists.guardar_resultado(tarea_id, lista[0], lista[1])
        detalle = f"Lista de comprobación: {lista[1]} — " + ", ".join(
            f"{v} {k}" for k, v in checklists.recuento(checklists.normalizar_items(lista[0])).items() if v)
    checklists.borrar_borrador(checklists.clave_borrador("pendiente", pendiente_id))   # ya no hay lista a medias
    db.borrar_pendiente(pendiente_id, motivo="completar", detalle=detalle)
    return tarea_id
