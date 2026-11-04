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

"""Copias de seguridad automáticas (motor, sin Qt).

Una copia automática son dos cosas en la carpeta de copias:
- "auto_backup_db_<fecha>.zip": copia coherente de las dos bases de datos
  (pesa poco, se hace entera cada vez y se guardan varias, ver conservar()).
- "fotos_backup_<clave>.zip": ZIP incrementales de fotos. Las fotos no cambian
  una vez guardadas, así que cada copia solo añade las nuevas. La clave es el
  mes de la foto ("2026-11"); los ZIP antiguos por año ("2026") siguen
  valiendo, porque al restaurar se leen todos los "fotos_backup_*.zip". Por
  mes y no por año para que el ZIP que cambia (el del mes en curso) sea
  pequeño al mandarlo al destino externo (NAS, USB, carpeta en la nube).

Cuándo se hace: al cerrar la aplicación, cada cierto tiempo mientras está
abierta, al rato de recibir datos de un móvil y al arrancar si quedaron
cambios sin copiar. Lo decide la interfaz (o un servidor sin ventana) con
toca_copia_periodica() y hay_cambios_sin_copiar(); aquí solo se hace.

Después de cada copia: se manda al destino externo (si se ha configurado,
ver DestinoCarpeta) y se prueba que se puede restaurar (probar_copia()):
las bases de datos se sacan de la copia (descifrándolas si hace falta), se
abren y se comprueban, y se leen unas cuantas fotos al azar. El resultado se
guarda en estado_copias.json (fuera de las bases de datos: restaurar una
copia no debe borrar el registro de las copias) y problemas() dice qué
avisar.

Las funciones devuelven códigos y datos técnicos, no textos traducidos: los
traduce quien los muestra.
"""

import errno
import hashlib
import io
import json
import os
import random
import re
import shutil
import tempfile
import threading
import zipfile
from datetime import datetime, timedelta

from .rutas import DATA_DIR
from .seguridad import escribir_atomico, anadir_bd_a_zip
from . import cifrado_copias, conexion_bd

RUTA_CONFIG = os.path.join(DATA_DIR, "config_copias.json")
RUTA_ESTADO = os.path.join(DATA_DIR, "estado_copias.json")

PREFIJO_BD = "auto_backup_db_"
PREFIJO_FOTOS = "fotos_backup_"

# Una foto que llegó hace menos de esto puede estar todavía escribiéndose
# (llega del móvil): en las copias hechas con la aplicación abierta se deja
# para la siguiente.
_SEGUNDOS_FOTO_RECIENTE = 30

# Fotos que se leen al azar en cada prueba de restauración
_MUESTRA_FOTOS = 5

# Tabla que tiene que existir en cada base de datos para darla por buena
_TABLA_DE_CADA_BD = {"mantenimiento.db": "tareas", "almacen.db": "materiales"}

CONFIG_POR_DEFECTO = {
    "periodica": True,      # copia cada [horas] mientras la aplicación está abierta
    "horas": 2,
    "tras_movil": True,     # copia al rato de recibir datos de un móvil
    "destino": "",          # carpeta externa (vacío: solo la carpeta local)
    "conservar_recientes": 10,   # copias de las bases de datos que se guardan siempre
    "conservar_dias": 14,        # y además la última de cada día de estos días
}

_RE_FECHA = re.compile(r"(\d{8})_(\d{6})")

# Una sola copia a la vez (la del cierre espera a la periódica, y viceversa)
_cerrojo = threading.Lock()


# --------------------------------------------------------- configuración

def leer_config():
    config = dict(CONFIG_POR_DEFECTO)
    try:
        with open(RUTA_CONFIG, encoding="utf-8") as f:
            guardada = json.load(f)
        if isinstance(guardada, dict):
            config.update({k: v for k, v in guardada.items() if k in CONFIG_POR_DEFECTO})
    except (OSError, ValueError):
        pass
    try:
        config["horas"] = min(24, max(1, int(config["horas"])))
        config["conservar_recientes"] = max(1, int(config["conservar_recientes"]))
        config["conservar_dias"] = max(0, int(config["conservar_dias"]))
    except (TypeError, ValueError):
        for clave in ("horas", "conservar_recientes", "conservar_dias"):
            config[clave] = CONFIG_POR_DEFECTO[clave]
    config["destino"] = (config.get("destino") or "").strip()
    return config


