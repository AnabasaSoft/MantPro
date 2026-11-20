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
"""Registrar un trabajo hecho (pestaña «📝 Registrar» del PC y la misma pantalla de MantPro Web).

El trabajo va directo al historial con su fecha, título y detalles, máquina, etiquetas (con «Avería» y sus horas
de parada), fotos de antes y de después y colección, repuestos (que salen del stock) y tiempo trabajado. Aquí se
comprueba también lo que el PC ya filtra con sus desplegables y la web tiene que comprobar en el servidor: la
máquina, los artículos y la sede tienen que ser de los que ve el usuario."""

import os
import re

from . import checklists, consumos, fotos as _fotos, mano_obra, maquinas, sedes, usuarios
from .pendientes import MAX_MINUTOS, MAX_PERSONAS, _fecha, _repuestos

MAX_HORAS_PARO = 999            # como el campo de horas de parada del PC


def descripcion(titulo, detalles="", foto=None, foto_despues=None, fotos=()):
    """«título\\ndetalles\\n[FOTO: a]\\n[FOTO_DESPUES: b]\\n[FOTOS: c, d]», como la guarda el PC."""
    texto = titulo + (f"\n{detalles}" if detalles else "") + (f"\n[FOTO: {foto}]" if foto else "") \
        + (f"\n[FOTO_DESPUES: {foto_despues}]" if foto_despues else "")
    return _fotos.con_fotos_galeria(texto, list(fotos or ()))


def registrar(db, usuario, fecha, titulo, detalles="", tags="", maquina_id=None, horas_paro=None, sede=None,
              repuestos=(), minutos=None, personas=1, foto=None, foto_despues=None, fotos=()):
    """Guarda un trabajo hecho y devuelve su id. [horas_paro]: solo si es una avería (None = sin parada).
    [sede]: la elegida en el selector (id, lista o None), como al crear un pendiente; con máquina, el trabajo va a
    la sede de la máquina. ValueError con un código si algo no vale."""
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValueError("titulo_obligatorio")
    fecha = _fecha(fecha)
    permitidas = sedes.permitidas(usuario)
    if maquina_id is not None:
        if maquina_id not in {m for m, _, _ in maquinas.para_elegir(permitidas)}:
            raise ValueError("maquina_no_existe")
    if horas_paro is not None and (isinstance(horas_paro, bool) or not isinstance(horas_paro, (int, float))
                                   or not 0 <= horas_paro <= MAX_HORAS_PARO):
        raise ValueError("horas_paro_no_validas")
    if minutos is not None and (isinstance(minutos, bool) or not isinstance(minutos, int) or not 0 <= minutos <= MAX_MINUTOS):
        raise ValueError("tiempo_no_valido")
    if isinstance(personas, bool) or not isinstance(personas, int) or not 1 <= personas <= MAX_PERSONAS:
        raise ValueError("personas_no_validas")
    if isinstance(sede, int) and permitidas is not None and sede not in permitidas:
        raise ValueError("sede_no_permitida")
    items = _repuestos(repuestos, usuario)
    usuario_id = usuario["id"] if usuario else usuarios.id_actual()
    usuario_nombre = usuario["nombre"] if usuario else usuarios.nombre_actual()
    tarea_id = db.agregar_tarea(fecha, descripcion(titulo, (detalles or "").strip(), foto, foto_despues, fotos),
                                tags or "", usuario_id, usuario_nombre, maquina_id=maquina_id, horas_paro=horas_paro,
                                sede_id=sedes.para_nuevo(sede if sede is not None else permitidas, usuario))
    if not tarea_id:
        raise ValueError("no_guardado")
    # Repuestos usados: salen del stock y quedan con el trabajo y su precio
    consumos.registrar_consumo(tarea_id, items, usuario_id, usuario_nombre, titulo, fecha)
    mano_obra.fijar_tiempo(tarea_id, minutos, personas, registrar=False)
    return tarea_id


