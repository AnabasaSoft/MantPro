# 📁 Project Structure

> Technical documentation of [MantPro](../README.md). En español: [desarrollo.md](desarrollo.md).


```
MantPro/
├── main.py                      # Entry point (python main.py)
├── mantpro/                     # Desktop app code
│   ├── version.py               # Version (CI sets it from the tag)
│   ├── nucleo/                  # Data and logic, no UI
│   │   ├── usuarios.py          # Users, passwords, roles and sessions
│   │   ├── almacen.py           # Warehouse stock: structure, materials and movements
│   │   ├── maquinas.py          # Machinery tree and its job history
│   │   ├── basedatos.py         # Jobs database
│   │   ├── conexion_bd.py       # Single entry to SQLite: encryption (SQLCipher) and keyring
│   │   ├── seguridad.py         # Sign-in attempt limit, photos, atomic writes
│   │   ├── certificado.py       # The server's own TLS certificate and its fingerprint
│   │   ├── cifrado_copias.py    # Password-encrypted backups
│   │   ├── estadisticas.py      # Statistics by technician
│   │   ├── nombres.py           # Duplicate or very similar name warning
│   │   ├── etiquetas.py         # QR labels for machines
│   │   ├── fotos.py             # Job photos (collection)
│   │   ├── rutas.py             # Data folder
│   │   └── importar.py          # Excel/CSV import
│   ├── interfaz/                # PyQt6 windows
│   │   ├── arranque.py          # Startup: single instance and sign-in
│   │   ├── app.py               # Main desktop application
│   │   ├── servidor.py          # Sync server for the phones
│   │   ├── pestanas/            # One per tab: dashboard, calendar, stock...
│   │   ├── acciones/            # Menu actions: backups, export, import, users
│   │   ├── dialogos/            # Dialogs (sign-in and user management included)
│   │   └── widgets/             # Photos and charts
│   └── idiomas/                 # Desktop translations (ES / EN / EU / CA / GL / PT / FR)
├── recursos/                    # Icons and logos
├── herramientas/                # Project scripts (verificar_idiomas.py...)
├── empaquetado/                 # Windows installer (Inno Setup)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── fotos_recibidas/             # Image folder
├── mantenimiento.db             # SQLite database (maintenance jobs)
├── almacen.db                   # SQLite database (warehouse stock, separate)
├── servidor_cert.pem / servidor_clave.pem  # Server TLS certificate (created by MantPro)
├── clave_copias.json            # Key for encrypted backups (if enabled)
├── clave_bd.json                # Encrypted-database key, only if there is no keyring
├── mantenimiento_app/           # Flutter mobile app (jobs)
│   ├── lib/main.dart            # Main mobile code
│   ├── lib/conexion_segura.dart # HTTPS with the PC's certificate pinned by its fingerprint
│   ├── lib/actualizador.dart    # Downloads and installs the new version
│   ├── lib/i18n/                # Mobile translations (ES / EN / EU / CA / GL / PT / FR)
│   ├── pubspec.yaml             # Flutter dependencies
│   └── android/                 # Android configuration
├── mantpro_stock_app/           # Flutter mobile app (warehouse stock)
│   ├── lib/modelos.dart         # Data models and stock colour rule
│   ├── lib/pantallas/           # Screens: warehouse, item, search, low stock...
│   ├── lib/i18n/                # Mobile translations (ES / EN / EU / CA / GL / PT / FR)
│   ├── pubspec.yaml             # Flutter dependencies
│   └── android/                 # Android configuration
├── backups/                     # Full manual backups (database + photos)
├── backups_auto/                # Automatic backups on close (rotating database + photos per year)
└── docs/                        # Additional documentation
```

> The data (database, photos and backups) does not necessarily live next to
> the code: if there is no `mantenimiento.db` in the current folder, the
> application uses `~/.local/share/MantPro` on Linux or `%APPDATA%\MantPro`
> on Windows.

## Running from source

On distributions that do not allow installing packages with `pip` outside a
virtual environment (openSUSE, Fedora, Debian…) and have no SQLCipher module for
Python, create an environment that uses the system packages and add only
SQLCipher to it:

```bash
python3 -m venv --system-site-packages venv
venv/bin/pip install sqlcipher3-wheels==0.5.7
venv/bin/python main.py
```

Without SQLCipher MantPro works the same, but it cannot open encrypted
databases. If you copy the encrypted databases from `~/.local/share/MantPro` to
the source folder, MantPro uses the key the keyring holds for that folder and
also saves it for the new one.

## Database

The application uses SQLite with the following tables:

- **`tareas`**: Record of completed jobs (date, description, tags, photos,
  **who did it** (`usuario_id` and `usuario_nombre`) and the **linked
  machine** (`maquina_id`), if any)
- **`maquinas`**: Machinery tree (name, parent machine, notes and photo)
- **`pendientes`**: Pending tasks (title, details, priority and **assigned
  technician**: `asignado_a` and `asignado_nombre`)
- **`usuarios`**: People who use the application (login, name, password
  hash, role and whether they are active)
- **`sesiones`**: Tokens of the linked phones, with their expiry date
- **`avisos_recurrentes`**: Maintenance alerts that repeat automatically
- **`dias_especiales`**: Public holidays, vacations and days marked on the calendar
- **`auditoria`**: History of who edits or deletes each job, with date,
  action and details
- **`config`**: Internal application settings (logo, province, etc.)

Passwords are stored with **PBKDF2-SHA256** (200,000 iterations and a
per-user salt), never in plain text. New tables and columns are created
automatically at startup, without losing existing data.

**Connections**: all code opens the databases with `conexion_bd.conectar()`
and uses the `sqlite3` exported by `mantpro/nucleo/conexion_bd.py` (never
`import sqlite3` or `sqlite3.connect` directly), because the databases may be
encrypted with **SQLCipher** (*Tools → Database encryption*). The key (256
random bits, the same for both databases) is kept in the system keyring with
`keyring` and passed raw (`PRAGMA key = "x'…'"`); to attach a database use
`conexion_bd.adjuntar()`. Encrypting and decrypting happen at startup, before
any connection is opened. Backups contain the databases unencrypted
(`copiar_sin_cifrar`) and, when restoring, `restaurar_desde_plano` encrypts
them again if needed. If `sqlcipher3` is not installed, Python's `sqlite3` is
used and the option is disabled.

> 🔐 `mantenimiento.db` contains password hashes and session tokens.
> It is in `.gitignore` for a reason: never push it to the repository.

Warehouse stock lives in its own database, **`almacen.db`**, deliberately
kept separate from the jobs database:

- **`estanterias`**: name and whether it has floor space
- **`baldas`**: shelves of each shelving unit, numbered from bottom to top
  (shelf `0` represents the floor space)
- **`secciones`**: subdivisions within each shelf
- **`materiales`**: code, name, description, unit, current stock, minimum
  stock, location (section) and photo
- **`movimientos`**: history of stock in and out, with date, quantity, user
  and reason

It is created automatically on first launch and included in backups (manual
and automatic on close) together with `mantenimiento.db`.
