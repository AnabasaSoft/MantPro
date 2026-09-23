# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# MantPro - Sistema de Mantenimiento Preventivo
# Copyright (C) 2026 AnabasaSoft <anabasasoft@gmail.com>
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
maquinas.py — Listado de maquinaria y su histórico de trabajos para MantPro.

Las máquinas forman un árbol (una máquina puede tener submáquinas, para poder
agrupar por planta/línea/equipo). Cada trabajo de la tabla "tareas" puede
vincularse opcionalmente a una máquina mediante la columna tareas.maquina_id.

Uso desde main.py:

    import maquinas
    maquinas.configurar_db(RUTA_DB)   # la misma BD que usa el resto de la app
    maquinas.inicializar()            # crea la tabla + migra la columna (idempotente)
"""

import sqlite3
from datetime import datetime

RUTA_DB = "mantenimiento.db"


def configurar_db(ruta):
    """Fija la ruta de la base de datos que usará este módulo."""
    global RUTA_DB
    RUTA_DB = ruta


def _conn():
    # timeout=20: igual que en almacen.py/usuarios.py, para no dar "database
    # is locked" cuando el hilo del servidor Flask lee mientras el PC está
    # escribiendo mucho seguido en mantenimiento.db.
    con = sqlite3.connect(RUTA_DB, timeout=20)
    con.row_factory = sqlite3.Row
    return con


def inicializar():
    """Crea la tabla de máquinas y añade la columna de vínculo en tareas.

    Es idempotente: se puede llamar en cada arranque sin efectos secundarios.
    """
    con = _conn()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maquinas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            padre_id  INTEGER,
            notas     TEXT,
            creado    TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_maquinas_padre ON maquinas(padre_id)")

    cols = {fila[1] for fila in cur.execute("PRAGMA table_info(tareas)")}
    if "maquina_id" not in cols:
        cur.execute("ALTER TABLE tareas ADD COLUMN maquina_id INTEGER")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tareas_maquina ON tareas(maquina_id)")
    if "prioridad" not in cols:
        cur.execute("ALTER TABLE tareas ADD COLUMN prioridad TEXT DEFAULT 'Media'")
    if "horas_paro" not in cols:
        cur.execute("ALTER TABLE tareas ADD COLUMN horas_paro REAL")

    cols_maquinas = {fila[1] for fila in cur.execute("PRAGMA table_info(maquinas)")}
    if "foto" not in cols_maquinas:
        cur.execute("ALTER TABLE maquinas ADD COLUMN foto TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS zonas (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    if "zona_id" not in cols_maquinas:
        cur.execute("ALTER TABLE maquinas ADD COLUMN zona_id INTEGER")

    con.commit()
    con.close()


# ---------------------------------------------------------------- zonas (ubicaciones)

def listar_zonas():
    """Todas las zonas dadas de alta, ordenadas por nombre."""
    con = _conn()
    filas = con.execute("SELECT id, nombre FROM zonas ORDER BY nombre COLLATE NOCASE").fetchall()
    con.close()
    return [dict(f) for f in filas]


def agregar_zona(nombre):
    """Da de alta una zona nueva y devuelve su id (o el de la existente si ya había una con ese nombre)."""
    con = _conn()
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO zonas (nombre) VALUES (?)", (nombre.strip(),))
    con.commit()
    fila = cur.execute("SELECT id FROM zonas WHERE nombre=?", (nombre.strip(),)).fetchone()
    con.close()
    return fila[0] if fila else None


def borrar_zona(id_zona):
    """Borra la zona. Las máquinas que la tenían asignada quedan sin zona."""
    con = _conn()
    con.execute("UPDATE maquinas SET zona_id=NULL WHERE zona_id=?", (id_zona,))
    con.execute("DELETE FROM zonas WHERE id=?", (id_zona,))
    con.commit()
    con.close()


def zonas_disponibles():
    """Zonas (id, nombre) con al menos una máquina asignada, ordenadas por nombre."""
    con = _conn()
    filas = con.execute(
        "SELECT DISTINCT z.id, z.nombre FROM zonas z JOIN maquinas m ON m.zona_id = z.id "
        "ORDER BY z.nombre COLLATE NOCASE"
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]


# ---------------------------------------------------------------- CRUD máquinas

def agregar_maquina(nombre, padre_id=None, notas="", foto=None, zona_id=None):
    con = _conn()
    con.execute(
        "INSERT INTO maquinas (nombre, padre_id, notas, creado, foto, zona_id) VALUES (?, ?, ?, ?, ?, ?)",
        (nombre.strip(), padre_id, (notas or "").strip(),
         datetime.now().isoformat(timespec="seconds"), foto, zona_id),
    )
    con.commit()
    con.close()


def actualizar_maquina(id_maquina, nombre, padre_id, notas, foto=None, zona_id=None):
    con = _conn()
    con.execute(
        "UPDATE maquinas SET nombre=?, padre_id=?, notas=?, foto=?, zona_id=? WHERE id=?",
        (nombre.strip(), padre_id, (notas or "").strip(), foto, zona_id, id_maquina),
    )
    con.commit()
    con.close()


def listar_maquinas():
    """Todas las máquinas (planas, con su padre_id y su zona), ordenadas por nombre."""
    con = _conn()
    filas = con.execute(
        "SELECT m.id, m.nombre, m.padre_id, m.notas, m.foto, m.zona_id, z.nombre AS zona_nombre "
        "FROM maquinas m LEFT JOIN zonas z ON z.id = m.zona_id "
        "ORDER BY m.nombre COLLATE NOCASE"
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]


def obtener_maquina(id_maquina):
    con = _conn()
    fila = con.execute(
        "SELECT id, nombre, padre_id, notas, foto, zona_id FROM maquinas WHERE id=?", (id_maquina,)
    ).fetchone()
    con.close()
    return dict(fila) if fila else None


def mapa_rutas_completas():
    """Devuelve {id_maquina: 'Máquina padre > Submáquina'} para todas las
    máquinas, útil para mostrar en informes y exportaciones."""
    todas = {m["id"]: m for m in listar_maquinas()}
    cache = {}

    def ruta(id_maquina):
        if id_maquina in cache:
            return cache[id_maquina]
        m = todas.get(id_maquina)
        if not m:
            return ""
        padre = ruta(m["padre_id"]) if m["padre_id"] else ""
        completo = f"{padre} > {m['nombre']}" if padre else m["nombre"]
        cache[id_maquina] = completo
        return completo

    for id_maquina in todas:
        ruta(id_maquina)
    return cache


def _descendientes(con, id_maquina):
    """IDs de una máquina y de todas sus submáquinas, recursivamente."""
    ids = [id_maquina]
    for (hijo_id,) in con.execute("SELECT id FROM maquinas WHERE padre_id=?", (id_maquina,)):
        ids.extend(_descendientes(con, hijo_id))
    return ids


def descendientes_ids(id_maquina):
    """IDs de una máquina y de todas sus submáquinas, recursivamente."""
    con = _conn()
    ids = _descendientes(con, id_maquina)
    con.close()
    return ids


def borrar_maquina(id_maquina):
    """Borra la máquina y sus submáquinas. Los trabajos ya registrados en ellas
    no se eliminan: simplemente quedan sin máquina asignada."""
    con = _conn()
    ids = _descendientes(con, id_maquina)
    marcas = ",".join("?" * len(ids))
    con.execute(f"UPDATE tareas SET maquina_id=NULL WHERE maquina_id IN ({marcas})", ids)
    con.execute(f"DELETE FROM maquinas WHERE id IN ({marcas})", ids)
    con.commit()
    con.close()


# ---------------------------------------------------------------- trabajos por máquina

def _contar_tareas(id_maquina, fecha_inicio=None, fecha_fin=None, solo_averias=False):
    """Base común de contar_trabajos/contar_averias: cuenta las tareas de
    maquina_id, opcionalmente filtrando por tag 'Avería' y/o por rango de
    fecha ('YYYY-MM-DD')."""
    sql = "SELECT COUNT(*) FROM tareas WHERE maquina_id=?"
    if solo_averias:
        sql += " AND tags LIKE '%Avería%'"
    parametros = [id_maquina]
    if fecha_inicio and fecha_fin:
        sql += " AND fecha BETWEEN ? AND ?"
        parametros += [fecha_inicio, fecha_fin]
    con = _conn()
    fila = con.execute(sql, parametros).fetchone()
    con.close()
    return fila[0] if fila else 0


def contar_trabajos(id_maquina, fecha_inicio=None, fecha_fin=None):
    """Nº de trabajos vinculados directamente a esta máquina (sin submáquinas),
    sea cual sea su etiqueta (avería, urgente, preventivo...). Si se indican
    fecha_inicio/fecha_fin ('YYYY-MM-DD'), solo cuenta los de ese rango."""
    return _contar_tareas(id_maquina, fecha_inicio, fecha_fin)


def _ranking_por(contador, top_n=8, fecha_inicio=None, fecha_fin=None):
    """Base común de ranking_trabajos/ranking_averias: suma contador() sobre
    cada máquina de nivel superior (incluyendo sus submáquinas) y devuelve
    las top_n con más total, de más a menos, descartando las que están a 0."""
    top_level = [m for m in listar_maquinas() if m["padre_id"] is None]

    def total(id_maquina):
        return sum(contador(i, fecha_inicio, fecha_fin) for i in descendientes_ids(id_maquina))

    datos = sorted(
        ((m["nombre"], total(m["id"])) for m in top_level),
        key=lambda par: par[1], reverse=True,
    )
    return [par for par in datos if par[1] > 0][:top_n]


def ranking_trabajos(top_n=8, fecha_inicio=None, fecha_fin=None):
    """Máquinas de nivel superior con más trabajos en total (sumando las de sus
    submáquinas), de más a menos, sea cual sea la etiqueta del trabajo (avería,
    urgente, preventivo...), para el ranking "más solicitadas" del dashboard.
    Solo incluye máquinas con al menos un trabajo. Si se indican
    fecha_inicio/fecha_fin ('YYYY-MM-DD'), solo cuenta los de ese rango."""
    return _ranking_por(contar_trabajos, top_n, fecha_inicio, fecha_fin)


def anios_de_maquina(id_maquina):
    """Años con trabajos en esta máquina y cuántos trabajos tiene cada uno."""
    con = _conn()
    filas = con.execute(
        "SELECT substr(fecha,1,4) AS anio, COUNT(*) FROM tareas "
        "WHERE maquina_id=? AND fecha IS NOT NULL AND fecha != '' "
        "GROUP BY anio ORDER BY anio DESC",
        (id_maquina,),
    ).fetchall()
    con.close()
    return [(f[0], f[1]) for f in filas]


def anios_disponibles():
    """Años (texto 'YYYY') con al menos un trabajo vinculado a alguna máquina,
    de más reciente a más antiguo."""
    con = _conn()
    filas = con.execute(
        "SELECT DISTINCT substr(fecha,1,4) AS anio FROM tareas "
        "WHERE maquina_id IS NOT NULL AND fecha IS NOT NULL AND fecha != '' "
        "ORDER BY anio DESC"
    ).fetchall()
    con.close()
    return [f[0] for f in filas]


def contar_trabajos_anio(id_maquina, anio):
    """Nº de trabajos de esta máquina en el año dado (texto 'YYYY')."""
    con = _conn()
    fila = con.execute(
        "SELECT COUNT(*) FROM tareas WHERE maquina_id=? AND substr(fecha,1,4)=?",
        (id_maquina, anio),
    ).fetchone()
    con.close()
    return fila[0] if fila else 0


def trabajos_de_maquina_anio(id_maquina, anio):
    """Trabajos de esta máquina en el año dado, más recientes primero."""
    con = _conn()
    filas = con.execute(
        "SELECT id, fecha, descripcion, tags FROM tareas WHERE maquina_id=? "
        "AND substr(fecha,1,4)=? ORDER BY fecha DESC, id DESC",
        (id_maquina, anio),
    ).fetchall()
    con.close()
    return [dict(f) for f in filas]


def indicadores_fiabilidad(id_maquina):
    """MTBF (tiempo medio entre averías, en días) y MTTR (tiempo medio de
    reparación, en horas) de una máquina y sus submáquinas, calculados a
    partir de los trabajos marcados con la etiqueta 'Avería'.

    Devuelve {"num_averias": int, "mtbf_dias": float|None, "mttr_horas": float|None}.
    mtbf_dias solo se calcula con 2 o más averías (hace falta al menos un
    intervalo entre dos fechas); mttr_horas solo con averías que tengan
    horas de parada registradas.
    """
    ids = descendientes_ids(id_maquina)
    marcas = ",".join("?" * len(ids))
    con = _conn()
    filas = con.execute(
        f"SELECT fecha, horas_paro FROM tareas WHERE maquina_id IN ({marcas}) "
        f"AND tags LIKE '%Avería%' AND fecha IS NOT NULL AND fecha != '' "
        f"ORDER BY fecha ASC, id ASC",
        ids,
    ).fetchall()
    con.close()

    fechas = []
    for fila in filas:
        try:
            fechas.append(datetime.strptime(fila["fecha"], "%Y-%m-%d"))
        except (ValueError, TypeError):
            pass

    mtbf_dias = None
    if len(fechas) >= 2:
        total_dias = (fechas[-1] - fechas[0]).days
        mtbf_dias = total_dias / (len(fechas) - 1)

    horas = [fila["horas_paro"] for fila in filas if fila["horas_paro"] is not None]
    mttr_horas = (sum(horas) / len(horas)) if horas else None

    return {"num_averias": len(filas), "mtbf_dias": mtbf_dias, "mttr_horas": mttr_horas}


def indicadores_fiabilidad_global(fecha_inicio=None, fecha_fin=None):
    """Igual que indicadores_fiabilidad, pero con las averías de todas las
    máquinas juntas (y las que no tienen máquina asignada), para dar una
    cifra de fiabilidad de toda la planta en el dashboard. Si se indican
    fecha_inicio/fecha_fin (formato 'YYYY-MM-DD'), solo se tienen en cuenta
    las averías de ese rango (p. ej. para un PDF exportado por rango)."""
    sql = "SELECT fecha, horas_paro FROM tareas WHERE tags LIKE '%Avería%' AND fecha IS NOT NULL AND fecha != ''"
    parametros = []
    if fecha_inicio and fecha_fin:
        sql += " AND fecha BETWEEN ? AND ?"
        parametros = [fecha_inicio, fecha_fin]
    sql += " ORDER BY fecha ASC, id ASC"
    con = _conn()
    filas = con.execute(sql, parametros).fetchall()
    con.close()

    fechas = []
    for fila in filas:
        try:
            fechas.append(datetime.strptime(fila["fecha"], "%Y-%m-%d"))
        except (ValueError, TypeError):
            pass

    mtbf_dias = None
    if len(fechas) >= 2:
        total_dias = (fechas[-1] - fechas[0]).days
        mtbf_dias = total_dias / (len(fechas) - 1)

    horas = [fila["horas_paro"] for fila in filas if fila["horas_paro"] is not None]
    mttr_horas = (sum(horas) / len(horas)) if horas else None

    return {"num_averias": len(filas), "mtbf_dias": mtbf_dias, "mttr_horas": mttr_horas}


def contar_averias(id_maquina, fecha_inicio=None, fecha_fin=None):
    """Nº de trabajos marcados como 'Avería' vinculados directamente a esta
    máquina (sin submáquinas). Si se indican fecha_inicio/fecha_fin
    ('YYYY-MM-DD'), solo cuenta las de ese rango."""
    return _contar_tareas(id_maquina, fecha_inicio, fecha_fin, solo_averias=True)


def ranking_averias(top_n=8, fecha_inicio=None, fecha_fin=None):
    """Máquinas de nivel superior con más averías (sumando las de sus
    submáquinas), de más a menos, para el ranking de "más problemáticas"
    del dashboard. Solo incluye máquinas con al menos una avería. Si se
    indican fecha_inicio/fecha_fin ('YYYY-MM-DD'), solo cuenta las averías
    de ese rango (p. ej. para un PDF exportado por rango)."""
    return _ranking_por(contar_averias, top_n, fecha_inicio, fecha_fin)


def averias_por_mes(n_meses=12, fecha_inicio=None, fecha_fin=None):
    """Nº de averías registradas por mes, en orden cronológico. Devuelve una
    lista de tuplas ('YYYY-MM', cantidad). Sin fecha_inicio/fecha_fin,
    cubre los últimos n_meses meses (incluido el actual), como en el
    dashboard. Con fecha_inicio/fecha_fin ('YYYY-MM-DD'), cubre en su lugar
    todos los meses de ese rango (p. ej. para un PDF exportado por rango)."""
    sql = "SELECT substr(fecha,1,7) AS mes, COUNT(*) AS n FROM tareas WHERE tags LIKE '%Avería%' AND fecha IS NOT NULL AND fecha != ''"
    parametros = []
    if fecha_inicio and fecha_fin:
        sql += " AND fecha BETWEEN ? AND ?"
        parametros = [fecha_inicio, fecha_fin]
    sql += " GROUP BY mes"
    con = _conn()
    filas = con.execute(sql, parametros).fetchall()
    con.close()
    por_mes = {fila["mes"]: fila["n"] for fila in filas}

    if fecha_inicio and fecha_fin:
        inicio = datetime.strptime(fecha_inicio[:7], "%Y-%m")
        fin = datetime.strptime(fecha_fin[:7], "%Y-%m")
        meses = []
        anio, mes = inicio.year, inicio.month
        while (anio, mes) <= (fin.year, fin.month):
            clave = f"{anio:04d}-{mes:02d}"
            meses.append((clave, por_mes.get(clave, 0)))
            mes += 1
            if mes > 12:
                mes = 1
                anio += 1
        return meses

    hoy = datetime.now()
    meses = []
    for i in range(n_meses - 1, -1, -1):
        anio, mes = hoy.year, hoy.month - i
        while mes <= 0:
            mes += 12
            anio -= 1
        clave = f"{anio:04d}-{mes:02d}"
        meses.append((clave, por_mes.get(clave, 0)))
    return meses
