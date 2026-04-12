"""Gemeinsamer Menüaufbau für Lernoptionen (Startdialog + Quizfenster)."""

import tkinter as tk

from ..core.learning_profiles import (
    CUSTOM_PROFILE,
    FEEDBACK_STYLE_OPTIONS,
    LEARNING_PROFILE_ORDER,
    LEARNING_PROFILES,
    MIN_RETRIEVAL_OPTIONS,
    SLOW_CORRECT_THRESHOLD_OPTIONS,
)
from ..core.review_scheduler import REVIEW_PROFILES


def populate_learning_menu(
    learning_menu,
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
    """Befüllt ein Menü mit allen Lern-Controls inkl. optionalen Presets."""

    if learning_profile_var is not None and callable(on_learning_profile_changed):
        preset_menu = tk.Menu(learning_menu, tearoff=0)
        for profile_key in LEARNING_PROFILE_ORDER:
            profile = LEARNING_PROFILES.get(profile_key)
            if not profile:
                continue
            preset_menu.add_radiobutton(
                label=profile["label"],
                variable=learning_profile_var,
                value=profile_key,
                command=on_learning_profile_changed,
            )
        preset_menu.add_separator()
        preset_menu.add_radiobutton(
            label="Individuell (manuell)",
            variable=learning_profile_var,
            value=CUSTOM_PROFILE,
            command=on_learning_profile_changed,
        )
        learning_menu.add_cascade(label="Lernprofil", menu=preset_menu)
        learning_menu.add_separator()

    for profile_key in ("leicht", "mittel", "stark"):
        profile = REVIEW_PROFILES.get(profile_key)
        if not profile:
            continue
        learning_menu.add_radiobutton(
            label=f"Wiederholungsprofil: {profile['label']}",
            variable=review_profile_var,
            value=profile_key,
            command=on_review_profile_changed,
        )

    learning_menu.add_separator()
    learning_menu.add_checkbutton(
        label="Gleicher Name darf direkt wiederkommen",
        variable=allow_immediate_repeat_var,
        command=on_learning_toggles_changed,
    )
    learning_menu.add_checkbutton(
        label="Fehler-Relearn priorisieren",
        variable=prioritize_urgent_var,
        command=on_learning_toggles_changed,
    )
    learning_menu.add_checkbutton(
        label="Neue Fotos trotz fälliger Wiederholungen beimischen",
        variable=mix_new_cards_var,
        command=on_learning_toggles_changed,
    )

    learning_menu.add_separator()

    min_delay_menu = tk.Menu(learning_menu, tearoff=0)
    for seconds in MIN_RETRIEVAL_OPTIONS:
        label = (
            "Mindest-Denkzeit: aus" if seconds == 0 else f"Mindest-Denkzeit: {seconds}s"
        )
        min_delay_menu.add_radiobutton(
            label=label,
            variable=min_retrieval_seconds_var,
            value=seconds,
            command=on_min_retrieval_changed,
        )
    learning_menu.add_cascade(label="Abrufaufwand", menu=min_delay_menu)

    learning_menu.add_checkbutton(
        label="Langsame richtige Antworten früher wiederholen (längenfair)",
        variable=revisit_slow_correct_var,
        command=on_learning_toggles_changed,
    )

    slow_threshold_menu = tk.Menu(learning_menu, tearoff=0)
    for seconds in SLOW_CORRECT_THRESHOLD_OPTIONS:
        slow_threshold_menu.add_radiobutton(
            label=f"Basis-Schwelle (≈ 6 Buchstaben): ≥ {seconds}s",
            variable=slow_correct_threshold_var,
            value=seconds,
            command=on_slow_correct_threshold_changed,
        )
    learning_menu.add_cascade(
        label="Langsam-richtig-Schwelle (Basis)", menu=slow_threshold_menu
    )

    feedback_menu = tk.Menu(learning_menu, tearoff=0)
    for style_key in FEEDBACK_STYLE_OPTIONS:
        label = {
            "sarkastisch": "Feedback: Sarkastisch",
            "ermutigend": "Feedback: Ermutigend",
            "neutral": "Feedback: Neutral",
        }.get(style_key, style_key)
        feedback_menu.add_radiobutton(
            label=label,
            variable=feedback_style_var,
            value=style_key,
            command=on_feedback_style_changed,
        )
    learning_menu.add_cascade(label="Feedbackstil", menu=feedback_menu)
