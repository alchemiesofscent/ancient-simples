# Vocab extractor prompt

```prompt

## Prompt (paste into LLM system/user message as-is)

You are an extraction agent for the Ancient Simples Project. Read the input text (Ancient Greek, possibly with TEI tags) and extract candidate terms relevant to ancient pharmacy/science. Output must be strictly valid JSON (no commentary).

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
- `normalized`: lowercase + strip accents/breathings ONLY; preserve iota subscripts; keep Greek script (no transliteration)
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

### Galenic quality tracking (mandatory)
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
CONTEXT_PREV_SOURCE_ID: GAL_ALIM-2.69
CONTEXT_PREV_TEXT:
Καὶ τούτων τῶν φυτῶν τὰς μὲν ῥίζας ἐσθίουσιν οἱ ἄνθρωποι πλειστάκις, ὀλιγάκις δὲ τὸν καυλὸν καὶ τὰ φύλλα. δριμεῖαν δ' ἱκανῶς ἔχοντα δύναμιν ἀνὰ λόγον αὐτῇ θερμαίνει τε τὸ σῶμα καὶ λεπτύνει τοὺς ἐν αὐτῷ παχεῖς χυμοὺς καὶ τέμνει τοὺς γλίσχρους. ἑψηθέντα μέντοι δὶς ἢ καὶ τρὶς ἀποτίθεται μὲν τὴν δριμύτητα, λεπτύνει δ' ὅμως ἔτι καὶ τροφὴν βραχυτάτην δίδωσι τῷ σώματι. τέως δ' οὐδ' ὅλως ἐδίδου πρὶν ἑψηθῆναι. τό γε μὴν σκόροδον οὐ μόνον ὡς ὄψον, ἀλλὰ καὶ ὡς φάρμακον ὑγιεινὸν ἐσθίου|σιν, ἐκφρακτικῆς τε καὶ διαφορητικῆς ὑπάρχον δυνάμεως. ἑψηθὲν δ' ἐπ' ὀλίγον, ὡς ἀποθέσθαι τὴν δριμύτητα, τῇ μὲν δυνάμει καταδεέστερον γίγνεται, τὴν κακοχυμίαν δ' οὐκέτι διασῴζει, καθάπερ οὐδ' ὅταν ἑψήσῃ τις δὶς τὰ πράσα καὶ τὰ κρόμυα. τὰ δ' ἀμπελόπρασα διαφέρει τῶν πράσων τοσοῦτον, ὅσον κἀν τοῖς ἄλλοις ἅπασι τοῖς ὁμογενέσι τὰ ἄγρια τῶν ἡμέρων. ἀποτίθενται δ' εἰς τοὐπιὸν ἔτος ὅλον ἔνιοι, καθάπερ τὰ κρόμυα, δι' ὄξους συντιθέντες, οὕτω καὶ τὰ ἀμπελόπρασα, καὶ γίγνεται πρός τε τὴν ἐδωδὴν ἀμείνω καὶ ἧττον κακόχυμα. φείδεσθαι δὲ χρὴ τῆς συνεχοῦς ἐδωδῆς ἁπάντων τῶν δριμέων, καὶ μάλισθ' ὅταν ὁ προσφερόμενος αὐτὰ χολωδέστερος ᾖ φύσει. μόνοις γὰρ τοῖς ἤτοι τὸν φλεγματώδη χυμὸν ἢ τὸν ὠμὸν καὶ παχὺν καὶ γλίσχρον ἠθροικόσιν ἐπιτήδεια τὰ τοιαῦτα τῶν ἐδεσμάτων ἐστίν.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_ALIM-3.15
TEXT:
Τὸ δ' ὀξύγαλα καλούμενον οὐ βλάπτει μὲν τοὺς ὀδόντας, ὅσοι γε κατὰ φύσιν ἔχουσιν, ὅσοι δ' ἤτοι διὰ φυσικὴν δυσκρασίαν ἤ τιν' ἐπίκτητον διάθεσίν εἰσι ψυχρότεροι τοῦ δέοντος, οὗτοι μόνοι βλάπτονται, καθάπερ ὑπὸ τῶν ἄλλων ψυχρῶν, οὕτω καὶ ὑπὸ τοῦδε· καὶ τὸ σύμπτωμα αὐτοῖς ἐνίοτε γίγνεται τὸ καλούμενον αἱμωδία, τοιοῦτον οἷον ἐπὶ τοῖς ἀώροις συκαμίνοις ὅσα τ' ἄλλα στρυφνὰ καὶ ὀξέα συμβαίνειν εἴωθε. πρόδηλον δ', ὅτι καὶ γαστὴρ ἡ μὲν ψυχροτέρα καθ' ἡντινοῦν αἰτίαν οὐ πέττει καλῶς τὸ ὀξύγαλα, τῇ συμμέτρως δ' ἐχούσῃ δύσπεπτον | μέν, οὐ μὴν ἄπεπτόν γε παντάπασίν ἐστιν. ὅσαι δὲ θερμότεραι τοῦ προσήκοντός εἰσι γαστέρες, εἴτ' ἐξ ἀρχῆς εἴτ' ἔκ τινος ὕστερον αἰτίας εἰς τοιαύτην κρᾶσιν ἀχθεῖσαι, πρὸς τῷ μηδὲν βλάπτεσθαι καὶ χρηστοῦ τινος ἀπολαύουσιν ἐκ τῶν τοιούτων ἐδεσμάτων. αὗται καὶ προψυχθὲν αὐτὸ διὰ χιόνος περιπλάσεως ἀλύπως φέρουσιν, ὥσπερ καὶ ἄλλα πολλὰ τῶν τοιούτων ἐδεσμάτων καὶ δηλονότι καὶ τὸ ὕδωρ αὐτὸ παρασκευασθὲν ὁμοίως. ἐφ' ᾧ καὶ θαυμάζειν ἐπῆλθέ μοι πολλοὺς τῶν ἰατρῶν ἁπλῶς ἀποφηναμένους ὑπὲρ ἑκάστης τροφῆς, τῆς μὲν ὡς ὠφελούσης ἡμᾶς, τῆς δ' ὡς βλαπτούσης, εὐπέπτου τε καὶ δυσπέπτου, κακοχύμου τε καὶ εὐχύμου, τροφίμου τε καὶ ἀτρόφου, κακοστομάχου τε καὶ εὐστομάχου, καὶ κοιλίαν ὑπαγούσης τε καὶ ἱστάσης ἤ τιν' ἄλλην ἀρετὴν ἢ κακίαν ἐχούσης. ἐπί τινων μὲν γὰρ ἐγχωρεῖ φάναι πᾶσιν ἀνθρώποις εἶναι κακόχυμον ἢ δύσπεπτον ἢ κακοστόμαχον ἔδεσμα τόδε τι, περὶ δὲ τῶν πλείστων οὐχ οἷόν τε χωρὶς διορισμοῦ διὰ μιᾶς ἀποφάσεως ἀληθεῦσαι. μακροῦ δ' ἐξ ἀνάγκης ἐσομένου τοῦ παντὸς λόγου γραφόν|των ἡμῶν ἐφ' ἑκάστου τῶν ἐδεσμάτων τοὺς ἀπὸ τῶν φυσικῶν κράσεων ἐπικτήτων τε διαθέσεων διορισμοὺς ἄμεινον ἔδοξεν εἶναι καθόλου μὲν ἐξ ἀρχῆς τῆς διδασκαλίας ἐπιδεῖξαι τὴν μέθοδον, ὡς ἐποιήσαμεν ἐν τῷ πρώτῳ τῶνδε τῶν ὑπομνημάτων, ἀναμιμνῄσκειν δ' ἐπὶ τῶν κατὰ μέρος ἐνίοτε, καὶ μάλιστ' ἐφ' ὧν ἡ φύσις οὐχ ἁπλῆ, καθάπερ ἀμέλει κἀπὶ τοῦ γάλακτός ἐστι, συγκειμένου μὲν ἐξ ἐναντίων οὐσιῶν τε καὶ δυνάμεων, ὁμοιομεροῦς δὲ φαινομένου πρός γε τὴν αἴσθησιν. οὕτω γὰρ αὐτῷ συμβαίνει, κἂν κάλλιστον ᾖ, παρὰ τὴν τῶν κοιλιῶν διαφορὰν ἐνίοτε μὲν ὀξύνεσθαι, κνισώδη δ' αὖθις ἐφ' ἑτέρου τὴν ἐρυγὴν ἀναπέμπειν, καίτοι γ' ἐναντίων οὐσῶν τῶν διαθέσεων, καθ' ἃς ὀξῶδες ἢ κνισῶδες γίγνεται τὸ κατὰ τὴν κοιλίαν ἀπεπτηθέν. ἡ μὲν γὰρ ἔνδεια τῆς θερμασίας ὀξύνειν αὐτὸ πέφυκεν, ἡ δ' ὑπερβολὴ κνισοῦν. γίγνεται δ' ἄμφω ταῦτα τῷ γάλακτι διὰ τὸ μὴ μόνον ἔχειν ἐν ἑαυτῷ τὴν ὀρώδη φύσιν, ἀλλὰ καὶ τὴν λιπαρὰν καὶ τὴν τυρώδη. τὸ γοῦν ὀξύγαλα διὰ τὴν αἰτίαν ταύτην | οὐδέποτε κνισῶδες ἀπεπτηθὲν γίγνεται, κἂν εἰς χολωδεστάτην ἢ πυρωδεστάτην ἐμπέσῃ κοιλίαν. οὔτε γὰρ ἐν αὑτῷ τὴν θερμὴν καὶ δριμεῖαν ἔχει ποιότητα καὶ δύναμιν, ἧς μετέχει τὸ γάλα διὰ τὸν ὀρόν, οὔτε τὴν λιπαράν τε καὶ μετρίως θερμήν, ἣν ἐκέκτητο διὰ τὸ λιπαρὸν τὸ ἐν ἑαυτῷ· μόνον γὰρ ὑπολείπεται κατὰ τὴν τοιαύτην σκευασίαν τὸ τυρῶδες, οὐδὲ τοῦτο τοιοῦτον τὴν φύσιν, ὁποῖον ἐξ ἀρχῆς ὑπῆρχεν, ἀλλ' ἐπὶ τὸ ψυχρότερον ἐκτετραμμένον. ἀρκεῖ τοιγαροῦν ἐπ' ὀξυγάλακτος εἰπεῖν, ὅτι ψυχρόν τ' ἐστὶ καὶ παχύχυμον. ἕπεται γὰρ τούτοις τὸ μὴ ῥᾳδίως αὐτὸ πέττεσθαι πρὸς τῆς συμμέτρως ἐχούσης κράσεως· ἐπ' ἐκείνην γὰρ ἀναφέρεσθαι τὸν λόγον ἠξίωσα πολλάκις ἤδη κατὰ πάσας τὰς ἐμὰς πραγματείας, ὅταν ἁπλῶς ἀποφαίνωμαί τι. καὶ μέντοι καὶ τὸν ὠμὸν ὀνομαζόμενον χυμόν, οὗ τὴν φύσιν ἔμπροσθέν τε διῆλθον ἑτέρωθί τε κατὰ τὸν προηγούμενον λόγον ἐξηγησάμην, εὔλογόν ἐστιν ἐκ τῶν τοιούτων ἐδεσμάτων πλεῖστον γεννᾶσθαι. χρήσιμον δ' εἶναι τὸ ἔδεσμα τοῦτο ταῖς πυρωδεστέραις κοιλίαις οὐδὲν ἄλογον, ὥσπερ γε καὶ ταῖς ψυχροτέραις ἐναντιώτατον. οὐ μὴν | οὐδὲ τοῦτο δεῖ καθ' ἕκαστον τῶν ἐδεσμάτων γράφειν, ἀλλ' ἀναμιμνῄσκειν ἐπί τινων μόνον, ὡς ὁ τοιόσδε χυμός, ὁποῖος ἐξ ὀξυγάλακτός τε καὶ τυροῦ καὶ τῶν παχυχύμων ἁπάντων γίγνεται, λίθους ἐν νεφροῖς πέφυκε γεννᾶν, ὅταν ὦσι θερμότεροι τοῦ δέοντος ἤτοι κατὰ φυσικὴν δυσκρασίαν ἢ κατά τινα ἄλλην ὕστερον ἐγγενομένην αὐτοῖς διάθεσιν, οὐ μὴν ἀνὰ λόγον γε τῇ θερμασίᾳ τὰς διεξόδους εὐρείας ἔχωσιν. αἱ γάρ τοι νοσωδέσταται κατασκευαὶ τῶν σωμάτων ἐξ ἐναντίων τῇ κράσει σύγκεινται μορίων, ὡς εἶναι γαστέρα μέν, εἰ τύχοι, θερμὴν ἱκανῶς, ἐγκέφαλον δὲ ψυχρόν. οὕτω δὲ καὶ πνεύμων ἐνίοτε καὶ θώραξ ὅλος ψυχρός ἐστιν ἐπὶ θερμῇ γαστρί. πολλάκις δὲ καὶ τοὐναντίον ἕκαστον μὲν τῶν ἄλλων θερμότερον ὑπάρχει τοῦ δέοντος, ἡ γαστὴρ δὲ μόνη ψυχροτέρα, καί ποτε κεφαλὴ μὲν ὅλη ψυχροτέρα, θερμότερον δὲ τὸ ἧπαρ ἐπί τε τῶν ἄλλων μορίων ὡσαύτως. διὸ καὶ κατ' ἀρχὰς ἐδείκνυον ὠφελιμωτάτην εἶναι τὴν περὶ τῶν ἐν ταῖς τροφαῖς δυνάμεων διδασκαλίαν, ὅταν ἐξηγῶνται τὴν καθ' ὑγρότητα καὶ ξηρότητα καὶ θερμότητα καὶ ψυχρότητα | διαφορὰν ἔτι τε τὸ γλίσχρον ἢ παχὺ τῆς οὐσίας αὐτῶν, καὶ πρὸς τούτοις, εἴθ' ὁμοιομερής ἐστιν εἴτ' ἐξ ἐναντίων ταῖς κράσεσι σύγκειται, καθάπερ τὸ γάλα. πρὸς δὲ τὴν τούτων διάγνωσιν ἐκ τῆς ὀσμῆς καὶ τῆς γεύσεως ἔτι τε τῶν ἄλλων συμπτωμάτων ἔφην ἡμᾶς ποδηγεῖσθαι, περὶ ὧν ἐν ἀρχῇ τῆσδε τῆς πραγματείας διῆλθον, ὥσπερ καὶ νῦν ἐπὶ τοῦ γάλακτος, ἐπιδεικνὺς αὐτοῦ τὴν φύσιν ἐξ ὧν ἴσχει συμπτωμάτων, ἤτοι θερμαινόμενον ἢ διὰ πυτίας πηγνύμενον ἢ ὁπωσοῦν ἄλλως διακρινομένων τῶν μορίων αὐτοῦ. καὶ γὰρ καὶ ἡ σχίσις καλουμένη τοῦτ' ἐργάζεται χωρὶς τῆς πυτίας, ὅταν ἱκανῶς προθερμήναντες τὸ γάλα καταρράνωμεν ὀξυμέλιτι ψυχρῷ. ταὐτὸν δ' ἐργαζόμεθα καὶ δι' οἰνομέλιτος, ἐνίοτε δὲ καὶ χωρὶς τοῦ καταρρᾶναι τὴν οὐσίαν αὐτοῦ καθιέντες ἀγγεῖον ὕδωρ ἔχον ψυχρότατον ἐργαζόμεθα τὴν σχίσιν. ἄνευ δὲ πυτίας καὶ τὸ μετὰ τὴν ἀποκύησιν ἀμελχθὲν αὐτίκα πήγνυται πυρωθὲν ἐπὶ θερμῆς σποδιᾶς ὀλίγῳ χρόνῳ. καλεῖν δ' ἐοίκασιν οἱ παλαιοὶ <κωμικοὶ> τὸ οὕτω παγὲν γάλα πυριάτην· οἱ δὲ παρ' ἡμῖν ἐν Ἀσίᾳ πυρίεφθον ὀνομάζουσιν αὐτό. τοῦτο μὲν οὖν ἀκρι|βῶς ἐστι γάλα χωρὶς οὐσίας ἑτέρας. ὅταν δὲ μέλι μίξαντες αὐτῷ διὰ πυτίας πήξωσι, χωρίζεται μὲν ἐν τῷδε τῷ ἔργῳ τό τε λεπτὸν καὶ ὑδατῶδες αὐτοῦ, προσφέρονται δ' ἔνιοι μὲν τὸ πεπηγὸς αὐτοῦ μόνον σύνθετον ὑπάρχον ἔκ τε τοῦ τυρώδους ἐν τῷ γάλακτι καὶ τοῦ θερμοῦ καὶ πυρώδους ἐν τῇ τῆς πυτίας δυνάμει καὶ τοῦ μιχθέντος αὐτοῖς μέλιτος. ἔνιοι δὲ καὶ τὸν ὀρὸν τῷ παγέντι συγκαταπίνουσιν, ἤτοι γε ὡσαύτως πάντα μετὰ παντὸς ἢ θάτερον αὐτῶν πλέον θατέρου. συμβήσεται δὲ δηλονότι τοῖς μὲν μᾶλλον ὑπαχθῆναι τὴν γαστέρα, τοῖς δ' ἧττον, ἀνὰ λόγον τῇ ποσότητι τῆς ὀρώδους ὑγρότητος. εὔδηλον δέ, ὅτι καὶ τραφῆναι τὸ σύμπαν σῶμα μᾶλλον μὲν ὑπάρξει τοῖς τὸ πεπηγὸς μόνον ἐδηδοκόσιν, ἧττον δὲ τοῖς συγκαταπιοῦσιν αὐτῷ τι καὶ τῆς ὀρώδους ὑγρότητος, ἔτι δ' ἧττον, ὅσοι τὸ μὲν πεπηγὸς ὀλίγον προσηνέγκαντο, τὸ δ' ὀρῶδες πλεῖστον. οὕτω δὲ κἀπὶ τοῦ μετὰ τὴν ἀποκύησιν παγέντος, ἤτοι χωρὶς μέλιτος ἢ σὺν αὐτῷ, διαφορά τις οὐ σμικρὰ γενήσεται. δυσπεπτότερον γάρ ἐστι καὶ παχυχυμότερον ἔτι τε βραδυπορώτερον εἰς τὴν κάτω διέξοδον, ὅταν μὴ | προσλάβῃ μέλιτος. ἥ γε μὴν ὅλου τοῦ σώματος θρέψις ἐξ ἀμφοτέρων γίγνεται δαψιλής. ταῦτ' ἀρκεῖ περὶ δυνάμεως γάλακτος ἐπίστασθαι κατὰ τὴν νῦν ἡμῖν ἐνεστῶσαν πραγματείαν· ὅσα γὰρ εἰς νόσους ἐστὶ χρήσιμα ἢ τοῖς φθίνουσιν ὁπωσοῦν ἢ τοῖς ἕλκος ἔχουσιν ἐν πνεύμονι, ταῦτ' ἴδια τῆς θεραπευτικῆς ἐστι μεθόδου.
