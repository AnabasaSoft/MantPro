# 💾 Backups

> Technical documentation of [MantPro](../README.md). En español: [copias-de-seguridad.md](copias-de-seguridad.md).


MantPro distinguishes between two kinds of backup, meant for different moments:

## Automatic backup (when closing the app)

Every time the program is closed, a quick backup is made in the background
with no user intervention, designed to stay unnoticeable even as the years go by:

- **Databases**: `mantenimiento.db` and `almacen.db` are packed whole into a
  ZIP (`auto_backup_db_<date>.zip`) every time, rotating and keeping only the
  3 most recent.
- **Photos**: instead of recompressing the whole photo history on every
  close, incremental ZIPs are kept per year (`fotos_backup_<year>.zip`):
  each close only adds to the matching year's ZIP the photos that were not
  already in it, without touching or recompressing those from previous
  years. This way, closing time does not grow with how long the application
  has been in use.

While this backup runs, a window with a progress bar holds the focus, and the
application only actually closes once it has finished.

## Manual backup (File menu)

`File > Backup` still generates, as always, a single ZIP
(`backup_completo_<date>.zip`) with both databases and **all** the photos
together and compressed, in the location you choose. `File > Restore` opens
as a submenu with two options: **"Restore..."**, to pick any ZIP by hand,
and **"Restore from automatic backup..."**, which opens the `backups_auto`
folder directly. In both cases, if the chosen ZIP is an automatic backup,
the database is restored first and, with it restored, the photos that are
needed are worked out and extracted only from the matching
`fotos_backup_<year>.zip` files, instead of dumping them all. All three
operations (backup and both restores) show their own progress bar with focus.

## Cleaning up orphan photos

`Tools > Clean up orphan photos` deletes the photos in `fotos_recibidas`
that are no longer referenced by any job, pending task or machine. When the
application closes and before a manual backup, `fotos_recibidas` is also
cleaned silently, but **only** that option in the Tools menu also goes
through the `fotos_backup_<year>.zip` files and rewrites them without any
orphan photos they may contain, so they are not carried along forever.

## Maximum job retention time

`Tools > Maximum job retention time…` (administrators only) asks for a number
and a unit (years, months or days) and deletes from the history every job
older than that date, counting back from today. Before deleting it shows how
many jobs will be removed and between which dates, and asks for confirmation.

- A copy of both databases is saved first in
  `backups_auto/antes_borrado_trabajos_<date>.zip`, which the automatic backup
  rotation does not delete.
- Their photos (before, after and collection) are deleted too, except those
  still used by another record. Photos are not in that copy, but they remain
  in the automatic backup's `fotos_backup_<year>.zip` files until
  `Tools > 🧹 Clean Orphan Photos` is used.
- Phones remove those jobs from their history on the next sync.
- It is a one-off deletion: it does not repeat on its own.
