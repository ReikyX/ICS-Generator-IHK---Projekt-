# 📅 ICS-Generator — IHK-Abschlussprojekt

> Eine webbasierte Anwendung zur einfachen Erstellung und zum Download von `.ics`-Kalenderdateien.  
> Kompatibel mit Google Calendar, Apple Kalender, Outlook und allen anderen Kalender-Apps.

---

## 📖 Was ist das hier?

Der **ICS-Generator** ist eine Webanwendung, mit der du ganz einfach Kalendereinträge erstellen und als `.ics`-Datei herunterladen kannst. `.ics` (iCalendar) ist ein universelles Format — jede Kalender-App der Welt versteht es.

**Warum das nützlich ist:**  
Statt einen Termin manuell in jeden Kalender einzutragen, erstellst du einmal eine `.ics`-Datei und kannst sie direkt importieren oder per Link teilen — für eine Person oder tausende.

Dieses Projekt wurde als **IHK-Abschlussprojekt** im Rahmen der Ausbildung zum Fachinformatiker entwickelt.

---

## ✨ Features

- 🖊️ **Termine erstellen** — Titel, Beschreibung, Datum, Uhrzeit und Ort eingeben
- 📥 **Download als `.ics`** — Direkt in den eigenen Kalender importierbar
- 🌐 **Webbasiert** — Kein Download nötig, läuft im Browser
- 📱 **Kompatibel** mit Google Calendar, Apple Kalender, Microsoft Outlook, Thunderbird und mehr

---

## 🛠️ Tech-Stack

| Bereich     | Technologie          |
|-------------|----------------------|
| Backend     | Python · Flask       |
| Frontend    | HTML · CSS · JavaScript |
| Ausgabe     | `.ics` / iCalendar-Format |

---

## 🚀 Installation & Starten

### Voraussetzungen

- Python **3.8+** installiert ([python.org](https://www.python.org/downloads/))
- `pip` (wird mit Python mitgeliefert)

### Schritt-für-Schritt

```bash
# 1. Repository klonen
git clone https://github.com/ReikyX/ICS-Generator-IHK---Projekt-.git
cd ICS-Generator-IHK---Projekt-

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Anwendung starten
python run.py
```

### Anwendung öffnen

Nach dem Start einfach im Browser aufrufen:

```
http://localhost:5000
```

---

## 📁 Projektstruktur

```
ICS-Generator-IHK---Projekt-/
│
├── app/                  # Flask-Anwendung (Routes, Logik, Templates)
│   ├── templates/        # HTML-Seiten (Jinja2)
│   ├── static/           # CSS, JavaScript, Bilder
│   ├── service/          # Parsing Logik
│   ├── model/            # Parsing Model
│   ├── __init__.py       # App-Initialisierung
│   └── routes.py         # Routen für Templates & Logik
│
├── run.py                # Einstiegspunkt — startet den Server
├── requirements.txt      # Python-Abhängigkeiten
├── .gitignore
└── README.md
```

---

## 💡 Wie es funktioniert

```
Nutzer gibt Termindaten ein
        ↓
Flask verarbeitet die Eingabe
        ↓
ICS-Datei wird serverseitig generiert
        ↓
Nutzer lädt die .ics-Datei herunter
        ↓
Datei direkt in Kalender-App importieren ✅
```

---

## 📆 Was ist eine `.ics`-Datei?

Eine `.ics`-Datei ist ein Textformat nach dem **iCalendar-Standard (RFC 5545)**. Sie sieht intern so aus:

```
BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Meeting mit dem Team
DTSTART:20240915T100000Z
DTEND:20240915T110000Z
LOCATION:Konferenzraum 1
DESCRIPTION:Wöchentliches Teammeeting
END:VEVENT
END:VCALENDAR
```

Diese Datei kann von jeder Kalender-Anwendung direkt importiert werden.

---

## 📄 Lizenz

Dieses Projekt steht unter der **MIT-Lizenz** — du kannst es frei verwenden, anpassen und weitergeben.

---

## 👤 Autor

**Erik Fries** — IHK-Abschlussprojekt  
GitHub: [@ReikyX](https://github.com/ReikyX)

---

> *Entwickelt als IHK-Abschlussprojekt im Ausbildungsberuf Fachinformatiker.*