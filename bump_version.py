#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# bump_version.py — Cambia la versión de MantPro en todos los archivos a la vez.
#
# Uso:
#   python bump_version.py 3.0.0
#   python bump_version.py              (sin argumento: muestra la versión actual)

import re
import sys
import os

# Archivos y patrones donde vive la versión
ARCHIVOS = [
    {
        "ruta": "main.py",
        "patron": r'(APP_VERSION\s*=\s*["\'])[\d.]+(["\'])',
    },
    {
        "ruta": os.path.join("mantenimiento_app", "lib", "main.dart"),
        "patron": r"(const\s+String\s+kAppVersion\s*=\s*['\"])[\d.]+(['\"])",
    },
    {
        "ruta": os.path.join("mantenimiento_app", "pubspec.yaml"),
        "patron": r'(version:\s*)[\d.]+(\+\d+)?',
        "formato": lambda v, m: f"{m.group(1)}{v}+{_build_number(v)}",
    },
]


def _build_number(version):
    """Genera un build number incremental a partir de la versión (ej: 3.0.0 → 300)."""
    partes = version.split(".")
    try:
        return int(partes[0]) * 100 + int(partes[1]) * 10 + int(partes[2])
    except (IndexError, ValueError):
        return 1


def leer_version_actual():
    """Lee la versión de main.py como fuente de verdad."""
    ruta = ARCHIVOS[0]["ruta"]
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        m = re.search(ARCHIVOS[0]["patron"], f.read())
        return re.search(r'[\d.]+', m.group(0)).group() if m else None


def actualizar(nueva_version):
    cambios = []
    for arch in ARCHIVOS:
        ruta = arch["ruta"]
        if not os.path.exists(ruta):
            print(f"  ⚠️  No encontrado: {ruta}")
            continue

        with open(ruta, encoding="utf-8") as f:
            contenido = f.read()

        if "formato" in arch:
            nuevo, n = re.subn(
                arch["patron"],
                lambda m: arch["formato"](nueva_version, m),
                contenido, count=1,
            )
        else:
            nuevo, n = re.subn(
                arch["patron"],
                rf"\g<1>{nueva_version}\g<2>",
                contenido, count=1,
            )

        if n > 0 and nuevo != contenido:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(nuevo)
            cambios.append(ruta)
            print(f"  ✅ {ruta}")
        else:
            print(f"  — {ruta} (sin cambios)")

    return cambios


def main():
    actual = leer_version_actual()

    if len(sys.argv) < 2:
        print(f"Versión actual: {actual or '?'}")
        print(f"Uso: python {sys.argv[0]} <nueva_version>")
        print(f"Ejemplo: python {sys.argv[0]} 3.0.0")
        return

    nueva = sys.argv[1].lstrip("v")
    if not re.match(r"^\d+\.\d+\.\d+$", nueva):
        print(f"❌ Formato incorrecto: '{nueva}'. Usa X.Y.Z (ej: 3.0.0)")
        sys.exit(1)

    if actual == nueva:
        print(f"Ya estás en la versión {nueva}")
        return

    print(f"Cambiando versión: {actual} → {nueva}\n")
    cambios = actualizar(nueva)

    if cambios:
        print(f"\n{'─' * 40}")
        print(f"Versión actualizada a {nueva} en {len(cambios)} archivo(s)")
        print(f"Ahora haz commit y crea el tag:\n")
        print(f"  git add {' '.join(cambios)}")
        print(f"  git commit -m 'Bump version to {nueva}'")
        print(f"  git tag v{nueva}")
        print(f"  git push origin main --tags")


if __name__ == "__main__":
    main()
