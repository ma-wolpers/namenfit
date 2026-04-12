# Lernprofil, Kalibrierung, Theme & Debug

Diese Seite erklärt die Menüoptionen im Quizfenster im Detail.

## Lernpsychologischer Hintergrund (kurz & praxisnah)

- **Retrieval Practice (aktives Erinnern)**
  - Lernen wird robuster, wenn du aktiv aus dem Gedächtnis abrufst.
  - Im Tool unterstützen das u. a. die Auflöse-Logik und die Mindest-Denkzeit.

- **Spacing (verteilte Wiederholung)**
  - Inhalte bleiben länger erhalten, wenn Wiederholungen zeitlich verteilt sind.
  - Im Tool passiert das über den Wiederholungsplan (fällige Karten/Intervalle).

- **Interleaving (Durchmischung)**
  - Gemischte Abfolgen fördern Unterscheidung ähnlicher Inhalte.
  - Im Tool entspricht das besonders der Option „Neue Fotos trotz fälliger Wiederholungen beimischen“.

- **Metakognitive Kalibrierung**
  - "Ich konnte es gerade so" ist nicht gleich sichere Beherrschung.
  - Im Tool hilft „Langsame richtige Antworten früher wiederholen".

## 1) Lernprofil (schnelle Voreinstellungen)

Menü: **Lernen → Lernprofil**

- **Preset: Einstieg**
  - Für regelmäßiges Üben mit klarer Relearn-Priorität.
  - Gut, wenn du neu startest oder eine Gruppe erstmal breit abdecken willst.
- **Preset: Prüfungsvorbereitung**
  - Höhere Wiederholungsdichte und strengeres Abfragen.
  - Nutzt eine mittlere Mindest-Denkzeit (`3s`) statt maximaler Bremse.
  - Gut kurz vor Tests oder Lernzielkontrollen.
- **Preset: Intensives Nachlernen**
  - Fehlerfokus mit schneller Wiederholung.
  - Direkte Doppel-Prompts bleiben standardmäßig aus, Relearn kommt trotzdem schnell zurück.
  - Gut, wenn viele Unsicherheiten in kurzer Zeit geschlossen werden sollen.
- **Individuell (manuell)**
  - Wird automatisch aktiv, wenn du einzelne Schalter/Werte vom Preset abweichend einstellst.

## 2) Wiederholung und Schalter

Menü: **Lernen → Wiederholung / Schalter**

### Wiederholungsprofil

- **Leicht / Mittel / Stark**
  - Steuert Relearn-Dichte und Intervallwachstum.
  - Stark = engere Relearn-Phasen und langsamere Freigabe in große Abstände.

### Zusätzliche Schalter

- **Gleicher Name darf direkt wiederkommen**
  - Aktiv: dieselbe Person kann direkt im nächsten Prompt auftauchen.
  - Inaktiv: nach Möglichkeit kein direkter Doppel-Prompt.

- **Fehler-Relearn priorisieren**
  - Falsch beantwortete Personen laufen in eine Relearn-Phase und werden vor normalen fälligen Karten bevorzugt.
  - Deaktiviert schwächt den Bonus nur ab; Relearn bleibt dennoch aktiv.

- **Neue Fotos trotz fälliger Wiederholungen beimischen**
  - Mischt nicht-fällige Karten zusätzlich ein.
  - Für sauberes Nachlernen besser deaktiviert lassen.
  - Auch wenn aktiviert, bleibt Wiederholung priorisiert; neue Fotos kommen nur gedrosselt hinzu.

- **Langsame richtige Antworten früher wiederholen (längenfair)**
  - Auch richtige, aber langsame Antworten kommen früher zurück.
  - Die Zeit wird bei Namensaufgaben an die Buchstabenlänge angepasst.

## 3) Abrufaufwand / Schwellen

Menü: **Lernen → Abrufaufwand** und **Lernen → Langsam-richtig-Schwelle (Basis)**

- **Mindest-Denkzeit** (`aus`, `2s`, `3s`, `5s`, `8s`)
  - Vor Ablauf kann nicht aufgelöst werden.
  - Verhindert zu frühes "Durchklicken".

- **Langsam-richtig-Schwelle (Basis)** (`≥ 4s`, `≥ 6s`, `≥ 8s`, `≥ 10s`)
  - Definiert die Basis-Schwelle für ungefähr 6 Buchstaben.
  - Längere Namen werden intern fair normalisiert, damit sie nicht systematisch als „zu langsam“ gelten.

## 4) Theme

Menü: **Ansicht → Farbkonzept**

- Theme kann jederzeit gewechselt werden.
- Auswahl bleibt zwischen Sitzungen erhalten.

Verfügbare Konzepte:
- Slate & Indigo
- Forest & Moss
- Sand & Terracotta
- Midnight & Cyan
- Lavender & Graphite
- Obsidian & Gold

## 5) Debug (optional)

Menü: **Debug**

- **Debug-Panel anzeigen**: zeigt zusätzliche Laufzeitinfos im Quizfenster.
- **Dateipfade im Debug-Panel**: ergänzt Pfadinfos für Diagnosezwecke.

Diese Optionen sind für Fehlersuche gedacht und im normalen Unterrichtseinsatz meist nicht nötig.

## 5b) Feedbackstil (Motivation)

Menü: **Lernen → Feedbackstil**

- **Ermutigend**
  - Fördert Selbstwirksamkeit und Durchhaltegefühl.
  - Sinnvoll für längere Lernphasen, sensible Gruppen oder wenn Motivation im Fokus steht.

- **Neutral**
  - Knappe, sachliche Rückmeldung ohne Tonfall-Effekt.
  - Sinnvoll, wenn möglichst nüchterne Diagnostik gewünscht ist.

- **Sarkastisch**
  - Humorvoller Stil wie bisher.
  - Kann motivieren, wenn die Gruppe diesen Ton mag; bei Unsicherheit besser auf ermutigend wechseln.

## 6) Persistenz (wichtig)

Die oben genannten Einstellungen werden global gespeichert und beim nächsten Start wiederverwendet – auch wenn du andere CSVs/Fotopfad-Kombinationen nutzt.

## 7) Session-Startlogik

- Zu Beginn einer neuen Übungssitzung startet NamenFit mit einer zufälligen Intro-Reihenfolge der aktuell geladenen Fotos/Namen.
- Sobald fällige Relearn-Karten vorhanden sind, wird diese Intro-Reihenfolge unterbrochen.
- Solange bereits eingeführte Karten noch nicht stabil sind (typisch: weniger als 4 richtige in Serie), werden neue Karten nur eingeschränkt oder gar nicht eingeführt.
- Gespeicherte Historie pro Person (Stabilität, Intervall, Relearn-Zustand) bleibt erhalten.
- Die Scheduler-Zeitleiste wird pro Session neu begonnen (kein Fortsetzen an der alten Prompt-Position).
- Die Historie bestimmt also nicht den Sessionstart, wirkt aber danach direkt auf die Wiederholungsauswahl.
