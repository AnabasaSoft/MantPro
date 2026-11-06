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
  <strong>GMAO/CMMS gratuíto e de código aberto para xestionar o mantemento preventivo e correctivo da túa planta, obradoiro ou frota, dende o PC e Android.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Offline--first-✔-success.svg" alt="Offline-first">
  <img src="https://img.shields.io/badge/Autoaloxado-de%20balde%20para%20sempre-orange.svg" alt="Autoaloxado: de balde para sempre">
</p>

---

## 📋 Índice

- [Que problema resolve?](#-que-problema-resolve)
- [Para quen é?](#-para-quen-é)
- [Por que MantPro?](#-por-que-mantpro-e-non-un-gmaocmms-comercial)
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
- [Contribuír](#-contribuír)
- [Folla de ruta](#-folla-de-ruta)
- [Licenza](#-licenza)
- [Contacto](#-contacto)

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

## 🆚 Por que MantPro e non un GMAO/CMMS comercial?

- **Código aberto e de balde**: código aberto baixo AGPL-3.0, sen límite de
  técnicos, máquinas ou rexistros
- **Autoaloxado: de balde para sempre**: instalado no teu propio PC ou servidor, non se paga por usuario nin por mes de uso
- **Os teus datos, na túa infraestrutura**: a base de datos vive no teu propio
  PC; non dependes de que un servizo na nube dun terceiro siga existindo o ano
  que vén
- **Sen conexión de verdade**: o móbil funciona sen conexión a internet nin ao
  PC durante toda a xornada, e sincroniza en canto volve haber rede
- **Feito dende o propio mantemento**: as funcións foron saíndo de necesidades
  reais de obradoiro (fotos de antes/despois, vínculo a máquina, stock de
  recambios, avisos recorrentes...), non dunha lista de requisitos xenérica de
  GMAO/CMMS

| | MantPro | GMAO/CMMS comercial habitual |
|---|---|---|
| **Prezo** | De balde (autoaloxado) | Cota mensual por usuario |
| **Usuarios, máquinas e rexistros** | Sen límite | Segundo o plan contratado |
| **Onde están os teus datos** | No teu PC ou servidor | Na nube do provedor |
| **App móbil sen conexión** | Toda a xornada | A miúdo limitada ou só consulta |
| **Almacén de recambios** | Incluído | Moitas veces como módulo á parte |
| **Código fonte** | Aberto (AGPL-3.0) | Pechado |
| **Se o provedor desaparece** | Segues usándoo | Quedas sen servizo |

*Comparación co modelo habitual dos GMAO/CMMS comerciais na nube; cada produto é distinto.*

## 🎬 Vídeo de demostración

https://github.com/user-attachments/assets/11572710-e0ba-4f8b-b914-0a959006d4fb

## 📸 Capturas de pantalla

### Aplicación de escritorio

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Panel" width="30%"/>
  <img src="Capturas/Maquinas.png" alt="Máquinas e recambios" width="30%"/>
  <img src="Capturas/Almacen.png" alt="Xestión do almacén" width="30%"/>
</p>

### Aplicación móbil

<p align="center">
  <img src="Capturas/Dashboard-movil.jpg" alt="Panel no móbil" width="30%"/>
  <img src="Capturas/Almacen-movil.jpg" alt="Almacén no móbil" width="30%"/>
  <img src="Capturas/Historial-movil.jpg" alt="Historial no móbil" width="30%"/>
</p>

---

## 📦 Descargas

Podes descargar as versións precompiladas dende [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: instalador (`MantPro_Setup_v….exe`) ou executable `.exe` solto
- **Linux**:
  - Binario executable de Linux
  - AppImage portable
  - Paquetes `.deb` (Debian, Ubuntu…) e `.rpm` (Fedora, openSUSE…), asinados con GPG
  - Tamén dispoñible en **AUR** (Arch User Repository)
  - Tamén dispoñible en [**OBS**](https://build.opensuse.org/package/show/home:danitxu79/MantPro) (openSUSE Build Service) para openSUSE Tumbleweed e Slowroll
- **Android**: ficheiros `.apk` para instalación directa
  - `MantPro.apk`: aplicación de traballos de mantemento
  - `MantProStock.apk`: aplicación de stock do almacén

As versións marcadas como *pre-release* (`v3.10.2-dev`, `-rc.1`…) son de
probas: só se ofrecen como actualización a quen xa ten instalada unha versión
de probas. Quen usa unha versión estable só recibe avisos de versións estables.
Os cambios de cada versión están en [CHANGELOG.md](CHANGELOG.md).

---

## ✨ Características

### 💻 Aplicación de escritorio (PC)

- **👥 Xestión de usuarios**: inicio de sesión con usuario e contrasinal, roles de administrador e técnico, alta e baixa de usuarios, e restablecemento de contrasinais
- **✍️ Autoría dos traballos**: cada intervención garda quen a fixo, visible no historial e nos informes
- **🔒 Permisos por rexistro**: un técnico só pode editar ou borrar os seus propios traballos; un administrador pode xestionar calquera, incluída a reasignación do autor dun ou varios rexistros á vez
- **📋 Rexistro de cambios**: quen cambiou que, cando e desde onde (PC ou móbil) en traballos, pendentes, avisos, listas de comprobación, máquinas, almacén, usuarios, seguranza e configuración, con cada campo antes → despois; filtros, buscador e exportación a Excel/CSV (só administradores)
- **🔐 Sesións de dispositivos**: lista os móbiles vinculados a cada usuario, co seu modelo real, e permite revogar unha ou varias sesións concretas sen desactivar o usuario enteiro (só administradores). Ao volver iniciar sesión dende o mesmo dispositivo, a sesión anterior substitúese automaticamente en vez de acumularse
- **🛡️ Seguranza**: sincronización cos móbiles cifrada por HTTPS (o certificado do PC queda fixado polo QR), **bases de datos cifradas** opcionais (SQLCipher, coa chave no chaveiro do sistema) e **copias de seguranza cifradas con contrasinal**, intentos de inicio de sesión limitados contra a forza bruta, fotos recibidas dos móbiles comprobadas e copias consistentes con comprobación de integridade
- **📊 Panel con KPI e gráficos**: tarxetas de avisos pendentes, tarefas por facer, rexistros do mes e MTBF/MTTR medios de toda a planta, ademais de gráficos das máquinas con máis avarías e de avarías por mes, debuxados sen depender de bibliotecas externas, ademais do custo de mantemento do mes e do ano, das máquinas con máis custo e do custo por mes
- **🎨 Temas visuais**: escolle entre modo escuro (por defecto), claro ou un estilo retro inspirado en Windows 98, dende o menú "Aparencia". As iconas dos selectores de ficheiros e cartafoles debúxanse a xogo con cada tema, así que se ven ben aínda que o tema de iconas do sistema sexa escuro ou non haxa ningún (Windows)
- **📅 Calendario interactivo**: visualiza e xestiona as tarefas de mantemento con códigos de cor (festivos, vacacións, días con tarefas)
- **📝 Historial completo**: rexistro histórico de todas as intervencións feitas, con fotos de antes/despois e unha **colección de fotos** adicional por traballo; pódense borrar varios rexistros á vez
- **📄 Informes PDF**: xeración automática de informes profesionais con logotipo personalizable
- **📸 Xestión de imaxes**: almacenamento e visualización das fotos das intervencións
- **📱 Sincronización móbil**: servidor integrado (arranca automaticamente) para sincronizar coa aplicación móbil mediante QR
- **🔍 Sistema de busca**: busca avanzada por datas, etiquetas e contido
- **👤 Filtro por técnico**: filtra o historial e as exportacións (PDF, CSV e Excel) pola persoa que fixo o traballo
- **📦 Copia e restauración**: copia manual completa (BD + fotos) escollendo onde gardala, copia automática incremental ao pechar, cada certo tempo e tras recibir datos dun móbil, con cartafol externo e proba de restauración (ver [Copias de seguranza](#-copias-de-seguranza)), e restauración con barra de progreso, co submenú `Ficheiro > Restaurar` para escoller entre calquera copia manual ou ir directamente ás copias automáticas. As copias pódense **cifrar con contrasinal** (`Ficheiro > 🔒 Contrasinal das copias…`)
- **🏷️ Sistema de etiquetas**: clasificación con etiquetas (Urxente, Eléctrico, Mecánico, Preventivo)
- **🔨 Tarefas pendentes**: xestión de traballos pendentes (crear, completar, editar, eliminar) e **asignación a un técnico concreto**
- **🚦 Prioridade dos pendentes**: cada traballo pendente ten unha prioridade (Baixa, Media, Alta ou Crítica) para decidir cal atacar primeiro, coa súa cor na lista; tamén se lle poden achegar fotos á súa colección
- **↩️ Reverter a pendente**: se un traballo se completou por erro, pódese devolver a Pendentes cun clic dende o historial (con aviso se tiña máquina vinculada, xa que se perdería ese dato), e queda rexistrado na auditoría
- **🔁 Lembretes**: avisos de mantemento que se repiten automaticamente. Se pasa a data non se saltan: quedan en **Pendente** (laranxa) mentres dura a marxe e despois en **Atrasado** (vermello) ata que se fan, e a data seguinte cóntase dende o día real en que se fixo o traballo
- **📟 Preventivo por contador**: avisos por **horas de uso, ciclos ou km** dunha máquina («cambio de aceite cada 500 h, avisar 50 h antes»), sós ou xunto a unha frecuencia por data (**o que antes chegue**: «cada 500 h ou cada ano»). As lecturas apúntanse no PC, na ficha da máquina no móbil (tamén sen conexión) e ao completar o preventivo; desde esa lectura cóntase o seguinte, e calcúlase cando se chegará segundo o uso medio
- **☑️ Listas de comprobación**: modelos reutilizables («Revisión mensual do compresor») con puntos que se marcan ben / mal / non aplica e lecturas coa súa unidade e o seu rango correcto (fóra de rango, «mal» automaticamente); asígnanse a avisos e pendentes e énchense ao completalos, no PC ou no móbil (tamén sen conexión). Gárdanse co traballo, vense no historial e saen nas exportacións a PDF, Excel e CSV
- **📦 Control do stock do almacén**: estrutura de andeis, baldas e seccións configurable, ficha de materiais con foto, entradas/saídas con historial e alertas de stock por baixo do mínimo
- **📄 Exportar o stock**: botón "📄 Exportar" na lapela de stock para sacar o almacén enteiro, unha zona ou un andel a PDF, CSV ou Excel, ordenado por localización; a lapela de stock por baixo do mínimo tamén ten o seu botón para exportar só os materiais en alerta
- **🏭 Provedores e provedor habitual**: lista de provedores (nome, persoa de contacto, teléfono, correo e notas) dende o botón «🏭 Provedores» da lapela de stock, e campo «Provedor habitual» en cada artigo. Historial de prezos por provedor para administradores («💶 Prezos por provedor…» na ficha, e provedor e prezo nas entradas de stock). Stock obxectivo e múltiplo de pedido por artigo, coa cantidade que se suxeriría pedir. Pedido suxerido (que pedir agora, descontando o xa pedido e pendente de chegar) e pedidos gardados coa súa data, que se envían por correo, WhatsApp, teléfono ou impresos; cada entrada de stock desconta o pendente. Só administradores
- **🗑️ Tempo máximo de gardado**: `Ferramentas` permite borrar do historial os traballos máis antigos que un número de anos, meses ou días, coas súas fotos e unha copia de seguranza previa (só administradores)
- **📥 Importar dende Excel/CSV**: `Ficheiro > Importar dende Excel/CSV…` (só administradores) trae máquinas, artigos do almacén, avisos recorrentes, usuarios, pendentes e historial de traballos antigo dende un modelo descargable ou dende o teu propio Excel (unha folla ou todo o libro dunha vez), emparellando soas as columnas, con vista previa fila a fila e copia de seguranza previa. As localizacións (zonas, andeis, baldas) e máquinas superiores que non existan créanse soas, e os usuarios reciben un contrasinal temporal que terán que cambiar ao entrar
- **🏭 Control de maquinaria**: árbore de máquinas e submáquinas con foto achegada, contador de traballos por ano e mes, e vínculo directo dende cada traballo rexistrado ou editado (ver [Maquinaria](#-maquinaria))
- **📊 Exportación**: a PDF, CSV e Excel, con filtro opcional por técnico e indicando a máquina/submáquina de cada traballo, se a ten
- **📖 Axuda integrada**: `Axuda > 📖 Instrucións` abre un manual completo por apartados (primeiros pasos, usuarios, cada lapela, menús, apps do móbil e problemas frecuentes), con índice e buscador, nos 7 idiomas. Con **F1** ábrese directamente no apartado da lapela na que esteas
- **👥 Estatísticas por técnico**: botón no Dashboard cos traballos de cada técnico por ano e mes, avarías, preventivos, horas de parada e pendentes asignados agora mesmo, con gráfico de barras; filtrable por tipo (todos, traballos e avarías ou mantemento preventivo) e exportable a PDF (con logotipo) e Excel
- **🔩 Recambios por máquina**: que artigos do almacén leva cada máquina e cantos, co seu stock e localización, e en que máquinas se usa cada artigo (ver [Maquinaria](#-maquinaria))
- **💶 Recambios usados e o seu custo**: ao rexistrar, completar ou editar un traballo apúntanse os recambios usados (propóñense primeiro os da máquina); saen do stock e quedan gardados co traballo e o prezo dese momento, así que o custo non cambia aínda que despois cambie o prezo. Ao corrixilos axústase o stock. Cada artigo pode ter prezo unitario (moeda configurable). `Máquinas > 💶 Custo de recambios` mostra o custo por máquina, coas súas submáquinas, por ano e exportable a Excel; o historial, o PDF, o Excel e o CSV inclúenos Os custos só os ven os administradores.
- **⏱️ Tempo traballado**: canto durou cada traballo e cantas persoas, **apuntado despois** (sen cronómetro: nunha avaría primeiro arránxase), no PC ou no móbil, tamén ao completar avisos e pendentes, e corrixible no historial. Cun custo da hora interno (só administradores; cada traballo garda a tarifa do momento), `Máquinas > 💶 Custos` mostra horas, man de obra, recambios e total por máquina, e as estatísticas por técnico inclúen as súas horas
- **🏷️ Etiquetas QR por máquina**: PDF de etiquetas para pegar nas máquinas; ao escanealas coa app MantPro ábrese a ficha da máquina
- **🔍 Aviso de repetidos**: ao crear ou renomear unha máquina, ou ao crear ou editar un artigo, avisa se xa hai outro co mesmo código ou un nome igual ou moi parecido (por exemplo «Extractor de finos» / «Extracción de finos»), sen avisar cando só cambia o número («Lora 1» / «Lora 2»)
- **📲 Instalar as apps cun QR**: `Ferramentas > 📱 Instalar MantPro no móbil` e `📦 Instalar MantPro Stock no móbil` mostran un QR que, ao escanealo coa cámara do móbil, descarga a última versión estable da app
- **🔔 Avisos de actualización**: `Axuda > 🔄 Buscar Actualizacións` avisa das versións novas; a instalada dende OBS (openSUSE) indica que se actualiza con `zypper`

### 📱 Aplicación móbil (Android)

- **🔐 Acceso con usuario**: cada técnico inicia sesión unha vez e a sesión queda gardada no dispositivo (o token gárdase no Keystore de Android, non en claro)
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
- **☑️ Listas de comprobación**: os avisos e pendentes con lista piden enchela ao completalos (ben / mal / non aplica e lecturas), tamén sen conexión; o historial mostra a lista enchida
- **🔌 Modo sen conexión**: traballa sen conexión e sincroniza cando poidas
- **⏰ Lembretes diarios**: notificación automática ás 8:00 (hora local) se hai traballos pendentes sen completar
- **🧰 Material usado**: engade ao traballo o material do almacén que empregaches, buscándoo polo nome ou o código; descóntase só do stock ao gardar (ver [Material usado nun traballo](#-stock-do-almacén)). Ao completar un aviso tamén se poden apuntar recambios, saen primeiro os da máquina, e ao corrixir un traballo do historial axústase o stock
- **🏭 Vincular máquina**: escolle nun despregable a máquina ou submáquina na que se fixo o traballo, tanto ao crear un rexistro novo como ao editar un xa sincronizado do historial
- **🔄 Conectada en segundo plano**: mentres a app está aberta, aínda que sexa en segundo plano, segue sincronizando co PC e mostra unha notificación («Conectado ao PC» / «Sen conexión co PC») cun botón «Pechar». Ao pechala de todo deixa de gastar batería
- **📶 Primeira sincronización con progreso**: barra de progreso ao descargar os datos e as fotos, con descarga en paralelo para que sexa máis rápida
- **🏷️ Escanear a máquina**: o botón de escanear le a etiqueta QR dunha máquina e abre a súa ficha, sen conexión: onde está, os seus últimos traballos, os seus **recambios** co stock do almacén, e un botón para rexistrar un traballo xa vinculado a ela
- **📟 Contadores da máquina**: na ficha da máquina apúntanse as lecturas dos seus contadores (horas, ciclos, km) sen conexión e vense os seus preventivos por contador co que falta; ao completar un, a lectura apúntase no mesmo paso
- **⬆️ Actualizar dende a app**: cando hai unha versión nova, o aviso ten os botóns «Despois» e «Actualizar»; «Actualizar» descarga o APK cunha barra de progreso e abre o instalador de Android, sen pasar por GitHub

### 📦 Aplicación móbil de stock (Android)

Aplicación independente (`mantpro_stock_app`), pensada para consultar e mover
o stock do almacén dende o móbil sen necesidade da aplicación de traballos.

- **🔐 Acceso con usuario**: emprega o mesmo sistema de usuarios e sesión que a aplicación de traballos (o token gárdase no Keystore de Android, non en claro)
- **🗂️ Navegación polo almacén**: árbore de andeis > baldas > seccións, igual que no PC
- **🔎 Busca de materiais**: por nome, código, descrición ou localización
- **➕➖ Entradas e saídas**: rexistra movementos de stock dende o móbil, con motivo opcional
- **🔀 Traslados**: mover un material de sección queda reflectido no seu historial de movementos
- **🎨 Aviso visual de stock**: cantidade en vermello por baixo do mínimo, en verde por riba e coa cor por defecto se coincide exactamente
- **⚠️ Stock por baixo do mínimo**: lapela dedicada aos materiais en alerta
- **🔄 Actualización automática**: a pantalla refréscase soa ao detectar cambios, tanto se o cambio se fixo no propio móbil como no PC
- **🔌 Modo sen conexión**: sen conexión co PC a aplicación non queda esperando: consulta os datos gardados e deixa rexistrar altas, edicións, entradas e saídas ao momento, que se envían soas ao PC en canto volve estar accesible
- **🔔 Lembrete diario de comprobación de stock**: notificación automática ás 8:00 (hora local) que convida a revisar a cantidade real de 5 materiais do almacén, escollidos ao chou e distintos cada día; ao premela ábrese unha pantalla para corrixir a cantidade de cada un sen ter que buscalos. Se non hai ningún material dado de alta, non se amosa ningunha notificación
- **🔄 Conectada en segundo plano**: coma MantPro, segue sincronizando en segundo plano, coa súa notificación; a icona de usuario ponse **verde** se hai conexión co PC e **vermella** se non
- **🔩 Úsase en**: cada artigo mostra en que máquinas se usa como recambio e cantos leva cada unha, tamén sen conexión
- **🔍 Aviso de repetidos**: ao crear ou editar un artigo avisa se xa hai outro co mesmo código ou un nome moi parecido, comparando cos artigos gardados no móbil (funciona sen conexión)
- **⬆️ Actualizar dende a app**: igual que MantPro, descarga e instala a nova versión dende o propio aviso

---

## 🔧 Requisitos

### Aplicación de escritorio

- **Python**: 3.10 ou superior
- **Sistema operativo**: Windows ou Linux
- **Dependencias de Python**:
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - xlsxwriter
  - openpyxl
  - Pillow
  - cryptography
  - keyring e sqlcipher3-wheels (opcionais: cifrado das bases de datos)
  - sqlite3 (incluído en Python)

### Aplicación móbil

Aplícase tanto a `mantenimiento_app` (traballos) como a `mantpro_stock_app` (stock):

- **Flutter**: 3.0 ou superior
- **Dart SDK**: 2.17 ou superior
- **Android**: API Level 24+ (Android 7.0+)

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

**Pegada da clave** (compróbaa tamén en [anabasasoft.github.io](https://anabasasoft.github.io/about.html#firma)): `11C7 C6C8 127D FE48 33DE  30EF 9D7A AEC8 1842 C199` (RSA 4096, caduca o 2028-10-06). Se a que che mostra `gpg` non coincide exactamente, non instales o paquete.

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
   # RPM
   rpm -qa 'gpg-pubkey*' --qf '%{name}-%{version}-%{release} --> %{summary}\n' | grep -i anabasasoft

   # DEB (ou calquera distribución con gpg): mostra tamén a pegada
   gpg --fingerprint AnabasaSoft
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

**Dende o PC, cun QR**: en `Ferramentas > 📱 Instalar MantPro no móbil` (ou
`📦 Instalar MantPro Stock no móbil`) aparece un QR. Escanéao coa cámara do
móbil, abre a ligazón e descárgase a última versión estable da app. Unha vez
instaladas, as apps avisan das versións novas e actualízanse dende o propio
aviso co botón «Actualizar».

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
seus dispositivos de golpe). **Móbil adxudicado a un técnico**: con `📲 Adxudicar móbil a un técnico…` o móbil só deixa iniciar sesión ao seu técnico (os administradores, sempre) e a app énchelle o usuario; vale para MantPro e MantPro Stock á vez, así que o mesmo técnico pode usar as dúas apps no mesmo móbil.

Se un usuario volve iniciar sesión dende un dispositivo co que xa tiña unha
sesión aberta (mesmo fabricante e modelo), a sesión anterior dese dispositivo
bórrase automaticamente ao crear a nova, en vez de quedar acumulada como unha
sesión solta máis na listaxe.

As sesións caducan por inactividade: cada vez que o móbil conecta co PC a súa
sesión renóvase, así que quen usa a app non ten que volver iniciar sesión, e
péchanse soas tras **60 días sen conectar** (un móbil perdido ou de alguén que
xa non está). O administrador cambia ese prazo (de 30 a 365 días) na mesma
xanela. O que o móbil tivese sen enviar non se perde: envíase ao volver iniciar
sesión.

A columna **Conexión** indica se cada móbil está **en liña** agora mesmo e cando
foi o seu último contacto. As apps avisan ao PC cada poucos segundos mentres
están abertas (tamén en segundo plano), e ao pechalas de todo avisan de que se
desconectan, así que o estado actualízase ao momento.

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

Os administradores ven en `Ferramentas` > `📋 Rexistro de cambios` **quen
cambiou que, cando e desde onde** (o PC ou que móbil): traballos, pendentes,
avisos, listas de comprobación, máquinas e recambios, artigos e estrutura do
almacén, usuarios e especialidades, seguranza (sesións revogadas, bloqueos por
intentos fallidos, cifrado, conexión sen cifrar), copias restauradas,
importacións e configuración. Cada cambio mostra os campos afectados
**antes → despois**. Pódese filtrar por categoría, acción, usuario e período,
buscar por texto e exportar a Excel ou CSV.

### Historial de revisións do almacén

Cada día MantPro Stock propón revisar 5 artigos do almacén ao chou. A aplicación anota **quen o fixo, cando e se revisou os 5**, coa cantidade contada fronte á que dicía o sistema (tamén se se fai sen conexión: envíase ao reconectar o móbil). Os administradores velo en `Ferramentas` > `📦 Historial de revisións do almacén`: ✅ completa, ⚠️ incompleta ou ❌ sen revisar, con filtros por usuario, período e estado, e exportación a Excel ou CSV. Se nalgún dos últimos 7 días laborables non se fixo ningunha revisión, MantPro avisa aos administradores ao abrir (e márcao en vermello no historial), e o historial indica **que móbiles fixeron revisións** e cando foi a última de cada un.

### Sesión no móbil

O técnico inicia sesión unha vez e o token queda gardado no dispositivo. A
sesión péchase soa se o administrador desactiva o usuario ou lle restablece o
contrasinal; nese caso a aplicación volve á pantalla de acceso **sen perder os
rexistros que aínda estean pendentes de subir**.

O token de sesión gárdase no **Keystore de Android** (almacenamento seguro), non en claro. Tras **5 intentos fallidos** seguidos de inicio de sesión, ese usuario bloquéase 15 minutos (e un móbil, tras 20 intentos fallidos); a app mostra canto hai que agardar. Na xanela do PC, 5 fallos bloquean o inicio de sesión un minuto.

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
- **🗺️ Zona herdada**: ao crear unha submáquina, toma por defecto a zona da
  súa máquina superior
- **🔩 Recambios de cada máquina**: debaixo da árbore vense os artigos do
  almacén que leva a máquina seleccionada, cantos leva, o seu stock (en
  vermello se está por baixo do mínimo), a súa localización e unha nota (por
  exemplo «lado motor»). Engádense con «➕ Engadir recambio», expórtanse a PDF
  ou Excel, e con dobre clic sáltase ao artigo no almacén
- **🏷️ Etiquetas QR**: o botón «🏷️ Etiquetas QR» xera un PDF de follas A4 con
  24 etiquetas de 70 × 37 mm (da máquina seleccionada, coas súas submáquinas
  ou de todas). Ao escanealas coa app MantPro ábrese a ficha da máquina
- **📟 Contadores**: o botón «📟 Contadores» xestiona as horas de uso, ciclos
  ou km da máquina seleccionada (créaos un administrador), coa última lectura,
  o uso medio por día e o historial de lecturas. Os preventivos por contador
  toman de aquí as súas lecturas
- **🔍 Nomes parecidos**: ao crear ou renomear unha máquina, avisa se no mesmo
  nivel xa hai outra cun nome igual ou moi parecido

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
- Cada material indica **en que máquinas se usa** como recambio, e ao crealo
  ou editalo pódenselle asociar máquinas directamente, coa cantidade que leva
  cada unha
- Ao crear ou editar un material avísase se xa hai outro co **mesmo código ou
  un nome moi parecido**, para non dalo de alta dúas veces

### Entradas, saídas e traslados

- **Calquera usuario** pode rexistrar entradas e saídas de stock; só a
  configuración da estrutura do almacén está restrinxida aos administradores
- Cada movemento queda rexistrado con data, cantidade, usuario e un motivo
  opcional, visible no historial xunto a cada material
- As saídas rexistradas a man (PC ou `mantpro_stock_app`) non poden deixar o
  stock en negativo
- Cambiar a localización dun material tamén queda rexistrado no seu historial,
  como un movemento de tipo **traslado** (de que sección a que sección)
- O botón **«📜 Historial»** mostra todos os movementos do almacén seguidos
  (entradas, saídas e traslados), co nome de cada artigo e filtros por texto e
  tipo

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
6. Mentres as apps do móbil están abertas, aínda que sexa en segundo plano,
   seguen sincronizando e o PC veas **en liña** en `Ferramentas > 🔐 Sesións de
   dispositivos`
7. A primeira sincronización mostra unha **barra de progreso** e descarga os
   datos en paralelo e as fotos de 4 en 4

> 🔒 A sincronización vai **cifrada (HTTPS)**. O PC crea o seu propio
> certificado e a súa pegada viaxa no QR: o móbil só se conecta a *ese* PC,
> así que ninguén na WiFi pode ler o tráfico nin facerse pasar por el. Os
> móbiles xa vinculados pasan sós a HTTPS ao actualizar a app.

### Configuración da rede

Para que a sincronización funcione:

- ✅ O PC e o móbil deben estar na **mesma rede WiFi**
- ✅ O **cortalumes** debe permitir conexións no porto 5000 (ou o configurado)
- ✅ Tamén debe permitir o **porto seguinte** (5001 por defecto), que usa a conexión cifrada (HTTPS)
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

**MantPro pide unha chave de recuperación ao arrancar:**
- As bases de datos están cifradas e o chaveiro do sistema xa non ten a súa chave (sistema reinstalado, outra conta de usuario…)
- Escribe a chave de recuperación que se mostrou ao activar o cifrado; MantPro volve gardala no chaveiro
- Se non a tes, as bases de datos non se poden abrir: saca `mantenimiento.db` e `almacen.db` do cartafol de datos, abre MantPro e restaura unha copia de seguranza

**«Demasiados intentos fallidos» ao iniciar sesión:**
- Tras varios contrasinais erróneos seguidos, o inicio de sesión bloquéase un tempo (15 minutos no móbil, un minuto no PC); agarda o que indica o aviso ou pídelle a un administrador que che restableza o contrasinal

### 🔒 Nota sobre seguranza

A sincronización vai cifrada con HTTPS e o certificado do PC queda fixado
pola pegada do QR. Durante a transición, o PC segue atendendo tamén por HTTP
no porto configurado para as apps de versións anteriores; HTTPS usa o **porto
seguinte** (por exemplo, 5000 e 5001), así que se hai un cortalumes hai que
abrir os dous. Se algunha vez expós o servidor fóra da rede local, faino a
través dunha VPN.

Cando todos os móbiles teñan a app actualizada, desactiva a conexión sen cifrar
en `Ferramentas > 🔐 Sesións de dispositivos`: a columna «Cifrado» mostra que
móbiles se conectan aínda sen ela. A partir de entón o PC só atende por HTTPS.

As bases de datos tamén se poden gardar **cifradas** (`Ferramentas > Cifrado
das bases de datos…`, SQLCipher): a chave vai no chaveiro do sistema e
móstrase unha chave de recuperación para apuntala. Vén desactivado.

---

## 💾 Copias de seguranza

MantPro fai **copias automáticas** (as bases de datos, e as fotos en ZIP
incrementais por mes) ao pechar, cada 2 horas mentres está aberto se hai
cambios, pouco despois de recibir datos dun móbil e ao abrilo se quedaron
cambios sen copiar. En `Ficheiro > 🛡️ Copias automáticas…` escóllese cada
canto, cantas se gardan e un **cartafol externo** (NAS, disco USB,
Nextcloud/Dropbox…) ao que se manda tamén cada copia. Despois de cada copia
**próbase que se pode restaurar**, e a barra de estado avisa se algo falla.
Tamén permite facer unha **copia completa a man**
dende `Ficheiro > Backup` e restaurala dende `Ficheiro > Restaurar`.
`Ferramentas` inclúe ademais limpar as fotos que xa non usa ningún rexistro e
borrar os traballos máis antigos que un tempo dado, sempre con copia previa.

🔒 Con `Ficheiro > Contrasinal das copias…` as copias gárdanse **cifradas**
(AES-256 cunha chave obtida do contrasinal): unha copia que sae do equipo
(USB, NAS, nube) non se pode abrir sen el. Se esqueces o contrasinal, as
copias cifradas non se poden recuperar.

Detalle completo: [docs/copias-de-seguridad.md](docs/copias-de-seguridad.md)
(en castelán) · [docs/backups.md](docs/backups.md) (en inglés).

---

## 🤝 Contribuír

As contribucións son benvidas! Antes de abrir un *pull request*, le
[CONTRIBUTING.md](CONTRIBUTING.md): explica como preparar os cambios (idiomas,
probas, cabeceiras dos ficheiros) e o **acordo de contribución
([CLA](CLA.md))** que hai que aceptar.

A estrutura do código e da base de datos está en
[docs/desarrollo.md](docs/desarrollo.md) (en castelán) e
[docs/development.md](docs/development.md) (en inglés). Para fallos de
seguranza, mira [SECURITY.md](SECURITY.md).

---

## 🧭 Folla de ruta

O que vén, sen datas e sen unha orde pechada:

- **Compras**: recibir os pedidos con entrada automática no stock e prezo real, e avisar dos pedidos sen enviar
- **Sinatura** ao pechar un traballo (tamén no móbil)
- **Documentación técnica por máquina** (manuais, planos e esquemas en PDF)
- **Criticidade das máquinas (ABC)**, para decidir onde investir en mantemento
- **Solicitudes de traballo** desde produción ou outros departamentos que crean un pendente
- **Notificacións push** de traballos urxentes e **vídeos** nos traballos
- **Varios PC á vez**, servidor sen xanela (Raspberry Pi, NAS, Docker) e acceso web
- **Varios centros ou plantas** con datos e indicadores por centro
- Máis idiomas (italiano, alemán…) e app para iPhone

Feito hai pouco: pedido suxerido e pedidos gardados, provedores e provedor habitual de cada artigo, custo de mantemento no panel, preventivos por contador (horas de uso, ciclos, km), tempo traballado e custo de man de obra en cada traballo, recambios usados en cada traballo co seu custo por máquina, listas de comprobación en preventivos e traballos, sincronización, bases de datos e copias cifradas, e un rexistro de cambios máis completo.

Os cambios de cada versión están en [CHANGELOG.md](CHANGELOG.md). Botas algo
en falta? Abre unha [*issue*](https://github.com/AnabasaSoft/MantPro/issues).

---

## 📄 Licenza

Este proxecto está baixo a **GNU Affero General Public License v3.0 (AGPL-3.0)**.
Consulta o ficheiro `LICENSE` para o texto completo.

Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft)

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
Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft)

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
