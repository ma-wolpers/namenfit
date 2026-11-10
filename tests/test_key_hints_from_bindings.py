"""Menüs und Tooltips lesen ihre Tasten aus der Bindung (eine Quelle), Anzeige deutsch.

Echte Bindungstabelle (``QuizApp._bind_shortcuts``) an einem echten, nie gezeigten
``WindowShortcutBinder``; die Erwartung sind die Texte, die vorher neben den Bindungen standen.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from bw_gui.runtime import WindowShortcutBinder, ui
from bw_gui.shortcuts import humanize_shortcut

from app.ui.ui import QuizApp
from app.ui.ui_intents import UiIntent

UI_DIR = Path(__file__).resolve().parents[1] / "app" / "ui"
_SHORTCUT_LITERAL = re.compile(r'shortcut="[^"]+"')
_KEY_IN_LABEL = re.compile(r'label=f?"[^"]*\((?:Strg|Ctrl|Shift|Alt|Entf|Esc|Enter|F\d{1,2})\b[^"]*\)"')


class _Host:
    """Nur was ``_bind_shortcuts`` und ``_menu_label`` brauchen; Handler sind Stubs."""

    def __init__(self, root) -> None:
        self._shortcuts = WindowShortcutBinder(root)

    def __getattr__(self, name):
        if name.startswith(("_on_", "_open_", "_toggle_")):
            return lambda *args: None
        raise AttributeError(name)


@pytest.fixture
def host():
    root = ui.Tk()
    root.withdraw()
    instance = _Host(root)
    QuizApp._bind_shortcuts(instance)
    yield instance
    instance._shortcuts.dispose()
    root.destroy()


def test_tooltip_and_menu_keys_come_from_the_bindings(host):
    registry = host._shortcuts.registry
    shown = {
        intent: humanize_shortcut(registry.shortcut_for_intent(intent))
        for intent in (UiIntent.QUIZ_ENTER, UiIntent.QUIZ_TYPO, UiIntent.DEBUG_RUNTIME_OVERLAY, UiIntent.DEBUG_RUNTIME_OFFLINE)
    }
    assert shown == {
        UiIntent.QUIZ_ENTER: "Enter",
        UiIntent.QUIZ_TYPO: "Rücktaste",
        UiIntent.DEBUG_RUNTIME_OVERLAY: "Strg+Shift+D",
        UiIntent.DEBUG_RUNTIME_OFFLINE: "Strg+Shift+O",
    }
    label = QuizApp._menu_label(host, "Offline simulieren", UiIntent.DEBUG_RUNTIME_OFFLINE)
    assert label == "Offline simulieren (Strg+Shift+O)"


def test_no_key_names_as_text_in_menus_or_tooltips():
    hits = [
        f"{path.name}:{number}: {line.strip()}"
        for path in sorted(UI_DIR.rglob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if _SHORTCUT_LITERAL.search(line) or _KEY_IN_LABEL.search(line)
    ]
    assert hits == []
