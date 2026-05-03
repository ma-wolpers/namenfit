# Development Log (namenfit)

Dieses Dokument trackt technische Aenderungen fuer Feature- und Architekturarbeit.

Regel:
- Keine Feature- oder Architekturaenderung ohne Update in diesem Log.
- Bugfix-Only-Changes koennen ohne Eintrag erfolgen.

## [Unreleased]

### Added
- Guardrail-Basis eingefuehrt: `AGENTS.md`, `.github/copilot-instructions.md`, PR-Template und lokales/CI-faeiges Guardrail-Skript `tools/ci/check_ai_guardrails.py`.
- Zentrale UI-Basis fuer Tastatur- und Popup-Steuerung eingefuehrt: `app/ui/keybinding_registry.py` und `app/ui/popup_policy.py`.

### Changed
- Governance erweitert: Feature-Arbeit wird als eigener Commit-Block gefuehrt, Push bleibt explizit manuell.
