<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-6e7781?style=for-the-badge" alt="English"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Espa%C3%B1ol-6e7781?style=for-the-badge" alt="Español"></a>
  <a href="README.eu.md"><img src="https://img.shields.io/badge/Euskara-6e7781?style=for-the-badge" alt="Euskara"></a>
  <a href="README.ca.md"><img src="https://img.shields.io/badge/Catal%C3%A0-0969da?style=for-the-badge" alt="Català"></a>
  <a href="README.gl.md"><img src="https://img.shields.io/badge/Galego-6e7781?style=for-the-badge" alt="Galego"></a>
  <a href="README.pt.md"><img src="https://img.shields.io/badge/Portugu%C3%AAs-6e7781?style=for-the-badge" alt="Português"></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/Fran%C3%A7ais-6e7781?style=for-the-badge" alt="Français"></a>
</p>

# MantPro

<p align="center">
  <img src="recursos/logo.png" alt="Logotip de MantPro" width="200"/>
</p>

<p align="center">
  <strong>GMAO/CMMS gratuït i de codi obert per gestionar el manteniment preventiu i correctiu de la teva planta, taller o flota, des del PC i Android.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Offline--first-✔-success.svg" alt="Offline-first">
  <img src="https://img.shields.io/badge/Autoallotjat-gratu%C3%AFt%20per%20sempre-orange.svg" alt="Autoallotjat: gratuït per sempre">
</p>

---

## 📋 Índex

