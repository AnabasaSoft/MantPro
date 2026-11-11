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

"""Sincronización de este PC con MantPro Cloud (motor, sin Qt). Paso 4: SUBIR (fase A) y BAJAR (fase B).

SUBIR: el PC envía a la nube lo que ha cambiado. Sirve como copia de seguridad fuera de casa.
BAJAR: aplica a las bases locales lo que han escrito otros (móviles, otros PCs); toda la lógica de
aplicarlo está en `sincro_bajada.py`. Se baja ANTES de subir, y antes de aplicar cambios de la nube
se hace una copia de seguridad (como mucho una al día).

Primer inicio de sesión de un PC («primer login con datos ya existentes»):
  * la nube sin datos: se sube todo lo de este PC;
  * la nube con datos y este PC VACÍO (solo lo que MantPro crea por defecto): adopta lo de la nube
    (no sube sus registros por defecto, que ensuciarían la cuenta con un segundo administrador);
  * la nube con datos y este PC con datos propios: no sube ni baja nada y devuelve NUBE_CON_DATOS
    para que el usuario decida; `sincronizar_ahora(adoptar=True)` sustituye lo de este PC por lo de
    la nube (con copia de seguridad previa). Sirve también para recuperar tras restaurar una copia.

Cómo funciona:
  * `sincronizacion.py` anota en la tabla `cambios` de cada base (mant y alma) qué
    registro cambió. Aquí se leen esos cambios, se funden los repetidos de un mismo
    registro, se lee el registro tal como está AHORA, se traducen sus referencias de
    id local a uuid (también entre las dos bases) y se envía en lotes a la nube.
  * Cada base sube con su propio `origen` (<origen del PC>-mant / -alma): el
    servidor descarta los números de cambio que ya recibió de ese origen, así que
    reenviar un lote tras un corte de red no duplica nada.
  * Un PC se sincroniza con UNA empresa. Si inicia sesión en otra, se rechaza
    (`empresa_distinta`) en vez de mezclar datos.
  * Si se restaura una copia de seguridad antigua, sus números de cambio quedan por
    debajo de los que la nube ya recibió y se descartarían sin avisar. Se detecta
    (el estado vive en un fichero FUERA de la base: la copia no lo arrastra) y el PC
    adopta un origen nuevo y vuelve a subirlo todo.
  * Las fotos no se suben todavía: los registros llevan solo el nombre del fichero.

Solo se activa con sesión de MantPro Cloud: sin ella no hay disparadores y MantPro
funciona exactamente igual que siempre."""

import contextlib
import json
import os
import threading
import uuid as _uuid

from . import conexion_bd, nube, sincro_bajada, sincronizacion
from .seguridad import escribir_atomico

BASES = ("mant", "alma")
LOTE = 200                          # cambios por petición (el servidor admite 500)
ARCHIVO_ESTADO = "sync_nube.json"

EMPRESA_DISTINTA = "empresa_distinta"
OCUPADO = "ocupado"
BD_NO_DISPONIBLE = "bd_no_disponible"
BD_OCUPADA = "bd_ocupada"
NUBE_CON_DATOS = "nube_con_datos"
COPIA_FALLIDA = "copia_fallida"
COPIA_RESTAURADA = "copia_restaurada"
PAGINA = 500                        # registros por petición al bajar (el servidor admite hasta 500)
_TABLAS_CONOCIDAS = {f"{b}.{t}" for b in sincronizacion.TABLAS for t in sincronizacion.TABLAS[b]}
# Las tablas que ya se sincronizaban antes de que el estado guardara cuáles se habían encolado (las sesiones
# de móvil y los móviles se añadieron después): un estado antiguo se da por encolado con estas.
_TABLAS_ANTERIORES = _TABLAS_CONOCIDAS - {"mant.sesiones", "mant.moviles"}

# Códigos del servidor que significan «esto no cabe»: si un lote da uno de ellos se parte
# por la mitad hasta dar con el registro que sobra.
_NO_CABE = ("registro_demasiado_grande", "peticion_demasiado_grande", "lote_demasiado_grande")

_cerrojo = threading.Lock()         # una sola sincronización a la vez (temporizador + botón)


