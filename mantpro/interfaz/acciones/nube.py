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

"""Sincronización automática con MantPro Cloud: subir y bajar los cambios cada pocos minutos."""

import threading
import time
from datetime import date

from PyQt6.QtCore import QSettings, QTimer
from PyQt6.QtWidgets import QMessageBox

from ..comun import tt
from ...nucleo import nube, sincro_nube

SEGUNDOS_SINCRONIZACION_NUBE = 60     # cada cuánto sube y BAJA lo nuevo mientras MantPro está abierto (lo que hagan los móviles en la nube)
SEGUNDOS_VIGILAR_CAMBIOS = 5          # cada cuánto mira si hay cambios sin subir (y los sube al momento)
SEGUNDOS_ESPERA_TRAS_ERROR = 60       # si la última subida falló (sin internet, licencia...), no insiste antes de esto
SEGUNDOS_ESPERA_AL_CERRAR = 8         # lo que espera al cerrar MantPro para dejar subido lo último
SEGUNDOS_PRIMERA_SINCRONIZACION = 15  # tras abrir MantPro (da tiempo a que cargue todo; poco, para que lo hecho por los móviles en la nube llegue pronto)
SEGUNDOS_REVISAR_RESULTADO = 3        # cada cuánto mira la ventana si ha terminado la sincronización de fondo
SEGUNDOS_COMPROBAR_CUENTA = 6 * 3600  # cada cuánto pregunta la licencia y el espacio (y tras abrir, con la primera sincronización)
ERRORES_DE_CUENTA = {"licencia_caducada": None, "licencia_suspendida": "licencia_suspendida",
                     "almacenamiento_lleno": "espacio_lleno"}   # error de sincronización -> aviso (None: según la licencia)