# Nombre de cada opción en el registro de cambios (se guarda en español y se
# traduce al mostrarlo, ver interfaz/dialogos/auditoria.py)
_CAMPOS_AUDITORIA = {
    "periodica": "Copia periódica", "horas": "Cada (horas)",
    "tras_movil": "Copia tras recibir datos de un móvil", "destino": "Carpeta externa de las copias",
    "conservar_recientes": "Copias recientes que se guardan", "conservar_dias": "Días con una copia diaria",
}


def guardar_config(config, auditar=True):
    anterior = leer_config()
    datos = {k: config.get(k, v) for k, v in CONFIG_POR_DEFECTO.items()}
    escribir_atomico(RUTA_CONFIG, json.dumps(datos, ensure_ascii=False, indent=1))
    cambios = [{"campo": _CAMPOS_AUDITORIA[k], "antes": str(anterior[k]), "despues": str(datos[k])}
               for k in CONFIG_POR_DEFECTO if str(anterior[k]) != str(datos[k])]
    if auditar and cambios:
        from . import usuarios
        usuarios.auditar("copias", "configurar", "Copias automáticas", cambios=cambios)


# ---------------------------------------------------------------- estado

def leer_estado():
    try:
        with open(RUTA_ESTADO, encoding="utf-8") as f:
            estado = json.load(f)
        return estado if isinstance(estado, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar_estado(estado):
    try:
        escribir_atomico(RUTA_ESTADO, json.dumps(estado, ensure_ascii=False, indent=1))
    except OSError as ex:
        print(f"No se ha podido guardar el estado de las copias: {ex}")


def _ahora():
    return datetime.now().replace(microsecond=0)


def _fecha(texto):
    try:
        return datetime.fromisoformat(texto) if texto else None
    except (TypeError, ValueError):
        return None


def ultima_copia_buena(carpeta_copias=None):
    """Fecha de la última copia que se hizo y pasó la prueba, o None. Si
    todavía no hay estado guardado (copias de versiones anteriores), la de la
    copia más reciente de la carpeta, aunque no se probara."""
    fecha = _fecha(leer_estado().get("ultima_buena", {}).get("fecha"))
    if fecha or not carpeta_copias:
        return fecha
    copias = _copias_bd_de(os.listdir(carpeta_copias)) if os.path.isdir(carpeta_copias) else {}
    return max(copias.values()) if copias else None


# -------------------------------------------------- huella de los datos

def huella(rutas_bd, carpeta_fotos):
    """Algo que cambia cuando cambian los datos: tamaño y fecha de las bases
    de datos (y de su -wal, donde SQLite apunta lo último) y las fotos que hay.
    Leer no la cambia; escribir, sí."""
    partes = []
    for ruta in rutas_bd:
        for r in (ruta, ruta + "-wal"):
            try:
                st = os.stat(r)
                partes.append(f"{os.path.basename(r)}:{st.st_size}:{int(st.st_mtime)}")
            except OSError:
                partes.append(f"{os.path.basename(r)}:-")
    try:
        fotos = sorted(os.listdir(carpeta_fotos))
    except OSError:
        fotos = []
    # hashlib y no hash(): hash() de un texto cambia en cada arranque
    partes.append(f"fotos:{len(fotos)}:{hashlib.sha1(chr(0).join(fotos).encode()).hexdigest()[:12]}")
    return "|".join(partes)


def hay_cambios_sin_copiar(rutas_bd, carpeta_fotos):
    estado = leer_estado()
    return not estado.get("ultima", {}).get("ok") or estado.get("huella") != huella(rutas_bd, carpeta_fotos)


def toca_copia_periodica(config=None, ahora=None):
    """Si ya ha pasado el tiempo de la copia periódica desde la última copia
    (buena o no: si falla, se vuelve a intentar al siguiente plazo)."""
    config = config or leer_config()
    if not config["periodica"]:
        return False
    ultima = _fecha(leer_estado().get("ultima", {}).get("fecha"))
    return ultima is None or (ahora or _ahora()) - ultima >= timedelta(hours=config["horas"])


# -------------------------------------------------------- destino externo

class DestinoCarpeta:
    """Destino externo de las copias: una carpeta (NAS, disco USB, carpeta
    sincronizada con la nube). Lo que hace falta de un destino está aquí
    (comprobar, listar, subir, abrir y borrar), para poder añadir otros
    (S3, SFTP…) con los mismos métodos sin tocar el resto."""

    def __init__(self, ruta):
        self.ruta = os.path.abspath(os.path.expanduser(ruta))

    def descripcion(self):
        return self.ruta

    def comprobar(self):
        """Lanza OSError si no se puede escribir en el destino (disco USB
        sin conectar, NAS apagado, sin permisos…)."""
        if not os.path.isdir(self.ruta):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.ruta)
        fd, prueba = tempfile.mkstemp(dir=self.ruta, prefix=".mantpro_prueba_")
        os.close(fd)
        os.remove(prueba)

    def listar(self):
        """{nombre: (tamaño, fecha de modificación)} de los ficheros."""
        ficheros = {}
        for nombre in os.listdir(self.ruta):
            ruta = os.path.join(self.ruta, nombre)
            if os.path.isfile(ruta) and not nombre.endswith(".tmp"):
                st = os.stat(ruta)
                ficheros[nombre] = (st.st_size, st.st_mtime)
        return ficheros

    def subir(self, origen, nombre):
        """Copia [origen] como [nombre]: a un temporal que se renombra al
        final, para que un corte no deje a medias un fichero con el nombre
        bueno. Conserva la fecha de modificación (se compara al sincronizar)."""
        destino = os.path.join(self.ruta, nombre)
        temporal = destino + ".tmp"
        try:
            with open(origen, "rb") as fo, open(temporal, "wb") as fd:
                shutil.copyfileobj(fo, fd, 1024 * 1024)
                fd.flush()
                os.fsync(fd.fileno())
            shutil.copystat(origen, temporal)
            os.replace(temporal, destino)
        except BaseException:
            try: os.remove(temporal)
            except OSError: pass
            raise

    def abrir(self, nombre):
        return open(os.path.join(self.ruta, nombre), "rb")

    def borrar(self, nombre):
        os.remove(os.path.join(self.ruta, nombre))


