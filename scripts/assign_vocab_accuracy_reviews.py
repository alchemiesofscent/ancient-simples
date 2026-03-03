#!/usr/bin/env python3
"""Create reviewer assignments for blinded packets.

Default policy: 2 reviews per packet.
- Pass 1: chunk packets sequentially across reviewers.
- Pass 2: rotate packet order by a fixed offset, then chunk again.

Outputs:
- assignments/reviewer_XX.txt (list of packet paths)
- assignments/manifest.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Assign packets to reviewers.")
    ap.add_argument("--packets-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--reviewers", type=int, default=10)
    ap.add_argument("--reviews-per-packet", type=int, default=2)
    ap.add_argument("--rotate", type=int, default=5, help="Rotation offset for pass 2")
    args = ap.parse_args()

    packets_dir = Path(args.packets_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    packets = sorted(packets_dir.glob("*.md"))
    if not packets:
        raise SystemExit(f"No packets found in {packets_dir}")

    reviewers = int(args.reviewers)
    rpp = int(args.reviews_per_packet)
    if reviewers <= 0:
        raise SystemExit("--reviewers must be > 0")
    if rpp not in (1, 2):
        raise SystemExit("Only 1 or 2 reviews-per-packet supported")

    assignments: dict[str, list[str]] = {f"reviewer_{i+1:02d}": [] for i in range(reviewers)}

    def assign_pass(packets_list: list[Path], pass_name: str) -> None:
        # chunk size so every reviewer gets roughly equal
        per = (len(packets_list) + reviewers - 1) // reviewers
        idx = 0
        for i in range(reviewers):
            chunk = packets_list[idx : idx + per]
            idx += per
            key = f"reviewer_{i+1:02d}"
            assignments[key].extend([str(p) for p in chunk])

    # Pass 1
    assign_pass(packets, "pass1")

    if rpp == 2:
        rot = int(args.rotate) % len(packets)
        rotated = packets[rot:] + packets[:rot]
        assign_pass(rotated, "pass2")

    # Write files
    manifest = {
        "packets_dir": str(packets_dir),
        "reviewers": reviewers,
        "reviews_per_packet": rpp,
        "rotate": int(args.rotate),
        "assignments": assignments,
    }

    for reviewer, paths in assignments.items():
        (out_dir / f"{reviewer}.txt").write_text("\n".join(paths) + "\n", encoding="utf-8")

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote assignments: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
