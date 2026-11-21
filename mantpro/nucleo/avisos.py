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

"""Avisos recurrentes (sin Qt): qué avisos ve cada usuario, cuáles tocan hoy, la tabla de la pestaña y crear,
editar, borrar y reasignar.

Lo usan la pestaña Avisos y el Dashboard del PC y MantPro Web, para que todos cuenten y hagan igual. En el PC los
desplegables solo ofrecen lo que existe; en la web llega lo que mande el navegador: aquí se comprueba todo y los
errores son códigos (ValueError), nunca texto.
Cada aviso es una fila de GestorBaseDatos.obtener_avisos:
(id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, asignado_a, asignado_nombre, especialidad_id)."""

from datetime import date, timedelta

from .. import idiomas
from . import checklists, consumos, contadores, frecuencias, mano_obra, pendientes, sedes, usuarios


def visibles(avisos, usuario):
    """Igual que en el móvil: el administrador ve todos los avisos; cada trabajador ve los suyos más los que
    no están asignados a nadie (y, si no lo están, coinciden con alguna de sus especialidades o no tienen
    ninguna), pero no los asignados a otro técnico ni los de una especialidad que no tiene.
    [usuario]: dict de sesión (el del PC o el de la petición web)."""
    if usuarios.es_admin(usuario):
        return list(avisos)
    uid = (usuario or {}).get("id")
    especialidades = (usuario or {}).get("especialidad_ids") or []
    return [a for a in avisos if a[6] == uid or (a[6] is None and (a[8] is None or a[8] in especialidades))]


def pendientes_hoy(avisos, por_contador, hoy=None):
    """Cuántos de [avisos] tocan hoy y no están hechos (la tarjeta «Avisos pendientes» del Dashboard).
    [por_contador]: contadores.estados_avisos(). Un aviso por contador cuenta si toca por contador (y no se ha
    hecho hoy); si además tiene fecha, también si toca por fecha. Por fecha: la ocurrencia de hoy y los días de
    margen siguientes, salvo los diarios, que no usan margen (el de ayer no cuenta como hecho hoy)."""
    hoy = hoy or date.today()
    hoy_iso = hoy.isoformat()
    total = 0
    for aid, _titulo, finicio, freq, dur, ult, *_ in avisos:
        info = por_contador.get(aid)
        if info and ult != hoy_iso and info["estado"] in ("PENDIENTE", "ATRASADO"):
            total += 1
            continue
        if info and info["solo_contador"]:
            continue
        if not finicio:
            continue
        try:
            ocurrencia = date.fromisoformat(finicio)
        except (TypeError, ValueError):
            continue
        freq = idiomas.normalizar_frecuencia(freq or "Anual")
        margen = timedelta(days=0 if freq == "Diario" else int(dur or 0))
        while ocurrencia + margen < hoy:
            siguiente = frecuencias.avanzar(ocurrencia, freq)
            if siguiente <= ocurrencia:           # frecuencia desconocida: no avanza
                break
            ocurrencia = siguiente
        if ocurrencia <= hoy <= ocurrencia + margen and ult != ocurrencia.isoformat():
            total += 1
    return total


# ---------------------------------------------------------------- la tabla de la pestaña

MANTENER = object()        # al editar o reasignar: deja el valor que tenía
# Estado -> (clave del texto, color, orden: lo más urgente primero)
ESTADOS = {"ATRASADO": ("estado_atrasado", "#cb4335", 0), "PENDIENTE": ("estado_pendiente", "#e67e22", 1),
           "FUTURO": ("estado_futuro", "#2e86c1", 2), "OK": ("estado_ok", "#27ae60", 3)}
MARGEN_MAXIMO = 365


def _iso(texto, por_defecto):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return por_defecto


