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
- Do NOT extract `δύναμις`/`οὐσία` when they are generic discourse uses (e.g., rhetorical summary like \"ἡ δύναμις αὐτῶν\" without concrete pharmacodynamic specification in the same clause/window).

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
CONTEXT_PREV_SOURCE_ID: AET_LM-2.120
CONTEXT_PREV_TEXT:
ῥύπος ὁ ἐπιτρεφόμενος τοῖς τῶν προβάτων ἐρίοις, ἐξ οὗ τὸ καλούμενον ὕσσωπον σκευάζομεν, πεπτικῆς ἐστι δυνάμεως παραπλησίως τῷ βουτύρῳ, βραχὺ δὲ τι καὶ διαφορητικὸν ἔχει. σκευάζεται δὲ, ὥς φησι Διοσκορίδης, ὕσσωπος τὸν τρόπον τοῦτον. λαβὼν ἔρια ῥυπαρὰ τὰ ἐν ταῖς μασχάλαις τῶν προβάτων εὑρισκόμενα κονδὰ καὶ οὖλα καὶ μαλακὰ ἔκπλυνον θερμῷ ὕδατι, ἅμα ἐκθλίβων αὐτῶν πᾶσαν τὴν ῥυπαρίαν ἤτοι λιπαρίαν. εἶτα τούτων τὸ ἀπόπλυμα εἰς κρατῆρα πλατύστομον βαλὼν καὶ ἐπιχέας ἕτερον ὕδωρ ζέον ἀνατάρασσε λαμβάνων ἐκ τοῦ ὑγροῦ ποτηρίῳ ἢ ἑτέρῳ τινὶ καὶ ἐξ ὑψηλοῦ καταράσσων ἕως ἂν ἀφρίσῃ· εἶτα κατάρραινε θαλάσσῃ, εἰ πάρεστιν, εἰ δὲ μὴ ψυχρῷ ὕδατι καὶ ἔα καταστῆναι καὶ μετὰ τὸ ψυγῆναι ἀνελοῦ τὸ ἐπιπολάζον μυακίῳ καὶ βαλὼν εἰς ἕτερον ἄγγος καὶ ἐπιβαλὼν ψυχρὸν ὕδωρ ὀλίγον ἀνάκοπτε ταῖς χερσίν· εἶτα ἀποχέας τὸ ὕδωρ ἐπίβαλλε ἕτερον θερμὸν καὶ ἀνατάρασσε ὁμοίως, ὡς προείρηται, καὶ ἐπίρραινε θαλάσσῃ ἢ ψυχρῷ ὕδατι καὶ ἔα καταστῆναι καὶ μετὰ τὸ ψυγῆναι πάλιν ἀνελοῦ μυακίῳ καὶ ἀνάκοπτε τῇ χειρὶ ὁμοίως. καὶ πάλιν ἐκ τρίτου ἐπίχεε θερμὸν ὕδωρ καὶ τὸ αὐτὸ ποίει, καθὼς προείρηται, ἄχρις ἂν λευκὸς καὶ λιπαρὸς ὁ ὕσσωπος γένηται καὶ μηδὲν ἀκάθαρτον ἔχῃ. καὶ οὕτως βαλὼν ἐν ἀγγείῳ κεραμείῳ τίθει ἐν ἡλίῳ ἐπὶ ἡμέρας τινὰς καὶ φύλαττε καὶ πάντα δὲ τὰ προειρημένα ἐν ἡλίῳ θερινῷ ποίει. οὕτως γὰρ χρησιμώτερος γίγνεται καὶ λευκὸς καὶ οὐδὲν ἔχων σύσκληρον καὶ συνεστραμμένον, ὥσπερ ὁ δολιζόμενος κηρωτῇ ἢ ζύμῃ. ποιεῖ δὲ πρὸς τὰ περὶ δακτύλιον καὶ ὑστέραν σὺν μελιλώτῳ καὶ βουτύρῳ καὶ ἕτερα πλεῖστα. ὁ δὲ κεκαυμένος ὕσσωπος ποιεῖ τὴν ἐξ αὐτοῦ συναγομένην αἰθάλην ἢ λιγνὺν χρησιμωτάτην πρὸς διαβεβρωμένους καὶ ψωρώδεις κανθοὺς καὶ τετυλωμένα βλέφαρα καὶ τριχορροοῦντα. καίεται δὲ ἐνίοτε καὶ ὑπ' ὀστράκου καινοῦ, ἄχρις ἂν πυρωθεὶς ἀποβάλῃ τὸ λίπος. κείσθω δὲ τὸ ὄστρακον ἐπ' ἀνθράκων, εἶτα συνάξας τὸ κεκαυμένον καὶ λεάνας χρῶ πρὸς τὰ εἰρημένα.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: AET_LM-2.121
TEXT:
οὐχ ἅπασαι τῶν ζῴων αἱ σάρκες ἄνθρωπον τρέφουσιν, ἀλλ' ἐνίων εἰσὶ καὶ θανάσιμοι, ἔνιαι δὲ οὐχ ὡς τροφὴ μόνον προσφέρονται, ἀλλ' ὡς βοήθημα. καὶ τῶν τρεφουσῶν δὲ οὐ τὴν αὐτὴν ἅπασαι δύναμιν ἔχουσι. πάντων μὲν οὖν ἐδεσμάτων ἡ σὰρξ τῶν ὑῶν ἐστι τροφιμωτάτη καὶ εὔχυμος καὶ εὐπεπτοτέρα πάντων, τὰ τε ἄλλα καὶ διὰ τὴν πρὸς ἀνθρώπους ὁμοιότητα. τὰ δὲ βόεα κρέα τροφὴν μὲν αὐτὰ δίδωσιν οὔτε ὀλίγην οὔτ' εὐδιαφόρητον, αἷμα μέντοι παχύτερον ἢ προσῆκε γεννᾷ καὶ εἰ φύσει τις εἴη μελαγχολικώτερος τὴν κρᾶσιν, ἁλώσεταὶ τινι πάθει τῶν μελαγχολικῶν ἐν τῇ τούτων ἐδωδῇ πλεονάσας, τοιαῦτα δὲ ἐστι πάθη· καρκῖνος ἐλέφας λειχῆνες ψώρα τεταρταῖος πυρετός, ἥ τε ἰδίως ὀνομαζομένη μελαγχολία. καὶ σπλὴν δὲ ἐνίοις ᾔρθη διὰ τοιοῦτον χυμόν, ᾧ καχεξίαι τε καὶ ὕδεροι πολλάκις ἐπηκολούθησαν. ξηρότερος γὰρ καὶ θερμότερος πάμπολυ τῇ κράσει ἐστὶ βοὺς ὑός· οἱ δὲ μόσχοι τῶν τελείων βοῶν ἀμείνους ἔχουσιν εἰς πέψιν τὰς σάρκας, ὡς ὑγρότεροι τὴν κρᾶσιν. οὕτως δὲ καὶ οἱ ἔριφοι τῶν αἰγῶν ἀμείνους· ἧττον μὲν γὰρ βοὸς ἡ αἲξ ξηρὰ τὴν κρᾶσιν, ἀλλ' ἀνθρώπῳ καὶ συὶ παραβαλλομένη πολλῷ διαλλάττει. ὑγροτάτην δὲ ἔχουσι καὶ φλεγματώδη σάρκα οἱ ἄρνες. ἡ δὲ τῶν προβάτων σὰρξ περιττωματικωτέρα τέ ἐστι καὶ κακοχυμωτέρα. κακόχυμος δὲ καὶ ἡ τῶν αἰγῶν μετὰ δριμύτητος. ἡ δὲ τῶν τράγων χειρίστη καὶ πρὸς εὐχυμίαν καὶ πέψιν. ἐφεξῆς δὲ ἡ τῶν κριῶν, εἶθ' ἡ τῶν ταύρων. ἐν ἅπασι δὲ τούτοις ἡ τῶν εὐνουχισθέντων ἀμείνων. τὰ δὲ πρεσβυτικὰ χείριστα πρὸς πέψιν ἐστὶ καὶ εὐχυμίαν καὶ θρέψιν, ὥστε καὶ τῶν ὑῶν αὐτῶν, καὶ τοι γε ὑγρῶν ὄντων τὴν κρᾶσιν, οἱ γηράσαντες ἰνώδη καὶ σκληρὰν καὶ ξηρὰν καὶ διὰ τοῦτο δύσπεπτον ἴσχουσι τὴν σάρκα. καὶ ἡ τοῦ λαγωοῦ δὲ σὰρξ αἵματος μὲν παχυτέρου γεννητικὴ, βελτίων δὲ εἰς εὐχυμίαν ἢ κατὰ βοῦς καὶ πρόβατα. κακόχυμος δὲ οὐδὲν ἧττόν ἐστι καὶ ἡ τῶν ἐλάφων καὶ σκληρὰ καὶ δύσπεπτος. ἡ δὲ τῶν ἀγρίων ὄνων, ἐπεὶ καὶ ταύτην τινὲς ἐσθίουσιν, ὥσπερ καὶ τὴν τῶν ἡμέρων ὄντων ἐν Ἀλεξανδρείᾳ, κακοχυμοτάτη τε καὶ δυσπεπτοτάτη καὶ κακοστόμαχος καὶ προσέτι καὶ ἀηδὴς κατὰ τὰς ἐδωδάς, καθάπερ καὶ ἡ τῶν ἵππων τε καὶ καμήλων· καὶ ταῦτα γὰρ ἐσθίουσιν ὀνώδεις τε καὶ καμηλώδεις ἄνθρωποι, τήν τε ψυχὴν καὶ τὸ σῶμα καὶ τὰ τῶν ἄρκτων κρέα ἔνιοι προσφέρονται. καὶ τὰ τούτων ἔτι χείρω τῶν λεόντων τε καὶ παρδάλεων. περὶ δὲ τῶν κυνῶν τὶ δεῖ καὶ λέγειν; ὡς τοὺς νέους τε καὶ λιπαροὺς αὐτῶν ἐσθίουσι πάμπολλοι, ὄντα τὰ τοιαῦτα πάντα ξηρότατα φύσει καὶ δριμεῖαν τροφὴν παρέχοντα τῷ σώματι καὶ παρὰ τοὺς τρόπους δὲ τῶν σκευασιῶν αὐτῶν μᾶλλον ἢ ἧττον τρέφει, καὶ μᾶλλον καὶ ἧττον πέττεται. ὅσα μὲν γὰρ ὀπτῶντες ἢ τηγανίζοντες ἐσθίουσι, ξηροτέραν τροφὴν δίδωσι τῷ σώματι· ὅσα δὲ ἕψοντες καὶ ἀρτύοντες προσφέρονται μεταξὺ τούτων εἰσί. καὶ αὐτῶν δὲ τούτων οὐ μικρὰ διαφορὰ γίγνεται παρὰ τὸν τῆς ἀρτύσεως τρόπον. καὶ διὰ ταῦτα ξηραίνειν μὲν θέλων τὸ σῶμα τῶν ξηροτέρων τῇ κράσει ζῴων δώσεις τὴν σάρκα, θερμαίνειν δὲ βουλόμενος τῶν θερμοτέρων καὶ ψυχροτέρων καὶ ὑγροτέρων ὁμοίως τοῖς καταλλήλοις δώσεις.
