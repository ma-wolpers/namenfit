"""Persistenz und adaptive Gewichtung für den Lernfortschritt."""

import ctypes
import json
import os
from pathlib import Path

from bw_libs.app_paths import atomic_write_text

from ..core.models import LEVEL_1
from ..core.review_scheduler import (
    DEFAULT_PROFILE,
    REVIEW_PROFILES,
    apply_scheduler_defaults,
    choose_next_due_name,
    mark_prompt_seen,
    schedule_after_result,
)
from ..core.learning_profiles import (
    CUSTOM_PROFILE,
    DEFAULT_LEARNING_SETTINGS,
    FEEDBACK_STYLE_OPTIONS,
    LEARNING_SETTING_KEYS,
    MIN_RETRIEVAL_OPTIONS,
    SLOW_CORRECT_THRESHOLD_OPTIONS,
    detect_matching_profile,
    get_profile_settings,
    normalize_learning_settings,
    normalize_learning_profile_key,
)
from ..ui.ui_theme import DEFAULT_THEME, normalize_theme_key


FILE_ATTRIBUTE_READONLY = 0x01
FILE_ATTRIBUTE_HIDDEN = 0x02
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


def log_path_for_csv(csv_path):
    """Liefert den Pfad zur versteckten Fortschrittsdatei einer CSV-Datei."""

    directory = os.path.dirname(csv_path)
    basename = os.path.basename(csv_path)
    return os.path.join(directory, f".{basename}.trainerlog.json")


