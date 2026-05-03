#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:[/\\]|^/|^\\\\")


def _iter_json_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*.json") if path.is_file())


def _contains_absolute_path(value: object) -> bool:
    if isinstance(value, str):
        return bool(ABSOLUTE_PATH_RE.match(value.strip()))
    if isinstance(value, list):
        return any(_contains_absolute_path(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_absolute_path(item) for item in value.values())
    return False


def main() -> int:
    violations: list[str] = []
    for json_file in _iter_json_files():
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if _contains_absolute_path(payload):
            rel = json_file.relative_to(ROOT).as_posix()
            violations.append(rel)

    if violations:
        print("Absolute path guardrail failed:")
        for rel in violations:
            print(f" - {rel}")
        return 2

    print("Absolute path guardrail passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
