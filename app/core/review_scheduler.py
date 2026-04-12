"""Spaced-Repetition-Scheduler für prompt-basierte Wiederholungen."""

DEFAULT_DUE_PROMPT = 1
DEFAULT_REVIEW_INTERVAL = 2
DEFAULT_LAST_SEEN_PROMPT = 0
DEFAULT_PREV_SEEN_PROMPT = 0
DEFAULT_URGENT_REPEATS = 0
DEFAULT_STABILITY = 0.25
DEFAULT_RELEARN_STEPS = 0
DEFAULT_RECALL_EMA = 0.5


REVIEW_PROFILES = {
    "leicht": {
        "label": "Leicht",
        "lapse_interval": 2,
        "relearn_steps": 2,
        "relearn_interval": 2,
        "stability_build_cap": 4,
        "success_growth": 2.2,
        "success_min": 5,
        "success_max": 300,
        "due_lateness_weight": 45.0,
        "instability_weight": 12.0,
    },
    "mittel": {
        "label": "Mittel",
        "lapse_interval": 1,
        "relearn_steps": 3,
        "relearn_interval": 2,
        "stability_build_cap": 3,
        "success_growth": 2.4,
        "success_min": 4,
        "success_max": 240,
        "due_lateness_weight": 52.0,
        "instability_weight": 15.0,
    },
    "stark": {
        "label": "Stark",
        "lapse_interval": 1,
        "relearn_steps": 4,
        "relearn_interval": 1,
        "stability_build_cap": 2,
        "success_growth": 2.0,
        "success_min": 3,
        "success_max": 200,
        "due_lateness_weight": 60.0,
        "instability_weight": 18.0,
    },
}

DEFAULT_PROFILE = "mittel"


def get_profile(profile_key=None):
    key = profile_key if profile_key in REVIEW_PROFILES else DEFAULT_PROFILE
    return REVIEW_PROFILES[key]


def apply_scheduler_defaults(stats):
    """Ergänzt fehlende Scheduler-Felder in einem Stats-Dict."""

    stats.setdefault("due_prompt", DEFAULT_DUE_PROMPT)
    stats.setdefault("review_interval", DEFAULT_REVIEW_INTERVAL)
    stats.setdefault("last_seen_prompt", DEFAULT_LAST_SEEN_PROMPT)
    stats.setdefault("prev_seen_prompt", DEFAULT_PREV_SEEN_PROMPT)
    stats.setdefault("urgent_repeats", DEFAULT_URGENT_REPEATS)
    stats.setdefault("stability", DEFAULT_STABILITY)
    stats.setdefault("relearn_steps", DEFAULT_RELEARN_STEPS)
    stats.setdefault("recall_ema", DEFAULT_RECALL_EMA)


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _derive_gap_ratio(stats, prompt_counter):
    prev_seen = int(stats.get("prev_seen_prompt", 0))
    if prev_seen <= 0:
        return 1.0
    observed_gap = max(1, int(prompt_counter) - prev_seen)
    expected_gap = max(1, int(stats.get("review_interval", DEFAULT_REVIEW_INTERVAL)))
    return observed_gap / expected_gap


def schedule_after_result(stats, prompt_counter, success, profile_key=None):
    """Aktualisiert Intervall und Fälligkeit nach einer Antwort."""

    apply_scheduler_defaults(stats)
    profile = get_profile(profile_key)
    interval = max(1, int(stats.get("review_interval", DEFAULT_REVIEW_INTERVAL)))
    stability = _clamp(float(stats.get("stability", DEFAULT_STABILITY)), 0.01, 0.99)
    relearn_steps = max(0, int(stats.get("relearn_steps", 0)))
    gap_ratio = _derive_gap_ratio(stats, int(prompt_counter))
    recall_ema = _clamp(float(stats.get("recall_ema", DEFAULT_RECALL_EMA)), 0.0, 1.0)
    recall_ema = (recall_ema * 0.8) + (0.2 if success else 0.0)

    success_streak = int(stats.get("streak", 0))

    if success:
        # Erfolg nach kurzer Distanz erhöht Stabilität nur wenig, nach längerer Distanz stärker.
        stability_gain = (
            0.08
            + (0.10 * _clamp(gap_ratio, 0.3, 1.7))
            + (0.015 * min(6, success_streak))
        )
        stability = _clamp(stability + stability_gain * (1.0 - stability), 0.01, 0.99)

        if relearn_steps > 0:
            relearn_steps -= 1
            interval = max(1, int(profile["relearn_interval"]))
        else:
            growth = 1.0 + (float(profile["success_growth"]) - 1.0) * (
                0.55 + (0.75 * stability)
            )
            # Erfolg deutlich früher als erwartet => noch nicht robust, daher defensiver wachsen.
            if gap_ratio < 0.85:
                growth *= 0.70 + (0.35 * gap_ratio)
            interval = min(
                int(profile["success_max"]),
                max(int(profile["success_min"]), int(round(max(1, interval) * growth))),
            )

            # Solange eine Karte noch keine stabile Erfolgsserie hat,
            # darf das Intervall nicht zu schnell explodieren.
            if success_streak < 4:
                interval = min(interval, int(profile.get("stability_build_cap", 3)))

        stats["urgent_repeats"] = 0
    else:
        # Fehler trotz kurzer Distanz ist ein starkes Instabilitäts-Signal.
        fail_penalty = 0.55 if gap_ratio >= 1.0 else 0.72
        stability = _clamp(stability * fail_penalty, 0.01, 0.99)

        base_relearn = int(profile["relearn_steps"])
        if gap_ratio < 0.85:
            base_relearn += 1
        relearn_steps = max(relearn_steps, base_relearn)

        interval = max(1, int(profile["lapse_interval"]))
        stats["urgent_repeats"] = max(0, relearn_steps - 1)

    stats["stability"] = stability
    stats["relearn_steps"] = relearn_steps
    stats["recall_ema"] = _clamp(recall_ema, 0.0, 1.0)
    stats["review_interval"] = max(1, int(interval))
    stats["due_prompt"] = int(prompt_counter) + int(stats["review_interval"])


