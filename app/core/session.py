"""Laufzeitaufbau des Trainers (Daten laden, validieren, Titel/Progress vorbereiten)."""

from dataclasses import dataclass
import hashlib
import os

from ..config import AppPaths
from .layout import SUPPORTED_IMAGE_EXTENSIONS, load_csv_layout, load_photo_folder, make_person_key
from .models import MODE_COMBINED, MODE_PHOTO
from ..storage.progress import ProgressStore, log_path_for_csv


@dataclass
class RuntimeSession:
    """Vollständig vorbereiteter Laufzeitkontext für die Quiz-GUI."""

    mode: str
    people: dict
    grid: list
    photo_map: dict
    progress_store: ProgressStore
    title: str
    ask_group_question: bool


class CombinedSourceMismatchError(ValueError):
    """Detaillierter Fehler bei CSV/Fotos-Unstimmigkeit im Kombi-Modus."""

    def __init__(self, message, csv_only_keys, photo_only_keys, common_keys):
        super().__init__(message)
        self.csv_only_keys = set(csv_only_keys)
        self.photo_only_keys = set(photo_only_keys)
        self.common_keys = set(common_keys)


def _photo_session_id(photo_folders):
    """Erzeugt einen stabilen Session-Key für Fotoquellen (pfadunabhängig)."""

    digest = hashlib.sha1()
    for folder in sorted(photo_folders):
        group_name = os.path.basename(folder.rstrip("\\/")) or folder
        digest.update(group_name.encode("utf-8", errors="ignore"))
        digest.update(b"\x1f")

        try:
            filenames = sorted(os.listdir(folder))
        except OSError:
            filenames = []

        for filename in filenames:
            name_part, ext = os.path.splitext(filename)
            if ext.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
                continue
            display_name = name_part.strip()
            if not display_name:
                continue
            digest.update(display_name.casefold().encode("utf-8", errors="ignore"))
            digest.update(b"\x1e")

        digest.update(b"\x1d")

    return digest.hexdigest()[:16]


def _person_label(person_key):
    """Formatiert einen internen Person-Key als lesbares Label."""

    if "::" in person_key:
        group_name, display_name = person_key.split("::", 1)
        return f"{display_name} ({group_name})"
    return person_key


def _format_mismatch_message(csv_only_keys, photo_only_keys):
    """Erzeugt eine detaillierte Fehlermeldung für CSV/Fotos-Unstimmigkeiten."""

    parts = [
        "CSV und Foto-Ordner passen nicht exakt zusammen.",
        "Bitte Namen/Dateinamen angleichen.",
    ]

    if csv_only_keys:
        csv_lines = "\n".join(f"- {_person_label(key)}" for key in sorted(csv_only_keys)[:30])
        if len(csv_only_keys) > 30:
            csv_lines += f"\n- ... (+{len(csv_only_keys) - 30} weitere)"
        parts.append("\nIn CSV vorhanden, aber kein passendes Foto:\n" + csv_lines)

    if photo_only_keys:
        photo_lines = "\n".join(f"- {_person_label(key)}" for key in sorted(photo_only_keys)[:30])
        if len(photo_only_keys) > 30:
            photo_lines += f"\n- ... (+{len(photo_only_keys) - 30} weitere)"
        parts.append("\nAls Foto vorhanden, aber nicht in CSV:\n" + photo_lines)

    return "\n".join(parts)