# ---------------------------------------------------------------- estado en disco

def _ruta_estado(carpeta=None):
    return os.path.join(nube._carpeta(carpeta), ARCHIVO_ESTADO)


def estado(carpeta=None):
    """Estado de la sincronización de este PC (dict) o None si todavía no se ha activado."""
    try:
        with open(_ruta_estado(carpeta), encoding="utf-8") as f:
            e = json.load(f)
        return e if isinstance(e, dict) and e.get("origen") and e.get("empresa_uuid") else None
    except (OSError, ValueError):
        return None


def _guardar_estado(e, carpeta=None):
    ruta = _ruta_estado(carpeta)
    escribir_atomico(ruta, json.dumps(e, ensure_ascii=False, indent=1))
    try:
        os.chmod(ruta, 0o600)
    except OSError:
        pass


def rutas_bd(carpeta=None):
    c = nube._carpeta(carpeta)
    return {"mant": os.path.join(c, "mantenimiento.db"), "alma": os.path.join(c, "almacen.db")}


@contextlib.contextmanager
def _conexiones(carpeta=None):
    """Conexiones propias (de este hilo) a las dos bases."""
    cons = {}
    try:
        for base, ruta in rutas_bd(carpeta).items():
            cons[base] = conexion_bd.conectar(ruta, timeout=30)
            if base == "alma":
                cons[base].execute("PRAGMA foreign_keys = ON")      # como almacen.py: los borrados en cascada
        yield cons
    finally:
        for c in cons.values():
            try:
                c.close()
            except Exception:
                pass


# ---------------------------------------------------------------- activación

def _restaurada(cons, e):
    """True si alguna base tiene un último número de cambio MENOR que el que ya se subió."""
    subido = e.get("subido_hasta") or {}
    return any(sincronizacion.ultimo_n(cons[b]) < int(subido.get(b, 0)) for b in BASES)


def _estado_base(empresa_uuid):
    return {"empresa_uuid": empresa_uuid, "origen": _uuid.uuid4().hex,
            "subido_hasta": {b: 0 for b in BASES}, "ultima_subida": None, "omitidos": 0,
            "bajado_hasta": 0, "ultima_bajada": None, "copia_nube": None,
            "tablas": sorted(_TABLAS_CONOCIDAS),        # tablas ya encoladas (una versión nueva puede añadir otras)
            "restaurada": False,            # copia restaurada: ni se sube ni se baja hasta recuperar de la nube
            "inicial_pendiente": False}     # adopción en curso: no se sube nada hasta acabar de bajar


def _estado_nuevo(cons, empresa_uuid, carpeta, restaurada=False):
    """Origen nuevo y todo encolado para subir (primera vez, o copia restaurada). Tras restaurar una copia
    NO se sincroniza nada más (`restaurada`): sus uuid pueden ser otros (si la copia es anterior a la primera
    sincronización) y subir o bajar ahora duplicaría los registros en la nube o en este PC.
    `sincronizar_ahora(adoptar=True)` recupera lo de la nube sin duplicar."""
    e = _estado_base(empresa_uuid)
    e["restaurada"] = restaurada
    for base in BASES:
        sincronizacion.encolar_todo(cons[base], base)
    _guardar_estado(e, carpeta)
    return e


def activar(cons, empresa_uuid, carpeta=None):
    """Prepara el registro de cambios en las dos bases (idempotente: repara los
    disparadores que una migración haya borrado) y el estado de la sincronización.
    Devuelve (estado, None) o (None, código de error)."""
    e = estado(carpeta)
    if e and e["empresa_uuid"] != empresa_uuid:
        return None, EMPRESA_DISTINTA
    for base in BASES:
        sincronizacion.preparar_base(cons[base], base)
    if e is None or _restaurada(cons, e):
        e = _estado_nuevo(cons, empresa_uuid, carpeta, restaurada=e is not None)
    else:
        _encolar_tablas_nuevas(cons, e, carpeta)
    return e, None


