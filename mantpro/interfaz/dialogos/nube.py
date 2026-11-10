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

"""Herramientas > MantPro Cloud: iniciar sesión con la cuenta de la nube y ver la licencia."""

import socket

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
                             QFormLayout, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices

from ...idiomas import t, formato_fecha_localizada
from ..comun import tt
from ...nucleo import nube, sincro_nube

_ERRORES = {
    "empresa_distinta": ("nube_error_empresa",
                         "Este PC ya se sincroniza con otra empresa de MantPro Cloud. No se pueden mezclar los datos de "
                         "dos empresas: inicia sesión con la cuenta de siempre."),
    "licencia_caducada": ("nube_error_licencia_caducada",
                          "La licencia ha caducado: puedes consultar tus datos, pero no subir cambios. "
                          "Renuévala para volver a sincronizar."),
    "licencia_suspendida": ("nube_error_licencia_suspendida",
                            "La cuenta está suspendida y no se puede sincronizar. Contacta con MantPro Cloud."),
    "almacenamiento_lleno": ("nube_error_espacio",
                             "Se ha llenado el espacio de tu plan en MantPro Cloud. Libera espacio o cambia de plan."),
    "ocupado": ("nube_error_ocupado", "Ya hay una sincronización en marcha."),
    "copia_fallida": ("nube_error_copia",
                      "No se ha podido hacer la copia de seguridad antes de cambiar tus datos, así que no se ha tocado nada."),
    "nube_con_datos": ("msg_nube_necesita_decision", "MantPro Cloud necesita tu decisión: Herramientas → MantPro Cloud…"),
    "copia_restaurada": ("msg_nube_necesita_decision", "MantPro Cloud necesita tu decisión: Herramientas → MantPro Cloud…"),
    "bd_no_disponible": ("nube_error_bd",
                         "No se han podido abrir las bases de datos para sincronizar. Inténtalo de nuevo en unos segundos."),
    "bd_ocupada": ("nube_error_bd",
                   "No se han podido abrir las bases de datos para sincronizar. Inténtalo de nuevo en unos segundos."),
    "sin_conexion": ("nube_error_sin_conexion",
                     "No se puede conectar con MantPro Cloud. Comprueba tu conexión a internet e inténtalo de nuevo."),
    "respuesta_no_valida": ("nube_error_respuesta",
                            "MantPro Cloud ha respondido algo inesperado. Inténtalo más tarde."),
    "credenciales": ("nube_error_credenciales", "Correo o contraseña incorrectos."),
    "demasiados_intentos": ("nube_error_intentos",
                            "Demasiados intentos fallidos. Espera 15 minutos antes de volver a probar."),
    "datos_incompletos": ("nube_error_datos", "Escribe el correo y la contraseña."),
    "url_no_valida": ("nube_error_url", "La dirección de MantPro Cloud no es segura (debe ser HTTPS)."),
    "sesion_caducada": ("nube_error_sesion",
                        "La sesión de MantPro Cloud ha caducado o se ha cerrado. Vuelve a iniciar sesión."),
    "sin_sesion": ("nube_error_sin_sesion", "No hay ninguna sesión iniciada."),
}

_ESTADOS = {
    "activa": ("nube_estado_activa", "Activa"),
    "gracia": ("nube_estado_gracia", "Caducada, en margen de gracia"),
    "vencida": ("nube_estado_vencida", "Caducada"),
    "suspendida": ("nube_estado_suspendida", "Suspendida"),
    "desconocida": ("nube_estado_desconocida", "Desconocido"),
}

_PLANES = {
    "prueba": ("nube_plan_prueba", "Prueba"),
    "pequena": ("nube_plan_pequena", "Pequeña empresa"),
    "empresa": ("nube_plan_empresa", "Empresa"),
}


