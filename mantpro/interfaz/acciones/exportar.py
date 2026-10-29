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

"""Exportación a CSV, Excel y PDF, y logo del PDF."""

import os
import shutil
import tempfile
import re
import csv
from datetime import datetime
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QMessageBox, QDialog, QFileDialog, QProgressBar
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QPixmap

from ... import idiomas
from ...idiomas import t
from ..comun import tt
from ..dialogos.trabajos import DialogoExportarPDF, DialogoFiltroTecnico
from ..hilos import GeneradorPDFThread
from ..widgets.graficos import GraficoBarrasMensual, GraficoBarrasRanking, GraficoCircularTrabajos
from ...nucleo import usuarios, maquinas
from ...nucleo.rutas import DATA_DIR

class AccionesExportar:
    """Exportación a CSV, Excel y PDF, y logo del PDF.

    Mixin de MaintenanceApp: sus métodos usan el estado de la ventana
    principal (self.db, self.tabs...) como si estuvieran en la propia clase."""

    def exportar_csv(self):
        dlg = DialogoFiltroTecnico(self, t("title_exportar_csv"))
        if not dlg.exec(): return
        filtro_usuario = dlg.get_filtro()
        nombre_limpio = re.sub(r'[<>:\"/\\\\|?*]', '', filtro_usuario) if filtro_usuario else ""
        sufijo = f"_{nombre_limpio}" if nombre_limpio else ""
        nombre_defecto = f"Mantenimiento_{QDate.currentDate().toString('yyyyMMdd')}{sufijo}.csv"
        archivo = self.guardar_archivo_dialogo(t("title_exportar_csv"), nombre_defecto, "CSV (*.csv)")
        if not archivo: return
        try:
            datos = self.db.obtener_todas_cronologico(filtro_usuario)
            mapa_maquinas = maquinas.mapa_rutas_completas()
            with open(archivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                # Nuevos encabezados sin Tags, añadiendo Máquina, Foto Antes y Foto Después
                writer.writerow([tt("hdr_id", "ID"), tt("hdr_fecha", "Fecha"), tt("hdr_descripcion", "Descripción"), tt("hdr_maquina", "Máquina"), tt("hdr_realizado_por", "Realizado por"), tt("hdr_foto_antes", "Foto Antes"), tt("hdr_foto_despues", "Foto Después")])
                for tarea in datos:
                    # Convertir formato de fecha de YYYY-MM-DD al formato corto del idioma activo
                    fecha_formateada = idiomas.formato_fecha_localizada(tarea[1])

                    # Limpiamos FOTO y REF de la descripción
                    desc_limpia = re.sub(r"\[FOTO.*?:.*?\]", "", tarea[2])
                    desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                    # Extraer nombres de fotos
                    foto_antes = "-"
                    m = re.search(r"\[FOTO:\s*(.*?)\]", tarea[2])
                    if m: foto_antes = m.group(1).split("]")[0].strip()

                    foto_despues = "-"
                    m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", tarea[2])
                    if m_d: foto_despues = m_d.group(1).split("]")[0].strip()

                    autor = tarea[4] if len(tarea) > 4 and tarea[4] else usuarios.ETIQUETA_HISTORICO
                    maquina_nombre = mapa_maquinas.get(tarea[5], "-") if len(tarea) > 5 and tarea[5] else "-"
                    writer.writerow([tarea[0], fecha_formateada, desc_limpia, maquina_nombre, autor, foto_antes, foto_despues])
            QMessageBox.information(self, t("title_exportado"), t("msg_csv_guardado"))
        except Exception as e: QMessageBox.critical(self, t("title_error"), str(e))

    def exportar_excel(self):
        try: import xlsxwriter
        except ImportError: QMessageBox.warning(self, t("title_falta_libreria"), t("msg_instalar_xlsxwriter")); return
        dlg = DialogoFiltroTecnico(self, t("title_exportar_excel"))
        if not dlg.exec(): return
        filtro_usuario = dlg.get_filtro()
        nombre_limpio = re.sub(r'[<>:\"/\\\\|?*]', '', filtro_usuario) if filtro_usuario else ""
        sufijo = f"_{nombre_limpio}" if nombre_limpio else ""
        nombre_defecto = f"Mantenimiento_{QDate.currentDate().toString('yyyyMMdd')}{sufijo}.xlsx"
        archivo = self.guardar_archivo_dialogo(t("title_exportar_excel"), nombre_defecto, "Excel (*.xlsx)")
        if not archivo: return
        try:
            workbook = xlsxwriter.Workbook(archivo)
            worksheet = workbook.add_worksheet("Registro")

            # Estilos profesionales
            bold = workbook.add_format({'bold': True, 'bg_color': '#3daee9', 'color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
            wrap = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
            center = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'border': 1})

            # Nuevos encabezados
            headers = [tt("hdr_id", "ID"), tt("hdr_fecha", "Fecha"), tt("hdr_descripcion", "Descripción"), tt("hdr_maquina", "Máquina"), tt("hdr_realizado_por", "Realizado por"), tt("hdr_foto_antes", "Foto Antes"), tt("hdr_foto_despues", "Foto Después")]
            for col, text in enumerate(headers): worksheet.write(0, col, text, bold)

            # Ajuste de anchura de columnas
            worksheet.set_column('A:A', 5)
            worksheet.set_column('B:B', 12)
            worksheet.set_column('C:C', 60) # Descripción ancha
            worksheet.set_column('D:D', 25) # Máquina
            worksheet.set_column('E:E', 20) # Realizado por
            worksheet.set_column('F:F', 25) # Foto Antes
            worksheet.set_column('G:G', 25) # Foto Después

            # --- FUNCIÓN INTERNA PARA CALCULAR LA ESCALA PERFECTA ---
            def obtener_opciones_img(ruta_img):
                pix = QPixmap(ruta_img)
                if pix.isNull() or pix.width() == 0 or pix.height() == 0:
                    return None

                # Tamaño máximo deseado en píxeles (para que quepa justo en la celda)
                max_w = 160.0
                max_h = 100.0

                # Calcular escala manteniendo la proporción real de la foto
                scale = min(max_w / pix.width(), max_h / pix.height())

                return {
                    'x_scale': scale,
                    'y_scale': scale,
                    'x_offset': 5,
                    'y_offset': 5,
                    'object_position': 1
                }

            datos = self.db.obtener_todas_cronologico(filtro_usuario)
            mapa_maquinas = maquinas.mapa_rutas_completas()
            row = 1
            for tarea in datos:
                # Convertir formato de fecha al formato corto del idioma activo
                fecha_formateada = idiomas.formato_fecha_localizada(tarea[1])

                worksheet.write(row, 0, tarea[0], center)
                worksheet.write(row, 1, fecha_formateada, center)

                # Limpieza de texto
                desc_limpia = re.sub(r"\[FOTO.*?:.*?\]", "", tarea[2])
                desc_limpia = re.sub(r"\[REF:.*?\]", "", desc_limpia).strip()

                worksheet.write(row, 2, desc_limpia, wrap)

                maquina_nombre = mapa_maquinas.get(tarea[5], "-") if len(tarea) > 5 and tarea[5] else "-"
                worksheet.write(row, 3, maquina_nombre, center)

                autor = tarea[4] if len(tarea) > 4 and tarea[4] else usuarios.ETIQUETA_HISTORICO
                worksheet.write(row, 4, autor, center)

                # Incrustar FOTO ANTES
                m = re.search(r"\[FOTO:\s*(.*?)\]", tarea[2])
                if m:
                    nombre = m.group(1).split("]")[0].strip()
                    ruta = os.path.join(self.carpeta_fotos, nombre)
                    if os.path.exists(ruta):
                        opc = obtener_opciones_img(ruta)
                        if opc:
                            try: worksheet.insert_image(row, 5, ruta, opc)
                            except: worksheet.write(row, 5, "Err Img", center)
                        else:
                            worksheet.write(row, 5, "Err Img", center)
                    else: worksheet.write(row, 5, "No File", center)
                else: worksheet.write(row, 5, "-", center)

                # Incrustar FOTO DESPUÉS
                m_d = re.search(r"\[FOTO_DESPUES:\s*(.*?)\]", tarea[2])
                if m_d:
                    nombre_d = m_d.group(1).split("]")[0].strip()
                    ruta_d = os.path.join(self.carpeta_fotos, nombre_d)
                    if os.path.exists(ruta_d):
                        opc = obtener_opciones_img(ruta_d)
                        if opc:
                            try: worksheet.insert_image(row, 6, ruta_d, opc)
                            except: worksheet.write(row, 6, "Err Img", center)
                        else:
                            worksheet.write(row, 6, "Err Img", center)
                    else: worksheet.write(row, 6, "No File", center)
                else: worksheet.write(row, 6, "-", center)

                worksheet.set_row(row, 90) # Altura de fila fija
                row += 1

            workbook.close()
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
        cond_u = " AND usuario_nombre = ?" if filtro_usuario else ""
        param_u = [filtro_usuario] if filtro_usuario else []

        try:
            conn = self.db.conectar()
            c = conn.cursor()
            lista_trabajos = []

            if modo == "RANGO" and inicio and fin:
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id FROM tareas "
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
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id FROM tareas "
                          "WHERE 1=1" + cond_u + " ORDER BY fecha DESC, id DESC", param_u)
                datos = c.fetchall()
                if not datos: return
                nombre_defecto = f"Reporte_Histórico_Completo_{datetime.now().strftime('%Y%m%d')}.pdf"
                archivo = self.guardar_archivo_dialogo(t("title_guardar_pdf"), nombre_defecto, "PDF (*.pdf)")
                if not archivo: return
                lista_trabajos.append({"archivo": archivo, "titulo": t("titulo_reporte_historico") + sufijo_u, "datos": datos, "rango": None})

            elif modo == "MESES":
                c.execute("SELECT fecha, descripcion, tags, COALESCE(usuario_nombre,''), maquina_id FROM tareas "
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
        indicadores = maquinas.indicadores_fiabilidad_global(fecha_inicio, fecha_fin)
        if indicadores["num_averias"] == 0:
            return None

        registros = self.db.obtener_todas_cronologico()
        if fecha_inicio and fecha_fin:
            registros = [r for r in registros if r[1] and fecha_inicio <= r[1] <= fecha_fin]
        total = len(registros)
        c_elec = sum(1 for r in registros if "eléctrico" in r[3].lower() or "electrico" in r[3].lower())
        c_mec = sum(1 for r in registros if "mecánico" in r[3].lower() or "mecanico" in r[3].lower())
        c_prev = sum(1 for r in registros if "preventivo" in r[3].lower())
        c_urg = sum(1 for r in registros if "urgente" in r[3].lower() or "avería" in r[3].lower())
        datos_pie = [
            (tt("tag_electrico", "Eléctrico"), c_elec), (tt("tag_mecanico", "Mecánico"), c_mec),
            (tt("tag_preventivo", "Preventivo"), c_prev), (tt("tag_urgente", "Urgente"), c_urg),
        ] if total else []

        ancho, alto = 760, 260
        color_fondo_pdf = "#f0f0f0"
        grafico_ranking = GraficoBarrasRanking(color="#c0392b", color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_ranking.establecer_datos(maquinas.ranking_averias(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin))
        grafico_ranking.resize(ancho, alto)

        grafico_mensual = GraficoBarrasMensual(color="#e67e22", color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_mensual.establecer_datos(maquinas.averias_por_mes(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin))
        grafico_mensual.resize(ancho, alto)

        grafico_pie = GraficoCircularTrabajos(color_texto="#000000", color_fondo=color_fondo_pdf)
        grafico_pie.establecer_datos(datos_pie)
        grafico_pie.resize(ancho, alto)

        tmp_dir = tempfile.mkdtemp(prefix="mantpro_pdf_graficos_")
        png_ranking = os.path.join(tmp_dir, "ranking.png")
        png_mensual = os.path.join(tmp_dir, "mensual.png")
        png_pie = os.path.join(tmp_dir, "pie.png")
        grafico_ranking.grab().save(png_ranking, "PNG")
        grafico_mensual.grab().save(png_mensual, "PNG")
        grafico_pie.grab().save(png_pie, "PNG")

        return {
            "png_ranking": png_ranking, "png_mensual": png_mensual, "png_pie": png_pie,
            "indicadores": indicadores, "tmp_dir": tmp_dir,
        }

    def pdf_finalizado(self, exito, mensaje):
        self.progreso_pdf.accept() # Cierra el diálogo de progreso
        if exito:
            QMessageBox.information(self, t("title_exito"), mensaje)
        else:
            QMessageBox.critical(self, t("title_error_pdf"), mensaje)
