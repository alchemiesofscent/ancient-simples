#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


_THIS_REPO_ROOT = Path(__file__).resolve().parents[1]
_PACKAGES_PATH = _THIS_REPO_ROOT / "packages"
if str(_PACKAGES_PATH) not in sys.path:
    sys.path.insert(0, str(_PACKAGES_PATH))

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

_PAGE_RE = re.compile(r"^(?P<vol>\d+)\.(?P<start>\d+)(?:-(?P<end>\d+))?$")


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
    return newline.join(p for p in parts if p)


def _word_count_simple(text: str) -> int:
    return len([t for t in text.strip().split() if t])


def parse_edition_pages(value: str) -> tuple[str, str, str]:
    value = _to_str(value)
    match = _PAGE_RE.match(value)
    if not match:
        return "", "", ""
    vol = match.group("vol")
    start = match.group("start")
    end = match.group("end") or start
    return vol, start, end


def build_rows(raw_rows: list[dict[str, str]], *, source: str) -> list[dict[str, str]]:
    rows_out: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for csv_line, row in enumerate(raw_rows, start=2):
        row_idx_raw = _to_str(row.get("row_idx"))
        if not row_idx_raw.isdigit():
            raise ValueError(f"line {csv_line}: row_idx must be numeric, got {row_idx_raw!r}")

        row_idx = int(row_idx_raw)
        book = _to_str(row.get("book")) or "7"
        chapter = _to_str(row.get("chapter")) or "3"
        ref = f"{book}.{chapter}.{row_idx + 1}"
        entry_id = f"{source}-{ref}"
        if entry_id in seen_ids:
            raise ValueError(f"line {csv_line}: duplicate generated entry_id {entry_id!r}")
        seen_ids.add(entry_id)

        greek = _single_line_text(_to_str(row.get("entry_gr")))
        if not greek:
            raise ValueError(f"line {csv_line}: entry_gr must be non-empty")

        e_vol, e_page_start, e_page_end = parse_edition_pages(_to_str(row.get("edition_pages")))
        notes_parts = [
            f"paul_row={row_idx_raw}",
            f"lemma_gr={_to_str(row.get('lemma_gr'))}",
            f"edition_pages={_to_str(row.get('edition_pages'))}",
        ]
        derived_from = _to_str(row.get("derived_from"))
        if derived_from:
            notes_parts.append(f"derived_from={derived_from}")

        rows_out.append(
            {
                "entry_id": entry_id,
                "source": source,
                "ref": ref,
                "chapter_title_gr": _to_str(row.get("section_gr")) or _to_str(row.get("lemma_gr")),
                "chapter_title_en": "",
                "lemma_ids": "",
                "part_id": "",
                "greek": greek,
                "greek_normalized": normalize_greek(greek),
                "translation": _single_line_text(_to_str(row.get("entry_en"))),
                "trans_status": "draft",
                "e_vol": e_vol,
                "e_page_start": e_page_start,
                "e_page_end": e_page_end,
                "word_count": str(_word_count_simple(greek)),
                "notes": "; ".join(notes_parts),
            }
        )

    return rows_out


def main() -> int:
    ap = argparse.ArgumentParser(description="Build data-workbench/entries_paul.csv from Paul Book 7.3 CSV.")
    ap.add_argument(
        "--in-csv",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "paul.csv"),
        help="Input Paul CSV path.",
    )
    ap.add_argument(
        "--out-csv",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "entries_paul.csv"),
        help="Output entries_paul.csv path.",
    )
    ap.add_argument(
        "--qc-md",
        default=str(_THIS_REPO_ROOT / "data-workbench" / "entries_paul_qc.md"),
        help="Output QC markdown report path.",
    )
    ap.add_argument("--source", default="PAUL_AEG", help="Source code for generated rows.")
    args = ap.parse_args()

    in_path = Path(args.in_csv)
    out_path = Path(args.out_csv)
    qc_path = Path(args.qc_md)
    source = args.source.strip()

    if not source:
        raise SystemExit("--source must be non-empty")
    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")

    with in_path.open("r", encoding="utf-8-sig", newline="") as f:
        raw_rows = [dict(row) for row in csv.DictReader(f)]
    rows_out = build_rows(raw_rows, source=source)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows_out)

    page_spans = [
        row["notes"].split("edition_pages=", 1)[1].split(";", 1)[0]
        for row in rows_out
        if "edition_pages=" in row["notes"]
    ]
    utc_now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    qc_lines = [
        "# entries_paul.csv QC report",
        "",
        f"- Generated: `{utc_now}`",
        f"- Input: `{in_path}`",
        f"- Output: `{out_path}`",
        f"- Total rows: **{len(rows_out)}**",
        f"- First entry: `{rows_out[0]['entry_id'] if rows_out else ''}`",
        f"- Last entry: `{rows_out[-1]['entry_id'] if rows_out else ''}`",
        f"- Multi-page source rows: {sum('-' in p for p in page_spans)}",
        "",
        "## Sample rows (first 10)",
    ]
    for row in rows_out[:10]:
        qc_lines.append(
            f"- `{row['entry_id']}` ref={row['ref']} pages={row['e_vol']}.{row['e_page_start']}-{row['e_page_end']} words={row['word_count']}"
        )
    qc_lines.append("")
    qc_path.parent.mkdir(parents=True, exist_ok=True)
    qc_path.write_text("\n".join(qc_lines), encoding="utf-8", newline="\n")

    print(f"Wrote {out_path} ({len(rows_out)} rows)")
    print(f"Wrote {qc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