def texto_error(codigo):
    """Traduce un código de error de la nube al idioma activo."""
    clave, defecto = _ERRORES.get(codigo, ("nube_error_otro", "No se ha podido completar la operación."))
    return tt(clave, defecto)


class _Hilo(QThread):
    """Ejecuta una función de red fuera del hilo de la ventana. Emite (resultado, código_error)."""
    terminado = pyqtSignal(object, object)

    def __init__(self, funcion, parent=None):
        super().__init__(parent)
        self._funcion = funcion

    def run(self):
        try:
            resultado, error = self._funcion()
        except Exception:
            resultado, error = None, "respuesta_no_valida"
        self.terminado.emit(resultado, error)


class DialogoNube(QDialog):
    """Sin sesión: formulario de acceso. Con sesión: cuenta, empresa y licencia."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tt("title_nube", "MantPro Cloud"))
        self.setModal(True)
        self.setMinimumWidth(460)
        self._hilo = None
        self._sincronizando = False
        self.boton_entrar = self.boton_comprobar = self.boton_salir_sesion = self.aviso = None
        self.boton_sincronizar = self.boton_recuperar = None
        self._layout = QVBoxLayout(self)
        self._construir()

    # ------------------------------------------------------------ construcción
    def _vaciar(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            elif item.layout() is not None:
                self._vaciar_layout(item.layout())

    def _vaciar_layout(self, lay):
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            elif item.layout() is not None:
                self._vaciar_layout(item.layout())

    def _construir(self):
        self._vaciar()
        # Los botones y el aviso de la vista anterior ya no existen
        self.boton_entrar = self.boton_comprobar = self.boton_salir_sesion = self.aviso = None
        self.boton_sincronizar = self.boton_recuperar = None
        datos = nube.sesion()
        if datos:
            self._construir_con_sesion(datos)
        else:
            self._construir_sin_sesion()

    def _boton_web(self):
        """Botón que abre la web de MantPro Cloud en el navegador (contratar, renovar, información)."""
        b = QPushButton("🌐 " + tt("btn_nube_web", "Abrir la web"))
        b.setAutoDefault(False)
        b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(nube.URL_WEB)))
        return b

    def _etiqueta(self, texto, negrita=False):
        lbl = QLabel(texto)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        if negrita:
            lbl.setStyleSheet("font-weight: bold;")
        return lbl

    def _construir_sin_sesion(self):
        l = self._layout
        l.addWidget(self._etiqueta("☁️ " + tt("lbl_nube_sin_sesion", "Este PC no está conectado a MantPro Cloud."), True))
        l.addWidget(self._etiqueta(tt("lbl_nube_info",
            "MantPro Cloud guarda tus datos en la nube y los mantiene al día entre varios PCs y los móviles, "
            "aunque no estén en la misma red. Inicia sesión con la cuenta que te dimos al contratarlo.\n\n"
            "MantPro sigue funcionando igual en este PC sin la nube: si no inicias sesión, no cambia nada.")))
        form = QFormLayout()
        self.campo_correo = QLineEdit()
        self.campo_correo.setPlaceholderText(tt("nube_correo", "Correo"))
        self.campo_password = QLineEdit()
        self.campo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_password.setPlaceholderText(tt("nube_password", "Contraseña"))
        form.addRow(tt("nube_correo", "Correo") + ":", self.campo_correo)
        form.addRow(tt("nube_password", "Contraseña") + ":", self.campo_password)
        l.addLayout(form)
        self.aviso = self._etiqueta("")
        self.aviso.setStyleSheet("color: #c62828;")
        l.addWidget(self.aviso)

        botones = QHBoxLayout()
        self.boton_cerrar = QPushButton(t("btn_cerrar"))
        self.boton_cerrar.clicked.connect(self.reject)
        self.boton_entrar = QPushButton(tt("btn_nube_iniciar", "Iniciar sesión"))
        self.boton_entrar.setDefault(True)
        self.boton_entrar.clicked.connect(self._iniciar)
        self.campo_password.returnPressed.connect(self._iniciar)
        self.campo_correo.returnPressed.connect(self.campo_password.setFocus)
        botones.addWidget(self.boton_cerrar)
        botones.addWidget(self._boton_web())
        botones.addStretch()
        botones.addWidget(self.boton_entrar)
        l.addLayout(botones)
        self.campo_correo.setFocus()

    def _construir_con_sesion(self, datos):
        l = self._layout
        lic = datos.get("licencia") or {}
        efectivo = nube.estado_efectivo(lic)
        icono = {"activa": "✅", "gracia": "⚠️", "vencida": "⛔", "suspendida": "⛔"}.get(efectivo, "❔")
        l.addWidget(self._etiqueta("☁️ " + tt("lbl_nube_conectado", "Este PC está conectado a MantPro Cloud."), True))

        form = QFormLayout()
        empresa = datos.get("empresa") or {}
        cuenta = datos.get("cuenta") or {}
        form.addRow(tt("nube_empresa", "Empresa") + ":", self._etiqueta(empresa.get("nombre", "")))
        form.addRow(tt("nube_cuenta", "Cuenta") + ":",
                    self._etiqueta(f"{cuenta.get('nombre', '')} ({cuenta.get('correo', '')})"))
        plan = lic.get("plan")
        clave_plan, defecto_plan = _PLANES.get(plan, ("", plan or ""))
        form.addRow(tt("nube_plan", "Plan") + ":", self._etiqueta(tt(clave_plan, defecto_plan) if clave_plan else defecto_plan))
        clave_e, defecto_e = _ESTADOS[efectivo]
        form.addRow(tt("nube_licencia", "Licencia") + ":", self._etiqueta(f"{icono} {tt(clave_e, defecto_e)}"))
        hasta = lic.get("valida_hasta")
        if hasta:
            dias = nube.dias_restantes(lic)
            texto = formato_fecha_localizada(hasta)
            if dias is not None and dias >= 0:
                texto += " (" + tt("nube_dias_restantes", "{n} días restantes").format(n=dias) + ")"
            form.addRow(tt("nube_valida_hasta", "Válida hasta") + ":", self._etiqueta(texto))
        comprobada = (datos.get("comprobada") or "")[:10]
        if comprobada:
            form.addRow(tt("nube_comprobada", "Última comprobación") + ":",
                        self._etiqueta(formato_fecha_localizada(comprobada)))
        l.addLayout(form)

        mensaje = {
            "gracia": tt("lbl_nube_gracia",
                "La licencia ha caducado. Renuévala antes de que termine el margen de gracia para no perder la sincronización."),
            "vencida": tt("lbl_nube_vencida",
                "La licencia ha caducado y este PC ya no sincroniza con la nube. MantPro sigue funcionando en local con tus "
                "datos y puedes exportarlos cuando quieras. Renueva la licencia para volver a sincronizar."),
            "suspendida": tt("lbl_nube_suspendida",
                "La cuenta está suspendida. MantPro sigue funcionando en local con tus datos. Contacta con MantPro Cloud."),
        }.get(efectivo)
        if mensaje:
            aviso_lic = self._etiqueta(mensaje)
            aviso_lic.setStyleSheet("color: #b26a00;")
            l.addWidget(aviso_lic)

        self._construir_sincronizacion(l)

        self.aviso = self._etiqueta("")
        l.addWidget(self.aviso)

        botones = QHBoxLayout()
        self.boton_salir_sesion = QPushButton(tt("btn_nube_cerrar_sesion", "Cerrar sesión"))
        self.boton_salir_sesion.clicked.connect(self._cerrar_sesion)
        self.boton_sincronizar = QPushButton(tt("btn_nube_sincronizar", "Sincronizar ahora"))
        self.boton_sincronizar.setAutoDefault(False)
        self.boton_sincronizar.clicked.connect(lambda: self._sincronizar())
        self.boton_comprobar = QPushButton(tt("btn_nube_comprobar", "Comprobar ahora"))
        self.boton_comprobar.clicked.connect(self._comprobar)
        self.boton_cerrar = QPushButton(t("btn_cerrar"))
        self.boton_cerrar.setDefault(True)
        self.boton_cerrar.clicked.connect(self.accept)
        botones.addWidget(self.boton_salir_sesion)
        botones.addWidget(self._boton_web())
        botones.addStretch()
        botones.addWidget(self.boton_sincronizar)
        botones.addWidget(self.boton_comprobar)
        botones.addWidget(self.boton_cerrar)
        l.addLayout(botones)

    def _construir_sincronizacion(self, l):
        """Estado de la subida de datos: última vez, qué queda sin subir y avisos."""
        estado = sincro_nube.resumen_estado()
        l.addWidget(self._etiqueta(tt("lbl_nube_sync_titulo", "Sincronización"), True))
        form = QFormLayout()
        ultima = estado.get("ultima_subida")
        form.addRow(tt("nube_ultima_subida", "Última subida") + ":", self._etiqueta(
            f"{formato_fecha_localizada(ultima[:10])} {ultima[11:16]}" if ultima else tt("nube_nunca", "Todavía no")))
        bajada = estado.get("ultima_bajada")
        if bajada:
            form.addRow(tt("nube_ultima_bajada", "Última descarga") + ":",
                        self._etiqueta(f"{formato_fecha_localizada(bajada[:10])} {bajada[11:16]}"))
        pendientes = estado.get("pendientes")
        if estado.get("activa") and pendientes is not None:
            form.addRow(tt("nube_sin_subir", "Sin subir") + ":", self._etiqueta(
                tt("nube_al_dia", "Todo al día") if pendientes == 0 else str(pendientes)))
        l.addLayout(form)
        l.addWidget(self._etiqueta(tt("lbl_nube_fotos_aparte",
            "Se sincronizan los datos; las fotos todavía no. MantPro sube y recibe lo nuevo solo cada 10 minutos mientras está abierto.")))
        if estado.get("restaurada"):
            aviso_r = self._etiqueta(tt("lbl_nube_restaurada",
                "Sincronización parada: se ha restaurado una copia de seguridad. Recupera los datos de la nube para continuar."))
            aviso_r.setStyleSheet("color: #b26a00;")
            l.addWidget(aviso_r)
            self.boton_recuperar = QPushButton(tt("btn_nube_recuperar", "Recuperar de la nube"))
            self.boton_recuperar.setAutoDefault(False)
            self.boton_recuperar.clicked.connect(self._recuperar)
            l.addWidget(self.boton_recuperar)
        if estado.get("omitidos"):
            omitidos = self._etiqueta(tt("lbl_nube_omitidos",
                "Atención: {n} registros eran demasiado grandes y no se han podido subir.").format(n=estado["omitidos"]))
            omitidos.setStyleSheet("color: #b26a00;")
            l.addWidget(omitidos)

    # ------------------------------------------------------------ acciones
    def _ocupado(self, ocupado, mensaje=""):
        for nombre in ("boton_entrar", "boton_comprobar", "boton_salir_sesion", "boton_sincronizar", "boton_recuperar"):
            w = getattr(self, nombre, None)
            if w is not None:
                w.setEnabled(not ocupado)
        if self.aviso is not None:
            self.aviso.setStyleSheet("")
            self.aviso.setText(mensaje)

    def _hilo_libre(self):
        """True si no hay otra petición en curso. Una señal de «terminado» llega cuando el hilo está
        acabando: se le da un momento para salir del todo, o una acción encadenada (sincronizar tras
        iniciar sesión, o tras aceptar «Usar los de la nube») se descartaría sin avisar."""
        if self._hilo is not None and self._hilo.isRunning():
            self._hilo.wait(3000)
        return self._hilo is None or not self._hilo.isRunning()

    def _lanzar(self, funcion, al_terminar, mensaje):
        if not self._hilo_libre():
            return
        self._ocupado(True, mensaje)
        self._hilo = _Hilo(funcion, self)
        self._hilo.terminado.connect(al_terminar)
        self._hilo.start()

    def _iniciar(self):
        correo = self.campo_correo.text()
        password = self.campo_password.text()
        self._lanzar(lambda: nube.iniciar_sesion(correo, password, dispositivo=socket.gethostname()),
                     self._tras_iniciar, tt("lbl_nube_conectando", "Conectando…"))

    def _tras_iniciar(self, datos, error):
        if error:
            self._ocupado(False)
            self.aviso.setStyleSheet("color: #c62828;")
            self.aviso.setText(texto_error(error))
            self.campo_password.clear()
            self.campo_password.setFocus()
            return
        # Un PC solo se sincroniza con UNA empresa: otra cuenta se rechaza antes de tocar nada
        empresa = ((datos or {}).get("empresa") or {}).get("uuid")
        rechazo = sincro_nube.comprobar_empresa(empresa) if empresa else None
        if rechazo:
            nube.cerrar_sesion()
            self._construir()
            self.aviso.setStyleSheet("color: #c62828;")
            self.aviso.setText(texto_error(rechazo))
            return
        self._construir()
        self._sincronizar()

    def _sincronizar(self, adoptar=False):
        """Baja lo de la nube y sube lo de este PC ahora (la primera vez, todo lo que ya hay). [adoptar]:
        sustituye lo de este PC por lo de la nube, con copia de seguridad previa (lo pide el usuario).
        No se puede cerrar el diálogo mientras tanto."""
        if not self._hilo_libre():
            return
        self._sincronizando = True
        self.boton_cerrar.setEnabled(False)
        self._lanzar(lambda: sincro_nube.sincronizar_ahora(adoptar=adoptar), self._tras_sincronizar,
                     tt("lbl_nube_sincronizando", "Sincronizando…"))

    def _preguntar(self, texto, texto_si):
        """Pregunta con dos botones: [texto_si] y «Ahora no». True si se elige el primero."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tt("title_nube", "MantPro Cloud"))
        msg.setText(texto)
        btn_si = msg.addButton(texto_si, QMessageBox.ButtonRole.YesRole)
        msg.addButton(tt("btn_nube_ahora_no", "Ahora no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        return msg.clickedButton() == btn_si

    def _avisar(self, texto):
        QMessageBox.warning(self, tt("title_nube", "MantPro Cloud"), texto)

    def _refrescar_ventana(self):
        """Tras bajar datos de la nube, repinta la ventana principal con lo nuevo."""
        refrescar = getattr(self.parent(), "refrescar_tras_nube", None)
        if refrescar:
            refrescar()

    def _recuperar(self):
        if self._preguntar(tt("msg_nube_restaurada",
                "Parece que has restaurado una copia de seguridad antigua de este PC. Para no duplicar datos, la "
                "sincronización está parada.\n\n¿Quieres recuperar los datos de la nube? Los de este PC se sustituirán "
                "por los de la nube (se hace antes una copia de seguridad)."),
                tt("btn_nube_recuperar", "Recuperar de la nube")):
            self._sincronizar(adoptar=True)

    def _tras_sincronizar(self, resultado, error):
        self._sincronizando = False
        if error == "sesion_caducada":
            self._construir()
            QMessageBox.information(self, tt("title_nube", "MantPro Cloud"), texto_error(error))
            return
        if error == "ocupado":
            error = None        # ya hay una subida en marcha (la del temporizador): no es un fallo
            resultado = None
        self._construir()
        if error == sincro_nube.NUBE_CON_DATOS:
            if self._preguntar(tt("msg_nube_con_datos",
                    "La cuenta de MantPro Cloud ya tiene datos y este PC también tiene los suyos. Para no mezclarlos, "
                    "no se ha sincronizado nada.\n\n¿Quieres usar los datos de la nube? Los de este PC se sustituirán "
                    "por los de la nube (se hace antes una copia de seguridad)."),
                    tt("btn_nube_adoptar", "Usar los de la nube")):
                self._sincronizar(adoptar=True)
            return
        if error == sincro_nube.COPIA_RESTAURADA:
            self._recuperar()
            return
        if error:
            self.aviso.setStyleSheet("color: #c62828;")
            self.aviso.setText(texto_error(error))
            return
        if resultado is None:
            return
        subidos, bajados = resultado.get("enviados", 0), resultado.get("aplicados", 0)
        if resultado.get("adoptado"):
            texto = tt("msg_nube_adoptado", "Datos de la nube recibidos: {n} registros.\n\nCierra MantPro y vuelve a "
                       "abrirlo para empezar con ellos (tendrás que iniciar sesión de nuevo).").format(n=bajados)
        else:
            partes = []
            if subidos:
                partes.append(tt("msg_nube_sync_ok", "Sincronizado: {n} registros subidos.").format(n=subidos))
            if bajados:
                partes.append(tt("msg_nube_sync_bajada", "Recibidos de la nube: {n} registros.").format(n=bajados))
            texto = " ".join(partes) or tt("msg_nube_sync_al_dia", "Todo al día: no había nada nuevo que subir.")
        sin_aplicar = resultado.get("rechazados", 0) + resultado.get("refs_vacias", 0)
        if sin_aplicar:
            texto += " " + tt("lbl_nube_aviso_bajada", "{n} registros de la nube no se han podido aplicar del todo.").format(n=sin_aplicar)
        self.aviso.setText(texto)
        if bajados or resultado.get("borrados"):
            self._refrescar_ventana()
        negativos = resultado.get("stock_negativo") or []
        if negativos:
            lista = "\n".join(f"• {x.get('nombre') or x.get('codigo')}: {x.get('stock'):g}" for x in negativos[:10])
            self._avisar(tt("msg_nube_stock_negativo", "Tras sincronizar, estos artículos han quedado con stock NEGATIVO. "
                            "Haz un recuento urgente:\n\n{lista}").format(lista=lista))

    def _comprobar(self):
        self._lanzar(nube.comprobar_licencia, self._tras_comprobar,
                     tt("lbl_nube_comprobando", "Comprobando…"))

    def _tras_comprobar(self, datos, error):
        if error == "sesion_caducada":
            self._construir()
            QMessageBox.information(self, tt("title_nube", "MantPro Cloud"), texto_error(error))
            return
        if error:
            self._ocupado(False)
            self.aviso.setStyleSheet("color: #c62828;")
            self.aviso.setText(texto_error(error))
            return
        self._construir()

    def _cerrar_sesion(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(tt("title_nube", "MantPro Cloud"))
        msg.setText(tt("msg_nube_confirmar_cerrar",
            "¿Cerrar la sesión de MantPro Cloud en este PC?\n\nTus datos de mantenimiento no se tocan: "
            "MantPro sigue funcionando en local."))
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() != btn_si:
            return
        self._lanzar(lambda: (nube.cerrar_sesion(), None), lambda *_: self._construir(),
                     tt("lbl_nube_cerrando", "Cerrando sesión…"))

    def done(self, resultado):
        # Una subida puede tardar (la primera, todo lo que ya hay): hasta que acabe no se cierra
        # (Esc o la X también llegan aquí) y así el hilo nunca toca una ventana ya destruida.
        if self._sincronizando:
            return
        # No cerrar mientras hay una petición en curso (el hilo seguiría tocando la ventana)
        if self._hilo is not None and self._hilo.isRunning():
            self._hilo.wait(nube.TIMEOUT * 1000 + 2000)
        super().done(resultado)
