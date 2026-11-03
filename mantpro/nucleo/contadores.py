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
contadores.py — Contadores de las máquinas y preventivos por contador.

- Cada máquina puede tener uno o varios **contadores** (horas de uso, ciclos,
  km…) con su unidad.
- Las **lecturas** se apuntan desde el PC, desde la ficha de la máquina en el
  móvil (también sin conexión: cada lectura lleva un identificador propio para
  no duplicarse si se reenvía) y al completar un preventivo por contador.
  La lectura actual es la **más reciente por fecha**, no la mayor: así un
  contador cambiado o puesto a cero sigue funcionando.
- Un aviso recurrente (preventivo) puede ir ligado a un contador: «cada 500 h,
  avisar 50 h antes», con la primera vez a una lectura concreta. Puede tener
  además su frecuencia por fecha («o como máximo cada año»: toca lo que antes
  llegue) o ir solo por contador.
- La lectura apuntada al completar el preventivo queda ligada a él
  (lecturas_contador.aviso_id) y de ella se cuenta el ciclo siguiente.
  Deshacer el completado la desliga (la lectura sigue siendo válida).

Todo vive en mantenimiento.db.
"""

from datetime import datetime, timedelta

from .conexion_bd import sqlite3, conectar

RUTA_DB = None

# Orden de gravedad de los estados de un aviso (para «lo que antes llegue»)
_GRAVEDAD = {"OK": -1, "FUTURO": 0, "PENDIENTE": 1, "ATRASADO": 2}


def configurar_db(ruta):
    global RUTA_DB
    RUTA_DB = ruta


def _conn():
    con = conectar(RUTA_DB, timeout=20)
    con.row_factory = sqlite3.Row
    return con


def _columnas(con, tabla):
    return {f[1] for f in con.execute(f"PRAGMA table_info({tabla})")}


def inicializar():
    con = _conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS contadores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            maquina_id  INTEGER NOT NULL,
            nombre      TEXT NOT NULL,
            unidad      TEXT,
            creado      TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_contadores_maquina ON contadores(maquina_id);
        CREATE TABLE IF NOT EXISTS lecturas_contador (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            contador_id     INTEGER NOT NULL,
            fecha           TEXT NOT NULL,
            valor           REAL NOT NULL,
            usuario_id      INTEGER,
            usuario_nombre  TEXT,
            origen          TEXT,
            aviso_id        INTEGER,
            tarea_id        INTEGER,
            uid             TEXT UNIQUE
        );
        CREATE INDEX IF NOT EXISTS idx_lecturas_contador ON lecturas_contador(contador_id, fecha);
        CREATE INDEX IF NOT EXISTS idx_lecturas_aviso ON lecturas_contador(aviso_id, fecha);
    """)
    try:
        cols = _columnas(con, "avisos_recurrentes")
        for col, tipo in (("contador_id", "INTEGER"), ("cada_valor", "REAL"), ("antelacion_valor", "REAL"),
                          ("primera_valor", "REAL"), ("solo_contador", "INTEGER DEFAULT 0")):
            if col not in cols:
                con.execute(f"ALTER TABLE avisos_recurrentes ADD COLUMN {col} {tipo}")
    except sqlite3.OperationalError:
        pass   # la tabla aún no existe: la crea GestorBaseDatos antes de llamar aquí
    con.commit()
    con.close()


# ------------------------------------------------------------------ utilidades

