"""Namenfit-specific theme configuration.

Delegates to bw_gui.theming for the canonical theme registry and color math.
There is no local THEMES dict — all themes come from bw_gui.

``startup_dialog.py`` and ``level_dialog.py`` run a standalone ``ui.Tk()``
that does not inherit BwBaseWindow's automatic ttk-style registration.  The
``style_primary_button``, ``style_secondary_button``, ``style_danger_button``
functions therefore style raw ``tk.Button`` widgets directly and are kept here
for those two dialogs.

``BG_MAIN``, ``FG_PRIMARY``, ``FG_MUTED`` are module-level constants derived
from ``DEFAULT_THEME`` at import time.  ``level_dialog.py`` uses them as
construction-time defaults for labels that are not re-themed on theme switch.
"""

from __future__ import annotations

from bw_libs.shared_gui_core import ensure_bw_gui_on_path

ensure_bw_gui_on_path()

from bw_gui.runtime import ui
from bw_gui.runtime.platform import apply_window_chrome_theme
from bw_gui.theming import THEME_ORDER, normalize_theme_key as _normalize
from bw_gui.theming._theme_manager import get_theme as _bw_get_theme, is_dark_color

DEFAULT_THEME = "sand_terracotta"


def normalize_theme_key(theme_key=None) -> str:
    """Return *theme_key* if known in bw_gui's registry, otherwise ``DEFAULT_THEME``.

    Delegates to bw_gui so the full 13-theme registry is used for validation.
    Re-exported so ``app_state_store.py`` and ``progress.py`` do not need to
    change their import statements.
    """
    return _normalize(theme_key)


def get_theme(theme_key=None) -> dict:
    """Return the fully-resolved theme dict for *theme_key*.

    Wraps ``bw_gui.theming.get_theme()``, which fills semantic defaults and
    applies intensity scaling.  Re-exported so ``ui.py``, ``startup_dialog.py``,
    and other files that import ``get_theme`` from this module continue to work.
    """
    return _bw_get_theme(theme_key)


def apply_window_theme(window, theme_key=None) -> None:
    """Set *window*'s background to ``bg_main`` and apply Windows title-bar chrome.

    The chrome call is a no-op on non-Windows platforms.  Called by ``QuizApp``
    on every theme switch and from the startup/level dialogs at open time.
    """
    theme = get_theme(theme_key)
    window.configure(bg=theme["bg_main"])
    apply_window_chrome_theme(window, prefer_dark=is_dark_color(str(theme["bg_main"])))


def style_primary_button(button, theme_key=None) -> None:
    """Apply primary-action colors to a raw ``tk.Button``.

    Used by ``startup_dialog.py`` which runs in a standalone ``ui.Tk()`` that
    does not go through BwBaseWindow's ttk-style registration.  ``QuizApp``
    widgets use ``ttk.Button(style='PrimaryAction.TButton')`` instead.

    Args:
        button:    A ``tk.Button`` widget to configure in-place.
        theme_key: Active theme key; falls back to bw_gui's DEFAULT_THEME.
    """
    theme = get_theme(theme_key)
    button.configure(
        bg=theme["accent"],
        fg="#FFFFFF",
        activebackground=theme["accent_hover"],
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=10,
        pady=6,
        cursor="hand2",
    )


def style_secondary_button(button, theme_key=None) -> None:
    """Apply secondary-action colors to a raw ``tk.Button``.

    Same rationale as ``style_primary_button`` — used for ``startup_dialog.py``
    widgets that cannot use ttk styles.

    Args:
        button:    A ``tk.Button`` widget to configure in-place.
        theme_key: Active theme key.
    """
    theme = get_theme(theme_key)
    button.configure(
        bg=theme["accent_soft"],
        fg=theme["fg_primary"],
        activebackground=theme["border"],
        activeforeground=theme["fg_primary"],
        relief="flat",
        bd=0,
        padx=10,
        pady=6,
        cursor="hand2",
    )


def style_danger_button(button, theme_key=None) -> None:
    """Apply danger-action colors to a raw ``tk.Button``.

    Same rationale as ``style_primary_button``.  The background stays
    ``accent_soft`` (not the full danger color) to keep the startup dialog
    visually calm; the ``danger`` color is used for the foreground text only.

    Args:
        button:    A ``tk.Button`` widget to configure in-place.
        theme_key: Active theme key.
    """
    theme = get_theme(theme_key)
    button.configure(
        bg=theme["accent_soft"],
        fg=theme.get("danger", "#A73B3B"),
        activebackground=theme["border"],
        activeforeground=theme.get("danger", "#A73B3B"),
        relief="flat",
        bd=0,
        padx=6,
        pady=2,
        cursor="hand2",
    )


def populate_theme_menu(view_menu, theme_var, on_theme_changed) -> None:
    """Fill *view_menu* with a radio button for every available theme.

    Uses bw_gui's ``THEME_ORDER`` so the full 13-theme list (plus any program-
    specific themes registered at import time) is shown.  Called by
    ``startup_dialog.py`` which manages its own tk.Menu.

    Args:
        view_menu:        A ``tk.Menu`` instance to populate.
        theme_var:        A ``tk.StringVar`` that holds the current theme key.
        on_theme_changed: Callback invoked when the user selects a theme.
    """
    for theme_key in THEME_ORDER:
        theme = get_theme(theme_key)
        view_menu.add_radiobutton(
            label=str(theme.get("label", theme_key)),
            variable=theme_var,
            value=theme_key,
            command=on_theme_changed,
        )


# ── Construction-time constants (used by level_dialog.py) ──────────────────
# level_dialog.py creates labels at construction time without live re-theming.
# These constants give sensible initial values derived from DEFAULT_THEME.
_default = get_theme(DEFAULT_THEME)
BG_MAIN = _default["bg_main"]
FG_PRIMARY = _default["fg_primary"]
FG_MUTED = _default["fg_muted"]
