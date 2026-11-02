# Cambios en MantPro

Registro de los cambios de cada versión. Lo nuevo se va apuntando en **Sin publicar** según se hace; al publicar una versión final, esa sección pasa a llevar su número y es la base de la descripción de la release en GitHub.

Las versiones de pruebas (`v3.10.2-dev`, `v3.10.2-dev1`…) se publican como *pre-release* y no tienen sección propia: lo que llevan está en **Sin publicar** hasta que sale la versión final.

## Sin publicar

### Novedades
- **☑️ Listas de comprobación** en preventivos y trabajos (*Herramientas → ☑️ Listas de comprobación…*, solo administradores): plantillas reutilizables («Revisión mensual de compresor») con puntos que se marcan **bien / mal / no aplica** con una nota, y puntos de **lectura** que piden además un valor con su unidad (6,8 bar, 78 °C); si la lectura se sale del mínimo o el máximo, el punto queda como «mal» solo. Las plantillas se asignan a los avisos recurrentes y a los pendientes; al completarlos se pide rellenar la lista (si quedan puntos sin marcar avisa, pero deja completarlo) y queda guardada con el trabajo, aunque luego cambie la plantilla. En el historial, los trabajos con lista llevan ☑️ (☑️❌ si algún punto salió mal) y con el botón derecho se ve o se corrige. Las exportaciones del historial la incluyen: en el PDF bajo cada trabajo, con los puntos «mal» en rojo, y una columna en Excel y CSV. Revertir un trabajo a pendiente le devuelve su lista. **En la app MantPro**, los avisos y pendientes con lista llevan ☑️ y, al completarlos, se rellena en el móvil, también sin conexión (las plantillas se guardan en el móvil y lo rellenado se envía con el resto al sincronizar); el historial muestra el resumen («3 bien · 1 mal», en rojo si algo salió mal) y al tocarlo se ve la lista entera.

### Seguridad
- **Desactivar la conexión sin cifrar** (*Herramientas → 🔐 Sesiones de dispositivos*, solo administradores): la columna nueva «Cifrado» muestra si cada móvil se conecta por la conexión cifrada o todavía sin cifrar (app anterior a la 3.10.3), y abajo se avisa de cuántos quedan. Cuando no queda ninguno, un botón desactiva la conexión sin cifrar y el PC pasa a atender solo por HTTPS (también las fotos, que por HTTP se servían sin sesión). Los móviles con la app ya actualizada pero vinculados con el QR antiguo siguen pasando solos a la conexión cifrada. Se puede volver a permitir desde el mismo sitio.

### Mejoras
- **Ayuda (F1)**: apartado nuevo **🛡️ Seguridad y cifrado** (conexión cifrada con los móviles, bloqueo tras intentos fallidos, fotos comprobadas, bases de datos y copias cifradas y qué no se cifra), una nota sobre la conexión cifrada en «Apps del móvil» y tres problemas frecuentes nuevos: la clave de recuperación al abrir, «Demasiados intentos fallidos» y la contraseña que se pide al restaurar una copia. En los 7 idiomas.

### Correcciones
- **Bases de datos cifradas copiadas a otra carpeta** (p. ej. a la de una instalación portable o a la del código fuente): MantPro no encontraba su clave, porque el llavero la guarda a nombre de la carpeta de datos, y pedía la clave de recuperación. Ahora prueba también la clave de la carpeta de datos normal y, si abre las bases de datos, la guarda para la carpeta nueva.
- **MantPro (móvil)**: el botón para cancelar la descarga de una actualización salía como «btn_cancelar» (faltaba su traducción). Si la descarga o la instalación fallan, el aviso dice ahora el motivo.
- **Paquete de openSUSE (OBS) con cifrado de las bases de datos**: openSUSE no tiene el módulo de SQLCipher para Python, así que el paquete no podía abrir unas bases de datos cifradas con la versión de GitHub (avisaba de que «esta instalación no incluye SQLCipher»). Ahora el paquete compila ese módulo desde su código fuente, como el que llevan los binarios de GitHub, y el cifrado funciona igual. El paquete pasa de `noarch` a `x86_64` y depende de `python3-keyring`.

## 3.10.3 — 2026-11-02

