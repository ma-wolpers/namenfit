"""Zentrale Konfiguration und robuste Pfadauflösung für den Namens-Trainer.

Dieses Modul kapselt alle laufzeitabhängigen Pfade, sodass das Programm auf
unterschiedlichen Rechnern stabil funktioniert (auch wenn der Projektordner
verschoben wird).
"""

from dataclasses import dataclass
from pathlib import Path
import os

from .app_info import APP_INFO
from .core.models import MODE_COMBINED, MODE_CSV, MODE_PHOTO


APP_DIR_NAME = APP_INFO.appdata_folder


@dataclass(frozen=True)
class AppPaths:
    """Enthält relevante Dateipfade der Anwendung."""

    data_dir: Path
    app_state_file: Path
    legacy_app_state_file: Path
    legacy_local_app_state_file: Path

    @classmethod
    def discover(cls):
        """Ermittelt robust plattformabhängige Speicherorte.

        Windows:
            %APPDATA%/Namenfit
        Sonst:
            ~/.namenfit
        """

        if os.name == "nt":
            appdata = os.environ.get("APPDATA")
            if appdata:
                data_dir = Path(appdata) / APP_DIR_NAME
            else:
                data_dir = Path.home() / f".{APP_DIR_NAME.lower()}"
        else:
            data_dir = Path.home() / f".{APP_DIR_NAME.lower()}"

        data_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            data_dir=data_dir,
            app_state_file=data_dir / "app_state.json",
            legacy_app_state_file=data_dir / "recent_sources.json",
            legacy_local_app_state_file=Path(__file__).with_name(
                ".recent_sources.json"
            ),
        )


@dataclass(frozen=True)
class DataSourceSelection:
    """Auswahl aus dem Startdialog."""

    csv_paths: tuple[str, ...]
    photo_folders: tuple[str, ...]
    prompt_limit: int | None = None
    learning_settings: dict | None = None

    @property
    def csv_path(self):
        return self.csv_paths[0] if self.csv_paths else None

    @property
    def photo_folder(self):
        return self.photo_folders[0] if self.photo_folders else None

    @property
    def mode(self):
        if self.csv_paths and self.photo_folders:
            return MODE_COMBINED
        if self.csv_paths:
            return MODE_CSV
        return MODE_PHOTO