def filas(avisos, por_contador, hoy=None):
    """Las filas de la tabla de la pestaña Avisos (PC y MantPro Web), ya ordenadas: atrasados, pendientes, futuros y
    hechos hoy; dentro de cada grupo, por fecha. [avisos]: filas de obtener_avisos (ya filtradas con visibles);
    [por_contador]: contadores.estados_avisos().

    La próxima vez se cuenta desde la ÚLTIMA VEZ QUE SE HIZO DE VERDAD, no desde el calendario fijo: si te retrasas,
    el aviso sigue «Pendiente» hasta que lo haces, y el siguiente se cuenta desde ese día. Está «Pendiente» dentro
    del margen y «Atrasado» pasado el margen; un diario no tiene margen. Solo cuenta como hecho («OK») si se hizo hoy.
    Por contador: toca lo que antes llegue (fecha o contador), o solo el contador si no tiene límite por fecha.

    Cada fila: id, titulo, frecuencia (canónica), ocurrencia y fin (date: la ventana por fecha), orden (date para
    ordenar), estado (clave de ESTADOS), completado, activo (se puede marcar), texto_frecuencia, rango (texto),
    consejo (texto del contador, o ""), contador (info o None), asignado_a, asignado_nombre, especialidad_id."""
    hoy = hoy or date.today()
    hoy_iso = hoy.isoformat()
    fmt = idiomas.formato_fecha_corta_py()
    resultado = []
    for aid, titulo, finicio, freq, dur, ult, asignado_a, asignado_nombre, especialidad_id in avisos:
        freq = idiomas.normalizar_frecuencia(freq or "Anual")
        inicio = _iso(finicio, date(hoy.year, 1, 1))
        ventana = timedelta(days=0 if freq == frecuencias.DIARIO else int(dur or 0))
        if ult:
            fecha_ult = _iso(ult, None)
            ocurrencia = frecuencias.avanzar(fecha_ult, freq) if fecha_ult else inicio
        else:
            ocurrencia = inicio
        fin = ocurrencia + ventana
        completado = ult == hoy_iso
        activo = hoy >= ocurrencia
        estado = "ATRASADO" if hoy > fin else ("PENDIENTE" if activo else "FUTURO")
        orden = ocurrencia
        rango = f"{ocurrencia.strftime(fmt)} - {fin.strftime(fmt)}"
        texto_frecuencia, consejo = frecuencias.texto(freq), ""
        info = por_contador.get(aid)
        if info:
            if info["solo_contador"]:
                estado = info["estado"]
                if estado == "FUTURO":
                    orden = _iso(info["estimada"], None) or frecuencias.avanzar(hoy, "Cada 5 años")
                else:
                    orden = hoy
            else:
                estado = contadores.peor(estado, info["estado"])
            activo = estado in ("PENDIENTE", "ATRASADO")
            texto_cada = contadores.texto_cada(info, idiomas.t("lbl_cada_corto"))
            texto_frecuencia = texto_cada if info["solo_contador"] else f"{texto_cada} · {frecuencias.texto(freq)}"
            texto_c = contadores.texto_proximo(info, idiomas.t("lbl_ahora"), idiomas.t("lbl_sin_lecturas"))
            rango = texto_c if info["solo_contador"] else f"{texto_c} · {rango}"
            consejo = f"📟 {info['contador']} — {info['maquina']}"
            if info["estimada"]:
                consejo += "\n" + idiomas.t("lbl_estimada").format(fecha=_iso(info["estimada"], hoy).strftime(fmt))
        if completado:
            estado = "OK"
        resultado.append({"id": aid, "titulo": titulo, "frecuencia": freq, "ocurrencia": ocurrencia, "fin": fin,
                          "orden": orden, "estado": estado, "completado": completado, "activo": activo,
                          "texto_frecuencia": texto_frecuencia, "rango": rango, "consejo": consejo, "contador": info,
                          "asignado_a": asignado_a, "asignado_nombre": asignado_nombre or "",
                          "especialidad_id": especialidad_id})
    resultado.sort(key=lambda f: (ESTADOS[f["estado"]][2], f["orden"]))
    return resultado


