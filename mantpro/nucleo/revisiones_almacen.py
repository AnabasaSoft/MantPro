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
revisiones_almacen.py — Control de las revisiones diarias del almacén.

Cada día MantPro Stock propone revisar 5 artículos al azar. Aquí queda
constancia de **quién** hizo la revisión, **cuándo** y **si revisó los 5**:

- Una *revisión* es lo que hace una persona un día (fecha, usuario, móvil).
- Cada revisión tiene sus *líneas*: los artículos propuestos, con la cantidad
  que decía el sistema, la que se contó y si se llegó a revisar.

El móvil manda la revisión entera cada vez que avanza (se identifica con un
`uid` propio, así reenviarla no la duplica), también si la hizo sin conexión.
Si llega una versión más antigua que la ya guardada, se ignora.

Vive en almacen.db, junto al resto del almacén. Python puro, sin Qt: lo usan
la API del servidor y la ventana del PC.
"""

from datetime import datetime, timedelta

from . import almacen

ESTADO_COMPLETA = "completa"
ESTADO_PARCIAL = "parcial"
ESTADO_SIN_EMPEZAR = "sin_empezar"

_MAX_LINEAS = 50  # tope razonable: lo normal son 5 por revisión


def inicializar():
    """Crea las tablas si no existen. Idempotente."""
    con = almacen._conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS revisiones_stock (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            uid            TEXT NOT NULL UNIQUE,
            fecha          TEXT NOT NULL,          -- día de la revisión (AAAA-MM-DD)
            usuario_id     INTEGER,
            usuario_nombre TEXT NOT NULL DEFAULT '',
            dispositivo    TEXT NOT NULL DEFAULT '',
            creada         TEXT NOT NULL,
            actualizada    TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_revisiones_stock_fecha ON revisiones_stock(fecha);
        CREATE TABLE IF NOT EXISTS revisiones_stock_lineas (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            revision_id      INTEGER NOT NULL REFERENCES revisiones_stock(id) ON DELETE CASCADE,
            material_id      INTEGER,               -- NULL si el artículo aún no existía en el PC
            codigo           TEXT NOT NULL DEFAULT '',
            nombre           TEXT NOT NULL DEFAULT '',
            ubicacion        TEXT NOT NULL DEFAULT '',
            unidad           TEXT NOT NULL DEFAULT '',
            cantidad_sistema REAL,                  -- lo que decía el sistema al empezar
            cantidad_contada REAL,                  -- lo que se contó (NULL si no se revisó)
            revisado         INTEGER NOT NULL DEFAULT 0,
            fecha_revision   TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_revisiones_lineas_rev ON revisiones_stock_lineas(revision_id);
    """)
    # Almacén revisado (NULL: el principal, también las revisiones de antes de haber varios)
    if "almacen_id" not in almacen._columnas(con, "revisiones_stock"):
        con.execute("ALTER TABLE revisiones_stock ADD COLUMN almacen_id INTEGER")
    con.commit()
    con.close()


def _numero(valor):
    """float o None (vacío, texto raro…)."""
    if valor is None or valor == "":
        return None
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def _texto(valor, maximo=200):
    return str(valor if valor is not None else "").strip()[:maximo]


