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

"""
conexion_bd.py — Única puerta de entrada a las bases de datos SQLite, con
cifrado opcional (SQLCipher).

Todo el código abre las bases de datos con `conectar()` y usa el módulo
`sqlite3` que exporta este fichero (el de SQLCipher si está instalado, que abre
igual las bases de datos sin cifrar; si no, el estándar de Python). Así las
excepciones (`sqlite3.Error`…) y `sqlite3.Row` siempre son las del módulo con
el que se ha abierto la conexión.

Cifrado:
- Lo activa el administrador (Herramientas). La conversión se hace al arrancar
  MantPro, antes de abrir nada (`aplicar_conversion_pendiente`), para no
  pelearse con conexiones abiertas ni con el fichero -wal.
- Las dos bases de datos (`mantenimiento.db`, `almacen.db`) usan la misma
  clave aleatoria de 256 bits, que se guarda en el llavero del sistema
  (Administrador de credenciales de Windows, KWallet / GNOME Keyring en Linux)
  con `keyring`. Se usa como clave en bruto (`x'…'`), sin derivarla, así que
  abrir una conexión no cuesta nada.
- Si el llavero no tiene la clave (perfil nuevo, sistema reinstalado…), se pide
  la **clave de recuperación** que se mostró al activar el cifrado.
- Una base de datos está cifrada si no empieza por la cabecera de SQLite; se
  mira en cada conexión, así que conviven sin problema las cifradas y las que no.
- Las copias de seguridad llevan las bases de datos **sin cifrar** (para poder
  restaurarlas en otro equipo); para protegerlas está la contraseña de las
  copias (cifrado_copias.py).
"""

import hashlib
import json
import os
import threading

try:
    from sqlcipher3 import dbapi2 as sqlite3
    HAY_SQLCIPHER = True
except ImportError:   # p. ej. paquetes de distribuciones sin SQLCipher
    import sqlite3
    HAY_SQLCIPHER = False

from .rutas import DATA_DIR
from .seguridad import escribir_atomico


# Abrir y cerrar conexiones a la vez desde dos hilos (el servidor atendiendo al
# móvil y la interfaz refrescándose) puede dejar SQLite interbloqueado: cada
# hilo coge dos mutex internos (el de la tabla de ficheros abiertos y el del
# inodo) en orden contrario y la aplicación se congela. Se serializa solo la
# apertura y el cierre; las consultas siguen ejecutándose en paralelo.
_cerrojo_apertura = threading.RLock()


class _Conexion(sqlite3.Connection):
    def close(self):
        with _cerrojo_apertura:
            super().close()


def _abrir(ruta, **kwargs):
    """sqlite3.connect() con la apertura serializada (ver _cerrojo_apertura)."""
    kwargs.setdefault("factory", _Conexion)
    with _cerrojo_apertura:
        return sqlite3.connect(ruta, **kwargs)

CABECERA_SQLITE = b"SQLite format 3\x00"
NOMBRES_BD = ("mantenimiento.db", "almacen.db")
SERVICIO_LLAVERO = "MantPro"
RUTA_PENDIENTE = os.path.join(DATA_DIR, "conversion_bd_pendiente.json")
RUTA_CLAVE_FICHERO = os.path.join(DATA_DIR, "clave_bd.json")

_clave_hex = None   # clave en uso (64 caracteres hexadecimales) o None


class ClaveNoDisponible(Exception):
    """La base de datos está cifrada y no se encuentra su clave."""


class SinSQLCipher(Exception):
    """La base de datos está cifrada y esta instalación no trae SQLCipher."""


# ------------------------------------------------------------------ detección

def esta_cifrada(ruta):
    """True si [ruta] existe, no está vacía y no es una base de datos SQLite
    sin cifrar."""
    try:
        with open(ruta, "rb") as f:
            cabecera = f.read(len(CABECERA_SQLITE))
    except OSError:
        return False
    return len(cabecera) > 0 and cabecera != CABECERA_SQLITE


def rutas_bd(carpeta=None):
    carpeta = carpeta or DATA_DIR
    return [os.path.join(carpeta, n) for n in NOMBRES_BD]


def cifrado_activo(carpeta=None):
    """True si la base de datos principal está cifrada."""
    return esta_cifrada(rutas_bd(carpeta)[0])


# --------------------------------------------------------------------- claves

