<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-6e7781?style=for-the-badge" alt="English"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Espa%C3%B1ol-6e7781?style=for-the-badge" alt="Español"></a>
  <a href="README.eu.md"><img src="https://img.shields.io/badge/Euskara-6e7781?style=for-the-badge" alt="Euskara"></a>
  <a href="README.ca.md"><img src="https://img.shields.io/badge/Catal%C3%A0-6e7781?style=for-the-badge" alt="Català"></a>
  <a href="README.gl.md"><img src="https://img.shields.io/badge/Galego-0969da?style=for-the-badge" alt="Galego"></a>
  <a href="README.pt.md"><img src="https://img.shields.io/badge/Portugu%C3%AAs-6e7781?style=for-the-badge" alt="Português"></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/Fran%C3%A7ais-6e7781?style=for-the-badge" alt="Français"></a>
</p>

# MantPro

<p align="center">
  <img src="recursos/logo.png" alt="Logotipo de MantPro" width="200"/>
</p>

<p align="center">
  <strong>CMMS gratuíto e de código aberto para xestionar o mantemento preventivo e correctivo da túa planta, obradoiro ou frota, dende o PC e Android.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Offline--first-✔-success.svg" alt="Offline-first">
  <img src="https://img.shields.io/badge/Sen%20subscrici%C3%B3n-100%25%20de%20balde-orange.svg" alt="Sen subscrición">
</p>

---

## 🧩 Que problema resolve?

En moitos obradoiros e plantas pequenas ou medianas, o mantemento lévase entre
papeis, un Excel compartido e mensaxes de WhatsApp. Funciona, ata que alguén
precisa saber **que se lle fixo a unha máquina concreta**, quen o fixo, cando e
con que material, e esa información está repartida entre tres sitios distintos
(ou en ningún).

**MantPro centraliza iso**: cada técnico rexistra a súa intervención dende o
móbil, no momento, con fotos de antes e despois se fai falta, e todo queda
ordenado no PC por máquina, por data e por persoa, listo para consultalo ou
sacar un informe en PDF.

## 🎯 Para quen é?

Pensado para quen leva o mantemento do día a día, non para departamentos de
informática: técnicos de mantemento, responsables de planta, obradoiros, pemes
industriais e encargados de almacén que precisan un control real de máquinas,
intervencións e stock sen depender de follas de cálculo soltas.

## 🆚 Por que MantPro e non un CMMS comercial?

- **Código aberto e de balde**: código aberto baixo AGPL-3.0, sen límite de
  técnicos, máquinas ou rexistros
- **Sen subscrición**: non se paga por usuario nin por mes de uso
- **Os teus datos, na túa infraestrutura**: a base de datos vive no teu propio
  PC; non dependes de que un servizo na nube dun terceiro siga existindo o ano
  que vén
- **Sen conexión de verdade**: o móbil funciona sen conexión a internet nin ao
  PC durante toda a xornada, e sincroniza en canto volve haber rede
- **Feito dende o propio mantemento**: as funcións foron saíndo de necesidades
  reais de obradoiro (fotos de antes/despois, vínculo a máquina, stock de
  recambios, avisos recorrentes...), non dunha lista de requisitos xenérica de
  CMMS

## 🎬 Vídeo de demostración

https://github.com/user-attachments/assets/11572710-e0ba-4f8b-b914-0a959006d4fb

## 📸 Capturas de pantalla

### Aplicación de escritorio

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Panel" width="45%"/>
  <img src="Capturas/Almacen.png" alt="Xestión do almacén" width="45%"/>
</p>

### Aplicación móbil

<p align="center">
  <img src="Capturas/Dashboard-movil.jpg" alt="Panel no móbil" width="30%"/>
  <img src="Capturas/Almacen-movil.jpg" alt="Almacén no móbil" width="30%"/>
  <img src="Capturas/Historial-movil.jpg" alt="Historial no móbil" width="30%"/>
</p>

---

## 📋 Índice

