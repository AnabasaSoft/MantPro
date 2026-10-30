# Cambios en MantPro

Registro de los cambios de cada versión. Lo nuevo se va apuntando en **Sin publicar** según se hace; al publicar una versión final, esa sección pasa a llevar su número y es la base de la descripción de la release en GitHub.

Las versiones de pruebas (`v3.10.2-dev`, `v3.10.2-dev1`…) se publican como *pre-release* y no tienen sección propia: lo que llevan está en **Sin publicar** hasta que sale la versión final.

## Sin publicar

### Novedades
- **Ayuda → 📖 Instrucciones (F1)** en el PC: manual por apartados (primeros pasos, usuarios, cada pestaña, menús Archivo y Herramientas, apps del móvil y problemas frecuentes), con índice y buscador, en los 7 idiomas.
- **Las apps móviles siguen conectadas en segundo plano**: MantPro y MantPro Stock sincronizan (cada 5 s en pantalla, cada 30 s en segundo plano) y el PC las ve en línea hasta que se cierran del todo. Mientras están abiertas muestran una notificación permanente («Conectado al PC» / «Sin conexión con el PC») con un botón «Cerrar». El aviso de las 8:00 no cambia.

### Mejoras
- **Versión de openSUSE (OBS)**: *Ayuda → Buscar actualizaciones* indica que se actualiza con `zypper`, en vez de decir que se ejecuta «desde el código fuente».

### Correcciones
- **Versiones de pruebas** (`3.10.2-dev1`, `3.10.2-rc.1`…): el PC las leía mal (`3.10.2-dev1` como 3.10.21) y no avisaba de la versión final; las apps del móvil las tomaban por la 3.10.0 y avisaban de una «actualización» a una versión más antigua. Ahora se compara la parte numérica y la versión final va por delante de sus versiones de pruebas.
- El workflow de OBS se salta las versiones de pruebas en vez de fallar.

## 3.10.1 — 2026-10-29

- **Etiquetas QR por máquina**: PDF A4 con 24 etiquetas de 70 × 37 mm (pestaña Máquinas → 🏷️ Etiquetas QR) y escáner en MantPro que abre la ficha de la máquina, sin conexión.
- **Sincronización del móvil más rápida y con barra de progreso**: datos descargados a la vez y fotos de 4 en 4.
- **Estado en línea de los móviles** en *Sesiones de dispositivos* (conexión y último contacto) e icono de usuario verde/rojo en MantPro Stock.
- **Historial de movimientos de todo el almacén** (📜 Historial) y nombre del artículo en los traslados.
- **Paquete para openSUSE en OBS** (Tumbleweed y Slowroll), publicado automáticamente con cada release.

## 3.10.0 — 2026-10-29

- **Importar desde Excel/CSV**: máquinas, artículos, avisos y usuarios, una hoja o el libro entero, con plantilla, vista previa y copia de seguridad previa.
- **Código reorganizado** en carpetas (`mantpro/nucleo`, `mantpro/interfaz`…) y `main.py` troceado en módulos.
- **Archivo → 📤 Exportar** agrupa PDF, CSV y Excel.
- Corregido el número de versión interno de los APK (la 3.10.0 no se instalaba encima de la 3.9.21).
