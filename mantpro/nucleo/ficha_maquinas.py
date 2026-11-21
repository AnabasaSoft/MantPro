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

"""La pestaña Máquinas (sin Qt): el árbol (máquinas raíz de una sede, y de cada máquina sus submáquinas, los años
de sus trabajos y los trabajos de cada año), los indicadores de fiabilidad, el gráfico de trabajos por máquina y
crear, editar y borrar máquinas. Lo usan la pestaña Máquinas del PC y MantPro Web.

En el PC los desplegables solo ofrecen lo que existe; en la web llega lo que mande el navegador: aquí se comprueba
todo (que existan la máquina superior, la zona y la sede, que el usuario vea la sede, que una máquina no cuelgue de
sí misma ni de sus submáquinas). Un nombre igual o muy parecido al de otra máquina del mismo nivel se avisa
(«nombre_parecido») salvo que se confirme. Los errores son códigos (ValueError), nunca texto."""

from .. import idiomas
from . import almacen, maquinas, sedes

MANTENER = object()        # al editar: deja la foto que tenía


# ---------------------------------------------------------------- ver

def _nodo(m):
    return {"id": m["id"], "nombre": m["nombre"], "trabajos": maquinas.contar_trabajos(m["id"]),
            "zona": m.get("zona_nombre") or "", "zona_id": m.get("zona_id"), "foto": m.get("foto") or None}


def raiz(sede=None):
    """Las máquinas raíz de [sede] (id, lista o None = todas), por nombre: [{id, nombre, trabajos (sin contar las
    submáquinas), zona, zona_id, foto}]. Las submáquinas van con su raíz."""
    return [_nodo(m) for m in maquinas.listar_maquinas() if m["padre_id"] is None and sedes.de_la_sede(m.get("sede_id"), sede)]


def hijos(maquina_id):
    """Lo que cuelga de una máquina en el árbol: {submaquinas: [nodos], anios: [(año, trabajos)]}."""
    subs = [_nodo(m) for m in maquinas.listar_maquinas() if m["padre_id"] == maquina_id]
    return {"submaquinas": subs, "anios": list(maquinas.anios_de_maquina(maquina_id))}


def trabajos_anio(maquina_id, anio):
    """Los trabajos de un año de la máquina: [{id, resumen (la primera línea), fecha (AAAA-MM-DD)}]."""
    return [{"id": t["id"], "resumen": (t["descripcion"] or "").splitlines()[0] if t["descripcion"] else "", "fecha": t["fecha"]}
            for t in maquinas.trabajos_de_maquina_anio(maquina_id, anio)]


def indicadores(maquina_id):
    """Las líneas de «Indicadores de fiabilidad» de la máquina con sus submáquinas: (título, [líneas], nota)."""
    t = idiomas.t
    ind = maquinas.indicadores_fiabilidad(maquina_id)
    lineas = [f"{t('lbl_num_averias')}: {ind['num_averias']}"]
    if ind["num_averias"] == 0 or ind["mtbf_dias"] is None:
        return t("lbl_indicadores_fiabilidad"), lineas, t("msg_sin_datos_fiabilidad")
    lineas.append(f"{t('lbl_mtbf')}: {t('fmt_dias').format(n=ind['mtbf_dias'])}")
    if ind["mttr_horas"] is not None:
        lineas.append(f"{t('lbl_mttr')}: {t('fmt_horas').format(n=ind['mttr_horas'])}")
    return t("lbl_indicadores_fiabilidad"), lineas, ""


def grafico(sede=None, anio=None, zona_id=None):
    """«Trabajos por máquina»: [(nombre, trabajos)] de las máquinas raíz de [sede] (y de [zona_id]), sumando las de
    sus submáquinas, del año [anio] o de todos (None), de más a menos."""
    raices = [m for m in maquinas.listar_maquinas() if m["padre_id"] is None and sedes.de_la_sede(m.get("sede_id"), sede)]
    if zona_id is not None:
        raices = [m for m in raices if m["zona_id"] == zona_id]

    def total(id_maquina):
        ids = maquinas.descendientes_ids(id_maquina)
        if anio is None:
            return sum(maquinas.contar_trabajos(i) for i in ids)
        return sum(maquinas.contar_trabajos_anio(i, anio) for i in ids)

    return sorted(((m["nombre"], total(m["id"])) for m in raices), key=lambda par: par[1], reverse=True)


# ---------------------------------------------------------------- comprobaciones

def visible(usuario, maquina_id):
    """La máquina [maquina_id] (dict) si es de una sede que ve [usuario]; si no (o no existe), ValueError."""
    m = maquinas.obtener_maquina(maquina_id) if maquina_id is not None else None
    if not m or not sedes.de_la_sede(m.get("sede_id"), sedes.permitidas(usuario)):
        raise ValueError("no_encontrado")
    return m


