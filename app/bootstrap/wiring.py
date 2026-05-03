from __future__ import annotations

from dataclasses import dataclass

from app.config import AppPaths
from app.storage.app_state_store import AppStateStore
from bw_libs.app_shell import AppShellConfig


@dataclass(frozen=True)
class AppDependencies:
    """Composition-root payload for Namenfit GUI startup."""

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
        shell_config=AppShellConfig(
            title="Namenfit",
            geometry="980x860",
            min_width=760,
            min_height=620,
        ),
        paths=paths,
        recent_store=recent_store,
    )
