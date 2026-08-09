# Changelog

All notable user-facing changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Foundation for unified keyboard and popup governance: central modules `bw_libs/ui_contract/keybinding.py` and `bw_libs/ui_contract/popup.py` are now part of the app structure.
- New shortcut runtime debug popup in the Debug menu with compact active/disabled diagnostics and offline simulation (`Strg+Shift+D`, `Strg+Shift+O`).
- Runtime module tests for keybinding evaluation and popup policy stack behavior.

### Fixed
- Leertaste und Enter sprangen nach einer gelösten Aufgabe nicht zur nächsten Person (und Enter/Leertaste am Rundenende nicht zurück zum Startdialog): Der Tastatur-Fokus blieb nach dem Lösen auf dem inzwischen deaktivierten Antwortfeld stehen, wodurch der zentrale Shortcut-Runtime-Gate `<space>` als "Text-Eingabefeld fokussiert" blockierte; zusätzlich hatte `_on_enter` nie eine Verzweigung für den bereits gelösten Zustand. `_show_action_button()` setzt den Fokus jetzt explizit auf das Hauptfenster, sobald der "Weiter"-Button erscheint, `<space>` ist nicht mehr grundsätzlich vom Text-Eingabefeld-Gate betroffen, und `_on_enter` löst jetzt auch den Sprung zur nächsten Person aus.
- Namenfit stürzte potenziell beim Start des Quiz-Fensters ab: `ui_theme.py` importierte `get_theme`/`is_dark_color` noch aus dem inzwischen privatisierten `bw_gui.theming`-Modul (`ImportError`), und `QuizApp` wies `self.theme_key` nach der `BwBaseWindow`-Migration weiterhin direkt zu, obwohl es seither eine schreibgeschützte Property ist (`AttributeError`). `bw_libs/shared_gui_core.py` enthielt zusätzlich einen fehlenden `r`-Prefix am Docstring, der bei einem Windows-Pfad mit Backslashes einen `SyntaxError` auslöste und den Absturz noch vor dem eigentlichen Theme-Import verursachte.
- `bw_libs/shared_gui_core.py`: Docstring als Raw-String (`r"""`) markiert, damit der enthaltene Windows-Pfad nicht als ungültige Unicode-Escape-Sequenz geparst wird.

