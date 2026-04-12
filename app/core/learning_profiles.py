"""Zentrale Lernprofile und zugehörige Settings-Bundles."""

from .review_scheduler import DEFAULT_PROFILE, REVIEW_PROFILES

LEARNING_SETTING_KEYS = (
    "review_profile",
    "allow_immediate_repeat",
    "prioritize_urgent_repeats",
    "mix_new_cards",
    "min_retrieval_seconds",
    "revisit_slow_correct",
    "slow_correct_threshold_seconds",
    "feedback_style",
)

MIN_RETRIEVAL_OPTIONS = (0, 2, 3, 5, 8)
SLOW_CORRECT_THRESHOLD_OPTIONS = (4, 6, 8, 10)
FEEDBACK_STYLE_OPTIONS = ("sarkastisch", "ermutigend", "neutral")

CUSTOM_PROFILE = "individuell"

LEARNING_PROFILES = {
    "einstieg": {
        "label": "Preset: Einstieg",
        "settings": {
            "review_profile": "leicht",
            "allow_immediate_repeat": False,
            "prioritize_urgent_repeats": True,
            "mix_new_cards": False,
            "min_retrieval_seconds": 2,
            "revisit_slow_correct": True,
            "slow_correct_threshold_seconds": 8,
            "feedback_style": "ermutigend",
        },
    },
    "pruefung": {
        "label": "Preset: Prüfungsvorbereitung",
        "settings": {
            "review_profile": "stark",
            "allow_immediate_repeat": False,
            "prioritize_urgent_repeats": True,
            "mix_new_cards": False,
            "min_retrieval_seconds": 3,
            "revisit_slow_correct": True,
            "slow_correct_threshold_seconds": 6,
            "feedback_style": "ermutigend",
        },
    },
    "nachlernen": {
        "label": "Preset: Intensives Nachlernen",
        "settings": {
            "review_profile": "stark",
            "allow_immediate_repeat": False,
            "prioritize_urgent_repeats": True,
            "mix_new_cards": False,
            "min_retrieval_seconds": 2,
            "revisit_slow_correct": True,
            "slow_correct_threshold_seconds": 4,
            "feedback_style": "ermutigend",
        },
    },
}

LEARNING_PROFILE_ORDER = tuple(LEARNING_PROFILES.keys())

DEFAULT_LEARNING_SETTINGS = {
    "review_profile": DEFAULT_PROFILE,
    "allow_immediate_repeat": False,
    "prioritize_urgent_repeats": True,
    "mix_new_cards": False,
    "min_retrieval_seconds": 2,
    "revisit_slow_correct": True,
    "slow_correct_threshold_seconds": 6,
    "feedback_style": "ermutigend",
    "learning_profile": CUSTOM_PROFILE,
}


def normalize_learning_profile_key(profile_key):
    if profile_key in LEARNING_PROFILES:
        return profile_key
    return CUSTOM_PROFILE


def get_profile_settings(profile_key):
    profile = LEARNING_PROFILES.get(profile_key)
    if not profile:
        return {}
    return dict(profile.get("settings", {}))


def detect_matching_profile(settings):
    """Liefert Preset-Key bei exaktem Settings-Match, sonst 'individuell'."""

    subset = {key: settings.get(key) for key in LEARNING_SETTING_KEYS}
    for profile_key, profile in LEARNING_PROFILES.items():
        if subset == profile.get("settings", {}):
            return profile_key
    return CUSTOM_PROFILE


def normalize_learning_settings(settings):
    """Normalisiert ein Settings-Dict robust auf erlaubte Lernoptionen."""

    incoming = settings if isinstance(settings, dict) else {}

    review_profile = incoming.get("review_profile", DEFAULT_PROFILE)
    if review_profile not in REVIEW_PROFILES:
        review_profile = DEFAULT_PROFILE

    min_retrieval_seconds = incoming.get("min_retrieval_seconds", 0)
    if not isinstance(min_retrieval_seconds, (int, float)):
        min_retrieval_seconds = 0
    min_retrieval_seconds = int(min_retrieval_seconds)
    if min_retrieval_seconds not in MIN_RETRIEVAL_OPTIONS:
        min_retrieval_seconds = 0

    slow_threshold = incoming.get("slow_correct_threshold_seconds", 6)
    if not isinstance(slow_threshold, (int, float)):
        slow_threshold = 6
    slow_threshold = int(slow_threshold)
    if slow_threshold not in SLOW_CORRECT_THRESHOLD_OPTIONS:
        slow_threshold = 6

    normalized = {
        "review_profile": review_profile,
        "allow_immediate_repeat": bool(incoming.get("allow_immediate_repeat", False)),
        "prioritize_urgent_repeats": bool(
            incoming.get("prioritize_urgent_repeats", True)
        ),
        "mix_new_cards": bool(incoming.get("mix_new_cards", False)),
        "min_retrieval_seconds": min_retrieval_seconds,
        "revisit_slow_correct": bool(incoming.get("revisit_slow_correct", False)),
        "slow_correct_threshold_seconds": slow_threshold,
        "feedback_style": incoming.get("feedback_style", "ermutigend"),
    }
    if normalized["feedback_style"] not in FEEDBACK_STYLE_OPTIONS:
        normalized["feedback_style"] = "ermutigend"
    normalized["learning_profile"] = detect_matching_profile(normalized)
    return normalized
