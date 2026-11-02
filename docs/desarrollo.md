# 📁 Estructura del Proyecto

> Documentación técnica de [MantPro](../README.es.md). In English: [development.md](development.md).


```
MantPro/
├── main.py                      # Punto de arranque (python main.py)
├── mantpro/                     # Código de la app de escritorio
│   ├── version.py               # Versión (la pone CI desde el tag)
│   ├── nucleo/                  # Datos y lógica, sin interfaz
│   │   ├── usuarios.py          # Usuarios, contraseñas, roles y sesiones
│   │   ├── almacen.py           # Stock de almacén: estructura, materiales y movimientos
│   │   ├── maquinas.py          # Árbol de maquinaria y su histórico de trabajos
│   │   ├── basedatos.py         # Base de datos de trabajos
│   │   ├── conexion_bd.py       # Única entrada a SQLite: cifrado (SQLCipher) y llavero
│   │   ├── seguridad.py         # Límite de intentos de login, fotos, escritura atómica
│   │   ├── certificado.py       # Certificado TLS propio del servidor y su huella
│   │   ├── cifrado_copias.py    # Copias de seguridad cifradas con contraseña
│   │   ├── estadisticas.py      # Estadísticas por técnico
│   │   ├── nombres.py           # Aviso de nombres repetidos o muy parecidos
│   │   ├── etiquetas.py         # Etiquetas QR de las máquinas
│   │   ├── fotos.py             # Fotos de los trabajos (colección)
│   │   ├── rutas.py             # Carpeta de datos
│   │   └── importar.py          # Importación desde Excel/CSV
│   ├── interfaz/                # Ventanas PyQt6
│   │   ├── arranque.py          # Arranque: instancia única y login
│   │   ├── app.py               # Aplicación principal de escritorio
│   │   ├── servidor.py          # Servidor de sincronización con los móviles
│   │   ├── pestanas/            # Una por pestaña: dashboard, calendario, stock...
│   │   ├── acciones/            # Acciones de los menús: copias, exportar, importar, usuarios
│   │   ├── dialogos/            # Diálogos (incluidos login y gestión de usuarios)
│   │   └── widgets/             # Fotos y gráficos
│   └── idiomas/                 # Traducciones del escritorio (ES / EN / EU / CA / GL / PT / FR)
├── recursos/                    # Iconos y logotipos
├── herramientas/                # Scripts del proyecto (verificar_idiomas.py...)
├── empaquetado/                 # Instalador de Windows (Inno Setup)
├── requirements.txt             # Dependencias Python
├── README.es.md                 # Este archivo
├── fotos_recibidas/             # Carpeta de imágenes
├── mantenimiento.db             # Base de datos SQLite (trabajos de mantenimiento)
├── almacen.db                   # Base de datos SQLite (stock de almacén, independiente)
├── servidor_cert.pem / servidor_clave.pem  # Certificado TLS del servidor (lo crea MantPro)
├── clave_copias.json            # Clave de las copias cifradas (si se activan)
├── clave_bd.json                # Clave de las BD cifradas, solo si no hay llavero
├── mantenimiento_app/           # Aplicación móvil Flutter (trabajos)
│   ├── lib/main.dart            # Código principal móvil
│   ├── lib/conexion_segura.dart # HTTPS con el certificado del PC fijado por su huella
│   ├── lib/actualizador.dart    # Descarga e instalación de la versión nueva
│   ├── lib/i18n/                # Traducciones del móvil (ES / EN / EU / CA / GL / PT / FR)
│   ├── pubspec.yaml             # Dependencias Flutter
│   └── android/                 # Configuración Android
├── mantpro_stock_app/           # Aplicación móvil Flutter (stock de almacén)
│   ├── lib/modelos.dart         # Modelos de datos y regla de color de stock
│   ├── lib/pantallas/           # Pantallas: almacén, artículo, búsqueda, bajo mínimo...
│   ├── lib/i18n/                # Traducciones del móvil (ES / EN / EU / CA / GL / PT / FR)
│   ├── pubspec.yaml             # Dependencias Flutter
│   └── android/                 # Configuración Android
├── backups/                     # Backups manuales completos (BD + fotos)
├── backups_auto/                # Backups automáticos al cerrar (BD rotativa + fotos por año)
└── docs/                        # Documentación adicional
```