### Seguridad
- **Sincronización cifrada (HTTPS)** entre el PC y los móviles. El PC crea su propio certificado y su huella va en el QR de vinculación: las apps solo se conectan a *ese* PC, así que nadie en la WiFi puede leer el tráfico ni hacerse pasar por él. Los móviles ya vinculados pasan solos a HTTPS al actualizar la app, sin volver a escanear. HTTPS usa el puerto siguiente al configurado (p. ej. 5001); el PC sigue atendiendo por HTTP en el configurado para las apps de versiones anteriores.
- **Bases de datos cifradas** (*Herramientas → 🔐 Cifrado de las bases de datos…*, solo administradores, desactivado por defecto): `mantenimiento.db` y `almacen.db` se guardan cifradas con SQLCipher (AES-256), así que quien copie los ficheros o se lleve el disco no puede leerlas. La clave se guarda en el llavero del sistema (Administrador de credenciales de Windows, KWallet / GNOME Keyring) y MantPro abre los datos solo; al activarlo se muestra una **clave de recuperación** para apuntar, que MantPro pide si el llavero pierde la clave. El cambio (y el de quitarlo) se hace al volver a abrir MantPro, comprobando las bases de datos antes de sustituirlas. Las copias de seguridad siguen llevando los datos sin cifrar (para poder restaurarlas en otro equipo): para protegerlas está la contraseña de las copias. No disponible en el paquete de openSUSE (no tiene el módulo de SQLCipher para Python). Dependencias nuevas: `sqlcipher3-wheels` y `keyring`.
- **Copias de seguridad cifradas con contraseña** (*Archivo → 🔒 Contraseña de las copias…*, solo administradores): la copia manual, la automática al cerrar y las previas a borrar o importar se guardan cifradas (AES-256), así que una copia que sale del equipo (USB, NAS, nube) no se puede abrir sin la contraseña. En el mismo equipo se restauran sin pedirla; en otro, sí (y ese equipo se queda con ella para sus copias). Al poner, cambiar o quitar la contraseña se pueden rehacer las copias que ya hay en las carpetas de copias. Si se olvida, las copias cifradas no se pueden recuperar. Una versión anterior de MantPro no restaura nada de una copia cifrada (no toca los datos).
- **Fotos con sesión**: por HTTPS, descargar una foto del PC exige haber iniciado sesión.
- **Límite de intentos de inicio de sesión**: desde los móviles, 5 fallos seguidos bloquean ese usuario 15 minutos y 20 fallos desde un mismo móvil lo bloquean igual; en la ventana del PC, 5 fallos bloquean un minuto. Las apps muestran cuánto hay que esperar.
- **Fotos recibidas de los móviles comprobadas**: solo se guardan imágenes de verdad (formato y contenido), de 30 MB como mucho y con un nombre que no puede salirse de su carpeta; los envíos de más de 300 MB se rechazan.
- **Token de sesión de las apps en el almacenamiento seguro de Android** (Keystore) en vez de en claro. Se pasa solo al actualizar, sin tener que volver a iniciar sesión.

### Novedades
- **Colección de fotos en las exportaciones del historial**: el PDF muestra debajo de cada trabajo sus fotos en miniatura (6 por línea), el Excel las incrusta en columnas «Colección 1, 2…» y el CSV lista sus nombres de fichero.
- **Herramientas → 📱 Instalar MantPro en móvil** y **📦 Instalar MantPro Stock en móvil**: un QR que, al escanearlo con la cámara del móvil, descarga la app de la última versión estable.

### Mejoras
- **Actualizar las apps del móvil desde la propia app**: el aviso de nueva versión de MantPro y MantPro Stock tiene los botones «Después» y «Actualizar». «Actualizar» descarga el APK con una barra de progreso y abre el instalador de Android, sin pasar por GitHub. La primera vez Android pide permitir que la app instale aplicaciones; al volver, la instalación empieza sola.
- **Menú Herramientas ordenado por grupos**: móviles y conexión (QR, sesiones de dispositivos, puerto), usuarios (contraseña, gestión de usuarios, registro de cambios), calendario (días y festivos, país o región), limpieza de datos (tiempo de guardado, fotos sin usar) e idioma.
- **Pestaña Registrar**: se quita el botón «Sincronizar App», que ya está en *Herramientas → 📲 Sincronizar App (QR)*.

### Correcciones
- **La 3.10.2 de Windows y Linux no arrancaba** («No module named 'mantpro.interfaz.dialogos.estadisticas'»): una línea de las estadísticas por técnico solo era válida desde Python 3.12, y al empaquetar con Python 3.10 PyInstaller dejaba fuera ese módulo sin avisar. El paquete de openSUSE no estaba afectado. La compilación de CI comprueba ahora que todo el código vale para Python 3.10 y que el ejecutable lleva todos los módulos de MantPro, SQLCipher y el llavero; si falta algo, no se publica.
- **Las versiones de pruebas se publican solas como *pre-release*** en GitHub. Antes había que marcarlas a mano: si se olvidaba, a quien usa la versión estable se le ofrecía la de pruebas y el QR de *Instalar en móvil* descargaba la de pruebas.
- **Restaurar una copia con MantPro abierto**: la base de datos se sobrescribía como fichero y podía mezclarse con el `-wal` que seguía en la carpeta. Ahora se comprueba la copia antes de tocar nada (si está dañada no se restaura) y se escribe con la API de copia de SQLite. Las fotos que no se puedan sacar de una copia automática se avisan en vez de saltarse en silencio.
- **Copias de seguridad que podían perder los últimos cambios**: con MantPro abierto, lo guardado más recientemente puede estar todavía en el fichero `-wal` de SQLite, y las copias solo guardaban el `.db`. Ahora se hace una copia consistente de cada base de datos, se comprueba su integridad (avisando si hay errores) y el ZIP se escribe en un temporal que solo se renombra al terminar, así que un corte a mitad no deja una copia rota.
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
