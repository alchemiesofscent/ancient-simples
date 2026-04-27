#!/usr/bin/env python3
"""TEI indexer for Ancient Simples TEI-first platform.

Reads TEI doc config + TEI XML -> extracts entries, citations, tokens ->
upserts to Supabase. Supports --dry-run for JSON preview.

Usage:
    python scripts/index_tei.py --config config/tei_docs/gal_smt.yaml
    python scripts/index_tei.py --config config/tei_docs/gal_smt.yaml --dry-run
    python scripts/index_tei.py --config config/tei_docs/gal_smt.yaml --subset config/test_subset.txt
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from lxml import etree

# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))  # for supabase_rest

from textutils import (
    NORMALIZATION_VERSION,
    TOKENIZER_VERSION,
    dual_hash,
    tokenize,
)
from supabase_rest import SupabaseRestClient, env_required  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEI_NS = "http://www.tei-c.org/ns/1.0"
NSMAP = {"tei": TEI_NS}
XML_NS = "http://www.w3.org/XML/1998/namespace"

INDEXER_VERSION = "1.0.0"
TOKEN_BATCH_SIZE = 500
ENTRY_BATCH_SIZE = 50
REF_BATCH_SIZE = 500

# Tags to skip entirely (omit from reading text)
SKIP_TAGS = {
    f"{{{TEI_NS}}}note",
    f"{{{TEI_NS}}}add",
    f"{{{TEI_NS}}}del",
}

# Milestone tags (no text contribution, but recorded as edition refs)
MILESTONE_TAGS = {
    f"{{{TEI_NS}}}pb",
    f"{{{TEI_NS}}}lb",
}

GAP_PLACEHOLDER = "[...]"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    """Load and return the TEI doc config YAML."""
    with config_path.open() as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# CMG submodule commit hash
# ---------------------------------------------------------------------------

def get_cmg_commit(repo_root: Path) -> str | None:
    """Return the CMG submodule commit hash, or None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "submodule", "status", "tei/cmg"],
            capture_output=True, text=True, cwd=str(repo_root),
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Format: " <hash> tei/cmg (<desc>)" or "+<hash> ..."
            line = result.stdout.strip()
            return line.lstrip(" +-").split()[0]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Reading text extraction with edition ref tracking
# ---------------------------------------------------------------------------

