#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_greek_numeral(n: int) -> str:
    ones = {1: "α", 2: "β", 3: "γ", 4: "δ", 5: "ε", 6: "ϛ", 7: "ζ", 8: "η", 9: "θ"}
    tens = {10: "ι", 20: "κ", 30: "λ", 40: "μ", 50: "ν", 60: "ξ", 70: "ο", 80: "π", 90: "ϟ"}
    hundreds = {
        100: "ρ",
        200: "σ",
        300: "τ",
        400: "υ",
        500: "φ",
        600: "χ",
        700: "ψ",
        800: "ω",
        900: "ϡ",
    }
    if n <= 0 or n >= 1000:
        return ""
    out: list[str] = []
    remaining = n
    for place, mapping in ((100, hundreds), (10, tens), (1, ones)):
        digit = remaining // place
        if digit:
            out.append(mapping[digit * place])
            remaining -= digit * place
    return "".join(out) + "´"


@dataclass(frozen=True)
class PatchRow:
    patch_id: str
    book_no: str
    chapter_no: str
    field: str
    op: str
    old: str
    new: str
    expect_count: int
    notes: str


VALID_OPS = {"SET", "REPLACE", "REGEX_REPLACE"}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise SystemExit(f"CSV has no header: {path}")
        rows = [dict(r) for r in reader]
    return fieldnames, rows


def _read_patch(path: Path) -> list[PatchRow]:
    _, rows = _read_csv(path)
    out: list[PatchRow] = []
    required = {
        "patch_id",
        "book_no",
        "chapter_no",
        "field",
        "op",
        "old",
        "new",
        "expect_count",
        "notes",
    }
    # allow missing expect_count/notes cells, but columns must exist
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        cols = set(reader.fieldnames or [])
        missing = sorted(required - cols)
        if missing:
            raise SystemExit(f"Patch CSV missing columns: {missing}")

        for r in reader:
            op = _clean(r.get("op")).upper()
            if op not in VALID_OPS:
                raise SystemExit(f"Invalid op {op!r} in patch_id={r.get('patch_id')!r}")
            expect_raw = _clean(r.get("expect_count"))
            expect = int(expect_raw) if expect_raw else (1 if op in {"REPLACE", "REGEX_REPLACE"} else 0)
            out.append(
                PatchRow(
                    patch_id=_clean(r.get("patch_id")),
                    book_no=_clean(r.get("book_no")),
                    chapter_no=_clean(r.get("chapter_no")),
                    field=_clean(r.get("field")),
                    op=op,
                    old=r.get("old") or "",
                    new=r.get("new") or "",
                    expect_count=expect,
                    notes=_clean(r.get("notes")),
                )
            )
    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Apply targeted Dioscorides text-fix patches.")
    ap.add_argument("--in-csv", default=str(repo_root / "data-workbench" / "diosc.patched.csv"))
    ap.add_argument("--patch-csv", default=str(repo_root / "data-workbench" / "diosc_text_fixes_patch.csv"))
    ap.add_argument("--out-csv", default=str(repo_root / "data-workbench" / "diosc.build.csv"))
    ap.add_argument(
        "--report-md",
        default=str(repo_root / "data-workbench" / "diosc_text_fixes_apply_report.md"),
    )
    args = ap.parse_args()

    in_path = Path(args.in_csv)
    patch_path = Path(args.patch_csv)
    out_path = Path(args.out_csv)
    report_path = Path(args.report_md)

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")
    if not patch_path.exists():
        raise SystemExit(f"Patch CSV not found: {patch_path}")

    columns, rows = _read_csv(in_path)
    patches = _read_patch(patch_path)

    # Build lookup by key (expect unique).
    rows_by_key: dict[tuple[str, str], dict[str, str]] = {}
    dup_keys: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        key = (_clean(r.get("book_no")), _clean(r.get("chapter_no")))
        if key in rows_by_key:
            dup_keys[key] += 1
        else:
            rows_by_key[key] = r
    if dup_keys:
        sample = list(dup_keys.items())[:10]
        raise SystemExit(f"Input has duplicate (book_no,chapter_no) keys; sample: {sample}")

    apply_log: list[str] = []
    errors: list[str] = []

    # Built-in consistency: fill blank chapter_no_gr on *_RV rows.
    rv_filled = 0
    for r in rows:
        ch = _clean(r.get("chapter_no"))
        if not ch.endswith("_RV"):
            continue
        if _clean(r.get("chapter_no_gr")):
            continue
        base = ch.split("_", 1)[0]
        if not base.isdigit():
            continue
        r["chapter_no_gr"] = _to_greek_numeral(int(base))
        rv_filled += 1
    apply_log.append(f"AUTOFILL blank chapter_no_gr on *_RV rows: {rv_filled}")

    for p in patches:
        if not p.patch_id:
            errors.append("Patch row missing patch_id")
            continue
        key = (p.book_no, p.chapter_no)
        if key not in rows_by_key:
            errors.append(f"{p.patch_id}: missing target row for {p.book_no}.{p.chapter_no}")
            continue
        row = rows_by_key[key]
        if p.field not in columns:
            errors.append(f"{p.patch_id}: unknown field {p.field!r}")
            continue

        current = row.get(p.field, "") or ""

        if p.op == "SET":
            row[p.field] = p.new
            apply_log.append(f"{p.patch_id}: SET {p.book_no}.{p.chapter_no}.{p.field}")
            continue

        if p.op == "REPLACE":
            count = current.count(p.old)
            if p.expect_count and count != p.expect_count:
                errors.append(
                    f"{p.patch_id}: expected {p.expect_count} occurrence(s) of old text in {p.book_no}.{p.chapter_no}.{p.field}, found {count}"
                )
                continue
            row[p.field] = current.replace(p.old, p.new)
            apply_log.append(
                f"{p.patch_id}: REPLACE {p.book_no}.{p.chapter_no}.{p.field} ({count} occurrence(s))"
            )
            continue

        if p.op == "REGEX_REPLACE":
            try:
                rx = re.compile(p.old, flags=re.MULTILINE)
            except re.error as e:
                errors.append(f"{p.patch_id}: invalid regex: {e}")
                continue
            new_text, count = rx.subn(p.new, current)
            if p.expect_count and count != p.expect_count:
                errors.append(
                    f"{p.patch_id}: expected {p.expect_count} regex match(es) in {p.book_no}.{p.chapter_no}.{p.field}, found {count}"
                )
                continue
            row[p.field] = new_text
            apply_log.append(
                f"{p.patch_id}: REGEX_REPLACE {p.book_no}.{p.chapter_no}.{p.field} ({count} match(es))"
            )
            continue

        errors.append(f"{p.patch_id}: unsupported op {p.op!r}")

    report_lines: list[str] = []
    report_lines.append("# Dioscorides Text-Fixes Apply Report")
    report_lines.append("")
    report_lines.append(f"- Input CSV: `{in_path}`")
    report_lines.append(f"- Patch CSV: `{patch_path}`")
    report_lines.append(f"- Output CSV: `{out_path}`")
    report_lines.append(f"- Rows: **{len(rows)}**")
    report_lines.append(f"- Patches: **{len(patches)}**")
    report_lines.append(f"- Errors: **{len(errors)}**")
    report_lines.append("")
    report_lines.append("## Operations")
    for line in apply_log:
        report_lines.append(f"- {line}")
    if errors:
        report_lines.append("")
        report_lines.append("## Errors")
        for e in errors:
            report_lines.append(f"- {e}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    if errors:
        raise SystemExit(f"Patch apply failed with {len(errors)} error(s). See {report_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {out_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