> Los datos (base de datos, fotos y backups) no viven necesariamente junto al
> código: si no existe `mantenimiento.db` en la carpeta actual, la aplicación usa
> `~/.local/share/MantPro` en Linux o `%APPDATA%\MantPro` en Windows.

## Ejecutar desde el código fuente

En distribuciones que no dejan instalar paquetes con `pip` fuera de un entorno
virtual (openSUSE, Fedora, Debian…) y que no tienen el módulo de SQLCipher para
Python, crea un entorno que use los paquetes del sistema y añádele solo SQLCipher:

```bash
python3 -m venv --system-site-packages venv
venv/bin/pip install sqlcipher3-wheels==0.5.7
venv/bin/python main.py
```

Sin SQLCipher MantPro funciona igual, pero no puede abrir unas bases de datos
cifradas. Si copias las bases de datos cifradas de `~/.local/share/MantPro` a la
carpeta del código, MantPro usa la clave que tiene el llavero para esa carpeta y
la guarda también para la nueva.

## Base de Datos

La aplicación utiliza SQLite con las siguientes tablas:

- **`tareas`**: Registro de intervenciones realizadas (fecha, descripción, tags,
  fotos, **quién lo realizó** (`usuario_id` y `usuario_nombre`) y la
  **máquina vinculada** (`maquina_id`), si tiene una)
- **`maquinas`**: Árbol de maquinaria (nombre, máquina superior, notas y foto)
- **`pendientes`**: Tareas pendientes de realizar (título, detalles, prioridad y
  **técnico asignado**: `asignado_a` y `asignado_nombre`)
- **`usuarios`**: Personas que usan la aplicación (login, nombre, hash de la
  contraseña, rol y si está activo)
- **`sesiones`**: Tokens de los móviles vinculados, con su fecha de caducidad
- **`avisos_recurrentes`**: Avisos de mantenimiento que se repiten automáticamente
- **`dias_especiales`**: Festivos, vacaciones y días marcados en el calendario
- **`auditoria`**: Historial de quién edita o borra cada trabajo, con fecha,
  acción y detalle
- **`config`**: Configuración interna de la aplicación (logo, provincia, etc.)

Las contraseñas se guardan con **PBKDF2-SHA256** (200.000 iteraciones y salt por
usuario), nunca en claro. Las tablas y columnas nuevas se crean solas al
arrancar, sin perder los datos existentes.

**Conexiones**: todo el código abre las bases de datos con
`conexion_bd.conectar()` y usa el `sqlite3` que exporta `mantpro/nucleo/conexion_bd.py`
(nunca `import sqlite3` ni `sqlite3.connect` directamente), porque las bases de
datos pueden estar cifradas con **SQLCipher** (*Herramientas → Cifrado de las
bases de datos*). La clave (256 bits aleatorios, la misma para las dos bases
de datos) va en el llavero del sistema con `keyring` y se pasa en bruto
(`PRAGMA key = "x'…'"`); para adjuntar una base de datos se usa
`conexion_bd.adjuntar()`. El cifrado y el descifrado se hacen al arrancar,
antes de abrir ninguna conexión. Las copias de seguridad llevan las bases de
datos sin cifrar (`copiar_sin_cifrar`) y, al restaurar, `restaurar_desde_plano`
las vuelve a cifrar si hace falta. Si no está instalado `sqlcipher3`, se usa el
`sqlite3` de Python y la opción aparece desactivada.

> 🔐 `mantenimiento.db` contiene hashes de contraseñas y tokens de sesión.
> Está en `.gitignore` por algo: no la subas nunca al repositorio.

El stock de almacén vive en su propia base de datos, **`almacen.db`**, separada
a propósito de la de los trabajos:

- **`estanterias`**: nombre y si tiene hueco en el suelo
- **`baldas`**: baldas de cada estantería, numeradas de abajo a arriba (la
  balda `0` representa el hueco de suelo)
- **`secciones`**: subdivisiones dentro de cada balda
- **`materiales`**: código, nombre, descripción, unidad, stock actual, stock
  mínimo, ubicación (sección) y foto
- **`movimientos`**: histórico de entradas y salidas, con fecha, cantidad,
  usuario y motivo

Se crea automáticamente en el primer arranque y se incluye en los backups
(manuales y automáticos al cerrar la app) junto con `mantenimiento.db`.
