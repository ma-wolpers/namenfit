"""UI-Zustandslogik für die Eingabefelder je Quiz-Phase."""

from ..core.models import LEVEL_1, LEVEL_2, MODE_COMBINED, MODE_CSV, MODE_PHOTO
from ..core.quiz_texts import PHASE_DONE, PHASE_GROUP, PHASE_NAME, PHASE_NEIGHBORS


def apply_phase_ui(app):
    """Aktiviert/Deaktiviert Eingabefelder basierend auf Modus, Level und Phase."""

    if app.mode == MODE_CSV and app.level == LEVEL_1:
        if app.ask_group_question:
            app.group_entry.config(state="normal")
            app.group_entry.focus_set()
        else:
            app.group_entry.config(state="disabled")
        return

    if app.mode == MODE_CSV and app.level == LEVEL_2:
        if app.current_phase == PHASE_GROUP:
            app.group_entry.config(state="normal")
            app.behind_entry.config(state="disabled")
            app.front_entry.config(state="disabled")
            app.opposite_entry.config(state="disabled")
            app.group_entry.focus_set()
        elif app.current_phase == PHASE_NEIGHBORS:
            app.group_entry.config(state="disabled")
            app.behind_entry.config(state="normal")
            app.front_entry.config(state="normal")
            app.opposite_entry.config(state="normal")
            app.behind_entry.focus_set()
        elif app.current_phase == PHASE_DONE:
            app.group_entry.config(state="disabled")
            app.behind_entry.config(state="disabled")
            app.front_entry.config(state="disabled")
            app.opposite_entry.config(state="disabled")
        return

    if app.mode == MODE_PHOTO:
        if app.current_phase == PHASE_NAME:
            app.name_entry.config(state="normal")
            app.group_entry.config(state="disabled")
            app.name_entry.focus_set()
        elif app.current_phase == PHASE_GROUP:
            app.name_entry.config(state="disabled")
            if app.ask_group_question:
                app.group_entry.config(state="normal")
                app.group_entry.focus_set()
            else:
                app.group_entry.config(state="disabled")
        elif app.current_phase == PHASE_DONE:
            app.name_entry.config(state="disabled")
            app.group_entry.config(state="disabled")
        return

    if app.mode == MODE_COMBINED:
        if app.current_phase == PHASE_NAME:
            app.name_entry.config(state="normal")
            app.group_entry.config(state="disabled")
            app.behind_entry.config(state="disabled")
            app.front_entry.config(state="disabled")
            app.opposite_entry.config(state="disabled")
            app.name_entry.focus_set()
        elif app.current_phase == PHASE_GROUP:
            app.name_entry.config(state="disabled")
            app.group_entry.config(state="normal")
            app.behind_entry.config(state="disabled")
            app.front_entry.config(state="disabled")
            app.opposite_entry.config(state="disabled")
            app.group_entry.focus_set()
        elif app.current_phase == PHASE_NEIGHBORS:
            app.name_entry.config(state="disabled")
            app.group_entry.config(state="disabled")
            app.behind_entry.config(state="normal")
            app.front_entry.config(state="normal")
            app.opposite_entry.config(state="normal")
            app.behind_entry.focus_set()
        elif app.current_phase == PHASE_DONE:
            app.name_entry.config(state="disabled")
            app.group_entry.config(state="disabled")
            app.behind_entry.config(state="disabled")
            app.front_entry.config(state="disabled")
            app.opposite_entry.config(state="disabled")