def _encolar_tablas_nuevas(cons, e, carpeta=None):
    """Si esta versión de MantPro sincroniza tablas que el estado no recuerda haber encolado (se añadieron
    después), sube lo que ya hay en ellas: los disparadores solo anotan lo que cambie A PARTIR DE AHORA."""
    ya = set(e.get("tablas") or _TABLAS_ANTERIORES)
    nuevas = _TABLAS_CONOCIDAS - ya
    if nuevas and not e.get("restaurada") and not e.get("inicial_pendiente"):
        for base in BASES:
            sincronizacion.encolar_todo(cons[base], base, solo={t.split(".", 1)[1] for t in nuevas if t.startswith(base + ".")})
    if nuevas or "tablas" not in e:
        e["tablas"] = sorted(_TABLAS_CONOCIDAS)
        _guardar_estado(e, carpeta)


def preparar_al_arrancar(carpeta=None):
    """Al abrir MantPro: si este PC ya sincroniza, repara los disparadores (una migración
    que recree una tabla los pierde) y detecta una copia restaurada ANTES de que se
    anote nada. Sin sesión o sin estado no hace nada. Nunca lanza: no debe impedir arrancar."""
    try:
        ses = nube.sesion(carpeta)
        empresa = ((ses or {}).get("empresa") or {}).get("uuid")
        if not empresa or estado(carpeta) is None:
            return None
        with _conexiones(carpeta) as cons:
            return activar(cons, empresa, carpeta)[1]
    except Exception as ex:      # noqa: BLE001
        print(f"Sincronización con la nube: no se pudo preparar al arrancar ({ex})")
        return BD_NO_DISPONIBLE


# ---------------------------------------------------------------- leer y empaquetar

_pk = {}


def _columna_pk(con, tabla):
    """Nombre de la clave primaria entera de [tabla] (o None si no tiene una sola)."""
    t = sincronizacion._nombre(tabla)
    pks = [f for f in con.execute(f"PRAGMA table_info({t})") if f[5]]
    # Solo una clave entera es «el id local» (no viaja). Un pk de texto (token, dispositivo_id) es un dato.
    return pks[0][1] if len(pks) == 1 and (pks[0][2] or "").upper() == "INTEGER" else None


def _uuid_de(cons, destino, valor):
    """uuid del registro al que apunta [valor] (id local) en [destino] «base.tabla»; None si no existe."""
    if valor is None:
        return None
    base, tabla = destino.split(".", 1)
    con = cons[base]
    pk = _columna_pk(con, tabla) or "id"
    f = con.execute(f"SELECT uuid FROM {sincronizacion._nombre(tabla)} WHERE {pk} = ?", (valor,)).fetchone()
    return f[0] if f else None


def _fila(cons, base, tabla, espec, uuid):
    """El registro [uuid] de [tabla] tal como está ahora, listo para la nube: sin el id
    local ni el uuid (es la identidad), sin columnas derivadas ni locales y con las
    referencias traducidas a uuid. None si ya no existe."""
    con = cons[base]
    t = sincronizacion._nombre(tabla)
    if espec["tipo"] == "clave":
        cond = espec["identidad"].format(r=t) + " = ?"
        if espec.get("solo_si"):
            cond += f" AND ({espec['solo_si'].format(r=t)})"
    else:
        cond = "uuid = ?"
    cur = con.execute(f"SELECT * FROM {t} WHERE {cond}", (uuid,))
    fila = cur.fetchone()
    if fila is None:
        return None
    datos = dict(zip([d[0] for d in cur.description], tuple(fila)))
    quitar = set(espec.get("derivadas", ())) | set(espec.get("ignorar", ()))
    if espec["tipo"] != "clave":
        quitar.add("uuid")
        pk = _columna_pk(con, t)
        if pk:
            quitar.add(pk)
    for col in quitar:
        datos.pop(col, None)
    for col, destino in espec.get("refs", {}).items():
        if col in datos:
            datos[col] = _uuid_de(cons, destino, datos[col])
    return datos


