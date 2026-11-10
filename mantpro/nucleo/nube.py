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

"""Cliente de MantPro Cloud: inicio de sesión, licencia y cierre de sesión.

MantPro sigue funcionando entero sin la nube (modo local). Iniciar sesión solo
vincula este PC con una cuenta de MantPro Cloud para sincronizar. El servidor
únicamente INFORMA del estado de la licencia; lo que se hace con él lo decide
este cliente (ver estado_efectivo). Nunca se bloquean ni se retienen los datos
locales.

Qué se guarda en este PC:
- El token de la sesión, en el llavero del sistema (o, si no hay, en un fichero
  de la carpeta de datos que solo puede leer el usuario).
- Los datos de la cuenta y la última licencia conocida, en nube.json.
- La contraseña NO se guarda nunca: solo viaja al iniciar sesión.

Los errores se devuelven como CÓDIGOS (segundo valor de la tupla), nunca como
texto: la interfaz los traduce a cada idioma."""

import json
import os
import socket
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

import requests

from .rutas import DATA_DIR
from .seguridad import escribir_atomico
from . import conexion_bd

URL_POR_DEFECTO = "https://mantpro-cloud.com/api/v1"
URL_WEB = "https://www.mantpro-cloud.com"     # web de MantPro Cloud (se abre en el navegador)
TIMEOUT = 10                       # segundos por petición
SERVICIO_LLAVERO = "MantPro Cloud"
GRACIA_POR_DEFECTO = 7             # si el servidor no dice otra cosa

# Códigos de error que devuelve este módulo. Los que manda el servidor se pasan tal cual.
SIN_CONEXION = "sin_conexion"
RESPUESTA_NO_VALIDA = "respuesta_no_valida"
SESION_CADUCADA = "sesion_caducada"
SIN_SESION = "sin_sesion"
URL_NO_VALIDA = "url_no_valida"


def url_base():
    """Dirección de la API. Solo se cambia con MANTPRO_CLOUD_URL (pruebas o
    servidor propio); debe ser HTTPS, salvo en esta misma máquina."""
    return (os.environ.get("MANTPRO_CLOUD_URL") or URL_POR_DEFECTO).rstrip("/")


def _url_valida(url):
    p = urlparse(url)
    if p.scheme == "https" and p.hostname:
        return True
    return p.scheme == "http" and p.hostname in ("localhost", "127.0.0.1", "::1")


def _carpeta(carpeta):
    return carpeta or DATA_DIR


def _ruta_datos(carpeta=None):
    return os.path.join(_carpeta(carpeta), "nube.json")


def _ruta_token(carpeta=None):
    return os.path.join(_carpeta(carpeta), "nube_token.json")


def _usuario_llavero(carpeta=None):
    return "nube-" + conexion_bd._usuario_llavero(_carpeta(carpeta))


# ---------------------------------------------------------------- estado guardado

def sesion(carpeta=None):
    """Datos guardados de la sesión (cuenta, empresa, licencia, comprobada), o
    None si este PC no tiene sesión de MantPro Cloud. No incluye el token."""
    try:
        with open(_ruta_datos(carpeta), encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) and datos.get("cuenta") else None
    except (OSError, ValueError):
        return None


def _guardar_sesion(datos, carpeta=None):
    ruta = _ruta_datos(carpeta)
    escribir_atomico(ruta, json.dumps(datos, ensure_ascii=False, indent=1))
    try:
        os.chmod(ruta, 0o600)
    except OSError:
        pass


