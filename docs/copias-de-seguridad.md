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
