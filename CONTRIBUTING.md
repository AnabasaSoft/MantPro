# Contributing to MantPro · Contribuir a MantPro

[English](#english) · [Español](#español)

---

## English

Thank you for wanting to improve MantPro! Bug reports, ideas, translations and
code are all welcome.

### Before you start

- **Bugs and ideas:** open an [issue](https://github.com/AnabasaSoft/MantPro/issues)
  describing what happens (or what you would like), the MantPro version and the
  platform (Windows, Linux, Android).
- **Security problems:** do not open a public issue; follow
  [SECURITY.md](SECURITY.md).
- **Large changes:** open an issue first to talk about them, so you don't spend
  time on something that does not fit the project.

### Contributor License Agreement (CLA)

To accept your code we need you to agree to the [CLA](CLA.md). In short: **you
keep the copyright of your contribution**, and you give Daniel Serrano Armenta
(AnabasaSoft) permission to use it in MantPro, both under the AGPL-3.0 and under
other licenses (for example, commercial licenses or a hosted MantPro service).
That is what allows the project to keep being free while being sustainable.

When you open your first pull request, a bot will ask you to accept the CLA
with a comment. You only have to do it once.

### How to prepare a pull request

1. **Fork** the repository and create a branch for your change
   (`git checkout -b my-change`).
2. **Keep the project's rules** (the code structure is explained in
   [docs/development.md](docs/development.md)):
   - **Mobile apps 100% offline:** any new mobile feature must work without a
     connection, saving locally and syncing later.
   - **Translations:** every text must exist in all 7 languages (es, en, eu, ca,
     gl, pt, fr). Run `python3 herramientas/verificar_idiomas.py` before
     committing.
   - **File header:** every new source file starts with the SPDX licence
     identifier and the copyright header used in the rest of the code.
   - **No version bumps:** the version comes from the Git tag; do not change it.
3. **Test your change:** run the desktop app (`python main.py`) and, if you touch
   a mobile app, run `flutter analyze` and try it on a device.
4. **Commit** with a clear message and open a **pull request** explaining what
   changes and why.

---

## Español

¡Gracias por querer mejorar MantPro! Son bienvenidos los avisos de fallos, las
ideas, las traducciones y el código.

### Antes de empezar

- **Fallos e ideas:** abre una [*issue*](https://github.com/AnabasaSoft/MantPro/issues)
  explicando qué pasa (o qué te gustaría), la versión de MantPro y la
  plataforma (Windows, Linux, Android).
- **Problemas de seguridad:** no abras una *issue* pública; sigue
  [SECURITY.md](SECURITY.md).
- **Cambios grandes:** abre antes una *issue* para hablarlo, así no dedicas
  tiempo a algo que no encaje en el proyecto.

### Acuerdo de contribución (CLA)

Para aceptar tu código necesitamos que aceptes el [CLA](CLA.md). En resumen:
**el copyright de tu contribución sigue siendo tuyo**, y das permiso a Daniel
Serrano Armenta (AnabasaSoft) para usarla en MantPro, tanto bajo la AGPL-3.0
como bajo otras licencias (por ejemplo, licencias comerciales o un servicio de
MantPro alojado en la nube). Es lo que permite que el proyecto siga siendo
libre y a la vez sostenible.

Al abrir tu primer *pull request*, un bot te pedirá que aceptes el CLA con un
comentario. Solo hay que hacerlo una vez.

### Cómo preparar un *pull request*

1. Haz un **fork** del repositorio y crea una rama para tu cambio
   (`git checkout -b mi-cambio`).
2. **Respeta las normas del proyecto** (la estructura del código está en
   [docs/desarrollo.md](docs/desarrollo.md)):
   - **Apps móviles 100 % sin conexión:** cualquier función nueva del móvil
     tiene que funcionar sin conexión, guardando en local y sincronizando
     después.
   - **Traducciones:** todo texto tiene que estar en los 7 idiomas (es, en, eu,
     ca, gl, pt, fr). Ejecuta `python3 herramientas/verificar_idiomas.py` antes
     de hacer el commit.
   - **Cabecera de los ficheros:** todo fichero de código nuevo empieza con el
     identificador SPDX de la licencia y la cabecera de copyright que lleva el
     resto del código.
   - **Sin cambiar la versión:** la versión sale del tag de Git; no la toques.
3. **Prueba tu cambio:** arranca la app de escritorio (`python main.py`) y, si
   tocas una app móvil, ejecuta `flutter analyze` y pruébala en un dispositivo.
4. Haz el **commit** con un mensaje claro y abre un ***pull request***
   explicando qué cambia y por qué.
