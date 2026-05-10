"""Zentrale Theme-Verwaltung für NamenFit."""

from bw_libs.shared_gui_core import ensure_bw_gui_on_path


ensure_bw_gui_on_path()

try:
    from bw_gui.theming import THEME_ORDER as BASE_THEME_ORDER
    from bw_gui.theming import get_theme as get_base_theme
except ModuleNotFoundError:
    BASE_THEME_ORDER = ()
    get_base_theme = None


THEMES = {
    "slate_indigo": {
        "label": "Slate & Indigo",
        "bg_main": "#EEF1F6",
        "bg_surface": "#FFFFFF",
        "fg_primary": "#1F2937",
        "fg_muted": "#5B6472",
        "accent": "#4F46E5",
        "accent_hover": "#4338CA",
        "accent_soft": "#DDE1FF",
        "danger": "#A73B3B",
        "success": "#1F8F3A",
        "error": "#A73B3B",
        "border": "#C7CFDD",
    },
    "forest_moss": {
        "label": "Forest & Moss",
        "bg_main": "#EEF3EF",
        "bg_surface": "#FAFCFA",
        "fg_primary": "#21322A",
        "fg_muted": "#587265",
        "accent": "#3E7A5D",
        "accent_hover": "#33664E",
        "accent_soft": "#D7E6DD",
        "danger": "#A14D45",
        "success": "#2C8A4D",
        "error": "#A14D45",
        "border": "#BDD1C5",
    },
    "sand_terracotta": {
        "label": "Sand & Terracotta",
        "bg_main": "#F5EFE6",
        "bg_surface": "#FFF9F3",
        "fg_primary": "#3B3129",
        "fg_muted": "#7A6A5E",
        "accent": "#B8634F",
        "accent_hover": "#A45443",
        "accent_soft": "#EBD8CC",
        "danger": "#9B4A3B",
        "success": "#3D8D3D",
        "error": "#9B4A3B",
        "border": "#D9C7B8",
    },
    "midnight_cyan": {
        "label": "Midnight & Cyan",
        "bg_main": "#1E252D",
        "bg_surface": "#26313C",
        "fg_primary": "#EAF1F7",
        "fg_muted": "#B8C7D4",
        "accent": "#18A7C9",
        "accent_hover": "#1286A2",
        "accent_soft": "#2F3E4A",
        "danger": "#E08A7E",
        "success": "#4BCB74",
        "error": "#E08A7E",
        "border": "#435564",
    },
    "lavender_graphite": {
        "label": "Lavender & Graphite",
        "bg_main": "#F2F1F8",
        "bg_surface": "#FCFBFF",
        "fg_primary": "#302D39",
        "fg_muted": "#666174",
        "accent": "#6E5BC7",
        "accent_hover": "#5946B1",
        "accent_soft": "#E0DAF6",
        "danger": "#A84A66",
        "success": "#2F8A4F",
        "error": "#A84A66",
        "border": "#CBC4E7",
    },
    "obsidian_gold": {
        "label": "Obsidian & Gold",
        "bg_main": "#1C1D1F",
        "bg_surface": "#242629",
        "fg_primary": "#F3E9D2",
        "fg_muted": "#C7BDA8",
        "accent": "#C9A34A",
        "accent_hover": "#B28E3E",
        "accent_soft": "#34312A",
        "danger": "#D9886B",
        "success": "#6CCB6C",
        "error": "#D9886B",
        "border": "#4A4740",
    },
}

THEME_ORDER = [
    "slate_indigo",
    "forest_moss",
    "sand_terracotta",
    "midnight_cyan",
    "lavender_graphite",
    "obsidian_gold",
]


def _map_base_theme_to_namenfit(base: dict[str, str], fallback_key: str) -> dict[str, str]:
    """Map shared theme contract keys to Namenfit's local theme shape."""

    return {
        "label": str(base.get("label", fallback_key)),
        "bg_main": str(base["bg_main"]),
        "bg_surface": str(base["bg_surface"]),
        "fg_primary": str(base["fg_primary"]),
        "fg_muted": str(base["fg_muted"]),
        "accent": str(base["accent"]),
        "accent_hover": str(base.get("accent_hover", base["accent"])),
        "accent_soft": str(base["accent_soft"]),
        "danger": str(base.get("danger", "#A73B3B")),
        "success": str(base.get("success", "#2F8A4F")),
        "error": str(base.get("error", base.get("danger", "#A73B3B"))),
        "border": str(base["border"]),
    }


def _merge_base_theme_registry() -> None:
    if not BASE_THEME_ORDER or not callable(get_base_theme):
        return

    merged_order: list[str] = []
    seen: set[str] = set()

    for theme_key in THEME_ORDER:
        if theme_key not in seen:
            merged_order.append(theme_key)
            seen.add(theme_key)

    for theme_key in BASE_THEME_ORDER:
        if theme_key in seen:
            continue
        try:
            base = get_base_theme(theme_key)
        except Exception:
            continue
        THEMES.setdefault(theme_key, _map_base_theme_to_namenfit(base, theme_key))
        merged_order.append(theme_key)
        seen.add(theme_key)

    THEME_ORDER[:] = merged_order


_merge_base_theme_registry()

DEFAULT_THEME = "sand_terracotta"


def normalize_theme_key(theme_key=None):
    """Liefert einen gültigen Theme-Key oder das Default-Theme."""

    return theme_key if theme_key in THEMES else DEFAULT_THEME


def get_theme(theme_key=None):
    key = normalize_theme_key(theme_key)
    return THEMES[key]


def apply_window_theme(window, theme_key=None):
    theme = get_theme(theme_key)
    window.configure(bg=theme["bg_main"])


def style_primary_button(button, theme_key=None):
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


def style_secondary_button(button, theme_key=None):
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


def style_danger_button(button, theme_key=None):
    theme = get_theme(theme_key)
    button.configure(
        bg=theme["accent_soft"],
        fg=theme["danger"],
        activebackground=theme["border"],
        activeforeground=theme["danger"],
        relief="flat",
        bd=0,
        padx=6,
        pady=2,
        cursor="hand2",
    )


def style_entry(entry, theme_key=None):
    theme = get_theme(theme_key)
    entry.configure(
        bg=theme["bg_surface"],
        fg=theme["fg_primary"],
        insertbackground=theme["fg_primary"],
        relief="flat",
        highlightthickness=1,
        highlightbackground=theme["border"],
        highlightcolor=theme["accent"],
    )


def populate_theme_menu(view_menu, theme_var, on_theme_changed):
    """Befüllt ein Tkinter-Menu mit einheitlichen Theme-Radiobuttons."""

    for theme_key in THEME_ORDER:
        view_menu.add_radiobutton(
            label=THEMES[theme_key]["label"],
            variable=theme_var,
            value=theme_key,
            command=on_theme_changed,
        )


# Rückwärtskompatible Konstanten für bestehende Aufrufe ohne Theme-Key
_DEFAULT = get_theme(DEFAULT_THEME)
BG_MAIN = _DEFAULT["bg_main"]
FG_PRIMARY = _DEFAULT["fg_primary"]
FG_MUTED = _DEFAULT["fg_muted"]
