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

"""«📦 Historial de revisiones del almacén» (sin Qt): los textos (estados, avisos de periodos sin revisar, móviles que
revisan), las filas de la tabla y de su detalle, y la exportación a Excel o CSV. Lo usan el diálogo del PC y MantPro
Web; los datos están en nucleo/revisiones_almacen.py. Solo de administradores (lo comprueba quien lo muestra, salvo
fijar_revision_sede, que cambia algo)."""

import csv
import io
from datetime import date

from .. import idiomas
from . import almacenes, festivos, ficha_almacenes, sedes, usuarios
from . import revisiones_almacen as rev

VENTANA_AVISO_DIAS = 7       # días hacia atrás que mira el aviso de «sin revisión»
VENTANA_MOVILES_DIAS = 30    # días hacia atrás de la lista de móviles que revisan
# Filtro «Estado»: clave en la URL -> (estados, clave del texto)
FILTROS_ESTADO = {"completas": ([rev.ESTADO_COMPLETA], "rev_filtro_completas"),
                  "incompletas": ([rev.ESTADO_PARCIAL, rev.ESTADO_SIN_EMPEZAR], "rev_filtro_incompletas")}
LIMITE = 5000


def _fecha(iso):
    return idiomas.formato_fecha_localizada(iso) if iso else ""


def nombres_estado():
    return {rev.ESTADO_COMPLETA: idiomas.t("rev_estado_completa"), rev.ESTADO_PARCIAL: idiomas.t("rev_estado_parcial"),
            rev.ESTADO_SIN_EMPEZAR: idiomas.t("rev_estado_sin_empezar")}


def texto_dias_sin_revision(festivos=()):
    """Aviso de los días laborables sin ninguna revisión del almacén, o "" si no falta ninguno."""
    faltan = rev.dias_sin_revision(VENTANA_AVISO_DIAS, festivos=festivos)
    if not faltan:
        return ""
    return idiomas.t("rev_aviso_dias").format(n=VENTANA_AVISO_DIAS, dias=", ".join(_fecha(d) for d in faltan))


def lineas_avisos(sede=None, festivos_de=None, almacen_id=None):
    """Avisos de los almacenes que se ven desde [sede] (o solo [almacen_id]) con periodos de su ciclo sin revisar."""
    def periodo(inicio, fin):
        return _fecha(inicio) if inicio == fin else f"{_fecha(inicio)} – {_fecha(fin)}"

    lineas = []
    for aviso in rev.avisos(sede, festivos_de=festivos_de):
        a = aviso["almacen"]
        if almacen_id is not None and a["id"] != almacen_id:
            continue
        lineas.append(idiomas.t("rev_aviso_almacen").format(
            almacen=a["nombre"], ciclo=ficha_almacenes.texto_ciclo(a).lower(),
            periodos=", ".join(periodo(i, f) for i, f in aviso["faltan"])))
    return lineas


def festivos_de_cache(db, anio):
    """Función sede_id -> festivos de [anio] de esa sede (los suyos si tiene región propia), solo de la caché: como el
    PC, los avisos no esperan a internet."""
    def de(sede_id):
        return festivos.fechas(db, anio, sedes.obtener(sede_id) if sede_id is not None else None, descargar_si_falta=False)
    return de


def texto_avisos(sede=None, festivos_de=None, almacen_id=None):
    return "\n".join(lineas_avisos(sede, festivos_de, almacen_id))


def lineas_moviles():
    """(título, [líneas]) de los móviles que han hecho revisiones, o (None, []) si ninguno en el periodo."""
    moviles = rev.moviles_que_revisan(VENTANA_MOVILES_DIAS)
    if not moviles:
        return None, []
    return (idiomas.t("rev_moviles_titulo").format(n=VENTANA_MOVILES_DIAS),
            [idiomas.t("rev_moviles_linea").format(movil=m["dispositivo"], usuario=m["usuario_nombre"] or "—",
                                                   fecha=_fecha(m["ultima_fecha"]), n=m["revisiones"])
             for m in moviles])


def texto_moviles():
    titulo, lineas = lineas_moviles()
    return titulo + "\n" + "\n".join(lineas) if titulo else ""


