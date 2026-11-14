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
seguridad.py — Utilidades de seguridad y de escritura segura de ficheros:

- Límite de intentos de inicio de sesión, contra ataques de fuerza bruta.
- Comprobación de las fotos que llegan desde los móviles.
- Escritura atómica de ficheros (un corte de luz a mitad no deja el fichero
  a medias) y copia consistente de las bases de datos SQLite.
"""

import os
import tempfile
import threading
import time

# ---------------------------------------------------------------- inicio de sesión

class LimiteIntentos:
    """Cuenta los inicios de sesión fallidos por clave (usuario, IP…) y
    bloquea esa clave un rato cuando pasan de [maximo] en [ventana] segundos.
    Vive en memoria: al reiniciar MantPro se olvida, que es suficiente para
    frenar a quien prueba contraseñas a ciegas."""

    def __init__(self, maximo, ventana=15 * 60, bloqueo=15 * 60):
        self.maximo, self.ventana, self.bloqueo = maximo, ventana, bloqueo
        self._fallos = {}      # clave -> [instantes de los fallos recientes]
        self._hasta = {}       # clave -> instante en que termina el bloqueo
        self._cerrojo = threading.Lock()

    def segundos_bloqueo(self, clave):
        """Segundos que le quedan de bloqueo a [clave] (0 si no lo está)."""
        with self._cerrojo:
            restante = self._hasta.get(clave, 0) - time.monotonic()
            if restante <= 0:
                self._hasta.pop(clave, None)
                return 0
            return int(restante) + 1

    def fallo(self, clave):
        """Apunta un intento fallido. Devuelve True si con este se bloquea."""
        ahora = time.monotonic()
        bloquea = False
        with self._cerrojo:
            recientes = [t for t in self._fallos.get(clave, []) if ahora - t < self.ventana] + [ahora]
            if len(recientes) >= self.maximo:
                self._hasta[clave] = ahora + self.bloqueo
                recientes = []
                bloquea = True
            self._fallos[clave] = recientes
        return bloquea

    def acierto(self, clave):
        with self._cerrojo:
            self._fallos.pop(clave, None)
            self._hasta.pop(clave, None)


# Desde los móviles (por la red): 5 fallos seguidos bloquean ese usuario 15
# minutos, y 20 desde una misma IP la bloquean (prueba varios usuarios).
LOGIN_RED_USUARIO = LimiteIntentos(maximo=5)
LOGIN_RED_IP = LimiteIntentos(maximo=20)
# En la ventana del PC se lleva aparte, para que un ataque desde la red no
# deje sin poder entrar a quien está sentado delante del ordenador.
LOGIN_LOCAL = LimiteIntentos(maximo=5, bloqueo=60)


# ---------------------------------------------------------------- fotos recibidas

# Vídeos de la colección de un trabajo (los graba el móvil). Viajan, se guardan y se
# sincronizan exactamente igual que las fotos, así que sus extensiones van también en
# EXTENSIONES_FOTO; donde haga falta distinguirlos (para enseñarlos), es_video().
EXTENSIONES_VIDEO = {".mp4", ".m4v", ".mov", ".3gp", ".webm"}
EXTENSIONES_FOTO = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic", ".heif"} | EXTENSIONES_VIDEO
# Formatos que Pillow sabe abrir; HEIC/HEIF no, y se aceptan solo por extensión.
_COMPROBABLES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
TAMANO_MAXIMO_FOTO = 30 * 1024 * 1024      # 30 MB por foto
TAMANO_MAXIMO_VIDEO = 100 * 1024 * 1024    # 100 MB por vídeo (el móvil graba como mucho 30 s)
# Por envío: una colección con varios vídeos y fotos. Flask guarda en disco lo que recibe,
# así que esto no se queda entero en memoria.
TAMANO_MAXIMO_PETICION = 1024 * 1024 * 1024


def es_video(nombre):
    """True si [nombre] (nombre o ruta) es un vídeo por su extensión."""
    return os.path.splitext(str(nombre or ""))[1].lower() in EXTENSIONES_VIDEO


def tamano_maximo(nombre):
    """Tamaño máximo admitido para [nombre]: el de los vídeos o el de las fotos."""
    return TAMANO_MAXIMO_VIDEO if es_video(nombre) else TAMANO_MAXIMO_FOTO


def _video_valido(extension, cabecera):
    """Comprobación ligera de que el contenido es de verdad un vídeo del formato de su
    extensión: MP4/MOV/3GP llevan la caja «ftyp» en los bytes 4-8; WebM empieza por la
    cabecera EBML."""
    if extension == ".webm":
        return cabecera[:4] == b"\x1a\x45\xdf\xa3"
    return cabecera[4:8] == b"ftyp"


def foto_valida(ruta):
    """True si el fichero tiene extensión de imagen o de vídeo, no pasa del tamaño
    máximo de su tipo y es de verdad lo que dice su extensión (las imágenes que
    Pillow conoce, abriéndolas; los vídeos, por su cabecera)."""
    extension = os.path.splitext(ruta)[1].lower()
    if extension not in EXTENSIONES_FOTO:
        return False
    try:
        tamano = os.path.getsize(ruta)
        if tamano == 0 or tamano > tamano_maximo(ruta):
            return False
    except OSError:
        return False
    if extension in EXTENSIONES_VIDEO:
        try:
            with open(ruta, "rb") as f:
                return _video_valido(extension, f.read(16))
        except OSError:
            return False
    if extension not in _COMPROBABLES:
        return True
    try:
        from PIL import Image
        with Image.open(ruta) as imagen:
            imagen.verify()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- escritura segura

def escribir_atomico(ruta, contenido, modo="w", encoding="utf-8"):
    """Escribe [contenido] en un temporal de la misma carpeta y lo renombra
    sobre [ruta]: o queda el fichero nuevo entero o el anterior intacto."""
    carpeta = os.path.dirname(os.path.abspath(ruta))
    fd, temporal = tempfile.mkstemp(dir=carpeta, prefix=".tmp_", suffix=os.path.basename(ruta))
    try:
        with os.fdopen(fd, modo, **({} if "b" in modo else {"encoding": encoding})) as f:
            f.write(contenido)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, ruta)
    except BaseException:
        try: os.remove(temporal)
        except OSError: pass
        raise


def copia_consistente_sqlite(origen, destino):
    """Copia la base de datos [origen] en [destino], sin cifrar y en un solo
    fichero, de forma consistente: incluye lo que todavía está en el fichero
    -wal (copiar el .db a mano lo perdería si hay conexiones abiertas) y sirve
    también si la base de datos está cifrada (ver conexion_bd). Devuelve el
    resultado de comprobar la integridad de la copia: "ok" si está bien."""
    from .conexion_bd import copiar_sin_cifrar
    return copiar_sin_cifrar(origen, destino)


def anadir_bd_a_zip(zipf, ruta_bd, clave=None):
    """Añade al ZIP abierto [zipf] una copia consistente de [ruta_bd], con
    su mismo nombre (cifrada si se da [clave], ver cifrado_copias). Devuelve
    el resultado de la comprobación de integridad ("ok" si está bien) o None
    si la base de datos no existe."""
    if not ruta_bd or not os.path.exists(ruta_bd):
        return None
    fd, temporal = tempfile.mkstemp(suffix=".db"); os.close(fd)
    try:
        integridad = copia_consistente_sqlite(ruta_bd, temporal)
        if clave is None:
            zipf.write(temporal, arcname=os.path.basename(ruta_bd))
        else:
            from .cifrado_copias import escribir_entrada
            escribir_entrada(zipf, temporal, os.path.basename(ruta_bd), clave)
    finally:
        try: os.remove(temporal)
        except OSError: pass
    return integridad
