# Paul vocab extractor prompt

```prompt
You are an extraction agent for the Ancient Simples Project. Read the input text from Paul of Aegina, Epitome Book 7.3. The text is Ancient Greek only. Output must be strictly valid JSON and must match the supplied schema; do not include commentary.

### Source-specific mode
- Treat the entry headword as the current materia medica subject when the text opens with a headword or clearly continues the entry.
- Paul often gives Galenic degrees with words such as τάξις, ἀπόστασις, πρώτη, δευτέρα, τρίτη, and τετάρτη. Extract explicit degrees 1-4 only when the text explicitly says them.
- Also extract intensity/balance statements without degrees when they are explicit.
- Do not infer qualities from therapeutic effects alone.
- Prefer preserving Paul’s wording as evidence snippets; do not translate or modernize.

### Context
You may be given the immediately preceding entry. Use CONTEXT only if the current TEXT explicitly signals a back-reference. Do not invent terms from context.

### Term labels
Choose exactly one label per term:
- SUBSTANCE: materia medica, ingredients, vehicles, bodily substances used as materials.
- SUBSTANCE_PART: a specific part of a specific substance. Set lemma_gr and lemma_normalized to empty strings, and populate substance_lemma_normalized and part_lemma_normalized.
- PART: plant/mineral/animal parts when the attached substance is not clear.
- PREPARATION: products made by procedures, such as decoctions, juices, ashes, plasters, salves.
- PROCESS: practitioner operations, such as boiling, mixing, grinding, washing, applying.
- TOOL_CONTAINER: implements and vessels.
- CONDITION: diseases and clinical states.
- QUALITY_PROPERTY: pharmacodynamic, sensory, or theoretical properties.
- APPLICATION_SITE: body sites where a remedy is applied or acts.
- ADMINISTRATION: route-of-use actions by the patient.
- PLACE: provenance, varietal, or source place names.

Exclude function words, generic discourse verbs, numbers, single-character tokens, TEI/page markers, and generic uses of δύναμις or οὐσία unless there is a concrete pharmacodynamic frame.

### Normalization and lemmatization
For every Greek display and lemma field, normalized values must be lowercase Greek with all combining marks U+0300-U+036F stripped, including iota subscript. Multiword normalized values use a single space between words.

Lemmas:
- nouns/adjectives: nominative singular where possible
- verbs: present infinitive if confident
- if not confident, use the best dictionary headword and lower lemma_confidence

### Four-quality extraction
Extract statements about:
- HOT: θερμός, θερμαίνειν, θερμότης
- COLD: ψυχρός, ψύχειν, ψυχρότης
- DRY: ξηρός, ξηραίνειν, ξηρότης, ξηραντικός
- WET: ὑγρός, ὑγραίνειν, ὑγρότης

Map explicit ordinals:
- πρώτη/πρώτην -> degree 1
- δευτέρα/δευτέραν -> degree 2
- τρίτη/τρίτην -> degree 3
- τετάρτη/τετάρτην -> degree 4

Degree phrases often appear as κατὰ τὴν πρώτη/δευτέρα/τρίτη/τετάρτη τάξιν or ἀπόστασιν. If multiple axes are explicitly coordinated, output one quality record per axis with the same degree. If the phrase has που or another approximation cue, set hedge to "που" or "approx" and lower confidence slightly.

Intensity values:
- weak: οὐκ ἰσχυρῶς or comparable weak markers
- moderate: μετρίως, συμμετρῶς
- balanced: ἐν τῷ μέσῳ, σύμμετρος/σύμμετος balance language
- strong: σφοδρῶς
- extreme: ἄκρως
- none: no explicit intensity marker

### Applies-to linking
For each term and quality, set applies_to only when the target is clear from the text or from an explicitly signalled context reference.
- SUBSTANCE/PREPARATION target: set kind and lemma_normalized.
- SUBSTANCE_PART target: set kind="SUBSTANCE_PART", substance_lemma_normalized, and part_lemma_normalized.
- Otherwise set kind="UNSPECIFIED" and all lemma fields to null.

If a term or quality is tied to a place-qualified variant, set variant_place_lemma_normalized to the normalized PLACE lemma; otherwise set it to null.

### Multiword substances
When a modified substance forms a distinct material or variety, emit both the multiword SUBSTANCE and the head noun SUBSTANCE. For the multiword term set is_multiword=true and head_lemma_normalized to the normalized head lemma.

### Deduplication
Deduplicate terms within the entry by (label, lemma_normalized). If lemma_normalized is empty, deduplicate by (label, normalized). Do not output the same lemma under multiple labels unless unavoidable.

### Output format
{
  "source_id": "<SOURCE_ID>",
  "terms": [
    {
      "label": "SUBSTANCE|SUBSTANCE_PART|PART|PREPARATION|PROCESS|TOOL_CONTAINER|CONDITION|QUALITY_PROPERTY|APPLICATION_SITE|ADMINISTRATION|PLACE",
      "display": "<Greek surface>",
      "normalized": "<normalized surface>",
      "lemma_gr": "<Greek lemma or empty>",
      "lemma_normalized": "<normalized lemma or empty>",
      "is_multiword": true,
      "head_lemma_normalized": "<normalized head lemma or null>",
      "substance_lemma_normalized": "<normalized substance lemma or null>",
      "part_lemma_normalized": "<normalized part lemma or null>",
      "variant_place_lemma_normalized": "<normalized place lemma or null>",
      "applies_to": {
        "kind": "SUBSTANCE|PART|PREPARATION|SUBSTANCE_PART|UNSPECIFIED",
        "lemma_normalized": "<normalized lemma or null>",
        "substance_lemma_normalized": "<normalized substance lemma or null>",
        "part_lemma_normalized": "<normalized part lemma or null>"
      },
      "confidence": 0.0,
      "lemma_confidence": 0.0
    }
  ],
  "qualities": [
    {
      "axis": "HOT|COLD|DRY|WET",
      "degree": 1,
      "intensity": "none|weak|moderate|balanced|strong|extreme",
      "hedge": "none|που|approx",
      "evidence_display": "<short Greek snippet>",
      "evidence_normalized": "<normalized snippet>",
      "variant_place_lemma_normalized": "<normalized place lemma or null>",
      "applies_to": {
        "kind": "SUBSTANCE|PART|PREPARATION|SUBSTANCE_PART|UNSPECIFIED",
        "lemma_normalized": "<normalized lemma or null>",
        "substance_lemma_normalized": "<normalized substance lemma or null>",
        "part_lemma_normalized": "<normalized part lemma or null>"
      },
      "confidence": 0.0
    }
  ]
}
```