def lista(db, usuario, sede=None, hoy=None):
    """Los avisos que ve [usuario] en [sede] (id, lista o None = todas), como filas() más la lista de comprobación:
    lista_id, lista (nombre de la plantilla) y a_medias ((hechos, total) si está empezada, o None)."""
    con_lista = checklists.checklists_de("aviso")
    a_medias = checklists.resumen_borradores("aviso")
    plantillas = {pl["id"]: pl["nombre"] for pl in checklists.listar_plantillas()}
    res = filas(visibles(db.obtener_avisos(sede=sede), usuario), contadores.estados_avisos(), hoy)
    for f in res:
        f["lista_id"] = con_lista.get(f["id"])
        f["lista"] = plantillas.get(f["lista_id"], "") if f["lista_id"] else ""
        f["a_medias"] = tuple(a_medias[f["id"]][:2]) if f["lista_id"] and f["id"] in a_medias else None
    return res


def titulo_en_tabla(fila):
    """El título como sale en la tabla: «☑️ » si tiene lista y «📝 hechos/total» si está a medias."""
    texto = ("☑️ " if fila["lista_id"] else "") + fila["titulo"]
    if fila["a_medias"]:
        texto += f"  📝 {fila['a_medias'][0]}/{fila['a_medias'][1]}"
    return texto


# ---------------------------------------------------------------- comprobaciones

def _solo_admin(usuario):
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def _fecha(valor):
    try:
        return date.fromisoformat((valor or "").strip()).isoformat()
    except (AttributeError, ValueError):
        raise ValueError("fecha_no_valida") from None


def _frecuencia(valor):
    if not valor or not frecuencias.conocida(valor):
        raise ValueError("frecuencia_no_valida")
    return frecuencias.canonica(valor)


def _margen(valor):
    if isinstance(valor, bool) or not isinstance(valor, int) or not 1 <= valor <= MARGEN_MAXIMO:
        raise ValueError("margen_no_valido")
    return valor


def contador_config(contador_id, cada, antelacion="", primera="", con_fecha=True):
    """La configuración de un preventivo por contador a partir de lo escrito en el formulario (lo que hace el grupo
    «📟 Por contador» del PC): «Cada» es obligatorio y mayor que cero; «Avisar antes» y «Primera vez a», números si
    se escriben. Sin «Primera vez a»: la lectura actual del contador más «Cada». ValueError con el código si no vale."""
    contador = next((c for c in contadores.listar_contadores() if c["id"] == contador_id), None) \
        if contador_id is not None else None
    if contador is None:
        raise ValueError("contador_no_existe")
    n_cada = contadores.numero(cada)
    if n_cada is None or n_cada <= 0:
        raise ValueError("cada_no_valido")
    for texto in (antelacion, primera):
        if (texto or "").strip() and contadores.numero(texto) is None:
            raise ValueError("lectura_no_valida")
    n_primera = contadores.numero(primera)
    if n_primera is None:
        n_primera = (contador["actual"] or 0) + n_cada
    return {"contador_id": contador["id"], "cada": n_cada, "antelacion": contadores.numero(antelacion) or 0,
            "primera": n_primera, "solo_contador": not con_fecha}


def _contador(config):
    """Una configuración de contador ya hecha (la del PC): que el contador exista y «Cada» sea mayor que cero."""
    if not config:
        return None
    if config.get("contador_id") not in {c["id"] for c in contadores.listar_contadores()}:
        raise ValueError("contador_no_existe")
    if (contadores.numero(config.get("cada")) or 0) <= 0:
        raise ValueError("cada_no_valido")
    return config


def _accesibles(db, usuario, ids):
    """Las filas de [ids] si [usuario] puede verlas todas (las de las sedes que ve y, si es técnico, las suyas o sin
    asignar de sus especialidades); si no, ValueError("no_encontrado")."""
    vistos = {a[0]: a for a in visibles(db.obtener_avisos(sede=sedes.permitidas(usuario)), usuario)}
    if not ids or any(i not in vistos for i in ids):
        raise ValueError("no_encontrado")
    return [vistos[i] for i in ids]


# ---------------------------------------------------------------- escribir (solo administradores)

