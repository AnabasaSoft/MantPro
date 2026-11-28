# MantPro Operarios

Tablet fija del taller para avisar de trabajos pendientes. Sustituye al PC o a la
web abiertos en la «Ventana de avisos (quiosco)» de MantPro: cada operario elige
su nombre en la lista, rellena el aviso (título, detalles, especialidad,
prioridad y fotos), escribe SU contraseña y pulsa «Añadir».

## Vinculación

1. En el PC, abre el QR de vinculación de MantPro (el mismo que usan las otras
   apps móviles; lleva también la ruta de MantPro Cloud).
2. En la tablet, pulsa «Escanear el QR del PC» e inicia sesión con un
   **administrador**. Si el usuario no es administrador, la tablet no se vincula.
3. La tablet descarga la lista de usuarios y entra en la ventana de avisos, que
   queda abierta y con la pantalla fijada (no se sale con los botones del
   sistema).

Para salir, «🔒 Cerrar» y la contraseña del administrador que la vinculó. Desde
el panel de administración se puede sincronizar, elegir la sede, el idioma y el
tema, buscar actualizaciones o desvincular la tablet.

## Sin conexión

La app funciona al 100 % sin conexión, igual que las otras apps móviles:

- La contraseña se comprueba en local contra el hash (PBKDF2) que descarga la
  tablet, nunca se envía a ninguna parte.
- Cada aviso se guarda al instante en una cola local (`cola_avisos`, con sus
  fotos) y se envía al PC o a MantPro Cloud en cuanto hay conexión: al arrancar,
  cada 30 s, tras cada aviso y con «Sincronizar ahora».
- La lista de usuarios, las especialidades y las sedes se guardan en caché y se
  refrescan después de cada envío.
- Los avisos que el servidor rechaza (sin permiso, sin título) se descartan y
  quedan apuntados en el panel de administración.

## Desarrollo

```
flutter pub get
flutter analyze
flutter test
```

La versión (`kAppVersion` en `lib/main.dart`, `version:` en `pubspec.yaml`) la
sustituye la CI a partir del tag. Los textos viven en `lib/i18n/` (8 idiomas) y
se comprueban con `python3 herramientas/verificar_idiomas.py` desde la raíz.
