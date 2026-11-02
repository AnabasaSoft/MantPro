#
# spec file for package mantpro
#
# Copyright (c) 2026 Daniel Serrano Armenta (AnabasaSoft) <anabasasoft@gmail.com>
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

# Módulo de Python de SQLCipher (cifrado de las bases de datos). openSUSE tiene
# la biblioteca de SQLCipher pero no su módulo de Python, así que se compila
# aquí desde su código fuente (trae SQLCipher dentro y usa el OpenSSL del
# sistema). Es la misma librería que llevan los binarios de GitHub.
%define sqlcipher3_version 0.6.4

Name:           mantpro
Version:        3.10.0
Release:        0
Summary:        Maintenance management (CMMS) for workshops and plants, with Android sync
# MantPro: AGPL; sqlcipher3 (módulo): Zlib; SQLCipher: BSD-3-Clause
License:        AGPL-3.0-or-later AND Zlib AND BSD-3-Clause
URL:            https://github.com/AnabasaSoft/MantPro
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        https://files.pythonhosted.org/packages/source/s/sqlcipher3/sqlcipher3-%{sqlcipher3_version}.tar.gz
BuildRequires:  desktop-file-utils
BuildRequires:  fdupes
BuildRequires:  gcc
BuildRequires:  pkgconfig(libcrypto)
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python-rpm-macros
BuildRequires:  python3
# Las dependencias de ejecución también como BuildRequires: así OBS comprueba
# que existen en la distribución y %%check prueba que la app las puede importar.
BuildRequires:  python3-Flask
BuildRequires:  python3-Pillow
BuildRequires:  python3-cryptography
BuildRequires:  python3-keyring
BuildRequires:  python3-PyQt6
BuildRequires:  python3-XlsxWriter
BuildRequires:  python3-openpyxl
BuildRequires:  python3-qrcode
BuildRequires:  python3-reportlab
BuildRequires:  python3-requests
Requires:       python3
Requires:       python3-Flask
Requires:       python3-Pillow
Requires:       python3-cryptography
Requires:       python3-keyring
# El módulo de SQLCipher va compilado para esta versión de Python
Requires:       python(abi) = %{python3_version}
Requires:       python3-PyQt6
Requires:       python3-XlsxWriter
Requires:       python3-openpyxl
Requires:       python3-qrcode
Requires:       python3-reportlab
Requires:       python3-requests
# Traducciones de los botones estándar de Qt (Aceptar, Cancelar...) a los
# idiomas de la app; sin ellas esos textos salen en inglés.
Recommends:     qt6-translations

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
%autosetup -n MantPro-%{version} -a1
# La versión que se muestra en "Acerca de" sale del paquete, igual que en
# los binarios de GitHub (build_desktop.yml).
sed -i 's/^APP_VERSION = ".*"/APP_VERSION = "%{version}"/' mantpro/version.py
# Se actualiza con zypper: "Buscar actualizaciones" lo indica en vez de mirar GitHub.
sed -i 's/^GESTOR_PAQUETES = .*/GESTOR_PAQUETES = "zypper"/' mantpro/version.py
# Licencia del módulo de SQLCipher, junto a la de MantPro
cp sqlcipher3-%{sqlcipher3_version}/LICENSE LICENSE.sqlcipher3

%build
# La app es Python puro; solo se compila el módulo de SQLCipher.
cd sqlcipher3-%{sqlcipher3_version}
export CFLAGS="%{optflags}"
python3 setup.py build --build-lib=../_sqlcipher3

%install
install -d %{buildroot}%{_datadir}/%{name}
cp -a main.py mantpro recursos %{buildroot}%{_datadir}/%{name}/
%py3_compile %{buildroot}%{_datadir}/%{name}

# Módulo de SQLCipher: compilado, así que en %%{_libdir} y no en /usr/share
install -d %{buildroot}%{_libdir}/%{name}
cp -a _sqlcipher3/sqlcipher3 %{buildroot}%{_libdir}/%{name}/
%py3_compile %{buildroot}%{_libdir}/%{name}

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} << 'EOF'
#!/bin/sh
export PYTHONPATH="%{_libdir}/%{name}${PYTHONPATH:+:$PYTHONPATH}"
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
Keywords=CMMS;GMAO;maintenance;mantenimiento;maintenance préventive;stock;almacén;
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
sys.path.insert(0, "%{buildroot}%{_libdir}/%{name}")
for m in ("flask", "openpyxl", "PIL", "cryptography", "keyring", "PyQt6.QtWidgets", "PyQt6.QtNetwork", "qrcode",
          "reportlab", "requests", "xlsxwriter"):
    importlib.import_module(m)
import mantpro
modulos = [m.name for m in pkgutil.walk_packages(mantpro.__path__, "mantpro.")]
for m in modulos:
    importlib.import_module(m)
# SQLCipher de verdad (cifra) y que la app lo usa
from sqlcipher3 import dbapi2
assert dbapi2.connect(":memory:").execute("PRAGMA cipher_version").fetchone()[0]
from mantpro.nucleo import conexion_bd
assert conexion_bd.HAY_SQLCIPHER
from mantpro.version import APP_VERSION
assert APP_VERSION == "%{version}", APP_VERSION
from mantpro.version import GESTOR_PAQUETES
assert GESTOR_PAQUETES == "zypper", GESTOR_PAQUETES
print("OK:", len(modulos), "módulos")
EOF

%files
%license LICENSE LICENSE.sqlcipher3
%doc README.md README.es.md
%{_bindir}/%{name}
%{_datadir}/%{name}
%{_libdir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/pixmaps/%{name}.png

%changelog