def crear(db, usuario, titulo, inicio, frecuencia, margen, asignado_id=None, especialidad_id=None, checklist_id=None,
          contador=None, sede=None):
    """Da de alta un aviso recurrente y devuelve su id. [contador]: configuración del preventivo por contador (ver
    contador_config) o None. [sede]: la elegida en el selector (id, lista o None); con varias, la principal si se
    ve (como en el PC)."""
    _solo_admin(usuario)
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValueError("titulo_obligatorio")
    inicio, frecuencia, margen = _fecha(inicio), _frecuencia(frecuencia), _margen(margen)
    asignado_id, asignado_nombre = pendientes._usuario_asignable(asignado_id)
    especialidad_id = pendientes._especialidad(especialidad_id)
    checklist_id = pendientes._lista(checklist_id)
    contador = _contador(contador)
    permitidas = sedes.permitidas(usuario)
    if isinstance(sede, int) and permitidas is not None and sede not in permitidas:
        raise ValueError("sede_no_permitida")
    nuevo = db.agregar_aviso(titulo, inicio, frecuencia, margen, asignado_id, asignado_nombre, especialidad_id,
                             contador=contador,
                             sede_id=sedes.para_nuevo(sede if sede is not None else permitidas, usuario))
    if not nuevo:
        raise ValueError("no_guardado")
    if checklist_id:
        checklists.asignar("aviso", nuevo, checklist_id)
    return nuevo


def editar(db, usuario, aviso_id, titulo, inicio, frecuencia, margen, asignado_id=None, especialidad_id=None,
           checklist_id=MANTENER, contador=MANTENER, sede_id=None):
    """Guarda los cambios de un aviso (el diálogo «Editar» del PC). [contador]: MANTENER, None (solo por fecha) o
    la configuración nueva. [sede_id]: la sede nueva (None = no cambia)."""
    _solo_admin(usuario)
    _accesibles(db, usuario, [aviso_id])
    titulo = (titulo or "").strip()
    if not titulo:
        raise ValueError("titulo_obligatorio")
    inicio, frecuencia, margen = _fecha(inicio), _frecuencia(frecuencia), _margen(margen)
    asignado_id, asignado_nombre = pendientes._usuario_asignable(asignado_id)
    especialidad_id = pendientes._especialidad(especialidad_id)
    if checklist_id is not MANTENER:
        checklist_id = pendientes._lista(checklist_id)
    contador = False if contador is MANTENER else _contador(contador)
    if sede_id is not None and sede_id not in {s["id"] for s in sedes.visibles(usuario)}:
        raise ValueError("sede_no_permitida")
    if not db.actualizar_aviso(aviso_id, titulo, inicio, frecuencia, margen, asignado_id, asignado_nombre,
                               especialidad_id, contador=contador):
        raise ValueError("no_guardado")
    if checklist_id is not MANTENER:
        checklists.asignar("aviso", aviso_id, checklist_id)
    if sede_id is not None:
        sedes.poner_sede("avisos_recurrentes", aviso_id, sede_id)
    return True


def borrar(db, usuario, ids):
    """Borra los avisos [ids] (todos o ninguno, si alguno no lo ve). Devuelve cuántos."""
    _solo_admin(usuario)
    _accesibles(db, usuario, list(ids))
    return sum(1 for i in ids if db.borrar_aviso(i))


def reasignar(db, usuario, ids, asignado_id=MANTENER, especialidad_id=MANTENER):
    """Cambia el técnico y/o la especialidad de varios avisos (el «👤 Asignar a...» del botón derecho). Lo que se
    deja en MANTENER no se toca. Devuelve cuántos."""
    _solo_admin(usuario)
    _accesibles(db, usuario, list(ids))
    if asignado_id is not MANTENER:
        asignado_id, asignado_nombre = pendientes._usuario_asignable(asignado_id)
    if especialidad_id is not MANTENER:
        especialidad_id = pendientes._especialidad(especialidad_id)
    for i in ids:
        if asignado_id is not MANTENER:
            db.asignar_aviso(i, asignado_id, asignado_nombre)
        if especialidad_id is not MANTENER:
            db.asignar_especialidad_aviso(i, especialidad_id)
    return len(ids)