def destino_de(config=None):
    """El destino externo configurado, o None."""
    config = config or leer_config()
    return DestinoCarpeta(config["destino"]) if config["destino"] else None


def mismo_disco(ruta, otra=DATA_DIR):
    """Si [ruta] está en el mismo disco (sistema de ficheros) que [otra]: una
    copia ahí no sirve si el disco falla (salvo que sea una carpeta que se
    sincroniza con otro sitio)."""
    try:
        return os.stat(ruta).st_dev == os.stat(otra).st_dev
    except OSError:
        return False


# ------------------------------------------------------------ conservar

def _copias_bd_de(nombres):
    """{nombre: fecha} de las copias automáticas de las bases de datos."""
    copias = {}
    for nombre in nombres:
        if nombre.startswith(PREFIJO_BD) and nombre.endswith(".zip"):
            m = _RE_FECHA.search(nombre)
            if m:
                try:
                    copias[nombre] = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
                except ValueError:
                    pass
    return copias


def sobrantes(copias, recientes, dias, ahora=None):
    """De {nombre: fecha}, las que sobran: se guardan las [recientes] más
    nuevas y, además, la última de cada uno de los [dias] últimos días."""
    ahora = ahora or _ahora()
    orden = sorted(copias, key=copias.get, reverse=True)
    guardar = set(orden[:recientes])
    limite = (ahora - timedelta(days=dias)).date()
    dias_vistos = set()
    for nombre in orden:
        dia = copias[nombre].date()
        if dia > limite and dia not in dias_vistos:
            dias_vistos.add(dia)
            guardar.add(nombre)
    return [n for n in orden if n not in guardar]


