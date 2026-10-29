<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-6e7781?style=for-the-badge" alt="English"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Espa%C3%B1ol-6e7781?style=for-the-badge" alt="Español"></a>
  <a href="README.eu.md"><img src="https://img.shields.io/badge/Euskara-6e7781?style=for-the-badge" alt="Euskara"></a>
  <a href="README.ca.md"><img src="https://img.shields.io/badge/Catal%C3%A0-6e7781?style=for-the-badge" alt="Català"></a>
  <a href="README.gl.md"><img src="https://img.shields.io/badge/Galego-6e7781?style=for-the-badge" alt="Galego"></a>
  <a href="README.pt.md"><img src="https://img.shields.io/badge/Portugu%C3%AAs-6e7781?style=for-the-badge" alt="Português"></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/Fran%C3%A7ais-0969da?style=for-the-badge" alt="Français"></a>
</p>

# MantPro

<p align="center">
  <img src="recursos/logo.png" alt="Logo de MantPro" width="200"/>
</p>

<p align="center">
  <strong>GMAO libre et gratuite pour gérer la maintenance préventive et corrective de votre usine, atelier ou flotte, depuis le PC et Android.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Offline--first-✔-success.svg" alt="Offline-first">
  <img src="https://img.shields.io/badge/Sans%20abonnement-100%25%20gratuit-orange.svg" alt="Sans abonnement">
</p>

---

## 🧩 Quel problème résout-elle ?

Dans beaucoup d'ateliers et de petites et moyennes usines, la maintenance se
suit entre des papiers, un tableur Excel partagé et des messages WhatsApp. Ça
fonctionne, jusqu'au jour où quelqu'un a besoin de savoir **ce qui a été fait
sur une machine précise**, par qui, quand et avec quel matériel — et que cette
information est éparpillée à trois endroits différents (ou nulle part).

**MantPro centralise tout cela** : chaque technicien enregistre son
intervention depuis son mobile, sur le moment, avec des photos avant/après si
besoin, et tout est classé sur le PC par machine, par date et par personne,
prêt à être consulté ou exporté en rapport PDF.

## 🎯 Pour qui ?

Pensée pour celles et ceux qui assurent la maintenance au quotidien, pas pour
les services informatiques : techniciens de maintenance, responsables d'usine,
ateliers, PME industrielles et magasiniers qui ont besoin d'un vrai suivi des
machines, des interventions et du stock sans dépendre de tableurs dispersés.

## 🆚 Pourquoi MantPro plutôt qu'une GMAO commerciale ?

- **Libre et gratuite** : code ouvert sous AGPL-3.0, sans limite de
  techniciens, de machines ni d'enregistrements
- **Sans abonnement** : on ne paie ni par utilisateur ni par mois d'utilisation
- **Vos données, sur votre infrastructure** : la base de données reste sur
  votre propre PC ; vous ne dépendez pas d'un service cloud tiers qui existera
  peut-être encore l'an prochain
- **Vraiment hors ligne** : le mobile fonctionne sans connexion à internet ni
  au PC toute la journée, et se synchronise dès qu'il retrouve le réseau
- **Conçue depuis la maintenance elle-même** : les fonctions sont nées de
  besoins réels d'atelier (photos avant/après, lien avec la machine, stock de
  pièces, rappels récurrents...), pas d'une liste générique d'exigences de
  GMAO

## 🎬 Vidéo de démonstration

https://github.com/user-attachments/assets/11572710-e0ba-4f8b-b914-0a959006d4fb

## 📸 Captures d'écran

### Application de bureau

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Tableau de bord" width="45%"/>
  <img src="Capturas/Almacen.png" alt="Gestion du magasin" width="45%"/>
</p>

### Application mobile

<p align="center">
  <img src="Capturas/Dashboard-movil.jpg" alt="Tableau de bord mobile" width="30%"/>
  <img src="Capturas/Almacen-movil.jpg" alt="Magasin mobile" width="30%"/>
  <img src="Capturas/Historial-movil.jpg" alt="Historique mobile" width="30%"/>
</p>

---

## 📋 Sommaire

