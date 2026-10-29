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

"""Utilidades compartidas por la interfaz: traducciones, recursos, URLs y
pequeños ayudantes de widgets."""

import sys
import os
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import QSettings, QTranslator, QLibraryInfo

from ..idiomas import t
from ..nucleo import almacen, maquinas

def tt(clave, defecto):
    """t() con texto por defecto: si la clave aún no está en idiomas.py,
    devuelve el literal en castellano en vez del nombre de la clave."""
    valor = t(clave)
    return defecto if valor == clave else valor


def traducir_motivo_movimiento(motivo):
    """Traduce al idioma activo los motivos de movimiento de stock que genera
    la propia aplicación (guardados en forma canónica, ver almacen.py). Los
    que escribe el usuario a mano se devuelven tal cual."""
    if motivo == almacen.MOTIVO_ALTA_INICIAL:
        return tt("motivo_alta_inicial", motivo)
    if motivo == almacen.MOTIVO_AJUSTE_IMPORTACION:
        return tt("motivo_ajuste_importacion", motivo)
    if motivo.startswith(almacen.PREFIJO_MOTIVO_USADO_EN_TRABAJO):
        trabajo = motivo[len(almacen.PREFIJO_MOTIVO_USADO_EN_TRABAJO):]
        return tt("motivo_usado_en_trabajo", "Usado en trabajo: {trabajo}").format(trabajo=trabajo)
    return motivo


# ==========================================
# GESTIÓN DE RUTAS (INTELIGENTE)
# ==========================================

# Raíz del proyecto (donde están main.py y recursos/), sea cual sea la carpeta
# desde la que se lance "python main.py".
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resource_path(relative_path):
    """ Para recursos ESTÁTICOS (solo lectura) empaquetados (recursos/icono.png).
    En el binario de PyInstaller están en sys._MEIPASS, con la misma ruta
    relativa que en el proyecto (ver --add-data en build_desktop.yml). """
    base_path = getattr(sys, "_MEIPASS", RAIZ_PROYECTO)
    return os.path.join(base_path, relative_path)


def entorno_sistema():
    """Entorno para lanzar programas del sistema desde el binario de PyInstaller.
    PyInstaller apunta LD_LIBRARY_PATH a su carpeta temporal (/tmp/_MEI…), y un
    programa del sistema que la herede carga bibliotecas empaquetadas
    incompatibles (p. ej. /bin/sh con su libreadline revienta con
    "undefined symbol: rl_full_quoting_desired"). Se restaura el valor original,
    que PyInstaller guarda en <VAR>_ORIG."""
    env = dict(os.environ)
    if not getattr(sys, "frozen", False):
        return env
    for var in [k for k in env if k.endswith("_ORIG")]:
        env[var[:-5]] = env.pop(var)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        for var in [k for k, v in env.items() if meipass in v]:
            del env[var]
    return env


