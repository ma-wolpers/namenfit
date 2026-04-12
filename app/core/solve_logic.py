"""Pure Auswertungslogik für Quiz-Phasen (ohne UI-Widgets)."""

from .models import answer_matches, directional_neighbors_of, normalize_text


def evaluate_group_guess(guess_group, correct_group):
    """Vergleicht eine Tischgruppen-Eingabe robust normalisiert."""

    return normalize_text(guess_group) == normalize_text(correct_group)


def evaluate_neighbors(current_name, people, grid, guess_behind, guess_front, guess_opposite):
    """Bewertet Nachbar-Eingaben und liefert Vergleichsdaten."""

    neighbors = directional_neighbors_of(current_name, people, grid)

    behind_ok = answer_matches(guess_behind, neighbors["behind"])
    front_ok = answer_matches(guess_front, neighbors["front"])
    opposite_ok = answer_matches(guess_opposite, neighbors["opposite"])

    return {
        "behind_ok": behind_ok,
        "front_ok": front_ok,
        "opposite_ok": opposite_ok,
        "behind_text": neighbors["behind"] or "—",
        "front_text": neighbors["front"] or "—",
        "opposite_text": neighbors["opposite"] or "—",
    }


def build_csv_level2_result_text(
    correct_group,
    group_ok,
    behind_ok,
    behind_text,
    opposite_ok,
    opposite_text,
    front_ok,
    front_text,
):
    """Erzeugt den Ergebnistext für CSV Level 2."""

    return (
        f"{'✅' if group_ok else '❌'} Tischgruppe: {correct_group}\n"
        f"{'✅' if behind_ok else '❌'} Dahinter: {behind_text}\n"
        f"{'✅' if opposite_ok else '❌'} Gegenüber: {opposite_text}\n"
        f"{'✅' if front_ok else '❌'} Davor: {front_text}"
    )


def _build_group_neighbors_lines(
    correct_group,
    group_ok,
    behind_ok,
    behind_text,
    opposite_ok,
    opposite_text,
    front_ok,
    front_text,
):
    """Gemeinsamer Textblock für Lerngruppe und Nachbar:innen."""

    return (
        f"{'✅' if group_ok else '❌'} Lerngruppe: {correct_group}\n"
        f"{'✅' if behind_ok else '❌'} Dahinter: {behind_text}\n"
        f"{'✅' if opposite_ok else '❌'} Gegenüber: {opposite_text}\n"
        f"{'✅' if front_ok else '❌'} Davor: {front_text}"
    )


def build_combined_level2_result_text(
    current_name,
    name_ok,
    correct_group,
    group_ok,
    behind_ok,
    behind_text,
    opposite_ok,
    opposite_text,
    front_ok,
    front_text,
):
    """Erzeugt den Ergebnistext für Kombi-Modus Level 2."""

    return (
        f"{'✅' if name_ok else '❌'} Name: {current_name}\n"
        + _build_group_neighbors_lines(
            correct_group,
            group_ok,
            behind_ok,
            behind_text,
            opposite_ok,
            opposite_text,
            front_ok,
            front_text,
        )
    )


def csv_level2_task_score(group_ok, behind_ok, front_ok, opposite_ok):
    success_count = int(group_ok) + int(behind_ok) + int(front_ok) + int(opposite_ok)
    return success_count / 4.0


def combined_level2_task_score(name_ok, group_ok, behind_ok, front_ok, opposite_ok):
    success_count = int(name_ok) + int(group_ok) + int(behind_ok) + int(front_ok) + int(opposite_ok)
    return success_count / 5.0
