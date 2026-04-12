"""Datenmodelle und reine Hilfsfunktionen des Trainers."""

from dataclasses import dataclass


LEVEL_1 = 1
LEVEL_2 = 2

# Modi für die Dateneingabe
MODE_CSV = "csv"
MODE_PHOTO = "photo"
MODE_COMBINED = "combined"


@dataclass(frozen=True)
class SeatInfo:
    """Sitzplatzdaten einer Person innerhalb des CSV-Rasters."""

    row: int
    col: int
    table: str
    name: str


def normalize_text(value):
    """Normalisiert Texteingaben für robuste, case-insensitive Vergleiche."""

    return (value or "").strip().casefold()


def is_empty_answer(value):
    """Erlaubte Platzhalter, wenn es keinen Nachbarn in der Richtung gibt."""

    return normalize_text(value) in {"", "-", "none", "niemand", "keiner", "kein"}


def answer_matches(guess, expected):
    """
    Vergleicht eine Nutzereingabe mit dem Erwartungswert.

    Wenn kein erwarteter Wert vorhanden ist, werden leere bzw. Platzhalter-
    Eingaben als korrekt akzeptiert.
    """

    if not expected:
        return is_empty_answer(guess)
    return normalize_text(guess) == normalize_text(expected)


def directional_neighbors_of(name, people, grid):
    """
    Ermittelt relative Nachbarn einer Person im Sitzraster.

    Richtungsdefinition:
    - behind: nächster belegter Sitz darüber (kleinere Zeile) in derselben Spalte
    - front: nächster belegter Sitz darunter (größere Zeile) in derselben Spalte
    - opposite: nächster belegter Sitz links oder rechts in derselben Zeile
    """

    seat = people[name]
    row_index = seat.row
    col_index = seat.col

    def find_vertical(step):
        current_row = row_index + step
        while 0 <= current_row < len(grid):
            if col_index < len(grid[current_row]):
                candidate = grid[current_row][col_index].strip()
                if (
                    candidate
                    and candidate in people
                    and people[candidate].table == seat.table
                ):
                    return people[candidate].name
            current_row += step
        return ""

    def find_opposite():
        distance = 1
        while True:
            left_col = col_index - distance
            right_col = col_index + distance
            checked_any = False

            if left_col >= 0:
                checked_any = True
                left_candidate = grid[row_index][left_col].strip()
                if (
                    left_candidate
                    and left_candidate in people
                    and people[left_candidate].table == seat.table
                ):
                    return people[left_candidate].name

            if right_col < len(grid[row_index]):
                checked_any = True
                right_candidate = grid[row_index][right_col].strip()
                if (
                    right_candidate
                    and right_candidate in people
                    and people[right_candidate].table == seat.table
                ):
                    return people[right_candidate].name

            if not checked_any:
                return ""

            distance += 1

    return {
        "behind": find_vertical(-1),
        "front": find_vertical(1),
        "opposite": find_opposite(),
    }