def titulos_usados(db, limite=500):
    """Los títulos de los trabajos ya registrados, para autocompletar (como el PC)."""
    return db.obtener_todas_las_descripciones()[:limite]


# ---------------------------------------------------------------- modificar lo ya registrado

MANTENER = object()                       # al editar: deja el valor que tenía
PREFIJO_PREVENTIVO = "Mantenimiento Preventivo: "     # descripción de un trabajo que viene de completar un aviso


def puede_modificar(usuario, fila):
    """Un administrador, todo; un técnico, solo sus trabajos ([fila]: obtener_tarea_por_id)."""
    u = usuario or usuarios.SESION_ACTUAL
    return usuarios.es_admin(u) or (u is not None and fila is not None and fila[4] == u.get("id"))


def _visible(db, usuario, tarea_id):
    """La fila del trabajo si es de una sede que ve [usuario]; si no (o no existe), ValueError("no_encontrado")."""
    fila = db.obtener_tarea_por_id(tarea_id)
    if not fila or not sedes.de_la_sede(sedes.sede_de("tareas", tarea_id), sedes.permitidas(usuario)):
        raise ValueError("no_encontrado")
    return fila


def _descompletar_aviso(db, fecha, descripcion):
    """Si el trabajo venía de completar un aviso recurrente, el aviso vuelve a estar sin completar ese día."""
    if not (descripcion or "").startswith(PREFIJO_PREVENTIVO):
        return
    # Solo la primera línea: detrás pueden ir los detalles y las marcas de las fotos
    titulo_aviso = descripcion.split("\n")[0].replace(PREFIJO_PREVENTIVO, "", 1).strip()
    try:
        con = db.conectar()
        try:
            aviso = con.execute("SELECT id FROM avisos_recurrentes WHERE titulo=? AND ultima_completada=?",
                                (titulo_aviso, fecha)).fetchone()
            if aviso:
                con.execute("UPDATE avisos_recurrentes SET ultima_completada=NULL WHERE id=?", (aviso[0],))
                con.commit()
        finally:
            con.close()
    except Exception as e:                    # noqa: BLE001  (como antes: el borrado sigue)
        print(f"Error intentando restaurar aviso: {e}")


