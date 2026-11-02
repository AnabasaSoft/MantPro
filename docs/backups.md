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

## Password-encrypted backups

`File > 🔒 Backup password…` (administrators only) makes every backup (manual,
automatic on closing, and the ones made before deleting or importing) be saved
encrypted. They are still regular ZIP files, but each file inside is encrypted
separately and gets `.mpc` added to its name (`mantenimiento.db.mpc`,
`fotos/…jpg.mpc`). That way the yearly photo ZIPs can keep growing little by
little, and an old MantPro version that cannot decrypt restores nothing over
the good data.

- **Encryption**: AES-256-GCM, which also detects any change or damage in the
  backup (a tampered backup is not restored). Data is compressed before being
  encrypted.
- **Key**: derived from the password with scrypt (n=2¹⁷, r=8, p=1) and a random
  salt. The standard ZIP AES encryption (WinZip AES) is not used because it
  derives the key with PBKDF2-SHA1 and only 1000 iterations, which is easy to
  brute-force. That is why encrypted backups can only be opened with MantPro,
  not with 7-Zip.
- **On the computer** the derived key (never the password) is kept in
  `clave_copias.json`, in the data folder, so the automatic backup on closing
  is encrypted without asking. That file is not included in the backups. What
  is protected are the backups that leave the computer (USB, NAS, cloud); for
  the computer itself, use full-disk encryption.
- **Restoring**: on the same computer the password is not asked for. On another
  computer (or with a backup made with an earlier password) it is; if that
  computer had no backup password yet, it takes the one from the restored
  backup.
- **Changing or removing the password**: with the "Also apply it to the
  backups already in MantPro's backup folders" box, the backups in `backups`
  and `backups_auto` are rewritten with the new password (or unencrypted),
  keeping their dates. Backups saved anywhere else keep their old password.
- **If the password is forgotten**, encrypted backups cannot be recovered.
- **With encrypted databases** (*Tools → Database encryption*), backups still
  contain the databases **unencrypted**, so they can be restored on another
  computer without its key; protect them with this password. Restoring over an
  encrypted database keeps it encrypted.

Format of each encrypted file:

```
"MPC1" (4) | salt (16) | check (8) | nonce (12) | data (zlib + AES-256-GCM) | tag (16)
```

The check is the first 8 bytes of HMAC-SHA256(key, "MantPro copia cifrada"),
used to know whether the password is right without decrypting anything; the
original file name is authenticated data. The code is in
`mantpro/nucleo/cifrado_copias.py`.

When restoring, the databases are decrypted and checked
(`PRAGMA integrity_check`) before anything is touched, and written with
SQLite's backup API, which respects open connections and the `-wal` file.

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
