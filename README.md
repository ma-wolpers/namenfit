# Namens-Trainer (CSV + Foto-Modus)

Ein Tkinter-basiertes Lerntool für Namen, Tischgruppen und Nachbar:innen.

- **CSV-Modus**: Tischgruppe + (optional, Level 2) Nachbar:innen
- **Foto-Modus**: Bild anzeigen, Name raten
- **Kombi-Modus**: Bild + Name + Tischgruppe + Nachbar:innen (sequentiell)
- **Multi-Quellen**: mehrere CSV-Dateien und mehrere Foto-Ordner gleichzeitig auswählbar
- **Adaptive Wiederholung**: Fehler kommen kurzfristig wieder, richtige Antworten mit wachsendem Abstand
- **Theme-Auswahl**: 5 gut lesbare Farbkonzepte über die Menüzeile im Quizfenster

---

## Quick Start (60 Sekunden)

1. Öffne den Ordner `namenfit`.
2. Doppelklick auf `start-namenfit.bat`.
3. Falls es der erste Start ist: einmal im Ordner-Terminal ausführen:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Danach reicht in der Regel wieder der Doppelklick auf `start-namenfit.bat`.

---

## Plattformhinweis (wichtig)

- Die beschriebenen Startwege sind **Windows-orientiert**.
- Besonders `start-namenfit.bat` und PowerShell-Befehle (`.venv\Scripts\Activate.ps1`) sind Windows-spezifisch.
- Auf macOS/Linux kann das Tool ggf. laufen, ist in dieser Anleitung aber nicht als Standard-Setup beschrieben.

---

## 1) Voraussetzungen

- Python **3.10+** (empfohlen 3.11+)
- Paket: `Pillow`

### Schnell-Check für Nicht-Programmierer:innen

1. Öffne den Projektordner `namenfit` im Explorer.
2. Rechtsklick in den Ordnerhintergrund → **Im Terminal öffnen**.
3. Führe diese Befehle genau nacheinander aus:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Wenn ein Befehl fehlschlägt, siehe Abschnitt **Häufige Probleme**.

---

## 2) Starten (einfachste Wege)

## Option A: Doppelklick (Windows)

- Doppelklick auf `start-namenfit.bat`
- Das Script nutzt automatisch die virtuelle Umgebung `.venv\Scripts\python.exe`, falls vorhanden.
- Falls keine venv gefunden wird, versucht es `py -3`.

## Option B: Terminal mit venv

```powershell
# im Projektordner 'namenfit' ausführen
.\.venv\Scripts\Activate.ps1
python namenfit.py
```

## Option C: als Modul

```powershell
# im Projektordner 'namenfit' ausführen
.\.venv\Scripts\Activate.ps1
python -m app
```

---

## 3) Kann ich einfach auf die Startdatei doppelklicken?

**Ja, empfohlen ist `start-namenfit.bat`** (nicht direkt `namenfit.py`).

Warum?

- `.bat` behandelt die Python-Auswahl robuster
- bei Fehlern bleibt das Fenster offen (`pause`), damit man die Meldung sieht
- direkte `.py`-Doppelklick-Ausführung hängt vom lokalen Python-File-Handler ab

---

## 4) Startbildschirm – so benutzt du ihn

1. Wähle eine oder mehrere CSV-Dateien und/oder Foto-Ordner.
2. Nutze bei Bedarf **Datei → Letzte ...**, um frühere Quellen schnell zu übernehmen.
3. Optional: Stelle unter **Lernen** dein Lernprofil ein.
4. Optional: Aktiviere unter **Debug** zusätzliche Anzeigen.
5. Klicke **Start**.

Hinweise:

- Der Modus wird automatisch aus deiner Auswahl bestimmt:
  - nur CSVs → CSV-Modus
  - nur Foto-Ordner → Foto-Modus
  - CSVs + Foto-Ordner → Kombi-Modus
- Wenn CSV/Fotos im Kombi-Modus nicht zusammenpassen, bekommst du eine verständliche Auswahl (neu wählen oder Schnittmenge starten).

## 4b) Menüs im Quiz

- **Ansicht → Farbkonzept**: Theme wählen.
- **Lernen → Lernprofil**: schnelle Presets (Einstieg, Prüfung, Nachlernen).
- **Lernen → Wiederholung / Schalter**: Feintuning für Relearn-Priorität, Intervallprofil und Durchmischung.
- **Lernen → Feedbackstil**: Rückmeldungen als sarkastisch, ermutigend oder neutral.
- **Debug**: optionale Zusatzanzeigen.

Details und Empfehlungen: [docs/lernprofil-kalibrierung.md](docs/lernprofil-kalibrierung.md)

Alle Lern-Einstellungen werden global gespeichert und beim nächsten Start wiederverwendet — auch bei anderen CSVs/Foto-Ordnern.

## 4c) Warum diese Lernoptionen? (kurz)

