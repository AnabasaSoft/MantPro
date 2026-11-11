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

"""Sincronizar las fotos de este PC con la carpeta de su empresa en MantPro Cloud.

Los trabajos solo guardan el NOMBRE de sus fotos (`[FOTO: x.jpg]`), y ese texto ya viaja con los datos
(`sincro_nube.py`). Aquí viajan los FICHEROS, que nunca se editan: se crean o se borran.

Cada pasada (`sincronizar`) hace, por este orden:
  1. Avisa a la nube de las fotos que este PC ha borrado (las anota `anotar_borradas`, desde la limpieza de
     fotos sin uso). La nube las borra salvo las que algún registro suyo siga usando.
  2. Pide la lista de la nube (nombre y tamaño).
  3. SUBE las que hay aquí y la nube no tiene. Un nombre que la nube ya tiene con otro tamaño es un conflicto:
     gana la de la nube y no se toca ninguna.
  4. BAJA las que usa algún trabajo, pendiente, máquina o artículo de este PC y le faltan aquí. Nunca baja las
     que nadie usa aquí (la limpieza de fotos sin uso las borraría y volverían a bajar).

Es reanudable: no guarda un «hasta dónde llegué», compara cada vez la lista de la nube con la carpeta, así que si
se corta (sin internet, MantPro se cierra) la siguiente pasada sigue donde se quedó, y subir dos veces no duplica
nada. Va en un hilo propio y nunca bloquea la sincronización de datos. Sin Qt, para poder probarla a fondo.

El estado (qué borrados faltan por avisar, qué ficheros se rechazaron) va en `sync_fotos.json` FUERA de las
bases de datos, como el de la sincronización de datos."""

import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from . import conexion_bd, nube
from .seguridad import EXTENSIONES_FOTO, TAMANO_MAXIMO_FOTO, escribir_atomico, foto_valida

ARCHIVO_ESTADO = "sync_fotos.json"
CARPETA_FOTOS = "fotos_recibidas"
LOCALES_PROPIOS = {"Logo.jpg", "icono.png"}          # imágenes de MantPro, no son de ningún trabajo
PAGINA = 1000
LOTE_BORRADOS = 200
TIMEOUT_FICHERO = 120
SEGUNDOS_ENTRE_PASADAS = 600                         # sin cambios de datos, se revisa como mucho cada 10 minutos
SEGUNDOS_SIN_SUBIR = 1800                            # con la nube llena o la licencia caducada, no se insiste en subir antes de esto

_NOMBRE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,150}$")
_NOMBRES_EN_TEXTO = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,150}\.(?:%s)" % "|".join(e[1:] for e in sorted(EXTENSIONES_FOTO)), re.I)
_cerrojo = threading.Lock()                          # una sola pasada de fotos a la vez
_en_curso = None                                     # progreso de la pasada que está en marcha (solo en memoria)


def _marcar(fase, hecho, total):
    global _en_curso
    _en_curso = {"fase": fase, "hecho": int(hecho), "total": int(total)}

# Códigos que paran la pasada (se reintenta más tarde) frente a los que solo descartan ESA foto
# Con estos dos NO se puede subir, pero sí BAJAR: se deja de subir y se sigue con las bajadas
_SOLO_BAJAR = {"almacenamiento_lleno", "licencia_caducada"}
_DESCARTAN = {"foto_no_valida", "foto_demasiado_grande", "tipo_no_permitido", "nombre_invalido", "foto_vacia"}


# ---------------------------------------------------------------- estado en disco

def carpeta_fotos(carpeta=None):
    return os.path.join(nube._carpeta(carpeta), CARPETA_FOTOS)


def _ruta_estado(carpeta=None):
    return os.path.join(nube._carpeta(carpeta), ARCHIVO_ESTADO)


def estado(carpeta=None):
    try:
        with open(_ruta_estado(carpeta), encoding="utf-8") as f:
            e = json.load(f)
        if not isinstance(e, dict):
            raise ValueError
    except (OSError, ValueError):
        e = {}
    e.setdefault("borrar", [])
    e.setdefault("rechazadas", {})
    e.setdefault("ultima", None)
    e.setdefault("resultado", None)
    e.setdefault("sin_subir", None)          # {"motivo": código, "desde": ISO}: la nube no deja subir (llena o caducada)
    return e


def _guardar(e, carpeta=None):
    ruta = _ruta_estado(carpeta)
    escribir_atomico(ruta, json.dumps(e, ensure_ascii=False, indent=1))
    try:
        os.chmod(ruta, 0o600)
    except OSError:
        pass


