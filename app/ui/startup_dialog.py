"""Startdialog fÃ¼r Quellauswahl inkl. 'Zuletzt geÃ¶ffnet'."""

import os

from bw_libs.shared_gui_core import ensure_bw_gui_on_path

from ..config import DataSourceSelection
from .dialog_services import filedialog, messagebox
from .learning_menu import populate_learning_menu
from ..core.learning_profiles import (
    CUSTOM_PROFILE,
    get_profile_settings,
    normalize_learning_settings,
)
from .ui_theme import (
    DEFAULT_THEME,
    THEMES,
    apply_window_theme,
    get_theme,
    normalize_theme_key,
    populate_theme_menu,
    style_danger_button,
    style_primary_button,
    style_secondary_button,
)
from .window_identity import apply_window_icon


ensure_bw_gui_on_path()
from bw_gui.runtime import ui


def ask_data_source_dialog(recent_store):
    """Ã–ffnet den Startdialog und liefert eine Datenquellen-Auswahl oder None."""

    dialog = ui.Tk()
    apply_window_icon(dialog)
    dialog.title("Namens-Trainer starten")
    dialog.resizable(False, False)
    theme_key = normalize_theme_key(recent_store.get_theme_key())
    apply_window_theme(dialog, theme_key)

    def _focus_dialog_window():
        if not dialog.winfo_exists():
            return
        dialog.deiconify()
        dialog.lift()
        dialog.focus_force()

    def _theme():
        return get_theme(theme_key)

    prompt_limit_default = recent_store.get_prompt_limit_default()
    result = {
        "csv_paths": [],
        "photo_folders": [],
        "prompt_limit": prompt_limit_default,
        "confirmed": False,
    }
    recent_data = recent_store.load()
    learning_settings = normalize_learning_settings(
        recent_data.get("learning_defaults", {})
    )

    learning_profile_var = ui.StringVar(
        value=learning_settings.get("learning_profile", CUSTOM_PROFILE)
    )
    review_profile_var = ui.StringVar(
        value=learning_settings.get("review_profile", "mittel")
    )
    allow_immediate_repeat_var = ui.BooleanVar(
        value=bool(learning_settings.get("allow_immediate_repeat", False))
    )
    prioritize_urgent_var = ui.BooleanVar(
        value=bool(learning_settings.get("prioritize_urgent_repeats", True))
    )
    mix_new_cards_var = ui.BooleanVar(
        value=bool(learning_settings.get("mix_new_cards", False))
    )
    min_retrieval_seconds_var = ui.IntVar(
        value=int(learning_settings.get("min_retrieval_seconds", 0))
    )
    revisit_slow_correct_var = ui.BooleanVar(
        value=bool(learning_settings.get("revisit_slow_correct", False))
    )
    slow_correct_threshold_var = ui.IntVar(
        value=int(learning_settings.get("slow_correct_threshold_seconds", 6))
    )
    feedback_style_var = ui.StringVar(
        value=learning_settings.get("feedback_style", "ermutigend")
    )
    debug_options = recent_store.get_debug_options()
    debug_show_panel_var = ui.BooleanVar(
        value=bool(debug_options.get("show_debug_panel", False))
    )
    debug_show_paths_var = ui.BooleanVar(
        value=bool(debug_options.get("show_paths", False))
    )

    def _persist_learning_defaults():
        nonlocal learning_settings
        learning_settings = normalize_learning_settings(
            {
                "review_profile": review_profile_var.get(),
                "allow_immediate_repeat": allow_immediate_repeat_var.get(),
                "prioritize_urgent_repeats": prioritize_urgent_var.get(),
                "mix_new_cards": mix_new_cards_var.get(),
                "min_retrieval_seconds": min_retrieval_seconds_var.get(),
                "revisit_slow_correct": revisit_slow_correct_var.get(),
                "slow_correct_threshold_seconds": slow_correct_threshold_var.get(),
                "feedback_style": feedback_style_var.get(),
            }
        )
        recent_store.set_learning_defaults(learning_settings)
        learning_profile_var.set(
            learning_settings.get("learning_profile", CUSTOM_PROFILE)
        )

    def _sync_learning_vars_from_settings(settings):
        normalized = normalize_learning_settings(settings)
        review_profile_var.set(normalized.get("review_profile", "mittel"))
        allow_immediate_repeat_var.set(
            bool(normalized.get("allow_immediate_repeat", False))
        )
        prioritize_urgent_var.set(
            bool(normalized.get("prioritize_urgent_repeats", True))
        )
        mix_new_cards_var.set(bool(normalized.get("mix_new_cards", False)))
        min_retrieval_seconds_var.set(int(normalized.get("min_retrieval_seconds", 0)))
        revisit_slow_correct_var.set(
            bool(normalized.get("revisit_slow_correct", False))
        )
        slow_correct_threshold_var.set(
            int(normalized.get("slow_correct_threshold_seconds", 6))
        )
        feedback_style_var.set(normalized.get("feedback_style", "ermutigend"))
        learning_profile_var.set(normalized.get("learning_profile", CUSTOM_PROFILE))

    def _on_learning_profile_changed():
        selected = learning_profile_var.get()
        if selected == CUSTOM_PROFILE:
            return
        preset = get_profile_settings(selected)
        if not preset:
            return
        _sync_learning_vars_from_settings(preset)
        _persist_learning_defaults()

    def _on_review_profile_changed():
        _persist_learning_defaults()

    def _on_learning_toggles_changed():
        _persist_learning_defaults()

    def _on_min_retrieval_changed():
        _persist_learning_defaults()

    def _on_slow_correct_threshold_changed():
        _persist_learning_defaults()

    def _on_feedback_style_changed():
        _persist_learning_defaults()

    def _persist_debug_options():
        options = {
            "show_debug_panel": bool(debug_show_panel_var.get()),
            "show_paths": bool(debug_show_paths_var.get()),
        }
        recent_store.set_debug_options(options)

    def _on_debug_options_changed():
        _persist_debug_options()

    container = ui.Frame(dialog, bg=_theme()["bg_main"])
    container.pack(padx=14, pady=12)

    heading_label = ui.Label(
        container,
        text="SitzplÃ¤ne und/oder Fotos auswÃ¤hlen:",
        font=("Arial", 12, "bold"),
        bg=_theme()["bg_main"],
        fg=_theme()["fg_primary"],
    )
    heading_label.pack(anchor="w", pady=(0, 8))

    prompt_frame = ui.Frame(container, bg=_theme()["bg_main"])
    prompt_frame.pack(fill="x", pady=(0, 8))
    prompt_label = ui.Label(
        prompt_frame,
        text="RundenlÃ¤nge:",
        width=12,
        anchor="w",
        bg=_theme()["bg_main"],
        fg=_theme()["fg_primary"],
    )
    prompt_label.pack(side="left")

    prompt_choices = [
        ("Schnell (30)", 30),
        ("Mittel (80)", 80),
        ("Lang (200)", 200),
        ("Unendlich", None),
    ]

    def _prompt_to_label(limit):
        for label, value in prompt_choices:
            if value == limit:
                return label
        return "Mittel (80)"

    def _label_to_prompt(label):
        for option_label, value in prompt_choices:
            if option_label == label:
                return value
        return 80

    prompt_limit_var = ui.StringVar(value=_prompt_to_label(prompt_limit_default))

    def _on_prompt_limit_changed(*_args):
        selected_label = prompt_limit_var.get()
        selected_limit = _label_to_prompt(selected_label)
        result["prompt_limit"] = selected_limit
        recent_store.set_prompt_limit_default(selected_limit)

    prompt_menu = ui.OptionMenu(
        prompt_frame, prompt_limit_var, *[label for label, _ in prompt_choices]
    )
    style_secondary_button(prompt_menu, theme_key)
    prompt_menu.configure(width=20, anchor="w", highlightthickness=0, bd=0)
    prompt_menu.pack(side="left")
    prompt_limit_var.trace_add("write", _on_prompt_limit_changed)

    csv_frame = ui.Frame(container, bg=_theme()["bg_main"])
    csv_frame.pack(fill="x", pady=(0, 6))
    csv_label = ui.Label(
        csv_frame,
        text="CSV-Dateien:",
        width=12,
        anchor="w",
        bg=_theme()["bg_main"],
        fg=_theme()["fg_primary"],
    )
    csv_label.pack(side="left")
    csv_name_var = ui.StringVar(value="(nicht gewÃ¤hlt)")
    csv_name_label = ui.Label(
        csv_frame,
        textvariable=csv_name_var,
        width=34,
        anchor="w",
        bg=_theme()["bg_main"],
        fg=_theme()["fg_muted"],
    )
    csv_name_label.pack(side="left", padx=(2, 8))

    def _set_csv_label():
        csv_paths = result["csv_paths"]
        if not csv_paths:
            csv_name_var.set("(nicht gewÃ¤hlt)")
            return
        if len(csv_paths) == 1:
            csv_name_var.set(os.path.basename(csv_paths[0]))
            return
        csv_name_var.set(f"{len(csv_paths)} Dateien ausgewÃ¤hlt")

    csv_selected_frame = ui.Frame(container, bg=_theme()["bg_main"])
    csv_selected_frame.pack(fill="x", pady=(0, 6))

    def _remove_csv_path(path):
        target = os.path.normcase(os.path.abspath(path))
        result["csv_paths"] = [
            entry
            for entry in result["csv_paths"]
            if os.path.normcase(os.path.abspath(entry)) != target
        ]
        _set_csv_label()
        _render_csv_selected_items()

    def _render_csv_selected_items():
        for child in csv_selected_frame.winfo_children():
            child.destroy()

        for csv_path in result["csv_paths"]:
            row = ui.Frame(csv_selected_frame, bg=_theme()["bg_main"])
            row.pack(fill="x", pady=(0, 2))
            ui.Label(
                row,
                text=f"â€¢ {os.path.basename(csv_path)}",
                anchor="w",
                bg=_theme()["bg_main"],
                fg=_theme()["fg_muted"],
            ).pack(side="left", fill="x", expand=True)
            remove_button = ui.Button(
                row,
                text="X",
                width=2,
                command=lambda p=csv_path: _remove_csv_path(p),
            )
            style_danger_button(remove_button, theme_key)
            remove_button.pack(side="right")

    def choose_csv():
        dialog_kwargs = {
            "title": "CSV-Dateien auswÃ¤hlen",
            "filetypes": [("CSV Dateien", "*.csv")],
        }
        initial_csv_dir = recent_store.get_last_dialog_dir("csv_source")
        if initial_csv_dir:
            dialog_kwargs["initialdir"] = initial_csv_dir

        chosen = filedialog.askopenfilenames(**dialog_kwargs)
        _focus_dialog_window()
        if chosen:
            result["csv_paths"] = list(chosen)
            recent_store.set_last_dialog_dir("csv_source", result["csv_paths"][0])
            _set_csv_label()
            _render_csv_selected_items()

    choose_csv_button = ui.Button(csv_frame, text="WÃ¤hlenâ€¦", command=choose_csv)
    style_secondary_button(choose_csv_button, theme_key)
    choose_csv_button.pack(side="right")

    photo_frame = ui.Frame(container, bg=_theme()["bg_main"])
    photo_frame.pack(fill="x", pady=(0, 8))
    photo_label = ui.Label(
        photo_frame,
        text="Foto-Ordner:",
        width=12,
        anchor="w",
        bg=_theme()["bg_main"],
        fg=_theme()["fg_primary"],
    )
    photo_label.pack(side="left")
    photo_name_var = ui.StringVar(value="(nicht gewÃ¤hlt)")
    photo_name_label = ui.Label(
        photo_frame,
        textvariable=photo_name_var,
        width=34,
        anchor="w",
        bg=_theme()["bg_main"],
        fg=_theme()["fg_muted"],
    )
    photo_name_label.pack(side="left", padx=(2, 8))

    def _set_photo_label():
        folders = result["photo_folders"]
        if not folders:
            photo_name_var.set("(nicht gewÃ¤hlt)")
            return
        if len(folders) == 1:
            folder = folders[0]
            photo_name_var.set(os.path.basename(folder.rstrip("\\/")) or folder)
            return
        photo_name_var.set(f"{len(folders)} Ordner ausgewÃ¤hlt")

    photo_selected_frame = ui.Frame(container, bg=_theme()["bg_main"])
    photo_selected_frame.pack(fill="x", pady=(0, 8))

    def _remove_photo_folder(path):
        target = os.path.normcase(os.path.abspath(path))
        result["photo_folders"] = [
            entry
            for entry in result["photo_folders"]
            if os.path.normcase(os.path.abspath(entry)) != target
        ]
        _set_photo_label()
        _render_photo_selected_items()

    def _render_photo_selected_items():
        for child in photo_selected_frame.winfo_children():
            child.destroy()

        for folder in result["photo_folders"]:
            row = ui.Frame(photo_selected_frame, bg=_theme()["bg_main"])
            row.pack(fill="x", pady=(0, 2))
            label = os.path.basename(folder.rstrip("\\/")) or folder
            ui.Label(
                row,
                text=f"â€¢ {label}",
                anchor="w",
                bg=_theme()["bg_main"],
                fg=_theme()["fg_muted"],
            ).pack(side="left", fill="x", expand=True)
            remove_button = ui.Button(
                row,
                text="X",
                width=2,
                command=lambda p=folder: _remove_photo_folder(p),
            )
            style_danger_button(remove_button, theme_key)
            remove_button.pack(side="right")

    def add_photo_folder():
        dialog_kwargs = {"title": "Foto-Ordner auswÃ¤hlen"}
        initial_photo_dir = recent_store.get_last_dialog_dir("photo_source")
        if initial_photo_dir:
            dialog_kwargs["initialdir"] = initial_photo_dir

        chosen = filedialog.askdirectory(**dialog_kwargs)
        _focus_dialog_window()
        if chosen:
            normalized = os.path.abspath(chosen)
            existing_norm = {
                os.path.normcase(os.path.abspath(p)) for p in result["photo_folders"]
            }
            if os.path.normcase(normalized) not in existing_norm:
                result["photo_folders"].append(normalized)
            recent_store.set_last_dialog_dir("photo_source", normalized)
            _set_photo_label()
            _render_photo_selected_items()

    def clear_photo_folders():
        result["photo_folders"] = []
        _set_photo_label()
        _render_photo_selected_items()

    clear_photos_button = ui.Button(
        photo_frame, text="Leeren", command=clear_photo_folders
    )
    style_secondary_button(clear_photos_button, theme_key)
    clear_photos_button.pack(side="right")
    add_photo_button = ui.Button(
        photo_frame, text="HinzufÃ¼genâ€¦", command=add_photo_folder
    )
    style_secondary_button(add_photo_button, theme_key)
    add_photo_button.pack(side="right", padx=(0, 6))

    def validate_selection():
        if not result["csv_paths"] and not result["photo_folders"]:
            messagebox.showwarning(
                "Hinweis",
                "Bitte mindestens eine CSV-Datei oder einen Foto-Ordner auswÃ¤hlen.",
            )
            return False
        return True

    def _apply_last_session_selection():
        last_session = recent_store.get_last_session_selection()
        csv_paths = list(last_session.get("csv_paths", []))
        photo_folders = list(last_session.get("photo_folders", []))
        prompt_limit = last_session.get(
            "prompt_limit", recent_store.get_prompt_limit_default()
        )

        if not csv_paths and not photo_folders:
            return

        result["csv_paths"] = csv_paths
        result["photo_folders"] = photo_folders
        result["prompt_limit"] = prompt_limit
        prompt_limit_var.set(_prompt_to_label(prompt_limit))
        _set_csv_label()
        _set_photo_label()
        _render_csv_selected_items()
        _render_photo_selected_items()

    def on_start():
        if not validate_selection():
            return

        result["prompt_limit"] = _label_to_prompt(prompt_limit_var.get())
        recent_store.set_prompt_limit_default(result["prompt_limit"])
        result["confirmed"] = True
        dialog.quit()

    def on_cancel():
        dialog.quit()

    def on_resume_last(_event=None):
        before_csv = list(result["csv_paths"])
        before_photos = list(result["photo_folders"])
        _apply_last_session_selection()
        if result["csv_paths"] == before_csv and result["photo_folders"] == before_photos:
            messagebox.showwarning(
                "Hinweis", "Kein zuletzt gestarteter Spielmodus gespeichert."
            )
            return "break"
        result["confirmed"] = True
        dialog.quit()
        return "break"

    def _append_unique_path(items, path):
        normalized = os.path.normcase(os.path.abspath(path))
        existing_norm = {os.path.normcase(os.path.abspath(item)) for item in items}
        if normalized not in existing_norm:
            items.append(os.path.abspath(path))

    def on_pick_recent(csv_path=None, photo_folder=None):
        if csv_path and not os.path.isfile(csv_path):
            recent_store.remove_invalid_path(csv_path, "csv")
            messagebox.showwarning(
                "Hinweis",
                "Die Datei existiert nicht mehr und wurde aus der Liste entfernt.",
            )
            return

        if photo_folder and not os.path.isdir(photo_folder):
            recent_store.remove_invalid_path(photo_folder, "photos")
            messagebox.showwarning(
                "Hinweis",
                "Der Ordner existiert nicht mehr und wurde aus der Liste entfernt.",
            )
            return

        if csv_path and photo_folder:
            _append_unique_path(result["csv_paths"], csv_path)
            _append_unique_path(result["photo_folders"], photo_folder)
            _set_csv_label()
            _set_photo_label()
            _render_csv_selected_items()
            _render_photo_selected_items()
            return

        if csv_path:
            _append_unique_path(result["csv_paths"], csv_path)
            recent_store.set_last_dialog_dir("csv_source", csv_path)
            _set_csv_label()
            _render_csv_selected_items()

        if photo_folder:
            _append_unique_path(result["photo_folders"], photo_folder)
            recent_store.set_last_dialog_dir("photo_source", photo_folder)
            _set_photo_label()
            _render_photo_selected_items()

    button_frame = ui.Frame(container, bg=_theme()["bg_main"])
    button_frame.pack(fill="x", pady=(2, 0))
    start_button = ui.Button(button_frame, text="Start", command=on_start, width=12)
    style_primary_button(start_button, theme_key)
    start_button.pack(side="left")
    cancel_button = ui.Button(
        button_frame, text="Abbrechen", command=on_cancel, width=12
    )
    style_secondary_button(cancel_button, theme_key)
    cancel_button.pack(side="right")

    def _apply_theme():
        apply_window_theme(dialog, theme_key)
        current = _theme()

        container.configure(bg=current["bg_main"])
        heading_label.configure(bg=current["bg_main"], fg=current["fg_primary"])

        csv_frame.configure(bg=current["bg_main"])
        prompt_frame.configure(bg=current["bg_main"])
        prompt_label.configure(bg=current["bg_main"], fg=current["fg_primary"])
        csv_label.configure(bg=current["bg_main"], fg=current["fg_primary"])
        csv_name_label.configure(bg=current["bg_main"], fg=current["fg_muted"])
        csv_selected_frame.configure(bg=current["bg_main"])

        photo_frame.configure(bg=current["bg_main"])
        photo_label.configure(bg=current["bg_main"], fg=current["fg_primary"])
        photo_name_label.configure(bg=current["bg_main"], fg=current["fg_muted"])
        photo_selected_frame.configure(bg=current["bg_main"])

        button_frame.configure(bg=current["bg_main"])

        style_secondary_button(choose_csv_button, theme_key)
        style_secondary_button(prompt_menu, theme_key)
        style_secondary_button(clear_photos_button, theme_key)
        style_secondary_button(add_photo_button, theme_key)
        style_primary_button(start_button, theme_key)
        style_secondary_button(cancel_button, theme_key)

        _render_csv_selected_items()
        _render_photo_selected_items()

    theme_var = ui.StringVar(value=theme_key)

    def _on_theme_changed():
        nonlocal theme_key
        selected = theme_var.get()
        if selected not in THEMES:
            return
        theme_key = selected
        recent_store.set_theme_key(theme_key)
        _apply_theme()

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.bind("<Escape>", lambda _event: (on_cancel(), "break")[1])
    dialog.bind("z", on_resume_last)
    dialog.bind("Z", on_resume_last)
    dialog.update_idletasks()
    _build_start_menu(
        dialog,
        recent_data,
        on_pick_recent,
        theme_var,
        _on_theme_changed,
        learning_profile_var,
        review_profile_var,
        allow_immediate_repeat_var,
        prioritize_urgent_var,
        mix_new_cards_var,
        min_retrieval_seconds_var,
        revisit_slow_correct_var,
        slow_correct_threshold_var,
        feedback_style_var,
        _on_learning_profile_changed,
        _on_review_profile_changed,
        _on_learning_toggles_changed,
        _on_min_retrieval_changed,
        _on_slow_correct_threshold_changed,
        _on_feedback_style_changed,
        debug_show_panel_var,
        debug_show_paths_var,
        _on_debug_options_changed,
    )
    _apply_theme()
    _apply_last_session_selection()
    _focus_dialog_window()
    _center_dialog(dialog)

    dialog.mainloop()
    dialog.destroy()

    if not result["confirmed"]:
        return None

    return DataSourceSelection(
        csv_paths=tuple(result["csv_paths"]),
        photo_folders=tuple(result["photo_folders"]),
        prompt_limit=result.get("prompt_limit"),
        learning_settings=dict(learning_settings),
    )