def _superior(usuario, padre_id):
    if padre_id is None:
        return None
    try:
        return visible(usuario, padre_id)["id"]
    except ValueError:
        raise ValueError("maquina_no_existe") from None


def _zona(zona_id):
    if zona_id is not None and zona_id not in {z["id"] for z in maquinas.listar_zonas()}:
        raise ValueError("zona_no_existe")
    return zona_id


def _sede(usuario, sede_id):
    if sede_id is not None and sede_id not in {s["id"] for s in sedes.visibles(usuario)}:
        raise ValueError("sede_no_permitida")
    return sede_id


def _nombre(nombre, padre_id, excluir_id, confirmar_parecido):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("nombre_obligatorio")
    if not confirmar_parecido and maquinas.nombres_parecidos(nombre, padre_id, excluir_id=excluir_id):
        raise ValueError("nombre_parecido")
    return nombre


def parecidos(nombre, padre_id=None, excluir_id=None):
    """Los nombres parecidos al mismo nivel (para enseñarlos al avisar)."""
    return maquinas.nombres_parecidos(nombre or "", padre_id, excluir_id=excluir_id)


# ---------------------------------------------------------------- escribir

def crear(usuario, nombre, padre_id=None, notas="", foto=None, zona_id=None, sede_id=None, confirmar_parecido=False):
    """Da de alta una máquina (o una submáquina, con [padre_id]) y devuelve su id. Una raíz va a [sede_id] (None: la
    principal si el usuario la ve, si no la primera suya); una submáquina, a la sede de su superior."""
    padre_id = _superior(usuario, padre_id)
    zona_id = _zona(zona_id)
    sede_id = _sede(usuario, sede_id) if padre_id is None else None
    nombre = _nombre(nombre, padre_id, None, confirmar_parecido)
    if padre_id is None and sede_id is None:
        sede_id = sedes.para_nuevo(sedes.permitidas(usuario), usuario)
    nuevo = maquinas.agregar_maquina(nombre, padre_id, notas or "", foto, zona_id, sede_id=sede_id)
    if not nuevo:
        raise ValueError("no_guardado")
    return nuevo


def editar(usuario, maquina_id, nombre, padre_id=None, notas="", foto=MANTENER, zona_id=None, sede_id=None,
           confirmar_parecido=False):
    """Guarda los cambios de una máquina. [padre_id]: la nueva superior (no puede ser ella ni una de sus
    submáquinas). [sede_id]: solo en una raíz; si cambia, se lleva sus submáquinas y sus trabajos."""
    m = visible(usuario, maquina_id)
    if padre_id is not None and padre_id in maquinas.descendientes_ids(maquina_id):
        raise ValueError("superior_no_valida")
    padre_id = _superior(usuario, padre_id)
    zona_id = _zona(zona_id)
    sede_id = _sede(usuario, sede_id) if padre_id is None else None
    cambia = (nombre or "").strip() != m["nombre"] or padre_id != m["padre_id"]
    nombre = _nombre(nombre, padre_id, maquina_id, confirmar_parecido or not cambia)
    maquinas.actualizar_maquina(maquina_id, nombre, padre_id, notas or "", m.get("foto") if foto is MANTENER else foto, zona_id)
    if padre_id is None and sede_id is not None and sede_id != sedes.efectiva(m.get("sede_id")):
        sedes.asignar_maquina(maquina_id, sede_id)
    return True


def borrar(usuario, maquina_id):
    """Borra la máquina con sus submáquinas (y sus repuestos y contadores); sus trabajos se quedan sin máquina.
    Devuelve cuántas máquinas se han borrado."""
    visible(usuario, maquina_id)
    ids = maquinas.descendientes_ids(maquina_id)
    maquinas.borrar_maquina(maquina_id)
    almacen.borrar_repuestos_de_maquinas(ids)
    return len(ids)


def nueva_zona(nombre):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("nombre_obligatorio")
    return maquinas.agregar_zona(nombre)


# ---------------------------------------------------------------- repuestos («🔩 Repuestos de …»)

CANTIDAD_MIN, CANTIDAD_MAX = 0.01, 99999          # los del campo «Cantidad que lleva» del PC


def ubicacion(seccion_id):
    """El texto de la ubicación de un artículo («Estantería A > Balda 2»), como en Stock de almacén."""
    return almacen.obtener_ubicacion_texto(seccion_id, idiomas.t("txt_balda_num"), idiomas.t("txt_hueco_suelo_corto"))


def color_stock(actual, minimo):
    """«bajo» por debajo del mínimo (rojo), «sobre» por encima (verde) o None si coincide."""
    if actual < minimo:
        return "bajo"
    if actual > minimo:
        return "sobre"
    return None