def resumen_estado(carpeta=None):
    """Para el diálogo: {"pendientes": fotos que quedaron sin subir en la última pasada (None si aún no hay ninguna),
    "motivo": por qué no se puede subir (almacenamiento_lleno, licencia_caducada) o None, "ultima": cuándo}."""
    e = estado(carpeta)
    resultado = e.get("resultado") or {}
    motivo = (e.get("sin_subir") or {}).get("motivo")
    return {"pendientes": resultado.get("pendientes") if e.get("ultima") else None, "motivo": motivo, "ultima": e.get("ultima"),
            "en_curso": dict(_en_curso) if (_en_curso and _cerrojo.locked()) else None}


def es_sincronizable(nombre):
    """True si [nombre] es una foto de trabajo que puede viajar: nombre sencillo, extensión de imagen y no una de
    las imágenes propias de MantPro (logo, icono, etiquetas QR)."""
    return (isinstance(nombre, str) and bool(_NOMBRE.match(nombre)) and ".." not in nombre
            and os.path.splitext(nombre)[1].lower() in EXTENSIONES_FOTO
            and nombre not in LOCALES_PROPIOS and not nombre.startswith("QR_"))


def anotar_borradas(nombres, carpeta=None):
    """Apunta fotos que este PC acaba de borrar, para avisar a la nube en la próxima pasada. Solo hace algo si
    este PC sincroniza con MantPro Cloud. Nunca lanza (no debe impedir limpiar)."""
    try:
        from . import sincro_nube
        if sincro_nube.estado(carpeta) is None:
            return 0
        validos = [n for n in nombres if es_sincronizable(n)]
        if not validos:
            return 0
        e = estado(carpeta)
        e["borrar"] = sorted(set(e["borrar"]) | set(validos))
        _guardar(e, carpeta)
        return len(validos)
    except Exception as ex:      # noqa: BLE001
        print(f"Fotos de la nube: no se pudieron anotar los borrados ({ex})")
        return 0


# ---------------------------------------------------------------- qué usa este PC

def fotos_en_uso(carpeta=None):
    """Nombres de foto que usan los datos de este PC (la misma regla que la limpieza de fotos sin uso): las
    marcas [FOTO:], [FOTO_DESPUES:] y [FOTOS:] de trabajos y pendientes, la foto de cada máquina y de cada artículo."""
    c = nube._carpeta(carpeta)
    usadas = set()

    def leer(base, sentencia):
        try:
            con = conexion_bd.conectar(os.path.join(c, base), timeout=10)
        except Exception:      # noqa: BLE001
            return
        try:
            for (texto,) in con.execute(sentencia):
                if texto:
                    usadas.update(_NOMBRES_EN_TEXTO.findall(texto))
        except conexion_bd.sqlite3.Error:
            pass
        finally:
            con.close()

    leer("mantenimiento.db", "SELECT descripcion FROM tareas")
    leer("mantenimiento.db", "SELECT detalles FROM pendientes")
    leer("mantenimiento.db", "SELECT foto FROM maquinas WHERE foto IS NOT NULL")
    leer("almacen.db", "SELECT foto FROM materiales WHERE foto IS NOT NULL")
    return {n for n in usadas if es_sincronizable(n)}


def _locales(carpeta=None):
    ruta = carpeta_fotos(carpeta)
    try:
        return {e.name: e.stat().st_size for e in os.scandir(ruta) if e.is_file() and es_sincronizable(e.name)}
    except OSError:
        return {}


# ---------------------------------------------------------------- la nube (red)

class NubeFotos:
    """Habla con `/sync/fotos` de la nube. Cada método devuelve (resultado, None) o (None, código de error).
    Las pruebas lo sustituyen por uno falso con los mismos cuatro métodos."""

    def __init__(self, token):
        self.token = token

    def _cab(self, extra=None):
        return dict({"Authorization": "Bearer " + self.token}, **(extra or {}))

    def _error(self, r):
        try:
            cuerpo = r.json()
            codigo = cuerpo.get("error") if isinstance(cuerpo, dict) else None
        except ValueError:
            return nube.RESPUESTA_NO_VALIDA
        return codigo if isinstance(codigo, str) and codigo else nube.RESPUESTA_NO_VALIDA

    def listar(self, despues="", limite=PAGINA):
        return nube._peticion("GET", f"/sync/fotos?limite={int(limite)}&despues={quote(despues)}", None, self.token, timeout=60)

    def borrar(self, nombres):
        return nube._peticion("POST", "/sync/fotos/borrar", {"nombres": list(nombres)}, self.token, timeout=60)

    def subir(self, nombre, contenido, sha256):
        base = nube.url_base()
        if not nube._url_valida(base):
            return None, nube.URL_NO_VALIDA
        try:
            r = requests.put(f"{base}/sync/fotos/{quote(nombre)}", data=contenido, timeout=TIMEOUT_FICHERO,
                             headers=self._cab({"X-Sha256": sha256, "Content-Type": "application/octet-stream"}))
        except (requests.RequestException, OSError):
            return None, nube.SIN_CONEXION
        if r.status_code >= 400:
            return None, self._error(r)
        try:
            return r.json(), None
        except ValueError:
            return None, nube.RESPUESTA_NO_VALIDA

    def bajar(self, nombre):
        base = nube.url_base()
        if not nube._url_valida(base):
            return None, nube.URL_NO_VALIDA
        try:
            r = requests.get(f"{base}/sync/fotos/{quote(nombre)}", headers=self._cab(), timeout=TIMEOUT_FICHERO)
        except (requests.RequestException, OSError):
            return None, nube.SIN_CONEXION
        if r.status_code != 200:
            return None, self._error(r)
        return r.content, None


