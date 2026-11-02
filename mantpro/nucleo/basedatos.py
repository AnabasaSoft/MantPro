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

"""Acceso a la base de datos de trabajos (mantenimiento.db)."""

from .conexion_bd import sqlite3, conectar
import os
import re

from . import usuarios, almacen, maquinas, checklists
from .rutas import DATA_DIR

# Función auxiliar para conectar de forma SEGURA
def get_db_connection(db_path):
    conn = conectar(db_path, timeout=20) # 20 segundos de espera antes de dar error
    conn.row_factory = sqlite3.Row
    # ACTIVAR MODO WAL: Esto es vital para evitar lo que te ha pasado
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# --- FUNCIÓN PARA REPARAR LA BASE DE DATOS AUTOMÁTICAMENTE ---
def reparar_base_datos(db_path):
    print(f"Verificando estructura de BD en: {db_path}")
    conn = conectar(db_path)
    c = conn.cursor()

    # 1. Intentar añadir columna 'raw_desc' si falta
    try:
        c.execute("ALTER TABLE tareas ADD COLUMN raw_desc TEXT")
        print("🔧 REPARACIÓN: Columna 'raw_desc' añadida con éxito.")
    except sqlite3.OperationalError:
        pass # La columna ya existe, no hacemos nada

    # 2. Intentar añadir columna 'foto' si falta (por seguridad)
    try:
        c.execute("ALTER TABLE tareas ADD COLUMN foto TEXT")
        print("🔧 REPARACIÓN: Columna 'foto' añadida con éxito.")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# ==========================================
# 2. GESTORES DE DATOS
# ==========================================

