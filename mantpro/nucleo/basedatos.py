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

"""Acceso a la base de datos de trabajos (mantenimiento.db)."""

import sqlite3
import os
import re

from . import usuarios, almacen, maquinas
from .rutas import DATA_DIR

# Función auxiliar para conectar de forma SEGURA
def get_db_connection(db_path):
    conn = sqlite3.connect(db_path, timeout=20) # 20 segundos de espera antes de dar error
    conn.row_factory = sqlite3.Row
    # ACTIVAR MODO WAL: Esto es vital para evitar lo que te ha pasado
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# --- FUNCIÓN PARA REPARAR LA BASE DE DATOS AUTOMÁTICAMENTE ---
def reparar_base_datos(db_path):
    print(f"Verificando estructura de BD en: {db_path}")
    conn = sqlite3.connect(db_path)
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

    def conectar(self):
        # timeout=20: igual que en almacen.py/usuarios.py/maquinas.py, para no
        # dar "database is locked" cuando el hilo del servidor Flask lee
        # mientras el PC está escribiendo mucho seguido en mantenimiento.db.
        return sqlite3.connect(self.db_name, timeout=20)

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
            conn.commit(); conn.close(); return True
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
            conn.commit(); conn.close(); return True
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
            conn.commit(); conn.close()
            usuarios.registrar_auditoria(usuarios.id_actual(), i, "borrar", detalle)
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
            conn.commit(); conn.close(); return True
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
