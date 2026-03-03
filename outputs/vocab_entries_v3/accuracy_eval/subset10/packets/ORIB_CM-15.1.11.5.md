# Packet: ORIB_CM-15.1.11.5

## Instructions
Score candidates A/B/C using the rubric. Do not try to guess the model.
Rubric: `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`

## SOURCE_ID
`ORIB_CM-15.1.11.5`

## TEXT
Λειμωνίου ὁ καρπὸς αὐστηρὸς ὑπάρχει.

## CONTEXT
(for anaphora; use only if explicitly signalled in TEXT)
CONTEXT_PREV_SOURCE_ID: ORIB_CM-15.1.11.4
CONTEXT_PREV_TEXT:
τὸ δ' ἱππολάπαθον μετὰ τοῦ διαφορεῖν καὶ ἀποκρουστικῆς ἐστι δυνάμεως, ἀσθενεστέρας δέ.


---

## Candidate A
```json
{
  "source_id": "ORIB_CM-15.1.11.5",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "αὐστηρὸς",
      "normalized": "αυστηρος",
      "lemma_gr": "αὐστηρός",
      "lemma_normalized": "αυστηρος",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE_PART",
        "lemma_normalized": null,
        "substance_lemma_normalized": "λειμωνιον",
        "part_lemma_normalized": "καρπος"
      },
      "confidence": 0.85,
      "lemma_confidence": 0.95
    },
    {
      "label": "SUBSTANCE",
      "display": "Λειμωνίου",
      "normalized": "λειμωνιου",
      "lemma_gr": "λειμώνιον",
      "lemma_normalized": "λειμωνιον",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.75,
      "lemma_confidence": 0.7
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "καρπὸς",
      "normalized": "καρπος",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "λειμωνιον",
      "part_lemma_normalized": "καρπος",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.9,
      "lemma_confidence": 1.0
    }
  ],
  "qualities": []
}
```

## Candidate B
```json
{
  "source_id": "ORIB_CM-15.1.11.5",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "αὐστηρὸς",
      "normalized": "αυστηρος",
      "lemma_gr": "αὐστηρός",
      "lemma_normalized": "αυστηρος",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE_PART",
        "lemma_normalized": null,
        "substance_lemma_normalized": "λειμωνιον",
        "part_lemma_normalized": "καρπος"
      },
      "confidence": 0.96,
      "lemma_confidence": 0.99
    },
    {
      "label": "SUBSTANCE",
      "display": "Λειμωνίου",
      "normalized": "λειμωνιου",
      "lemma_gr": "λειμώνιον",
      "lemma_normalized": "λειμωνιον",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.78,
      "lemma_confidence": 0.75
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "Λειμωνίου καρπὸς",
      "normalized": "λειμωνιου καρπος",
      "lemma_gr": "καρπός λειμωνίου",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "λειμωνιον",
      "part_lemma_normalized": "καρπος",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.94,
      "lemma_confidence": 0.72
    }
  ],
  "qualities": []
}
```

## Candidate C
```json
{
  "source_id": "ORIB_CM-15.1.11.5",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "αὐστηρὸς",
      "normalized": "αυστηρος",
      "lemma_gr": "αὐστηρός",
      "lemma_normalized": "αυστηρος",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE_PART",
        "lemma_normalized": null,
        "substance_lemma_normalized": "λειμωνιον",
        "part_lemma_normalized": "καρπος"
      },
      "confidence": 0.9,
      "lemma_confidence": 0.9
    },
    {
      "label": "SUBSTANCE",
      "display": "Λειμωνίου",
      "normalized": "λειμωνιου",
      "lemma_gr": "Λειμώνιον",
      "lemma_normalized": "λειμωνιον",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.85,
      "lemma_confidence": 0.6
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "καρπὸς",
      "normalized": "καρπος",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "λειμωνιον",
      "part_lemma_normalized": "καρπος",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.85,
      "lemma_confidence": 0.0
    }
  ],
  "qualities": []
}
```
