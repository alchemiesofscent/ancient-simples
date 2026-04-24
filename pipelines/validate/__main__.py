#!/usr/bin/env python3
"""Unified validation entry point.

Usage: python -m pipelines.validate [--data] [--tei] [--all]

Runs the requested validators. Defaults to --data if no flags given.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_data_validate() -> int:
    """Run CSV data validation (scripts/validate_data.py)."""
    return subprocess.call(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_data.py")]
    )


def run_tei_validate() -> int:
    """Run TEI structure validation (scripts/validate_tei.py)."""
    return subprocess.call(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_tei.py")]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Ancient Simples validation suite")
    parser.add_argument("--data", action="store_true", help="Validate CSV data")
    parser.add_argument("--tei", action="store_true", help="Validate TEI structure")
    parser.add_argument("--all", action="store_true", help="Run all validators")
    args = parser.parse_args()

    # Default to --data if nothing specified
    if not (args.data or args.tei or args.all):
        args.data = True

    results: list[tuple[str, int]] = []

    if args.data or args.all:
        print("=== CSV data validation ===")
        rc = run_data_validate()
        results.append(("data", rc))

    if args.tei or args.all:
        print("=== TEI structure validation ===")
        rc = run_tei_validate()
        results.append(("tei", rc))

    failed = [name for name, rc in results if rc != 0]
    if failed:
        print(f"\nFAILED: {', '.join(failed)}")
        return 1

    print(f"\nAll {len(results)} validator(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