# ---------------------------------------------------------------- una pasada

def _lista_de_la_nube(nube_fotos):
    """Todas las fotos de la nube: ({nombre: tamaño}, código de error)."""
    todas, despues = {}, ""
    while True:
        res, err = nube_fotos.listar(despues, PAGINA)
        if err:
            return None, err
        fotos = res.get("fotos") if isinstance(res, dict) else None
        if not isinstance(fotos, list):
            return None, nube.RESPUESTA_NO_VALIDA
        for f in fotos:
            if isinstance(f, dict) and isinstance(f.get("nombre"), str) and isinstance(f.get("bytes"), int):
                todas[f["nombre"]] = f["bytes"]
        if not res.get("hay_mas") or not fotos:
            return todas, None
        despues = fotos[-1]["nombre"]


def _avisar_borrados(nube_fotos, e, carpeta, resumen):
    pendientes = [n for n in e["borrar"] if not os.path.exists(os.path.join(carpeta_fotos(carpeta), n))]
    e["borrar"] = pendientes                  # si la foto ha vuelto a existir aquí, ya no hay que borrarla
    for i in range(0, len(pendientes), LOTE_BORRADOS):
        lote = pendientes[i:i + LOTE_BORRADOS]
        res, err = nube_fotos.borrar(lote)
        if err:
            return err
        resumen["borradas_en_nube"] += len(res.get("borradas") or [])
        e["borrar"] = [n for n in e["borrar"] if n not in lote]      # borradas, no existían o las sigue usando alguien
        _guardar(e, carpeta)
    return None


def sincronizar(carpeta=None, nube_fotos=None, progreso=None, parar=None):
    """Una pasada completa. Devuelve (resumen, None) o (resumen_parcial, código de error). [parar]: función que
    devuelve True si hay que dejarlo (MantPro se cierra). [progreso](texto, hecho, total): para el diálogo."""
    if not _cerrojo.acquire(blocking=False):
        return None, "ocupado"
    try:
        if nube_fotos is None:
            tk = nube.token(carpeta)
            if not nube.sesion(carpeta) or not tk:
                return None, nube.SIN_SESION
            nube_fotos = NubeFotos(tk)
        resumen = {"subidas": 0, "bajadas": 0, "borradas_en_nube": 0, "rechazadas": 0, "conflictos": 0, "pendientes": 0}
        e = estado(carpeta)
        avisar = progreso or (lambda *a: None)
        parado = parar or (lambda: False)

        err = _avisar_borrados(nube_fotos, e, carpeta, resumen)
        if err:
            return resumen, err
        en_nube, err = _lista_de_la_nube(nube_fotos)
        if err:
            return resumen, err
        locales = _locales(carpeta)

        # --- subir lo que la nube no tiene (salvo que la nube haya dicho hace poco que no deja subir)
        error_subida = None
        if e["sin_subir"]:
            try:
                desde = datetime.fromisoformat(e["sin_subir"]["desde"])
                if (datetime.now(timezone.utc).replace(tzinfo=None) - desde).total_seconds() < SEGUNDOS_SIN_SUBIR:
                    error_subida = e["sin_subir"]["motivo"]
            except (KeyError, ValueError, TypeError):
                pass
        por_subir = []
        for n in sorted(locales):
            if n in en_nube:
                if en_nube[n] != locales[n]:
                    resumen["conflictos"] += 1
                continue
            rechazo = e["rechazadas"].get(n)
            if rechazo and rechazo.get("bytes") == locales[n]:
                resumen["rechazadas"] += 1
                continue
            por_subir.append(n)
        resumen["pendientes"] = len(por_subir)
        for i, n in enumerate(por_subir if error_subida is None else []):
            if parado():
                return resumen, "parado"
            avisar(n, i, len(por_subir))
            _marcar("subiendo", len(locales) - len(por_subir) + i, len(locales))     # «231 de 341»: contando las que ya estaban
            ruta = os.path.join(carpeta_fotos(carpeta), n)
            try:
                if locales[n] > TAMANO_MAXIMO_FOTO or locales[n] == 0:
                    raise ValueError("foto_demasiado_grande" if locales[n] else "foto_vacia")
                with open(ruta, "rb") as f:
                    contenido = f.read()
            except (OSError, ValueError) as ex:
                if isinstance(ex, ValueError):
                    e["rechazadas"][n] = {"bytes": locales[n], "motivo": str(ex)}
                    resumen["rechazadas"] += 1
                continue                       # desapareció o no se puede leer ahora: se mira otra vez más tarde
            _, err = nube_fotos.subir(n, contenido, hashlib.sha256(contenido).hexdigest())
            if err in _DESCARTAN:
                e["rechazadas"][n] = {"bytes": locales[n], "motivo": err}
                resumen["rechazadas"] += 1
                continue
            if err == "nombre_en_uso":
                resumen["conflictos"] += 1
                continue
            if err in _SOLO_BAJAR:
                error_subida = err
                e["sin_subir"] = {"motivo": err, "desde": nube._ahora_iso()}
                break                          # no se puede subir más, pero las bajadas siguen
            if err:
                _guardar(e, carpeta)
                return resumen, err
            resumen["subidas"] += 1
            resumen["pendientes"] -= 1
        if error_subida is None:
            e["sin_subir"] = None              # volvió a poder subir (o no había nada que subir)

        # --- bajar lo que usan los datos de este PC y falta aquí
        necesarias = sorted(n for n in fotos_en_uso(carpeta) if n not in locales and n in en_nube)
        for i, n in enumerate(necesarias):
            if parado():
                return resumen, "parado"
            avisar(n, i, len(necesarias))
            _marcar("bajando", i, len(necesarias))
            contenido, err = nube_fotos.bajar(n)
            if err == "foto_no_existe":
                continue
            if err:
                _guardar(e, carpeta)
                return resumen, err
            if _guardar_foto_bajada(carpeta, n, contenido):
                resumen["bajadas"] += 1
            else:
                resumen["rechazadas"] += 1

        e["ultima"] = nube._ahora_iso()
        e["resultado"] = dict(resumen)
        _guardar(e, carpeta)
        return resumen, error_subida
    finally:
        global _en_curso
        _en_curso = None
        _cerrojo.release()


