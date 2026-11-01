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

- **Sync between the PC and the phones uses HTTP**, not HTTPS. Every request
  needs a session token, but traffic is not encrypted: anyone on the same
  network could read it. Do not expose the sync port to the internet.
- **Data is stored unencrypted** on the PC (`mantenimiento.db`, `almacen.db`
  and the photos folder). Protect the computer and the backups.
- On the first start the user `admin` / `admin` is created, and the program
  **forces you to change the password** on first login.

An encryption layer (HTTPS and encrypted data at rest) is planned, and will be
mandatory before offering a server reachable from outside the local network.

### Verifying packages

The `.deb` and `.rpm` packages of each release are signed with AnabasaSoft's
GPG key ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)):

```
11C7 C6C8 127D FE48 33DE  30EF 9D7A AEC8 1842 C199
```

The steps to verify them are in the [README](README.md).

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

- **La sincronización entre el PC y los móviles va por HTTP**, no HTTPS. Todas
  las peticiones necesitan un token de sesión, pero el tráfico no va cifrado:
  alguien en la misma red podría leerlo. No expongas el puerto de
  sincronización a internet.
- **Los datos se guardan sin cifrar** en el PC (`mantenimiento.db`,
  `almacen.db` y la carpeta de fotos). Protege el equipo y las copias de
  seguridad.
- En el primer arranque se crea el usuario `admin` / `admin`, y el programa
  **obliga a cambiar la contraseña** al entrar por primera vez.

Está prevista una capa de cifrado (HTTPS y datos cifrados en disco), que será
obligatoria antes de ofrecer un servidor accesible desde fuera de la red local.

### Verificar los paquetes

Los paquetes `.deb` y `.rpm` de cada versión están firmados con la clave GPG de
AnabasaSoft ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)):

```
11C7 C6C8 127D FE48 33DE  30EF 9D7A AEC8 1842 C199
```

Los pasos para verificarlos están en el [README](README.es.md).
