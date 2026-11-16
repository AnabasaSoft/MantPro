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

"""Columnas que siempre se pueden ajustar arrastrando, en todas las tablas y árboles.

Qt no deja arrastrar una columna en modo «Stretch» o «ResizeToContents». En vez de
cambiar cada tabla, `instalar(app)` pone un filtro en la aplicación: al mostrarse
una cabecera horizontal con esos modos, la pasa a «Interactive» y simula lo que
hacían:
  * las de «ajustar al contenido» se adaptan a los datos cada vez que cambian;
  * las de «estirar» se reparten el espacio que sobra al cambiar el tamaño.
En cuanto el usuario arrastra una columna, esa se queda con su ancho, y se guarda
(QSettings, grupo «columnas»): al volver a abrir la misma ventana se recupera.
Vale para todas las tablas y árboles con columnas, también las que ya eran arrastrables."""

import json

from PyQt6.QtCore import QEvent, QObject, QSettings, QTimer
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView

_MODO = QHeaderView.ResizeMode


def _clave(vista):
    """Identificador estable de una tabla: la ventana y el camino hasta ella (clase e índice
    entre los hermanos de la misma clase)."""
    partes = []
    w = vista
    while w is not None:
        padre = w.parentWidget()
        hermanos = [h for h in (padre.findChildren(type(w)) if padre is not None else [])
                    if h.parentWidget() is padre]
        indice = hermanos.index(w) if w in hermanos else 0
        partes.append(f"{type(w).__name__}{indice}" if padre is not None else type(w).__name__)
        if w.isWindow():
            break
        w = padre
    return "/".join(reversed(partes))


def _ajustes():
    return QSettings("MyCompany", "MantenimientoApp")


# Los ajustes vivos. Sin esta referencia Python recoge el objeto (aunque Qt conserve su
# parte C++ como hija de la cabecera) y se pierde toda su lógica. Sale de aquí al destruirse su tabla.
_vivos = set()


