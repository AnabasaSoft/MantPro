<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-6e7781?style=for-the-badge" alt="English"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Espa%C3%B1ol-6e7781?style=for-the-badge" alt="Español"></a>
  <a href="README.eu.md"><img src="https://img.shields.io/badge/Euskara-6e7781?style=for-the-badge" alt="Euskara"></a>
  <a href="README.ca.md"><img src="https://img.shields.io/badge/Catal%C3%A0-6e7781?style=for-the-badge" alt="Català"></a>
  <a href="README.gl.md"><img src="https://img.shields.io/badge/Galego-6e7781?style=for-the-badge" alt="Galego"></a>
  <a href="README.pt.md"><img src="https://img.shields.io/badge/Portugu%C3%AAs-6e7781?style=for-the-badge" alt="Português"></a>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/Fran%C3%A7ais-6e7781?style=for-the-badge" alt="Français"></a>
  <a href="README.de.md"><img src="https://img.shields.io/badge/Deutsch-0969da?style=for-the-badge" alt="Deutsch"></a>
</p>

# MantPro

<p align="center">
  <img src="recursos/logo.png" alt="MantPro Logo" width="200"/>
</p>

<p align="center">
  <strong>Kostenlose Open-Source-Instandhaltungssoftware (CMMS) für die vorbeugende und korrektive Wartung Ihres Werks, Ihrer Werkstatt oder Ihres Fuhrparks, auf PC und Android.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flutter-3.0+-02569B.svg" alt="Flutter">
  <img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Offline--first-✔-success.svg" alt="Offline-first">
  <img src="https://img.shields.io/badge/Selbst%20gehostet-f%C3%BCr%20immer%20kostenlos-orange.svg" alt="Selbst gehostet: für immer kostenlos">
</p>

---

## 📋 Inhalt