def numero(v):
    """Número (float) o None a partir de lo que se escriba («1.500», «6,5», «»)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    texto = str(v).strip().replace(" ", "")
    if not texto:
        return None
    # «1.500,5» o «1500,5» → 1500.5; «1.500» (miles) → 1500; «6.5» → 6.5
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif texto.count(".") == 1 and len(texto.split(".")[1]) == 3 and texto.split(".")[0] not in ("", "0"):
        texto = texto.replace(".", "")
    elif texto.count(".") > 1:   # «1.234.567»
        texto = texto.replace(".", "")
    try:
        return float(texto)
    except ValueError:
        return None


def numero_api(v):
    """Número enviado por el móvil (formato de máquina: «1530.5»); si no lo
    es, como lo escribiría una persona (ver numero)."""
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return numero(v)


def cifra(v):
    """Texto de una lectura: sin decimales si es entera, si no con uno o dos."""
    if v is None:
        return "—"
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def con_unidad(v, unidad):
    return f"{cifra(v)} {unidad}".strip() if unidad else cifra(v)


def _ahora():
    return datetime.now().isoformat(timespec="seconds")


def _fecha_lectura(fecha):
    """Normaliza la fecha de una lectura a AAAA-MM-DDTHH:MM:SS. Si solo llega
    el día (p. ej. al completar un preventivo con fecha), se usa la hora
    actual si es hoy y las 12:00 si es otro día."""
    if not fecha:
        return _ahora()
    fecha = str(fecha).strip().replace(" ", "T")
    if len(fecha) == 10:
        if fecha == datetime.now().strftime("%Y-%m-%d"):
            return _ahora()
        return fecha + "T12:00:00"
    return fecha[:19]


def _ruta_maquina(maquina_id):
    from . import maquinas
    try:
        return maquinas.mapa_rutas_completas().get(maquina_id) or ""
    except Exception:
        return ""


# ------------------------------------------------------------------ contadores

def _ultima(con, contador_id):
    return con.execute(
        "SELECT valor, fecha FROM lecturas_contador WHERE contador_id=? ORDER BY fecha DESC, id DESC LIMIT 1",
        (contador_id,)).fetchone()


def listar_contadores(maquina_id=None):
    """[{id, maquina_id, maquina, nombre, unidad, actual, fecha_actual, n_avisos}]"""
    con = _conn()
    sql = "SELECT id, maquina_id, nombre, COALESCE(unidad,'') AS unidad FROM contadores"
    params = ()
    if maquina_id is not None:
        sql += " WHERE maquina_id=?"
        params = (maquina_id,)
    filas = [dict(f) for f in con.execute(sql + " ORDER BY nombre COLLATE NOCASE", params)]
    try:
        usados = dict(con.execute("SELECT contador_id, COUNT(*) FROM avisos_recurrentes "
                                  "WHERE contador_id IS NOT NULL GROUP BY contador_id").fetchall())
    except sqlite3.OperationalError:
        usados = {}
    for f in filas:
        u = _ultima(con, f["id"])
        f["actual"] = u["valor"] if u else None
        f["fecha_actual"] = u["fecha"] if u else None
        f["n_avisos"] = usados.get(f["id"], 0)
    con.close()
    if filas:
        from . import maquinas
        try:
            rutas = maquinas.mapa_rutas_completas()
        except Exception:
            rutas = {}
        for f in filas:
            f["maquina"] = rutas.get(f["maquina_id"], "")
    return filas


def obtener_contador(contador_id):
    return next((c for c in listar_contadores() if c["id"] == contador_id), None)


def por_maquina():
    """{maquina_id: [contadores]} con la lectura actual, para el móvil."""
    resultado = {}
    for c in listar_contadores():
        resultado.setdefault(c["maquina_id"], []).append(
            {"id": c["id"], "nombre": c["nombre"], "unidad": c["unidad"],
             "actual": c["actual"], "fecha_actual": c["fecha_actual"]})
    return resultado


def crear_contador(maquina_id, nombre, unidad="", lectura_inicial=None, usuario=None):
    nombre = (nombre or "").strip()
    if not nombre or maquina_id is None:
        return None
    con = _conn()
    cur = con.execute("INSERT INTO contadores (maquina_id, nombre, unidad, creado) VALUES (?,?,?,?)",
                      (maquina_id, nombre, (unidad or "").strip(), _ahora()))
    nuevo = cur.lastrowid
    con.commit()
    con.close()
    from . import usuarios
    usuarios.auditar("maquinas", "crear", f"{nombre} — {_ruta_maquina(maquina_id)}",
                     cambios=usuarios.diferencias({}, {"nombre": nombre, "unidad": (unidad or "").strip()},
                                                  {"nombre": "Contador", "unidad": "Unidad"}))
    if lectura_inicial is not None:
        registrar_lectura(nuevo, lectura_inicial, usuario=usuario, origen="pc")
    return nuevo


def editar_contador(contador_id, nombre, unidad=""):
    antes = obtener_contador(contador_id)
    nombre = (nombre or "").strip()
    if not antes or not nombre:
        return False
    con = _conn()
    con.execute("UPDATE contadores SET nombre=?, unidad=? WHERE id=?", (nombre, (unidad or "").strip(), contador_id))
    con.commit()
    con.close()
    from . import usuarios
    usuarios.auditar("maquinas", "editar", f"{nombre} — {antes['maquina']}",
                     cambios=usuarios.diferencias({"nombre": antes["nombre"], "unidad": antes["unidad"]},
                                                  {"nombre": nombre, "unidad": (unidad or "").strip()},
                                                  {"nombre": "Contador", "unidad": "Unidad"}))
    return True


def borrar_contador(contador_id):
    """Borra el contador y sus lecturas. No se puede si algún preventivo lo
    usa (devuelve False): primero hay que cambiar o borrar esos preventivos."""
    antes = obtener_contador(contador_id)
    if not antes or antes["n_avisos"]:
        return False
    con = _conn()
    n = con.execute("SELECT COUNT(*) FROM lecturas_contador WHERE contador_id=?", (contador_id,)).fetchone()[0]
    con.execute("DELETE FROM lecturas_contador WHERE contador_id=?", (contador_id,))
    con.execute("DELETE FROM contadores WHERE id=?", (contador_id,))
    con.commit()
    con.close()
    from . import usuarios
    usuarios.auditar("maquinas", "borrar", f"{antes['nombre']} — {antes['maquina']}",
                     cambios=[{"campo": "Contador", "antes": antes["nombre"], "despues": ""},
                              {"campo": "Lecturas", "antes": str(n), "despues": ""},
                              {"campo": "Lectura", "antes": con_unidad(antes["actual"], antes["unidad"]), "despues": ""}])
    return True


def borrar_contadores_de_maquinas(ids_maquinas):
    """Al borrar máquinas: quita sus contadores, sus lecturas y el vínculo de
    los preventivos que los usaban (que pasan a ser solo por fecha)."""
    if not ids_maquinas:
        return
    marcas = ",".join("?" * len(ids_maquinas))
    con = _conn()
    ids = [f[0] for f in con.execute(f"SELECT id FROM contadores WHERE maquina_id IN ({marcas})", list(ids_maquinas))]
    if ids:
        m2 = ",".join("?" * len(ids))
        con.execute(f"DELETE FROM lecturas_contador WHERE contador_id IN ({m2})", ids)
        con.execute(f"DELETE FROM contadores WHERE id IN ({m2})", ids)
        try:
            con.execute(f"UPDATE avisos_recurrentes SET contador_id=NULL, solo_contador=0 WHERE contador_id IN ({m2})", ids)
        except sqlite3.OperationalError:
            pass
    con.commit()
    con.close()


# --------------------------------------------------------------------- lecturas

def registrar_lectura(contador_id, valor, fecha=None, usuario=None, origen="pc", aviso_id=None,
                      tarea_id=None, uid=None):
    """Apunta una lectura. Devuelve su id, o None si el valor no es válido, el
    contador no existe o esa lectura (mismo uid) ya se había recibido."""
    valor = numero(valor)
    if valor is None or valor < 0:
        return None
    if usuario is None:
        from . import usuarios
        usuario = usuarios.SESION_ACTUAL or {}
    con = _conn()
    if not con.execute("SELECT 1 FROM contadores WHERE id=?", (contador_id,)).fetchone():
        con.close()
        return None
    if uid and con.execute("SELECT 1 FROM lecturas_contador WHERE uid=?", (uid,)).fetchone():
        con.close()
        return None
    cur = con.execute(
        "INSERT INTO lecturas_contador (contador_id, fecha, valor, usuario_id, usuario_nombre, origen, aviso_id, tarea_id, uid) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (contador_id, _fecha_lectura(fecha), valor, (usuario or {}).get("id"), (usuario or {}).get("nombre"),
         origen, aviso_id, tarea_id, uid or None))
    nuevo = cur.lastrowid
    con.commit()
    con.close()
    return nuevo


def lecturas(contador_id, limite=500):
    """Lecturas del contador, las más recientes primero, con el preventivo
    al que van ligadas (si se apuntaron al completarlo)."""
    con = _conn()
    filas = [dict(f) for f in con.execute(
        "SELECT l.*, a.titulo AS aviso FROM lecturas_contador l "
        "LEFT JOIN avisos_recurrentes a ON a.id = l.aviso_id "
        "WHERE l.contador_id=? ORDER BY l.fecha DESC, l.id DESC LIMIT ?", (contador_id, limite))]
    con.close()
    return filas


def borrar_lectura(lectura_id):
    con = _conn()
    fila = con.execute("SELECT l.*, c.nombre, c.unidad, c.maquina_id FROM lecturas_contador l "
                       "JOIN contadores c ON c.id = l.contador_id WHERE l.id=?", (lectura_id,)).fetchone()
    if not fila:
        con.close()
        return False
    con.execute("DELETE FROM lecturas_contador WHERE id=?", (lectura_id,))
    con.commit()
    con.close()
    from . import usuarios
    usuarios.auditar("maquinas", "borrar", f"{fila['nombre']} — {_ruta_maquina(fila['maquina_id'])}",
                     cambios=[{"campo": "Lectura", "despues": "",
                               "antes": f"{con_unidad(fila['valor'], fila['unidad'] or '')} · {fila['fecha'].replace('T', ' ')[:16]}"
                                        f" · {fila['usuario_nombre'] or '—'}"}])
    return True


def ritmo_diario(contador_id, con=None):
    """Uso medio por día (unidades/día) con las lecturas de los últimos 180
    días, o None si no hay datos suficientes. Sirve para estimar la fecha en
    que llegará al próximo preventivo."""
    propia = con is None
    con = con or _conn()
    desde = (datetime.now() - timedelta(days=180)).isoformat(timespec="seconds")
    filas = con.execute("SELECT fecha, valor FROM lecturas_contador WHERE contador_id=? AND fecha>=? "
                        "ORDER BY fecha, id", (contador_id, desde)).fetchall()
    if propia:
        con.close()
    if len(filas) < 2:
        return None
    # Desde la última vez que el contador bajó (cambio o puesta a cero)
    inicio = 0
    for i in range(1, len(filas)):
        if filas[i]["valor"] < filas[i - 1]["valor"]:
            inicio = i
    filas = filas[inicio:]
    if len(filas) < 2:
        return None
    try:
        dias = (datetime.fromisoformat(filas[-1]["fecha"]) - datetime.fromisoformat(filas[0]["fecha"])).total_seconds() / 86400
    except ValueError:
        return None
    subida = filas[-1]["valor"] - filas[0]["valor"]
    if dias < 1 or subida <= 0:
        return None
    return subida / dias


# --------------------------------------------------------- preventivos por contador

def config_aviso(aviso_id):
    """Configuración del contador de un aviso, o None si es solo por fecha."""
    return estados_avisos().get(aviso_id)


def fijar_aviso(aviso_id, config):
    """Liga (o desliga, con config vacía/None) un aviso a un contador.
    config = {contador_id, cada, antelacion, primera, solo_contador}."""
    con = _conn()
    if not config or not config.get("contador_id"):
        con.execute("UPDATE avisos_recurrentes SET contador_id=NULL, cada_valor=NULL, antelacion_valor=NULL, "
                    "primera_valor=NULL, solo_contador=0 WHERE id=?", (aviso_id,))
    else:
        con.execute("UPDATE avisos_recurrentes SET contador_id=?, cada_valor=?, antelacion_valor=?, primera_valor=?, "
                    "solo_contador=? WHERE id=?",
                    (config["contador_id"], numero(config.get("cada")), numero(config.get("antelacion")) or 0,
                     numero(config.get("primera")), 1 if config.get("solo_contador") else 0, aviso_id))
    con.commit()
    con.close()


def ids_solo_contador():
    """Avisos que van solo por contador (sin fecha): el calendario no los
    pinta y el resto de cálculos por fecha los saltan."""
    try:
        con = _conn()
        ids = {f[0] for f in con.execute("SELECT id FROM avisos_recurrentes WHERE contador_id IS NOT NULL "
                                         "AND COALESCE(solo_contador,0)=1")}
        con.close()
        return ids
    except Exception:
        return set()


def estado_por_valor(actual, proximo, antelacion):
    """FUTURO / PENDIENTE (dentro de la antelación) / ATRASADO (pasado)."""
    if actual is None or proximo is None:
        return "FUTURO"
    if actual > proximo:
        return "ATRASADO"
    if actual >= proximo - (antelacion or 0):
        return "PENDIENTE"
    return "FUTURO"


def peor(estado_a, estado_b):
    return estado_a if _GRAVEDAD.get(estado_a, 0) >= _GRAVEDAD.get(estado_b, 0) else estado_b


def estados_avisos():
    """{aviso_id: info} de los avisos ligados a un contador, con todo lo que
    hace falta para pintarlos y para que el móvil los recalcule sin conexión:
    contador, unidad, máquina, cada, antelación, solo_contador, lectura actual
    (y su fecha), lectura del último completado, próximo, estado por contador,
    lo que falta y la fecha estimada de llegada según el ritmo de uso."""
    con = _conn()
    try:
        avisos = con.execute(
            "SELECT a.id, a.contador_id, a.cada_valor, a.antelacion_valor, a.primera_valor, "
            "COALESCE(a.solo_contador,0) AS solo, c.nombre, COALESCE(c.unidad,'') AS unidad, c.maquina_id "
            "FROM avisos_recurrentes a JOIN contadores c ON c.id = a.contador_id").fetchall()
    except sqlite3.OperationalError:
        con.close()
        return {}
    resultado = {}
    rutas = None
    ritmos = {}
    for a in avisos:
        u = _ultima(con, a["contador_id"])
        actual = u["valor"] if u else None
        ult = con.execute("SELECT valor FROM lecturas_contador WHERE aviso_id=? ORDER BY fecha DESC, id DESC LIMIT 1",
                          (a["id"],)).fetchone()
        cada = a["cada_valor"] or 0
        if ult is not None:
            proximo = ult["valor"] + cada
        elif a["primera_valor"] is not None:
            proximo = a["primera_valor"]
        else:
            proximo = cada
        antelacion = a["antelacion_valor"] or 0
        if a["contador_id"] not in ritmos:
            ritmos[a["contador_id"]] = ritmo_diario(a["contador_id"], con)
        ritmo = ritmos[a["contador_id"]]
        estimada = None
        if ritmo and actual is not None and proximo > actual:
            try:
                estimada = (datetime.fromisoformat(u["fecha"]) + timedelta(days=(proximo - actual) / ritmo)).strftime("%Y-%m-%d")
            except (ValueError, OverflowError):
                estimada = None
        if rutas is None:
            from . import maquinas
            try:
                rutas = maquinas.mapa_rutas_completas()
            except Exception:
                rutas = {}
        resultado[a["id"]] = {
            "contador_id": a["contador_id"], "contador": a["nombre"], "unidad": a["unidad"],
            "maquina_id": a["maquina_id"], "maquina": rutas.get(a["maquina_id"], ""),
            "cada": cada, "antelacion": antelacion, "primera": a["primera_valor"],
            "solo_contador": bool(a["solo"]),
            "actual": actual, "fecha_actual": u["fecha"] if u else None,
            "ultima_valor": ult["valor"] if ult else None,
            "proximo": proximo, "restante": (proximo - actual) if actual is not None else None,
            "estado": estado_por_valor(actual, proximo, antelacion),
            "ritmo": ritmo, "estimada": estimada,
        }
    con.close()
    return resultado


def texto_proximo(info, lbl_ahora="ahora", lbl_sin_lecturas="sin lecturas"):
    """«1500 h (ahora 1430 h)»."""
    u = info["unidad"]
    actual = con_unidad(info["actual"], u) if info["actual"] is not None else lbl_sin_lecturas
    return f"{con_unidad(info['proximo'], u)} ({lbl_ahora} {actual})"


def texto_cada(info, lbl_cada="Cada"):
    return f"{lbl_cada} {con_unidad(info['cada'], info['unidad'])}"


def registrar_completado(aviso_id, valor, fecha=None, usuario=None, origen="pc", tarea_id=None, uid=None):
    """Al completar un preventivo por contador: apunta la lectura de ese
    momento ligada al aviso (de ella se cuenta el ciclo siguiente) y, si el
    trabajo del historial aún no tiene máquina, lo liga a la del contador."""
    con = _conn()
    fila = con.execute("SELECT a.contador_id, c.maquina_id FROM avisos_recurrentes a "
                       "JOIN contadores c ON c.id = a.contador_id WHERE a.id=?", (aviso_id,)).fetchone()
    con.close()
    if not fila:
        return None
    if tarea_id:
        con = _conn()
        con.execute("UPDATE tareas SET maquina_id=? WHERE id=? AND maquina_id IS NULL", (fila["maquina_id"], tarea_id))
        con.commit()
        con.close()
    if numero(valor) is None:
        return None
    return registrar_lectura(fila["contador_id"], valor, fecha=fecha, usuario=usuario, origen=origen,
                             aviso_id=aviso_id, tarea_id=tarea_id, uid=uid)


def olvidar_trabajo(tarea_id):
    """El trabajo del historial se ha borrado o ha vuelto a pendientes."""
    con = _conn()
    con.execute("UPDATE lecturas_contador SET aviso_id=NULL, tarea_id=NULL WHERE tarea_id=?", (tarea_id,))
    con.commit()
    con.close()


def deshacer_completado(aviso_id):
    """Al deshacer el último completado: la lectura que se apuntó deja de
    contar como inicio del ciclo (sigue en el historial de lecturas)."""
    con = _conn()
    fila = con.execute("SELECT id FROM lecturas_contador WHERE aviso_id=? ORDER BY fecha DESC, id DESC LIMIT 1",
                       (aviso_id,)).fetchone()
    if fila:
        con.execute("UPDATE lecturas_contador SET aviso_id=NULL, tarea_id=NULL WHERE id=?", (fila["id"],))
        con.commit()
    con.close()