class _Ajuste(QObject):
    def __init__(self, cabecera, vista):
        super().__init__(cabecera)
        self.cabecera = cabecera
        self.vista = vista
        self.contenido = set()     # columnas que se ajustaban al contenido
        self.estirar = set()       # columnas que se estiraban
        self.manuales = set()      # columnas que ha arrastrado el usuario
        self.guardados = {}        # {columna: ancho} guardados por el usuario
        self._clave = None
        self._ajustando = False
        self._vivo = True
        _vivos.add(self)
        # Temporizador propio (hijo de este objeto): muere con él, nunca queda una llamada colgada
        self._temporizador = QTimer(self)
        self._temporizador.setSingleShot(True)
        self._temporizador.setInterval(0)
        self._temporizador.timeout.connect(self._hacer)
        self._guardar_tm = QTimer(self)           # guarda medio segundo después de arrastrar
        self._guardar_tm.setSingleShot(True)
        self._guardar_tm.setInterval(500)
        self._guardar_tm.timeout.connect(self._guardar)
        self._cargar()
        vista.destroyed.connect(self._morir)
        cabecera.destroyed.connect(self._morir)
        self._absorber()
        cabecera.sectionResized.connect(self._al_redimensionar)
        vista.viewport().installEventFilter(self)
        modelo = vista.model()
        if modelo is not None:
            for senal in (modelo.rowsInserted, modelo.rowsRemoved, modelo.modelReset,
                          modelo.layoutChanged, modelo.dataChanged, modelo.columnsInserted):
                senal.connect(self.recalcular)
        self.recalcular()

    def _absorber(self):
        """Pasa a Interactive las columnas con otro modo (también si el código lo vuelve a poner)."""
        cambiado = False
        for i in range(self.cabecera.count()):
            modo = self.cabecera.sectionResizeMode(i)
            if modo == _MODO.Stretch:
                self.estirar.add(i); self.contenido.discard(i)
            elif modo == _MODO.ResizeToContents:
                self.contenido.add(i); self.estirar.discard(i)
            else:
                continue
            self.cabecera.setSectionResizeMode(i, _MODO.Interactive)
            cambiado = True
        if self.cabecera.stretchLastSection():
            ultima = self.cabecera.count() - 1
            if ultima >= 0 and ultima not in self.contenido:
                self.estirar.add(ultima)
            self.cabecera.setStretchLastSection(False)
            cambiado = True
        return cambiado

    def _cargar(self):
        try:
            self._clave = "columnas/" + _clave(self.vista)
            datos = json.loads(_ajustes().value(self._clave, "") or "{}")
        except (TypeError, ValueError, RuntimeError):
            datos = {}
        if datos.get("n") == self.cabecera.count():   # si la tabla ha cambiado de columnas, se ignora
            self.guardados = {int(k): int(v) for k, v in (datos.get("anchos") or {}).items()}
            self.manuales |= set(self.guardados)

    def _guardar(self):
        if not self._vivo or not self._clave:
            return
        try:
            for i in self.manuales:
                if 0 <= i < self.cabecera.count() and not self.cabecera.isSectionHidden(i):
                    self.guardados[i] = self.cabecera.sectionSize(i)
            _ajustes().setValue(self._clave, json.dumps(
                {"n": self.cabecera.count(), "anchos": {str(k): v for k, v in self.guardados.items()}}))
        except RuntimeError:
            pass

    def _morir(self, *_):
        if self._guardar_tm.isActive():
            self._guardar_tm.stop()
            self._guardar()
        self._vivo = False
        self._temporizador.stop()
        _vivos.discard(self)

    def eventFilter(self, obj, evento):
        if self._vivo and not _cerrando and evento.type() == QEvent.Type.Resize:
            self.recalcular()
        return False

    def _al_redimensionar(self, indice, _viejo, nuevo):
        if not self._ajustando and self._vivo and nuevo > 0:
            self.manuales.add(indice)
            self.guardados[indice] = nuevo
            self._guardar()

    def recalcular(self, *_):
        if self._vivo and not _cerrando and not self._temporizador.isActive():
            self._temporizador.start()

    def _hacer(self):
        if not self._vivo or _cerrando:
            return
        try:
            cab, vista = self.cabecera, self.vista
            if cab is None or vista is None:
                return
            self._ajustando = True
            self._absorber()
            for i, ancho in self.guardados.items():   # los anchos que puso el usuario
                if 0 <= i < cab.count() and cab.sectionSize(i) != ancho and not cab.isSectionHidden(i):
                    cab.resizeSection(i, ancho)
            for i in self.contenido - self.manuales:
                if not cab.isSectionHidden(i):
                    vista.resizeColumnToContents(i)
            estirables = [i for i in sorted(self.estirar - self.manuales) if not cab.isSectionHidden(i)]
            if estirables:
                ocupado = sum(cab.sectionSize(i) for i in range(cab.count())
                              if not cab.isSectionHidden(i) and i not in estirables)
                sobra = vista.viewport().width() - ocupado
                reparto = sobra // len(estirables)
                for i in estirables:
                    # nunca más estrecha que su contenido (si no cabe, sale la barra horizontal)
                    try:
                        minimo = max(cab.sectionSizeHint(i), vista.sizeHintForColumn(i))
                    except (AttributeError, RuntimeError, TypeError):
                        minimo = cab.sectionSizeHint(i)
                    cab.resizeSection(i, max(cab.minimumSectionSize(), 60, minimo, reparto))
        except RuntimeError:      # la tabla ya no existe
            pass
        finally:
            self._ajustando = False


class _Filtro(QObject):
    def eventFilter(self, obj, evento):
        if _cerrando or evento.type() != QEvent.Type.Show:
            return False
        if isinstance(obj, QAbstractItemView):
            cab = getattr(obj, "horizontalHeader", None) or getattr(obj, "header", None)
            cab = cab() if callable(cab) else None
            if isinstance(cab, QHeaderView) and not cab.property("_ajuste_columnas"):
                if cab.count() > 1 and not cab.isHidden():
                    cab.setProperty("_ajuste_columnas", True)
                    _Ajuste(cab, obj)          # su padre es la cabecera: muere con ella
        return False


_filtro = None
_cerrando = False


def _quitar():
    """Al cerrar: quita el filtro antes de que Python destruya las ventanas (si no, Qt
    puede llamar a un filtro ya medio destruido y el programa se cae al salir)."""
    global _filtro, _cerrando
    _cerrando = True
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None and _filtro is not None:
            app.removeEventFilter(_filtro)
    except RuntimeError:
        pass


def instalar(app):
    """Activa las columnas ajustables en toda la aplicación (una vez)."""
    global _filtro
    if _filtro is None:
        import atexit
        _filtro = _Filtro()          # sin padre: lo guarda este módulo, no Qt
        app.installEventFilter(_filtro)
        app.aboutToQuit.connect(_quitar)
        atexit.register(_quitar)
