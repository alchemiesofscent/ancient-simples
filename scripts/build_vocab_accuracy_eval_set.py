#!/usr/bin/env python3
"""Build a deterministic eval set for vocab extraction accuracy.

Inputs:
- data-workbench/entries.csv (text)
- outputs/vocab_entries_v3/entries_full_v3/results/*.json (baseline outputs to drive feature selection)

Output:
- A newline-delimited ids file

Design goals:
- Deterministic selection
- Coverage of key features (qualities, substance_part, place variants, linked actions)
- Balanced across sources
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Entry:
    entry_id: str
    source: str
    word_count: int


def _load_entries_csv(path: Path) -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = (row.get("entry_id") or "").strip()
            if not eid:
                continue
            src = (row.get("source") or "").strip()
            wc_raw = (row.get("word_count") or "").strip()
            try:
                wc = int(wc_raw)
            except Exception:
                wc = 10**9
            out[eid] = Entry(entry_id=eid, source=src, word_count=wc)
    return out


def _load_baseline_obj(results_dir: Path, entry_id: str) -> dict | None:
    fp = results_dir / f"{entry_id}.json"
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None


def _has_qualities(obj: dict) -> bool:
    return bool(obj.get("qualities"))


def _has_substance_part(obj: dict) -> bool:
    for t in obj.get("terms") or []:
        if t.get("label") == "SUBSTANCE_PART":
            return True
    return False


def _has_place_variant(obj: dict) -> bool:
    for t in obj.get("terms") or []:
        if t.get("variant_place_lemma_normalized"):
            return True
    for q in obj.get("qualities") or []:
        if q.get("variant_place_lemma_normalized"):
            return True
    return False


def _has_linked_action(obj: dict) -> bool:
    for t in obj.get("terms") or []:
        if t.get("label") not in ("PROCESS", "ADMINISTRATION", "QUALITY_PROPERTY"):
            continue
        applies_to = t.get("applies_to") or {}
        if applies_to.get("kind") and applies_to.get("kind") != "UNSPECIFIED":
            return True
    for q in obj.get("qualities") or []:
        applies_to = q.get("applies_to") or {}
        if applies_to.get("kind") and applies_to.get("kind") != "UNSPECIFIED":
            return True
    return False


def _pick_smallest_by_wc(cands: list[Entry], n: int) -> list[str]:
    cands_sorted = sorted(cands, key=lambda e: (e.word_count, e.entry_id))
    return [e.entry_id for e in cands_sorted[:n]]


def _fill_diverse_by_wc(cands: list[Entry], n: int, already: set[str]) -> list[str]:
    # Even-ish sampling across the sorted list.
    c = [e for e in sorted(cands, key=lambda e: (e.word_count, e.entry_id)) if e.entry_id not in already]
    if not c or n <= 0:
        return []
    step = max(1, len(c) // n)
    out: list[str] = []
    for i in range(0, len(c), step):
        if len(out) >= n:
            break
        out.append(c[i].entry_id)
    return out[:n]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a deterministic accuracy eval set.")
    ap.add_argument(
        "--entries",
        default=str(_REPO_ROOT / "data-workbench/entries.csv"),
        help="entries.csv path",
    )
    ap.add_argument(
        "--baseline-results",
        default=str(_REPO_ROOT / "outputs/vocab_entries_v3/entries_full_v3/results"),
        help="Baseline per-entry results dir",
    )
    ap.add_argument(
        "--out",
        required=True,
        help="Write ids (one per line) to this path",
    )
    ap.add_argument(
        "--per-source",
        type=int,
        default=10,
        help="How many ids per source (GAL_SMT/ORIB_CM/GAL_ALIM)",
    )
    args = ap.parse_args()

    entries_path = Path(args.entries)
    results_dir = Path(args.baseline_results)
    out_path = Path(args.out)

    entries = _load_entries_csv(entries_path)

    # Sources we can evaluate from current baseline outputs.
    sources = [
        ("GAL_SMT", "GAL_SMT-"),
        ("ORIB_CM", "ORIB_CM-"),
        ("GAL_ALIM", "GAL_ALIM-"),
    ]

    selected: list[str] = []

    for source_code, prefix in sources:
        # Candidate entries must have baseline results.
        cands: list[Entry] = []
        feats: dict[str, list[Entry]] = defaultdict(list)

        for eid, e in entries.items():
            if not eid.startswith(prefix):
                continue
            obj = _load_baseline_obj(results_dir, eid)
            if not obj:
                continue
            cands.append(e)
            if _has_qualities(obj):
                feats["qualities"].append(e)
            if _has_substance_part(obj):
                feats["substance_part"].append(e)
            if _has_place_variant(obj):
                feats["place_variant"].append(e)
            if _has_linked_action(obj):
                feats["linked_action"].append(e)

        if not cands:
            raise SystemExit(f"No baseline results found for {source_code} ({prefix}).")

        # Feature-first selection (smallest word_count to keep eval feasible), then fill.
        chosen: list[str] = []
        chosen_set: set[str] = set()

        def choose(feature: str, k: int) -> None:
            picks = _pick_smallest_by_wc(feats.get(feature, []), k)
            for pid in picks:
                if pid not in chosen_set:
                    chosen.append(pid)
                    chosen_set.add(pid)

        choose("qualities", 3)
        choose("substance_part", 3)
        choose("place_variant", 2)
        choose("linked_action", 2)

        # Fill up to per-source with diverse sampling by word_count.
        need = int(args.per_source) - len(chosen)
        if need > 0:
            chosen.extend(_fill_diverse_by_wc(cands, need, chosen_set))

        chosen = chosen[: int(args.per_source)]
        selected.extend(chosen)

    # Deterministic ordering for file.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(selected) + "\n", encoding="utf-8")
    print(f"Wrote {len(selected)} ids to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
