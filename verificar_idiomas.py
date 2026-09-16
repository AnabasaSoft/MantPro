#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# verificar_idiomas.py — Comprueba que todos los idiomas tengan las mismas
# claves que el español (idioma de referencia), tanto en la app de PC
# (idiomas/*.json) como en las dos apps móviles
# (mantenimiento_app y mantpro_stock_app, lib/i18n/*.dart).
#
# Si a algún idioma le falta una clave, se añade automáticamente con el
# texto en español como valor provisional, para que no quede nada sin
# traducir a medias (el texto en español hace de recordatorio de que hay
# que traducirlo, en vez de quedar mostrando la clave en bruto o cayendo
# silenciosamente al español).
#
# Uso:
#   python3 verificar_idiomas.py
#
# Correr este script siempre que se añada o modifique cualquier texto de
# la interfaz (PC o móvil), al terminar los cambios (ver regla en CLAUDE.md).

import json
import os
import re

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
DIR_IDIOMAS_PC = os.path.join(RUTA_BASE, "idiomas")
IDIOMA_REFERENCIA = "es"

CARPETAS_I18N_MOVIL = [
    os.path.join(RUTA_BASE, "mantenimiento_app", "lib", "i18n"),
    os.path.join(RUTA_BASE, "mantpro_stock_app", "lib", "i18n"),
]

_RE_PAR_DART = re.compile(r'"([a-zA-Z0-9_]+)"\s*:\s*"((?:[^"\\]|\\.)*)"')


# --------------------------------------------------------------------
# App de PC: idiomas/*.json
# --------------------------------------------------------------------

def _cargar_json(codigo):
    with open(os.path.join(DIR_IDIOMAS_PC, f"{codigo}.json"), encoding="utf-8") as f:
        return json.load(f)


def _guardar_json(codigo, datos):
    with open(os.path.join(DIR_IDIOMAS_PC, f"{codigo}.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def revisar_pc():
    if not os.path.isdir(DIR_IDIOMAS_PC):
        return 0
    idiomas_disponibles = sorted(
        os.path.splitext(f)[0] for f in os.listdir(DIR_IDIOMAS_PC) if f.endswith(".json")
    )
    if IDIOMA_REFERENCIA not in idiomas_disponibles:
        print(f"No se encuentra idiomas/{IDIOMA_REFERENCIA}.json para usarlo de referencia.")
        return 0

    referencia = _cargar_json(IDIOMA_REFERENCIA)
    total = 0

    for codigo in idiomas_disponibles:
        if codigo == IDIOMA_REFERENCIA:
            continue
        datos = _cargar_json(codigo)

        faltan = [clave for clave in referencia if clave not in datos]
        sobran = [clave for clave in datos if clave not in referencia]

        if faltan:
            print(f"[PC/{codigo}.json] Faltan {len(faltan)} clave(s). Añadidas con el texto en español, pendientes de traducir:")
            for clave in faltan:
                print(f"    {clave}: {referencia[clave]!r}")
                datos[clave] = referencia[clave]
            _guardar_json(codigo, datos)
            total += len(faltan)

        if sobran:
            print(f"[PC/{codigo}.json] Aviso: {len(sobran)} clave(s) que ya no existen en {IDIOMA_REFERENCIA}.json (revisar si sobran):")
            for clave in sobran:
                print(f"    {clave}")

    return total


# --------------------------------------------------------------------
# Apps móviles: lib/i18n/*.dart (un Map<String, String> const por fichero)
# --------------------------------------------------------------------

def _extraer_claves_dart(ruta):
    with open(ruta, encoding="utf-8") as f:
        contenido = f.read()
    return dict(_RE_PAR_DART.findall(contenido))


def _anadir_claves_dart(ruta, claves_a_anadir):
    """Inserta las claves que faltan justo antes del '};' final del fichero,
    con el valor en español escapado como literal Dart."""
    with open(ruta, encoding="utf-8") as f:
        contenido = f.read()
    idx = contenido.rstrip().rfind("};")
    if idx == -1:
        raise ValueError(f"No se encontró el cierre '}};' en {ruta}")
    lineas_nuevas = ""
    for clave, valor in claves_a_anadir.items():
        valor_escapado = valor.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
        lineas_nuevas += f'  "{clave}": "{valor_escapado}",\n'
    nuevo_contenido = contenido[:idx] + lineas_nuevas + contenido[idx:]
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(nuevo_contenido)


def revisar_app_movil(carpeta_i18n):
    if not os.path.isdir(carpeta_i18n):
        return 0
    ruta_es = os.path.join(carpeta_i18n, f"{IDIOMA_REFERENCIA}.dart")
    if not os.path.exists(ruta_es):
        return 0

    nombre_app = os.path.basename(os.path.dirname(os.path.dirname(carpeta_i18n)))
    referencia = _extraer_claves_dart(ruta_es)
    total = 0

    for nombre in sorted(os.listdir(carpeta_i18n)):
        if not nombre.endswith(".dart") or nombre in (f"{IDIOMA_REFERENCIA}.dart", "strings.dart"):
            continue
        ruta = os.path.join(carpeta_i18n, nombre)
        datos = _extraer_claves_dart(ruta)

        faltan = {clave: referencia[clave] for clave in referencia if clave not in datos}
        sobran = [clave for clave in datos if clave not in referencia]

        etiqueta = f"{nombre_app}/{nombre}"
        if faltan:
            print(f"[{etiqueta}] Faltan {len(faltan)} clave(s). Añadidas con el texto en español, pendientes de traducir:")
            for clave, valor in faltan.items():
                print(f"    {clave}: {valor!r}")
            _anadir_claves_dart(ruta, faltan)
            total += len(faltan)

        if sobran:
            print(f"[{etiqueta}] Aviso: {len(sobran)} clave(s) que ya no existen en {IDIOMA_REFERENCIA}.dart (revisar si sobran):")
            for clave in sobran:
                print(f"    {clave}")

    return total


def main():
    total = revisar_pc()
    for carpeta in CARPETAS_I18N_MOVIL:
        total += revisar_app_movil(carpeta)

    if total == 0:
        print("Todos los idiomas (PC y apps móviles) tienen las mismas claves que el español. Todo en orden.")
    else:
        print(f"\nSe han añadido {total} clave(s) en total, copiadas del español. Tradúcelas antes de dar la función por terminada.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