def token(carpeta=None):
    """Token de la sesión (llavero o fichero de respaldo), o None."""
    llavero = conexion_bd._llavero()
    if llavero is not None:
        try:
            valor = llavero.get_password(SERVICIO_LLAVERO, _usuario_llavero(carpeta))
            if valor:
                return valor
        except Exception:
            pass
    try:
        with open(_ruta_token(carpeta), encoding="utf-8") as f:
            return json.load(f)["token"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _guardar_token(valor, carpeta=None):
    """Guarda el token en el llavero; si no hay, en un fichero que solo lee el usuario."""
    llavero = conexion_bd._llavero()
    if llavero is not None:
        try:
            llavero.set_password(SERVICIO_LLAVERO, _usuario_llavero(carpeta), valor)
            if llavero.get_password(SERVICIO_LLAVERO, _usuario_llavero(carpeta)) == valor:
                try:
                    os.remove(_ruta_token(carpeta))
                except OSError:
                    pass
                return "llavero"
        except Exception:
            pass
    ruta = _ruta_token(carpeta)
    escribir_atomico(ruta, json.dumps({"token": valor}))
    try:
        os.chmod(ruta, 0o600)
    except OSError:
        pass
    return "fichero"


def _borrar_token(carpeta=None):
    llavero = conexion_bd._llavero()
    if llavero is not None:
        try:
            llavero.delete_password(SERVICIO_LLAVERO, _usuario_llavero(carpeta))
        except Exception:
            pass
    try:
        os.remove(_ruta_token(carpeta))
    except OSError:
        pass


# ---------------------------------------------------------------- red

def _ahora_iso(ahora=None):
    ahora = ahora or datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    return ahora.strftime("%Y-%m-%dT%H:%M:%S")


def _peticion(metodo, ruta, json_cuerpo=None, token_=None):
    """Una petición a la API. Devuelve (datos, None) o (None, código)."""
    base = url_base()
    if not _url_valida(base):
        return None, URL_NO_VALIDA
    cabeceras = {"Accept": "application/json"}
    if token_:
        cabeceras["Authorization"] = "Bearer " + token_
    try:
        r = requests.request(metodo, base + ruta, json=json_cuerpo, headers=cabeceras, timeout=TIMEOUT)
    except (requests.RequestException, socket.error, OSError):
        return None, SIN_CONEXION
    try:
        cuerpo = r.json()
    except ValueError:
        return None, RESPUESTA_NO_VALIDA
    if not isinstance(cuerpo, dict):
        return None, RESPUESTA_NO_VALIDA
    if r.status_code >= 400:
        codigo = cuerpo.get("error")
        return None, codigo if isinstance(codigo, str) and codigo else RESPUESTA_NO_VALIDA
    return cuerpo, None


def iniciar_sesion(correo, password, dispositivo=None, carpeta=None, ahora=None):
    """Inicia sesión en MantPro Cloud y la guarda en este PC.
    Devuelve (datos de la sesión, None) o (None, código de error)."""
    correo = (correo or "").strip()
    if not correo or not password:
        return None, "datos_incompletos"
    cuerpo = {"correo": correo, "password": password}
    if dispositivo:
        cuerpo["dispositivo"] = dispositivo
    res, error = _peticion("POST", "/login", cuerpo)
    if error:
        return None, error
    try:
        datos = {"cuenta": res["cuenta"], "empresa": res["empresa"], "licencia": res["licencia"],
                 "expira": res.get("expira"), "comprobada": _ahora_iso(ahora)}
        nuevo_token = res["token"]
        if not isinstance(nuevo_token, str) or not nuevo_token:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        return None, RESPUESTA_NO_VALIDA
    _guardar_token(nuevo_token, carpeta)
    _guardar_sesion(datos, carpeta)
    return datos, None


def comprobar_licencia(carpeta=None, ahora=None):
    """Pregunta al servidor la licencia y la guarda. Devuelve (datos de la sesión,
    None) o (None, código). Si el servidor dice que la sesión ya no vale
    (SESION_CADUCADA), se borra la sesión de este PC; si no hay conexión se
    conserva la última licencia conocida (el cliente aplica el margen de gracia)."""
    actual = sesion(carpeta)
    tk = token(carpeta)
    if not actual or not tk:
        return None, SIN_SESION
    res, error = _peticion("GET", "/licencia", token_=tk)
    if error == "no_autorizado":
        cerrar_sesion(carpeta, avisar=False)
        return None, SESION_CADUCADA
    if error:
        return None, error
    if not isinstance(res.get("licencia"), dict):
        return None, RESPUESTA_NO_VALIDA
    actual["licencia"] = res["licencia"]
    for clave in ("cuenta", "empresa"):
        if isinstance(res.get(clave), dict):
            actual[clave] = res[clave]
    actual["comprobada"] = _ahora_iso(ahora)
    _guardar_sesion(actual, carpeta)
    return actual, None


def cerrar_sesion(carpeta=None, avisar=True):
    """Cierra la sesión en este PC (siempre) y, si hay conexión, en el servidor
    (para que el token deje de valer). Nunca toca los datos de mantenimiento."""
    tk = token(carpeta)
    if avisar and tk:
        _peticion("POST", "/logout", token_=tk)       # si falla, da igual: el token caduca solo
    _borrar_token(carpeta)
    try:
        os.remove(_ruta_datos(carpeta))
    except OSError:
        pass


# ---------------------------------------------------------------- licencia

def estado_efectivo(licencia, hoy=None):
    """Qué le toca hacer a este PC con la licencia que conoce:

    - "activa":     vigente.
    - "gracia":     ya pasó la fecha, pero dentro del margen de gracia (se sigue
                    sincronizando y se avisa).
    - "vencida":    pasado el margen. Sin sincronizar con la nube; MantPro sigue
                    funcionando en local y se puede exportar todo.
    - "suspendida": la empresa está suspendida (sin margen).
    - "desconocida": no hay licencia guardada."""
    if not isinstance(licencia, dict):
        return "desconocida"
    if licencia.get("estado") == "suspendida":
        return "suspendida"
    hasta = licencia.get("valida_hasta")
    if not hasta:
        return "vencida"
    hoy = hoy or date.today()
    try:
        limite = date.fromisoformat(hasta)
    except (TypeError, ValueError):
        return "desconocida"
    if hoy <= limite:
        return "activa"
    gracia = licencia.get("gracia_dias")
    gracia = gracia if isinstance(gracia, int) and gracia >= 0 else GRACIA_POR_DEFECTO
    return "gracia" if hoy <= limite + timedelta(days=gracia) else "vencida"


def dias_restantes(licencia, hoy=None):
    """Días hasta el fin de la licencia (negativo si ya pasó), o None."""
    try:
        return (date.fromisoformat(licencia["valida_hasta"]) - (hoy or date.today())).days
    except (KeyError, TypeError, ValueError):
        return None
