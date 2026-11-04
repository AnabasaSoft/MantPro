# 💾 Copias de Seguridad

> Documentación técnica de [MantPro](../README.es.md). In English: [backups.md](backups.md).


MantPro distingue entre dos tipos de copia, pensados para momentos distintos:

## Backup automático

Se hace solo, sin intervención, y está pensado para no notarse aunque pasen los
años. La lógica vive en el motor (`mantpro/nucleo/copias.py`, sin Qt), para que
un futuro servidor sin ventana la use igual.

**Cuándo** (se configura en `Archivo > 🛡️ Copias automáticas…`, solo
administradores):

- Siempre **al cerrar** la aplicación (con una ventana de progreso; el cierre
  real espera a que termine).
- **Cada cierto tiempo mientras está abierta** (por defecto, cada 2 horas), solo
  si ha habido cambios. Antes solo se copiaba al cerrar: si el PC pasaba el día
  encendido y el disco fallaba, se perdía el día, también lo que habían mandado
  los móviles (que ya lo habían quitado de sus colas).
- **Al poco de recibir datos de un móvil** (10 minutos después del último envío,
  para hacer una sola copia por sincronización).
- **Al abrir**, si quedaron cambios sin copiar (la copia del cierre falló o la
  aplicación se cerró de golpe).

Las copias hechas con la aplicación abierta van en segundo plano, y nunca hay
dos a la vez. Para saber si ha habido cambios se mira el tamaño y la fecha de
las bases de datos (y de su `-wal`) y las fotos que hay.

**Qué se guarda** (carpeta `backups_auto`):

- **Bases de datos**: `mantenimiento.db` y `almacen.db` se empaquetan enteras
  (copia coherente con la API de copia de SQLite y `integrity_check`) en un ZIP
  (`auto_backup_db_<fecha>.zip`) cada vez. Se guardan las **10 más recientes y,
  además, la última de cada uno de los últimos 14 días** (los dos números se
  configuran). Antes eran solo las 3 últimas, que con copias cada 2 horas no
  llegarían ni a un día.
- **Fotos**: en vez de volver a comprimir todo el historial de fotos en cada
  copia, se mantienen unos ZIP incrementales **por mes**
  (`fotos_backup_<año>-<mes>.zip`): cada copia solo añade las fotos que todavía
  no estuvieran en ninguno. Por mes, y no por año, para que el único que cambia
  (el del mes en curso) sea pequeño al mandarlo a la carpeta externa. Los ZIP
  antiguos por año (`fotos_backup_<año>.zip`) siguen valiendo: al restaurar se
  leen todos los `fotos_backup_*.zip`. Una foto llegada hace menos de 30
  segundos (que puede estar escribiéndose) se deja para la copia siguiente.

**Carpeta externa** (opcional): una copia en el mismo disco no sirve si el disco
muere. Se puede elegir una carpeta en un NAS, un disco USB o una carpeta
sincronizada con la nube (Nextcloud, Dropbox, Google Drive…). Después de cada
copia se manda allí el ZIP de las bases de datos y los ZIP de fotos que hayan
cambiado (comparando tamaño y fecha), a un temporal que se renombra al final, y
allí se aplica la misma regla de cuántas copias se guardan (los ZIP de fotos no
se borran nunca del destino). La carpeta externa tiene la misma estructura que
`backups_auto`, así que se restaura desde ella con `Archivo > Restaurar >
Restaurar desde copia automática...`. Si la carpeta está en el mismo disco que
los datos, el diálogo lo avisa. El destino está detrás de una interfaz
(`DestinoCarpeta`: comprobar, listar, subir, abrir y borrar) para poder añadir
otros (S3, SFTP…) sin tocar el resto.

**Prueba de restauración**: después de cada copia se comprueba que se puede
restaurar, en este equipo y en la carpeta externa, sin tocar los datos de
verdad: se sacan las bases de datos de la copia a un temporal (descifrándolas
si la copia está cifrada), se abren, se pasa `integrity_check` y se lee su tabla
principal; se mira que todas las fotos estén en los ZIP de fotos y se leen
enteras 5 al azar (comprueba el CRC o el cifrado). También se puede lanzar a
mano (`🧪 Probar restauración ahora`).

**Estado y avisos**: el resultado se guarda en `estado_copias.json`, en la
carpeta de datos y fuera de las bases de datos (restaurar una copia no borra el
registro de las copias); la configuración, en `config_copias.json`. La barra de
estado muestra «🛡️ Última copia: <fecha>», o «⚠️ Copias: revisar» en rojo si
la última copia falló, si la prueba de restauración falló o si no se pudo
mandar a la carpeta externa (al pulsarlo se abre el diálogo). Cada problema se
avisa con una ventana una vez por sesión (un disco USB desconectado no salta
cada 2 horas). Los cambios de configuración quedan en el registro de cambios.

## Backup manual (menú Archivo)

