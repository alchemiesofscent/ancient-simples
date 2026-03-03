# Packet: GAL_SMT-7.12.2

## Instructions
Score candidates A/B/C using the rubric. Do not try to guess the model.
Rubric: `outputs/vocab_entries_v3/accuracy_eval/rubric_v1.md`

## SOURCE_ID
`GAL_SMT-7.12.2`

## TEXT
μαλαβάθρου φύλλον νάρδου στάχυϊ παραπλήσιόν ἐστι τὴν δύναμιν.

## CONTEXT
(for anaphora; use only if explicitly signalled in TEXT)
CONTEXT_PREV_SOURCE_ID: GAL_SMT-7.12.1
CONTEXT_PREV_TEXT:
μάκερ φλοιός ἐστιν ἐκ τῆς Ἰνδικῆς κομιζόμενος, ἐν μὲν τῷ γεύεσθαι στρυφνὸς ἱκανῶς, μετὰ τινος βραχείας δριμύτητος ἀρωματιζούσης·ὀσμώμενος δὲ ἡδὺς ὁμοίως τοῖς πλείστοις ἀρώμασι τοῖς Ἰνδικοῖς. ἔοικεν οὖν καὶ αὐτὸς ἐκ μικτῆς οὐσίας συνεστάναι, τῆς πλείστης μὲν γεώδους ψυχρᾶς, ὀλίγης δὲ τινος θερμῆς τε καὶ λεπτομεροῦς, ὅθεν ἰσχυρῶς ξηραίνει καὶ στύφει καὶ διὰ τοῦτο κοιλιακαῖς τε καὶ δυσεντερικαῖς μίγνυται δυνάμεσιν, ἐν μὲν τῇ τρίτῃ τάξει τῶν ξηραινόντων ὑπάρχων, ἐν δὲ τῇ κατὰ θερμότητα καὶ ψυχρότητα διαφορᾷ μηδέτερον ἐπιφανῶς ἐργαζόμενος.


---

## Candidate A
```json
{
  "source_id": "GAL_SMT-7.12.2",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "δύναμιν",
      "normalized": "δυναμιν",
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
        "substance_lemma_normalized": "μαλαβαθρον",
        "part_lemma_normalized": "φυλλον"
      },
      "confidence": 0.82,
      "lemma_confidence": 0.9
    },
    {
      "label": "SUBSTANCE",
      "display": "μαλαβάθρου",
      "normalized": "μαλαβαθρου",
      "lemma_gr": "μαλαβάθρον",
      "lemma_normalized": "μαλαβαθρον",
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
      "confidence": 0.88,
      "lemma_confidence": 0.85
    },
    {
      "label": "SUBSTANCE",
      "display": "νάρδου",
      "normalized": "ναρδου",
      "lemma_gr": "νάρδος",
      "lemma_normalized": "ναρδος",
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
      "lemma_confidence": 0.95
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "μαλαβάθρου φύλλον",
      "normalized": "μαλαβαθρου φυλλον",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "μαλαβαθρον",
      "part_lemma_normalized": "φυλλον",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.86,
      "lemma_confidence": 0.0
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "νάρδου στάχυϊ",
      "normalized": "ναρδου σταχυι",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "ναρδος",
      "part_lemma_normalized": "σταχυς",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.8,
      "lemma_confidence": 0.0
    }
  ],
  "qualities": []
}
```

## Candidate B
```json
{
  "source_id": "GAL_SMT-7.12.2",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "δύναμιν",
      "normalized": "δυναμιν",
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
        "substance_lemma_normalized": "μαλαβαθρον",
        "part_lemma_normalized": "φυλλον"
      },
      "confidence": 0.85,
      "lemma_confidence": 0.95
    },
    {
      "label": "SUBSTANCE",
      "display": "μαλαβάθρου",
      "normalized": "μαλαβαθρου",
      "lemma_gr": "μαλάβαθρον",
      "lemma_normalized": "μαλαβαθρον",
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
      "lemma_confidence": 0.8
    },
    {
      "label": "SUBSTANCE",
      "display": "νάρδου",
      "normalized": "ναρδου",
      "lemma_gr": "νάρδος",
      "lemma_normalized": "ναρδος",
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
      "lemma_confidence": 0.95
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "μαλαβάθρου φύλλον",
      "normalized": "μαλαβαθρου φυλλον",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "μαλαβαθρον",
      "part_lemma_normalized": "φυλλον",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.9,
      "lemma_confidence": 0.9
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "νάρδου στάχυϊ",
      "normalized": "ναρδου σταχυι",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "ναρδος",
      "part_lemma_normalized": "σταχυς",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.85,
      "lemma_confidence": 0.9
    }
  ],
  "qualities": []
}
```

## Candidate C
```json
{
  "source_id": "GAL_SMT-7.12.2",
  "terms": [
    {
      "label": "QUALITY_PROPERTY",
      "display": "δύναμιν",
      "normalized": "δυναμιν",
      "lemma_gr": "δύναμις",
      "lemma_normalized": "δυναμις",
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
      "confidence": 0.72,
      "lemma_confidence": 0.93
    },
    {
      "label": "SUBSTANCE",
      "display": "μαλαβάθρου",
      "normalized": "μαλαβαθρου",
      "lemma_gr": "μαλάβαθρον",
      "lemma_normalized": "μαλαβαθρον",
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
      "lemma_confidence": 0.78
    },
    {
      "label": "SUBSTANCE",
      "display": "νάρδου",
      "normalized": "ναρδου",
      "lemma_gr": "νάρδος",
      "lemma_normalized": "ναρδος",
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
      "lemma_confidence": 0.96
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "μαλαβάθρου φύλλον",
      "normalized": "μαλαβαθρου φυλλον",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "μαλαβαθρον",
      "part_lemma_normalized": "φυλλον",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.97,
      "lemma_confidence": 0.0
    },
    {
      "label": "SUBSTANCE_PART",
      "display": "νάρδου στάχυϊ",
      "normalized": "ναρδου σταχυϊ",
      "lemma_gr": "",
      "lemma_normalized": "",
      "is_multiword": true,
      "head_lemma_normalized": null,
      "substance_lemma_normalized": "ναρδος",
      "part_lemma_normalized": "σταχυς",
      "variant_place_lemma_normalized": null,
      "applies_to": {
        "kind": "UNSPECIFIED",
        "lemma_normalized": null,
        "substance_lemma_normalized": null,
        "part_lemma_normalized": null
      },
      "confidence": 0.96,
      "lemma_confidence": 0.0
    }
  ],
  "qualities": []
}
```
