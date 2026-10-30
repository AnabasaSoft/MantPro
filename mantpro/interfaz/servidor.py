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

"""Servidor de sincronización con las apps móviles (Flask en un hilo de Qt)."""

import json
import os
import socket
import re
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, g
from PyQt6.QtCore import pyqtSignal, QThread

from .. import idiomas
from ..nucleo import usuarios, almacen, maquinas
from ..nucleo.basedatos import get_db_connection
from ..nucleo.fotos import con_fotos_galeria, fotos_galeria

PUERTO_POR_DEFECTO = 5000


def puerto_libre(puerto):
    """True si el servidor de sincronización podría escuchar en [puerto]
    (mismas opciones de socket que usa Werkzeug)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if os.name != "nt":
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", puerto))
        return True
    except OSError:
        return False
    finally:
        s.close()


def primer_puerto_libre(desde):
    for p in range(desde, min(desde + 200, 65536)):
        if puerto_libre(p): return p
    return desde


class ServidorSincronizacion(QThread):
    registro_recibido = pyqtSignal(str, str, str, str, str)
    pendiente_actualizado = pyqtSignal()
    stock_actualizado = pyqtSignal()

    error_arranque = pyqtSignal(str)

    def __init__(self, carpeta_destino, db_path, puerto=None):
        super().__init__()
        self.carpeta_destino = carpeta_destino
        self.db_path = db_path
        self.app = Flask(__name__)
        self.server_port = puerto or PUERTO_POR_DEFECTO
        usuarios.configurar_db(db_path)

        # Reutilizamos get_db_connection (timeout=20 + modo WAL) para que
        # este hilo (servidor Flask para las apps móviles) no lance
        # "database is locked" al chocar con la GUI, igual que ya se hacía
        # en un par de rutas de esta misma clase.
        self._conn = lambda: get_db_connection(self.db_path)

        # --- AUTENTICACIÓN POR TOKEN ---------------------------------------
        def _token_peticion():
            cabecera = request.headers.get('Authorization', '')
            if cabecera.startswith('Bearer '):
                return cabecera[7:].strip()
            return request.headers.get('X-MantPro-Token', '')

        def _usuario_peticion():
            """Devuelve el usuario del token, o None si no es válido. De paso
            anota el contacto, para ver en "Sesiones de dispositivos" qué
            móviles están en línea."""
            token = _token_peticion()
            u = usuarios.usuario_por_token(token)
            if u is not None:
                usuarios.registrar_contacto(token)
            return u

        def requiere_token(func):
            from functools import wraps

            @wraps(func)
            def envoltorio(*args, **kwargs):
                u = _usuario_peticion()
                if u is None:
                    return jsonify({
                        "status": "error",
                        "error": "token_invalido",
                        "message": "Sesión no válida. Vuelve a iniciar sesión."
                    }), 401
                g.usuario_mantpro = u
                return func(*args, **kwargs)
            return envoltorio

        self._usuario_peticion = _usuario_peticion

        # --- API DE TRABAJOS (app MantPro) ----------------------------------
        # Lectura: cualquier usuario autenticado. Alta/edición/completar/borrar
        # trabajos y avisos: solo admin o rol "técnico" (usuarios.puede_hacer_trabajos).
        def requiere_tecnico(func):
            from functools import wraps

            @wraps(func)
            def envoltorio(*args, **kwargs):
                if not usuarios.puede_hacer_trabajos(g.usuario_mantpro):
                    return jsonify({
                        "status": "error", "error": "sin_permiso",
                        "message": "Tu usuario no puede gestionar trabajos."
                    }), 403
                return func(*args, **kwargs)
            return envoltorio

        @self.app.route('/api/login', methods=['POST'])
        def api_login():
            datos = request.get_json(silent=True) or request.form
            login_usuario = (datos.get('login') or '').strip()
            password = datos.get('password') or ''
            dispositivo = (datos.get('dispositivo') or '')[:120]
            if not login_usuario or not password:
                return jsonify({"status": "error", "message": "Faltan datos"}), 400
            usuario = usuarios.autenticar(login_usuario, password)
            if usuario is None:
                return jsonify({"status": "error", "error": "credenciales",
                                "message": "Usuario o contraseña incorrectos."}), 401
            token = usuarios.crear_token(usuario['id'], dispositivo)
            return jsonify({"status": "ok", "token": token, "usuario": {
                "id": usuario['id'], "login": usuario['login'],
                "nombre": usuario['nombre'], "rol": usuario['rol'],
                "roles": usuario['roles']}})

        @self.app.route('/api/logout', methods=['POST'])
        @requiere_token
        def api_logout():
            usuarios.revocar_token(_token_peticion())
            return jsonify({"status": "ok"})

        @self.app.route('/api/yo', methods=['GET'])
        @requiere_token
        def api_yo():
            return jsonify({"status": "ok", "usuario": g.usuario_mantpro})

        @self.app.route('/api/desconectar', methods=['POST'])
        @requiere_token
        def api_desconectar():
            # La app se cierra o pasa a segundo plano: en "Sesiones de
            # dispositivos" sale "Sin conexión" al momento.
            usuarios.registrar_desconexion(_token_peticion())
            return jsonify({"status": "ok"})

        @self.app.route('/api/ping', methods=['GET'])
        def api_ping():
            # Sin token: sirve para comprobar conectividad y si el PC ya pide login
            return jsonify({"status": "ok", "auth": True, "version_api": 2})
        # -------------------------------------------------------------------

        # --- RUTAS EXISTENTES ---
        @self.app.route('/api/upload', methods=['POST'])
        @requiere_token
        def api_upload():
            try:
                usuario = g.usuario_mantpro
                titulo = request.form.get('titulo', 'Sin Título')
                detalles = request.form.get('detalles', '')
                tags = request.form.get('tags', 'General')

                # --- LEER FECHA DEL MÓVIL ---
                fecha_movil = request.form.get('fecha')
                if fecha_movil:
                    fecha_final = fecha_movil
                else:
                    fecha_final = datetime.now().strftime("%Y-%m-%d")
                # -----------------------------

                filename, ruta_local = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')
                raw_desc = ruta_local if ruta_local else detalles

                # --- Máquina vinculada (opcional, enviada por la app móvil) ---
                maquina_id_raw = request.form.get('maquina_id')
                try:
                    maquina_id = int(maquina_id_raw) if maquina_id_raw else None
                except (TypeError, ValueError):
                    maquina_id = None

                # --- FIX: CREAR LA DESCRIPCIÓN COMPLETA CON TÍTULO Y FOTO ---
                desc_final = titulo
                if detalles:
                    desc_final += f"\n{detalles}"
                if filename:
                    desc_final += f"\n[FOTO: {filename}]"
                if filename_d:
                    desc_final += f"\n[FOTO_DESPUES: {filename_d}]"
                # Colección de fotos extra: las que ya traían los detalles (marca
                # [FOTOS:], p. ej. de un pendiente que venía de revertir un
                # trabajo) más las nuevas recibidas como ficheros.
                desc_final = con_fotos_galeria(desc_final, fotos_galeria(desc_final) + self._procesar_galeria(request))

                # Usamos el bloque with para asegurar el guardado
                with get_db_connection(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO tareas (fecha, descripcion, tags, raw_desc, foto, usuario_id, usuario_nombre, maquina_id) VALUES (?,?,?,?,?,?,?,?)',
                                   (fecha_final, desc_final, tags, raw_desc, filename,
                                    usuario['id'], usuario['nombre'], maquina_id))
                    conn.commit()

                self._descontar_materiales_trabajo(request, usuario, titulo)

                # Emitimos la señal pasando el título correcto para la notificación
                self.registro_recibido.emit(titulo, detalles, tags, raw_desc if raw_desc else "", filename if filename else "")
                return jsonify({"status": "ok"})
            except Exception as e:
                print(f"Error api_upload: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/maquinas', methods=['GET'])
        @requiere_token
        def api_maquinas():
            try:
                return jsonify(maquinas.listar_maquinas())
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/repuestos', methods=['GET'])
        @requiere_token
        def api_repuestos():
            """Repuestos de todas las máquinas (vínculo máquina ↔ artículo con la
            cantidad que lleva), con los datos del artículo y el nombre completo
            de la máquina, para que los móviles los guarden y los consulten sin
            conexión: MantPro en la ficha de la máquina y MantPro Stock en el
            artículo («Se usa en…»)."""
            try:
                rutas = maquinas.mapa_rutas_completas()
                materiales = {m["id"]: m for m in almacen.listar_materiales()}
                ubicaciones = {}
                resultado = []
                for r in almacen.listar_repuestos():
                    m = materiales.get(r["material_id"])
                    if m is None or r["maquina_id"] not in rutas:
                        continue
                    if m["seccion_id"] not in ubicaciones:
                        ubicaciones[m["seccion_id"]] = almacen.obtener_ubicacion_texto(m["seccion_id"])
                    resultado.append({**r, "maquina": rutas[r["maquina_id"]], "codigo": m.get("codigo") or "",
                                      "nombre": m["nombre"], "unidad": m.get("unidad") or "",
                                      "stock_actual": m["stock_actual"], "stock_minimo": m["stock_minimo"],
                                      "ubicacion": ubicaciones[m["seccion_id"]]})
                return jsonify({"status": "ok", "repuestos": resultado})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/pendientes', methods=['GET'])
        @requiere_token
        def api_get_pendientes():
            try:
                conn = self._conn()
                c = conn.cursor()
                u = g.usuario_mantpro
                solo_mios = request.args.get('solo_mios', '') in ('1', 'true', 'True')
                columnas = ("SELECT id, titulo, detalles, asignado_a, COALESCE(asignado_nombre,''), "
                            "COALESCE(prioridad,'Media'), especialidad_id FROM pendientes")
                if solo_mios:
                    c.execute(columnas + " WHERE asignado_a = ? ORDER BY id DESC", (u['id'],))
                elif usuarios.es_admin(u):
                    c.execute(columnas + " ORDER BY id DESC")
                else:
                    # Igual que en los avisos: cada técnico ve los suyos más los
                    # que no están asignados a nadie y coinciden con alguna de
                    # sus especialidades (o no tienen ninguna); no ve los
                    # asignados a otro técnico ni los restringidos a una
                    # especialidad que no tiene.
                    especialidades_u = u.get('especialidad_ids') or []
                    interrogantes = ", ".join("?" * len(especialidades_u))
                    condicion_especialidad = (
                        f"especialidad_id IS NULL OR especialidad_id IN ({interrogantes})"
                        if especialidades_u else "especialidad_id IS NULL")
                    c.execute(columnas + " WHERE asignado_a = ? OR (asignado_a IS NULL AND "
                              f"({condicion_especialidad})) ORDER BY id DESC",
                              (u['id'], *especialidades_u))
                filas = c.fetchall()
                conn.close()
                especialidades_por_id = {e['id']: e['nombre'] for e in usuarios.listar_especialidades()}
                datos = [{"id": r[0], "titulo": r[1], "detalles": r[2],
                          "asignado_a": r[3], "asignado": r[4], "prioridad": r[5],
                          "especialidad_id": r[6], "especialidad": especialidades_por_id.get(r[6])} for r in filas]
                return jsonify(datos)
            except Exception as e: return jsonify({"error": str(e)}), 500

        @self.app.route('/api/especialidades', methods=['GET'])
        @requiere_token
        def api_get_especialidades():
            try:
                return jsonify(usuarios.listar_especialidades())
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/completar_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_completar_pendiente():
            try:
                usuario = g.usuario_mantpro
                id_pend = request.form.get('id')
                titulo = request.form.get('titulo') or "Sin Título"
                detalles = request.form.get('detalles', '')
                tags = request.form.get('tags', '')

                # --- LEER FECHA DEL MÓVIL ---
                fecha_movil = request.form.get('fecha')
                fecha_final = fecha_movil if fecha_movil else datetime.now().strftime("%Y-%m-%d")
                # ----------------------------

                # Reintento de un envío que ya se procesó (la respuesta no le llegó
                # al móvil, o dos sincronizaciones mandaron la misma cola a la vez):
                # si el pendiente ya no existe pero este mismo trabajo ya está en el
                # historial, respondemos OK sin duplicar nada. Si devolviéramos 404,
                # el móvil lo dejaría para siempre como "listo para sincronizar".
                desc_sin_fotos = con_fotos_galeria(titulo + (f"\n{detalles}" if detalles else ""), [])
                with get_db_connection(self.db_path) as conn:
                    c = conn.cursor()
                    c.execute('SELECT 1 FROM pendientes WHERE id=?', (id_pend,))
                    if c.fetchone() is None:
                        c.execute('SELECT descripcion FROM tareas WHERE fecha=? AND usuario_id=?',
                                  (fecha_final, usuario['id']))
                        if any(d == desc_sin_fotos or (d or "").startswith(desc_sin_fotos + "\n[FOTO")
                               for (d,) in c.fetchall()):
                            return jsonify({"status": "ok", "ya_completado": True})

                filename, ruta_local = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')
                raw_desc = ruta_local if ruta_local else detalles

                # --- FIX: CREAR LA DESCRIPCIÓN COMPLETA CON TÍTULO Y FOTO ---
                desc_final = titulo
                if detalles:
                    desc_final += f"\n{detalles}"
                if filename:
                    desc_final += f"\n[FOTO: {filename}]"
                if filename_d:
                    desc_final += f"\n[FOTO_DESPUES: {filename_d}]"
                # Colección de fotos extra: las que ya traían los detalles (marca
                # [FOTOS:], p. ej. de un pendiente que venía de revertir un
                # trabajo) más las nuevas recibidas como ficheros.
                desc_final = con_fotos_galeria(desc_final, fotos_galeria(desc_final) + self._procesar_galeria(request))

                with get_db_connection(self.db_path) as conn:
                    c = conn.cursor()
                    c.execute('DELETE FROM pendientes WHERE id=?', (id_pend,))
                    if c.rowcount == 0:
                        # El pendiente no existe (id inválido, ya completado o aún no
                        # sincronizado desde el móvil): no creamos nada en el historial
                        # para no duplicar el trabajo.
                        return jsonify({"status": "error", "message": "El pendiente ya no existe."}), 404
                    # Usamos el INSERT completo para alimentar todas las columnas
                    c.execute('INSERT INTO tareas (fecha, descripcion, tags, raw_desc, foto, usuario_id, usuario_nombre) VALUES (?,?,?,?,?,?,?)',
                              (fecha_final, desc_final, tags, raw_desc, filename,
                               usuario['id'], usuario['nombre']))
                    conn.commit()

                self._descontar_materiales_trabajo(request, usuario, titulo)

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                print(f"Error completar_pendiente: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/agregar_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_agregar_pendiente():
            print(">>> PETICIÓN: AGREGAR PENDIENTE")
            try:
                titulo = request.form.get('titulo')
                detalles = request.form.get('detalles')
                prioridad = request.form.get('prioridad') or 'Media'
                especialidad_id = request.form.get('especialidad_id') or None
                if especialidad_id is not None:
                    especialidad_id = int(especialidad_id)
                filename, ruta_foto = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')
                if filename: detalles += f"\n[FOTO: {filename}]"
                if filename_d: detalles += f"\n[FOTO_DESPUES: {filename_d}]"
                detalles = con_fotos_galeria(detalles, fotos_galeria(detalles) + self._procesar_galeria(request))

                conn = self._conn()
                c = conn.cursor()
                # Un pendiente creado desde el móvil queda asignado a quien lo crea
                usuario = g.usuario_mantpro
                c.execute('INSERT INTO pendientes (titulo, detalles, asignado_a, asignado_nombre, prioridad, especialidad_id) VALUES (?,?,?,?,?,?)',
                          (titulo, detalles, usuario['id'], usuario['nombre'], prioridad, especialidad_id))
                conn.commit()
                conn.close()

                print("✅ Pendiente guardado OK")
                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                print(f"!!! ERROR AGREGAR PENDIENTE: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/editar_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_editar_pendiente():
            try:
                id_p = request.form.get('id')
                titulo = request.form.get('titulo')
                detalles = request.form.get('detalles')
                prioridad = request.form.get('prioridad')

                # Gestión de foto nueva si la hubiera
                filename, ruta = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')
                if filename:
                    detalles += f"\n[FOTO: {filename}]"
                if filename_d:
                    detalles += f"\n[FOTO_DESPUES: {filename_d}]"
                # Colección: las que ya tenía (vienen en los detalles) + las nuevas
                detalles = con_fotos_galeria(detalles, fotos_galeria(detalles) + self._procesar_galeria(request))

                conn = self._conn()
                c = conn.cursor()
                # Actualizamos título y detalles (y prioridad si el móvil la ha enviado)
                if prioridad:
                    c.execute('UPDATE pendientes SET titulo=?, detalles=?, prioridad=? WHERE id=?', (titulo, detalles, prioridad, id_p))
                else:
                    c.execute('UPDATE pendientes SET titulo=?, detalles=? WHERE id=?', (titulo, detalles, id_p))
                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/eliminar_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_eliminar_pendiente():
            # (Mantener código original)
            try:
                id_p = request.form.get('id')
                conn = self._conn()
                c = conn.cursor()
                c.execute('DELETE FROM pendientes WHERE id=?', (id_p,))
                conn.commit()
                conn.close()
                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        # ==========================================
        # --- NUEVAS RUTAS PARA EL MÓVIL ---
        # ==========================================

        @self.app.route('/api/dashboard', methods=['GET'])
        @requiere_token
        def api_dashboard():
            try:
                conn = self._conn()
                c = conn.cursor()
                # 1. Contar pendientes
                c.execute("SELECT COUNT(*) FROM pendientes")
                n_pendientes = c.fetchone()[0]

                # 2. Contar registros del mes actual
                mes_actual = datetime.now().strftime("%Y-%m")
                c.execute("SELECT COUNT(*) FROM tareas WHERE fecha LIKE ?", (f"{mes_actual}%",))
                n_mes = c.fetchone()[0]

                # 3. Contar avisos activos (lógica simplificada para SQL)
                c.execute("SELECT titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada FROM avisos_recurrentes")
                avisos = c.fetchall()
                n_avisos = 0
                hoy = datetime.now().date() # Usamos objeto date de Python para calcular rápido aquí

                # (Nota: Replicar lógica exacta de recurrencia en SQL puro es complejo,
                # enviamos el total de avisos configurados como dato simple o hacemos un cálculo aproximado)
                n_avisos_total = len(avisos)

                conn.close()
                return jsonify({
                    "pendientes": n_pendientes,
                    "registros_mes": n_mes,
                    "avisos_total": n_avisos_total
                })
            except Exception as e: return jsonify({"error": str(e)}), 500

        @self.app.route('/api/historial', methods=['GET'])
        @requiere_token
        def api_historial():
            try:
                query = request.args.get('q', '').lower()
                # Paginación: 'page' empieza en 0, 'limit' registros por página (por defecto 50)
                try:
                    page = max(0, int(request.args.get('page', 0)))
                except (TypeError, ValueError):
                    page = 0
                try:
                    limit = int(request.args.get('limit', 50))
                except (TypeError, ValueError):
                    limit = 50
                limit = max(1, min(limit, 200))
                offset = page * limit

                conn = self._conn()
                c = conn.cursor()

                mes = request.args.get('mes', '')
                sql = "SELECT id, fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id FROM tareas WHERE 1=1"
                params = []

                if query:
                    sql += " AND (descripcion LIKE ? OR tags LIKE ?)"
                    p_query = f"%{query}%"
                    params.extend([p_query, p_query])

                if mes:
                    sql += " AND fecha LIKE ?"
                    params.append(f"{mes}%")

                sql += " ORDER BY fecha DESC, id DESC LIMIT ? OFFSET ?"
                params.extend([limit + 1, offset])

                c.execute(sql, params)
                filas = c.fetchall()
                hay_mas = len(filas) > limit
                filas = filas[:limit]
                nombres_maquinas = {m["id"]: m["nombre"] for m in maquinas.listar_maquinas()}
                # Procesamos para extraer nombre de foto si existe
                resultados = []
                for r in filas:
                    desc = r[2]
                    foto = None
                    m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
                    if m: foto = m.group(1).split("]")[0].strip()

                    foto_d = None
                    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc)
                    if m_d: foto_d = m_d.group(1).split("]")[0].strip()

                    # Limpieza visual para el móvil
                    desc_limpia = re.sub(r"\[FOTO.*?:.*?\]", "", desc)
                    desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                    maquina_id = r[5] if len(r) > 5 else None
                    resultados.append({
                        "id": r[0],
                        "fecha": r[1],
                        "descripcion": desc_limpia,
                        "tags": r[3],
                        "foto": foto,
                        "foto_d": foto_d,
                        "fotos": fotos_galeria(desc),
                        "raw_desc": desc, # Necesario para editar
                        "usuario": r[4] if len(r) > 4 else "",
                        "maquina_id": maquina_id,
                        "maquina_nombre": nombres_maquinas.get(maquina_id, "") if maquina_id else ""
                    })
                conn.close()
                return jsonify({"items": resultados, "has_more": hay_mas, "page": page})
            except Exception as e: return jsonify({"error": str(e)}), 500

        # ---------------------------------------------------------
        # 1. API AVISOS (Lógica corregida: Acepta retrasos)
        # ---------------------------------------------------------
        @self.app.route('/api/avisos', methods=['GET'])
        @requiere_token
        def api_avisos():
            try:
                conn = self._conn()
                c = conn.cursor()
                u = g.usuario_mantpro
                # Cada trabajador ve sus avisos asignados más los que todavía
                # no están asignados a nadie y, de esos, solo los que no
                # tienen especialidad o coinciden con la suya. Los asignados
                # a otro técnico, o restringidos a otra especialidad, no se
                # le muestran. El admin los ve todos.
                if usuarios.es_admin(u):
                    c.execute("SELECT id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, "
                              "asignado_a, COALESCE(asignado_nombre,''), especialidad_id FROM avisos_recurrentes")
                    raw_avisos = c.fetchall()
                else:
                    especialidades_u = u.get('especialidad_ids') or []
                    interrogantes = ", ".join("?" * len(especialidades_u))
                    condicion_especialidad = (
                        f"especialidad_id IS NULL OR especialidad_id IN ({interrogantes})"
                        if especialidades_u else "especialidad_id IS NULL")
                    c.execute("SELECT id, titulo, fecha_inicio, frecuencia, duracion_dias, ultima_completada, "
                              "asignado_a, COALESCE(asignado_nombre,''), especialidad_id FROM avisos_recurrentes "
                              f"WHERE asignado_a = ? OR (asignado_a IS NULL AND ({condicion_especialidad}))",
                              (u['id'], *especialidades_u))
                    raw_avisos = c.fetchall()
                conn.close()

                lista_procesada = []
                hoy = datetime.now().date()

                for aid, tit, finicio, freq, dur, ult, asignado_a, asignado_nombre, especialidad_id in raw_avisos:
                    if not finicio: continue
                    try:
                        fi = datetime.strptime(finicio, "%Y-%m-%d").date()
                    except: continue

                    if not freq: freq = "Anual"
                    freq = idiomas.normalizar_frecuencia(freq)

                    # Un aviso "Diario" no necesita ventana: un margen de varios días
                    # daría un "rango" confuso para un recordatorio de todos los días.
                    dur_ventana = 0 if freq == "Diario" else dur

                    def _avanzar(fecha):
                        if freq == "Diario": return fecha + timedelta(days=1)
                        elif freq == "Semanal": return fecha + timedelta(days=7)
                        elif freq == "Mensual":
                            ny = fecha.year + (fecha.month // 12)
                            nm = (fecha.month % 12) + 1
                            try: return fecha.replace(year=ny, month=nm)
                            except: return fecha.replace(year=ny, month=nm, day=28)
                        elif freq == "Trimestral":
                             m_add = fecha.month + 3
                             ny = fecha.year + (m_add - 1) // 12
                             nm = (m_add - 1) % 12 + 1
                             try: return fecha.replace(year=ny, month=nm)
                             except: return fecha.replace(year=ny, month=nm, day=28)
                        elif freq == "Semestral":
                             m_add = fecha.month + 6
                             ny = fecha.year + (m_add - 1) // 12
                             nm = (m_add - 1) % 12 + 1
                             try: return fecha.replace(year=ny, month=nm)
                             except: return fecha.replace(year=ny, month=nm, day=28)
                        elif freq == "Anual": return fecha.replace(year=fecha.year + 1)
                        else: return fecha

                    # La fecha en que toca la próxima vez se cuenta desde la ÚLTIMA
                    # VEZ QUE SE HIZO DE VERDAD (ult), no desde el calendario fijo
                    # original. Así, si te retrasas, el aviso se queda en
                    # "Pendiente" (no salta al ciclo siguiente sin más) hasta que
                    # lo completas, y el siguiente se cuenta desde ese día real.
                    if ult:
                        try:
                            fecha_ult = datetime.strptime(ult, "%Y-%m-%d").date()
                            ocurrencia = _avanzar(fecha_ult)
                        except: ocurrencia = fi
                    else:
                        ocurrencia = fi

                    fin_ocurrencia = ocurrencia + timedelta(days=dur_ventana)

                    # Completado "para hoy" solo si se hizo justo hoy: ahora esa
                    # fecha decide cuándo toca el siguiente, no si el ciclo
                    # actual ya está hecho.
                    estado = "FUTURO"
                    color_code = "blue"
                    es_completado = (ult == hoy.strftime("%Y-%m-%d"))
                    es_activo = hoy >= ocurrencia
                    # Distinguimos "toca ahora" (dentro del margen configurado)
                    # de "se ha pasado ese margen sin hacerlo" (atrasado).
                    es_atrasado = hoy > fin_ocurrencia

                    if es_completado:
                        estado = "OK"
                        color_code = "green"
                    elif es_atrasado:
                        estado = "ATRASADO"
                        color_code = "red"
                    elif es_activo:
                        estado = "PENDIENTE"
                        color_code = "orange"
                    else:
                        estado = "FUTURO"
                        color_code = "blue"

                    lista_procesada.append({
                        "id": aid,
                        "titulo": tit,
                        "frecuencia": freq,
                        "rango": f"{ocurrencia.strftime(idiomas.formato_fecha_corta_py())} - {fin_ocurrencia.strftime(idiomas.formato_fecha_corta_py())}",
                        "estado": estado,
                        "color": color_code,
                        "raw_inicio": ocurrencia.strftime("%Y-%m-%d"),
                        "raw_fin": fin_ocurrencia.strftime("%Y-%m-%d"),
                        # Datos "crudos" del aviso (fecha de inicio original, duración y última
                        # completada) para que el móvil pueda recalcular el ciclo por su cuenta
                        # con la fecha del propio teléfono, aunque lleve meses sin sincronizar.
                        "fecha_inicio_raw": finicio,
                        "duracion_dias": dur,
                        "ultima_completada": ult or "",
                        "asignado_a": asignado_a,
                        "asignado": asignado_nombre or ""
                    })

                return jsonify(lista_procesada)
            except Exception as e: return jsonify({"error": str(e)}), 500

        # ---------------------------------------------------------
        # 2. API COMPLETAR (Anti-Duplicados)
        # ---------------------------------------------------------
        @self.app.route('/api/completar_aviso', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_completar_aviso():
            print("\n" + "="*40)
            print(">>> RECIBIDA PETICIÓN: COMPLETAR AVISO")

            try:
                # 1. IMPRIMIR QUÉ NOS LLEGA EXACTAMENTE
                print(f"Datos recibidos (RAW): {request.form}")

                id_aviso_str = request.form.get('id')
                titulo = request.form.get('titulo') or "Sin Título"
                fecha_custom = request.form.get('fecha_custom')

                # 2. VALIDACIÓN DE ID
                if not id_aviso_str:
                    print("!!! ERROR: No ha llegado el ID")
                    return jsonify({"status": "error", "message": "Falta ID"}), 400

                try:
                    id_aviso = int(id_aviso_str)
                    print(f"ID convertido a entero: {id_aviso}")
                except ValueError:
                    print(f"!!! ERROR: El ID '{id_aviso_str}' no es un número")
                    return jsonify({"status": "error", "message": "ID no numérico"}), 400

                # 3. FECHA
                fecha_final = fecha_custom if fecha_custom else datetime.now().strftime("%Y-%m-%d")
                print(f"Fecha a guardar: {fecha_final}")

                # 4. CONEXIÓN BASE DE DATOS
                print("Intentando conectar a BD...")
                conn = self._conn()
                c = conn.cursor()

                # 5. ACTUALIZAR AVISO
                print("Ejecutando UPDATE en avisos_recurrentes...")
                c.execute('UPDATE avisos_recurrentes SET ultima_completada=? WHERE id=?', (fecha_final, id_aviso))
                if c.rowcount == 0:
                    print("⚠️ AVISO: No se actualizó ninguna fila. ¿Existe el ID?")
                else:
                    print("✅ UPDATE correcto.")

                # 6. INSERTAR HISTORIAL
                print("Verificando historial para evitar duplicados...")
                desc_historial = f"Mantenimiento Preventivo: {titulo}"
                tags_historial = "Preventivo, Aviso Recurrente"

                c.execute("SELECT id FROM tareas WHERE fecha=? AND descripcion=?", (fecha_final, desc_historial))
                existe = c.fetchone()

                if not existe:
                    print("Insertando nueva tarea en historial...")
                    usuario_aviso = g.usuario_mantpro
                    c.execute('INSERT INTO tareas (fecha, descripcion, tags, usuario_id, usuario_nombre) VALUES (?,?,?,?,?)',
                              (fecha_final, desc_historial, tags_historial,
                               usuario_aviso['id'], usuario_aviso['nombre']))
                else:
                    print("La tarea ya existe en el historial. Saltando insert.")

                conn.commit()
                conn.close()
                print("✅ BD CERRADA Y COMMIT REALIZADO")

                # 7. AVISAR INTERFAZ PC
                self.pendiente_actualizado.emit()

                print(">>> PROCESO TERMINADO CON ÉXITO")
                print("="*40 + "\n")
                return jsonify({"status": "ok"})

            except Exception as e:
                print("\n!!! EXCEPCIÓN CRÍTICA EN EL SERVIDOR !!!")
                print(f"Error: {str(e)}")
                import traceback
                traceback.print_exc()
                print("="*40 + "\n")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/foto/<path:filename>')
        def serve_foto(filename):
            try:
                return send_from_directory(self.carpeta_destino, filename)
            except Exception as e:
                return str(e), 404

        @self.app.route('/api/historial_todo', methods=['GET'])
        @requiere_token
        def api_historial_todo():
            # Versión ligera y SIN LIMIT, usada solo por la herramienta de "reenviar fotos"
            # del móvil para poder revisar TODO el histórico, no solo los últimos 50.
            try:
                conn = self._conn()
                c = conn.cursor()
                c.execute("SELECT id, descripcion FROM tareas ORDER BY fecha DESC, id DESC")
                resultados = []
                for id_t, desc in c.fetchall():
                    foto = None
                    m = re.search(r"\[FOTO:\s*(.*?)\]", desc)
                    if m: foto = m.group(1).split("]")[0].strip()
                    foto_d = None
                    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc)
                    if m_d: foto_d = m_d.group(1).split("]")[0].strip()
                    resultados.append({"id": id_t, "foto": foto, "foto_d": foto_d, "fotos": fotos_galeria(desc)})
                conn.close()
                return jsonify(resultados)
            except Exception as e: return jsonify({"error": str(e)}), 500

        @self.app.route('/api/editar_historial', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_editar_historial():
            try:
                id_t = request.form.get('id')
                desc_final = request.form.get('detalles') # Ya viene formateada desde el móvil (sin tags FOTO)
                tags = request.form.get('tags')

                conn = self._conn()
                c = conn.cursor()

                # Recuperamos la descripción actual para no perder fotos que no se reenvían en esta edición
                c.execute("SELECT descripcion FROM tareas WHERE id=?", (id_t,))
                row = c.fetchone()
                desc_actual = row[0] if row else ""

                m_actual = re.search(r"\[FOTO:\s*(.*?)\]", desc_actual)
                foto_actual = m_actual.group(1).strip() if m_actual else None
                m_actual_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", desc_actual)
                foto_actual_d = m_actual_d.group(1).strip() if m_actual_d else None

                # Si envían foto nueva, procesarla; si no, mantenemos la que ya había en BD
                filename, ruta = self._procesar_foto(request, 'foto')
                filename_d, _ = self._procesar_foto(request, 'foto_despues')

                foto_final = filename if filename else foto_actual
                foto_final_d = filename_d if filename_d else foto_actual_d

                if foto_final:
                    desc_final += f"\n[FOTO: {foto_final}]"
                if foto_final_d:
                    desc_final += f"\n[FOTO_DESPUES: {foto_final_d}]"

                # Colección: el móvil manda qué fotos ya existentes conserva (en
                # su orden) y las nuevas como ficheros. Una app antigua que no
                # mande la lista conserva todas las que ya había.
                galeria_actual = fotos_galeria(desc_actual)
                if 'fotos_extra_mantener' in request.form:
                    pedidas = [n.strip() for n in request.form.get('fotos_extra_mantener', '').split(',') if n.strip()]
                    mantener = [n for n in pedidas if n in galeria_actual]
                else:
                    mantener = galeria_actual
                desc_final = con_fotos_galeria(desc_final, mantener + self._procesar_galeria(request))

                if 'maquina_id' in request.form:
                    maquina_id_raw = request.form.get('maquina_id')
                    try:
                        maquina_id = int(maquina_id_raw) if maquina_id_raw else None
                    except (TypeError, ValueError):
                        maquina_id = None
                    c.execute("UPDATE tareas SET descripcion=?, tags=?, maquina_id=? WHERE id=?", (desc_final, tags, maquina_id, id_t))
                else:
                    c.execute("UPDATE tareas SET descripcion=?, tags=? WHERE id=?", (desc_final, tags, id_t))
                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit() # Para refrescar la UI de escritorio
                return jsonify({"status": "ok"})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/restaurar_foto', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_restaurar_foto():
            # Endpoint de reparación manual: sube una foto (antes o después) para un registro
            # existente SIN tocar el resto de la descripción ni la otra foto.
            try:
                id_t = request.form.get('id')
                tipo = request.form.get('tipo')  # 'antes', 'despues' o 'galeria'
                key = {'antes': 'foto', 'galeria': 'foto_galeria'}.get(tipo, 'foto_despues')

                filename, ruta = self._procesar_foto(request, key)
                if not filename:
                    return jsonify({"status": "error", "message": "No se recibió ningún archivo"}), 400

                conn = self._conn()
                c = conn.cursor()
                c.execute("SELECT descripcion FROM tareas WHERE id=?", (id_t,))
                row = c.fetchone()
                if not row:
                    conn.close()
                    return jsonify({"status": "error", "message": "Registro no encontrado"}), 404
                desc = row[0]

                if tipo == 'galeria':
                    # 'nombre' es el fichero que falta en el PC: se sustituye
                    # en la colección por el que se acaba de recibir.
                    original = (request.form.get('nombre') or '').strip()
                    galeria = fotos_galeria(desc)
                    galeria = [filename if n == original else n for n in galeria] if original in galeria else galeria + [filename]
                    desc = con_fotos_galeria(desc, galeria)
                elif tipo == 'antes':
                    if re.search(r"\[FOTO:\s*.*?\]", desc):
                        desc = re.sub(r"\[FOTO:\s*.*?\]", f"[FOTO: {filename}]", desc, count=1)
                    else:
                        desc += f"\n[FOTO: {filename}]"
                else:
                    if re.search(r"\[FOTO_DESPUES:\s*.*?\]", desc):
                        desc = re.sub(r"\[FOTO_DESPUES:\s*.*?\]", f"[FOTO_DESPUES: {filename}]", desc, count=1)
                    else:
                        desc += f"\n[FOTO_DESPUES: {filename}]"

                c.execute("UPDATE tareas SET descripcion=? WHERE id=?", (desc, id_t))
                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok", "filename": filename})
            except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/descompletar_aviso', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_descompletar_aviso():
            try:
                id_aviso = request.form.get('id')

                conn = self._conn()
                c = conn.cursor()

                # 1. Obtener datos actuales del aviso
                c.execute("SELECT titulo, ultima_completada FROM avisos_recurrentes WHERE id=?", (id_aviso,))
                row = c.fetchone()

                if row:
                    titulo, ult_fecha = row

                    # 2. Intentar borrar del historial la entrada generada para esa fecha
                    # La descripción debe coincidir con la que generamos automáticamente
                    desc = f"Mantenimiento Preventivo: {titulo}"
                    if ult_fecha:
                        c.execute("DELETE FROM tareas WHERE descripcion=? AND fecha=?", (desc, ult_fecha))

                    # 3. Buscar cuál es la NUEVA última fecha real (la anterior a la borrada)
                    # Esto evita que se quede en NULL si ya se había hecho el mes pasado
                    c.execute("SELECT MAX(fecha) FROM tareas WHERE descripcion=?", (desc,))
                    resultado = c.fetchone()
                    prev_fecha = resultado[0] if resultado else None # Puede ser None si nunca se hizo antes

                    # 4. Actualizar el aviso con la fecha histórica correcta
                    c.execute("UPDATE avisos_recurrentes SET ultima_completada=? WHERE id=?", (prev_fecha, id_aviso))

                conn.commit()
                conn.close()

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/revertir_pendiente', methods=['POST'])
        @requiere_token
        @requiere_tecnico
        def api_revertir_pendiente():
            # Deshace la finalización de un trabajo: lo saca del historial y lo
            # vuelve a poner en Pendientes. Mismo comportamiento que el PC.
            try:
                usuario = g.usuario_mantpro
                id_t = request.form.get('id')

                conn = self._conn()
                c = conn.cursor()
                c.execute("SELECT id, fecha, descripcion, tags, usuario_id, COALESCE(usuario_nombre,''), maquina_id FROM tareas WHERE id=?", (id_t,))
                d = c.fetchone()
                if not d:
                    conn.close()
                    return jsonify({"status": "error", "message": "Registro no encontrado"}), 404

                fecha_tarea, desc_tarea = d[1], d[2]
                uid_original = d[4] if len(d) > 4 else None
                unombre_original = d[5] if len(d) > 5 else ""

                if not usuarios.es_admin(usuario) and uid_original != usuario['id']:
                    conn.close()
                    return jsonify({"status": "error", "message": "Solo puedes modificar tus propios trabajos."}), 403

                # Si el trabajo venía de un aviso recurrente, lo "descompletamos" igual
                # que se hace al borrar un registro del historial.
                prefijo = "Mantenimiento Preventivo: "
                if desc_tarea.startswith(prefijo):
                    titulo_aviso = desc_tarea.replace(prefijo, "").strip()
                    try:
                        c.execute("SELECT id FROM avisos_recurrentes WHERE titulo=? AND ultima_completada=?", (titulo_aviso, fecha_tarea))
                        aviso = c.fetchone()
                        if aviso:
                            c.execute("UPDATE avisos_recurrentes SET ultima_completada=NULL WHERE id=?", (aviso[0],))
                            conn.commit()
                    except Exception as e:
                        print(f"Error intentando restaurar aviso: {e}")

                lineas = desc_tarea.split("\n")
                titulo = lineas[0].strip()
                detalles = "\n".join(lineas[1:]).strip()

                try:
                    c.execute('INSERT INTO pendientes (titulo,detalles,asignado_a,asignado_nombre) VALUES (?,?,?,?)',
                              (titulo, detalles, uid_original, unombre_original or None))
                    conn.commit()
                except Exception as e:
                    conn.close()
                    print(f"Error revirtiendo a pendiente: {e}")
                    return jsonify({"status": "error", "message": "No se ha podido revertir el trabajo a pendiente."}), 500

                detalle_auditoria = f"Registro del {fecha_tarea}: {titulo[:80]} (autor original: {unombre_original or usuarios.ETIQUETA_HISTORICO})"
                c.execute("DELETE FROM tareas WHERE id=?", (id_t,))
                conn.commit(); conn.close()
                usuarios.registrar_auditoria(usuario['id'], id_t, "revertir", detalle_auditoria)

                self.pendiente_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        # --- API DE STOCK (app MantPro Stock) ------------------------------
        # Lectura: cualquier usuario autenticado. Alta/edición/movimientos:
        # solo admin o rol "almacen" (usuarios.puede_gestionar_almacen).
        def requiere_almacen(func):
            from functools import wraps

            @wraps(func)
            def envoltorio(*args, **kwargs):
                if not usuarios.puede_gestionar_almacen(g.usuario_mantpro):
                    return jsonify({
                        "status": "error", "error": "sin_permiso",
                        "message": "Tu usuario no puede gestionar el almacén."
                    }), 403
                return func(*args, **kwargs)
            return envoltorio

        @self.app.route('/api/stock/estructura', methods=['GET'])
        @requiere_token
        def api_stock_estructura():
            return jsonify({"status": "ok", "estanterias": almacen.listar_estructura()})

        @self.app.route('/api/stock/zonas', methods=['GET'])
        @requiere_token
        def api_stock_zonas():
            return jsonify({"status": "ok", "zonas": almacen.listar_zonas()})

        @self.app.route('/api/stock/materiales', methods=['GET'])
        @requiere_token
        def api_stock_materiales():
            filtro = request.args.get('q') or None
            materiales = almacen.listar_materiales(filtro)
            for m in materiales:
                m["ubicacion"] = almacen.obtener_ubicacion_texto(m.get("seccion_id"))
            return jsonify({"status": "ok", "materiales": materiales})

        @self.app.route('/api/stock/bajo_minimo', methods=['GET'])
        @requiere_token
        def api_stock_bajo_minimo():
            materiales = almacen.materiales_bajo_minimo()
            for m in materiales:
                m["ubicacion"] = almacen.obtener_ubicacion_texto(m.get("seccion_id"))
            return jsonify({"status": "ok", "materiales": materiales})

        @self.app.route('/api/stock/material/<int:material_id>', methods=['GET'])
        @requiere_token
        def api_stock_material(material_id):
            material = almacen.obtener_material(material_id)
            if material is None:
                return jsonify({"status": "error", "message": "Material no encontrado"}), 404
            material["ubicacion"] = almacen.obtener_ubicacion_texto(material.get("seccion_id"))
            material["movimientos"] = almacen.obtener_movimientos(material_id, limite=20)
            return jsonify({"status": "ok", "material": material})

        @self.app.route('/api/stock/material', methods=['POST'])
        @requiere_token
        @requiere_almacen
        def api_stock_crear_material():
            try:
                usuario = g.usuario_mantpro
                datos = request.form
                nombre = (datos.get('nombre') or '').strip()
                if not nombre:
                    return jsonify({"status": "error", "message": "El nombre del material es obligatorio."}), 400
                seccion_id = datos.get('seccion_id')
                seccion_id = int(seccion_id) if seccion_id else None
                if seccion_id is None:
                    balda_id = datos.get('balda_id')
                    if balda_id:
                        seccion_id = almacen.seccion_para_balda(int(balda_id))
                filename, _ = self._procesar_foto(request, 'foto')
                material_id = almacen.crear_material(
                    datos.get('codigo', ''), nombre, datos.get('descripcion', ''),
                    datos.get('unidad', ''), float(datos.get('stock_minimo') or 0),
                    seccion_id, filename or None, float(datos.get('stock_inicial') or 0),
                    usuario['id'], usuario['nombre'])
                self.stock_actualizado.emit()
                return jsonify({"status": "ok", "id": material_id, "foto": filename or None})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/stock/material/<int:material_id>', methods=['POST'])
        @requiere_token
        @requiere_almacen
        def api_stock_editar_material(material_id):
            try:
                material = almacen.obtener_material(material_id)
                if material is None:
                    return jsonify({"status": "error", "message": "Material no encontrado"}), 404
                datos = request.form
                nombre = (datos.get('nombre') or '').strip()
                if not nombre:
                    return jsonify({"status": "error", "message": "El nombre del material es obligatorio."}), 400
                seccion_id = datos.get('seccion_id')
                seccion_id = int(seccion_id) if seccion_id else None
                if seccion_id is None:
                    balda_id = datos.get('balda_id')
                    if balda_id:
                        seccion_id = almacen.seccion_para_balda(int(balda_id))

                foto_final = material.get('foto')
                filename, _ = self._procesar_foto(request, 'foto')
                if filename:
                    foto_final = filename
                elif datos.get('borrar_foto') == '1':
                    foto_final = None

                usuario = g.usuario_mantpro
                almacen.actualizar_material(
                    material_id, datos.get('codigo', ''), nombre, datos.get('descripcion', ''),
                    datos.get('unidad', ''), float(datos.get('stock_minimo') or 0),
                    seccion_id, foto_final, usuario['id'], usuario['nombre'])
                self.stock_actualizado.emit()
                return jsonify({"status": "ok", "foto": foto_final})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/stock/material/<int:material_id>', methods=['DELETE'])
        @requiere_token
        @requiere_almacen
        def api_stock_borrar_material(material_id):
            try:
                material = almacen.obtener_material(material_id)
                if material is None:
                    return jsonify({"status": "error", "message": "Material no encontrado"}), 404
                almacen.borrar_material(material_id)
                self.stock_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route('/api/stock/material/<int:material_id>/movimiento', methods=['POST'])
        @requiere_token
        @requiere_almacen
        def api_stock_movimiento(material_id):
            try:
                usuario = g.usuario_mantpro
                datos = request.form
                tipo = datos.get('tipo')
                if tipo not in ('entrada', 'salida'):
                    return jsonify({"status": "error", "message": "Tipo de movimiento no válido."}), 400
                try:
                    cantidad = float(datos.get('cantidad') or 0)
                except ValueError:
                    cantidad = 0
                if cantidad <= 0:
                    return jsonify({"status": "error", "message": "La cantidad debe ser mayor que 0."}), 400
                ok, error = almacen.registrar_movimiento(
                    material_id, tipo, cantidad, usuario['id'], usuario['nombre'],
                    datos.get('motivo', ''))
                if not ok:
                    mensaje = ("No hay stock suficiente para esta salida."
                               if error == "stock_insuficiente" else "Material no encontrado")
                    return jsonify({"status": "error", "error": error, "message": mensaje}), 400
                self.stock_actualizado.emit()
                return jsonify({"status": "ok"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        # -------------------------------------------------------------------

    def _procesar_foto(self, req, key='foto'):
        if key in req.files:
            file = req.files[key]
            if file and file.filename != '':
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = re.sub(r'[^a-zA-Z0-9.]', '_', file.filename)
                filename = f"app_{timestamp}_{safe_name}"
                ruta = os.path.join(self.carpeta_destino, filename)
                file.save(ruta)
                return filename, ruta
        return "", ""

    def _procesar_galeria(self, req, key='fotos_extra'):
        """Guarda todas las fotos enviadas en el campo [key] (puede repetirse)
        y devuelve sus nombres de fichero en el orden recibido."""
        nombres = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for i, file in enumerate(req.files.getlist(key)):
            if not file or file.filename == '':
                continue
            safe_name = re.sub(r'[^a-zA-Z0-9.]', '_', file.filename)
            filename = f"app_{timestamp}_g{i}_{safe_name}"
            file.save(os.path.join(self.carpeta_destino, filename))
            nombres.append(filename)
        return nombres

    def _descontar_materiales_trabajo(self, req, usuario, referencia):
        """Lee el campo 'materiales' (JSON: [{"material_id":.., "cantidad":..}, ...])
        del formulario de un trabajo y descuenta cada cantidad del almacén. El
        material ya se ha usado en la realidad, así que el descuento se aplica
        aunque deje el stock en negativo: eso es lo que dispara el aviso de
        "bajo mínimo" en la app para que se verifique y se reponga."""
        materiales_raw = req.form.get('materiales')
        if not materiales_raw:
            return
        try:
            materiales = json.loads(materiales_raw)
        except (ValueError, TypeError):
            return
        hubo_algo = False
        for item in materiales:
            try:
                material_id = int(item.get('material_id'))
                cantidad = float(item.get('cantidad') or 0)
            except (TypeError, ValueError):
                continue
            if cantidad <= 0:
                continue
            ok, _ = almacen.registrar_movimiento(
                material_id, "salida", cantidad, usuario['id'], usuario['nombre'],
                motivo=f"{almacen.PREFIJO_MOTIVO_USADO_EN_TRABAJO}{referencia}", permitir_negativo=True)
            if ok:
                hubo_algo = True
        if hubo_algo:
            self.stock_actualizado.emit()

    def obtener_ip_local(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]; s.close()
            return ip
        except: return "127.0.0.1"

    def run(self):
        # Silencia el log de peticiones HTTP de Werkzeug (una línea por cada
        # sincronización del móvil): con la app ya probada no aporta nada y
        # solo llena la consola.
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        # Werkzeug llama a sys.exit() si no puede abrir el puerto: dentro de
        # este hilo eso acababa tumbando la ventana principal. Se captura y se
        # avisa a la interfaz por señal.
        try:
            self.app.run(host='0.0.0.0', port=self.server_port, debug=False, use_reloader=False)
        except BaseException as e:
            self.error_arranque.emit(str(e) or type(e).__name__)
