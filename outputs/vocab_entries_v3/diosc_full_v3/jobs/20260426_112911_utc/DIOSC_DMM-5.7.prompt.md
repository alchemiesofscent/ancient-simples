# Vocab extractor prompt (Dioscorides variant)

```prompt

## Prompt (paste into LLM system/user message as-is)

You are an extraction agent for the Ancient Simples Project. Read the input text (Ancient Greek, possibly with TEI tags) and extract candidate terms relevant to ancient pharmacy/science. Output must be strictly valid JSON (no commentary).

### Source-specific mode (Dioscorides DMM)
- Keep the same JSON schema and `qualities[]` array shape as the standard extractor.
- Do NOT assume Galenic parallel degree methodology is present.
- Extract quality axes/degrees/intensity only when the text explicitly supports them.
- Prefer `degree=null` when no explicit ordinal/degree language is present.
- Do not infer numeric degrees from generic potency language alone.

### Context (mandatory)
You may be given a CONTEXT section containing the immediately preceding entry.
Use CONTEXT ONLY if the current TEXT explicitly signals a back-reference (e.g., “as said earlier”, “the wild [X]”, “τῇ τῆς ἀγρίας” where the head is recoverable by explicit signal).
- Do NOT invent terms from CONTEXT if the TEXT does not explicitly signal the reference.
- If you resolve an implied head using CONTEXT, lower confidence and keep evidence snippets from the current TEXT.

### Labels (choose exactly one per term)
- SUBSTANCE
- SUBSTANCE_PART
- PART
- PREPARATION
- PROCESS
- TOOL_CONTAINER
- CONDITION
- QUALITY_PROPERTY
- APPLICATION_SITE
- ADMINISTRATION
- PLACE

### Exclusions (hard)
- Ignore teiHeader metadata, page/line markers, and TEI-only tokens.
- Exclude function words (articles, particles, conjunctions, pronouns), numbers, and single-character tokens.
- Exclude generic discourse verbs unless part of a technical expression: εἰμί, γίγνομαι, λέγω, δοκέω.
- Exclude generic anatomy containers as APPLICATION_SITE unless modified by a specific anatomical term: μόριον, μέρος, σῶμα.
- Exclude culinary accompaniment/food terms unless clearly used as medicinal substances/remedies.

### Normalization rules (mandatory)
For every term provide:
- `display`: representative Greek surface form from the text
- `normalized`: lowercase + strip all combining marks U+0300-U+036F (including iota subscript); keep Greek script (no transliteration)
If multiword, normalize each word and join with single spaces.

### Lemma rules (mandatory)
For every term provide:
- `lemma_gr`: best lemma candidate in polytonic Greek
  - nouns/adjectives: nominative singular
  - verbs (PROCESS/ADMINISTRATION): present infinitive if confident; otherwise dictionary headword
- `lemma_normalized`: apply the same normalization to lemma_gr
- `lemma_confidence`: 0.0–1.0 confidence that lemma_gr is correct

### Label examples (illustrative; do not restrict extraction to these)
SUBSTANCE (materials/ingredients/vehicles; includes bodily substances like καταμήνια when treated as substances)
- Examples: μανδραγόρα, ἑλλέβορος, πέπερι, ὕδωρ, ὄξος, ἅλμη, θάλαττα, ψιμμύθιον, καταμήνια
- Rule: could be a materia medica headword.

SUBSTANCE_PART (a specific part of a specific substance; keep specificity)
- Examples (shape): “ἀμπέλου ἀγρίας οἱ βότρυες …” → substance=ἀμπελος ἀγρια, part=βότρυς
- Rule: if a PART term is explicitly attached to a particular substance (genitive-of, “of X”, or clear attachment in the clause), emit SUBSTANCE_PART rather than a bare PART.
- Output requirement: set `substance_lemma_normalized` and `part_lemma_normalized` (both non-null) and set the generic `lemma_normalized` to "" (empty string). Set applies_to.kind="UNSPECIFIED" and all applies_to lemma fields to null.

PART (physical parts of a substance; not produced by a procedure)
- Examples: ῥίζα, φύλλον, σπέρμα, φλοιός, ἄνθος (botanical), καρπός, βλαστός
- Rule: answers “which part of the substance?” Use PART only if the substance is not clearly identifiable in the same clause/window.

PREPARATION (products produced by procedures)
- Examples: ἀφέψημα, χυμός, τέφρα/σποδός, κηρωτή, κατάπλασμα, ἄλειμμα
- Rule: if you can ask “how was this made?”, it is a PREPARATION.

PROCESS (hands-on preparation/application operations)
- Examples: μίγνυμι, τήκω, ἕψω, διηθέω, καταθραύω, ἐπιτίθημι, ἐπαλείφω, βρέχω, καταντλέω, φρύγειν
- Rule: what the practitioner does to make/apply a remedy. Exclude generic effect predictions unless framed as instructions.

ADMINISTRATION (route-of-use actions by the patient)
- Examples: ἐσθίειν, πίνειν, καταπίνειν, λαμβάνειν (when “take a drug”)
- Rule: denotes how the remedy is taken/received.

TOOL_CONTAINER (implements/vessels)
- Examples: ἀγγεῖον, θυεία, σπόγγος, ἔριον, κεράμιον

CONDITION (diseases/clinical states; includes κεφαλαλγής when used as a named adverse state)
- Examples: πυρετός, φλεγμονή, ἕλκος, ἐρυσίπελας, καῦμα, κεφαλαλγία/κεφαλαλγής

QUALITY_PROPERTY (pharmacodynamic/sensory/theoretical properties)
- Examples: θερμός/θερμότης, ψυχρός/ψυχρότης, ξηρός/ξηρότης, ὑγρός/ὑγρότης, δύναμις, κρᾶσις, στύψις, πικρός
- `δύναμις`/`οὐσία` rule: extract as QUALITY_PROPERTY only when clearly pharmacodynamic/technical in context (e.g., with explicit effect predicates or quality framing such as θερμαίνει/ψύχει/ξηραίνει/ὑγραίνει, δραστικὴ ποιότης, specific therapeutic action).


APPLICATION_SITE (bodily target site where remedy is applied/acts)
- Examples: δέρμα, γλῶττα, γαστήρ, κεφαλή, ὑποχόνδρια, κνῆμαι, ἧπαρ, σπλήν
- Rule: where applied or where it acts in the body.

PLACE (place names; provenance/varietal qualifiers)
- Examples: Παρνασσός
- Rule: toponyms used as provenance, varietal, or source qualifiers (do not treat as SUBSTANCE).

Disambiguation reminders:
- PART ≠ APPLICATION_SITE (ῥίζα is PART; δέρμα/κεφαλή are APPLICATION_SITE)
- SUBSTANCE ≠ PREPARATION (μανδραγόρα is SUBSTANCE; ἀφέψημα μανδραγόρας is PREPARATION)
- Adjectives are usually QUALITY_PROPERTY unless they clearly denote a CONDITION (e.g., κεφαλαλγής in therapeutic context).

### Primary quality tracking (mandatory; source-aware)
Additionally, extract statements about the four primary qualities, including:
- explicit degrees (1–4)
- intensity / balance statements (even without degrees)

Axes:
- HOT (θερμός / θερμαίνειν / θερμότης)
- COLD (ψυχρός / ψύχειν / ψυχρότης)
- DRY (ξηρός / ξηραίνειν / ξηρότης / ξηραντικός)
- WET (ὑγρός / ὑγραίνειν / ὑγρότης)

Detect explicit degrees 1–4 when the text uses phrases like:
- “κατὰ τὴν πρώτην/δευτέραν/τρίτην/τετάρτην …” especially with ἀπόστασις or equivalent degree language.

Map:
- πρώτην → 1
- δευτέραν → 2
- τρίτην → 3
- τετάρτην → 4

Detect intensity/balance (set `intensity`, even if `degree` is null):
- moderate: μετρίως, συμμετρῶς → intensity="moderate"
- balanced: ἐν τῷ μέσῳ καθέστηκε → intensity="balanced"
- balanced between WET and DRY: σύμμετος/σύμμετρος … κατὰ ὑγρότητα καὶ ξηρότητα → output TWO records (axis=WET and axis=DRY), both intensity="balanced", same evidence snippet
- weak: οὐκ ἰσχυρῶς → intensity="weak"
- strong: σφοδρῶς → intensity="strong"
- extreme: ἄκρως → intensity="extreme"
If multiple strength markers occur, choose the strongest that applies to the same axis.

Hedges:
- If the degree phrase contains “που” or similar approximation cues, record hedge="που" and lower confidence slightly.

Axis assignment:
- If “θερμ-” terms occur in the same clause/window as the degree phrase, record axis=HOT.
- If “ψυχ-” terms occur, axis=COLD.
- If “ξηρ- / ξηραντ-” terms occur, axis=DRY.
- If “ὑγρ-” terms occur, axis=WET.
If multiple axes are explicitly coordinated (e.g., “θερμὸς … καὶ ξηραντικὸς κατὰ τὴν τρίτην…”), output one record per axis with the same degree.

Applies-to linking:
- If the subject is clearly a SUBSTANCE/PREPARATION (e.g., “ἄγνος… θερμὸς…”) set applies_to.kind accordingly and set applies_to.lemma_normalized to that term’s lemma_normalized.
- If the clause is specifically about a SUBSTANCE PART (e.g., ῥίζα/πόα/σπέρμα/φλοιός/φύλλον/ἄνθος/etc. of a substance), set applies_to.kind="SUBSTANCE_PART" and include:
  - applies_to.substance_lemma_normalized
  - applies_to.part_lemma_normalized
- If unclear, set applies_to.kind="UNSPECIFIED".
Always include all applies_to lemma fields; set unused fields to null.

Place-qualifying variants:
- Extract place names as PLACE terms.
- If a quality statement is explicitly tied to a place-qualified variant/provenance (e.g., a substance “from/at” a named place, or a place-epithet modifying the subject), set qualities[].variant_place_lemma_normalized to that place’s lemma_normalized; otherwise set it to null.

Do NOT treat degree ordinals as separate terms.

### Multiword SUBSTANCE extraction (mandatory)
When a substance head noun is modified by a qualifier yielding a distinct material/variety (MWE), ALWAYS emit:
1) the multiword term (is_multiword=true) as SUBSTANCE
2) the head noun alone as SUBSTANCE

Examples of MWEs:
- κίκινον ἔλαιον (castor oil) → emit MWE “κίκινον ἔλαιον” AND head “ἔλαιον”
- μῆλον κυδώνιον (quince) → emit MWE “μῆλον κυδώνιον” AND head “μῆλον”

For MWEs, set `head_lemma_normalized` to the head noun’s lemma_normalized. If not an MWE, set head_lemma_normalized=null.

Qualifier-only rule:
- If only the qualifier appears without the head noun, do NOT treat it as standalone SUBSTANCE unless it is clearly used as a headword/substance name in context.
- If you include it anyway, lower confidence substantially and prefer omitting unless clearly warranted.

### Term-level linking (mandatory; do not guess)
For each extracted term, also record whether it applies to a specific subject in the clause/window.

Set `terms[].applies_to` ONLY when the target is clear from the TEXT (or from CONTEXT when explicitly signalled):
- QUALITY_PROPERTY terms: if the property describes a specific subject, set applies_to to that subject:
  - kind="SUBSTANCE" or "PREPARATION" with applies_to.lemma_normalized set
  - kind="SUBSTANCE_PART" with applies_to.substance_lemma_normalized + applies_to.part_lemma_normalized set
- PROCESS / ADMINISTRATION terms: if the action is performed on/with a specific remedy/material, set applies_to similarly.

Otherwise:
- set applies_to.kind="UNSPECIFIED" and set applies_to.lemma_normalized/substance_lemma_normalized/part_lemma_normalized all to null.

### Place association on terms (mandatory; do not guess)
If a term itself is explicitly place-qualified (provenance/varietal/source), set `terms[].variant_place_lemma_normalized` to that place’s lemma_normalized; otherwise set it to null.
Populate this field primarily for labels SUBSTANCE, PREPARATION, and SUBSTANCE_PART. For other labels, set it to null unless the term itself is unambiguously a place-qualified variant name.

### Deduplication (hard)
- Deduplicate within the chunk by (label, lemma_normalized). If lemma_normalized is empty, deduplicate by (label, normalized).
- Do not output the same lemma_normalized more than once under the same label.
- Do not output the same lemma_normalized under multiple labels unless unavoidable; if unavoidable, choose the best label and lower confidence.

### Output format (strict JSON only)
{
  "source_id": "<SOURCE_ID>",
  "terms": [
    {
      "label": "SUBSTANCE|SUBSTANCE_PART|PART|PREPARATION|PROCESS|TOOL_CONTAINER|CONDITION|QUALITY_PROPERTY|APPLICATION_SITE|ADMINISTRATION|PLACE",
      "display": "<GREEK_SURFACE>",
      "normalized": "<NORMALIZED_SURFACE>",
      "lemma_gr": "<GREEK_LEMMA_OR_EMPTY>",
      "lemma_normalized": "<NORMALIZED_LEMMA_OR_EMPTY>",
      "is_multiword": true|false,
      "head_lemma_normalized": "<NORMALIZED_HEAD_LEMMA (or null if not an MWE)>",
      "substance_lemma_normalized": "<SUBSTANCE_LEMMA_NORMALIZED (or null)>",
      "part_lemma_normalized": "<PART_LEMMA_NORMALIZED (or null)>",
      "variant_place_lemma_normalized": "<PLACE_LEMMA_NORMALIZED (or null)>",
      "applies_to": {
        "kind": "SUBSTANCE|PART|PREPARATION|SUBSTANCE_PART|UNSPECIFIED",
        "lemma_normalized": "<LEMMA_NORMALIZED (or null)>",
        "substance_lemma_normalized": "<SUBSTANCE_LEMMA_NORMALIZED (or null)>",
        "part_lemma_normalized": "<PART_LEMMA_NORMALIZED (or null)>"
      },
      "confidence": 0.0-1.0,
      "lemma_confidence": 0.0-1.0
    }
  ],
  "qualities": [
    {
      "axis": "HOT|COLD|DRY|WET",
      "degree": 1|2|3|4|null,
      "intensity": "none|weak|moderate|balanced|strong|extreme",
      "hedge": "none|που|approx",
      "evidence_display": "<short Greek snippet>",
      "evidence_normalized": "<normalized snippet>",
      "variant_place_lemma_normalized": "<PLACE_LEMMA_NORMALIZED (or null)>",
      "applies_to": {
        "kind": "SUBSTANCE|PART|PREPARATION|SUBSTANCE_PART|UNSPECIFIED",
        "lemma_normalized": "<LEMMA_NORMALIZED (or null)>",
        "substance_lemma_normalized": "<SUBSTANCE_LEMMA_NORMALIZED (or null)>",
        "part_lemma_normalized": "<PART_LEMMA_NORMALIZED (or null)>"
      },
      "confidence": 0.0-1.0
    }
  ]
}

Sorting:
- Sort `terms` by label, then lemma_normalized (or normalized if lemma missing).
- Sort `qualities` by axis, then degree, then intensity.

Deduplication refinements:
- For label=SUBSTANCE_PART, deduplicate by (substance_lemma_normalized, part_lemma_normalized) and do NOT collapse distinct parts across different substances.
- For label=QUALITY_PROPERTY, PROCESS, ADMINISTRATION: if applies_to is specified (kind != "UNSPECIFIED"), deduplicate by (label, lemma_normalized, applies_to.kind, applies_to.lemma_normalized, applies_to.substance_lemma_normalized, applies_to.part_lemma_normalized).

Now process the following input.

SOURCE_ID: <paste stable chunk id>
TEXT:
<paste chunk here>

---

## Examples (expected behavior)

### Example 1: Degree extraction (HOT + DRY, degree 3 with hedge)

Input snippet:
“ἄγνος … θερμὸς μὲν ἐστι καὶ ξηραντικὸς κατὰ τὴν τρίτην που ἀπόστασιν …”

Expected `qualities` records (shape):
- HOT degree=3 hedge=που applies_to=αγνος
- DRY degree=3 hedge=που applies_to=αγνος

### Example 2: Administration

Input snippet:
“οὐ μόνον ἐσθιόμενα καὶ πινόμενα …”

Expected:
- ADMINISTRATION: ἐσθίειν
- ADMINISTRATION: πίνειν

### Example 3: Parts vs sites

Input snippet:
“τὰ φύλλα καὶ τὸ σπέρμα … ἄφυσος κατὰ γαστέρα …”

Expected:
- PART: φύλλον, σπέρμα
- APPLICATION_SITE: γαστήρ
- QUALITY_PROPERTY: ἄφυσος (aflatulent)


---

## CONTEXT (for anaphora; use only if explicitly signalled in TEXT)
CONTEXT_PREV_SOURCE_ID: DIOSC_DMM-5.6
CONTEXT_PREV_TEXT:
οἶνοι· οἱ μὲν παλαιοὶ βλαπτικοὶ νεύρων καὶ τῶν λοιπῶν αἰσθητηρίων, πρὸς δὲ γεῦσιν ἡδίονες, ὅθεν ἐπὶ τῶν ἀσθενές τι μέρος ἐχόντων παραιτητέοι, ἐπὶ μέντοι τῆς ἐν ὑγιείᾳ χρήσεως ὀλίγος τε καὶ ὑδαρὴς λαμβάνεται ἀβλαβῶς. ὁ δὲ νέος ἐμπνευματωτικός, δύσπεπτος, δυσόνειρος, οὐρητικός. ὁ δὲ μέσος τῇ ἡλικίᾳ ἐκπέφευγε τὰ ἀμφοτέρων ἐλαττώματα, ὅθεν ἐγκριτέος ἐστὶν ἐν τῇ τε ὑγιείας καὶ ἀσθενείας χρήσει. ἔτι ὁ μὲν λευκὸς λεπτός τε καὶ εὐανάδοτος καὶ εὐστόμαχος 2 ὑπάρχει· ὁ δὲ μέλας παχὺς καὶ δύσπεπτος, μέθης καὶ σαρκῶν γεννητικός· ὁ δὲ κιρρός, μέσος ὤν, μέσην ἔχει καὶ τὴν πρὸς ἑκάτερον τούτων δύναμιν. αἱρετώτερος μέντοι ἔν τε ὑγιείᾳ καὶ ἀσθενείᾳ ὁ λευκός. ἔτι καὶ παρὰ τὴν ποιότητα διαφέρουσιν· ὁ μὲν γὰρ γλυκὺς οἶνος ἁδρομερής τέ ἐστι καὶ δυσδιάπνευστος, στομάχου πνευματωτικός, κοιλίας τε καὶ ἐντέρων ταρακτικὸς ὥσπερ καὶ τὸ γλεῦκος, ἦττον δὲ μεθύσκει, κύστει δὲ καὶ νεφροῖς εὔθετος. 3 ὁ δὲ αὐστηρὸς οὐρητικώτερος, κεφαλαλγίας τε καὶ μέθης ποιητικός. ὁ δὲ στρυφνὸς εὐθετώτατος πρὸς ἀνάδοσιν σιτίων, κοιλίας τε στατικὸς καὶ τῶν ἄλλων ῥευματισμῶν. ὁ δὲ ἁπαλὸς ἦττον ἅπτεται τοῦ νευρώδους, ἦττον δʼ ἐστὶν οὐρητικός. ὁ δὲ τεθαλασσωμένος κακοστόμαχος, διψοποιός, νεύρων κακωτικός, εὐκοίλιος, ἀνεπιτήδειος τοῖς ἐξ ἀσθενείας [ἀναλαμβάνουσι χρονίας]. 4 ὁ δὲ ἐκ τῆς θειλοπεδευθείσης σταφυλῆς ἢ ἐπὶ τῶν κλημάτων ὀπτηθείσης καὶ τριβομένης γινόμενος γλυκύς, καλούμενος δὲ Κρητικὸς ἡ πρότροπος ἢ Πράμνειος, ἢ καθεψομένου τοῦ γλεύκους σίραιος ἢ ἕψημα καλούμενος· ὁ μὲν μέλας, καλούμενος δὲ μελαμψίθιος, παχύς ἐστι καὶ πολύτροφος, ὁ δὲ λευκὸς λεπτότερος, ὁ δὲ μέσος μέσην ἔχει καὶ τὴν δύναμιν. στυπτικὸς δὲ πᾶς ἐστι, σφυγμῶν ἀνακλητικός, ποιῶν πρὸς πάντα τὰ θανάσιμα, ὅσα κατὰ ἕλκωσιν ἀναιρεῖ, πινόμενος σὺν ἐλαίῳ καὶ ἐξεμούμενος, καὶ πρὸς μηκώνιον δὲ καὶ φαρικὸν καὶ τοξικὸν καὶ κώνειον καὶ γάλα θρομβωθέν, καὶ πρὸς κύστιν καὶ νεφροὺς ὀδαξουμένους καὶ εἱλκωμένους. εἰσὶ δὲ πνευματικώτατοι 5 καὶ κακοστόμαχοι· ἰδίως δὲ ἐπὶ τῶν τὴν κοιλίαν ῥευματιζομένων ἁρμόζει ὀ μελαμψίθιος, ὁ δὲ λευκὸς μαλακτικώτερος κοιλίας τῶν λοιπῶν μᾶλλον. ὁ δὲ τὴν γύψον ἔχων κακωτικὸς τοῦ νευρώδους, καρηβαρικός, πυρώδης, κύστει ἄθετος, πρὸς δὲ τὰ θανάσιμα τῶν ἄλλων εὐθετώτερος. οἱ δὲ πίτταν ἢ ῥητίνην πιτυίνην ἔχοντες θερμαντικοὶ καὶ πεπτικοί, ἄθετοι δὲ τοῖς ἐμετικοῖς. οἱ δὲ καλούμενοι ἀπαράχυτοι, ἔχοντες δὲ ἕψημα μεμειγμένον, κεφαλῆς εἰσι πληκτικοὶ καὶ πυρωτικοί, μέθης γεννητικοί, φυσώδεις, δυσδιάπνευστοι, κακοστόμαχοι. ὁ μὲν οὖν δοκῶν πρωτεύειν τῶν ἐν Ἰταλίᾳ οἴνων, Φαλερῖνος 6 δὲ καλούμενος, παλαιωθεὶς ἄγαν εὔπεπτος, σφυγμῶν ἀνακλητικός, κοιλίας στεγνωτικὸς καὶ εὐστόμαχος, κύστει ἄθετος καὶ ἀμβλυωπός, πρὸς δὲ πολυποσίαν ἀνάρμοστος. ὁ δʼ Ἀλβανὸς ἁδρομερέστερος τοῦ Φαλερίνου, ἔγγλυκυς, ἐμπνευματῶν στόμαχον, κοιλίαν τε μαλάττων, πέψει τε οὐχ ὁμοίως συνεργῶν, τοῦ δὲ νευρώδους ἧττον κακωτικός· παλαιωθεὶς δὲ καὶ οὗτος αὐστηρὸς γίνεται. ὁ δὲ Καίκουβος, γλυκὺς ὤν, ἁδρομερέστερός 7 ἐστι τοῦ Ἀλβανοῦ, σαρκῶν τε καὶ εὐχροίας γεννητικός, πέψει δὲ ἄθετος· ὁ δὲ Συρεντῖνος αὐστηρὸς ἱκανῶς ἐστιν, ὅθεν ἐντέρων καὶ στομάχου ῥεῦμα ἵστησι, κεφαλῆς τε ἧττον ἅπτεται, λεπτομερὴς ὤν· παλαιωθεὶς δὲ εὐστομαχώτερος καὶ ἡδίων γίνεται. ὁ δὲ Ἀδριανὸς καὶ ὁ Μαμερτῖνος, γεννώμενος δὲ ἐν Σικελίᾳ, κατʼ ἴσον εἰσὶν ἁδρομερεῖς, μετρίως στύφοντες, καὶ τάχιον παλαιοῦνται, ἧττον δὲ τοῦ νευρώδους ἅπτονται διὰ τὸ ἐν αὐτοῖς λεῖον. 8 ὁ δὲ Πραιτυτιανός, καὶ αὐτὸς ἐκ τῶν κατʼ Ἀδρίαν κομιζόμενος τόπων, εὐώδης καὶ λειότερός ἐστιν, ὅθεν λανθάνει μὲν πολύς πινόμενος, φυλάττει δὲ ἐφ ἱκανὸν τὴν μέθην. καὶ ὁ Πστρικὸς δὲ λεγόμενος ἔοικε τῷ Πραιτυτιανῷ, οὐρητικώτερος ὑπάρχων. ὁ μέντοι Χῖος, Ἀριούσιος δὲ καλούμενος, ἁπαλώτερος τῶν προειρημένων, εὔποτος, τρόφιμος, ἦττον μεθύσκων, ῥεύματος σταλτι κός, χρήσιμος εἰς τὰ ὀφθαλμικά. 9 ὁ δὲ Λέσβιος εὐανάδοτος, κουφότερός τε τοῦ Χίου καὶ εὐκοίλιος. τὴν αὐτὴν δὲ τούτῳ κέκτηται δύναμιν ὁ κατὰ Εφεσον γεννώμενος, καλούμενος δὲ Φυγελίτης. ὁ δὲ ἐκ τῆς Ἀσίας Μεσωγίτης ἐκ τοῦ Τμώλου κεφαλαλγὴς καὶ νεύρων βλαπτικός. ὁ δὲ Κῷος καὶ Κλαζομένιος διὰ τὸ θαλάττης πολλῆς μετέχειν εὔφθαρτοι καὶ πνευματώδεις, κοιλίας τε ταρακτικοί, καὶ νεύρων δέ εἰσι βλαπτικοί. 10 κοινὴ δύναμις οἴνου. κοινῶς δὲ πᾶς ἀμιγὴς οἶνος καὶ ἀκέραιος, αὐστηρὸς δὲ τὴν φύσιν, θερμαντικός, εὐανάδοτος, εὐστόμαχος, ὀρεκτικός, θρεπτικός, ὑπνοποιός, ῥωστικός, εὐχροίας παρασκευαστικός. ἱκανῶς δὲ ποθεὶς βοηθεῖ τοῖς κώνειον ἢ κόριον ἢ ἰξίαν ἢ φαρικὸν ἢ μηκώνιον ἢ λιθάργυρον ἢ σμίλακα ἡ ἀκόνιτον ἢ μύκητας εἰληφόσι, πρός τε ἑρπετῶν δηγμοὺς καὶ πληγὰς πάντων, ὅσα πλήξαντα ἢ δακόντα κατὰ ψῦξιν ἀναιρεῖ ἢ ἀνατρέπει τὸν στόμαχον· ποιεῖ καὶ πρὸς ἐμπνευμάτωσιν χρόνιον καὶ δῆξιν ὑποχονδρίου καὶ πλατυσμὸν καὶ ἀνάλυσιν στομάχου ἢ ἐντέρων καὶ κοιλίας ῥευματισμόν, καὶ ἀφιδροῦσι καὶ διαφορουμένοις ἁρμόζουσι, μάλιστα δὲ οἱ λευκοὶ καὶ παλαιοὶ καὶ εὐώδεις. οἱ μέντοι παλαιοὶ καὶ γλυκεῖς πρὸς 11 τὰ περὶ κύστιν καὶ νεφρούς ἐπιτηδειότεροι, πρός τε τραύματα καὶ φλεγμονὰς σύν ἐρίοις οἰσυπηροῖς ἐπιτιθέμενοι, καὶ καταντλοῦνται δὲ ὠφελίμως πρὸς τὰ θηριώδη καὶ φαγεδαινικὰ καὶ ῥευματιζόμενα ἕλκη. πρὸς δὲ τὴν ἐν ὑγιείᾳ χρῆσιν εὔθετοι οἱ ἀθάλασσοι, αὐστηροὶ καὶ λευκοί· διαφέρουσι δὲ τούτων οἱ ἐταλικοί, ὡς ὁ Φαλερῖνος Συρεντῖνος Καίκουβος Σιγνῖνος καὶ ἄλλοι πολλοὶ οἱ ἀπὸ τῆς Καμπανίας καὶ ὁ Πραιτυτιανὸς ὁ ἀπὸ τοῦ Ἀδρία καὶ ὁ Σικελιωτικὸς ὁ Μαμερτῖνος καλούμενος, Ἑλληνικῶν δὲ ὁ Χῖος Λέσβιος Φυγελίτης ὁ ἐν Εφέσῳ γεννωμενος. οἱ δὲ παχεῖς καὶ μέλανες κακοστόμαχοι, φυσώδεις, 12 σαρκὸς μέντοι γεννητικοί, οἶ μέντοι λεπτοὶ καὶ αὐστηροὶ εὐστόμαχοι, ἦττον δὲ σαρκοποιοί, οὐρητικώτεροι δὲ καὶ κεφαλαλγεῖς οἱ σφόδρα παλαιοὶ καὶ λευκοί [καὶ λεπτοί]· ἅπτονται δὲ τοῦ νευρώδους πλεονασθέντες· οἱ μέσοι δὲ τὴν ἡλικίαν ἄριστοι πρὸς πόσιν ὡς οἱ ἀπὸ ἑπτὰ ἐτῶν. ἡ δὲ ποσότης παρά τε τὴν ἡλικίαν καὶ τὴν τοῦ ἔτους ὥραν καὶ ἔθη καὶ ποιότητα τοῦ οἴνου ὁριζέσθω· καὶ τὸ μὴ διψῆν δὲ ἄριστόν ἐστι παράγγελμα καὶ τὸ μετρίως βραχῆναι τὴν τροφήν. μέθη 13 δὲ πᾶσα, καὶ μάλιστα ἡ συνεχής, ἐπιβλαβής· τά τε γὰρ νεῦρα πολιορκούμενα καθ ἑκάστην ἡμέραν ἐνδίδωσι, καὶ παθῶν ὀξέων ἀρχάς ἐμποιεῖ ἡ καθημερινὴ πολυποσία· μετρίως δὲ οἰνοῦσθαι διά τινων ἡμερῶν, καὶ μάλιστα ἀπὸ ὑδροποσίας, ὠφέλιμον· μετασυγκρίνει γάρ πως, τάς τε αἰσθητὰς ἀνακαθαῖρον ἐκκρίσεις καὶ ἀδήλως ποροποιοῦν. δεῖ μέντοι καὶ μετὰ τὴν οἴνωσιν ὕδωρ πίνειν· ἀποθεραπείας γάρ τινα τῇ συγκρίθει τρόπον ἐπάγει. 14 ὀμφακίτης. ὁ δὲ καλούμενος ὀμφακίτης σκευάζεται ἰδίως ἐν Λέσβῳ, θειλοπεδευομένης μήπω κατὰ πάντα πεπείρου τῆς σταφυλῆς οὔσης, ἔτι δὲ ὀξιζούσης, ἐπὶ ἡμέρας γ΄ ἢ δ΄, ἕως ἂν ῥυσωθῶσιν οἱ βότρυες, καὶ μετὰ τὸ ἐκθλιβῆναι ἡλιάζεται ἐν κεραμεοῖς ὁ οἷνος. στυπτικὴν δἐ ἔχει τὴν δύναμιν καὶ εὐστόμαχον, ἁρμόζουσαν τοῖς δυσπεπτοῦσι καὶ ἐκλελυμένοις τὸν στόμαχον καὶ κισσώδεσι καὶ εἰλεώδεσι· δοκεῖ δὲ καὶ λοιμικαῖς διαθέσεσι βοηθεῖν καταρροφούμενος. 15 χρῄζουσι δὲ οἱ τοιοῦτοι οἶινοι ἐτῶν πλειόνων· ἄλλως γὰρ οὔκ εἰσι πότιμοι. δευτερίας. ὁ δὲ καλούμενος δευτερίας, ὅν ἔνιοι πότιμον καλοῦσι, σκευάζεται τὸν τρόπον τοῦτον· εἰς τὰ στέμφυλα, ὧν ἐξέθλιψας οἴνου μετρητὰς τριάκοντα, βάλε ὕδατος μετρητὰς γ΄ καὶ μείξας καὶ πατήσας ἔκθλιψον καὶ ἀφέψησον εἰς τὸ τρίτον. χοεῖ δὲ ἑκάστῳ τῶν ὑπολειφθέντων μετρητῶν μεῖξον ἁλὸς ξέστας β΄ καὶ μετὰ τὸν χειμῶνα διάχει εἰς κεράμια. χρῶ δὲ αὐτῷ μετʼ ἐνιαυτόν· ταχέως γὰρ ἐξίτηλος γίνεται. 16 ἁρμόζει δὲ ἐχʼ ὧν διστάζομεν οἷνον διδόναι, ἀναγκαζόμενοι διʼ ἐπιθυμίαν τοῦ νοσοῦντος, καὶ ἐπὶ τῶν ἐκ νόσου ἀναλαμβανόντων χρονίας. ἀδύναμος. γίνεται δὲ καὶ ὁ ἀδύναμος λεγόμενος, τὴν αὐτὴν ἔχων τῷ δευτερίᾳ δύναμιν. δεῖ δὲ ἴσον μέτρον ὕδατος τῷ τοῦ γλεύκους μείξαντας ἑψῆσαι πραέως πυρὶ μαλακῷ, ἄχρι ἄν ἐξαναλωθῇ τὸ ὕδωρ, καὶ μετὰ τοῦτο ψύξαντας καταγγίζειν εἰς ἀγγεῖον πεπισσωμένον. ἔνιοι δὲ θαλάττης πελαγίας καὶ 17 ὕδατος ὀμβρίου καὶ μέλιτος καὶ γλεύκους ἴσα μείξαντες καὶ καταγγίσαντες ἡλιάζουσιν ἐπὶ ἡμέρας τεσσαράκοντα· χρῶνται δ᾿ αὐτῷ πρὸς τὰ αὐτὰ μετʼ ἐνιαυτόν. ἀγριοσταφυλίτης· ὁ δὲ ἐκ τῆς ἀγρίας σταφυλῆς μέλας στυπτικὸς ὑπάρχων, ἁρμόζει κοιλίᾳ ῥευματιζομένῃ καὶ στομάχῳ, καὶ πρὸς τὰ ἄλλα, ὅσα στύψεως καὶ συστολῆς χρῄζει.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: DIOSC_DMM-5.7
TEXT:
ὁ δὲ καλούμενος μελιτίτης οἶνος δίδοται μὲν ἐν χρονίοις πυρετοῖς τοῖς ἀσθενῆ τὸν στόμαχον ἔχουσιν· ὑπομαλάττει γάρ τὴν κοιλίαν, οὖρα κινεῖ, στόμαχον ἀποκαθαίρει, ἁρμόζει καὶ ἀρθριτικοῖς καὶ νεφριτικοῖς καὶ τοῖς ἀσθενῆ τὴν κεφαλὴν ἔχουσι· χρήσιμος δὲ καὶ γυναιξὶν ὑδροποτούσαις· εὐώδης γάρ ἐστι καὶ θρεπτικός. διαφέρει δὲ τοῦ οἰνομέλιτος, 2 ὅτι ἐκεῖνο μὲν ἐξ αὐστηροῦ οἴνου καὶ παλαιοῦ καὶ ὀλίγου μέλιτος σκευάζεται, ὁ δὲ μελιτίτης πρὸς πέντε χοεῖς αὐστηροῦ γλεύκους λαμβάνει μέλιτος χοῦν ἕνα καὶ ἁλὸς κύαθον ἔνα. σκευάζειν δὲ δεῖ ἐν μεγάλῳ ἀγγείῳ, ἵνα τόπον ἔχῃ πρὸς τὸ ὑπερζεῖν, παραπάσσοντας τοῦ προειρημένου ἁλὸς κατʼ ὀλίγον, ἄχρι ἂν ἐκζέσῃ παυσαμένου δὲ καταγγίζειν εἰς κεράμια.
