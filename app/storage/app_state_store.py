"""Persistenter Speicher für Datenquellen-Verlauf und globale Präferenzen.

Speichert CSV-Dateien, Foto-Ordner, Kombinationen sowie startrelevante
UI-/Lern-Defaults in einer JSON-Datei. Ungültige Quell-Einträge werden beim
Laden automatisch bereinigt.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import os

from ..core.learning_profiles import (
    DEFAULT_LEARNING_SETTINGS,
    normalize_learning_settings,
)
from ..ui.ui_theme import DEFAULT_THEME, normalize_theme_key


DEFAULT_LAST_LEVEL = 1
DEFAULT_PROMPT_LIMIT = 80
DEFAULT_DEBUG_OPTIONS = {
    "show_debug_panel": False,
    "show_paths": False,
}
DEFAULT_SOUND_OPTIONS = {
    "enabled": True,
    "volume": 70,
}
DEFAULT_LEVEL2_REQUIRE_GROUP_BEFORE_NEIGHBORS = False

RELATIVE_7THCLOUD_PREFIX = "7THCLOUD_REL::"
ROOT_FOLDER_NAME = "7thCloud"


def _norm(path):
    return os.path.normcase(os.path.abspath(path))


def _normalize_level2_group_gate(value):
    return bool(value)


def _find_root_named(path, root_name):
    if not isinstance(path, str) or not path.strip():
        return None

    current = os.path.abspath(path)
    if not os.path.isdir(current):
        current = os.path.dirname(current)

    if not current:
        return None

    expected = root_name.casefold()
    while True:
        base = os.path.basename(current.rstrip("\\/"))
        if base and base.casefold() == expected:
            return current

        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _resolve_7thcloud_root():
    from_cwd = _find_root_named(os.getcwd(), ROOT_FOLDER_NAME)
    if from_cwd:
        return from_cwd

    from_module = _find_root_named(__file__, ROOT_FOLDER_NAME)
    if from_module:
        return from_module

    return None


def _serialize_source_path(path):
    if not isinstance(path, str) or not path.strip():
        return None

    absolute = os.path.abspath(path)
    root = _find_root_named(absolute, ROOT_FOLDER_NAME)
    if not root:
        return None

    try:
        relative = os.path.relpath(absolute, root)
    except ValueError:
        return None

    if relative.startswith(".."):
        return None

    return RELATIVE_7THCLOUD_PREFIX + relative.replace("\\", "/")


def _deserialize_source_path(value):
    if not isinstance(value, str) or not value.strip():
        return None

    if value.startswith(RELATIVE_7THCLOUD_PREFIX):
        relative = value[len(RELATIVE_7THCLOUD_PREFIX) :].replace("/", os.sep)
        root = _resolve_7thcloud_root()
        if not root:
            return None
        return os.path.abspath(os.path.join(root, relative))

    # Altbestand: absolute Pfade bleiben lesbar.
    return os.path.abspath(value)


def _normalize_last_level(level):
    value = int(level) if isinstance(level, (int, float)) else DEFAULT_LAST_LEVEL
    return value if value in (1, 2) else DEFAULT_LAST_LEVEL


def _normalize_debug_options(options):
    source = options if isinstance(options, dict) else {}
    return {
        "show_debug_panel": bool(
            source.get("show_debug_panel", DEFAULT_DEBUG_OPTIONS["show_debug_panel"])
        ),
        "show_paths": bool(
            source.get("show_paths", DEFAULT_DEBUG_OPTIONS["show_paths"])
        ),
    }


def _normalize_prompt_limit(limit):
    if limit is None:
        return None
    if isinstance(limit, str):
        value = limit.strip().lower()
        if value in ("", "none", "inf", "infinite", "unendlich", "∞"):
            return None
        try:
            limit = int(value)
        except ValueError:
            return DEFAULT_PROMPT_LIMIT
    elif not isinstance(limit, (int, float)):
        return DEFAULT_PROMPT_LIMIT

    normalized = int(limit)
    if normalized <= 0:
        return DEFAULT_PROMPT_LIMIT
    return normalized


def _normalize_sound_options(options):
    source = options if isinstance(options, dict) else {}
    try:
        volume = int(source.get("volume", DEFAULT_SOUND_OPTIONS["volume"]))
    except (TypeError, ValueError):
        volume = DEFAULT_SOUND_OPTIONS["volume"]
    volume = max(0, min(100, volume))
    return {
        "enabled": bool(source.get("enabled", DEFAULT_SOUND_OPTIONS["enabled"])),
        "volume": volume,
    }


def _normalize_dialog_initial_dirs(initial_dirs):
    source = initial_dirs if isinstance(initial_dirs, dict) else {}
    cleaned = {}
    for purpose, path in source.items():
        if not isinstance(purpose, str) or not purpose.strip():
            continue
        if not isinstance(path, str) or not path.strip():
            continue
        normalized = os.path.abspath(path)
        if os.path.isdir(normalized):
            cleaned[purpose] = normalized
    return cleaned


@dataclass
class AppStateStore:
    """Verwaltet Quellenverlauf und globale Standard-Einstellungen."""

    file_path: Path
    max_entries: int = 5

    def migrate_from_legacy(self, legacy_path):
        """Übernimmt alte Recent-Datei am bisherigen Speicherort (best effort)."""

        if self.file_path.exists() or not legacy_path:
            return

        legacy = Path(legacy_path)
        if not legacy.exists():
            return

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(
                legacy.read_text(encoding="utf-8"), encoding="utf-8"
            )
        except Exception:
            return

    def load(self):
        default = {
            "csv": [],
            "photos": [],
            "combined": [],
            "dialog_initial_dirs": {},
            "last_session": {
                "csv_paths": [],
                "photo_folders": [],
                "prompt_limit": DEFAULT_PROMPT_LIMIT,
            },
            "prompt_limit_default": DEFAULT_PROMPT_LIMIT,
            "sound_options": dict(DEFAULT_SOUND_OPTIONS),
            "ui_theme": DEFAULT_THEME,
            "learning_defaults": dict(DEFAULT_LEARNING_SETTINGS),
            "last_level": DEFAULT_LAST_LEVEL,
            "debug_options": dict(DEFAULT_DEBUG_OPTIONS),
            "level2_require_group_before_neighbors": DEFAULT_LEVEL2_REQUIRE_GROUP_BEFORE_NEIGHBORS,
        }

        if not self.file_path.exists():
            return default

        try:
            loaded = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return default

        csv_entries = loaded.get("csv", []) if isinstance(loaded, dict) else []
        photo_entries = loaded.get("photos", []) if isinstance(loaded, dict) else []
        combined_entries = (
            loaded.get("combined", []) if isinstance(loaded, dict) else []
        )

        csv_clean = []
        for entry in csv_entries:
            resolved = _deserialize_source_path(entry)
            if resolved and os.path.isfile(resolved):
                csv_clean.append(resolved)
            if len(csv_clean) >= self.max_entries:
                break

        photos_clean = []
        for entry in photo_entries:
            resolved = _deserialize_source_path(entry)
            if resolved and os.path.isdir(resolved):
                photos_clean.append(resolved)
            if len(photos_clean) >= self.max_entries:
                break

        combined_clean = []
        for item in combined_entries:
            if not isinstance(item, dict):
                continue
            csv_path = item.get("csv")
            photo_path = item.get("photo")
            if not isinstance(csv_path, str) or not isinstance(photo_path, str):
                continue
            resolved_csv = _deserialize_source_path(csv_path)
            resolved_photo = _deserialize_source_path(photo_path)
            if resolved_csv and resolved_photo and os.path.isfile(resolved_csv) and os.path.isdir(resolved_photo):
                combined_clean.append({"csv": resolved_csv, "photo": resolved_photo})
            if len(combined_clean) >= self.max_entries:
                break

        data = {
            "csv": csv_clean,
            "photos": photos_clean,
            "combined": combined_clean,
            "dialog_initial_dirs": loaded.get("dialog_initial_dirs", {})
            if isinstance(loaded, dict)
            else {},
            "last_session": (
                loaded.get(
                    "last_session",
                    {
                        "csv_paths": [],
                        "photo_folders": [],
                        "prompt_limit": DEFAULT_PROMPT_LIMIT,
                    },
                )
                if isinstance(loaded, dict)
                else {
                    "csv_paths": [],
                    "photo_folders": [],
                    "prompt_limit": DEFAULT_PROMPT_LIMIT,
                }
            ),
            "prompt_limit_default": (
                loaded.get("prompt_limit_default", DEFAULT_PROMPT_LIMIT)
                if isinstance(loaded, dict)
                else DEFAULT_PROMPT_LIMIT
            ),
            "sound_options": (
                loaded.get("sound_options", dict(DEFAULT_SOUND_OPTIONS))
                if isinstance(loaded, dict)
                else dict(DEFAULT_SOUND_OPTIONS)
            ),
            "ui_theme": loaded.get("ui_theme", DEFAULT_THEME)
            if isinstance(loaded, dict)
            else DEFAULT_THEME,
            "learning_defaults": (
                loaded.get("learning_defaults", dict(DEFAULT_LEARNING_SETTINGS))
                if isinstance(loaded, dict)
                else dict(DEFAULT_LEARNING_SETTINGS)
            ),
            "last_level": loaded.get("last_level", DEFAULT_LAST_LEVEL)
            if isinstance(loaded, dict)
            else DEFAULT_LAST_LEVEL,
            "debug_options": (
                loaded.get("debug_options", dict(DEFAULT_DEBUG_OPTIONS))
                if isinstance(loaded, dict)
                else dict(DEFAULT_DEBUG_OPTIONS)
            ),
            "level2_require_group_before_neighbors": (
                loaded.get(
                    "level2_require_group_before_neighbors",
                    DEFAULT_LEVEL2_REQUIRE_GROUP_BEFORE_NEIGHBORS,
                )
                if isinstance(loaded, dict)
                else DEFAULT_LEVEL2_REQUIRE_GROUP_BEFORE_NEIGHBORS
            ),
        }
        data["ui_theme"] = normalize_theme_key(data["ui_theme"])
        data["learning_defaults"] = normalize_learning_settings(
            data["learning_defaults"]
        )
        data["last_level"] = _normalize_last_level(data["last_level"])
        data["debug_options"] = _normalize_debug_options(data["debug_options"])
        data["dialog_initial_dirs"] = _normalize_dialog_initial_dirs(
            data.get("dialog_initial_dirs")
        )
        data["last_session"] = self._normalize_last_session(data.get("last_session"))
        data["prompt_limit_default"] = _normalize_prompt_limit(
            data.get("prompt_limit_default")
        )
        data["sound_options"] = _normalize_sound_options(data.get("sound_options"))
        data["level2_require_group_before_neighbors"] = _normalize_level2_group_gate(
            data.get("level2_require_group_before_neighbors")
        )
        self.save(data)
        return data

    def save(self, data):
        payload = {
            "csv": list(data.get("csv", []))[: self.max_entries],
            "photos": list(data.get("photos", []))[: self.max_entries],
            "combined": list(data.get("combined", []))[: self.max_entries],
            "dialog_initial_dirs": data.get("dialog_initial_dirs", {}),
            "last_session": data.get(
                "last_session", {"csv_paths": [], "photo_folders": []}
            ),
            "prompt_limit_default": data.get(
                "prompt_limit_default", DEFAULT_PROMPT_LIMIT
            ),
            "sound_options": data.get("sound_options", dict(DEFAULT_SOUND_OPTIONS)),
            "ui_theme": data.get("ui_theme", DEFAULT_THEME),
            "learning_defaults": data.get(
                "learning_defaults", dict(DEFAULT_LEARNING_SETTINGS)
            ),
            "last_level": data.get("last_level", DEFAULT_LAST_LEVEL),
            "debug_options": data.get("debug_options", dict(DEFAULT_DEBUG_OPTIONS)),
            "level2_require_group_before_neighbors": data.get(
                "level2_require_group_before_neighbors",
                DEFAULT_LEVEL2_REQUIRE_GROUP_BEFORE_NEIGHBORS,
            ),
        }
        payload["ui_theme"] = normalize_theme_key(payload["ui_theme"])
        payload["learning_defaults"] = normalize_learning_settings(
            payload["learning_defaults"]
        )
        payload["last_level"] = _normalize_last_level(payload["last_level"])
        payload["debug_options"] = _normalize_debug_options(payload["debug_options"])
        payload["dialog_initial_dirs"] = _normalize_dialog_initial_dirs(
            payload.get("dialog_initial_dirs")
        )
        payload["last_session"] = self._normalize_last_session(
            payload.get("last_session")
        )
        payload["prompt_limit_default"] = _normalize_prompt_limit(
            payload.get("prompt_limit_default")
        )
        payload["sound_options"] = _normalize_sound_options(
            payload.get("sound_options")
        )
        payload["level2_require_group_before_neighbors"] = _normalize_level2_group_gate(
            payload.get("level2_require_group_before_neighbors")
        )

        serialized_csv = []
        for path in payload.get("csv", []):
            encoded = _serialize_source_path(path)
            if encoded:
                serialized_csv.append(encoded)

        serialized_photos = []
        for path in payload.get("photos", []):
            encoded = _serialize_source_path(path)
            if encoded:
                serialized_photos.append(encoded)

        serialized_combined = []
        for item in payload.get("combined", []):
            if not isinstance(item, dict):
                continue
            encoded_csv = _serialize_source_path(item.get("csv"))
            encoded_photo = _serialize_source_path(item.get("photo"))
            if not encoded_csv or not encoded_photo:
                continue
            serialized_combined.append({"csv": encoded_csv, "photo": encoded_photo})

        last_session = payload.get("last_session", {})
        last_session_csv = []
        for path in last_session.get("csv_paths", []):
            encoded = _serialize_source_path(path)
            if encoded:
                last_session_csv.append(encoded)

        last_session_photos = []
        for path in last_session.get("photo_folders", []):
            encoded = _serialize_source_path(path)
            if encoded:
                last_session_photos.append(encoded)

        payload["csv"] = serialized_csv[: self.max_entries]
        payload["photos"] = serialized_photos[: self.max_entries]
        payload["combined"] = serialized_combined[: self.max_entries]
        payload["last_session"] = {
            "csv_paths": last_session_csv,
            "photo_folders": last_session_photos,
            "prompt_limit": _normalize_prompt_limit(last_session.get("prompt_limit")),
        }
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def remove_invalid_path(self, path, kind):
        data = self.load()
        key = "csv" if kind == "csv" else "photos"
        normalized = _norm(path)
        data[key] = [p for p in data.get(key, []) if _norm(p) != normalized]
        data["combined"] = [
            item
            for item in data.get("combined", [])
            if _norm(item.get("csv", "")) != normalized
            and _norm(item.get("photo", "")) != normalized
        ]
        self.save(data)

    def register(self, csv_path=None, photo_folder=None):
        return self.register_many(
            [csv_path] if csv_path else [],
            [photo_folder] if photo_folder else [],
        )

    def can_store_source_path(self, path):
        return bool(_serialize_source_path(path))

    def register_many(self, csv_paths=None, photo_folders=None):
        data = self.load()

        csv_paths = list(csv_paths or [])
        photo_folders = list(photo_folders or [])

        for csv_path in csv_paths:
            if csv_path and os.path.isfile(csv_path) and self.can_store_source_path(csv_path):
                data["csv"] = self._push_path(data.get("csv", []), csv_path)

        for photo_folder in photo_folders:
            if photo_folder and os.path.isdir(photo_folder) and self.can_store_source_path(photo_folder):
                data["photos"] = self._push_path(data.get("photos", []), photo_folder)

        if len(csv_paths) == 1 and len(photo_folders) == 1:
            csv_path = csv_paths[0]
            photo_folder = photo_folders[0]
            if (
                os.path.isfile(csv_path)
                and os.path.isdir(photo_folder)
                and self.can_store_source_path(csv_path)
                and self.can_store_source_path(photo_folder)
            ):
                data["combined"] = self._push_combined(
                    data.get("combined", []), csv_path, photo_folder
                )

        self.save(data)
        return data

    def _push_path(self, items, path):
        normalized = _norm(path)
        result = [entry for entry in items if _norm(entry) != normalized]
        result.insert(0, os.path.abspath(path))
        return result[: self.max_entries]

    def _push_combined(self, items, csv_path, photo_folder):
        csv_norm = _norm(csv_path)
        photo_norm = _norm(photo_folder)
        result = []

        for entry in items:
            if not isinstance(entry, dict):
                continue
            entry_csv = entry.get("csv")
            entry_photo = entry.get("photo")
            if not isinstance(entry_csv, str) or not isinstance(entry_photo, str):
                continue
            if _norm(entry_csv) == csv_norm and _norm(entry_photo) == photo_norm:
                continue
            result.append({"csv": entry_csv, "photo": entry_photo})

        result.insert(
            0,
            {"csv": os.path.abspath(csv_path), "photo": os.path.abspath(photo_folder)},
        )
        return result[: self.max_entries]

    def _normalize_last_session(self, session):
        source = session if isinstance(session, dict) else {}
        csv_paths = (
            source.get("csv_paths", [])
            if isinstance(source.get("csv_paths", []), list)
            else []
        )
        photo_folders = (
            source.get("photo_folders", [])
            if isinstance(source.get("photo_folders", []), list)
            else []
        )
        prompt_limit = _normalize_prompt_limit(
            source.get("prompt_limit", DEFAULT_PROMPT_LIMIT)
        )

        csv_clean = []
        seen_csv = set()
        for csv_path in csv_paths:
            resolved = _deserialize_source_path(csv_path)
            if not resolved or not os.path.isfile(resolved):
                continue
            if not self.can_store_source_path(resolved):
                continue
            normalized = _norm(resolved)
            if normalized in seen_csv:
                continue
            seen_csv.add(normalized)
            csv_clean.append(os.path.abspath(resolved))

        photo_clean = []
        seen_photos = set()
        for photo_folder in photo_folders:
            resolved = _deserialize_source_path(photo_folder)
            if not resolved or not os.path.isdir(resolved):
                continue
            if not self.can_store_source_path(resolved):
                continue
            normalized = _norm(resolved)
            if normalized in seen_photos:
                continue
            seen_photos.add(normalized)
            photo_clean.append(os.path.abspath(resolved))

        return {
            "csv_paths": csv_clean,
            "photo_folders": photo_clean,
            "prompt_limit": prompt_limit,
        }

    def get_theme_key(self):
        data = self.load()
        return normalize_theme_key(data.get("ui_theme", DEFAULT_THEME))

    def get_last_dialog_dir(self, purpose):
        if not isinstance(purpose, str) or not purpose.strip():
            return None
        data = self.load()
        dialog_dirs = _normalize_dialog_initial_dirs(data.get("dialog_initial_dirs"))
        return dialog_dirs.get(purpose)

    def set_last_dialog_dir(self, purpose, selected_path):
        if not isinstance(purpose, str) or not purpose.strip():
            return
        if not isinstance(selected_path, str) or not selected_path.strip():
            return

        candidate = os.path.abspath(selected_path)
        directory = (
            candidate if os.path.isdir(candidate) else os.path.dirname(candidate)
        )
        if not directory or not os.path.isdir(directory):
            return

        data = self.load()
        dialog_dirs = _normalize_dialog_initial_dirs(data.get("dialog_initial_dirs"))
        dialog_dirs[purpose] = os.path.abspath(directory)
        data["dialog_initial_dirs"] = dialog_dirs
        self.save(data)

    def set_theme_key(self, theme_key):
        data = self.load()
        data["ui_theme"] = normalize_theme_key(theme_key)
        self.save(data)

    def get_learning_defaults(self):
        data = self.load()
        return normalize_learning_settings(
            data.get("learning_defaults", dict(DEFAULT_LEARNING_SETTINGS))
        )

    def set_learning_defaults(self, settings):
        data = self.load()
        data["learning_defaults"] = normalize_learning_settings(settings)
        self.save(data)

    def get_last_level(self):
        data = self.load()
        return _normalize_last_level(data.get("last_level", DEFAULT_LAST_LEVEL))

    def set_last_level(self, level):
        data = self.load()
        data["last_level"] = _normalize_last_level(level)
        self.save(data)

    def get_debug_options(self):
        data = self.load()
        return _normalize_debug_options(
            data.get("debug_options", dict(DEFAULT_DEBUG_OPTIONS))
        )

    def set_debug_options(self, options):
        data = self.load()
        data["debug_options"] = _normalize_debug_options(options)
        self.save(data)

    def get_prompt_limit_default(self):
        data = self.load()
        return _normalize_prompt_limit(data.get("prompt_limit_default"))

    def set_prompt_limit_default(self, prompt_limit):
        data = self.load()
        data["prompt_limit_default"] = _normalize_prompt_limit(prompt_limit)
        self.save(data)

    def get_last_session_selection(self):
        data = self.load()
        return self._normalize_last_session(data.get("last_session"))

    def get_sound_options(self):
        data = self.load()
        return _normalize_sound_options(
            data.get("sound_options", dict(DEFAULT_SOUND_OPTIONS))
        )

    def set_sound_options(self, options):
        data = self.load()
        data["sound_options"] = _normalize_sound_options(options)
        self.save(data)

    def get_level2_require_group_before_neighbors(self):
        data = self.load()
        return _normalize_level2_group_gate(
            data.get(
                "level2_require_group_before_neighbors",
                DEFAULT_LEVEL2_REQUIRE_GROUP_BEFORE_NEIGHBORS,
            )
        )

    def set_level2_require_group_before_neighbors(self, enabled):
        data = self.load()
        data["level2_require_group_before_neighbors"] = _normalize_level2_group_gate(
            enabled
        )
        self.save(data)

    def set_last_session_selection(
        self, csv_paths=None, photo_folders=None, prompt_limit=DEFAULT_PROMPT_LIMIT
    ):
        data = self.load()
        data["last_session"] = self._normalize_last_session(
            {
                "csv_paths": list(csv_paths or []),
                "photo_folders": list(photo_folders or []),
                "prompt_limit": prompt_limit,
            }
        )
        self.save(data)


# Backward-compatible alias for existing imports.
RecentSourcesStore = AppStateStore