class ReadingStreamExtractor:
    """Extract reading text from a TEI segment, tracking edition milestones.

    Follows C-01 section 6.2 rules for TEI construct resolution and C-04
    for edition ref extraction.
    """

    def __init__(self) -> None:
        self._parts: list[str] = []
        self._offset: int = 0  # current codepoint offset into reading_text
        self.edition_refs: list[dict[str, Any]] = []

    def extract(self, node: etree._Element) -> str:
        """Extract reading text from a segment node. Returns the text."""
        self._parts = []
        self._offset = 0
        self.edition_refs = []
        self._walk(node)
        raw = "".join(self._parts)
        # Collapse whitespace, trim
        text = re.sub(r"\s+", " ", raw).strip()
        # NFC normalize
        text = unicodedata.normalize("NFC", text)
        return text

    def _emit(self, text: str) -> None:
        """Append text to the reading stream and advance offset."""
        if text:
            self._parts.append(text)
            self._offset += len(text)

    def _record_milestone(self, node: etree._Element) -> None:
        """Record a pb/lb milestone with its current codepoint offset."""
        tag = node.tag if isinstance(node.tag, str) else ""
        if tag == f"{{{TEI_NS}}}pb":
            kind = "pb"
        elif tag == f"{{{TEI_NS}}}lb":
            kind = "lb"
        else:
            return
        n = node.get("n", "")
        # Compute offset into the *final* reading text. We use the current
        # accumulated codepoint count. After whitespace collapse this may
        # shift slightly, so we compute the offset relative to the raw
        # accumulated text and then adjust in _finalize_offsets.
        self.edition_refs.append({
            "kind": kind,
            "n": n,
            "offset": self._offset,
        })

    def _walk(self, node: etree._Element) -> None:
        """Recursively walk TEI nodes and emit reading text."""
        tag = node.tag if isinstance(node.tag, str) else ""

        # Skip tags: omit entirely (no text, no tail)
        if tag in SKIP_TAGS:
            return

        # Milestone tags: record ref, emit nothing for text
        if tag in MILESTONE_TAGS:
            self._record_milestone(node)
            return

        # <gap>: insert placeholder with spacing
        if tag == f"{{{TEI_NS}}}gap":
            self._emit_gap_placeholder()
            return

        # <choice>: prefer <reg> over <orig>, <expan> over <abbr>
        if tag == f"{{{TEI_NS}}}choice":
            reg = node.find(f"{{{TEI_NS}}}reg")
            if reg is not None:
                self._walk(reg)
                return
            expan = node.find(f"{{{TEI_NS}}}expan")
            if expan is not None:
                self._walk(expan)
                return
            # Fallback: first child element
            for child in node:
                self._walk(child)
                return
            return

        # <app>: prefer <lem>, ignore <rdg>
        if tag == f"{{{TEI_NS}}}app":
            lem = node.find(f"{{{TEI_NS}}}lem")
            if lem is not None:
                self._walk(lem)
                return
            # Fallback: first <rdg>
            rdg = node.find(f"{{{TEI_NS}}}rdg")
            if rdg is not None:
                self._walk(rdg)
            return

        # Default: emit text, recurse children, emit tail of children
        if node.text:
            self._emit(node.text)
        for child in node:
            self._walk(child)
            if child.tag in SKIP_TAGS:
                # Skipped tags still contribute their tail text
                if child.tail:
                    self._emit(child.tail)
            elif child.tag in MILESTONE_TAGS:
                # Milestones contribute tail text
                if child.tail:
                    self._emit(child.tail)
            elif child.tail:
                self._emit(child.tail)

    def _emit_gap_placeholder(self) -> None:
        """Emit [...] with spacing per C-01 section 6.3.

        If the placeholder would abut a letter/digit, ensure a space.
        """
        # Check last character emitted
        accumulated = "".join(self._parts)
        needs_leading_space = False
        if accumulated and _is_letter_or_digit(accumulated[-1]):
            needs_leading_space = True

        if needs_leading_space:
            self._emit(" ")
        self._emit(GAP_PLACEHOLDER)
        # We cannot know the next character yet; we add a trailing space
        # unconditionally. The final whitespace collapse will clean it
        # up if it is redundant (e.g., before punctuation or existing space).
        self._emit(" ")


def _is_letter_or_digit(ch: str) -> bool:
    """Return True if ch is a Unicode letter or digit."""
    cat = unicodedata.category(ch)
    return cat.startswith("L") or cat.startswith("N")


def finalize_edition_ref_offsets(
    raw_parts_text: str, collapsed_text: str, raw_refs: list[dict]
) -> list[dict]:
    """Adjust raw offsets to account for whitespace collapse.

    This is a best-effort mapping: for each raw offset, we find the
    corresponding position in the collapsed text by tracking how
    whitespace collapse compresses the string.

    In practice, milestone offsets almost always land at whitespace
    boundaries or the start of text, so the adjustment is small.
    """
    # Build a mapping from raw offset -> collapsed offset
    # by walking both strings in parallel.
    if not raw_refs:
        return raw_refs

    # Simplified approach: rebuild the collapse mapping
    # raw_parts_text has already been joined but not yet collapsed.
    # collapsed_text is the final NFC-normalized result.
    # We map by scanning the raw text and tracking where we are
    # in the collapsed version.
    raw_to_collapsed: dict[int, int] = {}
    ri = 0  # raw index
    ci = 0  # collapsed index
    in_ws = False
    # Account for leading whitespace trim
    while ri < len(raw_parts_text) and raw_parts_text[ri] in " \t\n\r":
        raw_to_collapsed[ri] = 0
        ri += 1

    while ri < len(raw_parts_text) and ci < len(collapsed_text):
        raw_ch = raw_parts_text[ri]
        col_ch = collapsed_text[ci]
        if raw_ch in " \t\n\r":
            if not in_ws:
                # First whitespace char maps to the space in collapsed
                raw_to_collapsed[ri] = ci
                in_ws = True
                if col_ch == " ":
                    ci += 1
            else:
                # Subsequent whitespace chars in a run
                raw_to_collapsed[ri] = ci
            ri += 1
        else:
            in_ws = False
            raw_to_collapsed[ri] = ci
            ri += 1
            ci += 1

    # Any remaining raw positions map to end of collapsed text
    while ri < len(raw_parts_text):
        raw_to_collapsed[ri] = len(collapsed_text)
        ri += 1

    # Also map the position at end of raw to end of collapsed
    raw_to_collapsed[len(raw_parts_text)] = len(collapsed_text)

    adjusted = []
    for ref in raw_refs:
        raw_off = ref["offset"]
        collapsed_off = raw_to_collapsed.get(raw_off, raw_off)
        adjusted.append({**ref, "offset": collapsed_off})
    return adjusted


