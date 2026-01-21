#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
import unicodedata
from pathlib import Path
from typing import Any

from supabase_rest import SupabaseRestClient, env_required


def normalize_greek_for_match(text: str) -> str:
    lowered = (text or "").lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch) or ch == "\u0345")
    return unicodedata.normalize("NFC", stripped)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]


def chunked(items: list[dict[str, Any]], n: int) -> list[list[dict[str, Any]]]:
    return [items[i : i + n] for i in range(0, len(items), n)]


def to_int_or_none(v: str) -> int | None:
    s = (v or "").strip()
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Import data-workbench CSVs into Supabase (hosted).")
    parser.add_argument(
        "--workbench",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data-workbench",
        help="Path to data-workbench directory",
    )
    parser.add_argument("--batch-parts", type=int, default=500)
    parser.add_argument("--batch-lemmata", type=int, default=500)
    parser.add_argument("--batch-entries", type=int, default=10)
    parser.add_argument("--batch-links", type=int, default=2000)
    args = parser.parse_args()

    supabase_url = env_required("SUPABASE_URL")
    service_key = env_required("SUPABASE_SERVICE_ROLE_KEY")
    client = SupabaseRestClient(supabase_url=supabase_url, api_key=service_key)

    wb = args.workbench
    parts_path = wb / "parts.csv"
    preps_path = wb / "preparations.csv"
    lemmata_path = wb / "lemmata.csv"
    entries_path = wb / "entries.csv"
    entry_preps_path = wb / "entry_preparations.csv"

    missing = [p for p in [parts_path, preps_path, lemmata_path, entries_path, entry_preps_path] if not p.exists()]
    if missing:
        print("ERROR: missing required CSV files:", file=sys.stderr)
        for p in missing:
            print(f"- {p}", file=sys.stderr)
        return 2

    parts = read_csv(parts_path)
    preps = read_csv(preps_path)
    lemmata = read_csv(lemmata_path)
    entries = read_csv(entries_path)
    entry_preps = read_csv(entry_preps_path)

    print(f"Importing parts: {len(parts)}")
    for batch in chunked(
        [
            {
                "part_id": r["part_id"],
                "greek": r.get("greek", "") or "",
                "english": r.get("english", "") or "",
                "category": r.get("category", "") or "",
                "notes": r.get("notes", "") or "",
            }
            for r in parts
        ],
        args.batch_parts,
    ):
        client.upsert("parts", batch, on_conflict="part_id")

    print(f"Importing preparations: {len(preps)}")
    for batch in chunked(
        [
            {
                "prep_id": r["prep_id"],
                "greek": r.get("greek", "") or "",
                "english": r.get("english", "") or "",
                "scope": r.get("scope", "") or "",
                "notes": r.get("notes", "") or "",
            }
            for r in preps
        ],
        args.batch_parts,
    ):
        client.upsert("preparations", batch, on_conflict="prep_id")

    # Lemmata has a self-referential FK (parent_lemma -> lemma_id). Import in two passes:
    # 1) Upsert all rows with parent_lemma=NULL to satisfy FK ordering.
    # 2) Upsert again with the real parent_lemma values restored.
    print(f"Lemmata pass 1 (no parent_lemma): {len(lemmata)}")
    for batch in chunked(
        [
            {
                "lemma_id": r["lemma_id"],
                "headword_gr": r.get("headword_gr", "") or "",
                "headword_normalized": normalize_greek_for_match(r.get("headword_gr", "") or ""),
                "headword_en": r.get("headword_en", "") or "",
                "parent_lemma": None,
                "relationship": r.get("relationship", "") or "",
                "category": r.get("category", "") or "",
                "notes": r.get("notes", "") or "",
            }
            for r in lemmata
        ],
        args.batch_lemmata,
    ):
        client.upsert("lemmata", batch, on_conflict="lemma_id")

    print(f"Lemmata pass 2 (with parent_lemma): {len(lemmata)}")
    for batch in chunked(
        [
            {
                "lemma_id": r["lemma_id"],
                "headword_gr": r.get("headword_gr", "") or "",
                "headword_normalized": normalize_greek_for_match(r.get("headword_gr", "") or ""),
                "headword_en": r.get("headword_en", "") or "",
                "parent_lemma": (r.get("parent_lemma", "") or "").strip() or None,
                "relationship": r.get("relationship", "") or "",
                "category": r.get("category", "") or "",
                "notes": r.get("notes", "") or "",
            }
            for r in lemmata
        ],
        args.batch_lemmata,
    ):
        client.upsert("lemmata", batch, on_conflict="lemma_id")

    print(f"Importing entries: {len(entries)}")
    entry_rows: list[dict[str, Any]] = []
    ref_rows: list[dict[str, Any]] = []

    editions = client.get_json("/rest/v1/editions", query={"code": "eq.KUHN", "select": "edition_id"})
    if not editions:
        print("ERROR: missing editions row with code=KUHN (migration should have seeded it).", file=sys.stderr)
        return 2
    edition_id = editions[0]["edition_id"]

    for r in entries:
        greek = r.get("greek", "") or ""
        greek_normalized = normalize_greek_for_match(greek)
        translation = (r.get("translation", "") or "").replace("\\n", "\n")
        entry_rows.append(
            {
                "entry_id": r["entry_id"],
                "source": r.get("source", "") or "",
                "ref": r.get("ref", "") or "",
                "chapter_title_gr": r.get("chapter_title_gr", "") or "",
                "chapter_title_en": r.get("chapter_title_en", "") or "",
                "part_id": (r.get("part_id", "") or "") or None,
                "greek": greek,
                "greek_normalized": greek_normalized,
                "translation": translation,
                "trans_status": r.get("trans_status", "") or "draft",
                "word_count": to_int_or_none(r.get("word_count", "")),
                "notes": r.get("notes", "") or "",
            }
        )

        vol = (r.get("e_vol", "") or "").strip()
        p_start = to_int_or_none(r.get("e_page_start", ""))
        p_end = to_int_or_none(r.get("e_page_end", ""))
        if vol or p_start is not None or p_end is not None:
            ref_rows.append(
                {
                    "entry_id": r["entry_id"],
                    "edition_id": edition_id,
                    "ref_type": "kuhn_page",
                    "volume": vol,
                    "page_start": p_start,
                    "page_end": p_end,
                    "notes": "",
                }
            )

    for batch in chunked(entry_rows, args.batch_entries):
        client.upsert("entries", batch, on_conflict="entry_id")

    print(f"Importing entry_references (KUHN): {len(ref_rows)}")
    for batch in chunked(ref_rows, args.batch_links):
        client.upsert("entry_references", batch, on_conflict="entry_id,edition_id,ref_type")

    # Explode lemma_ids into entry_lemmata
    link_rows: list[dict[str, Any]] = []
    for r in entries:
        lemma_ids = (r.get("lemma_ids", "") or "").strip()
        if not lemma_ids:
            continue
        ids = [x.strip() for x in lemma_ids.split(",") if x.strip()]
        for idx, lemma_id in enumerate(ids):
            link_rows.append(
                {
                    "entry_id": r["entry_id"],
                    "lemma_id": lemma_id,
                    "is_primary": idx == 0,
                }
            )

    print(f"Importing entry_lemmata: {len(link_rows)}")
    for batch in chunked(link_rows, args.batch_links):
        client.upsert("entry_lemmata", batch, on_conflict="entry_id,lemma_id")

    # Import entry_preparations.csv (already exploded)
    prep_link_rows: list[dict[str, Any]] = []
    for r in entry_preps:
        prep_link_rows.append(
            {
                "entry_id": r["entry_id"],
                "prep_id": r["prep_id"],
                "is_primary": (r.get("is_primary", "") or "").strip().lower() == "true",
                "notes": r.get("notes", "") or "",
            }
        )

    print(f"Importing entry_preparations: {len(prep_link_rows)}")
    for batch in chunked(prep_link_rows, args.batch_links):
        client.upsert("entry_preparations", batch, on_conflict="entry_id,prep_id")

    print("Remote row counts (post-import):")
    for table in [
        "parts",
        "preparations",
        "lemmata",
        "entries",
        "entry_lemmata",
        "entry_preparations",
        "entry_references",
    ]:
        try:
            print(f"- {table}: {client.count(table)}")
        except Exception as e:
            print(f"- {table}: (count failed: {e})")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
