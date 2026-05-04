"""Zentrale Konfiguration und Datenquellenmodelle fuer den Namens-Trainer."""

from dataclasses import dataclass
from pathlib import Path

from .app_info import APP_INFO
from .core.models import MODE_COMBINED, MODE_CSV, MODE_PHOTO
from bw_libs.app_paths import AppPaths

def discover_app_paths(start_dir: Path | None = None) -> AppPaths:
    """Return shared app paths for Namenfit using the central discovery logic."""

    return AppPaths.discover(
        app_name=APP_INFO.appdata_folder,
        start_dir=start_dir or Path(__file__).resolve().parent,
    )


def app_state_file(paths: AppPaths) -> Path:
    """Primary app-state store location."""

    return paths.data_dir / "app_state.json"


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