def _fecha_valida(texto):
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def guardar_revision(datos, usuario_id, usuario_nombre):
    """Guarda (o actualiza) una revisión que manda un móvil.

    [datos] es un diccionario: `uid`, `fecha` (AAAA-MM-DD), `dispositivo`
    (opcional), `actualizada` (AAAA-MM-DD HH:MM:SS) y `lineas`: lista de
    diccionarios con `material_id` (o None), `codigo`, `nombre`, `ubicacion`,
    `unidad`, `cantidad_sistema`, `cantidad_contada`, `revisado`,
    `fecha_revision`.

    Devuelve (True, id) si se guardó, (True, id) también si se ignoró por
    llegar una versión más antigua que la guardada, o (False, motivo) si los
    datos no valen. El usuario es siempre el de la sesión, no el que diga el
    móvil: así nadie puede firmar una revisión como otro."""
    from . import almacenes
    uid = _texto(datos.get("uid"), 80)
    fecha = _texto(datos.get("fecha"), 10)
    almacen_id = datos.get("almacen_id")
    almacen_id = almacenes.guardable(int(almacen_id)) if isinstance(almacen_id, (int, float)) and almacen_id > 0 else None
    lineas = datos.get("lineas")
    if not uid:
        return False, "falta_uid"
    if not _fecha_valida(fecha):
        return False, "fecha_no_valida"
    if not isinstance(lineas, list) or not lineas or len(lineas) > _MAX_LINEAS:
        return False, "lineas_no_validas"
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    actualizada = _texto(datos.get("actualizada"), 19) or ahora

    con = almacen._conn()
    try:
        existente = con.execute("SELECT id, actualizada, usuario_id FROM revisiones_stock WHERE uid=?", (uid,)).fetchone()
        if existente is not None:
            if existente["usuario_id"] != usuario_id:
                return False, "revision_de_otro_usuario"
            if actualizada < existente["actualizada"]:
                return True, existente["id"]   # llegó una versión vieja: ya hay una más nueva
            revision_id = existente["id"]
            con.execute("UPDATE revisiones_stock SET actualizada=?, dispositivo=?, almacen_id=? WHERE id=?",
                        (actualizada, _texto(datos.get("dispositivo"), 120), almacen_id, revision_id))
            con.execute("DELETE FROM revisiones_stock_lineas WHERE revision_id=?", (revision_id,))
        else:
            revision_id = con.execute("""
                INSERT INTO revisiones_stock (uid, fecha, usuario_id, usuario_nombre, dispositivo, creada, actualizada,
                                              almacen_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (uid, fecha, usuario_id, _texto(usuario_nombre, 120), _texto(datos.get("dispositivo"), 120),
                 ahora, actualizada, almacen_id)).lastrowid
        for linea in lineas:
            if not isinstance(linea, dict):
                continue
            material_id = linea.get("material_id")
            material_id = int(material_id) if isinstance(material_id, (int, float)) and material_id > 0 else None
            revisado = 1 if linea.get("revisado") in (True, 1, "1", "true", "True") else 0
            contada = _numero(linea.get("cantidad_contada")) if revisado else None
            con.execute("""
                INSERT INTO revisiones_stock_lineas
                    (revision_id, material_id, codigo, nombre, ubicacion, unidad,
                     cantidad_sistema, cantidad_contada, revisado, fecha_revision)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (revision_id, material_id, _texto(linea.get("codigo"), 60), _texto(linea.get("nombre")),
                 _texto(linea.get("ubicacion")), _texto(linea.get("unidad"), 20),
                 _numero(linea.get("cantidad_sistema")), contada, revisado,
                 _texto(linea.get("fecha_revision"), 19) if revisado else ""))
        con.commit()
        return True, revision_id
    finally:
        con.close()


def estado_de(total, revisados):
    if total and revisados >= total:
        return ESTADO_COMPLETA
    return ESTADO_PARCIAL if revisados else ESTADO_SIN_EMPEZAR


