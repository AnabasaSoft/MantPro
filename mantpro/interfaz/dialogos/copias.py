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

"""Archivo > Copias automáticas: cuándo se hacen, cuántas se guardan, la
carpeta externa y el estado (última copia, última prueba de restauración)."""

import html
import os
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QDialogButtonBox,
                             QSpinBox, QCheckBox, QGroupBox, QLineEdit, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ...nucleo import copias


def fecha_hora(iso):
    """«04/11/2026 10:42» (en euskera, «2026/11/04 10:42») de una fecha ISO."""
    if not iso:
        return "—"
    return f"{idiomas.formato_fecha_localizada(iso[:10])} {iso[11:16]}".strip()


def nombre_motivo(motivo):
    return {
        "cierre": tt("motivo_copia_cierre", "al cerrar"),
        "periodica": tt("motivo_copia_periodica", "periódica"),
        "movil": tt("motivo_copia_movil", "tras recibir datos de un móvil"),
        "arranque": tt("motivo_copia_arranque", "al abrir"),
        "manual": tt("motivo_copia_manual", "hecha a mano"),
    }.get(motivo, motivo or "")


def textos_problemas(lista, estado=None):
    """Texto de cada problema de copias.problemas(), para mostrarlo."""
    estado = estado if estado is not None else copias.leer_estado()
    ultima = estado.get("ultima", {})
    prueba = estado.get("prueba", {})
    destino = estado.get("destino", {})
    textos = []
    for codigo in lista:
        if codigo == "copia_fallida":
            textos.append(tt("msg_copia_fallida", "La última copia automática ({fecha}) ha fallado:\n{error}").format(
                fecha=fecha_hora(ultima.get("fecha")), error=ultima.get("error", "")))
        elif codigo == "prueba_fallida":
            donde = tt("lbl_en_carpeta_externa", "en la carpeta externa") if prueba.get("donde") == "destino" \
                else tt("lbl_en_este_equipo", "en este equipo")
            textos.append(tt("msg_prueba_restauracion_fallida",
                             "La prueba de restauración de la última copia {donde} ({fecha}) ha fallado: la copia no se podría restaurar entera.\n{detalle}").format(
                donde=donde, fecha=fecha_hora(prueba.get("fecha")), detalle="\n".join(prueba.get("detalle", [])[:5])))
        elif codigo == "destino_fallido":
            textos.append(tt("msg_destino_copias_fallido",
                             "No se ha podido guardar la copia en la carpeta externa {ruta} ({fecha}). Comprueba que el disco USB o el NAS está conectado.\n{error}").format(
                ruta=destino.get("ruta", ""), fecha=fecha_hora(destino.get("fecha_error")), error=destino.get("error", "")))
        elif codigo == "sin_copia":
            textos.append(tt("msg_sin_copia_buena", "Todavía no hay ninguna copia automática buena."))
    return textos


