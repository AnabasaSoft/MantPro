#
# spec file for package mantpro
#
# Copyright (c) 2026 AnabasaSoft <anabasasoft@gmail.com>
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License).
#
# Las versiones nuevas se publican solas: al subir un tag vX.Y.Z a GitHub,
# .github/workflows/publicar_obs.yml pone esa versión en Version, añade la
# entrada a mantpro.changes y hace el commit en OBS. El código se descarga
# del tag v<Version> de GitHub (servicio download_files, ver _service).
#

Name:           mantpro
Version:        3.10.0
Release:        0
Summary:        Maintenance management (CMMS) for workshops and plants, with Android sync
License:        AGPL-3.0-or-later
URL:            https://github.com/AnabasaSoft/MantPro
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildRequires:  desktop-file-utils
BuildRequires:  fdupes
BuildRequires:  python-rpm-macros
BuildRequires:  python3
# Las dependencias de ejecución también como BuildRequires: así OBS comprueba
# que existen en la distribución y %%check prueba que la app las puede importar.
BuildRequires:  python3-Flask
BuildRequires:  python3-Pillow
BuildRequires:  python3-PyQt6
BuildRequires:  python3-XlsxWriter
BuildRequires:  python3-openpyxl
BuildRequires:  python3-qrcode
BuildRequires:  python3-reportlab
BuildRequires:  python3-requests
Requires:       python3
Requires:       python3-Flask
Requires:       python3-Pillow
Requires:       python3-PyQt6
Requires:       python3-XlsxWriter
Requires:       python3-openpyxl
Requires:       python3-qrcode
Requires:       python3-reportlab
Requires:       python3-requests
# Traducciones de los botones estándar de Qt (Aceptar, Cancelar...) a los
# idiomas de la app; sin ellas esos textos salen en inglés.
Recommends:     qt6-translations
BuildArch:      noarch

%description
MantPro is a free CMMS for preventive and corrective maintenance of plants,
workshops and fleets. It keeps a job history with before/after photos,
recurring maintenance reminders, pending jobs assigned to technicians, a
machinery tree with reliability indicators (MTBF/MTTR), warehouse stock with
shelving locations, PDF/CSV/Excel reports and import from Excel/CSV.

The desktop application includes a sync server for the MantPro and
MantPro Stock Android apps, which work fully offline and synchronise when
they are back on the same network as the PC.

Available in Spanish, English, Basque, Catalan, Galician, Portuguese and
French.

%prep
%autosetup -n MantPro-%{version}
# La versión que se muestra en "Acerca de" sale del paquete, igual que en
# los binarios de GitHub (build_desktop.yml).
sed -i 's/^APP_VERSION = ".*"/APP_VERSION = "%{version}"/' mantpro/version.py

%build
# Nada que compilar: aplicación Python pura.

%install
install -d %{buildroot}%{_datadir}/%{name}
cp -a main.py mantpro recursos %{buildroot}%{_datadir}/%{name}/
%py3_compile %{buildroot}%{_datadir}/%{name}

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} << 'EOF'
#!/bin/sh
exec /usr/bin/python3 %{_datadir}/%{name}/main.py "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/%{name}

install -Dm0644 recursos/icono.png %{buildroot}%{_datadir}/pixmaps/%{name}.png

install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/%{name}.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=MantPro
GenericName=Maintenance management
GenericName[es]=Gestión de mantenimiento
GenericName[eu]=Mantentze-lanen kudeaketa
GenericName[ca]=Gestió del manteniment
GenericName[gl]=Xestión do mantemento
GenericName[pt]=Gestão de manutenção
GenericName[fr]=Gestion de la maintenance
Comment=Preventive and corrective maintenance, warehouse stock and Android sync
Comment[es]=Mantenimiento preventivo y correctivo, stock de almacén y sincronización con Android
Exec=%{name}
Icon=%{name}
Terminal=false
Categories=Office;ProjectManagement;
Keywords=CMMS;maintenance;mantenimiento;stock;almacén;
StartupWMClass=MantPro
EOF
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

# Al final y sobre todo /usr/share: el icono del menú es el mismo fichero que
# recursos/icono.png (y este, que logo.png).
%fdupes %{buildroot}%{_datadir}

%check
# Que la app instalada pueda importar todas sus librerías y todos sus
# módulos (sin abrir ventanas: plataforma Qt "offscreen").
export QT_QPA_PLATFORM=offscreen HOME=$(mktemp -d)
cd "$HOME"
python3 - << 'EOF'
import importlib, pkgutil, sys
sys.path.insert(0, "%{buildroot}%{_datadir}/%{name}")
for m in ("flask", "openpyxl", "PIL", "PyQt6.QtWidgets", "PyQt6.QtNetwork", "qrcode",
          "reportlab", "requests", "xlsxwriter"):
    importlib.import_module(m)
import mantpro
modulos = [m.name for m in pkgutil.walk_packages(mantpro.__path__, "mantpro.")]
for m in modulos:
    importlib.import_module(m)
from mantpro.version import APP_VERSION
assert APP_VERSION == "%{version}", APP_VERSION
print("OK:", len(modulos), "módulos")
EOF

%files
%license LICENSE
%doc README.md README.es.md
%{_bindir}/%{name}
%{_datadir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/pixmaps/%{name}.png

%changelog