# ----------------------------------------------------------- filtros y filas

def filtros(dias=None, usuario_id=None, estado=None, sede=None, almacen_id=None):
    """Los argumentos de rev.listar_revisiones. [estado]: clave de FILTROS_ESTADO (otra cosa = todas). [sede]: la
    elegida o, sin elegir, las que se ven (None = todas). [almacen_id]: uno concreto."""
    estados = FILTROS_ESTADO.get(estado, (None, None))[0]
    if almacen_id is not None:
        ids = [almacen_id]
    else:
        ids = None if sede is None else [a["id"] for a in almacenes.listar(sede)]
    return dict(dias=dias, usuario_id=usuario_id, estado=estados, almacen_ids=ids)


class Almacenes:
    """Nombre y sede de cada almacén (también inactivos), leídos una vez."""
    def __init__(self):
        self.por_id = {a["id"]: a for a in almacenes.listar(incluir_inactivos=True)}
        self.nombres_sedes = sedes.nombres()

    def nombre(self, almacen_id):
        a = self.por_id.get(almacen_id)
        return a["nombre"] if a else "—"

    def sede(self, almacen_id):
        a = self.por_id.get(almacen_id)
        return (ficha_almacenes.nombre_sede(a, self.nombres_sedes) or "—") if a else "—"


def _numero(valor):
    return "—" if valor is None else f"{valor:g}"


def _diferencia(valor):
    if valor is None:
        return "—"
    return f"{valor:+g}" if valor else "0"


def _actividad(texto):
    """«2026-11-04 08:15:02» → fecha del idioma + hora."""
    fecha, _, hora = (texto or "").partition(" ")
    return f"{_fecha(fecha)} {hora[:5]}".strip()


def filas(filtro, limite=LIMITE):
    """(filas, cuentas): las revisiones con sus 8 columnas ya en texto y cuántas hay de cada estado."""
    estados, alm = nombres_estado(), Almacenes()
    cuentas = {rev.ESTADO_COMPLETA: 0, rev.ESTADO_PARCIAL: 0, rev.ESTADO_SIN_EMPEZAR: 0}
    resultado = []
    for r in rev.listar_revisiones(limite=limite, **filtro):
        cuentas[r["estado"]] += 1
        resultado.append({"id": r["id"], "uid": r.get("uid"), "almacen_id": r["almacen_id"], "estado": r["estado"],
                          "fecha": _fecha(r["fecha"]),
                          "usuario": r["usuario_nombre"] or "—", "movil": r["dispositivo"] or "—",
                          "revisados": f"{r['revisados']}/{r['total']}  {estados[r['estado']]}",
                          "revisados_n": f"{r['revisados']}/{r['total']}",
                          "ajustados": str(r["ajustados"]) if r["revisados"] else "—",
                          "actividad": _actividad(r["actualizada"]), "almacen": r["almacen_nombre"],
                          "sede": alm.sede(r["almacen_id"])})
    return resultado, cuentas


def texto_resumen(cuentas):
    return idiomas.t("rev_resumen").format(c=cuentas[rev.ESTADO_COMPLETA], i=cuentas[rev.ESTADO_PARCIAL],
                                           s=cuentas[rev.ESTADO_SIN_EMPEZAR])


def lineas(revision_id, alm=None):
    """El detalle de una revisión: sus artículos con las 8 columnas ya en texto."""
    alm = alm or Almacenes()
    resultado = []
    for ln in rev.lineas_de_revision(revision_id):
        unidad = f" {ln['unidad']}" if ln["unidad"] else ""
        if ln["revisado"]:
            estado = idiomas.t("rev_linea_revisada") + (f" {ln['fecha_revision'][11:16]}" if ln["fecha_revision"] else "")
        else:
            estado = idiomas.t("rev_linea_pendiente")
        resultado.append({"articulo": f"{ln['codigo']} · {ln['nombre']}" if ln["codigo"] else ln["nombre"],
                          "ubicacion": ln["ubicacion"] or "—", "sistema": _numero(ln["cantidad_sistema"]) + unidad,
                          "contado": (_numero(ln["cantidad_contada"]) + unidad) if ln["revisado"] else "—",
                          "diferencia": _diferencia(ln["diferencia"]), "con_diferencia": bool(ln["diferencia"]),
                          "revisado": bool(ln["revisado"]), "estado": estado,
                          "almacen": alm.nombre(ln["almacen_id"]), "sede": alm.sede(ln["almacen_id"])})
    return resultado


