#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


_THIS_REPO_ROOT = Path(__file__).resolve().parents[1]
_PACKAGES_PATH = _THIS_REPO_ROOT / "packages"
if str(_PACKAGES_PATH) not in sys.path:
    sys.path.insert(0, str(_PACKAGES_PATH))

from textutils.normalize import normalize as normalize_greek


EXPECTED_COLUMNS = [
    "entry_id",
    "source",
    "ref",
    "chapter_title_gr",
    "chapter_title_en",
    "lemma_ids",
    "part_id",
    "greek",
    "greek_normalized",
    "translation",
    "trans_status",
    "e_vol",
    "e_page_start",
    "e_page_end",
    "word_count",
    "notes",
]

_ENTRY_RE = re.compile(r"^PAUL_AEG-7\.3\.(\d+)$")
_DIGITS_RE = re.compile(r"^\d+$")


def _word_count_simple(text: str) -> int:
    return len([t for t in (text or "").strip().split() if t])


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate data-workbench/entries_paul.csv.")
    ap.add_argument(
        "--csv",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "entries_paul.csv"),
        help="Path to entries_paul.csv",
    )
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 2

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    errors: list[str] = []
    warnings: list[str] = []
    if fieldnames != EXPECTED_COLUMNS:
        errors.append(f"Header mismatch. Expected {EXPECTED_COLUMNS}, got {fieldnames}")

    seen: set[str] = set()
    expected_next = 1
    for line_no, row in enumerate(rows, start=2):
        entry_id = (row.get("entry_id") or "").strip()
        ref = (row.get("ref") or "").strip()
        greek = row.get("greek") or ""
        greek_normalized = row.get("greek_normalized") or ""
        word_count = (row.get("word_count") or "").strip()

        if entry_id in seen:
            errors.append(f"line {line_no}: duplicate entry_id {entry_id!r}")
        seen.add(entry_id)

        match = _ENTRY_RE.match(entry_id)
        if not match:
            errors.append(f"line {line_no}: malformed Paul entry_id {entry_id!r}")
        else:
            number = int(match.group(1))
            if number != expected_next:
                errors.append(f"line {line_no}: expected sequential entry number {expected_next}, got {number}")
            expected_next += 1

        if ref and entry_id != f"PAUL_AEG-{ref}":
            errors.append(f"line {line_no}: entry_id/ref mismatch for {entry_id!r} and {ref!r}")
        if row.get("source") != "PAUL_AEG":
            errors.append(f"line {line_no}: source must be PAUL_AEG")
        if row.get("trans_status") != "draft":
            errors.append(f"line {line_no}: trans_status must be draft")
        if not greek.strip():
            errors.append(f"line {line_no}: greek must be non-empty")
        if greek_normalized != normalize_greek(greek):
            errors.append(f"line {line_no}: greek_normalized mismatch for {entry_id}")
        if not word_count or not _DIGITS_RE.match(word_count):
            errors.append(f"line {line_no}: word_count must be numeric")
        elif int(word_count) != _word_count_simple(greek):
            errors.append(f"line {line_no}: word_count mismatch for {entry_id}")
        for col in ["e_vol", "e_page_start", "e_page_end"]:
            value = (row.get(col) or "").strip()
            if value and not _DIGITS_RE.match(value):
                errors.append(f"line {line_no}: {col} must be numeric or empty")
        if not (row.get("translation") or "").strip():
            warnings.append(f"line {line_no}: blank translation for {entry_id}")

    if errors:
        print(f"Validation failed: {len(errors)} error(s)", file=sys.stderr)
        for msg in errors[:200]:
            print(f"- {msg}", file=sys.stderr)
        if len(errors) > 200:
            print(f"- ... and {len(errors) - 200} more", file=sys.stderr)
        return 2

    print(f"Validated {csv_path} ({len(rows)} rows)")
    print("OK")
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for msg in warnings[:20]:
            print(f"- {msg}")
        if len(warnings) > 20:
            print(f"- ... and {len(warnings) - 20} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
