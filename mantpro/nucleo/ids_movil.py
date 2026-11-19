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
ids_movil.py — Los ids que manda el móvil, traducidos con el uuid.

El problema: el id de cada registro es de cada base de datos. El de una máquina
en el PC no es el de la misma máquina en MantPro Cloud (ni en otro PC). El móvil
guarda sus listas con los ids de la ruta que tenía activa al bajarlas (el PC por
la WiFi o la nube por internet) y puede mandar los cambios por la otra: un
trabajo apuntado sin conexión con la lista del PC y enviado a la nube acabaría
en OTRA máquina.

La solución: el móvil manda, junto a cada id, el uuid del registro (el mismo en
todas partes, ver nucleo/sincronizacion.py). Antes de que la petición llegue a la
ruta, `traducir()` cambia cada id por el local del registro con ese uuid:

- el `id` del formulario, si viene `uuid` (la tabla depende de la ruta: RUTAS);
- cada `<campo>`, si viene `<campo>_uuid` (la tabla depende del campo: CAMPOS);
- en el JSON `materiales`, el `material_id` de cada línea con `material_uuid` (o `material_id_uuid`,
  como llega en las listas que baja el móvil: un trabajo del historial que se edita los reenvía así).

Si el uuid no existe aquí (el registro se borró, o aún no ha llegado) NO se usa el
id que mandó el móvil, que podría ser el de otro registro: el `id` pasa a uno que
no existe (la ruta responde como con algo ya borrado) y los demás campos se vacían
(un trabajo sin máquina es mejor que en la máquina equivocada). Sin uuid (apps
antiguas, o PC sin MantPro Cloud, cuyas tablas no tienen uuid) todo sigue igual.

