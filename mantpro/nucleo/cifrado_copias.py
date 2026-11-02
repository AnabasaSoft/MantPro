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
cifrado_copias.py — Copias de seguridad cifradas con contraseña.

Las copias siguen siendo ficheros ZIP normales, pero cada fichero de dentro
(bases de datos y fotos) va cifrado por separado. Así las copias de fotos por
año pueden seguir creciendo poco a poco, añadiendo solo las fotos nuevas, sin
tener que volver a cifrar todo el ZIP.

Formato de cada fichero cifrado dentro del ZIP (se guarda con su nombre más
la extensión ".mpc", para que una versión antigua de MantPro que no sepa
descifrar no lo restaure encima de la base de datos buena):

    "MPC1" (4) | sal (16) | comprobación (8) | nonce (12) | datos | etiqueta (16)

- La clave (AES-256) sale de la contraseña con scrypt (n=2^17, r=8, p=1) y la
  sal. No se usa el cifrado AES de los ZIP (WinZip AES) porque deriva la clave
  con PBKDF2-SHA1 de solo 1000 vueltas: se prueba por fuerza bruta muy rápido.
- Los datos se comprimen con zlib y se cifran con AES-256-GCM, que además
  detecta cualquier cambio o daño. El nombre del fichero va como dato
  autenticado: no se puede cambiar un fichero por otro de la copia.
- La comprobación (los 8 primeros bytes de HMAC-SHA256 de la clave) sirve para
  saber al momento si la contraseña es la buena, sin descifrar nada.

