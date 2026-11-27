# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# MantPro - Sesiones temporales de subida de fotos (ventana de avisos)
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

"""Sesiones temporales de subida de fotos: registro en memoria para recibir fotos desde el navegador de un móvil
sin token de usuario (ventana de avisos, modo quiosco). Cada sesión vale para un solo aviso, caduca a los
MINUTOS_VALIDEZ y admite como mucho MAX_FOTOS. No da acceso a ningún dato.

Seguro entre hilos (Flask atiende cada petición en uno). Hoy vive en la memoria del proceso del PC: para MantPro
Cloud o MantPro Web habría que guardarlo en un almacenamiento compartido entre workers (ver ROADMAP.md)."""

import os
import secrets
import threading
import time

MAX_FOTOS = 20
# Variable de entorno solo para las pruebas: minutos (admite decimales) que vale una sesión, para poder comprobar la
# caducidad sin esperar media hora (MantPro Web la hereda en el proceso del trabajador de cada empresa)
MINUTOS_VALIDEZ = float(os.environ.get("MANTPRO_SUBIDAS_MINUTOS") or 30)

_cerrojo = threading.Lock()
_sesiones = {}          # token -> {"caduca": time.monotonic(), "fotos": int, "nombres": [str]}


def _purgar():
    """Quita las caducadas. Hay que llamarla con el cerrojo cogido."""
    ahora = time.monotonic()
    for token in [t for t, s in _sesiones.items() if s["caduca"] <= ahora]:
        del _sesiones[token]


def crear(minutos=MINUTOS_VALIDEZ):
    """Crea una sesión nueva y devuelve su token."""
    token = secrets.token_urlsafe(24)
    with _cerrojo:
        _purgar()
        _sesiones[token] = {"caduca": time.monotonic() + minutos * 60, "fotos": 0, "nombres": []}
    return token


def _vigente(token):
    """La sesión si existe y no ha caducado (con el cerrojo cogido)."""
    s = _sesiones.get(token) if token else None
    if s is not None and s["caduca"] <= time.monotonic():
        del _sesiones[token]
        return None
    return s


def alargar(token, minutos=MINUTOS_VALIDEZ):
    """Renueva la caducidad de un token aún válido (que no caduque con el QR abierto ni mientras llegan fotos).
    False si no existe o ya caducó: un token caducado no se resucita."""
    with _cerrojo:
        s = _vigente(token)
        if s is None:
            return False
        s["caduca"] = time.monotonic() + minutos * 60
        return True


def valido(token):
    with _cerrojo:
        return _vigente(token) is not None


def admite_otra(token):
    with _cerrojo:
        s = _vigente(token)
        return s is not None and s["fotos"] < MAX_FOTOS


def apuntar(token, nombre):
    """Suma una foto a la sesión. False si ya no es válida o está llena."""
    with _cerrojo:
        s = _vigente(token)
        if s is None or s["fotos"] >= MAX_FOTOS:
            return False
        s["fotos"] += 1
        s["nombres"].append(nombre)
        return True


def recibidas(token):
    """Copia de la lista de nombres recibidos por [token], en orden de llegada (vacía si no es válido)."""
    with _cerrojo:
        s = _vigente(token)
        return list(s["nombres"]) if s is not None else []


def quitar(token, nombre):
    """Saca [nombre] de la lista del token (la web permite quitar una miniatura). True si estaba."""
    with _cerrojo:
        s = _vigente(token)
        if s is None or nombre not in s["nombres"]:
            return False
        s["nombres"].remove(nombre)
        s["fotos"] = max(0, s["fotos"] - 1)
        return True


def anular(token):
    with _cerrojo:
        _sesiones.pop(token, None)
