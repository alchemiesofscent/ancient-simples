#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import re
import sys


_THIS_REPO_ROOT = Path(__file__).resolve().parents[1]

from textutils.normalize import normalize as normalize_greek


OUTPUT_COLUMNS = [
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

_DIGITS_RE = re.compile(r"^\d+$")


def _to_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _single_line_text(text: str, *, newline: str = "\\n") -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\n" not in text:
        return text
    parts = [p.strip() for p in text.split("\n")]
    parts = [p for p in parts if p]
    return newline.join(parts)


def _word_count_simple(text: str) -> int:
    return len([t for t in text.strip().split() if t])


def _build_ref(row: dict[str, str], *, row_index_1_based: int) -> str:
    parts = [
        _to_str(row.get("book_no")),
        _to_str(row.get("chapter_no")),
        _to_str(row.get("section_no")),
        _to_str(row.get("subsection_no")),
    ]
    parts = [p for p in parts if p]
    if not parts:
        return f"row{row_index_1_based}"
    return ".".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build data-workbench/entries_diosc.csv from diosc CSV.")
    ap.add_argument(
        "--in-csv",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "diosc.build.csv"),
        help="Input diosc CSV path (default: data-workbench/diosc.build.csv).",
    )
    ap.add_argument(
        "--out-csv",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "entries_diosc.csv"),
        help="Output entries_diosc.csv path.",
    )
    ap.add_argument(
        "--qc-md",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "entries_diosc_qc.md"),
        help="Output QC markdown report path.",
    )
    ap.add_argument(
        "--source",
        default="DIOSC_DMM",
        help="Source code to use in output entry_id/source columns.",
    )
    args = ap.parse_args()

    in_path = Path(args.in_csv)
    out_path = Path(args.out_csv)
    qc_path = Path(args.qc_md)
    source = args.source.strip()

    if not source:
        raise SystemExit("--source must be non-empty")
    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")

    rows_out: list[dict[str, str]] = []
    seen_entry_id: Counter[str] = Counter()
    seen_ref: Counter[str] = Counter()
    dedup_occurrences: defaultdict[str, list[str]] = defaultdict(list)
    missing_translation_ids: list[str] = []
    chapter_non_numeric: list[tuple[int, str, str]] = []

    with in_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            ref = _build_ref(row, row_index_1_based=line_no)
            seen_ref[ref] += 1

            chapter_no = _to_str(row.get("chapter_no"))
            if chapter_no and not _DIGITS_RE.match(chapter_no):
                chapter_non_numeric.append((line_no, chapter_no, ref))

            base_entry_id = f"{source}-{ref}"
            seen_entry_id[base_entry_id] += 1
            dedupe_idx = seen_entry_id[base_entry_id]
            entry_id = base_entry_id if dedupe_idx == 1 else f"{base_entry_id}~{dedupe_idx}"
            if dedupe_idx > 1:
                dedup_occurrences[base_entry_id].append(entry_id)

            greek = _single_line_text(_to_str(row.get("entry_gr")))
            translation = _single_line_text(_to_str(row.get("entry_en")))
            greek_normalized = normalize_greek(greek)

            notes_parts = [f"diosc_row={line_no}"]
            if dedupe_idx > 1:
                notes_parts.append(f"dedup_from={ref}")

            rows_out.append(
                {
                    "entry_id": entry_id,
                    "source": source,
                    "ref": ref,
                    "chapter_title_gr": _to_str(row.get("chapter_gr")) or _to_str(row.get("section_gr")),
                    "chapter_title_en": "",
                    "lemma_ids": "",
                    "part_id": "",
                    "greek": greek,
                    "greek_normalized": greek_normalized,
                    "translation": translation,
                    "trans_status": "draft",
                    "e_vol": _to_str(row.get("e_vol")),
                    "e_page_start": _to_str(row.get("e_p_start")),
                    "e_page_end": _to_str(row.get("e_p_end")),
                    "word_count": str(_word_count_simple(greek)),
                    "notes": "; ".join(notes_parts),
                }
            )

            if not translation:
                missing_translation_ids.append(entry_id)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows_out)

    utc_now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    qc_lines: list[str] = []
    qc_lines.append("# entries_diosc.csv QC report")
    qc_lines.append("")
    qc_lines.append(f"- Generated: `{utc_now}`")
    qc_lines.append(f"- Input: `{in_path}`")
    qc_lines.append(f"- Output: `{out_path}`")
    qc_lines.append(f"- Total rows: **{len(rows_out)}**")
    qc_lines.append("")
    qc_lines.append("## Duplicate structural refs")
    duplicate_refs = {ref: n for ref, n in seen_ref.items() if n > 1}
    if duplicate_refs:
        for ref, n in sorted(duplicate_refs.items()):
            qc_lines.append(f"- `{ref}` occurs {n} times")
    else:
        qc_lines.append("- _(none)_")
    qc_lines.append("")
    qc_lines.append("## Duplicate entry_id base deduping")
    if dedup_occurrences:
        for base_id, resolved in sorted(dedup_occurrences.items()):
            qc_lines.append(f"- `{base_id}` -> {', '.join(f'`{x}`' for x in resolved)}")
    else:
        qc_lines.append("- _(none)_")
    qc_lines.append("")
    qc_lines.append("## Non-numeric chapter_no values")
    if chapter_non_numeric:
        for line_no, chapter, ref in chapter_non_numeric:
            qc_lines.append(f"- line {line_no}: chapter_no=`{chapter}` ref=`{ref}`")
    else:
        qc_lines.append("- _(none)_")
    qc_lines.append("")
    qc_lines.append("## Missing translations")
    if missing_translation_ids:
        qc_lines.append(f"- Count: {len(missing_translation_ids)}")
        for eid in missing_translation_ids[:20]:
            qc_lines.append(f"- `{eid}`")
    else:
        qc_lines.append("- Count: 0")
    qc_lines.append("")
    qc_lines.append("## Sample rows (first 10)")
    for row in rows_out[:10]:
        qc_lines.append(f"- `{row['entry_id']}` ref={row['ref']} words={row['word_count']}")
    qc_lines.append("")

    qc_path.parent.mkdir(parents=True, exist_ok=True)
    qc_path.write_text("\n".join(qc_lines), encoding="utf-8", newline="\n")

    print(f"Wrote {out_path} ({len(rows_out)} rows)")
    print(f"Wrote {qc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