def listar_revisiones(dias=None, usuario_id=None, estado=None, limite=500, desplazamiento=0, almacen_ids=None):
    """Revisiones, de la más reciente a la más antigua, cada una con `total`
    (artículos propuestos), `revisados`, `ajustados` (con diferencia entre lo
    contado y lo que decía el sistema) y `estado`.

    [dias]: solo las de los últimos N días. [usuario_id]: solo de esa persona.
    [estado]: "completa", "parcial", "sin_empezar" o una lista de ellos.
    [almacen_ids]: solo de esos almacenes (un id, una lista o None = todos). Cada
    revisión lleva `almacen_id` (el efectivo) y `almacen_nombre`."""
    from . import almacenes
    condiciones, parametros = [], []
    if almacen_ids is not None:
        condiciones.append(almacenes.condicion(almacen_ids, "r.almacen_id"))
    if dias:
        condiciones.append("r.fecha >= ?")
        parametros.append((datetime.now() - timedelta(days=int(dias))).strftime("%Y-%m-%d"))
    if usuario_id:
        condiciones.append("r.usuario_id = ?")
        parametros.append(usuario_id)
    donde = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    con = almacen._conn()
    filas = con.execute(f"""
        SELECT r.*,
               COUNT(l.id) AS total,
               COALESCE(SUM(l.revisado), 0) AS revisados,
               COALESCE(SUM(CASE WHEN l.revisado = 1 AND l.cantidad_sistema IS NOT NULL
                                  AND l.cantidad_contada IS NOT NULL
                                  AND ABS(l.cantidad_contada - l.cantidad_sistema) > 0.0000001
                                 THEN 1 ELSE 0 END), 0) AS ajustados
        FROM revisiones_stock r LEFT JOIN revisiones_stock_lineas l ON l.revision_id = r.id
        {donde}
        GROUP BY r.id
        ORDER BY r.fecha DESC, r.actualizada DESC, r.id DESC""", parametros).fetchall()
    con.close()
    resultado = []
    permitidos = {estado} if isinstance(estado, str) else set(estado or [])
    nombres = almacenes.nombres()
    for f in filas:
        d = dict(f)
        d["almacen_id"] = almacenes.efectivo(d.get("almacen_id"))
        d["almacen_nombre"] = nombres.get(d["almacen_id"], "")
        d["estado"] = estado_de(d["total"], d["revisados"])
        if permitidos and d["estado"] not in permitidos:
            continue
        resultado.append(d)
    return resultado[desplazamiento:desplazamiento + limite]


def lineas_de_revision(revision_id):
    """Líneas de una revisión, con la `diferencia` (contada − sistema) cuando
    se revisó."""
    con = almacen._conn()
    filas = con.execute("SELECT * FROM revisiones_stock_lineas WHERE revision_id=? ORDER BY id", (revision_id,)).fetchall()
    con.close()
    lineas = []
    for f in filas:
        d = dict(f)
        if d["revisado"] and d["cantidad_sistema"] is not None and d["cantidad_contada"] is not None:
            d["diferencia"] = d["cantidad_contada"] - d["cantidad_sistema"]
        else:
            d["diferencia"] = None
        lineas.append(d)
    return lineas


def usuarios_con_revisiones():
    """[(usuario_id, nombre)] de quien ha hecho alguna revisión, para el filtro."""
    con = almacen._conn()
    filas = con.execute("""
        SELECT usuario_id, MAX(usuario_nombre) AS nombre FROM revisiones_stock
        WHERE usuario_id IS NOT NULL GROUP BY usuario_id ORDER BY nombre COLLATE NOCASE""").fetchall()
    con.close()
    return [(f["usuario_id"], f["nombre"]) for f in filas]


# ------------------------------------------------- días sin revisión y móviles

def dias_sin_revision(dias=7, hoy=None, festivos=(), almacen_ids=None):
    """Días laborables de los últimos [dias] días en los que nadie revisó ni
    un solo artículo, de más antiguo a más reciente ('AAAA-MM-DD').

    No cuenta el día de hoy (aún no ha acabado), ni sábados, domingos y los
    [festivos] que se pasen (conjunto de 'AAAA-MM-DD'). Tampoco cuenta nada
    anterior a la primera revisión guardada: quien aún no usa la comprobación
    diaria no recibe avisos, y quien la empieza no arrastra días de antes.
    [almacen_ids]: solo las revisiones de esos almacenes (None = todas)."""
    hoy = hoy or datetime.now().date()
    primera, con_revision = _fechas_revisadas(almacen_ids, (hoy - timedelta(days=int(dias))).strftime("%Y-%m-%d"))
    if not primera:
        return []
    festivos = set(festivos or ())
    faltan = []
    for atras in range(int(dias), 0, -1):
        dia = hoy - timedelta(days=atras)
        texto = dia.strftime("%Y-%m-%d")
        if texto < primera or dia.weekday() >= 5 or texto in festivos:
            continue
        if texto not in con_revision:
            faltan.append(texto)
    return faltan


