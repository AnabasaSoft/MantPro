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

"""Sincronización de este PC con MantPro Cloud (motor, sin Qt). Paso 4, fase A: SUBIR.

El PC envía a la nube lo que ha cambiado y NUNCA modifica sus datos locales por lo
que haya en la nube (bajar es la fase B). Sirve ya como copia de seguridad fuera
de casa y no puede estropear nada local.

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

from . import conexion_bd, nube, sincronizacion
from .seguridad import escribir_atomico

BASES = ("mant", "alma")
LOTE = 200                          # cambios por petición (el servidor admite 500)
ARCHIVO_ESTADO = "sync_nube.json"

EMPRESA_DISTINTA = "empresa_distinta"
OCUPADO = "ocupado"
BD_NO_DISPONIBLE = "bd_no_disponible"
BD_OCUPADA = "bd_ocupada"

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


def _estado_nuevo(cons, empresa_uuid, carpeta):
    """Origen nuevo y todo encolado para subir (primera vez, o copia restaurada)."""
    e = {"empresa_uuid": empresa_uuid, "origen": _uuid.uuid4().hex,
         "subido_hasta": {b: 0 for b in BASES}, "ultima_subida": None, "omitidos": 0}
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
        e = _estado_nuevo(cons, empresa_uuid, carpeta)
    return e, None


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
    pks = [f[1] for f in con.execute(f"PRAGMA table_info({t})") if f[5]]
    return pks[0] if len(pks) == 1 else None


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


def sincronizar_ahora(carpeta=None, enviar=None):
    """Una sincronización completa (hay que llamarla fuera del hilo de la ventana).
    Devuelve (resumen, None) o (None, código). [enviar] solo lo usan las pruebas."""
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
        try:
            with _conexiones(carpeta) as cons:
                e, err = activar(cons, empresa, carpeta)
                if err:
                    return None, err
                resumen, err = subir_pendiente(cons, e, enviar or _enviar_por_red(tk, carpeta), carpeta)
                if err:
                    return None, err
                for base in BASES:
                    sincronizacion.purgar_subidos(cons[base])
                e["ultima_subida"] = nube._ahora_iso()
                e["omitidos"] = int(e.get("omitidos", 0)) + resumen["omitidos"]
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


def resumen_estado(carpeta=None):
    """Para mostrarlo en el diálogo: {"activa", "ultima_subida", "pendientes", "omitidos"}.
    «pendientes» es None si todavía no se puede contar."""
    e = estado(carpeta)
    res = {"activa": e is not None, "ultima_subida": (e or {}).get("ultima_subida"),
           "pendientes": None, "omitidos": int((e or {}).get("omitidos", 0))}
    if e is None:
        return res
    try:
        with _conexiones(carpeta) as cons:
            res["pendientes"] = sum(
                cons[b].execute("SELECT COUNT(*) FROM cambios WHERE subido = 0").fetchone()[0] for b in BASES)
    except Exception:      # noqa: BLE001
        pass
    return res
