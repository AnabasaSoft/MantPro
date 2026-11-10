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

Paso 2 del roadmap (sección «Sincronización PC ↔ nube»). Lo usa nucleo/sincro_nube.py
(paso 4: subir los cambios a MantPro Cloud) y lo ejercita
herramientas/pruebas/prueba_sincronizacion.py.

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


def preparar_tabla(con, tabla, identidad=None, solo_si=None, uuid_desde=None, ignorar=()):
    """Añade `uuid` a [tabla] (rellenándolo en las filas que ya hay, sin anotar
    cambios) y (re)crea sus disparadores. Idempotente. Requiere que la tabla
    tenga rowid (todas las de MantPro: INTEGER PRIMARY KEY).

    Tablas «de clave» (config, dias_especiales), cuya identidad es su propia
    clave y no un uuid: se pasa [identidad], una expresión SQL con {r} en lugar
    de NEW/OLD (p. ej. "{r}.clave"), que es lo que se anota en `cambios.uuid`.
    No se añade columna. [solo_si] (misma sintaxis) limita qué filas se anotan.

    [uuid_desde]: nombre de una columna que ya identifica cada registro (el `uid` que
    generan los móviles); se reutiliza como uuid si tiene valor, y si no se genera uno.

    [ignorar]: columnas locales de cada PC (p. ej. `ultimo_acceso`): modificar solo
    esas no anota ningún cambio."""
    t = _nombre(tabla)
    origen = _UUID_NUEVO
    if uuid_desde:
        origen = f"COALESCE(NULLIF({_nombre(uuid_desde)}, ''), {_UUID_NUEVO})"
    if identidad is not None:
        return _preparar_tabla_de_clave(con, t, identidad, solo_si)
    columnas = {f[1] for f in con.execute(f"PRAGMA table_info({t})")}
    if "uuid" not in columnas:
        con.execute(f"ALTER TABLE {t} ADD COLUMN uuid TEXT")
    # Los disparadores todavía no existen la primera vez, así que rellenar los
    # uuid de las filas antiguas no genera cambios. Al repetir no hay nada que rellenar.
    con.execute(f"UPDATE {t} SET uuid = {origen} WHERE uuid IS NULL")
    con.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{t}_uuid ON {t}(uuid)")

    for sufijo in ("ai", "au", "ad"):
        con.execute(f"DROP TRIGGER IF EXISTS sync_{t}_{sufijo}")
    # Alta: asigna el uuid si no lo trae (los cambios de la nube sí lo traen) y anota 'i'.
    con.execute(f"""
        CREATE TRIGGER sync_{t}_ai AFTER INSERT ON {t}
        BEGIN
            UPDATE {t} SET uuid = {origen} WHERE rowid = NEW.rowid AND uuid IS NULL;
            INSERT INTO cambios (tabla, uuid, op)
                SELECT '{t}', uuid, 'i' FROM {t}
                WHERE rowid = NEW.rowid AND {_NO_SILENCIADO};
        END
    """)
    # Modificación: no anota el cambio de uuid en sí (la asignación del alta) ni
    # los de las columnas ignoradas (solo se anota si cambia alguna otra).
    columnas = [f[1] for f in con.execute(f"PRAGMA table_info({t})")]
    distintas = " OR ".join(f"OLD.{c} IS NOT NEW.{c}" for c in columnas
                            if c != "uuid" and c not in ignorar)
    cond_cambio = f" AND ({distintas})" if ignorar and distintas else ""
    con.execute(f"""
        CREATE TRIGGER sync_{t}_au AFTER UPDATE ON {t}
        WHEN OLD.uuid IS NEW.uuid AND {_NO_SILENCIADO}{cond_cambio}
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


def _preparar_tabla_de_clave(con, t, identidad, solo_si):
    nuevo, viejo = identidad.format(r="NEW"), identidad.format(r="OLD")
    cond_n = f" AND {solo_si.format(r='NEW')}" if solo_si else ""
    cond_v = f" AND {solo_si.format(r='OLD')}" if solo_si else ""
    for sufijo in ("ai", "au", "ad"):
        con.execute(f"DROP TRIGGER IF EXISTS sync_{t}_{sufijo}")
    # INSERT OR REPLACE sobre una clave que ya existe llega como 'i' (SQLite no
    # dispara el borrado del REPLACE): para estas tablas 'i' y 'u' significan lo mismo.
    for sufijo, op, tipo, ref, cond in (("ai", "i", "INSERT", nuevo, cond_n),
                                        ("au", "u", "UPDATE", nuevo, cond_n),
                                        ("ad", "d", "DELETE", viejo, cond_v)):
        con.execute(f"""
            CREATE TRIGGER sync_{t}_{sufijo} AFTER {tipo} ON {t}
            WHEN {_NO_SILENCIADO}{cond}
            BEGIN
                INSERT INTO cambios (tabla, uuid, op) VALUES ('{t}', {ref}, '{op}');
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


def ultimo_n(con):
    """Último número de cambio que se ha dado en esta base (0 si nunca hubo ninguno).
    `cambios` usa AUTOINCREMENT: el número no baja aunque se purguen filas, así que
    si es MENOR que el último que se subió, esta base es una copia antigua restaurada."""
    f = con.execute("SELECT seq FROM sqlite_sequence WHERE name = 'cambios'").fetchone()
    return f[0] if f else 0


def purgar_subidos(con):
    """Borra de `cambios` lo que ya se subió (solo sirve de cola de salida). Devuelve cuántos."""
    n = con.execute("DELETE FROM cambios WHERE subido = 1").rowcount
    con.commit()
    return n


def vaciar_tablas(con, base):
    """Borra TODOS los registros sincronizables de [base] sin anotar cambios: es lo que hace falta
    para «adoptar» lo que hay en la nube. De `config` solo se borran los ajustes compartidos
    (idioma, puerto y demás son de este PC y se quedan). Devuelve cuántos registros se borraron."""
    existentes = {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    total = 0
    with silenciar(con):
        for tabla in reversed(list(TABLAS[base])):
            if tabla not in existentes:
                continue
            t, espec = _nombre(tabla), TABLAS[base][tabla]
            donde = f" WHERE {espec['solo_si'].format(r=t)}" if espec["tipo"] == "clave" and espec.get("solo_si") else ""
            total += con.execute(f"DELETE FROM {t}{donde}").rowcount
    con.commit()
    return total


def encolar_todo(con, base, solo=None):
    """Anota como alta ('i') TODOS los registros que ya hay en las tablas sincronizables
    de [base], para subirlos enteros (primera subida de un PC, o la que sigue a restaurar
    una copia). Lo que había pendiente en `cambios` pasa a «subido»: lo sustituye esto.
    Con [solo] (nombres de tabla sin prefijo) encola únicamente esas tablas —las que se han añadido a la
    sincronización en una versión nueva de MantPro— y NO toca lo que ya estaba pendiente.
    Requiere `preparar_base()` hecha antes (los registros ya tienen uuid).
    Devuelve cuántos registros se han encolado."""
    if solo is None:
        con.execute("UPDATE cambios SET subido = 1 WHERE subido = 0")
    existentes = {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    total = 0
    for tabla, espec in TABLAS[base].items():
        if tabla not in existentes or (solo is not None and tabla not in solo):
            continue
        t = _nombre(tabla)
        if espec["tipo"] == "clave":
            identidad = espec["identidad"].format(r=t)
            donde = f" WHERE {espec['solo_si'].format(r=t)}" if espec.get("solo_si") else ""
        else:
            identidad, donde = "uuid", " WHERE uuid IS NOT NULL"
        total += con.execute(
            f"INSERT INTO cambios (tabla, uuid, op) SELECT '{t}', {identidad}, 'i' FROM {t}{donde}").rowcount
    con.commit()
    return total


# ------------------------------------------------------------ qué se sincroniza
#
# MantPro tiene dos bases de datos: "mant" (mantenimiento.db) y "alma"
# (almacen.db). Las dos tienen una tabla `zonas` distinta, así que en el
# protocolo con la nube una tabla se nombra «base.tabla» (p. ej. "alma.zonas").
# `cambios.tabla` guarda el nombre sin prefijo: cada base tiene su `cambios`.
#
# tipo:
#   "entidad"   registro editable con identidad propia (uuid). Conflicto: gana el último cambio.
#   "inmutable" solo se crea (y se borra con su padre): historiales y libros de movimientos.
#               Nunca hay conflicto; se sincroniza el alta.
#   "enlace"    une dos registros (relación N:M) con una clave natural, que es la que
#               hay que respetar al combinar (el mismo enlace creado en dos PCs tendrá
#               dos uuid pero es el mismo enlace).
#   "clave"     identidad = su clave (no hay uuid). Solo se anota lo de [solo_si].
# refs: columna -> "base.tabla" a la que apunta (id entero local). Muchas no son claves
#   ajenas declaradas: al sincronizar hay que traducirlas por uuid. OJO: se han deducido
#   de los nombres y del código; revisar antes de usarlas en la sincronización real.
# derivadas: columnas que se recalculan en destino y no se sincronizan como valor.
# ignorar: columnas locales de cada PC: nunca viajan y cambiarlas no anota nada.
# silenciosas: columnas que SÍ viajan (se mandan con el registro) pero cambiarlas solo no anota
#   nada, para no inundar la nube (p. ej. la caducidad de una sesión, que se renueva cada minuto).
# relleno: columnas locales obligatorias que no viajan y hay que inventar al CREAR el registro en
#   otro PC; la plantilla usa los datos que llegan (p. ej. token «~{huella}» para una sesión).
# uuid_desde: columna cuyo valor sirve de identidad (así el mismo móvil o la misma sesión tienen el
#   mismo uuid en todos los PCs sin que se dupliquen).

# Ajustes compartidos por toda la empresa (los demás de `config` son de cada PC:
# idioma, puerto_servidor, dias_sesion, http_desactivado, ultimo_usuario…).
CONFIG_COMPARTIDA = ("coste_hora", "moneda", "factor_objetivo",
                     "country_iso", "region_iso", "parent_iso")

TABLAS = {
    "mant": {
        "usuarios": {"tipo": "entidad", "ignorar": ("ultimo_acceso",), "refs": {"especialidad_id": "mant.especialidades"}},
        "especialidades": {"tipo": "entidad", "refs": {}},
        "usuario_roles": {"tipo": "enlace", "clave_natural": ("usuario_id", "rol"),
                          "refs": {"usuario_id": "mant.usuarios"}},
        "usuario_especialidades": {"tipo": "enlace", "clave_natural": ("usuario_id", "especialidad_id"),
                                   "refs": {"usuario_id": "mant.usuarios", "especialidad_id": "mant.especialidades"}},
        # Sesiones de los móviles: viajan con la HUELLA del token (SHA-256), NUNCA con el token (una credencial).
        # El móvil presenta su token en cualquier PC y se reconoce por la huella (usuarios.usuario_por_token).
        "sesiones": {"tipo": "entidad", "uuid_desde": "huella", "ignorar": ("token", "ultimo_contacto", "cifrada"),
                     "silenciosas": ("expira",), "relleno": {"token": "~{huella}"},
                     "refs": {"usuario_id": "mant.usuarios"}},
        # Los móviles conocidos y a qué técnico están adjudicados: valen para toda la empresa.
        "moviles": {"tipo": "entidad", "uuid_desde": "dispositivo_id", "silenciosas": ("visto",),
                    "refs": {"usuario_id": "mant.usuarios"}},
        "zonas": {"tipo": "entidad", "refs": {}},
        "maquinas": {"tipo": "entidad", "refs": {"padre_id": "mant.maquinas", "zona_id": "mant.zonas"}},
        "tareas": {"tipo": "entidad", "refs": {"usuario_id": "mant.usuarios", "maquina_id": "mant.maquinas"}},
        "pendientes": {"tipo": "entidad", "refs": {"asignado_a": "mant.usuarios", "especialidad_id": "mant.especialidades",
                                                   "checklist_id": "mant.checklist_plantillas"}},
        "avisos_recurrentes": {"tipo": "entidad", "refs": {"asignado_a": "mant.usuarios", "especialidad_id": "mant.especialidades",
                                                           "checklist_id": "mant.checklist_plantillas", "contador_id": "mant.contadores"}},
        "checklist_plantillas": {"tipo": "entidad", "refs": {}},
        "checklist_puntos": {"tipo": "entidad", "refs": {"plantilla_id": "mant.checklist_plantillas"}},
        "checklist_resultados": {"tipo": "entidad", "refs": {"tarea_id": "mant.tareas"}},
        "contadores": {"tipo": "entidad", "refs": {"maquina_id": "mant.maquinas"}},
        "lecturas_contador": {"tipo": "inmutable", "uuid_desde": "uid", "refs": {"contador_id": "mant.contadores", "usuario_id": "mant.usuarios",
                                                            "aviso_id": "mant.avisos_recurrentes", "tarea_id": "mant.tareas"}},
        "auditoria": {"tipo": "inmutable", "refs": {"usuario_id": "mant.usuarios", "tarea_id": "mant.tareas"}},
        "config": {"tipo": "clave", "identidad": "{r}.clave",
                   "solo_si": "{r}.clave IN (" + ", ".join(f"'{k}'" for k in CONFIG_COMPARTIDA) + ")", "refs": {}},
        "dias_especiales": {"tipo": "clave", "identidad": "{r}.fecha", "refs": {}},
    },
    "alma": {
        "zonas": {"tipo": "entidad", "refs": {}},
        "estanterias": {"tipo": "entidad", "refs": {"zona_id": "alma.zonas"}},
        "baldas": {"tipo": "entidad", "refs": {"estanteria_id": "alma.estanterias"}},
        "secciones": {"tipo": "entidad", "refs": {"balda_id": "alma.baldas"}},
        "proveedores": {"tipo": "entidad", "refs": {}},
        "materiales": {"tipo": "entidad", "derivadas": ("stock_actual",),
                       "refs": {"seccion_id": "alma.secciones", "proveedor_id": "alma.proveedores"}},
        "movimientos": {"tipo": "inmutable", "refs": {"material_id": "alma.materiales", "usuario_id": "mant.usuarios"}},
        "maquina_repuestos": {"tipo": "enlace", "clave_natural": ("maquina_id", "material_id"),
                              "refs": {"maquina_id": "mant.maquinas", "material_id": "alma.materiales"}},
        "precios_proveedor": {"tipo": "inmutable", "refs": {"material_id": "alma.materiales", "proveedor_id": "alma.proveedores"}},
        "pedidos": {"tipo": "entidad", "refs": {"proveedor_id": "alma.proveedores"}},
        "pedidos_lineas": {"tipo": "entidad", "refs": {"pedido_id": "alma.pedidos", "material_id": "alma.materiales"}},
        "revisiones_stock": {"tipo": "entidad", "uuid_desde": "uid", "refs": {"usuario_id": "mant.usuarios"}},
        "revisiones_stock_lineas": {"tipo": "entidad", "refs": {"revision_id": "alma.revisiones_stock",
                                                                "material_id": "alma.materiales"}},
        "trabajo_materiales": {"tipo": "entidad", "refs": {"tarea_id": "mant.tareas", "material_id": "alma.materiales"}},
    },
}

# Tablas que NO se sincronizan, con el motivo. La prueba exige que toda tabla
# real esté en TABLAS o aquí: una tabla nueva obliga a decidir.
TABLAS_LOCALES = {
    "mant": {
        "cambios": "el propio registro de cambios",
        "sync_estado": "interruptor local de la sincronización",
    },
    "alma": {
        "cambios": "el propio registro de cambios",
        "sync_estado": "interruptor local de la sincronización",
    },
}


def tablas_sincronizables(base):
    """Nombres de las tablas de [base] ("mant" o "alma") que se sincronizan."""
    return list(TABLAS[base])


def preparar_base(con, base):
    """Prepara el registro de cambios y todas las tablas sincronizables de
    [base] en la conexión [con] (que debe ser de esa base). Idempotente: hay que
    llamarla tras cada migración que recree una tabla (los triggers se pierden
    con DROP TABLE). Devuelve la lista de tablas que todavía no existen en la
    base (se prepararán cuando se creen)."""
    preparar_registro_cambios(con)
    existentes = {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    faltan = []
    for tabla, espec in TABLAS[base].items():
        if tabla not in existentes:
            faltan.append(tabla)
        elif espec["tipo"] == "clave":
            preparar_tabla(con, tabla, identidad=espec["identidad"], solo_si=espec.get("solo_si"))
        else:
            preparar_tabla(con, tabla, uuid_desde=espec.get("uuid_desde"),
                           ignorar=tuple(espec.get("ignorar", ())) + tuple(espec.get("silenciosas", ())))
    return faltan
