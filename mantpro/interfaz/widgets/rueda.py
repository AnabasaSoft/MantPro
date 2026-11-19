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
rueda.py — La rueda del ratón no cambia los desplegables.

Con el cursor encima de un desplegable (QComboBox) cerrado, la rueda no cambia
la opción elegida: se pasa a lo que lo contiene (la tabla, el formulario con
barra de desplazamiento…), que sube o baja como si el desplegable no estuviera.
Así no se cambia un valor sin querer al desplazarse por una ventana. Con el
desplegable abierto, la rueda recorre su lista como siempre.

Un solo filtro para toda la aplicación: vale para los desplegables que ya hay
y para los que se creen después, sin tocar cada ventana.
"""

from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtWidgets import QApplication, QComboBox


class _FiltroRueda(QObject):
    def eventFilter(self, obj, evento):
        if evento.type() == QEvent.Type.Wheel and isinstance(obj, QComboBox):
            # Hacia arriba, padre a padre, hasta quien lo use (la tabla o la zona desplazable).
            # Reenviado a mano Qt no lo propaga solo.
            padre = obj.parentWidget()
            while padre is not None:
                evento.setAccepted(False)
                QApplication.sendEvent(padre, evento)
                if evento.isAccepted():
                    break
                padre = padre.parentWidget()
            return True          # el desplegable no se entera
        return False


_filtro = None


def instalar(app):
    global _filtro
    if _filtro is None:
        _filtro = _FiltroRueda(app)
        app.installEventFilter(_filtro)
