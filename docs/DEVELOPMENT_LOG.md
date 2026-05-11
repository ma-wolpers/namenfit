# Development Log (namenfit)

Dieses Dokument trackt technische Aenderungen fuer Feature- und Architekturarbeit.

Regel:
- Keine Feature- oder Architekturaenderung ohne Update in diesem Log.
- Bugfix-Only-Changes koennen ohne Eintrag erfolgen.

## [Unreleased]

### Added
- LaufKern-Bridge eingefuehrt: neues zentrales Modul `bw_libs/ui_contract/laufkern.py` (Shared-`bw_gui.laufkern`-Bridge mit lokalem Fallback) und Export ueber `bw_libs/ui_contract/__init__.py`; zusaetzlicher Regressionstest `tests/test_laufkern_bridge.py` fuer Manifestaufbau und Shortcut-basierte Reachability.
- Guardrail-Basis eingefuehrt: `AGENTS.md`, `.github/copilot-instructions.md`, PR-Template und lokales/CI-faeiges Guardrail-Skript `tools/ci/check_ai_guardrails.py`.
- Zentrale UI-Basis fuer Tastatur- und Popup-Steuerung eingefuehrt: `app/ui/keybinding_registry.py` und `app/ui/popup_policy.py`.
- Runtime-Debug-Popup fuer Shortcuts in der GUI (`Debug -> Shortcut-Runtime-Debug anzeigen`, `Strg+Shift+D`) inkl. Offline-Simulation (`Strg+Shift+O`) und tabellarischer Aktiv/Disabled-Gruende.
- Tests fuer zentrale Runtime-Module ergaenzt: `tests/test_keybinding_registry_runtime.py` und `tests/test_popup_policy_registry.py`.
- HSM-Contract-Modul `app/ui/hsm_contract.py` eingefuehrt (Intent-/Payload-Validierung, Transition-Regeln, Escape-Resolver).
- Zentralen Intent-Katalog in `app/ui/ui_intents.py` eingefuehrt und Runtime-Shortcuts darauf umgestellt.
- Tests `tests/test_hsm_contract.py` fuer Intent-Contract, Transition-Gates und Escape-Prioritaetskette hinzugefuegt.

