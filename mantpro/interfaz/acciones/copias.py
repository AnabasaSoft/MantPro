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

"""Copias de seguridad, restauración, limpieza de fotos y borrado de trabajos antiguos."""

import os
import re
import zipfile
from datetime import datetime
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QMessageBox, QDialog, QFileDialog, QProgressBar,
                             QInputDialog, QLineEdit, QApplication, QPushButton)
from PyQt6.QtCore import Qt, QTimer

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..dialogos.trabajos import DialogoTiempoGuardado
from ..dialogos.sistema import DialogoContrasenaCopias, DialogoCifradoBD, DialogoClaveRecuperacion
from ..hilos import BackupThread, BackupManualThread, RestoreManualThread, RecifrarCopiasThread
from ..dialogos.copias import DialogoCopiasAutomaticas, textos_problemas, fecha_hora
from ...nucleo import usuarios, almacen
from ...nucleo.fotos import fotos_galeria
from ...nucleo.seguridad import anadir_bd_a_zip
from ...nucleo import cifrado_copias, conexion_bd, copias

class AccionesCopias:
    """Copias de seguridad, restauración, limpieza de fotos y borrado de trabajos antiguos.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    # =========================================================================
    # FUNCIONES RESTAURADAS Y NUEVAS
    # =========================================================================

    def realizar_backup(self):
        self.limpiar_fotos_huerfanas(silencioso=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_zip = f"backup_completo_{timestamp}.zip"
        # Sugerimos la carpeta de backups habitual, pero el usuario puede elegir otra ubicación
        ruta_sugerida = os.path.join(self.carpeta_backups, nombre_zip)
        ruta_zip = self.guardar_archivo_dialogo(t("title_guardar_backup"), ruta_sugerida, "Archivos ZIP (*.zip)")
        if not ruta_zip: return

        dlg = QDialog(self)
        dlg.setWindowTitle(t("title_guardar_backup"))
        dlg.setFixedSize(420, 110)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_haciendo_backup", "Haciendo copia de seguridad...")))
        barra = QProgressBar(); barra.setRange(0, 0)
        l.addWidget(barra)
        dlg.setLayout(l)

        def _actualizar_progreso(actual, total):
            if total:
                barra.setRange(0, total)
                barra.setValue(actual)

        def _terminado(exito, mensaje, ruta):
            dlg.accept()
            if exito:
                texto = t("msg_backup_guardado").format(archivo=os.path.basename(ruta))
                if cifrado_copias.clave_actual():
                    texto += "\n\n🔒 " + tt("msg_backup_cifrada", "La copia está cifrada con la contraseña de las copias.")
                QMessageBox.information(self, t("title_backup_completo"), texto)
                if mensaje:   # la copia se ha hecho, pero alguna base de datos está dañada
                    QMessageBox.warning(self, t("title_backup_completo"), tt(
                        "msg_bd_integridad", "La copia se ha guardado, pero la comprobación de integridad ha encontrado errores en:\n\n{detalle}\n\nGuarda también una copia anterior y revisa el equipo (disco, cortes de luz).").format(detalle=mensaje))
            else:
                QMessageBox.critical(self, t("title_error_backup"), mensaje)

        self.hilo_backup_manual = BackupManualThread(ruta_zip, self.carpeta_fotos, self.db.db_name, self.db.db_almacen_name)
        self.hilo_backup_manual.progreso.connect(_actualizar_progreso)
        self.hilo_backup_manual.resultado.connect(_terminado)
        self.hilo_backup_manual.start()

        dlg.exec()

    def configurar_contrasena_copias(self):
        """Archivo > Contraseña de las copias: poner, cambiar o quitar la
        contraseña y, si se pide, rehacer con ella las copias que ya hay."""
        if not usuarios.es_admin(): return
        anterior = cifrado_copias.clave_actual()
        dlg = DialogoContrasenaCopias(self, activada=anterior is not None)
        if not dlg.exec() or not dlg.accion: return
        titulo = tt("title_contrasena_copias", "Contraseña de las copias de seguridad")
        if dlg.accion == "quitar":
            nueva = None
        else:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                nueva = cifrado_copias.Clave.desde_contrasena(dlg.contrasena)
            finally:
                QApplication.restoreOverrideCursor()
        cifrado_copias.guardar_clave(nueva)
        usuarios.auditar("seguridad", "configurar", "Contraseña de las copias de seguridad " + ("quitada" if nueva is None else "puesta o cambiada"))
        hecho = (tt("msg_contrasena_copias_quitada", "Las copias nuevas se guardarán sin cifrar.") if nueva is None
                 else tt("msg_contrasena_copias_puesta", "Las copias nuevas se guardarán cifradas con esta contraseña."))
        if not dlg.aplicar_existentes:
            QMessageBox.information(self, titulo, hecho)
            return

        espera = QDialog(self)
        espera.setWindowTitle(titulo)
        espera.setFixedSize(420, 110)
        espera.setWindowModality(Qt.WindowModality.ApplicationModal)
        espera.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        l = QVBoxLayout(espera)
        l.addWidget(QLabel(tt("lbl_recifrando_copias", "Actualizando las copias que ya hay...")))
        barra = QProgressBar(); barra.setRange(0, 0)
        l.addWidget(barra)

        def _progreso(actual, total):
            if total:
                barra.setRange(0, total); barra.setValue(actual)

        def _terminado(exito, mensaje):
            espera.accept()
            if exito:
                QMessageBox.information(self, titulo, hecho + "\n\n" + tt("msg_copias_recifradas",
                    "Copias actualizadas: {n}. Las copias guardadas fuera de las carpetas de MantPro "
                    "(USB, NAS…) siguen como estaban.").format(n=mensaje))
            else:
                QMessageBox.critical(self, titulo, mensaje)

        conocidas = {anterior.sal: anterior} if anterior else {}
        self.hilo_recifrar = RecifrarCopiasThread([self.carpeta_backups, self.carpeta_backups_auto], conocidas, nueva)
        self.hilo_recifrar.progreso.connect(_progreso)
        self.hilo_recifrar.resultado.connect(_terminado)
        self.hilo_recifrar.start()
        espera.exec()

    def configurar_cifrado_bd(self):
        """Herramientas > Cifrado de las bases de datos: activarlo (crea la
        clave, la guarda en el llavero y enseña la de recuperación), verla o
        quitarlo. La conversión se hace al volver a abrir MantPro."""
        if not usuarios.es_admin(): return
        activo = conexion_bd.cifrado_activo()
        dlg = DialogoCifradoBD(self, activo=activo, disponible=conexion_bd.HAY_SQLCIPHER,
                               hay_llavero=conexion_bd.hay_llavero())
        if not dlg.exec() or not dlg.accion: return
        titulo = tt("title_cifrado_bd", "Cifrado de las bases de datos")
        if dlg.accion == "ver_clave":
            clave = conexion_bd._clave_hex
            if clave:
                DialogoClaveRecuperacion(conexion_bd.formato_recuperacion(clave), self, obligatorio=False).exec()
            return
        if dlg.accion == "cifrar":
            clave = conexion_bd.nueva_clave()
            donde = conexion_bd.guardar_clave(clave)
            if conexion_bd.leer_clave_guardada() != clave:
                QMessageBox.critical(self, titulo, tt("msg_clave_no_guardada",
                    "No se ha podido guardar la clave; las bases de datos no se cifrarán."))
                return
            DialogoClaveRecuperacion(conexion_bd.formato_recuperacion(clave), self).exec()
            detalle = "fichero clave_bd.json" if donde == "fichero" else "llavero"
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle(titulo)
            msg.setText(tt("msg_confirmar_quitar_cifrado_bd",
                "Las bases de datos se guardarán sin cifrar en este ordenador. ¿Continuar?"))
            btn_si = msg.addButton(tt("btn_quitar_cifrado_bd", "Quitar el cifrado"), QMessageBox.ButtonRole.DestructiveRole)
            msg.addButton(t("btn_cancelar"), QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            if msg.clickedButton() != btn_si: return
            detalle = ""
        conexion_bd.programar_conversion(dlg.accion)
        usuarios.auditar("seguridad", "configurar", ("Cifrado de las bases de datos activado (clave en " + detalle + ")") if dlg.accion == "cifrar"
            else "Cifrado de las bases de datos quitado")
        QMessageBox.information(self, titulo, tt("msg_reabrir_para_cifrar",
            "MantPro se cerrará ahora (con su copia de seguridad de siempre). Al volver a abrirlo se hará el cambio, "
            "que tarda unos segundos."))
        self.close()

    def _confirmar_restaurar(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(t("title_restaurar_copia"))
        msg.setText(t("msg_advertencia_restaurar"))
        btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        return msg.clickedButton() == btn_si

    def restaurar_backup(self):
        if not self._confirmar_restaurar(): return
        # Use a dialog instance to allow setting DontUseNativeDialog if needed, though getOpenFileName static usually works.
        # But to be safe with styles, we could instantiate QFileDialog.
        # For restore, let's keep it simple as it's a critical operation.
        archivo_zip, _ = QFileDialog.getOpenFileName(self, t("title_seleccionar_backup"), "backups", "Archivos ZIP (*.zip)", options=QFileDialog.Option.DontUseNativeDialog)
        if not archivo_zip: return
        self._ejecutar_restauracion(archivo_zip)

    def restaurar_backup_auto(self):
        if not self._confirmar_restaurar(): return
        carpeta_inicial = self.carpeta_backups_auto if os.path.isdir(self.carpeta_backups_auto) else "backups"
        archivo_zip, _ = QFileDialog.getOpenFileName(
            self, tt("title_seleccionar_backup_auto", "Seleccionar copia automática"), carpeta_inicial,
            tt("filtro_backup_auto", "Copias automáticas") + " (auto_backup_db_*.zip)",
            options=QFileDialog.Option.DontUseNativeDialog)
        if not archivo_zip: return
        self._ejecutar_restauracion(archivo_zip)

    def _claves_para_restaurar(self, zips):
        """Claves para descifrar esos ZIP ({sal: Clave}). La de este equipo
        no hace falta pedirla; para el resto se pide la contraseña (una copia
        de otro equipo, o hecha antes de cambiarla). Devuelve (claves, nuevas)
        o None si se cancela."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            sales = cifrado_copias.sales_de(zips)
        finally:
            QApplication.restoreOverrideCursor()
        claves, nuevas = {}, {}
        actual = cifrado_copias.clave_actual()
        if actual and actual.sal in sales:
            claves[actual.sal] = actual
        faltan = {s: c for s, c in sales.items() if s not in claves}
        texto = tt("msg_pedir_contrasena_copia", "Esta copia está cifrada. Escribe su contraseña:")
        while faltan:
            contrasena, ok = QInputDialog.getText(self, tt("title_copia_cifrada", "Copia cifrada"), texto,
                                                  QLineEdit.EchoMode.Password)
            if not ok:
                return None
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                abiertas = cifrado_copias.probar_contrasena(contrasena, faltan)
            finally:
                QApplication.restoreOverrideCursor()
            if not abiertas:
                texto = tt("msg_contrasena_copia_mal", "La contraseña no es correcta. Vuelve a escribirla:")
                continue
            claves.update(abiertas); nuevas.update(abiertas)
            for sal in abiertas:
                del faltan[sal]
            texto = tt("msg_contrasena_copia_otra",
                       "Una parte de la copia se cifró con otra contraseña (por ejemplo, una anterior). Escríbela:")
        return claves, nuevas

    def _ejecutar_restauracion(self, archivo_zip):
        # Restaurar en DATA_DIR o carpeta local según donde estemos
        restore_path = os.path.dirname(self.db.db_name)
        es_auto_backup = os.path.basename(archivo_zip).startswith("auto_backup_db_")

        zips = [archivo_zip]
        if es_auto_backup:
            carpeta = os.path.dirname(archivo_zip)
            zips += [os.path.join(carpeta, f) for f in os.listdir(carpeta)
                     if f.startswith("fotos_backup_") and f.endswith(".zip")]
        resultado_claves = self._claves_para_restaurar(zips)
        if resultado_claves is None:
            return
        claves, nuevas = resultado_claves

        dlg = QDialog(self)
        dlg.setWindowTitle(t("title_restaurar_copia"))
        dlg.setFixedSize(420, 110)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        l = QVBoxLayout()
        l.addWidget(QLabel(tt("lbl_restaurando_backup", "Restaurando copia de seguridad...")))
        barra = QProgressBar(); barra.setRange(0, 0)
        l.addWidget(barra)
        dlg.setLayout(l)

        def _actualizar_progreso(actual, total):
            if total:
                barra.setRange(0, total)
                barra.setValue(actual)

        def _terminado(exito, mensaje):
            dlg.accept()
            if exito:
                texto = t("msg_sistema_restaurado")
                # Equipo nuevo sin contraseña de copias: se queda con la de la
                # copia restaurada, para que las siguientes salgan igual de cifradas
                if nuevas and cifrado_copias.clave_actual() is None:
                    cifrado_copias.guardar_clave(next(iter(nuevas.values())))
                    texto += "\n\n🔒 " + tt("msg_contrasena_copias_adoptada",
                        "Las copias nuevas de este equipo también se cifrarán con esa contraseña.")
                usuarios.auditar("copias", "restaurar", os.path.basename(archivo_zip),
                                 detalle="Copia automática" if es_auto_backup else "Copia completa")
                QMessageBox.information(self, t("title_restauracion"), texto); self.refresh_all()
                if mensaje:   # BD restaurada, pero alguna foto no se ha podido sacar
                    QMessageBox.warning(self, t("title_restauracion"), tt("msg_fotos_no_restauradas",
                        "No se han podido restaurar algunas fotos (copia dañada o con otra contraseña):\n\n{detalle}").format(detalle=mensaje))
            else:
                QMessageBox.critical(self, t("title_error_restauracion"), t("msg_zip_corrupto").format(error=mensaje))

        self.hilo_restore = RestoreManualThread(archivo_zip, restore_path, self.carpeta_fotos, es_auto_backup, self._fotos_en_uso, claves)
        self.hilo_restore.progreso.connect(_actualizar_progreso)
        self.hilo_restore.resultado.connect(_terminado)
        self.hilo_restore.start()

        dlg.exec()

    def _fotos_en_uso(self):
        """Nombres de fichero de foto referenciados desde cualquier sitio de la
        BD (trabajos, pendientes, fotos de máquinas y fotos de materiales del
        almacén, que comparten la misma carpeta aunque vivan en almacen.db).
        Se usa tanto para saber qué es basura como para saber qué hace falta
        restaurar de un backup."""
        fotos_en_uso = set(); conn = self.db.conectar(); c = conn.cursor()
        c.execute("SELECT descripcion FROM tareas")
        for row in c.fetchall():
            m = re.search(r"\[FOTO:\s*(.*?)\]", row[0])
            if m: fotos_en_uso.add(m.group(1).strip())
            m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", row[0])
            if m_d: fotos_en_uso.add(m_d.group(1).strip())
            fotos_en_uso.update(fotos_galeria(row[0]))
        c.execute("SELECT detalles FROM pendientes")
        for row in c.fetchall():
            m = re.search(r"\[FOTO:\s*(.*?)\]", row[0])
            if m: fotos_en_uso.add(m.group(1).strip())
            m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", row[0])
            if m_d: fotos_en_uso.add(m_d.group(1).strip())
            fotos_en_uso.update(fotos_galeria(row[0]))
        c.execute("SELECT foto FROM maquinas WHERE foto IS NOT NULL")
        for row in c.fetchall():
            if row[0]: fotos_en_uso.add(row[0].strip())
        conn.close()
        for material in almacen.listar_materiales():
            foto = material.get('foto')
            if foto: fotos_en_uso.add(foto.strip())
        return fotos_en_uso

    def _copia_previa_bases(self, prefijo):
        """Copia de las dos bases de datos antes de una operación masiva
        (borrar trabajos antiguos, importar...). No empieza por "auto_backup_db_"
        para que la rotación del backup automático (se quedan 3) no la borre."""
        os.makedirs(self.carpeta_backups_auto, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_copia = os.path.join(self.carpeta_backups_auto, f"{prefijo}_{ts}.zip")
        temporal = ruta_copia + ".tmp"
        clave = cifrado_copias.clave_actual()
        with zipfile.ZipFile(temporal, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for ruta in (self.db.db_name, getattr(self.db, "db_almacen_name", None)):
                anadir_bd_a_zip(zipf, ruta, clave)   # copia consistente (incluye el -wal)
        os.replace(temporal, ruta_copia)
        return ruta_copia

    def borrar_trabajos_antiguos(self):
        """Herramientas > Tiempo máximo de guardado: borra del historial los
        trabajos anteriores a la fecha elegida, con sus fotos, tras confirmar."""
        if not usuarios.es_admin(): return
        dlg = DialogoTiempoGuardado(self)
        if not dlg.exec(): return
        corte = dlg.fecha_corte().toString("yyyy-MM-dd")

        conn = self.db.conectar(); c = conn.cursor()
        c.execute("SELECT id, fecha, descripcion FROM tareas WHERE fecha < ? ORDER BY fecha", (corte,))
        filas = c.fetchall(); conn.close()
        if not filas:
            QMessageBox.information(self, tt("title_tiempo_guardado", "Tiempo máximo de guardado de trabajos"),
                tt("msg_sin_trabajos_antiguos", "No hay trabajos anteriores al {fecha}. No se borrará nada.").format(
                    fecha=idiomas.formato_fecha_localizada(corte)))
            return

        desde = idiomas.formato_fecha_localizada(filas[0][1])
        hasta = idiomas.formato_fecha_localizada(filas[-1][1])
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(tt("title_confirmar_borrado_antiguos", "Confirmar borrado de trabajos antiguos"))
        msg.setText(tt("msg_confirmar_borrado_antiguos",
            "Se van a borrar {n} trabajos del historial, del {desde} al {hasta}, junto con sus fotos.\n\n"
            "Antes se guardará una copia de seguridad de la base de datos.\n\n¿Continuar?").format(
                n=len(filas), desde=desde, hasta=hasta))
        btn_si = msg.addButton(tt("btn_borrar_trabajos", "Borrar trabajos"), QMessageBox.ButtonRole.DestructiveRole)
        msg.addButton(t("btn_cancelar"), QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() != btn_si: return

        try:
            ruta_copia = self._copia_previa_bases("antes_borrado_trabajos")

            fotos_candidatas = set()
            for _, _, desc in filas:
                for m in re.findall(r"\[FOTO(?:_DESPUES)?:\s*(.*?)\]", desc or ""):
                    fotos_candidatas.add(m.split("]")[0].strip())
                fotos_candidatas.update(fotos_galeria(desc))

            conn = self.db.conectar(); c = conn.cursor()
            c.execute("DELETE FROM tareas WHERE fecha < ?", (corte,))
            borrados = c.rowcount
            conn.commit(); conn.close()
            usuarios.registrar_auditoria(usuarios.id_actual(), None, "borrar",
                f"Borrado por tiempo máximo de guardado: {borrados} registros del {filas[0][1]} al {filas[-1][1]}")

            # Solo se borran del disco las fotos que ya no usa ningún otro registro
            en_uso = self._fotos_en_uso()
            fotos_borradas = 0
            for nombre in fotos_candidatas - en_uso:
                ruta = os.path.join(self.carpeta_fotos, nombre)
                if nombre and os.path.isfile(ruta):
                    try: os.remove(ruta); fotos_borradas += 1
                    except OSError: pass

            self.refresh_all()
            if hasattr(self, 'servidor') and self.servidor:
                self.servidor.pendiente_actualizado.emit()
            QMessageBox.information(self, tt("title_tiempo_guardado", "Tiempo máximo de guardado de trabajos"),
                tt("msg_trabajos_antiguos_borrados",
                   "Se han borrado {n} trabajos y {f} fotos.\n\nCopia de seguridad previa:\n{ruta}").format(
                    n=borrados, f=fotos_borradas, ruta=ruta_copia))
        except Exception as e:
            QMessageBox.critical(self, t("title_error"), str(e))

    def limpiar_fotos_huerfanas(self, silencioso=False, limpiar_backups=False):
        try:
            fotos_en_uso = self._fotos_en_uso()

            basura = []
            if os.path.exists(self.carpeta_fotos):
                for f in os.listdir(self.carpeta_fotos):
                    if f not in fotos_en_uso and f not in ["Logo.jpg", "icono.png"] and not f.startswith("QR_"):
                        basura.append(f)

            # Los ZIP de fotos del backup automático solo se revisan cuando se pide
            # explícitamente desde el menú Herramientas, nunca al cerrar el programa
            # ni antes de un backup manual, para no alargar esas operaciones.
            zips_con_huerfanas = {}
            if limpiar_backups and os.path.isdir(self.carpeta_backups_auto):
                for f in os.listdir(self.carpeta_backups_auto):
                    if f.startswith("fotos_backup_") and f.endswith(".zip"):
                        ruta_zip = os.path.join(self.carpeta_backups_auto, f)
                        try:
                            with zipfile.ZipFile(ruta_zip, 'r') as zf:
                                huerfanas = [n for n in zf.namelist()
                                             if cifrado_copias.nombre_real(n) not in fotos_en_uso]
                            if huerfanas: zips_con_huerfanas[ruta_zip] = huerfanas
                        except Exception:
                            pass

            total_huerfanas = len(basura) + sum(len(v) for v in zips_con_huerfanas.values())
            if total_huerfanas == 0: return

            confirmado = True
            if not silencioso:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle(t("title_limpieza"))
                msg.setText(t("msg_fotos_basura").format(n=total_huerfanas))
                btn_si = msg.addButton(t("btn_si"), QMessageBox.ButtonRole.YesRole)
                msg.addButton(t("btn_no"), QMessageBox.ButtonRole.NoRole)
                msg.exec()
                if msg.clickedButton() != btn_si: confirmado = False
            if not confirmado: return

            for f in basura:
                try: os.remove(os.path.join(self.carpeta_fotos, f))
                except: pass

            for ruta_zip, huerfanas in zips_con_huerfanas.items():
                try:
                    huerfanas_set = set(huerfanas)
                    ruta_tmp = ruta_zip + ".tmp"
                    with zipfile.ZipFile(ruta_zip, 'r') as origen, \
                         zipfile.ZipFile(ruta_tmp, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as nuevo:
                        for info in origen.infolist():
                            if info.filename not in huerfanas_set:
                                # Tal cual (las cifradas siguen cifradas, sin comprimirlas otra vez)
                                copia = zipfile.ZipInfo(info.filename, info.date_time)
                                copia.compress_type = info.compress_type
                                nuevo.writestr(copia, origen.read(info))
                    os.replace(ruta_tmp, ruta_zip)
                except Exception:
                    pass
        except Exception as e: print(f"Error limpieza: {e}")

    # =========================================================================
    # COPIAS AUTOMÁTICAS MIENTRAS LA APLICACIÓN ESTÁ ABIERTA
    # (la lógica está en nucleo/copias.py; aquí solo cuándo y los avisos)
    # =========================================================================

    _MINUTOS_TRAS_MOVIL = 10

    def iniciar_copias_automaticas(self):
        """Temporizadores de las copias automáticas e indicador de la barra de
        estado. Se llama una vez, al crear la ventana."""
        self.hilo_copia_fondo = None
        self._avisos_copias_mostrados = set()
        self.btn_estado_copias = QPushButton()
        self.btn_estado_copias.setFlat(True)
        self.btn_estado_copias.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_estado_copias.clicked.connect(self.configurar_copias_automaticas)
        self.statusBar().addPermanentWidget(self.btn_estado_copias)
        # Cada 5 minutos se mira si toca la copia periódica (mirar la hora de la
        # última copia, y no un temporizador de 2 h, sigue valiendo tras
        # suspender el equipo)
        self.temporizador_copias = QTimer(self)
        self.temporizador_copias.timeout.connect(self._tic_copias)
        self.temporizador_copias.start(5 * 60 * 1000)
        # Tras recibir datos de un móvil: se espera a que deje de enviar
        self.temporizador_copia_movil = QTimer(self)
        self.temporizador_copia_movil.setSingleShot(True)
        self.temporizador_copia_movil.timeout.connect(lambda: self._lanzar_copia_fondo("movil"))
        # Al arrancar: si quedaron cambios sin copiar (la copia del cierre
        # falló o la aplicación se cerró de golpe), copia; si no, avisa de lo
        # que quedara mal de la última vez (p. ej. la carpeta externa)
        QTimer.singleShot(20 * 1000, self._copias_al_arrancar)
        self.actualizar_indicador_copias()

    def parar_copias_automaticas(self):
        for nombre in ("temporizador_copias", "temporizador_copia_movil"):
            temporizador = getattr(self, nombre, None)
            if temporizador is not None:
                temporizador.stop()
        hilo = getattr(self, "hilo_copia_fondo", None)
        if hilo is not None and hilo.isRunning():
            hilo.wait()

    def _rutas_bd(self):
        return [self.db.db_name, self.db.db_almacen_name]

    def _copias_al_arrancar(self):
        if copias.hay_cambios_sin_copiar(self._rutas_bd(), self.carpeta_fotos):
            self._lanzar_copia_fondo("arranque")
        else:
            self._avisar_problemas_copias()

    def _tic_copias(self):
        self.actualizar_indicador_copias()
        if copias.toca_copia_periodica():
            self._lanzar_copia_fondo("periodica")

    def programar_copia_tras_movil(self):
        """Un móvil ha terminado de mandar datos: copia al rato (si llegan más,
        se vuelve a esperar, para hacer una sola copia por sincronización)."""
        temporizador = getattr(self, "temporizador_copia_movil", None)
        if temporizador is not None and copias.leer_config()["tras_movil"]:
            temporizador.start(self._MINUTOS_TRAS_MOVIL * 60 * 1000)

    def _lanzar_copia_fondo(self, motivo, config=None, accion="copia", al_terminar=None):
        """Copia (o prueba) en segundo plano, sin ventana de progreso. Las
        automáticas solo se hacen si ha habido cambios; las pedidas a mano,
        siempre. Si ya hay una en marcha (o se está restaurando), no hace nada."""
        ocupado = (self.hilo_copia_fondo is not None and self.hilo_copia_fondo.isRunning()) or \
            (getattr(self, "hilo_restore", None) is not None and self.hilo_restore.isRunning())
        if ocupado:
            if al_terminar:
                self.statusBar().showMessage(tt("msg_copia_en_marcha", "Ya hay una copia de seguridad en marcha."), 5000)
                al_terminar(None)
            return
        if accion == "copia":
            self.btn_estado_copias.setText(tt("lbl_indicador_copiando", "🛡️ Haciendo copia…"))
        hilo = BackupThread(self.carpeta_fotos, self.carpeta_backups_auto, self.db.db_name, self.db.db_almacen_name,
                            motivo=motivo, solo_si_hay_cambios=motivo not in ("manual", "cierre"),
                            config=config, accion=accion)

        def _terminado(resultado):
            self.actualizar_indicador_copias()
            if al_terminar:
                al_terminar(resultado)
            if al_terminar is None and resultado.get("hecha"):
                # Pedida desde el diálogo, el resultado lo enseña el propio diálogo
                self._avisar_problemas_copias()

        hilo.terminado.connect(_terminado)
        self.hilo_copia_fondo = hilo
        hilo.start()

    def _avisar_problemas_copias(self, solo_nuevos=True):
        """Avisa de lo que va mal en las copias. Cada problema se avisa una vez
        por sesión (si la carpeta externa sigue sin conectar, no salta cada 2
        horas): luego se ve en el indicador de la barra de estado."""
        textos = textos_problemas(copias.problemas(self.carpeta_backups_auto))
        if solo_nuevos:
            textos = [x for x in textos if x not in self._avisos_copias_mostrados]
        if not textos:
            return
        self._avisos_copias_mostrados.update(textos)
        QMessageBox.warning(self, tt("title_problema_copias", "Copias de seguridad"),
                            "\n\n".join(textos) + "\n\n" + tt("msg_ver_copias_automaticas",
                                                              "Más detalles en Archivo → Copias automáticas."))

    def actualizar_indicador_copias(self):
        boton = getattr(self, "btn_estado_copias", None)
        if boton is None:
            return
        lista = copias.problemas(self.carpeta_backups_auto)
        buena = copias.ultima_copia_buena(self.carpeta_backups_auto)
        if lista:
            boton.setText(tt("lbl_indicador_copias_problema", "⚠️ Copias: revisar"))
            boton.setStyleSheet("color: #e74c3c; font-weight: bold;")
            boton.setToolTip("\n\n".join(textos_problemas(lista)))
        else:
            cuando = fecha_hora(buena.isoformat()) if buena else "—"
            boton.setText(tt("lbl_indicador_copias", "🛡️ Última copia: {fecha}").format(fecha=cuando))
            boton.setStyleSheet("")
            boton.setToolTip(tt("tip_indicador_copias", "Copias automáticas: pulsa para ver el estado y configurarlas"))
        boton.setEnabled(usuarios.es_admin())

    def configurar_copias_automaticas(self):
        if not usuarios.es_admin():
            return

        def _lanzar(accion, config, al_terminar):
            self._lanzar_copia_fondo("manual", config=config, accion=accion, al_terminar=al_terminar)

        DialogoCopiasAutomaticas(self, self.carpeta_backups_auto, _lanzar).exec()
        self.actualizar_indicador_copias()
