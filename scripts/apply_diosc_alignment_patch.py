#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


VALID_ACTIONS = {"KEEP", "REPLACE", "DELETE", "INSERT_AFTER"}


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _row_hash(row: dict[str, str], source_columns: list[str]) -> str:
    payload = {column: row.get(column, "") for column in source_columns}
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_source_rows(path: Path) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        source_columns = list(reader.fieldnames or [])
        if not source_columns:
            raise SystemExit(f"Source CSV has no header columns: {path}")
        rows: list[tuple[int, dict[str, str]]] = []
        for line_no, row in enumerate(reader, start=2):
            rows.append((line_no, dict(row)))
    return source_columns, rows


@dataclass
class ApplyStats:
    keep_rows: int = 0
    replace_rows: int = 0
    delete_rows: int = 0
    insert_rows: int = 0
    errors: int = 0


def _build_revised_row(
    review_row: dict[str, str],
    source_row: dict[str, str] | None,
    source_columns: list[str],
) -> dict[str, str]:
    out: dict[str, str] = {}
    for column in source_columns:
        revised_key = f"revised_{column}"
        revised_value = review_row.get(revised_key, "")
        if revised_value != "":
            out[column] = revised_value
            continue
        if source_row is not None:
            out[column] = source_row.get(column, "")
        else:
            out[column] = ""
    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Apply edited Dioscorides alignment review rows back to CSV")
    ap.add_argument(
        "--in-csv",
        default=str(repo_root / "data-workbench" / "diosc.csv"),
        help="Input source CSV",
    )
    ap.add_argument(
        "--review-csv",
        default=str(repo_root / "data-workbench" / "diosc_alignment_review.csv"),
        help="Edited review CSV from extractor",
    )
    ap.add_argument(
        "--out-csv",
        default=str(repo_root / "data-workbench" / "diosc.patched.csv"),
        help="Output patched CSV (ignored with --in-place)",
    )
    ap.add_argument(
        "--report-md",
        default=str(repo_root / "data-workbench" / "diosc_alignment_apply_report.md"),
        help="Apply report markdown output",
    )
    ap.add_argument(
        "--in-place",
        action="store_true",
        help="Write patched data directly to --in-csv",
    )
    args = ap.parse_args()

    in_path = Path(args.in_csv)
    review_path = Path(args.review_csv)
    out_path = Path(args.out_csv)
    report_path = Path(args.report_md)

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")
    if not review_path.exists():
        raise SystemExit(f"Review CSV not found: {review_path}")

    source_columns, source_rows = _read_source_rows(in_path)
    source_by_line: dict[int, dict[str, str]] = {line_no: row for line_no, row in source_rows}
    min_line = min(source_by_line.keys())
    max_line = max(source_by_line.keys())

    replace_by_line: dict[int, dict[str, str]] = {}
    delete_lines: set[int] = set()
    inserts_after: dict[int, list[dict[str, str]]] = {}
    errors: list[str] = []
    stats = ApplyStats()

    with review_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"source_line_no", "action", "insert_after_line_no", "original_row_hash"}
        missing_required = sorted(required - set(reader.fieldnames or []))
        if missing_required:
            raise SystemExit(f"Review CSV missing required columns: {missing_required}")

        for review_idx, review_row in enumerate(reader, start=2):
            action = _clean(review_row.get("action")).upper() or "KEEP"
            source_line_raw = _clean(review_row.get("source_line_no"))
            insert_after_raw = _clean(review_row.get("insert_after_line_no"))
            review_hash = _clean(review_row.get("original_row_hash"))

            if action not in VALID_ACTIONS:
                errors.append(f"review line {review_idx}: invalid action {action!r}")
                continue

            source_line: int | None = None
            if source_line_raw:
                if not source_line_raw.isdigit():
                    errors.append(
                        f"review line {review_idx}: source_line_no must be integer, got {source_line_raw!r}"
                    )
                    continue
                source_line = int(source_line_raw)
                if source_line not in source_by_line:
                    errors.append(f"review line {review_idx}: source_line_no {source_line} not found")
                    continue

            if action in {"REPLACE", "DELETE"}:
                if source_line is None:
                    errors.append(f"review line {review_idx}: action {action} requires source_line_no")
                    continue
                current_hash = _row_hash(source_by_line[source_line], source_columns)
                if not review_hash:
                    errors.append(f"review line {review_idx}: missing original_row_hash for {action}")
                    continue
                if review_hash != current_hash:
                    errors.append(
                        f"review line {review_idx}: hash mismatch at source_line_no {source_line}"
                    )
                    continue

            if action == "KEEP":
                stats.keep_rows += 1
                continue

            if action == "DELETE":
                if source_line in replace_by_line:
                    errors.append(
                        f"review line {review_idx}: source_line_no {source_line} already set for REPLACE"
                    )
                    continue
                delete_lines.add(source_line)
                stats.delete_rows += 1
                continue

            if action == "REPLACE":
                if source_line in delete_lines:
                    errors.append(
                        f"review line {review_idx}: source_line_no {source_line} already set for DELETE"
                    )
                    continue
                if source_line in replace_by_line:
                    errors.append(
                        f"review line {review_idx}: source_line_no {source_line} already set for REPLACE"
                    )
                    continue
                replace_by_line[source_line] = _build_revised_row(
                    review_row=review_row,
                    source_row=source_by_line[source_line],
                    source_columns=source_columns,
                )
                stats.replace_rows += 1
                continue

            if action == "INSERT_AFTER":
                if not insert_after_raw:
                    errors.append(f"review line {review_idx}: INSERT_AFTER requires insert_after_line_no")
                    continue
                if not insert_after_raw.isdigit():
                    errors.append(
                        f"review line {review_idx}: insert_after_line_no must be integer, got {insert_after_raw!r}"
                    )
                    continue
                insert_after = int(insert_after_raw)
                if insert_after < min_line or insert_after > max_line:
                    errors.append(
                        f"review line {review_idx}: insert_after_line_no {insert_after} out of source range"
                    )
                    continue
                new_row = _build_revised_row(
                    review_row=review_row,
                    source_row=None,
                    source_columns=source_columns,
                )
                if not any(new_row.get(column, "") != "" for column in source_columns):
                    errors.append(
                        f"review line {review_idx}: INSERT_AFTER row is empty; populate revised_* columns"
                    )
                    continue
                inserts_after.setdefault(insert_after, []).append(new_row)
                stats.insert_rows += 1

    if errors:
        stats.errors = len(errors)
        report_lines: list[str] = []
        report_lines.append("# Dioscorides alignment apply report")
        report_lines.append("")
        report_lines.append(f"- Input CSV: `{in_path}`")
        report_lines.append(f"- Review CSV: `{review_path}`")
        report_lines.append(f"- Status: **FAILED**")
        report_lines.append(f"- Error count: **{len(errors)}**")
        report_lines.append("")
        report_lines.append("## Errors")
        for message in errors:
            report_lines.append(f"- {message}")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
        print(f"Wrote {report_path}")
        print(f"Apply failed with {len(errors)} error(s).")
        return 2

    patched_rows: list[dict[str, str]] = []
    for line_no, source_row in source_rows:
        if line_no in delete_lines:
            continue
        if line_no in replace_by_line:
            patched_rows.append(replace_by_line[line_no])
        else:
            patched_rows.append(source_row)
        if line_no in inserts_after:
            patched_rows.extend(inserts_after[line_no])

    target_path = in_path if args.in_place else out_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=source_columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(patched_rows)

    report_lines = []
    report_lines.append("# Dioscorides alignment apply report")
    report_lines.append("")
    report_lines.append(f"- Input CSV: `{in_path}`")
    report_lines.append(f"- Review CSV: `{review_path}`")
    report_lines.append(f"- Output CSV: `{target_path}`")
    report_lines.append(f"- Status: **OK**")
    report_lines.append("")
    report_lines.append("## Actions applied")
    report_lines.append(f"- KEEP rows seen: {stats.keep_rows}")
    report_lines.append(f"- REPLACE rows applied: {stats.replace_rows}")
    report_lines.append(f"- DELETE rows applied: {stats.delete_rows}")
    report_lines.append(f"- INSERT_AFTER rows applied: {stats.insert_rows}")
    report_lines.append("")
    report_lines.append("## Row counts")
    report_lines.append(f"- Source data rows: {len(source_rows)}")
    report_lines.append(f"- Output data rows: {len(patched_rows)}")
    report_lines.append("")
    if replace_by_line:
        report_lines.append("## Replaced source lines")
        for line_no in sorted(replace_by_line.keys()):
            report_lines.append(f"- {line_no}")
        report_lines.append("")
    if delete_lines:
        report_lines.append("## Deleted source lines")
        for line_no in sorted(delete_lines):
            report_lines.append(f"- {line_no}")
        report_lines.append("")
    if inserts_after:
        report_lines.append("## Insertions by source line")
        for line_no in sorted(inserts_after.keys()):
            report_lines.append(f"- after {line_no}: {len(inserts_after[line_no])} row(s)")
        report_lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Wrote {target_path} ({len(patched_rows)} rows)")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
