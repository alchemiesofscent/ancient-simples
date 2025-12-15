#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"

    preparations_csv_path = workbench / "preparations.csv"
    out_md_path = workbench / "preparations_diff_report.md"

    if not preparations_csv_path.exists():
        raise SystemExit(f"Missing {preparations_csv_path}")

    df = pd.read_csv(preparations_csv_path, dtype=str).fillna("")

    utc_now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines: list[str] = []
    lines.append("# preparations.csv update report")
    lines.append("")
    lines.append(f"- Generated: `{utc_now}`")
    lines.append("")
    lines.append("## Current controlled vocabulary")
    for _, r in df.iterrows():
        lines.append(
            f"- `{r['prep_id']}` {r['greek']} — {r['english']} (scope: {r['scope']})"
        )
    lines.append("")
    ids = set(df["prep_id"].astype(str).tolist())
    lines.append("## Notes")
    if {"PR003", "PR004"} <= ids:
        lines.append("- Includes PR003 (ἕψησις) and PR004 (πεπλυμένος) as promoted preparation/process terms.")
    else:
        lines.append("- _(none)_")
    lines.append("")
    lines.append("## Matching policy")
    lines.append(
        "- `entry_preparations.csv` linking uses strict tokenization + normalization + exact token match against explicit controlled forms per preparation."
    )
    lines.append("")
    lines.append("## Exclusions")
    lines.append(
        "- `ωμοτριβες`: lexicalized oil-type qualifier (not a preparation/state in this corpus)."
    )
    lines.append(
        "- `ξηρα`: lexicalized subtype adjective in resin/oil naming (e.g., πιτυινη ἡ ξηρά), not a generic drying preparation/state."
    )
    lines.append("")

    out_md_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Wrote {out_md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
