#!/usr/bin/env python3
"""Build blinded review packets for vocab extraction accuracy.

Inputs:
- Prep job prompts under a single directory (generated via --prepare-only)
- Model results dirs for three configs (per-entry JSON)

Outputs:
- packets/<packet_id>.md
- blinding_key.json (maps packet_id -> letter -> model_key)

Notes:
- Deterministic shuffling per packet to avoid reviewer bias.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _stable_shuffle(items: list[str], seed: str) -> list[str]:
    # Fisher-Yates using deterministic bytes.
    out = items[:]
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    j = 0
    for i in range(len(out) - 1, 0, -1):
        b = h[j % len(h)]
        j += 1
        k = b % (i + 1)
        out[i], out[k] = out[k], out[i]
    return out


def _extract_section(job_text: str, header: str) -> str | None:
    # Very small parser: find header line and return text until next '## ' header.
    idx = job_text.rfind(header)
    if idx == -1:
        return None
    after = job_text[idx + len(header) :]
    # Split on next markdown header.
    nxt = after.find("\n## ")
    if nxt != -1:
        return after[:nxt].strip("\n")
    return after.strip("\n")


def _parse_authoritative_source_and_text(job_text: str) -> tuple[str, str]:
    block = _extract_section(job_text, "## INPUT (authoritative)")
    if not block:
        raise ValueError("Missing authoritative input section")

    # Find last SOURCE_ID and TEXT:
    sid = None
    text = None
    lines = block.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("SOURCE_ID:"):
            sid = line.split(":", 1)[1].strip()
        if line.strip() == "TEXT:" and i + 1 < len(lines):
            text = "\n".join(lines[i + 1 :]).strip("\n")
            break
    if not sid or text is None:
        raise ValueError("Failed to parse SOURCE_ID/TEXT")
    return sid, text


def _parse_context(job_text: str) -> str:
    block = _extract_section(job_text, "## CONTEXT")
    if not block:
        return "(none)"
    # Keep as-is; reviewers can use it only when text explicitly signals.
    return block.strip("\n")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Build blinded review packets.")
    ap.add_argument("--prep-jobs-dir", required=True, help="Directory containing *.prompt.md job prompts.")
    ap.add_argument("--out-dir", required=True, help="Output directory (will create packets/ and blinding_key.json).")
    ap.add_argument(
        "--ids-file",
        default=None,
        help="Optional ids file to restrict packets (one SOURCE_ID per line).",
    )
    ap.add_argument(
        "--models",
        required=True,
        nargs=3,
        metavar=("KEY=DIR", "KEY=DIR", "KEY=DIR"),
        help="Three model result dirs, like gpt_5_2_high=.../results",
    )
    ap.add_argument(
        "--rubric-path",
        required=True,
        help="Path to rubric markdown (referenced from packets).",
    )
    args = ap.parse_args()

    prep_jobs_dir = Path(args.prep_jobs_dir)
    out_dir = Path(args.out_dir)
    rubric_path = Path(args.rubric_path)

    if not prep_jobs_dir.exists():
        raise SystemExit(f"prep jobs dir not found: {prep_jobs_dir}")
    if not rubric_path.exists():
        raise SystemExit(f"rubric not found: {rubric_path}")

    model_map: dict[str, Path] = {}
    for item in args.models:
        if "=" not in item:
            raise SystemExit(f"Invalid --models item: {item} (expected KEY=DIR)")
        k, v = item.split("=", 1)
        k = k.strip()
        p = Path(v.strip())
        if not p.exists():
            raise SystemExit(f"Model results dir not found for {k}: {p}")
        model_map[k] = p

    if len(model_map) != 3:
        raise SystemExit("Expected exactly 3 model dirs")

    ids_set: set[str] | None = None
    if args.ids_file:
        ids_path = Path(args.ids_file)
        if not ids_path.exists():
            raise SystemExit(f"ids file not found: {ids_path}")
        ids = []
        for line in ids_path.read_text(encoding="utf-8", errors="replace").splitlines():
            v = line.strip()
            if not v or v.startswith("#"):
                continue
            ids.append(v)
        ids_set = set(ids)
        if not ids_set:
            raise SystemExit(f"--ids-file was empty: {ids_path}")

    packets_dir = out_dir / "packets"
    packets_dir.mkdir(parents=True, exist_ok=True)

    blinding_key: dict[str, dict[str, str]] = {}

    prompt_files = sorted(prep_jobs_dir.glob("*.prompt.md"))
    if not prompt_files:
        raise SystemExit(f"No *.prompt.md files under {prep_jobs_dir}")

    model_keys = sorted(model_map.keys())

    for pf in prompt_files:
        job_text = pf.read_text(encoding="utf-8", errors="replace")
        source_id, text = _parse_authoritative_source_and_text(job_text)
        if ids_set is not None and source_id not in ids_set:
            continue
        context = _parse_context(job_text)

        packet_id = source_id  # safe enough for filenames in this repo

        # Deterministically permute model->letter per packet.
        shuffled = _stable_shuffle(model_keys, seed=f"{packet_id}|v1")
        letters = ["A", "B", "C"]
        mapping = {letters[i]: shuffled[i] for i in range(3)}
        blinding_key[packet_id] = mapping

        # Load each model output.
        outputs_by_letter: dict[str, dict] = {}
        for letter, model_key in mapping.items():
            fp = model_map[model_key] / f"{source_id}.json"
            if not fp.exists():
                raise SystemExit(f"Missing model output: {fp}")
            outputs_by_letter[letter] = _load_json(fp)

        md = []
        md.append(f"# Packet: {packet_id}\n")
        md.append("\n## Instructions\n")
        md.append("Score candidates A/B/C using the rubric. Do not try to guess the model.\n")
        md.append(f"Rubric: `{rubric_path}`\n")
        md.append("\n## SOURCE_ID\n")
        md.append(f"`{source_id}`\n")
        md.append("\n## TEXT\n")
        md.append(text.strip() + "\n")
        md.append("\n## CONTEXT\n")
        md.append(context.strip() + "\n")

        for letter in letters:
            md.append(f"\n## Candidate {letter}\n")
            md.append("```json\n")
            md.append(json.dumps(outputs_by_letter[letter], ensure_ascii=False, indent=2))
            md.append("\n```\n")

        (packets_dir / f"{packet_id}.md").write_text("".join(md), encoding="utf-8")

    (out_dir / "blinding_key.json").write_text(
        json.dumps(blinding_key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Wrote packets: {packets_dir}")
    print(f"Wrote blinding key: {out_dir / 'blinding_key.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
