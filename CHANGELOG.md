# Changelog

All notable user-facing changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Foundation for unified keyboard and popup governance: central modules `bw_libs/ui_contract/keybinding.py` and `bw_libs/ui_contract/popup.py` are now part of the app structure.
- New shortcut runtime debug popup in the Debug menu with compact active/disabled diagnostics and offline simulation (`Strg+Shift+D`, `Strg+Shift+O`).
- Runtime module tests for keybinding evaluation and popup policy stack behavior.

### Changed
- Central UI contracts for keybindings, popup policy, and HSM semantics now live in shared `bw_libs/ui_contract` modules to avoid duplicate maintenance.
- Escape now follows centralized runtime behavior: active popups are closed first, then input focus is exited consistently.
- Runtime shortcuts now validate intents against a central HSM contract before execution.
- Shortcut intent semantics are now sourced from a central UI intent catalog.
- The shortcut runtime debug popup now opens as a non-blocking parallel popup and no longer pushes shortcut resolution into dialog mode.
- Global quiz shortcuts are now routed through a centralized runtime keybinding resolver with mode/offline/text-focus/dialog evaluation.
- Keybinding registry now exposes a shared runtime context and evaluate API for consistent activation reasons.
- Guardrail checks now verify runtime integration in the UI layer (not only module existence).
- Governance checks now enforce changelog updates only for user- or co-developer-relevant changes; commit/push process hints are local-only and no longer emitted in CI logs.
- Repository path guardrail for absolute JSON path strings was removed to keep enforcement aligned with Namenfit's existing relative-path persistence behavior.
