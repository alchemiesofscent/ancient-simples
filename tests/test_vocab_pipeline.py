from __future__ import annotations

import json

from scripts.consolidate_results import consolidate
from scripts.build_simple_name_relation_candidates import candidate_rows, choose_sample
from scripts.build_simples_public_index import build_index as build_simples_public_index
from scripts.build_simples_registry import build_registry
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


def test_simples_registry_keeps_run_and_source_metadata(tmp_path):
    result_dir = tmp_path / "results"
    result_dir.mkdir()
    (result_dir / "AET_LM-1.1.json").write_text(
        json.dumps(
            {
                "source_id": "AET_LM-1.1",
                "terms": [
                    {
                        "label": "SUBSTANCE",
                        "display": "ἄγνος",
                        "lemma_gr": "ἄγνος",
                        "lemma_normalized": "αγνος",
                        "normalized": "αγνος",
                        "is_multiword": False,
                        "head_lemma_normalized": None,
                        "substance_lemma_normalized": None,
                        "part_lemma_normalized": None,
                        "variant_place_lemma_normalized": None,
                        "applies_to": {
                            "kind": "UNSPECIFIED",
                            "lemma_normalized": None,
                            "substance_lemma_normalized": None,
                            "part_lemma_normalized": None,
                        },
                        "confidence": 0.95,
                        "lemma_confidence": 0.95,
                    }
                ],
                "qualities": [],
            }
        ),
        encoding="utf-8",
    )
    entry_csv = tmp_path / "entries.csv"
    entry_csv.write_text(
        "entry_id,source,ref,chapter_title_gr,greek\n"
        "AET_LM-1.1,AET_LM,1.1,περὶ ἄγνου,ἄγνος θερμός\n",
        encoding="utf-8",
    )
    config = {
        "included_runs": [
            {
                "run_id": "test_run",
                "result_dir": str(result_dir),
                "complete": True,
            }
        ],
        "entry_csvs": [str(entry_csv)],
        "author_groups": [
            {
                "author_group": "Aetius",
                "source_codes": ["AET_LM"],
            }
        ],
        "future_corpora": [
            {
                "label": "Aetius 3-4",
                "expected_source_codes": ["AET_LM"],
            }
        ],
    }

    terms, occurrences, forms, manifest = build_registry(config)

    assert terms[0]["term_key"] == "αγνος"
    assert terms[0]["text_sources"] == "AET_LM"
    assert terms[0]["result_runs"] == "test_run"
    assert occurrences[0]["text_source"] == "AET_LM"
    assert occurrences[0]["author_group"] == "Aetius"
    assert occurrences[0]["result_run"] == "test_run"
    assert forms[0]["form_display"] == "ἄγνος"
    assert manifest["counts"]["sources"] == {"AET_LM": 1}
    assert manifest["future_corpora"][0]["label"] == "Aetius 3-4"


def test_name_relation_candidate_sample_includes_trigger_and_control():
    entries = {
        "AET_LM-1.1": {
            "entry_id": "AET_LM-1.1",
            "ref": "1.1",
            "chapter_title_gr": "περὶ ἄγνου ἢ λύγου",
            "greek": "ἄγνος ἢ λύγος θερμός.",
            "greek_normalized": "αγνος η λυγος θερμος.",
        },
        "AET_LM-1.2": {
            "entry_id": "AET_LM-1.2",
            "ref": "1.2",
            "chapter_title_gr": "περὶ ἀλόης",
            "greek": "ἀλόη ξηραίνει.",
            "greek_normalized": "αλοη ξηραινει.",
        },
    }
    by_entry = {
        "AET_LM-1.1": [
            {
                "term_key": "αγνος",
                "display": "ἄγνος",
                "label": "SUBSTANCE",
                "head_lemma_normalized": "",
                "variant_place_lemma_normalized": "",
            },
            {
                "term_key": "λυγος",
                "display": "λύγος",
                "label": "SUBSTANCE",
                "head_lemma_normalized": "",
                "variant_place_lemma_normalized": "",
            },
        ],
        "AET_LM-1.2": [
            {
                "term_key": "αλοη",
                "display": "ἀλόη",
                "label": "SUBSTANCE",
                "head_lemma_normalized": "",
                "variant_place_lemma_normalized": "",
            }
        ],
    }

    sample = choose_sample(entries, by_entry, {"AET_LM": "Aetius"}, per_author=2)
    rows, packets, counts = candidate_rows(sample)

    assert [item["entry_id"] for item in sample] == ["AET_LM-1.1", "AET_LM-1.2"]
    assert any(row["candidate_method"] == "heading_eta" for row in rows)
    assert any(row["candidate_method"] == "control_no_trigger" for row in rows)
    assert rows[0]["review_status"] == "pending_llm_review"
    assert packets[0]["candidate_terms"][0]["term_key"] == "αγνος"
    assert counts["sample_Aetius"] == 2