def mark_prompt_seen(stats, prompt_counter):
    """Markiert eine Karte als angezeigt und verwaltet akute Wiederholungen."""

    apply_scheduler_defaults(stats)
    stats["prev_seen_prompt"] = int(stats.get("last_seen_prompt", 0))
    stats["last_seen_prompt"] = int(prompt_counter)


def choose_next_due_name(
    names,
    level_stats_getter,
    person_weight_getter,
    next_prompt,
    last_name=None,
    profile_key=None,
    allow_immediate_repeat=False,
    prioritize_urgent_repeats=True,
    mix_new_cards=False,
):
    """Wählt due-basiert die nächste Person mit hoher Priorität für fällige Karten."""

    profile = get_profile(profile_key)

    if not names:
        raise ValueError("Keine Namen zur Auswahl vorhanden.")

    if len(names) == 1:
        return names[0]

    def _without_last(entries):
        if allow_immediate_repeat or not last_name:
            return list(entries)
        return [entry for entry in entries if entry[0] != last_name]

    due_candidates = []
    scored = []

    for name in names:
        stats = level_stats_getter(name)
        apply_scheduler_defaults(stats)

        due_prompt = int(stats.get("due_prompt", DEFAULT_DUE_PROMPT))
        relearn_steps = int(stats.get("relearn_steps", 0))
        stability = _clamp(float(stats.get("stability", DEFAULT_STABILITY)), 0.01, 0.99)
        base_weight = float(person_weight_getter(name))
        lateness = max(0, int(next_prompt) - due_prompt)

        # Einheitliches Prioritätsmodell:
        # 1) Relearn (nach Fehlern) immer zuerst
        # 2) dann fällige Karten nach Überfälligkeit + Instabilität
        # 3) erst wenn nichts fällig: nächste Fälligkeiten
        score = base_weight
        score += lateness * float(profile.get("due_lateness_weight", 50.0))
        score += (1.0 - stability) * float(profile.get("instability_weight", 15.0))
        if relearn_steps > 0:
            score += 900.0 + (relearn_steps * 120.0)
            if prioritize_urgent_repeats:
                score += 220.0

        if name == last_name and not allow_immediate_repeat:
            score -= 10000.0

        scored.append((name, score, due_prompt, relearn_steps))

        if due_prompt <= int(next_prompt):
            due_candidates.append((name, score, due_prompt, relearn_steps))

    if due_candidates:
        due_pool = _without_last(due_candidates)
        if not due_pool:
            due_pool = list(due_candidates)

        # Deterministische Auswahl: höchste Priorität gewinnt.
        due_pool.sort(key=lambda item: (-item[1], item[2], item[0]))
        return due_pool[0][0]

    # Wenn nichts fällig ist: nächste Fälligkeit zuerst (Durchmischung bleibt sekundär).
    non_due = [entry for entry in scored if entry[2] > int(next_prompt)]
    non_due = _without_last(non_due) or non_due
    if mix_new_cards:
        non_due.sort(key=lambda item: item[2])
        window = non_due[: min(6, len(non_due))]
        window.sort(key=lambda item: (-item[1], item[2], item[0]))
        return window[0][0]

    non_due.sort(key=lambda item: (item[2], -item[1], item[0]))
    return non_due[0][0]
