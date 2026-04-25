#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_THIS_REPO_ROOT = Path(__file__).resolve().parents[1]

_REVIEW_METADATA_FIELDS = [
    "source_line_no",
    "ref",
    "previous_ref",
    "next_ref",
    "priority",
    "audit_flags",
    "review_status",
    "decision",
    "notes",
]

_REVIEW_EDITABLE_FIELDS = [
    "review_status",
    "decision",
    "notes",
    "corrected_lemma_gr",
    "corrected_entry_gr",
    "corrected_lemma_en",
    "corrected_entry_en",
]

_CORRECTED_FIELDS = [
    "corrected_lemma_gr",
    "corrected_entry_gr",
    "corrected_lemma_en",
    "corrected_entry_en",
]

_TEXT_COLUMNS = ["lemma_gr", "entry_gr", "lemma_en", "entry_en"]
_HIGH_PRIORITY_FLAGS = {
    "BOOK_ORDER_DECREASE",
    "CHAPTER_ORDER_DECREASE",
    "CHAPTER_NON_NUMERIC_UNEXPECTED",
    "DUPLICATE_BOOK_CHAPTER",
    "DUPLICATE_STRUCTURAL_KEY",
    "ENTRY_EN_BLANK",
    "ENTRY_EN_GREEK_HEAVY",
    "ENTRY_GR_BLANK",
    "ENTRY_GR_HOST_RV_PAYLOAD",
    "ENTRY_GR_LATIN_HEAVY",
    "ENTRY_GR_PRESENTATION_PREFIX",
    "LEMMA_EN_BLANK",
    "LEMMA_EN_GREEK_HEAVY",
    "LEMMA_GR_BLANK",
    "LEMMA_GR_LATIN_HEAVY",
    "RV_BASE_MISSING",
}
_MEDIUM_PRIORITY_FLAGS = {
    "ENTRY_EN_FOOTNOTE_MARKER",
    "ENTRY_EN_UNBALANCED_BRACKETS",
    "ENTRY_EN_DUPLICATE_EXACT",
    "ENTRY_GR_DUPLICATE_EXACT",
    "ENTRY_GR_FOOTNOTE_MARKER",
    "ENTRY_GR_UNBALANCED_BRACKETS",
    "LEMMA_EN_TOO_LONG",
    "LEMMA_GR_TOO_LONG",
    "RV_BASE_FAR",
    "RV_ROW_REVIEW",
}
_PRESENTATION_PREFIX_RE = re.compile(r"^\s*\[\s*\d+(?:\s*[_A-Z]+)?")
_RV_INLINE_RE = re.compile(r"\[\s*\d+\s*\]?\s*RV\s*:", flags=re.IGNORECASE)
_TRAILING_FOOTNOTE_RE = re.compile(r"\]\d+\s+%%")
_DIGITS_RE = re.compile(r"^\d+$")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _read_csv_rows(path: Path) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise SystemExit(f"CSV has no header: {path}")

        rows: list[tuple[int, dict[str, str]]] = []
        for line_no, row in enumerate(reader, start=2):
            rows.append((line_no, dict(row)))
    return fieldnames, rows


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _build_ref(row: dict[str, str], *, row_index_1_based: int) -> str:
    parts = [
        _clean(row.get("book_no")),
        _clean(row.get("chapter_no")),
        _clean(row.get("section_no")),
        _clean(row.get("subsection_no")),
    ]
    parts = [p for p in parts if p]
    if not parts:
        return f"row{row_index_1_based}"
    return ".".join(parts)


def _chapter_base(chapter_no: str) -> tuple[str, int | None, bool]:
    cleaned = _clean(chapter_no)
    is_rv = cleaned.endswith("_RV")
    base = cleaned[:-3] if is_rv else cleaned
    return base, int(base) if base.isdigit() else None, is_rv


def _script_counts(text: str) -> tuple[int, int]:
    greek = 0
    latin = 0
    for ch in text:
        cp = ord(ch)
        if 0x0370 <= cp <= 0x03FF or 0x1F00 <= cp <= 0x1FFF:
            greek += 1
        elif ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            latin += 1
    return greek, latin


def _is_latin_heavy(text: str, *, min_latin: int) -> bool:
    greek, latin = _script_counts(text)
    return latin >= min_latin and latin > (greek * 2)


