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

"""Marcas de fotos dentro de la descripción de un trabajo ([FOTOS: ...])."""

import re

# --- Colección de fotos de un trabajo -------------------------------------
# Además de la foto de antes ([FOTO: x]) y la de después ([FOTO_DESPUES: y]),
# un trabajo puede llevar una colección de fotos extra, guardada igual que
# las otras: como una marca en la propia descripción, [FOTOS: a.jpg, b.jpg].
# Así viaja sola con el trabajo (pendiente -> historial, revertir, editar,
# sincronizar con el móvil) sin cambiar el esquema de la base de datos.
_RE_GALERIA = re.compile(r"\[FOTOS:\s*(.*?)\]")


def fotos_galeria(texto):
    """Lista de nombres de fichero de la colección de fotos de [texto]."""
    m = _RE_GALERIA.search(texto or "")
    if not m: return []
    return [f.strip() for f in m.group(1).split(",") if f.strip()]


def con_fotos_galeria(texto, nombres):
    """Devuelve [texto] con la marca de colección sustituida por [nombres]
    (o quitada si la lista está vacía)."""
    texto = re.sub(r"\n?\[FOTOS:.*?\]", "", texto or "").rstrip()
    nombres = [n for n in nombres if n]
    if nombres:
        texto += ("\n" if texto else "") + f"[FOTOS: {', '.join(nombres)}]"
    return texto


def quitar_marcas_foto(texto):
    """Quita del texto todas las marcas de foto ([FOTO:], [FOTO_DESPUES:],
    [FOTOS:]) y la de referencia [REF:], para mostrarlo."""
    texto = re.sub(r"\[FOTO.*?:.*?\]", "", texto or "")
    return re.sub(r"\[REF:.*?\]", "", texto).strip()