def _fechas_revisadas(almacen_ids, desde):
    """(primera fecha con revisión, {fechas desde [desde] con algún artículo revisado})
    de los almacenes [almacen_ids] (None = todos)."""
    from . import almacenes
    donde = almacenes.condicion(almacen_ids, "r.almacen_id")
    con = almacen._conn()
    primera = con.execute(f"SELECT MIN(r.fecha) FROM revisiones_stock r WHERE {donde}").fetchone()[0]
    fechas = {f[0] for f in con.execute(f"""
        SELECT DISTINCT r.fecha FROM revisiones_stock r
        JOIN revisiones_stock_lineas l ON l.revision_id = r.id
        WHERE l.revisado = 1 AND r.fecha >= ? AND {donde}""", (desde,))} if primera else set()
    con.close()
    return primera, fechas


def ultima_revision(almacen_id):
    """Fecha ('AAAA-MM-DD') de la última revisión del almacén con algún artículo
    revisado, o '' si no hay ninguna."""
    from . import almacenes
    con = almacen._conn()
    fila = con.execute(f"""SELECT MAX(r.fecha) FROM revisiones_stock r
                           JOIN revisiones_stock_lineas l ON l.revision_id = r.id
                           WHERE l.revisado = 1 AND {almacenes.condicion([almacen_id], "r.almacen_id")}""").fetchone()
    con.close()
    return fila[0] or ""


# ------------------------------------------------------ ciclo de cada almacén

PERIODOS_AVISO = {"diario": 7, "semanal": 4, "mensual": 3}   # cuántos periodos atrás se miran


def periodo(ciclo, dia, fecha):
    """(inicio, fin) del periodo de revisión que contiene [fecha] (objetos date).
    Diario: el propio día. Semanal: del [dia] de la semana (0 = lunes) a la víspera
    del siguiente. Mensual: del [dia] del mes (el último si el mes es más corto) a la
    víspera del siguiente."""
    import calendar
    if ciclo == "semanal":
        inicio = fecha - timedelta(days=(fecha.weekday() - dia) % 7)
        return inicio, inicio + timedelta(days=6)

    if ciclo == "mensual":
        def dia_en(anio, mes):
            return fecha.replace(year=anio, month=mes, day=min(dia, calendar.monthrange(anio, mes)[1]))

        def mes_mas(anio, mes, n):
            total = anio * 12 + (mes - 1) + n
            return total // 12, total % 12 + 1

        inicio = dia_en(fecha.year, fecha.month)
        if inicio > fecha:
            inicio = dia_en(*mes_mas(fecha.year, fecha.month, -1))
        siguiente = dia_en(*mes_mas(inicio.year, inicio.month, 1))
        return inicio, siguiente - timedelta(days=1)
    return fecha, fecha


def _laborable(dia, festivos):
    return dia.weekday() < 5 and dia.strftime("%Y-%m-%d") not in festivos