class DialogoCopiasAutomaticas(QDialog):
    """Configuración y estado de las copias automáticas. [lanzar(accion,
    config, al_terminar)] hace una copia ("copia") o prueba la última
    ("probar") en segundo plano con la configuración del diálogo."""

    def __init__(self, parent, carpeta_copias, lanzar):
        super().__init__(parent)
        self.setWindowTitle(tt("title_copias_automaticas", "Copias automáticas"))
        self.setMinimumWidth(620)
        self.carpeta_copias = carpeta_copias
        self.lanzar = lanzar
        config = copias.leer_config()
        l = QVBoxLayout()

        # --- Cuándo
        g = QGroupBox(tt("grp_cuando_copia", "Cuándo se hacen")); lg = QVBoxLayout()
        lbl = QLabel(tt("lbl_copia_siempre_al_cerrar",
                        "Siempre al cerrar MantPro y al abrirlo si quedaron cambios sin copiar. Además:"))
        lbl.setWordWrap(True); lg.addWidget(lbl)
        fila = QHBoxLayout()
        self.chk_periodica = QCheckBox(tt("chk_copia_periodica", "Mientras MantPro está abierto, cada"))
        self.chk_periodica.setChecked(bool(config["periodica"]))
        self.spin_horas = QSpinBox(); self.spin_horas.setRange(1, 24); self.spin_horas.setValue(config["horas"])
        self.spin_horas.setSuffix(" " + tt("sufijo_horas", "h"))
        self.chk_periodica.toggled.connect(self.spin_horas.setEnabled); self.spin_horas.setEnabled(self.chk_periodica.isChecked())
        fila.addWidget(self.chk_periodica); fila.addWidget(self.spin_horas)
        fila.addWidget(QLabel(tt("lbl_si_hay_cambios", "(solo si ha habido cambios)"))); fila.addStretch()
        lg.addLayout(fila)
        self.chk_movil = QCheckBox(tt("chk_copia_tras_movil",
                                      "Al poco de recibir datos de un móvil (10 minutos después del último envío)"))
        self.chk_movil.setChecked(bool(config["tras_movil"]))
        lg.addWidget(self.chk_movil)
        g.setLayout(lg); l.addWidget(g)

        # --- Cuántas
        g = QGroupBox(tt("grp_copias_guardadas", "Copias que se guardan")); lg = QHBoxLayout()
        lg.addWidget(QLabel(tt("lbl_conservar_ultimas", "Las últimas")))
        self.spin_recientes = QSpinBox(); self.spin_recientes.setRange(1, 100); self.spin_recientes.setValue(config["conservar_recientes"])
        lg.addWidget(self.spin_recientes)
        lg.addWidget(QLabel(tt("lbl_conservar_y_dias", "y, además, una de cada día de los últimos")))
        self.spin_dias = QSpinBox(); self.spin_dias.setRange(0, 365); self.spin_dias.setValue(config["conservar_dias"])
        lg.addWidget(self.spin_dias); lg.addWidget(QLabel(tt("lbl_dias", "días"))); lg.addStretch()
        g.setToolTip(tt("lbl_nota_copias_fotos",
                         "Se refiere a las copias de las bases de datos. Las fotos se guardan una sola vez, en ZIP por meses, y solo se añaden las nuevas."))
        g.setLayout(lg); l.addWidget(g)

        # --- Carpeta externa
        g = QGroupBox(tt("grp_carpeta_externa", "Copia también en otra carpeta")); lg = QVBoxLayout()
        lbl = QLabel(tt("lbl_explica_carpeta_externa",
                        "Un NAS, un disco USB o una carpeta que se sincroniza con la nube (Nextcloud, Dropbox, Google Drive…). "
                        "Una copia en el mismo disco que los datos no sirve si el disco falla."))
        lbl.setWordWrap(True); lg.addWidget(lbl)
        fila = QHBoxLayout()
        self.txt_destino = QLineEdit(config["destino"]); self.txt_destino.setReadOnly(True)
        self.txt_destino.setPlaceholderText(tt("ph_sin_carpeta_externa", "Sin carpeta externa"))
        btn_elegir = QPushButton(tt("btn_elegir_carpeta", "Elegir…")); btn_elegir.clicked.connect(self._elegir_destino)
        btn_quitar = QPushButton(tt("btn_quitar", "Quitar")); btn_quitar.clicked.connect(lambda: self._poner_destino(""))
        fila.addWidget(self.txt_destino, 1); fila.addWidget(btn_elegir); fila.addWidget(btn_quitar)
        lg.addLayout(fila)
        self.lbl_mismo_disco = QLabel(tt("lbl_aviso_mismo_disco",
                                         "⚠️ Esta carpeta está en el mismo disco que los datos de MantPro: solo sirve si se sincroniza con otro sitio (Nextcloud, Dropbox…)."))
        self.lbl_mismo_disco.setWordWrap(True); self.lbl_mismo_disco.setStyleSheet("color: #e67e22;")
        lg.addWidget(self.lbl_mismo_disco)
        g.setLayout(lg); l.addWidget(g)
        self._poner_destino(config["destino"])

        # --- Estado
        g = QGroupBox(tt("grp_estado_copias", "Estado")); lg = QVBoxLayout()
        # Una etiqueta por línea («Título: valor»): los errores y las rutas
        # largas se parten en varias líneas sin descuadrar el diálogo
        self.lbl_ultima = QLabel(); self.lbl_buena = QLabel(); self.lbl_prueba = QLabel()
        self.lbl_destino = QLabel(); self.lbl_carpeta = QLabel()
        for w in (self.lbl_ultima, self.lbl_buena, self.lbl_prueba, self.lbl_destino, self.lbl_carpeta):
            w.setWordWrap(True); w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lg.addWidget(w)
        self.lbl_carpeta.setText(self._fila(tt("lbl_carpeta_copias_local", "Carpeta de las copias en este equipo:"), carpeta_copias))
        fila = QHBoxLayout()
        self.btn_copia = QPushButton(tt("btn_copia_ahora", "💾 Hacer copia ahora"))
        self.btn_probar = QPushButton(tt("btn_probar_restauracion", "🧪 Probar restauración ahora"))
        self.btn_copia.clicked.connect(lambda: self._lanzar("copia"))
        self.btn_probar.clicked.connect(lambda: self._lanzar("probar"))
        fila.addWidget(self.btn_copia); fila.addWidget(self.btn_probar); fila.addStretch()
        lg.addLayout(fila)
        self.lbl_trabajando = QLabel(); lg.addWidget(self.lbl_trabajando)
        self.btn_probar.setToolTip(tt("lbl_explica_prueba_restauracion",
                            "Después de cada copia se prueba que se puede restaurar: se sacan las bases de datos de la copia "
                            "(también de la carpeta externa), se abren y se comprueban, se mira que estén todas las fotos y se leen "
                            "unas cuantas al azar. Los datos de verdad no se tocan."))
        g.setLayout(lg); l.addWidget(g)
        self._pintar_estado()

        b = QDialogButtonBox()
        b.addButton(t("btn_guardar"), QDialogButtonBox.ButtonRole.AcceptRole)
        b.addButton(t("btn_cancelar"), QDialogButtonBox.ButtonRole.RejectRole)
        b.accepted.connect(self._guardar); b.rejected.connect(self.reject)
        l.addWidget(b)
        self.setLayout(l)

    # ------------------------------------------------------------------
    def config(self):
        return {"periodica": self.chk_periodica.isChecked(), "horas": self.spin_horas.value(),
                "tras_movil": self.chk_movil.isChecked(), "destino": self.txt_destino.text().strip(),
                "conservar_recientes": self.spin_recientes.value(), "conservar_dias": self.spin_dias.value()}

    def _elegir_destino(self):
        carpeta = QFileDialog.getExistingDirectory(self, tt("title_elegir_carpeta_externa", "Carpeta externa de las copias"),
                                                   self.txt_destino.text() or os.path.expanduser("~"),
                                                   QFileDialog.Option.DontUseNativeDialog)
        if carpeta:
            self._poner_destino(carpeta)

    def _poner_destino(self, carpeta):
        self.txt_destino.setText(carpeta)
        self.lbl_mismo_disco.setVisible(bool(carpeta) and copias.mismo_disco(carpeta, self.carpeta_copias))
        if hasattr(self, "lbl_destino"):   # el estado de la carpeta externa cambia con ella
            self._pintar_estado()

    def showEvent(self, evento):
        super().showEvent(evento)
        # Después de que Qt coloque los controles con su ancho real
        QTimer.singleShot(0, self._ajustar_alto)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        if evento.oldSize().width() != evento.size().width():
            QTimer.singleShot(0, self._ajustar_alto)

    def _ajustar_alto(self):
        """Qt no cuenta, en una ventana, la altura de las etiquetas que se
        parten en varias líneas: se calcula con el ancho real, no se deja
        encoger por debajo y se crece si hace falta."""
        self.layout().activate()
        alto = self.layout().totalHeightForWidth(self.width())
        if alto <= 0:
            return
        self.setMinimumHeight(alto)
        if alto > self.height():
            self.resize(self.width(), alto)

    @staticmethod
    def _fila(titulo, valor):
        return f"<b>{html.escape(titulo)}</b> {html.escape(valor).replace(chr(10), '<br>')}"

    def _pintar_estado(self):
        estado = copias.leer_estado()
        ultima = estado.get("ultima")
        if ultima:
            texto = f"{fecha_hora(ultima.get('fecha'))} ({nombre_motivo(ultima.get('motivo'))}) "
            texto += "✅" if ultima.get("ok") else "❌ " + (ultima.get("error") or "")
        else:
            texto = "—"
        self.lbl_ultima.setText(self._fila(tt("lbl_ultima_copia", "Última copia:"), texto))
        buena = copias.ultima_copia_buena(self.carpeta_copias)
        self.lbl_buena.setText(self._fila(tt("lbl_ultima_copia_buena", "Última copia buena:"),
                                          fecha_hora(buena.isoformat()) if buena else "—"))
        prueba = estado.get("prueba")
        if prueba:
            texto = fecha_hora(prueba.get("fecha")) + " "
            texto += "✅" if prueba.get("ok") else "❌ " + "; ".join(prueba.get("detalle", [])[:3])
        else:
            texto = "—"
        self.lbl_prueba.setText(self._fila(tt("lbl_ultima_prueba", "Última prueba de restauración:"), texto))
        destino = estado.get("destino")
        if not self.txt_destino.text():
            texto = tt("ph_sin_carpeta_externa", "Sin carpeta externa")
        elif not destino or destino.get("ruta") != copias.DestinoCarpeta(self.txt_destino.text()).descripcion():
            texto = tt("lbl_destino_sin_copias_aun", "Todavía no se ha copiado nada en ella")
        elif destino.get("error"):
            texto = "❌ " + tt("lbl_destino_error", "Falló el {fecha}: {error}").format(
                fecha=fecha_hora(destino.get("fecha_error")), error=destino.get("error"))
            if destino.get("fecha_ok"):
                texto += "\n" + tt("lbl_destino_ultimo_ok", "Último envío bueno: {fecha}").format(fecha=fecha_hora(destino["fecha_ok"]))
        else:
            texto = "✅ " + tt("lbl_destino_ultimo_ok", "Último envío bueno: {fecha}").format(fecha=fecha_hora(destino.get("fecha_ok")))
        self.lbl_destino.setText(self._fila(tt("lbl_carpeta_externa", "Carpeta externa:"), texto))
        if self.isVisible():
            QTimer.singleShot(0, self._ajustar_alto)

    def _lanzar(self, accion):
        self.btn_copia.setEnabled(False); self.btn_probar.setEnabled(False)
        self.lbl_trabajando.setText(tt("lbl_haciendo_backup", "Haciendo copia de seguridad...") if accion == "copia"
                                    else tt("lbl_probando_restauracion", "Probando la restauración…"))

        def _terminado(resultado):
            self.btn_copia.setEnabled(True); self.btn_probar.setEnabled(True)
            self.lbl_trabajando.setText("")
            self._pintar_estado()
            if resultado is not None:   # None: ya había una copia en marcha
                self._mostrar_resultado(accion, resultado)

        self.lanzar(accion, self.config(), _terminado)

    def _mostrar_resultado(self, accion, resultado):
        """Ventana con el resultado de «Hacer copia ahora» o «Probar
        restauración ahora»: si ha ido bien o qué ha fallado."""
        prueba = resultado.get("prueba") or {}
        hay_destino = bool(self.txt_destino.text())
        if accion == "probar":
            titulo = tt("title_prueba_restauracion", "Prueba de restauración")
            if prueba.get("ok"):
                texto = tt("msg_prueba_ok_ambas", "✅ La última copia se puede restaurar entera, en este equipo y en la carpeta externa.") \
                    if hay_destino and prueba.get("donde") == "destino" else \
                    tt("msg_prueba_ok_local", "✅ La última copia se puede restaurar entera.")
                QMessageBox.information(self, titulo, texto)
            else:
                QMessageBox.warning(self, titulo, "\n\n".join(textos_problemas(["prueba_fallida"])))
            return
        titulo = tt("title_copia_hecha", "Copia de seguridad")
        problemas = []
        if resultado.get("error") or not resultado.get("ok") and not prueba:
            problemas.append("copia_fallida")
        if prueba and not prueba.get("ok"):
            problemas.append("prueba_fallida")
        if resultado.get("destino_error"):
            problemas.append("destino_fallido")
        if problemas:
            QMessageBox.warning(self, titulo, "\n\n".join(textos_problemas(problemas)))
        elif hay_destino:
            QMessageBox.information(self, titulo, tt("msg_copia_ok_destino",
                "✅ Copia hecha, guardada también en la carpeta externa y comprobada: se puede restaurar entera."))
        else:
            QMessageBox.information(self, titulo, tt("msg_copia_ok_local",
                "✅ Copia hecha y comprobada: se puede restaurar entera."))

    def _guardar(self):
        copias.guardar_config(self.config())
        self.accept()