# ---------------------------------------------------------------------------
# Structure ref extraction
# ---------------------------------------------------------------------------

def extract_structure_refs(
    segment: etree._Element, tree: etree._ElementTree
) -> list[dict[str, Any]]:
    """Walk ancestor divs from segment up to body, return outer-to-inner path.

    Each entry in the path has: type, n, xml_id, head (all optional strings).
    """
    # Collect ancestor chain
    # lxml does not have a direct parent pointer for arbitrary nodes when
    # using tree.xpath, so we build a parent map.
    parent_map = {child: parent for parent in tree.iter() for child in parent}

    divs: list[etree._Element] = []
    current = parent_map.get(segment)
    body_tag = f"{{{TEI_NS}}}body"

    while current is not None:
        tag = current.tag if isinstance(current.tag, str) else ""
        if tag == body_tag:
            break
        if tag == f"{{{TEI_NS}}}div":
            divs.append(current)
        current = parent_map.get(current)

    # Reverse to get outer-to-inner order
    divs.reverse()

    path: list[dict[str, Any]] = []
    for div in divs:
        entry: dict[str, Any] = {}
        div_type = div.get("type")
        if div_type:
            entry["type"] = div_type
        n = div.get("n")
        if n:
            entry["n"] = n
        xml_id = div.get(f"{{{XML_NS}}}id")
        if xml_id:
            entry["xml_id"] = xml_id
        head_el = div.find(f"{{{TEI_NS}}}head")
        if head_el is not None:
            head_text = "".join(head_el.itertext())
            head_text = re.sub(r"\s+", " ", head_text).strip()
            if head_text:
                entry["head"] = head_text
        if entry:
            path.append(entry)

    return path


# ---------------------------------------------------------------------------
# Summary edition ref computation (C-04 section 4.3)
# ---------------------------------------------------------------------------

def compute_summary_edition_ref(
    edition_events: list[dict], edition_label: str
) -> dict[str, Any] | None:
    """Derive summary start/end from edition milestone events.

    Returns the edition ref payload for the entry_refs row, or None if
    no pb milestones exist.
    """
    pbs = [e for e in edition_events if e["kind"] == "pb"]
    lbs = [e for e in edition_events if e["kind"] == "lb"]

    if not pbs:
        return None

    start_pb = pbs[0]["n"]
    end_pb = pbs[-1]["n"]

    # Start lb: first lb after (or at same position as) the first pb
    start_lb = None
    first_pb_offset = pbs[0]["offset"]
    for lb in lbs:
        if lb["offset"] >= first_pb_offset:
            start_lb = lb["n"]
            break

    # End lb: last lb
    end_lb = lbs[-1]["n"] if lbs else None

    payload: dict[str, Any] = {
        "edition": edition_label,
        "start": {"pb": start_pb},
        "end": {"pb": end_pb},
        "events": edition_events,
    }
    if start_lb is not None:
        payload["start"]["lb"] = start_lb
    if end_lb is not None:
        payload["end"]["lb"] = end_lb

    return payload


# ---------------------------------------------------------------------------
# Subset file loading
# ---------------------------------------------------------------------------

def load_subset(subset_path: Path, tei_doc_id: str) -> set[str]:
    """Load a subset file of entry IDs and return the set of tei_segment_ids.

    The file contains display_entry_ids (one per line), formatted as
    {tei_doc_id}~{tei_segment_id}. Lines starting with # are comments.
    Blank lines are ignored.
    """
    segment_ids: set[str] = set()
    prefix = f"{tei_doc_id}~"
    with subset_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Accept either display_entry_id or bare tei_segment_id
            if line.startswith(prefix):
                segment_ids.add(line[len(prefix):])
            else:
                # Assume it is a bare tei_segment_id
                segment_ids.add(line)
    return segment_ids