def periodos_sin_revision(almacen, hoy=None, festivos=()):
    """Periodos ya acabados del ciclo del [almacen] (dict de nucleo/almacenes) en los
    que nadie revisó ni un artículo: lista de (inicio, fin) 'AAAA-MM-DD', del más
    antiguo al más reciente. Diario: los días laborables de la última semana (sin hoy).
    Semanal y mensual: las últimas 4 semanas / 3 meses (un periodo sin ningún día
    laborable no cuenta). Nada anterior a la primera revisión del almacén."""
    from . import almacenes
    hoy = hoy or datetime.now().date()
    festivos = set(festivos or ())
    ciclo, dia, _n = almacenes.revision(almacen)
    if ciclo == almacenes.CICLO_DIARIO:
        return [(d, d) for d in dias_sin_revision(PERIODOS_AVISO["diario"], hoy, festivos, [almacen["id"]])]
    periodos = []
    inicio, _fin = periodo(ciclo, dia, hoy)
    for _ in range(PERIODOS_AVISO[ciclo]):
        inicio, fin = periodo(ciclo, dia, inicio - timedelta(days=1))
        periodos.append((inicio, fin))
    periodos.reverse()
    primera, revisadas = _fechas_revisadas([almacen["id"]], periodos[0][0].strftime("%Y-%m-%d"))
    if not primera:
        return []
    faltan = []
    for inicio, fin in periodos:
        a, b = inicio.strftime("%Y-%m-%d"), fin.strftime("%Y-%m-%d")
        if b < primera or any(a <= f <= b for f in revisadas):
            continue
        if not any(_laborable(inicio + timedelta(days=i), festivos) for i in range((fin - inicio).days + 1)):
            continue
        faltan.append((a, b))
    return faltan


def toca_revisar(almacen, hoy=None, festivos=()):
    """Si el [almacen] tiene pendiente la revisión del periodo actual: en el diario, hoy
    si es laborable; en el semanal y mensual, si en el periodo en curso no se ha
    revisado nada todavía."""
    from . import almacenes
    hoy = hoy or datetime.now().date()
    ciclo, dia, _n = almacenes.revision(almacen)
    if ciclo == almacenes.CICLO_DIARIO and not _laborable(hoy, set(festivos or ())):
        return False
    inicio, _fin = periodo(ciclo, dia, hoy)
    _primera, revisadas = _fechas_revisadas([almacen["id"]], inicio.strftime("%Y-%m-%d"))
    return not any(f <= hoy.strftime("%Y-%m-%d") for f in revisadas)


def almacenes_a_revisar(sede=None):
    """Almacenes activos que se ven desde [sede] (None = todos) y cuya sede tiene la
    revisión activada (los comunes, si la tiene la sede principal)."""
    from . import almacenes, sedes
    return [a for a in almacenes.listar(sede) if sedes.revision_activa(a["sede_id"])]


def avisos(sede=None, hoy=None, festivos_de=None):
    """Almacenes con periodos sin revisar: [{almacen, faltan}] (ver periodos_sin_revision).
    [festivos_de]: función sede_id -> conjunto de festivos 'AAAA-MM-DD' (o None)."""
    from . import sedes
    resultado = []
    for a in almacenes_a_revisar(sede):
        festivos = festivos_de(sedes.efectiva(a["sede_id"])) if festivos_de else ()
        faltan = periodos_sin_revision(a, hoy, festivos)
        if faltan:
            resultado.append({"almacen": a, "faltan": faltan})
    return resultado


def moviles_que_revisan(dias=30, hoy=None):
    """Móviles desde los que se han hecho revisiones en los últimos [dias]
    días: [{dispositivo, usuario_nombre, ultima_fecha, revisiones}], el que
    revisó más recientemente primero. `usuario_nombre` es el de la última
    revisión de ese móvil."""
    hoy = hoy or datetime.now().date()
    desde = (hoy - timedelta(days=int(dias))).strftime("%Y-%m-%d")
    con = almacen._conn()
    filas = con.execute("""
        SELECT r.dispositivo, r.usuario_nombre, r.fecha FROM revisiones_stock r
        WHERE r.fecha >= ? AND r.dispositivo != ''
        ORDER BY r.fecha DESC, r.actualizada DESC, r.id DESC""", (desde,)).fetchall()
    con.close()
    por_movil = {}
    for f in filas:
        m = por_movil.setdefault(f["dispositivo"], {"dispositivo": f["dispositivo"],
                                                    "usuario_nombre": f["usuario_nombre"],
                                                    "ultima_fecha": f["fecha"], "revisiones": 0})
        m["revisiones"] += 1
    return list(por_movil.values())