def _componer(cons, base, pendientes):
    """Convierte los cambios pendientes en el lote que se envía. Devuelve (lote, hasta):
    [hasta] es el último número de cambio que se da por atendido.
      * Varios cambios del mismo registro se funden en uno, con su estado actual.
      * Si el registro ya no existe: borrado ('d'), salvo que se creara en este mismo
        grupo (la nube nunca lo vio: no hay nada que borrar).
      * Si existe: alta ('i') si el grupo trae un alta, y si no modificación ('u')."""
    grupos = {}
    for c in pendientes:
        g = grupos.setdefault((c["tabla"], c["uuid"]), {"n": 0, "ops": set()})
        g["n"] = max(g["n"], c["n"])
        g["ops"].add(c["op"])
    lote = []
    for (tabla, uuid), g in grupos.items():
        espec = sincronizacion.TABLAS[base].get(tabla)
        if espec is None:
            continue
        datos = _fila(cons, base, tabla, espec, uuid)
        if datos is None:
            if "i" in g["ops"]:
                continue
            lote.append({"n": g["n"], "tabla": f"{base}.{tabla}", "uuid": uuid, "op": "d"})
        else:
            lote.append({"n": g["n"], "tabla": f"{base}.{tabla}", "uuid": uuid,
                         "op": "i" if "i" in g["ops"] else "u", "datos": datos})
    lote.sort(key=lambda c: c["n"])
    return lote, pendientes[-1]["n"]


# ---------------------------------------------------------------- enviar

def _enviar_por_red(tk, carpeta=None):
    """Función que sube un lote a la nube: (origen, lote) -> (respuesta, código de error)."""
    def enviar(origen, lote):
        res, err = nube._peticion("POST", "/sync/subir", {"origen": origen, "cambios": lote}, tk, timeout=60)
        if err == "no_autorizado":
            nube.cerrar_sesion(carpeta, avisar=False)
            return None, nube.SESION_CADUCADA
        if not err and not isinstance(res.get("version"), int):
            return None, nube.RESPUESTA_NO_VALIDA
        return res, err
    return enviar


def _subir_lote(enviar, origen, lote):
    """Envía [lote]; si no cabe, lo parte por la mitad hasta aislar lo que sobra.
    Devuelve (omitidos, código de error). Un registro suelto que no cabe se omite
    (y se cuenta): no puede bloquear para siempre todo lo demás."""
    res, err = enviar(origen, lote)
    if not err:
        return 0, None
    # nginx contesta 413 con HTML, no con JSON: llega como RESPUESTA_NO_VALIDA.
    parece_tamano = err in _NO_CABE or err == nube.RESPUESTA_NO_VALIDA
    if not parece_tamano:
        return 0, err
    if len(lote) == 1:
        return (1, None) if err in _NO_CABE else (0, err)
    medio = len(lote) // 2
    o1, e1 = _subir_lote(enviar, origen, lote[:medio])
    if e1:
        return o1, e1
    o2, e2 = _subir_lote(enviar, origen, lote[medio:])
    return o1 + o2, e2


def subir_pendiente(cons, e, enviar, carpeta=None, lote=LOTE):
    """Sube todo lo pendiente de las dos bases. Guarda el avance tras cada lote: si se
    corta, la próxima vez sigue donde se quedó. Devuelve (resumen, código de error)."""
    resumen = {"enviados": 0, "omitidos": 0}
    for base in BASES:
        con = cons[base]
        origen = f"{e['origen']}-{base}"
        while True:
            pendientes = sincronizacion.cambios_pendientes(con, lote)
            if not pendientes:
                break
            registros, hasta = _componer(cons, base, pendientes)
            if registros:
                omitidos, err = _subir_lote(enviar, origen, registros)
                resumen["omitidos"] += omitidos
                if err:
                    return resumen, err
                resumen["enviados"] += len(registros) - omitidos
            sincronizacion.marcar_subidos(con, hasta)
            e["subido_hasta"][base] = hasta
            _guardar_estado(e, carpeta)
            if len(pendientes) < lote:
                break
    return resumen, None


# ---------------------------------------------------------------- bajar

def _hoy():
    return nube._ahora_iso()[:10]