def editar(db, usuario, tarea_id, fecha, texto, tags="", maquina_id=None, horas_paro=None, autor_id=MANTENER,
           repuestos=MANTENER, minutos=MANTENER, personas=1, foto=MANTENER, foto_despues=MANTENER, fotos=MANTENER):
    """Guarda los cambios de un trabajo del historial (el diálogo «Editar» del PC). [texto]: título y detalles
    (la referencia del móvil se conserva). [autor_id]: solo lo cambia un administrador (None = «Histórico»).
    [repuestos]: la lista nueva; el stock se ajusta por la diferencia (los que ya tenía valen aunque sean de un
    almacén que el usuario no ve). Fotos: MANTENER, None (quitarla) o el nombre nuevo."""
    fila = _visible(db, usuario, tarea_id)
    if not puede_modificar(usuario, fila):
        raise ValueError("solo_tus_trabajos")
    texto = (texto or "").strip()
    if not texto:
        raise ValueError("titulo_obligatorio")
    fecha = _fecha(fecha)
    permitidas = sedes.permitidas(usuario)
    if maquina_id is not None and maquina_id != fila[6] and \
            maquina_id not in {m for m, _, _ in maquinas.para_elegir(permitidas)}:
        raise ValueError("maquina_no_existe")
    if horas_paro is not None and (isinstance(horas_paro, bool) or not isinstance(horas_paro, (int, float))
                                   or not 0 <= horas_paro <= MAX_HORAS_PARO):
        raise ValueError("horas_paro_no_validas")
    if minutos is not MANTENER and minutos is not None and (isinstance(minutos, bool) or not isinstance(minutos, int)
                                                            or not 0 <= minutos <= MAX_MINUTOS):
        raise ValueError("tiempo_no_valido")
    if isinstance(personas, bool) or not isinstance(personas, int) or not 1 <= personas <= MAX_PERSONAS:
        raise ValueError("personas_no_validas")
    if autor_id is MANTENER or not usuarios.es_admin(usuario):
        autor_id, autor_nombre = fila[4], fila[5] or None
    else:
        autor = next((u for u in usuarios.listar_usuarios(incluir_inactivos=True) if u["id"] == autor_id), None)
        if autor_id is not None and autor is None:
            raise ValueError("usuario_no_existe")
        autor_nombre = autor["nombre"] if autor else usuarios.ETIQUETA_HISTORICO
    items = None
    if repuestos is not MANTENER:
        ya = {m["material_id"] for m in consumos.materiales_de_trabajo(tarea_id)}
        items = _repuestos([r for r in repuestos if r.get("material_id") not in ya], usuario) + \
            [r for r in _cantidades([r for r in repuestos if r.get("material_id") in ya])]
    original = fila[2] or ""
    m_ref = re.search(r"\[REF:\s*\d+\]", original)
    marcas = {}
    for marca, nuevo in (("FOTO", foto), ("FOTO_DESPUES", foto_despues)):
        m = re.search(rf"\[{marca}:\s*(.*?)\]", original)
        marcas[marca] = (m.group(1).split("]")[0].strip() if m else None) if nuevo is MANTENER else nuevo
    descripcion_nueva = descripcion(texto + (f" {m_ref.group(0)}" if m_ref and m_ref.group(0) not in texto else ""), "",
                                    marcas["FOTO"], marcas["FOTO_DESPUES"],
                                    _fotos.fotos_galeria(original) if fotos is MANTENER else fotos)
    guardar_editado(db, tarea_id, fecha, descripcion_nueva, tags, autor_id, autor_nombre, maquina_id, horas_paro,
                    items, minutos, personas, usuario)
    return True


def guardar_editado(db, tarea_id, fecha, descripcion_nueva, tags, autor_id, autor_nombre, maquina_id, horas_paro,
                    repuestos=None, minutos=MANTENER, personas=1, usuario=None):
    """Guarda un trabajo editado ya comprobado (lo usan editar() y el diálogo del PC, que comprueba con sus
    desplegables): los datos, el tiempo (MANTENER = no se toca) y los repuestos (None = no se tocan; si cambian,
    el stock se ajusta por la diferencia)."""
    db.actualizar_tarea(tarea_id, fecha, descripcion_nueva, tags or "", autor_id, autor_nombre, maquina_id, horas_paro)
    if minutos is not MANTENER:
        mano_obra.fijar_tiempo(tarea_id, minutos, personas)
    if repuestos is not None:
        actor = usuario or usuarios.SESION_ACTUAL or {}
        consumos.corregir_consumo(tarea_id, repuestos, actor.get("id"), actor.get("nombre") or usuarios.nombre_actual(),
                                  (descripcion_nueva or "").split("\n")[0])


def _cantidades(items):
    limpios = []
    for r in items:
        cantidad = consumos.numero(r.get("cantidad"))
        if cantidad is None or not 0 < cantidad < 1e9:
            raise ValueError("cantidad_no_valida")
        limpios.append({"material_id": r["material_id"], "cantidad": cantidad})
    return limpios


def borrar(db, usuario, ids, carpeta_fotos=None):
    """Borra los trabajos [ids] que el usuario puede modificar (los ajenos de un técnico se saltan) y devuelve
    (borrados, saltados). Los que venían de un aviso lo dejan sin completar. Con [carpeta_fotos] (el PC) se borra
    también el fichero de la foto de antes; MantPro Cloud deja que las huérfanas se limpien solas."""
    filas = [_visible(db, usuario, i) for i in ids]
    permitidas = [f for f in filas if puede_modificar(usuario, f)]
    for fila in permitidas:
        _descompletar_aviso(db, fila[1], fila[2])
        if carpeta_fotos:
            m = re.search(r"\[FOTO:\s*(.*?)\]", fila[2] or "")
            ruta = _fotos.ruta_en(carpeta_fotos, m.group(1).split("]")[0].strip()) if m else None
            if ruta and os.path.exists(ruta):
                try:
                    os.remove(ruta)
                except OSError:
                    pass
        db.borrar_tarea(fila[0])
    return len(permitidas), len(filas) - len(permitidas)