def _guardar_foto_bajada(carpeta, nombre, contenido):
    """Escribe una foto bajada de la nube, comprobando que de verdad es una imagen (lo que llega de fuera no es
    de fiar). Primero a un fichero temporal y se publica de golpe. True si quedó guardada."""
    if not es_sincronizable(nombre) or not isinstance(contenido, (bytes, bytearray)) or not contenido:
        return False
    destino_dir = carpeta_fotos(carpeta)
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, nombre)
    if os.path.exists(destino):
        return True
    temporal = os.path.join(destino_dir, f".bajando-{os.getpid()}-{threading.get_ident()}{os.path.splitext(nombre)[1].lower()}")
    try:
        with open(temporal, "wb") as f:
            f.write(contenido)
        if not foto_valida(temporal):
            return False
        os.replace(temporal, destino)
        return True
    except OSError:
        return False
    finally:
        try:
            os.remove(temporal)
        except OSError:
            pass


# ---------------------------------------------------------------- en segundo plano

def hace_falta(resumen, carpeta=None):
    """True si conviene una pasada de fotos tras una sincronización de datos: cuando ha subido o bajado algo
    (puede haber fotos nuevas en un lado o en otro), nunca se ha hecho una pasada o hace más de 10 minutos."""
    if resumen and (resumen.get("enviados") or resumen.get("aplicados")):
        return True
    ultima = estado(carpeta).get("ultima")
    if not ultima:
        return True
    try:
        antes = datetime.fromisoformat(ultima.replace("Z", "+00:00"))
        if antes.tzinfo is None:
            antes = antes.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - antes).total_seconds() > SEGUNDOS_ENTRE_PASADAS
    except ValueError:
        return True


def lanzar_en_segundo_plano(carpeta=None, al_terminar=None):
    """Una pasada en un hilo propio «demonio». Devuelve el hilo, o None si ya hay una en marcha."""
    if _cerrojo.locked():
        return None

    def tarea():
        try:
            resumen, error = sincronizar(carpeta)
        except Exception as ex:      # noqa: BLE001  (un fallo aquí nunca debe tumbar nada más)
            resumen, error = None, f"fallo_inesperado: {ex!r}"
            print(f"Fotos de la nube: {error}")
        if al_terminar:
            al_terminar(resumen, error)
    hilo = threading.Thread(target=tarea, name="sincronizacion-fotos", daemon=True)
    hilo.start()
    return hilo