En el PC solo se guarda la clave derivada y su sal (en `clave_copias.json`,
en la carpeta de datos, que no va dentro de las copias), nunca la contraseña.
Así la copia automática al cerrar se cifra sin preguntar nada; lo que se
protege son las copias que salen del equipo (USB, NAS, nube).
"""

import base64
import hashlib
import hmac
import json
import os
import shutil
import tempfile
import zipfile
import zlib

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .rutas import DATA_DIR
from .seguridad import escribir_atomico
from . import conexion_bd

MAGIA = b"MPC1"
EXTENSION = ".mpc"
_LONG_SAL = 16
_LONG_COMPROBACION = 8
_LONG_NONCE = 12
_LONG_ETIQUETA = 16
_LONG_CABECERA = len(MAGIA) + _LONG_SAL + _LONG_COMPROBACION + _LONG_NONCE
_TROZO = 1024 * 1024
LONGITUD_MINIMA = 8

RUTA_CLAVE = os.path.join(DATA_DIR, "clave_copias.json")


class ErrorCifrado(Exception):
    """Fichero cifrado dañado o modificado (no pasa la autenticación)."""


class ContrasenaNecesaria(Exception):
    """Para descifrar hace falta una contraseña que no se ha dado."""


# ------------------------------------------------------------------ claves

def derivar_clave(contrasena, sal):
    """Clave AES-256 a partir de la contraseña (unas décimas de segundo y
    128 MB de memoria a propósito, para frenar la fuerza bruta)."""
    return Scrypt(salt=sal, length=32, n=2 ** 17, r=8, p=1).derive(contrasena.encode("utf-8"))


def _comprobacion(clave):
    return hmac.new(clave, b"MantPro copia cifrada", hashlib.sha256).digest()[:_LONG_COMPROBACION]


class Clave:
    """Clave derivada de una contraseña, con su sal."""

    def __init__(self, sal, clave):
        self.sal = sal
        self.clave = clave
        self.comprobacion = _comprobacion(clave)

    @classmethod
    def desde_contrasena(cls, contrasena, sal=None):
        sal = sal or os.urandom(_LONG_SAL)
        return cls(sal, derivar_clave(contrasena, sal))


def clave_actual():
    """La clave con la que se cifran las copias nuevas, o None si las copias
    no se cifran."""
    try:
        with open(RUTA_CLAVE, encoding="utf-8") as f:
            datos = json.load(f)
        return Clave(base64.b64decode(datos["sal"]), base64.b64decode(datos["clave"]))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def guardar_clave(clave):
    """Guarda [clave] como la de las copias nuevas (None: dejar de cifrar)."""
    if clave is None:
        try: os.remove(RUTA_CLAVE)
        except FileNotFoundError: pass
        return
    datos = {"version": 1,
             "sal": base64.b64encode(clave.sal).decode("ascii"),
             "clave": base64.b64encode(clave.clave).decode("ascii")}
    escribir_atomico(RUTA_CLAVE, json.dumps(datos))
    try: os.chmod(RUTA_CLAVE, 0o600)   # solo lo lee el usuario (en Linux)
    except OSError: pass


# ------------------------------------------------------- entradas del ZIP

def esta_cifrada(nombre):
    return nombre.endswith(EXTENSION)


def nombre_real(nombre):
    """Nombre del fichero original de una entrada del ZIP (sin ".mpc")."""
    return nombre[:-len(EXTENSION)] if esta_cifrada(nombre) else nombre


def _cifrar_flujo(origen, destino, nombre, clave):
    """Comprime y cifra lo que se lee de [origen] y lo escribe en [destino]."""
    nonce = os.urandom(_LONG_NONCE)
    cifrador = Cipher(algorithms.AES(clave.clave), modes.GCM(nonce)).encryptor()
    cifrador.authenticate_additional_data(nombre.encode("utf-8"))
    destino.write(MAGIA + clave.sal + clave.comprobacion + nonce)
    compresor = zlib.compressobj(6)
    while True:
        trozo = origen.read(_TROZO)
        if not trozo:
            break
        destino.write(cifrador.update(compresor.compress(trozo)))
    destino.write(cifrador.update(compresor.flush()))
    destino.write(cifrador.finalize())
    destino.write(cifrador.tag)


def escribir_entrada(zipf, origen, nombre, clave):
    """Añade al ZIP el fichero [origen] (ruta o fichero abierto) con el nombre
    [nombre], cifrado con [clave] o sin cifrar si [clave] es None."""
    if clave is None:
        if isinstance(origen, str):
            zipf.write(origen, arcname=nombre, compress_type=zipfile.ZIP_DEFLATED)
        else:
            info = zipfile.ZipInfo(nombre); info.compress_type = zipfile.ZIP_DEFLATED
            with zipf.open(info, "w", force_zip64=True) as destino:
                shutil.copyfileobj(origen, destino, _TROZO)
        return
    info = zipfile.ZipInfo(nombre + EXTENSION)
    info.compress_type = zipfile.ZIP_STORED   # lo cifrado no se comprime
    if isinstance(origen, str):
        info.date_time = zipfile.ZipInfo.from_file(origen).date_time
    with zipf.open(info, "w", force_zip64=True) as destino:
        if isinstance(origen, str):
            with open(origen, "rb") as f:
                _cifrar_flujo(f, destino, nombre, clave)
        else:
            _cifrar_flujo(origen, destino, nombre, clave)


def datos_cifrado(zipf, nombre):
    """(sal, comprobación) de una entrada cifrada, o None si no lo está."""
    if not esta_cifrada(nombre):
        return None
    with zipf.open(nombre) as f:
        cabecera = f.read(_LONG_CABECERA)
    if len(cabecera) < _LONG_CABECERA or not cabecera.startswith(MAGIA):
        raise ErrorCifrado(nombre)
    inicio = len(MAGIA)
    return (cabecera[inicio:inicio + _LONG_SAL],
            cabecera[inicio + _LONG_SAL:inicio + _LONG_SAL + _LONG_COMPROBACION])


def _descifrar_flujo(zipf, nombre, destino, claves):
    """Descifra la entrada [nombre] y escribe el original en [destino].
    [claves] es un diccionario sal -> Clave. Si los datos no están intactos
    lanza ErrorCifrado (y lo escrito en [destino] no vale)."""
    tamano = zipf.getinfo(nombre).file_size
    with zipf.open(nombre) as f:
        cabecera = f.read(_LONG_CABECERA)
        if len(cabecera) < _LONG_CABECERA or not cabecera.startswith(MAGIA):
            raise ErrorCifrado(nombre)
        i = len(MAGIA)
        sal = cabecera[i:i + _LONG_SAL]; i += _LONG_SAL
        comprobacion = cabecera[i:i + _LONG_COMPROBACION]; i += _LONG_COMPROBACION
        nonce = cabecera[i:i + _LONG_NONCE]
        clave = claves.get(sal)
        if clave is None or not hmac.compare_digest(clave.comprobacion, comprobacion):
            raise ContrasenaNecesaria(nombre)
        descifrador = Cipher(algorithms.AES(clave.clave), modes.GCM(nonce)).decryptor()
        descifrador.authenticate_additional_data(nombre_real(nombre).encode("utf-8"))
        descompresor = zlib.decompressobj()
        quedan = tamano - _LONG_CABECERA - _LONG_ETIQUETA
        if quedan < 0:
            raise ErrorCifrado(nombre)
        while quedan > 0:
            trozo = f.read(min(_TROZO, quedan))
            if not trozo:
                raise ErrorCifrado(nombre)
            quedan -= len(trozo)
            try:
                destino.write(descompresor.decompress(descifrador.update(trozo)))
            except zlib.error:   # datos cambiados: ni siquiera se descomprimen
                raise ErrorCifrado(nombre) from None
        etiqueta = f.read(_LONG_ETIQUETA)
        try:
            descifrador.finalize_with_tag(etiqueta)
        except (InvalidTag, ValueError):
            raise ErrorCifrado(nombre) from None
        try:
            destino.write(descompresor.flush())
        except zlib.error:
            raise ErrorCifrado(nombre) from None
        if not descompresor.eof:
            raise ErrorCifrado(nombre)


def leer_entrada(zipf, nombre, destino, claves):
    """Escribe en el fichero abierto [destino] el contenido original de la
    entrada [nombre], descifrándola si hace falta."""
    if esta_cifrada(nombre):
        _descifrar_flujo(zipf, nombre, destino, claves)
    else:
        with zipf.open(nombre) as f:
            shutil.copyfileobj(f, destino, _TROZO)


def ruta_segura(carpeta, nombre):
    """Ruta dentro de [carpeta] para la entrada [nombre] del ZIP, o None si
    el nombre intenta salirse de ella (rutas absolutas, "..")."""
    partes = [p for p in nombre.replace("\\", "/").split("/") if p not in ("", ".")]
    if not partes or any(p == ".." or ":" in p for p in partes):
        return None
    ruta = os.path.join(os.path.abspath(carpeta), *partes)
    if os.path.commonpath([ruta, os.path.abspath(carpeta)]) != os.path.abspath(carpeta):
        return None
    return ruta


def extraer_entrada(zipf, nombre, carpeta, claves):
    """Extrae la entrada [nombre] en [carpeta] con su nombre original,
    descifrándola si hace falta. Escribe en un temporal y solo lo pone en su
    sitio si está intacto. Devuelve la ruta creada (None si se ha saltado)."""
    ruta = ruta_segura(carpeta, nombre_real(nombre))
    if ruta is None or nombre.endswith("/"):
        return None
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    fd, temporal = tempfile.mkstemp(dir=os.path.dirname(ruta), prefix=".tmp_")
    try:
        with os.fdopen(fd, "wb") as destino:
            leer_entrada(zipf, nombre, destino, claves)
        os.replace(temporal, ruta)
    except BaseException:
        try: os.remove(temporal)
        except OSError: pass
        raise
    return ruta


def restaurar_bd(zipf, nombre, ruta_bd, claves):
    """Restaura la base de datos [nombre] del ZIP sobre [ruta_bd] con la API
    de copia de SQLite: así se respetan las conexiones abiertas y el fichero
    -wal que haya (sobrescribir el .db a mano podía mezclarlo con un -wal
    antiguo). Antes comprueba que la copia está intacta."""
    fd, temporal = tempfile.mkstemp(suffix=".db"); os.close(fd)
    try:
        with open(temporal, "wb") as destino:
            leer_entrada(zipf, nombre, destino, claves)
        fuente = conexion_bd.conectar_plano(temporal)
        try:
            resultado = fuente.execute("PRAGMA integrity_check").fetchone()[0]
        except conexion_bd.sqlite3.DatabaseError as ex:
            resultado = str(ex)   # no es una base de datos (p. ej. copia cifrada con SQLCipher)
        finally:
            fuente.close()
        if resultado != "ok":
            raise ErrorCifrado(f"{nombre_real(nombre)}: {resultado}")
        # Si la base de datos de destino está cifrada, sigue cifrada
        conexion_bd.restaurar_desde_plano(temporal, ruta_bd)
    finally:
        try: os.remove(temporal)
        except OSError: pass


# ------------------------------------------------------- contraseñas pedidas

def sales_de(rutas_zip):
    """{sal: comprobación} de todas las entradas cifradas de esos ZIP. Los ZIP
    que no se pueden leer se saltan (ya fallarán al restaurar)."""
    sales = {}
    for ruta in rutas_zip:
        try:
            with zipfile.ZipFile(ruta) as zf:
                for nombre in zf.namelist():
                    datos = datos_cifrado(zf, nombre)
                    if datos:
                        sales[datos[0]] = datos[1]
        except (OSError, zipfile.BadZipFile, ErrorCifrado):
            pass
    return sales


def probar_contrasena(contrasena, sales):
    """Claves de las sales de [sales] ({sal: comprobación}) que abre esa
    contraseña: {sal: Clave}."""
    abiertas = {}
    for sal, comprobacion in sales.items():
        clave = Clave.desde_contrasena(contrasena, sal)
        if hmac.compare_digest(clave.comprobacion, comprobacion):
            abiertas[sal] = clave
    return abiertas


# ------------------------------------------- cifrar las copias que ya hay

def zips_de_copias(carpeta):
    """ZIP de copias de una carpeta (copias automáticas, de fotos y previas)."""
    if not os.path.isdir(carpeta):
        return []
    return sorted(os.path.join(carpeta, f) for f in os.listdir(carpeta)
                  if f.endswith(".zip") and os.path.isfile(os.path.join(carpeta, f)))


def _hay_que_rehacer(zf, conocidas, nueva):
    for nombre in zf.namelist():
        datos = datos_cifrado(zf, nombre)
        if datos is None:
            if nueva is not None:
                return True
        elif datos[0] in conocidas and (nueva is None or datos[0] != nueva.sal):
            return True
    return False


def recifrar_zip(ruta, conocidas, nueva, progreso=None):
    """Rehace el ZIP [ruta] con la clave [nueva] (None: sin cifrar). Se
    vuelven a cifrar las entradas sin cifrar y las cifradas con una de las
    claves [conocidas] ({sal: Clave}); las demás se dejan tal cual. Mantiene la
    fecha del fichero (la rotación de copias va por fecha). Devuelve True si
    lo ha cambiado."""
    with zipfile.ZipFile(ruta) as zf:
        if not _hay_que_rehacer(zf, conocidas, nueva):
            return False
    estado = os.stat(ruta)
    temporal = ruta + ".tmp"
    try:
        with zipfile.ZipFile(ruta) as origen, \
             zipfile.ZipFile(temporal, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as nuevo:
            for info in origen.infolist():
                nombre = info.filename
                datos = datos_cifrado(origen, nombre)
                igual = (datos is not None and (datos[0] not in conocidas
                                                or (nueva is not None and datos[0] == nueva.sal))) \
                        or (datos is None and nueva is None)
                if igual:
                    copia = zipfile.ZipInfo(nombre, info.date_time)
                    copia.compress_type = info.compress_type
                    with origen.open(info) as f, nuevo.open(copia, "w", force_zip64=True) as destino:
                        shutil.copyfileobj(f, destino, _TROZO)
                else:
                    with tempfile.TemporaryFile() as plano:
                        leer_entrada(origen, nombre, plano, conocidas)
                        plano.seek(0)
                        escribir_entrada(nuevo, plano, nombre_real(nombre), nueva)
                if progreso:
                    progreso()
        os.replace(temporal, ruta)
    except BaseException:
        try: os.remove(temporal)
        except OSError: pass
        raise
    os.utime(ruta, (estado.st_atime, estado.st_mtime))
    return True


def entradas_de(rutas_zip):
    """Número total de entradas de esos ZIP (para la barra de progreso)."""
    total = 0
    for ruta in rutas_zip:
        try:
            with zipfile.ZipFile(ruta) as zf:
                total += len(zf.namelist())
        except (OSError, zipfile.BadZipFile):
            pass
    return total