def _is_greek_heavy(text: str, *, min_greek: int = 4) -> bool:
    greek, latin = _script_counts(text)
    return greek >= min_greek and greek > (latin * 2)


def _word_count(text: str) -> int:
    return len([part for part in _normalize_text(text).split(" ") if part])


def _is_unbalanced_brackets(text: str) -> bool:
    return text.count("[") != text.count("]")


def _has_footnote_marker(text: str) -> bool:
    return "%%" in text or bool(_TRAILING_FOOTNOTE_RE.search(text))


def _has_presentation_prefix(text: str) -> bool:
    return bool(_PRESENTATION_PREFIX_RE.match(text))


def _row_hash(row: dict[str, str], source_columns: list[str]) -> str:
    payload = {column: row.get(column, "") for column in source_columns}
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _priority_for_flags(flags: set[str]) -> str:
    if not flags:
        return "none"
    if flags & _HIGH_PRIORITY_FLAGS:
        return "high"
    if flags & _MEDIUM_PRIORITY_FLAGS:
        return "medium"
    return "low"


def _load_existing_review(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows: dict[str, dict[str, str]] = {}
        for row in reader:
            line_no = _clean(row.get("source_line_no"))
            if not line_no:
                continue
            rows[line_no] = {field: row.get(field, "") for field in _REVIEW_EDITABLE_FIELDS}
        return rows


def _preview(text: str, *, limit: int = 90) -> str:
    normalized = _normalize_text(text)
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit data-workbench/diosc.build.csv for review.")
    ap.add_argument(
        "--in-csv",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "diosc.build.csv"),
        help="Input Dioscorides build CSV.",
    )
    ap.add_argument(
        "--out-md",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "diosc_build_audit.md"),
        help="Markdown audit summary output path.",
    )
    ap.add_argument(
        "--out-review-csv",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "diosc_build_review.csv"),
        help="Review spreadsheet output path.",
    )
    args = ap.parse_args()

    in_path = Path(args.in_csv)
    out_md_path = Path(args.out_md)
    out_review_path = Path(args.out_review_csv)

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")

    source_columns, rows_with_lines = _read_csv_rows(in_path)
    if not rows_with_lines:
        raise SystemExit(f"Input CSV contains no data rows: {in_path}")

    existing_review = _load_existing_review(out_review_path)

    rows = [row for _line_no, row in rows_with_lines]
    line_nos = [line_no for line_no, _row in rows_with_lines]
    refs = [_build_ref(row, row_index_1_based=line_no) for line_no, row in rows_with_lines]

    structural_key_counts: Counter[tuple[str, str, str, str]] = Counter()
    book_chapter_counts: Counter[tuple[str, str]] = Counter()
    entry_gr_counts: Counter[str] = Counter()
    entry_en_counts: Counter[str] = Counter()
    book_chapter_lines: dict[tuple[str, str], int] = {}

    for line_no, row in rows_with_lines:
        structural_key = (
            _clean(row.get("book_no")),
            _clean(row.get("chapter_no")),
            _clean(row.get("section_no")),
            _clean(row.get("subsection_no")),
        )
        structural_key_counts[structural_key] += 1
        book_chapter_key = (_clean(row.get("book_no")), _clean(row.get("chapter_no")))
        book_chapter_counts[book_chapter_key] += 1
        book_chapter_lines[book_chapter_key] = line_no

        entry_gr = _normalize_text(_clean(row.get("entry_gr")))
        entry_en = _normalize_text(_clean(row.get("entry_en")))
        if entry_gr:
            entry_gr_counts[entry_gr] += 1
        if entry_en:
            entry_en_counts[entry_en] += 1

    priority_counts: Counter[str] = Counter()
    issue_counts: Counter[str] = Counter()
    review_rows: list[dict[str, str]] = []
    flagged_rows: list[tuple[str, int, str, list[str], str, str]] = []

    previous_book_int: int | None = None
    previous_chapter_base_int: int | None = None

    for idx, (line_no, row) in enumerate(rows_with_lines):
        book_no = _clean(row.get("book_no"))
        chapter_no = _clean(row.get("chapter_no"))
        ref = refs[idx]
        previous_ref = refs[idx - 1] if idx > 0 else ""
        next_ref = refs[idx + 1] if idx + 1 < len(refs) else ""
        base_chapter, base_chapter_int, is_rv = _chapter_base(chapter_no)
        book_int = int(book_no) if book_no.isdigit() else None

        flags: set[str] = set()
        structural_key = (
            book_no,
            chapter_no,
            _clean(row.get("section_no")),
            _clean(row.get("subsection_no")),
        )
        book_chapter_key = (book_no, chapter_no)

        if structural_key_counts[structural_key] > 1:
            flags.add("DUPLICATE_STRUCTURAL_KEY")
        if book_chapter_counts[book_chapter_key] > 1:
            flags.add("DUPLICATE_BOOK_CHAPTER")

        for column in _TEXT_COLUMNS:
            value = _clean(row.get(column))
            if not value:
                flags.add(f"{column.upper()}_BLANK")

        lemma_gr = _clean(row.get("lemma_gr"))
        entry_gr = _clean(row.get("entry_gr"))
        lemma_en = _clean(row.get("lemma_en"))
        entry_en = _clean(row.get("entry_en"))

        if _is_latin_heavy(lemma_gr, min_latin=5):
            flags.add("LEMMA_GR_LATIN_HEAVY")
        if _is_latin_heavy(entry_gr, min_latin=15):
            flags.add("ENTRY_GR_LATIN_HEAVY")
        if _is_greek_heavy(lemma_en):
            flags.add("LEMMA_EN_GREEK_HEAVY")
        if _is_greek_heavy(entry_en, min_greek=10):
            flags.add("ENTRY_EN_GREEK_HEAVY")

        if _word_count(lemma_gr) > 8 or len(lemma_gr) > 80:
            flags.add("LEMMA_GR_TOO_LONG")
        if _word_count(lemma_en) > 8 or len(lemma_en) > 80:
            flags.add("LEMMA_EN_TOO_LONG")

        if _has_presentation_prefix(entry_gr):
            flags.add("ENTRY_GR_PRESENTATION_PREFIX")
        if _has_footnote_marker(entry_gr):
            flags.add("ENTRY_GR_FOOTNOTE_MARKER")
        if _has_footnote_marker(entry_en):
            flags.add("ENTRY_EN_FOOTNOTE_MARKER")
        if _is_unbalanced_brackets(entry_gr):
            flags.add("ENTRY_GR_UNBALANCED_BRACKETS")
        if _is_unbalanced_brackets(entry_en):
            flags.add("ENTRY_EN_UNBALANCED_BRACKETS")
        if _RV_INLINE_RE.search(entry_gr) and not is_rv:
            flags.add("ENTRY_GR_HOST_RV_PAYLOAD")

        normalized_entry_gr = _normalize_text(entry_gr)
        normalized_entry_en = _normalize_text(entry_en)
        if normalized_entry_gr and entry_gr_counts[normalized_entry_gr] > 1:
            flags.add("ENTRY_GR_DUPLICATE_EXACT")
        if normalized_entry_en and entry_en_counts[normalized_entry_en] > 1:
            flags.add("ENTRY_EN_DUPLICATE_EXACT")

        if is_rv:
            flags.add("RV_ROW_REVIEW")
            base_key = (book_no, base_chapter)
            if base_key not in book_chapter_lines:
                flags.add("RV_BASE_MISSING")
            else:
                base_distance = abs(book_chapter_lines[base_key] - line_no)
                if base_distance > 3:
                    flags.add("RV_BASE_FAR")

        if chapter_no and not is_rv and not _DIGITS_RE.match(chapter_no):
            flags.add("CHAPTER_NON_NUMERIC_UNEXPECTED")

        if book_int is not None:
            if previous_book_int is not None and book_int < previous_book_int:
                flags.add("BOOK_ORDER_DECREASE")
            if previous_book_int != book_int:
                previous_chapter_base_int = None
            previous_book_int = book_int

        if base_chapter_int is not None:
            if previous_chapter_base_int is not None and base_chapter_int < previous_chapter_base_int:
                flags.add("CHAPTER_ORDER_DECREASE")
            previous_chapter_base_int = base_chapter_int

        priority = _priority_for_flags(flags)
        priority_counts[priority] += 1
        for flag in flags:
            issue_counts[flag] += 1

        previous_values = existing_review.get(str(line_no), {})
        review_row: dict[str, str] = {
            "source_line_no": str(line_no),
            "ref": ref,
            "previous_ref": previous_ref,
            "next_ref": next_ref,
            "priority": priority,
            "audit_flags": "|".join(sorted(flags)),
            "review_status": previous_values.get("review_status", "todo"),
            "decision": previous_values.get("decision", ""),
            "notes": previous_values.get("notes", ""),
        }
        for column in source_columns:
            review_row[column] = row.get(column, "")
        review_row["original_row_hash"] = _row_hash(row, source_columns)
        for field in _CORRECTED_FIELDS:
            review_row[field] = previous_values.get(field, "")
        review_rows.append(review_row)

        if flags:
            flagged_rows.append(
                (
                    priority,
                    line_no,
                    ref,
                    sorted(flags),
                    _preview(lemma_en or lemma_gr, limit=50),
                    _preview(entry_en or entry_gr, limit=120),
                )
            )

    review_fieldnames = (
        _REVIEW_METADATA_FIELDS
        + source_columns
        + ["original_row_hash"]
        + _CORRECTED_FIELDS
    )
    out_review_path.parent.mkdir(parents=True, exist_ok=True)
    with out_review_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=review_fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(review_rows)

    utc_now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    md_lines: list[str] = []
    md_lines.append("# Dioscorides Build Audit")
    md_lines.append("")
    md_lines.append(f"- Generated: `{utc_now}`")
    md_lines.append(f"- Input: `{in_path}`")
    md_lines.append(f"- Review CSV: `{out_review_path}`")
    md_lines.append(f"- Total rows: **{len(review_rows)}**")
    md_lines.append(
        "- Current assessment: "
        + (
            "manual review still required before treating `diosc.build.csv` as fully trusted."
            if flagged_rows
            else "no automated anomalies detected in the current build file."
        )
    )
    md_lines.append("")
    md_lines.append("## Summary")
    md_lines.append(f"- High-priority rows: **{priority_counts['high']}**")
    md_lines.append(f"- Medium-priority rows: **{priority_counts['medium']}**")
    md_lines.append(f"- Low-priority rows: **{priority_counts['low']}**")
    md_lines.append(f"- Rows with no automated flags: **{priority_counts['none']}**")
    md_lines.append(f"- `_RV` rows flagged for split review: **{issue_counts['RV_ROW_REVIEW']}**")
    md_lines.append("")
    md_lines.append("## Issue Counts")
    if issue_counts:
        for flag, count in sorted(issue_counts.items()):
            md_lines.append(f"- `{flag}`: {count}")
    else:
        md_lines.append("- _(none)_")

    grouped_rows: dict[str, list[tuple[int, str, list[str], str, str]]] = {
        "high": [],
        "medium": [],
        "low": [],
    }
    for priority, line_no, ref, flags, lemma_preview, entry_preview in flagged_rows:
        if priority in grouped_rows:
            grouped_rows[priority].append((line_no, ref, flags, lemma_preview, entry_preview))

    for priority in ["high", "medium", "low"]:
        md_lines.append("")
        md_lines.append(f"## {priority.capitalize()} Priority Rows")
        if not grouped_rows[priority]:
            md_lines.append("- _(none)_")
            continue
        for line_no, ref, flags, lemma_preview, entry_preview in grouped_rows[priority]:
            md_lines.append(
                f"- line {line_no} `{ref}` flags=`{'|'.join(flags)}` "
                f"lemma=`{lemma_preview}` entry=`{entry_preview}`"
            )

    md_lines.append("")
    md_lines.append("## Review Workflow")
    md_lines.append("- Use `data-workbench/diosc_build_review.csv` as the working review sheet.")
    md_lines.append("- Route row fixes back into `diosc_missing_text_patch.csv` or `diosc_text_fixes_patch.csv`, then regenerate `diosc.build.csv`.")
    md_lines.append("- Re-run this audit after every patch batch and keep the review sheet in sync.")
    md_lines.append("")

    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.write_text("\n".join(md_lines), encoding="utf-8", newline="\n")

    print(f"Wrote {out_md_path}")
    print(f"Wrote {out_review_path}")
    print(
        "Flagged rows: "
        f"high={priority_counts['high']} medium={priority_counts['medium']} "
        f"low={priority_counts['low']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
