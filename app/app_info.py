from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppInfo:
    """Canonical identity metadata for the application."""

    name: str
    version: str
    appdata_folder: str
    window_title: str


APP_INFO = AppInfo(
    name="Namenfit",
    version="0.1.0-dev",
    appdata_folder="Namenfit",
    window_title="Namenfit",
)