### Changed
- Lokale Theme-Daten entfernt; Quiz-Widgets auf ttk-Äquivalente umgestellt, damit Styling vollständig über den zentralen `bw_gui`-Theme-Mechanismus läuft.
- `QuizApp` auf `BwBaseWindow` aus `bw_gui` umgestellt; das redundante lokale Themeeinstellungs-Feld entfiel.
- Menueleiste auf den neuen zentralen bw-gui-Standardbaukasten umgestellt: Kernrubriken laufen jetzt konsistent ueber `Datei`, `Bearbeiten`, `Ansicht`, `Hilfe`; die app-spezifischen Menues `Lernen`, `Debug`, `Ton` und `Sitzplan` bleiben als Erweiterungssektionen erhalten.
- Settings-Flow auf einen zentralen bw-gui-Orchestrator umgestellt (`SettingsDialogOrchestrator`), damit Theme-/Lern-/Debug-/Ton-/Sitzplan-Einstellungen ueber einen einheitlichen Dialog-Einstiegspfad laufen.
- AI guardrails now emit non-blocking local warnings when configured core keyboard intents (for example quiz enter/space/typo, settings toggle, debug overlay/offline, escape) are present but matching shortcut binding markers are missing.
- UI contract bridges are now fully decommissioned to thin shared re-export shims (`bw_libs/ui_contract/keybinding.py`, `bw_libs/ui_contract/popup.py`, `bw_libs/ui_contract/hsm.py`, `bw_libs/ui_contract/laufkern.py`); dead local duplicate implementations were removed.
- AI guardrails now enforce a Phase-I decommission gate for UI contract bridges: each bridge must keep `ensure_bw_gui_on_path` plus shared `bw_gui` imports and may not reintroduce local contract class/function implementations.
- AI guardrails now enforce LaufKern fallback sunset Wave-3: local `ModuleNotFoundError` fallback branches were removed from the central contract bridges (`bw_libs/ui_contract/keybinding.py`, `bw_libs/ui_contract/popup.py`, `bw_libs/ui_contract/hsm.py`, `bw_libs/ui_contract/laufkern.py`), and fallback handlers are now forbidden repo-wide in guardrail scan scopes.
- Namenfit bindet jetzt eine zentrale LaufKern-Bridge (`bw_libs.ui_contract.laufkern`) fuer Manifest-, Reachability- und Tracking-Vertraege ein und bereitet damit die Trennung "Programm = Was" und "LaufKern = Wie" technisch vor.
- Die Shortcut-Runtime-Debug-Ansicht zeigt jetzt zusaetzlich eine LaufKern-Zusammenfassung zur aktuellen Intent-Erreichbarkeit (erreichbare Intents pro Runtime-Kontext und Manifest-Validierungsstatus).
- Der LaufKern-Manifestaufbau wurde in einen dedizierten Provider (`app/ui/laufkern_manifest_provider.py`) ausgelagert, damit Runtime-Integration (Wie) und app-spezifische Deklaration (Was) klar getrennt bleiben.
- Der produktive Shortcut-Dispatch protokolliert jetzt LaufKern-Tracking-Artefakte; das Runtime-Debug zeigt dazu einen Completion-Status aus der Artefaktaggregation.
- AI guardrails now enforce LaufKern fallback sunset Wave-2: `except ModuleNotFoundError` is only allowed in the central contract bridges (`bw_libs/ui_contract/keybinding.py`, `bw_libs/ui_contract/popup.py`, `bw_libs/ui_contract/hsm.py`, `bw_libs/ui_contract/laufkern.py`); new local fallback branches are rejected.
- AI guardrails now also block local redefinitions of reserved shared primitives (`TkRootHost`, `ScrollablePopupWindow`, `WrappedTextField`) so these runtime/dialog/widget foundations must be consumed from `bw-gui` instead of being rebuilt in-repo.
- `bw-gui` submodule was updated to the latest shared runtime/dialog/widget baseline so the new central primitives (`TkRootHost`, `ScrollablePopupWindow`, `WrappedTextField`) are available for further migration steps.
- AI guardrails now include `bw_libs/` in the repo-wide GUI contract scan scope, so direct `tkinter`/`ttk` imports and new local `ui`/`widgets`/`tui` baseclass patterns are also blocked in shared-library paths.
- AI guardrails no longer keep a future-entrypoint baseline exemption for `app/ui/ui.py`; Namenfit now runs this entrypoint under the strict shared-GUI contract checks.
- AI guardrails now require an explicit GUI migration backlog (`docs/GUI_MIGRATION_BACKLOG.md`) for active GUI baselines/exemptions, including time-bound `remove_by` tracking.
- Governance policy now explicitly requires strict bw-gui-only usage: no local tkinter/ttk widget implementations in repo modules, and reusable GUI building blocks must be implemented in bw-gui first.
- AI guardrails now enforce repo-wide strict bw-gui usage in `app/ui`: direct `tkinter`/`ttk` imports and new local `ui`/`widgets`/`tui` baseclass patterns are rejected via AST-based checks.
- AI guardrails now also enforce shared-GUI bootstrap requirements for any newly added GUI entrypoint files and reject direct tkinter imports in those entrypoints.
- AI guardrails were hardened to enforce mandatory shared UI contracts in `app/ui/ui.py` and fail fast on legacy fallback branches.
- Shared UI fallback branches were removed from `app/ui/ui.py`: menu rendering, hover help formatting, and shared tabbed settings now run without native/optional fallback paths.
- Theme special paths were removed from `app/ui/ui_theme.py`: Namenfit now requires the shared `bw_gui.theming` registry path directly and no longer keeps optional fallback branches for missing shared theming.
- Namenfit theme availability now also includes the shared `bw_gui.theming` registry; central themes are auto-mapped into the local Namenfit theme contract without replacing existing app-native themes.
- The runtime debug toolbar now also uses shared hover help overlays for offline simulation and refresh controls.
- Core quiz action buttons now use shared hover tooltips with consistent shortcut wording (solve/typo/next/level switch), and tooltip themes now update together with active app theme changes.
- A new tab-based shared settings dialog is now available from the main menu (`Ansicht -> Einstellungen...`) and centralizes runtime controls for theme, learning behavior, debug options, sound, and level-2 seat-group gating.
- Main menu rendering now uses the shared `bw_gui.menu.CustomMenuBar` with provider-based menu definitions for Ansicht/Lernen/Debug/Ton/Sitzplan, while retaining a native fallback path if shared menu modules are unavailable.
- Hover tooltips now appear with smoother delayed behavior, pick up the active app theme automatically, and stay fully visible on-screen.
- Shared settings/sidebar and scrollbar theming received a visual polish via the updated `bw-gui` baseline styles.
- App startup now initializes the root window via shared `bw_gui.runtime.ui` aliases instead of importing `tkinter` directly in `app/app.py`.
- Window identity/icon helpers now use shared `bw_gui.runtime.ui` aliases in `app/ui/window_identity.py` instead of importing `tkinter` directly.
- Level selection and learning menu builders now use shared `bw_gui.runtime.ui` aliases (`app/ui/level_dialog.py`, `app/ui/learning_menu.py`) instead of direct `tkinter` imports.
- Main quiz UI wiring now uses shared `bw_gui.runtime` aliases (`ui`, `widgets`) in `app/ui/ui.py` instead of direct `tkinter` / `ttk` imports.
- Shared shell setup now uses `bw_gui.runtime.ui` in `bw_libs/app_shell.py` instead of direct `tkinter` imports.
- Startup dialog UI construction now uses shared `bw_gui.runtime.ui` aliases in `app/ui/startup_dialog.py` instead of direct `tkinter` imports.
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
