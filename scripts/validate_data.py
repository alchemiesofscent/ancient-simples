#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path
import unicodedata


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]


def normalize_greek_for_match(text: str) -> str:
    """Greek normalization v1.1: strip ALL combining marks U+0300-U+036F including iota subscript."""
    lowered = (text or "").lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(ch for ch in decomposed if not (0x0300 <= ord(ch) <= 0x036F))
    return unicodedata.normalize("NFC", stripped)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"

    entries_path = workbench / "entries.csv"
    lemmata_path = workbench / "lemmata.csv"
    parts_path = workbench / "parts.csv"
    preparations_path = workbench / "preparations.csv"
    entry_preps_path = workbench / "entry_preparations.csv"

    missing = [
        p for p in [entries_path, lemmata_path, parts_path, preparations_path, entry_preps_path] if not p.exists()
    ]
    if missing:
        print("Missing required CSV outputs:", file=sys.stderr)
        for p in missing:
            print(f"- {p}", file=sys.stderr)
        return 2

    entries = read_csv(entries_path)
    lemmata = read_csv(lemmata_path)
    parts = read_csv(parts_path)
    preps = read_csv(preparations_path)
    entry_preps = read_csv(entry_preps_path)

    print(f"entries.csv rows: {len(entries)}")
    print(f"lemmata.csv rows: {len(lemmata)}")
    print(f"parts.csv rows: {len(parts)}")
    print(f"preparations.csv rows: {len(preps)}")
    print(f"entry_preparations.csv rows: {len(entry_preps)}")

    # Basic entry_id uniqueness and source distribution
    entry_ids = [e.get("entry_id", "") for e in entries]
    dup_entry_ids = [k for k, v in Counter(entry_ids).items() if k and v > 1]
    if dup_entry_ids:
        print(f"ERROR: duplicate entry_id values: {len(dup_entry_ids)}", file=sys.stderr)
        print("Example:", dup_entry_ids[:10], file=sys.stderr)
        return 2

    source_counts = Counter(e.get("source", "") for e in entries)
    print("entries by source:", dict(source_counts))

    lemma_ids_set = {r.get("lemma_id", "") for r in lemmata if r.get("lemma_id")}
    part_ids_set = {r.get("part_id", "") for r in parts if r.get("part_id")}
    prep_ids_set = {r.get("prep_id", "") for r in preps if r.get("prep_id")}

    bad_trans_status = 0
    bad_part_refs = 0
    bad_lemma_refs = 0
    bad_newlines = 0
    bad_greek_norm = 0
    alpha_diacritic_examples: list[str] = []
    alpha_diacritic_total = 0
    total_with_lemma = 0

    for r in entries:
        trans_status = (r.get("trans_status") or "").strip()
        if trans_status not in {"draft", "review", "final"}:
            bad_trans_status += 1

        part_id = (r.get("part_id") or "").strip()
        if part_id and part_id not in part_ids_set:
            bad_part_refs += 1

        lemma_ids = (r.get("lemma_ids") or "").strip()
        if lemma_ids:
            total_with_lemma += 1
            for lid in [x.strip() for x in lemma_ids.split(",") if x.strip()]:
                if lid not in lemma_ids_set:
                    bad_lemma_refs += 1
                    break

        # Ensure the file uses literal \\n tokens, not physical newlines inside fields.
        # DictReader would not split physical newlines inside a quoted field, but we still
        # check for embedded newline characters as a sanity guard.
        for field in ["chapter_title_gr", "greek", "translation"]:
            if "\n" in (r.get(field) or ""):
                bad_newlines += 1
                break

        if "\\n" in (r.get("translation") or ""):
            bad_newlines += 0

        greek = r.get("greek") or ""
        greek_norm = r.get("greek_normalized") or ""
        expected_norm = normalize_greek_for_match(greek)
        if greek_norm != expected_norm:
            bad_greek_norm += 1
            if bad_greek_norm <= 5:
                print(
                    f"ERROR: greek_normalized mismatch for entry_id={r.get('entry_id','')}: "
                    f"expected {expected_norm!r} got {greek_norm!r}",
                    file=sys.stderr,
                )

        greek_strip = greek.lstrip()
        expected_strip = expected_norm.lstrip()
        if greek_strip and expected_strip.startswith("α") and not greek_strip.startswith("α"):
            alpha_diacritic_total += 1
            if not greek_norm.lstrip().startswith("α") and len(alpha_diacritic_examples) < 5:
                alpha_diacritic_examples.append(r.get("entry_id", ""))

    if bad_trans_status:
        print(f"ERROR: entries with invalid trans_status: {bad_trans_status}", file=sys.stderr)
        return 2
    if bad_part_refs:
        print(f"ERROR: entries with invalid part_id FK refs: {bad_part_refs}", file=sys.stderr)
        return 2
    if bad_lemma_refs:
        print(f"ERROR: entries with invalid lemma_ids refs: {bad_lemma_refs}", file=sys.stderr)
        return 2
    if bad_newlines:
        print(
            f"ERROR: entries contain physical newline characters in a field (expected literal \\\\n tokens): {bad_newlines}",
            file=sys.stderr,
        )
        return 2
    if bad_greek_norm:
        print(f"ERROR: entries with incorrect greek_normalized values: {bad_greek_norm}", file=sys.stderr)
        return 2
    if alpha_diacritic_total == 0:
        print(
            "ERROR: expected at least one entry whose Greek starts with diacritic alpha (e.g., ἀ...) to validate normalization",
            file=sys.stderr,
        )
        return 2
    if alpha_diacritic_examples:
        print(
            f"ERROR: entries where Greek starts with diacritic alpha but greek_normalized does not start with plain α: {alpha_diacritic_examples}",
            file=sys.stderr,
        )
        return 2

    coverage = (total_with_lemma / len(entries) * 100.0) if entries else 0.0
    print(f"lemma_ids coverage: {total_with_lemma}/{len(entries)} ({coverage:.1f}%)")

    bad_entry_preps = 0
    for r in entry_preps:
        if (r.get("prep_id") or "").strip() not in prep_ids_set:
            bad_entry_preps += 1
    if bad_entry_preps:
        print(f"ERROR: entry_preparations.csv has invalid prep_id refs: {bad_entry_preps}", file=sys.stderr)
        return 2

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
