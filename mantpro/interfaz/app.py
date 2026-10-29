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

"""Ventana principal de MantPro. Cada pestaña y cada grupo de acciones del menú
está en su propio mixin (pestanas/, acciones/, temas.py), del que hereda MaintenanceApp."""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTabWidget,
                             QMessageBox, QHeaderView, QDialog, QAbstractItemView, QFileDialog,
                             QProgressBar)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction, QActionGroup, QIcon

from .. import idiomas
from ..idiomas import t
from .acciones.copias import AccionesCopias
from .acciones.exportar import AccionesExportar
from .acciones.importacion import AccionesImportacion
from .acciones.usuarios import AccionesUsuarios
from .comun import abrir_url_externa, resource_path, tt
from .dialogos.sistema import (DialogoPuertoServidor, DialogoQR, DialogoSeleccionPais,
                               DialogoSeleccionRegion)
from .festivos import GestorFestivos
from .hilos import BackupThread, ChequeadorActualizaciones
from .pestanas.avisos import PestanaAvisos
from .pestanas.calendario import PestanaCalendario
from .pestanas.dashboard import PestanaDashboard
from .pestanas.historial import PestanaHistorial
from .pestanas.maquinas import PestanaMaquinas
from .pestanas.pendientes import PestanaPendientes
from .pestanas.registrar import PestanaRegistrar
from .pestanas.stock import PestanaStock
from .servidor import PUERTO_POR_DEFECTO, ServidorSincronizacion, puerto_libre
from .temas import Temas
from ..nucleo import usuarios
from ..nucleo.basedatos import GestorBaseDatos
from ..nucleo.rutas import DATA_DIR
from ..version import APP_VERSION, GESTOR_PAQUETES

# ==========================================
# 4. APLICACIÓN PRINCIPAL
# ==========================================

