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

"""Copias de seguridad, restauración, limpieza de fotos y borrado de trabajos antiguos."""

import os
import re
import zipfile
from datetime import datetime
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QMessageBox, QDialog, QFileDialog, QProgressBar
from PyQt6.QtCore import Qt

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..dialogos.trabajos import DialogoTiempoGuardado
from ..hilos import BackupManualThread, RestoreManualThread
from ...nucleo import usuarios, almacen
from ...nucleo.fotos import fotos_galeria

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
                QMessageBox.information(self, t("title_backup_completo"), t("msg_backup_guardado").format(archivo=os.path.basename(ruta)))
            else:
                QMessageBox.critical(self, t("title_error_backup"), mensaje)

        self.hilo_backup_manual = BackupManualThread(ruta_zip, self.carpeta_fotos, self.db.db_name, self.db.db_almacen_name)
        self.hilo_backup_manual.progreso.connect(_actualizar_progreso)
        self.hilo_backup_manual.resultado.connect(_terminado)
        self.hilo_backup_manual.start()

        dlg.exec()

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

    def _ejecutar_restauracion(self, archivo_zip):
        # Restaurar en DATA_DIR o carpeta local según donde estemos
        restore_path = os.path.dirname(self.db.db_name)
        es_auto_backup = os.path.basename(archivo_zip).startswith("auto_backup_db_")

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
                QMessageBox.information(self, t("title_restauracion"), t("msg_sistema_restaurado")); self.refresh_all()
            else:
                QMessageBox.critical(self, t("title_error_restauracion"), t("msg_zip_corrupto").format(error=mensaje))

        self.hilo_restore = RestoreManualThread(archivo_zip, restore_path, self.carpeta_fotos, es_auto_backup, self._fotos_en_uso)
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
        with zipfile.ZipFile(ruta_copia, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for ruta in (self.db.db_name, getattr(self.db, "db_almacen_name", None)):
                if ruta and os.path.exists(ruta):
                    zipf.write(ruta, arcname=os.path.basename(ruta))
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
                                huerfanas = [n for n in zf.namelist() if n not in fotos_en_uso]
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
                         zipfile.ZipFile(ruta_tmp, 'w', zipfile.ZIP_DEFLATED) as nuevo:
                        for n in origen.namelist():
                            if n not in huerfanas_set:
                                nuevo.writestr(n, origen.read(n))
                    os.replace(ruta_tmp, ruta_zip)
                except Exception:
                    pass
        except Exception as e: print(f"Error limpieza: {e}")
