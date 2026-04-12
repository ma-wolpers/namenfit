"""Feedback-Generator aus Lerndaten und Aufgabenqualität."""

import random

from .quiz_texts import (
    DELTA_REACTION,
    DIFFICULTY_REACTION,
    HISTORY_REACTION,
    ROUND_REACTION,
    STREAK_REACTION,
    TIME_REACTION,
    VOLUME_REACTION,
)


def _derive_round_key(task_score):
    if task_score >= 0.999:
        return "excellent"
    if task_score >= 0.70:
        return "good"
    if task_score >= 0.40:
        return "mid"
    return "bad"


def _build_encouraging_line(task_score, component_results, response_seconds):
    round_key = _derive_round_key(task_score)
    missed_fields = [name for name, is_ok in component_results.items() if not is_ok]

    opening = {
        "excellent": [
            "Stark gelöst.",
            "Sehr sicher – genau so.",
            "Top Runde.",
        ],
        "good": [
            "Gute Runde.",
            "Das war schon sehr ordentlich.",
            "Stabil beantwortet.",
        ],
        "mid": [
            "Gute Basis.",
            "Da steckt schon viel drin.",
            "Richtung stimmt.",
        ],
        "bad": [
            "Weiter so – die nächste wird besser.",
            "Dranbleiben, das wird schnell stabiler.",
            "Guter Lernmoment, jetzt festigen wir das.",
        ],
    }

    if missed_fields:
        close = (
            f"Nächstes Ziel: {', '.join(missed_fields)} noch einmal fokussiert abrufen."
        )
    elif response_seconds >= 7.0:
        close = "Richtig war es schon – mit etwas Tempo-Training wird es noch sicherer."
    else:
        close = "Weiter so, die Abrufsicherheit steigt sichtbar."

    return f"{random.choice(opening[round_key])} {close}"


def _build_neutral_line(task_score, component_results, response_seconds):
    round_key = _derive_round_key(task_score)
    missed_fields = [name for name, is_ok in component_results.items() if not is_ok]

    score_text = {
        "excellent": "Ergebnis: sehr gut.",
        "good": "Ergebnis: gut.",
        "mid": "Ergebnis: teilweise korrekt.",
        "bad": "Ergebnis: noch unsicher.",
    }[round_key]

    if missed_fields:
        focus_text = f"Offen: {', '.join(missed_fields)}."
    else:
        focus_text = "Alle Teilaufgaben korrekt."

    tempo_text = "Tempo: ruhig" if response_seconds >= 7.0 else "Tempo: angemessen"
    return f"{score_text} {focus_text} {tempo_text}."


def pick_feedback_line(style, **kwargs):
    """Wählt Rückmeldestil: sarkastisch, ermutigend oder neutral."""

    style_key = (style or "sarkastisch").strip().lower()
    if style_key == "sarkastisch":
        return pick_sarcastic_feedback_line(**kwargs)
    if style_key == "neutral":
        return _build_neutral_line(
            task_score=kwargs.get("task_score", 0.0),
            component_results=kwargs.get("component_results", {}),
            response_seconds=float(kwargs.get("response_seconds", 0.0)),
        )
    return _build_encouraging_line(
        task_score=kwargs.get("task_score", 0.0),
        component_results=kwargs.get("component_results", {}),
        response_seconds=float(kwargs.get("response_seconds", 0.0)),
    )


def pick_sarcastic_feedback_line(
    task_score,
    component_results,
    shown,
    correct,
    wrong,
    streak,
    person_weight,
    class_ratio_percent,
    class_avg_time_sec,
    response_seconds,
):
    """Erzeugt genau einen differenzierten, sarkastischen Kommentar."""

    ratio_percent = (
        round((correct / (correct + wrong)) * 100) if (correct + wrong) > 0 else 0
    )

    round_key = _derive_round_key(task_score)

    if ratio_percent >= 85:
        history_key = "elite"
    elif ratio_percent >= 60:
        history_key = "stable"
    else:
        history_key = "shaky"

    if streak >= 5:
        streak_key = "hot"
    elif streak == 0:
        streak_key = "cold"
    else:
        streak_key = "neutral"

    if shown < 8:
        volume_key = "new"
    elif shown < 30:
        volume_key = "experienced"
    else:
        volume_key = "veteran"

    if person_weight >= 4.5:
        difficulty_key = "high"
    elif person_weight >= 2.0:
        difficulty_key = "mid"
    else:
        difficulty_key = "low"

    if class_avg_time_sec > 0:
        time_factor = response_seconds / class_avg_time_sec
        if time_factor <= 0.7:
            time_key = "very_fast"
        elif time_factor <= 0.95:
            time_key = "fast"
        elif time_factor <= 1.2:
            time_key = "normal"
        elif time_factor <= 1.6:
            time_key = "slow"
        else:
            time_key = "very_slow"
    else:
        if response_seconds <= 2.5:
            time_key = "very_fast"
        elif response_seconds <= 4.0:
            time_key = "fast"
        elif response_seconds <= 6.0:
            time_key = "normal"
        elif response_seconds <= 9.0:
            time_key = "slow"
        else:
            time_key = "very_slow"

    ratio_delta = ratio_percent - class_ratio_percent
    if ratio_delta >= 12:
        delta_key = "well_above"
    elif ratio_delta >= 4:
        delta_key = "above"
    elif ratio_delta <= -12:
        delta_key = "well_below"
    elif ratio_delta <= -4:
        delta_key = "below"
    else:
        delta_key = "near"

    base_parts = [
        random.choice(ROUND_REACTION[round_key]),
        random.choice(HISTORY_REACTION[history_key]),
        random.choice(STREAK_REACTION[streak_key]),
        random.choice(VOLUME_REACTION[volume_key]),
        random.choice(DIFFICULTY_REACTION[difficulty_key]),
        random.choice(TIME_REACTION[time_key]),
        random.choice(DELTA_REACTION[delta_key]),
    ]

    missed_fields = [name for name, is_ok in component_results.items() if not is_ok]
    miss_part = (
        f"Heute daneben bei: {', '.join(missed_fields)}."
        if missed_fields
        else "Heute ohne Fehlfeld. Wie unkooperativ von dir."
    )

    candidates = [
        f"{base_parts[0]} {base_parts[1]}",
        f"{base_parts[0]} {base_parts[2]}",
        f"{base_parts[0]} {base_parts[3]}",
        f"{base_parts[1]} {base_parts[4]}",
        f"{base_parts[2]} {base_parts[5]}",
        f"{base_parts[0]} {base_parts[6]}",
        f"{base_parts[5]} {base_parts[6]}",
        f"{base_parts[2]} {miss_part}",
        f"{base_parts[0]} {miss_part}",
    ]

    return random.choice(candidates)


# Backward-compatible alias for existing imports.
pick_sarcastic_line = pick_sarcastic_feedback_line
