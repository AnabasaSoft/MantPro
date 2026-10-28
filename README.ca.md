<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-6e7781?style=for-the-badge" alt="English"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Espa%C3%B1ol-6e7781?style=for-the-badge" alt="Español"></a>
  <a href="README.eu.md"><img src="https://img.shields.io/badge/Euskara-6e7781?style=for-the-badge" alt="Euskara"></a>
  <a href="README.ca.md"><img src="https://img.shields.io/badge/Catal%C3%A0-0969da?style=for-the-badge" alt="Català"></a>
  <a href="README.gl.md"><img src="https://img.shields.io/badge/Galego-6e7781?style=for-the-badge" alt="Galego"></a>
  <a href="README.pt.md"><img src="https://img.shields.io/badge/Portugu%C3%AAs-6e7781?style=for-the-badge" alt="Português"></a>
</p>

# MantPro

<p align="center">
  <img src="logo.png" alt="Logotip de MantPro" width="200"/>
</p>

<p align="center">
  <strong>CMMS gratuït i de codi obert per gestionar el manteniment preventiu i correctiu de la teva planta, taller o flota, des del PC i Android.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Offline--first-✔-success.svg" alt="Offline-first">
  <img src="https://img.shields.io/badge/Sense%20subscripci%C3%B3-100%25%20gratu%C3%AFt-orange.svg" alt="Sense subscripció">
</p>

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

## 🆚 Per què MantPro i no un CMMS comercial?

- **Codi obert i gratuït**: codi obert sota AGPL-3.0, sense límit de tècnics,
  màquines o registres
- **Sense subscripció**: no es paga per usuari ni per mes d'ús
- **Les teves dades, a la teva infraestructura**: la base de dades viu al teu
  propi PC; no depens que un servei al núvol d'un tercer continuï existint
  l'any vinent
- **Fora de línia de veritat**: el mòbil funciona sense connexió a internet ni
  al PC durant tota la jornada, i se sincronitza tan bon punt torna a haver-hi
  xarxa
- **Fet des del mateix manteniment**: les funcions han anat sortint de
  necessitats reals de taller (fotos d'abans/després, vincle a màquina, estoc
  de recanvis, avisos recurrents...), no d'una llista de requisits genèrica de
  CMMS

## 🎬 Vídeo de demostració

https://github.com/user-attachments/assets/11572710-e0ba-4f8b-b914-0a959006d4fb

## 📸 Captures de pantalla

### Aplicació d'escriptori

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Tauler" width="45%"/>
  <img src="Capturas/Almacen.png" alt="Gestió del magatzem" width="45%"/>
</p>

### Aplicació mòbil

<p align="center">
  <img src="Capturas/Dashboard-movil.jpg" alt="Tauler al mòbil" width="30%"/>
  <img src="Capturas/Almacen-movil.jpg" alt="Magatzem al mòbil" width="30%"/>
  <img src="Capturas/Historial-movil.jpg" alt="Historial al mòbil" width="30%"/>
</p>

---

## 📋 Índex

