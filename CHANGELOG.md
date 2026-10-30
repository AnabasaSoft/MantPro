# Cambios en MantPro

Registro de los cambios de cada versión. Lo nuevo se va apuntando en **Sin publicar** según se hace; al publicar una versión final, esa sección pasa a llevar su número y es la base de la descripción de la release en GitHub.

Las versiones de pruebas (`v3.10.2-dev`, `v3.10.2-dev1`…) se publican como *pre-release* y no tienen sección propia: lo que llevan está en **Sin publicar** hasta que sale la versión final.

## Sin publicar

### Correcciones
- **Pestaña Registrar**: en pantallas bajas o al sacar la ventana de maximizada, los recuadros de las fotos y los botones «Añadir fotos» / «Quitar» se dibujaban unos encima de otros y el botón «Guardar registro» quedaba cortado. Ahora, si el formulario no cabe, aparece una barra de desplazamiento.

## 3.10.2 — 2026-10-30

### Novedades
- **👥 Estadísticas por técnico** (botón en el Dashboard): trabajos de cada técnico por año y mes, averías, preventivos, horas de parada y pendientes asignados ahora mismo, con gráfico de barras, filtrable por tipo (**todos**, **trabajos y averías** o **mantenimiento preventivo**) y exportable a **PDF** (con el logo de la empresa) y **Excel**.
- **Ayuda → 📖 Instrucciones (F1)** en el PC: manual por apartados (primeros pasos, usuarios, cada pestaña, menús Archivo y Herramientas, apps del móvil y problemas frecuentes), con índice y buscador, en los 7 idiomas.
- **Las apps móviles siguen conectadas en segundo plano**: MantPro y MantPro Stock sincronizan (cada 5 s en pantalla, cada 30 s en segundo plano) y el PC las ve en línea hasta que se cierran del todo. Mientras están abiertas muestran una notificación permanente («Conectado al PC» / «Sin conexión con el PC») con un botón «Cerrar». El aviso de las 8:00 no cambia.
- **🔩 Repuestos de cada máquina**: qué artículos del almacén lleva cada máquina y cuántos, con su stock (en rojo bajo mínimo) y ubicación, debajo del árbol de Máquinas; exportable a PDF y Excel. En Stock de almacén cada artículo indica en qué máquinas se usa, y al crear o editar un artículo se le pueden asociar máquinas directamente. En el móvil, sin conexión: MantPro los muestra en la ficha de la máquina (la del QR) y MantPro Stock dice en qué máquinas se usa cada artículo.

### Mejoras
- En MantPro (móvil), la pestaña **«Local» pasa a llamarse «Nuevo»**, que describe mejor para qué sirve.
- Al crear una **submáquina**, toma por defecto la **zona de su máquina superior** (y la cambia si se elige otra superior, mientras no se haya elegido una zona a mano).
- **Aviso de repetidos**: al crear o renombrar una máquina, avisa si al mismo nivel ya hay otra con un nombre igual o muy parecido (p. ej. «Extractor de finos» / «Extracción de finos»); al crear o editar un artículo del almacén (en el PC y en MantPro Stock, también sin conexión), si ya hay otro con el mismo código o un nombre muy parecido. No avisa cuando solo cambia el número («Lora 1» / «Lora 2», «Grapa 8mm» / «Grapa 16mm»).
- **F1 contextual**: la ayuda se abre directamente en el apartado de la pestaña en la que estás.
- **Versión de openSUSE (OBS)**: *Ayuda → Buscar actualizaciones* indica que se actualiza con `zypper`, en vez de decir que se ejecuta «desde el código fuente».

### Correcciones
- **Versiones de pruebas** (`3.10.2-dev1`, `3.10.2-rc.1`…): el PC las leía mal (`3.10.2-dev1` como 3.10.21) y no avisaba de la versión final; las apps del móvil las tomaban por la 3.10.0 y avisaban de una «actualización» a una versión más antigua. Ahora se compara la parte numérica y la versión final va por delante de sus versiones de pruebas.
- **Temas claro y clásico**: los textos de los gráficos (Dashboard, Máquinas, Estadísticas) salían en gris muy claro y casi no se leían; los desplegables y campos numéricos no mostraban sus flechas; en el clásico, los botones, pestañas y recuadros apenas se distinguían del fondo (ahora tienen el relieve clásico); y la fecha del calendario tenía poco contraste.
- **Tema oscuro**: las filas alternas de las tablas (p. ej. Stock de almacén) salían casi blancas y el texto no se leía.
- **Avisos de actualización con versiones de pruebas** (PC y las dos apps): quien tiene instalada una versión de pruebas no veía las siguientes, porque GitHub no incluye las *pre-releases* en su «última versión», y además dos versiones de pruebas del mismo número se daban por iguales. Ahora, a quien tiene una versión estable solo se le ofrecen estables, y a quien ya tiene una de pruebas (`-dev`, `-beta`, `-rc`…) se le ofrece la más nueva, sea de pruebas o estable (`dev` < `dev.1` < `dev.3` < `beta` < `rc.1` < final).
- El workflow de OBS se salta las versiones de pruebas en vez de fallar.
- Las apps del móvil no compilaban con un tag de pruebas con punto (`v3.10.2-dev.1`): el número de versión interno se calculaba con el sufijo. Ahora sale solo de la parte numérica.

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