- [Que problema resolve?](#-que-problema-resolve)
- [Para quen é?](#-para-quen-é)
- [Por que MantPro?](#-por-que-mantpro-e-non-un-cmms-comercial)
- [Vídeo de demostración](#-vídeo-de-demostración)
- [Capturas de pantalla](#-capturas-de-pantalla)
- [Descargas](#-descargas)
- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Usuarios e acceso](#-usuarios-e-acceso)
- [Maquinaria](#-maquinaria)
- [Stock do almacén](#-stock-do-almacén)
- [Sincronización PC-móbil](#-sincronización-pc-móbil)
- [Copias de seguranza](#-copias-de-seguranza)
- [Estrutura do proxecto](#-estrutura-do-proxecto)
- [Contribuír](#-contribuír)
- [Licenza](#-licenza)
- [Contacto](#-contacto)

---

## 📦 Descargas

Podes descargar as versións precompiladas dende [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: executable `.exe` para Windows
- **Linux**:
  - Binario executable de Linux
  - AppImage portable
  - Tamén dispoñible en **AUR** (Arch User Repository)
  - Tamén dispoñible en [**OBS**](https://build.opensuse.org/package/show/home:danitxu79/MantPro) (openSUSE Build Service) para openSUSE Tumbleweed e Slowroll
- **Android**: ficheiros `.apk` para instalación directa
  - `MantPro.apk`: aplicación de traballos de mantemento
  - `MantProStock.apk`: aplicación de stock do almacén

---

## ✨ Características

### 💻 Aplicación de escritorio (PC)

- **👥 Xestión de usuarios**: inicio de sesión con usuario e contrasinal, roles de administrador e técnico, alta e baixa de usuarios, e restablecemento de contrasinais
- **✍️ Autoría dos traballos**: cada intervención garda quen a fixo, visible no historial e nos informes
- **🔒 Permisos por rexistro**: un técnico só pode editar ou borrar os seus propios traballos; un administrador pode xestionar calquera, incluída a reasignación do autor dun ou varios rexistros á vez
- **📋 Auditoría de cambios**: rexistro de quen edita ou borra cada traballo (non só quen o creou), consultable e filtrable por técnico e por tipo de acción dende "Rexistro de cambios" (só administradores)
- **🔐 Sesións de dispositivos**: lista os móbiles vinculados a cada usuario, co seu modelo real, e permite revogar unha ou varias sesións concretas sen desactivar o usuario enteiro (só administradores). Ao volver iniciar sesión dende o mesmo dispositivo, a sesión anterior substitúese automaticamente en vez de acumularse
- **📊 Panel con KPI e gráficos**: tarxetas de avisos pendentes, tarefas por facer, rexistros do mes e MTBF/MTTR medios de toda a planta, ademais de gráficos das máquinas con máis avarías e de avarías por mes, debuxados sen depender de bibliotecas externas
- **🎨 Temas visuais**: escolle entre modo escuro (por defecto), claro ou un estilo retro inspirado en Windows 98, dende o menú "Aparencia"
- **📅 Calendario interactivo**: visualiza e xestiona as tarefas de mantemento con códigos de cor (festivos, vacacións, días con tarefas)
- **📝 Historial completo**: rexistro histórico de todas as intervencións feitas, con fotos de antes/despois e unha **colección de fotos** adicional por traballo; pódense borrar varios rexistros á vez
- **📄 Informes PDF**: xeración automática de informes profesionais con logotipo personalizable
- **📸 Xestión de imaxes**: almacenamento e visualización das fotos das intervencións
- **📱 Sincronización móbil**: servidor integrado (arranca automaticamente) para sincronizar coa aplicación móbil mediante QR
- **🔍 Sistema de busca**: busca avanzada por datas, etiquetas e contido
- **👤 Filtro por técnico**: filtra o historial e as exportacións (PDF, CSV e Excel) pola persoa que fixo o traballo
- **📦 Copia e restauración**: copia manual completa (BD + fotos) escollendo onde gardala, copia automática incremental ao pechar a aplicación (ver [Copias de seguranza](#-copias-de-seguranza)), e restauración con barra de progreso, co submenú `Ficheiro > Restaurar` para escoller entre calquera copia manual ou ir directamente ás copias automáticas
- **🏷️ Sistema de etiquetas**: clasificación con etiquetas (Urxente, Eléctrico, Mecánico, Preventivo)
- **🔨 Tarefas pendentes**: xestión de traballos pendentes (crear, completar, editar, eliminar) e **asignación a un técnico concreto**
- **🚦 Prioridade dos pendentes**: cada traballo pendente ten unha prioridade (Baixa, Media, Alta ou Crítica) para decidir cal atacar primeiro, coa súa cor na lista; tamén se lle poden achegar fotos á súa colección
- **↩️ Reverter a pendente**: se un traballo se completou por erro, pódese devolver a Pendentes cun clic dende o historial (con aviso se tiña máquina vinculada, xa que se perdería ese dato), e queda rexistrado na auditoría
- **🔁 Lembretes**: avisos de mantemento que se repiten automaticamente. Se pasa a data non se saltan: quedan en **Pendente** (laranxa) mentres dura a marxe e despois en **Atrasado** (vermello) ata que se fan, e a data seguinte cóntase dende o día real en que se fixo o traballo
- **📦 Control do stock do almacén**: estrutura de andeis, baldas e seccións configurable, ficha de materiais con foto, entradas/saídas con historial e alertas de stock por baixo do mínimo
- **📄 Exportar o stock**: botón "📄 Exportar" na lapela de stock para sacar o almacén enteiro, unha zona ou un andel a PDF, CSV ou Excel, ordenado por localización; a lapela de stock por baixo do mínimo tamén ten o seu botón para exportar só os materiais en alerta
- **🗑️ Tempo máximo de gardado**: `Ferramentas` permite borrar do historial os traballos máis antigos que un número de anos, meses ou días, coas súas fotos e unha copia de seguranza previa (só administradores)
- **📥 Importar dende Excel/CSV**: `Ficheiro > Importar dende Excel/CSV…` (só administradores) trae máquinas, artigos do almacén, avisos recorrentes e usuarios dende un modelo descargable ou dende o teu propio Excel (unha folla ou todo o libro dunha vez), emparellando soas as columnas, con vista previa fila a fila e copia de seguranza previa. As localizacións (zonas, andeis, baldas) e máquinas superiores que non existan créanse soas, e os usuarios reciben un contrasinal temporal que terán que cambiar ao entrar
- **🏭 Control de maquinaria**: árbore de máquinas e submáquinas con foto achegada, contador de traballos por ano e mes, e vínculo directo dende cada traballo rexistrado ou editado (ver [Maquinaria](#-maquinaria))
- **📊 Exportación**: a PDF, CSV e Excel, con filtro opcional por técnico e indicando a máquina/submáquina de cada traballo, se a ten

### 📱 Aplicación móbil (Android)

- **🔐 Acceso con usuario**: cada técnico inicia sesión unha vez e a sesión queda gardada no dispositivo
- **📝 Rexistro rápido**: captura de intervencións sobre o terreo, asinadas automaticamente co seu usuario
- **📷 Cámara integrada**: toma de fotos e edición con anotacións
- **🖼️ Colección de fotos**: ademais das fotos de antes e despois, engade a un traballo ou pendente todas as fotos que queiras (cámara ou galería); ao tocar calquera foto vese a pantalla completa, pasando dunha a outra e ampliando con dous dedos
- **✏️ Editor de imaxes**: debuxa sobre as fotos para marcar zonas de interese
- **🔄 Sincronización automática**: envío automático de datos ao PC mediante código QR
- **💾 Almacenamento local**: garda os rexistros sen conexión ata que se sincronicen
- **📋 Traballos pendentes**: visualiza e xestiona as tarefas asignadas dende o PC, co filtro **"Só os meus"**
- **🔄 Posta ao día ao abrir**: ao arrancar, a aplicación sincroniza en segundo plano os datos de todas as lapelas
- **🔁 Volver sincronizar a man**: as lapelas Pendentes, Historial e Lembretes teñen o seu propio botón para reenviar de inmediato o que teña o móbil e aínda non teña o PC
- **↩️ Reverter a pendente**: mantendo premido un rexistro do Historial pódese devolver á lapela Pendentes se se completou por erro
- **🏷️ Etiquetas rápidas**: sistema de etiquetado rápido con caixas de verificación
- **🔌 Modo sen conexión**: traballa sen conexión e sincroniza cando poidas
- **⏰ Lembretes diarios**: notificación automática ás 8:00 (hora local) se hai traballos pendentes sen completar
- **🧰 Material usado**: engade ao traballo o material do almacén que empregaches, buscándoo polo nome ou o código; descóntase só do stock ao gardar (ver [Material usado nun traballo](#-stock-do-almacén))
- **🏭 Vincular máquina**: escolle nun despregable a máquina ou submáquina na que se fixo o traballo, tanto ao crear un rexistro novo como ao editar un xa sincronizado do historial

### 📦 Aplicación móbil de stock (Android)

Aplicación independente (`mantpro_stock_app`), pensada para consultar e mover
o stock do almacén dende o móbil sen necesidade da aplicación de traballos.

- **🔐 Acceso con usuario**: emprega o mesmo sistema de usuarios e sesión que a aplicación de traballos
- **🗂️ Navegación polo almacén**: árbore de andeis > baldas > seccións, igual que no PC
- **🔎 Busca de materiais**: por nome, código, descrición ou localización
- **➕➖ Entradas e saídas**: rexistra movementos de stock dende o móbil, con motivo opcional
- **🔀 Traslados**: mover un material de sección queda reflectido no seu historial de movementos
- **🎨 Aviso visual de stock**: cantidade en vermello por baixo do mínimo, en verde por riba e coa cor por defecto se coincide exactamente
- **⚠️ Stock por baixo do mínimo**: lapela dedicada aos materiais en alerta
- **🔄 Actualización automática**: a pantalla refréscase soa ao detectar cambios, tanto se o cambio se fixo no propio móbil como no PC
- **🔌 Modo sen conexión**: sen conexión co PC a aplicación non queda esperando: consulta os datos gardados e deixa rexistrar altas, edicións, entradas e saídas ao momento, que se envían soas ao PC en canto volve estar accesible
- **🔔 Lembrete diario de comprobación de stock**: notificación automática ás 8:00 (hora local) que convida a revisar a cantidade real de 5 materiais do almacén, escollidos ao chou e distintos cada día; ao premela ábrese unha pantalla para corrixir a cantidade de cada un sen ter que buscalos. Se non hai ningún material dado de alta, non se amosa ningunha notificación

---

## 🔧 Requisitos

### Aplicación de escritorio

- **Python**: 3.8 ou superior
- **Sistema operativo**: Windows ou Linux
- **Dependencias de Python**:
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - xlsxwriter
  - openpyxl
  - sqlite3 (incluído en Python)

### Aplicación móbil

Aplícase tanto a `mantenimiento_app` (traballos) como a `mantpro_stock_app` (stock):

- **Flutter**: 3.0 ou superior
- **Dart SDK**: 2.17 ou superior
- **Android**: API Level 21+ (Android 5.0+)

---

## 📥 Instalación

### Aplicación de escritorio

#### Opción 1: descarga precompilada (recomendado)

Descarga a versión correspondente ao teu sistema dende [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: descarga e executa o `.exe`
- **Linux**:
  - Descarga o binario executable e dálle permisos de execución: `chmod +x mantpro`
  - Ou emprega o **AppImage** (sen instalación): `chmod +x MantPro.AppImage && ./MantPro.AppImage`
  - Os paquetes **`.deb`** e **`.rpm`** están asinados dixitalmente con GPG (ver [Verificar a sinatura dos paquetes](#-verificar-a-sinatura-dos-paquetes-linux))
  - **Arch Linux**: dispoñible en AUR: `yay -S mantpro` ou `paru -S mantpro`
  - **openSUSE Tumbleweed / Slowroll**: dispoñible en [OBS](https://build.opensuse.org/package/show/home:danitxu79/MantPro), compilado co Python e o PyQt6 da propia distribución e actualizado con `zypper`:
    ```bash
    sudo zypper ar -f https://download.opensuse.org/repositories/home:/danitxu79/openSUSE_Tumbleweed/home:danitxu79.repo
    sudo zypper in mantpro
    ```
    (en Slowroll, cambia `openSUSE_Tumbleweed` por `openSUSE_Slowroll` na URL)

#### 🔏 Verificar a sinatura dos paquetes (Linux)

Os paquetes `.deb` e `.rpm` publicados en cada release están asinados coa chave GPG oficial de AnabasaSoft. Para verificalos antes de instalalos:

1. Descarga a chave pública do repositorio ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)) a un ficheiro (**non empregues `curl | rpm --import -`**: algunhas versións de `rpm` non admiten ler a chave pola entrada estándar e fallan):
   ```bash
   curl -sL https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/firma/anabasasoft_public.asc -o /tmp/anabasasoft_public.asc
   ```

2. Importa a chave (só fai falta unha vez por equipo):
   ```bash
   # Fedora, openSUSE, RHEL... (paquete .rpm)
   sudo rpm --import /tmp/anabasasoft_public.asc

   # Debian, Ubuntu... (paquete .deb, require dpkg-sig)
   gpg --import /tmp/anabasasoft_public.asc
   ```

3. Comproba que a chave se importou correctamente:
   ```bash
   rpm -qa 'gpg-pubkey*' --qf '%{name}-%{version}-%{release} --> %{summary}\n' | grep -i anabasasoft
   ```

4. Verifica a sinatura do paquete descargado:
   ```bash
   # RPM
   rpm --checksig mantpro-*.rpm

   # DEB
   dpkg-sig --verify mantpro_*.deb
   ```
   Unha sinatura correcta amosa `OK` na liña da sinatura (en vez de `NOKEY` ou `MISSING KEYS`).

Unha sinatura válida confirma que o paquete procede de AnabasaSoft e que non se modificou.

#### Opción 2: instalación dende o código fonte

1. **Clonar o repositorio**:
   ```bash
   git clone https://github.com/AnabasaSoft/MantPro.git
   cd MantPro
   ```

2. **Crear un contorno virtual** (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar as dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Executar a aplicación**:
   ```bash
   python main.py
   ```

### Aplicación móbil

#### Opción 1: descarga directa (recomendado)

Descarga o `.apk` correspondente dende [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) e instálao no teu dispositivo Android: `MantPro.apk` para os traballos, `MantProStock.apk` para o stock do almacén. Son aplicacións independentes e podes instalar unha, a outra ou as dúas.

**Nota**: é posible que teñas que habilitar "Orixes descoñecidas" na configuración de seguranza do dispositivo.

#### Opción 2: compilar dende o código fonte

1. **Ir ao directorio da aplicación móbil** (`mantenimiento_app` para os traballos, `mantpro_stock_app` para o stock):
   ```bash
   cd mantenimiento_app
   ```

2. **Instalar as dependencias**:
   ```bash
   flutter pub get
   ```

3. **Executar nun dispositivo ou emulador**:
   ```bash
   flutter run
   ```

4. **Compilar o APK (Android)**:
   ```bash
   flutter build apk --release
   ```

---

## 🚀 Uso

### Primeira configuración

#### Aplicación de escritorio

1. **Iniciar a aplicación**: executa `python main.py` (o servidor de sincronización arranca só, non fai falta inicialo a man)
2. **Primeiro acceso**: no primeiro arranque créase o usuario `admin` co contrasinal `admin`. A aplicación **obriga a cambialo** ao entrar
3. **Crear os usuarios**: menú `Ferramentas` > `👥 Xestión de usuarios` > dá de alta cada técnico
4. **Configurar o logotipo** (opcional): menú `Ficheiro` > `📤 Exportar` > `📄 Opcións PDF` > `🖼️ Engadir / cambiar o logotipo`
5. **Rexistrar un traballo**: lapela "📝 Rexistrar" > enche o resumo e os detalles > "💾 GARDAR REXISTRO"
6. **Crear un pendente**: lapela "🔨 Pendentes" > grupo "Traballo novo" (Título + Detalles + "Asignar a") > "Engadir"

#### Aplicación móbil

1. **Instalar a aplicación** no teu dispositivo móbil
2. **Conectar co PC**:
   - Asegúrate de que o PC e o móbil están na mesma rede WiFi
   - No PC: menú `Ferramentas` > `📲 Sincronizar App (QR)`
   - No móbil: toca "Vincular PC" e escanea o código
3. **Iniciar sesión**: introduce o usuario e o contrasinal que che creou o administrador. A sesión queda gardada: só hai que facelo unha vez
4. **Listo**: xa podes rexistrar intervencións dende o móbil

### Fluxo de traballo habitual

#### Dende o PC

1. **Crear e asignar unha tarefa pendente**:
   - Lapela "🔨 Pendentes" > grupo "Traballo novo" > enche o Título e os Detalles, escolle o técnico en "Asignar a" > "Engadir"
   - Xestiónaa cos botóns "✅ Completar", "✏️ Editar", "❌ Eliminar" ou "👤 Reasignar"
   - O despregable "Ver os de" filtra a lista por técnico (inclúe "Sen asignar")

2. **Revisar os traballos completados**:
   - Os traballos sincronizados dende o móbil aparecen automaticamente
   - Revisa as fotos (antes/despois e colección) e os detalles na lapela "🗂 Historial" ou no "📅 Calendario"
   - A columna "Feito por" indica quen fixo cada traballo, e o despregable de arriba permite ver só os dunha persoa

3. **Xerar informes**:
   - Menú `Ficheiro` > `📤 Exportar` > `📄 Opcións PDF` > `📄 Xerar PDF agora`
   - No diálogo podes escoller o técnico, e o seu nome aparece no título do informe
   - Ou exporta a `📄 CSV` / `📊 Excel` dende `Ficheiro` > `📤 Exportar`

#### Dende o móbil

1. **Vincular co PC e iniciar sesión** (só a primeira vez, ou se cambias de rede):
   - Toca "Vincular PC" e escanea o QR que amosa o PC
   - Introduce o teu usuario e o contrasinal
   - O móbil garda o enderezo do PC e a túa sesión para sincronizar automaticamente a partir de aí

2. **Rexistrar unha intervención**:
   - Toca "Novo" ou selecciona un traballo pendente xa sincronizado dende o PC
   - Co chip "Só os meus" ves unicamente os traballos que che asignaron
   - Completa o título e os detalles
   - Fai a foto de "antes" e, opcionalmente, a de "despois" coa cámara; se fai falta, engade máis á colección de fotos
   - Debuxa ou anota sobre a foto se fai falta
   - Selecciona as etiquetas axeitadas
   - Garda

3. **Sincronizar**:
   - Ao abrir a aplicación sincronízase todo en segundo plano (verás un indicador na barra superior)
   - Tamén o podes forzar tirando da lista cara abaixo ou coa icona de sincronización
   - Os rexistros envíanse ao PC e elimínanse do móbil cando se confirma o envío
   - Todo funciona sen conexión: o pendente gárdase e súbese cando hai cobertura

---

## 👥 Usuarios e acceso

### Roles

Un mesmo usuario pode ter **un ou varios roles á vez** (por exemplo, técnico e
almacén). Roles dispoñibles:

| Rol | Que pode facer |
|-----|----------------|
| **Administrador** | Todo o que fan o técnico e o de almacén, ademais de dar de alta e de baixa usuarios, cambiar roles, restablecer contrasinais, editar ou borrar **calquera** rexistro do historial, reasignar o autor dun ou varios rexistros á vez, e consultar o rexistro de auditoría de cambios |
| **Técnico** | Rexistrar traballos, completar pendentes e avisos, editar ou borrar **só os seus propios** rexistros do historial, e cambiar o seu propio contrasinal |
| **Almacén** | Dar de alta ou editar materiais e rexistrar entradas/saídas de stock dende a aplicación móbil **MantPro Stock** |

Sempre debe quedar **polo menos un administrador activo**: a aplicación impide
quitarlle o rol ou desactivar o último que queda.

> Dende a aplicación de escritorio, calquera usuario (sexa cal sexa o seu rol)
> pode rexistrar movementos de stock; o rol **Almacén** é o que habilita esa
> mesma xestión (altas, edicións e movementos) dende o móbil.

### Xestión dende o PC

- **Alta**: `Ferramentas` > `👥 Xestión de usuarios` > enche o usuario, o nome,
  o contrasinal e o rol > "➕ Engadir". Se deixas marcado "Pedir cambio ao
  entrar", a persoa terá que definir o seu propio contrasinal no primeiro
  acceso.
- **Baixa**: faise de forma **lóxica** (o usuario queda inactivo). Nunca se
  borra, para non romper a autoría dos traballos que xa fixo.
- **Restablecer o contrasinal**: útil cando alguén o esquece. Ao cambialo
  péchanse automaticamente todas as sesións abertas desa persoa no móbil.
- **Cambiar o propio contrasinal**: `Ferramentas` > `🔑 Cambiar o meu contrasinal`.

### Sesións de dispositivos

`Ferramentas` > `🔐 Sesións de dispositivos` (só administradores) lista todas
as sesións abertas no móbil de todos os usuarios, co modelo do dispositivo,
cando se iniciou, cando caduca e se segue activa ou xa caducou. Pódense
seleccionar unha ou varias filas á vez e revogalas, o que pecha a sesión dese
móbil sen necesidade de desactivar o usuario enteiro (que pecharía *todos* os
seus dispositivos de golpe).

Se un usuario volve iniciar sesión dende un dispositivo co que xa tiña unha
sesión aberta (mesmo fabricante e modelo), a sesión anterior dese dispositivo
bórrase automaticamente ao crear a nova, en vez de quedar acumulada como unha
sesión solta máis na listaxe.

### Autoría dos traballos

Cada rexistro garda o técnico que o fixo, tanto se se creou no PC como se
chegou do móbil. Os rexistros anteriores á implantación do sistema de usuarios
quedaron marcados como **`Histórico`**.

No móbil, a atribución decídea **sempre o servidor** a partir do token da
sesión, nunca un dato enviado pola aplicación. Un dispositivo non pode asinar
traballos en nome doutra persoa.

Dende o PC, un técnico só pode editar ou borrar os seus propios rexistros do
historial; un administrador pode facelo con calquera. Co botón dereito sobre
unha ou varias filas do historial (selección múltiple con Ctrl/Maiús), un
administrador tamén pode **reasignar o autor** en bloque, e cada cambio queda
anotado no rexistro de auditoría.

### Rexistro de cambios (auditoría)

Cada vez que se edita ou se borra un traballo queda constancia de quen o fixo,
cando e que cambiou. Os administradores poden consultalo dende
`Ferramentas` > `📋 Rexistro de cambios`, con filtros por técnico e por tipo de
acción (editar/borrar).

### Sesión no móbil

O técnico inicia sesión unha vez e o token queda gardado no dispositivo. A
sesión péchase soa se o administrador desactiva o usuario ou lle restablece o
contrasinal; nese caso a aplicación volve á pantalla de acceso **sen perder os
rexistros que aínda estean pendentes de subir**.

---

## 🏭 Maquinaria

> Xestión dispoñible dende a aplicación de escritorio, co vínculo á máquina
> tamén seleccionable dende o móbil ao rexistrar ou editar un traballo.

Lapela "🏭 Máquinas" do PC, pensada para levar o control de avarías e
intervencións de cada equipo ao longo do tempo.

- **🌳 Árbore de maquinaria**: as máquinas poden ter submáquinas (por exemplo,
  unha liña con varios equipos), formando unha xerarquía tan profunda como faga
  falta
- **📅 Traballos organizados por ano e mes**: ao despregar unha máquina vense
  os anos con traballos, e ao despregar un ano, os meses; cada nivel amosa un
  contador de cantos traballos ten, con carga baixo demanda para non ralentizar
  a árbore
- **🖱️ Acceso directo ao traballo**: con dobre clic sobre un traballo da árbore
  ábrese directamente a súa ficha de edición
- **📸 Foto da máquina**: cada máquina ou submáquina pode ter unha foto
  achegada, visible nun recadro xunto á árbore ao seleccionala
- **🔗 Vínculo dende cada traballo**: ao rexistrar un traballo novo (PC ou
  móbil) ou editar un existente pódese escoller a que máquina/submáquina
  pertence
- **📊 Nas exportacións**: a máquina ou submáquina vinculada aparece como
  columna adicional nas exportacións a PDF, CSV e Excel

---

## 📦 Stock do almacén

> Xestión completa dende a aplicación de escritorio, con consulta e movementos
> tamén dispoñibles dende o móbil (`mantpro_stock_app`). Vive na súa propia
> base de datos (`almacen.db`), independente da dos traballos de mantemento.

### Estrutura do almacén

O almacén organízase en tres niveis, inspirados nas convencións habituais de
codificación de localizacións de almacén:

```
Andel → Balda → Sección
```

- Ao crear un andel defínese o **número de baldas**, o **número de seccións
  por balda** (0 = sen seccións predefinidas, pódense engadir despois) e se ten
  **oco no chan** baixo a balda inferior, que se xestiona como unha balda
  especial ("Chan")
- As baldas numéranse de abaixo arriba empezando no 1, para poder engadir
  baldas novas sen ter que renumerar as existentes
- Non se pode eliminar un andel, unha balda ou unha sección mentres conteña
  material situado

A estrutura xestiónase dende o botón **"⚙️ Configurar almacén"** da lapela
"📦 Stock de almacén", visible **só para os administradores**.

### Materiais

- Alta e edición con código (opcional), nome, descrición, unidade, stock
  mínimo, localización (andel / balda / sección) e **foto achegada**
- Busca por **nome, código, descrición ou localización**
- O stock resáltase en **vermello** por baixo do mínimo, en **verde** por riba
  e coa cor por defecto se coincide exactamente co mínimo, tanto no PC como no
  móbil
- Seleccionando varios materiais á vez (Ctrl/Maiús + botón dereito) no PC
  pódense **mover de localización** ou **eliminar** en bloque

### Entradas, saídas e traslados

- **Calquera usuario** pode rexistrar entradas e saídas de stock; só a
  configuración da estrutura do almacén está restrinxida aos administradores
- Cada movemento queda rexistrado con data, cantidade, usuario e un motivo
  opcional, visible no historial xunto a cada material
- As saídas rexistradas a man (PC ou `mantpro_stock_app`) non poden deixar o
  stock en negativo
- Cambiar a localización dun material tamén queda rexistrado no seu historial,
  como un movemento de tipo **traslado** (de que sección a que sección)

### Material usado nun traballo (MantPro)

Ao completar un traballo dende a aplicación **MantPro** (móbil), pódese engadir
o material empregado buscándoo polo nome ou o código e indicando a cantidade.
Ao gardar o traballo, ese material descóntase automaticamente do almacén, co
motivo "Usado nun traballo: ..." para manter a trazabilidade.

A diferenza das saídas manuais, **este desconto si pode deixar o stock en
negativo**: o material xa se usou fisicamente para facer o traballo aínda que
non houbese stock rexistrado abondo, así que bloquear o movemento non tería
sentido. O stock negativo verase tanto no PC como en `mantpro_stock_app`, e
serve de aviso de que hai que comprobar e repoñer ese material canto antes.

### Alertas de stock por baixo do mínimo

A lapela **"⚠️ Stock por baixo do mínimo"** amosa, nunha vista á parte, os
materiais sen stock ou por baixo do mínimo establecido. O propio título da
lapela indica cantos materiais están en alerta, e dende alí pódese saltar
directamente ao material en "Stock de almacén", rexistrar unha entrada sen
cambiar de lapela ou exportar a lista co botón "📄 Exportar".

### Exportar o stock

Na lapela **"📦 Stock de almacén"** do PC, o botón **"📄 Exportar"** abre unha
xanela para escoller o **formato** (PDF, CSV ou Excel) e **que exportar**: todo
o almacén, unha zona ou un só andel. A lista sae ordenada por localización,
para poder percorrer o almacén con ela na man; o PDF e o Excel inclúen ademais
a data, o número de materiais e cantos están por baixo do mínimo (en
vermello). A propia táboa de stock tamén se amosa ordenada por localización
por defecto (Andel 1, 2… 10).

---

## 🔄 Sincronización PC-móbil

### Como funciona

MantPro emprega un sistema de sincronización baseado en:

1. **Servidor Flask** integrado na aplicación de escritorio
2. **Códigos QR** para unha conexión rápida e segura
3. **API REST autenticada por token**: todos os puntos de acceso de datos
   esixen unha sesión válida; se o token deixa de valer, o servidor responde
   `401` e o móbil volve ao inicio de sesión
4. **WiFi local**, sen necesidade de internet
5. **Sincronización completa ao abrir a aplicación**, en segundo plano e sen
   bloquear a interface

> ⚠️ O tráfico viaxa por **HTTP dentro da rede local**. O sistema de usuarios
> achega trazabilidade (saber quen fixo cada traballo), non protección fronte a
> alguén con acceso a esa mesma rede.

### Configuración da rede

Para que a sincronización funcione:

- ✅ O PC e o móbil deben estar na **mesma rede WiFi**
- ✅ O **cortalumes** debe permitir conexións no porto 5000 (ou o configurado)
- ✅ Se empregas Windows, poida que teñas que crear unha excepción no cortalumes

### Solución de problemas

**O móbil non conecta co PC:**
- Verifica que os dous dispositivos están na mesma rede
- Comproba que o servidor está activo no PC (icona verde)
- Proba a desactivar temporalmente o cortalumes do PC
- Xera de novo o código QR e volve escanealo

**Non podo iniciar sesión dende o móbil:**
- Comproba que MantPro está aberto no PC: o inicio de sesión valídase contra el
- Verifica o usuario e o contrasinal co administrador; pode restablecelo
- Se o PC cambiou de IP, volve escanear o QR dende a propia pantalla de acceso ("Vincular outro PC")

**A aplicación devolveume á pantalla de acceso:**
- É normal se o administrador restableceu o teu contrasinal ou desactivou o teu usuario
- Os teus rexistros sen subir **non se perden**: volve entrar e sincronízanse

**Esquecín o contrasinal de administrador:**
- Outro administrador pode restablecelo dende `Ferramentas` > `👥 Xestión de usuarios`
- Se non hai ningún outro administrador, hai que restablecelo directamente na
  táboa `usuarios` da base de datos

**As fotos non se sincronizan:**
- Verifica que hai espazo abondo no disco do PC
- Comproba os permisos do cartafol `fotos_recibidas`
- Asegúrate de que a foto se gardou correctamente no móbil

**Non me chega a notificación diaria de avisos pendentes (Android):**
- Comproba que o permiso de notificacións está concedido: `Axustes → Aplicacións → MantPro → Notificacións`
- En fabricantes como **OPPO/Realme (ColorOS), Xiaomi (MIUI) ou Huawei**, o sistema pode deter a alarma programada aínda que o permiso estea concedido. Ademais, hai que:
  - `Axustes → Batería → Uso da batería por aplicación → MantPro` → poñelo en **"Sen restricións"**
  - `Axustes → Batería → Inicio automático` → **activar** MantPro
- A notificación volve avaliarse cada vez que abres o Panel, así que se acabas de marcar un traballo como completado, ábreo de novo para que se cancele ou se reprograme correctamente.

**Non me chega a notificación diaria de comprobación de stock (MantPro Stock):**
- Aplícanse as mesmas comprobacións que en MantPro (permiso de notificacións e exclusión da optimización da batería, ver arriba)
- Se o almacén non ten ningún material dado de alta, non se amosa ningunha notificación: é o comportamento esperado
- Volve avaliarse cada vez que a aplicación se sincroniza co PC (ao abrila e cada 25 segundos mentres está aberta)

### 🔒 Nota sobre seguranza

A sincronización viaxa por HTTP dentro da rede local. O sistema de usuarios
está pensado para a **trazabilidade** (saber quen fixo cada traballo), non como
barreira fronte a alguén con acceso a esa mesma rede. Se no futuro se expón o
servidor fóra da rede local, o tráfico debe ir cifrado (VPN ou túnel con
HTTPS).

---

## 💾 Copias de seguranza

MantPro distingue entre dous tipos de copia, pensados para momentos distintos:

### Copia automática (ao pechar a aplicación)

Cada vez que se pecha o programa faise, en segundo plano e sen necesidade de
intervención, unha copia rápida pensada para que non se note aínda que pasen
os anos:

- **Bases de datos**: `mantenimiento.db` e `almacen.db` empaquétanse enteiras
  nun ZIP (`auto_backup_db_<data>.zip`) cada vez, de forma rotativa,
  conservando só as 3 máis recentes.
- **Fotos**: en vez de volver comprimir todo o historial de fotos en cada
  peche, mantéñense uns ZIP incrementais por ano (`fotos_backup_<ano>.zip`):
  cada peche só engade ao ZIP do ano que corresponda as fotos que aínda non
  estaban dentro, sen tocar nin volver comprimir as de anos anteriores. Así o
  tempo de peche non medra co tempo de uso da aplicación.

Mentres se fai esta copia amósase unha xanela cunha barra de progreso que
retén o foco, e o peche real da aplicación agarda a que remate.

### Copia manual (menú Ficheiro)

`Ficheiro > Copia de seguranza` segue xerando, como sempre, un único ZIP
(`backup_completo_<data>.zip`) coas dúas bases de datos e **todas** as fotos
xuntas e comprimidas, na localización que escollas. `Ficheiro > Restaurar`
ábrese como un submenú con dúas opcións: **"Restaurar..."**, para escoller
calquera ZIP a man, e **"Restaurar dende unha copia automática..."**, que abre
directamente o cartafol `backups_auto`. Nos dous casos, se o ZIP escollido é
unha copia automática, restáurase primeiro a base de datos e, con ela xa
restaurada, calcúlase que fotos fan falta e extráense unicamente dos
`fotos_backup_<ano>.zip` correspondentes, en vez de envorcalas todas. As tres
operacións (copia e as dúas restauracións) amosan a súa propia barra de
progreso con foco.

### Limpeza de fotos orfas

`Ferramentas > 🧹 Limpar Fotos Lixo` borra as fotos de `fotos_recibidas` que
xa non están referenciadas por ningún traballo, pendente ou máquina. Ao pechar
a aplicación e antes dunha copia manual tamén se limpa `fotos_recibidas` en
silencio, pero **só** esa opción do menú Ferramentas revisa ademais os
`fotos_backup_<ano>.zip` e reescríbeos sen as fotos orfas que puidesen conter,
para non arrastralas indefinidamente.

### Tempo máximo de gardado de traballos

`Ferramentas > 🗑️ Tempo máximo de gardado de traballos…` (só administradores)
pide un número e unha unidade (anos, meses ou días) e borra do historial todos
os traballos anteriores a esa data, contando dende hoxe. Antes de borrar amosa
cantos traballos se van eliminar e entre que datas, e pide confirmación.

- Antes de borrar gárdase unha copia das dúas bases de datos en
  `backups_auto/antes_borrado_trabajos_<data>.zip`, que a rotación da copia
  automática non elimina.
- Tamén se borran as súas fotos (antes, despois e colección), agás as que
  aínda use outro rexistro. As fotos non van nesa copia previa, pero seguen
  nos `fotos_backup_<ano>.zip` da copia automática ata que se emprega
  `Ferramentas > 🧹 Limpar Fotos Lixo`.
- Os móbiles quitan eses traballos do seu historial na seguinte
  sincronización.
- É un borrado puntual: non se repite só.

---

## 📁 Estrutura do proxecto

```
MantPro/
├── main.py                      # Punto de arranque (python main.py)
├── mantpro/                     # Código da aplicación de escritorio
│   ├── version.py               # Versión (pona CI dende o tag)
│   ├── nucleo/                  # Datos e lóxica, sen interface
│   │   ├── usuarios.py          # Usuarios, contrasinais, roles e sesións
│   │   ├── almacen.py           # Stock do almacén: estrutura, materiais e movementos
│   │   ├── maquinas.py          # Árbore de maquinaria e o seu historial de traballos
│   │   ├── basedatos.py         # Base de datos de traballos
│   │   └── importar.py          # Importación dende Excel/CSV
│   ├── interfaz/                # Xanelas PyQt6
│   │   ├── arranque.py          # Arranque: instancia única e inicio de sesión
│   │   ├── app.py               # Aplicación principal de escritorio
│   │   ├── servidor.py          # Servidor de sincronización cos móbiles
│   │   ├── pestanas/            # Unha por lapela: panel, calendario, stock...
│   │   ├── acciones/            # Accións dos menús: copias, exportar, importar, usuarios
│   │   ├── dialogos/            # Diálogos (incluídos inicio de sesión e xestión de usuarios)
│   │   └── widgets/             # Fotos e gráficos
│   └── idiomas/                 # Traducións do escritorio (ES / EN / EU / CA / GL / PT / FR)
├── recursos/                    # Iconas e logotipos
├── herramientas/                # Scripts do proxecto (verificar_idiomas.py...)
├── empaquetado/                 # Instalador de Windows (Inno Setup)
├── requirements.txt             # Dependencias de Python
├── README.gl.md                 # Este ficheiro
├── fotos_recibidas/             # Cartafol de imaxes
├── mantenimiento.db             # Base de datos SQLite (traballos de mantemento)
├── almacen.db                   # Base de datos SQLite (stock do almacén, independente)
├── mantenimiento_app/           # Aplicación móbil Flutter (traballos)
│   ├── lib/main.dart            # Código principal do móbil
│   ├── lib/i18n/                # Traducións do móbil (ES / EN / EU / CA / GL / PT / FR)
│   ├── pubspec.yaml             # Dependencias de Flutter
│   └── android/                 # Configuración de Android
├── mantpro_stock_app/           # Aplicación móbil Flutter (stock do almacén)
│   ├── lib/modelos.dart         # Modelos de datos e regra de cor do stock
│   ├── lib/pantallas/           # Pantallas: almacén, artigo, busca, por baixo do mínimo...
│   ├── lib/i18n/                # Traducións do móbil (ES / EN / EU / CA / GL / PT / FR)
│   ├── pubspec.yaml             # Dependencias de Flutter
│   └── android/                 # Configuración de Android
├── backups/                     # Copias manuais completas (BD + fotos)
├── backups_auto/                # Copias automáticas ao pechar (BD rotativa + fotos por ano)
└── docs/                        # Documentación adicional
```

> Os datos (base de datos, fotos e copias) non viven necesariamente xunto ao
> código: se non existe `mantenimiento.db` no cartafol actual, a aplicación
> emprega `~/.local/share/MantPro` en Linux ou `%APPDATA%\MantPro` en Windows.

### Base de datos

A aplicación emprega SQLite coas seguintes táboas:

- **`tareas`**: rexistro das intervencións feitas (data, descrición,
  etiquetas, fotos, **quen a fixo** (`usuario_id` e `usuario_nombre`) e a
  **máquina vinculada** (`maquina_id`), se a ten)
- **`maquinas`**: árbore de maquinaria (nome, máquina superior, notas e foto)
- **`pendientes`**: tarefas pendentes de facer (título, detalles, prioridade e
  **técnico asignado**: `asignado_a` e `asignado_nombre`)
- **`usuarios`**: persoas que empregan a aplicación (usuario, nome, hash do
  contrasinal, rol e se está activo)
- **`sesiones`**: tokens dos móbiles vinculados, coa súa data de caducidade
- **`avisos_recurrentes`**: avisos de mantemento que se repiten
  automaticamente
- **`dias_especiales`**: festivos, vacacións e días marcados no calendario
- **`auditoria`**: historial de quen edita ou borra cada traballo, con data,
  acción e detalle
- **`config`**: configuración interna da aplicación (logotipo, provincia, etc.)

Os contrasinais gárdanse con **PBKDF2-SHA256** (200.000 iteracións e salt por
usuario), nunca en claro. As táboas e columnas novas créanse soas ao arrancar,
sen perder os datos existentes.

> 🔐 `mantenimiento.db` contén hashes de contrasinais e tokens de sesión. Está
> en `.gitignore` por algo: non a subas nunca ao repositorio.

O stock do almacén vive na súa propia base de datos, **`almacen.db`**,
separada a propósito da dos traballos:

- **`estanterias`**: nome e se ten oco no chan
- **`baldas`**: baldas de cada andel, numeradas de abaixo arriba (a balda `0`
  representa o oco no chan)
- **`secciones`**: subdivisións dentro de cada balda
- **`materiales`**: código, nome, descrición, unidade, stock actual, stock
  mínimo, localización (sección) e foto
- **`movimientos`**: histórico de entradas e saídas, con data, cantidade,
  usuario e motivo

Créase automaticamente no primeiro arranque e inclúese nas copias de seguranza
(manuais e automáticas ao pechar a aplicación) xunto con `mantenimiento.db`.

---

## 🤝 Contribuír

As contribucións son benvidas! Se queres mellorar MantPro:

1. Fai un **fork** do proxecto
2. Crea unha **rama** para o teu cambio (`git checkout -b feature/AMiñaMellora`)
3. Fai **commit** dos cambios (`git commit -m 'Engade AMiñaMellora'`)
4. Fai **push** da rama (`git push origin feature/AMiñaMellora`)
5. Abre un **Pull Request**

---

## ✅ Feito

- **Xestión de usuarios**: inicio de sesión con usuario e contrasinal no PC e
  no móbil, varios roles por usuario (administrador / técnico / almacén), alta
  e baixa lóxica de usuarios, cambio e restablecemento de contrasinal.
- **Autoría dos traballos**: cada rexistro garda quen o fixo. Os rexistros
  anteriores ao sistema de usuarios quedan marcados como `Histórico`.
- **Sesión persistente no móbil**: o técnico inicia sesión unha vez e o token
  queda gardado no dispositivo.
- **API autenticada**: todos os puntos de acceso de datos esixen token; un
  `401` pecha a sesión do móbil e volve ao inicio de sesión sen perder os
  rexistros locais pendentes de enviar.
- **Pendentes asignados**: o PC asigna cada traballo a un técnico e o móbil
  pode filtrar por "Só os meus".
- **Filtro por técnico** no historial e na exportación a PDF, CSV e Excel.
- **Auditoría de edicións**: rexístrase quen edita ou borra un traballo (non
  só quen o creou), consultable e filtrable por técnico/acción dende
  "Rexistro de cambios".
- **Permisos por rexistro**: un técnico só pode editar ou borrar os seus
  propios traballos; un administrador pode xestionar calquera e reasignar o
  autor dun ou varios rexistros á vez (selección múltiple + menú contextual).
- **Temas visuais**: modo escuro (por defecto), claro ou clásico ao estilo
  Windows 98, seleccionable dende o menú "Aparencia" e lembrado entre sesións.
- **Copia baixo demanda con selección de destino**: ao xerar unha copia de
  seguranza manual pódese escoller onde gardala, en vez de ir sempre ao
  cartafol `backups` por defecto.
- **Control do stock do almacén**: estrutura configurable de andeis, baldas e
  seccións (só administradores), ficha de materiais con foto, entradas e
  saídas con historial (calquera usuario), traslados entre localizacións
  rexistrados no historial, selección múltiple con menú contextual para mover
  ou eliminar en bloque, e unha lapela dedicada aos materiais sen stock ou por
  baixo do mínimo. Con base de datos propia (`almacen.db`) e aplicación móbil
  independente (`mantpro_stock_app`) para consultar e mover o stock dende o
  teléfono.
- **Sesións de dispositivos**: listar os móbiles vinculados a cada usuario, co
  seu modelo real de dispositivo, e poder revogar unha ou varias sesións
  concretas sen ter que desactivar o usuario enteiro.
- **Listaxe de maquinaria**: árbore de máquinas e submáquinas con foto
  achegada, contador de traballos por ano e mes, e vínculo de cada traballo
  (PC ou móbil) á máquina na que se fixo, incluído nas exportacións a PDF, CSV
  e Excel.
- **Copia automática incremental**: o peche da aplicación xa non volve
  empaquetar todo o historial de fotos cada vez; as bases de datos rotan nun
  ZIP e as fotos repártense en ZIP incrementais por ano, cunha barra de
  progreso con foco tanto no peche como na copia e na restauración manuais
  (ver [Copias de seguranza](#-copias-de-seguranza)).
- **Reverter un traballo a pendente**: desfacer por erro a finalización dun
  traballo, tanto dende o historial do PC como mantendo premido o rexistro no
  móbil, con aviso de perda da máquina vinculada se a tiña e restauración
  automática do aviso recorrente de orixe, se viña dun.
- **Restaurar dende unha copia automática**: `Ficheiro > Restaurar` ábrese
  como un submenú para escoller entre calquera copia manual ou ir
  directamente ao cartafol de copias automáticas ao pechar a aplicación.
- **Lembrete diario de stock**: a aplicación `mantpro_stock_app` avisa cada
  mañá ás 8:00 para comprobar a cantidade real de 5 materiais do almacén (ao
  chou, distintos cada día) e permite corrixila ao momento dende a propia
  notificación.
- **Panel con KPI e gráficos de fiabilidade**: tarxetas de MTBF e MTTR medios
  de toda a planta, e gráficos de clasificación das máquinas con máis avarías
  e de avarías por mes, debuxados a man con `QPainter` sen depender de
  ningunha biblioteca de gráficos externa.
- **Substitución automática da sesión por dispositivo**: se un usuario volve
  iniciar sesión dende un móbil co que xa tiña unha sesión aberta, a anterior
  bórrase soa en vez de acumularse na listaxe de sesións.
- **Colección de fotos por traballo**: ademais de antes e despois, calquera
  número de fotos extra en traballos e pendentes, no PC e no móbil, cun visor
  a tamaño completo que pasa dunha a outra.
- **Avisos recorrentes que non se saltan**: un aviso atrasado queda pendente
  (laranxa) ou atrasado (vermello) ata facerse, e o ciclo seguinte cóntase
  dende a data real en que se fixo.
- **Exportar o stock do almacén** a PDF, CSV ou Excel, completo, por zona, por
  andel ou só os materiais por baixo do mínimo.
- **Tempo máximo de gardado de traballos**: borrado de traballos antigos con
  confirmación e copia de seguranza previa.
- **Importar dende Excel/CSV**: máquinas, artigos do almacén, avisos
  recorrentes e usuarios, con modelo, emparellamento de columnas, vista previa
  fila a fila e copia de seguranza previa.

## 📄 Licenza

Este proxecto está baixo a **GNU Affero General Public License v3.0 (AGPL-3.0)**.
Consulta o ficheiro `LICENSE` para o texto completo.

Copyright (C) 2026 AnabasaSoft

### Que significa na práctica

- ✅ Podes **usar** MantPro libremente, tamén na túa empresa e con fins comerciais
- ✅ Podes **estudar, modificar e redistribuír** o código
- ⚠️ Se distribúes unha versión modificada, debes publicala **tamén baixo AGPL-3.0**
- ⚠️ Se ofreces MantPro (ou un derivado) **como servizo a través dunha rede**,
  debes poñer o código fonte á disposición de quen o use, aínda que non
  distribúas ningún executable. Esta é a diferenza clave respecto á GPL v3
- ⚠️ Debes manter os avisos de copyright e de licenza

### Aviso de licenza

```
MantPro - Sistema de Mantemento Preventivo
Copyright (C) 2026 AnabasaSoft

Este programa é software libre: podes redistribuílo e/ou modificalo baixo
os termos da Licenza Pública Xeral Affero de GNU publicada pola Free
Software Foundation, xa sexa a versión 3 da Licenza ou (á túa elección)
calquera versión posterior.

Este programa distribúese coa esperanza de que sexa útil, pero SEN
NINGUNHA GARANTÍA; nin sequera a garantía implícita de COMERCIABILIDADE ou
IDONEIDADE PARA UN PROPÓSITO PARTICULAR. Consulta a Licenza Pública Xeral
Affero de GNU para máis detalles.

Deberías ter recibido unha copia da Licenza Pública Xeral Affero de GNU
xunto con este programa. Se non é así, consulta
<https://www.gnu.org/licenses/>.
```

> **Nota sobre licenzas comerciais**: AnabasaSoft é o único titular do
> copyright de MantPro e, polo tanto, pode ofrecer o mesmo código en
> condicións distintas da AGPL. Se precisas integrar MantPro nun produto
> propietario, ponte en contacto.

---

## 📧 Contacto

**AnabasaSoft**

- 📧 Correo: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com)
- 🌐 GitHub: [github.com/AnabasaSoft](https://github.com/AnabasaSoft)
- 💼 Proxecto: [github.com/AnabasaSoft/MantPro](https://github.com/AnabasaSoft/MantPro)

---

## 🙏 Agradecementos

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/): framework de interface gráfica multiplataforma para a aplicación de escritorio
- [Flutter](https://flutter.dev/): SDK para as aplicacións móbiles
- [ReportLab](https://www.reportlab.com/): xeración de informes en PDF
- [SQLite](https://www.sqlite.org/): base de datos integrada
- [Flask](https://flask.palletsprojects.com/): microframework web para o servidor de sincronización
- A comunidade de código aberto, polo seu apoio e as súas contribucións

---

<div align="center">

<img src="https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/recursos/AnabasaSoft.png" alt="Anabasa Software" width="120"/>

**Desenvolvido con ❤️ por [Anabasa Software](https://anabasasoft.github.io)**

📧 Correo: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com) • 🌐 Portafolio: [anabasasoft.github.io](https://anabasasoft.github.io)

⭐ Se che gusta este proxecto, dálle unha estrela en GitHub

</div>

<div align="center">
  <br/>
  <p><code>>_ sudo buy-me-a-coffee --theme=dark --force</code></p>
  <a href="https://www.buymeacoffee.com/danitxu" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-black.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important; box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;">
  </a>
  <br/>
</div>