def _usuario_llavero(carpeta=None):
    # Una clave por carpeta de datos (una instalación portable y la normal
    # no se pisan)
    carpeta = os.path.abspath(carpeta or DATA_DIR)
    return "bd-" + hashlib.sha256(carpeta.encode("utf-8")).hexdigest()[:16]


# Llaveros de verdad (guardan la clave cifrada y de forma permanente). Se
# descartan otros que keyring puede elegir si están instalados, como
# keyrings.alt (fichero en claro) o keyutils (llavero del núcleo de Linux, que
# se borra al reiniciar: pediría la clave de recuperación en cada arranque).
LLAVEROS_ADMITIDOS = {"keyring.backends.Windows", "keyring.backends.SecretService",
                      "keyring.backends.kwallet", "keyring.backends.libsecret",
                      "keyring.backends.macOS"}


def _llavero():
    """El llavero del sistema (un backend de keyring admitido), o None."""
    try:
        import keyring
        from keyring.backends import chainer
        elegido = keyring.get_keyring()
        candidatos = elegido.backends if isinstance(elegido, chainer.ChainerBackend) else [elegido]
        validos = [b for b in candidatos if type(b).__module__ in LLAVEROS_ADMITIDOS]
        return max(validos, key=lambda b: b.priority) if validos else None
    except Exception:
        return None


def hay_llavero():
    return _llavero() is not None