- [Welches Problem löst es?](#-welches-problem-löst-es)
- [Für wen ist es?](#-für-wen-ist-es)
- [Warum MantPro?](#-warum-mantpro-und-nicht-ein-kommerzielles-cmms)
- [Demovideo](#-demovideo)
- [Screenshots](#-screenshots)
- [Downloads](#-downloads)
- [Funktionen](#-funktionen)
- [Voraussetzungen](#-voraussetzungen)
- [Installation](#-installation)
- [Verwendung](#-verwendung)
- [Benutzer und Zugang](#-benutzer-und-zugang)
- [Maschinen](#-maschinen)
- [Lagerbestand](#-lagerbestand)
- [Synchronisierung PC–Handy](#-synchronisierung-pchandy)
- [MantPro Cloud](#-mantpro-cloud)
- [Sicherungen](#-sicherungen)
- [Mitwirken](#-mitwirken)
- [Roadmap](#-roadmap)
- [Lizenz](#-lizenz)
- [Kontakt](#-kontakt)

---

## 🧩 Welches Problem löst es?

In vielen kleinen und mittleren Werkstätten und Werken läuft die Instandhaltung
über Zettel, eine gemeinsame Excel-Datei und WhatsApp-Nachrichten. Das klappt,
bis jemand wissen muss, **was an einer bestimmten Maschine gemacht wurde**, wer
es gemacht hat, wann und mit welchem Material, und diese Information auf drei
verschiedene Orte verteilt ist (oder an keinem steht).

**MantPro bündelt das**: Jeder Techniker erfasst seinen Einsatz direkt auf dem
Handy, mit Fotos vorher und nachher, wenn nötig, und auf dem PC ist alles nach
Maschine, Datum und Person geordnet, bereit zum Nachschlagen oder für einen
PDF-Bericht.

## 🎯 Für wen ist es?

Gedacht für die Menschen, die die tägliche Instandhaltung machen, nicht für
IT-Abteilungen: Instandhaltungstechniker, Werksleiter, Werkstätten,
Industrie-KMU und Lagerverantwortliche, die Maschinen, Einsätze und Bestand
wirklich im Griff haben wollen, ohne von verstreuten Tabellen abzuhängen.

## 🆚 Warum MantPro und nicht ein kommerzielles CMMS?

- **Open Source und kostenlos**: offener Quellcode unter AGPL-3.0, ohne Grenze
  bei Technikern, Maschinen oder Einträgen
- **Selbst gehostet: für immer kostenlos**: auf Ihrem eigenen PC oder Server installiert, ohne Gebühren pro Benutzer oder Nutzungsmonat
- **Ihre Daten in Ihrer Infrastruktur**: Die Datenbank liegt auf Ihrem eigenen
  PC; Sie hängen nicht davon ab, dass ein Cloud-Dienst eines Dritten nächstes
  Jahr noch existiert
- **Wirklich offline**: Das Handy funktioniert den ganzen Arbeitstag ohne
  Internet- oder PC-Verbindung und synchronisiert, sobald wieder Netz da ist
- **Aus der Instandhaltung heraus entstanden**: Die Funktionen sind aus
  echten Bedürfnissen der Werkstatt entstanden (Fotos vorher/nachher,
  Maschinenbezug, Ersatzteillager, wiederkehrende Erinnerungen...), nicht aus
  einer allgemeinen CMMS-Anforderungsliste

| | MantPro | Übliches kommerzielles CMMS |
|---|---|---|
| **Preis** | Kostenlos (selbst gehostet) | Monatliche Gebühr pro Benutzer |
| **Benutzer, Maschinen und Einträge** | Unbegrenzt | Je nach Tarif |
| **Wo Ihre Daten liegen** | Auf Ihrem PC oder Server | In der Cloud des Anbieters |
| **Handy-App ohne Verbindung** | Den ganzen Tag | Oft eingeschränkt oder nur Lesen |
| **Ersatzteillager** | Inklusive | Oft als Zusatzmodul |
| **Quellcode** | Offen (AGPL-3.0) | Geschlossen |
| **Wenn der Anbieter verschwindet** | Sie nutzen es weiter | Sie stehen ohne Dienst da |

*Vergleich mit dem üblichen Modell kommerzieller Cloud-CMMS; jedes Produkt ist anders.*

## 🎬 Demovideo

https://github.com/user-attachments/assets/11572710-e0ba-4f8b-b914-0a959006d4fb

## 📸 Screenshots

### Desktop-Anwendung

<p align="center">
  <img src="Capturas/Dashboard.png" alt="Dashboard" width="30%"/>
  <img src="Capturas/Maquinas.png" alt="Maschinen und Ersatzteile" width="30%"/>
  <img src="Capturas/Almacen.png" alt="Lagerverwaltung" width="30%"/>
</p>

### Handy-App

<p align="center">
  <img src="Capturas/Dashboard-movil.jpg" alt="Dashboard auf dem Handy" width="30%"/>
  <img src="Capturas/Almacen-movil.jpg" alt="Lager auf dem Handy" width="30%"/>
  <img src="Capturas/Historial-movil.jpg" alt="Verlauf auf dem Handy" width="30%"/>
</p>

---

## 📦 Downloads

Die vorkompilierten Versionen können Sie unter [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) herunterladen:

- **Windows**: Installer (`MantPro_Setup_v….exe`) oder einzelne `.exe`-Datei
- **Linux**: 
  - Ausführbare Linux-Binärdatei
  - Portables AppImage
  - Pakete `.deb` (Debian, Ubuntu…) und `.rpm` (Fedora, openSUSE…), mit GPG signiert
  - Auch im **AUR** (Arch User Repository) verfügbar
  - Auch im [**OBS**](https://build.opensuse.org/package/show/home:danitxu79/MantPro) (openSUSE Build Service) für openSUSE Tumbleweed und Slowroll verfügbar
- **Android**: `.apk`-Dateien zur direkten Installation
  - `MantPro.apk`: App für Wartungsarbeiten
  - `MantProStock.apk`: App für den Lagerbestand

Als *Pre-Release* gekennzeichnete Versionen (`v3.10.2-dev`, `-rc.1`…) sind
Testversionen: Sie werden nur denen als Update angeboten, die bereits eine
Testversion installiert haben. Wer eine stabile Version nutzt, erhält nur
Hinweise auf stabile Versionen. Die Änderungen jeder Version stehen in
[CHANGELOG.md](CHANGELOG.md).

---

## ✨ Funktionen

### 💻 Desktop-Anwendung (PC)

- **👥 Benutzerverwaltung**: Anmeldung mit Benutzer und Passwort, Rollen Administrator und Techniker, Anlegen und Löschen von Benutzern sowie Zurücksetzen von Passwörtern
- **✍️ Autorschaft der Arbeiten**: Jeder Einsatz speichert, wer ihn ausgeführt hat, sichtbar im Verlauf und in den Berichten
- **🔒 Berechtigungen pro Eintrag**: Ein Techniker kann nur seine eigenen Arbeiten bearbeiten oder löschen; ein Administrator kann alle verwalten, einschließlich der Neuzuweisung des Autors eines oder mehrerer Einträge auf einmal
- **📋 Änderungsprotokoll**: wer was wann und von wo (PC oder Handy) geändert hat, bei Arbeiten, offenen Arbeiten, Erinnerungen, Checklisten, Maschinen, Lager, Benutzern, Sicherheit und Einstellungen, mit jedem Feld vorher → nachher; Filter, Suche und Export nach Excel/CSV (nur Administratoren)
- **🔐 Gerätesitzungen**: listet die mit jedem Benutzer verbundenen Handys mit ihrem echten Modell auf und erlaubt, einzelne oder mehrere Sitzungen zu widerrufen, ohne den ganzen Benutzer zu deaktivieren (nur Administratoren). Bei erneuter Anmeldung vom selben Gerät wird seine vorherige Sitzung automatisch ersetzt, statt sich anzuhäufen
- **🛡️ Sicherheit**: Synchronisierung mit den Handys per HTTPS verschlüsselt (das Zertifikat des PCs wird über den QR-Code festgelegt), optional **verschlüsselte Datenbanken** (SQLCipher, mit dem Schlüssel im Schlüsselbund des Systems) und **passwortverschlüsselte Sicherungen**, begrenzte Anmeldeversuche gegen Brute-Force-Angriffe, geprüfte Fotos von den Handys und konsistente Sicherungen mit Integritätsprüfung
- **📊 Dashboard mit KPIs und Diagrammen**: Karten mit offenen Erinnerungen, zu erledigenden Aufgaben, Einträgen des Monats und mittlerer MTBF/MTTR des ganzen Werks, dazu Diagramme der Maschinen mit den meisten Störungen und der Störungen pro Monat, ohne externe Bibliotheken gezeichnet, sowie die Wartungskosten des Monats und des Jahres, die Maschinen mit den höchsten Kosten und die Kosten pro Monat
- **🎨 Designs**: Wählen Sie im Menü „Darstellung“ zwischen dunklem Modus (Standard), hellem Modus oder einem an Windows 98 angelehnten Retro-Stil. Die Symbole der Datei- und Ordnerauswahl werden passend zu jedem Design gezeichnet, sodass sie auch bei dunklem oder fehlendem System-Symboldesign (Windows) gut aussehen
- **📅 Interaktiver Kalender**: Wartungsaufgaben mit Farbcodes anzeigen und verwalten (Feiertage, Urlaub, Tage mit Aufgaben)
- **📝 Vollständiger Verlauf**: Verlauf aller ausgeführten Einsätze, mit Fotos vorher/nachher und einer zusätzlichen **Fotosammlung** pro Arbeit; mehrere Einträge lassen sich auf einmal löschen
- **📄 PDF-Berichte**: Automatische Erstellung professioneller Berichte mit anpassbarem Logo
- **📸 Bildverwaltung**: Speichern und Anzeigen der Fotos der Einsätze
- **📱 Handy-Synchronisierung**: Integrierter Server (startet automatisch) zur Synchronisierung mit der Handy-App per QR-Code
- **🔍 Suchsystem**: Erweiterte Suche nach Datum, Tags und Inhalt
- **👤 Filter nach Techniker**: Filtert den Verlauf und die Exporte (PDF, CSV und Excel) nach der Person, die die Arbeit ausgeführt hat
- **📦 Sicherung/Wiederherstellung**: vollständige manuelle Sicherung (DB + Fotos) an einem Ort Ihrer Wahl, inkrementelle automatische Sicherung beim Beenden, in regelmäßigen Abständen und nach Empfang von Handydaten, mit externem Ordner und Wiederherstellungsprobe (siehe [Sicherungen](#-sicherungen)), und Wiederherstellung mit Fortschrittsbalken, mit Untermenü `Datei > Wiederherstellen`, um eine beliebige manuelle Sicherung oder direkt die automatischen Sicherungen zu wählen. Die Sicherungen lassen sich **mit Passwort verschlüsseln** (`Datei > 🔒 Passwort der Sicherungen…`)
- **🏷️ Tag-System**: Einordnung mit Tags (Dringend, Elektrisch, Mechanisch, Vorbeugend)
- **🔨 Offene Aufgaben**: Verwaltung offener Arbeiten (anlegen, erledigen, bearbeiten, löschen) und **Zuweisung an einen bestimmten Techniker**
- **🚦 Priorität offener Arbeiten**: Jede offene Arbeit hat eine Priorität (Niedrig, Mittel, Hoch oder Kritisch), um zu entscheiden, welche zuerst angegangen wird, mit ihrer Farbe in der Liste; außerdem lassen sich Fotos zu ihrer Sammlung hinzufügen
- **↩️ Zurück zu offen**: Wurde eine Arbeit versehentlich erledigt, kann sie mit einem Klick im Verlauf zu den offenen Arbeiten zurückgeschickt werden (mit Hinweis, wenn sie eine verknüpfte Maschine hatte, da diese Angabe verloren ginge), und es wird im Protokoll festgehalten
- **🔁 Erinnerungen**: Wartungserinnerungen, die sich automatisch wiederholen. Verstreicht das Datum, werden sie nicht übersprungen: Sie bleiben **Offen** (orange), solange der Spielraum läuft, und danach **Überfällig** (rot), bis sie erledigt sind, und das nächste Datum wird ab dem tatsächlichen Tag der Arbeit gezählt
- **📟 Zählerbasierte Wartung**: Erinnerungen nach **Betriebsstunden, Zyklen oder km** einer Maschine („Ölwechsel alle 500 h, 50 h vorher erinnern“), allein oder zusammen mit einer Häufigkeit nach Datum (**was zuerst eintritt**: „alle 500 h oder jedes Jahr“). Die Ablesungen werden auf dem PC, im Steckbrief der Maschine auf dem Handy (auch ohne Verbindung) und beim Erledigen der Wartung erfasst; ab dieser Ablesung wird die nächste gezählt, und es wird geschätzt, wann sie anhand der mittleren Nutzung erreicht wird
- **☑️ Checklisten**: wiederverwendbare Vorlagen („Monatliche Prüfung Kompressor“) mit Punkten, die als in Ordnung / nicht in Ordnung / entfällt markiert werden, und Messwerten mit Einheit und gültigem Bereich (außerhalb des Bereichs automatisch „nicht in Ordnung“); sie werden Erinnerungen und offenen Arbeiten zugewiesen und beim Erledigen ausgefüllt, auf dem PC oder auf dem Handy (auch ohne Verbindung). Sie werden mit der Arbeit gespeichert, sind im Verlauf sichtbar und erscheinen in den Exporten als PDF, Excel und CSV
- **📦 Lagerbestandsverwaltung**: Konfigurierbare Struktur aus Regalen, Fachböden und Fächern, Materialsteckbrief mit Foto, Zu- und Abgänge mit Verlauf und Warnungen bei Bestand unter Minimum
- **📄 Bestand exportieren**: Schaltfläche „📄 Exportieren“ im Reiter Lagerbestand, um das ganze Lager, eine Zone oder ein Regal als PDF, CSV oder Excel auszugeben, nach Lagerort sortiert; der Reiter Bestand unter Minimum hat ebenfalls eine Schaltfläche, um nur das Material mit Warnung zu exportieren
- **🏭 Lieferanten und Stammlieferant**: Lieferantenliste (Name, Ansprechpartner, Telefon, E-Mail und Notizen) über die Schaltfläche „🏭 Lieferanten“ im Reiter Lagerbestand und das Feld „Stammlieferant“ bei jedem Artikel. Preisverlauf pro Lieferant für Administratoren („💶 Preise pro Lieferant…“ im Steckbrief sowie Lieferant und Preis bei den Zugängen). Zielbestand und Bestellvielfaches pro Artikel, mit der vorgeschlagenen Bestellmenge. Bestellvorschlag (was jetzt zu bestellen ist, abzüglich bereits bestellter und noch ausstehender Mengen) und gespeicherte Bestellungen mit Datum, die per E-Mail, WhatsApp, Telefon oder ausgedruckt versendet werden; jeder Zugang verrechnet das Ausstehende. Nur Administratoren
- **🗑️ Maximale Aufbewahrungsdauer**: Unter `Werkzeuge` lassen sich Arbeiten, die älter als eine bestimmte Zahl von Jahren, Monaten oder Tagen sind, mit ihren Fotos und einer vorherigen Sicherung aus dem Verlauf löschen (nur Administratoren)
- **📥 Aus Excel/CSV importieren**: `Datei > Aus Excel/CSV importieren…` (nur Administratoren) übernimmt Maschinen, Lagerartikel, wiederkehrende Erinnerungen, Benutzer, offene Arbeiten und alte Arbeitsverläufe aus einer herunterladbaren Vorlage oder aus Ihrer eigenen Excel-Datei (ein Blatt oder die ganze Arbeitsmappe auf einmal), ordnet die Spalten selbst zu, mit Vorschau Zeile für Zeile und vorheriger Sicherung. Nicht vorhandene Lagerorte (Zonen, Regale, Fachböden) und übergeordnete Maschinen werden automatisch angelegt, und die Benutzer erhalten ein vorläufiges Passwort, das sie bei der Anmeldung ändern müssen
- **🏭 Maschinenverwaltung**: Baum aus Maschinen und Untermaschinen mit Foto, Zähler der Arbeiten pro Jahr und Monat und direkter Verknüpfung aus jeder erfassten oder bearbeiteten Arbeit (siehe [Maschinen](#-maschinen))
- **📊 Export**: Als PDF, CSV und Excel, mit optionalem Filter nach Techniker und Angabe der Maschine/Untermaschine jeder Arbeit, falls vorhanden
- **📖 Integrierte Hilfe**: `Hilfe > 📖 Anleitung` öffnet ein vollständiges Handbuch nach Abschnitten (erste Schritte, Benutzer, jeder Reiter, Menüs, Handy-Apps und häufige Probleme), mit Inhaltsverzeichnis und Suche, in 8 Sprachen. Mit **F1** öffnet es sich direkt beim Abschnitt des Reiters, in dem Sie sich befinden
- **👥 Statistik pro Techniker**: Schaltfläche im Dashboard mit den Arbeiten jedes Technikers pro Jahr und Monat, Störungen, vorbeugenden Wartungen, Stillstandsstunden und aktuell zugewiesenen offenen Arbeiten, mit Balkendiagramm; filterbar nach Art (alle, Arbeiten und Störungen oder vorbeugende Wartung) und exportierbar als PDF (mit Logo) und Excel
- **🔩 Ersatzteile pro Maschine**: welche Lagerartikel in jeder Maschine verbaut sind und wie viele, mit Bestand und Lagerort, und in welchen Maschinen jeder Artikel verwendet wird (siehe [Maschinen](#-maschinen))
- **💶 Verbrauchte Ersatzteile und ihre Kosten**: Beim Erfassen, Erledigen oder Bearbeiten einer Arbeit werden die verbrauchten Ersatzteile eingetragen (die der Maschine werden zuerst vorgeschlagen); sie werden vom Bestand abgebucht und mit der Arbeit und dem damaligen Preis gespeichert, sodass sich die Kosten nicht ändern, auch wenn sich der Preis später ändert. Beim Korrigieren passt sich der Bestand an. Jeder Artikel kann einen Stückpreis haben (Währung einstellbar). `Maschinen > 💶 Ersatzteilkosten` zeigt die Kosten pro Maschine, mit ihren Untermaschinen, pro Jahr und als Excel exportierbar; Verlauf, PDF, Excel und CSV enthalten sie. Die Kosten sehen nur Administratoren.
- **⏱️ Arbeitszeit**: wie lange jede Arbeit gedauert hat und wie viele Personen, **nachträglich erfasst** (ohne Stoppuhr: bei einer Störung wird zuerst repariert), auf dem PC oder auf dem Handy, auch beim Erledigen von Erinnerungen und offenen Arbeiten, und im Verlauf korrigierbar. Mit einem internen Stundensatz (nur Administratoren; jede Arbeit speichert den damaligen Satz) zeigt `Maschinen > 💶 Kosten` Stunden, Arbeitskosten, Ersatzteile und Summe pro Maschine, und die Statistik pro Techniker enthält seine Stunden
- **🏷️ QR-Etiketten pro Maschine**: PDF mit Etiketten zum Aufkleben auf die Maschinen; beim Scannen mit der App MantPro öffnet sich der Steckbrief der Maschine
- **🔍 Hinweis auf Doppelte**: Beim Anlegen oder Umbenennen einer Maschine oder beim Anlegen oder Bearbeiten eines Artikels weist es darauf hin, wenn es bereits einen mit demselben Code oder einem gleichen bzw. sehr ähnlichen Namen gibt (zum Beispiel „Feinstaubabsaugung“ / „Feinstaub-Absaugung“), ohne Hinweis, wenn sich nur die Nummer ändert („Lora 1“ / „Lora 2“)
- **📲 Apps per QR-Code installieren**: `Werkzeuge > 📱 MantPro auf dem Handy installieren` und `📦 MantPro Stock auf dem Handy installieren` zeigen einen QR-Code, der beim Scannen mit der Handykamera die neueste stabile Version der App herunterlädt
- **🔔 Update-Hinweise**: `Hilfe > 🔄 Nach Updates suchen` weist auf neue Versionen hin; bei Installation über OBS (openSUSE) wird angezeigt, dass das Update über `zypper` erfolgt

### 📱 Handy-App (Android)

- **🔐 Anmeldung mit Benutzer**: Jeder Techniker meldet sich einmal an, und die Sitzung bleibt auf dem Gerät gespeichert (das Token liegt im Android Keystore, nicht im Klartext)
- **📝 Schnelle Erfassung**: Erfassung von Einsätzen vor Ort, automatisch mit dem Benutzer gekennzeichnet
- **📷 Integrierte Kamera**: Fotos aufnehmen und mit Anmerkungen bearbeiten
- **🖼️ Fotosammlung**: Neben den Fotos vorher und nachher können Sie einer Arbeit oder offenen Arbeit beliebig viele Fotos hinzufügen (Kamera oder Galerie); ein Tippen auf ein Foto zeigt es im Vollbild, mit Wischen von einem zum nächsten und Zoomen mit zwei Fingern. Die Sammlung nimmt auch **🎬 Videos** auf (bis 30 s und 100 MB; direkt aufgenommen oder aus der Galerie gewählt), die in der App abgespielt werden, ohne Verbindung, und auf dem PC mit dessen Videoplayer; die Fotos vorher und nachher sind immer Fotos
- **✏️ Bildeditor**: Auf Fotos zeichnen, um Bereiche zu markieren
- **🔄 Automatische Synchronisierung**: Automatisches Senden der Daten an den PC per QR-Code
- **💾 Lokale Speicherung**: Speichert Einträge offline bis zur Synchronisierung
- **📋 Offene Arbeiten**: Vom PC zugewiesene Aufgaben anzeigen und verwalten, mit dem Filter **„Nur meine“**
- **🔄 Aktuell beim Öffnen**: Beim Start synchronisiert die App die Daten aller Reiter im Hintergrund
- **🔁 Manuell neu synchronisieren**: Die Reiter Offen, Verlauf und Erinnerungen haben eine eigene Schaltfläche, um sofort zu senden, was das Handy hat und der PC noch nicht
- **↩️ Zurück zu offen**: Durch langes Drücken auf einen Eintrag im Verlauf lässt er sich in den Reiter Offen zurückschicken, wenn er versehentlich erledigt wurde
- **🏷️ Schnell-Tags**: Schnelles Taggen mit Kontrollkästchen
- **☑️ Checklisten**: Erinnerungen und offene Arbeiten mit Liste verlangen beim Erledigen das Ausfüllen (in Ordnung / nicht in Ordnung / entfällt und Messwerte), auch ohne Verbindung; der Verlauf zeigt die ausgefüllte Liste
- **🔌 Offline-Modus**: Arbeiten ohne Verbindung und synchronisieren, sobald möglich
- **⏰ Tägliche Erinnerungen**: Automatische Benachrichtigung um 8:00 Uhr (Ortszeit), wenn offene Arbeiten nicht erledigt sind
- **🧰 Verbrauchtes Material**: Fügen Sie der Arbeit das verwendete Lagermaterial hinzu, gesucht nach Name oder Code; es wird beim Speichern automatisch vom Bestand abgebucht (siehe [Bei einer Arbeit verbrauchtes Material](#-lagerbestand)). Beim Erledigen einer Erinnerung lassen sich ebenfalls Ersatzteile eintragen, die der Maschine stehen oben, und beim Korrigieren einer Arbeit im Verlauf passt sich der Bestand an
- **🏭 Maschine verknüpfen**: Wählen Sie in einer Auswahlliste die Maschine oder Untermaschine, an der gearbeitet wurde, sowohl beim Anlegen eines neuen Eintrags als auch beim Bearbeiten eines bereits synchronisierten aus dem Verlauf
- **🔄 Im Hintergrund verbunden**: Solange die App geöffnet ist, auch im Hintergrund, synchronisiert sie weiter mit dem PC und zeigt eine Benachrichtigung („Mit dem PC verbunden“ / „Keine Verbindung zum PC“) mit einer Schaltfläche „Schließen“. Ganz geschlossen verbraucht sie keinen Akku mehr
- **📶 Erste Synchronisierung mit Fortschritt**: Fortschrittsbalken beim Herunterladen der Daten und Fotos, mit parallelem Download für mehr Tempo
- **🏷️ Maschine scannen**: Die Scan-Schaltfläche liest das QR-Etikett einer Maschine und öffnet ihren Steckbrief, ohne Verbindung: wo sie steht, ihre letzten Arbeiten, ihre **Ersatzteile** mit dem Lagerbestand und eine Schaltfläche, um eine bereits mit ihr verknüpfte Arbeit zu erfassen
- **📟 Zähler der Maschine**: Im Steckbrief der Maschine werden die Ablesungen ihrer Zähler (Stunden, Zyklen, km) ohne Verbindung erfasst, und ihre zählerbasierten Wartungen sind mit dem noch Fehlenden zu sehen; beim Erledigen einer davon wird die Ablesung im selben Schritt erfasst
- **⬆️ Aus der App aktualisieren**: Gibt es eine neue Version, hat der Hinweis die Schaltflächen „Später“ und „Aktualisieren“; „Aktualisieren“ lädt das APK mit Fortschrittsbalken herunter und öffnet den Android-Installer, ohne Umweg über GitHub

### 📦 Lager-App (Android)

Eigenständige App (`mantpro_stock_app`), gedacht zum Nachsehen und Bewegen
des Lagerbestands auf dem Handy, ohne die App für Arbeiten zu brauchen.

- **🔐 Anmeldung mit Benutzer**: verwendet dasselbe Benutzer- und Sitzungssystem wie die App für Arbeiten (das Token liegt im Android Keystore, nicht im Klartext)
- **🗂️ Lagernavigation**: Baum aus Regalen > Fachböden > Fächern, wie auf dem PC
- **🔎 Materialsuche**: nach Name, Code, Beschreibung oder Lagerort
- **➕➖ Zu- und Abgänge**: erfasst Lagerbewegungen auf dem Handy, mit optionalem Grund
- **🔀 Umlagerungen**: Das Verschieben eines Materials in ein anderes Fach wird in seinem Bewegungsverlauf festgehalten
- **🎨 Optischer Bestandshinweis**: Menge rot unter dem Minimum, grün darüber und in der Standardfarbe, wenn sie genau übereinstimmt
- **⚠️ Bestand unter Minimum**: eigener Reiter für das Material mit Warnung
- **🔄 Automatische Aktualisierung**: Der Bildschirm aktualisiert sich selbst, wenn Änderungen erkannt werden, egal ob sie auf dem Handy oder auf dem PC vorgenommen wurden
- **🔌 Offline-Modus**: Ohne Verbindung zum PC wartet die App nicht: Sie zeigt die gespeicherten Daten und lässt Neuanlagen, Änderungen, Zu- und Abgänge sofort erfassen, die automatisch an den PC gesendet werden, sobald er wieder erreichbar ist
- **🔔 Tägliche Erinnerung zur Bestandsprüfung**: automatische Benachrichtigung um 8:00 Uhr (Ortszeit), die einlädt, die tatsächliche Menge von 5 Lagermaterialien zu prüfen, zufällig ausgewählt und jeden Tag andere; ein Tippen öffnet einen Bildschirm, um die Menge jedes einzelnen zu korrigieren, ohne sie suchen zu müssen. Ist kein Material angelegt, erscheint keine Benachrichtigung. Wird sie halb fertig geschlossen oder der Hinweis verworfen, öffnet die Schaltfläche 📋 „Lagerprüfung“ in der oberen Leiste sie jederzeit am selben Tag erneut, mit denselben Artikeln und dem bereits Geprüften (ein Zähler zeigt, wie viele noch fehlen)
- **🔄 Im Hintergrund verbunden**: wie MantPro synchronisiert sie im Hintergrund weiter, mit ihrer Benachrichtigung; das Benutzersymbol wird **grün**, wenn eine Verbindung zum PC besteht, und **rot**, wenn nicht
- **🔩 Verwendet in**: Jeder Artikel zeigt, in welchen Maschinen er als Ersatzteil verwendet wird und wie viele jede hat, auch ohne Verbindung
- **🔍 Hinweis auf Doppelte**: Beim Anlegen oder Bearbeiten eines Artikels weist sie darauf hin, wenn es bereits einen mit demselben Code oder einem sehr ähnlichen Namen gibt, im Vergleich mit den auf dem Handy gespeicherten Artikeln (funktioniert ohne Verbindung)
- **⬆️ Aus der App aktualisieren**: wie MantPro lädt sie die neue Version direkt aus dem Hinweis herunter und installiert sie

---

## 🔧 Voraussetzungen

### Desktop-Anwendung

- **Python**: 3.10 oder höher
- **Betriebssystem**: Windows oder Linux
- **Python-Abhängigkeiten**:
  - PyQt6
  - Flask
  - ReportLab
  - qrcode
  - requests
  - xlsxwriter
  - openpyxl
  - Pillow
  - cryptography
  - keyring und sqlcipher3-wheels (optional: Verschlüsselung der Datenbanken)
  - sqlite3 (in Python enthalten)

### Handy-App

Gilt sowohl für `mantenimiento_app` (Arbeiten) als auch für `mantpro_stock_app` (Lager):

- **Flutter**: 3.0 oder höher
- **Dart SDK**: 2.17 oder höher
- **Android**: API-Level 24+ (Android 7.0+)

---

## 📥 Installation

### Desktop-Anwendung

#### Option 1: Vorkompilierter Download (empfohlen)

Laden Sie die passende Version für Ihr System unter [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) herunter:

- **Windows**: Laden Sie die `.exe` herunter und führen Sie sie aus
- **Linux**: 
  - Laden Sie die ausführbare Binärdatei herunter und machen Sie sie ausführbar: `chmod +x mantpro`
  - Oder verwenden Sie das **AppImage** (ohne Installation): `chmod +x MantPro.AppImage && ./MantPro.AppImage`
  - Die Pakete **`.deb`** und **`.rpm`** sind digital mit GPG signiert (siehe [Paketsignatur prüfen](#-paketsignatur-prüfen-linux))
  - **Arch Linux**: Im AUR verfügbar: `yay -S mantpro` oder `paru -S mantpro`
  - **openSUSE Tumbleweed / Slowroll**: im [OBS](https://build.opensuse.org/package/show/home:danitxu79/MantPro) verfügbar, mit dem Python und PyQt6 der Distribution kompiliert und über `zypper` aktualisiert:
    ```bash
    sudo zypper ar -f https://download.opensuse.org/repositories/home:/danitxu79/openSUSE_Tumbleweed/home:danitxu79.repo
    sudo zypper in mantpro
    ```
    (unter Slowroll ersetzen Sie `openSUSE_Tumbleweed` in der URL durch `openSUSE_Slowroll`)

#### 🔏 Paketsignatur prüfen (Linux)

Die in jedem Release veröffentlichten Pakete `.deb` und `.rpm` sind mit dem offiziellen GPG-Schlüssel von AnabasaSoft signiert. So prüfen Sie sie vor der Installation:

**Fingerabdruck des Schlüssels** (prüfen Sie ihn auch auf [anabasasoft.github.io](https://anabasasoft.github.io/about.html#firma)): `11C7 C6C8 127D FE48 33DE  30EF 9D7A AEC8 1842 C199` (RSA 4096, läuft am 2028-10-06 ab). Stimmt der von `gpg` angezeigte nicht genau überein, installieren Sie das Paket nicht.

1. Laden Sie den öffentlichen Schlüssel des Repositorys ([`firma/anabasasoft_public.asc`](firma/anabasasoft_public.asc)) in eine Datei herunter (**verwenden Sie nicht `curl | rpm --import -`**, manche `rpm`-Versionen können den Schlüssel nicht von der Standardeingabe lesen und brechen mit einem Lesefehler beim Import ab):
   ```bash
   curl -sL https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/firma/anabasasoft_public.asc -o /tmp/anabasasoft_public.asc
   ```

2. Importieren Sie den Schlüssel (nur einmal pro Rechner nötig):
   ```bash
   # Fedora, openSUSE, RHEL... (.rpm-Paket)
   sudo rpm --import /tmp/anabasasoft_public.asc

   # Debian, Ubuntu... (.deb-Paket, benötigt dpkg-sig)
   gpg --import /tmp/anabasasoft_public.asc
   ```

3. Prüfen Sie, ob der Schlüssel korrekt importiert wurde:
   ```bash
   # RPM
   rpm -qa 'gpg-pubkey*' --qf '%{name}-%{version}-%{release} --> %{summary}\n' | grep -i anabasasoft

   # DEB (oder jede Distribution mit gpg): zeigt auch den Fingerabdruck
   gpg --fingerprint AnabasaSoft
   ```

4. Prüfen Sie die Signatur des heruntergeladenen Pakets:
   ```bash
   # RPM
   rpm --checksig mantpro-*.rpm

   # DEB
   dpkg-sig --verify mantpro_*.deb
   ```
   Eine korrekte Signatur zeigt `OK` in der Signaturzeile (statt `NOKEY` oder `MISSING KEYS`).

Eine gültige Signatur bestätigt, dass das Paket von AnabasaSoft stammt und nicht verändert wurde.

#### Option 2: Installation aus dem Quellcode

1. **Repository klonen**:
   ```bash
   git clone https://github.com/AnabasaSoft/MantPro.git
   cd MantPro
   ```

2. **Virtuelle Umgebung anlegen** (empfohlen):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   ```

3. **Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Anwendung starten**:
   ```bash
   python main.py
   ```

### Handy-App

#### Option 1: Direkter Download (empfohlen)

Laden Sie das passende `.apk` unter [GitHub Releases](https://github.com/AnabasaSoft/MantPro/releases) herunter und installieren Sie es auf Ihrem Android-Gerät: `MantPro.apk` für Arbeiten, `MantProStock.apk` für den Lagerbestand. Es sind eigenständige Apps; Sie können eine, die andere oder beide installieren.

**Hinweis**: Eventuell müssen Sie in den Sicherheitseinstellungen Ihres Geräts „Unbekannte Quellen“ erlauben.

**Vom PC aus, per QR-Code**: Unter `Werkzeuge > 📱 MantPro auf dem Handy installieren`
(oder `📦 MantPro Stock auf dem Handy installieren`) erscheint ein QR-Code. Scannen Sie ihn mit der
Handykamera, öffnen Sie den Link, und die neueste stabile Version der App wird heruntergeladen.
Einmal installiert, weisen die Apps auf neue Versionen hin und aktualisieren sich
direkt aus dem Hinweis mit der Schaltfläche „Aktualisieren“.

#### Option 2: Aus dem Quellcode kompilieren

1. **In das Handy-Verzeichnis wechseln** (`mantenimiento_app` für Arbeiten, `mantpro_stock_app` für den Lagerbestand):
   ```bash
   cd mantenimiento_app
   ```

2. **Abhängigkeiten installieren**:
   ```bash
   flutter pub get
   ```

3. **Auf Gerät/Emulator ausführen**:
   ```bash
   flutter run
   ```

4. **APK kompilieren (Android)**:
   ```bash
   flutter build apk --release
   ```

---

## 🚀 Verwendung

### Ersteinrichtung

#### Desktop-Anwendung

1. **Anwendung starten**: Führen Sie `python main.py` aus (der Synchronisierungsserver startet von selbst, Sie müssen ihn nicht manuell starten)
2. **Erste Anmeldung**: Beim ersten Start wird der Benutzer `admin` mit dem Passwort `admin` angelegt. Die Anwendung **verlangt, es bei der Anmeldung zu ändern**
3. **Benutzer anlegen**: Menü `Werkzeuge` > `👥 Benutzerverwaltung` > legen Sie jeden Techniker an
4. **Logo einrichten** (optional): Menü `Datei` > `📤 Exportieren` > `📄 PDF-Optionen` > `🖼️ Logo hinzufügen / ändern`
5. **Eine Arbeit erfassen**: Reiter „📝 Erfassen“ > Zusammenfassung/Details ausfüllen > „💾 EINTRAG SPEICHERN“
6. **Eine offene Arbeit anlegen**: Reiter „🔨 Offene Arbeiten“ > Gruppe „Neue Arbeit“ (Titel + Details + „Zuweisen an“) > „Hinzufügen“

#### Handy-App

1. **Installieren Sie die App** auf Ihrem Handy
2. **Mit dem PC verbinden**:
   - Stellen Sie sicher, dass PC und Handy im selben WLAN sind
   - Auf dem PC: Menü `Werkzeuge` > `📲 App synchronisieren (QR)`
   - Auf dem Handy: Tippen Sie auf „PC verbinden“ und scannen Sie den Code
3. **Anmelden**: Geben Sie den Benutzer und das Passwort ein, die der Administrator für Sie angelegt hat. Die Sitzung bleibt gespeichert: Das ist nur einmal nötig
4. **Fertig**: Sie können jetzt Einsätze auf dem Handy erfassen

### Typischer Arbeitsablauf

#### Am PC

1. **Eine offene Aufgabe anlegen und zuweisen**:
   - Reiter „🔨 Offene Arbeiten“ > Gruppe „Neue Arbeit“ > Titel und Details ausfüllen, den Techniker unter „Zuweisen an“ wählen > „Hinzufügen“
   - Verwalten Sie sie mit den Schaltflächen „✅ Erledigen“, „✏️ Bearbeiten“, „❌ Löschen“ oder „👤 Neu zuweisen“
   - Die Auswahlliste „Anzeigen von“ filtert die Liste nach Techniker (einschließlich „Nicht zugewiesen“)

2. **Erledigte Arbeiten prüfen**:
   - Die vom Handy synchronisierten Arbeiten erscheinen automatisch
   - Prüfen Sie Fotos (vorher/nachher) und Details im Reiter „📋 Verlauf“ oder im „📅 Kalender“
   - Die Spalte „Ausgeführt von“ zeigt, wer welche Arbeit erledigt hat, und die Auswahlliste oben zeigt nur die einer Person

3. **Berichte erstellen**:
   - Menü `Datei` > `📤 Exportieren` > `📄 PDF-Optionen` > `📄 PDF jetzt erstellen`
   - Im Dialog können Sie den Techniker wählen, und sein Name erscheint im Titel des Berichts
   - Oder exportieren Sie als `📄 CSV` / `📊 Excel` über `Datei` > `📤 Exportieren`

#### Auf dem Handy

1. **Mit dem PC verbinden und anmelden** (nur beim ersten Mal oder bei einem Netzwechsel):
   - Tippen Sie auf „PC verbinden“ und scannen Sie den QR-Code, den der PC anzeigt
   - Geben Sie Ihren Benutzer und Ihr Passwort ein
   - Das Handy speichert die Adresse des PCs und Ihre Sitzung, um ab dann automatisch zu synchronisieren

2. **Einen Einsatz erfassen**:
   - Tippen Sie auf „Neu“ oder wählen Sie eine bereits vom PC synchronisierte offene Arbeit
   - Mit dem Chip „Nur meine“ sehen Sie nur die Ihnen zugewiesenen Arbeiten
   - Füllen Sie Titel und Details aus
   - Nehmen Sie mit der Kamera ein Foto „vorher“ und optional ein Foto „nachher“ auf
   - Zeichnen/markieren Sie bei Bedarf auf dem Foto
   - Wählen Sie passende Tags
   - Speichern

3. **Synchronisieren**:
   - Beim Öffnen der App wird alles im Hintergrund synchronisiert (Sie sehen eine Anzeige in der oberen Leiste)
   - Sie können es auch erzwingen, indem Sie die Liste nach unten ziehen oder auf das Synchronisierungssymbol tippen
   - Die Einträge werden an den PC gesendet und nach bestätigtem Versand vom Handy gelöscht
   - Alles funktioniert ohne Verbindung: Ausstehendes wird gespeichert und hochgeladen, sobald Empfang besteht

---

## 👥 Benutzer und Zugang

### Rollen

Ein Benutzer kann **eine oder mehrere Rollen gleichzeitig** haben (zum Beispiel
Techniker und Lager). Verfügbare Rollen:

| Rolle | Darf |
|-----|-------------|
| **Administrator** | Alles, was Techniker und Lager dürfen, dazu Benutzer anlegen und löschen, Rollen ändern, Passwörter zurücksetzen, **jeden** Eintrag im Verlauf bearbeiten oder löschen, den Autor eines oder mehrerer Einträge auf einmal neu zuweisen und das Änderungsprotokoll einsehen |
| **Techniker** | Arbeiten erfassen, offene Arbeiten und Erinnerungen erledigen, **nur seine eigenen** Einträge im Verlauf bearbeiten oder löschen und sein eigenes Passwort ändern |
| **Lager** | Material anlegen oder bearbeiten und Zu-/Abgänge in der Handy-App **MantPro Stock** erfassen |

Es muss immer **mindestens ein aktiver Administrator** übrig bleiben: Die Anwendung verhindert,
dem letzten die Rolle zu entziehen oder ihn zu deaktivieren.

> In der Desktop-Anwendung kann jeder Benutzer (gleich welcher Rolle)
> Lagerbewegungen erfassen; die Rolle **Lager** schaltet dieselbe Verwaltung
> (Neuanlagen, Änderungen und Bewegungen) auf dem Handy frei.

### Verwaltung am PC

- **Anlegen**: `Werkzeuge` > `👥 Benutzerverwaltung` > Benutzer, Name,
  Passwort und Rolle ausfüllen > „➕ Hinzufügen“. Bleibt „Änderung bei Anmeldung verlangen“ angehakt,
  muss die Person bei der ersten Anmeldung ein eigenes Passwort festlegen.
- **Deaktivieren**: erfolgt **logisch** (der Benutzer wird inaktiv). Er wird nie
  gelöscht, damit die Autorschaft seiner bisherigen Arbeiten erhalten bleibt.
- **Passwort zurücksetzen**: nützlich, wenn jemand es vergessen hat. Bei der Änderung
  werden alle offenen Sitzungen dieser Person auf dem Handy automatisch geschlossen.
- **Eigenes Passwort ändern**: `Werkzeuge` > `🔑 Mein Passwort ändern`.

### Gerätesitzungen

`Werkzeuge` > `🔐 Gerätesitzungen` (nur Administratoren) listet
alle offenen Handysitzungen aller Benutzer auf, mit dem Modell
des Geräts, wann sie begonnen hat, wann sie abläuft und ob sie noch aktiv oder bereits
abgelaufen ist. Eine oder mehrere Zeilen lassen sich gleichzeitig auswählen und widerrufen, was
die Sitzung dieses Handys schließt, ohne den ganzen Benutzer deaktivieren zu müssen
(was *alle* seine Geräte auf einmal abmelden würde). **Handy einem Techniker zuordnen**: Mit `📲 Handy einem Techniker zuordnen…` kann sich auf dem Handy nur sein Techniker anmelden (Administratoren immer), und die App trägt seinen Benutzer ein; das gilt für MantPro und MantPro Stock zugleich, sodass derselbe Techniker beide Apps auf demselben Handy nutzen kann.

Meldet sich ein Benutzer erneut von einem Gerät an, mit dem er bereits
eine offene Sitzung hatte (gleicher Hersteller und gleiches Modell), wird die vorherige Sitzung dieses
Geräts beim Anlegen der neuen automatisch gelöscht, statt sich als weitere
lose Sitzung in der Liste anzuhäufen.

Sitzungen laufen bei Inaktivität ab: Jedes Mal, wenn sich das Handy mit dem PC verbindet, wird seine
Sitzung erneuert, sodass sich wer die App nutzt nicht erneut anmelden muss,
und nach **60 Tagen ohne Verbindung** schließen sie sich von selbst (ein verlorenes Handy oder das einer
Person, die nicht mehr da ist). Der Administrator ändert diese Frist (30 bis 365 Tage)
im selben Fenster. Was das Handy noch nicht gesendet hat, geht nicht verloren: Es wird
nach der nächsten Anmeldung gesendet.

Die Spalte **Verbindung** zeigt, ob jedes Handy gerade **online** ist und
wann sein letzter Kontakt war. Die Apps melden sich alle paar Sekunden beim PC,
solange sie geöffnet sind (auch im Hintergrund), und beim vollständigen Schließen
melden sie sich ab, sodass der Status sofort aktuell ist.

### Autorschaft der Arbeiten

Jeder Eintrag speichert den Techniker, der ihn erstellt hat, egal ob er am PC angelegt wurde oder
vom Handy kam. Einträge aus der Zeit vor Einführung der Benutzerverwaltung
sind als **`Histórico`** (Altbestand) gekennzeichnet.

Auf dem Handy entscheidet **immer der Server** über die Zuordnung, anhand des Tokens
der Sitzung, nie anhand einer von der App gesendeten Angabe. Ein Gerät kann keine
Arbeiten im Namen einer anderen Person kennzeichnen.

Am PC kann ein Techniker nur seine eigenen Einträge im Verlauf bearbeiten oder löschen;
ein Administrator kann das bei allen. Mit Rechtsklick auf
eine oder mehrere Zeilen des Verlaufs (Mehrfachauswahl mit Strg/Umschalt) kann ein
Administrator außerdem **den Autor** gesammelt **neu zuweisen**, wobei jede
Änderung im Änderungsprotokoll festgehalten wird.

### Änderungsprotokoll (Audit)

Administratoren sehen unter `Werkzeuge` > `📋 Änderungsprotokoll`, **wer
was wann und von wo geändert hat** (vom PC oder von welchem Handy): Arbeiten, offene Arbeiten,
Erinnerungen, Checklisten, Maschinen und Ersatzteile, Artikel und Lagerstruktur,
Benutzer und Fachbereiche, Sicherheit (widerrufene Sitzungen, Sperren wegen
Fehlversuchen, Verschlüsselung, unverschlüsselte Verbindung), wiederhergestellte Sicherungen,
Importe und Einstellungen. Jede Änderung zeigt die betroffenen Felder
**vorher → nachher**. Filterbar nach Kategorie, Aktion, Benutzer und Zeitraum,
durchsuchbar nach Text und exportierbar als Excel oder CSV.

### Verlauf der Lagerprüfungen

Jeden Tag schlägt MantPro Stock vor, 5 zufällige Lagerartikel zu prüfen. Die Anwendung hält fest, **wer es getan hat, wann und ob alle 5 geprüft wurden**, mit der gezählten Menge im Vergleich zur Menge im System (auch ohne Verbindung: Es wird gesendet, sobald sich das Handy wieder verbindet). Administratoren sehen es unter `Werkzeuge` > `📦 Verlauf der Lagerprüfungen`: ✅ vollständig, ⚠️ unvollständig oder ❌ nicht geprüft, mit Filtern nach Benutzer, Zeitraum und Status sowie Export als Excel oder CSV. Gab es an den letzten 7 Arbeitstagen einen Tag ohne Prüfung, weist MantPro die Administratoren beim Öffnen darauf hin (und markiert ihn im Verlauf rot), und der Verlauf zeigt, **welche Handys Prüfungen durchgeführt haben** und wann die letzte jedes Handys war.

### Sitzung auf dem Handy

Der Techniker meldet sich einmal an, und das Token bleibt auf dem Gerät gespeichert. Die
Sitzung schließt sich von selbst, wenn der Administrator den Benutzer deaktiviert oder sein
Passwort zurücksetzt; dann kehrt die App zum Anmeldebildschirm zurück, **ohne die
noch nicht hochgeladenen Einträge zu verlieren**.

Das Sitzungstoken wird im **Android Keystore** (sicherer Speicher) abgelegt, nicht im Klartext. Nach **5 Fehlversuchen** hintereinander wird dieser Benutzer 15 Minuten gesperrt (ein Handy nach 20 Fehlversuchen); die App zeigt, wie lange zu warten ist. Im Fenster des PCs sperren 5 Fehlversuche die Anmeldung für eine Minute.

---

## 🏭 Maschinen

> Verwaltung in der Desktop-Anwendung; die Verknüpfung mit der
> Maschine lässt sich auch auf dem Handy beim Erfassen oder Bearbeiten einer
> Arbeit wählen.

Reiter „🏭 Maschinen“ am PC, gedacht, um Störungen und
Einsätze jeder Anlage über die Zeit im Blick zu behalten.

- **🌳 Maschinenbaum**: Maschinen können Untermaschinen haben (zum
  Beispiel eine Linie mit mehreren Anlagen) und bilden eine Hierarchie, so tief
  wie nötig
- **📅 Arbeiten nach Jahr und Monat**: Beim Aufklappen einer Maschine erscheinen die
  Jahre mit Arbeiten, beim Aufklappen eines Jahres die Monate; jede Ebene zeigt einen
  Zähler ihrer Arbeiten, mit Nachladen bei Bedarf, damit der Baum
  nicht langsam wird
- **🖱️ Direkter Zugriff auf die Arbeit**: Ein Doppelklick auf eine Arbeit im
  Baum öffnet direkt ihr Bearbeitungsfenster
- **📸 Foto der Maschine**: Jede Maschine oder Untermaschine kann ein Foto
  haben, das beim Auswählen in einem Feld neben dem Baum erscheint
- **🔗 Verknüpfung aus jeder Arbeit**: Beim Erfassen einer neuen Arbeit (PC oder Handy)
  oder beim Bearbeiten einer vorhandenen lässt sich wählen, zu welcher Maschine/Untermaschine sie gehört
- **📊 In den Exporten**: Die verknüpfte Maschine oder Untermaschine erscheint als
  zusätzliche Spalte in den Exporten als PDF, CSV und Excel
- **🗺️ Geerbte Zone**: Eine neue Untermaschine übernimmt standardmäßig die Zone
  ihrer übergeordneten Maschine
- **🔩 Ersatzteile jeder Maschine**: Unter dem Baum stehen die
  Lagerartikel, die in der ausgewählten Maschine verbaut sind, wie viele, ihr Bestand (rot,
  wenn unter Minimum), ihr Lagerort und eine Notiz (zum Beispiel „Motorseite“). Sie
  werden mit „➕ Ersatzteil hinzufügen“ hinzugefügt, als PDF oder Excel exportiert, und ein Doppelklick
  springt zum Artikel im Lager
- **🏷️ QR-Etiketten**: Die Schaltfläche „🏷️ QR-Etiketten“ erzeugt ein PDF auf A4-Bögen
  mit 24 Etiketten zu 70 × 37 mm (für die ausgewählte Maschine, mit ihren
  Untermaschinen oder für alle). Beim Scannen mit der App MantPro öffnet sich der Steckbrief
  der Maschine
- **📟 Zähler**: Die Schaltfläche „📟 Zähler“ verwaltet Betriebsstunden, Zyklen
  oder km der ausgewählten Maschine (ein Administrator legt sie an), mit ihrer letzten
  Ablesung, der mittleren Nutzung pro Tag und dem Ablesungsverlauf. Die zählerbasierten
  Wartungen beziehen ihre Ablesungen von hier
- **🔍 Ähnliche Namen**: Beim Anlegen oder Umbenennen einer Maschine weist es darauf hin, wenn es auf derselben
  Ebene bereits eine mit gleichem oder sehr ähnlichem Namen gibt

---

## 📦 Lagerbestand

> Vollständige Verwaltung in der Desktop-Anwendung; Abfrage und
> Bewegungen sind auch auf dem Handy möglich (`mantpro_stock_app`). Der Lagerbestand liegt
> in einer eigenen Datenbank (`almacen.db`), unabhängig von der der
> Wartungsarbeiten.

### Lagerstruktur

Das Lager ist in drei Ebenen gegliedert, angelehnt an die üblichen
Konventionen zur Kennzeichnung von Lagerplätzen:

```
Regal → Fachboden → Fach
```

- Beim Anlegen eines Regals legen Sie die **Anzahl der Fachböden**, die **Anzahl der
  Fächer pro Fachboden** (0 = keine vordefinierten Fächer, sie lassen sich später
  hinzufügen) fest und ob es einen **Bodenplatz** unter dem untersten Fachboden hat, der
  als besonderer Fachboden („Boden“) verwaltet wird
- Die Fachböden werden von unten nach oben ab 1 nummeriert, damit
  neue Fachböden hinzukommen können, ohne die vorhandenen neu zu nummerieren
- Ein Regal, ein Fachboden oder ein Fach lässt sich nicht löschen, solange dort
  Material eingelagert ist

Die Struktur wird über die Schaltfläche **„⚙️ Lager einrichten“** im
Reiter „📦 Lagerbestand“ verwaltet, die **nur für Administratoren** sichtbar ist.

### Material

- Anlegen und Bearbeiten mit Code (optional), Name, Beschreibung, Einheit, Mindestbestand,
  Lagerort (Regal / Fachboden / Fach) und **Foto**
- Suche nach **Name, Code, Beschreibung oder Lagerort**
- Der Bestand wird **rot** hervorgehoben, wenn er unter dem Minimum liegt, **grün**,
  wenn er darüber liegt, und in der Standardfarbe, wenn er genau dem Minimum entspricht,
  am PC wie auf dem Handy
- Durch Auswahl mehrerer Materialien gleichzeitig (Strg/Umschalt + Rechtsklick) am
  PC lassen sie sich gesammelt **an einen anderen Lagerort verschieben** oder **löschen**
- Jedes Material zeigt, **in welchen Maschinen es** als Ersatzteil **verwendet wird**, und beim Anlegen
  oder Bearbeiten lassen sich ihm direkt Maschinen zuordnen, mit der Menge, die
  jede enthält
- Beim Anlegen oder Bearbeiten eines Materials erscheint ein Hinweis, wenn es bereits eines mit **demselben Code
  oder einem sehr ähnlichen Namen** gibt, um es nicht doppelt anzulegen

### Zugänge, Abgänge und Umlagerungen

- **Jeder Benutzer** kann Zu- und Abgänge erfassen; nur die
  Einrichtung der Lagerstruktur ist Administratoren vorbehalten
- Jede Bewegung wird mit Datum, Menge, Benutzer und optionalem
  Grund erfasst, sichtbar im Verlauf bei jedem Material
- Manuell erfasste Abgänge (PC oder `mantpro_stock_app`) dürfen
  den Bestand nicht ins Negative bringen
- Auch eine Änderung des Lagerorts eines Materials wird in seinem
  Verlauf festgehalten, als Bewegung der Art **Umlagerung** (von welchem Fach in welches
  Fach)
- Die Schaltfläche **„📜 Verlauf“** zeigt alle Bewegungen des Lagers
  nacheinander (Zugänge, Abgänge und Umlagerungen), mit dem Namen jedes Artikels und
  Filtern nach Text und Art

### Bei einer Arbeit verbrauchtes Material (MantPro)

Beim Erledigen einer Arbeit in der App **MantPro** (Handy) lässt sich das
verwendete Material hinzufügen, gesucht nach Name oder Code und mit Angabe der
Menge. Beim Speichern der Arbeit wird dieses Material automatisch
vom Lager abgebucht, mit dem Grund „Verbraucht bei Arbeit: ...“, damit
die Rückverfolgbarkeit erhalten bleibt.

Anders als bei manuellen Abgängen **kann diese Abbuchung den
Bestand ins Negative bringen**: Das Material wurde für die Arbeit bereits tatsächlich verbraucht,
auch wenn nicht genug Bestand erfasst war, daher wäre es sinnlos, die
Bewegung zu sperren. Der negative Bestand ist am PC wie
in `mantpro_stock_app` zu sehen und ist ein Hinweis, dieses Material so bald wie möglich
zu prüfen und nachzufüllen.

### Warnungen bei Bestand unter Minimum

Der Reiter **„⚠️ Bestand unter Minimum“** zeigt in einer eigenen Ansicht das
Material ohne Bestand oder unter dem festgelegten Minimum. Der Titel des
Reiters zeigt, wie viele Materialien eine Warnung haben, und von dort lässt sich
direkt zum Material im „Lagerbestand“ springen oder ein Zugang erfassen,
ohne den Reiter zu wechseln, oder die Liste mit der Schaltfläche „📄 Exportieren“ exportieren.

### Bestand exportieren

Im Reiter **„📦 Lagerbestand“** am PC öffnet die Schaltfläche **„📄 Exportieren“**
ein Fenster, um das **Format** (PDF, CSV oder Excel) und **was exportiert wird** zu wählen:
das ganze Lager, eine Zone oder ein einzelnes Regal. Die Liste ist nach
Lagerort sortiert, damit Sie damit in der Hand durch das Lager gehen können; PDF und
Excel enthalten zusätzlich das Datum, die Anzahl der Materialien und wie viele unter
dem Minimum liegen (rot). Die Bestandstabelle selbst ist ebenfalls standardmäßig nach
Lagerort sortiert (Regal 1, 2… 10).

---

## 🔄 Synchronisierung PC–Handy

### Funktionsweise

MantPro verwendet ein Synchronisierungssystem auf Basis von:

1. **Flask-Server**, integriert in die Desktop-Anwendung
2. **QR-Codes** für eine schnelle und sichere Verbindung
3. **Per Token authentifizierte REST-API**: Alle Datenendpunkte verlangen eine
   gültige Sitzung; wird das Token ungültig, antwortet der Server mit `401`, und das
   Handy kehrt zur Anmeldung zurück
4. **Lokales WLAN** – kein Internet nötig
5. **Vollständige Synchronisierung beim Öffnen der App**, im Hintergrund und ohne die
   Oberfläche zu blockieren
6. Solange die Handy-Apps geöffnet sind, auch im Hintergrund,
   synchronisieren sie weiter, und der PC sieht sie **online** unter `Werkzeuge > 🔐
   Gerätesitzungen`
7. Die erste Synchronisierung zeigt einen **Fortschrittsbalken** und lädt die
   Daten parallel und die Fotos zu je 4 herunter

> 🔒 Die Synchronisierung ist **verschlüsselt (HTTPS)**. Der PC erstellt sein eigenes Zertifikat,
> und dessen Fingerabdruck steht im QR-Code: Das Handy verbindet sich nur mit *diesem* PC, sodass niemand
> im WLAN den Datenverkehr mitlesen oder sich als dieser PC ausgeben kann. Bereits
> verbundene Handys wechseln beim Aktualisieren der App von selbst zu HTTPS.

### Netzwerkeinstellungen

Damit die Synchronisierung funktioniert:

- ✅ PC und Handy müssen im **selben WLAN** sein
- ✅ Die **Firewall** muss Verbindungen auf Port 5000 (oder dem eingestellten) erlauben
- ✅ Sie muss auch den **nächsten Port** erlauben (standardmäßig 5001), den die verschlüsselte Verbindung (HTTPS) nutzt
- ✅ Unter Windows müssen Sie eventuell eine Firewall-Ausnahme anlegen

### Fehlerbehebung

**Das Handy verbindet sich nicht mit dem PC:**
- Prüfen Sie, ob beide Geräte im selben Netz sind
- Prüfen Sie, ob der Server am PC aktiv ist (grünes Symbol)
- Deaktivieren Sie testweise vorübergehend die Firewall des PCs
- Erzeugen Sie den QR-Code neu und scannen Sie ihn erneut

**Ich kann mich auf dem Handy nicht anmelden:**
- Prüfen Sie, ob MantPro am PC geöffnet ist: Die Anmeldung wird dort geprüft
- Prüfen Sie Benutzer und Passwort mit dem Administrator; er kann es zurücksetzen
- Hat der PC eine neue IP-Adresse, scannen Sie den QR-Code direkt im Anmeldebildschirm erneut („Anderen PC verbinden“)

**Die App hat mich zum Anmeldebildschirm zurückgeschickt:**
- Das ist normal, wenn der Administrator Ihr Passwort zurückgesetzt oder Ihren Benutzer deaktiviert hat
- Ihre noch nicht hochgeladenen Einträge **gehen nicht verloren**: Melden Sie sich erneut an, dann werden sie synchronisiert

**Ich habe das Administratorpasswort vergessen:**
- Ein anderer Administrator kann es unter `Werkzeuge` > `👥 Benutzerverwaltung` zurücksetzen
- Gibt es keinen anderen Administrator, muss es direkt in
  der Tabelle `usuarios` der Datenbank zurückgesetzt werden

**Die Fotos werden nicht synchronisiert:**
- Prüfen Sie, ob auf der Festplatte des PCs genug Platz ist
- Prüfen Sie die Berechtigungen des Ordners `fotos_recibidas`
- Stellen Sie sicher, dass das Foto auf dem Handy korrekt gespeichert wurde

**Die tägliche Benachrichtigung über offene Erinnerungen kommt nicht an (Android):**
- Prüfen Sie, ob die Berechtigung für Benachrichtigungen erteilt ist: `Einstellungen → Apps → MantPro → Benachrichtigungen`
- Bei Herstellern wie **OPPO/Realme (ColorOS), Xiaomi (MIUI) oder Huawei** kann das System den geplanten Alarm beenden, obwohl die Berechtigung erteilt ist. Zusätzlich nötig:
  - `Einstellungen → Akku → Akkunutzung pro App → MantPro` → auf **„Keine Einschränkungen“** stellen
  - `Einstellungen → Akku → Autostart` → MantPro **aktivieren**
- Die Benachrichtigung wird bei jedem Öffnen des Dashboards neu bewertet; wenn Sie gerade eine Arbeit als erledigt markiert haben, öffnen Sie es erneut, damit sie korrekt abgebrochen/neu geplant wird.

**Die tägliche Benachrichtigung zur Bestandsprüfung kommt nicht an (MantPro Stock):**
- Es gelten dieselben Prüfungen wie bei MantPro (Benachrichtigungsberechtigung und Ausnahme von der Akkuoptimierung, siehe oben)
- Ist im Lager kein Material angelegt, erscheint keine Benachrichtigung: Das ist so gewollt
- Sie wird bei jeder Synchronisierung der App mit dem PC neu bewertet (beim Öffnen und alle 25 Sekunden, solange sie geöffnet ist)

**MantPro fragt beim Start nach einem Wiederherstellungsschlüssel:**
- Die Datenbanken sind verschlüsselt, und der Schlüsselbund des Systems hat ihren Schlüssel nicht mehr (System neu installiert, anderes Benutzerkonto…)
- Geben Sie den Wiederherstellungsschlüssel ein, der beim Aktivieren der Verschlüsselung angezeigt wurde; MantPro speichert ihn wieder im Schlüsselbund
- Haben Sie ihn nicht, lassen sich die Datenbanken nicht öffnen: Nehmen Sie `mantenimiento.db` und `almacen.db` aus dem Datenordner, öffnen Sie MantPro und stellen Sie eine Sicherung wieder her

**„Zu viele Fehlversuche“ bei der Anmeldung:**
- Nach mehreren falschen Passwörtern hintereinander wird die Anmeldung eine Zeit lang gesperrt (15 Minuten auf dem Handy, eine Minute am PC); warten Sie die angegebene Zeit oder bitten Sie einen Administrator, Ihr Passwort zurückzusetzen

### 🔒 Hinweis zur Sicherheit

Die Synchronisierung ist mit HTTPS verschlüsselt, und das Zertifikat des PCs wird über den
Fingerabdruck im QR-Code festgelegt. Während der Übergangszeit bedient der PC Apps älterer Versionen
weiterhin auch per HTTP auf dem eingestellten Port; HTTPS nutzt
den **nächsten Port** (zum Beispiel 5000 und 5001), daher müssen bei einer
Firewall beide geöffnet werden. Sollten Sie den Server jemals außerhalb
des lokalen Netzes erreichbar machen, tun Sie das über ein VPN.

Wenn alle Handys die aktualisierte App haben, deaktivieren Sie die unverschlüsselte
Verbindung unter `Werkzeuge > 🔐 Gerätesitzungen`: Die Spalte „Verschlüsselung“
zeigt, welche Handys sich noch ohne sie verbinden. Ab dann bedient der PC
nur noch über HTTPS.

Die Datenbanken lassen sich auch **verschlüsselt** speichern (`Werkzeuge >
Verschlüsselung der Datenbanken…`, SQLCipher): Der Schlüssel liegt im Schlüsselbund des
Systems, und es wird ein Wiederherstellungsschlüssel zum Notieren angezeigt. Standardmäßig
deaktiviert.

---

## 🌐 MantPro Cloud

> **Demnächst verfügbar.**

MantPro ist und bleibt **kostenlos und Open Source**: Alles, was in diesem README beschrieben ist, funktioniert auf Ihrem PC – ohne Konto, ohne Internetverbindung und ohne Begrenzung bei Technikern oder Maschinen.

**MantPro Cloud** wird ein **optionaler, kostenpflichtiger Dienst** für alle, die mehr als ein lokales Netzwerk brauchen:

- **Mehrere PCs mit denselben Daten**: Jeder PC behält seine eigene Datenbank und arbeitet offline; sobald er eine Verbindung hat, lädt er die Änderungen hoch und herunter.
- **Handys synchronisieren von überall** (4G oder jedes WLAN), nicht nur im Büronetz. Ist die Cloud nicht erreichbar, synchronisieren sie wie gewohnt mit dem PC.
- **Fotos und Videos in der Cloud**, gemeinsam für PCs und Handys.
- **Automatische Sicherungen außerhalb des Betriebs**, zusätzlich zu denen Ihres PCs.
- **30 Tage kostenlos testen.**

Ihre Daten bleiben Ihre Daten: Wenn Sie nicht mehr zahlen, arbeitet der PC mit allem weiter, was er lokal hat; er synchronisiert nur nicht mehr.

> 🎁 **Sonderpreis für die ersten Kunden:** Schreiben Sie an [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com) und erhalten Sie **30 % Rabatt in den ersten 6 Monaten** des Dienstes.

---

## 💾 Sicherungen

MantPro erstellt **automatische Sicherungen** (die Datenbanken und die Fotos als monatliche
inkrementelle ZIPs) beim Beenden, alle 2 Stunden, solange es geöffnet ist und es
Änderungen gibt, kurz nach dem Empfang von Handydaten und beim Öffnen, falls noch ungesicherte
Änderungen vorhanden sind. Unter `Datei > 🛡️ Automatische Sicherungen…` wählen Sie, wie oft, wie viele
aufbewahrt werden und einen **externen Ordner** (NAS, USB-Festplatte, Nextcloud/Dropbox…), in den
jede Sicherung zusätzlich geschickt wird. Nach jeder Sicherung wird **geprüft, ob sie sich
wiederherstellen lässt**, und die Statusleiste warnt, wenn etwas schiefgeht. Außerdem lässt sich eine **vollständige Sicherung von Hand**
über `Datei > Sicherung` erstellen und über `Datei > Wiederherstellen` wiederherstellen.
`Werkzeuge` bietet zudem, nicht mehr verwendete Fotos zu bereinigen und
Arbeiten zu löschen, die älter als ein bestimmter Zeitraum sind, immer mit vorheriger Sicherung.

🔒 Mit `Datei > Passwort der Sicherungen…` werden die Sicherungen **verschlüsselt** gespeichert
(AES-256 mit einem aus dem Passwort abgeleiteten Schlüssel): Eine Sicherung, die den Rechner verlässt
(USB, NAS, Cloud), lässt sich ohne Passwort nicht öffnen. Vergessen Sie das Passwort, lassen sich die
verschlüsselten Sicherungen nicht wiederherstellen.

Alle Details: [docs/copias-de-seguridad.md](docs/copias-de-seguridad.md)
(auf Englisch: [docs/backups.md](docs/backups.md)).

---

## 🤝 Mitwirken

Beiträge sind willkommen! Bevor Sie einen *Pull Request* öffnen, lesen Sie
[CONTRIBUTING.md](CONTRIBUTING.md): Dort steht, wie Änderungen vorbereitet werden (Sprachen,
Tests, Dateiköpfe) und welche **Beitragsvereinbarung
([CLA](CLA.md))** akzeptiert werden muss.

Die Struktur des Codes und der Datenbank steht in
[docs/desarrollo.md](docs/desarrollo.md) (auf Englisch:
[docs/development.md](docs/development.md)). Für Sicherheitslücken siehe
[SECURITY.md](SECURITY.md).

---

## 🧭 Roadmap

Was kommt, ohne Termine und ohne feste Reihenfolge:

- **Einkauf**: Bestellungen mit automatischem Lagerzugang und tatsächlichem Preis empfangen und auf nicht gesendete Bestellungen hinweisen
- **Unterschrift** beim Abschluss einer Arbeit (auch auf dem Handy)
- **Technische Dokumentation pro Maschine** (Handbücher, Pläne und Schaltpläne als PDF)
- **Kritikalität der Maschinen (ABC)**, um zu entscheiden, wo in die Instandhaltung investiert wird
- **Arbeitsanfragen** aus der Produktion oder anderen Abteilungen, die eine offene Arbeit anlegen
- **Push-Benachrichtigungen** für dringende Arbeiten
- **Mehrere PCs gleichzeitig**, Server ohne Fenster (Raspberry Pi, NAS, Docker) und Webzugang
- **Mehrere Standorte oder Werke** mit Daten und Kennzahlen pro Standort
- Weitere Sprachen (Italienisch…) und App für das iPhone

Gerade fertig: Deutsch in den drei Anwendungen, Videos in der Fotosammlung der Arbeiten, Bestellvorschlag und gespeicherte Bestellungen, Lieferanten und Stammlieferant jedes Artikels, Wartungskosten im Dashboard, zählerbasierte Wartungen (Betriebsstunden, Zyklen, km), Arbeitszeit und Arbeitskosten bei jeder Arbeit, verbrauchte Ersatzteile bei jeder Arbeit mit ihren Kosten pro Maschine, Checklisten bei Wartungen und Arbeiten, verschlüsselte Synchronisierung, Datenbanken und Sicherungen sowie ein umfassenderes Änderungsprotokoll.

Die Änderungen jeder Version stehen in [CHANGELOG.md](CHANGELOG.md). Fehlt Ihnen
etwas? Öffnen Sie ein [*Issue*](https://github.com/AnabasaSoft/MantPro/issues).

---

## 📄 Lizenz

Dieses Projekt steht unter der **GNU Affero General Public License v3.0 (AGPL-3.0)**.
Den vollständigen Text finden Sie in der Datei `LICENSE`.

Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft)

### Was das in der Praxis bedeutet

- ✅ Sie dürfen MantPro frei **nutzen**, auch in Ihrem Unternehmen und für kommerzielle Zwecke
- ✅ Sie dürfen den Code **studieren, ändern und weitergeben**
- ⚠️ Wenn Sie eine geänderte Version weitergeben, müssen Sie sie **ebenfalls unter der AGPL-3.0** veröffentlichen
- ⚠️ Wenn Sie MantPro (oder ein abgeleitetes Werk) **als Dienst über ein Netzwerk** anbieten, müssen Sie
  den Quellcode den Nutzern zur Verfügung stellen, auch wenn Sie keine
  ausführbare Datei weitergeben. Das ist der entscheidende Unterschied zur GPL v3
- ⚠️ Sie müssen die Copyright- und Lizenzhinweise beibehalten

### Lizenzhinweis

```
MantPro - Sistema de Mantenimiento Preventivo
Copyright (C) 2026 Daniel Serrano Armenta (AnabasaSoft)

Dieses Programm ist freie Software: Sie können es unter den Bedingungen der
GNU Affero General Public License, wie von der Free Software Foundation
veröffentlicht, weitergeben und/oder ändern, entweder gemäß Version 3 der
Lizenz oder (nach Ihrer Wahl) jeder späteren Version.

Dieses Programm wird in der Hoffnung verbreitet, dass es nützlich ist, aber
OHNE JEDE GEWÄHRLEISTUNG, sogar ohne die implizite Gewährleistung der
MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK. Weitere Einzelheiten
finden Sie in der GNU Affero General Public License.

Sie sollten zusammen mit diesem Programm eine Kopie der GNU Affero General
Public License erhalten haben. Falls nicht, siehe <https://www.gnu.org/licenses/>.
```

> **Hinweis zu kommerziellen Lizenzen**: AnabasaSoft ist alleiniger Inhaber des
> Urheberrechts an MantPro und kann denselben Code daher zu anderen
> Bedingungen als der AGPL anbieten. Wenn Sie MantPro in ein
> proprietäres Produkt integrieren möchten, nehmen Sie Kontakt auf.

---

## 📧 Kontakt

**AnabasaSoft**

- 📧 E-Mail: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com)
- 🌐 GitHub: [github.com/AnabasaSoft](https://github.com/AnabasaSoft)
- 💼 Projekt: [github.com/AnabasaSoft/MantPro](https://github.com/AnabasaSoft/MantPro)

---

## 🙏 Danksagungen

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/): plattformübergreifendes GUI-Framework für die Desktop-Anwendung
- [Flutter](https://flutter.dev/): SDK für die Handy-Apps
- [ReportLab](https://www.reportlab.com/): Erstellung von PDF-Berichten
- [SQLite](https://www.sqlite.org/): eingebettete Datenbank
- [Flask](https://flask.palletsprojects.com/): Web-Mikroframework für den Synchronisierungsserver
- Der Open-Source-Community für ihre Unterstützung und ihre Beiträge

---

<div align="center">

<img src="https://raw.githubusercontent.com/AnabasaSoft/MantPro/main/recursos/AnabasaSoft.png" alt="Anabasa Software" width="120"/>

**Mit ❤️ entwickelt von [Anabasa Software](https://anabasasoft.github.io)**

📧 E-Mail: [anabasasoft@gmail.com](mailto:anabasasoft@gmail.com) • 🌐 Portfolio: [anabasasoft.github.io](https://anabasasoft.github.io)

⭐ Wenn Ihnen dieses Projekt gefällt, geben Sie ihm einen Stern auf GitHub

</div>

<div align="center">
  <br/>
  <p><code>>_ sudo buy-me-a-coffee --theme=dark --force</code></p>
  <a href="https://www.buymeacoffee.com/danitxu" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-black.png" alt="Buy Me A Coffee" style="height: 50px !important;width: 180px !important; box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;">
  </a>
  <br/>
</div>