def abrir_url_externa(url):
    """Abre una URL en el navegador del sistema."""
    import webbrowser
    if sys.platform.startswith("linux"):
        try:
            import subprocess
            # Sin shell: la URL va como argumento y no pasa por /bin/sh.
            subprocess.Popen(["xdg-open", url], env=entorno_sistema(),
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            return
        except Exception as e:
            print(f"xdg-open falló ({e}), probando webbrowser")
    webbrowser.open(url)


def instalar_traductor_qt(app, codigo_idioma):
    """Traduce los textos propios de Qt (menú contextual de cortar/copiar/pegar,
    botones de QMessageBox, etc.) al idioma de la app. Sin esto, esos textos
    siempre salen en inglés aunque el resto de la interfaz esté en español.
    El euskara no tiene traducción oficial en Qt, así que se queda en inglés."""
    traductor = QTranslator(app)
    ruta_traducciones = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    # Qt trae el portugués de Brasil como "pt_BR", no como "pt".
    codigo_qt = {"pt": "pt_BR"}.get(codigo_idioma, codigo_idioma)
    if traductor.load(f"qtbase_{codigo_qt}", ruta_traducciones):
        app.installTranslator(traductor)
        app._traductor_qt = traductor  # evitar que el GC lo destruya


def _estilo_zona_arrastre(activo=False):
    """Estilo de las zonas de 'arrastra una foto aquí', adaptado al tema actual
    (oscuro/claro/retro), para no quedar siempre en negro en temas claros."""
    oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
    if activo:
        return ("border: 2px dashed #3daee9; background: #333; color: #3daee9;" if oscuro
                else "border: 2px dashed #0078d4; background: #eaf3fb; color: #0078d4;")
    return ("border: 2px dashed #666; color: #888; background: #2b2b2b;" if oscuro
            else "border: 2px dashed #999; color: #666; background: #f0f0f0;")


def _estilo_check_etiqueta():
    """Estilo de los checkboxes de 'Etiquetas rápidas' (Urgente/Eléctrico/...),
    adaptado al tema actual para que el texto no quede gris clarito sobre fondo claro."""
    oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
    return "font-weight: bold; color: #bbb;" if oscuro else "font-weight: bold; color: #555;"


def _crear_checks_etiquetas(host, layout, incluir_averia=True):
    """Crea los checkboxes de 'etiquetas rápidas' (Urgente/Eléctrico/Mecánico/
    Preventivo y, si procede, Avería), los deja guardados en host.chk_urgente/
    chk_electrico/chk_mecanico/chk_prev/chk_averia y los añade a layout con el
    estilo común. Evita repetir esta construcción en cada diálogo/pestaña."""
    host.chk_urgente = QCheckBox(t("tag_urgente"))
    host.chk_electrico = QCheckBox(t("tag_electrico"))
    host.chk_mecanico = QCheckBox(t("tag_mecanico"))
    host.chk_prev = QCheckBox(t("tag_preventivo"))
    checks = [host.chk_urgente, host.chk_electrico, host.chk_mecanico, host.chk_prev]
    if incluir_averia:
        host.chk_averia = QCheckBox(tt("tag_averia", "Avería"))
        checks.append(host.chk_averia)
    for c in checks:
        c.setStyleSheet(_estilo_check_etiqueta())
        layout.addWidget(c)


def _tags_desde_checks(host, incluir_averia=True):
    """Devuelve la lista de etiquetas marcadas en los checks creados por
    _crear_checks_etiquetas, en el mismo orden en que se guardaban antes de
    unificar esta lógica (para no alterar el texto ya guardado en BD)."""
    tags = []
    if host.chk_urgente.isChecked(): tags.append("Urgente")
    if host.chk_electrico.isChecked(): tags.append("Eléctrico")
    if host.chk_mecanico.isChecked(): tags.append("Mecánico")
    if host.chk_prev.isChecked(): tags.append("Preventivo")
    if incluir_averia and host.chk_averia.isChecked(): tags.append("Avería")
    return tags


def _estilo_label_dialogo():
    """Estilo de las etiquetas de campo de formularios de diálogo (p.ej. AvisoEditDialog),
    adaptado al tema para que no queden en gris clarito sobre fondo claro."""
    oscuro = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro") == "oscuro"
    return f"font-weight: bold; font-size: 14px; color: {'#ccc' if oscuro else '#444'};"


def _poblar_combo_maquinas(combo, seleccion_id=None):
    """Rellena un QComboBox con el árbol de máquinas (indentado por nivel) y una
    primera opción de 'sin máquina', dejando seleccionada la máquina indicada."""
    combo.clear()
    combo.addItem(tt("lbl_sin_maquina", "— Sin máquina —"), None)
    todas = maquinas.listar_maquinas()
    por_padre = {}
    for m in todas:
        por_padre.setdefault(m["padre_id"], []).append(m)

    def anadir(padre_id, nivel):
        for m in por_padre.get(padre_id, []):
            combo.addItem(("    " * nivel) + m["nombre"], m["id"])
            anadir(m["id"], nivel + 1)

    anadir(None, 0)
    idx = combo.findData(seleccion_id)
    if idx >= 0:
        combo.setCurrentIndex(idx)


def traducir_tags_bd(tags_bd):
    traducciones = {
        "Urgente": t("tag_urgente"),
        "Eléctrico": t("tag_electrico"),
        "Mecánico": t("tag_mecanico"),
        "Preventivo": t("tag_preventivo"),
        "Avería": tt("tag_averia", "Avería"),
    }
    return ", ".join([traducciones.get(x.strip(), x.strip()) for x in tags_bd.split(",") if x.strip()])


def traducir_prioridad(codigo):
    claves = {"Baja": "prioridad_baja", "Media": "prioridad_media", "Alta": "prioridad_alta", "Crítica": "prioridad_critica"}
    return tt(claves.get(codigo, "prioridad_media"), codigo or "Media")