def _build_start_menu(
    dialog,
    recent_data,
    on_pick_recent,
    theme_var,
    on_theme_changed,
    learning_profile_var,
    review_profile_var,
    allow_immediate_repeat_var,
    prioritize_urgent_var,
    mix_new_cards_var,
    min_retrieval_seconds_var,
    revisit_slow_correct_var,
    slow_correct_threshold_var,
    feedback_style_var,
    on_learning_profile_changed,
    on_review_profile_changed,
    on_learning_toggles_changed,
    on_min_retrieval_changed,
    on_slow_correct_threshold_changed,
    on_feedback_style_changed,
    debug_show_panel_var,
    debug_show_paths_var,
    on_debug_options_changed,
):
    menu_bar = ui.Menu(dialog)
    file_menu = ui.Menu(menu_bar, tearoff=0)
    view_menu = ui.Menu(menu_bar, tearoff=0)
    learning_menu = ui.Menu(menu_bar, tearoff=0)
    debug_menu = ui.Menu(menu_bar, tearoff=0)

    csv_menu = ui.Menu(file_menu, tearoff=0)
    _populate_recent_simple_menu(
        csv_menu,
        recent_data.get("csv", []),
        label_fn=lambda csv_path: os.path.basename(csv_path),
        command_fn=lambda csv_path: on_pick_recent(
            csv_path=csv_path, photo_folder=None
        ),
    )

    photo_menu = ui.Menu(file_menu, tearoff=0)
    _populate_recent_simple_menu(
        photo_menu,
        recent_data.get("photos", []),
        label_fn=lambda photo_folder: os.path.basename(photo_folder.rstrip("\\/"))
        or photo_folder,
        command_fn=lambda photo_folder: on_pick_recent(
            csv_path=None, photo_folder=photo_folder
        ),
    )

    combined_menu = ui.Menu(file_menu, tearoff=0)
    _populate_recent_combined_menu(
        combined_menu, recent_data.get("combined", []), on_pick_recent
    )

    file_menu.add_cascade(label="Letzte CSV-Dateien", menu=csv_menu)
    file_menu.add_cascade(label="Letzte Fotoordner", menu=photo_menu)
    file_menu.add_cascade(label="Letzte Kombinationen", menu=combined_menu)
    file_menu.add_command(label="SchlieÃŸen", command=dialog.quit)

    menu_bar.add_cascade(label="Datei", menu=file_menu, underline=0)
    populate_theme_menu(view_menu, theme_var, on_theme_changed)
    menu_bar.add_cascade(label="Ansicht", menu=view_menu, underline=0)
    populate_learning_menu(
        learning_menu,
        review_profile_var=review_profile_var,
        allow_immediate_repeat_var=allow_immediate_repeat_var,
        prioritize_urgent_var=prioritize_urgent_var,
        mix_new_cards_var=mix_new_cards_var,
        min_retrieval_seconds_var=min_retrieval_seconds_var,
        revisit_slow_correct_var=revisit_slow_correct_var,
        slow_correct_threshold_var=slow_correct_threshold_var,
        feedback_style_var=feedback_style_var,
        on_review_profile_changed=on_review_profile_changed,
        on_learning_toggles_changed=on_learning_toggles_changed,
        on_min_retrieval_changed=on_min_retrieval_changed,
        on_slow_correct_threshold_changed=on_slow_correct_threshold_changed,
        on_feedback_style_changed=on_feedback_style_changed,
        learning_profile_var=learning_profile_var,
        on_learning_profile_changed=on_learning_profile_changed,
    )
    menu_bar.add_cascade(label="Lernen", menu=learning_menu, underline=0)
    debug_menu.add_checkbutton(
        label="Debug-Panel im Quiz anzeigen",
        variable=debug_show_panel_var,
        command=on_debug_options_changed,
    )
    debug_menu.add_checkbutton(
        label="Dateipfade im Debug-Panel",
        variable=debug_show_paths_var,
        command=on_debug_options_changed,
    )
    menu_bar.add_cascade(label="Debug", menu=debug_menu, underline=0)
    dialog.config(menu=menu_bar)


