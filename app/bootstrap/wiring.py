from __future__ import annotations

from dataclasses import dataclass

from app.app_info import APP_INFO, AppInfo
from app.config import AppPaths
from app.storage.app_state_store import AppStateStore
from bw_libs.app_shell import AppShellConfig


@dataclass(frozen=True)
class AppDependencies:
    """Composition-root payload for Namenfit GUI startup."""

    app_info: AppInfo
    shell_config: AppShellConfig
    paths: AppPaths
    recent_store: AppStateStore


def build_gui_dependencies() -> AppDependencies:
    """Build GUI dependencies including persisted app-state services."""

    paths = AppPaths.discover()
    recent_store = AppStateStore(paths.app_state_file, max_entries=5)
    recent_store.migrate_from_legacy(paths.legacy_app_state_file)
    recent_store.migrate_from_legacy(paths.legacy_local_app_state_file)
    return AppDependencies(
        app_info=APP_INFO,
        shell_config=AppShellConfig(
            title=APP_INFO.window_title,
            geometry="980x860",
            min_width=760,
            min_height=620,
        ),
        paths=paths,
        recent_store=recent_store,
    )
