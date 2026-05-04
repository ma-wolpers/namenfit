"""Orchestrator für den Namens-Trainer.

Dieses Modul hält bewusst nur den Ablauf zusammen:
1) Startdialog öffnen
2) Level wählen (falls nötig)
3) Runtime-Session aufbauen
4) Quiz starten

Fachlogik, Persistenz und UI-Teilbereiche liegen in eigenen Modulen.
"""

import tkinter as tk

from .bootstrap.wiring import build_gui_dependencies
from .core.models import LEVEL_1, LEVEL_2, MODE_COMBINED, MODE_CSV
from .core.session import CombinedSourceMismatchError, build_runtime_session
from .ui.dialog_services import messagebox
from .ui import ui
from .ui.startup_dialog import ask_data_source_dialog
from .ui.window_identity import configure_windows_process_identity


def _focus_window(window):
    if not window or not window.winfo_exists():
        return
    window.deiconify()
    window.lift()
    window.focus_force()


def main():
    """Startet die Anwendung robust und modular."""

    configure_windows_process_identity()

    dependencies = build_gui_dependencies()
    recent_store = dependencies.recent_store

    while True:
        selection = ask_data_source_dialog(recent_store)
        if not selection:
            return

        root = tk.Tk()
        _focus_window(root)

        selected_level = LEVEL_1
        if selection.mode in (MODE_CSV, MODE_COMBINED):
            selected_level = ui.ask_level(root, current_level=recent_store.get_last_level())
            if selected_level not in (LEVEL_1, LEVEL_2):
                root.destroy()
                return
            recent_store.set_last_level(selected_level)

        try:
            runtime = build_runtime_session(selection, selected_level)
        except CombinedSourceMismatchError as err:
            decision = messagebox.askyesno(
                "Unstimmige Namen",
                (
                    f"{err}\n\n"
                    f"Gemeinsame Einträge (Schnittmenge): {len(err.common_keys)}\n\n"
                    "Ja = nur mit Schnittmenge starten\n"
                    "Nein = zurück zur Auswahl"
                ),
                parent=root,
            )
            _focus_window(root)

            if not decision:
                root.destroy()
                continue

            try:
                runtime = build_runtime_session(
                    selection,
                    selected_level,
                    allow_intersection_on_mismatch=True,
                )
            except ValueError as retry_err:
                messagebox.showerror("Fehler", str(retry_err), parent=root)
                _focus_window(root)
                root.destroy()
                continue
        except ValueError as err:
            # Ungültige Quellen direkt aus Recent entfernen, wenn sie nicht mehr existieren.
            if "nicht gefunden" in str(err):
                for csv_path in selection.csv_paths:
                    recent_store.remove_invalid_path(csv_path, "csv")
                for photo_folder in selection.photo_folders:
                    recent_store.remove_invalid_path(photo_folder, "photos")

            messagebox.showerror("Fehler", str(err), parent=root)
            _focus_window(root)
            root.destroy()
            continue

        recent_store.register_many(selection.csv_paths, selection.photo_folders)
        recent_store.set_last_session_selection(
            selection.csv_paths,
            selection.photo_folders,
            prompt_limit=selection.prompt_limit,
        )
        initial_theme_key = recent_store.get_theme_key()
        debug_options = recent_store.get_debug_options()
        sound_options = recent_store.get_sound_options()
        level2_require_group_before_neighbors = (
            recent_store.get_level2_require_group_before_neighbors()
        )

        if isinstance(selection.learning_settings, dict):
            runtime.progress_store.apply_learning_settings(selection.learning_settings)

        root.title(runtime.title)
        ui.QuizApp(
            root,
            runtime.people,
            runtime.grid,
            selected_level,
            runtime.progress_store,
            runtime.mode,
            runtime.photo_map,
            runtime.ask_group_question,
            initial_theme_key,
            recent_store.set_theme_key,
            recent_store.set_learning_defaults,
            debug_options,
            recent_store.set_debug_options,
            selection.prompt_limit,
            sound_options,
            recent_store.set_sound_options,
            level2_require_group_before_neighbors,
            recent_store.set_level2_require_group_before_neighbors,
            shell_config=dependencies.shell_config,
        )
        root.mainloop()
        continue