class MaintenanceApp(Temas, PestanaDashboard, PestanaCalendario, PestanaRegistrar, PestanaAvisos, PestanaHistorial, PestanaPendientes, PestanaMaquinas, PestanaStock, AccionesCopias, AccionesExportar, AccionesImportacion, AccionesUsuarios, QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = GestorBaseDatos()
        # Cargamos el idioma guardado (por defecto español) antes de construir nada de la UI
        idiomas.set_idioma(self.db.get_config("idioma") or "es")
        # GestorFestivos ahora necesita la BD para saber qué región usar
        self.gestor_festivos = GestorFestivos(self.db)

        # --- USAR DATA_DIR PARA FOTOS Y BACKUPS ---
        # Pero si existen localmente, usar la ruta local (Mantener compatibilidad)
        cwd = os.path.abspath(".")

        # Lógica para fotos:
        local_fotos = os.path.join(cwd, "fotos_recibidas")
        if os.path.exists(local_fotos):
             self.carpeta_fotos = local_fotos
        else:
             self.carpeta_fotos = os.path.join(DATA_DIR, "fotos_recibidas")

        if not os.path.exists(self.carpeta_fotos): os.makedirs(self.carpeta_fotos)

        # Lógica para backups:
        local_backups = os.path.join(cwd, "backups")
        if os.path.exists(local_backups):
             self.carpeta_backups = local_backups
        else:
             self.carpeta_backups = os.path.join(DATA_DIR, "backups")

        if not os.path.exists(self.carpeta_backups): os.makedirs(self.carpeta_backups)

        # Lógica para backups auto:
        local_backups_auto = os.path.join(cwd, "backups_auto")
        if os.path.exists(local_backups_auto):
             self.carpeta_backups_auto = local_backups_auto
        else:
             self.carpeta_backups_auto = os.path.join(DATA_DIR, "backups_auto")

        if not os.path.exists(self.carpeta_backups_auto): os.makedirs(self.carpeta_backups_auto)
        # ------------------------------------------

        self.qr_dialog = None
        self.settings = QSettings("MyCompany", "MantenimientoApp")
        try: puerto = int(self.db.get_config("puerto_servidor") or PUERTO_POR_DEFECTO)
        except ValueError: puerto = PUERTO_POR_DEFECTO
        self.sincronizacion_activa = True
        if not puerto_libre(puerto):
            dlg = DialogoPuertoServidor(None, puerto, ocupado=True)
            if dlg.exec():
                puerto = dlg.puerto(); self.db.set_config("puerto_servidor", str(puerto))
            else:
                self.sincronizacion_activa = False
        self.server_thread = ServidorSincronizacion(self.carpeta_fotos, self.db.db_name, puerto)
        self.server_thread.registro_recibido.connect(self.on_registro_recibido)
        self.server_thread.pendiente_actualizado.connect(self.refresh_all)
        self.server_thread.stock_actualizado.connect(self.refresh_stock)
        self.server_thread.stock_actualizado.connect(self.refresh_stock_alertas)
        self.server_thread.error_arranque.connect(self._servidor_no_arranca)
        if self.sincronizacion_activa:
            self.server_thread.start()
        self.setWindowTitle(t("title_control_mantenimiento"))
        self.resize(1100, 750)
        g = self.settings.value("geometry")
        if g: self.restoreGeometry(g)

        # --- FIJAR EL ICONO DE LA APLICACIÓN (WAYLAND/LINUX FIX) ---
        icon_path = resource_path(os.path.join("recursos", "icono.png"))
        if os.path.exists(icon_path):
             icon = QIcon(icon_path)
             self.setWindowIcon(icon)
             QApplication.instance().setWindowIcon(icon)
        try:
            if usuarios.SESION_ACTUAL:
                self.setWindowTitle(f"{self.windowTitle()}  —  👤 {usuarios.SESION_ACTUAL['nombre']}")
        except Exception:
            pass

        self._tema_actual = QSettings("MyCompany", "MantenimientoApp").value("tema", "oscuro")
        self.crear_menu()
        self.aplicar_estilo_visual()
        cw = QWidget(); self.setCentralWidget(cw); ml = QVBoxLayout(); ml.setContentsMargins(10, 10, 10, 10); cw.setLayout(ml)
        self.tabs = QTabWidget(); ml.addWidget(self.tabs)
        self._poblar_tabs()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.refresh_all(); self.pintar_calendario(); self.update_calendar_list(); self.refresh_avisos(); self.refresh_todos(); self.setup_autocompletado()

        # NOTA: La comprobación automática de actualizaciones YA NO se lanza aquí.
        # Se dispara desde el punto de entrada (bloque __main__), una vez que la
        # ventana principal ya está visible y el splash se ha cerrado del todo,
        # para evitar la carrera de foco/apilamiento entre el splash, la ventana
        # principal y el diálogo modal de "nueva versión disponible".

    def _poblar_tabs(self):
        """Crea (o recrea) todas las pestañas dentro de self.tabs, ya existente."""
        self.tab_dashboard = QWidget(); self.init_dashboard_tab(); self.tabs.addTab(self.tab_dashboard, t("tab_dashboard"))
        self.tab_calendar = QWidget(); self.init_calendar_tab(); self.tabs.addTab(self.tab_calendar, t("tab_calendario"))
        self.tab_avisos = QWidget(); self.init_avisos_tab(); self.tabs.addTab(self.tab_avisos, t("tab_avisos"))
        self.tab_entry = QWidget(); self.init_entry_tab(); self.tabs.addTab(self.tab_entry, t("tab_registrar"))
        self.tab_history = QWidget(); self.init_history_tab(); self.tabs.addTab(self.tab_history, t("tab_historial"))
        self.tab_search = QWidget(); self.init_search_tab(); self.tabs.addTab(self.tab_search, t("tab_buscador"))
        self.tab_todo = QWidget(); self.init_todo_tab(); self.tabs.addTab(self.tab_todo, t("tab_pendientes"))
        self.tab_maquinas = QWidget(); self.init_maquinas_tab(); self.tabs.addTab(self.tab_maquinas, tt("tab_maquinas", "🏭 Máquinas"))
        self.tab_stock = QWidget(); self.init_stock_tab(); self.tabs.addTab(self.tab_stock, tt("tab_stock", "📦 Stock de almacén"))
        self.tab_stock_alertas = QWidget(); self.init_stock_alertas_tab(); self.tabs.addTab(self.tab_stock_alertas, tt("tab_stock_alertas", "⚠️ Stock bajo mínimo"))

    def recargar_interfaz_completa(self):
        """Reconstruye el menú y todas las pestañas en caliente (p.ej. tras un
        cambio de idioma), sin tener que cerrar y volver a abrir la aplicación."""
        self.menuBar().clear()
        self.crear_menu()

        titulo_base = t("title_control_mantenimiento")
        if usuarios.SESION_ACTUAL:
            titulo_base += f"  —  👤 {usuarios.SESION_ACTUAL['nombre']}"
        self.setWindowTitle(titulo_base)

        indice_actual = self.tabs.currentIndex()
        self.tabs.blockSignals(True)
        while self.tabs.count():
            viejo = self.tabs.widget(0)
            self.tabs.removeTab(0)
            viejo.deleteLater()
        self._poblar_tabs()
        if 0 <= indice_actual < self.tabs.count():
            self.tabs.setCurrentIndex(indice_actual)
        self.tabs.blockSignals(False)

        self.refresh_all(); self.pintar_calendario(); self.update_calendar_list(); self.refresh_avisos(); self.refresh_todos(); self.setup_autocompletado()

    def closeEvent(self, e):
        # Posponemos el cierre real (aceptando el evento al final de esta misma
        # llamada, no volviendo a invocar self.close(): Qt ignora los close()
        # reentrantes mientras ya se está procesando uno, así que llamarlo aquí
        # dejaría la ventana abierta y obligaría a pulsar "Salir" dos veces).
        e.ignore()

        print("Iniciando limpieza de fotos...")
        self.limpiar_fotos_huerfanas(silencioso=True)

        print("Iniciando Auto-Backup...")
        dlg = QDialog(self)
        dlg.setWindowTitle(tt("title_cerrando", "Cerrando MantPro"))
        dlg.setFixedSize(420, 110)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_haciendo_backup", "Haciendo copia de seguridad antes de cerrar...")))
        barra = QProgressBar(); barra.setRange(0, 0)
        l.addWidget(barra)
        dlg.setLayout(l)

        def _actualizar_progreso(actual, total):
            if total:
                barra.setRange(0, total)
                barra.setValue(actual)

        def _backup_terminado(exito, mensaje):
            if not exito:
                print(f"Error en auto-backup: {mensaje}")
            dlg.accept()

        self.hilo_backup = BackupThread(self.carpeta_fotos, self.carpeta_backups_auto, self.db.db_name, self.db.db_almacen_name)
        self.hilo_backup.progreso.connect(_actualizar_progreso)
        self.hilo_backup.resultado.connect(_backup_terminado)
        self.hilo_backup.start()

        dlg.exec()

        self.settings.setValue("geometry", self.saveGeometry())
        e.accept()

    def on_registro_recibido(self, titulo, detalles, tags, filename, ruta_foto):
        if self.qr_dialog: self.qr_dialog.accept(); self.qr_dialog = None

        # ELIMINADO EL GUARDADO DUPLICADO (self.db.agregar_tarea).
        # La BD ya se actualizó en la API, así que solo refrescamos la vista:
        self.refresh_all()
        self.statusBar().showMessage(f"📲 Recibido: {titulo}", 4000)

    def _servidor_no_arranca(self, detalle):
        self.sincronizacion_activa = False
        QMessageBox.warning(self, tt("title_puerto_servidor", "Puerto de sincronización"),
            tt("msg_servidor_no_arranca", "No se ha podido arrancar la sincronización con los móviles en el puerto {p}.\n\n"
               "Puedes cambiar el puerto en Herramientas > Puerto de sincronización.").format(p=self.server_thread.server_port)
            + f"\n\n({detalle})")

    def cambiar_puerto_servidor(self):
        actual = self.server_thread.server_port
        dlg = DialogoPuertoServidor(self, actual, ocupado=False)
        if dlg.exec() and dlg.puerto() != actual:
            self.db.set_config("puerto_servidor", str(dlg.puerto()))
            QMessageBox.information(self, tt("title_puerto_servidor", "Puerto de sincronización"),
                tt("msg_puerto_reiniciar", "El nuevo puerto se usará la próxima vez que abras MantPro."))

    def mostrar_dialogo_qr(self):
        if not getattr(self, "sincronizacion_activa", True):
            QMessageBox.warning(self, tt("title_puerto_servidor", "Puerto de sincronización"),
                tt("msg_sincronizacion_desactivada", "La sincronización con los móviles está desactivada en esta sesión "
                   "porque su puerto estaba ocupado. Cierra el programa que lo usa o cambia el puerto en "
                   "Herramientas > Puerto de sincronización, y vuelve a abrir MantPro."))
            return
        url = f"http://{self.server_thread.obtener_ip_local()}:{self.server_thread.server_port}"
        self.qr_dialog = DialogoQR(url, self)
        self.qr_dialog.exec(); self.qr_dialog = None

    def mostrar_about(self):
        import webbrowser
        texto = f"""
        <h2>MantPro {'v' + APP_VERSION if APP_VERSION[:1].isdigit() else APP_VERSION}</h2>
        <p><b>AnabasaSoft</b></p>
        <p>📧 Email: <a href="mailto:anabasasoft@gmail.com">anabasasoft@gmail.com</a></p>
        <p>🌐 GitHub: <a href="https://github.com/AnabasaSoft">github.com/AnabasaSoft</a></p>
        <p>💼 Proyecto: <a href="https://github.com/AnabasaSoft/MantPro">github.com/AnabasaSoft/MantPro</a></p>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle(t("title_acerca_de"))
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(texto)
        # Esto permite que los enlaces abran el navegador de KDE (o el por defecto del SO)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        msg.exec()

    def comprobar_actualizaciones(self, manual=False):
        # Instalado con el gestor de paquetes de la distribución (OBS/zypper):
        # se actualiza con él, así que no se busca nada en GitHub.
        if GESTOR_PAQUETES:
            if manual:
                comandos = {"zypper": "sudo zypper refresh && sudo zypper update mantpro"}
                QMessageBox.information(self, t("title_actualizado"),
                    tt("msg_actualizaciones_gestor_paquetes",
                       "MantPro se ha instalado con el gestor de paquetes del sistema ({gestor}) y se actualiza con él:\n\n{comando}").format(
                        gestor=GESTOR_PAQUETES, comando=comandos.get(GESTOR_PAQUETES, GESTOR_PAQUETES)))
            return
        # Ejecutado con "python main.py" (no el binario instalado): su
        # APP_VERSION no es la real, que solo se fija al compilar desde el tag,
        # así que siempre parecería desactualizado.
        if not getattr(sys, "frozen", False):
            if manual:
                QMessageBox.information(self, t("title_actualizado"),
                    tt("msg_actualizaciones_codigo_fuente",
                       "MantPro se está ejecutando desde el código fuente: no se buscan actualizaciones."))
            return
        self._check_manual = manual
        if manual: self.statusBar().showMessage("🔄 Buscando actualizaciones en GitHub...", 3000)
        self.hilo_updates = ChequeadorActualizaciones()
        self.hilo_updates.resultado.connect(self.on_actualizacion_comprobada)
        self.hilo_updates.start()

    def on_actualizacion_comprobada(self, hay_nueva, version, url, notas):
        if hay_nueva:
            msg = QMessageBox(self)
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg.setWindowTitle(t("title_nueva_version"))
            msg.setText(t("msg_nueva_version_disponible").format(actual=APP_VERSION, nueva=version))
            msg.setInformativeText(t("msg_quieres_descargar"))
            if notas: msg.setDetailedText(notas)

            btn_si = msg.addButton(t("btn_descargar"), QMessageBox.ButtonRole.YesRole)
            msg.addButton(t("btn_luego"), QMessageBox.ButtonRole.NoRole)

            msg.setWindowState(msg.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
            msg.raise_()
            msg.activateWindow()

            msg.exec()

            if msg.clickedButton() == btn_si:
                abrir_url_externa(url)
        elif self._check_manual:
            if version == "error":
                QMessageBox.warning(self, t("title_error"), t("msg_error_conexion_github"))
            else:
                QMessageBox.information(self, t("title_actualizado"), t("msg_ya_actualizado").format(v=APP_VERSION))

    def crear_menu(self):
        mb = self.menuBar()

        # --- MENÚ SESIÓN (delante de Archivo) ---
        sm = mb.addMenu(tt("menu_sesion", "&Sesión"))
        sm.addAction(QAction(tt("menu_cambiar_usuario", "🔁 Cambiar de usuario"),
                             self, triggered=self.cerrar_sesion))
        sm.addAction(QAction(tt("menu_cerrar_sesion", "🚪 Cerrar sesión"),
                             self, triggered=self.cerrar_sesion))
        sm.addSeparator()
        sm.addAction(QAction(t("menu_salir"), self, triggered=self.close))
        # ------------------------------------------

        fm = mb.addMenu(t("menu_archivo"))
        if usuarios.es_admin():
            fm.addAction(QAction(t("menu_backup"), self, triggered=self.realizar_backup))
            menu_restaurar = fm.addMenu(t("menu_restaurar"))
            menu_restaurar.addAction(QAction(tt("menu_restaurar_manual", "Restaurar..."), self, triggered=self.restaurar_backup))
            menu_restaurar.addAction(QAction(tt("menu_restaurar_auto", "Restaurar desde copia automática..."), self, triggered=self.restaurar_backup_auto))
            fm.addSeparator()
            fm.addAction(QAction(t("menu_importar"), self, triggered=self.importar_datos))
            fm.addSeparator()

        # --- SUBMENÚ EXPORTAR (PDF, CSV y Excel) ---
        menu_exportar = fm.addMenu(t("menu_exportar"))
        menu_pdf = menu_exportar.addMenu(t("menu_opciones_pdf"))

        act_exportar = QAction(t("menu_generar_pdf"), self)
        act_exportar.triggered.connect(self.exportar_pdf)
        menu_pdf.addAction(act_exportar)

        menu_pdf.addSeparator()

        act_cambiar_logo = QAction(t("menu_add_logo"), self)
        act_cambiar_logo.triggered.connect(self.cambiar_logo)
        menu_pdf.addAction(act_cambiar_logo)

        act_quitar_logo = QAction(t("menu_quitar_logo"), self)
        act_quitar_logo.triggered.connect(self.quitar_logo)
        menu_pdf.addAction(act_quitar_logo)
        # --------------------

        menu_exportar.addAction(QAction(t("menu_csv"), self, triggered=self.exportar_csv))
        menu_exportar.addAction(QAction(t("menu_excel"), self, triggered=self.exportar_excel))
        tm = mb.addMenu(t("menu_herramientas"))
        act_sync = QAction(t("menu_sync_qr"), self); act_sync.triggered.connect(self.mostrar_dialogo_qr); tm.addAction(act_sync)
        if usuarios.es_admin():
            tm.addAction(QAction(t("menu_gestionar_dias"), self, triggered=self.gest_dias));

            # --- OPCIÓN DE PAÍS / PROVINCIA ---
            act_prov = QAction(t("menu_pais_region"), self)
            act_prov.triggered.connect(self.cambiar_pais_region)
            tm.addAction(act_prov)
            tm.addAction(QAction(tt("menu_puerto_servidor", "🔌 Puerto de sincronización…"), self,
                                 triggered=self.cambiar_puerto_servidor))
            tm.addAction(QAction(tt("menu_tiempo_guardado", "🗑️ Tiempo máximo de guardado de trabajos…"), self,
                                 triggered=self.borrar_trabajos_antiguos))
            # ---------------------------------

        # --- SUBMENÚ DE IDIOMA ---
        menu_idioma = tm.addMenu(t("menu_idioma"))
        self.acciones_idioma = []
        for codigo, nombre in idiomas.IDIOMAS_DISPONIBLES:
            act_idioma = QAction(nombre, self)
            act_idioma.setCheckable(True)
            act_idioma.setChecked(codigo == idiomas.get_idioma())
            act_idioma.triggered.connect(lambda checked, c=codigo: self.cambiar_idioma(c))
            menu_idioma.addAction(act_idioma)
            self.acciones_idioma.append((codigo, act_idioma))
        # -------------------------

        fm.addSeparator()
        if usuarios.es_admin():
            tm.addAction(QAction(t("menu_limpiar_fotos"), self, triggered=lambda: self.limpiar_fotos_huerfanas(limpiar_backups=True)))
            tm.addSeparator()
        tm.addAction(QAction(tt("menu_cambiar_password", "🔑 Cambiar mi contraseña"),
                             self, triggered=self.cambiar_mi_password))
        if usuarios.es_admin():
            tm.addAction(QAction(tt("menu_usuarios", "👥 Gestión de usuarios"),
                                 self, triggered=self.gestionar_usuarios))
            tm.addAction(QAction(tt("menu_sesiones", "🔐 Sesiones de dispositivos"),
                                 self, triggered=self.gestionar_sesiones))
            tm.addAction(QAction(tt("menu_auditoria", "📋 Registro de cambios"),
                                 self, triggered=self.ver_auditoria))
        # --- Menú de tema visual ---
        vm = mb.addMenu(tt("menu_tema", "Apariencia"))
        self._acciones_tema = {}
        grupo_tema = QActionGroup(self)
        for nombre, etiqueta in [("oscuro", tt("tema_oscuro", "🌙 Oscuro (por defecto)")),
                                  ("claro", tt("tema_claro", "☀️ Claro")),
                                  ("retro", tt("tema_retro", "🖥️ Clásico (Windows 98)"))]:
            act = QAction(etiqueta, self, checkable=True)
            act.setData(nombre)
            act.triggered.connect(lambda checked, n=nombre: self.aplicar_estilo_visual(n))
            grupo_tema.addAction(act)
            vm.addAction(act)
            self._acciones_tema[nombre] = act
            if nombre == self._tema_actual:
                act.setChecked(True)

        hm = mb.addMenu(t("menu_ayuda"))
        hm.addAction(QAction(t("menu_buscar_actualizaciones"), self, triggered=lambda: self.comprobar_actualizaciones(manual=True)))
        hm.addAction(QAction(t("menu_acerca_de"), self, triggered=self.mostrar_about))

    def cambiar_idioma(self, codigo):
        if codigo == idiomas.get_idioma():
            return
        idiomas.set_idioma(codigo)
        self.db.set_config("idioma", codigo)
        self.recargar_interfaz_completa()

    def cambiar_pais_region(self):
        # PASO 1: Elegir país
        dlg_pais = DialogoSeleccionPais(self.gestor_festivos, self.db, self)
        if not dlg_pais.exec():
            return  # Cancelado

        nombre_pais, iso_pais = dlg_pais.get_selection()
        self.db.set_config("country_iso", iso_pais)

        if iso_pais == "ES":
            # PASO 2 (solo España): Elegir provincia, igual que antes
            dlg = DialogoSeleccionRegion(self.db, self)
            if dlg.exec():
                nombre, iso_prov, iso_parent = dlg.get_selection()
                self.db.set_config("region_iso", iso_prov)
                self.db.set_config("parent_iso", iso_parent)
                self.gestor_festivos.limpiar_cache()
                QMessageBox.information(self, t("title_region_cambiada"), t("msg_region_cambiada").format(zona=nombre, parent=iso_parent, prov=iso_prov))
            else:
                # Canceló la provincia, pero el país ya quedó guardado como España
                self.gestor_festivos.limpiar_cache()
        else:
            # Otro país: sin desglose regional, solo festivos nacionales
            self.db.set_config("region_iso", "")
            self.db.set_config("parent_iso", "")
            self.gestor_festivos.limpiar_cache()
            QMessageBox.information(self, t("title_pais_cambiado"), t("msg_pais_cambiado").format(pais=nombre_pais))

        # Repintar el calendario
        self.pintar_calendario()
        self.update_calendar_list()

    def _llenar_combo_especialidades(self, combo, incluir_ninguna=True):
        """Rellena un combo con el catálogo de especialidades, conservando la selección."""
        anterior = combo.currentData() if combo.count() > 0 else "__SIN_SELECCION_PREVIA__"
        combo.blockSignals(True)
        combo.clear()
        if incluir_ninguna:
            combo.addItem(tt("especialidades_ninguna", "Sin especialidad"), None)
        for e in usuarios.listar_especialidades():
            combo.addItem(e["nombre"], e["id"])
        idx = combo.findData(anterior)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def _llenar_combo_usuarios(self, combo, incluir_todos=False, incluir_sin_asignar=False):
        """Rellena un combo con los usuarios activos, conservando la selección."""
        # Si el combo aún no tenía nada cargado (primer llenado), no hay
        # selección previa real que conservar: usamos un centinela que no
        # coincide con ningún dato, para no confundir "sin selección" con
        # "Sin asignar" (ambos usan None como dato) y así caer en el índice 0.
        anterior = combo.currentData() if combo.count() > 0 else "__SIN_SELECCION_PREVIA__"
        combo.blockSignals(True)
        combo.clear()
        if incluir_todos:
            combo.addItem(tt("filtro_todos", "Todos"), "TODOS")
        if incluir_sin_asignar:
            combo.addItem(tt("lbl_sin_asignar", "Sin asignar"), None)
        for u in usuarios.listar_usuarios(incluir_inactivos=False):
            combo.addItem(u["nombre"], u["id"])
        idx = combo.findData(anterior)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def _llenar_combo_prioridad(self, combo, valor_actual=None):
        """Rellena un combo con los niveles de prioridad, seleccionando valor_actual (o Media por defecto)."""
        combo.blockSignals(True)
        combo.clear()
        for cod, clave in (("Baja", "prioridad_baja"), ("Media", "prioridad_media"),
                           ("Alta", "prioridad_alta"), ("Crítica", "prioridad_critica")):
            combo.addItem(tt(clave, cod), cod)
        idx = combo.findData(valor_actual or "Media")
        combo.setCurrentIndex(idx if idx >= 0 else 1)
        combo.blockSignals(False)

    def on_tab_changed(self, i):
        if i == 0: self.refresh_dashboard()
        elif i == 1: self.pintar_calendario(); self.update_calendar_list()
        elif i == 2: self.refresh_avisos()
        elif i == 4: self.refresh_history()
        self.refresh_todos()

    def refresh_all(self):
        self.refresh_dashboard(); self.pintar_calendario(); self.update_calendar_list()
        self.refresh_history(); self.search(); self.refresh_todos(); self.refresh_avisos(); self.refresh_stock()
        if hasattr(self, 'arbol_maquinas'):
            self.refrescar_arbol_maquinas()

    def setup_table(self, tabla_widget):
        tabla_widget.setColumnCount(4); tabla_widget.setHorizontalHeaderLabels([t("hdr_fecha"), t("hdr_descripcion"), t("hdr_tags"), tt("hdr_realizado_por", "Realizado por")]); tabla_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch); # La columna del técnico se ajusta al contenido (cabecera o nombre, lo que sea más ancho)
        tabla_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents); tabla_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); tabla_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection); tabla_widget.setAlternatingRowColors(True); tabla_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def configurar_deseleccion(self, widget):
        clase_base = type(widget)
        def click_inteligente(event):
            clase_base.mousePressEvent(widget, event)
            if not widget.indexAt(event.pos()).isValid(): widget.clearSelection(); widget.setCurrentItem(None)
        widget.mousePressEvent = click_inteligente

    def guardar_archivo_dialogo(self, titulo, nombre_defecto, filtro):
        dialogo = QFileDialog(self, titulo); dialogo.setAcceptMode(QFileDialog.AcceptMode.AcceptSave); dialogo.setFileMode(QFileDialog.FileMode.AnyFile); dialogo.setNameFilter(filtro); dialogo.selectFile(nombre_defecto)
        dialogo.setOption(QFileDialog.Option.DontUseNativeDialog, True); dialogo.setLabelText(QFileDialog.DialogLabel.Accept, t("btn_guardar_form")); dialogo.setLabelText(QFileDialog.DialogLabel.Reject, t("btn_cancelar"))
        if dialogo.exec(): return dialogo.selectedFiles()[0]
        return None
