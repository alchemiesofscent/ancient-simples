#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def _term_has_place(term: dict) -> bool:
    return bool(term.get("variant_place_lemma_normalized"))


def _term_is_substance_part(term: dict) -> bool:
    return term.get("label") == "SUBSTANCE_PART"


def _term_is_linked_action(term: dict) -> bool:
    if term.get("label") not in ("PROCESS", "ADMINISTRATION"):
        return False
    applies_to = term.get("applies_to") or {}
    return applies_to.get("kind") not in (None, "UNSPECIFIED")


def pick_ids(results_dir: Path, prefix: str, n: int) -> list[str]:
    files = sorted(results_dir.glob(f"{prefix}*.json"))
    if not files:
        raise SystemExit(f"No result files found for prefix {prefix!r} under {results_dir}")

    parsed: list[tuple[str, dict]] = []
    for fp in files:
        obj = json.loads(fp.read_text(encoding="utf-8"))
        sid = obj.get("source_id") or fp.stem
        parsed.append((sid, obj))

    # Deterministically choose feature-covering exemplars first.
    chosen: list[str] = []
    chosen_set: set[str] = set()

    def choose_first(predicate) -> None:
        for sid, obj in parsed:
            if sid in chosen_set:
                continue
            if predicate(obj):
                chosen.append(sid)
                chosen_set.add(sid)
                return

    choose_first(lambda o: bool(o.get("qualities")))  # has Galenic qualities
    choose_first(lambda o: any(_term_is_substance_part(t) for t in o.get("terms", [])))
    choose_first(lambda o: any(_term_has_place(t) for t in o.get("terms", [])))
    choose_first(lambda o: any(_term_is_linked_action(t) for t in o.get("terms", [])))

    # Fill remaining slots by evenly sampling the sorted list.
    remaining = max(0, n - len(chosen))
    if remaining:
        sids = [sid for sid, _ in parsed if sid not in chosen_set]
        if sids:
            step = max(1, len(sids) // remaining)
            for i in range(0, len(sids), step):
                if len(chosen) >= n:
                    break
                sid = sids[i]
                if sid not in chosen_set:
                    chosen.append(sid)
                    chosen_set.add(sid)

    return sorted(chosen)[:n]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Pick a deterministic sample of SOURCE_IDs from an existing results directory."
    )
    ap.add_argument("--results-dir", required=True, help="Directory containing per-entry *.json results.")
    ap.add_argument("--prefix", required=True, help="SOURCE_ID prefix to sample (e.g. GAL_SMT-).")
    ap.add_argument("--n", type=int, default=10, help="Number of ids to pick.")
    ap.add_argument("--out", required=True, help="Write ids (one per line) to this file.")
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ids = pick_ids(results_dir, args.prefix, int(args.n))
    out_path.write_text("\n".join(ids) + "\n", encoding="utf-8")
    print(f"Wrote {len(ids)} ids to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

