# Security Policy · Política de seguridad

[English](#english) · [Español](#español)

---

## English

### Supported versions

Security fixes are made on the **latest stable release** (the one GitHub marks
as *Latest*). Test versions (`-dev`, `-rc`…) are not supported: update to the
stable release before reporting.

### Reporting a vulnerability

Please **do not open a public issue** for security problems. Instead:

- Use GitHub's private reporting: **Security → Report a vulnerability** in this
  repository, or
- Write to **anabasasoft@gmail.com** with the subject `[MantPro security]`.

Include the MantPro version, the platform (Windows, Linux, Android) and the
steps to reproduce the problem. You will get an answer within **7 days**. Once
the problem is fixed and a new version is published, it will be listed in
[CHANGELOG.md](CHANGELOG.md), crediting you if you wish.

### Known limitations

MantPro is designed today to run **inside a local network** (office or
workshop Wi-Fi). Keep in mind:

- **Sync between the PC and the phones is encrypted (HTTPS).** The PC creates
  its own certificate and the phones only accept it if its fingerprint matches
  the one in the pairing QR code. During the transition the PC also answers
  over unencrypted HTTP on the configured port, for apps from earlier
  versions. Do not expose the sync ports to the internet.
- **The databases can be encrypted** (`Tools > Database encryption…`,
  SQLCipher/AES-256, key in the system keyring plus a recovery key). It is
  off by default. **Photos are not encrypted.** Protect the computer. **Backups can be encrypted**
  with a password (`File > Backup password…`, AES-256-GCM with a scrypt-derived
  key); without one they are plain ZIP files.
- On the first start the user `admin` / `admin` is created, and the program
  **forces you to change the password** on first login.
- Repeated failed logins are blocked for a while (15 minutes from the phones,
  one minute in the PC window), and photos sent from the phones are checked
  before being saved.
- If several people use the same computer, use **one system account for
  MantPro** and let each person sign in with their own MantPro user: each
  system account keeps its own separate data. To protect the data on disk,
  use full-disk encryption (BitLocker on Windows, LUKS on Linux).

Full-disk encryption is still recommended: it also protects the photos and the
temporary files.

### Verifying packages

The `.deb` and `.rpm` packages of each release are signed with AnabasaSoft's
GPG key ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)):

```
11C7 C6C8 127D FE48 33DE  30EF 9D7A AEC8 1842 C199
```

The fingerprint is also published at
[anabasasoft.github.io](https://anabasasoft.github.io/about.html#firma). The steps to
verify the packages are in the [README](README.md).

---

## Español

### Versiones con soporte

Los arreglos de seguridad se hacen sobre la **última versión estable** (la que
GitHub marca como *Latest*). Las versiones de pruebas (`-dev`, `-rc`…) no
tienen soporte: actualiza a la estable antes de informar.

### Cómo informar de una vulnerabilidad

Por favor, **no abras una *issue* pública** para un problema de seguridad. En
su lugar:

- Usa el aviso privado de GitHub: **Security → Report a vulnerability** en este
  repositorio, o
- Escribe a **anabasasoft@gmail.com** con el asunto `[MantPro seguridad]`.

Indica la versión de MantPro, la plataforma (Windows, Linux, Android) y los
pasos para reproducir el problema. Recibirás respuesta en un máximo de
**7 días**. Cuando esté corregido y publicada la nueva versión, aparecerá en el
[CHANGELOG.md](CHANGELOG.md), con tu nombre si así lo quieres.

### Limitaciones conocidas

MantPro está pensado hoy para funcionar **dentro de una red local** (la WiFi de
la oficina o del taller). Ten en cuenta que:

- **La sincronización entre el PC y los móviles va cifrada (HTTPS).** El PC
  crea su propio certificado y los móviles solo lo aceptan si su huella
  coincide con la del QR de vinculación. Durante la transición, el PC sigue
  respondiendo también por HTTP sin cifrar en el puerto configurado, para las
  apps de versiones anteriores. No expongas los puertos de sincronización a
  internet.
- **Las bases de datos se pueden cifrar** (`Herramientas > Cifrado de las
  bases de datos…`, SQLCipher/AES-256, con la clave en el llavero del sistema y
  una clave de recuperación). Viene desactivado. **Las fotos no se cifran.** Protege el equipo. **Las copias de
  seguridad se pueden cifrar** con contraseña (`Archivo > Contraseña de las
  copias…`, AES-256-GCM con la clave sacada con scrypt); sin ella son ZIP
  normales.
- En el primer arranque se crea el usuario `admin` / `admin`, y el programa
  **obliga a cambiar la contraseña** al entrar por primera vez.
- Los intentos fallidos de inicio de sesión seguidos se bloquean un tiempo
  (15 minutos desde los móviles, un minuto en la ventana del PC), y las fotos
  que llegan de los móviles se comprueban antes de guardarlas.
- Si varias personas usan el mismo ordenador, usad **una sola cuenta del
  sistema para MantPro** y que cada uno entre con su usuario de MantPro: cada
  cuenta del sistema guarda sus propios datos por separado. Para proteger los
  datos del disco, usa el cifrado de disco completo (BitLocker en Windows,
  LUKS en Linux).

Se sigue recomendando el cifrado de disco completo: protege también las fotos y
los ficheros temporales.

### Verificar los paquetes

Los paquetes `.deb` y `.rpm` de cada versión están firmados con la clave GPG de
AnabasaSoft ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)):

```
11C7 C6C8 127D FE48 33DE  30EF 9D7A AEC8 1842 C199
```

La huella está publicada también en
[anabasasoft.github.io](https://anabasasoft.github.io/about.html#firma). Los pasos
para verificar los paquetes están en el [README](README.es.md).