- [Quel problème résout-elle ?](#-quel-problème-résout-elle-)
- [Pour qui ?](#-pour-qui-)
- [Pourquoi MantPro ?](#-pourquoi-mantpro-plutôt-quune-gmao-commerciale-)
- [Vidéo de démonstration](#-vidéo-de-démonstration)
- [Captures d'écran](#-captures-décran)
- [Téléchargements](#-téléchargements)
- [Fonctionnalités](#-fonctionnalités)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Utilisateurs et accès](#-utilisateurs-et-accès)
- [Machines](#-machines)
- [Stock du magasin](#-stock-du-magasin)
- [Synchronisation PC-mobile](#-synchronisation-pc-mobile)
- [Sauvegardes](#-sauvegardes)
- [Structure du projet](#-structure-du-projet)
- [Contribuer](#-contribuer)
- [Licence](#-licence)
- [Contact](#-contact)

---

## 📦 Téléchargements

Vous pouvez télécharger les versions précompilées depuis [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) :

- **Windows** : exécutable `.exe` pour Windows
- **Linux** :
  - Binaire exécutable pour Linux
  - AppImage portable
  - Également disponible sur l'**AUR** (Arch User Repository)
- **Android** : fichiers `.apk` à installer directement
  - `MantPro.apk` : application des interventions de maintenance
  - `MantProStock.apk` : application de stock du magasin

---

## ✨ Fonctionnalités

### 💻 Application de bureau (PC)

- **👥 Gestion des utilisateurs** : connexion par identifiant et mot de passe, rôles administrateur et technicien, création et désactivation d'utilisateurs et réinitialisation des mots de passe
- **✍️ Auteur des interventions** : chaque intervention enregistre qui l'a réalisée, visible dans l'historique et les rapports
- **🔒 Droits par enregistrement** : un technicien ne peut modifier ou supprimer que ses propres interventions ; un administrateur peut gérer n'importe laquelle, y compris réassigner l'auteur d'un ou plusieurs enregistrements à la fois
- **📋 Audit des modifications** : journal de qui modifie ou supprime chaque intervention (pas seulement de qui l'a créée), consultable et filtrable par technicien et par type d'action dans « Journal des modifications » (administrateurs uniquement)
- **🔐 Sessions des appareils** : liste les mobiles associés à chaque utilisateur, avec le modèle réel, et permet de révoquer une ou plusieurs sessions précises sans désactiver tout l'utilisateur (administrateurs uniquement). En se reconnectant depuis le même appareil, la session précédente est remplacée automatiquement au lieu de s'accumuler
- **📊 Tableau de bord avec KPI et graphiques** : cartes des rappels en attente, des tâches à faire, des enregistrements du mois et du MTBF/MTTR moyens de toute l'usine, ainsi que des graphiques des machines avec le plus de pannes et des pannes par mois, dessinés sans bibliothèque externe
- **🎨 Thèmes visuels** : choisissez entre mode sombre (par défaut), clair ou un style rétro inspiré de Windows 98, dans le menu « Apparence »
- **📅 Calendrier interactif** : visualisez et gérez les tâches de maintenance avec un code couleur (fériés, congés, jours avec tâches)
- **📝 Historique complet** : registre de toutes les interventions réalisées, avec photos avant/après et une **collection de photos** supplémentaire par intervention ; plusieurs enregistrements peuvent être supprimés à la fois
- **📄 Rapports PDF** : génération automatique de rapports professionnels avec logo personnalisable
- **📸 Gestion des images** : stockage et affichage des photos des interventions
- **📱 Synchronisation avec le mobile** : serveur intégré (démarrage automatique) pour se synchroniser avec l'application mobile via QR
- **🔍 Moteur de recherche** : recherche avancée par dates, tags et contenu
- **👤 Filtre par technicien** : filtrez l'historique et les exports (PDF, CSV et Excel) par la personne qui a réalisé l'intervention
- **📦 Sauvegarde et restauration** : sauvegarde manuelle complète (BD + photos) en choisissant où l'enregistrer, sauvegarde automatique incrémentale à la fermeture de l'application (voir [Sauvegardes](#-sauvegardes)) et restauration avec barre de progression, avec le sous-menu `Fichier > ♻️ Restaurer` pour choisir n'importe quelle sauvegarde manuelle ou aller directement aux sauvegardes automatiques
- **🏷️ Système de tags** : classement par étiquettes (Urgent, Électrique, Mécanique, Préventif)
- **🔨 Tâches en attente** : gestion des interventions en attente (créer, terminer, modifier, supprimer) et **assignation à un technicien précis**
- **🚦 Priorité des tâches en attente** : chaque intervention en attente a une priorité (Basse, Moyenne, Haute ou Critique) pour décider laquelle traiter en premier, avec sa couleur dans la liste ; on peut aussi joindre des photos à sa collection
- **↩️ Remettre en attente** : si une intervention a été terminée par erreur, elle peut revenir dans En attente d'un clic depuis l'historique (avec un avertissement si une machine y était associée, car cette information serait perdue), et cela est consigné dans l'audit
- **🔁 Rappels** : rappels de maintenance qui se répètent automatiquement. Si la date passe, ils ne sont pas sautés : ils restent **En attente** (orange) pendant la marge puis **En retard** (rouge) jusqu'à ce qu'ils soient faits, et la date suivante est calculée à partir du jour où l'intervention a réellement été faite
- **📦 Gestion du stock du magasin** : structure configurable de rayonnages, tablettes et sections, fiche article avec photo, entrées/sorties avec historique et alertes de stock sous le minimum
- **📄 Exporter le stock** : bouton « 📄 Exporter » dans l'onglet stock pour générer tout le magasin, une zone ou un rayonnage en PDF, CSV ou Excel, trié par emplacement ; l'onglet du stock sous le minimum a aussi son bouton pour n'exporter que les articles en alerte
- **🗑️ Durée maximale de conservation** : `Outils` permet de supprimer de l'historique les interventions plus anciennes qu'un nombre d'années, de mois ou de jours, avec leurs photos et une sauvegarde préalable (administrateurs uniquement)
- **📥 Importer depuis Excel/CSV** : `Fichier > Importer depuis Excel/CSV…` (administrateurs uniquement) importe machines, articles du magasin, rappels récurrents et utilisateurs depuis un modèle téléchargeable ou depuis votre propre Excel (une feuille ou le classeur entier en une fois), en associant les colonnes automatiquement, avec un aperçu ligne par ligne et une sauvegarde préalable. Les emplacements (zones, rayonnages, tablettes) et machines parentes inexistants sont créés automatiquement, et les utilisateurs reçoivent un mot de passe temporaire à changer à la première connexion
- **🏭 Suivi des machines** : arborescence de machines et sous-machines avec photo jointe, compteur d'interventions par année et par mois et association directe depuis chaque intervention enregistrée ou modifiée (voir [Machines](#-machines))
- **📊 Export** : vers PDF, CSV et Excel, avec filtre facultatif par technicien et indiquant la machine/sous-machine de chaque intervention, le cas échéant

### 📱 Application mobile (Android)

- **🔐 Connexion par utilisateur** : chaque technicien se connecte une fois et la session reste enregistrée sur l'appareil
- **📝 Saisie rapide** : enregistrement des interventions sur le terrain, signées automatiquement avec votre utilisateur
- **📷 Appareil photo intégré** : prenez des photos et annotez-les
- **🖼️ Collection de photos** : en plus des photos avant et après, ajoutez à une intervention ou à une tâche en attente autant de photos que vous voulez (appareil photo ou galerie) ; en touchant une photo, elle s'affiche en plein écran, en passant de l'une à l'autre et en zoomant à deux doigts
- **✏️ Éditeur d'images** : dessinez sur les photos pour marquer les zones importantes
- **🔄 Synchronisation automatique** : envoi automatique des données au PC via QR code
- **💾 Stockage local** : conserve les enregistrements hors ligne jusqu'à la synchronisation
- **📋 Interventions en attente** : consultez et gérez les tâches assignées depuis le PC, avec le filtre **« Seulement les miens »**
- **🔄 Actualisation à l'ouverture** : au démarrage, l'application synchronise en arrière-plan les données de tous les onglets
- **🔁 Synchroniser manuellement** : les onglets En attente, Historique et Rappels ont leur propre bouton pour renvoyer immédiatement ce que le mobile a et que le PC n'a pas encore
- **↩️ Remettre en attente** : par un appui long sur un enregistrement de l'Historique, il peut revenir dans l'onglet En attente s'il a été terminé par erreur
- **🏷️ Tags rapides** : système d'étiquettes rapide avec cases à cocher
- **🔌 Mode hors ligne** : travaillez sans connexion et synchronisez quand vous pouvez
- **⏰ Rappels quotidiens** : notification automatique à 8 h 00 (heure locale) s'il reste des interventions en attente non terminées
- **🧰 Articles utilisés** : ajoutez à l'intervention les articles du magasin que vous avez utilisés, en les recherchant par nom ou code ; ils sont déduits du stock automatiquement à l'enregistrement (voir [Articles utilisés dans une intervention](#-stock-du-magasin))
- **🏭 Associer une machine** : choisissez dans une liste la machine ou sous-machine sur laquelle l'intervention a été faite, aussi bien en créant un enregistrement qu'en modifiant un enregistrement déjà synchronisé de l'historique

### 📦 Application mobile de stock (Android)

Application indépendante (`mantpro_stock_app`), conçue pour consulter et
mouvementer le stock du magasin depuis le mobile sans avoir besoin de
l'application des interventions.

- **🔐 Connexion par utilisateur** : utilise le même système d'utilisateurs et de session que l'application des interventions
- **🗂️ Navigation dans le magasin** : arborescence rayonnages > tablettes > sections, comme sur le PC
- **🔎 Recherche d'articles** : par nom, code, description ou emplacement
- **➕➖ Entrées et sorties** : enregistrez des mouvements de stock depuis le mobile, avec un motif facultatif
- **🔀 Transferts** : déplacer un article d'une section à une autre est consigné dans son historique de mouvements
- **🎨 Alerte visuelle de stock** : quantité en rouge sous le minimum, en vert au-dessus et dans la couleur normale si elle est exactement égale
- **⚠️ Stock sous le minimum** : onglet dédié aux articles en alerte
- **🔄 Actualisation automatique** : l'écran se met à jour tout seul lorsqu'il détecte des modifications, faites sur le mobile comme sur le PC
- **🔌 Mode hors ligne** : sans connexion au PC, l'application n'attend pas : elle consulte les données enregistrées et permet d'enregistrer immédiatement créations, modifications, entrées et sorties, qui sont envoyées toutes seules au PC dès qu'il est de nouveau joignable
- **🔔 Rappel quotidien de contrôle du stock** : notification automatique à 8 h 00 (heure locale) invitant à vérifier la quantité réelle de 5 articles du magasin, choisis au hasard et différents chaque jour ; en la touchant, un écran s'ouvre pour corriger la quantité de chacun sans avoir à les chercher. S'il n'y a aucun article enregistré, aucune notification n'est affichée

---

## 🔧 Prérequis

### Application de bureau

- **Python** : 3.8 ou supérieur
- **Système d'exploitation** : Windows ou Linux
- **Dépendances Python** :
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - xlsxwriter
  - openpyxl
  - sqlite3 (inclus avec Python)

### Application mobile

Valable aussi bien pour `mantenimiento_app` (interventions) que pour `mantpro_stock_app` (stock) :

- **Flutter** : 3.0 ou supérieur
- **Dart SDK** : 2.17 ou supérieur
- **Android** : API Level 21+ (Android 5.0+)

---

## 📥 Installation

### Application de bureau

#### Option 1 : téléchargement précompilé (recommandé)

Téléchargez la version correspondant à votre système depuis [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) :

- **Windows** : téléchargez et lancez le `.exe`
- **Linux** :
  - Téléchargez le binaire exécutable et rendez-le exécutable : `chmod +x mantpro`
  - Ou utilisez l'**AppImage** (sans installation) : `chmod +x MantPro.AppImage && ./MantPro.AppImage`
  - Les paquets **`.deb`** et **`.rpm`** sont signés numériquement avec GPG (voir [Vérifier la signature des paquets](#-vérifier-la-signature-des-paquets-linux))
  - **Arch Linux** : disponible sur l'AUR : `yay -S mantpro` ou `paru -S mantpro`

#### 🔏 Vérifier la signature des paquets (Linux)

Les paquets `.deb` et `.rpm` publiés dans chaque release sont signés avec la clé GPG officielle d'AnabasaSoft. Pour les vérifier avant de les installer :

1. Téléchargez la clé publique du dépôt ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)) dans un fichier (**n'utilisez pas `curl | rpm --import -`** : certaines versions de `rpm` n'acceptent pas de lire la clé depuis l'entrée standard et échouent) :
   ```bash
   curl -sL https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/firma/anabasasoft_public.asc -o /tmp/anabasasoft_public.asc
   ```

2. Importez la clé (une seule fois par ordinateur) :
   ```bash
   # Fedora, openSUSE, RHEL... (paquet .rpm)
   sudo rpm --import /tmp/anabasasoft_public.asc

   # Debian, Ubuntu... (paquet .deb, nécessite dpkg-sig)
   gpg --import /tmp/anabasasoft_public.asc
   ```

3. Vérifiez que la clé a bien été importée :
   ```bash
   rpm -qa 'gpg-pubkey*' --qf '%{name}-%{version}-%{release} --> %{summary}\n' | grep -i anabasasoft
   ```

4. Vérifiez la signature du paquet téléchargé :
   ```bash
   # RPM
   rpm --checksig mantpro-*.rpm

   # DEB
   dpkg-sig --verify mantpro_*.deb
   ```
   Une signature correcte affiche `OK` sur la ligne de la signature (au lieu de `NOKEY` ou `MISSING KEYS`).

Une signature valide confirme que le paquet provient d'AnabasaSoft et qu'il n'a pas été modifié.

#### Option 2 : installation depuis le code source

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/AnabasaSoft/MantPro.git
   cd MantPro
   ```

2. **Créer un environnement virtuel** (recommandé) :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sous Windows : venv\Scripts\activate
   ```

3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Lancer l'application** :
   ```bash
   python main.py
   ```

### Application mobile

#### Option 1 : téléchargement direct (recommandé)

Téléchargez le `.apk` correspondant depuis [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) et installez-le sur votre appareil Android : `MantPro.apk` pour les interventions, `MantProStock.apk` pour le stock du magasin. Ce sont des applications indépendantes : vous pouvez installer l'une, l'autre ou les deux.

**Remarque** : il peut être nécessaire d'activer « Sources inconnues » dans les paramètres de sécurité de l'appareil.

#### Option 2 : compiler depuis le code source

1. **Aller dans le dossier de l'application** (`mantenimiento_app` pour les interventions, `mantpro_stock_app` pour le stock) :
   ```bash
   cd mantenimiento_app
   ```

2. **Installer les dépendances** :
   ```bash
   flutter pub get
   ```

3. **Lancer sur un appareil ou un émulateur** :
   ```bash
   flutter run
   ```

4. **Compiler l'APK (Android)** :
   ```bash
   flutter build apk --release
   ```

---

## 🚀 Utilisation

### Première configuration

#### Application de bureau

1. **Lancer l'application** : exécutez `python main.py` (le serveur de synchronisation démarre tout seul, inutile de le lancer à la main)
2. **Première connexion** : au premier lancement, l'utilisateur `admin` est créé avec le mot de passe `admin`. L'application **oblige à le changer** à la connexion
3. **Créer les utilisateurs** : menu `Outils` > `👥 Gestion des utilisateurs` > ajoutez chaque technicien
4. **Configurer le logo** (facultatif) : menu `Fichier` > `📤 Exporter` > `📄 Options PDF` > `🖼️ Ajouter / Changer le logo`
5. **Enregistrer une intervention** : onglet « 📝 Enregistrer » > remplissez le résumé et les détails > « 💾 ENREGISTRER »
6. **Créer une tâche en attente** : onglet « 🔨 En attente » > groupe « Nouvelle intervention » (Titre + Détails + « Assigner à ») > « Ajouter »

#### Application mobile

1. **Installer l'application** sur votre mobile
2. **Se connecter au PC** :
   - Vérifiez que le PC et le mobile sont sur le même réseau Wi-Fi
   - Sur le PC : menu `Outils` > `📲 Synchroniser l'app (QR)`
   - Sur le mobile : touchez « Associer le PC » et scannez le code
3. **Se connecter** : saisissez l'utilisateur et le mot de passe que l'administrateur vous a créés. La session reste enregistrée : il suffit de le faire une fois
4. **C'est prêt** : vous pouvez désormais enregistrer des interventions depuis le mobile

### Flux de travail type

#### Depuis le PC

1. **Créer et assigner une tâche en attente** :
   - Onglet « 🔨 En attente » > groupe « Nouvelle intervention » > remplissez le Titre et les Détails, choisissez le technicien dans « Assigner à » > « Ajouter »
   - Gérez-la avec les boutons « ✅ Terminer », « ✏️ Modifier », « ❌ Supprimer » ou « 👤 Réassigner »
   - La liste « Voir ceux de » filtre par technicien (inclut « Non assigné »)

2. **Vérifier les interventions terminées** :
   - Les interventions synchronisées depuis le mobile apparaissent automatiquement
   - Consultez les photos (avant/après et collection) et les détails dans l'onglet « 📋 Historique » ou dans le « 📅 Calendrier »
   - La colonne « Réalisé par » indique qui a fait chaque intervention, et la liste au-dessus permet de n'afficher que celles d'une personne

3. **Générer des rapports** :
   - Menu `Fichier` > `📤 Exporter` > `📄 Options PDF` > `📄 Générer le PDF maintenant`
   - Dans la fenêtre, vous pouvez choisir le technicien, et son nom apparaît dans le titre du rapport
   - Ou exportez en `📄 CSV` / `📊 Excel` depuis `Fichier` > `📤 Exporter`

#### Depuis le mobile

1. **Associer au PC et se connecter** (seulement la première fois, ou en cas de changement de réseau) :
   - Touchez « Associer le PC » et scannez le QR affiché par le PC
   - Saisissez votre utilisateur et votre mot de passe
   - Le mobile mémorise l'adresse du PC et votre session pour se synchroniser automatiquement ensuite

2. **Enregistrer une intervention** :
   - Touchez « Nouveau » ou sélectionnez une intervention en attente déjà synchronisée depuis le PC
   - Avec le filtre « Seulement les miens », vous ne voyez que celles qui vous sont assignées
   - Remplissez le titre et les détails
   - Prenez la photo « avant » et, si vous voulez, la photo « après » avec l'appareil photo ; si besoin, ajoutez-en d'autres à la collection
   - Dessinez ou annotez la photo si nécessaire
   - Sélectionnez les tags adaptés
   - Enregistrez

3. **Synchroniser** :
   - À l'ouverture de l'application, tout se synchronise en arrière-plan (un indicateur apparaît dans la barre du haut)
   - Vous pouvez aussi forcer la synchronisation en tirant la liste vers le bas ou avec l'icône de synchronisation
   - Les enregistrements sont envoyés au PC et retirés du mobile une fois l'envoi confirmé
   - Tout fonctionne sans connexion : ce qui est en attente reste enregistré et part dès qu'il y a du réseau

---

## 👥 Utilisateurs et accès

### Rôles

Un même utilisateur peut avoir **un ou plusieurs rôles à la fois** (par
exemple technicien et magasin). Rôles disponibles :

| Rôle | Ce qu'il peut faire |
|------|---------------------|
| **Administrateur** | Tout ce que font le technicien et le magasin, plus créer et désactiver des utilisateurs, changer les rôles, réinitialiser les mots de passe, modifier ou supprimer **n'importe quel** enregistrement de l'historique, réassigner l'auteur d'un ou plusieurs enregistrements à la fois et consulter le journal d'audit des modifications |
| **Technicien** | Enregistrer des interventions, terminer les tâches en attente et les rappels, modifier ou supprimer **uniquement ses propres** enregistrements de l'historique et changer son propre mot de passe |
| **Magasin** | Créer ou modifier des articles et enregistrer des entrées/sorties de stock depuis l'application **MantPro Stock** |

Il doit toujours y avoir **au moins un administrateur actif** : l'application
empêche de retirer le rôle ou de désactiver le dernier qui reste.

> Dans l'application de bureau, n'importe quel utilisateur (quel que soit son
> rôle) peut enregistrer des mouvements de stock ; le rôle **Magasin** est ce
> qui autorise cette même gestion (créations, modifications et mouvements)
> depuis le mobile.

### Gestion depuis le PC

- **Création** : `Outils` > `👥 Gestion des utilisateurs` > remplissez
  identifiant, nom, mot de passe et rôle > « ➕ Ajouter ». Si vous laissez
  cochée « Exiger le changement à la connexion », la personne devra définir
  son propre mot de passe à la première connexion.
- **Désactivation** : elle est **logique** (l'utilisateur devient inactif). Il
  n'est jamais supprimé, afin de ne pas perdre l'auteur des interventions
  qu'il a déjà réalisées.
- **Réinitialiser le mot de passe** : utile quand quelqu'un l'oublie. En le
  changeant, toutes les sessions mobiles ouvertes de cette personne sont
  fermées automatiquement.
- **Changer son propre mot de passe** : `Outils` > `🔑 Changer mon mot de passe`.

### Sessions des appareils

`Outils` > `🔐 Sessions des appareils` (administrateurs uniquement) liste
toutes les sessions mobiles ouvertes de tous les utilisateurs, avec le modèle
de l'appareil, sa date d'ouverture, sa date d'expiration et si elle est
toujours active ou déjà expirée. On peut sélectionner une ou plusieurs lignes
et les révoquer, ce qui ferme la session de ce mobile sans devoir désactiver
tout l'utilisateur (ce qui fermerait *tous* ses appareils d'un coup).

Si un utilisateur se reconnecte depuis un appareil où il avait déjà une
session ouverte (même fabricant et même modèle), l'ancienne session de cet
appareil est supprimée automatiquement lors de la création de la nouvelle, au
lieu de s'accumuler dans la liste.

### Auteur des interventions

Chaque enregistrement conserve le technicien qui l'a réalisé, qu'il ait été
créé sur le PC ou envoyé depuis le mobile. Les enregistrements antérieurs à la
mise en place du système d'utilisateurs sont marqués **`Histórico`**.

Sur le mobile, l'attribution est toujours décidée **par le serveur** à partir
du jeton de session, jamais d'après une donnée envoyée par l'application. Un
appareil ne peut pas signer des interventions au nom d'une autre personne.

Depuis le PC, un technicien ne peut modifier ou supprimer que ses propres
enregistrements de l'historique ; un administrateur peut le faire avec
n'importe lequel. En faisant un clic droit sur une ou plusieurs lignes de
l'historique (sélection multiple avec Ctrl/Maj), un administrateur peut aussi
**réassigner l'auteur** en bloc, et chaque changement est consigné dans le
journal d'audit.

### Journal des modifications (audit)

Chaque fois qu'une intervention est modifiée ou supprimée, on enregistre qui
l'a fait, quand et ce qui a changé. Les administrateurs peuvent le consulter
dans `Outils` > `📋 Journal des modifications`, avec des filtres par
technicien et par type d'action (modifier/supprimer).

### Session sur le mobile

Le technicien se connecte une fois et le jeton reste enregistré sur
l'appareil. La session se ferme toute seule si l'administrateur désactive
l'utilisateur ou réinitialise son mot de passe ; dans ce cas, l'application
revient à l'écran de connexion **sans perdre les enregistrements encore en
attente d'envoi**.

---

## 🏭 Machines

> Gestion disponible dans l'application de bureau, avec l'association à la
> machine également sélectionnable depuis le mobile lors de l'enregistrement
> ou de la modification d'une intervention.

Onglet « 🏭 Machines » du PC, conçu pour suivre les pannes et les
interventions de chaque équipement dans le temps.

- **🌳 Arborescence de machines** : les machines peuvent avoir des
  sous-machines (par exemple, une ligne avec plusieurs équipements), formant
  une hiérarchie aussi profonde que nécessaire
- **📅 Interventions classées par année et par mois** : en dépliant une
  machine apparaissent les années avec interventions et, en dépliant une
  année, les mois ; chaque niveau affiche un compteur du nombre
  d'interventions, avec un chargement à la demande pour ne pas ralentir
  l'arborescence
- **🖱️ Accès direct à l'intervention** : un double-clic sur une intervention
  de l'arborescence ouvre directement sa fiche de modification
- **📸 Photo de la machine** : chaque machine ou sous-machine peut avoir une
  photo jointe, visible dans un cadre à côté de l'arborescence en la
  sélectionnant
- **🔗 Association depuis chaque intervention** : en enregistrant une nouvelle
  intervention (PC ou mobile) ou en modifiant une intervention existante, on
  peut choisir à quelle machine/sous-machine elle appartient
- **📊 Dans les exports** : la machine ou sous-machine associée apparaît comme
  colonne supplémentaire dans les exports PDF, CSV et Excel

---

## 📦 Stock du magasin

> Gestion complète depuis l'application de bureau, avec consultation et
> mouvements également disponibles depuis le mobile (`mantpro_stock_app`).
> Elle utilise sa propre base de données (`almacen.db`), indépendante de
> celle des interventions de maintenance.

### Structure du magasin

Le magasin est organisé en trois niveaux, inspirés des conventions
habituelles d'adressage des magasins :

```
Rayonnage → Tablette → Section
```

- En créant un rayonnage, on définit le **nombre de tablettes**, le **nombre
  de sections par tablette** (0 = sans sections prédéfinies, qu'on peut
  ajouter ensuite) et s'il possède un **espace au sol** sous la tablette
  inférieure, traité comme une tablette spéciale (« Sol »)
- Les tablettes sont numérotées de bas en haut à partir de 1, pour pouvoir en
  ajouter de nouvelles sans renuméroter les existantes
- On ne peut pas supprimer un rayonnage, une tablette ou une section tant
  qu'ils contiennent des articles

La structure se gère avec le bouton **« ⚙️ Configurer le magasin »** de
l'onglet « 📦 Stock du magasin », visible **uniquement pour les
administrateurs**.

### Articles

- Création et modification avec code (facultatif), nom, description, unité,
  stock minimum, emplacement (rayonnage / tablette / section) et **photo
  jointe**
- Recherche par **nom, code, description ou emplacement**
- Le stock est mis en évidence en **rouge** sous le minimum, en **vert**
  au-dessus et dans la couleur normale s'il est exactement égal au minimum,
  aussi bien sur le PC que sur le mobile
- En sélectionnant plusieurs articles à la fois (Ctrl/Maj + clic droit) sur
  le PC, on peut **les changer d'emplacement** ou **les supprimer** en bloc

### Entrées, sorties et transferts

- **N'importe quel utilisateur** peut enregistrer des entrées et des sorties
  de stock ; seule la configuration de la structure du magasin est réservée
  aux administrateurs
- Chaque mouvement est enregistré avec la date, la quantité, l'utilisateur et
  un motif facultatif, visible dans l'historique de chaque article
- Les sorties enregistrées manuellement (PC ou `mantpro_stock_app`) ne peuvent
  pas rendre le stock négatif
- Changer un article d'emplacement est aussi consigné dans son historique,
  comme un mouvement de type **transfert** (de quelle section vers quelle
  section)

### Articles utilisés dans une intervention (MantPro)

En terminant une intervention depuis l'application **MantPro** (mobile), on
peut ajouter les articles utilisés, en les recherchant par nom ou code et en
indiquant la quantité. À l'enregistrement de l'intervention, ces articles sont
automatiquement déduits du magasin, avec le motif « Utilisé pour
l'intervention : ... » pour assurer la traçabilité.

Contrairement aux sorties manuelles, **cette déduction peut rendre le stock
négatif** : l'article a déjà été physiquement utilisé, même s'il n'y avait pas
assez de stock enregistré, donc bloquer le mouvement n'aurait pas de sens. Le
stock négatif apparaît aussi bien sur le PC que dans `mantpro_stock_app` et
sert d'avertissement : il faut vérifier et réapprovisionner cet article au
plus vite.

### Alertes de stock sous le minimum

L'onglet **« ⚠️ Stock sous le minimum »** affiche, dans une vue séparée, les
articles en rupture ou sous le minimum défini. Le titre de l'onglet indique
lui-même combien d'articles sont en alerte, et de là on peut aller
directement à l'article dans « Stock du magasin », enregistrer une entrée sans
changer d'onglet ou exporter la liste avec le bouton « 📄 Exporter ».

### Exporter le stock

Dans l'onglet **« 📦 Stock du magasin »** du PC, le bouton **« 📄 Exporter »**
ouvre une fenêtre pour choisir le **format** (PDF, CSV ou Excel) et **quoi
exporter** : tout le magasin, une zone ou un seul rayonnage. La liste est
triée par emplacement, pour parcourir le magasin avec elle en main ; le PDF et
l'Excel indiquent aussi la date, le nombre d'articles et combien sont sous le
minimum (en rouge). Le tableau de stock lui-même s'affiche aussi trié par
emplacement par défaut (Rayonnage 1, 2… 10).

---

## 🔄 Synchronisation PC-mobile

### Fonctionnement

MantPro utilise un système de synchronisation basé sur :

1. **Un serveur Flask** intégré à l'application de bureau
2. **Des QR codes** pour une connexion rapide et sûre
3. **Une API REST authentifiée par jeton** : tous les endpoints de données
   exigent une session valide ; si le jeton n'est plus valide, le serveur
   répond `401` et le mobile revient à l'écran de connexion
4. **Le Wi-Fi local**, sans besoin d'internet
5. **Une synchronisation complète à l'ouverture de l'application**, en
   arrière-plan et sans bloquer l'interface

> ⚠️ Le trafic passe en **HTTP sur le réseau local**. Le système
> d'utilisateurs apporte de la traçabilité (savoir qui a fait chaque
> intervention), pas une protection contre quelqu'un ayant accès à ce même
> réseau.

### Configuration réseau

Pour que la synchronisation fonctionne :

- ✅ Le PC et le mobile doivent être sur le **même réseau Wi-Fi**
- ✅ Le **pare-feu** doit autoriser les connexions sur le port 5000 (ou celui
  configuré)
- ✅ Sous Windows, il peut être nécessaire de créer une exception dans le
  pare-feu

### Dépannage

**Le mobile ne se connecte pas au PC :**
- Vérifiez que les deux appareils sont sur le même réseau
- Vérifiez que le serveur est actif sur le PC (icône verte)
- Essayez de désactiver temporairement le pare-feu du PC
- Générez de nouveau le QR code et scannez-le à nouveau

**Je ne peux pas me connecter depuis le mobile :**
- Vérifiez que MantPro est ouvert sur le PC : c'est lui qui valide la connexion
- Confirmez l'utilisateur et le mot de passe avec l'administrateur ; il peut le réinitialiser
- Si le PC a changé d'IP, scannez de nouveau le QR depuis l'écran de connexion lui-même (« Associer un autre PC »)

**L'application m'a renvoyé à l'écran de connexion :**
- C'est normal si l'administrateur a réinitialisé votre mot de passe ou désactivé votre utilisateur
- Vos enregistrements non envoyés **ne sont pas perdus** : reconnectez-vous et ils seront synchronisés

**J'ai oublié le mot de passe administrateur :**
- Un autre administrateur peut le réinitialiser dans `Outils` > `👥 Gestion des utilisateurs`
- S'il n'y a aucun autre administrateur, il faut le réinitialiser directement
  dans la table `usuarios` de la base de données

**Les photos ne se synchronisent pas :**
- Vérifiez qu'il y a assez d'espace disque sur le PC
- Vérifiez les droits du dossier `fotos_recibidas`
- Vérifiez que la photo a bien été enregistrée sur le mobile

**Je ne reçois pas la notification quotidienne des rappels en attente (Android) :**
- Vérifiez que l'autorisation des notifications est accordée : `Paramètres → Applications → MantPro → Notifications`
- Chez des fabricants comme **OPPO/Realme (ColorOS), Xiaomi (MIUI) ou Huawei**, le système peut supprimer l'alarme programmée même avec l'autorisation accordée. Il faut en plus :
  - `Paramètres → Batterie → Utilisation de la batterie par application → MantPro` → choisir **« Aucune restriction »**
  - `Paramètres → Batterie → Démarrage automatique` → **activer** MantPro
- La notification est réévaluée à chaque ouverture du Tableau de bord ; si vous venez de marquer une intervention comme terminée, rouvrez-le pour qu'elle soit annulée ou reprogrammée correctement.

**Je ne reçois pas la notification quotidienne de contrôle du stock (MantPro Stock) :**
- Les mêmes vérifications que pour MantPro s'appliquent (autorisation des notifications et exclusion de l'optimisation de la batterie, voir ci-dessus)
- Si le magasin n'a aucun article enregistré, aucune notification n'est affichée : c'est le comportement attendu
- Elle est réévaluée à chaque synchronisation de l'application avec le PC (à l'ouverture et toutes les 25 secondes tant qu'elle est ouverte)

### 🔒 Remarque sur la sécurité

La synchronisation passe en HTTP sur le réseau local. Le système
d'utilisateurs est pensé pour la **traçabilité** (savoir qui a fait chaque
intervention), pas comme une barrière contre quelqu'un ayant accès à ce même
réseau. Si un jour le serveur est exposé en dehors du réseau local, le trafic
doit être chiffré (VPN ou tunnel HTTPS).

---

## 💾 Sauvegardes

MantPro distingue deux types de sauvegarde, pensés pour des moments
différents :

### Sauvegarde automatique (à la fermeture de l'application)

À chaque fermeture du programme, une sauvegarde rapide est faite en
arrière-plan, sans intervention, conçue pour rester légère même au fil des
années :

- **Bases de données** : `mantenimiento.db` et `almacen.db` sont regroupées
  entières dans un ZIP (`auto_backup_db_<date>.zip`) à chaque fois, en
  rotation, en ne gardant que les 3 plus récents.
- **Photos** : au lieu de compresser tout l'historique des photos à chaque
  fermeture, des ZIP incrémentaux par année sont conservés
  (`fotos_backup_<année>.zip`) : chaque fermeture n'ajoute au ZIP de l'année
  correspondante que les photos qui n'y figuraient pas encore, sans toucher
  ni recompresser celles des années précédentes. Ainsi, le temps de fermeture
  n'augmente pas avec la durée d'utilisation de l'application.

Pendant cette sauvegarde, une fenêtre avec une barre de progression garde le
focus, et la fermeture réelle de l'application attend qu'elle soit terminée.

### Sauvegarde manuelle (menu Fichier)

`Fichier > 💾 Sauvegarde` génère toujours, comme avant, un seul ZIP
(`backup_completo_<date>.zip`) avec les deux bases de données et **toutes**
les photos ensemble et compressées, à l'endroit de votre choix.
`Fichier > ♻️ Restaurer` ouvre un sous-menu avec deux options :
**« Restaurer... »**, pour choisir manuellement n'importe quel ZIP, et
**« Restaurer depuis une sauvegarde automatique... »**, qui ouvre directement
le dossier `backups_auto`. Dans les deux cas, si le ZIP choisi est une
sauvegarde automatique, la base de données est restaurée d'abord puis, une
fois restaurée, on calcule quelles photos sont nécessaires et on ne les
extrait que des `fotos_backup_<année>.zip` correspondants, au lieu de tout
déverser. Les trois opérations (sauvegarde et les deux restaurations)
affichent leur propre barre de progression avec focus.

### Nettoyage des photos orphelines

`Outils > 🧹 Nettoyer les photos inutiles` supprime les photos de
`fotos_recibidas` qui ne sont plus référencées par aucune intervention, tâche
en attente ou machine. À la fermeture de l'application et avant une
sauvegarde manuelle, `fotos_recibidas` est aussi nettoyé en silence, mais
**seule** cette option du menu Outils vérifie aussi les
`fotos_backup_<année>.zip` et les réécrit sans les photos orphelines qu'ils
pourraient contenir, pour ne pas les traîner indéfiniment.

### Durée maximale de conservation des interventions

`Outils > 🗑️ Durée maximale de conservation des interventions…`
(administrateurs uniquement) demande un nombre et une unité (années, mois ou
jours) et supprime de l'historique toutes les interventions antérieures à
cette date, comptée à partir d'aujourd'hui. Avant de supprimer, elle indique
combien d'interventions seront supprimées et entre quelles dates, et demande
une confirmation.

- Avant la suppression, une copie des deux bases de données est enregistrée
  dans `backups_auto/antes_borrado_trabajos_<date>.zip`, que la rotation de la
  sauvegarde automatique ne supprime pas.
- Leurs photos sont aussi supprimées (avant, après et collection), sauf
  celles encore utilisées par un autre enregistrement. Les photos n'entrent
  pas dans cette copie préalable, mais restent dans les
  `fotos_backup_<année>.zip` de la sauvegarde automatique jusqu'à ce qu'on
  utilise `Outils > 🧹 Nettoyer les photos inutiles`.
- Les mobiles retirent ces interventions de leur historique à la
  synchronisation suivante.
- C'est une suppression ponctuelle : elle ne se répète pas toute seule.

---

## 📁 Structure du projet

```
MantPro/
├── main.py                      # Point d'entrée (python main.py)
├── mantpro/                     # Code de l'application de bureau
│   ├── version.py               # Version (définie par la CI à partir du tag)
│   ├── nucleo/                  # Données et logique, sans interface
│   │   ├── usuarios.py          # Utilisateurs, mots de passe, rôles et sessions
│   │   ├── almacen.py           # Stock du magasin : structure, articles et mouvements
│   │   ├── maquinas.py          # Arborescence des machines et historique de leurs interventions
│   │   ├── basedatos.py         # Base de données des interventions
│   │   └── importar.py          # Import depuis Excel/CSV
│   ├── interfaz/                # Fenêtres PyQt6
│   │   ├── arranque.py          # Démarrage : instance unique et connexion
│   │   ├── app.py               # Application de bureau principale
│   │   ├── servidor.py          # Serveur de synchronisation avec les mobiles
│   │   ├── pestanas/            # Un par onglet : tableau de bord, calendrier, stock...
│   │   ├── acciones/            # Actions des menus : sauvegardes, export, import, utilisateurs
│   │   ├── dialogos/            # Dialogues (connexion et gestion des utilisateurs incluses)
│   │   └── widgets/             # Photos et graphiques
│   └── idiomas/                 # Traductions du bureau (ES / EN / EU / CA / GL / PT / FR)
├── recursos/                    # Icônes et logos
├── herramientas/                # Scripts du projet (verificar_idiomas.py...)
├── empaquetado/                 # Installateur Windows (Inno Setup)
├── requirements.txt             # Dépendances Python
├── README.fr.md                 # Ce fichier
├── fotos_recibidas/             # Dossier des images
├── mantenimiento.db             # Base de données SQLite (interventions de maintenance)
├── almacen.db                   # Base de données SQLite (stock du magasin, indépendante)
├── mantenimiento_app/           # Application mobile Flutter (interventions)
│   ├── lib/main.dart            # Code principal du mobile
│   ├── lib/i18n/                # Traductions du mobile (ES / EN / EU / CA / GL / PT / FR)
│   ├── pubspec.yaml             # Dépendances Flutter
│   └── android/                 # Configuration Android
├── mantpro_stock_app/           # Application mobile Flutter (stock du magasin)
│   ├── lib/modelos.dart         # Modèles de données et règle de couleur du stock
│   ├── lib/pantallas/           # Écrans : magasin, article, recherche, sous le minimum...
│   ├── lib/i18n/                # Traductions du mobile (ES / EN / EU / CA / GL / PT / FR)
│   ├── pubspec.yaml             # Dépendances Flutter
│   └── android/                 # Configuration Android
├── backups/                     # Sauvegardes manuelles complètes (BD + photos)
├── backups_auto/                # Sauvegardes automatiques à la fermeture (BD en rotation + photos par année)
└── docs/                        # Documentation supplémentaire
```

> Les données (base de données, photos et sauvegardes) ne sont pas
> forcément à côté du code : s'il n'existe pas de `mantenimiento.db` dans le
> dossier courant, l'application utilise `~/.local/share/MantPro` sous Linux
> ou `%APPDATA%\MantPro` sous Windows.

### Base de données

L'application utilise SQLite avec les tables suivantes :

- **`tareas`** : registre des interventions réalisées (date, description,
  tags, photos, **qui l'a réalisée** (`usuario_id` et `usuario_nombre`) et la
  **machine associée** (`maquina_id`), le cas échéant)
- **`maquinas`** : arborescence des machines (nom, machine parente, notes et
  photo)
- **`pendientes`** : tâches en attente (titre, détails, priorité et
  **technicien assigné** : `asignado_a` et `asignado_nombre`)
- **`usuarios`** : personnes qui utilisent l'application (identifiant, nom,
  hash du mot de passe, rôle et si elle est active)
- **`sesiones`** : jetons des mobiles associés, avec leur date d'expiration
- **`avisos_recurrentes`** : rappels de maintenance qui se répètent
  automatiquement
- **`dias_especiales`** : fériés, congés et jours marqués dans le calendrier
- **`auditoria`** : historique de qui modifie ou supprime chaque intervention,
  avec date, action et détail
- **`config`** : configuration interne de l'application (logo, province, etc.)

Les mots de passe sont stockés avec **PBKDF2-SHA256** (200 000 itérations et
un sel par utilisateur), jamais en clair. Les nouvelles tables et colonnes
sont créées toutes seules au démarrage, sans perdre les données existantes.

> 🔐 `mantenimiento.db` contient des hashs de mots de passe et des jetons de
> session. Il est dans le `.gitignore` pour une raison : ne l'envoyez jamais
> dans le dépôt.

Le stock du magasin utilise sa propre base de données, **`almacen.db`**,
volontairement séparée de celle des interventions :

- **`estanterias`** : nom et présence d'un espace au sol
- **`baldas`** : tablettes de chaque rayonnage, numérotées de bas en haut (la
  tablette `0` représente l'espace au sol)
- **`secciones`** : subdivisions de chaque tablette
- **`materiales`** : code, nom, description, unité, stock actuel, stock
  minimum, emplacement (section) et photo
- **`movimientos`** : historique des entrées et sorties, avec date, quantité,
  utilisateur et motif

Elle est créée automatiquement au premier lancement et fait partie des
sauvegardes (manuelles et automatiques à la fermeture) avec
`mantenimiento.db`.

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! Si vous voulez améliorer MantPro :

1. Faites un **fork** du projet
2. Créez une **branche** pour votre modification (`git checkout -b feature/MonAmelioration`)
3. Faites un **commit** de vos modifications (`git commit -m 'Ajoute MonAmelioration'`)
4. Faites un **push** de la branche (`git push origin feature/MonAmelioration`)
5. Ouvrez une **Pull Request**

---

## ✅ Réalisé

- **Gestion des utilisateurs** : connexion par identifiant et mot de passe sur
  le PC et le mobile, plusieurs rôles par utilisateur (administrateur /
  technicien / magasin), création et désactivation logique des utilisateurs,
  changement et réinitialisation du mot de passe.
- **Auteur des interventions** : chaque enregistrement conserve qui l'a
  réalisé. Les enregistrements antérieurs au système d'utilisateurs sont
  marqués `Histórico`.
- **Session persistante sur le mobile** : le technicien se connecte une fois
  et le jeton reste enregistré sur l'appareil.
- **API authentifiée** : tous les endpoints de données exigent un jeton ; un
  `401` ferme la session mobile et revient à la connexion sans perdre les
  enregistrements locaux en attente d'envoi.
- **Tâches en attente assignées** : le PC assigne chaque intervention à un
  technicien et le mobile peut filtrer par « Seulement les miens ».
- **Filtre par technicien** dans l'historique et dans l'export PDF, CSV et
  Excel.
- **Audit des modifications** : on enregistre qui modifie ou supprime une
  intervention (pas seulement qui l'a créée), consultable et filtrable par
  technicien/action dans « Journal des modifications ».
- **Droits par enregistrement** : un technicien ne peut modifier ou supprimer
  que ses propres interventions ; un administrateur peut gérer n'importe
  laquelle et réassigner l'auteur d'un ou plusieurs enregistrements à la fois
  (sélection multiple + menu contextuel).
- **Thèmes visuels** : mode sombre (par défaut), clair ou classique façon
  Windows 98, au choix dans le menu « Apparence » et mémorisé d'une session à
  l'autre.
- **Sauvegarde à la demande avec choix de la destination** : en générant une
  sauvegarde manuelle, on peut choisir où l'enregistrer, au lieu du dossier
  `backups` par défaut.
- **Gestion du stock du magasin** : structure configurable de rayonnages,
  tablettes et sections (administrateurs uniquement), fiche article avec
  photo, entrées et sorties avec historique (tout utilisateur), transferts
  entre emplacements consignés dans l'historique, sélection multiple avec
  menu contextuel pour déplacer ou supprimer en bloc et un onglet dédié aux
  articles en rupture ou sous le minimum. Avec sa propre base de données
  (`almacen.db`) et une application mobile indépendante
  (`mantpro_stock_app`) pour consulter et mouvementer le stock depuis le
  téléphone.
- **Sessions des appareils** : lister les mobiles associés à chaque
  utilisateur, avec le modèle réel de l'appareil, et pouvoir révoquer une ou
  plusieurs sessions précises sans désactiver tout l'utilisateur.
- **Liste des machines** : arborescence de machines et sous-machines avec
  photo jointe, compteur d'interventions par année et par mois et association
  de chaque intervention (PC ou mobile) à la machine concernée, incluse dans
  les exports PDF, CSV et Excel.
- **Sauvegarde automatique incrémentale** : la fermeture de l'application ne
  recompresse plus tout l'historique des photos à chaque fois ; les bases de
  données tournent dans un ZIP et les photos sont dans des ZIP incrémentaux
  par année, avec une barre de progression avec focus aussi bien à la
  fermeture que pour la sauvegarde et la restauration manuelles (voir
  [Sauvegardes](#-sauvegardes)).
- **Remettre une intervention en attente** : annuler une fin d'intervention
  faite par erreur, depuis l'historique du PC comme par un appui long sur
  l'enregistrement dans le mobile, avec avertissement de perte de la machine
  associée le cas échéant, et restauration automatique du rappel récurrent
  d'origine s'il en provient.
- **Restaurer depuis une sauvegarde automatique** : `Fichier > ♻️ Restaurer`
  ouvre un sous-menu pour choisir n'importe quelle sauvegarde manuelle ou
  aller directement au dossier des sauvegardes automatiques faites à la
  fermeture.
- **Rappel quotidien du stock** : l'application `mantpro_stock_app` prévient
  chaque matin à 8 h 00 de vérifier la quantité réelle de 5 articles du
  magasin (au hasard, différents chaque jour) et permet de la corriger
  immédiatement depuis la notification.
- **Tableau de bord avec KPI et graphiques de fiabilité** : cartes du MTBF et
  du MTTR moyens de toute l'usine et graphiques du classement des machines
  avec le plus de pannes et des pannes par mois, dessinés à la main avec
  `QPainter` sans aucune bibliothèque de graphiques externe.
- **Remplacement automatique de la session par appareil** : si un
  utilisateur se reconnecte depuis un mobile où il avait déjà une session
  ouverte, l'ancienne est supprimée toute seule au lieu de s'accumuler dans la
  liste des sessions.
- **Collection de photos par intervention** : en plus de l'avant et de
  l'après, autant de photos supplémentaires que voulu dans les interventions
  et les tâches en attente, sur le PC et le mobile, avec une visionneuse en
  taille réelle qui passe de l'une à l'autre.
- **Rappels récurrents qui ne sont pas sautés** : un rappel en retard reste
  en attente (orange) ou en retard (rouge) jusqu'à ce qu'il soit fait, et le
  cycle suivant est calculé à partir de la date où il a réellement été fait.
- **Exporter le stock du magasin** en PDF, CSV ou Excel, en entier, par zone,
  par rayonnage ou seulement les articles sous le minimum.
- **Durée maximale de conservation des interventions** : suppression des
  anciennes interventions avec confirmation et sauvegarde préalable.
- **Importer depuis Excel/CSV** : machines, articles du magasin, rappels
  récurrents et utilisateurs, avec modèle, association des colonnes, aperçu
  ligne par ligne et sauvegarde préalable.

## 📄 Licence

Ce projet est sous **GNU Affero General Public License v3.0 (AGPL-3.0)**.
Consultez le fichier `LICENSE` pour le texte complet.

Copyright (C) 2026 AnabasaSoft

### Ce que cela signifie en pratique

- ✅ Vous pouvez **utiliser** MantPro librement, y compris dans votre entreprise et à des fins commerciales
- ✅ Vous pouvez **étudier, modifier et redistribuer** le code
- ⚠️ Si vous distribuez une version modifiée, vous devez la publier **aussi sous AGPL-3.0**
- ⚠️ Si vous proposez MantPro (ou un dérivé) **comme service via un réseau**,
  vous devez mettre le code source à disposition de ses utilisateurs, même si
  vous ne distribuez aucun exécutable. C'est la principale différence avec la
  GPL v3
- ⚠️ Vous devez conserver les mentions de copyright et de licence

### Avis de licence

```
MantPro - Système de maintenance préventive
Copyright (C) 2026 AnabasaSoft

Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou le
modifier selon les termes de la Licence Publique Générale Affero GNU, telle
que publiée par la Free Software Foundation, soit la version 3 de la
Licence, soit (à votre choix) toute version ultérieure.

Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS
AUCUNE GARANTIE ; sans même la garantie implicite de QUALITÉ MARCHANDE ou
D'ADÉQUATION À UN USAGE PARTICULIER. Consultez la Licence Publique Générale
Affero GNU pour plus de détails.

Vous devriez avoir reçu une copie de la Licence Publique Générale Affero GNU
avec ce programme. Sinon, consultez <https://www.gnu.org/licenses/>.
```

> **Remarque sur les licences commerciales** : AnabasaSoft est l'unique
> titulaire du copyright de MantPro et peut donc proposer le même code sous
> des conditions différentes de l'AGPL. Si vous avez besoin d'intégrer MantPro
> dans un produit propriétaire, contactez-nous.

---

## 📧 Contact

**AnabasaSoft**

- 📧 E-mail : [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com)
- 🌐 GitHub : [github.com/AnabasaSoft](https://github.com/AnabasaSoft)
- 💼 Projet : [github.com/AnabasaSoft/MantPro](https://github.com/AnabasaSoft/MantPro)

---

## 🙏 Remerciements

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) : framework d'interface graphique multiplateforme pour l'application de bureau
- [Flutter](https://flutter.dev/) : SDK des applications mobiles
- [ReportLab](https://www.reportlab.com/) : génération des rapports PDF
- [SQLite](https://www.sqlite.org/) : base de données embarquée
- [Flask](https://flask.palletsprojects.com/) : micro-framework web du serveur de synchronisation
- La communauté open source, pour son soutien et ses contributions

---

<div align="center">

<img src="https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/recursos/AnabasaSoft.png" alt="Anabasa Software" width="120"/>

**Développé avec ❤️ par [Anabasa Software](https://anabasasoft.github.io)**

📧 E-mail : [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com) • 🌐 Portfolio : [anabasasoft.github.io](https://anabasasoft.github.io)

⭐ Si ce projet vous plaît, donnez-lui une étoile sur GitHub

</div>

<div align="center">
  <br/>
  <p><code>>_ sudo buy-me-a-coffee --theme=dark --force</code></p>
  <a href="https://www.buymeacoffee.com/danitxu" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-black.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important; box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;">
  </a>
  <br/>
</div>