def repuestos(maquina_id):
    """Los repuestos de la máquina para la tabla: los de almacen.repuestos_de_maquina más ubicacion (texto o «-»),
    color (color_stock) y bajo_minimo (para el informe)."""
    return [dict(r, ubicacion=ubicacion(r["seccion_id"]) or "-", color=color_stock(r["stock_actual"], r["stock_minimo"]),
                 bajo_minimo=almacen.esta_bajo_minimo(r))
            for r in almacen.repuestos_de_maquina(maquina_id)]


def elegibles_repuesto(maquina_id):
    """Los artículos que se pueden añadir como repuesto: los de los almacenes que se ven desde la sede de la máquina
    (todos, con una sola sede) que aún no lleva. [{id, texto, stock, busqueda}]; con varios almacenes, el texto dice
    de cuál es."""
    from . import almacenes
    almacen_ids = almacenes.ids_de_sede(sedes.sede_de_maquina(maquina_id)) if sedes.hay_varias() else None
    ya = {r["material_id"] for r in almacen.repuestos_de_maquina(maquina_id)}
    nombres_alm = almacenes.nombres() if almacenes.hay_varios() else {}
    lista = []
    for m in almacen.listar_materiales(almacen_ids=almacen_ids):
        if m["id"] in ya:
            continue
        texto = f"[{m['codigo']}] {m['nombre']}" if m.get("codigo") else m["nombre"]
        if nombres_alm:
            texto += f"  · {nombres_alm.get(almacenes.efectivo(m['almacen_id']), '')}"
        lista.append({"id": m["id"], "texto": texto, "stock": f"{m['stock_actual']:g} {m.get('unidad') or ''}".strip(),
                      "busqueda": f"{m.get('codigo') or ''} {m['nombre']}".lower()})
    return lista


def _cantidad(cantidad):
    try:
        valor = float(str(cantidad).replace(",", "."))
    except (TypeError, ValueError):
        raise ValueError("cantidad_no_valida") from None
    if not CANTIDAD_MIN <= valor <= CANTIDAD_MAX:
        raise ValueError("cantidad_no_valida")
    return valor


def guardar_repuesto(usuario, maquina_id, material_id, cantidad, notas="", nuevo=True):
    """Añade un repuesto a la máquina ([nuevo]: tiene que ser uno de elegibles_repuesto) o cambia la cantidad y las
    notas de uno que ya lleva."""
    visible(usuario, maquina_id)
    cantidad = _cantidad(cantidad)
    if nuevo:
        if material_id not in {m["id"] for m in elegibles_repuesto(maquina_id)}:
            raise ValueError("material_no_existe")
    elif material_id not in {r["material_id"] for r in almacen.repuestos_de_maquina(maquina_id)}:
        raise ValueError("repuesto_no_existe")
    almacen.guardar_repuesto(maquina_id, material_id, cantidad, (notas or "").strip()[:200])
    return True


def quitar_repuesto(usuario, maquina_id, material_id):
    """La máquina deja de llevar el artículo (que sigue en el almacén)."""
    visible(usuario, maquina_id)
    if material_id not in {r["material_id"] for r in almacen.repuestos_de_maquina(maquina_id)}:
        raise ValueError("repuesto_no_existe")
    almacen.quitar_repuesto(maquina_id, material_id)
    return True


# ---------------------------------------------------------------- etiquetas QR

MODOS_ETIQUETAS = ("una", "rama", "todas")


def ids_etiquetas(usuario, modo, maquina_id=None):
    """De qué máquinas se hacen las etiquetas QR (lo que pregunta «🏷️ Etiquetas QR»): «una» (la elegida), «rama» (la
    elegida y sus submáquinas) o «todas»; de las sedes que ve el usuario, ordenadas por su ruta completa."""
    if modo not in MODOS_ETIQUETAS:
        raise ValueError("modo_no_valido")
    rutas = maquinas.mapa_rutas_completas()
    permitidas = sedes.permitidas(usuario)
    if modo == "todas":
        vistas = [m["id"] for m in maquinas.listar_maquinas() if sedes.de_la_sede(m.get("sede_id"), permitidas)]
        return sorted(vistas, key=lambda i: rutas.get(i, "").lower())
    visible(usuario, maquina_id)
    if modo == "una":
        return [maquina_id]
    subs = [i for i in maquinas.descendientes_ids(maquina_id) if i != maquina_id]
    return [maquina_id] + sorted(subs, key=lambda i: rutas.get(i, "").lower())


# ---------------------------------------------------------------- contadores («📟 Contadores de …»)