def build_runtime_session(selection, selected_level, allow_intersection_on_mismatch=False):
    """Erzeugt eine validierte RuntimeSession oder wirft ValueError bei Problemen."""

    csv_paths = list(selection.csv_paths)
    photo_folders = list(selection.photo_folders)
    mode = selection.mode
    ask_group_question = True

    people = {}
    grid = []
    photo_map = {}
    photo_groups = {}

    if csv_paths:
        merged_grid = []
        for csv_path in csv_paths:
            if not os.path.isfile(csv_path):
                raise ValueError(f"CSV-Datei nicht gefunden: {csv_path}")

            group_name = os.path.splitext(os.path.basename(csv_path))[0]
            csv_people, csv_grid, _header = load_csv_layout(csv_path, group_name=group_name)
            if not csv_people:
                raise ValueError(f"CSV enthält keine Personen: {csv_path}")

            duplicate_keys = set(people.keys()) & set(csv_people.keys())
            if duplicate_keys:
                duplicate_key = sorted(duplicate_keys)[0]
                duplicate_name = duplicate_key.split("::", 1)[1] if "::" in duplicate_key else duplicate_key
                raise ValueError(
                    "Doppelte Namen innerhalb derselben Lerngruppe sind nicht erlaubt: "
                    f"{duplicate_name} ({group_name})"
                )

            people.update(csv_people)
            merged_grid.extend(csv_grid)
            merged_grid.append([])

        if merged_grid and not merged_grid[-1]:
            merged_grid.pop()
        grid = merged_grid

    if photo_folders:
        for photo_folder in photo_folders:
            if not os.path.isdir(photo_folder):
                raise ValueError(f"Foto-Ordner nicht gefunden: {photo_folder}")

            loaded_photos = load_photo_folder(photo_folder)
            if not loaded_photos:
                raise ValueError(f"Der Ordner enthält keine Bilder: {photo_folder}")

            group_name = os.path.basename(photo_folder.rstrip("\\/")) or photo_folder
            for display_name, path in loaded_photos.items():
                person_key = make_person_key(group_name, display_name)
                if person_key in photo_map:
                    raise ValueError(
                        "Doppelte Namen innerhalb derselben Lerngruppe sind nicht erlaubt: "
                        f"{display_name} ({group_name})"
                    )
                photo_map[person_key] = path
                photo_groups[person_key] = group_name

    if mode == MODE_COMBINED:
        csv_keys = set(people.keys())
        photo_keys = set(photo_map.keys())
        common_keys = csv_keys & photo_keys
        csv_only = csv_keys - photo_keys
        photo_only = photo_keys - csv_keys

        if csv_only or photo_only:
            if not allow_intersection_on_mismatch:
                raise CombinedSourceMismatchError(
                    _format_mismatch_message(csv_only, photo_only),
                    csv_only_keys=csv_only,
                    photo_only_keys=photo_only,
                    common_keys=common_keys,
                )

            if not common_keys:
                raise ValueError(
                    "CSV und Foto-Ordner haben keine gemeinsame Schnittmenge; Start mit Schnittmenge ist nicht möglich."
                )

            people = {name: info for name, info in people.items() if name in common_keys}
            photo_map = {name: path for name, path in photo_map.items() if name in common_keys}

    if mode == MODE_PHOTO:
        from .models import SeatInfo

        people = {
            person_key: SeatInfo(
                row=0,
                col=0,
                table=photo_groups.get(person_key, ""),
                name=person_key.split("::", 1)[1] if "::" in person_key else person_key,
            )
            for person_key in photo_map.keys()
        }

    if mode == "photo" and len(photo_folders) == 1 and not csv_paths:
        ask_group_question = False

    if len(csv_paths) == 1 and not photo_folders:
        progress_path = log_path_for_csv(csv_paths[0])
    elif len(photo_folders) == 1 and not csv_paths:
        session_id = _photo_session_id(photo_folders)
        app_paths = AppPaths.discover()
        progress_path = str(app_paths.data_dir / f"photo_session_{session_id}.json")
    else:
        if photo_folders and not csv_paths:
            session_id = _photo_session_id(photo_folders)
            app_paths = AppPaths.discover()
            progress_path = str(app_paths.data_dir / f"photo_session_multi_{session_id}.json")
        else:
            base_dir = os.path.dirname(csv_paths[0]) if csv_paths else photo_folders[0]
            progress_path = os.path.join(base_dir, ".namenfit.multi.trainerlog.json")

    progress_store = ProgressStore(progress_path, people.keys())
    progress_store.reset_session_timeline()

    title_parts = []
    if mode == "combined":
        title_parts.append("Kombi-Modus")
    elif mode == "photo":
        title_parts.append("Foto-Modus")
    else:
        title_parts.append("CSV-Modus")

    if mode in ("csv", "combined"):
        title_parts.append(f"Level {selected_level}")

    return RuntimeSession(
        mode=mode,
        people=people,
        grid=grid,
        photo_map=photo_map,
        progress_store=progress_store,
        title=f"Namens-Trainer ({' · '.join(title_parts)})",
        ask_group_question=ask_group_question,
    )
