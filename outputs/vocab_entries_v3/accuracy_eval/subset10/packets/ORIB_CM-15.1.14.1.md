# Packet: ORIB_CM-15.1.14.1

## Instructions
Score candidates A/B/C using the rubric. Do not try to guess the model.
Rubric: `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`

## SOURCE_ID
`ORIB_CM-15.1.14.1`

## TEXT
Ξανθίου καρπὸς διαφορητικῆς ἐστι δυνάμεως.

## CONTEXT
(for anaphora; use only if explicitly signalled in TEXT)
CONTEXT_PREV_SOURCE_ID: ORIB_CM-15.1.13.10
CONTEXT_PREV_TEXT:
ἔχουσι δέ τι καὶ ῥυπτικόν.


---

## Candidate A
```json
{
  "source_id": "ORIB_CM-15.1.14.1",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "διαφορητικῆς",
      "normalized": "διαφορητικης",
      "lemma_gr": "διαφορητικός",
      "lemma_normalized": "διαφορητικος",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE_PART",
        "lemma_normalized": null,
        "substance_lemma_normalized": "ξανθιον",
        "part_lemma_normalized": "καρπος"
      },
      "confidence": 0.85,
      "lemma_confidence": 0.8
    },
    {
      "label": "QUALITY_PROPERTY",
      "display": "δυνάμεως",
      "normalized": "δυναμεως",
      "lemma_gr": "δύναμις",
      "lemma_normalized": "δυναμις",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE_PART",
        "lemma_normalized": null,
        "substance_lemma_normalized": "ξανθιον",
        "part_lemma_normalized": "καρπος"
      },
      "confidence": 0.75,
      "lemma_confidence": 0.95
    },
    {
      "label": "SUBSTANCE",
      "display": "Ξανθίου",
      "normalized": "ξανθιου",
      "lemma_gr": "Ξάνθιον",
      "lemma_normalized": "ξανθιον",
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
      "confidence": 0.8,
      "lemma_confidence": 0.8
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "Ξανθίου καρπὸς",
      "normalized": "ξανθιου καρπος",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "ξανθιον",
      "part_lemma_normalized": "καρπος",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.87,
      "lemma_confidence": 0.0
    }
  ],
  "qualities": []
}
```

## Candidate B
```json
{
  "source_id": "ORIB_CM-15.1.14.1",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "διαφορητικῆς δυνάμεως",
      "normalized": "διαφορητικης δυναμεως",
      "lemma_gr": "διαφορητική δύναμις",
      "lemma_normalized": "διαφορητικη δυναμις",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE_PART",
        "lemma_normalized": null,
        "substance_lemma_normalized": "ξανθιον",
        "part_lemma_normalized": "καρπος"
      },
      "confidence": 0.87,
      "lemma_confidence": 0.78
    },
    {
      "label": "SUBSTANCE",
      "display": "Ξανθίου",
      "normalized": "ξανθιου",
      "lemma_gr": "ξάνθιον",
      "lemma_normalized": "ξανθιον",
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
      "confidence": 0.84,
      "lemma_confidence": 0.76
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "Ξανθίου καρπός",
      "normalized": "ξανθιου καρπος",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "ξανθιον",
      "part_lemma_normalized": "καρπος",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.93,
      "lemma_confidence": 0.0
    }
  ],
  "qualities": []
}
```

## Candidate C
```json
{
  "source_id": "ORIB_CM-15.1.14.1",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "διαφορητικῆς",
      "normalized": "διαφορητικης",
      "lemma_gr": "διαφορητικός",
      "lemma_normalized": "διαφορητικος",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE_PART",
        "lemma_normalized": null,
        "substance_lemma_normalized": "ξανθιον",
        "part_lemma_normalized": "καρπος"
      },
      "confidence": 0.9,
      "lemma_confidence": 0.8
    },
    {
      "label": "QUALITY_PROPERTY",
      "display": "δυνάμεως",
      "normalized": "δυναμεως",
      "lemma_gr": "δύναμις",
      "lemma_normalized": "δυναμις",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE_PART",
        "lemma_normalized": null,
        "substance_lemma_normalized": "ξανθιον",
        "part_lemma_normalized": "καρπος"
      },
      "confidence": 0.85,
      "lemma_confidence": 0.95
    },
    {
      "label": "SUBSTANCE",
      "display": "Ξανθίου",
      "normalized": "ξανθιου",
      "lemma_gr": "ξανθίον",
      "lemma_normalized": "ξανθιον",
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
      "confidence": 0.8,
      "lemma_confidence": 0.65
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "Ξανθίου καρπὸς",
      "normalized": "ξανθιου καρπος",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "ξανθιον",
      "part_lemma_normalized": "καρπος",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.82,
      "lemma_confidence": 0.0
    }
  ],
  "qualities": []
}
```