---

## CONTEXT (for anaphora; use only if explicitly signalled in TEXT)
CONTEXT_PREV_SOURCE_ID: PAUL_AEG-7.3.370
CONTEXT_PREV_TEXT:
Λιθάργυρος τῆς μέσης ἐν τοῖς μεταλλικοῖς ἐστι τάξεως· δι' ὃ καὶ ὡς ὕλῃ χρώμεθα πολλάκις αὐτῇ μιγνύντες ἑτέραις δυνάμεσιν. ξηραίνει γε μὴν μετρίως καὶ ῥύπτει καὶ στύφει· δι' ὃ πρὸς τὰ ἐν μηροῖς παρατρίμματα χρησιμεύει.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: PAUL_AEG-7.3.371
TEXT:
Λίθοι πάντες μὲν ὥσπερ καὶ ἡ γῆ ξηραίνουσιν· ἀλλ' ὁ μὲν αἱματίτης στυπτικός τε καὶ ξηραντικὸς ἱκανῶς ἐστιν· ὥστε καὶ τραχώμασιν ὀφθαλμῶν ἁρμόττει, ἀφλεγμάντοις μὲν σὺν ὕδατι, φλεγμαίνουσι δὲ σὺν ᾠῷ· ἁρμόττει δὲ καὶ πτύσεσιν αἵματος πινόμενος καὶ ἕλκη ὑπερσαρκοῦντα καταστέλλει. ὁ δὲ σχιστὸς παραπλησίαν μὲν ἔχει τούτῳ δύναμιν, ἀσθενέστερος δέ, καὶ μετ' αὐτὸν ὁ γαλακτίτης. ὁ δὲ μελιτίτης ἔχει τι καὶ θερμότητος. ὁ δὲ μέροξος, ὃν δὴ καὶ λευκογραφίδα καλοῦσιν, ὅσῳ μαλακώτερος τούτων ἐστὶ διὰ τὸ μηδεμίαν ἔχειν δραστικὴν ποιότητα, τοσούτῳ μετριώτερός τε καὶ ἀνωδυνώτερός ἐστι· διόπερ ἐπὶ τῶν μαλακοσώμων μετὰ κηρωτῆς αὐτῷ πρὸς ἀφούλωσιν ἑλκῶν χρῶνται. ὁ δὲ ὑπόχλωρος ἴασπις ἰσχυροτέρας ὢν δυνάμεως οὐλάς τε καὶ πτερύγια λεπτύνει· ὁ δὲ χλωρὸς ἴασπις στόμαχον ὠφελεῖ περιαπτόμενός τε καὶ ἐν δακτυλίῳ φορούμενος. ὁ δὲ Ἰουδαϊκὸς καλούμενος τῶν ἐν νεφροῖς λίθων ἐστὶ θρυπτικός· ὅθεν καὶ τηκόλιθον αὐτὸν οἱ νεώτεροι προσαγορεύουσιν. ὁ δὲ πυρίτης τῶν ἰσχυρῶς ἐστι διαφορούντων ὄγκους τε καὶ θρόμβους· οὗ μὴ παρόντος τῷ μυλίτῃ χρῶνται. ὁ δὲ Φρύγιος μετὰ τοῦ ξηραίνειν ἰσχυρῶς ἔχει τι καὶ στύψεως καὶ δήξεως· ὅθεν ἀποκρουστικός τε καὶ διαφορητικός ἐστιν, δι' ὃ καὶ ὀφθαλμικαῖς μίγνυται δυνάμεσιν. καὶ ὁ ἀγήρατος δὲ στυπτικῆς τε καὶ διαφορητικῆς ὑπάρχων δυνάμεως γαργαρεῶνας φλεγμαίνοντας ὠφελεῖ. τὸ δὲ τῆς Ἀσσίας πέτρας ἄνθος λεπτομερὲς εἰς τοσοῦτόν ἐστιν, ὡς ἀδήκτως τὰς πλαδαρὰς σάρκας ἐκτήκειν. ὁ δὲ γαγάτης ξηραντικὸς ἱκανῶς ὑπάρχων ἐμφυσήμασιν ἁρμόττει μάλιστα χρονίοις. ἡ δὲ Μαγνῆτίς τε καὶ Ἡρακλεία καλουμένη λίθος παραπλησίαν ἔχει τῷ αἱματίτῃ τὴν δύναμιν. ὅ γε μὴν Ἀράβιος ἐοικὼς ἐλέφαντι ξηραντικός τε καὶ ῥυπτικός ἐστι. τῷ δὲ ἀλαβαστρίτῃ καυθέντι τοὺς στομαχικοὺς ἔνιοι ποτίζουσιν. ἡ δὲ σμίρις ῥυπτικὴν ἔχουσα δύναμιν ὀδόντας σμήχει. οἱ δὲ ἐν τοῖς σπόγγοις εὑρισκόμενοι λίθοι τοὺς ἐν νεφροῖς θρύπτουσι λίθους· παραπλησίας δὲ τούτοις εἰσὶ δυνάμεως καὶ οἱ ἐν τῷ Ἀργαίῳ τῆς Καππαδοκίας ὄρει γεννώμενοι· ὁμοίως δὲ καὶ ὁ ὀφίτης καλούμενος, ὅστις καὶ τοὺς ἐχεοδήκτους ὠφελεῖ περιαπτόμενος. τὸν δὲ ὀστρακίτην καὶ τὸν γεώδη ξηραντικοὺς ἱκανῶς φασιν, ὥστε καὶ φλεγμονώδεις ὄγκους ἰᾶσθαι. τό γε μὴν τῆς Ναξίας ἀκόνης ἀπότριμμα ψυκτικὸν εἶναί φασιν, ὥστε καὶ τιτθοὺς παρθένων καὶ παίδων ὄρχεις προσστέλλειν. τῆς ἐλαιακόνης δὲ τὸ ἀπότριμμα ῥυπτικὸν ὑπάρχον ἀλωπεκίαις ἁρμόττει. τὸν ἱερακίτην δὲ καὶ Ἰνδικὸν λίθον φασὶ περιαπτόμενον τὸ ἐκ τῶν αἱμορροΐδων ἱστᾶν αἷμα, τὸν δὲ σάπφειρον πινόμενον τοὺς ὑπὸ σκορπίου πληγέντας ὠφελεῖν καὶ τὸν ἀφροσέλινον τοὺς ἐπιλήπτους. ὁ δὲ Ἀρμενιακὸς καθαίρει μὲν κάτω τὴν κοιλίαν, ἔστι δὲ κακοστόμαχος.
