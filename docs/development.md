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
├── mantenimiento_app/           # Flutter mobile app (jobs)
│   ├── lib/main.dart            # Main mobile code
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
