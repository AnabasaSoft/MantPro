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

"""Registro local de cambios para la sincronización PC <-> MantPro Cloud (motor, sin Qt).

PROTOTIPO (paso 2 del roadmap, sección «Sincronización PC ↔ nube»): todavía no
se usa desde la aplicación; solo lo ejercita herramientas/pruebas/prueba_sincronizacion.py.

Idea: cada tabla sincronizable lleva una columna `uuid` (identificador global;
el id entero sigue siendo el local, así la API y las apps móviles no cambian) y
unos disparadores (triggers) de SQLite anotan en la tabla `cambios` cada
alta ('i'), modificación ('u') y borrado ('d'). Así no hay que tocar el código
que ya escribe en esas tablas. El borrado queda como marca (tombstone) en
`cambios`, con el uuid del registro que ya no existe.

Al aplicar cambios que llegan de la nube hay que usar `silenciar()` para que
no se vuelvan a anotar (y se reenvíen)."""

import contextlib
import re

_NOMBRE_VALIDO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NO_SILENCIADO = "(SELECT silenciado FROM sync_estado WHERE id = 1) = 0"
_UUID_NUEVO = "lower(hex(randomblob(16)))"


def _nombre(tabla):
    # Los nombres de tabla se interpolan en SQL (no se pueden parametrizar).
    if not _NOMBRE_VALIDO.match(tabla):
        raise ValueError(f"Nombre de tabla no válido: {tabla!r}")
    return tabla


def preparar_registro_cambios(con):
    """Crea la tabla `cambios` y el interruptor `sync_estado`. Idempotente.
    Pone el interruptor en «no silenciado»: si el programa se cerró a medias
    durante una sincronización, no se pierden cambios para siempre."""
    con.execute("""
        CREATE TABLE IF NOT EXISTS sync_estado (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            silenciado INTEGER NOT NULL DEFAULT 0
        )
    """)
    con.execute("INSERT OR IGNORE INTO sync_estado (id, silenciado) VALUES (1, 0)")
    con.execute("UPDATE sync_estado SET silenciado = 0 WHERE id = 1")
    con.execute("""
        CREATE TABLE IF NOT EXISTS cambios (
            n INTEGER PRIMARY KEY AUTOINCREMENT,
            tabla TEXT NOT NULL,
            uuid TEXT NOT NULL,
            op TEXT NOT NULL CHECK (op IN ('i', 'u', 'd')),
            fecha TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            subido INTEGER NOT NULL DEFAULT 0
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_cambios_subido ON cambios(subido, n)")
    con.commit()


def preparar_tabla(con, tabla):
    """Añade `uuid` a [tabla] (rellenándolo en las filas que ya hay, sin anotar
    cambios) y (re)crea sus disparadores. Idempotente. Requiere que la tabla
    tenga rowid (todas las de MantPro: INTEGER PRIMARY KEY)."""
    t = _nombre(tabla)
    columnas = {f[1] for f in con.execute(f"PRAGMA table_info({t})")}
    if "uuid" not in columnas:
        con.execute(f"ALTER TABLE {t} ADD COLUMN uuid TEXT")
    # Los disparadores todavía no existen la primera vez, así que rellenar los
    # uuid de las filas antiguas no genera cambios. Al repetir no hay nada que rellenar.
    con.execute(f"UPDATE {t} SET uuid = {_UUID_NUEVO} WHERE uuid IS NULL")
    con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{t}_uuid ON {t}(uuid)")

    for sufijo in ("ai", "au", "ad"):
        con.execute(f"DROP TRIGGER IF EXISTS sync_{t}_{sufijo}")
    # Alta: asigna el uuid si no lo trae (los cambios de la nube sí lo traen) y anota 'i'.
    con.execute(f"""
        CREATE TRIGGER sync_{t}_ai AFTER INSERT ON {t}
        BEGIN
            UPDATE {t} SET uuid = {_UUID_NUEVO} WHERE rowid = NEW.rowid AND uuid IS NULL;
            INSERT INTO cambios (tabla, uuid, op)
                SELECT '{t}', uuid, 'i' FROM {t}
                WHERE rowid = NEW.rowid AND {_NO_SILENCIADO};
        END
    """)
    # Modificación: no anota el cambio de uuid en sí (la asignación del alta).
    con.execute(f"""
        CREATE TRIGGER sync_{t}_au AFTER UPDATE ON {t}
        WHEN OLD.uuid IS NEW.uuid AND {_NO_SILENCIADO}
        BEGIN
            INSERT INTO cambios (tabla, uuid, op) VALUES ('{t}', NEW.uuid, 'u');
        END
    """)
    # Borrado (también el que llega por ON DELETE CASCADE): marca de borrado.
    con.execute(f"""
        CREATE TRIGGER sync_{t}_ad AFTER DELETE ON {t}
        WHEN {_NO_SILENCIADO}
        BEGIN
            INSERT INTO cambios (tabla, uuid, op) VALUES ('{t}', OLD.uuid, 'd');
        END
    """)
    con.commit()


@contextlib.contextmanager
def silenciar(con):
    """Mientras dura el bloque, los cambios no se anotan en `cambios`. Úsalo al
    aplicar cambios que vienen de la nube. El interruptor se activa y se
    desactiva dentro de la misma transacción que los cambios: si algo falla y se
    deshace (rollback), el interruptor vuelve a «no silenciado» solo.
    El llamador hace el commit después del bloque."""
    con.execute("UPDATE sync_estado SET silenciado = 1 WHERE id = 1")
    try:
        yield
    finally:
        con.execute("UPDATE sync_estado SET silenciado = 0 WHERE id = 1")


def cambios_pendientes(con, limite=500):
    """Cambios aún sin subir, del más antiguo al más nuevo: lista de dicts."""
    filas = con.execute(
        "SELECT n, tabla, uuid, op, fecha FROM cambios WHERE subido = 0 ORDER BY n LIMIT ?",
        (limite,)).fetchall()
    return [{"n": f[0], "tabla": f[1], "uuid": f[2], "op": f[3], "fecha": f[4]} for f in filas]


def marcar_subidos(con, hasta_n):
    """Marca como subidos los cambios con n <= [hasta_n]."""
    con.execute("UPDATE cambios SET subido = 1 WHERE subido = 0 AND n <= ?", (hasta_n,))
    con.commit()
