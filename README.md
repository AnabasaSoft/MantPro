🌐 **English** · [Español](README.es.md) · [Euskara](README.eu.md)

# MantPro

<p align="center">
  <img src="logo.png" alt="MantPro Logo" width="200"/>
</p>

<p align="center">
  <strong>Free and open source CMMS to manage preventive and corrective maintenance for your plant, workshop or fleet, from PC and Android.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Offline--first-✔-success.svg" alt="Offline-first">
  <img src="https://img.shields.io/badge/No%20subscription-100%25%20free-orange.svg" alt="No subscription">
</p>

---

## 🧩 What problem does it solve?

In many small and medium-sized workshops and plants, maintenance is tracked
with paper, a shared Excel file and WhatsApp messages. It works, until
someone needs to know **what has been done to a specific machine**, who did
it, when and with what material, and that information is spread across three
different places (or none at all).

**MantPro brings it all together**: each technician logs their work from
their phone, on the spot, with before and after photos if needed, and
everything is organised on the PC by machine, by date and by person, ready
to be looked up or turned into a PDF report.

## 🎯 Who is it for?

Designed for the people who run day-to-day maintenance, not for IT
departments: maintenance technicians, plant managers, workshops, industrial
SMEs and warehouse staff who need real control over machines, jobs and stock
without relying on scattered spreadsheets.

## 🆚 Why MantPro and not a commercial CMMS?

- **Open source and free**: open code under AGPL-3.0, with no limit on
  technicians, machines or records
- **No subscription**: no per-user or per-month fees
- **Your data, on your infrastructure**: the database lives on your own PC;
  you do not depend on a third-party cloud service still existing next year
- **Truly offline**: the phone works without an internet or PC connection
  for the whole working day, and syncs as soon as the network is back
- **Built from inside maintenance**: the features came from real workshop
  needs (before/after photos, machine links, spare parts stock, recurring
  alerts...), not from a generic CMMS requirements list

## 🎬 Demo video

https://github.com/user-attachments/assets/11572710-e0ba-4f8b-b914-0a959006d4fb

## 📸 Screenshots

### Desktop Application

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Dashboard" width="45%"/>
  <img src="Capturas/Almacen.png" alt="Warehouse management" width="45%"/>
</p>

### Mobile Application

<p align="center">
  <img src="Capturas/Dashboard-movil.jpg" alt="Mobile dashboard" width="30%"/>
  <img src="Capturas/Almacen-movil.jpg" alt="Mobile warehouse" width="30%"/>
  <img src="Capturas/Historial-movil.jpg" alt="Mobile history" width="30%"/>
</p>

---

## 📋 Table of Contents

