# Changelog

All notable user-facing changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Foundation for unified keyboard and popup governance: central modules `bw_libs/ui_contract/keybinding.py` and `bw_libs/ui_contract/popup.py` are now part of the app structure.
- New shortcut runtime debug popup in the Debug menu with compact active/disabled diagnostics and offline simulation (`Strg+Shift+D`, `Strg+Shift+O`).
- Runtime module tests for keybinding evaluation and popup policy stack behavior.

### Changed
- App startup now initializes the root window via shared `bw_gui.runtime.ui` aliases instead of importing `tkinter` directly in `app/app.py`.
- Window identity/icon helpers now use shared `bw_gui.runtime.ui` aliases in `app/ui/window_identity.py` instead of importing `tkinter` directly.
- Level selection and learning menu builders now use shared `bw_gui.runtime.ui` aliases (`app/ui/level_dialog.py`, `app/ui/learning_menu.py`) instead of direct `tkinter` imports.
- Main quiz UI wiring now uses shared `bw_gui.runtime` aliases (`ui`, `widgets`) in `app/ui/ui.py` instead of direct `tkinter` / `ttk` imports.
- Startup and source-selection dialogs now use shared `bw_gui.dialogs` services, reducing direct tkinter dialog coupling.
- Pilot integration for the shared GUI core started: Namenfit now resolves keybinding, popup, and HSM contracts through the shared `bw-gui` core (via submodule bridge).
- Test discovery is now limited to repository tests (`pytest.ini`) so submodule test suites are excluded from normal Namenfit test runs.
- Source-path persistence now uses only the future format (absolute source paths) without workspace-folder coupling; legacy `7THCLOUD_REL::` handling and old recent-file migration paths were removed.
- App path discovery in config/bootstrap/session is fully harmonized to shared `bw_libs.app_paths.AppPaths` without legacy migration branches.
- App identity metadata is now centralized in `app/app_info.py` and used as the source for startup shell identity and app-data folder naming.
- Startup wiring now goes through a centralized GUI dependency builder and applies a shared Tk shell lifecycle configuration (`bw_libs/app_shell.py`).
- Progress log persistence now uses the centralized atomic text writer, and app-state writes atomically via `bw_libs/app_paths.py`.
- Shared app path/atomic-write foundation introduced via `bw_libs/app_paths.py`; app-state persistence now uses the centralized atomic JSON writer.
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