# ---------------------------------------------------------------- completar y deshacer (la casilla de la tabla)

PREFIJO = "Mantenimiento Preventivo: "               # descripción del trabajo que apunta el preventivo hecho
ETIQUETAS = "Preventivo, Aviso Recurrente"


def descripcion(titulo):
    return PREFIJO + (titulo or "")


def lista_aviso(aviso_id):
    """La plantilla de la lista de comprobación que hay que rellenar al completar el aviso, o None."""
    plantilla_id = checklists.checklist_de("aviso", aviso_id)
    plantilla = checklists.obtener_plantilla(plantilla_id) if plantilla_id else None
    return plantilla if plantilla and plantilla["puntos"] else None


def lectura(texto):
    """La lectura del contador escrita al completar: None si se deja en blanco; si no, un número no negativo
    (ValueError("lectura_no_valida") si no lo es)."""
    if texto is None or (isinstance(texto, str) and not texto.strip()):
        return None
    valor = texto if isinstance(texto, (int, float)) and not isinstance(texto, bool) else contadores.numero(texto)
    if valor is None or valor < 0:
        raise ValueError("lectura_no_valida")
    return valor


def _del_usuario(db, usuario, aviso_id, estricto):
    """La fila de un aviso que el usuario puede marcar. Estricto (PC y web): uno de los que ve. Si no (lo que llega
    de la cola de un móvil, que no se puede quedar atascado): basta con que exista (la sede la comprueba la API)."""
    if estricto:
        return _accesibles(db, usuario, [aviso_id])[0]
    return next((a for a in db.obtener_avisos() if a[0] == aviso_id), None)


def _ids_trabajos(con, fecha, desc):
    return [f[0] for f in con.execute("SELECT id FROM tareas WHERE fecha=? AND descripcion=?", (fecha, desc)).fetchall()]