### Changed
- Wave-2-Sunset-Gate aktiviert: `tools/ci/check_ai_guardrails.py` erlaubt `except ModuleNotFoundError` nur noch in den zentralen UI-Contract-Bridges (`bw_libs/ui_contract/keybinding.py`, `bw_libs/ui_contract/popup.py`, `bw_libs/ui_contract/hsm.py`, `bw_libs/ui_contract/laufkern.py`) und blockiert neue lokale Fallback-Zweige ausserhalb dieser Baseline.
- LaufKern-Runtime-Auswertung in den produktiven Shortcut-Debug-Flow integriert: `app/ui/ui.py` baut jetzt ein Manifest aus der Runtime-Shortcut-Registry, validiert es zentral und zeigt die aktuelle Intent-Reachability im Debug-Summary.
- LaufKern-Manifestaufbau aus der UI-Klasse in einen dedizierten Provider ausgelagert: `app/ui/laufkern_manifest_provider.py` erzeugt jetzt den deklarativen Runtime-Manifestzustand aus der Shortcut-Registry.
- LaufKern-Tracking an produktiven Shortcut-Dispatch angebunden: `app/ui/ui.py` protokolliert ausgefuehrte Runtime-Intents jetzt als LaufKern-Tracking-Artefakte (done/failed) und zeigt den Completion-Status aus der Artefaktaggregation im Runtime-Debug.
- Step-6-Guardrail-Hardening umgesetzt: `tools/ci/check_ai_guardrails.py` blockiert jetzt zusaetzlich repo-weit lokale Neudefinitionen der reservierten Shared-Primitives `TkRootHost`, `ScrollablePopupWindow` und `WrappedTextField`, damit zentrale bw-gui-Bausteine nicht mehr als lokale Klassen nachgebaut werden.
- Step-5-Rollout fortgesetzt: `bw-gui`-Submodule auf den neuen Shared-Stand mit `TkRootHost`, `ScrollablePopupWindow` und `WrappedTextField` aktualisiert, sodass die zentralen Host-/Popup-/Form-Bausteine fuer Folge-Migrationen im Repo verfuegbar sind.
- Step-2-Guardrail-Scope abgeschlossen: die repo-weite GUI-Vertragspruefung in `tools/ci/check_ai_guardrails.py` umfasst jetzt zusaetzlich `bw_libs/`, sodass direkte `tkinter`/`ttk`-Imports und neue lokale `ui`/`widgets`/`tui`-Basisklassen auch in Shared-Library-Pfaden blockiert werden.
- Step-3-Exemption-Abbau fortgesetzt: Future-Entrypoint-Baseline fuer `app/ui/ui.py` entfernt; der Exemption-Backlog ist fuer Namenfit jetzt leer (nur `none`-Marker).
- Step-3-Exemption-Governance aktiviert: `docs/GUI_MIGRATION_BACKLOG.md` ist jetzt verbindliche Referenz fuer aktive GUI-Baselines/Exemptions inkl. `remove_by`-Datum; Guardrails validieren die Backlog-Referenzen explizit.
- Governance-Policy geschaerft: `AGENTS.md` und `.github/copilot-instructions.md` enthalten jetzt explizit die Strict-bw-gui-only-Regel (keine lokale tkinter/ttk-Widgetimplementierung in Repos; wiederverwendbare GUI-Bausteine zuerst in bw-gui).
- Repo-weite Strict-bw-gui-Guardrails eingefuehrt: `tools/ci/check_ai_guardrails.py` scannt jetzt alle GUI-Pythondateien unter `app/ui/` per AST, blockiert direkte `tkinter`/`ttk`-Imports und verhindert neue lokale Basisklassen auf `ui`/`widgets`/`tui`.
- Future-App-Guardrails erweitert: `tools/ci/check_ai_guardrails.py` prueft jetzt zusaetzlich neue GUI-Entrypoint-Dateien auf verpflichtenden Shared-GUI-Bootstrap (`ensure_bw_gui_on_path`, `bw_gui.runtime`, Shared-Menu/Dialog/Shortcut/Hover) und blockiert direkte `tkinter`-Imports.
- Guardrails gehaertet: `tools/ci/check_ai_guardrails.py` erzwingt in `app/ui/ui.py` verpflichtende Shared-UI-Contracts (Shared-Menue/Shared-Dialog/Shared-Hover) und blockiert Legacy-Fallbackzweige (`ModuleNotFoundError`, `_build_native_menu`, `None`-Guards).
- Nicht-Theme-Sonderpfade entfernt: `app/ui/ui.py` nutzt Shared-Menueleiste, Shared-Hover-Formatter und Shared-Settings-Dialog jetzt ohne nativen Fallback-Branch (`_build_native_menu`) oder optionale Modulguards.
- Theme-Sonderpfade entfernt: `app/ui/ui_theme.py` laedt die zentrale `bw_gui.theming`-Registry jetzt verbindlich und ohne optionalen Fallback-Branch auf fehlende Shared-Theme-Module.
- Welle-13-Theme-Pilot erweitert: `app/ui/ui_theme.py` merged die zentrale `bw_gui.theming`-Registry (`THEME_ORDER` + `get_theme`) in die lokale Namenfit-Theme-Liste und mappt Shared-Tokens auf den bestehenden Namenfit-Theme-Contract.
- Hover-Contract weitergezogen: auch die Runtime-Debug-Toolbar in `app/ui/ui.py` (Offline-Simulation + Aktualisieren) zeigt jetzt Shared-Tooltip-Hinweise statt unkommentierter Nebenaktionen.
- Hover-Contract in der Quiz-UI erweitert: `app/ui/ui.py` bindet zentrale Action-Buttons (`Aufloesen`, `Ups, vertippt`, `Weiter`, `Level wechseln`) an `SharedHoverTooltip` mit einheitlicher Shared-Shortcut-Formatierung.
- Theme-Sync fuer Hover-Overlays gehaertet: bei Themewechsel aktualisiert `_on_theme_changed` jetzt die `theme_key` aller aktiven Shared-Tooltips, damit Overlays visuell konsistent bleiben.
- Shared-Settings-Dialog integriert: `app/ui/ui.py` oeffnet jetzt einen tab-basierten `bw_gui.dialogs.open_tabbed_settings_dialog`-Flow (`Ansicht -> Einstellungen...`) fuer Theme-, Lern-, Debug-, Ton- und Sitzplan-Optionen.
- Runtime-Settings-Mapping verdrahtet: Shared-Dialog-Payload wird beim Commit auf die bestehenden Tk-Variablen/Handler (`_on_theme_changed`, Lern-/Debug-/Ton-Callbacks) zurueckgefuehrt, sodass Persistenz und Nebenwirkungen konsistent mit den bisherigen Menueaktionen bleiben.
- Shared-Menueleiste integriert: `app/ui/ui.py` baut das Hauptmenue jetzt primaer ueber `bw_gui.menu.CustomMenuBar` mit provider-basierten Menuedefinitionen (Ansicht/Lernen/Debug/Ton/Sitzplan) und behaelt einen nativen `ui.Menu`-Fallback fuer fehlende Shared-Menu-Module.
- Menueaktionen fuer Lern-/Debug-/Ton-/Sitzplan-Optionen wurden auf deklarative Shared-Menu-Items abgebildet (inkl. checked-Rows fuer bool/int-Optionen), sodass Runtime-Status beim Oeffnen dynamisch aus den zentralen Tk-Variablen gelesen wird.
- Shared-Tooltip-Polish uebernommen: `bw_gui.widgets.HoverTooltip` nutzt jetzt verzoegertes Anzeigen, Theme-Ableitung aus dem aktiven Fensterkontext sowie Bildschirm-Clamping fuer stabile Hover-Overlays.
- Shared-Theme-Feinschliff uebernommen: gemeinsame Settings-/Sidebar-Stile und verfeinerte Scrollbar-Kontraste kommen jetzt aus dem aktualisierten `bw-gui`-Submodule-Stand.
- Tk/ttk-Runtime-Pilotmigration erweitert: `app/ui/ui.py` nutzt jetzt zentrale Runtime-Aliases aus `bw_gui.runtime` (`ui`/`widgets`) statt direkter `tkinter`-/`ttk`-Imports.
- Tk-Runtime-Pilotmigration erweitert: `app/ui/level_dialog.py` und `app/ui/learning_menu.py` nutzen jetzt `bw_gui.runtime.ui` statt direkter `tkinter`-Imports.
- Tk-Runtime-Pilotmigration erweitert: `app/ui/window_identity.py` nutzt jetzt `bw_gui.runtime.ui`-Typen/Exceptions statt direktem `tkinter`-Import.
- Tk-Runtime-Pilotmigration erweitert: `app/app.py` nutzt jetzt `bw_gui.runtime.ui` fuer den Root-Window-Start statt direktem `tkinter`-Import.
- Tk-Runtime-Pilotmigration erweitert: `bw_libs/app_shell.py` nutzt jetzt `bw_gui.runtime.ui` statt direktem `tkinter`-Import.
- Tk-Runtime-Pilotmigration erweitert: `app/ui/startup_dialog.py` nutzt jetzt `bw_gui.runtime.ui` statt direktem `tkinter`-Import.
- Shared-Dialogmigration gestartet: zentrale Bridge `app/ui/dialog_services.py` auf `bw_gui.dialogs` eingefuehrt; `app/app.py` sowie `app/ui/startup_dialog.py` nutzen jetzt Shared `messagebox`/`filedialog`-Services statt direkter `tkinter`-Dialogimports.
- Pilotmigration zum gemeinsamen GUI-Core gestartet: `bw-gui` als Git-Submodule eingebunden und `bw_libs/ui_contract/*` via Bridge auf `bw_gui.contracts.*` umgestellt, sodass Keybinding-/Popup-/HSM-Vertraege aus der gemeinsamen Quelle geladen werden.
- Testsuche gehaertet: `pytest.ini` begrenzt die Sammlung auf `tests`, damit Submodule-Tests nicht unbeabsichtigt in Namenfit-Laeufe einfließen.
- Legacy-Modus abgeschlossen und deprecated: `app/storage/app_state_store.py` verarbeitet nur noch das Zukunftsformat (absolute Quellenpfade); 7thCloud-Relative-Prefix-Parsing und alte Recent-File-Migrationspfade wurden entfernt.
- Optional G2.3.3 abgeschlossen: app-spezifische Pfadauflosung in `app/config.py` auf zentrales `bw_libs.app_paths.AppPaths` harmonisiert; Bootstrap/Session nutzen jetzt die Shared-Discovery ohne Legacy-Migrationszweige.
- G5 abgeschlossen: AppIdentity-Manifest `app/app_info.py` eingefuehrt und fuer Startup-Metadaten (Window-Titel/AppData-Folder) als Single-Source in Bootstrap/Config verdrahtet.
- G3/G4 gestartet: GUI-Startup nutzt jetzt ein explizites Composition-Root (`app/bootstrap/wiring.py` mit `build_gui_dependencies()`/`AppDependencies`), und `QuizApp` verwendet die Shared-Shell-Basis `bw_libs/app_shell.py`.
- G2.2 erweitert: `app/storage/progress.py` nutzt jetzt zentrale Atomic-Text-Writes, und `app/storage/app_state_store.py` schreibt atomisch ueber `bw_libs/app_paths.py`.
- G2.1 gestartet: Shared-Modul `bw_libs/app_paths.py` eingefuehrt (AppPaths-Discovery sowie atomische JSON/Text-Write-Helfer).
- Persistenz-Pilot: `app/storage/app_state_store.py` nutzt jetzt die zentrale `atomic_write_json`-API.
- Guardrails beruecksichtigen `bw_libs/app_paths.py` als relevanten Shared-Pfad.
- UI-Contracts fuer Keybindings, Popup-Lifecycle und HSM wurden auf das Shared-Paket `bw_libs/ui_contract/` umgestellt; GUI und Tests importieren die Vertraege jetzt zentral statt aus lokalen Duplikatmodulen.
- Guardrails/Governance wurden auf `bw_libs/ui_contract`-Pfade umgestellt; `bw_libs/` wird bei Changelog-/Development-Log-Relevanz mitgeprueft.
- Runtime-Shortcut-Registrierung validiert Intents jetzt gegen den zentralen HSM-Contract; unbekannte Intents werden frueh als Konfigurationsfehler geblockt.
- Escape-Verhalten ist jetzt zentralisiert: Esc schliesst zunaechst aktive Popups und verlaesst danach Eingabefokus ohne Nebenpfade.
- Runtime-Debug-Popup laeuft jetzt als nicht mode-blockierendes Parallel-Popup (`dialog.non_blocking`); der Resolver wertet nur noch mode-blockierende Popups als Dialogkontext.
- Wave-B-Integration gestartet: `app/ui/ui.py` nutzt jetzt zentrale Runtime-Shortcut-Registrierung mit `evaluate_runtime` und PopupPolicy-basiertem Dialogkontext.
- `app/ui/keybinding_registry.py` um `KeybindingRuntimeContext` und `evaluate_runtime` erweitert (mode-/offline-/textfokus-/dialogbasierte Aktivierungspruefung).
- Guardrails erweitert: `tools/ci/check_ai_guardrails.py` validiert die tatsaechliche Runtime-Integration in `app/ui/ui.py`.
- Governance erweitert: Feature-Arbeit wird als eigener Commit-Block gefuehrt, Push bleibt explizit manuell.
- Repo-Path-Guardrail fuer absolute JSON-Strings entfernt; Namenfit verlaesst sich hier auf die bestehende relative Pfadserialisierung im App-State-Store.
- Guardrails praezisiert: `CHANGELOG.md` wird nur bei nutzer- oder coentwicklerrelevanten Aenderungen erzwungen; Prozesswarnungen (Commit-/Push-Guidance) werden nur lokal ausgegeben.