def test_simples_public_index_merges_registry_review_and_quality_data(tmp_path):
    workbench = tmp_path / "simples"
    workbench.mkdir()
    (workbench / "simple_terms_v0.csv").write_text(
        "term_key,preferred_display,lemma_normalized,labels,is_multiword,head_lemma_normalized,variant_place_lemma_normalized,source_count,entry_count,occurrence_count,text_sources,author_groups,result_runs,confidence_avg,status\n"
        "αγνος,ἄγνος,αγνος,SUBSTANCE:1,false,,,1,1,1,AET_LM,Aetius,test_run,0.950,draft\n",
        encoding="utf-8",
    )
    (workbench / "simple_term_forms_v0.csv").write_text(
        "term_key,form_display,form_normalized,count,entry_count,text_sources,author_groups\n"
        "αγνος,ἄγνος,αγνος,1,1,AET_LM,Aetius\n",
        encoding="utf-8",
    )
    (workbench / "simple_term_occurrences_v0.csv").write_text(
        "occurrence_id,term_key,entry_id,text_source,author_group,result_run,entry_ref,chapter_title_gr,display,lemma_gr,label,normalized,lemma_normalized,is_multiword,head_lemma_normalized,substance_lemma_normalized,part_lemma_normalized,variant_place_lemma_normalized,confidence,lemma_confidence,result_file,applies_to_kind,applies_to_lemma_normalized,applies_to_substance_lemma_normalized,applies_to_part_lemma_normalized\n"
        "test_run:AET_LM-1.1:0,αγνος,AET_LM-1.1,AET_LM,Aetius,test_run,1.1,περὶ ἄγνου,ἄγνος,ἄγνος,SUBSTANCE,αγνος,αγνος,false,,,,,0.950,0.950,test.json,UNSPECIFIED,,,\n",
        encoding="utf-8",
    )
    (workbench / "simple_name_relation_candidates.csv").write_text(
        "candidate_id,author_group,entry_id,text_source,sample_type,candidate_method,trigger_pattern,left_term_key,left_display,right_term_key,right_display,relation_hint,evidence_display,review_status,review_confidence,review_note\n"
        "SNRC-00001,Aetius,AET_LM-1.1,AET_LM,trigger,heading_eta,,αγνος,ἄγνος,λυγος,λύγος,unreviewed,περὶ ἄγνου ἢ λύγου,pending_llm_review,,\n",
        encoding="utf-8",
    )
    (workbench / "simple_name_relations_pilot.csv").write_text(
        "candidate_id,entry_id,text_source,author_group,left_term_key,right_term_key,relation_type,evidence_display,review_status,review_confidence,reviewer,review_note\n"
        "SNRC-00001,AET_LM-1.1,AET_LM,Aetius,αγνος,λυγος,unreviewed,περὶ ἄγνου ἢ λύγου,pending_llm_review,,,\n",
        encoding="utf-8",
    )
    (workbench / "simple_registry_manifest.json").write_text(
        json.dumps({"counts": {"terms": 1, "occurrences": 1, "forms": 1}}),
        encoding="utf-8",
    )
    vocab_index = tmp_path / "vocab-index.json"
    vocab_index.write_text(
        json.dumps(
            {
                "simples": [
                    {
                        "lemma_normalized": "αγνος",
                        "qualities": [
                            {
                                "axis": "HOT",
                                "degree": "3",
                                "entry_count": 1,
                                "direct": True,
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps({"future_corpora": [{"label": "Aetius 3-4"}]}),
        encoding="utf-8",
    )

    index = build_simples_public_index(workbench=workbench, vocab_index_path=vocab_index, config_path=config)

    assert index["stats"]["terms"] == 1
    assert index["stats"]["review_statuses"] == {"pending_candidates": 1}
    assert index["future_corpora"][0]["label"] == "Aetius 3-4"
    term = index["terms"][0]
    assert term["term_key"] == "αγνος"
    assert term["source_counts"] == {"AET_LM": 1}
    assert term["name_relation"]["candidate_count"] == 1
    assert term["quality_summary"][0]["axis"] == "HOT"
