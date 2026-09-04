# MantPro - Sistema de Mantenimiento Preventivo

<p align="center">
  <img src="logo.png" alt="MantPro Logo" width="200"/>
</p>

<p align="center">
  <strong>Gestión profesional de mantenimiento preventivo y correctivo para equipos y flotas</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
</p>

---

## 📋 Índice

- [Descargas](#-descargas)
- [Características](#-características)
- [Capturas de Pantalla](#-capturas-de-pantalla)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Sincronización PC-Móvil](#-sincronización-pc-móvil)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)
- [Contacto](#-contacto)

---

## 📦 Descargas

Puedes descargar las versiones precompiladas desde [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: Ejecutable `.exe` para Windows
- **Linux**: 
  - Binario ejecutable de Linux
  - AppImage portable
  - También disponible en **AUR** (Arch User Repository)
- **Android**: Archivo `.apk` para instalación directa

---

## ✨ Características

### 💻 Aplicación de Escritorio (PC)

- **📅 Calendario Interactivo**: Visualiza y gestiona tareas de mantenimiento con códigos de color (festivos, vacaciones, días con tareas)
- **📝 Historial Completo**: Registro histórico de todas las intervenciones realizadas, con fotos antes/después
- **📄 Reportes PDF**: Generación automática de informes profesionales con logo personalizable
- **📸 Gestión de Imágenes**: Almacenamiento y visualización de fotos de intervenciones
- **📱 Sincronización Móvil**: Servidor integrado (arranca automáticamente) para sincronización con la app móvil vía QR
- **🔍 Sistema de Búsqueda**: Búsqueda avanzada por fechas, tags y contenido
- **📦 Backup/Restore**: Exportación e importación de base de datos completa
- **🏷️ Sistema de Tags**: Categorización con etiquetas (Urgente, Eléctrico, Mecánico, Preventivo)
- **🔨 Tareas Pendientes**: Gestión de trabajos pendientes (crear, completar, editar, eliminar)
- **⚠️ Avisos Recurrentes**: Avisos de mantenimiento que se repiten automáticamente
- **📊 Exportación**: A PDF, CSV y Excel

### 📱 Aplicación Móvil (Android)

- **📝 Registro Rápido**: Captura de intervenciones sobre el terreno
- **📷 Cámara Integrada**: Toma de fotos y edición con anotaciones
- **✏️ Editor de Imágenes**: Dibuja sobre las fotos para marcar áreas de interés
- **🔄 Sincronización Automática**: Envío automático de datos al PC mediante código QR
- **💾 Almacenamiento Local**: Guarda registros offline hasta sincronizar
- **📋 Trabajos Pendientes**: Visualiza y gestiona tareas asignadas desde el PC
- **🏷️ Tags Rápidos**: Sistema de etiquetado rápido con checkboxes
- **🔌 Modo Offline**: Trabaja sin conexión y sincroniza cuando estés disponible
- **⏰ Recordatorios Diarios**: Notificación automática a las 8:00 AM (hora local) si hay trabajos pendientes sin completar

---

## 📸 Capturas de Pantalla

### Aplicación de Escritorio

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Dashboard" width="45%"/>
  <img src="Capturas/Avisos.png" alt="Avisos" width="45%"/>
</p>

### Aplicación Móvil

<p align="center">
  <img src="Capturas/mobile-home.jpg" alt="Inicio Móvil" width="45%"/>
  <img src="Capturas/mobile-pendientes.jpg" alt="Trabajos Pendientes" width="45%"/>
</p>

---

## 🔧 Requisitos

### Aplicación de Escritorio

- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows o Linux
- **Dependencias Python**:
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - sqlite3 (incluido en Python)

### Aplicación Móvil

- **Flutter**: 3.0 o superior
- **Dart SDK**: 2.17 o superior
- **Android**: API Level 21+ (Android 5.0+)

---

## 📥 Instalación

### Aplicación de Escritorio

#### Opción 1: Descarga Precompilada (Recomendado)

Descarga la versión correspondiente a tu sistema desde [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: Descarga y ejecuta el `.exe`
- **Linux**: 
  - Descarga el binario ejecutable y dale permisos de ejecución: `chmod +x mantpro`
  - O usa el **AppImage** (sin instalación): `chmod +x MantPro.AppImage && ./MantPro.AppImage`
  - **Arch Linux**: Disponible en AUR: `yay -S mantpro` o `paru -S mantpro`

#### Opción 2: Instalación desde Código Fuente

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/AnabasaSoft/MantPro.git
   cd MantPro
   ```

2. **Crear entorno virtual** (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**:
   ```bash
   python main.py
   ```

### Aplicación Móvil

#### Opción 1: Descarga Directa (Recomendado)

Descarga el archivo `.apk` desde [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) e instálalo en tu dispositivo Android.

**Nota**: Es posible que necesites habilitar "Orígenes desconocidos" en la configuración de seguridad de tu dispositivo.

#### Opción 2: Compilar desde Código Fuente

1. **Navegar al directorio móvil**:
   ```bash
   cd mantenimiento_app
   ```

2. **Instalar dependencias**:
   ```bash
   flutter pub get
   ```

3. **Ejecutar en dispositivo/emulador**:
   ```bash
   flutter run
   ```

4. **Compilar APK (Android)**:
   ```bash
   flutter build apk --release
   ```

---

## 🚀 Uso

### Primera Configuración

#### Aplicación de Escritorio

1. **Iniciar la aplicación**: Ejecuta `python main.py` (el servidor de sincronización arranca solo, no hace falta iniciarlo a mano)
2. **Configurar logo** (opcional): Menú `Archivo` > `📄 Opciones PDF` > `🖼️ Añadir / Cambiar Logo`
3. **Registrar un trabajo**: Pestaña "📝 Registrar" > rellena resumen/detalles > "💾 GUARDAR REGISTRO"
4. **Crear un pendiente**: Pestaña "🔨 Pendientes" > grupo "Nuevo Trabajo" (Título + Detalles) > "Añadir"

#### Aplicación Móvil

1. **Instalar la app** en tu dispositivo móvil
2. **Conectar con PC**: 
   - Asegúrate de que el PC y el móvil están en la misma red WiFi
   - En el PC: Menú `Herramientas` > `📲 Sincronizar App (QR)`
   - En el móvil: Tap en el icono QR y escanea el código
3. **Listo**: Ya puedes registrar intervenciones desde el móvil

### Flujo de Trabajo Típico

#### Desde el PC

1. **Crear tarea pendiente**:
   - Pestaña "🔨 Pendientes" > grupo "Nuevo Trabajo" > rellena Título y Detalles > "Añadir"
   - Gestiónala con los botones "✅ Completar", "✏️ Editar" o "❌ Eliminar"

2. **Revisar trabajos completados**:
   - Los trabajos sincronizados desde el móvil aparecen automáticamente
   - Revisa fotos (antes/después) y detalles en la pestaña "🗂 Historial" o en el "📅 Calendario"

3. **Generar reportes**:
   - Menú `Archivo` > `📄 Opciones PDF` > `📄 Generar PDF Ahora`
   - O exporta a `📄 CSV` / `📊 Excel` desde el mismo menú `Archivo`

#### Desde el Móvil

1. **Vincular con el PC** (solo la primera vez, o si cambias de red):
   - Tap en "Vincular PC" y escanea el QR que muestra el PC
   - El móvil guarda la dirección del PC para sincronizar automáticamente a partir de ahí

2. **Registrar intervención**:
   - Tap en "Nuevo" o selecciona un trabajo pendiente ya sincronizado desde el PC
   - Completa título y detalles
   - Toma foto "antes" y, opcionalmente, foto "después" con la cámara
   - Dibuja/anota sobre la foto si es necesario
   - Selecciona tags apropiados
   - Guarda

3. **Sincronizar**:
   - Tap en el icono de sincronización
   - Los registros se envían automáticamente al PC
   - Se eliminan del móvil al confirmar envío exitoso

---

## 🔄 Sincronización PC-Móvil

### Cómo Funciona

MantPro utiliza un sistema de sincronización basado en:

1. **Servidor Flask** integrado en la app de escritorio
2. **Códigos QR** para conexión rápida y segura
3. **API REST** para comunicación entre dispositivos
4. **WiFi local** - sin necesidad de internet

### Configuración de Red

Para que la sincronización funcione:

- ✅ PC y móvil deben estar en la **misma red WiFi**
- ✅ El **firewall** debe permitir conexiones en el puerto 5000 (o el configurado)
- ✅ Si usas Windows, puede que necesites crear una excepción de firewall

### Solución de Problemas

**El móvil no conecta con el PC:**
- Verifica que ambos dispositivos están en la misma red
- Comprueba que el servidor está activo en el PC (icono verde)
- Prueba a desactivar temporalmente el firewall del PC
- Regenera el código QR y vuelve a escanearlo

**Las fotos no se sincronizan:**
- Verifica que hay espacio suficiente en el disco del PC
- Comprueba los permisos de la carpeta `fotos_mantenimiento`
- Asegúrate de que la foto se guardó correctamente en el móvil

**No me llega la notificación diaria de avisos pendientes (Android):**
- Comprueba que el permiso de notificaciones está concedido: `Ajustes → Apps → MantPro → Notificaciones`
- En fabricantes como **OPPO/Realme (ColorOS), Xiaomi (MIUI) o Huawei**, el sistema puede matar la alarma programada aunque el permiso esté dado. Hay que además:
  - `Ajustes → Batería → Uso de batería por app → MantPro` → ponerlo en **"Sin restricciones"**
  - `Ajustes → Batería → Inicio automático` → **activar** MantPro
- La notificación se reevalúa cada vez que abres el Dashboard, así que si acabas de marcar un trabajo como completado, ábrelo de nuevo para que se cancele/reprograme correctamente.

---

## 📁 Estructura del Proyecto

```
MantPro/
├── main.py                      # Aplicación principal de escritorio
├── requirements.txt             # Dependencias Python
├── logo.png                     # Logo de la aplicación
├── README.md                    # Este archivo
├── fotos_mantenimiento/         # Carpeta de imágenes
├── mantenimiento.db             # Base de datos SQLite
├── mantenimiento_app/            # Aplicación móvil Flutter
│   ├── lib/main.dart            # Código principal móvil
│   ├── pubspec.yaml             # Dependencias Flutter
│   └── android/                 # Configuración Android
├── backups/                     # Backups de base de datos
└── docs/                        # Documentación adicional
```

### Base de Datos

La aplicación utiliza SQLite con las siguientes tablas:

- **`tareas`**: Registro de intervenciones realizadas (fecha, descripción, tags)
- **`pendientes`**: Tareas pendientes de realizar (título, detalles)
- **`avisos_recurrentes`**: Avisos de mantenimiento que se repiten automáticamente
- **`dias_especiales`**: Festivos, vacaciones y días marcados en el calendario
- **`config`**: Configuración interna de la aplicación (logo, provincia, etc.)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Si quieres mejorar MantPro:

1. **Fork** el proyecto
2. Crea una **rama** para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. Abre un **Pull Request**

### Ideas de Mejora

- [X] Implementar notificaciones push para recordatorios
- [ ] Añadir gráficas de estadísticas más detalladas
- [ ] Integración con calendario de Google
- [X] Modo oscuro
- [X] Multi-idioma (Español, Inglés, Euskara)
- [X] Exportación a Excel
- [ ] API para integración con otros sistemas
- [ ] Firma digital de trabajos completados

---

## 🗺️ Roadmap

Estado actual y siguientes pasos previstos.

### ✅ Hecho

- **Gestión de usuarios**: login con usuario y contraseña en PC y móvil, roles
  (administrador / técnico), alta y baja lógica de usuarios, cambio y
  restablecimiento de contraseña.
- **Autoría de los trabajos**: cada registro guarda quién lo realizó. Los
  registros anteriores al sistema de usuarios quedan marcados como `Histórico`.
- **Sesión persistente en el móvil**: el técnico inicia sesión una vez y el
  token queda guardado en el dispositivo.
- **API autenticada**: todos los endpoints de datos exigen token; un `401`
  cierra la sesión del móvil y devuelve al login sin perder los registros
  locales pendientes de enviar.
- **Pendientes asignados**: el PC asigna cada trabajo a un técnico y el móvil
  puede filtrar por "Solo míos".
- **Filtro por técnico** en el histórico y en la exportación a PDF.

### 🔜 Siguientes pasos

- [ ] **Sesiones activas**: listar los móviles vinculados a cada usuario y poder
      revocar uno concreto (hoy solo se puede desactivar al usuario entero,
      lo que invalida todos sus dispositivos a la vez).
- [ ] **Auditoría de ediciones**: registrar quién edita o borra un trabajo, no
      solo quién lo creó.
- [ ] **Estadísticas por técnico** en el dashboard: trabajos por persona y mes.
- [ ] **Filtro por técnico en CSV y Excel** (por ahora solo está en el PDF).
- [ ] **Sincronización remota**: poder sincronizar desde fuera de la red de la
      oficina, sin depender de estar en la misma WiFi que el PC.
- [ ] **Firma digital de trabajos completados**, apoyada en el sistema de
      usuarios.

### 🔒 Nota sobre seguridad

La sincronización viaja por HTTP dentro de la red local. El sistema de usuarios
está pensado para **trazabilidad** (saber quién hizo cada trabajo), no como
barrera frente a alguien con acceso a esa misma red. Si en el futuro se expone
el servidor fuera de la red local, el tráfico debe ir cifrado (VPN o túnel con
HTTPS).

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

```
MIT License

Copyright (c) 2026 AnabasaSoft

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📧 Contacto

**AnabasaSoft**

- 📧 Email: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com)
- 🌐 GitHub: [github.com/AnabasaSoft](https://github.com/AnabasaSoft)
- 💼 Proyecto: [github.com/AnabasaSoft/MantPro](https://github.com/AnabasaSoft/MantPro)

---

## 🙏 Agradecimientos

- **PyQt6** - Framework GUI multiplataforma
- **Flutter** - SDK para desarrollo móvil
- **ReportLab** - Generación de PDFs
- **SQLite** - Base de datos embebida
- **Flask** - Microframework web para el servidor de sincronización

---

<p align="center">
  Hecho con ❤️ por AnabasaSoft
</p>

<p align="center">
  <sub>Si este proyecto te ha sido útil, ¡dale una ⭐️!</sub>
</p>
