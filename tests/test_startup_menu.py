"""Startdialog-Menü: bw-gui CustomMenuBar statt nativer tk.Menu (synthetische Daten)."""

from __future__ import annotations

import pytest

from bw_gui.menu import CustomMenuBar
from bw_gui.menu._toggle_glyphs import menu_item_command
from bw_gui.runtime import ui

from app.ui.startup_dialog import _build_start_menu


@pytest.fixture(scope="module")
def _module_root():
    # One interpreter per module: creating/destroying several tk.Tk() back to back
    # intermittently fails on Windows (Tcl init race, see bw-gui tests/conftest.py).
    window = ui.Tk()
    window.withdraw()
    yield window
    window.destroy()


@pytest.fixture
def root(_module_root):
    yield _module_root
    for child in _module_root.winfo_children():
        child.destroy()


def _build(root, calls):
    bool_var = lambda value=False: ui.BooleanVar(master=root, value=value)  # noqa: E731
    variables = {
        "theme_var": ui.StringVar(master=root, value="mono_day"),
        "learning_profile_var": ui.StringVar(master=root, value="custom"),
        "review_profile_var": ui.StringVar(master=root, value="mittel"),
        "allow_immediate_repeat_var": bool_var(),
        "prioritize_urgent_var": bool_var(True),
        "mix_new_cards_var": bool_var(),
        "min_retrieval_seconds_var": ui.IntVar(master=root, value=0),
        "revisit_slow_correct_var": bool_var(),
        "slow_correct_threshold_var": ui.IntVar(master=root, value=4),
        "feedback_style_var": ui.StringVar(master=root, value="neutral"),
        "debug_show_panel_var": bool_var(),
        "debug_show_paths_var": bool_var(),
    }
    note = lambda name: (lambda *_args, **_kwargs: calls.append(name))  # noqa: E731
    bar = _build_start_menu(
        root,
        "mono_day",
        {"csv": ["C:/demo/klasse.csv"], "photos": [], "combined": []},
        note("pick_recent"),
        on_theme_changed=note("theme"),
        on_learning_profile_changed=note("profile"),
        on_review_profile_changed=note("review"),
        on_learning_toggles_changed=note("toggles"),
        on_min_retrieval_changed=note("min"),
        on_slow_correct_threshold_changed=note("slow"),
        on_feedback_style_changed=note("feedback"),
        on_debug_options_changed=note("debug"),
        **variables,
    )
    return bar, variables


def _items(bar: CustomMenuBar, key: str):
    return next(d for d in bar.definitions if d.key == key).items_provider()


def test_start_menu_uses_custom_menu_bar_with_four_sections(root) -> None:
    bar, _variables = _build(root, [])
    assert isinstance(bar, CustomMenuBar)
    assert [d.label for d in bar.definitions] == ["Datei", "Ansicht", "Lernen", "Debug"]


def test_recent_entries_and_empty_placeholder(root) -> None:
    calls: list[str] = []
    bar, _variables = _build(root, calls)
    csv_menu, photo_menu, _combined, close = _items(bar, "file")
    assert [item.label for item in csv_menu.items] == ["klasse.csv"]
    csv_menu.items[0].command()
    assert calls == ["pick_recent"]
    assert [(item.type, item.label) for item in photo_menu.items] == [("disabled", "(keine)")]
    assert close.label == "Schließen"


def test_learning_switch_applies_requested_value(root) -> None:
    calls: list[str] = []
    bar, variables = _build(root, calls)
    switch = next(item for item in _items(bar, "lernen") if item.label == "Fehler-Relearn priorisieren")
    assert switch.type == "switch" and switch.checked is True
    menu_item_command(switch)()
    assert variables["prioritize_urgent_var"].get() is False
    assert calls == ["toggles"]


def test_debug_switches_and_theme_radios(root) -> None:
    calls: list[str] = []
    bar, variables = _build(root, calls)
    panel = _items(bar, "debug")[0]
    menu_item_command(panel)()
    assert variables["debug_show_panel_var"].get() is True and calls == ["debug"]
    themes = _items(bar, "view")
    assert all(item.type == "radio" for item in themes)
    assert sum(item.checked for item in themes) == 1
