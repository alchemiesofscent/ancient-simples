from __future__ import annotations

import json

from scripts.consolidate_results import consolidate
from scripts.build_vocab_frontend_index import LABELS, build_index
from scripts.import_vocab_v3 import build_legacy_rows
from scripts.make_entries_paul import build_rows as build_paul_rows
from scripts.make_entries_paul import parse_edition_pages


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


def test_paul_parse_edition_pages():
    assert parse_edition_pages("2.186-187") == ("2", "186", "187")
    assert parse_edition_pages("2.274") == ("2", "274", "274")
    assert parse_edition_pages("") == ("", "", "")


def test_paul_entries_builder_generates_legacy_entry_rows():
    rows = build_paul_rows(
        [
            {
                "row_idx": "0",
                "book": "7",
                "chapter": "3",
                "lemma_gr": "ἄψινθος",
                "section_gr": "Περὶ ἀψίνθου",
                "entry_gr": "Ἄψινθος θερμή ἐστι κατὰ τὴν πρώτην τάξιν.",
                "entry_en": "",
                "edition_pages": "2.186-187",
                "derived_from": "",
            }
        ],
        source="PAUL_AEG",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["entry_id"] == "PAUL_AEG-7.3.1"
    assert row["source"] == "PAUL_AEG"
    assert row["ref"] == "7.3.1"
    assert row["chapter_title_gr"] == "Περὶ ἀψίνθου"
    assert row["greek_normalized"] == "αψινθος θερμη εστι κατα την πρωτην ταξιν."
    assert row["translation"] == ""
    assert row["trans_status"] == "draft"
    assert row["e_vol"] == "2"
    assert row["e_page_start"] == "186"
    assert row["e_page_end"] == "187"
    assert row["notes"].startswith("paul_row=0; lemma_gr=ἄψινθος; edition_pages=2.186-187")


def test_vocab_frontend_index_links_all_facet_categories(tmp_path):
    run_dir = tmp_path / "results"
    run_dir.mkdir()
    (run_dir / "AET_LM-1.1.json").write_text(
        json.dumps(
            {
                "source_id": "AET_LM-1.1",
                "terms": [
                    {
                        "label": "SUBSTANCE",
                        "display": "ἄγνος",
                        "lemma_gr": "ἄγνος",
                        "lemma_normalized": "αγνος",
                        "confidence": 0.95,
                    },
                    {
                        "label": "CONDITION",
                        "display": "φλεγμονή",
                        "lemma_gr": "φλεγμονή",
                        "lemma_normalized": "φλεγμονη",
                        "confidence": 0.8,
                    },
                    {
                        "label": "ADMINISTRATION",
                        "display": "πίνεται",
                        "lemma_gr": "πίνειν",
                        "lemma_normalized": "πινειν",
                        "confidence": 0.82,
                    },
                    {
                        "label": "PREPARATION",
                        "display": "ἀφέψημα",
                        "lemma_gr": "ἀφέψημα",
                        "lemma_normalized": "αφεψημα",
                        "confidence": 0.86,
                    },
                    {
                        "label": "PROCESS",
                        "display": "ἕψειν",
                        "lemma_gr": "ἕψω",
                        "lemma_normalized": "εψω",
                        "confidence": 0.78,
                    },
                    {
                        "label": "PLACE",
                        "display": "Αἴγυπτος",
                        "lemma_gr": "Αἴγυπτος",
                        "lemma_normalized": "αιγυπτος",
                        "confidence": 0.75,
                    },
                    {
                        "label": "QUALITY_PROPERTY",
                        "display": "θερμός",
                        "lemma_gr": "θερμός",
                        "lemma_normalized": "θερμος",
                        "confidence": 0.9,
                    },
                    {
                        "label": "TOOL_CONTAINER",
                        "display": "ἀγγεῖον",
                        "lemma_gr": "ἀγγεῖον",
                        "lemma_normalized": "αγγειον",
                        "confidence": 0.76,
                    },
                    {
                        "label": "PART",
                        "display": "ῥίζα",
                        "lemma_gr": "ῥίζα",
                        "lemma_normalized": "ριζα",
                        "confidence": 0.83,
                    },
                    {
                        "label": "APPLICATION_SITE",
                        "display": "δέρμα",
                        "lemma_gr": "δέρμα",
                        "lemma_normalized": "δερμα",
                        "confidence": 0.81,
                    },
                ],
                "qualities": [
                    {
                        "axis": "HOT",
                        "degree": 3,
                        "evidence_display": "θερμὸν κατὰ τὴν τρίτην τάξιν",
                        "applies_to": {
                            "kind": "SUBSTANCE",
                            "lemma_normalized": "αγνος",
                            "substance_lemma_normalized": None,
                            "part_lemma_normalized": None,
                        },
                        "confidence": 0.9,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    index = build_index([run_dir])

    assert index["labels"] == LABELS
    assert index["stats"]["simples"] == 1
    simple = index["simples"][0]
    assert simple["lemma_normalized"] == "αγνος"
    assert simple["qualities"][0]["axis"] == "HOT"
    assert simple["qualities"][0]["degree"] == "3"
    for label in [
        "CONDITION",
        "ADMINISTRATION",
        "PREPARATION",
        "PROCESS",
        "PLACE",
        "QUALITY_PROPERTY",
        "TOOL_CONTAINER",
        "PART",
        "APPLICATION_SITE",
    ]:
        assert simple["facets"][label], label
