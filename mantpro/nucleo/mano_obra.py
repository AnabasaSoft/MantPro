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
mano_obra.py — Tiempo trabajado en cada trabajo y su coste.

- El tiempo **se apunta después** (no hay cronómetro): al registrar,
  completar o editar el trabajo, en el PC o en el móvil. Se guarda en
  minutos (tareas.minutos_trabajo) junto con cuántas personas trabajaron
  (tareas.personas); las horas de trabajo son tiempo × personas.
- El **coste de la hora** es uno interno para todos (config «coste_hora»), y
  solo lo pone un administrador. Cada trabajo guarda la tarifa del momento en
  que se apuntó su tiempo (tareas.coste_hora): si cambia después, los costes
  ya hechos no cambian.

Vive en mantenimiento.db.
"""

import re

from . import usuarios as _usuarios


def _conn():
    return _usuarios._conn()


def inicializar():
    con = _conn()
    columnas = {f[1] for f in con.execute("PRAGMA table_info(tareas)")}
    for columna, tipo in (("minutos_trabajo", "INTEGER"), ("personas", "INTEGER"), ("coste_hora", "REAL")):
        if columna not in columnas:
            con.execute(f"ALTER TABLE tareas ADD COLUMN {columna} {tipo}")
    con.commit()
    con.close()


# ---------------------------------------------------------------- tarifa

def coste_hora():
    """Coste de una hora de trabajo (None si no se ha configurado)."""
    try:
        con = _conn()
        fila = con.execute("SELECT valor FROM config WHERE clave='coste_hora'").fetchone()
        con.close()
        return float(fila[0]) if fila and fila[0] not in (None, "") else None
    except (ValueError, TypeError, Exception):
        return None


def fijar_coste_hora(valor):
    anterior = coste_hora()
    con = _conn()
    con.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    con.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('coste_hora', ?)",
                ("" if valor is None else str(valor),))
    con.commit()
    con.close()
    if anterior != valor:
        _usuarios.auditar("configuracion", "configurar", "Coste de la hora de trabajo",
                          cambios=[{"campo": "Coste de la hora de trabajo",
                                    "antes": "" if anterior is None else f"{anterior:g}",
                                    "despues": "" if valor is None else f"{valor:g}"}])


# ---------------------------------------------------------------- duraciones

def leer_duracion(texto):
    """Minutos a partir de lo que escriba el usuario: «1:30», «1,5» (horas),
    «2» (horas), «90 min», «1 h 30». None si está vacío o no se entiende."""
    if texto is None:
        return None
    if isinstance(texto, (int, float)):
        return int(round(texto)) if texto >= 0 else None
    t = str(texto).strip().lower().replace(",", ".")
    if not t:
        return None
    m = re.fullmatch(r"(\d+):(\d{1,2})", t)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*min(?:utos)?", t)
    if m:
        return int(round(float(m.group(1))))
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*h(?:oras?)?\s*(?:(\d+)\s*(?:min(?:utos)?)?)?", t)
    if m:
        return int(round(float(m.group(1)) * 60)) + int(m.group(2) or 0)
    try:
        return int(round(float(t) * 60))
    except ValueError:
        return None


def texto_duracion(minutos):
    """«1 h 30 min», «45 min», «2 h»."""
    if not minutos:
        return ""
    h, m = divmod(int(minutos), 60)
    if h and m:
        return f"{h} h {m} min"
    return f"{h} h" if h else f"{m} min"


def texto_entrada(minutos):
    """«1:30» para volver a mostrarlo en un campo editable."""
    if not minutos:
        return ""
    h, m = divmod(int(minutos), 60)
    return f"{h}:{m:02d}"


# ---------------------------------------------------------------- por trabajo

def fijar_tiempo(tarea_id, minutos, personas=1, con=None, registrar=True):
    """Tiempo trabajado del trabajo [tarea_id] (None/0: sin tiempo). Guarda la
    tarifa vigente si el trabajo aún no tenía. Si cambia algo y [registrar],
    lo apunta en el registro de cambios."""
    minutos = int(minutos) if minutos else None
    personas = max(1, int(personas or 1))
    propia = con is None
    if propia:
        con = _conn()
    fila = con.execute("SELECT minutos_trabajo, personas, coste_hora, descripcion FROM tareas WHERE id=?",
                       (tarea_id,)).fetchone()
    if not fila:
        if propia:
            con.close()
        return
    antes_min, antes_pers, tarifa, desc = fila[0], fila[1] or 1, fila[2], fila[3]
    if minutos and tarifa is None:
        tarifa = coste_hora()
    con.execute("UPDATE tareas SET minutos_trabajo=?, personas=?, coste_hora=? WHERE id=?",
                (minutos, personas if minutos else None, tarifa if minutos else None, tarea_id))
    if propia:
        con.commit()
        con.close()
    antes_txt = texto_duracion(antes_min) + (f" × {antes_pers}" if antes_min and antes_pers > 1 else "")
    despues_txt = texto_duracion(minutos) + (f" × {personas}" if minutos and personas > 1 else "")
    # Al crear el trabajo no se apunta (ya se ve en el propio trabajo); al corregirlo, sí
    if registrar and antes_txt != despues_txt:
        _usuarios.auditar("trabajos", "editar", (desc or "").split("\n")[0], objeto_id=tarea_id,
                          cambios=[{"campo": "Tiempo trabajado", "antes": antes_txt, "despues": despues_txt}])


def tiempos_de(tarea_ids):
    """{tarea_id: {minutos, personas, horas, coste_hora, importe}} de los que tienen tiempo."""
    ids = [int(i) for i in tarea_ids if i is not None]
    resultado = {}
    if not ids:
        return resultado
    con = _conn()
    for trozo in range(0, len(ids), 500):
        parte = ids[trozo:trozo + 500]
        marcas = ",".join("?" * len(parte))
        for f in con.execute(f"SELECT id, minutos_trabajo, personas, coste_hora FROM tareas "
                             f"WHERE id IN ({marcas}) AND minutos_trabajo > 0", parte):
            personas = f[2] or 1
            horas = f[1] * personas / 60
            resultado[f[0]] = {"minutos": f[1], "personas": personas, "horas": horas, "coste_hora": f[3],
                               "importe": horas * f[3] if f[3] is not None else None}
    con.close()
    return resultado


def tiempo_de(tarea_id):
    return tiempos_de([tarea_id]).get(int(tarea_id)) if tarea_id is not None else None


def texto_tiempo(t):
    """«1 h 30 min × 2 personas» para historial y exportaciones."""
    if not t:
        return ""
    texto = texto_duracion(t["minutos"])
    if t["personas"] > 1:
        texto += f" × {t['personas']}"
    return texto