def _bajar_por_red(tk, carpeta=None):
    """Función que pide una página a la nube: (desde, limite) -> (respuesta, código de error)."""
    def bajar(desde, limite=PAGINA):
        res, err = nube._peticion("GET", f"/sync/bajar?desde={int(desde)}&limite={int(limite)}", None, tk, timeout=60)
        if err == "no_autorizado":
            nube.cerrar_sesion(carpeta, avisar=False)
            return None, nube.SESION_CADUCADA
        if not err and not (isinstance(res.get("cambios"), list) and isinstance(res.get("hay_mas"), bool)
                            and isinstance(res.get("hasta"), int) and not isinstance(res.get("hasta"), bool)):
            return None, nube.RESPUESTA_NO_VALIDA
        return res, err
    return bajar


def _hacer_copia(carpeta=None, copia=None):
    """Copia de seguridad de las bases antes de que la nube cambie algo. True si salió bien."""
    if copia is not None:
        return bool(copia())
    from . import copias
    c = nube._carpeta(carpeta)
    fotos, destino = os.path.join(c, "fotos_recibidas"), os.path.join(c, "backups_auto")
    os.makedirs(fotos, exist_ok=True)
    os.makedirs(destino, exist_ok=True)
    return bool(copias.hacer_copia(fotos, destino, list(rutas_bd(carpeta).values()), motivo="nube").get("ok"))


def _hay_ajenos(cambios, propio):
    return any(c.get("tabla") in _TABLAS_CONOCIDAS and not (c.get("origen") or "").startswith(propio) for c in cambios)


def bajar_y_aplicar(cons, e, bajar, carpeta=None, copia=None):
    """Baja de la nube todo lo posterior a `bajado_hasta` y lo aplica, página a página. Antes de aplicar
    lo primero ajeno del día se hace una copia de seguridad (si falla, no se aplica nada).
    Devuelve (recuentos, código de error)."""
    res = sincro_bajada.resultado_vacio()
    while True:
        desde = int(e.get("bajado_hasta", 0))
        pagina, err = bajar(desde, PAGINA)
        if err:
            return res, err
        cambios = pagina["cambios"]
        if _hay_ajenos(cambios, e["origen"]) and e.get("copia_nube") != _hoy():
            if not _hacer_copia(carpeta, copia):
                return res, COPIA_FALLIDA
            e["copia_nube"] = _hoy()
            _guardar_estado(e, carpeta)
        try:
            sincro_bajada.aplicar(cons, cambios, e["origen"], res)
        except conexion_bd.sqlite3.Error:
            return res, BD_OCUPADA
        if pagina["hay_mas"] and pagina["hasta"] <= desde:
            return res, nube.RESPUESTA_NO_VALIDA          # no avanza: no se puede quedar dando vueltas
        e["bajado_hasta"] = max(desde, pagina["hasta"])
        _guardar_estado(e, carpeta)
        if not pagina["hay_mas"]:
            break
    if e.get("inicial_pendiente"):
        # Adopción terminada: lo que se anotó mientras tanto son los registros por defecto que MantPro
        # recrea al arrancar con la base vacía; no deben subirse a la cuenta.
        for base in BASES:
            sincronizacion.marcar_subidos(cons[base], 10 ** 12)
            e["subido_hasta"][base] = sincronizacion.ultimo_n(cons[base])
        e["inicial_pendiente"] = False
    e["ultima_bajada"] = nube._ahora_iso()
    _guardar_estado(e, carpeta)
    sincro_bajada.olvidar_esquemas()
    res.pop("_tocados", None)        # solo servía para mirar el stock final al acabar
    return res, None


def _nube_tiene_datos(bajar):
    """¿Hay en la nube algún registro (no borrado) de las tablas que este PC sincroniza?"""
    desde = 0
    while True:
        pagina, err = bajar(desde, PAGINA)
        if err:
            return None, err
        if any(c.get("op") == "u" and c.get("tabla") in _TABLAS_CONOCIDAS for c in pagina["cambios"]):
            return True, None
        if not pagina["hay_mas"] or pagina["hasta"] <= desde:
            return False, None
        desde = pagina["hasta"]