- **Retrieval Practice**: Aktives Erinnern stärkt Abrufbarkeit besser als reines Wiederlesen.
- **Spacing**: Wiederholungen mit Abstand sind nachhaltiger als geballtes Üben.
- **Interleaving**: Gemischte Abfolge hilft, Inhalte sicherer zu unterscheiden.
- **Metakognitive Kalibrierung**: "Richtig, aber langsam" wird gezielt nachtrainiert.
- Bei Namensaufgaben wird die Zeitbewertung dabei an die Namenslänge angepasst (längenfair).

Ausführlicher mit Praxisbeispielen: [docs/lernprofil-kalibrierung.md](docs/lernprofil-kalibrierung.md)

---

## 5) Was wird wo gespeichert?

## Fortschritt pro Training

- CSV-Modus: neben der CSV als versteckte Datei
  - Beispiel: `.meineklasse.csv.trainerlog.json`
- Foto-only-Modus: sessionbasiert im App-Datenordner (pfadunabhängig)
  - Windows: `%APPDATA%\Namenfit\photo_session_<id>.json`
- Mehrere Foto-Ordner: ebenfalls sessionbasiert im App-Datenordner
- Der Wiederholungsplan (`prompt_counter`, Fälligkeit, Intervall) wird in derselben Datei gespeichert.
- Neue Sitzungen starten mit einer zufälligen Intro-Reihenfolge der geladenen Personen.
- Diese Intro-Phase wird sofort unterbrochen, sobald fällige Relearn-Wiederholungen vorliegen.
- Personenhistorie bleibt erhalten und wirkt nach der Intro-Phase auf die adaptive Wiederholungslogik.

## Zuletzt geöffnete Quellen (global pro Rechner/User)

- In einem Benutzer-Datenordner:
  - Windows: `%APPDATA%\Namenfit\app_state.json`
  - Fallback (ohne APPDATA): `~/.namenfit/app_state.json`

Einträge werden automatisch bereinigt, wenn Dateien/Ordner nicht mehr existieren.

Zusätzlich werden dort globale Defaults gespeichert, z. B.:
- letztes gewähltes Level im Level-Dialog
- Lernprofil/Lernoptionen als Start-Standard
- Debug-Optionen (Debug-Panel, Pfadanzeige)

Bestehende ältere Dateien (`recent_sources.json`, `.recent_sources.json`) werden beim nächsten Start automatisch migriert.

---

## 6) Auf anderem Rechner einrichten

1. Ordner kopieren (oder Repo klonen)
2. Python installieren (bei Windows am besten von python.org, Option „Add Python to PATH“ aktivieren)
3. Im Projektordner `namenfit` ein Terminal öffnen
4. venv erstellen + Pakete installieren:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

5. Starten über:
  - Doppelklick auf `start-namenfit.bat`, oder
  - `python namenfit.py`

### Brauche ich die alte `.venv` vom anderen Rechner?

**Nein.** Eine venv ist systemabhängig. Auf neuem Rechner immer neu erstellen.

---

## 7) Häufige Probleme

## „Beim Start passiert nichts“

- Über `start-namenfit.bat` starten (zeigt Fehler im Fenster)
- prüfen, ob Python installiert ist: `py -3 --version`
- prüfen, ob Abhängigkeiten installiert sind: `pip show Pillow`
- im Projektordner ausführen (nicht in einem beliebigen anderen Ordner)

## „`py` wird nicht erkannt“

- Python ist nicht installiert oder nicht im PATH
- Workaround: Rechner neu starten nach Python-Installation
- Alternativ im Terminal testen: `python --version`

## „CSV enthält keine Personen“

- Header in Zeile 1
- Namen ab Zeile 2
- leere Zeilen/Zellen werden ignoriert

## „Keine übereinstimmenden Namen zwischen CSV und Fotos“

- Dateiname (ohne Endung) muss exakt dem Namen in der CSV entsprechen
- Beispiel: `Max Mustermann.jpg` ↔ `Max Mustermann`

## PowerShell blockiert Aktivierungsskripte

Temporär im aktuellen Terminal erlauben:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## 8) Entwicklung (optional)

Schneller Syntax-Check:

```powershell
python -m py_compile app/app.py app/config.py app/ui/ui.py app/ui/startup_dialog.py app/ui/phase_ui.py app/ui/learning_menu.py app/ui/level_dialog.py app/ui/ui_theme.py app/core/session.py app/core/solve_logic.py app/core/layout.py app/core/models.py app/core/quiz_texts.py app/core/feedback.py app/core/stats_format.py app/core/review_scheduler.py app/core/learning_profiles.py app/storage/progress.py app/storage/app_state_store.py
```

---

## 9) Lizenz / Hinweise

- Kein Cloud-Zwang, läuft lokal
- Daten bleiben lokal auf dem Rechner
- Für Bilder werden gängige Formate unterstützt (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`)

### OER-Lizenz

Dieses Material ist als **Open Educational Resource (OER)** veröffentlicht unter:

- **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**
- https://creativecommons.org/licenses/by-sa/4.0/

Copyright (c) 2026 Alex Wolpers