def fijar_revision_sede(admin, sede_id, activa):
    """«Revisión del almacén activa en esta sede» (None = la principal)."""
    if not usuarios.es_admin(admin):
        raise ValueError("solo_admin")
    sedes.fijar_revision(sede_id, activa)


# ----------------------------------------------------------- exportar

def cabecera_exportar():
    t = idiomas.t
    return [t("lbl_fecha"), t("aud_usuario"), t("rev_col_movil"), t("rev_col_estado"), t("rev_col_revisados"),
            t("rev_col_articulo"), t("lbl_ubicacion"), t("rev_col_sistema"), t("rev_col_contado"),
            t("rev_col_diferencia"), t("rev_linea_estado"), t("lbl_almacen"), t("alm_lbl_sede")]


def filas_exportar(filtro):
    """Una fila por artículo propuesto."""
    estados, alm = nombres_estado(), Almacenes()
    si, no = idiomas.t("rev_si"), idiomas.t("rev_no")
    for r in rev.listar_revisiones(limite=100000, **filtro):
        for ln in rev.lineas_de_revision(r["id"]):
            articulo = f"{ln['codigo']} · {ln['nombre']}" if ln["codigo"] else ln["nombre"]
            yield [_fecha(r["fecha"]), r["usuario_nombre"], r["dispositivo"], estados[r["estado"]],
                   f"{r['revisados']}/{r['total']}", articulo, ln["ubicacion"],
                   ln["cantidad_sistema"] if ln["cantidad_sistema"] is not None else "",
                   ln["cantidad_contada"] if ln["revisado"] and ln["cantidad_contada"] is not None else "",
                   ln["diferencia"] if ln["diferencia"] is not None else "", si if ln["revisado"] else no,
                   alm.nombre(ln["almacen_id"]), alm.sede(ln["almacen_id"])]


def nombre_fichero(formato):
    return f"{idiomas.t('rev_fichero')}_{date.today().strftime('%Y%m%d')}.{formato}"


def exportar(destino, formato, filtro):
    """Escribe las revisiones de [filtro] en [destino] (ruta o fichero binario abierto) como «xlsx» o «csv».
    Devuelve cuántas filas ha escrito. Los números van como números y los textos siempre como texto."""
    cab = cabecera_exportar()
    filas_ = list(filas_exportar(filtro))
    if formato == "csv":
        texto = io.StringIO(newline="")
        w = csv.writer(texto, delimiter=";")
        w.writerow(cab)
        w.writerows(filas_)
        datos = texto.getvalue().encode("utf-8-sig")
        if isinstance(destino, str):
            with open(destino, "wb") as fh:
                fh.write(datos)
        else:
            destino.write(datos)
        return len(filas_)
    import xlsxwriter
    libro = xlsxwriter.Workbook(destino, {"in_memory": True})
    hoja = libro.add_worksheet(idiomas.t("rev_hoja")[:31])
    negrita = libro.add_format({"bold": True, "bg_color": "#2c3e50", "font_color": "white"})
    for col, texto in enumerate(cab):
        hoja.write(0, col, texto, negrita)
    for i, fila_ in enumerate(filas_, start=1):
        for col, valor in enumerate(fila_):
            if isinstance(valor, (int, float)) and not isinstance(valor, bool):
                hoja.write_number(i, col, valor)
            else:
                hoja.write_string(i, col, "" if valor is None else str(valor))
    for col, ancho in enumerate((12, 18, 20, 16, 11, 36, 24, 14, 12, 12, 11)):
        hoja.set_column(col, col, ancho)
    hoja.freeze_panes(1, 0)
    hoja.autofilter(0, 0, max(len(filas_), 1), len(cab) - 1)
    libro.close()
    return len(filas_)
