# Changelog

All notable user-facing changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Foundation for unified keyboard and popup governance: central modules `app/ui/keybinding_registry.py` and `app/ui/popup_policy.py` are now part of the app structure.
- New shortcut runtime debug popup in the Debug menu with compact active/disabled diagnostics and offline simulation (`Strg+Shift+D`, `Strg+Shift+O`).
- Runtime module tests for keybinding evaluation and popup policy stack behavior.

### Changed
- The shortcut runtime debug popup now opens as a non-blocking parallel popup and no longer pushes shortcut resolution into dialog mode.
- Global quiz shortcuts are now routed through a centralized runtime keybinding resolver with mode/offline/text-focus/dialog evaluation.
- Keybinding registry now exposes a shared runtime context and evaluate API for consistent activation reasons.
- Guardrail checks now verify runtime integration in the UI layer (not only module existence).
- Governance checks now enforce changelog updates only for user- or co-developer-relevant changes; commit/push process hints are local-only and no longer emitted in CI logs.
- Repository path guardrail for absolute JSON path strings was removed to keep enforcement aligned with Namenfit's existing relative-path persistence behavior.