`Archivo > Backup` sigue generando, como siempre, un único ZIP
(`backup_completo_<fecha>.zip`) con las dos bases de datos y **todas** las fotos
juntas y comprimidas, en la ubicación que elijas. `Archivo > Restaurar` se abre
como submenú con dos opciones: **"Restaurar..."**, para elegir cualquier ZIP a
mano, y **"Restaurar desde copia automática..."**, que abre directamente la
carpeta `backups_auto`. En ambos casos, si el ZIP elegido es un backup
automático, se restaura primero la base de datos y, con ella ya restaurada, se
calcula qué fotos hacen falta y se extraen únicamente de los
`fotos_backup_*.zip` correspondientes, en vez de volcarlas todas. Las tres
operaciones (backup, y ambas restauraciones) muestran su propia barra de
progreso con foco.

## Copias cifradas con contraseña

`Archivo > 🔒 Contraseña de las copias…` (solo administradores) hace que todas
las copias (la manual, la automática al cerrar y las previas a borrar o
importar) se guarden cifradas. Siguen siendo ZIP normales, pero cada fichero de
dentro va cifrado por separado y con `.mpc` añadido al nombre
(`mantenimiento.db.mpc`, `fotos/…jpg.mpc`); así los ZIP de fotos por año pueden
seguir creciendo poco a poco, y una versión antigua de MantPro que no sepa
descifrar no restaura nada encima de los datos buenos.

- **Cifrado**: AES-256-GCM, que además detecta cualquier cambio o daño en la
  copia (si se ha tocado, no se restaura). Los datos se comprimen antes de
  cifrar.
- **Clave**: sale de la contraseña con scrypt (n=2¹⁷, r=8, p=1) y una sal
  aleatoria. No se usa el cifrado AES estándar de los ZIP (WinZip AES) porque
  saca la clave con PBKDF2-SHA1 de solo 1000 vueltas, que se rompe por fuerza
  bruta con facilidad. Por eso las copias cifradas solo se abren con MantPro,
  no con 7-Zip.
- **En el equipo** se guarda la clave derivada (nunca la contraseña) en
  `clave_copias.json`, en la carpeta de datos, para que la copia automática al
  cerrar se cifre sin preguntar. Ese fichero no va dentro de las copias. Lo que
  se protege son las copias que salen del equipo (USB, NAS, nube); para el
  propio equipo, usa el cifrado de disco completo.
- **Restaurar**: en el mismo equipo no se pide la contraseña. En otro equipo (o
  con una copia hecha con una contraseña anterior) se pide; si ese equipo aún no
  tenía contraseña de copias, se queda con la de la copia restaurada.
- **Cambiar o quitar la contraseña**: con la casilla «Aplicar también a las
  copias que ya hay», se rehacen con la nueva (o sin cifrar) las copias de las
  carpetas `backups` y `backups_auto`, manteniendo sus fechas. Las copias que
  hayas guardado en otros sitios siguen con la contraseña que tenían.
- **Si se olvida la contraseña**, las copias cifradas no se pueden recuperar.
- **Con las bases de datos cifradas** (*Herramientas → Cifrado de las bases de
  datos*), las copias llevan igualmente las bases de datos **sin cifrar**, para
  poder restaurarlas en otro equipo sin su clave; protégelas con esta
  contraseña. Al restaurar sobre una base de datos cifrada, sigue cifrada.

Formato de cada fichero cifrado:

```
"MPC1" (4) | sal (16) | comprobación (8) | nonce (12) | datos (zlib + AES-256-GCM) | etiqueta (16)
```

La comprobación son los 8 primeros bytes de HMAC-SHA256(clave, "MantPro copia
cifrada"), para saber si la contraseña es buena sin descifrar nada; el nombre
original del fichero va como dato autenticado. El código está en
`mantpro/nucleo/cifrado_copias.py`.

Al restaurar, las bases de datos se descifran y se comprueban
(`PRAGMA integrity_check`) antes de tocar nada, y se escriben con la API de
copia de SQLite, que respeta las conexiones abiertas y el fichero `-wal`.

## Limpieza de fotos huérfanas

`Herramientas > Limpiar fotos huérfanas` borra las fotos de `fotos_recibidas`
que ya no estén referenciadas por ningún trabajo, pendiente o máquina. Al cerrar
la aplicación y antes de un backup manual también se limpia `fotos_recibidas`
en silencio, pero **solo** esa opción del menú Herramientas revisa además los
`fotos_backup_<año>.zip` y los reescribe sin las fotos huérfanas que pudieran
contener, para no arrastrarlas indefinidamente.

## Tiempo máximo de guardado de trabajos

`Herramientas > Tiempo máximo de guardado de trabajos…` (solo administradores)
pide un número y una unidad (años, meses o días) y borra del historial todos
los trabajos anteriores a esa fecha, contando desde hoy. Antes de borrar
muestra cuántos trabajos se van a eliminar y entre qué fechas, y pide
confirmación.

- Antes de borrar se guarda una copia de las dos bases de datos en
  `backups_auto/antes_borrado_trabajos_<fecha>.zip`, que la rotación del
  backup automático no elimina.
- Se borran también sus fotos (antes, después y colección), salvo las que
  siga usando otro registro. Las fotos no van en esa copia previa, pero siguen
  en los `fotos_backup_<año>.zip` del backup automático hasta que se use
  `Herramientas > 🧹 Limpiar Fotos Basura`.
- Los móviles quitan esos trabajos de su historial en la siguiente
  sincronización.
- Es un borrado puntual: no se repite solo.
