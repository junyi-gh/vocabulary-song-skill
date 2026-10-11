#!/usr/bin/env python3
"""Validate a vocabulary-song JSON specification."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


TOP_FIELDS = {
    "title": str,
    "style_prompt": str,
    "bpm": int,
    "key": str,
    "duration_seconds": (int, float),
    "arrangement": dict,
    "vocal": dict,
    "words": list,
    "sections": list,
}
WORD_FIELDS = {
    "word": str,
    "ipa": str,
    "stress": str,
    "meaning_zh": str,
    "part_of_speech": str,
    "collocation": str,
    "example": str,
}


def load_spec(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("The JSON root must be an object.")
    return data


def validate(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for name, expected in TOP_FIELDS.items():
        if name not in data:
            errors.append(f"Missing top-level field: {name}")
        elif not isinstance(data[name], expected):
            errors.append(f"Field {name!r} has the wrong type")

    if errors:
        return errors, warnings

    bpm = data["bpm"]
    duration = data["duration_seconds"]
    if not 30 <= bpm <= 300:
        errors.append("bpm must be between 30 and 300")
    if not 10 <= duration <= 600:
        errors.append("duration_seconds must be between 10 and 600")
    if not 1 <= len(data["words"]) <= 12:
        errors.append("words must contain between 1 and 12 entries")
    if not data["sections"]:
        errors.append("sections must not be empty")

    arrangement = data["arrangement"]
    instruments = arrangement.get("instruments") if isinstance(arrangement, dict) else None
    if not isinstance(instruments, list) or len([item for item in instruments if isinstance(item, str) and item.strip()]) < 3:
        errors.append("arrangement.instruments must contain at least three named instrumental roles")
    if not isinstance(arrangement.get("arc"), str) or not arrangement.get("arc", "").strip():
        errors.append("arrangement.arc must describe the section-level musical development")

    vocal = data["vocal"]
    for field in ("format", "timbre", "accent", "diction", "delivery"):
        if not isinstance(vocal.get(field), str) or not vocal.get(field, "").strip():
            errors.append(f"vocal.{field} must be a non-empty string")

    lyric_lines: list[str] = []
    for index, section in enumerate(data["sections"], start=1):
        if not isinstance(section, dict):
            errors.append(f"Section {index} must be an object")
            continue
        if not isinstance(section.get("name"), str) or not section["name"].strip():
            errors.append(f"Section {index} needs a non-empty name")
        lines = section.get("lines")
        if not isinstance(lines, list) or not lines:
            errors.append(f"Section {index} needs a non-empty lines array")
            continue
        for line in lines:
            if not isinstance(line, str) or not line.strip():
                errors.append(f"Section {index} contains an invalid lyric line")
            else:
                lyric_lines.append(line.strip())

    lyrics = "\n".join(lyric_lines)
    seen_words: set[str] = set()
    for index, entry in enumerate(data["words"], start=1):
        if not isinstance(entry, dict):
            errors.append(f"Word entry {index} must be an object")
            continue
        for name, expected in WORD_FIELDS.items():
            if name not in entry:
                errors.append(f"Word entry {index} is missing {name}")
            elif not isinstance(entry[name], expected) or not entry[name].strip():
                errors.append(f"Word entry {index} has an invalid {name}")
        word = str(entry.get("word", "")).strip()
        normalized = word.casefold()
        if normalized in seen_words:
            errors.append(f"Duplicate target word: {word}")
        seen_words.add(normalized)
        if word:
            count = len(re.findall(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", lyrics, re.I))
            if count < 2:
                errors.append(f"Target word {word!r} appears only {count} time(s) in lyrics; minimum is 2")
            elif count > 6:
                warnings.append(f"Target word {word!r} appears {count} times; check for mechanical repetition")
        ipa = str(entry.get("ipa", ""))
        if ipa and not ((ipa.startswith("/") and ipa.endswith("/")) or (ipa.startswith("[") and ipa.endswith("]"))):
            warnings.append(f"IPA for {word!r} is not enclosed in /slashes/ or [brackets]")

    return errors, warnings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: validate_spec.py <song.json>", file=sys.stderr)
        return 2
    path = Path(argv[1]).expanduser().resolve()
    try:
        data = load_spec(path)
        errors, warnings = validate(data)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: {path.name} is a valid vocabulary-song specification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
