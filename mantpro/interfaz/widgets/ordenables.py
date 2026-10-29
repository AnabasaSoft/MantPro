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

"""Elementos de árbol y tabla con orden natural por ubicación."""

import re
from PyQt6.QtWidgets import QTableWidgetItem, QTreeWidgetItem
from PyQt6.QtCore import Qt

class _ItemArbolOrdenable(QTreeWidgetItem):
    """QTreeWidgetItem que, si la columna tiene una clave de orden guardada en
    UserRole+1 (un número o una fecha ISO), la usa para comparar en vez del
    texto mostrado. Así "10" no queda antes que "2" y las fechas se ordenan
    cronológicamente y no alfabéticamente al pulsar la cabecera del árbol."""
    def __lt__(self, otro):
        arbol = self.treeWidget()
        columna = arbol.sortColumn() if arbol else 0
        clave_propia = self.data(columna, Qt.ItemDataRole.UserRole + 1)
        clave_otro = otro.data(columna, Qt.ItemDataRole.UserRole + 1)
        if clave_propia is not None and clave_otro is not None:
            return clave_propia < clave_otro
        return super().__lt__(otro)


def _clave_orden_ubicacion(ubicacion, nombre=""):
    """Clave de texto para ordenar ubicaciones de forma natural ("Estantería 2"
    antes que "Estantería 10"), con el nombre del material como desempate y
    los materiales sin ubicación al final."""
    natural = lambda t: re.sub(r"\d+", lambda m: m.group().zfill(8), (t or "").lower())
    return ("\uffff" if not ubicacion else natural(ubicacion)) + "\x00" + natural(nombre)


class _ItemTablaOrdenable(QTableWidgetItem):
    """QTableWidgetItem que, si tiene guardada una clave de orden en
    UserRole+1 (un número), la usa para comparar en vez del texto mostrado.
    Así "10" no queda antes que "2" al pulsar la cabecera para ordenar."""
    def __lt__(self, otro):
        clave_propia = self.data(Qt.ItemDataRole.UserRole + 1)
        clave_otro = otro.data(Qt.ItemDataRole.UserRole + 1)
        if clave_propia is not None and clave_otro is not None:
            return clave_propia < clave_otro
        return super().__lt__(otro)
