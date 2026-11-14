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

"""
operaciones_movil.py — Que una operación del móvil no se aplique dos veces.

Las apps trabajan sin conexión: cada cambio (completar un trabajo, un movimiento
de stock...) se guarda en una cola del móvil y se envía al PC cuando hay red. Si
la respuesta del PC se pierde (se corta la wifi justo entonces) o la cola se
vacía por dos sitios a la vez, el móvil vuelve a mandar lo mismo, y sin esto el
PC lo aplicaría otra vez (dos trabajos iguales, el stock descontado dos veces).

Cada operación de la cola lleva un identificador propio, creado en el móvil al
meterla en la cola, que viaja en la cabecera `X-MantPro-Op`. Aquí se apunta:

- La primera vez se «reclama» (queda *en curso*) y se aplica.
- Al terminar se guarda la respuesta que se dio (queda *hecha*).
- Si vuelve a llegar, se devuelve esa misma respuesta sin aplicar nada.
- Si llega mientras la primera aún está en curso, se responde «en curso» y el
  móvil la reintenta más tarde (para entonces ya estará hecha).

Una operación que falla en el servidor (error 5xx) se suelta, para que el
reintento la aplique de verdad. Una *en curso* de hace más de
SEGUNDOS_EN_CURSO (el PC se cerró a mitad) se puede volver a reclamar.

Vive en mantenimiento.db, tabla `operaciones_movil`. No viaja a MantPro Cloud
(solo se sincronizan las tablas de `sincronizacion.TABLAS`). Python puro.
"""

import re
import threading
from datetime import datetime, timedelta

from .conexion_bd import conectar

CABECERA = "X-MantPro-Op"
SEGUNDOS_EN_CURSO = 600          # una operación «en curso» de hace más se da por abandonada
DIAS_GUARDADAS = 45              # las hechas se olvidan pasado este tiempo (ninguna cola espera tanto)
MAX_RESPUESTA = 64 * 1024        # respuestas más grandes no se guardan enteras (no hace falta: las de escritura son cortas)
_OP_VALIDA = re.compile(r"^[A-Za-z0-9_.:-]{8,100}$")

NUEVA, HECHA, EN_CURSO = "nueva", "hecha", "en_curso"

_cerrojo = threading.Lock()      # reclamar es «mirar y apuntar» de una vez, también entre hilos
_creadas = set()


def op_valida(op):
    """True si [op] tiene forma de identificador de operación (lo que no la tenga se ignora)."""
    return isinstance(op, str) and bool(_OP_VALIDA.match(op))


def _ahora(ahora=None):
    return (ahora or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")


def _conn(db_path):
    con = conectar(db_path, timeout=20)       # igual que basedatos.get_db_connection (WAL, espera 20 s)
    con.execute("PRAGMA journal_mode=WAL;")
    if db_path not in _creadas:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS operaciones_movil (
                usuario_id  INTEGER NOT NULL,
                op          TEXT NOT NULL,
                ruta        TEXT NOT NULL DEFAULT '',
                estado      TEXT NOT NULL,             -- en_curso | hecha
                codigo      INTEGER,                   -- respuesta que se dio (al estar hecha)
                cuerpo      BLOB,
                tipo        TEXT,
                creada      TEXT NOT NULL,
                actualizada TEXT NOT NULL,
                PRIMARY KEY (usuario_id, op)
            );
            CREATE INDEX IF NOT EXISTS idx_operaciones_movil_act ON operaciones_movil(actualizada);
        """)
        con.commit()
        _creadas.add(db_path)
    return con


def reclamar(db_path, usuario_id, op, ruta="", ahora=None):
    """Mira si la operación [op] de [usuario_id] ya se hizo. Devuelve:
    (NUEVA, None) si hay que aplicarla (queda apuntada como en curso),
    (HECHA, (codigo, cuerpo, tipo)) con la respuesta que se dio la primera vez, o
    (EN_CURSO, None) si otra petición la está aplicando ahora mismo."""
    momento = ahora or datetime.now()
    with _cerrojo:
        con = _conn(db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            fila = con.execute("SELECT estado, codigo, cuerpo, tipo, actualizada FROM operaciones_movil "
                               "WHERE usuario_id = ? AND op = ?", (usuario_id, op)).fetchone()
            if fila is None:
                con.execute("INSERT INTO operaciones_movil (usuario_id, op, ruta, estado, creada, actualizada) "
                            "VALUES (?, ?, ?, ?, ?, ?)", (usuario_id, op, ruta, EN_CURSO, _ahora(momento), _ahora(momento)))
                con.commit()
                return NUEVA, None
            estado, codigo, cuerpo, tipo, actualizada = fila
            if estado == HECHA:
                con.commit()
                return HECHA, (codigo, bytes(cuerpo or b""), tipo or "application/json")
            try:
                abandonada = momento - datetime.strptime(actualizada, "%Y-%m-%d %H:%M:%S") > timedelta(seconds=SEGUNDOS_EN_CURSO)
            except (TypeError, ValueError):
                abandonada = True
            if abandonada:
                con.execute("UPDATE operaciones_movil SET actualizada = ?, ruta = ? WHERE usuario_id = ? AND op = ?",
                            (_ahora(momento), ruta, usuario_id, op))
                con.commit()
                return NUEVA, None
            con.commit()
            return EN_CURSO, None
        except Exception:              # también los de SQLCipher, que no heredan de sqlite3.Error
            con.rollback()
            raise
        finally:
            con.close()


def terminar(db_path, usuario_id, op, codigo, cuerpo, tipo, ahora=None):
    """Apunta la operación como hecha, con la respuesta que se dio (para repetirla si vuelve a llegar)."""
    cuerpo = bytes(cuerpo or b"")
    if len(cuerpo) > MAX_RESPUESTA:
        cuerpo = b'{"status": "ok"}'
        tipo = "application/json"
    with _cerrojo:
        con = _conn(db_path)
        try:
            con.execute("UPDATE operaciones_movil SET estado = ?, codigo = ?, cuerpo = ?, tipo = ?, actualizada = ? "
                        "WHERE usuario_id = ? AND op = ?",
                        (HECHA, int(codigo), cuerpo, tipo, _ahora(ahora), usuario_id, op))
            con.commit()
        finally:
            con.close()


def soltar(db_path, usuario_id, op):
    """Olvida una operación en curso que no ha llegado a aplicarse (error del servidor): el reintento la aplicará."""
    with _cerrojo:
        con = _conn(db_path)
        try:
            con.execute("DELETE FROM operaciones_movil WHERE usuario_id = ? AND op = ? AND estado = ?",
                        (usuario_id, op, EN_CURSO))
            con.commit()
        finally:
            con.close()


def purgar(db_path, dias=DIAS_GUARDADAS, ahora=None):
    """Borra las operaciones de hace más de [dias]. Devuelve cuántas."""
    limite = _ahora((ahora or datetime.now()) - timedelta(days=dias))
    with _cerrojo:
        con = _conn(db_path)
        try:
            n = con.execute("DELETE FROM operaciones_movil WHERE actualizada < ?", (limite,)).rowcount
            con.commit()
            return n
        finally:
            con.close()
