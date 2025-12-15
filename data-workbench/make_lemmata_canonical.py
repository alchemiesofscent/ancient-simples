#!/usr/bin/env python3
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class CanonicalRow:
    canonical_lemma_id: str
    headword_normalized: str
    member_lemma_ids: str
    notes: str


def lemma_id_sort_key(lemma_id: str) -> int:
    # Expect L###, but be defensive.
    s = str(lemma_id).strip()
    if len(s) >= 2 and (s[0] in {"L", "l"}):
        digits = "".join(ch for ch in s[1:] if ch.isdigit())
        if digits:
            return int(digits)
    return 10**9


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workbench = repo_root / "data-workbench"
    lemmata_path = workbench / "lemmata.csv"
    out_csv_path = workbench / "lemmata_canonical.csv"
    out_qc_path = workbench / "lemmata_canonical_qc.md"

    if not lemmata_path.exists():
        raise SystemExit(f"Missing input: {lemmata_path}")

    df = pd.read_csv(lemmata_path, dtype=str).fillna("")
    required = {"lemma_id", "headword_normalized"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"lemmata.csv missing columns: {sorted(missing)}")

    groups = df.groupby("headword_normalized", dropna=False)["lemma_id"].apply(list)
    collision_groups = {k: v for k, v in groups.items() if len(v) >= 2 and str(k).strip() != ""}

    rows: list[CanonicalRow] = []
    for head_norm, ids in collision_groups.items():
        sorted_ids = sorted((i for i in ids if str(i).strip()), key=lemma_id_sort_key)
        if not sorted_ids:
            continue
        canonical = sorted_ids[0]
        rows.append(
            CanonicalRow(
                canonical_lemma_id=canonical,
                headword_normalized=str(head_norm),
                member_lemma_ids=",".join(sorted_ids),
                notes="normalised collision group",
            )
        )

    out_df = pd.DataFrame([r.__dict__ for r in rows])[
        ["canonical_lemma_id", "headword_normalized", "member_lemma_ids", "notes"]
    ].sort_values(by="canonical_lemma_id", key=lambda s: s.map(lemma_id_sort_key))

    out_df.to_csv(
        out_csv_path,
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    # QC report
    utc_now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    total_groups = len(out_df)
    involved = 0
    group_sizes: list[tuple[str, int, str]] = []
    for _, r in out_df.iterrows():
        members = [m for m in str(r["member_lemma_ids"]).split(",") if m]
        involved += len(members)
        group_sizes.append((str(r["headword_normalized"]), len(members), str(r["member_lemma_ids"])))

    lines: list[str] = []
    lines.append("# lemmata_canonical.csv QC report")
    lines.append("")
    lines.append(f"- Generated: `{utc_now}`")
    lines.append(f"- Input: `{lemmata_path.name}`")
    lines.append(f"- Collision groups: **{total_groups}**")
    lines.append(f"- Total lemmata involved: **{involved}**")
    lines.append("")
    lines.append("## Top 20 largest groups")
    for head_norm, size, members in sorted(group_sizes, key=lambda t: (-t[1], t[0]))[:20]:
        lines.append(f"- `{head_norm}`: {size} ({members})")
    lines.append("")

    out_qc_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    print(f"Wrote {out_csv_path} ({len(out_df)} rows)")
    print(f"Wrote {out_qc_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

