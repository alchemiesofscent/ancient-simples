#!/usr/bin/env python3
"""Import cross-author alignment data into TEI-first schema.

Reads alignment JSONL (per AL-01 interchange format) and creates
tei_entry_alignments rows. Entry display IDs are resolved to
tei_entries.id integers via Supabase REST lookup.

Usage:
    python scripts/import_alignments.py --data config/alignments/seed.jsonl
    python scripts/import_alignments.py --data config/alignments/seed.jsonl --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path for imports
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
sys.path.insert(0, str(_REPO_ROOT))

from supabase_rest import SupabaseRestClient, env_required

VALID_ALIGNMENT_TYPES = {"chapter_parallel", "excerpt", "rearrangement", "independent"}


def load_alignments(path: Path) -> list[dict]:
    """Load alignment records from JSONL file."""
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"WARNING: Line {line_num}: invalid JSON: {e}", file=sys.stderr)
                continue

            # Validate required fields
            missing = []
            for field in ("source_a_entry_id", "source_b_entry_id", "alignment_type", "source"):
                if field not in rec:
                    missing.append(field)
            if missing:
                print(f"WARNING: Line {line_num}: missing fields: {missing}", file=sys.stderr)
                continue

            if rec["alignment_type"] not in VALID_ALIGNMENT_TYPES:
                print(
                    f"WARNING: Line {line_num}: invalid alignment_type: {rec['alignment_type']}",
                    file=sys.stderr,
                )
                continue

            if rec["source_a_entry_id"] == rec["source_b_entry_id"]:
                print(f"WARNING: Line {line_num}: self-alignment skipped", file=sys.stderr)
                continue

            records.append(rec)
    return records


def resolve_entry_ids(client: SupabaseRestClient, display_ids: set[str]) -> dict[str, int]:
    """Resolve display_entry_ids to tei_entries.id integers."""
    mapping = {}
    for did in display_ids:
        result = client.get_json(
            "/rest/v1/tei_entries",
            query={
                "select": "id",
                "display_entry_id": f"eq.{did}",
                "is_active": "eq.true",
                "limit": "1",
            },
        )
        if result and len(result) > 0:
            mapping[did] = result[0]["id"]
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Import alignment data into tei_entry_alignments")
    parser.add_argument("--data", required=True, help="Path to alignment JSONL file")
    parser.add_argument("--dry-run", action="store_true", help="Print report without DB writes")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Data file not found: {data_path}", file=sys.stderr)
        return 1

    records = load_alignments(data_path)
    print(f"Loaded {len(records)} alignment record(s) from {data_path}")

    if not records:
        print("No valid records to import.")
        return 0

    # Collect all unique display entry IDs
    all_display_ids = set()
    for rec in records:
        all_display_ids.add(rec["source_a_entry_id"])
        all_display_ids.add(rec["source_b_entry_id"])

    if args.dry_run:
        print(f"\n[DRY RUN] Would resolve {len(all_display_ids)} unique entry IDs")
        print(f"[DRY RUN] Would create up to {len(records)} alignment rows")
        by_type = {}
        for rec in records:
            t = rec["alignment_type"]
            by_type[t] = by_type.get(t, 0) + 1
        for t, count in sorted(by_type.items()):
            print(f"  {t}: {count}")
        return 0

    # Connect to Supabase
    client = SupabaseRestClient(
        supabase_url=env_required("SUPABASE_URL"),
        api_key=env_required("SUPABASE_SERVICE_ROLE_KEY"),
    )

    # Resolve entry IDs
    print(f"Resolving {len(all_display_ids)} display entry IDs...")
    id_map = resolve_entry_ids(client, all_display_ids)
    print(f"  Resolved: {len(id_map)} / {len(all_display_ids)}")

    unresolved = all_display_ids - set(id_map.keys())
    if unresolved:
        print(f"  Unresolved: {sorted(unresolved)[:10]}{'...' if len(unresolved) > 10 else ''}")

    # Build rows for upsert
    rows = []
    skipped = 0
    for rec in records:
        a_id = id_map.get(rec["source_a_entry_id"])
        b_id = id_map.get(rec["source_b_entry_id"])
        if a_id is None or b_id is None:
            skipped += 1
            continue

        row = {
            "tei_entry_id_a": a_id,
            "tei_entry_id_b": b_id,
            "alignment_type": rec["alignment_type"],
            "source": rec["source"],
        }
        if "confidence" in rec and rec["confidence"] is not None:
            row["confidence"] = rec["confidence"]
        if "evidence" in rec and rec["evidence"] is not None:
            row["evidence"] = rec["evidence"]
        if "curator" in rec:
            row["curator"] = rec["curator"]
        rows.append(row)

    if rows:
        # Batch upsert
        batch_size = 200
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            client.upsert(
                "tei_entry_alignments",
                batch,
                on_conflict="tei_entry_id_a,tei_entry_id_b,alignment_type",
            )

    # Report
    print(f"\nImport complete:")
    print(f"  Alignment rows created/updated: {len(rows)}")
    print(f"  Skipped (unresolved IDs): {skipped}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
