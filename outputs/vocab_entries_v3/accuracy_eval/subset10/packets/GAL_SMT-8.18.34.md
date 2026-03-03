# Packet: GAL_SMT-8.18.34

## Instructions
Score candidates A/B/C using the rubric. Do not try to guess the model.
Rubric: `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`

## SOURCE_ID
`GAL_SMT-8.18.34`

## TEXT
σπαργάνιον ξηραντικῆς καὶ τοῦτο δυνάμεώς ἐστι.

## CONTEXT
(for anaphora; use only if explicitly signalled in TEXT)
CONTEXT_PREV_SOURCE_ID: GAL_SMT-8.18.33
CONTEXT_PREV_TEXT:
σόγχος ἐπειδὰν μὲν τελειωθῇ, τῶν ἀκανθωδῶν ἐστιν φυτῶν, χλωρὸς δ' ἔτι καὶ ἁπαλὸς ἐσθίεται τοῖς ἄλλοις ἀγρίοις λαχάνοις ὡσαύτως. ἡ κρᾶσις δ' αὐτοῦ μικτὴ πώς ἐστι, σύγκειται γάρ ἐξ ὑδατώδους τε καὶ γεώδους οὐσίας, ἀμφοῖν ἀτρέμα ψυχρῶν. καὶ γάρ στύψεώς τι μετέχει καὶ σαφῶς ἐμψύχει, καταπλασσόμενός τε καὶ ἐσθιόμενος. ἐπειδὴ δὲ τελέως ξηρανθῇ, γεώδης ἡ κρᾶσις αὐτοῦ γίνεται μετρίως θερμότητα ἔχουσα.


---

## Candidate A
```json
{
  "source_id": "GAL_SMT-8.18.34",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "δυνάμεώς",
      "normalized": "δυναμεως",
      "lemma_gr": "δύναμις",
      "lemma_normalized": "δυναμις",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.78,
      "lemma_confidence": 0.9
    },
    {
      "label": "QUALITY_PROPERTY",
      "display": "ξηραντικῆς",
      "normalized": "ξηραντικης",
      "lemma_gr": "ξηραντικός",
      "lemma_normalized": "ξηραντικος",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.82,
      "lemma_confidence": 0.7
    },
    {
      "label": "SUBSTANCE",
      "display": "σπαργάνιον",
      "normalized": "σπαργανιον",
      "lemma_gr": "σπαργάνιον",
      "lemma_normalized": "σπαργανιον",
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
      "lemma_confidence": 0.9
    }
  ],
  "qualities": [
    {
      "axis": "DRY",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "ξηραντικῆς καὶ τοῦτο δυνάμεώς",
      "evidence_normalized": "ξηραντικης και τουτο δυναμεως",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.76
    }
  ]
}
```

## Candidate B
```json
{
  "source_id": "GAL_SMT-8.18.34",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "δυνάμεώς",
      "normalized": "δυναμεως",
      "lemma_gr": "δύναμις",
      "lemma_normalized": "δυναμις",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.9,
      "lemma_confidence": 0.98
    },
    {
      "label": "QUALITY_PROPERTY",
      "display": "ξηραντικῆς",
      "normalized": "ξηραντικης",
      "lemma_gr": "ξηραντικός",
      "lemma_normalized": "ξηραντικος",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.96,
      "lemma_confidence": 0.96
    },
    {
      "label": "SUBSTANCE",
      "display": "σπαργάνιον",
      "normalized": "σπαργανιον",
      "lemma_gr": "σπαργάνιον",
      "lemma_normalized": "σπαργανιον",
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
      "confidence": 0.98,
      "lemma_confidence": 0.98
    }
  ],
  "qualities": [
    {
      "axis": "DRY",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "ξηραντικῆς καὶ τοῦτο δυνάμεώς ἐστι",
      "evidence_normalized": "ξηραντικης και τουτο δυναμεως εστι",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
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
  "source_id": "GAL_SMT-8.18.34",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "δυνάμεώς",
      "normalized": "δυναμεως",
      "lemma_gr": "δύναμις",
      "lemma_normalized": "δυναμις",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.82,
      "lemma_confidence": 0.9
    },
    {
      "label": "QUALITY_PROPERTY",
      "display": "ξηραντικῆς",
      "normalized": "ξηραντικης",
      "lemma_gr": "ξηραντικός",
      "lemma_normalized": "ξηραντικος",
      "is_multiword": false,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": null,
      "part_lemma_normalized": null,
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.86,
      "lemma_confidence": 0.88
    },
    {
      "label": "SUBSTANCE",
      "display": "σπαργάνιον",
      "normalized": "σπαργανιον",
      "lemma_gr": "σπαργάνιον",
      "lemma_normalized": "σπαργανιον",
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
      "lemma_confidence": 0.88
    }
  ],
  "qualities": [
    {
      "axis": "DRY",
      "degree": null,
      "intensity": "none",
      "hedge": "none",
      "evidence_display": "ξηραντικῆς καὶ τοῦτο δυνάμεώς ἐστι",
      "evidence_normalized": "ξηραντικης και τουτο δυναμεως εστι",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "SUBSTANCE",
        "lemma_normalized": "σπαργανιον",
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.86
    }
  ]
}
```