- [Quin problema resol?](#-quin-problema-resol)
- [Per a qui és?](#-per-a-qui-és)
- [Per què MantPro?](#-per-què-mantpro-i-no-un-gmaocmms-comercial)
- [Vídeo de demostració](#-vídeo-de-demostració)
- [Captures de pantalla](#-captures-de-pantalla)
- [Descàrregues](#-descàrregues)
- [Característiques](#-característiques)
- [Requisits](#-requisits)
- [Instal·lació](#-installació)
- [Ús](#-ús)
- [Usuaris i accés](#-usuaris-i-accés)
- [Maquinària](#-maquinària)
- [Estoc del magatzem](#-estoc-del-magatzem)
- [Sincronització PC-mòbil](#-sincronització-pc-mòbil)
- [Còpies de seguretat](#-còpies-de-seguretat)
- [Contribuir](#-contribuir)
- [Full de ruta](#-full-de-ruta)
- [Llicència](#-llicència)
- [Contacte](#-contacte)

---

## 🧩 Quin problema resol?

En molts tallers i plantes petites o mitjanes, el manteniment es porta entre
papers, un Excel compartit i missatges de WhatsApp. Funciona, fins que algú
necessita saber **què s'ha fet a una màquina concreta**, qui ho va fer, quan i
amb quin material, i aquesta informació està repartida entre tres llocs
diferents (o en cap).

**MantPro ho centralitza**: cada tècnic registra la seva intervenció des del
mòbil, en el moment, amb fotos d'abans i després si cal, i tot queda ordenat al
PC per màquina, per data i per persona, a punt per consultar-ho o treure'n un
informe en PDF.

## 🎯 Per a qui és?

Pensat per a qui porta el manteniment del dia a dia, no per a departaments
d'informàtica: tècnics de manteniment, responsables de planta, tallers, pimes
industrials i encarregats de magatzem que necessiten un control real de
màquines, intervencions i estoc sense dependre de fulls de càlcul solts.

## 🆚 Per què MantPro i no un GMAO/CMMS comercial?

- **Codi obert i gratuït**: codi obert sota AGPL-3.0, sense límit de tècnics,
  màquines o registres
- **Autoallotjat: gratuït per sempre**: instal·lat al teu propi PC o servidor, no es paga per usuari ni per mes d'ús
- **Les teves dades, a la teva infraestructura**: la base de dades viu al teu
  propi PC; no depens que un servei al núvol d'un tercer continuï existint
  l'any vinent
- **Fora de línia de veritat**: el mòbil funciona sense connexió a internet ni
  al PC durant tota la jornada, i se sincronitza tan bon punt torna a haver-hi
  xarxa
- **Fet des del mateix manteniment**: les funcions han anat sortint de
  necessitats reals de taller (fotos d'abans/després, vincle a màquina, estoc
  de recanvis, avisos recurrents...), no d'una llista de requisits genèrica de
  GMAO/CMMS

| | MantPro | GMAO/CMMS comercial habitual |
|---|---|---|
| **Preu** | Gratuït (autoallotjat) | Quota mensual per usuari |
| **Usuaris, màquines i registres** | Sense límit | Segons el pla contractat |
| **On són les teves dades** | Al teu PC o servidor | Al núvol del proveïdor |
| **App mòbil sense connexió** | Tota la jornada | Sovint limitada o només consulta |
| **Magatzem de recanvis** | Inclòs | Moltes vegades com a mòdul a part |
| **Codi font** | Obert (AGPL-3.0) | Tancat |
| **Si el proveïdor desapareix** | El continues fent servir | Et quedes sense servei |

*Comparació amb el model habitual dels GMAO/CMMS comercials al núvol; cada producte és diferent.*

## 🎬 Vídeo de demostració

https://github.com/user-attachments/assets/11572710-e0ba-4f8b-b914-0a959006d4fb

## 📸 Captures de pantalla

### Aplicació d'escriptori

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Tauler" width="30%"/>
  <img src="Capturas/Maquinas.png" alt="Màquines i recanvis" width="30%"/>
  <img src="Capturas/Almacen.png" alt="Gestió del magatzem" width="30%"/>
</p>

### Aplicació mòbil

<p align="center">
  <img src="Capturas/Dashboard-movil.jpg" alt="Tauler al mòbil" width="30%"/>
  <img src="Capturas/Almacen-movil.jpg" alt="Magatzem al mòbil" width="30%"/>
  <img src="Capturas/Historial-movil.jpg" alt="Historial al mòbil" width="30%"/>
</p>

---

## 📦 Descàrregues

Pots descarregar les versions precompilades des de [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: instal·lador (`MantPro_Setup_v….exe`) o executable `.exe` solt
- **Linux**:
  - Binari executable de Linux
  - AppImage portable
  - Paquets `.deb` (Debian, Ubuntu…) i `.rpm` (Fedora, openSUSE…), signats amb GPG
  - També disponible a **AUR** (Arch User Repository)
  - També disponible a [**OBS**](https://build.opensuse.org/package/show/home:danitxu79/MantPro) (openSUSE Build Service) per a openSUSE Tumbleweed i Slowroll
- **Android**: fitxers `.apk` per a instal·lació directa
  - `MantPro.apk`: aplicació de treballs de manteniment
  - `MantProStock.apk`: aplicació d'estoc del magatzem

Les versions marcades com a *pre-release* (`v3.10.2-dev`, `-rc.1`…) són de
proves: només s'ofereixen com a actualització a qui ja té instal·lada una
versió de proves. Qui fa servir una versió estable només rep avisos de versions
estables. Els canvis de cada versió són a [CHANGELOG.md](CHANGELOG.md).

---

## ✨ Característiques

### 💻 Aplicació d'escriptori (PC)

- **👥 Gestió d'usuaris**: inici de sessió amb usuari i contrasenya, rols d'administrador i tècnic, alta i baixa d'usuaris, i restabliment de contrasenyes
- **✍️ Autoria dels treballs**: cada intervenció desa qui la va fer, visible a l'historial i als informes
- **🔒 Permisos per registre**: un tècnic només pot editar o esborrar els seus propis treballs; un administrador pot gestionar-ne qualsevol, inclosa la reassignació de l'autor d'un o diversos registres alhora
- **📋 Registre de canvis**: qui va canviar què, quan i des d'on (PC o mòbil) en treballs, pendents, avisos, llistes de comprovació, màquines, magatzem, usuaris, seguretat i configuració, amb cada camp abans → després; filtres, cercador i exportació a Excel/CSV (només administradors)
- **🔐 Sessions de dispositius**: llista els mòbils vinculats a cada usuari, amb el seu model real, i permet revocar una o diverses sessions concretes sense desactivar l'usuari sencer (només administradors). En tornar a iniciar sessió des del mateix dispositiu, la sessió anterior se substitueix automàticament en lloc d'acumular-se
- **🛡️ Seguretat**: sincronització amb els mòbils xifrada per HTTPS (el certificat del PC queda fixat pel QR), **bases de dades xifrades** opcionals (SQLCipher, amb la clau al clauer del sistema) i **còpies de seguretat xifrades amb contrasenya**, intents d'inici de sessió limitats contra la força bruta, fotos rebudes dels mòbils comprovades i còpies consistents amb comprovació d'integritat
- **📊 Tauler amb KPI i gràfics**: targetes d'avisos pendents, tasques per fer, registres del mes i MTBF/MTTR mitjans de tota la planta, a més de gràfics de les màquines amb més avaries i d'avaries per mes, dibuixats sense dependre de biblioteques externes
- **🎨 Temes visuals**: tria entre mode fosc (per defecte), clar o un estil retro inspirat en Windows 98, des del menú "Aparença"
- **📅 Calendari interactiu**: visualitza i gestiona les tasques de manteniment amb codis de color (festius, vacances, dies amb tasques)
- **📝 Historial complet**: registre històric de totes les intervencions fetes, amb fotos d'abans/després i una **col·lecció de fotos** addicional per treball; es poden esborrar diversos registres alhora
- **📄 Informes PDF**: generació automàtica d'informes professionals amb logotip personalitzable
- **📸 Gestió d'imatges**: emmagatzematge i visualització de fotos de les intervencions
- **📱 Sincronització mòbil**: servidor integrat (s'engega automàticament) per sincronitzar amb l'aplicació mòbil mitjançant QR
- **🔍 Sistema de cerca**: cerca avançada per dates, etiquetes i contingut
- **👤 Filtre per tècnic**: filtra l'historial i les exportacions (PDF, CSV i Excel) per la persona que va fer el treball
- **📦 Còpia i restauració**: còpia manual completa (BD + fotos) triant on desar-la, còpia automàtica incremental en tancar l'aplicació (vegeu [Còpies de seguretat](#-còpies-de-seguretat)), i restauració amb barra de progrés, amb el submenú `Arxiu > Restaurar` per triar entre qualsevol còpia manual o anar directament a les còpies automàtiques. Les còpies es poden **xifrar amb contrasenya** (`Arxiu > 🔒 Contrasenya de les còpies…`)
- **🏷️ Sistema d'etiquetes**: classificació amb etiquetes (Urgent, Elèctric, Mecànic, Preventiu)
- **🔨 Tasques pendents**: gestió de treballs pendents (crear, completar, editar, eliminar) i **assignació a un tècnic concret**
- **🚦 Prioritat dels pendents**: cada treball pendent té una prioritat (Baixa, Mitjana, Alta o Crítica) per decidir quin atacar primer, amb el seu color a la llista; també s'hi poden adjuntar fotos a la seva col·lecció
- **↩️ Revertir a pendent**: si un treball es va completar per error, es pot tornar a Pendents amb un clic des de l'historial (amb avís si tenia màquina vinculada, ja que es perdria aquesta dada), i queda registrat a l'auditoria
- **🔁 Recordatoris**: avisos de manteniment que es repeteixen automàticament. Si es passa la data no se salten: queden en **Pendent** (taronja) mentre dura el marge i després en **Endarrerit** (vermell) fins que es fan, i la data següent es compta des del dia real en què es va fer el treball
- **☑️ Llistes de comprovació**: plantilles reutilitzables («Revisió mensual del compressor») amb punts que es marquen bé / malament / no s'aplica i lectures amb la seva unitat i el seu rang correcte (fora de rang, «malament» automàticament); s'assignen a avisos i pendents i s'omplen en completar-los, al PC o al mòbil (també sense connexió). Es desen amb el treball, es veuen a l'historial i surten a les exportacions a PDF, Excel i CSV
- **📦 Control de l'estoc del magatzem**: estructura de prestatgeries, prestatges i seccions configurable, fitxa de materials amb foto, entrades/sortides amb historial i alertes d'estoc per sota del mínim
- **📄 Exportar l'estoc**: botó "📄 Exportar" a la pestanya d'estoc per treure el magatzem sencer, una zona o una prestatgeria a PDF, CSV o Excel, ordenat per ubicació; la pestanya d'estoc per sota del mínim també té el seu botó per exportar només els materials en alerta
- **🗑️ Temps màxim de conservació**: `Eines` permet esborrar de l'historial els treballs més antics que un nombre d'anys, mesos o dies, amb les seves fotos i una còpia de seguretat prèvia (només administradors)
- **📥 Importar des d'Excel/CSV**: `Arxiu > Importar des d'Excel/CSV…` (només administradors) porta màquines, articles del magatzem, avisos recurrents i usuaris des d'una plantilla descarregable o des del teu propi Excel (un full o tot el llibre d'una vegada), aparellant soles les columnes, amb previsualització fila a fila i còpia de seguretat prèvia. Les ubicacions (zones, prestatgeries, prestatges) i màquines superiors que no existeixin es creen soles, i els usuaris reben una contrasenya temporal que hauran de canviar en entrar
- **🏭 Control de maquinària**: arbre de màquines i submàquines amb foto adjunta, comptador de treballs per any i mes, i vincle directe des de cada treball registrat o editat (vegeu [Maquinària](#-maquinària))
- **📊 Exportació**: a PDF, CSV i Excel, amb filtre opcional per tècnic i indicant la màquina/submàquina de cada treball, si en té
- **📖 Ajuda integrada**: `Ajuda > 📖 Instruccions` obre un manual complet per apartats (primers passos, usuaris, cada pestanya, menús, apps del mòbil i problemes freqüents), amb índex i cercador, en els 7 idiomes. Amb **F1** s'obre directament a l'apartat de la pestanya on ets
- **👥 Estadístiques per tècnic**: botó al Dashboard amb els treballs de cada tècnic per any i mes, avaries, preventius, hores d'aturada i pendents assignats ara mateix, amb gràfic de barres; filtrable per tipus (tots, treballs i avaries o manteniment preventiu) i exportable a PDF (amb logotip) i Excel
- **🔩 Recanvis per màquina**: quins articles del magatzem porta cada màquina i quants, amb el seu estoc i ubicació, i a quines màquines s'utilitza cada article (vegeu [Maquinària](#-maquinària))
- **💶 Recanvis utilitzats i el seu cost**: en registrar, completar o editar un treball s'hi apunten els recanvis utilitzats (es proposen primer els de la màquina); surten de l'estoc i queden desats amb el treball i el preu d'aquell moment, així que el cost no canvia encara que després canviï el preu. En corregir-los s'ajusta l'estoc. Cada article pot tenir preu unitari (moneda configurable). `Màquines > 💶 Cost de recanvis` mostra el cost per màquina, amb les submàquines, per any i exportable a Excel; l'historial, el PDF, l'Excel i el CSV els inclouen
- **🏷️ Etiquetes QR per màquina**: PDF d'etiquetes per enganxar a les màquines; en escanejar-les amb l'app MantPro s'obre la fitxa de la màquina
- **🔍 Avís de repetits**: en crear o reanomenar una màquina, o en crear o editar un article, avisa si ja n'hi ha un altre amb el mateix codi o un nom igual o molt semblant (per exemple «Extractor de fins» / «Extracció de fins»), sense avisar quan només canvia el número («Lora 1» / «Lora 2»)
- **📲 Instal·lar les apps amb un QR**: `Eines > 📱 Instal·lar MantPro al mòbil` i `📦 Instal·lar MantPro Stock al mòbil` mostren un QR que, en escanejar-lo amb la càmera del mòbil, baixa l'última versió estable de l'app
- **🔔 Avisos d'actualització**: `Ajuda > 🔄 Cercar Actualitzacions` avisa de les versions noves; la instal·lada des d'OBS (openSUSE) indica que s'actualitza amb `zypper`

### 📱 Aplicació mòbil (Android)

- **🔐 Accés amb usuari**: cada tècnic inicia sessió una vegada i la sessió queda desada al dispositiu (el token es desa al Keystore d'Android, no en clar)
- **📝 Registre ràpid**: captura d'intervencions sobre el terreny, signades automàticament amb el seu usuari
- **📷 Càmera integrada**: presa de fotos i edició amb anotacions
- **🖼️ Col·lecció de fotos**: a més de les fotos d'abans i després, afegeix a un treball o pendent totes les fotos que vulguis (càmera o galeria); en tocar qualsevol foto es veu a pantalla completa, passant de l'una a l'altra i ampliant amb dos dits
- **✏️ Editor d'imatges**: dibuixa sobre les fotos per marcar zones d'interès
- **🔄 Sincronització automàtica**: enviament automàtic de dades al PC mitjançant codi QR
- **💾 Emmagatzematge local**: desa els registres fora de línia fins que se sincronitzin
- **📋 Treballs pendents**: visualitza i gestiona les tasques assignades des del PC, amb el filtre **"Només els meus"**
- **🔄 Posada al dia en obrir**: en arrencar, l'aplicació sincronitza en segon pla les dades de totes les pestanyes
- **🔁 Tornar a sincronitzar manualment**: les pestanyes Pendents, Historial i Recordatoris tenen el seu propi botó per reenviar de seguida el que tingui el mòbil i encara no tingui el PC
- **↩️ Revertir a pendent**: mantenint premut un registre de l'Historial es pot tornar a la pestanya Pendents si es va completar per error
- **🏷️ Etiquetes ràpides**: sistema d'etiquetatge ràpid amb caselles
- **☑️ Llistes de comprovació**: els avisos i pendents amb llista demanen omplir-la en completar-los (bé / malament / no s'aplica i lectures), també sense connexió; l'historial mostra la llista omplerta
- **🔌 Mode fora de línia**: treballa sense connexió i sincronitza quan puguis
- **⏰ Recordatoris diaris**: notificació automàtica a les 8:00 (hora local) si hi ha treballs pendents sense completar
- **🧰 Material utilitzat**: afegeix al treball el material del magatzem que has fet servir, cercant-lo pel nom o el codi; es descompta sol de l'estoc en desar (vegeu [Material utilitzat en un treball](#-estoc-del-magatzem)). En completar un avís també s'hi poden apuntar recanvis, surten primer els de la màquina, i en corregir un treball de l'historial s'ajusta l'estoc
- **🏭 Vincular màquina**: tria en un desplegable la màquina o submàquina en què s'ha fet el treball, tant en crear un registre nou com en editar-ne un de ja sincronitzat de l'historial
- **🔄 Connectada en segon pla**: mentre l'app és oberta, encara que sigui en segon pla, continua sincronitzant amb el PC i mostra una notificació («Connectat al PC» / «Sense connexió amb el PC») amb un botó «Tancar». En tancar-la del tot deixa de gastar bateria
- **📶 Primera sincronització amb progrés**: barra de progrés en baixar les dades i les fotos, amb baixada en paral·lel perquè sigui més ràpida
- **🏷️ Escanejar la màquina**: el botó d'escanejar llegeix l'etiqueta QR d'una màquina i n'obre la fitxa, sense connexió: on és, els seus últims treballs, els seus **recanvis** amb l'estoc del magatzem, i un botó per registrar un treball ja vinculat a ella
- **⬆️ Actualitzar des de l'app**: quan hi ha una versió nova, l'avís té els botons «Després» i «Actualitzar»; «Actualitzar» baixa l'APK amb una barra de progrés i obre l'instal·lador d'Android, sense passar per GitHub

### 📦 Aplicació mòbil d'estoc (Android)

Aplicació independent (`mantpro_stock_app`), pensada per consultar i moure
l'estoc del magatzem des del mòbil sense necessitat de l'aplicació de
treballs.

- **🔐 Accés amb usuari**: fa servir el mateix sistema d'usuaris i sessió que l'aplicació de treballs (el token es desa al Keystore d'Android, no en clar)
- **🗂️ Navegació pel magatzem**: arbre de prestatgeries > prestatges > seccions, igual que al PC
- **🔎 Cerca de materials**: per nom, codi, descripció o ubicació
- **➕➖ Entrades i sortides**: registra moviments d'estoc des del mòbil, amb motiu opcional
- **🔀 Trasllats**: moure un material de secció queda reflectit al seu historial de moviments
- **🎨 Avís visual d'estoc**: quantitat en vermell per sota del mínim, en verd per sobre i amb el color per defecte si coincideix exactament
- **⚠️ Estoc per sota del mínim**: pestanya dedicada als materials en alerta
- **🔄 Actualització automàtica**: la pantalla es refresca sola en detectar canvis, tant si el canvi es va fer al mateix mòbil com al PC
- **🔌 Mode fora de línia**: sense connexió amb el PC l'aplicació no es queda esperant: consulta les dades desades i permet registrar altes, edicions, entrades i sortides al moment, que s'envien soles al PC tan bon punt torna a ser accessible
- **🔔 Recordatori diari de comprovació d'estoc**: notificació automàtica a les 8:00 (hora local) que convida a revisar la quantitat real de 5 materials del magatzem, triats a l'atzar i diferents cada dia; en prémer-la s'obre una pantalla per corregir la quantitat de cadascun sense haver-los de cercar. Si no hi ha cap material donat d'alta, no es mostra cap notificació
- **🔄 Connectada en segon pla**: com MantPro, continua sincronitzant en segon pla, amb la seva notificació; la icona d'usuari es posa **verda** si hi ha connexió amb el PC i **vermella** si no
- **🔩 S'utilitza a**: cada article mostra a quines màquines s'utilitza com a recanvi i quants en porta cadascuna, també sense connexió
- **🔍 Avís de repetits**: en crear o editar un article avisa si ja n'hi ha un altre amb el mateix codi o un nom molt semblant, comparant amb els articles desats al mòbil (funciona sense connexió)
- **⬆️ Actualitzar des de l'app**: igual que MantPro, baixa i instal·la la nova versió des del mateix avís

---

## 🔧 Requisits

### Aplicació d'escriptori

- **Python**: 3.10 o superior
- **Sistema operatiu**: Windows o Linux
- **Dependències de Python**:
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - xlsxwriter
  - openpyxl
  - Pillow
  - cryptography
  - keyring i sqlcipher3-wheels (opcionals: xifratge de les bases de dades)
  - sqlite3 (inclòs a Python)

### Aplicació mòbil

S'aplica tant a `mantenimiento_app` (treballs) com a `mantpro_stock_app` (estoc):

- **Flutter**: 3.0 o superior
- **Dart SDK**: 2.17 o superior
- **Android**: API Level 24+ (Android 7.0+)

---

## 📥 Instal·lació

### Aplicació d'escriptori

#### Opció 1: descàrrega precompilada (recomanat)

Descarrega la versió corresponent al teu sistema des de [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: descarrega i executa el `.exe`
- **Linux**:
  - Descarrega el binari executable i dona-li permisos d'execució: `chmod +x mantpro`
  - O fes servir l'**AppImage** (sense instal·lació): `chmod +x MantPro.AppImage && ./MantPro.AppImage`
  - Els paquets **`.deb`** i **`.rpm`** estan signats digitalment amb GPG (vegeu [Verificar la signatura dels paquets](#-verificar-la-signatura-dels-paquets-linux))
  - **Arch Linux**: disponible a AUR: `yay -S mantpro` o `paru -S mantpro`
  - **openSUSE Tumbleweed / Slowroll**: disponible a [OBS](https://build.opensuse.org/package/show/home:danitxu79/MantPro), compilat amb el Python i el PyQt6 de la mateixa distribució i actualitzat amb `zypper`:
    ```bash
    sudo zypper ar -f https://download.opensuse.org/repositories/home:/danitxu79/openSUSE_Tumbleweed/home:danitxu79.repo
    sudo zypper in mantpro
    ```
    (a Slowroll, canvia `openSUSE_Tumbleweed` per `openSUSE_Slowroll` a la URL)

#### 🔏 Verificar la signatura dels paquets (Linux)

Els paquets `.deb` i `.rpm` publicats a cada release estan signats amb la clau GPG oficial d'AnabasaSoft. Per verificar-los abans d'instal·lar-los:

**Empremta de la clau** (comprova-la també a [anabasasoft.github.io](https://anabasasoft.github.io/about.html#firma)): `11C7 C6C8 127D FE48 33DE  30EF 9D7A AEC8 1842 C199` (RSA 4096, caduca el 2028-10-06). Si la que et mostra `gpg` no coincideix exactament, no instal·lis el paquet.

1. Descarrega la clau pública del repositori ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)) a un fitxer (**no facis servir `curl | rpm --import -`**: algunes versions de `rpm` no admeten llegir la clau per l'entrada estàndard i fallen):
   ```bash
   curl -sL https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/firma/anabasasoft_public.asc -o /tmp/anabasasoft_public.asc
   ```

2. Importa la clau (només cal fer-ho una vegada per equip):
   ```bash
   # Fedora, openSUSE, RHEL... (paquet .rpm)
   sudo rpm --import /tmp/anabasasoft_public.asc

   # Debian, Ubuntu... (paquet .deb, requereix dpkg-sig)
   gpg --import /tmp/anabasasoft_public.asc
   ```

3. Comprova que la clau s'ha importat correctament:
   ```bash
   # RPM
   rpm -qa 'gpg-pubkey*' --qf '%{name}-%{version}-%{release} --> %{summary}\n' | grep -i anabasasoft

   # DEB (o qualsevol distribució amb gpg): mostra també l'empremta
   gpg --fingerprint AnabasaSoft
   ```

4. Verifica la signatura del paquet descarregat:
   ```bash
   # RPM
   rpm --checksig mantpro-*.rpm

   # DEB
   dpkg-sig --verify mantpro_*.deb
   ```
   Una signatura correcta mostra `OK` a la línia de la signatura (en lloc de `NOKEY` o `MISSING KEYS`).

Una signatura vàlida confirma que el paquet prové d'AnabasaSoft i que no s'ha modificat.

#### Opció 2: instal·lació des del codi font

1. **Clonar el repositori**:
   ```bash
   git clone https://github.com/AnabasaSoft/MantPro.git
   cd MantPro
   ```

2. **Crear un entorn virtual** (recomanat):
   ```bash
   python -m venv venv
   source venv/bin/activate  # A Windows: venv\Scripts\activate
   ```

3. **Instal·lar les dependències**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Executar l'aplicació**:
   ```bash
   python main.py
   ```

### Aplicació mòbil

#### Opció 1: descàrrega directa (recomanat)

Descarrega l'`.apk` corresponent des de [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) i instal·la'l al teu dispositiu Android: `MantPro.apk` per als treballs, `MantProStock.apk` per a l'estoc del magatzem. Són aplicacions independents i en pots instal·lar una, l'altra o totes dues.

**Nota**: és possible que hagis d'habilitar "Orígens desconeguts" a la configuració de seguretat del dispositiu.

**Des del PC, amb un QR**: a `Eines > 📱 Instal·lar MantPro al mòbil` (o
`📦 Instal·lar MantPro Stock al mòbil`) apareix un QR. Escaneja'l amb la càmera
del mòbil, obre l'enllaç i es baixa l'última versió estable de l'app. Un cop
instal·lades, les apps avisen de les versions noves i s'actualitzen des del
mateix avís amb el botó «Actualitzar».

#### Opció 2: compilar des del codi font

1. **Anar al directori de l'aplicació mòbil** (`mantenimiento_app` per als treballs, `mantpro_stock_app` per a l'estoc):
   ```bash
   cd mantenimiento_app
   ```

2. **Instal·lar les dependències**:
   ```bash
   flutter pub get
   ```

3. **Executar en un dispositiu o emulador**:
   ```bash
   flutter run
   ```

4. **Compilar l'APK (Android)**:
   ```bash
   flutter build apk --release
   ```

---

## 🚀 Ús

### Primera configuració

#### Aplicació d'escriptori

1. **Iniciar l'aplicació**: executa `python main.py` (el servidor de sincronització s'engega sol, no cal iniciar-lo a mà)
2. **Primer accés**: en el primer arrencament es crea l'usuari `admin` amb contrasenya `admin`. L'aplicació **obliga a canviar-la** en entrar
3. **Crear els usuaris**: menú `Eines` > `👥 Gestió d'usuaris` > dona d'alta cada tècnic
4. **Configurar el logotip** (opcional): menú `Arxiu` > `📤 Exportar` > `📄 Opcions PDF` > `🖼️ Afegir / canviar el logotip`
5. **Registrar un treball**: pestanya "📝 Registrar" > omple el resum i els detalls > "💾 DESAR REGISTRE"
6. **Crear un pendent**: pestanya "🔨 Pendents" > grup "Treball nou" (Títol + Detalls + "Assignar a") > "Afegir"

#### Aplicació mòbil

1. **Instal·lar l'aplicació** al teu dispositiu mòbil
2. **Connectar amb el PC**:
   - Assegura't que el PC i el mòbil són a la mateixa xarxa WiFi
   - Al PC: menú `Eines` > `📲 Sincronitzar App (QR)`
   - Al mòbil: toca "Vincular PC" i escaneja el codi
3. **Iniciar sessió**: introdueix l'usuari i la contrasenya que t'hagi creat l'administrador. La sessió queda desada: només cal fer-ho una vegada
4. **A punt**: ja pots registrar intervencions des del mòbil

### Flux de treball habitual

#### Des del PC

1. **Crear i assignar una tasca pendent**:
   - Pestanya "🔨 Pendents" > grup "Treball nou" > omple el Títol i els Detalls, tria el tècnic a "Assignar a" > "Afegir"
   - Gestiona-la amb els botons "✅ Completar", "✏️ Editar", "❌ Eliminar" o "👤 Reassignar"
   - El desplegable "Veure els de" filtra la llista per tècnic (inclou "Sense assignar")

2. **Revisar els treballs completats**:
   - Els treballs sincronitzats des del mòbil apareixen automàticament
   - Revisa les fotos (abans/després i col·lecció) i els detalls a la pestanya "🗂 Historial" o al "📅 Calendari"
   - La columna "Fet per" indica qui va fer cada treball, i el desplegable de dalt permet veure només els d'una persona

3. **Generar informes**:
   - Menú `Arxiu` > `📤 Exportar` > `📄 Opcions PDF` > `📄 Generar PDF ara`
   - Al diàleg pots triar el tècnic, i el seu nom apareix al títol de l'informe
   - O exporta a `📄 CSV` / `📊 Excel` des de `Arxiu` > `📤 Exportar`

#### Des del mòbil

1. **Vincular amb el PC i iniciar sessió** (només la primera vegada, o si canvies de xarxa):
   - Toca "Vincular PC" i escaneja el QR que mostra el PC
   - Introdueix el teu usuari i la contrasenya
   - El mòbil desa l'adreça del PC i la teva sessió per sincronitzar automàticament a partir d'aquí

2. **Registrar una intervenció**:
   - Toca "Nou" o selecciona un treball pendent ja sincronitzat des del PC
   - Amb el xip "Només els meus" veus únicament els treballs que t'han assignat
   - Completa el títol i els detalls
   - Fes la foto d'"abans" i, opcionalment, la d'"després" amb la càmera; si cal, afegeix-ne més a la col·lecció de fotos
   - Dibuixa o anota sobre la foto si cal
   - Selecciona les etiquetes adequades
   - Desa

3. **Sincronitzar**:
   - En obrir l'aplicació se sincronitza tot en segon pla (veuràs un indicador a la barra superior)
   - També ho pots forçar estirant la llista cap avall o amb la icona de sincronització
   - Els registres s'envien al PC i s'eliminen del mòbil quan es confirma l'enviament
   - Tot funciona sense connexió: el que està pendent es desa i es puja quan hi ha cobertura

---

## 👥 Usuaris i accés

### Rols

Un mateix usuari pot tenir **un o diversos rols alhora** (per exemple, tècnic
i magatzem). Rols disponibles:

| Rol | Què pot fer |
|-----|-------------|
| **Administrador** | Tot el que fan el tècnic i el de magatzem, a més de donar d'alta i de baixa usuaris, canviar rols, restablir contrasenyes, editar o esborrar **qualsevol** registre de l'historial, reassignar l'autor d'un o diversos registres alhora, i consultar el registre d'auditoria de canvis |
| **Tècnic** | Registrar treballs, completar pendents i avisos, editar o esborrar **només els seus propis** registres de l'historial, i canviar la seva pròpia contrasenya |
| **Magatzem** | Donar d'alta o editar materials i registrar entrades/sortides d'estoc des de l'aplicació mòbil **MantPro Stock** |

Sempre ha de quedar **almenys un administrador actiu**: l'aplicació impedeix
treure el rol o desactivar l'últim que queda.

> Des de l'aplicació d'escriptori, qualsevol usuari (sigui quin sigui el seu
> rol) pot registrar moviments d'estoc; el rol **Magatzem** és el que habilita
> aquesta mateixa gestió (altes, edicions i moviments) des del mòbil.

### Gestió des del PC

- **Alta**: `Eines` > `👥 Gestió d'usuaris` > omple l'usuari, el nom, la
  contrasenya i el rol > "➕ Afegir". Si deixes marcat "Demanar canvi en
  entrar", la persona haurà de definir la seva pròpia contrasenya en el primer
  accés.
- **Baixa**: es fa de manera **lògica** (l'usuari queda inactiu). No s'esborra
  mai, per no trencar l'autoria dels treballs que ja va fer.
- **Restablir la contrasenya**: útil quan algú l'oblida. En canviar-la es
  tanquen automàticament totes les sessions obertes d'aquesta persona al mòbil.
- **Canviar la pròpia contrasenya**: `Eines` > `🔑 Canviar la meva contrasenya`.

### Sessions de dispositius

`Eines` > `🔐 Sessions de dispositius` (només administradors) llista totes les
sessions obertes al mòbil de tots els usuaris, amb el model del dispositiu,
quan es va iniciar, quan caduca i si continua activa o ja ha caducat. Es poden
seleccionar una o diverses files alhora i revocar-les, cosa que tanca la sessió
d'aquell mòbil sense necessitat de desactivar l'usuari sencer (que tancaria
*tots* els seus dispositius de cop).

Si un usuari torna a iniciar sessió des d'un dispositiu amb què ja tenia una
sessió oberta (mateix fabricant i model), la sessió anterior d'aquest
dispositiu s'esborra automàticament en crear la nova, en lloc de quedar-se
acumulada com una sessió solta més al llistat.

La columna **Connexió** indica si cada mòbil està **en línia** ara mateix i quan
va ser el seu últim contacte. Les apps avisen el PC cada pocs segons mentre són
obertes (també en segon pla), i en tancar-les del tot avisen que es
desconnecten, així que l'estat s'actualitza al moment.

### Autoria dels treballs

Cada registre desa el tècnic que el va fer, tant si es va crear al PC com si
va arribar del mòbil. Els registres anteriors a la implantació del sistema
d'usuaris van quedar marcats com a **`Histórico`**.

Al mòbil, l'atribució la decideix **sempre el servidor** a partir del testimoni
de la sessió, mai una dada enviada per l'aplicació. Un dispositiu no pot signar
treballs en nom d'una altra persona.

Des del PC, un tècnic només pot editar o esborrar els seus propis registres de
l'historial; un administrador ho pot fer amb qualsevol. Amb el botó dret sobre
una o diverses files de l'historial (selecció múltiple amb Ctrl/Maj), un
administrador també pot **reassignar l'autor** en bloc, i cada canvi queda
anotat al registre d'auditoria.

### Registre de canvis (auditoria)

Els administradors veuen a `Eines` > `📋 Registre de canvis` **qui va canviar
què, quan i des d'on** (el PC o quin mòbil): treballs, pendents, avisos, llistes
de comprovació, màquines i recanvis, articles i estructura del magatzem, usuaris
i especialitats, seguretat (sessions revocades, bloquejos per intents fallits,
xifratge, connexió sense xifrar), còpies restaurades, importacions i
configuració. Cada canvi mostra els camps afectats **abans → després**. Es pot
filtrar per categoria, acció, usuari i període, cercar per text i exportar a
Excel o CSV.

### Sessió al mòbil

El tècnic inicia sessió una vegada i el testimoni queda desat al dispositiu. La
sessió es tanca sola si l'administrador desactiva l'usuari o li restableix la
contrasenya; en aquest cas l'aplicació torna a la pantalla d'accés **sense
perdre els registres que encara estiguin pendents de pujar**.

El token de sessió es desa al **Keystore d'Android** (emmagatzematge segur), no en clar. Després de **5 intents fallits** seguits d'inici de sessió, aquell usuari es bloqueja 15 minuts (i un mòbil, després de 20 intents fallits); l'aplicació mostra quant cal esperar. A la finestra del PC, 5 errors bloquegen l'inici de sessió un minut.

---

## 🏭 Maquinària

> Gestió disponible des de l'aplicació d'escriptori, amb el vincle a la
> màquina també seleccionable des del mòbil en registrar o editar un treball.

Pestanya "🏭 Màquines" del PC, pensada per portar el control d'avaries i
intervencions de cada equip al llarg del temps.

- **🌳 Arbre de maquinària**: les màquines poden tenir submàquines (per
  exemple, una línia amb diversos equips), formant una jerarquia tan profunda
  com calgui
- **📅 Treballs organitzats per any i mes**: en desplegar una màquina es veuen
  els anys amb treballs, i en desplegar un any, els mesos; cada nivell mostra
  un comptador de quants treballs té, amb càrrega a demanda per no alentir
  l'arbre
- **🖱️ Accés directe al treball**: amb doble clic sobre un treball de l'arbre
  s'obre directament la seva fitxa d'edició
- **📸 Foto de la màquina**: cada màquina o submàquina pot tenir una foto
  adjunta, visible en un requadre al costat de l'arbre en seleccionar-la
- **🔗 Vincle des de cada treball**: en registrar un treball nou (PC o mòbil) o
  editar-ne un d'existent es pot triar a quina màquina/submàquina pertany
- **📊 A les exportacions**: la màquina o submàquina vinculada apareix com a
  columna addicional a les exportacions a PDF, CSV i Excel
- **🗺️ Zona heretada**: en crear una submàquina, pren per defecte la zona de
  la seva màquina superior
- **🔩 Recanvis de cada màquina**: a sota de l'arbre es veuen els articles del
  magatzem que porta la màquina seleccionada, quants en porta, el seu estoc
  (en vermell si és per sota del mínim), la seva ubicació i una nota (per
  exemple «costat motor»). S'afegeixen amb «➕ Afegir recanvi», s'exporten a
  PDF o Excel, i amb doble clic es salta a l'article al magatzem
- **🏷️ Etiquetes QR**: el botó «🏷️ Etiquetes QR» genera un PDF de fulls A4 amb
  24 etiquetes de 70 × 37 mm (de la màquina seleccionada, amb les seves
  submàquines o de totes). En escanejar-les amb l'app MantPro s'obre la fitxa
  de la màquina
- **🔍 Noms semblants**: en crear o reanomenar una màquina, avisa si al mateix
  nivell ja n'hi ha una altra amb un nom igual o molt semblant

---

## 📦 Estoc del magatzem

> Gestió completa des de l'aplicació d'escriptori, amb consulta i moviments
> també disponibles des del mòbil (`mantpro_stock_app`). Viu a la seva pròpia
> base de dades (`almacen.db`), independent de la dels treballs de
> manteniment.

### Estructura del magatzem

El magatzem s'organitza en tres nivells, inspirats en les convencions habituals
de codificació d'ubicacions de magatzem:

```
Prestatgeria → Prestatge → Secció
```

- En crear una prestatgeria es defineix el **nombre de prestatges**, el
  **nombre de seccions per prestatge** (0 = sense seccions predefinides, se'n
  poden afegir després) i si té **espai a terra** sota el prestatge inferior,
  que es gestiona com un prestatge especial ("Terra")
- Els prestatges es numeren de baix a dalt començant per l'1, per poder afegir
  prestatges nous sense haver de renumerar els existents
- No es pot eliminar una prestatgeria, un prestatge o una secció mentre
  contingui material ubicat

L'estructura es gestiona des del botó **"⚙️ Configurar magatzem"** de la
pestanya "📦 Estoc de magatzem", visible **només per als administradors**.

### Materials

- Alta i edició amb codi (opcional), nom, descripció, unitat, estoc mínim,
  ubicació (prestatgeria / prestatge / secció) i **foto adjunta**
- Cerca per **nom, codi, descripció o ubicació**
- L'estoc es ressalta en **vermell** per sota del mínim, en **verd** per sobre
  i amb el color per defecte si coincideix exactament amb el mínim, tant al PC
  com al mòbil
- Seleccionant diversos materials alhora (Ctrl/Maj + botó dret) al PC es poden
  **moure d'ubicació** o **eliminar** en bloc
- Cada material indica **a quines màquines s'utilitza** com a recanvi, i en
  crear-lo o editar-lo s'hi poden associar màquines directament, amb la
  quantitat que en porta cadascuna
- En crear o editar un material s'avisa si ja n'hi ha un altre amb el **mateix
  codi o un nom molt semblant**, per no donar-lo d'alta dues vegades

### Entrades, sortides i trasllats

- **Qualsevol usuari** pot registrar entrades i sortides d'estoc; només la
  configuració de l'estructura del magatzem està restringida als
  administradors
- Cada moviment queda registrat amb data, quantitat, usuari i un motiu
  opcional, visible a l'historial al costat de cada material
- Les sortides registrades a mà (PC o `mantpro_stock_app`) no poden deixar
  l'estoc en negatiu
- Canviar la ubicació d'un material també queda registrat al seu historial, com
  un moviment de tipus **trasllat** (de quina secció a quina secció)
- El botó **«📜 Historial»** mostra tots els moviments del magatzem seguits
  (entrades, sortides i trasllats), amb el nom de cada article i filtres per
  text i tipus

### Material utilitzat en un treball (MantPro)

En completar un treball des de l'aplicació **MantPro** (mòbil), es pot afegir el
material que s'ha fet servir cercant-lo pel nom o el codi i indicant-ne la
quantitat. En desar el treball, aquest material es descompta automàticament del
magatzem, amb el motiu "Usat en un treball: ..." per mantenir la traçabilitat.

A diferència de les sortides manuals, **aquest descompte sí que pot deixar
l'estoc en negatiu**: el material ja s'ha fet servir físicament per fer el
treball encara que no hi hagués prou estoc registrat, així que bloquejar el
moviment no tindria sentit. L'estoc negatiu es veurà tant al PC com a
`mantpro_stock_app`, i serveix d'avís que cal comprovar i reposar aquest
material com més aviat millor.

### Alertes d'estoc per sota del mínim

La pestanya **"⚠️ Estoc per sota del mínim"** mostra, en una vista a part, els
materials sense estoc o per sota del mínim establert. El mateix títol de la
pestanya indica quants materials estan en alerta, i des d'allà es pot saltar
directament al material a "Estoc de magatzem", registrar una entrada sense
canviar de pestanya o exportar la llista amb el botó "📄 Exportar".

### Exportar l'estoc

A la pestanya **"📦 Estoc de magatzem"** del PC, el botó **"📄 Exportar"** obre
una finestra per triar el **format** (PDF, CSV o Excel) i **què exportar**: tot
el magatzem, una zona o una sola prestatgeria. La llista surt ordenada per
ubicació, per poder recórrer el magatzem amb ella a la mà; el PDF i l'Excel
inclouen a més la data, el nombre de materials i quants n'hi ha per sota del
mínim (en vermell). La mateixa taula d'estoc també es mostra ordenada per
ubicació per defecte (Prestatgeria 1, 2… 10).

---

## 🔄 Sincronització PC-mòbil

### Com funciona

MantPro fa servir un sistema de sincronització basat en:

1. **Servidor Flask** integrat a l'aplicació d'escriptori
2. **Codis QR** per a una connexió ràpida i segura
3. **API REST autenticada per testimoni**: tots els punts d'accés de dades
   exigeixen una sessió vàlida; si el testimoni deixa de valer, el servidor
   respon `401` i el mòbil torna a l'inici de sessió
4. **WiFi local**, sense necessitat d'internet
5. **Sincronització completa en obrir l'aplicació**, en segon pla i sense
   bloquejar la interfície
6. Mentre les apps del mòbil són obertes, encara que sigui en segon pla,
   continuen sincronitzant i el PC les veu **en línia** a `Eines > 🔐 Sessions
   de dispositius`
7. La primera sincronització mostra una **barra de progrés** i baixa les dades
   en paral·lel i les fotos de 4 en 4

> 🔒 La sincronització va **xifrada (HTTPS)**. El PC crea el seu propi
> certificat i la seva empremta viatja al QR: el mòbil només es connecta a
> *aquell* PC, així que ningú a la WiFi pot llegir el trànsit ni fer-se passar
> per ell. Els mòbils ja vinculats passen sols a HTTPS en actualitzar l'app.

### Configuració de la xarxa

Perquè la sincronització funcioni:

- ✅ El PC i el mòbil han de ser a la **mateixa xarxa WiFi**
- ✅ El **tallafoc** ha de permetre connexions al port 5000 (o el configurat)
- ✅ També ha de permetre el **port següent** (5001 per defecte), que fa servir la connexió xifrada (HTTPS)
- ✅ Si fas servir Windows, potser hauràs de crear una excepció al tallafoc

### Resolució de problemes

**El mòbil no connecta amb el PC:**
- Verifica que tots dos dispositius són a la mateixa xarxa
- Comprova que el servidor està actiu al PC (icona verda)
- Prova de desactivar temporalment el tallafoc del PC
- Torna a generar el codi QR i torna'l a escanejar

**No puc iniciar sessió des del mòbil:**
- Comprova que MantPro està obert al PC: l'inici de sessió es valida contra ell
- Verifica l'usuari i la contrasenya amb l'administrador; la pot restablir
- Si el PC ha canviat d'IP, torna a escanejar el QR des de la mateixa pantalla d'accés ("Vincular un altre PC")

**L'aplicació m'ha tornat a la pantalla d'accés:**
- És normal si l'administrador ha restablert la teva contrasenya o ha desactivat el teu usuari
- Els teus registres sense pujar **no es perden**: torna a entrar i se sincronitzen

**He oblidat la contrasenya d'administrador:**
- Un altre administrador la pot restablir des de `Eines` > `👥 Gestió d'usuaris`
- Si no hi ha cap altre administrador, cal restablir-la directament a la taula
  `usuarios` de la base de dades

**Les fotos no se sincronitzen:**
- Verifica que hi ha prou espai al disc del PC
- Comprova els permisos de la carpeta `fotos_recibidas`
- Assegura't que la foto es va desar correctament al mòbil

**No m'arriba la notificació diària d'avisos pendents (Android):**
- Comprova que el permís de notificacions està concedit: `Configuració → Aplicacions → MantPro → Notificacions`
- En fabricants com **OPPO/Realme (ColorOS), Xiaomi (MIUI) o Huawei**, el sistema pot aturar l'alarma programada encara que el permís estigui concedit. A més, cal:
  - `Configuració → Bateria → Ús de la bateria per aplicació → MantPro` → posar-lo a **"Sense restriccions"**
  - `Configuració → Bateria → Inici automàtic` → **activar** MantPro
- La notificació es torna a avaluar cada vegada que obres el Tauler, així que si acabes de marcar un treball com a completat, torna'l a obrir perquè es cancel·li o es reprogrami correctament.

**No m'arriba la notificació diària de comprovació d'estoc (MantPro Stock):**
- S'apliquen les mateixes comprovacions que a MantPro (permís de notificacions i exclusió de l'optimització de bateria, vegeu més amunt)
- Si el magatzem no té cap material donat d'alta, no es mostra cap notificació: és el comportament esperat
- Es torna a avaluar cada vegada que l'aplicació se sincronitza amb el PC (en obrir-la i cada 25 segons mentre està oberta)

**MantPro demana una clau de recuperació en arrencar:**
- Les bases de dades estan xifrades i el clauer del sistema ja no en té la clau (sistema reinstal·lat, un altre compte d'usuari…)
- Escriu la clau de recuperació que es va mostrar en activar el xifratge; MantPro la torna a desar al clauer
- Si no la tens, les bases de dades no es poden obrir: treu `mantenimiento.db` i `almacen.db` de la carpeta de dades, obre MantPro i restaura una còpia de seguretat

**«Massa intents fallits» en iniciar sessió:**
- Després de diverses contrasenyes errònies seguides, l'inici de sessió es bloqueja una estona (15 minuts al mòbil, un minut al PC); espera el temps que indica l'avís o demana a un administrador que et restableixi la contrasenya

### 🔒 Nota sobre seguretat

La sincronització va xifrada amb HTTPS i el certificat del PC queda fixat
per l'empremta del QR. Durant la transició, el PC continua atenent també per
HTTP al port configurat per a les apps de versions anteriors; HTTPS fa servir
el **port següent** (per exemple, 5000 i 5001), així que si hi ha un tallafoc
cal obrir-los tots dos. Si mai exposes el servidor fora de la xarxa local,
fes-ho a través d'una VPN.

Quan tots els mòbils tinguin l'app actualitzada, desactiva la connexió sense
xifrar a `Eines > 🔐 Sessions de dispositius`: la columna «Xifratge» mostra quins
mòbils es connecten encara sense ella. A partir d'aleshores el PC només atén
per HTTPS.

Les bases de dades també es poden desar **xifrades** (`Eines > Xifratge de
les bases de dades…`, SQLCipher): la clau va al clauer del sistema i es mostra
una clau de recuperació per apuntar-la. Ve desactivat.

---

## 💾 Còpies de seguretat

MantPro fa una **còpia automàtica en tancar** (les bases de dades, i les fotos
en ZIP incrementals per any) i permet fer una **còpia completa a mà** des
d'`Arxiu > Backup` i restaurar-la des d'`Arxiu > Restaurar`. `Eines` inclou
a més netejar les fotos que ja no fa servir cap registre i esborrar els
treballs més antics que un temps donat, sempre amb còpia prèvia.

🔒 Amb `Arxiu > Contrasenya de les còpies…` les còpies es desen **xifrades**
(AES-256 amb una clau obtinguda de la contrasenya): una còpia que surt de
l'equip (USB, NAS, núvol) no es pot obrir sense ella. Si oblides la
contrasenya, les còpies xifrades no es poden recuperar.

Detall complet: [docs/copias-de-seguridad.md](docs/copias-de-seguridad.md)
(en castellà) · [docs/backups.md](docs/backups.md) (en anglès).

---

## 🤝 Contribuir

Les contribucions són benvingudes! Abans d'obrir un *pull request*, llegeix
[CONTRIBUTING.md](CONTRIBUTING.md): explica com preparar els canvis (idiomes,
proves, capçaleres dels fitxers) i l'**acord de contribució ([CLA](CLA.md))**
que cal acceptar.

L'estructura del codi i de la base de dades és a
[docs/desarrollo.md](docs/desarrollo.md) (en castellà) i
[docs/development.md](docs/development.md) (en anglès). Per a errors de
seguretat, mira [SECURITY.md](SECURITY.md).

---

## 🧭 Full de ruta

El que ve, sense dates i sense un ordre tancat:

- **Cost de mà d'obra** (preu per hora de cada tècnic) per sumar al de material
- **Proveïdors, preus i comandes de compra** a partir de l'estoc sota mínim
- **Preventiu per comptador** (hores d'ús, cicles, km), a més de per data
- **Temps treballat i signatura** en tancar un treball (també al mòbil)
- **Documentació tècnica per màquina** (manuals, plànols i esquemes en PDF)
- **Criticitat de les màquines (ABC)**, per decidir on invertir en manteniment
- **Sol·licituds de treball** des de producció o altres departaments que creen un pendent
- **Notificacions push** de treballs urgents i **vídeos** als treballs
- **Diversos PC alhora**, servidor sense finestra (Raspberry Pi, NAS, Docker) i accés web
- **Diversos centres o plantes** amb dades i indicadors per centre
- Més idiomes (italià, alemany…) i app per a iPhone

Fet fa poc: recanvis utilitzats en cada treball amb el seu cost per màquina, llistes de comprovació en preventius i treballs, sincronització, bases de dades i còpies xifrades, i un registre de canvis més complet.

Els canvis de cada versió són a [CHANGELOG.md](CHANGELOG.md). Hi trobes a
faltar alguna cosa? Obre una [*issue*](https://github.com/AnabasaSoft/MantPro/issues).

---

## 📄 Llicència

Aquest projecte està sota la **GNU Affero General Public License v3.0 (AGPL-3.0)**.
Consulta el fitxer `LICENSE` per al text complet.

Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft)

### Què vol dir a la pràctica

- ✅ Pots **fer servir** MantPro lliurement, també a la teva empresa i amb finalitats comercials
- ✅ Pots **estudiar, modificar i redistribuir** el codi
- ⚠️ Si distribueixes una versió modificada, l'has de publicar **també sota AGPL-3.0**
- ⚠️ Si ofereixes MantPro (o un derivat) **com a servei a través d'una xarxa**, has
  de posar el codi font a disposició de qui el faci servir, encara que no
  distribueixis cap executable. Aquesta és la diferència clau respecte a la GPL v3
- ⚠️ Has de mantenir els avisos de copyright i de llicència

### Avís de llicència

```
MantPro - Sistema de Manteniment Preventiu
Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft)

Aquest programa és programari lliure: el pots redistribuir i/o modificar
sota els termes de la Llicència Pública General Affero de GNU publicada per
la Free Software Foundation, ja sigui la versió 3 de la Llicència o (a la
teva elecció) qualsevol versió posterior.

Aquest programa es distribueix amb l'esperança que sigui útil, però SENSE
CAP GARANTIA; ni tan sols la garantia implícita de COMERCIABILITAT o
IDONEÏTAT PER A UN PROPÒSIT PARTICULAR. Consulta la Llicència Pública
General Affero de GNU per a més detalls.

Hauries d'haver rebut una còpia de la Llicència Pública General Affero de
GNU juntament amb aquest programa. Si no és així, consulta
<https://www.gnu.org/licenses/>.
```

> **Nota sobre llicències comercials**: AnabasaSoft és l'únic titular del
> copyright de MantPro i, per tant, pot oferir el mateix codi en condicions
> diferents de l'AGPL. Si necessites integrar MantPro en un producte
> propietari, posa't en contacte.

---

## 📧 Contacte

**AnabasaSoft**

- 📧 Correu: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com)
- 🌐 GitHub: [github.com/AnabasaSoft](https://github.com/AnabasaSoft)
- 💼 Projecte: [github.com/AnabasaSoft/MantPro](https://github.com/AnabasaSoft/MantPro)

---

## 🙏 Agraïments

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/): framework d'interfície gràfica multiplataforma per a l'aplicació d'escriptori
- [Flutter](https://flutter.dev/): SDK per a les aplicacions mòbils
- [ReportLab](https://www.reportlab.com/): generació d'informes en PDF
- [SQLite](https://www.sqlite.org/): base de dades integrada
- [Flask](https://flask.palletsprojects.com/): microframework web per al servidor de sincronització
- La comunitat de codi obert, pel seu suport i les seves contribucions

---

<div align="center">

<img src="https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/recursos/AnabasaSoft.png" alt="Anabasa Software" width="120"/>

**Desenvolupat amb ❤️ per [Anabasa Software](https://anabasasoft.github.io)**

📧 Correu: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com) • 🌐 Portafoli: [anabasasoft.github.io](https://anabasasoft.github.io)

⭐ Si t'agrada aquest projecte, dona-li una estrella a GitHub

</div>

<div align="center">
  <br/>
  <p><code>>_ sudo buy-me-a-coffee --theme=dark --force</code></p>
  <a href="https://www.buymeacoffee.com/danitxu" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-black.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important; box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;">
  </a>
  <br/>
</div>
