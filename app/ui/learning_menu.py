"""Gemeinsamer "Lernen"-Menüinhalt für Startdialog und Quizfenster.

Beide Fenster nutzen bw-guis ``CustomMenuBar``; diese Funktion liefert die
``MenuItem``-Zeilen aus den Tk-Variablen des jeweiligen Fensters. Ein/Aus-
Einstellungen sind Switches (sofortige Wirkung, siehe bw-gui TOGGLE_CONTRACT),
Mehrfachoptionen Radio-Zeilen. Der Items-Provider wird bei jedem Öffnen neu
aufgerufen, zeigt also immer den aktuellen Zustand.
"""

from bw_libs.shared_gui_core import ensure_bw_gui_on_path

ensure_bw_gui_on_path()
from bw_gui.menu import MenuItem

from ..core.learning_profiles import (
    CUSTOM_PROFILE,
    FEEDBACK_STYLE_OPTIONS,
    LEARNING_PROFILE_ORDER,
    LEARNING_PROFILES,
    MIN_RETRIEVAL_OPTIONS,
    SLOW_CORRECT_THRESHOLD_OPTIONS,
)
from ..core.review_scheduler import REVIEW_PROFILES

_FEEDBACK_LABELS = {
    "sarkastisch": "Feedback: Sarkastisch",
    "ermutigend": "Feedback: Ermutigend",
    "neutral": "Feedback: Neutral",
}


def _set_var(tk_var, value, callback):
    """Setzt eine Radio-Auswahl (nur bei Änderung) und ruft den Handler auf."""

    if tk_var.get() != value:
        tk_var.set(value)
    if callable(callback):
        callback()


def _apply_switch(tk_var, requested, callback):
    """Übernimmt den vom Switch angeforderten Wert und ruft den Handler auf."""

    tk_var.set(bool(requested))
    if callable(callback):
        callback()


def _radio(label, tk_var, value, callback):
    """Eine Radio-Zeile, die *tk_var* auf *value* setzt."""

    return MenuItem(
        type="radio",
        label=label,
        checked=(tk_var.get() == value),
        command=lambda: _set_var(tk_var, value, callback),
    )


def _switch(label, tk_var, callback):
    """Eine Switch-Zeile für eine boolesche Einstellung mit sofortiger Wirkung."""

    return MenuItem(
        type="switch",
        label=label,
        checked=bool(tk_var.get()),
        on_toggle=lambda requested: _apply_switch(tk_var, requested, callback),
    )


def learning_menu_items(
    *,
    review_profile_var,
    allow_immediate_repeat_var,
    prioritize_urgent_var,
    mix_new_cards_var,
    min_retrieval_seconds_var,
    revisit_slow_correct_var,
    slow_correct_threshold_var,
    feedback_style_var,
    on_review_profile_changed,
    on_learning_toggles_changed,
    on_min_retrieval_changed,
    on_slow_correct_threshold_changed,
    on_feedback_style_changed,
    learning_profile_var=None,
    on_learning_profile_changed=None,
):
    """Liefert alle Lern-Controls als ``MenuItem``-Tupel (inkl. optionaler Presets).

    Args:
        review_profile_var: StringVar des Wiederholungsprofils.
        allow_immediate_repeat_var: BooleanVar "Gleicher Name darf direkt wiederkommen".
        prioritize_urgent_var: BooleanVar "Fehler-Relearn priorisieren".
        mix_new_cards_var: BooleanVar "Neue Fotos beimischen".
        min_retrieval_seconds_var: IntVar der Mindest-Denkzeit.
        revisit_slow_correct_var: BooleanVar "Langsame richtige Antworten früher wiederholen".
        slow_correct_threshold_var: IntVar der Langsam-richtig-Schwelle.
        feedback_style_var: StringVar des Feedbackstils.
        on_review_profile_changed: Handler nach Profilwechsel.
        on_learning_toggles_changed: Handler nach einem Ein/Aus-Schalter.
        on_min_retrieval_changed: Handler nach Änderung der Denkzeit.
        on_slow_correct_threshold_changed: Handler nach Änderung der Schwelle.
        on_feedback_style_changed: Handler nach Änderung des Feedbackstils.
        learning_profile_var: Optional StringVar des Lernprofils (Presets-Untermenü).
        on_learning_profile_changed: Handler nach Wechsel des Lernprofils.

    Returns:
        Die Menüzeilen in Anzeigereihenfolge.
    """

    items = []
    if learning_profile_var is not None and callable(on_learning_profile_changed):
        presets = [
            _radio(str(profile.get("label", key)), learning_profile_var, key, on_learning_profile_changed)
            for key in LEARNING_PROFILE_ORDER
            if (profile := LEARNING_PROFILES.get(key))
        ]
        presets.append(MenuItem(type="separator"))
        presets.append(_radio("Individuell (manuell)", learning_profile_var, CUSTOM_PROFILE, on_learning_profile_changed))
        items.append(MenuItem(type="submenu", label="Lernprofil", items=tuple(presets)))
        items.append(MenuItem(type="separator"))

    for key in ("leicht", "mittel", "stark"):
        profile = REVIEW_PROFILES.get(key)
        if profile:
            items.append(_radio(f"Wiederholungsprofil: {profile['label']}", review_profile_var, key, on_review_profile_changed))

    items.append(MenuItem(type="separator"))
    items.append(_switch("Gleicher Name darf direkt wiederkommen", allow_immediate_repeat_var, on_learning_toggles_changed))
    items.append(_switch("Fehler-Relearn priorisieren", prioritize_urgent_var, on_learning_toggles_changed))
    items.append(_switch("Neue Fotos trotz fälliger Wiederholungen beimischen", mix_new_cards_var, on_learning_toggles_changed))
    items.append(MenuItem(type="separator"))

    min_delay = tuple(
        _radio(
            "Mindest-Denkzeit: aus" if seconds == 0 else f"Mindest-Denkzeit: {seconds}s",
            min_retrieval_seconds_var, seconds, on_min_retrieval_changed,
        )
        for seconds in MIN_RETRIEVAL_OPTIONS
    )
    items.append(MenuItem(type="submenu", label="Abrufaufwand", items=min_delay))
    items.append(_switch(
        "Langsame richtige Antworten früher wiederholen (längenfair)", revisit_slow_correct_var, on_learning_toggles_changed,
    ))
    thresholds = tuple(
        _radio(f"Basis-Schwelle (≈ 6 Buchstaben): ≥ {seconds}s", slow_correct_threshold_var, seconds,
               on_slow_correct_threshold_changed)
        for seconds in SLOW_CORRECT_THRESHOLD_OPTIONS
    )
    items.append(MenuItem(type="submenu", label="Langsam-richtig-Schwelle (Basis)", items=thresholds))
    feedback = tuple(
        _radio(_FEEDBACK_LABELS.get(key, key), feedback_style_var, key, on_feedback_style_changed)
        for key in FEEDBACK_STYLE_OPTIONS
    )
    items.append(MenuItem(type="submenu", label="Feedbackstil", items=feedback))
    return tuple(items)
