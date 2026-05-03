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

### Changed
- Wave-B-Integration gestartet: `app/ui/ui.py` nutzt jetzt zentrale Runtime-Shortcut-Registrierung mit `evaluate_runtime` und PopupPolicy-basiertem Dialogkontext.
- `app/ui/keybinding_registry.py` um `KeybindingRuntimeContext` und `evaluate_runtime` erweitert (mode-/offline-/textfokus-/dialogbasierte Aktivierungspruefung).
- Guardrails erweitert: `tools/ci/check_ai_guardrails.py` validiert die tatsaechliche Runtime-Integration in `app/ui/ui.py`.
- Governance erweitert: Feature-Arbeit wird als eigener Commit-Block gefuehrt, Push bleibt explizit manuell.
- Repo-Path-Guardrail fuer absolute JSON-Strings entfernt; Namenfit verlaesst sich hier auf die bestehende relative Pfadserialisierung im App-State-Store.
- Guardrails praezisiert: `CHANGELOG.md` wird nur bei nutzer- oder coentwicklerrelevanten Aenderungen erzwungen; Prozesswarnungen (Commit-/Push-Guidance) werden nur lokal ausgegeben.