class AccionesNube:
    """Temporizador de la sincronización con MantPro Cloud (sube lo nuevo y baja lo de otros). Solo hace
    algo si este PC tiene sesión iniciada: sin ella MantPro funciona igual que siempre. La red va en un
    hilo aparte, así que nunca bloquea la ventana, y sin conexión no pasa nada: lo no subido queda en
    la cola y se sube la siguiente vez. No avisa de errores (el diálogo Herramientas → MantPro Cloud
    muestra el estado y deja sincronizar a mano), salvo de dos cosas: un stock que ha quedado negativo
    tras bajar movimientos de otros (recuento urgente) y que hace falta una decisión del usuario.
    El hilo de fondo nunca toca la interfaz: deja el resultado y es la ventana quien lo recoge."""

    def iniciar_sincronizacion_nube(self):
        """Se llama una vez, al crear la ventana."""
        self._hilo_nube = None
        self._resultado_nube = None
        self._aviso_decision_mostrado = False
        self.temporizador_resultado_nube = QTimer(self)
        self.temporizador_resultado_nube.timeout.connect(self._revisar_resultado_nube)
        self.temporizador_resultado_nube.start(SEGUNDOS_REVISAR_RESULTADO * 1000)
        self.temporizador_nube = QTimer(self)
        self.temporizador_nube.timeout.connect(self._tic_nube)
        self.temporizador_nube.start(SEGUNDOS_SINCRONIZACION_NUBE * 1000)
        QTimer.singleShot(SEGUNDOS_PRIMERA_SINCRONIZACION * 1000, self._tic_nube)
        # Licencia y espacio: al abrir y cada pocas horas, en un hilo; si hay que pagar o queda poco
        # espacio, un aviso emergente a los administradores (como mucho una vez al día por aviso)
        self._avisos_cuenta = None
        self.temporizador_cuenta_nube = QTimer(self)
        self.temporizador_cuenta_nube.timeout.connect(self._comprobar_cuenta_nube)
        self.temporizador_cuenta_nube.start(SEGUNDOS_COMPROBAR_CUENTA * 1000)
        QTimer.singleShot(SEGUNDOS_PRIMERA_SINCRONIZACION * 1000, self._comprobar_cuenta_nube)
        # Subir al momento: cada pocos segundos se mira si hay algo sin subir (una lectura mínima, sin red);
        # solo si lo hay se sincroniza. Lo que cambian los móviles contra este PC también cuenta.
        self._proximo_intento_nube = 0.0
        self.temporizador_cambios_nube = QTimer(self)
        self.temporizador_cambios_nube.timeout.connect(self._vigilar_cambios_nube)
        self.temporizador_cambios_nube.start(SEGUNDOS_VIGILAR_CAMBIOS * 1000)

    def parar_sincronizacion_nube(self):
        for nombre in ("temporizador_nube", "temporizador_cambios_nube", "temporizador_resultado_nube",
                       "temporizador_cuenta_nube"):
            temporizador = getattr(self, nombre, None)
            if temporizador is not None:
                temporizador.stop()
        self._sincronizar_al_cerrar()

    def _sincronizar_al_cerrar(self):
        """Al cerrar MantPro deja subido lo último (un cambio de hace unos segundos no debe quedarse solo en
        este PC: otro PC o un móvil en la nube no lo verían). Espera como mucho unos segundos."""
        try:
            if nube.sesion() is None:
                return
            hilo = getattr(self, "_hilo_nube", None)
            if hilo is None or not hilo.is_alive():
                if not sincro_nube.hay_cambios_sin_subir():
                    return
                hilo = sincro_nube.lanzar_en_segundo_plano()
            hilo.join(SEGUNDOS_ESPERA_AL_CERRAR)
        except Exception as ex:      # noqa: BLE001  (nada de esto debe impedir cerrar)
            print(f"Sincronización con la nube: no se pudo subir lo último al cerrar ({ex})")

    def _vigilar_cambios_nube(self):
        """Cada pocos segundos: si hay cambios sin subir y toca, sincroniza ya."""
        if time.monotonic() < getattr(self, "_proximo_intento_nube", 0.0):
            return
        if nube.sesion() is None:
            return
        hilo = getattr(self, "_hilo_nube", None)
        if hilo is not None and hilo.is_alive():
            return
        if sincro_nube.hay_cambios_sin_subir():
            self._tic_nube()

    def _tic_nube(self):
        if nube.sesion() is None:
            return
        hilo = getattr(self, "_hilo_nube", None)
        if hilo is not None and hilo.is_alive():
            return
        self._hilo_nube = sincro_nube.lanzar_en_segundo_plano(al_terminar=self._guardar_resultado_nube)

    def _guardar_resultado_nube(self, resultado, error):
        """Lo llama el hilo de fondo: solo guarda el resultado (nada de tocar la interfaz desde aquí)."""
        self._resultado_nube = (resultado, error)
        # Si ha fallado (sin internet, licencia caducada...) el vigilante espera un rato antes de volver a probar
        self._proximo_intento_nube = time.monotonic() + (SEGUNDOS_ESPERA_TRAS_ERROR if error else 0.0)

    def _comprobar_cuenta_nube(self):
        """En un hilo: pregunta la licencia y el espacio y deja los avisos para la ventana."""
        if nube.sesion() is None:
            return

        def trabajo():
            datos, _error = nube.comprobar_licencia()
            # sin conexión: lo último que se sabía (la licencia también caduca sin conexión)
            self._avisos_cuenta = nube.avisos(datos or nube.sesion())
        threading.Thread(target=trabajo, daemon=True).start()

    def _mostrar_avisos_cuenta(self, codigos):
        """Aviso emergente de licencia o espacio, solo a administradores y una vez al día por aviso."""
        from ...nucleo import usuarios
        if not codigos or not usuarios.es_admin():
            return
        ajustes = QSettings("MyCompany", "MantenimientoApp")
        hoy = date.today().isoformat()
        nuevos = [c for c in codigos if ajustes.value(f"nube/aviso_{c}", "") != hoy]
        if not nuevos:
            return
        for c in nuevos:
            ajustes.setValue(f"nube/aviso_{c}", hoy)
        from ..dialogos.nube import mostrar_avisos_cuenta
        mostrar_avisos_cuenta(self, nuevos)

    def _revisar_resultado_nube(self):
        """En el hilo de la ventana: recoge el resultado de la sincronización de fondo."""
        avisos_cuenta, self._avisos_cuenta = getattr(self, "_avisos_cuenta", None), None
        if avisos_cuenta:
            self._mostrar_avisos_cuenta(avisos_cuenta)
        recogido, self._resultado_nube = self._resultado_nube, None
        if recogido is None:
            return
        resultado, error = recogido
        if error in ERRORES_DE_CUENTA:
            # La nube no deja subir: hay que pagar o comprar espacio
            codigos = nube.avisos(nube.sesion())
            if ERRORES_DE_CUENTA[error] and ERRORES_DE_CUENTA[error] not in codigos:
                codigos = [c for c in codigos if not c.startswith("espacio_")] + [ERRORES_DE_CUENTA[error]]
            self._mostrar_avisos_cuenta(codigos)
            return
        if error in (sincro_nube.NUBE_CON_DATOS, sincro_nube.COPIA_RESTAURADA):
            if not self._aviso_decision_mostrado:        # una vez por sesión: no insistir cada 10 minutos
                self._aviso_decision_mostrado = True
                self.statusBar().showMessage(tt("msg_nube_necesita_decision",
                                                "MantPro Cloud necesita tu decisión: Herramientas → MantPro Cloud…"), 20000)
            return
        if not resultado:
            return
        if resultado.get("aplicados") or resultado.get("borrados"):
            self.refrescar_tras_nube()
        negativos = resultado.get("stock_negativo") or []
        if negativos:
            lista = "\n".join(f"• {x.get('nombre') or x.get('codigo')}: {x.get('stock'):g}" for x in negativos[:10])
            QMessageBox.warning(self, tt("title_nube", "MantPro Cloud"),
                                tt("msg_nube_stock_negativo", "Tras sincronizar, estos artículos han quedado con stock NEGATIVO. "
                                   "Haz un recuento urgente:\n\n{lista}").format(lista=lista))

    def refrescar_tras_nube(self):
        """Repinta la ventana con lo que ha llegado de la nube."""
        for nombre in ("refresh_all", "pintar_calendario", "update_calendar_list", "refresh_avisos", "refresh_todos", "refresh_stock"):
            funcion = getattr(self, nombre, None)
            if funcion is not None:
                try:
                    funcion()
                except Exception as ex:      # noqa: BLE001  (un repintado que falla no debe romper la sincronización)
                    print(f"Sincronización con la nube: no se pudo repintar ({nombre}: {ex})")
