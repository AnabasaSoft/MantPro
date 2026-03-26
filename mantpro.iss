[Setup]
; Información básica de la aplicación
AppName=MantPro
AppVersion=2.0
AppPublisher=AnabasaSoft
AppPublisherURL=https://github.com/AnabasaSoft/MantPro

; Dónde se instalará por defecto (Archivos de Programa)
DefaultDirName={autopf}\MantPro
DefaultGroupName=MantPro

; Configuración del archivo de salida (El instalador)
OutputDir=.\Output
OutputBaseFilename=MantPro_Setup_v2.0
SetupIconFile=icono.ico

; Compresión para que pese menos
Compression=lzma2
SolidCompression=yes

; Pide permisos de administrador para instalar en Archivos de Programa
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
; Aquí le decimos dónde está el .exe que generó PyInstaller
; OJO: Asegúrate de que la ruta coincida con donde PyInstaller deja tu ejecutable (suele ser 'dist')
Source: "dist\MantPro.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Crea el acceso directo en el menú de inicio
Name: "{group}\MantPro"; Filename: "{app}\MantPro.exe"
; Crea el acceso directo en el escritorio
Name: "{autodesktop}\MantPro"; Filename: "{app}\MantPro.exe"; Tasks: desktopicon

[Run]
; Casilla opcional al final para "Ejecutar MantPro ahora"
Filename: "{app}\MantPro.exe"; Description: "Abrir MantPro"; Flags: nowait postinstall skipifsilent