def revertir(db, usuario, tarea_id):
    """Deshace la finalización de un trabajo: sale del historial y vuelve a Pendientes (con su técnico, su sede y,
    si su plantilla sigue existiendo, su lista de comprobación). Devuelve el id del pendiente nuevo."""
    fila = _visible(db, usuario, tarea_id)
    if not puede_modificar(usuario, fila):
        raise ValueError("solo_tus_trabajos")
    tid, fecha, desc = fila[0], fila[1], fila[2] or ""
    uid_original, nombre_original = fila[4], fila[5] or ""
    _descompletar_aviso(db, fecha, desc)
    lineas = desc.split("\n")
    titulo, detalles = lineas[0].strip(), "\n".join(lineas[1:]).strip()
    lista_previa = checklists.resultado_de(tid)
    nuevo = db.agregar_pendiente(titulo, detalles, uid_original, nombre_original or None,
                                 sede_id=sedes.sede_de("tareas", tid))
    if not nuevo:
        raise ValueError("no_guardado")
    con = db.conectar()
    try:
        con.execute("DELETE FROM tareas WHERE id=?", (tid,))
        con.execute("DELETE FROM checklist_resultados WHERE tarea_id=?", (tid,))
        con.commit()
    finally:
        con.close()
    consumos.olvidar_trabajo(tid)
    if lista_previa:
        plantilla = next((p for p in checklists.listar_plantillas() if p["nombre"] == lista_previa["plantilla"]), None)
        if plantilla:
            checklists.asignar("pendiente", nuevo, plantilla["id"])
    actor = usuario or usuarios.SESION_ACTUAL or {}
    usuarios.registrar_auditoria(actor.get("id"), tid, "revertir",
                                 f"Registro del {fecha}: {titulo[:80]} (autor original: {nombre_original or usuarios.ETIQUETA_HISTORICO})")
    return nuevo


def reasignar_autor(db, usuario, ids, autor_id, progreso=None):
    """Cambia quién hizo los trabajos [ids] (solo administradores; None = «Histórico»). Devuelve cuántos han
    cambiado. [progreso](hechos, total): para la barra del PC."""
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")
    for i in ids:
        _visible(db, usuario, i)
    autor = next((u for u in usuarios.listar_usuarios(incluir_inactivos=True) if u["id"] == autor_id), None)
    if autor_id is not None and autor is None:
        raise ValueError("usuario_no_existe")
    nombre = autor["nombre"] if autor else usuarios.ETIQUETA_HISTORICO
    auditorias = []
    con = db.conectar()
    try:
        for n, tarea_id in enumerate(ids, 1):
            fila = con.execute("SELECT COALESCE(usuario_nombre,'') FROM tareas WHERE id=?", (tarea_id,)).fetchone()
            anterior = fila[0] if fila and fila[0] else usuarios.ETIQUETA_HISTORICO
            if anterior != nombre:
                con.execute("UPDATE tareas SET usuario_id=?, usuario_nombre=? WHERE id=?", (autor_id, nombre, tarea_id))
                auditorias.append((tarea_id, f"autor: {anterior} → {nombre}"))
            if progreso:
                progreso(n, len(ids))
        con.commit()
    finally:
        con.close()
    actor = usuario or usuarios.SESION_ACTUAL or {}
    for tarea_id, detalle in auditorias:        # después de cerrar la conexión (evita bloqueos de SQLite)
        usuarios.registrar_auditoria(actor.get("id"), tarea_id, "editar", detalle)
    return len(auditorias)
