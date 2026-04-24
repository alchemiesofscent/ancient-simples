#!/usr/bin/env python3
"""Import vocab v3 extraction results into TEI-first schema.

Reads results.jsonl + entry_id_bridge.csv -> creates:
- lemma_form candidates (lemma_forms)
- entry <-> lemma form links (entry_lemma_forms)
- quality assertions (assertions)

Conservative merge: never auto-merges across sources.

Usage:
    python scripts/import_vocab_v3.py \
        --results outputs/vocab_entries_v3/entries_full_v3/results.jsonl \
        --bridge config/entry_id_bridge.csv \
        [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))  # for supabase_rest

from textutils import normalize
from supabase_rest import SupabaseRestClient, SupabaseRestError, env_required

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VALID_QUALITY_AXES = {"HOT", "COLD", "DRY", "WET"}
SUBSTANCE_CONFIDENCE_THRESHOLD = 0.75
QUALITY_CONFIDENCE_THRESHOLD = 0.70
BATCH_SIZE = 200
SOURCE_TAG = "v3_import"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_bridge(path: Path) -> dict[str, dict[str, str]]:
    """Load entry_id_bridge.csv -> {old_entry_id: row_dict}."""
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        # Skip comment lines
        lines = [line for line in f if not line.startswith("#")]
    reader = csv.DictReader(lines)
    for row in reader:
        old_id = row["old_entry_id"].strip()
        if old_id:
            rows[old_id] = {
                "tei_doc_id": row["tei_doc_id"].strip(),
                "tei_segment_id": row["tei_segment_id"].strip(),
                "display_entry_id": row["display_entry_id"].strip(),
            }
    return rows


def load_results(path: Path) -> list[dict[str, Any]]:
    """Load results.jsonl -> list of result objects."""
    results: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"WARNING: skipping malformed JSON at line {lineno}: {e}", file=sys.stderr)
                continue
            results.append(obj)
    return results


def chunked(items: list[Any], n: int) -> list[list[Any]]:
    return [items[i : i + n] for i in range(0, len(items), n)]


def make_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

class ImportReport:
    """Tracks import statistics."""

    def __init__(self) -> None:
        self.entries_processed: int = 0
        self.entries_skipped_no_bridge: int = 0
        self.entries_skipped_no_tei: int = 0
        self.lemma_forms_created: int = 0
        self.entry_lemma_forms_linked: int = 0
        self.assertions_created: int = 0
        self.needs_review_count: int = 0
        self.terms_skipped_low_conf: int = 0
        self.terms_skipped_non_substance: int = 0
        self.qualities_skipped_low_conf: int = 0
        self.qualities_skipped_bad_axis: int = 0

    def print_report(self) -> None:
        print("\n=== Vocab v3 Import Report ===")
        print(f"  Entries processed:           {self.entries_processed}")
        print(f"  Entries skipped (no bridge):  {self.entries_skipped_no_bridge}")
        print(f"  Entries skipped (no TEI row): {self.entries_skipped_no_tei}")
        print(f"  Lemma forms created:         {self.lemma_forms_created}")
        print(f"  Entry-lemma links created:   {self.entry_lemma_forms_linked}")
        print(f"  Assertions created:          {self.assertions_created}")
        print(f"  Needs review (cross-source): {self.needs_review_count}")
        print(f"  Terms skipped (low conf):    {self.terms_skipped_low_conf}")
        print(f"  Terms skipped (non-SUBST):   {self.terms_skipped_non_substance}")
        print(f"  Qualities skipped (low conf):{self.qualities_skipped_low_conf}")
        print(f"  Qualities skipped (bad axis):{self.qualities_skipped_bad_axis}")
        print("==============================\n")


def resolve_tei_entry_id(
    client: SupabaseRestClient,
    tei_doc_id: str,
    tei_segment_id: str,
    *,
    cache: dict[str, int | None],
) -> int | None:
    """Look up tei_entries.id by (tei_doc_id, tei_segment_id). Caches results."""
    cache_key = f"{tei_doc_id}|{tei_segment_id}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        rows = client.get_json(
            "/rest/v1/tei_entries",
            query={
                "select": "id",
                "tei_doc_id": f"eq.{tei_doc_id}",
                "tei_segment_id": f"eq.{tei_segment_id}",
                "is_active": "eq.true",
                "limit": "1",
            },
        )
    except SupabaseRestError as e:
        print(f"WARNING: REST lookup failed for {cache_key}: {e}", file=sys.stderr)
        cache[cache_key] = None
        return None

    if rows:
        cache[cache_key] = rows[0]["id"]
    else:
        cache[cache_key] = None
    return cache[cache_key]


def extract_source_from_entry_id(entry_id: str) -> str:
    """Extract the source code prefix from a legacy entry_id (e.g. 'GAL_SMT' from 'GAL_SMT-6.1.1')."""
    if "-" in entry_id:
        return entry_id.rsplit("-", 1)[0]
    return entry_id


def process_results(
    results: list[dict[str, Any]],
    bridge: dict[str, dict[str, str]],
    client: SupabaseRestClient | None,
    dry_run: bool,
    batch_size: int = BATCH_SIZE,
) -> ImportReport:
    """Process all results and produce DB rows (or dry-run report).

    Returns the import report.
    """
    report = ImportReport()
    tei_id_cache: dict[str, int | None] = {}

    # Accumulators for batch upsert
    lemma_form_rows: list[dict[str, Any]] = []
    entry_lemma_form_rows: list[dict[str, Any]] = []
    assertion_rows: list[dict[str, Any]] = []

    # Track form_normalized -> list of (source_code, form_grc, uuid) for cross-source detection
    normalized_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for result in results:
        entry_id: str = result.get("entry_id", "")
        if not entry_id:
            continue

        # --- Bridge lookup ---
        bridge_row = bridge.get(entry_id)
        if not bridge_row:
            report.entries_skipped_no_bridge += 1
            continue

        tei_doc_id = bridge_row["tei_doc_id"]
        tei_segment_id = bridge_row["tei_segment_id"]
        source_code = extract_source_from_entry_id(entry_id)

        # --- TEI entry lookup (skip in dry-run if no client) ---
        tei_entry_id: int | None = None
        if client and not dry_run:
            tei_entry_id = resolve_tei_entry_id(
                client, tei_doc_id, tei_segment_id, cache=tei_id_cache
            )
            if tei_entry_id is None:
                report.entries_skipped_no_tei += 1
                continue
        elif dry_run:
            # In dry-run mode, use a placeholder so we can still count
            tei_entry_id = -1
        else:
            report.entries_skipped_no_tei += 1
            continue

        report.entries_processed += 1

        # --- Process SUBSTANCE terms -> lemma_forms + entry_lemma_forms ---
        terms = result.get("terms", [])
        for term in terms:
            label = (term.get("label", "") or "").upper()
            if label != "SUBSTANCE":
                report.terms_skipped_non_substance += 1
                continue

            confidence = term.get("confidence", 0)
            if confidence < SUBSTANCE_CONFIDENCE_THRESHOLD:
                report.terms_skipped_low_conf += 1
                continue

            # Use lemma_gr if available, otherwise term_gr
            form_grc = (term.get("lemma_gr") or term.get("term_gr", "")).strip()
            if not form_grc:
                continue

            form_normalized = normalize(form_grc)
            form_id = make_uuid()

            lemma_form_rows.append({
                "id": form_id,
                "form_grc": form_grc,
                "form_normalized": form_normalized,
                "source": SOURCE_TAG,
                "status": "draft",
                "confidence": confidence,
                "lemma_id": None,  # never auto-assign concept
            })

            entry_lemma_form_rows.append({
                "tei_entry_id": tei_entry_id,
                "lemma_form_id": form_id,
                "role": "headword",
                "confidence": confidence,
            })

            normalized_groups[form_normalized].append({
                "source_code": source_code,
                "form_grc": form_grc,
                "form_id": form_id,
            })

            report.lemma_forms_created += 1
            report.entry_lemma_forms_linked += 1

        # --- Process qualities -> assertions ---
        qualities = result.get("qualities", [])
        for quality in qualities:
            confidence = quality.get("confidence", 0)
            if confidence < QUALITY_CONFIDENCE_THRESHOLD:
                report.qualities_skipped_low_conf += 1
                continue

            axis = (quality.get("axis", "") or "").upper()
            if axis not in VALID_QUALITY_AXES:
                report.qualities_skipped_bad_axis += 1
                continue

            payload: dict[str, Any] = {"axis": axis}
            degree = quality.get("degree")
            if degree is not None:
                payload["degree"] = str(degree)

            text_evidence = quality.get("text_evidence")
            if text_evidence:
                payload["text_evidence"] = text_evidence

            assertion_rows.append({
                "tei_entry_id": tei_entry_id,
                "assertion_type": "quality",
                "payload": payload,
                "status": "draft",
                "source": SOURCE_TAG,
                "is_stale": False,
            })
            report.assertions_created += 1

    # --- Cross-source collision detection ---
    # Mark lemma_forms as needs_review if the same form_normalized appears
    # from multiple source codes (conservative: never auto-merge across sources).
    needs_review_ids: set[str] = set()
    for form_norm, group in normalized_groups.items():
        source_codes = {item["source_code"] for item in group}
        if len(source_codes) > 1:
            # Cross-source collision: mark all forms in this group
            for item in group:
                needs_review_ids.add(item["form_id"])

    for row in lemma_form_rows:
        if row["id"] in needs_review_ids:
            row["status"] = "needs_review"
            report.needs_review_count += 1

    # --- Write to DB (or dry-run) ---
    if dry_run:
        print("[DRY RUN] Would create the following rows:")
        print(f"  lemma_forms:       {len(lemma_form_rows)}")
        print(f"  entry_lemma_forms: {len(entry_lemma_form_rows)}")
        print(f"  assertions:        {len(assertion_rows)}")

        # Show a few sample rows for inspection
        if lemma_form_rows:
            print("\n  Sample lemma_forms (first 5):")
            for row in lemma_form_rows[:5]:
                print(f"    {row['form_grc']} -> {row['form_normalized']} "
                      f"[conf={row['confidence']}, status={row['status']}]")

        if assertion_rows:
            print("\n  Sample assertions (first 5):")
            for row in assertion_rows[:5]:
                print(f"    type={row['assertion_type']} payload={row['payload']} "
                      f"[status={row['status']}]")

        # Show cross-source collisions
        cross_source_groups = {
            k: v for k, v in normalized_groups.items()
            if len({item["source_code"] for item in v}) > 1
        }
        if cross_source_groups:
            print(f"\n  Cross-source collisions ({len(cross_source_groups)} normalized forms):")
            for form_norm, group in list(cross_source_groups.items())[:10]:
                sources = sorted({item["source_code"] for item in group})
                print(f"    '{form_norm}': sources={sources}, "
                      f"variants={[item['form_grc'] for item in group]}")

    elif client:
        print(f"Upserting {len(lemma_form_rows)} lemma_forms...")
        for batch in chunked(lemma_form_rows, batch_size):
            # Serialize payload fields for lemma_forms
            client.upsert("lemma_forms", batch, on_conflict="id")

        print(f"Upserting {len(entry_lemma_form_rows)} entry_lemma_forms...")
        for batch in chunked(entry_lemma_form_rows, batch_size):
            client.upsert(
                "entry_lemma_forms",
                batch,
                on_conflict="tei_entry_id,lemma_form_id",
            )

        print(f"Upserting {len(assertion_rows)} assertions...")
        # JSON-serialize payload for assertions before sending
        for row in assertion_rows:
            if isinstance(row.get("payload"), dict):
                row["payload"] = json.dumps(row["payload"], ensure_ascii=False)
        for batch in chunked(assertion_rows, batch_size):
            client.upsert("assertions", batch, on_conflict="id")

    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import vocab v3 extraction results into TEI-first schema.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--results",
        type=Path,
        required=True,
        help="Path to results.jsonl (one JSON object per line).",
    )
    parser.add_argument(
        "--bridge",
        type=Path,
        default=_REPO_ROOT / "config" / "entry_id_bridge.csv",
        help="Path to entry_id_bridge.csv (default: config/entry_id_bridge.csv).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report without writing to database.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Upsert batch size (default: {BATCH_SIZE}).",
    )
    args = parser.parse_args()

    # --- Validate inputs ---
    if not args.results.exists():
        print(f"ERROR: results file not found: {args.results}", file=sys.stderr)
        return 2

    if not args.bridge.exists():
        print(f"ERROR: bridge CSV not found: {args.bridge}", file=sys.stderr)
        return 2

    batch_size = args.batch_size

    # --- Load data ---
    print(f"Loading bridge CSV: {args.bridge}")
    bridge = load_bridge(args.bridge)
    print(f"  {len(bridge)} bridge mappings loaded.")

    print(f"Loading results JSONL: {args.results}")
    results = load_results(args.results)
    print(f"  {len(results)} result entries loaded.")

    if not results:
        print("WARNING: no results to process.", file=sys.stderr)
        return 0

    # --- Connect to Supabase (skip in dry-run) ---
    client: SupabaseRestClient | None = None
    if not args.dry_run:
        supabase_url = env_required("SUPABASE_URL")
        service_key = env_required("SUPABASE_SERVICE_ROLE_KEY")
        client = SupabaseRestClient(supabase_url=supabase_url, api_key=service_key)
        print("Connected to Supabase.")
    else:
        print("[DRY RUN] Skipping Supabase connection.")

    # --- Process ---
    report = process_results(results, bridge, client, args.dry_run, batch_size=batch_size)
    report.print_report()

    if not args.dry_run and client:
        print("Post-import row counts:")
        for table in ["lemma_forms", "entry_lemma_forms", "assertions"]:
            try:
                print(f"  {table}: {client.count(table)}")
            except Exception as e:
                print(f"  {table}: (count failed: {e})")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