def fecha_hora(iso):
    """AAAA-MM-DDTHH:MM:SS → la fecha corta del idioma y la hora («21/11/2026 10:30»)."""
    from datetime import datetime
    if not iso:
        return ""
    try:
        d = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    return d.strftime(idiomas.formato_fecha_corta_py()) + d.strftime(" %H:%M")


def contadores_de(maquina_id):
    """Los contadores de la máquina para la tabla del diálogo: los de contadores.listar_contadores más los textos de
    Lectura, Última lectura y Uso medio/día («—» si no hay)."""
    from . import contadores
    lista = []
    for c in contadores.listar_contadores(maquina_id):
        ritmo = contadores.ritmo_diario(c["id"])
        lista.append(dict(c, lectura_txt=contadores.con_unidad(c["actual"], c["unidad"]) if c["actual"] is not None else "—",
                          fecha_txt=fecha_hora(c["fecha_actual"]),
                          ritmo_txt=contadores.con_unidad(round(ritmo, 1), c["unidad"]) if ritmo else "—"))
    return lista


def contador_visible(usuario, contador_id):
    """El contador si es de una máquina que ve el usuario; si no, ValueError("no_encontrado")."""
    from . import contadores
    c = contadores.obtener_contador(contador_id) if contador_id is not None else None
    if not c:
        raise ValueError("no_encontrado")
    visible(usuario, c["maquina_id"])
    return c


def _solo_admin(usuario):
    from . import usuarios
    if not usuarios.es_admin(usuario):
        raise ValueError("solo_admin")


def _lectura(valor):
    from . import avisos
    return avisos.lectura(valor)


def crear_contador(usuario, maquina_id, nombre, unidad="", inicial=None):
    """«➕ Nuevo contador» (administradores): nombre obligatorio y, si se escribe, la lectura actual."""
    from . import contadores
    _solo_admin(usuario)
    visible(usuario, maquina_id)
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("nombre_obligatorio")
    nuevo = contadores.crear_contador(maquina_id, nombre[:100], (unidad or "").strip()[:20], _lectura(inicial), usuario=usuario)
    if not nuevo:
        raise ValueError("no_guardado")
    return nuevo


def editar_contador(usuario, contador_id, nombre, unidad=""):
    from . import contadores
    _solo_admin(usuario)
    contador_visible(usuario, contador_id)
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("nombre_obligatorio")
    contadores.editar_contador(contador_id, nombre[:100], (unidad or "").strip()[:20])
    return True


def borrar_contador(usuario, contador_id):
    """Borra el contador y sus lecturas; no si lo usa algún preventivo («contador_en_uso»)."""
    from . import contadores
    _solo_admin(usuario)
    c = contador_visible(usuario, contador_id)
    if c["n_avisos"]:
        raise ValueError("contador_en_uso")
    if not contadores.borrar_contador(contador_id):
        raise ValueError("no_guardado")
    return True


def apuntar_lectura(usuario, contador_id, valor, confirmar_menor=False):
    """«📟 Apuntar lectura» (quien puede hacer trabajos): un número no negativo; si es menor que la última, se avisa
    («lectura_menor») salvo que se confirme (el contador se ha cambiado o puesto a cero)."""
    from . import contadores, usuarios
    if not usuarios.puede_hacer_trabajos(usuario):
        raise ValueError("solo_tecnicos")
    c = contador_visible(usuario, contador_id)
    valor = _lectura(valor)
    if valor is None:
        raise ValueError("lectura_no_valida")
    if not confirmar_menor and c["actual"] is not None and valor < c["actual"]:
        raise ValueError("lectura_menor")
    if not contadores.registrar_lectura(contador_id, valor, usuario=usuario, origen="pc"):
        raise ValueError("no_guardado")
    return True


def lecturas_de(contador_id):
    """El historial de lecturas del contador (más recientes primero) con los textos de la tabla del PC."""
    from . import contadores
    c = contadores.obtener_contador(contador_id) or {"unidad": ""}
    origenes = {"pc": idiomas.t("origen_pc"), "movil": idiomas.t("origen_movil")}
    return [dict(l, fecha_txt=fecha_hora(l["fecha"]), valor_txt=contadores.con_unidad(l["valor"], c["unidad"]),
                 origen_txt=origenes.get(l["origen"], l["origen"] or ""))
            for l in contadores.lecturas(contador_id)]


def borrar_lectura(usuario, contador_id, lectura_id):
    """Borra una lectura mal puesta (administradores)."""
    from . import contadores
    _solo_admin(usuario)
    contador_visible(usuario, contador_id)
    if lectura_id not in {l["id"] for l in contadores.lecturas(contador_id)}:
        raise ValueError("no_encontrado")
    contadores.borrar_lectura(lectura_id)
    return True