def leer_clave_guardada(carpeta=None):
    """Clave guardada para esta carpeta de datos (llavero o, si no hay
    llavero, el fichero de respaldo), o None."""
    llavero = _llavero()
    if llavero is not None:
        try:
            valor = llavero.get_password(SERVICIO_LLAVERO, _usuario_llavero(carpeta))
            if valor:
                return valor
        except Exception:
            pass
    ruta = os.path.join(carpeta, "clave_bd.json") if carpeta else RUTA_CLAVE_FICHERO
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)["clave"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def guardar_clave(clave_hex, carpeta=None):
    """Guarda la clave en el llavero. Devuelve "llavero" o, si no hay
    llavero, "fichero" (se guarda en clave_bd.json, solo legible por el
    usuario: protege mucho menos y hay que avisar)."""
    llavero = _llavero()
    if llavero is not None:
        try:
            llavero.set_password(SERVICIO_LLAVERO, _usuario_llavero(carpeta), clave_hex)
            if llavero.get_password(SERVICIO_LLAVERO, _usuario_llavero(carpeta)) == clave_hex:
                # Si había un fichero de respaldo de antes, ya no hace falta
                ruta = os.path.join(carpeta, "clave_bd.json") if carpeta else RUTA_CLAVE_FICHERO
                try: os.remove(ruta)
                except OSError: pass
                return "llavero"
        except Exception:
            pass
    ruta = os.path.join(carpeta, "clave_bd.json") if carpeta else RUTA_CLAVE_FICHERO
    escribir_atomico(ruta, json.dumps({"clave": clave_hex}))
    try: os.chmod(ruta, 0o600)
    except OSError: pass
    return "fichero"


def borrar_clave_guardada(carpeta=None):
    llavero = _llavero()
    if llavero is not None:
        try: llavero.delete_password(SERVICIO_LLAVERO, _usuario_llavero(carpeta))
        except Exception: pass
    ruta = os.path.join(carpeta, "clave_bd.json") if carpeta else RUTA_CLAVE_FICHERO
    try: os.remove(ruta)
    except OSError: pass


def nueva_clave():
    return os.urandom(32).hex()


def formato_recuperacion(clave_hex):
    """La clave en grupos de 4 para apuntarla: «1A2B-3C4D-…»."""
    c = clave_hex.upper()
    return "-".join(c[i:i + 4] for i in range(0, len(c), 4))


def leer_recuperacion(texto):
    """Clave hexadecimal a partir de lo que escribe el usuario (con o sin
    guiones y espacios), o None si no tiene el formato."""
    limpio = "".join(ch for ch in (texto or "") if ch not in " -\t\r\n").lower()
    if len(limpio) != 64 or any(ch not in "0123456789abcdef" for ch in limpio):
        return None
    return limpio


def clave_abre(ruta, clave_hex):
    """True si [clave_hex] abre la base de datos cifrada [ruta]."""
    if not HAY_SQLCIPHER:
        return False
    con = _abrir(ruta)
    try:
        _poner_clave(con, clave_hex)
        con.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return True
    except sqlite3.DatabaseError:
        return False
    finally:
        con.close()


def usar_clave(clave_hex):
    """Fija la clave con la que se abren las bases de datos cifradas."""
    global _clave_hex
    _clave_hex = clave_hex


def preparar():
    """Al arrancar: si las bases de datos están cifradas, busca su clave.
    Lanza SinSQLCipher o ClaveNoDisponible si no se pueden abrir (el arranque
    pide entonces la clave de recuperación)."""
    if not any(esta_cifrada(r) for r in rutas_bd()):
        return
    if not HAY_SQLCIPHER:
        raise SinSQLCipher()
    cifradas = [r for r in rutas_bd() if esta_cifrada(r)]
    clave = leer_clave_guardada()
    if clave and all(clave_abre(r, clave) for r in cifradas):
        usar_clave(clave)
        return
    # La clave va a nombre de la carpeta de datos: si las bases de datos se
    # han copiado a otra (p. ej. a la del código fuente), se prueba la de la
    # carpeta de datos normal y, si las abre, se guarda también para esta.
    from .rutas import ruta_datos_sistema
    otra = ruta_datos_sistema()
    if os.path.abspath(otra) != os.path.abspath(DATA_DIR):
        clave = leer_clave_guardada(otra)
        if clave and all(clave_abre(r, clave) for r in cifradas):
            guardar_clave(clave)
            usar_clave(clave)
            return
    raise ClaveNoDisponible()


# ---------------------------------------------------------------- conexiones

def _poner_clave(con, clave_hex):
    con.execute(f"PRAGMA key = \"x'{clave_hex}'\"")


def conectar(ruta, **kwargs):
    """sqlite3.connect() que, si la base de datos está cifrada (o es nueva y
    las de esta carpeta van cifradas), le pone la clave."""
    if esta_cifrada(ruta):
        if not HAY_SQLCIPHER:
            raise SinSQLCipher()
        if _clave_hex is None:
            raise ClaveNoDisponible()
        con = _abrir(ruta, **kwargs)
        _poner_clave(con, _clave_hex)
        return con
    nueva = not os.path.exists(ruta) or os.path.getsize(ruta) == 0
    con = _abrir(ruta, **kwargs)
    if nueva and _clave_hex is not None and HAY_SQLCIPHER \
            and os.path.dirname(os.path.abspath(ruta)) == os.path.abspath(DATA_DIR):
        _poner_clave(con, _clave_hex)   # base de datos nueva en una carpeta cifrada
    return con


def adjuntar(con, ruta, alias):
    """ATTACH de [ruta] como [alias] en la conexión [con], con su clave si
    está cifrada (con clave en bruto, SQLCipher no la hereda de la principal)."""
    if esta_cifrada(ruta):
        if _clave_hex is None:
            raise ClaveNoDisponible()
        con.execute(f"ATTACH DATABASE ? AS {alias} KEY \"x'{_clave_hex}'\"", (ruta,))
    elif HAY_SQLCIPHER:
        con.execute(f"ATTACH DATABASE ? AS {alias} KEY ''", (ruta,))
    else:
        con.execute(f"ATTACH DATABASE ? AS {alias}", (ruta,))


def conectar_plano(ruta, **kwargs):
    """Conexión sin clave (para copias temporales sin cifrar)."""
    return _abrir(ruta, **kwargs)


# ------------------------------------------------- copias y restauraciones

def _exportar(con, destino, clave_destino_hex):
    """Copia todo lo de [con] a la base de datos nueva [destino], cifrada con
    esa clave o sin cifrar (None). Copia también user_version."""
    clave = f"x'{clave_destino_hex}'" if clave_destino_hex else ""
    version = con.execute("PRAGMA user_version").fetchone()[0]
    con.execute(f"ATTACH DATABASE ? AS destino KEY \"{clave}\"", (destino,))
    try:
        con.execute("BEGIN")   # lectura consistente mientras se exporta
        con.execute("SELECT sqlcipher_export('destino')")
        con.execute(f"PRAGMA destino.user_version = {int(version)}")
        con.execute("COMMIT")
    except BaseException:
        try: con.execute("ROLLBACK")
        except Exception: pass
        raise
    finally:
        con.execute("DETACH DATABASE destino")


def copiar_sin_cifrar(origen, destino, timeout=20):
    """Copia consistente de [origen] (cifrada o no) en [destino], SIN cifrar y
    en un único fichero (sin -wal). Devuelve el resultado de comprobar la
    integridad de la copia: "ok" si está bien."""
    if esta_cifrada(origen):
        fuente = conectar(origen, timeout=timeout)
        try:
            _exportar(fuente, destino, None)
        finally:
            fuente.close()
        copia = conectar_plano(destino)
        try:
            return copia.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            copia.close()
    # Sin cifrar: API de copia de SQLite (incluye lo que siga en el -wal)
    fuente = conectar_plano(origen, timeout=timeout)
    copia = conectar_plano(destino)
    try:
        fuente.backup(copia)
        copia.execute("PRAGMA journal_mode=DELETE")
        return copia.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        copia.close(); fuente.close()


def restaurar_desde_plano(plano, destino, timeout=20):
    """Vuelca la base de datos sin cifrar [plano] sobre [destino] (que puede
    estar abierta y cifrada) con la API de copia de SQLite. Si [destino] va
    cifrada, antes se pasa [plano] a una copia cifrada con la misma clave (la
    API de copia no mezcla bases de datos cifradas y sin cifrar)."""
    if esta_cifrada(destino) and _clave_hex is not None:
        cifrada = plano + ".cif"
        fuente = conectar_plano(plano)
        try:
            _exportar(fuente, cifrada, _clave_hex)
        finally:
            fuente.close()
        try:
            fuente = conectar(cifrada)
            destino_con = conectar(destino, timeout=timeout)
            try:
                fuente.backup(destino_con)
            finally:
                destino_con.close(); fuente.close()
        finally:
            try: os.remove(cifrada)
            except OSError: pass
        return
    fuente = conectar_plano(plano)
    destino_con = conectar(destino, timeout=timeout)
    try:
        fuente.backup(destino_con)
    finally:
        destino_con.close(); fuente.close()


# ------------------------------------------------------- cifrar / descifrar

def programar_conversion(accion):
    """Deja apuntado cifrar ("cifrar", con su clave ya guardada) o descifrar
    ("descifrar") las bases de datos la próxima vez que arranque MantPro."""
    escribir_atomico(RUTA_PENDIENTE, json.dumps({"accion": accion}))


def conversion_pendiente():
    try:
        with open(RUTA_PENDIENTE, encoding="utf-8") as f:
            return json.load(f).get("accion")
    except (OSError, ValueError, AttributeError):
        return None


def cancelar_conversion():
    try: os.remove(RUTA_PENDIENTE)
    except OSError: pass


def _borrar_auxiliares(ruta):
    for sufijo in ("-wal", "-shm", "-journal"):
        try: os.remove(ruta + sufijo)
        except OSError: pass


def convertir(accion, clave_hex, carpeta=None):
    """Cifra ("cifrar") o descifra ("descifrar") las bases de datos de la
    carpeta con [clave_hex]. Hay que llamarla sin ninguna conexión abierta (al
    arrancar). Primero se crean y comprueban todas las copias convertidas y
    solo entonces se cambian por las originales, así que si algo falla las
    bases de datos se quedan como estaban."""
    hechas = []
    try:
        for ruta in rutas_bd(carpeta):
            if not os.path.exists(ruta):
                continue
            cifrada = esta_cifrada(ruta)
            if (accion == "cifrar") == cifrada:
                continue   # ya está como se quiere
            nueva = ruta + ".convirtiendo"
            for f in (nueva, nueva + "-wal", nueva + "-shm"):
                try: os.remove(f)
                except OSError: pass
            con = _abrir(ruta, timeout=20)
            try:
                if cifrada:
                    _poner_clave(con, clave_hex)
                else:
                    # Vacía el -wal en el .db antes de copiar
                    con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                _exportar(con, nueva, clave_hex if accion == "cifrar" else None)
            finally:
                con.close()
            comprobar = _abrir(nueva)
            try:
                if accion == "cifrar":
                    _poner_clave(comprobar, clave_hex)
                resultado = comprobar.execute("PRAGMA integrity_check").fetchone()[0]
                if accion == "cifrar":
                    comprobar.execute("PRAGMA journal_mode=WAL")
            finally:
                comprobar.close()
            if resultado != "ok":
                raise sqlite3.DatabaseError(f"{os.path.basename(ruta)}: {resultado}")
            hechas.append((ruta, nueva))
    except BaseException:
        for _, nueva in hechas:
            try: os.remove(nueva)
            except OSError: pass
        raise
    for ruta, nueva in hechas:
        _borrar_auxiliares(ruta)
        os.replace(nueva, ruta)
        _borrar_auxiliares(nueva)
    return len(hechas)
