#!/usr/bin/env python3
"""
migrar_foto_unica_a_despues.py
--------------------------------
Corrige el histórico de MantPro: hay trabajos completados que se hicieron
ANTES de existir el campo "foto después", así que su única foto (la del
resultado final) quedó guardada como [FOTO: ...] (antes) en vez de
[FOTO_DESPUES: ...] (después).

Este script recorre la tabla 'tareas' (el historial) y, para cada registro
que tenga EXACTAMENTE una foto -> [FOTO: x] presente y [FOTO_DESPUES: ...]
ausente -> mueve esa foto de "antes" a "después", dejando "antes" vacío.

Los registros que ya tienen las dos fotos, o que ya tienen la foto en
"después", o que no tienen ninguna foto, se dejan tal cual.

SEGURIDAD:
- Antes de tocar nada hace una COPIA DE SEGURIDAD del .db con fecha/hora.
- Por defecto se ejecuta en modo DRY-RUN (solo enseña qué cambiaría, no
  modifica nada). Hay que confirmar explícitamente para aplicar los cambios.

Uso:
    python3 migrar_foto_unica_a_despues.py            -> solo previsualiza
    python3 migrar_foto_unica_a_despues.py --aplicar   -> aplica los cambios
    python3 migrar_foto_unica_a_despues.py --db /ruta/a/mantenimiento.db --aplicar
"""

import os
import re
import sys
import shutil
import sqlite3
import argparse
from datetime import datetime

PATRON_FOTO = re.compile(r"\[FOTO:\s*(.*?)\]")
PATRON_FOTO_DESPUES = re.compile(r"\[FOTO_DESPUES:\s*(.*?)\]")


def obtener_ruta_datos():
    """Misma lógica que usa main.py para localizar la carpeta de datos."""
    cwd = os.path.abspath(".")
    db_local = os.path.join(cwd, "mantenimiento.db")
    if os.path.exists(db_local):
        return cwd

    nombre_app = "MantPro"
    if sys.platform == "win32":
        base_dir = os.getenv("APPDATA")
    else:
        base_dir = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return os.path.join(base_dir, nombre_app)


def localizar_db(ruta_forzada: str | None) -> str:
    if ruta_forzada:
        if not os.path.exists(ruta_forzada):
            sys.exit(f"❌ No existe el archivo indicado: {ruta_forzada}")
        return ruta_forzada

    carpeta = obtener_ruta_datos()
    ruta = os.path.join(carpeta, "mantenimiento.db")
    if not os.path.exists(ruta):
        sys.exit(
            "❌ No he encontrado 'mantenimiento.db' automáticamente.\n"
            f"   Busqué en: {ruta}\n"
            "   Indica la ruta manualmente con --db /ruta/al/mantenimiento.db"
        )
    return ruta


def analizar(descripcion: str):
    """Devuelve (nombre_foto_antes, tiene_despues) o (None, ...) si no aplica el caso."""
    m_antes = PATRON_FOTO.search(descripcion)
    m_despues = PATRON_FOTO_DESPUES.search(descripcion)
    if m_antes and not m_despues:
        return m_antes.group(1).split("]")[0].strip()
    return None


def migrar_descripcion(descripcion: str, nombre_foto: str) -> str:
    """Sustituye la etiqueta [FOTO: x] por [FOTO_DESPUES: x] (mismo archivo, solo cambia la etiqueta)."""
    nueva = PATRON_FOTO.sub("", descripcion, count=1)
    nueva = nueva.rstrip()
    nueva += f"\n[FOTO_DESPUES: {nombre_foto}]"
    return nueva


def main():
    parser = argparse.ArgumentParser(description="Mueve la foto única de 'antes' a 'después' en trabajos ya finalizados.")
    parser.add_argument("--db", help="Ruta al archivo mantenimiento.db (si no se indica, se autodetecta como hace la app).")
    parser.add_argument("--aplicar", action="store_true", help="Aplica los cambios de verdad. Sin esta opción solo se previsualiza.")
    args = parser.parse_args()

    ruta_db = localizar_db(args.db)
    print(f"📂 Base de datos: {ruta_db}")

    conn = sqlite3.connect(ruta_db)
    c = conn.cursor()
    c.execute("SELECT id, fecha, descripcion FROM tareas ORDER BY fecha DESC")
    filas = c.fetchall()

    candidatos = []
    for id_, fecha, descripcion in filas:
        nombre_foto = analizar(descripcion or "")
        if nombre_foto:
            candidatos.append((id_, fecha, descripcion, nombre_foto))

    if not candidatos:
        print("✅ No hay ningún trabajo con una sola foto en 'antes'. No hace falta cambiar nada.")
        conn.close()
        return

    print(f"\n🔍 Encontrados {len(candidatos)} trabajos con una única foto guardada como 'antes':\n")
    for id_, fecha, descripcion, nombre_foto in candidatos:
        primera_linea = (descripcion or "").split("\n")[0].strip()[:60]
        print(f"   #{id_:<5} {fecha}  {primera_linea!r:<62}  foto: {nombre_foto}")

    if not args.aplicar:
        print(f"\n👀 Modo previsualización (no se ha tocado nada). Total a mover: {len(candidatos)}")
        print("   Vuelve a ejecutar con --aplicar cuando quieras aplicar el cambio de verdad.")
        conn.close()
        return

    # --- Copia de seguridad antes de tocar nada ---
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_backup = f"{ruta_db}.backup_{marca}"
    shutil.copy2(ruta_db, ruta_backup)
    print(f"\n💾 Copia de seguridad creada en: {ruta_backup}")

    confirmacion = input(f"\n⚠️  Se van a modificar {len(candidatos)} registros. Escribe SI para confirmar: ").strip()
    if confirmacion.upper() != "SI":
        print("❌ Cancelado. No se ha modificado nada.")
        conn.close()
        return

    aplicados = 0
    for id_, fecha, descripcion, nombre_foto in candidatos:
        nueva_descripcion = migrar_descripcion(descripcion, nombre_foto)
        c.execute("UPDATE tareas SET descripcion = ? WHERE id = ?", (nueva_descripcion, id_))
        aplicados += 1

    conn.commit()
    conn.close()
    print(f"\n✅ Listo. Se han movido {aplicados} fotos de 'antes' a 'después'.")
    print("   Si algo no ha salido como esperabas, restaura la copia de seguridad:")
    print(f"   cp \"{ruta_backup}\" \"{ruta_db}\"")


if __name__ == "__main__":
    main()
