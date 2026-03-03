#!/usr/bin/env python3
"""Aggregate blinded accuracy reviews.

Inputs:
- blinding_key.json: {packet_id: {A: model_key, B: model_key, C: model_key}}
- reviews/*.jsonl: each line is a JSON object:
  {
    "packet_id": "...",
    "ranked": ["A","B","C"],
    "scores": {
      "A": {"precision":0-5, "coverage":0-5, "labeling":0-5, "lemma":0-5, "linking":0-5, "qualities":0-5},
      ...
    },
    "notes": {"A":"...", "B":"...", "C":"..."}
  }

Outputs:
- summary.json
- summary.md
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


DIMENSIONS = ["precision", "coverage", "labeling", "lemma", "linking", "qualities"]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_jsonl(path: Path):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        yield json.loads(line)


def main() -> int:
    ap = argparse.ArgumentParser(description="Aggregate vocab accuracy reviews.")
    ap.add_argument("--blinding-key", required=True)
    ap.add_argument("--reviews-dir", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    key_path = Path(args.blinding_key)
    reviews_dir = Path(args.reviews_dir)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)

    blinding = _load_json(key_path)

    review_files = sorted(reviews_dir.glob("*.jsonl"))
    if not review_files:
        raise SystemExit(f"No review files found in {reviews_dir}")

    # Accumulate
    sums = defaultdict(lambda: Counter())  # model_key -> dim -> total
    counts = defaultdict(lambda: Counter())
    wins = Counter()  # model_key -> #1 rank count
    rank_counts = defaultdict(lambda: Counter())  # model_key -> rank position counts

    n_reviews = 0
    missing_packets = 0

    for rf in review_files:
        for obj in _iter_jsonl(rf):
            n_reviews += 1
            packet_id = obj.get("packet_id")
            if packet_id not in blinding:
                missing_packets += 1
                continue
            mapping = blinding[packet_id]

            ranked = obj.get("ranked") or []
            scores = obj.get("scores") or {}

            # Ranking
            if ranked and isinstance(ranked, list) and len(ranked) == 3:
                for idx, letter in enumerate(ranked):
                    mk = mapping.get(letter)
                    if mk:
                        rank_counts[mk][str(idx + 1)] += 1
                top = mapping.get(ranked[0])
                if top:
                    wins[top] += 1

            # Scores
            for letter, sc in scores.items():
                mk = mapping.get(letter)
                if not mk or not isinstance(sc, dict):
                    continue
                for dim in DIMENSIONS:
                    v = sc.get(dim)
                    if v is None:
                        continue
                    try:
                        iv = int(v)
                    except Exception:
                        continue
                    sums[mk][dim] += iv
                    counts[mk][dim] += 1

    models = sorted(set(sums.keys()) | set(wins.keys()) | set(rank_counts.keys()))
    summary = {
        "n_reviews": n_reviews,
        "missing_packets": missing_packets,
        "models": {},
    }

    for mk in models:
        model_entry = {
            "avg": {},
            "wins": int(wins.get(mk, 0)),
            "rank_counts": {k: int(v) for k, v in rank_counts[mk].items()},
        }
        for dim in DIMENSIONS:
            c = counts[mk][dim]
            model_entry["avg"][dim] = (sums[mk][dim] / c) if c else None
        # overall average across dims (where present)
        vals = [model_entry["avg"][d] for d in DIMENSIONS if model_entry["avg"][d] is not None]
        model_entry["avg"]["overall"] = (sum(vals) / len(vals)) if vals else None
        summary["models"][mk] = model_entry

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Markdown
    lines = []
    lines.append("# Vocab Accuracy Eval Summary\n\n")
    lines.append(f"- Reviews: {n_reviews}\n")
    lines.append(f"- Unknown packet_ids: {missing_packets}\n\n")

    lines.append("## Model Averages (0-5)\n\n")
    lines.append("| model_key | overall | precision | coverage | labeling | lemma | linking | qualities | wins |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for mk in models:
        avg = summary["models"][mk]["avg"]
        def fmt(x):
            return "" if x is None else f"{x:.2f}"
        lines.append(
            "| "
            + mk
            + " | "
            + fmt(avg.get("overall"))
            + " | "
            + fmt(avg.get("precision"))
            + " | "
            + fmt(avg.get("coverage"))
            + " | "
            + fmt(avg.get("labeling"))
            + " | "
            + fmt(avg.get("lemma"))
            + " | "
            + fmt(avg.get("linking"))
            + " | "
            + fmt(avg.get("qualities"))
            + " | "
            + str(summary["models"][mk]["wins"])
            + " |\n"
        )

    out_md.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
