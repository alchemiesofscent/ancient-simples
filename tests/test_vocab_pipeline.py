from __future__ import annotations

import json

from scripts.consolidate_results import consolidate
from scripts.import_vocab_v3 import build_legacy_rows


def test_consolidate_adds_entry_id_alias(tmp_path):
    run_dir = tmp_path / "run"
    results_dir = run_dir / "results"
    results_dir.mkdir(parents=True)
    (results_dir / "A.json").write_text(
        json.dumps(
            {
                "source_id": "A",
                "terms": [],
                "qualities": [],
            }
        ),
        encoding="utf-8",
    )

    summary = consolidate(run_dir)

    assert summary["valid_results"] == 1
    rows = [json.loads(line) for line in (run_dir / "results.jsonl").read_text().splitlines()]
    assert rows == [{"entry_id": "A", "qualities": [], "source_id": "A", "terms": []}]


def test_legacy_import_uses_entry_id_aliases():
    result = {
        "source_id": "OLD-1",
        "terms": [
            {
                "label": "SUBSTANCE",
                "lemma_gr": "ἄγνος",
                "display": "ἄγνον",
                "confidence": 0.9,
            }
        ],
        "qualities": [
            {
                "axis": "HOT",
                "degree": 3,
                "intensity": "none",
                "hedge": "none",
                "evidence_display": "θερμὸν",
                "evidence_normalized": "θερμον",
                "applies_to": {
                    "kind": "SUBSTANCE",
                    "lemma_normalized": "αγνος",
                    "substance_lemma_normalized": None,
                    "part_lemma_normalized": None,
                },
                "confidence": 0.95,
            }
        ],
    }

    report, forms, links, assertions = build_legacy_rows(
        [result],
        existing_entry_ids={"NEW-1"},
        entry_id_aliases={"OLD-1": "NEW-1"},
    )

    assert report.entries_processed == 1
    assert report.entries_skipped_missing_legacy == 0
    assert forms[0]["form_normalized"] == "αγνος"
    assert links[0]["entry_id"] == "NEW-1"
    assert assertions[0]["entry_id"] == "NEW-1"
    assert assertions[0]["payload"]["degree"] == "3"
