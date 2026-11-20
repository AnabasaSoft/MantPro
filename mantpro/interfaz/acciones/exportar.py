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

"""Exportación a CSV, Excel y PDF, y logo del PDF."""

import os
import shutil
import tempfile
import re
from datetime import datetime
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QMessageBox, QDialog, QFileDialog, QProgressBar
from PyQt6.QtCore import QDate, Qt

from ...idiomas import t
from ..comun import tt
from ..dialogos.trabajos import DialogoExportarPDF, DialogoFiltroTecnico
from ..hilos import GeneradorPDFThread
from ..widgets.graficos import GraficoBarrasMensual, GraficoBarrasRanking, GraficoCircularTrabajos
from ...nucleo import maquinas, informe_historial
from ...nucleo.rutas import DATA_DIR

class AccionesExportar:
    """Exportación a CSV, Excel y PDF, y logo del PDF.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def _lineas_sede(self):
        """Datos de la sede elegida para los informes: [nombre, «CIF: …», dirección, contacto…],
        o [] si no hay una sola sede elegida (o solo hay una sede)."""
        from ...nucleo import sedes
        elegida = self.sede_filtro()
        if not isinstance(elegida, int) or not sedes.hay_varias():
            return []
        s = sedes.obtener(elegida)
        if not s:
            return []
        lineas = [s["nombre"]]
        if s.get("cif"):
            lineas.append(f'{tt("sede_lbl_cif", "CIF / NIF")}: {s["cif"]}')
        if s.get("direccion"):
            lineas.append(s["direccion"])
        contacto = " · ".join(x for x in (s.get("contacto"), s.get("telefono"), s.get("email")) if x)
        if contacto:
            lineas.append(contacto)
        return lineas

    def _sufijo_sede(self):
        lineas = self._lineas_sede()
        return "_" + re.sub(r'[<>:\"/\\|?*\s]+', '_', lineas[0]) if lineas else ""

    def exportar_csv(self):
        dlg = DialogoFiltroTecnico(self, t("title_exportar_csv"))
        if not dlg.exec(): return
        filtro_usuario = dlg.get_filtro()
        nombre_limpio = re.sub(r'[<>:\"/\\\\|?*]', '', filtro_usuario) if filtro_usuario else ""
        sufijo = (f"_{nombre_limpio}" if nombre_limpio else "") + self._sufijo_sede()
        nombre_defecto = f"Mantenimiento_{QDate.currentDate().toString('yyyyMMdd')}{sufijo}.csv"
        archivo = self.guardar_archivo_dialogo(t("title_exportar_csv"), nombre_defecto, "CSV (*.csv)")
        if not archivo: return
        try:
            datos = self.db.obtener_todas_cronologico(filtro_usuario, sede=self.sede_filtro())
            with open(archivo, 'w', newline='', encoding='utf-8') as f:
                informe_historial.generar_csv(datos, f, maquinas.mapa_rutas_completas())     # el núcleo (también la web)
            QMessageBox.information(self, t("title_exportado"), t("msg_csv_guardado"))
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))

    def exportar_excel(self):
        try: import xlsxwriter
        except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        dlg = DialogoFiltroTecnico(self, t("title_exportar_excel"))
        if not dlg.exec(): return
        filtro_usuario = dlg.get_filtro()
        nombre_limpio = re.sub(r'[<>:\"/\\\\|?*]', '', filtro_usuario) if filtro_usuario else ""
        sufijo = (f"_{nombre_limpio}" if nombre_limpio else "") + self._sufijo_sede()
        nombre_defecto = f"Mantenimiento_{QDate.currentDate().toString('yyyyMMdd')}{sufijo}.xlsx"
        archivo = self.guardar_archivo_dialogo(t("title_exportar_excel"), nombre_defecto, "Excel (*.xlsx)")
        if not archivo: return
        try:
            # Lo genera el núcleo (también lo usa MantPro Web)
            informe_historial.generar_excel(self.db.obtener_todas_cronologico(filtro_usuario, sede=self.sede_filtro()), archivo,
                                            self.carpeta_fotos, maquinas.mapa_rutas_completas(), self._lineas_sede())
            QMessageBox.information(self, t("title_exportado"), t("msg_excel_guardado"))
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))

    # ========================================================
    #  NUEVAS FUNCIONES PARA GESTIÓN DE LOGO PDF
    # ========================================================
    def cambiar_logo(self):
        # Use DontUseNativeDialog to ensure stylesheets apply
        archivo, _ = QFileDialog.getOpenFileName(self, t("title_seleccionar_logo"), "", "Imágenes (*.jpg *.png *.jpeg)", options=QFileDialog.Option.DontUseNativeDialog)
        if archivo:
            try:
                # Copiamos la imagen a la carpeta local con el nombre que busca el PDF
                # Use DATA_DIR path
                destino = os.path.join(DATA_DIR, "Logo.jpg")
                shutil.copy2(archivo, destino)
                QMessageBox.information(self, t("title_logo_actualizado"), t("msg_logo_actualizado"))
            except Exception as e:
                QMessageBox.critical(self, t("title_error"), str(e))

    def quitar_logo(self):
        # Use DATA_DIR path
        destino = os.path.join(DATA_DIR, "Logo.jpg")
        if os.path.exists(destino):
            try:
                os.remove(destino)
                QMessageBox.information(self, t("title_logo_borrado"), t("msg_logo_borrado"))
            except Exception as e:
                QMessageBox.critical(self, t("title_error"), str(e))
        else:
            QMessageBox.information(self, t("title_informacion"), t("msg_sin_logo"))

    def exportar_pdf(self):
        dlg = DialogoExportarPDF(self)
        if not dlg.exec(): return
        modo, inicio, fin, filtro_usuario, incluir_graficos = dlg.get_data()
        sufijo_u = f" — {filtro_usuario}" if filtro_usuario else ""
        lineas_sede = self._lineas_sede()
        if lineas_sede:
            sufijo_u = f" — {lineas_sede[0]}" + sufijo_u
        from ...nucleo import sedes as _sedes   # solo los trabajos de la sede elegida
        cond_u = " AND " + _sedes.condicion(self.sede_filtro()) + (" AND usuario_nombre = ?" if filtro_usuario else "")
        param_u = [filtro_usuario] if filtro_usuario else []

        try:
            conn = self.db.conectar()
            c = conn.cursor()
            lista_trabajos = []

            if modo == "RANGO" and inicio and fin:
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id, id FROM tareas "
                          "WHERE fecha BETWEEN ? AND ?" + cond_u + " ORDER BY fecha DESC, id DESC",
                          [inicio, fin] + param_u)
                datos = c.fetchall()
                if not datos: return
                nombre_defecto = f"Reporte_Mantenimiento_{inicio}_a_{fin}.pdf"
                archivo = self.guardar_archivo_dialogo(t("title_guardar_pdf"), nombre_defecto, "PDF (*.pdf)")
                if not archivo: return
                titulo_pdf = t("titulo_reporte_rango").format(inicio=inicio, fin=fin) + sufijo_u
                lista_trabajos.append({"archivo": archivo, "titulo": titulo_pdf, "datos": datos, "rango": (inicio, fin)})

            elif modo == "TODO":
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id, id FROM tareas "
                          "WHERE 1=1" + cond_u + " ORDER BY fecha DESC, id DESC", param_u)
                datos = c.fetchall()
                if not datos: return
                nombre_defecto = f"Reporte_Histórico_Completo_{datetime.now().strftime('%Y%m%d')}.pdf"
                archivo = self.guardar_archivo_dialogo(t("title_guardar_pdf"), nombre_defecto, "PDF (*.pdf)")
                if not archivo: return
                lista_trabajos.append({"archivo": archivo, "titulo": t("titulo_reporte_historico") + sufijo_u, "datos": datos, "rango": None})

            elif modo == "MESES":
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id, id FROM tareas "
                          "WHERE 1=1" + cond_u + " ORDER BY fecha DESC, id DESC", param_u)
                datos = c.fetchall()
                if not datos: return

                # Pedir carpeta en vez de archivo
                carpeta_destino = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta para Guardar los PDFs", "", options=QFileDialog.Option.DontUseNativeDialog)
                if not carpeta_destino: return

                # Agrupar por mes (YYYY-MM)
                datos_por_mes = {}
                for row in datos:
                    fecha_str = row[0]
                    if not fecha_str or len(fecha_str) < 7: continue
                    mes_str = fecha_str[:7]
                    if mes_str not in datos_por_mes:
                        datos_por_mes[mes_str] = []
                    datos_por_mes[mes_str].append(row)

                for mes, datos_mes in datos_por_mes.items():
                    archivo = os.path.join(carpeta_destino, f"Reporte_Mantenimiento_{mes}.pdf")
                    titulo_mes = t("titulo_reporte_mes").format(mes=mes) + sufijo_u
                    lista_trabajos.append({"archivo": archivo, "titulo": titulo_mes, "datos": datos_mes, "rango": (f"{mes}-01", f"{mes}-31")})

            conn.close()
        except Exception as e:
            QMessageBox.critical(self, t("title_error_db"), str(e))
            return

        if not lista_trabajos: return

        if incluir_graficos:
            for trabajo in lista_trabajos:
                ini_rango, fin_rango = trabajo["rango"] if trabajo["rango"] else (None, None)
                trabajo["graficos"] = self._generar_graficos_pdf(ini_rango, fin_rango)
        for trabajo in lista_trabajos:
            trabajo["sede"] = lineas_sede[1:] if lineas_sede else []   # datos de la sede bajo el título

        # Configurar UI de progreso
        self.progreso_pdf = QDialog(self)
        self.progreso_pdf.setWindowTitle(t("title_generando_pdf"))
        self.progreso_pdf.setFixedSize(450, 120)
        self.progreso_pdf.setWindowModality(Qt.WindowModality.ApplicationModal)
        l = QVBoxLayout()
        l.addWidget(QLabel(t("lbl_procesando_pdf")))
        bar = QProgressBar()
        bar.setRange(0, 0)
        l.addWidget(bar)
        self.progreso_pdf.setLayout(l)
        self.progreso_pdf.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        # Iniciar Hilo
        self.hilo_pdf = GeneradorPDFThread(lista_trabajos, self.carpeta_fotos, maquinas.mapa_rutas_completas())
        self.hilo_pdf.resultado.connect(self.pdf_finalizado)
        self.hilo_pdf.start()

        self.progreso_pdf.exec()

    def _generar_graficos_pdf(self, fecha_inicio=None, fecha_fin=None):
        """Renderiza a PNG (en el hilo principal, porque QWidget.grab() no se
        puede usar desde el QThread que genera el PDF) los mismos gráficos del
        dashboard, con el texto en negro para que se lean sobre fondo blanco,
        y los guarda en una carpeta temporal que el hilo del PDF borra al
        terminar. Si se indican fecha_inicio/fecha_fin ('YYYY-MM-DD'), los
        gráficos y los indicadores solo tienen en cuenta ese periodo, para
        que un PDF exportado por rango o por mes muestre sus propias
        estadísticas y no las de todo el histórico. Si no hay ninguna avería
        registrada en el periodo, no genera nada."""
        # Los datos salen del núcleo (los mismos que usa MantPro Web); aquí solo se pintan con Qt
        datos = informe_historial.datos_graficos(self.db, fecha_inicio, fecha_fin, sede=self.sede_filtro())
        if datos is None:
            return None

        ancho, alto = 760, 260
        color_fondo_pdf = "#f0f0f0"
        grafico_ranking = GraficoBarrasRanking(color="#c0392b", color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_ranking.establecer_datos(datos["ranking"])
        grafico_ranking.resize(ancho, alto)

        grafico_mensual = GraficoBarrasMensual(color="#e67e22", color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_mensual.establecer_datos(datos["mensual"])
        grafico_mensual.resize(ancho, alto)

        grafico_pie = GraficoCircularTrabajos(color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_pie.establecer_datos(datos["pie"])
        grafico_pie.resize(ancho, alto)

        tmp_dir = tempfile.mkdtemp(prefix="mantpro_pdf_graficos_")
        png_ranking = os.path.join(tmp_dir, "ranking.png")
        png_mensual = os.path.join(tmp_dir, "mensual.png")
        png_pie = os.path.join(tmp_dir, "pie.png")
        grafico_ranking.grab().save(png_ranking, "PNG")
        grafico_mensual.grab().save(png_mensual, "PNG")
        grafico_pie.grab().save(png_pie, "PNG")

        return dict(datos, png_ranking=png_ranking, png_mensual=png_mensual, png_pie=png_pie, tmp_dir=tmp_dir)

    def pdf_finalizado(self, exito, mensaje):
        self.progreso_pdf.accept() # Cierra el diálogo de progreso
        if exito:
            QMessageBox.information(self, t("title_exito"), mensaje)
        else:
            QMessageBox.critical(self, t("title_error_pdf"), mensaje)