# ---------------------------------------------------------------------------
# Batching helper
# ---------------------------------------------------------------------------

def chunked(items: list, n: int) -> list[list]:
    """Split items into chunks of at most n."""
    return [items[i:i + n] for i in range(0, len(items), n)]


# ---------------------------------------------------------------------------
# Main indexing logic
# ---------------------------------------------------------------------------

def index_tei(
    config: dict,
    repo_root: Path,
    *,
    dry_run: bool = False,
    subset: set[str] | None = None,
) -> dict[str, Any]:
    """Index a TEI document per config. Returns a report dict.

    If dry_run is True, no database writes are made and the report includes
    sample entries and full metadata.
    """
    tei_doc_id: str = config["tei_doc_id"]
    source_code: str = config.get("source_code", tei_doc_id)
    tei_relpath: str = config["tei_relpath"]
    segment_xpath: str = config["segment_xpath"]
    edition_label: str = config.get("edition_label", "")

    tei_path = repo_root / tei_relpath
    if not tei_path.exists():
        raise FileNotFoundError(f"TEI file not found: {tei_path}")

    tree = etree.parse(str(tei_path))
    segments = tree.xpath(segment_xpath, namespaces=NSMAP)

    if not segments:
        raise ValueError(f"Zero segments selected by XPath: {segment_xpath}")

    # Build parent map once for structure ref extraction
    # (kept outside the per-segment loop for efficiency)

    # -----------------------------------------------------------------------
    # Process segments
    # -----------------------------------------------------------------------
    entry_rows: list[dict[str, Any]] = []
    ref_rows: list[dict[str, Any]] = []
    token_rows: list[dict[str, Any]] = []
    seen_segment_ids: list[str] = []

    for seg in segments:
        xml_id = seg.get(f"{{{XML_NS}}}id")
        if xml_id is None:
            continue  # validation should have caught this

        # Subset filtering
        if subset is not None and xml_id not in subset:
            continue

        display_entry_id = f"{tei_doc_id}~{xml_id}"
        seen_segment_ids.append(xml_id)

        # Extract reading text with edition refs
        extractor = ReadingStreamExtractor()
        reading_text = extractor.extract(seg)

        # Finalize edition ref offsets (adjust for whitespace collapse)
        raw_joined = "".join(extractor._parts)
        edition_events = finalize_edition_ref_offsets(
            raw_joined, reading_text, extractor.edition_refs
        )

        # Compute hashes
        rh, nh = dual_hash(reading_text)

        # Extract structure refs
        structure_path = extract_structure_refs(seg, tree)

        # Compute summary edition ref
        summary_edition = compute_summary_edition_ref(
            edition_events, edition_label
        )

        # Tokenize
        tokens = tokenize(reading_text)

        # Build entry row
        entry_row: dict[str, Any] = {
            "tei_doc_id": tei_doc_id,
            "tei_segment_id": xml_id,
            "display_entry_id": display_entry_id,
            "source_code": source_code,
            "reading_text": reading_text,
            "raw_hash": rh,
            "normalized_hash": nh,
            "is_active": True,
            "normalization_version": NORMALIZATION_VERSION,
            "tokenizer_version": TOKENIZER_VERSION,
            "indexer_version": INDEXER_VERSION,
        }
        entry_rows.append(entry_row)

        # Build structure ref row
        ref_rows.append({
            "tei_doc_id": tei_doc_id,
            "tei_segment_id": xml_id,
            "ref_type": "structure",
            "payload": {"path": structure_path},
        })

        # Build edition ref row (if milestones exist)
        if summary_edition is not None:
            ref_rows.append({
                "tei_doc_id": tei_doc_id,
                "tei_segment_id": xml_id,
                "ref_type": "edition",
                "payload": summary_edition,
            })

        # Build token rows
        for tok in tokens:
            token_rows.append({
                "tei_doc_id": tei_doc_id,
                "tei_segment_id": xml_id,
                "token_index": tok["token_index"],
                "start_offset": tok["start_offset"],
                "end_offset": tok["end_offset"],
                "token_text": tok["token_text"],
                "token_normalized": tok["token_normalized"],
            })

    # -----------------------------------------------------------------------
    # Build report
    # -----------------------------------------------------------------------
    report: dict[str, Any] = {
        "tei_doc_id": tei_doc_id,
        "source_code": source_code,
        "tei_relpath": tei_relpath,
        "segment_count": len(entry_rows),
        "token_count": len(token_rows),
        "ref_count": len(ref_rows),
        "versions": {
            "indexer": INDEXER_VERSION,
            "normalization": NORMALIZATION_VERSION,
            "tokenizer": TOKENIZER_VERSION,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    cmg_commit = get_cmg_commit(repo_root)
    if cmg_commit:
        report["cmg_commit"] = cmg_commit

    if dry_run:
        # Include sample entries
        sample_entries = []
        for row in entry_rows[:5]:
            sid = row["tei_segment_id"]
            # Find corresponding refs
            entry_refs = [
                r for r in ref_rows if r["tei_segment_id"] == sid
            ]
            entry_tokens = [
                t for t in token_rows if t["tei_segment_id"] == sid
            ]
            sample_entries.append({
                "entry": row,
                "refs": entry_refs,
                "token_count": len(entry_tokens),
                "tokens_sample": entry_tokens[:10],
            })
        report["sample_entries"] = sample_entries
        report["dry_run"] = True
        return report

    # -----------------------------------------------------------------------
    # Database writes
    # -----------------------------------------------------------------------
    supabase_url = env_required("SUPABASE_URL")
    service_key = env_required("SUPABASE_SERVICE_ROLE_KEY")
    client = SupabaseRestClient(supabase_url=supabase_url, api_key=service_key)

    # Step 1: Create import_runs row
    import_run = {
        "tei_doc_id": tei_doc_id,
        "indexer_version": INDEXER_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "tokenizer_version": TOKENIZER_VERSION,
        "cmg_commit": cmg_commit,
        "config_path": config.get("config_path", ""),
        "segment_count": len(entry_rows),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    # Upsert import_runs and get back the run id
    status, _headers, body = client._request(
        "POST",
        "/rest/v1/import_runs",
        headers={
            "Prefer": "return=representation",
            "Content-Type": "application/json",
        },
        json_body=[import_run],
    )
    if status < 200 or status >= 300:
        raise RuntimeError(
            f"Failed to create import_runs row: HTTP {status}"
        )
    run_data = json.loads(body.decode("utf-8"))
    run_id = run_data[0]["id"]
    print(f"Created import_run: {run_id}")

    # Step 2: Fetch existing entries for this tei_doc_id to detect hash changes
    existing_entries_raw = client.get_json(
        "/rest/v1/tei_entries",
        query={
            "tei_doc_id": f"eq.{tei_doc_id}",
            "select": "tei_segment_id,raw_hash,is_active",
        },
    )
    existing_by_seg: dict[str, dict] = {}
    if existing_entries_raw:
        for ex in existing_entries_raw:
            existing_by_seg[ex["tei_segment_id"]] = ex

    # Add last_import_run_id to entry rows
    stale_segment_ids: list[str] = []
    for row in entry_rows:
        row["last_import_run_id"] = run_id
        sid = row["tei_segment_id"]
        if sid in existing_by_seg:
            old_hash = existing_by_seg[sid].get("raw_hash")
            if old_hash and old_hash != row["raw_hash"]:
                stale_segment_ids.append(sid)

    # Step 3: Upsert tei_entries
    print(f"Upserting {len(entry_rows)} tei_entries...")
    for batch in chunked(entry_rows, ENTRY_BATCH_SIZE):
        client.upsert(
            "tei_entries", batch,
            on_conflict="tei_doc_id,tei_segment_id",
        )

    # Step 4: Upsert tei_entry_refs
    print(f"Upserting {len(ref_rows)} tei_entry_refs...")
    for batch in chunked(ref_rows, REF_BATCH_SIZE):
        client.upsert(
            "tei_entry_refs", batch,
            on_conflict="tei_doc_id,tei_segment_id,ref_type",
        )

    # Step 5: Upsert tei_tokens in batches
    print(f"Upserting {len(token_rows)} tei_tokens...")
    for batch in chunked(token_rows, TOKEN_BATCH_SIZE):
        client.upsert(
            "tei_tokens", batch,
            on_conflict="tei_doc_id,tei_segment_id,token_index",
        )

    # Step 6: Mark assertions stale for segments whose raw_hash changed
    if stale_segment_ids:
        print(
            f"Marking assertions stale for {len(stale_segment_ids)} "
            f"changed segments..."
        )
        for sid in stale_segment_ids:
            display_id = f"{tei_doc_id}~{sid}"
            try:
                client._request(
                    "PATCH",
                    "/rest/v1/assertions",
                    query={
                        "display_entry_id": f"eq.{display_id}",
                    },
                    headers={
                        "Prefer": "return=minimal",
                        "Content-Type": "application/json",
                    },
                    json_body={"is_stale": True},
                )
            except Exception as e:
                # Non-fatal: assertions table may not exist yet
                print(
                    f"  Warning: could not mark assertions stale for "
                    f"{display_id}: {e}",
                    file=sys.stderr,
                )

    # Step 7: Deactivate unseen segments (C-01 section 9)
    unseen: list[str] = []
    if subset is None:
        # Only deactivate when doing a full run (not subset)
        seen_set = set(seen_segment_ids)
        for sid, ex in existing_by_seg.items():
            if sid not in seen_set and ex.get("is_active", True):
                unseen.append(sid)

        if unseen:
            print(f"Deactivating {len(unseen)} unseen segments...")
            for sid in unseen:
                try:
                    client._request(
                        "PATCH",
                        "/rest/v1/tei_entries",
                        query={
                            "tei_doc_id": f"eq.{tei_doc_id}",
                            "tei_segment_id": f"eq.{sid}",
                        },
                        headers={
                            "Prefer": "return=minimal",
                            "Content-Type": "application/json",
                        },
                        json_body={
                            "is_active": False,
                            "last_import_run_id": run_id,
                        },
                    )
                except Exception as e:
                    print(
                        f"  Warning: could not deactivate {sid}: {e}",
                        file=sys.stderr,
                    )

    # Step 8: Finalize import_runs row
    try:
        client._request(
            "PATCH",
            "/rest/v1/import_runs",
            query={"id": f"eq.{run_id}"},
            headers={
                "Prefer": "return=minimal",
                "Content-Type": "application/json",
            },
            json_body={
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "status": "completed",
                "stale_count": len(stale_segment_ids),
            },
        )
    except Exception as e:
        print(f"Warning: could not finalize import_run: {e}", file=sys.stderr)

    report["import_run_id"] = run_id
    report["stale_count"] = len(stale_segment_ids)
    report["deactivated_count"] = len(unseen)
    print(
        f"Done: {len(entry_rows)} entries, "
        f"{len(token_rows)} tokens, "
        f"{len(stale_segment_ids)} stale, "
        f"{report.get('deactivated_count', 0)} deactivated"
    )
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Index TEI document for Ancient Simples"
    )
    parser.add_argument(
        "--config", required=True, help="Path to TEI doc config YAML"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Output JSON report without writing to database",
    )
    parser.add_argument(
        "--subset",
        help="Path to file listing entry IDs to index (one per line)",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 1

    repo_root = REPO_ROOT
    config = load_config(config_path)

    # Attach config_path to config for provenance
    config["config_path"] = str(config_path)

    # Load subset if specified
    subset: set[str] | None = None
    if args.subset:
        subset_path = Path(args.subset)
        if not subset_path.exists():
            print(f"Subset file not found: {subset_path}", file=sys.stderr)
            return 1
        subset = load_subset(subset_path, config["tei_doc_id"])
        print(f"Subset filter: {len(subset)} segment IDs loaded")

    try:
        report = index_tei(
            config, repo_root, dry_run=args.dry_run, subset=subset,
        )
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        # Print summary report
        print(json.dumps(
            {k: v for k, v in report.items() if k != "sample_entries"},
            indent=2, ensure_ascii=False,
        ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