- [Quin problema resol?](#-quin-problema-resol)
- [Per a qui és?](#-per-a-qui-és)
- [Per què MantPro?](#-per-què-mantpro-i-no-un-cmms-comercial)
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
- [Estructura del projecte](#-estructura-del-projecte)
- [Contribuir](#-contribuir)
- [Llicència](#-llicència)
- [Contacte](#-contacte)

---

## 📦 Descàrregues

Pots descarregar les versions precompilades des de [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases):

- **Windows**: executable `.exe` per a Windows
- **Linux**:
  - Binari executable de Linux
  - AppImage portable
  - També disponible a **AUR** (Arch User Repository)
- **Android**: fitxers `.apk` per a instal·lació directa
  - `MantPro.apk`: aplicació de treballs de manteniment
  - `MantProStock.apk`: aplicació d'estoc del magatzem

---

## ✨ Característiques

### 💻 Aplicació d'escriptori (PC)

- **👥 Gestió d'usuaris**: inici de sessió amb usuari i contrasenya, rols d'administrador i tècnic, alta i baixa d'usuaris, i restabliment de contrasenyes
- **✍️ Autoria dels treballs**: cada intervenció desa qui la va fer, visible a l'historial i als informes
- **🔒 Permisos per registre**: un tècnic només pot editar o esborrar els seus propis treballs; un administrador pot gestionar-ne qualsevol, inclosa la reassignació de l'autor d'un o diversos registres alhora
- **📋 Auditoria de canvis**: registre de qui edita o esborra cada treball (no només qui el va crear), consultable i filtrable per tècnic i per tipus d'acció des de "Registre de canvis" (només administradors)
- **🔐 Sessions de dispositius**: llista els mòbils vinculats a cada usuari, amb el seu model real, i permet revocar una o diverses sessions concretes sense desactivar l'usuari sencer (només administradors). En tornar a iniciar sessió des del mateix dispositiu, la sessió anterior se substitueix automàticament en lloc d'acumular-se
- **📊 Tauler amb KPI i gràfics**: targetes d'avisos pendents, tasques per fer, registres del mes i MTBF/MTTR mitjans de tota la planta, a més de gràfics de les màquines amb més avaries i d'avaries per mes, dibuixats sense dependre de biblioteques externes
- **🎨 Temes visuals**: tria entre mode fosc (per defecte), clar o un estil retro inspirat en Windows 98, des del menú "Aparença"
- **📅 Calendari interactiu**: visualitza i gestiona les tasques de manteniment amb codis de color (festius, vacances, dies amb tasques)
- **📝 Historial complet**: registre històric de totes les intervencions fetes, amb fotos d'abans/després i una **col·lecció de fotos** addicional per treball; es poden esborrar diversos registres alhora
- **📄 Informes PDF**: generació automàtica d'informes professionals amb logotip personalitzable
- **📸 Gestió d'imatges**: emmagatzematge i visualització de fotos de les intervencions
- **📱 Sincronització mòbil**: servidor integrat (s'engega automàticament) per sincronitzar amb l'aplicació mòbil mitjançant QR
- **🔍 Sistema de cerca**: cerca avançada per dates, etiquetes i contingut
- **👤 Filtre per tècnic**: filtra l'historial i les exportacions (PDF, CSV i Excel) per la persona que va fer el treball
- **📦 Còpia i restauració**: còpia manual completa (BD + fotos) triant on desar-la, còpia automàtica incremental en tancar l'aplicació (vegeu [Còpies de seguretat](#-còpies-de-seguretat)), i restauració amb barra de progrés, amb el submenú `Arxiu > Restaurar` per triar entre qualsevol còpia manual o anar directament a les còpies automàtiques
- **🏷️ Sistema d'etiquetes**: classificació amb etiquetes (Urgent, Elèctric, Mecànic, Preventiu)
- **🔨 Tasques pendents**: gestió de treballs pendents (crear, completar, editar, eliminar) i **assignació a un tècnic concret**
- **🚦 Prioritat dels pendents**: cada treball pendent té una prioritat (Baixa, Mitjana, Alta o Crítica) per decidir quin atacar primer, amb el seu color a la llista; també s'hi poden adjuntar fotos a la seva col·lecció
- **↩️ Revertir a pendent**: si un treball es va completar per error, es pot tornar a Pendents amb un clic des de l'historial (amb avís si tenia màquina vinculada, ja que es perdria aquesta dada), i queda registrat a l'auditoria
- **🔁 Recordatoris**: avisos de manteniment que es repeteixen automàticament. Si es passa la data no se salten: queden en **Pendent** (taronja) mentre dura el marge i després en **Endarrerit** (vermell) fins que es fan, i la data següent es compta des del dia real en què es va fer el treball
- **📦 Control de l'estoc del magatzem**: estructura de prestatgeries, prestatges i seccions configurable, fitxa de materials amb foto, entrades/sortides amb historial i alertes d'estoc per sota del mínim
- **📄 Exportar l'estoc**: botó "📄 Exportar" a la pestanya d'estoc per treure el magatzem sencer, una zona o una prestatgeria a PDF, CSV o Excel, ordenat per ubicació; la pestanya d'estoc per sota del mínim també té el seu botó per exportar només els materials en alerta
- **🗑️ Temps màxim de conservació**: `Eines` permet esborrar de l'historial els treballs més antics que un nombre d'anys, mesos o dies, amb les seves fotos i una còpia de seguretat prèvia (només administradors)
- **🏭 Control de maquinària**: arbre de màquines i submàquines amb foto adjunta, comptador de treballs per any i mes, i vincle directe des de cada treball registrat o editat (vegeu [Maquinària](#-maquinària))
- **📊 Exportació**: a PDF, CSV i Excel, amb filtre opcional per tècnic i indicant la màquina/submàquina de cada treball, si en té

### 📱 Aplicació mòbil (Android)

- **🔐 Accés amb usuari**: cada tècnic inicia sessió una vegada i la sessió queda desada al dispositiu
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
- **🔌 Mode fora de línia**: treballa sense connexió i sincronitza quan puguis
- **⏰ Recordatoris diaris**: notificació automàtica a les 8:00 (hora local) si hi ha treballs pendents sense completar
- **🧰 Material utilitzat**: afegeix al treball el material del magatzem que has fet servir, cercant-lo pel nom o el codi; es descompta sol de l'estoc en desar (vegeu [Material utilitzat en un treball](#-estoc-del-magatzem))
- **🏭 Vincular màquina**: tria en un desplegable la màquina o submàquina en què s'ha fet el treball, tant en crear un registre nou com en editar-ne un de ja sincronitzat de l'historial

### 📦 Aplicació mòbil d'estoc (Android)

Aplicació independent (`mantpro_stock_app`), pensada per consultar i moure
l'estoc del magatzem des del mòbil sense necessitat de l'aplicació de
treballs.

- **🔐 Accés amb usuari**: fa servir el mateix sistema d'usuaris i sessió que l'aplicació de treballs
- **🗂️ Navegació pel magatzem**: arbre de prestatgeries > prestatges > seccions, igual que al PC
- **🔎 Cerca de materials**: per nom, codi, descripció o ubicació
- **➕➖ Entrades i sortides**: registra moviments d'estoc des del mòbil, amb motiu opcional
- **🔀 Trasllats**: moure un material de secció queda reflectit al seu historial de moviments
- **🎨 Avís visual d'estoc**: quantitat en vermell per sota del mínim, en verd per sobre i amb el color per defecte si coincideix exactament
- **⚠️ Estoc per sota del mínim**: pestanya dedicada als materials en alerta
- **🔄 Actualització automàtica**: la pantalla es refresca sola en detectar canvis, tant si el canvi es va fer al mateix mòbil com al PC
- **🔌 Mode fora de línia**: sense connexió amb el PC l'aplicació no es queda esperant: consulta les dades desades i permet registrar altes, edicions, entrades i sortides al moment, que s'envien soles al PC tan bon punt torna a ser accessible
- **🔔 Recordatori diari de comprovació d'estoc**: notificació automàtica a les 8:00 (hora local) que convida a revisar la quantitat real de 5 materials del magatzem, triats a l'atzar i diferents cada dia; en prémer-la s'obre una pantalla per corregir la quantitat de cadascun sense haver-los de cercar. Si no hi ha cap material donat d'alta, no es mostra cap notificació

---

## 🔧 Requisits

### Aplicació d'escriptori

- **Python**: 3.8 o superior
- **Sistema operatiu**: Windows o Linux
- **Dependències de Python**:
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - xlsxwriter
  - sqlite3 (inclòs a Python)

### Aplicació mòbil

S'aplica tant a `mantenimiento_app` (treballs) com a `mantpro_stock_app` (estoc):

- **Flutter**: 3.0 o superior
- **Dart SDK**: 2.17 o superior
- **Android**: API Level 21+ (Android 5.0+)

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

#### 🔏 Verificar la signatura dels paquets (Linux)

Els paquets `.deb` i `.rpm` publicats a cada release estan signats amb la clau GPG oficial d'AnabasaSoft. Per verificar-los abans d'instal·lar-los:

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
   rpm -qa 'gpg-pubkey*' --qf '%{name}-%{version}-%{release} --> %{summary}\n' | grep -i anabasasoft
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
4. **Configurar el logotip** (opcional): menú `Arxiu` > `📄 Opcions PDF` > `🖼️ Afegir / canviar el logotip`
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
   - Menú `Arxiu` > `📄 Opcions PDF` > `📄 Generar PDF ara`
   - Al diàleg pots triar el tècnic, i el seu nom apareix al títol de l'informe
   - O exporta a `📄 CSV` / `📊 Excel` des del mateix menú `Arxiu`

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

Cada vegada que s'edita o s'esborra un treball en queda constància: qui ho va
fer, quan i què va canviar. Els administradors ho poden consultar des de
`Eines` > `📋 Registre de canvis`, amb filtres per tècnic i per tipus d'acció
(editar/esborrar).

### Sessió al mòbil

El tècnic inicia sessió una vegada i el testimoni queda desat al dispositiu. La
sessió es tanca sola si l'administrador desactiva l'usuari o li restableix la
contrasenya; en aquest cas l'aplicació torna a la pantalla d'accés **sense
perdre els registres que encara estiguin pendents de pujar**.

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

> ⚠️ El trànsit viatja per **HTTP dins de la xarxa local**. El sistema d'usuaris
> aporta traçabilitat (saber qui va fer cada treball), no protecció davant d'algú
> amb accés a aquesta mateixa xarxa.

### Configuració de la xarxa

Perquè la sincronització funcioni:

- ✅ El PC i el mòbil han de ser a la **mateixa xarxa WiFi**
- ✅ El **tallafoc** ha de permetre connexions al port 5000 (o el configurat)
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

### 🔒 Nota sobre seguretat

La sincronització viatja per HTTP dins de la xarxa local. El sistema d'usuaris
està pensat per a la **traçabilitat** (saber qui va fer cada treball), no com a
barrera davant d'algú amb accés a aquesta mateixa xarxa. Si en el futur
s'exposa el servidor fora de la xarxa local, el trànsit ha d'anar xifrat (VPN o
túnel amb HTTPS).

---

## 💾 Còpies de seguretat

MantPro distingeix entre dos tipus de còpia, pensats per a moments diferents:

### Còpia automàtica (en tancar l'aplicació)

Cada vegada que es tanca el programa es fa, en segon pla i sense necessitat
d'intervenció, una còpia ràpida pensada perquè no es noti encara que passin els
anys:

- **Bases de dades**: `mantenimiento.db` i `almacen.db` s'empaqueten senceres en
  un ZIP (`auto_backup_db_<data>.zip`) cada vegada, de manera rotativa, i es
  conserven només les 3 més recents.
- **Fotos**: en lloc de tornar a comprimir tot l'historial de fotos a cada
  tancament, es mantenen uns ZIP incrementals per any (`fotos_backup_<any>.zip`):
  cada tancament només afegeix al ZIP de l'any corresponent les fotos que encara
  no hi eren, sense tocar ni tornar a comprimir les d'anys anteriors. Així el
  temps de tancament no creix amb el temps d'ús de l'aplicació.

Mentre es fa aquesta còpia es mostra una finestra amb una barra de progrés que
reté el focus, i el tancament real de l'aplicació espera que acabi.

### Còpia manual (menú Arxiu)

`Arxiu > Còpia de seguretat` continua generant, com sempre, un únic ZIP
(`backup_completo_<data>.zip`) amb les dues bases de dades i **totes** les fotos
juntes i comprimides, a la ubicació que triïs. `Arxiu > Restaurar` s'obre com
un submenú amb dues opcions: **"Restaurar..."**, per triar qualsevol ZIP a mà, i
**"Restaurar des d'una còpia automàtica..."**, que obre directament la carpeta
`backups_auto`. En tots dos casos, si el ZIP triat és una còpia automàtica, es
restaura primer la base de dades i, amb ella ja restaurada, es calcula quines
fotos calen i s'extreuen únicament dels `fotos_backup_<any>.zip` corresponents,
en lloc de bolcar-les totes. Les tres operacions (còpia i totes dues
restauracions) mostren la seva pròpia barra de progrés amb focus.

### Neteja de fotos òrfenes

`Eines > 🧹 Netejar Fotos Escombraries` esborra les fotos de `fotos_recibidas` que ja
no estan referenciades per cap treball, pendent o màquina. En tancar
l'aplicació i abans d'una còpia manual també es neteja `fotos_recibidas` en
silenci, però **només** aquesta opció del menú Eines revisa a més els
`fotos_backup_<any>.zip` i els reescriu sense les fotos òrfenes que poguessin
contenir, per no arrossegar-les indefinidament.

### Temps màxim de conservació de treballs

`Eines > 🗑️ Temps màxim de conservació de treballs…` (només administradors)
demana un nombre i una unitat (anys, mesos o dies) i esborra de l'historial
tots els treballs anteriors a aquesta data, comptant des d'avui. Abans
d'esborrar mostra quants treballs s'eliminaran i entre quines dates, i demana
confirmació.

- Abans d'esborrar es desa una còpia de les dues bases de dades a
  `backups_auto/antes_borrado_trabajos_<data>.zip`, que la rotació de la còpia
  automàtica no elimina.
- També s'esborren les seves fotos (abans, després i col·lecció), excepte les
  que encara faci servir un altre registre. Les fotos no van en aquesta còpia
  prèvia, però continuen als `fotos_backup_<any>.zip` de la còpia automàtica
  fins que es fa servir `Eines > 🧹 Netejar Fotos Escombraries`.
- Els mòbils treuen aquests treballs del seu historial a la sincronització
  següent.
- És un esborrat puntual: no es repeteix sol.

---

## 📁 Estructura del projecte

```
MantPro/
├── main.py                      # Aplicació principal d'escriptori
├── usuarios.py                  # Usuaris, contrasenyes, rols i sessions
├── dialogos_usuarios.py         # Diàlegs PyQt6: inici de sessió i gestió d'usuaris
├── almacen.py                   # Estoc del magatzem: estructura, materials i moviments
├── maquinas.py                  # Arbre de maquinària i el seu historial de treballs
├── idiomas/                     # Traduccions de l'escriptori (ES / EN / EU / CA / GL)
├── requirements.txt             # Dependències de Python
├── logo.png                     # Logotip de l'aplicació
├── README.ca.md                 # Aquest fitxer
├── fotos_recibidas/             # Carpeta d'imatges
├── mantenimiento.db             # Base de dades SQLite (treballs de manteniment)
├── almacen.db                   # Base de dades SQLite (estoc del magatzem, independent)
├── mantenimiento_app/           # Aplicació mòbil Flutter (treballs)
│   ├── lib/main.dart            # Codi principal del mòbil
│   ├── lib/i18n/                # Traduccions del mòbil (ES / EN / EU / CA / GL)
│   ├── pubspec.yaml             # Dependències de Flutter
│   └── android/                 # Configuració d'Android
├── mantpro_stock_app/           # Aplicació mòbil Flutter (estoc del magatzem)
│   ├── lib/modelos.dart         # Models de dades i regla de color de l'estoc
│   ├── lib/pantallas/           # Pantalles: magatzem, article, cerca, per sota del mínim...
│   ├── lib/i18n/                # Traduccions del mòbil (ES / EN / EU / CA / GL)
│   ├── pubspec.yaml             # Dependències de Flutter
│   └── android/                 # Configuració d'Android
├── backups/                     # Còpies manuals completes (BD + fotos)
├── backups_auto/                # Còpies automàtiques en tancar (BD rotativa + fotos per any)
└── docs/                        # Documentació addicional
```

> Les dades (base de dades, fotos i còpies) no viuen necessàriament al costat
> del codi: si no existeix `mantenimiento.db` a la carpeta actual, l'aplicació
> fa servir `~/.local/share/MantPro` a Linux o `%APPDATA%\MantPro` a Windows.

### Base de dades

L'aplicació fa servir SQLite amb les taules següents:

- **`tareas`**: registre de les intervencions fetes (data, descripció,
  etiquetes, fotos, **qui la va fer** (`usuario_id` i `usuario_nombre`) i la
  **màquina vinculada** (`maquina_id`), si en té)
- **`maquinas`**: arbre de maquinària (nom, màquina superior, notes i foto)
- **`pendientes`**: tasques pendents de fer (títol, detalls, prioritat i
  **tècnic assignat**: `asignado_a` i `asignado_nombre`)
- **`usuarios`**: persones que fan servir l'aplicació (usuari, nom, hash de la
  contrasenya, rol i si està actiu)
- **`sesiones`**: testimonis dels mòbils vinculats, amb la seva data de
  caducitat
- **`avisos_recurrentes`**: avisos de manteniment que es repeteixen
  automàticament
- **`dias_especiales`**: festius, vacances i dies marcats al calendari
- **`auditoria`**: historial de qui edita o esborra cada treball, amb data,
  acció i detall
- **`config`**: configuració interna de l'aplicació (logotip, província, etc.)

Les contrasenyes es desen amb **PBKDF2-SHA256** (200.000 iteracions i salt per
usuari), mai en clar. Les taules i columnes noves es creen soles en arrencar,
sense perdre les dades existents.

> 🔐 `mantenimiento.db` conté hashes de contrasenyes i testimonis de sessió.
> És a `.gitignore` per alguna cosa: no la pugis mai al repositori.

L'estoc del magatzem viu a la seva pròpia base de dades, **`almacen.db`**,
separada expressament de la dels treballs:

- **`estanterias`**: nom i si té espai a terra
- **`baldas`**: prestatges de cada prestatgeria, numerats de baix a dalt (el
  prestatge `0` representa l'espai a terra)
- **`secciones`**: subdivisions dins de cada prestatge
- **`materiales`**: codi, nom, descripció, unitat, estoc actual, estoc mínim,
  ubicació (secció) i foto
- **`movimientos`**: històric d'entrades i sortides, amb data, quantitat,
  usuari i motiu

Es crea automàticament en el primer arrencament i s'inclou a les còpies de
seguretat (manuals i automàtiques en tancar l'aplicació) juntament amb
`mantenimiento.db`.

---

## 🤝 Contribuir

Les contribucions són benvingudes! Si vols millorar MantPro:

1. Fes un **fork** del projecte
2. Crea una **branca** per al teu canvi (`git checkout -b feature/LaMevaMillora`)
3. Fes **commit** dels canvis (`git commit -m 'Afegeix LaMevaMillora'`)
4. Fes **push** de la branca (`git push origin feature/LaMevaMillora`)
5. Obre un **Pull Request**

---

## ✅ Fet

- **Gestió d'usuaris**: inici de sessió amb usuari i contrasenya al PC i al
  mòbil, diversos rols per usuari (administrador / tècnic / magatzem), alta i
  baixa lògica d'usuaris, canvi i restabliment de contrasenya.
- **Autoria dels treballs**: cada registre desa qui el va fer. Els registres
  anteriors al sistema d'usuaris queden marcats com a `Histórico`.
- **Sessió persistent al mòbil**: el tècnic inicia sessió una vegada i el
  testimoni queda desat al dispositiu.
- **API autenticada**: tots els punts d'accés de dades exigeixen testimoni; un
  `401` tanca la sessió del mòbil i torna a l'inici de sessió sense perdre els
  registres locals pendents d'enviar.
- **Pendents assignats**: el PC assigna cada treball a un tècnic i el mòbil pot
  filtrar per "Només els meus".
- **Filtre per tècnic** a l'historial i a l'exportació a PDF, CSV i Excel.
- **Auditoria d'edicions**: es registra qui edita o esborra un treball (no
  només qui el va crear), consultable i filtrable per tècnic/acció des de
  "Registre de canvis".
- **Permisos per registre**: un tècnic només pot editar o esborrar els seus
  propis treballs; un administrador en pot gestionar qualsevol i reassignar
  l'autor d'un o diversos registres alhora (selecció múltiple + menú
  contextual).
- **Temes visuals**: mode fosc (per defecte), clar o clàssic a l'estil Windows
  98, seleccionable des del menú "Aparença" i recordat entre sessions.
- **Còpia a demanda amb selecció de destinació**: en generar una còpia de
  seguretat manual es pot triar on desar-la, en lloc d'anar sempre a la
  carpeta `backups` per defecte.
- **Control de l'estoc del magatzem**: estructura configurable de
  prestatgeries, prestatges i seccions (només administradors), fitxa de
  materials amb foto, entrades i sortides amb historial (qualsevol usuari),
  trasllats entre ubicacions registrats a l'historial, selecció múltiple amb
  menú contextual per moure o eliminar en bloc, i una pestanya dedicada als
  materials sense estoc o per sota del mínim. Amb base de dades pròpia
  (`almacen.db`) i aplicació mòbil independent (`mantpro_stock_app`) per
  consultar i moure l'estoc des del telèfon.
- **Sessions de dispositius**: llistar els mòbils vinculats a cada usuari, amb
  el seu model real de dispositiu, i poder revocar una o diverses sessions
  concretes sense haver de desactivar l'usuari sencer.
- **Llistat de maquinària**: arbre de màquines i submàquines amb foto adjunta,
  comptador de treballs per any i mes, i vincle de cada treball (PC o mòbil) a
  la màquina en què s'ha fet, inclòs a les exportacions a PDF, CSV i Excel.
- **Còpia automàtica incremental**: el tancament de l'aplicació ja no torna a
  empaquetar tot l'historial de fotos cada vegada; les bases de dades roten en
  un ZIP i les fotos es reparteixen en ZIP incrementals per any, amb una barra
  de progrés amb focus tant en el tancament com en la còpia i la restauració
  manuals (vegeu [Còpies de seguretat](#-còpies-de-seguretat)).
- **Revertir un treball a pendent**: desfer per error la finalització d'un
  treball, tant des de l'historial del PC com mantenint premut el registre al
  mòbil, amb avís de pèrdua de la màquina vinculada si en tenia i restauració
  automàtica de l'avís recurrent d'origen, si en venia d'un.
- **Restaurar des d'una còpia automàtica**: `Arxiu > Restaurar` s'obre com un
  submenú per triar entre qualsevol còpia manual o anar directament a la
  carpeta de còpies automàtiques en tancar l'aplicació.
- **Recordatori diari d'estoc**: l'aplicació `mantpro_stock_app` avisa cada
  matí a les 8:00 per comprovar la quantitat real de 5 materials del magatzem
  (a l'atzar, diferents cada dia) i permet corregir-la al moment des de la
  mateixa notificació.
- **Tauler amb KPI i gràfics de fiabilitat**: targetes de MTBF i MTTR mitjans
  de tota la planta, i gràfics de rànquing de les màquines amb més avaries i
  d'avaries per mes, dibuixats a mà amb `QPainter` sense dependre de cap
  biblioteca de gràfics externa.
- **Substitució automàtica de la sessió per dispositiu**: si un usuari torna a
  iniciar sessió des d'un mòbil amb què ja tenia una sessió oberta, l'anterior
  s'esborra sola en lloc d'acumular-se al llistat de sessions.
- **Col·lecció de fotos per treball**: a més d'abans i després, qualsevol
  nombre de fotos extra en treballs i pendents, al PC i al mòbil, amb un visor
  a mida completa que passa de l'una a l'altra.
- **Avisos recurrents que no se salten**: un avís endarrerit queda pendent
  (taronja) o endarrerit (vermell) fins que es fa, i el cicle següent es compta
  des de la data real en què es va fer.
- **Exportar l'estoc del magatzem** a PDF, CSV o Excel, complet, per zona, per
  prestatgeria o només els materials per sota del mínim.
- **Temps màxim de conservació de treballs**: esborrat de treballs antics amb
  confirmació i còpia de seguretat prèvia.

## 📄 Llicència

Aquest projecte està sota la **GNU Affero General Public License v3.0 (AGPL-3.0)**.
Consulta el fitxer `LICENSE` per al text complet.

Copyright (C) 2026 AnabasaSoft

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
Copyright (C) 2026 AnabasaSoft

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

<img src="https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/AnabasaSoft.png" alt="Anabasa Software" width="120"/>

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