def ensure_hidden(path):
    """Markiert eine Datei unter Windows als versteckt (best effort)."""

    if os.name != "nt":
        return

    try:
        current = _get_file_attributes(path)
        if current is None:
            return
        _set_file_attributes(path, current | FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        pass


def _get_file_attributes(path):
    """Liest Windows-Dateiattribute oder None bei Fehler."""

    if os.name != "nt":
        return None

    attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
    if attrs == INVALID_FILE_ATTRIBUTES:
        return None
    return attrs


def _set_file_attributes(path, attrs):
    """Setzt Windows-Dateiattribute (best effort)."""

    if os.name != "nt":
        return
    ctypes.windll.kernel32.SetFileAttributesW(path, attrs)


def _clear_read_only(path):
    """Entfernt Read-only-Flag, falls gesetzt."""

    if os.name != "nt" or not os.path.exists(path):
        return

    current = _get_file_attributes(path)
    if current is None:
        return

    if current & FILE_ATTRIBUTE_READONLY:
        _set_file_attributes(path, current & ~FILE_ATTRIBUTE_READONLY)


def _default_level_stats():
    stats = {
        "shown": 0,
        "correct": 0,
        "wrong": 0,
        "streak": 0,
        "response_time_total_sec": 0.0,
        "response_time_count": 0,
    }
    apply_scheduler_defaults(stats)
    return stats


def _default_level2_detail_stats():
    return {
        "group_correct": 0,
        "group_wrong": 0,
        "behind_correct": 0,
        "behind_wrong": 0,
        "front_correct": 0,
        "front_wrong": 0,
        "opposite_correct": 0,
        "opposite_wrong": 0,
    }


def default_person_progress():
    """Erzeugt den Default-Fortschritt für eine einzelne Person."""

    level2 = _default_level_stats()
    level2.update(_default_level2_detail_stats())

    return {
        "level1": _default_level_stats(),
        "level2": level2,
    }


class ProgressStore:
    """
    Kapselt Lesen/Schreiben der Logdatei und die adaptive Wiederholungslogik.

    Daten werden versioniert gespeichert, damit ältere Formate migriert werden
    können (z. B. vom anfangs einfachen v1-Format auf das level-getrennte v2).
    """

    SCHEMA_VERSION = 2

    def __init__(self, log_path, names):
        self.log_path = log_path
        self.names = list(names)
        self.last_save_error = None
        self.data = self._load_or_create()
        self.save()

    def _empty_progress(self):
        return {
            "version": self.SCHEMA_VERSION,
            "prompt_counter": 0,
            "review_profile": DEFAULT_PROFILE,
            "ui_theme": DEFAULT_THEME,
            "allow_immediate_repeat": False,
            "prioritize_urgent_repeats": True,
            "mix_new_cards": False,
            "min_retrieval_seconds": 0,
            "revisit_slow_correct": False,
            "slow_correct_threshold_seconds": 6,
            "feedback_style": "ermutigend",
            "learning_profile": CUSTOM_PROFILE,
            "people": {name: default_person_progress() for name in self.names},
        }

    def _migrate_if_needed(self, data):
        version = data.get("version", 1)
        if version == self.SCHEMA_VERSION:
            return data

        if version == 1:
            migrated = self._empty_progress()
            old_people = data.get("people", {})
            for name, old_stats in old_people.items():
                if name not in migrated["people"]:
                    continue
                level1 = migrated["people"][name]["level1"]
                level1["shown"] = int(old_stats.get("shown", 0))
                level1["correct"] = int(old_stats.get("correct", 0))
                level1["wrong"] = int(old_stats.get("wrong", 0))
                level1["streak"] = int(old_stats.get("streak", 0))

            migrated["version"] = self.SCHEMA_VERSION
            return migrated

        return self._empty_progress()

    def _load_or_create(self):
        if not os.path.exists(self.log_path):
            return self._empty_progress()

        try:
            with open(self.log_path, "r", encoding="utf-8") as file_handle:
                loaded = json.load(file_handle)
        except Exception:
            return self._empty_progress()

        data = self._migrate_if_needed(loaded)
        people_data = data.get("people", {})

        for name in self.names:
            if name not in people_data:
                people_data[name] = default_person_progress()

        data["people"] = people_data
        data["version"] = self.SCHEMA_VERSION
        data.setdefault("prompt_counter", 0)
        data.setdefault("review_profile", DEFAULT_PROFILE)
        data.setdefault("ui_theme", DEFAULT_THEME)
        data.setdefault("allow_immediate_repeat", False)
        data.setdefault("prioritize_urgent_repeats", True)
        data.setdefault("mix_new_cards", False)
        data.setdefault("min_retrieval_seconds", 0)
        data.setdefault("revisit_slow_correct", False)
        data.setdefault("slow_correct_threshold_seconds", 6)
        data.setdefault("feedback_style", "ermutigend")
        data.setdefault("learning_profile", CUSTOM_PROFILE)

        data["ui_theme"] = normalize_theme_key(data.get("ui_theme", DEFAULT_THEME))
        data["min_retrieval_seconds"] = self._normalize_min_retrieval_seconds(
            data.get("min_retrieval_seconds", 0)
        )
        data["slow_correct_threshold_seconds"] = (
            self._normalize_slow_correct_threshold_seconds(
                data.get("slow_correct_threshold_seconds", 6)
            )
        )
        data["feedback_style"] = self._normalize_feedback_style(
            data.get("feedback_style", "ermutigend")
        )
        data["learning_profile"] = normalize_learning_profile_key(
            data.get("learning_profile", CUSTOM_PROFILE)
        )
        self._sync_learning_profile_from_current_settings(data)

        for name in self.names:
            for level_key in ("level1", "level2"):
                self._ensure_scheduler_fields(people_data[name][level_key])
        return data

    def _ensure_scheduler_fields(self, stats):
        apply_scheduler_defaults(stats)

    def reset_session_timeline(self):
        """Startet die Scheduler-Zeitleiste für eine neue Sitzung neu.

        Beibehaltet werden personenbezogene Lernhistorien (z. B. richtig/falsch,
        Stabilität), zurückgesetzt werden ausschließlich zeitsensitive
        Sitzungsfelder wie Prompt-Zähler und fällige Prompt-Positionen.
        """

        self.data["prompt_counter"] = 0

        for name in self.names:
            person = self.data.get("people", {}).get(name)
            if not isinstance(person, dict):
                continue

            for level_key in ("level1", "level2"):
                stats = person.get(level_key)
                if not isinstance(stats, dict):
                    continue

                apply_scheduler_defaults(stats)
                stats["due_prompt"] = 1
                stats["review_interval"] = max(1, int(stats.get("review_interval", 1)))
                stats["last_seen_prompt"] = 0
                stats["prev_seen_prompt"] = 0
                stats["urgent_repeats"] = 0
                stats["relearn_steps"] = 0

        self.save()

    def _schedule_after_result(self, name, level, success):
        stats = self._level_stats(name, level)
        now_prompt = int(self.data.get("prompt_counter", 0))
        schedule_after_result(
            stats,
            now_prompt,
            success=bool(success),
            profile_key=self.get_review_profile(),
        )

    def get_review_profile(self):
        profile = self.data.get("review_profile", DEFAULT_PROFILE)
        if profile not in REVIEW_PROFILES:
            return DEFAULT_PROFILE
        return profile

    def set_review_profile(self, profile_key):
        if profile_key not in REVIEW_PROFILES:
            return
        self.data["review_profile"] = profile_key
        self._sync_learning_profile_from_current_settings()
        self.save()

    def get_learning_profile_key(self):
        return normalize_learning_profile_key(
            self.data.get("learning_profile", CUSTOM_PROFILE)
        )

    def apply_learning_profile(self, profile_key):
        profile_key = normalize_learning_profile_key(profile_key)
        if profile_key == CUSTOM_PROFILE:
            return

        settings = get_profile_settings(profile_key)
        if not settings:
            return

        self.data["review_profile"] = settings.get("review_profile", DEFAULT_PROFILE)
        self.data["allow_immediate_repeat"] = bool(
            settings.get("allow_immediate_repeat", False)
        )
        self.data["prioritize_urgent_repeats"] = bool(
            settings.get("prioritize_urgent_repeats", True)
        )
        self.data["mix_new_cards"] = bool(settings.get("mix_new_cards", False))
        self.data["min_retrieval_seconds"] = self._normalize_min_retrieval_seconds(
            settings.get("min_retrieval_seconds", 0)
        )
        self.data["revisit_slow_correct"] = bool(
            settings.get("revisit_slow_correct", False)
        )
        self.data["slow_correct_threshold_seconds"] = (
            self._normalize_slow_correct_threshold_seconds(
                settings.get("slow_correct_threshold_seconds", 6)
            )
        )
        self.data["feedback_style"] = self._normalize_feedback_style(
            settings.get("feedback_style", "ermutigend")
        )
        self.data["learning_profile"] = profile_key
        self.save()

    def apply_learning_settings(self, settings):
        """Wendet ein vollständiges Lern-Settings-Bundle in einem Schritt an."""

        normalized = normalize_learning_settings(settings)
        fallback = normalize_learning_settings(DEFAULT_LEARNING_SETTINGS)

        self.data["review_profile"] = normalized.get(
            "review_profile", fallback["review_profile"]
        )
        self.data["allow_immediate_repeat"] = bool(
            normalized.get("allow_immediate_repeat", fallback["allow_immediate_repeat"])
        )
        self.data["prioritize_urgent_repeats"] = bool(
            normalized.get(
                "prioritize_urgent_repeats", fallback["prioritize_urgent_repeats"]
            )
        )
        self.data["mix_new_cards"] = bool(
            normalized.get("mix_new_cards", fallback["mix_new_cards"])
        )
        self.data["min_retrieval_seconds"] = self._normalize_min_retrieval_seconds(
            normalized.get("min_retrieval_seconds", fallback["min_retrieval_seconds"])
        )
        self.data["revisit_slow_correct"] = bool(
            normalized.get("revisit_slow_correct", fallback["revisit_slow_correct"])
        )
        self.data["slow_correct_threshold_seconds"] = (
            self._normalize_slow_correct_threshold_seconds(
                normalized.get(
                    "slow_correct_threshold_seconds",
                    fallback["slow_correct_threshold_seconds"],
                )
            )
        )
        self.data["feedback_style"] = self._normalize_feedback_style(
            normalized.get("feedback_style", fallback["feedback_style"])
        )
        self._sync_learning_profile_from_current_settings()
        self.save()

    def get_learning_settings(self):
        """Liefert die aktuellen Lernsettings als normalisiertes Bundle."""

        return normalize_learning_settings(
            {
                "review_profile": self.data.get("review_profile", DEFAULT_PROFILE),
                "allow_immediate_repeat": self.data.get(
                    "allow_immediate_repeat", False
                ),
                "prioritize_urgent_repeats": self.data.get(
                    "prioritize_urgent_repeats", True
                ),
                "mix_new_cards": self.data.get("mix_new_cards", False),
                "min_retrieval_seconds": self.data.get("min_retrieval_seconds", 0),
                "revisit_slow_correct": self.data.get("revisit_slow_correct", False),
                "slow_correct_threshold_seconds": self.data.get(
                    "slow_correct_threshold_seconds", 6
                ),
                "feedback_style": self.data.get("feedback_style", "ermutigend"),
            }
        )

    def _sync_learning_profile_from_current_settings(self, data=None):
        target = data if isinstance(data, dict) else self.data
        settings = {key: target.get(key) for key in LEARNING_SETTING_KEYS}
        target["learning_profile"] = detect_matching_profile(settings)

    def get_theme_key(self):
        return normalize_theme_key(self.data.get("ui_theme", DEFAULT_THEME))

    def set_theme_key(self, theme_key):
        self.data["ui_theme"] = normalize_theme_key(theme_key)
        self.save()

    def get_allow_immediate_repeat(self):
        return bool(self.data.get("allow_immediate_repeat", False))

    def set_allow_immediate_repeat(self, enabled):
        self.data["allow_immediate_repeat"] = bool(enabled)
        self._sync_learning_profile_from_current_settings()
        self.save()

    def get_prioritize_urgent_repeats(self):
        return bool(self.data.get("prioritize_urgent_repeats", True))

    def set_prioritize_urgent_repeats(self, enabled):
        self.data["prioritize_urgent_repeats"] = bool(enabled)
        self._sync_learning_profile_from_current_settings()
        self.save()

    def get_mix_new_cards(self):
        return bool(self.data.get("mix_new_cards", False))

    def set_mix_new_cards(self, enabled):
        self.data["mix_new_cards"] = bool(enabled)
        self._sync_learning_profile_from_current_settings()
        self.save()

    def _normalize_min_retrieval_seconds(self, seconds):
        value = int(seconds) if isinstance(seconds, (int, float)) else 0
        return value if value in MIN_RETRIEVAL_OPTIONS else 0

    def get_min_retrieval_seconds(self):
        return self._normalize_min_retrieval_seconds(
            self.data.get("min_retrieval_seconds", 0)
        )

    def set_min_retrieval_seconds(self, seconds):
        self.data["min_retrieval_seconds"] = self._normalize_min_retrieval_seconds(
            seconds
        )
        self._sync_learning_profile_from_current_settings()
        self.save()

    def get_revisit_slow_correct(self):
        return bool(self.data.get("revisit_slow_correct", False))

    def set_revisit_slow_correct(self, enabled):
        self.data["revisit_slow_correct"] = bool(enabled)
        self._sync_learning_profile_from_current_settings()
        self.save()

    def _normalize_slow_correct_threshold_seconds(self, seconds):
        value = int(seconds) if isinstance(seconds, (int, float)) else 6
        return value if value in SLOW_CORRECT_THRESHOLD_OPTIONS else 6

    def get_slow_correct_threshold_seconds(self):
        return self._normalize_slow_correct_threshold_seconds(
            self.data.get("slow_correct_threshold_seconds", 6)
        )

    def set_slow_correct_threshold_seconds(self, seconds):
        self.data["slow_correct_threshold_seconds"] = (
            self._normalize_slow_correct_threshold_seconds(seconds)
        )
        self._sync_learning_profile_from_current_settings()
        self.save()

    def _normalize_feedback_style(self, style):
        key = str(style).strip().lower() if style is not None else "ermutigend"
        return key if key in FEEDBACK_STYLE_OPTIONS else "ermutigend"

    def get_feedback_style(self):
        return self._normalize_feedback_style(
            self.data.get("feedback_style", "ermutigend")
        )

    def set_feedback_style(self, style):
        self.data["feedback_style"] = self._normalize_feedback_style(style)
        self._sync_learning_profile_from_current_settings()
        self.save()

    def mark_prompt_shown(self, name, level):
        """Erhöht den Prompt-Zähler und markiert die gezeigte Person."""

        self.data["prompt_counter"] = int(self.data.get("prompt_counter", 0)) + 1
        stats = self._level_stats(name, level)
        mark_prompt_seen(stats, int(self.data["prompt_counter"]))
        self.save()

    def get_prompt_counter(self):
        """Liefert den aktuellen Prompt-Zähler der Session."""

        return int(self.data.get("prompt_counter", 0))

    def has_pending_relearn_due(self, names, level, last_name=None):
        """Prüft, ob fällige Relearn-Karten vorliegen (für Intro-Queue-Interrupt)."""

        next_prompt = int(self.data.get("prompt_counter", 0)) + 1
        allow_immediate_repeat = self.get_allow_immediate_repeat()
        candidates = []

        for name in names:
            stats = self._level_stats(name, level)
            apply_scheduler_defaults(stats)

            due_prompt = int(stats.get("due_prompt", 1))
            relearn_steps = int(stats.get("relearn_steps", 0))
            if due_prompt <= next_prompt and relearn_steps > 0:
                candidates.append(name)

        if not candidates:
            return False

        if allow_immediate_repeat or not last_name:
            return True

        # Bei deaktiviertem Sofort-Repeat nur dann blocken, wenn es echte Alternativen gibt.
        non_last = [name for name in candidates if name != last_name]
        return bool(non_last or len(names) == 1)

    def choose_next_name(self, names, level, last_name=None):
        """Wählt die nächste Person due-basiert mit Priorität auf fällige Wiederholungen."""
        next_prompt = int(self.data.get("prompt_counter", 0)) + 1
        return choose_next_due_name(
            names=names,
            level_stats_getter=lambda name: self._level_stats(name, level),
            person_weight_getter=lambda name: self.person_weight(name, level),
            next_prompt=next_prompt,
            last_name=last_name,
            profile_key=self.get_review_profile(),
            allow_immediate_repeat=self.get_allow_immediate_repeat(),
            prioritize_urgent_repeats=self.get_prioritize_urgent_repeats(),
            mix_new_cards=self.get_mix_new_cards(),
        )

    def save(self):
        """
        Schreibt Fortschritt robust auf die Festplatte.

        Strategie:
        1) Per zentralem Atomic-Writer in temporäre Datei schreiben und austauschen
        2) Hidden-Attribut setzen

        Bei Permission-Problemen wird einmalig versucht, Read-only zu entfernen.
        Rückgabe: True bei Erfolg, sonst False.
        """

        payload = json.dumps(self.data, ensure_ascii=False, indent=2)
        target_path = Path(self.log_path)

        def write_atomic():
            atomic_write_text(target_path, payload, encoding="utf-8")

        try:
            write_atomic()
            ensure_hidden(self.log_path)
            self.last_save_error = None
            return True
        except PermissionError:
            _clear_read_only(self.log_path)
            try:
                write_atomic()
                ensure_hidden(self.log_path)
                self.last_save_error = None
                return True
            except OSError as err:
                self.last_save_error = str(err)
                return False
        except OSError as err:
            self.last_save_error = str(err)
            return False

    def _level_key(self, level):
        return "level1" if level == LEVEL_1 else "level2"

    def _level_stats(self, name, level):
        return self.data["people"][name][self._level_key(level)]

    def person_weight(self, name, level):
        """
        Berechnet ein adaptives Gewicht für die nächste Auswahl einer Person.

        Höheres Gewicht => Person kommt häufiger dran.
        """

        stats = self._level_stats(name, level)
        shown = stats.get("shown", 0)
        correct = stats.get("correct", 0)
        wrong = stats.get("wrong", 0)
        streak = stats.get("streak", 0)

        mastery = correct / max(shown, 1)
        weight = 1.0
        weight += wrong * 2.5
        weight += max(0, 3 - streak) * 0.6
        weight += (1.0 - mastery) * 1.5
        weight -= min(correct, 10) * 0.08
        return max(weight, 0.2)

    def _apply_slow_success_revisit(self, stats, success, response_seconds):
        """Plant eine frühe Wiederholung bei langsamen, aber richtigen Antworten."""

        if not success or not self.get_revisit_slow_correct():
            return

        effective_seconds = float(response_seconds)
        expected_length = int(stats.get("expected_answer_length", 0))
        if expected_length > 0:
            length_factor = 1.0 + min(0.45, max(0, expected_length - 6) * 0.04)
            effective_seconds = effective_seconds / length_factor

        if effective_seconds < float(self.get_slow_correct_threshold_seconds()):
            return

        apply_scheduler_defaults(stats)
        now_prompt = int(self.data.get("prompt_counter", 0))
        stats["due_prompt"] = min(
            int(stats.get("due_prompt", now_prompt + 1)), now_prompt + 1
        )
        stats["review_interval"] = max(1, min(int(stats.get("review_interval", 1)), 1))
        stats["relearn_steps"] = max(int(stats.get("relearn_steps", 0)), 1)
        stats["urgent_repeats"] = max(int(stats.get("urgent_repeats", 0)), 1)
        stats["stability"] = max(0.01, float(stats.get("stability", 0.25)) * 0.88)

    def update_level1(
        self, name, group_ok, response_seconds=0.0, expected_name_length=None
    ):
        """Aktualisiert Fortschritt nach einer Level-1-Antwort."""

        stats = self._level_stats(name, LEVEL_1)
        stats.setdefault("response_time_total_sec", 0.0)
        stats.setdefault("response_time_count", 0)
        safe_seconds = max(0.0, float(response_seconds))
        stats["response_time_total_sec"] += safe_seconds
        stats["response_time_count"] += 1
        stats["shown"] += 1

        if group_ok:
            stats["correct"] += 1
            stats["streak"] += 1
        else:
            stats["wrong"] += 1
            stats["streak"] = 0

        if expected_name_length is None:
            stats.pop("expected_answer_length", None)
        else:
            stats["expected_answer_length"] = max(0, int(expected_name_length))

        self._schedule_after_result(name, LEVEL_1, success=bool(group_ok))
        self._apply_slow_success_revisit(
            stats, success=bool(group_ok), response_seconds=response_seconds
        )

        self.save()

    def update_level2(
        self,
        name,
        group_ok,
        behind_ok,
        front_ok,
        opposite_ok,
        name_ok=None,
        response_seconds=0.0,
        expected_name_length=None,
    ):
        """Aktualisiert Fortschritt nach einer Level-2-Antwort inkl. Teilfeldern."""

        stats = self._level_stats(name, 2)
        if name_ok is None:
            all_ok = group_ok and behind_ok and front_ok and opposite_ok
        else:
            all_ok = (
                bool(name_ok) and group_ok and behind_ok and front_ok and opposite_ok
            )

        stats.setdefault("shown", 0)
        stats.setdefault("correct", 0)
        stats.setdefault("wrong", 0)
        stats.setdefault("streak", 0)
        stats.setdefault("response_time_total_sec", 0.0)
        stats.setdefault("response_time_count", 0)
        safe_seconds = max(0.0, float(response_seconds))
        stats["response_time_total_sec"] += safe_seconds
        stats["response_time_count"] += 1
        stats["shown"] += 1
        if all_ok:
            stats["correct"] += 1
            stats["streak"] += 1
        else:
            stats["wrong"] += 1
            stats["streak"] = 0

        if expected_name_length is None:
            stats.pop("expected_answer_length", None)
        else:
            stats["expected_answer_length"] = max(0, int(expected_name_length))

        self._schedule_after_result(name, 2, success=bool(all_ok))
        self._apply_slow_success_revisit(
            stats, success=bool(all_ok), response_seconds=response_seconds
        )

        stats.setdefault("group_correct", 0)
        stats.setdefault("group_wrong", 0)
        stats.setdefault("behind_correct", 0)
        stats.setdefault("behind_wrong", 0)
        stats.setdefault("front_correct", 0)
        stats.setdefault("front_wrong", 0)
        stats.setdefault("opposite_correct", 0)
        stats.setdefault("opposite_wrong", 0)

        stats["group_correct"] += 1 if group_ok else 0
        stats["group_wrong"] += 0 if group_ok else 1
        stats["behind_correct"] += 1 if behind_ok else 0
        stats["behind_wrong"] += 0 if behind_ok else 1
        stats["front_correct"] += 1 if front_ok else 0
        stats["front_wrong"] += 0 if front_ok else 1
        stats["opposite_correct"] += 1 if opposite_ok else 0
        stats["opposite_wrong"] += 0 if opposite_ok else 1

        if name_ok is not None:
            stats.setdefault("name_correct", 0)
            stats.setdefault("name_wrong", 0)
            stats["name_correct"] += 1 if bool(name_ok) else 0
            stats["name_wrong"] += 0 if bool(name_ok) else 1

        self.save()

    def register_confusion_wrong(self, name, level):
        """Wertet einen Namensverwechslungs-Tipp als zusätzliche falsche Antwort."""

        if name not in self.data.get("people", {}):
            return

        stats = self._level_stats(name, level)
        stats.setdefault("shown", 0)
        stats.setdefault("wrong", 0)
        stats.setdefault("streak", 0)

        stats["shown"] += 1
        stats["wrong"] += 1
        stats["streak"] = 0

        self._schedule_after_result(name, level, success=False)
        self.save()

    def aggregate_stats_for_names(self, names, level):
        """Aggregiert Kennzahlen über eine Personenliste für ein Level."""

        total_correct = 0
        total_wrong = 0
        total_shown = 0
        total_time = 0.0
        total_time_count = 0

        for name in names:
            if name not in self.data.get("people", {}):
                continue
            stats = self._level_stats(name, level)
            total_correct += int(stats.get("correct", 0))
            total_wrong += int(stats.get("wrong", 0))
            total_shown += int(stats.get("shown", 0))
            total_time += float(stats.get("response_time_total_sec", 0.0))
            total_time_count += int(stats.get("response_time_count", 0))

        total_answers = total_correct + total_wrong
        ratio = (total_correct / total_answers) if total_answers > 0 else 0.0
        avg_time = (total_time / total_time_count) if total_time_count > 0 else 0.0

        return {
            "shown": total_shown,
            "correct": total_correct,
            "wrong": total_wrong,
            "ratio": ratio,
            "avg_time_sec": avg_time,
            "time_count": total_time_count,
        }

    def level_stats_for_display(self, name, level):
        """Liefert eine Kopie der Kennzahlen für die GUI-Ausgabe."""

        return dict(self._level_stats(name, level))