Python puro, sin Qt (lo usan el PC y el trabajador de móviles de la nube).
"""

import json

# Ruta del móvil -> tabla de su campo `id`
RUTAS = {
    "/api/completar_pendiente": ("mant", "pendientes"),
    "/api/editar_pendiente": ("mant", "pendientes"),
    "/api/eliminar_pendiente": ("mant", "pendientes"),
    "/api/completar_aviso": ("mant", "avisos_recurrentes"),
    "/api/descompletar_aviso": ("mant", "avisos_recurrentes"),
    "/api/editar_historial": ("mant", "tareas"),
    "/api/revertir_pendiente": ("mant", "tareas"),
    "/api/restaurar_foto": ("mant", "tareas"),
}
# Campo del formulario -> tabla a la que apunta
CAMPOS = {
    "maquina_id": ("mant", "maquinas"),
    "sede_id": ("mant", "sedes"),
    "especialidad_id": ("mant", "especialidades"),
    "asignado_a": ("mant", "usuarios"),
    "material_id": ("alma", "materiales"),
    "contador_id": ("mant", "contadores"),
    "almacen_id": ("alma", "almacenes"),
    "seccion_id": ("alma", "secciones"),
    "balda_id": ("alma", "baldas"),
    "estanteria_id": ("alma", "estanterias"),
}
# Rutas con el id en la dirección (regla de Flask -> argumento y tabla). El uuid llega en el
# formulario o en la consulta (?uuid=, en un DELETE).
EN_RUTA = {
    "/api/stock/material/<int:material_id>": ("material_id", "alma", "materiales"),
    "/api/stock/material/<int:material_id>/movimiento": ("material_id", "alma", "materiales"),
}
# Cuerpos JSON: la revisión del almacén (almacen_id y cada línea con su material_id)
JSON_RUTAS = {"/api/stock/revision"}
ID_INEXISTENTE = "-1"


def _tiene_uuid(con, tabla):
    return "uuid" in {f[1] for f in con.execute(f"PRAGMA table_info({tabla})")}


class Traductor:
    """Resuelve uuid -> id local con las conexiones a las dos bases ({"mant": con, "alma": con})."""

    def __init__(self, cons):
        self.cons = cons
        self._con_uuid = {}

    def _con_uuid_de(self, base, tabla):
        clave = (base, tabla)
        if clave not in self._con_uuid:
            try:
                self._con_uuid[clave] = _tiene_uuid(self.cons[base], tabla)
            except Exception:
                self._con_uuid[clave] = False
        return self._con_uuid[clave]

    def resolver(self, base, tabla, uuid, id_original):
        """El id local del registro [uuid]; sin uuid (o tabla sin uuid), [id_original] tal cual;
        uuid desconocido -> None."""
        uuid = str(uuid or "").strip().lower()
        if not uuid or not self._con_uuid_de(base, tabla):
            return id_original
        fila = self.cons[base].execute(f"SELECT id FROM {tabla} WHERE lower(uuid) = ?", (uuid,)).fetchone()
        return str(fila[0]) if fila else None


def necesita(ruta, campos):
    """¿Hay algo que traducir en esta petición? (para no abrir las bases sin motivo)."""
    if "uuid" in campos and ruta in RUTAS:
        return True
    if any(f"{c}_uuid" in campos for c in CAMPOS):
        return True
    return "uuid" in (campos.get("materiales") or "")


def traducir(ruta, campos, cons):
    """Copia de [campos] (dict de texto -> texto, el formulario) con los ids traducidos."""
    nuevos = dict(campos)
    t = Traductor(cons)
    if "uuid" in nuevos and ruta in RUTAS:
        base, tabla = RUTAS[ruta]
        local = t.resolver(base, tabla, nuevos.get("uuid"), nuevos.get("id"))
        nuevos["id"] = ID_INEXISTENTE if local is None else local
    for campo, (base, tabla) in CAMPOS.items():
        if f"{campo}_uuid" in nuevos:
            local = t.resolver(base, tabla, nuevos.get(f"{campo}_uuid"), nuevos.get(campo))
            nuevos[campo] = "" if local is None else local
    if nuevos.get("materiales") and "uuid" in nuevos["materiales"]:
        try:
            lineas = json.loads(nuevos["materiales"])
        except (TypeError, ValueError):
            lineas = None
        if isinstance(lineas, list):
            buenas = []
            for linea in lineas:
                u = (linea.get("material_uuid") or linea.get("material_id_uuid")) if isinstance(linea, dict) else None
                if u:
                    local = t.resolver("alma", "materiales", u, linea.get("material_id"))
                    if local is None:
                        continue        # ese artículo ya no existe aquí: no se descuenta OTRO
                    linea = dict(linea, material_id=int(local))
                buenas.append(linea)
            nuevos["materiales"] = json.dumps(buenas)
    return nuevos


def traducir_en_ruta(regla, view_args, uuid, cons):
    """Cambia en [view_args] el id de la dirección por el local del registro [uuid] (-1 si no existe)."""
    nombre, base, tabla = EN_RUTA[regla]
    local = Traductor(cons).resolver(base, tabla, uuid, view_args.get(nombre))
    view_args[nombre] = -1 if local is None else int(local)


def traducir_json(datos, cons):
    """La revisión del almacén con sus ids traducidos (almacen_id y el material_id de cada línea).
    Una línea de un artículo que aquí no existe se quita (no se revisa OTRO)."""
    if not isinstance(datos, dict):
        return datos
    t = Traductor(cons)
    nuevos = dict(datos)
    if nuevos.get("almacen_id_uuid"):
        local = t.resolver("alma", "almacenes", nuevos["almacen_id_uuid"], nuevos.get("almacen_id"))
        nuevos["almacen_id"] = -1 if local is None else int(local)
    if isinstance(nuevos.get("lineas"), list):
        lineas = []
        for linea in nuevos["lineas"]:
            if isinstance(linea, dict) and linea.get("material_id_uuid"):
                local = t.resolver("alma", "materiales", linea["material_id_uuid"], linea.get("material_id"))
                if local is None:
                    continue
                linea = dict(linea, material_id=int(local))
            lineas.append(linea)
        nuevos["lineas"] = lineas
    return nuevos


def uuids(con, tabla, ids):
    """{id: uuid} de esos registros (vacío si la tabla no tiene uuid: PC sin MantPro Cloud)."""
    ids = [int(i) for i in ids if i is not None]
    if not ids or not _tiene_uuid(con, tabla):
        return {}
    resultado = {}
    for trozo in range(0, len(ids), 500):
        parte = ids[trozo:trozo + 500]
        for fila in con.execute(f"SELECT id, uuid FROM {tabla} WHERE id IN ({','.join('?' * len(parte))})", parte):
            resultado[fila[0]] = fila[1]
    return resultado


# Listas que guarda el móvil (regla de Flask) -> tabla del `id` de sus elementos (None: sus elementos
# no tienen id propio que el móvil devuelva). Los campos de CAMPOS se completan en todas.
LISTAS = {
    "/api/pendientes": ("mant", "pendientes"),
    "/api/avisos": ("mant", "avisos_recurrentes"),
    "/api/historial": ("mant", "tareas"),
    "/api/historial_todo": ("mant", "tareas"),
    "/api/maquinas": ("mant", "maquinas"),
    "/api/sedes": ("mant", "sedes"),
    "/api/especialidades": ("mant", "especialidades"),
    "/api/stock/materiales": ("alma", "materiales"),
    "/api/stock/bajo_minimo": ("alma", "materiales"),
    "/api/stock/material/<int:material_id>": ("alma", "materiales"),
    "/api/stock/almacenes": ("alma", "almacenes"),
    "/api/stock/estructura": ("alma", "estanterias"),
    "/api/repuestos": None,
}
# Listas anidadas dentro de un elemento: su clave -> tabla de sus elementos
NIDOS = {
    "estanterias": ("alma", "estanterias"),
    "baldas": ("alma", "baldas"),
    "secciones": ("alma", "secciones"),
    "contadores": ("mant", "contadores"),
}


def _con_tabla(valor, tabla, salida):
    """Recorre [valor] y apunta (dict, tabla de su id) de cada elemento: los de la lista principal
    con [tabla], los de las listas anidadas de NIDOS con la suya, y el resto con None."""
    if isinstance(valor, dict):
        salida.append((valor, tabla))
        for clave, v in valor.items():
            if isinstance(v, list):
                for e in v:
                    _con_tabla(e, NIDOS.get(clave), salida)
            elif isinstance(v, dict):
                _con_tabla(v, NIDOS.get(clave), salida)
    elif isinstance(valor, list):
        for v in valor:
            _con_tabla(v, tabla, salida)


def anadir_uuids(ruta, datos, cons):
    """Pone «uuid» a cada elemento de la lista de [ruta] (y de sus listas anidadas, NIDOS) y
    «<campo>_uuid» a cada campo de CAMPOS (en cualquier nivel). Modifica [datos]; True si añadió algo."""
    destino = LISTAS.get(ruta)
    pares = []
    if isinstance(datos, dict):
        # La respuesta: sus listas (o un único elemento, «material») son de la tabla de la ruta
        for clave, v in datos.items():
            if isinstance(v, (list, dict)):
                _con_tabla(v, NIDOS.get(clave, destino), pares)
    else:
        _con_tabla(datos, destino, pares)
    pedidos = {}                                     # (base, tabla) -> ids
    for d, tabla in pares:
        if tabla and isinstance(d.get("id"), int):
            pedidos.setdefault(tabla, set()).add(d["id"])
        for campo, t_campo in CAMPOS.items():
            if isinstance(d.get(campo), int):
                pedidos.setdefault(t_campo, set()).add(d[campo])
    mapas = {}
    for (base, tabla), ids in pedidos.items():
        try:
            mapas[(base, tabla)] = uuids(cons[base], tabla, ids)
        except Exception:
            mapas[(base, tabla)] = {}
    if not any(mapas.values()):
        return False
    for d, tabla in pares:
        u = mapas.get(tabla, {}).get(d.get("id")) if tabla and isinstance(d.get("id"), int) else None
        if u:
            d["uuid"] = u
        for campo, t_campo in CAMPOS.items():
            u = mapas.get(t_campo, {}).get(d.get(campo)) if isinstance(d.get(campo), int) else None
            if u:
                d[f"{campo}_uuid"] = u
    return True