- [What problem does it solve?](#-what-problem-does-it-solve)
- [Who is it for?](#-who-is-it-for)
- [Why MantPro?](#-why-mantpro-and-not-a-commercial-cmms)
- [Demo video](#-demo-video)
- [Screenshots](#-screenshots)
- [Downloads](#-downloads)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Users and Access](#-users-and-access)
- [Machinery](#-machinery)
- [Warehouse Stock](#-warehouse-stock)
- [PC-Mobile Sync](#-pc-mobile-sync)
- [Backups](#-backups)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [Roadmap](#-roadmap)
- [License](#-license)
- [Contact](#-contact)

---

## 📦 Downloads

You can download the prebuilt versions from [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: `.exe` executable for Windows
- **Linux**:
  - Linux executable binary
  - Portable AppImage
  - Also available on the **AUR** (Arch User Repository)
- **Android**: `.apk` files for direct installation
  - `MantPro.apk`: maintenance jobs app
  - `MantProStock.apk`: warehouse stock app

---

## ✨ Features

### 💻 Desktop Application (PC)

- **👥 User Management**: Username and password login, administrator and technician roles, adding and deactivating users, and password resets
- **✍️ Job Authorship**: Each job records who carried it out, visible in the history and in reports
- **🔒 Per-Record Permissions**: a technician can only edit or delete their own jobs; an administrator can manage any of them, including reassigning the author of one or several records at once
- **📋 Change Auditing**: a log of who edits or deletes each job (not just who created it), searchable and filterable by technician and action type from "Change log" (administrators only)
- **🔐 Device Sessions**: lists the phones linked to each user, with their real model, and lets you revoke one or several specific sessions without deactivating the whole user (administrators only). When someone signs in again from the same device, their previous session is replaced automatically instead of piling up
- **📊 Dashboard with KPIs and Charts**: cards for pending alerts, to-do tasks, records this month and plant-wide average MTBF/MTTR, plus charts of the machines with the most breakdowns and breakdowns per month, drawn without relying on external libraries
- **🎨 Visual Themes**: choose between dark mode (default), light mode or a retro style inspired by Windows 98, from the "Appearance" menu
- **📅 Interactive Calendar**: View and manage maintenance tasks with colour codes (public holidays, vacations, days with tasks)
- **📝 Full History**: A record of every job carried out, with before/after photos
- **📄 PDF Reports**: Automatic generation of professional reports with a customisable logo
- **📸 Image Management**: Storage and display of job photos
- **📱 Mobile Sync**: Built-in server (starts automatically) to sync with the mobile app via QR code
- **🔍 Search**: Advanced search by date, tags and content
- **👤 Filter by Technician**: Filter the history and exports (PDF, CSV and Excel) by the person who did the job
- **📦 Backup/Restore**: full manual backup (database + photos) choosing where to save it, incremental automatic backup when closing the app (see [Backups](#-backups)), and restore with a progress bar, with a `File > Restore` submenu to pick any manual backup or go straight to the automatic ones
- **🏷️ Tags**: Categorisation with labels (Urgent, Electrical, Mechanical, Preventive)
- **🔨 Pending Tasks**: Management of pending jobs (create, complete, edit, delete) and **assignment to a specific technician**
- **↩️ Revert to Pending**: if a job was completed by mistake, it can be sent back to Pending with one click from the history (with a warning if it had a linked machine, since that data would be lost), and it is recorded in the audit log
- **🔁 Reminders**: Maintenance alerts that repeat automatically
- **📦 Warehouse Stock Control**: Configurable structure of shelving units, shelves and sections, material records with photo, stock in/out with history and low-stock alerts
- **🏭 Machinery Control**: Tree of machines and sub-machines with an attached photo, job counter per year and month, and a direct link from every job logged or edited (see [Machinery](#-machinery))
- **📊 Export**: To PDF, CSV and Excel, with an optional technician filter and showing each job's machine/sub-machine, if it has one

### 📱 Mobile Application (Android)

- **🔐 User Sign-in**: Each technician signs in once and the session is kept on the device
- **📝 Quick Logging**: Capture jobs in the field, automatically signed with the user's name
- **📷 Built-in Camera**: Take photos and annotate them
- **✏️ Image Editor**: Draw on photos to mark areas of interest
- **🔄 Automatic Sync**: Data is sent to the PC automatically after pairing via QR code
- **💾 Local Storage**: Keeps records offline until they are synced
- **📋 Pending Jobs**: View and manage tasks assigned from the PC, with an **"Only mine"** filter
- **🔄 Catch-up on Open**: When it starts, the app syncs the data of every tab in the background
- **🔁 Manual Resync**: The Pending, History and Reminders tabs each have their own button to immediately resend whatever the phone has and the PC does not yet
- **↩️ Revert to Pending**: long-pressing a record in the History lets you send it back to the Pending tab if it was completed by mistake
- **🏷️ Quick Tags**: Fast tagging with checkboxes
- **🔌 Offline Mode**: Work without a connection and sync when you are able to
- **⏰ Daily Reminders**: Automatic notification at 8:00 AM (local time) if there are pending jobs not yet completed
- **🧰 Materials Used**: Add the warehouse materials you used to the job, searching by name or code; they are deducted from stock automatically when saving (see [Materials used in a job](#-warehouse-stock))
- **🏭 Link Machine**: Choose from a drop-down list the machine or sub-machine the job was done on, both when creating a new record and when editing one already synced in the history

### 📦 Mobile Stock Application (Android)

A standalone app (`mantpro_stock_app`) for checking and moving warehouse stock
from your phone without needing the jobs app.

- **🔐 User Sign-in**: uses the same user and session system as the jobs app
- **🗂️ Warehouse Browsing**: shelving unit > shelf > section tree, just like on the PC
- **🔎 Material Search**: by name, code, description or location
- **➕➖ Stock In and Out**: log stock movements from your phone, with an optional reason
- **🔀 Transfers**: moving a material to another section is recorded in its movement history
- **🎨 Visual Stock Indicator**: quantity in red below the minimum, in green above it and in the default colour if it matches exactly
- **⚠️ Low Stock**: a dedicated tab for materials on alert
- **🔄 Auto-refresh**: the screen refreshes itself when it detects changes, whether they were made on the phone itself or on the PC
- **🔌 Offline Mode**: browse the latest synced information when there is no connection to the PC
- **🔔 Daily Stock Check Reminder**: automatic notification at 8:00 AM (local time) inviting you to check the real quantity of 5 warehouse materials, picked at random and different each day; tapping it opens a screen to correct each quantity without searching for them by hand. If no materials have been added, no notification is shown

---

## 🔧 Requirements

### Desktop Application

- **Python**: 3.8 or later
- **Operating System**: Windows or Linux
- **Python dependencies**:
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - xlsxwriter
  - sqlite3 (included with Python)

### Mobile Application

Applies to both `mantenimiento_app` (jobs) and `mantpro_stock_app` (stock):

- **Flutter**: 3.0 or later
- **Dart SDK**: 2.17 or later
- **Android**: API Level 21+ (Android 5.0+)

---

## 📥 Installation

### Desktop Application

#### Option 1: Prebuilt Download (Recommended)

Download the version for your system from [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: Download and run the `.exe`
- **Linux**:
  - Download the executable binary and make it executable: `chmod +x mantpro`
  - Or use the **AppImage** (no installation): `chmod +x MantPro.AppImage && ./MantPro.AppImage`
  - The **`.deb`** and **`.rpm`** packages are digitally signed with GPG (see [Verifying the package signature](#-verifying-the-package-signature-linux))
  - **Arch Linux**: Available on the AUR: `yay -S mantpro` or `paru -S mantpro`

#### 🔏 Verifying the package signature (Linux)

The `.deb` and `.rpm` packages published in each release are signed with AnabasaSoft's official GPG key. To verify them before installing:

1. Download the public key from the repository ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)) to a file (**do not use `curl | rpm --import -`**: some versions of `rpm` cannot read the key from standard input and fail with `read failed`):
   ```bash
   curl -sL https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/firma/anabasasoft_public.asc -o /tmp/anabasasoft_public.asc
   ```

2. Import the key (only needed once per machine):
   ```bash
   # Fedora, openSUSE, RHEL... (.rpm package)
   sudo rpm --import /tmp/anabasasoft_public.asc

   # Debian, Ubuntu... (.deb package, requires dpkg-sig)
   gpg --import /tmp/anabasasoft_public.asc
   ```

3. Check that the key was imported correctly:
   ```bash
   rpm -qa 'gpg-pubkey*' --qf '%{name}-%{version}-%{release} --> %{summary}\n' | grep -i anabasasoft
   ```

4. Verify the signature of the downloaded package:
   ```bash
   # RPM
   rpm --checksig mantpro-*.rpm

   # DEB
   dpkg-sig --verify mantpro_*.deb
   ```
   A correct signature shows `OK` on the signature line (instead of `NOKEY` or `MISSING KEYS`).

A valid signature confirms that the package comes from AnabasaSoft and has not been modified.

#### Option 2: Installing from Source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AnabasaSoft/MantPro.git
   cd MantPro
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

### Mobile Application

#### Option 1: Direct Download (Recommended)

Download the matching `.apk` from [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) and install it on your Android device: `MantPro.apk` for jobs, `MantProStock.apk` for warehouse stock. They are independent apps and you can install either one or both.

**Note**: You may need to enable "Unknown sources" in your device's security settings.

#### Option 2: Building from Source

1. **Go to the mobile directory** (`mantenimiento_app` for jobs, `mantpro_stock_app` for stock):
   ```bash
   cd mantenimiento_app
   ```

2. **Install the dependencies**:
   ```bash
   flutter pub get
   ```

3. **Run on a device/emulator**:
   ```bash
   flutter run
   ```

4. **Build the APK (Android)**:
   ```bash
   flutter build apk --release
   ```

---

## 🚀 Usage

### Initial Setup

#### Desktop Application

1. **Start the application**: Run `python main.py` (the sync server starts on its own, there is no need to start it by hand)
2. **First sign-in**: On first launch the user `admin` is created with password `admin`. The application **forces you to change it** when you sign in
3. **Create the users**: `Tools` menu > `👥 User management` > add each technician
4. **Set up the logo** (optional): `File` menu > `📄 PDF Options` > `🖼️ Add / Change Logo`
5. **Log a job**: "📝 New Entry" tab > fill in summary/details > "💾 SAVE RECORD"
6. **Create a pending task**: "🔨 Pending" tab > "New Job" group (Title + Details + "Assign to") > "Add"

#### Mobile Application

1. **Install the app** on your mobile device
2. **Connect to the PC**:
   - Make sure the PC and the phone are on the same Wi-Fi network
   - On the PC: `Tools` menu > `📲 Sync App (QR)`
   - On the phone: tap "Link PC" and scan the code
3. **Sign in**: Enter the username and password the administrator created for you. The session is kept: you only need to do this once
4. **Done**: You can now log jobs from your phone

### Typical Workflow

#### From the PC

1. **Create and assign a pending task**:
   - "🔨 Pending" tab > "New Job" group > fill in Title and Details, choose the technician in "Assign to" > "Add"
   - Manage it with the "✅ Complete", "✏️ Edit", "❌ Delete" or "👤 Reassign" buttons
   - The "Show those of" drop-down filters the list by technician (including "Unassigned")

2. **Review completed jobs**:
   - Jobs synced from the phone appear automatically
   - Check photos (before/after) and details in the "📋 History" tab or in the "📅 Calendar"
   - The "Performed by" column shows who did each job, and the drop-down above lets you see only one person's jobs

3. **Generate reports**:
   - `File` menu > `📄 PDF Options` > `📄 Generate PDF Now`
   - In the dialog you can choose the technician, and their name appears in the report title
   - Or export to `📄 CSV` / `📊 Excel` from the same `File` menu

#### From the Phone

1. **Link to the PC and sign in** (only the first time, or if you change networks):
   - Tap "Link PC" and scan the QR code shown on the PC
   - Enter your username and password
   - The phone stores the PC's address and your session to sync automatically from then on

2. **Log a job**:
   - Tap "New" or pick a pending job already synced from the PC
   - With the "Only mine" chip you only see the jobs assigned to you
   - Fill in the title and details
   - Take a "before" photo and, optionally, an "after" photo with the camera
   - Draw/annotate on the photo if needed
   - Select the appropriate tags
   - Save

3. **Sync**:
   - When you open the app everything syncs in the background (you will see an indicator in the top bar)
   - You can also force it by pulling the list down or with the sync icon
   - Records are sent to the PC and removed from the phone once delivery is confirmed
   - Everything works offline: pending data is kept and uploaded when there is coverage

---

## 👥 Users and Access

### Roles

A single user can have **one or several roles at the same time** (for example,
technician and warehouse). Available roles:

| Role | Can do |
|-----|-------------|
| **Administrator** | Everything a technician and warehouse user can do, plus adding and deactivating users, changing roles, resetting passwords, editing or deleting **any** history record, reassigning the author of one or several records at once, and viewing the change audit log |
| **Technician** | Log jobs, complete pending tasks and alerts, edit or delete **only their own** history records, and change their own password |
| **Warehouse** | Add or edit materials and log stock in/out from the **MantPro Stock** mobile app |

There must always be **at least one active administrator**: the application
prevents removing the role from, or deactivating, the last one left.

> In the desktop application, any user (whatever their role) can log stock
> movements; the **Warehouse** role is what enables that same management
> (adding, editing and movements) from the phone.

### Management from the PC

- **Add**: `Tools` > `👥 User management` > fill in username, name,
  password and role > "➕ Add". If you leave "Require change at sign-in" ticked,
  the person will have to set their own password the first time they sign in.
- **Deactivate**: done **logically** (the user becomes inactive). Users are
  never deleted, so that the authorship of the jobs they already did is kept.
- **Reset password**: useful when someone forgets it. Changing it
  automatically closes all of that person's open sessions on the phone.
- **Change your own password**: `Tools` > `🔑 Change my password`.

### Device sessions

`Tools` > `🔐 Device sessions` (administrators only) lists every open mobile
session for every user, with the device model, when it started, when it
expires and whether it is still active or already expired. You can select one
or several rows at once and revoke them, which closes the session on that
phone without having to deactivate the whole user (which would close *all*
their devices in one go).

If a user signs in again from a device on which they already had an open
session (same manufacturer and model), that device's previous session is
deleted automatically when the new one is created, instead of piling up as
one more stray session in the list.

### Job authorship

Each record stores the technician who did it, whether it was created on the
PC or arrived from the phone. Records from before the user system was
introduced are marked as **`Histórico`** (legacy).

On the phone, attribution is **always decided by the server** from the
session token, never from data sent by the app. A device cannot sign jobs on
someone else's behalf.

On the PC, a technician can only edit or delete their own history records;
an administrator can do so with any of them. By right-clicking one or several
history rows (multiple selection with Ctrl/Shift), an administrator can also
**reassign the author** in bulk, with each change written to the audit log.

### Change log (audit)

Every time a job is edited or deleted, a record is kept of who did it, when
and what changed. Administrators can view it from `Tools` > `📋 Change log`,
with filters by technician and by action type (edit/delete).

### Session on the phone

The technician signs in once and the token is stored on the device. The
session ends on its own if the administrator deactivates the user or resets
their password; in that case the app returns to the sign-in screen **without
losing any records still waiting to be uploaded**.

---

## 🏭 Machinery

> Managed from the desktop application, with the machine link also
> selectable from the phone when logging or editing a job.

The PC's "🏭 Machines" tab is designed to keep track of breakdowns and work
on each piece of equipment over time.

- **🌳 Machinery tree**: machines can have sub-machines (for example, a
  line with several pieces of equipment), forming a hierarchy as deep as
  needed
- **📅 Jobs organised by year and month**: expanding a machine shows the
  years with jobs, and expanding a year shows the months; each level shows a
  count of how many jobs it has, loaded on demand so the tree stays fast
- **🖱️ Direct access to the job**: double-clicking a job in the tree opens
  its edit form directly
- **📸 Machine photo**: each machine or sub-machine can have an attached
  photo, shown in a box next to the tree when it is selected
- **🔗 Link from each job**: when logging a new job (PC or phone) or editing
  an existing one, you can choose which machine/sub-machine it belongs to
- **📊 In exports**: the linked machine or sub-machine appears as an extra
  column in PDF, CSV and Excel exports

---

## 📦 Warehouse Stock

> Fully managed from the desktop application, with lookups and movements
> also available from the phone (`mantpro_stock_app`). It lives in its own
> database (`almacen.db`), separate from the maintenance jobs database.

### Warehouse structure

The warehouse is organised in three levels, inspired by common warehouse
location coding conventions:

```
Shelving unit → Shelf → Section
```

- When creating a shelving unit you define the **number of shelves**, the
  **number of sections per shelf** (0 = no predefined sections, they can be
  added later) and whether it has **floor space** below the bottom shelf,
  which is handled as a special shelf ("Floor")
- Shelves are numbered from bottom to top starting at 1, so new shelves can
  be added without renumbering the existing ones
- A shelving unit, shelf or section cannot be deleted while it holds any
  material

The structure is managed from the **"⚙️ Configure warehouse"** button in the
"📦 Warehouse stock" tab, visible **to administrators only**.

### Materials

- Add and edit with code (optional), name, description, unit, minimum
  stock, location (shelving unit / shelf / section) and **attached photo**
- Search by **name, code, description or location**
- Stock is highlighted in **red** below the minimum, in **green** above it
  and in the default colour if it matches the minimum exactly, both on the
  PC and on the phone
- By selecting several materials at once (Ctrl/Shift + right click) on the
  PC you can **move them to another location** or **delete** them in bulk

### Stock in, stock out and transfers

- **Any user** can log stock in and out; only configuring the warehouse
  structure is restricted to administrators
- Each movement is recorded with date, quantity, user and an optional
  reason, visible in the history next to each material
- Stock-outs logged by hand (PC or `mantpro_stock_app`) cannot take stock
  below zero
- Changing a material's location is also recorded in its history, as a
  **transfer** movement (from which section to which section)

### Materials used in a job (MantPro)

When completing a job from the **MantPro** app (phone), you can add the
materials used by searching for them by name or code and entering the
quantity. When the job is saved, that material is automatically deducted
from the warehouse, with the reason "Used in job: ..." to keep it traceable.

Unlike manual stock-outs, **this deduction can take stock below zero**: the
material has already been physically used to do the job even if there was
not enough stock recorded, so blocking the movement would make no sense.
Negative stock is shown both on the PC and in `mantpro_stock_app`, and
serves as a warning that the material needs checking and restocking as soon
as possible.

### Low stock alerts

The **"⚠️ Low stock"** tab shows, in a separate view, the materials that
are out of stock or below the set minimum. The tab title itself shows how
many materials are on alert, and from there you can jump straight to the
material in "Warehouse stock" or log a stock-in without switching tabs.

---

## 🔄 PC-Mobile Sync

### How It Works

MantPro uses a sync system based on:

1. A **Flask server** built into the desktop app
2. **QR codes** for quick and secure pairing
3. A **token-authenticated REST API**: every data endpoint requires a valid
   session; if the token is no longer valid, the server responds with `401`
   and the phone goes back to the sign-in screen
4. **Local Wi-Fi** - no internet needed
5. **Full sync when the app opens**, in the background and without blocking
   the interface

> ⚠️ Traffic travels over **HTTP within the local network**. The user system
> provides traceability (knowing who did each job), not protection against
> someone with access to that same network.

### Network Setup

For sync to work:

- ✅ The PC and the phone must be on the **same Wi-Fi network**
- ✅ The **firewall** must allow connections on port 5000 (or the configured one)
- ✅ On Windows, you may need to create a firewall exception

### Troubleshooting

**The phone cannot connect to the PC:**
- Check that both devices are on the same network
- Check that the server is running on the PC (green icon)
- Try temporarily disabling the PC's firewall
- Regenerate the QR code and scan it again

**I cannot sign in from the phone:**
- Check that MantPro is open on the PC: sign-in is validated against it
- Check your username and password with the administrator; they can reset it
- If the PC's IP address has changed, scan the QR code again from the sign-in screen itself ("Link another PC")

**The app sent me back to the sign-in screen:**
- This is normal if the administrator has reset your password or deactivated your user
- Your records not yet uploaded **are not lost**: sign in again and they will sync

**I forgot the administrator password:**
- Another administrator can reset it from `Tools` > `👥 User management`
- If there is no other administrator, it has to be reset directly in the
  `usuarios` table of the database

**Photos are not syncing:**
- Check that there is enough space on the PC's disk
- Check the permissions of the `fotos_recibidas` folder
- Make sure the photo was saved correctly on the phone

**I do not get the daily pending alerts notification (Android):**
- Check that the notification permission is granted: `Settings → Apps → MantPro → Notifications`
- On brands such as **OPPO/Realme (ColorOS), Xiaomi (MIUI) or Huawei**, the system may kill the scheduled alarm even when the permission is granted. You also need to:
  - `Settings → Battery → App battery usage → MantPro` → set it to **"Unrestricted"**
  - `Settings → Battery → Auto-launch` → **enable** MantPro
- The notification is re-evaluated every time you open the Dashboard, so if you have just marked a job as completed, open it again so the notification is cancelled/rescheduled correctly.

**I do not get the daily stock check notification (MantPro Stock):**
- The same checks as for MantPro apply (notification permission and exclusion from battery optimisation, see above)
- If the warehouse has no materials added, no notification is shown: this is the expected behaviour
- It is re-evaluated every time the app syncs with the PC (when opening it and every 25 seconds while it is open)

---

## 💾 Backups

MantPro distinguishes between two kinds of backup, meant for different moments:

### Automatic backup (when closing the app)

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

### Manual backup (File menu)

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

### Cleaning up orphan photos

`Tools > Clean up orphan photos` deletes the photos in `fotos_recibidas`
that are no longer referenced by any job, pending task or machine. When the
application closes and before a manual backup, `fotos_recibidas` is also
cleaned silently, but **only** that option in the Tools menu also goes
through the `fotos_backup_<year>.zip` files and rewrites them without any
orphan photos they may contain, so they are not carried along forever.

---

## 📁 Project Structure

```
MantPro/
├── main.py                      # Main desktop application
├── usuarios.py                  # Users, passwords, roles and sessions
├── dialogos_usuarios.py         # PyQt6 dialogs: sign-in and user management
├── almacen.py                   # Warehouse stock: structure, materials and movements
├── maquinas.py                  # Machinery tree and its job history
├── idiomas.py                   # Desktop translations (ES / EN / EU)
├── requirements.txt             # Python dependencies
├── logo.png                     # Application logo
├── README.md                    # This file
├── fotos_recibidas/             # Image folder
├── mantenimiento.db             # SQLite database (maintenance jobs)
├── almacen.db                   # SQLite database (warehouse stock, separate)
├── mantenimiento_app/           # Flutter mobile app (jobs)
│   ├── lib/main.dart            # Main mobile code
│   ├── lib/i18n/strings.dart    # Mobile translations (ES / EN / EU)
│   ├── pubspec.yaml             # Flutter dependencies
│   └── android/                 # Android configuration
├── mantpro_stock_app/           # Flutter mobile app (warehouse stock)
│   ├── lib/modelos.dart         # Data models and stock colour rule
│   ├── lib/pantallas/           # Screens: warehouse, item, search, low stock...
│   ├── lib/i18n/strings.dart    # Mobile translations (ES / EN / EU)
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

### Database

The application uses SQLite with the following tables:

- **`tareas`**: Record of completed jobs (date, description, tags, photos,
  **who did it** (`usuario_id` and `usuario_nombre`) and the **linked
  machine** (`maquina_id`), if any)
- **`maquinas`**: Machinery tree (name, parent machine, notes and photo)
- **`pendientes`**: Pending tasks (title, details and **assigned
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

---

## 🤝 Contributing

Contributions are welcome! If you want to improve MantPro:

1. **Fork** the project
2. Create a **branch** for your feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. Open a **Pull Request**

### Improvement Ideas

- [X] Push notifications for reminders
- [X] More detailed statistics charts
- [ ] Google Calendar integration
- [X] Dark mode (and light mode, and a retro Windows 98-style theme)
- [X] Multi-language (Spanish, English, Basque, Catalan, Galician)
- [X] Excel export
- [X] Audit log of edits and deletions
- [X] Warehouse materials stock control
- [ ] API for integration with other systems
- [ ] Digital signature of completed jobs

---

## ✅ Done

- **User management**: username and password sign-in on PC and phone,
  multiple roles per user (administrator / technician / warehouse), logical
  adding and deactivation of users, password change and reset.
- **Job authorship**: each record stores who carried it out. Records from
  before the user system are marked as `Histórico` (legacy).
- **Persistent session on the phone**: the technician signs in once and the
  token is stored on the device.
- **Authenticated API**: every data endpoint requires a token; a `401`
  closes the session on the phone and returns to sign-in without losing the
  local records waiting to be sent.
- **Assigned pending tasks**: the PC assigns each job to a technician and the
  phone can filter by "Only mine".
- **Filter by technician** in the history and in PDF, CSV and Excel exports.
- **Edit auditing**: who edits or deletes a job is recorded (not just who
  created it), searchable and filterable by technician/action from
  "Change log".
- **Per-record permissions**: a technician can only edit or delete their own
  jobs; an administrator can manage any of them and reassign the author of
  one or several records at once (multiple selection + context menu).
- **Visual themes**: dark mode (default), light mode or classic Windows
  98 style, selectable from the "Appearance" menu and remembered between
  sessions.
- **On-demand backup with a choice of destination**: when making a manual
  backup you can choose where to save it, instead of always using the
  default `backups` folder.
- **Warehouse stock control**: configurable structure of shelving units,
  shelves and sections (administrators only), material records with photo,
  stock in/out with history (any user), transfers between locations recorded
  in the history, multiple selection with a context menu to move or delete in
  bulk, and a dedicated tab for materials out of stock or below their
  minimum. With its own database (`almacen.db`) and a standalone mobile app
  (`mantpro_stock_app`) to check and move stock from the phone.
- **Device sessions**: list the phones linked to each user, with their real
  device model, and revoke one or several specific sessions without having
  to deactivate the whole user.
- **Machinery list**: tree of machines and sub-machines with an attached
  photo, job counter per year and month, and a link from each job (PC or
  phone) to the machine it was done on, included in PDF, CSV and Excel
  exports.
- **Incremental automatic backup**: closing the application no longer
  repackages the whole photo history every time; the databases rotate in a
  ZIP and the photos are split into incremental ZIPs per year, with a
  progress bar holding focus both when closing and during manual backup and
  restore (see [Backups](#-backups)).
- **Revert a job to pending**: undo a job that was completed by mistake,
  both from the PC history and by long-pressing the record on the phone,
  with a warning about losing the linked machine if it had one and automatic
  restoration of the originating recurring alert, if it came from one.
- **Restore from automatic backup**: `File > Restore` opens as a submenu to
  choose between any manual backup or going straight to the folder of
  automatic backups made on close.
- **Daily stock reminder**: the `mantpro_stock_app` app reminds you every
  morning at 8:00 to check the real quantity of 5 warehouse materials (random,
  different each day) and lets you correct it right away from the
  notification itself.
- **Dashboard with KPIs and reliability charts**: plant-wide average MTBF and
  MTTR cards, and charts ranking the machines with the most breakdowns and
  showing breakdowns per month, hand-drawn with `QPainter` without relying on
  any external charting library.
- **Automatic per-device session replacement**: if a user signs in again
  from a phone on which they already had an open session, the previous one is
  deleted on its own instead of piling up in the session list.

## 🧭 Roadmap

- [ ] **Per-technician statistics** on the dashboard: jobs per person and month.
- [ ] **Remote sync**: being able to sync from outside the office network,
without needing to be on the same Wi-Fi as the PC.
- [ ] **Digital signature of completed jobs**: capture on the phone, with a
finger or stylus, the signature of the person receiving the work when it is
marked as finished, and attach it to the record, building on the existing
user system.

### 🔒 Security note

Sync travels over HTTP within the local network. The user system is
designed for **traceability** (knowing who did each job), not as a barrier
against someone with access to that same network. If the server is ever
exposed outside the local network, the traffic must be encrypted (VPN or a
tunnel with HTTPS).

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.
See the `LICENSE` file for the full text.

Copyright (C) 2026 AnabasaSoft

### What it means in practice

- ✅ You can **use** MantPro freely, including in your company and for commercial purposes
- ✅ You can **study, modify and redistribute** the code
- ⚠️ If you distribute a modified version, you must release it **under AGPL-3.0 as well**
- ⚠️ If you offer MantPro (or a derivative) **as a service over a network**, you must
  make the source code available to its users, even if you do not distribute
  any executable. This is the key difference from the GPL v3
- ⚠️ You must keep the copyright and license notices

### License notice

```
MantPro - Preventive Maintenance System
Copyright (C) 2026 AnabasaSoft

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

> **Note on commercial licenses**: AnabasaSoft is the sole copyright holder
> of MantPro and can therefore offer the same code under terms other than
> the AGPL. If you need to integrate MantPro into a proprietary product,
> get in touch.

---

## 📧 Contact

**AnabasaSoft**

- 📧 Email: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com)
- 🌐 GitHub: [github.com/AnabasaSoft](https://github.com/AnabasaSoft)
- 💼 Project: [github.com/AnabasaSoft/MantPro](https://github.com/AnabasaSoft/MantPro)

---

## 🙏 Acknowledgements

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/): cross-platform GUI framework for the desktop app
- [Flutter](https://flutter.dev/): SDK for the mobile apps
- [ReportLab](https://www.reportlab.com/): PDF report generation
- [SQLite](https://www.sqlite.org/): embedded database
- [Flask](https://flask.palletsprojects.com/): web microframework for the sync server
- The open source community, for its support and contributions

---

<div align="center">

<img src="https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/AnabasaSoft.png" alt="Anabasa Software" width="120"/>

**Made with ❤️ by [Anabasa Software](https://anabasasoft.github.io)**

📧 Email: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com) • 🌐 Portfolio: [anabasasoft.github.io](https://anabasasoft.github.io)

⭐ If you like this project, give it a star on GitHub

</div>

<div align="center">
  <br/>
  <p><code>>_ sudo buy-me-a-coffee --theme=dark --force</code></p>
  <a href="https://www.buymeacoffee.com/danitxu" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-black.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important; box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;">
  </a>
  <br/>
</div>
