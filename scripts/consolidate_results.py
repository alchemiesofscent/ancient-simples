#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_result(path: Path) -> dict[str, Any] | None:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    source_id = (obj.get("source_id") or obj.get("entry_id") or "").strip()
    if not source_id:
        return None
    obj["source_id"] = source_id
    obj.setdefault("entry_id", source_id)
    return obj


def consolidate(run_dir: Path, *, out_path: Path | None = None) -> dict[str, Any]:
    results_dir = run_dir / "results"
    if not results_dir.exists():
        raise SystemExit(f"Missing results dir: {results_dir}")

    out_path = out_path or (run_dir / "results.jsonl")
    valid: list[dict[str, Any]] = []
    invalid: list[str] = []

    for path in sorted(results_dir.glob("*.json"), key=lambda p: p.stem):
        obj = _load_result(path)
        if obj is None:
            invalid.append(str(path))
            continue
        valid.append(obj)

    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as out:
        for obj in valid:
            out.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
    tmp_path.replace(out_path)

    return {
        "run_dir": str(run_dir),
        "results_dir": str(results_dir),
        "out_path": str(out_path),
        "valid_results": len(valid),
        "invalid_results": len(invalid),
        "invalid_examples": invalid[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidate per-entry vocab JSON results into JSONL.")
    parser.add_argument("run_dir", type=Path, help="Run directory containing results/*.json")
    parser.add_argument("--out", type=Path, default=None, help="Output JSONL path")
    args = parser.parse_args()

    summary = consolidate(args.run_dir, out_path=args.out)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["invalid_results"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