def completar(db, usuario, aviso_id, fecha=None, lista=None, valor_lectura=None, repuestos=(), minutos=None, personas=1,
              titulo=None, lectura_fecha=None, lectura_uid=None, origen="pc", estricto=True):
    """Marca un aviso como hecho (la casilla de la tabla en el PC y en MantPro Web, y «completar» en la app MantPro)
    y devuelve el id del trabajo que lo apunta en el historial («Mantenimiento Preventivo: <título>»).

    [fecha]: AAAA-MM-DD (None = hoy). [lista]: (items, nombre de la plantilla) de la lista rellenada; obligatoria si el
    aviso tiene una. [valor_lectura]: la lectura del contador en ese momento (None = sin lectura): desde ella se cuenta
    el siguiente. [repuestos], [minutos], [personas]: los de la app (se descuentan y apuntan como al completar un
    pendiente). Si el preventivo de ese día ya está en el historial (un reintento), no se repite: se devuelve el mismo
    trabajo. Estricto (PC y web): solo un aviso que se ve y que toca (o atrasado), con todo comprobado. Si no (cola del
    móvil): tolerante; si el aviso ya no existe se apunta igual con [titulo]."""
    fila = _del_usuario(db, usuario, aviso_id, estricto)
    hoy = date.today().isoformat()
    if estricto:
        fecha = pendientes._fecha(fecha or hoy)
        estado = next((f for f in filas([fila], contadores.estados_avisos()) if f["id"] == aviso_id), None)
        if not estado or not estado["activo"] or estado["completado"]:
            raise ValueError("aviso_no_toca")
        if lista_aviso(aviso_id) is not None and not (lista and lista[0]):
            raise ValueError("lista_sin_rellenar")
        valor_lectura = lectura(valor_lectura)
        if minutos is not None and (isinstance(minutos, bool) or not isinstance(minutos, int)
                                    or not 0 <= minutos <= pendientes.MAX_MINUTOS):
            raise ValueError("tiempo_no_valido")
        if isinstance(personas, bool) or not isinstance(personas, int) or not 1 <= personas <= pendientes.MAX_PERSONAS:
            raise ValueError("personas_no_validas")
        items = pendientes._repuestos(repuestos, usuario)
    else:
        fecha, minutos, personas, items = pendientes._tolerante(fecha, minutos, personas, repuestos)
        try:
            valor_lectura = lectura(valor_lectura)
        except ValueError:
            valor_lectura = None
    titulo_aviso = fila[1] if fila else (titulo or "")
    desc = descripcion(titulo_aviso)
    detalle = ""
    if lista and lista[0]:
        detalle = f"Lista de comprobación: {lista[1]} — " + ", ".join(
            f"{v} {k}" for k, v in checklists.recuento(checklists.normalizar_items(lista[0])).items() if v)
    if fila:
        db.marcar_aviso_completado(aviso_id, fecha, True, detalle=detalle)
    con = db.conectar()
    try:
        ya = _ids_trabajos(con, fecha, desc)
    finally:
        con.close()
    usuario_id = usuario["id"] if usuario else None
    usuario_nombre = usuario["nombre"] if usuario else None
    if ya:
        tarea_id = ya[0]                       # reintento: ni otro trabajo ni otro descuento de repuestos
    else:
        tarea_id = db.agregar_tarea(fecha, desc, ETIQUETAS, usuario_id, usuario_nombre,
                                    sede_id=sedes.sede_de("avisos_recurrentes", aviso_id) if fila else None)
        if not tarea_id:
            raise ValueError("no_guardado")
    if lista and lista[0]:
        checklists.guardar_resultado(tarea_id, lista[0], lista[1])
    if fila:
        checklists.borrar_borrador(checklists.clave_borrador("aviso", aviso_id))    # ya no hay lista a medias
    if not ya:
        consumos.registrar_consumo(tarea_id, items, usuario_id if usuario else usuarios.id_actual(),
                                   usuario_nombre if usuario else usuarios.nombre_actual(), desc, fecha)
        if minutos is not None:
            mano_obra.fijar_tiempo(tarea_id, minutos or None, personas, registrar=False)
        if fila:
            contadores.registrar_completado(aviso_id, valor_lectura, fecha=lectura_fecha or fecha, usuario=usuario,
                                            origen=origen, tarea_id=tarea_id, uid=lectura_uid)
    return tarea_id


def descompletar(db, usuario, aviso_id, estricto=True):
    """Deshace el último completado (desmarcar la casilla, o «deshacer» en la app): borra del historial el preventivo
    de ese día (con su lista y sus repuestos, que dejan de contar en los costes) y la «última vez» vuelve a la
    anterior que haya en el historial (o a ninguna). La lectura que se apuntó se queda, pero ya no cuenta como inicio
    del ciclo. Estricto (PC y web): solo un aviso que se ve y que está hecho hoy. Devuelve la fecha que queda."""
    fila = _del_usuario(db, usuario, aviso_id, estricto)
    if fila is None:
        raise ValueError("no_encontrado")
    if estricto and fila[5] != date.today().isoformat():
        raise ValueError("aviso_no_hecho_hoy")
    titulo, ultima = fila[1], fila[5]
    desc = descripcion(titulo)
    con = db.conectar()
    try:
        if ultima:
            ids = _ids_trabajos(con, ultima, desc)
            for tarea_id in ids:
                consumos.olvidar_trabajo(tarea_id)
            con.executemany("DELETE FROM checklist_resultados WHERE tarea_id=?", [(i,) for i in ids])
            con.executemany("DELETE FROM tareas WHERE id=?", [(i,) for i in ids])
            con.commit()
        anterior = con.execute("SELECT MAX(fecha) FROM tareas WHERE descripcion=?", (desc,)).fetchone()[0]
    finally:
        con.close()
    db.marcar_aviso_completado(aviso_id, anterior, anterior is not None, deshacer=True,
                               detalle="Se borra del historial el preventivo apuntado")
    contadores.deshacer_completado(aviso_id)
    return anterior
