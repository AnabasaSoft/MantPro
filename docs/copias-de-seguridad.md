# 💾 Copias de Seguridad

> Documentación técnica de [MantPro](../README.es.md). In English: [backups.md](backups.md).


MantPro distingue entre dos tipos de copia, pensados para momentos distintos:

## Backup automático (al cerrar la app)

Cada vez que se cierra el programa se hace, en segundo plano y sin necesidad de
intervención, un backup rápido pensado para no notarse aunque pasen los años:

- **Bases de datos**: `mantenimiento.db` y `almacen.db` se empaquetan enteras en
  un ZIP (`auto_backup_db_<fecha>.zip`) cada vez, rotando y conservando solo los
  3 más recientes.
- **Fotos**: en vez de volver a comprimir todo el historial de fotos en cada
  cierre, se mantienen unos ZIP incrementales por año (`fotos_backup_<año>.zip`):
  cada cierre solo añade a su ZIP del año que corresponda las fotos que todavía
  no estuvieran dentro, sin tocar ni recomprimir las de años anteriores. Así el
  tiempo de cierre no crece con el tiempo de uso de la aplicación.

Mientras se hace esta copia se muestra una ventana con una barra de progreso que
retiene el foco, y el cierre real de la aplicación espera a que termine.

## Backup manual (menú Archivo)

`Archivo > Backup` sigue generando, como siempre, un único ZIP
(`backup_completo_<fecha>.zip`) con las dos bases de datos y **todas** las fotos
juntas y comprimidas, en la ubicación que elijas. `Archivo > Restaurar` se abre
como submenú con dos opciones: **"Restaurar..."**, para elegir cualquier ZIP a
mano, y **"Restaurar desde copia automática..."**, que abre directamente la
carpeta `backups_auto`. En ambos casos, si el ZIP elegido es un backup
automático, se restaura primero la base de datos y, con ella ya restaurada, se
calcula qué fotos hacen falta y se extraen únicamente de los
`fotos_backup_<año>.zip` correspondientes, en vez de volcarlas todas. Las tres
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
