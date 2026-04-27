#!/usr/bin/env python3
"""Import vocab v3 extraction results.

The extraction contract emits `source_id`. For the current outputs-to-search
path, that ID maps directly to legacy `entries.entry_id`; TEI import remains
available but bridge-gated.
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


_REPO_ROOT = Path(__file__).resolve().parents[1]
_PACKAGES_PATH = _REPO_ROOT / "packages"
if str(_PACKAGES_PATH) not in sys.path:
    sys.path.insert(0, str(_PACKAGES_PATH))
_SCRIPTS_PATH = _REPO_ROOT / "scripts"
if str(_SCRIPTS_PATH) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_PATH))

from textutils import normalize
from supabase_rest import SupabaseRestClient, SupabaseRestError, env_required


VALID_QUALITY_AXES = {"HOT", "COLD", "DRY", "WET"}
SUBSTANCE_CONFIDENCE_THRESHOLD = 0.75
QUALITY_CONFIDENCE_THRESHOLD = 0.70
BATCH_SIZE = 200
SOURCE_TAG = "v3_import"
UUID_NAMESPACE = uuid.UUID("8b0d9035-550e-4ec4-9e42-0e6e736d7659")


def stable_uuid(*parts: object) -> str:
    return str(uuid.uuid5(UUID_NAMESPACE, "|".join(str(part) for part in parts)))


def load_bridge(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
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
            source_id = (obj.get("source_id") or obj.get("entry_id") or "").strip()
            if not source_id:
                print(f"WARNING: skipping result with no source_id at line {lineno}", file=sys.stderr)
                continue
            obj["source_id"] = source_id
            obj.setdefault("entry_id", source_id)
            results.append(obj)
    return results


def load_entry_id_aliases(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    aliases: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(line for line in f if not line.startswith("#"))
        for row in reader:
            old_id = (row.get("old_entry_id") or "").strip()
            new_id = (row.get("new_entry_id") or "").strip()
            if old_id and new_id:
                aliases[old_id] = new_id
    return aliases


def chunked(items: list[Any], n: int) -> list[list[Any]]:
    return [items[i : i + n] for i in range(0, len(items), n)]


def extract_source_from_entry_id(entry_id: str) -> str:
    if "-" in entry_id:
        return entry_id.rsplit("-", 1)[0]
    return entry_id


class ImportReport:
    def __init__(self) -> None:
        self.entries_processed = 0
        self.entries_skipped_no_bridge = 0
        self.entries_skipped_no_tei = 0
        self.entries_skipped_missing_legacy = 0
        self.lemma_forms_created = 0
        self.entry_lemma_forms_linked = 0
        self.assertions_created = 0
        self.needs_review_count = 0
        self.terms_skipped_low_conf = 0
        self.terms_skipped_non_substance = 0
        self.qualities_skipped_low_conf = 0
        self.qualities_skipped_bad_axis = 0

    def print_report(self) -> None:
        print("\n=== Vocab v3 Import Report ===")
        print(f"  Entries processed:              {self.entries_processed}")
        print(f"  Entries skipped (no bridge):     {self.entries_skipped_no_bridge}")
        print(f"  Entries skipped (no TEI row):    {self.entries_skipped_no_tei}")
        print(f"  Entries skipped (no legacy row): {self.entries_skipped_missing_legacy}")
        print(f"  Lemma forms upserted:            {self.lemma_forms_created}")
        print(f"  Entry-lemma links upserted:      {self.entry_lemma_forms_linked}")
        print(f"  Assertions upserted:             {self.assertions_created}")
        print(f"  Needs review (cross-source):     {self.needs_review_count}")
        print(f"  Terms skipped (low conf):        {self.terms_skipped_low_conf}")
        print(f"  Terms skipped (non-SUBST):       {self.terms_skipped_non_substance}")
        print(f"  Qualities skipped (low conf):    {self.qualities_skipped_low_conf}")
        print(f"  Qualities skipped (bad axis):    {self.qualities_skipped_bad_axis}")
        print("==============================\n")


def resolve_tei_entry_id(
    client: SupabaseRestClient,
    tei_doc_id: str,
    tei_segment_id: str,
    *,
    cache: dict[str, int | None],
) -> int | None:
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
    cache[cache_key] = rows[0]["id"] if rows else None
    return cache[cache_key]


def _quality_payload(quality: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "axis": (quality.get("axis") or "").upper(),
        "intensity": quality.get("intensity"),
        "hedge": quality.get("hedge"),
        "evidence_display": quality.get("evidence_display"),
        "evidence_normalized": quality.get("evidence_normalized"),
        "applies_to": quality.get("applies_to"),
    }
    degree = quality.get("degree")
    if degree is not None:
        payload["degree"] = str(degree)
    variant_place = quality.get("variant_place_lemma_normalized")
    if variant_place:
        payload["variant_place_lemma_normalized"] = variant_place
    return {k: v for k, v in payload.items() if v is not None}


def build_legacy_rows(
    results: list[dict[str, Any]],
    *,
    existing_entry_ids: set[str] | None,
    entry_id_aliases: dict[str, str],
) -> tuple[ImportReport, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    report = ImportReport()
    lemma_form_rows_by_id: dict[str, dict[str, Any]] = {}
    entry_lemma_form_rows_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    assertion_rows_by_id: dict[str, dict[str, Any]] = {}
    normalized_groups: dict[str, set[str]] = defaultdict(set)

    for result in results:
        source_id = (result.get("source_id") or result.get("entry_id") or "").strip()
        if not source_id:
            continue
        entry_id = entry_id_aliases.get(source_id, source_id)
        if existing_entry_ids is not None and entry_id not in existing_entry_ids:
            report.entries_skipped_missing_legacy += 1
            continue
        report.entries_processed += 1
        source_code = extract_source_from_entry_id(entry_id)

        for term in result.get("terms") or []:
            label = (term.get("label", "") or "").upper()
            if label != "SUBSTANCE":
                report.terms_skipped_non_substance += 1
                continue
            confidence = float(term.get("confidence", 0) or 0)
            if confidence < SUBSTANCE_CONFIDENCE_THRESHOLD:
                report.terms_skipped_low_conf += 1
                continue

            form_grc = (term.get("lemma_gr") or term.get("display") or "").strip()
            if not form_grc:
                continue
            form_normalized = normalize(form_grc)
            form_id = stable_uuid("legacy_lemma_form", source_code, form_normalized)
            normalized_groups[form_normalized].add(source_code)

            row = lemma_form_rows_by_id.get(form_id)
            if row is None or confidence > float(row.get("confidence") or 0):
                lemma_form_rows_by_id[form_id] = {
                    "id": form_id,
                    "source_code": source_code,
                    "form_grc": form_grc,
                    "form_normalized": form_normalized,
                    "status": "draft",
                    "source": SOURCE_TAG,
                    "confidence": confidence,
                }

            link_key = (entry_id, form_id, "headword")
            link_row = entry_lemma_form_rows_by_key.get(link_key)
            if link_row is None or confidence > float(link_row.get("confidence") or 0):
                entry_lemma_form_rows_by_key[link_key] = {
                    "entry_id": entry_id,
                    "lemma_form_id": form_id,
                    "role": "headword",
                    "confidence": confidence,
                }

        for idx, quality in enumerate(result.get("qualities") or []):
            confidence = float(quality.get("confidence", 0) or 0)
            if confidence < QUALITY_CONFIDENCE_THRESHOLD:
                report.qualities_skipped_low_conf += 1
                continue
            axis = (quality.get("axis", "") or "").upper()
            if axis not in VALID_QUALITY_AXES:
                report.qualities_skipped_bad_axis += 1
                continue
            evidence = quality.get("evidence_normalized") or quality.get("evidence_display") or ""
            assertion_id = stable_uuid("legacy_assertion", entry_id, idx, axis, evidence)
            assertion_rows_by_id[assertion_id] = {
                "id": assertion_id,
                "entry_id": entry_id,
                "assertion_type": "quality",
                "payload": _quality_payload(quality),
                "status": "draft",
                "source": SOURCE_TAG,
                "is_stale": False,
                "confidence": confidence,
            }

    cross_source_norms = {norm for norm, sources in normalized_groups.items() if len(sources) > 1}
    for row in lemma_form_rows_by_id.values():
        if row["form_normalized"] in cross_source_norms:
            row["status"] = "needs_review"
            report.needs_review_count += 1

    lemma_form_rows = list(lemma_form_rows_by_id.values())
    entry_lemma_form_rows = list(entry_lemma_form_rows_by_key.values())
    assertion_rows = list(assertion_rows_by_id.values())
    report.lemma_forms_created = len(lemma_form_rows)
    report.entry_lemma_forms_linked = len(entry_lemma_form_rows)
    report.assertions_created = len(assertion_rows)
    return report, lemma_form_rows, entry_lemma_form_rows, assertion_rows


def load_legacy_entry_ids_from_csv(paths: list[Path]) -> set[str]:
    ids: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                entry_id = (row.get("entry_id") or "").strip()
                if entry_id:
                    ids.add(entry_id)
    return ids


def upsert_rows(
    client: SupabaseRestClient | None,
    dry_run: bool,
    *,
    lemma_form_rows: list[dict[str, Any]],
    entry_lemma_form_rows: list[dict[str, Any]],
    assertion_rows: list[dict[str, Any]],
    batch_size: int,
) -> None:
    if dry_run:
        print("[DRY RUN] Would create/update the following legacy extraction rows:")
        print(f"  legacy_vocab_lemma_forms:       {len(lemma_form_rows)}")
        print(f"  legacy_vocab_entry_lemma_forms: {len(entry_lemma_form_rows)}")
        print(f"  legacy_vocab_assertions:        {len(assertion_rows)}")
        if lemma_form_rows:
            print("\n  Sample lemma forms:")
            for row in lemma_form_rows[:5]:
                print(
                    f"    {row['source_code']} {row['form_grc']} -> {row['form_normalized']} "
                    f"[{row['status']}, conf={row['confidence']}]"
                )
        if assertion_rows:
            print("\n  Sample assertions:")
            for row in assertion_rows[:5]:
                print(f"    {row['entry_id']} {row['payload']}")
        return

    if client is None:
        raise RuntimeError("client is required for live import")

    for batch in chunked(lemma_form_rows, batch_size):
        client.upsert("legacy_vocab_lemma_forms", batch, on_conflict="id")
    for batch in chunked(entry_lemma_form_rows, batch_size):
        client.upsert(
            "legacy_vocab_entry_lemma_forms",
            batch,
            on_conflict="entry_id,lemma_form_id,role",
        )
    assertion_payload_rows = []
    for row in assertion_rows:
        copy = dict(row)
        if isinstance(copy.get("payload"), dict):
            copy["payload"] = json.dumps(copy["payload"], ensure_ascii=False)
        assertion_payload_rows.append(copy)
    for batch in chunked(assertion_payload_rows, batch_size):
        client.upsert("legacy_vocab_assertions", batch, on_conflict="id")


def process_tei_results(
    results: list[dict[str, Any]],
    bridge: dict[str, dict[str, str]],
    client: SupabaseRestClient | None,
    dry_run: bool,
    batch_size: int,
    entry_id_aliases: dict[str, str],
) -> ImportReport:
    report = ImportReport()
    tei_id_cache: dict[str, int | None] = {}
    legacy_rows = build_legacy_rows(
        results,
        existing_entry_ids=None,
        entry_id_aliases=entry_id_aliases,
    )
    report, lemma_form_rows, entry_lemma_form_rows, assertion_rows = legacy_rows

    for row in list(entry_lemma_form_rows):
        entry_id = row.pop("entry_id")
        bridge_row = bridge.get(entry_id)
        if not bridge_row:
            report.entries_skipped_no_bridge += 1
            entry_lemma_form_rows.remove(row)
            continue
        if client and not dry_run:
            tei_entry_id = resolve_tei_entry_id(
                client,
                bridge_row["tei_doc_id"],
                bridge_row["tei_segment_id"],
                cache=tei_id_cache,
            )
            if tei_entry_id is None:
                report.entries_skipped_no_tei += 1
                entry_lemma_form_rows.remove(row)
                continue
        else:
            tei_entry_id = -1
        row["tei_entry_id"] = tei_entry_id

    for row in list(assertion_rows):
        entry_id = row.pop("entry_id")
        bridge_row = bridge.get(entry_id)
        if not bridge_row:
            report.entries_skipped_no_bridge += 1
            assertion_rows.remove(row)
            continue
        if client and not dry_run:
            tei_entry_id = resolve_tei_entry_id(
                client,
                bridge_row["tei_doc_id"],
                bridge_row["tei_segment_id"],
                cache=tei_id_cache,
            )
            if tei_entry_id is None:
                report.entries_skipped_no_tei += 1
                assertion_rows.remove(row)
                continue
        else:
            tei_entry_id = -1
        row["tei_entry_id"] = tei_entry_id

    if dry_run:
        print("[DRY RUN] TEI import remains bridge-gated.")
        print(f"  tei_lemma_forms:       {len(lemma_form_rows)}")
        print(f"  tei_entry_lemma_forms: {len(entry_lemma_form_rows)}")
        print(f"  tei_assertions:        {len(assertion_rows)}")
        return report

    if client is None:
        raise RuntimeError("client is required for live import")
    for batch in chunked(lemma_form_rows, batch_size):
        client.upsert("tei_lemma_forms", batch, on_conflict="id")
    for batch in chunked(entry_lemma_form_rows, batch_size):
        client.upsert("tei_entry_lemma_forms", batch, on_conflict="tei_entry_id,lemma_form_id")
    for row in assertion_rows:
        if isinstance(row.get("payload"), dict):
            row["payload"] = json.dumps(row["payload"], ensure_ascii=False)
    for batch in chunked(assertion_rows, batch_size):
        client.upsert("tei_assertions", batch, on_conflict="id")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Import vocab v3 extraction results.")
    parser.add_argument("--results", type=Path, required=True, help="Path to results.jsonl.")
    parser.add_argument(
        "--target",
        choices=["legacy", "tei"],
        default="legacy",
        help="Import target. legacy is the outputs-to-search path; tei requires a populated bridge.",
    )
    parser.add_argument(
        "--bridge",
        type=Path,
        default=_REPO_ROOT / "config" / "entry_id_bridge.csv",
        help="Path to entry_id_bridge.csv for --target tei.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report without writing to Supabase.")
    parser.add_argument(
        "--entry-id-aliases",
        type=Path,
        default=_REPO_ROOT / "config" / "vocab_entry_id_aliases.csv",
        help="CSV mapping extraction source_id values to current legacy entry IDs.",
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    if not args.results.exists():
        print(f"ERROR: results file not found: {args.results}", file=sys.stderr)
        return 2

    print(f"Loading results JSONL: {args.results}")
    results = load_results(args.results)
    print(f"  {len(results)} result entries loaded.")
    if not results:
        print("WARNING: no results to process.", file=sys.stderr)
        return 0
    entry_id_aliases = load_entry_id_aliases(args.entry_id_aliases)
    if entry_id_aliases:
        print(f"Loaded {len(entry_id_aliases)} entry-id aliases from {args.entry_id_aliases}")

    client: SupabaseRestClient | None = None
    if not args.dry_run:
        client = SupabaseRestClient(
            supabase_url=env_required("SUPABASE_URL"),
            api_key=env_required("SUPABASE_SERVICE_ROLE_KEY"),
        )
        print("Connected to Supabase.")
    else:
        print("[DRY RUN] Skipping Supabase connection.")

    if args.target == "legacy":
        existing_entry_ids = None
        if args.dry_run:
            existing_entry_ids = load_legacy_entry_ids_from_csv(
                [
                    _REPO_ROOT / "data-workbench" / "entries.csv",
                    _REPO_ROOT / "data-workbench" / "entries_diosc.csv",
                    _REPO_ROOT / "data-workbench" / "entries_paul.csv",
                ]
            )
        report, lemma_form_rows, entry_lemma_form_rows, assertion_rows = build_legacy_rows(
            results,
            existing_entry_ids=existing_entry_ids,
            entry_id_aliases=entry_id_aliases,
        )
        upsert_rows(
            client,
            args.dry_run,
            lemma_form_rows=lemma_form_rows,
            entry_lemma_form_rows=entry_lemma_form_rows,
            assertion_rows=assertion_rows,
            batch_size=args.batch_size,
        )
    else:
        if not args.bridge.exists():
            print(f"ERROR: bridge CSV not found: {args.bridge}", file=sys.stderr)
            return 2
        print(f"Loading bridge CSV: {args.bridge}")
        bridge = load_bridge(args.bridge)
        print(f"  {len(bridge)} bridge mappings loaded.")
        result_entry_ids = set()
        for result in results:
            source_id = (result.get("source_id") or result.get("entry_id") or "").strip()
            if source_id:
                result_entry_ids.add(entry_id_aliases.get(source_id, source_id))
        missing_bridge = sorted(result_entry_ids - set(bridge))
        if missing_bridge:
            print(
                f"ERROR: TEI import is bridge-gated; {len(missing_bridge)} result entries "
                f"have no bridge mapping. First missing IDs: {missing_bridge[:20]}",
                file=sys.stderr,
            )
            return 2
        report = process_tei_results(
            results,
            bridge,
            client,
            args.dry_run,
            args.batch_size,
            entry_id_aliases,
        )

    report.print_report()

    if not args.dry_run and client:
        tables = (
            ["legacy_vocab_lemma_forms", "legacy_vocab_entry_lemma_forms", "legacy_vocab_assertions"]
            if args.target == "legacy"
            else ["tei_lemma_forms", "tei_entry_lemma_forms", "tei_assertions"]
        )
        print("Post-import row counts:")
        for table in tables:
            try:
                print(f"  {table}: {client.count(table)}")
            except Exception as e:
                print(f"  {table}: (count failed: {e})")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