def _populate_recent_simple_menu(menu, entries, label_fn, command_fn):
    """BefÃ¼llt ein UntermenÃ¼ mit einfachen Path-EintrÃ¤gen oder '(keine)'."""

    valid_entries = [entry for entry in entries if isinstance(entry, str)]
    if not valid_entries:
        menu.add_command(label="(keine)", state="disabled")
        return

    for entry in valid_entries:
        menu.add_command(
            label=label_fn(entry), command=lambda path=entry: command_fn(path)
        )


def _populate_recent_combined_menu(menu, entries, on_pick_recent):
    """BefÃ¼llt das Kombi-UntermenÃ¼ aus gespeicherten CSV+Foto-Paaren."""

    added = 0
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        csv_path = entry.get("csv")
        photo_folder = entry.get("photo")
        if not isinstance(csv_path, str) or not isinstance(photo_folder, str):
            continue
        csv_name = os.path.basename(csv_path)
        photo_name = os.path.basename(photo_folder.rstrip("\\/")) or photo_folder
        menu.add_command(
            label=f"{csv_name} + {photo_name}",
            command=lambda c=csv_path, p=photo_folder: on_pick_recent(
                csv_path=c, photo_folder=p
            ),
        )
        added += 1

    if added == 0:
        menu.add_command(label="(keine)", state="disabled")


def _center_dialog(dialog):
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    window_width = dialog.winfo_reqwidth()
    window_height = dialog.winfo_reqheight()
    x_pos = max(0, int((screen_width - window_width) / 2))
    y_pos = max(0, int((screen_height - window_height) / 3))
    dialog.geometry(f"+{x_pos}+{y_pos}")