class GestorBaseDatos:
    def __init__(self):
        # USAMOS DATA_DIR PARA UBICAR LA DB
        # La lógica de DATA_DIR se calcula arriba globalmente
        self.db_name = os.path.join(DATA_DIR, "mantenimiento.db")
        self.inicializar_tablas()
        # Tablas de usuarios/sesiones + columnas de autoría (idempotente)
        usuarios.configurar_db(self.db_name)
        usuarios.inicializar()
        # Stock de almacén: base de datos propia, separada de la de trabajos
        self.db_almacen_name = os.path.join(DATA_DIR, "almacen.db")
        almacen.configurar_db(self.db_almacen_name)
        almacen.inicializar()
        # Listado de maquinaria + vínculo de cada trabajo con su máquina (idempotente)
        maquinas.configurar_db(self.db_name)
        maquinas.inicializar()
        # Listas de comprobación (plantillas, su asignación a avisos y
        # pendientes, y lo rellenado en cada trabajo)
        checklists.configurar_db(self.db_name)
        checklists.inicializar()

    def conectar(self):
        # timeout=20: igual que en almacen.py/usuarios.py/maquinas.py, para no
        # dar "database is locked" cuando el hilo del servidor Flask lee
        # mientras el PC está escribiendo mucho seguido en mantenimiento.db.
        return conectar(self.db_name, timeout=20)

    def inicializar_tablas(self):
        try:
            conn = self.conectar()
            c = conn.cursor()
            c.execute('CREATE TABLE IF NOT EXISTS tareas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, descripcion TEXT, tags TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS dias_especiales (fecha TEXT PRIMARY KEY, tipo TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS pendientes (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT, detalles TEXT)')
            c.execute('CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)')

            necesita_recrear = False
            try:
                c.execute("PRAGMA table_info(avisos_recurrentes)")
                cols = [info[1] for info in c.fetchall()]
                if 'mes' in cols: necesita_recrear = True
            except: pass

            if necesita_recrear:
                c.execute("DROP TABLE IF EXISTS avisos_recurrentes")

            c.execute('''CREATE TABLE IF NOT EXISTS avisos_recurrentes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        titulo TEXT, fecha_inicio TEXT, frecuencia TEXT, duracion_dias INTEGER, ultima_completada TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e: print(f"Error crítico inicializando BD: {e}")

    def set_config(self, clave, valor):
        try:
            conn = self.conectar()
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO config (clave, valor) VALUES (?, ?)', (clave, valor))
            conn.commit()
            conn.close()
            return True
        except: return False

    def get_config(self, clave):
        try:
            conn = self.conectar()
            c = conn.cursor()
            c.execute('SELECT valor FROM config WHERE clave = ?', (clave,))
            res = c.fetchone()
            conn.close()
            return res[0] if res else None
        except: return None

    def agregar_aviso(self, titulo, fecha_inicio, frecuencia, duracion, asignado_a=None, asignado_nombre=None, especialidad_id=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('INSERT INTO avisos_recurrentes (titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, asignado_a, asignado_nombre, especialidad_id) VALUES (?,?,?,?,?,?,?,?)',
                      (titulo, fecha_inicio, frecuencia, duracion, "", asignado_a, asignado_nombre, especialidad_id))
            nuevo_id = c.lastrowid
            conn.commit(); conn.close(); return nuevo_id
        except Exception as e: return False

    def actualizar_aviso(self, id_aviso, titulo, fecha_inicio, frecuencia, duracion, asignado_a=None, asignado_nombre=None, especialidad_id=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE avisos_recurrentes SET titulo=?, fecha_inicio=?, frecuencia=?, duracion_dias=?, asignado_a=?, asignado_nombre=?, especialidad_id=? WHERE id=?',
                      (titulo, fecha_inicio, frecuencia, duracion, asignado_a, asignado_nombre, especialidad_id, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False

    def obtener_avisos(self):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('SELECT id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, '
                      'asignado_a, COALESCE(asignado_nombre,\'\'), especialidad_id FROM avisos_recurrentes')
            return c.fetchall()
        except: return []
    def borrar_aviso(self, i):
        try: conn = self.conectar(); c = conn.cursor(); c.execute('DELETE FROM avisos_recurrentes WHERE id=?', (i,)); conn.commit(); conn.close(); return True
        except: return False
    def asignar_aviso(self, id_aviso, asignado_a, asignado_nombre):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE avisos_recurrentes SET asignado_a=?, asignado_nombre=? WHERE id=?',
                      (asignado_a, asignado_nombre, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False
    def asignar_especialidad_aviso(self, id_aviso, especialidad_id):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE avisos_recurrentes SET especialidad_id=? WHERE id=?',
                      (especialidad_id, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False
    def marcar_aviso_completado(self, id_aviso, fecha_completada, estado):
        try:
            conn = self.conectar(); c = conn.cursor(); val = fecha_completada if estado else ""
            c.execute('UPDATE avisos_recurrentes SET ultima_completada=? WHERE id=?', (val, id_aviso))
            conn.commit(); conn.close(); return True
        except: return False

    def agregar_tarea(self, f, d, t, usuario_id=None, usuario_nombre=None, maquina_id=None, horas_paro=None):
        """Guarda un registro atribuido al usuario que ha iniciado sesión."""
        if usuario_id is None: usuario_id = usuarios.id_actual()
        if usuario_nombre is None: usuario_nombre = usuarios.nombre_actual()
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('INSERT INTO tareas (fecha,descripcion,tags,usuario_id,usuario_nombre,maquina_id,horas_paro) VALUES (?,?,?,?,?,?,?)',
                      (f, d, t, usuario_id, usuario_nombre, maquina_id, horas_paro))
            nuevo_id = c.lastrowid
            conn.commit(); conn.close(); return nuevo_id   # id del trabajo (cierto, como antes)
        except Exception as e:
            print(f"Error agregar_tarea: {e}"); return False
    def obtener_todas_cronologico(self, filtro_usuario=None):
        try:
            conn=self.conectar(); c=conn.cursor()
            sql = "SELECT id,fecha,descripcion,tags,COALESCE(usuario_nombre,''),maquina_id FROM tareas"
            params = []
            if filtro_usuario:
                sql += " WHERE usuario_nombre = ?"
                params.append(filtro_usuario)
            sql += " ORDER BY fecha DESC, id DESC"
            c.execute(sql, params)
            return c.fetchall()
        except: return []
    def obtener_tareas_por_fecha(self,f):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT id,descripcion,tags FROM tareas WHERE fecha=?',(f,)); return c.fetchall()
        except: return []
    def borrar_tarea(self, i):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute("SELECT fecha, descripcion, COALESCE(usuario_nombre,'') FROM tareas WHERE id=?", (i,))
            fila = c.fetchone()
            detalle = ""
            if fila:
                desc_corta = fila[1][:80].split("\n")[0]
                detalle = f"Registro del {fila[0]}: {desc_corta} (autor original: {fila[2] or 'Histórico'})"
            c.execute('DELETE FROM tareas WHERE id=?', (i,))
            c.execute('DELETE FROM checklist_resultados WHERE tarea_id=?', (i,))
            conn.commit(); conn.close()
            usuarios.registrar_auditoria(None, i, "borrar", detalle, "trabajos",
                                         objeto=(fila[1].split("\n")[0][:120] if fila else ""))
            return True
        except Exception as e:
            print(f"Error borrar_tarea: {e}"); return False
    def actualizar_tarea(self, i, f, d, t, usuario_id=None, usuario_nombre=None, maquina_id=None, horas_paro=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            if usuario_id is not None:
                c.execute('UPDATE tareas SET fecha=?, descripcion=?, tags=?, usuario_id=?, usuario_nombre=?, maquina_id=?, horas_paro=? WHERE id=?',
                          (f, d, t, usuario_id, usuario_nombre, maquina_id, horas_paro, i))
            else:
                c.execute('UPDATE tareas SET fecha=?, descripcion=?, tags=?, maquina_id=?, horas_paro=? WHERE id=?', (f, d, t, maquina_id, horas_paro, i))
            conn.commit(); conn.close(); return True
        except: return False
    def obtener_tarea_por_id(self, i):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute("SELECT id, fecha, descripcion, tags, usuario_id, COALESCE(usuario_nombre,''), maquina_id, horas_paro FROM tareas WHERE id=?", (i,))
            return c.fetchone()
        except: return None
    def buscar_tareas_avanzado(self, texto, fecha=None):
        try:
            conn = self.conectar(); c = conn.cursor(); param_texto = f"%{texto}%"
            query = "SELECT id, fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id FROM tareas WHERE (descripcion LIKE ? OR tags LIKE ?)"
            parametros = [param_texto, param_texto]
            if fecha: query += " AND fecha = ?"; parametros.append(fecha)
            query += " ORDER BY fecha DESC, id DESC"; c.execute(query, parametros); return c.fetchall()
        except: return []
    def obtener_fechas_con_tareas(self):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT DISTINCT fecha FROM tareas'); return [x[0] for x in c.fetchall()]
        except: return []
    def obtener_todas_las_descripciones(self):
        try:
            conn=self.conectar(); c=conn.cursor(); c.execute('SELECT DISTINCT descripcion FROM tareas'); l=[]
            for r in c.fetchall(): t=re.sub(r"\[FOTO:.*?\]","",r[0]).strip().split('\n')[0].replace("[DESDE PENDIENTES] ","").strip(); (l.append(t) if t else None)
            conn.close(); return sorted(list(set(l)))
        except: return []
    def marcar_dia_especial(self,f,t):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('INSERT OR REPLACE INTO dias_especiales (fecha,tipo) VALUES (?,?)',(f,t)); conn.commit(); conn.close(); return True
        except: return False
    def borrar_dia_especial(self,f):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('DELETE FROM dias_especiales WHERE fecha=?',(f,)); conn.commit(); conn.close(); return True
        except: return False
    def obtener_dias_especiales(self):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('SELECT fecha,tipo FROM dias_especiales'); return {r[0]:r[1] for r in c.fetchall()}
        except: return {}
    def agregar_pendiente(self, t, d, asignado_a=None, asignado_nombre=None, prioridad="Media", especialidad_id=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('INSERT INTO pendientes (titulo,detalles,asignado_a,asignado_nombre,prioridad,especialidad_id) VALUES (?,?,?,?,?,?)',
                      (t, d, asignado_a, asignado_nombre, prioridad, especialidad_id))
            nuevo_id = c.lastrowid
            conn.commit(); conn.close(); return nuevo_id
        except Exception as e:
            print(f"Error agregar_pendiente: {e}"); return False
    def obtener_pendientes(self):
        """Devuelve (id, titulo, detalles, asignado_a, asignado_nombre, prioridad, especialidad_id)."""
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute("SELECT id,titulo,detalles,asignado_a,COALESCE(asignado_nombre,''),COALESCE(prioridad,'Media'),especialidad_id FROM pendientes ORDER BY id DESC")
            return c.fetchall()
        except: return []
    def asignar_pendiente(self, id_p, asignado_a, asignado_nombre):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE pendientes SET asignado_a=?, asignado_nombre=? WHERE id=?',
                      (asignado_a, asignado_nombre, id_p))
            conn.commit(); conn.close(); return True
        except: return False
    def asignar_especialidad_pendiente(self, id_p, especialidad_id):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE pendientes SET especialidad_id=? WHERE id=?',
                      (especialidad_id, id_p))
            conn.commit(); conn.close(); return True
        except: return False
    def borrar_pendiente(self,i):
        try: conn=self.conectar(); c=conn.cursor(); c.execute('DELETE FROM pendientes WHERE id=?',(i,)); conn.commit(); conn.close(); return True
        except: return False
    def actualizar_pendiente(self, i, t, d, prioridad="Media", especialidad_id=None):
        try:
            conn = self.conectar(); c = conn.cursor()
            c.execute('UPDATE pendientes SET titulo=?, detalles=?, prioridad=?, especialidad_id=? WHERE id=?', (t, d, prioridad, especialidad_id, i))
            conn.commit(); conn.close(); return True
        except: return False


# ==========================================
# 3. REGISTRO DE CAMBIOS (Herramientas → Registro de cambios)
# ==========================================
# Las operaciones de GestorBaseDatos que cambian trabajos, pendientes, avisos
# y días del calendario apuntan qué ha cambiado, campo a campo. Se envuelven
# aquí para no repetir el código en cada pestaña que las usa.

from functools import wraps as _wraps

_PRIORIDADES = {"Baja": "Baja", "Media": "Media", "Alta": "Alta", "Crítica": "Crítica"}


def _limpiar_desc(desc):
    desc = re.sub(r"\[FOTO.*?:.*?\]", "", desc or "")
    return re.sub(r"\[REF:.*?\]", "", desc).strip()


def _nombre_especialidad(eid):
    if not eid:
        return ""
    return next((e["nombre"] for e in usuarios.listar_especialidades() if e["id"] == eid), str(eid))


def _foto_tarea(db, i):
    d = db.obtener_tarea_por_id(i)
    if not d:
        return {}
    rutas = maquinas.mapa_rutas_completas() if d[6] else {}
    return {"fecha": d[1], "descripcion": _limpiar_desc(d[2]), "tags": d[3], "autor": d[5] or usuarios.ETIQUETA_HISTORICO,
            "maquina": rutas.get(d[6], "") if d[6] else "", "horas_paro": d[7] if d[7] is not None else ""}


_ETIQ_TAREA = {"fecha": "Fecha", "descripcion": "Descripción", "tags": "Etiquetas", "autor": "Realizado por",
               "maquina": "Máquina", "horas_paro": "Horas de paro"}


def _foto_pendiente(db, i):
    try:
        con = db.conectar()
        f = con.execute("SELECT titulo, detalles, asignado_nombre, prioridad, especialidad_id FROM pendientes WHERE id=?", (i,)).fetchone()
        con.close()
    except Exception:
        return {}
    if not f:
        return {}
    return {"titulo": f[0], "detalles": _limpiar_desc(f[1]), "asignado": f[2] or "", "prioridad": f[3] or "",
            "especialidad": _nombre_especialidad(f[4])}


_ETIQ_PENDIENTE = {"titulo": "Título", "detalles": "Detalles", "asignado": "Asignado a", "prioridad": "Prioridad",
                   "especialidad": "Especialidad"}


def _foto_aviso(db, i):
    a = next((x for x in db.obtener_avisos() if x[0] == i), None)
    if not a:
        return {}
    return {"titulo": a[1], "inicio": a[2], "frecuencia": a[3], "margen": a[4], "ultima": a[5] or "",
            "asignado": a[7] or "", "especialidad": _nombre_especialidad(a[8])}


_ETIQ_AVISO = {"titulo": "Título", "inicio": "Fecha de inicio", "frecuencia": "Frecuencia", "margen": "Días de margen",
               "asignado": "Asignado a", "especialidad": "Especialidad"}


def _envolver_edicion(nombre_metodo, foto, etiquetas, categoria, accion="editar"):
    original = getattr(GestorBaseDatos, nombre_metodo)

    @_wraps(original)
    def envoltorio(self, item_id, *args, **kwargs):
        antes = foto(self, item_id)
        resultado = original(self, item_id, *args, **kwargs)
        if resultado:
            despues = foto(self, item_id)
            usuarios.auditar(categoria, accion, despues.get("titulo") or (despues.get("descripcion") or "").split("\n")[0],
                             cambios=usuarios.diferencias(antes, despues, etiquetas),
                             objeto_id=item_id if categoria == "trabajos" else None)
        return resultado
    setattr(GestorBaseDatos, nombre_metodo, envoltorio)


for _m in ("actualizar_tarea",):
    _envolver_edicion(_m, _foto_tarea, _ETIQ_TAREA, "trabajos")
for _m in ("actualizar_pendiente", "asignar_pendiente", "asignar_especialidad_pendiente"):
    _envolver_edicion(_m, _foto_pendiente, _ETIQ_PENDIENTE, "pendientes")
for _m in ("actualizar_aviso", "asignar_aviso", "asignar_especialidad_aviso"):
    _envolver_edicion(_m, _foto_aviso, _ETIQ_AVISO, "avisos")


def _envolver_creacion(nombre_metodo, foto, etiquetas, categoria):
    original = getattr(GestorBaseDatos, nombre_metodo)

    @_wraps(original)
    def envoltorio(self, *args, **kwargs):
        nuevo_id = original(self, *args, **kwargs)
        if nuevo_id:
            despues = foto(self, nuevo_id)
            usuarios.auditar(categoria, "crear", despues.get("titulo", ""),
                             cambios=usuarios.diferencias({}, despues, etiquetas))
        return nuevo_id
    setattr(GestorBaseDatos, nombre_metodo, envoltorio)


_envolver_creacion("agregar_pendiente", _foto_pendiente, _ETIQ_PENDIENTE, "pendientes")
_envolver_creacion("agregar_aviso", _foto_aviso, _ETIQ_AVISO, "avisos")


def _resumen(foto, etiquetas):
    return "\n".join(f"{etiquetas[k]}: {foto[k]}" for k in etiquetas if foto.get(k) not in (None, ""))


_borrar_aviso_original = GestorBaseDatos.borrar_aviso


def _borrar_aviso(self, i):
    antes = _foto_aviso(self, i)
    ok = _borrar_aviso_original(self, i)
    if ok and antes:
        usuarios.auditar("avisos", "borrar", antes.get("titulo", ""), cambios=usuarios.diferencias(antes, {}, _ETIQ_AVISO))
    return ok


GestorBaseDatos.borrar_aviso = _borrar_aviso

_borrar_pendiente_original = GestorBaseDatos.borrar_pendiente


def _borrar_pendiente(self, i, motivo="borrar"):
    """motivo="completar" cuando el pendiente pasa al historial (no es un borrado)."""
    antes = _foto_pendiente(self, i)
    ok = _borrar_pendiente_original(self, i)
    if ok and antes:
        if motivo == "completar":
            usuarios.auditar("pendientes", "completar", antes.get("titulo", ""), detalle="Pasa al historial")
        else:
            usuarios.auditar("pendientes", "borrar", antes.get("titulo", ""), cambios=usuarios.diferencias(antes, {}, _ETIQ_PENDIENTE))
    return ok


GestorBaseDatos.borrar_pendiente = _borrar_pendiente

_marcar_aviso_original = GestorBaseDatos.marcar_aviso_completado


def _marcar_aviso(self, id_aviso, fecha_completada, estado):
    antes = _foto_aviso(self, id_aviso)
    ok = _marcar_aviso_original(self, id_aviso, fecha_completada, estado)
    if antes:
        if estado and fecha_completada and fecha_completada != antes.get("ultima"):
            usuarios.auditar("avisos", "completar", antes.get("titulo", ""), detalle=f"Completado el {fecha_completada}")
        elif not estado or fecha_completada != antes.get("ultima"):
            usuarios.auditar("avisos", "descompletar", antes.get("titulo", ""),
                             cambios=usuarios.diferencias({"u": antes.get("ultima")}, {"u": fecha_completada or ""},
                                                          {"u": "Última vez completado"}))
    return ok


GestorBaseDatos.marcar_aviso_completado = _marcar_aviso

for _m, _accion in (("marcar_dia_especial", "crear"), ("borrar_dia_especial", "borrar")):
    def _hacer(original, accion):
        @_wraps(original)
        def envoltorio(self, fecha, *args):
            ok = original(self, fecha, *args)
            usuarios.auditar("configuracion", accion, f"Día especial {fecha}",
                             detalle=(f"Tipo: {args[0]}" if args else ""))
            return ok
        return envoltorio
    setattr(GestorBaseDatos, _m, _hacer(getattr(GestorBaseDatos, _m), _accion))


class LectorBD:
    """Lo justo de GestorBaseDatos para leer el estado de un trabajo, un
    pendiente o un aviso desde otra parte (el servidor de los móviles), sin
    volver a preparar las tablas."""

    def __init__(self, ruta):
        self.db_name = ruta

    def conectar(self):
        return conectar(self.db_name, timeout=20)

    obtener_tarea_por_id = GestorBaseDatos.obtener_tarea_por_id
    obtener_avisos = GestorBaseDatos.obtener_avisos


# Para el servidor de los móviles: fotografía de cada cosa y nombres de campo
foto_tarea, foto_pendiente, foto_aviso = _foto_tarea, _foto_pendiente, _foto_aviso
ETIQ_TAREA, ETIQ_PENDIENTE, ETIQ_AVISO = _ETIQ_TAREA, _ETIQ_PENDIENTE, _ETIQ_AVISO


_CONFIG_AUDITADA = {"puerto_servidor": "Puerto de sincronización", "country_iso": "País (festivos)",
                    "region_iso": "Región (festivos)", "parent_iso": "Región superior (festivos)",
                    "idioma": "Idioma"}
_set_config_original = GestorBaseDatos.set_config


def _set_config(self, clave, valor):
    antes = self.get_config(clave) if clave in _CONFIG_AUDITADA else None
    ok = _set_config_original(self, clave, valor)
    if ok and clave in _CONFIG_AUDITADA and (antes or "") != (valor or ""):
        usuarios.auditar("configuracion", "configurar", _CONFIG_AUDITADA[clave],
                         cambios=[{"campo": _CONFIG_AUDITADA[clave], "antes": antes or "", "despues": valor or ""}])
    return ok


GestorBaseDatos.set_config = _set_config
