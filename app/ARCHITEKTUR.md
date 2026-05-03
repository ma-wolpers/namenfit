# NamenFit – Architektur (app)

Dieses Dokument beschreibt die modulare Aufteilung von NamenFit im Paket `app`.

## Paketstruktur

```text
app/
├─ app.py
├─ config.py
├─ ui/
│  ├─ startup_dialog.py
│  ├─ ui.py
│  ├─ phase_ui.py
│  ├─ level_dialog.py
│  ├─ learning_menu.py
│  ├─ keybinding_registry.py
│  ├─ popup_policy.py
│  └─ ui_theme.py
├─ core/
│  ├─ session.py
│  ├─ layout.py
│  ├─ models.py
│  ├─ solve_logic.py
│  ├─ quiz_texts.py
│  ├─ feedback.py
│  ├─ stats_format.py
│  ├─ review_scheduler.py
│  └─ learning_profiles.py
└─ storage/
   ├─ progress.py
   └─ app_state_store.py
```

## Verantwortlichkeiten

- `app.py`
  - Startpunkt für den Laufzeitfluss.
  - Verbindet Startdialog, Session-Laden und Quiz-Fenster.

- `config.py`
  - App-Pfade und Konfigurationsdataklassen.

- `ui/*`
  - Tkinter-Interaktion, Dialoge, Layout-Zustände und Theming.
  - `ui.py` orchestriert den Quizablauf.
  - `startup_dialog.py` kapselt Quellenauswahl und Start-Defaults.
  - `keybinding_registry.py` ist die zentrale Registry fuer modebasierte Tastatursteuerung.
  - `popup_policy.py` ist die zentrale Policy fuer Popup-Lifecycle, Fokus und Escape-Verhalten.

- `core/*`
  - Domänenlogik ohne direkte Tkinter-Abhängigkeit.
  - `session.py` baut den Runtime-Kontext.
  - `solve_logic.py`, `stats_format.py`, `feedback.py` kapseln Auswertung/Text.
  - `learning_profiles.py` und `review_scheduler.py` kapseln Lernsteuerung.

- `storage/*`
  - Persistenz pro Training (`progress.py`) und globaler App-Status (`app_state_store.py`).

## Datenfluss pro Aufgabe

1. `ui/ui.py` wählt nächste Person und setzt Phase.
2. Nutzerantworten werden in Widgets erfasst.
3. `ui/ui.py` ruft `core/solve_logic.py` zur fachlichen Auswertung auf.
4. `storage/progress.py` aktualisiert Lernstand und Wiederholungsplan.
5. `core/stats_format.py` erzeugt Statistiktexte.
6. `core/feedback.py` liefert eine kontextabhängige Reaktion.
7. `ui/phase_ui.py` stellt den nächsten Eingabezustand ein.

## Qualitätsziel

Die GUI bleibt wartbar, weil UI, Domänenlogik und Persistenz klar getrennt sind.