def pc_vacio(cons):
    """True si este PC no tiene NADA suyo: solo lo que MantPro crea por defecto (el administrador y su
    rol) y los apuntes de auditoría de ese administrador (p. ej. el cambio de su contraseña al entrar
    por primera vez). Los ajustes y los días especiales no cuentan."""
    for base, tablas in sincronizacion.TABLAS.items():
        existentes = {f[0] for f in cons[base].execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        for tabla, espec in tablas.items():
            if espec["tipo"] == "clave" or tabla not in existentes:
                continue
            n = cons[base].execute(f"SELECT COUNT(*) FROM {sincronizacion._nombre(tabla)}").fetchone()[0]
            if tabla == "usuarios":
                if n > 1 or (n == 1 and cons[base].execute("SELECT login FROM usuarios").fetchone()[0] != "admin"):
                    return False
            elif tabla == "usuario_roles":
                if n > 1:
                    return False
            elif tabla == "auditoria":
                admin = cons[base].execute("SELECT id FROM usuarios WHERE login = 'admin'").fetchone()
                if n and (admin is None or cons[base].execute(
                        "SELECT COUNT(*) FROM auditoria WHERE usuario_id IS NOT ?", (admin[0],)).fetchone()[0]):
                    return False
            elif n:
                return False
    return True


def _adoptar(cons, empresa_uuid, carpeta, con_copia, copia=None):
    """Empieza de cero con lo de la nube: copia de seguridad (si se pide; si falla NO se toca nada),
    se vacían las tablas sincronizables y se queda pendiente la bajada completa."""
    if con_copia and not _hacer_copia(carpeta, copia):
        return None, COPIA_FALLIDA
    for base in BASES:
        sincronizacion.preparar_base(cons[base], base)
        sincronizacion.vaciar_tablas(cons[base], base)
    e = _estado_base(empresa_uuid)
    e["inicial_pendiente"] = True
    if con_copia:
        e["copia_nube"] = _hoy()          # ya hay copia de ahora mismo: no hace falta otra al empezar a bajar
    for base in BASES:
        e["subido_hasta"][base] = sincronizacion.ultimo_n(cons[base])
        sincronizacion.marcar_subidos(cons[base], 10 ** 12)
    _guardar_estado(e, carpeta)
    return e, None


def _primer_inicio(cons, empresa_uuid, carpeta, bajar, copia):
    """Primer sincronización de un PC (no hay estado). Devuelve (estado, código de error)."""
    if bajar is None:
        return activar(cons, empresa_uuid, carpeta)
    hay, err = _nube_tiene_datos(bajar)
    if err:
        return None, err
    if not hay:
        return activar(cons, empresa_uuid, carpeta)
    for base in BASES:
        sincronizacion.preparar_base(cons[base], base)
    if pc_vacio(cons):
        return _adoptar(cons, empresa_uuid, carpeta, True, copia)    # copia siempre: se vacía lo local
    return None, NUBE_CON_DATOS


def sincronizar_ahora(carpeta=None, enviar=None, bajar=None, copia=None, adoptar=False):
    """Una sincronización completa: baja lo de la nube y sube lo de este PC (hay que llamarla fuera del
    hilo de la ventana). Devuelve (resumen, None) o (None, código). [adoptar]: sustituye lo de este PC por
    lo de la nube (con copia de seguridad); lo pide el usuario tras NUBE_CON_DATOS o tras restaurar una copia.
    [enviar], [bajar] y [copia] solo los usan las pruebas; con [enviar] y sin [bajar] no se baja nada."""
    if not _cerrojo.acquire(blocking=False):
        return None, OCUPADO
    try:
        ses = nube.sesion(carpeta)
        tk = nube.token(carpeta)
        if not ses or not tk:
            return None, nube.SIN_SESION
        empresa = (ses.get("empresa") or {}).get("uuid")
        if not empresa:
            return None, nube.RESPUESTA_NO_VALIDA
        if bajar is None and enviar is None:
            bajar = _bajar_por_red(tk, carpeta)
        try:
            with _conexiones(carpeta) as cons:
                e = estado(carpeta)
                if e is not None and e["empresa_uuid"] != empresa:
                    return None, EMPRESA_DISTINTA
                if adoptar:
                    if bajar is None:
                        return None, nube.RESPUESTA_NO_VALIDA
                    e, err = _adoptar(cons, empresa, carpeta, True, copia)
                elif e is None:
                    e, err = _primer_inicio(cons, empresa, carpeta, bajar, copia)
                else:
                    e, err = activar(cons, empresa, carpeta)
                if err:
                    return None, err
                if e.get("restaurada"):
                    return None, COPIA_RESTAURADA
                resumen = {"enviados": 0, "omitidos": 0}
                resumen.update(sincro_bajada.resultado_vacio())
                resumen["adoptado"] = bool(e.get("inicial_pendiente"))
                if bajar is not None:
                    bajado, err = bajar_y_aplicar(cons, e, bajar, carpeta, copia)
                    resumen.update(bajado)
                    if err:
                        return None, err
                if not e.get("inicial_pendiente"):
                    subido, err = subir_pendiente(cons, e, enviar or _enviar_por_red(tk, carpeta), carpeta)
                    if err:
                        return None, err
                    resumen.update(subido)
                    for base in BASES:
                        sincronizacion.purgar_subidos(cons[base])
                    e["ultima_subida"] = nube._ahora_iso()
                    e["omitidos"] = int(e.get("omitidos", 0)) + subido["omitidos"]
                _guardar_estado(e, carpeta)
                return resumen, None
        except (conexion_bd.SinSQLCipher, conexion_bd.ClaveNoDisponible):
            return None, BD_NO_DISPONIBLE
        except conexion_bd.sqlite3.Error:
            return None, BD_OCUPADA
    finally:
        _cerrojo.release()


def comprobar_empresa(empresa_uuid, carpeta=None):
    """EMPRESA_DISTINTA si este PC ya sincroniza con otra empresa (se mira nada más
    iniciar sesión, antes de tocar nada); None si puede seguir."""
    e = estado(carpeta)
    return EMPRESA_DISTINTA if e and e["empresa_uuid"] != empresa_uuid else None


def lanzar_en_segundo_plano(carpeta=None, al_terminar=None):
    """Una sincronización en un hilo propio (para el temporizador). Es un hilo «demonio»:
    si se cierra MantPro a mitad no lo espera (cada lote se guarda por completo o no se
    guarda, y lo que quede se sube la próxima vez). Devuelve el hilo."""
    def tarea():
        resultado, error = sincronizar_ahora(carpeta)
        if al_terminar:
            al_terminar(resultado, error)
    hilo = threading.Thread(target=tarea, name="sincronizacion-nube", daemon=True)
    hilo.start()
    return hilo


def hay_cambios_sin_subir(carpeta=None):
    """True si este PC sincroniza con la nube y tiene algún cambio sin subir. Es una lectura mínima (dos
    consultas con un máximo de 1 s de espera) pensada para mirarla cada pocos segundos desde la ventana:
    nunca lanza y, si no puede mirar (bases ocupadas, sin sincronización activa...), dice False."""
    e = estado(carpeta)
    if e is None or e.get("restaurada") or e.get("inicial_pendiente"):
        return False
    for ruta in rutas_bd(carpeta).values():
        try:
            con = conexion_bd.conectar(ruta, timeout=1)
            try:
                if con.execute("SELECT 1 FROM cambios WHERE subido = 0 LIMIT 1").fetchone():
                    return True
            finally:
                con.close()
        except Exception:      # noqa: BLE001  (no poder mirar no debe romper la ventana)
            continue
    return False


def resumen_estado(carpeta=None):
    """Para mostrarlo en el diálogo: {"activa", "ultima_subida", "pendientes", "omitidos"}.
    «pendientes» es None si todavía no se puede contar."""
    e = estado(carpeta)
    res = {"activa": e is not None, "ultima_subida": (e or {}).get("ultima_subida"),
           "pendientes": None, "omitidos": int((e or {}).get("omitidos", 0)),
           "ultima_bajada": (e or {}).get("ultima_bajada"), "restaurada": bool((e or {}).get("restaurada")),
           "adoptando": bool((e or {}).get("inicial_pendiente"))}
    if e is None:
        return res
    try:
        with _conexiones(carpeta) as cons:
            res["pendientes"] = sum(
                cons[b].execute("SELECT COUNT(*) FROM cambios WHERE subido = 0").fetchone()[0] for b in BASES)
    except Exception:      # noqa: BLE001
        pass
    return res
