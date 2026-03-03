# Packet: ORIB_CM-15.1.10.28

## Instructions
Score candidates A/B/C using the rubric. Do not try to guess the model.
Rubric: `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`

## SOURCE_ID
`ORIB_CM-15.1.10.28`

## TEXT
Καυκαλὶς θερμαίνει καὶ ξηραίνει.

## CONTEXT
(for anaphora; use only if explicitly signalled in TEXT)
CONTEXT_PREV_SOURCE_ID: ORIB_CM-15.1.10.27
CONTEXT_PREV_TEXT:
ἄμεινον δ' ἐστὶ τὸ Γογγρικὸν τοῦ Λαερτικοῦ, καὶ πλείστων αὐτῶν εὐπορήσαις ἂν ἐν Σίδῃ.


---

## Candidate A
```json
{
  "source_id": "ORIB_CM-15.1.10.28",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "θερμαίνει",
      "normalized": "θερμαινει",
      "lemma_gr": "θερμαίνειν",
      "lemma_normalized": "θερμαινειν",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.9,
      "lemma_confidence": 0.95
    },
    {
      "label": "QUALITY_PROPERTY",
      "display": "ξηραίνει",
      "normalized": "ξηραινει",
      "lemma_gr": "ξηραίνειν",
      "lemma_normalized": "ξηραινειν",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.9,
      "lemma_confidence": 0.95
    },
    {
      "label": "SUBSTANCE",
      "display": "Καυκαλὶς",
      "normalized": "καυκαλις",
      "lemma_gr": "Καυκαλίς",
      "lemma_normalized": "καυκαλις",
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
      "confidence": 0.9,
      "lemma_confidence": 0.75
    }
  ],
  "qualities": [
    {
      "axis": "DRY",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "ξηραίνει",
      "evidence_normalized": "ξηραινει",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.9
    },
    {
      "axis": "HOT",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "θερμαίνει",
      "evidence_normalized": "θερμαινει",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.9
    }
  ]
}
```

## Candidate B
```json
{
  "source_id": "ORIB_CM-15.1.10.28",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "θερμαίνει",
      "normalized": "θερμαινει",
      "lemma_gr": "θερμαίνω",
      "lemma_normalized": "θερμαινω",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.96,
      "lemma_confidence": 0.97
    },
    {
      "label": "QUALITY_PROPERTY",
      "display": "ξηραίνει",
      "normalized": "ξηραινει",
      "lemma_gr": "ξηραίνω",
      "lemma_normalized": "ξηραινω",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.96,
      "lemma_confidence": 0.97
    },
    {
      "label": "SUBSTANCE",
      "display": "Καυκαλὶς",
      "normalized": "καυκαλις",
      "lemma_gr": "καυκαλίς",
      "lemma_normalized": "καυκαλις",
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
      "confidence": 0.99,
      "lemma_confidence": 0.99
    }
  ],
  "qualities": [
    {
      "axis": "DRY",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "ξηραίνει",
      "evidence_normalized": "ξηραινει",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.97
    },
    {
      "axis": "HOT",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "θερμαίνει",
      "evidence_normalized": "θερμαινει",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.97
    }
  ]
}
```

## Candidate C
```json
{
  "source_id": "ORIB_CM-15.1.10.28",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "θερμαίνει",
      "normalized": "θερμαινει",
      "lemma_gr": "θερμαίνειν",
      "lemma_normalized": "θερμαινειν",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.93,
      "lemma_confidence": 0.95
    },
    {
      "label": "QUALITY_PROPERTY",
      "display": "ξηραίνει",
      "normalized": "ξηραινει",
      "lemma_gr": "ξηραίνειν",
      "lemma_normalized": "ξηραινειν",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.93,
      "lemma_confidence": 0.95
    },
    {
      "label": "SUBSTANCE",
      "display": "Καυκαλὶς",
      "normalized": "καυκαλις",
      "lemma_gr": "καυκαλίς",
      "lemma_normalized": "καυκαλις",
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
      "confidence": 0.95,
      "lemma_confidence": 0.9
    }
  ],
  "qualities": [
    {
      "axis": "DRY",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "ξηραίνει",
      "evidence_normalized": "ξηραινει",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.95
    },
    {
      "axis": "HOT",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "θερμαίνει",
      "evidence_normalized": "θερμαινει",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "καυκαλις",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.95
    }
  ]
}
```
