# Development Log (namenfit)

Dieses Dokument trackt technische Aenderungen fuer Feature- und Architekturarbeit.

Regel:
- Keine Feature- oder Architekturaenderung ohne Update in diesem Log.
- Bugfix-Only-Changes koennen ohne Eintrag erfolgen.

## [Unreleased]

### Added
- Guardrail-Basis eingefuehrt: `AGENTS.md`, `.github/copilot-instructions.md`, PR-Template und lokales/CI-faeiges Guardrail-Skript `tools/ci/check_ai_guardrails.py`.
- Zentrale UI-Basis fuer Tastatur- und Popup-Steuerung eingefuehrt: `app/ui/keybinding_registry.py` und `app/ui/popup_policy.py`.
- Runtime-Debug-Popup fuer Shortcuts in der GUI (`Debug -> Shortcut-Runtime-Debug anzeigen`, `Strg+Shift+D`) inkl. Offline-Simulation (`Strg+Shift+O`) und tabellarischer Aktiv/Disabled-Gruende.
- Tests fuer zentrale Runtime-Module ergaenzt: `tests/test_keybinding_registry_runtime.py` und `tests/test_popup_policy_registry.py`.
- HSM-Contract-Modul `app/ui/hsm_contract.py` eingefuehrt (Intent-/Payload-Validierung, Transition-Regeln, Escape-Resolver).
- Zentralen Intent-Katalog in `app/ui/ui_intents.py` eingefuehrt und Runtime-Shortcuts darauf umgestellt.
- Tests `tests/test_hsm_contract.py` fuer Intent-Contract, Transition-Gates und Escape-Prioritaetskette hinzugefuegt.

### Changed
- G5 abgeschlossen: AppIdentity-Manifest `app/app_info.py` eingefuehrt und fuer Startup-Metadaten (Window-Titel/AppData-Folder) als Single-Source in Bootstrap/Config verdrahtet.
- G3/G4 gestartet: GUI-Startup nutzt jetzt ein explizites Composition-Root (`app/bootstrap/wiring.py` mit `build_gui_dependencies()`/`AppDependencies`), und `QuizApp` verwendet die Shared-Shell-Basis `bw_libs/app_shell.py`.
- G2.2 erweitert: `app/storage/progress.py` nutzt jetzt zentrale Atomic-Text-Writes, und Legacy-Migrationen in `app/storage/app_state_store.py` schreiben atomisch ueber `bw_libs/app_paths.py`.
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
