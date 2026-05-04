"""Level-Auswahldialog für den Namens-Trainer."""

from bw_libs.shared_gui_core import ensure_bw_gui_on_path

ensure_bw_gui_on_path()
from bw_gui.runtime import ui

from ..core.models import LEVEL_1, LEVEL_2
from .ui_theme import BG_MAIN, FG_PRIMARY, apply_window_theme, style_primary_button


def ask_level(root, current_level=None):
    """Zeigt einen robusten Level-Dialog an."""

    level_win = ui.Toplevel(root)
    level_win.title("Schwierigkeit auswählen")
    level_win.resizable(False, False)
    level_win.transient(root)
    level_win.deiconify()
    apply_window_theme(level_win)

    chosen_level = ui.IntVar(value=current_level or LEVEL_1)
    result_level = ui.IntVar(value=0)

    ui.Label(
        level_win,
        text="Mit welchem Level möchtest du spielen?",
        font=("Arial", 12),
        bg=BG_MAIN,
        fg=FG_PRIMARY,
    ).pack(padx=16, pady=(12, 8))

    ui.Radiobutton(
        level_win,
        text="Level 1: Tischgruppe raten",
        variable=chosen_level,
        value=LEVEL_1,
        font=("Arial", 11),
        bg=BG_MAIN,
        fg=FG_PRIMARY,
        selectcolor=BG_MAIN,
        activebackground=BG_MAIN,
        activeforeground=FG_PRIMARY,
    ).pack(anchor="w", padx=16, pady=2)

    ui.Radiobutton(
        level_win,
        text="Level 2: Tischgruppe + dahinter/davor/gegenüber",
        variable=chosen_level,
        value=LEVEL_2,
        font=("Arial", 11),
        bg=BG_MAIN,
        fg=FG_PRIMARY,
        selectcolor=BG_MAIN,
        activebackground=BG_MAIN,
        activeforeground=FG_PRIMARY,
    ).pack(anchor="w", padx=16, pady=2)

    def confirm():
        result_level.set(chosen_level.get())
        level_win.destroy()

    def on_close():
        result_level.set(0)
        level_win.destroy()

    start_button = ui.Button(level_win, text="Start", command=confirm)
    style_primary_button(start_button)
    start_button.pack(pady=(10, 12))

    level_win.protocol("WM_DELETE_WINDOW", on_close)
    level_win.update_idletasks()
    if level_win.winfo_exists():
        level_win.lift()
        level_win.focus_force()
    level_win.grab_set()
    root.wait_window(level_win)

    selected = result_level.get()
    return selected if selected in (LEVEL_1, LEVEL_2) else None