# ---------------------------------------------------------------- copia

def _clave_foto(nombre, ruta):
    """Mes de la foto ("2026-11"): el nombre lleva casi siempre la fecha
    (pc_drag_20260115_..., app_20260115_...); si no, la de modificación."""
    m = _RE_FECHA.search(nombre)
    if m:
        return f"{m.group(1)[:4]}-{m.group(1)[4:6]}"
    try:
        return datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%Y-%m")
    except OSError:
        return _ahora().strftime("%Y-%m")


def _zips_fotos(carpeta):
    return sorted(f for f in os.listdir(carpeta)
                  if f.startswith(PREFIJO_FOTOS) and f.endswith(".zip"))


def _copiar_fotos(carpeta_fotos, carpeta_copias, clave, incluir_recientes, progreso):
    """Añade a los ZIP de fotos las que aún no están. Devuelve cuántas se han
    dejado para otra vez por ser demasiado recientes."""
    ya_copiadas = set()
    for f in _zips_fotos(carpeta_copias):
        try:
            with zipfile.ZipFile(os.path.join(carpeta_copias, f)) as zf:
                ya_copiadas.update(cifrado_copias.nombre_real(n) for n in zf.namelist())
        except (OSError, zipfile.BadZipFile):
            pass
    limite = _ahora().timestamp() - _SEGUNDOS_FOTO_RECIENTE
    por_zip, aplazadas = {}, 0
    nombres = os.listdir(carpeta_fotos) if os.path.isdir(carpeta_fotos) else []
    for nombre in nombres:
        ruta = os.path.join(carpeta_fotos, nombre)
        if nombre in ya_copiadas or not os.path.isfile(ruta):
            continue
        if not incluir_recientes and os.path.getmtime(ruta) > limite:
            aplazadas += 1
            continue
        por_zip.setdefault(_clave_foto(nombre, ruta), []).append(nombre)

    total = sum(len(v) for v in por_zip.values())
    hechas = 0
    if progreso: progreso(0, total)
    for clave_zip, lista in sorted(por_zip.items()):
        ruta_zip = os.path.join(carpeta_copias, f"{PREFIJO_FOTOS}{clave_zip}.zip")
        with zipfile.ZipFile(ruta_zip, "a", zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
            for nombre in lista:
                cifrado_copias.escribir_entrada(zipf, os.path.join(carpeta_fotos, nombre), nombre, clave)
                hechas += 1
                if progreso: progreso(hechas, total)
    return aplazadas


def _copiar_bd(rutas_bd, carpeta_copias, clave):
    """Hace el ZIP de las bases de datos. Devuelve (nombre, errores de
    integridad)."""
    nombre = f"{PREFIJO_BD}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    ruta_zip = os.path.join(carpeta_copias, nombre)
    if os.path.exists(ruta_zip):   # dos copias en el mismo segundo
        os.remove(ruta_zip)
    temporal = ruta_zip + ".tmp"
    dañadas = []
    try:
        with zipfile.ZipFile(temporal, "w", zipfile.ZIP_STORED) as zipf:
            for ruta_bd in rutas_bd:
                integridad = anadir_bd_a_zip(zipf, ruta_bd, clave)
                if integridad not in (None, "ok"):
                    dañadas.append(f"{os.path.basename(ruta_bd)}: {integridad}")
        os.replace(temporal, ruta_zip)
    except BaseException:
        try: os.remove(temporal)
        except OSError: pass
        raise
    return nombre, dañadas


def _borrar_sobrantes(nombres, borrar, config):
    for nombre in sobrantes(_copias_bd_de(nombres), config["conservar_recientes"], config["conservar_dias"]):
        try: borrar(nombre)
        except OSError: pass


def _enviar_a_destino(destino, carpeta_copias, nombre_bd, config):
    """Manda al destino la copia de las bases de datos y los ZIP de fotos que
    hayan cambiado, y borra allí las copias de las bases de datos que sobran.
    Los ZIP de fotos no se borran nunca del destino."""
    destino.comprobar()
    remotos = destino.listar()
    for nombre in [nombre_bd] + _zips_fotos(carpeta_copias):
        st = os.stat(os.path.join(carpeta_copias, nombre))
        remoto = remotos.get(nombre)
        # 2 s de margen: FAT (discos USB) guarda la hora de 2 en 2 segundos
        if remoto is None or remoto[0] != st.st_size or abs(remoto[1] - st.st_mtime) > 2:
            destino.subir(os.path.join(carpeta_copias, nombre), nombre)
    _borrar_sobrantes(destino.listar(), destino.borrar, config)


def hacer_copia(carpeta_fotos, carpeta_copias, rutas_bd, motivo="cierre", progreso=None,
                solo_si_hay_cambios=False, config=None):
    """Hace una copia automática, la manda al destino externo, la prueba y
    guarda el resultado en el estado. [motivo]: "cierre", "periodica",
    "movil", "arranque" o "manual". Con [solo_si_hay_cambios], no hace nada
    si los datos no han cambiado desde la última copia buena.

    Devuelve un diccionario: "hecha" (False si no había cambios), "ok",
    "error" (texto técnico o ""), "integridad" (lista de bases de datos que
    no pasan la comprobación), "destino_error" y "prueba" ({"ok", "detalle"})."""
    config = config or leer_config()
    with _cerrojo:
        estado = leer_estado()
        huella_antes = huella(rutas_bd, carpeta_fotos)
        if solo_si_hay_cambios and estado.get("ultima", {}).get("ok") and estado.get("huella") == huella_antes:
            return {"hecha": False, "ok": True, "error": "", "integridad": [], "destino_error": "", "prueba": None}

        resultado = {"hecha": True, "ok": False, "error": "", "integridad": [], "destino_error": "", "prueba": None}
        ahora = _ahora().isoformat()
        nombre_bd = None
        aplazadas = 0
        try:
            clave = cifrado_copias.clave_actual()
            os.makedirs(carpeta_copias, exist_ok=True)
            aplazadas = _copiar_fotos(carpeta_fotos, carpeta_copias, clave, motivo == "cierre", progreso)
            nombre_bd, resultado["integridad"] = _copiar_bd(rutas_bd, carpeta_copias, clave)
            _borrar_sobrantes(os.listdir(carpeta_copias),
                              lambda n: os.remove(os.path.join(carpeta_copias, n)), config)
        except Exception as ex:
            resultado["error"] = str(ex) or ex.__class__.__name__

        if nombre_bd:
            claves = {}
            if clave:
                claves[clave.sal] = clave
            prueba = probar_copia(lambda n: open(os.path.join(carpeta_copias, n), "rb"),
                                  nombre_bd, _zips_fotos(carpeta_copias), claves, rutas_bd, carpeta_fotos)
            prueba["donde"] = "local"
            destino = destino_de(config)
            if destino:
                info_destino = {"ruta": destino.descripcion()}
                try:
                    _enviar_a_destino(destino, carpeta_copias, nombre_bd, config)
                    prueba_destino = probar_copia(destino.abrir, nombre_bd,
                                                  [n for n in destino.listar() if n.startswith(PREFIJO_FOTOS) and n.endswith(".zip")],
                                                  claves, rutas_bd, carpeta_fotos)
                    info_destino["fecha_ok"] = ahora
                    if prueba["ok"] and not prueba_destino["ok"]:
                        prueba = dict(prueba_destino, donde="destino")
                except Exception as ex:
                    resultado["destino_error"] = info_destino["error"] = str(ex) or ex.__class__.__name__
                    info_destino["fecha_error"] = ahora
                    info_destino["fecha_ok"] = estado.get("destino", {}).get("fecha_ok") \
                        if estado.get("destino", {}).get("ruta") == destino.descripcion() else None
                estado["destino"] = info_destino
            else:
                estado.pop("destino", None)
            prueba["fecha"] = ahora
            estado["prueba"] = prueba
            resultado["prueba"] = prueba
            resultado["ok"] = not resultado["error"] and not resultado["integridad"] and prueba["ok"]

        if resultado["integridad"] and not resultado["error"]:
            resultado["error"] = "; ".join(resultado["integridad"])
        estado["ultima"] = {"fecha": ahora, "motivo": motivo, "ok": resultado["ok"],
                            "error": resultado["error"], "archivo": nombre_bd}
        if resultado["ok"]:
            estado["ultima_buena"] = {"fecha": ahora, "archivo": nombre_bd}
            # Con fotos aplazadas, la huella no vale: que la siguiente copia las recoja
            estado["huella"] = huella_antes if not aplazadas else None
        _guardar_estado(estado)
        return resultado


# ----------------------------------------------------- prueba de restauración

def probar_copia(abrir, nombre_bd, zips_fotos, claves, rutas_bd, carpeta_fotos, muestra=_MUESTRA_FOTOS):
    """Prueba que se puede restaurar una copia, sin tocar los datos de
    verdad: saca cada base de datos a un temporal (descifrándola), la abre y
    comprueba su integridad y que tiene su tabla principal; comprueba que
    todas las fotos que hay ahora están en los ZIP de fotos y lee unas
    cuantas al azar (si una foto está dañada, falla al leerla). [abrir(nombre)]
    abre un fichero de la copia para leerlo (local o del destino).

    Devuelve {"ok": bool, "detalle": [texto técnico de cada fallo]}."""
    fallos = []
    try:
        with abrir(nombre_bd) as f, zipfile.ZipFile(f) as zf:
            entradas = {cifrado_copias.nombre_real(n): n for n in zf.namelist()}
            for ruta_bd in rutas_bd:
                base = os.path.basename(ruta_bd)
                if not os.path.exists(ruta_bd):
                    continue
                if base not in entradas:
                    fallos.append(f"{base}: falta en la copia")
                    continue
                fallo = _probar_bd(zf, entradas[base], _TABLA_DE_CADA_BD.get(base), claves)
                if fallo:
                    fallos.append(f"{base}: {fallo}")
    except Exception as ex:
        fallos.append(f"{nombre_bd}: {ex or ex.__class__.__name__}")

    # Fotos: todas las que hay (salvo las recién llegadas) tienen que estar
    en_copia = {}
    for nombre_zip in zips_fotos:
        try:
            with abrir(nombre_zip) as f, zipfile.ZipFile(f) as zf:
                for n in zf.namelist():
                    en_copia[cifrado_copias.nombre_real(n)] = (nombre_zip, n)
        except Exception as ex:
            fallos.append(f"{nombre_zip}: {ex or ex.__class__.__name__}")
    limite = _ahora().timestamp() - _SEGUNDOS_FOTO_RECIENTE
    try:
        fotos = [n for n in os.listdir(carpeta_fotos)
                 if os.path.isfile(os.path.join(carpeta_fotos, n))
                 and os.path.getmtime(os.path.join(carpeta_fotos, n)) <= limite]
    except OSError:
        fotos = []
    faltan = [n for n in fotos if n not in en_copia]
    if faltan:
        fallos.append(f"faltan {len(faltan)} fotos en la copia (p. ej. {faltan[0]})")

    # Unas cuantas al azar, leídas enteras (comprueba el CRC o el cifrado)
    elegidas = random.sample(sorted(en_copia), min(muestra, len(en_copia)))
    por_zip = {}
    for nombre in elegidas:
        nombre_zip, entrada = en_copia[nombre]
        por_zip.setdefault(nombre_zip, []).append(entrada)
    for nombre_zip, entradas_zip in por_zip.items():
        try:
            with abrir(nombre_zip) as f, zipfile.ZipFile(f) as zf:
                for entrada in entradas_zip:
                    try:
                        cifrado_copias.leer_entrada(zf, entrada, _Descarte(), claves)
                    except cifrado_copias.ContrasenaNecesaria:
                        pass   # cifrada con una contraseña anterior: no se puede comprobar aquí
                    except Exception as ex:
                        fallos.append(f"{nombre_zip}/{cifrado_copias.nombre_real(entrada)}: {ex or ex.__class__.__name__}")
        except Exception as ex:
            fallos.append(f"{nombre_zip}: {ex or ex.__class__.__name__}")
    return {"ok": not fallos, "detalle": fallos}


class _Descarte(io.RawIOBase):
    """Fichero que lo tira todo (para leer una foto solo para comprobarla)."""
    def writable(self): return True
    def write(self, datos): return len(datos)


def _probar_bd(zf, entrada, tabla, claves):
    """Saca la base de datos [entrada] a un temporal y la comprueba. Devuelve
    el fallo (texto) o None si está bien."""
    fd, temporal = tempfile.mkstemp(suffix=".db"); os.close(fd)
    try:
        with open(temporal, "wb") as destino:
            cifrado_copias.leer_entrada(zf, entrada, destino, claves)
        con = conexion_bd.conectar_plano(temporal)
        try:
            integridad = con.execute("PRAGMA integrity_check").fetchone()[0]
            if integridad != "ok":
                return integridad
            if tabla:
                con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()
        finally:
            con.close()
        return None
    except cifrado_copias.ContrasenaNecesaria:
        return "cifrada con una contraseña que este equipo no tiene"
    except Exception as ex:
        return str(ex) or ex.__class__.__name__
    finally:
        try: os.remove(temporal)
        except OSError: pass


def probar_ultima(carpeta_copias, rutas_bd, carpeta_fotos, config=None):
    """Prueba ahora la última copia (la local y, si hay destino, la del
    destino), sin hacer una nueva, y guarda el resultado."""
    config = config or leer_config()
    with _cerrojo:
        estado = leer_estado()
        clave = cifrado_copias.clave_actual()
        claves = {clave.sal: clave} if clave else {}
        locales = _copias_bd_de(os.listdir(carpeta_copias)) if os.path.isdir(carpeta_copias) else {}
        if not locales:
            prueba = {"ok": False, "detalle": ["no hay ninguna copia automática"], "donde": "local"}
        else:
            nombre = max(locales, key=locales.get)
            prueba = probar_copia(lambda n: open(os.path.join(carpeta_copias, n), "rb"),
                                  nombre, _zips_fotos(carpeta_copias), claves, rutas_bd, carpeta_fotos)
            prueba["donde"] = "local"
            destino = destino_de(config)
            if destino and prueba["ok"]:
                try:
                    destino.comprobar()
                    remotos = destino.listar()
                    copias_destino = _copias_bd_de(remotos)
                    if not copias_destino:
                        raise FileNotFoundError(nombre)
                    prueba = probar_copia(destino.abrir, max(copias_destino, key=copias_destino.get),
                                          [n for n in remotos if n.startswith(PREFIJO_FOTOS) and n.endswith(".zip")],
                                          claves, rutas_bd, carpeta_fotos)
                    prueba["donde"] = "destino"
                except Exception as ex:
                    prueba = {"ok": False, "detalle": [str(ex) or ex.__class__.__name__], "donde": "destino"}
        prueba["fecha"] = _ahora().isoformat()
        estado["prueba"] = prueba
        _guardar_estado(estado)
        return prueba


# --------------------------------------------------------------- avisos

def problemas(carpeta_copias=None, config=None, estado=None):
    """Lo que hay que avisar de las copias, como lista de códigos:
    "copia_fallida" (la última copia ha fallado), "prueba_fallida" (la
    última copia no se ha podido restaurar en la prueba), "destino_fallido"
    (no se ha podido mandar al destino externo) y "sin_copia" (nunca se ha
    hecho una copia buena)."""
    config = config or leer_config()
    estado = estado if estado is not None else leer_estado()
    lista = []
    ultima = estado.get("ultima")
    if ultima and not ultima.get("ok") and ultima.get("error"):
        lista.append("copia_fallida")
    prueba = estado.get("prueba")
    if prueba and not prueba.get("ok"):
        lista.append("prueba_fallida")
    if config["destino"] and estado.get("destino", {}).get("error") \
            and estado["destino"].get("ruta") == DestinoCarpeta(config["destino"]).descripcion():
        lista.append("destino_fallido")
    if ultima and not ultima_copia_buena(carpeta_copias):
        lista.append("sin_copia")
    return lista
