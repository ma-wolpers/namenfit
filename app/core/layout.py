"""Einlesen und Aufbereiten von Sitzordnungen aus CSV-Dateien und Bildordnern."""

import csv
import os

from .models import SeatInfo


SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")


def make_person_key(group_name, person_name):
    """Erzeugt einen stabilen, gruppen-eindeutigen Schlüssel für eine Person."""

    return f"{group_name}::{person_name}"


def load_csv_layout(path, group_name=None):
    """
    Lädt die Sitzordnung aus einer CSV-Datei.

    Erwartung:
    - Zeile 1 = Header mit Tischgruppenbezeichnungen
    - Ab Zeile 2 = Namen im Sitzraster

    Rückgabe:
    - people: Dict Name -> SeatInfo
    - grid: 2D-Liste der CSV-Zellen (ohne Header)
    - header: Header-Zeile
    """

    with open(path, newline="", encoding="utf-8") as file_handle:
        rows = list(csv.reader(file_handle))

    if not rows:
        return {}, [], []

    header = rows[0]
    if group_name is None:
        group_name = os.path.splitext(os.path.basename(path))[0]
    grid = rows[1:]
    people = {}

    table_by_col = []
    last_table_label = ""
    for raw_label in header:
        label = raw_label.strip()
        if label:
            last_table_label = label
        table_by_col.append(last_table_label)

    for row_index, row in enumerate(grid):
        for col_index, raw_name in enumerate(row):
            display_name = raw_name.strip()
            if not display_name:
                continue

            table = table_by_col[col_index].strip() if col_index < len(table_by_col) else ""
            if not table:
                table = group_name
            person_key = make_person_key(group_name, display_name)
            people[person_key] = SeatInfo(
                row=row_index,
                col=col_index,
                table=table,
                name=display_name,
            )
            grid[row_index][col_index] = person_key

    return people, grid, header


def load_photo_folder(folder_path):
    """
    Lädt Namen und Bildpfade aus einem Ordner.

    Bildnamen entsprechen den Namen der Personen (ohne Extension).
    Beispiel: "Max.png" -> Name = "Max"

    Rückgabe:
    - photo_map: Dict Name -> absoluter Bildpfad
    """
    photo_map = {}

    if not folder_path or not os.path.isdir(folder_path):
        return photo_map

    for filename in os.listdir(folder_path):
        name_part, ext = os.path.splitext(filename)
        if ext.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue

        name = name_part.strip()
        if not name:
            continue

        full_path = os.path.join(folder_path, filename)
        photo_map[name] = full_path

    return photo_map
