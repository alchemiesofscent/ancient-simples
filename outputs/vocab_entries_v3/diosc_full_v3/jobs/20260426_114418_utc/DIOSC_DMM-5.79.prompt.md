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
CONTEXT_PREV_SOURCE_ID: DIOSC_DMM-5.78
CONTEXT_PREV_TEXT:
λεπὶς δὲ ἡ μὲν ἐκ τῶν Κυπρίων μετάλλων παχεῖα, καλουμένη δὲ ἡλῖτις, καλή· φαύλη δὲ ἡ ἐκ τοῦ λευκοῦ χαλκοῦ, λεπτὴ καὶ ἀσθενὴς ὑπάρχουσα, ἣν ἀποδοκιμάζομεν, ἐγκρίνοντες τὴν παχεῖαν καὶ ἔγκιρρον καὶ ὄξους ἐπιρραινομένου ἰουμένην. δύναμιν δὲ ἔχει στυπτικήν, σταλτικήν, λεπτυντικήν, σηπτικήν, νομῶν ἐφεκτικήν, ἀπουλωτικήν· πινομένη δὲ μετὰ μελικράτου ὕδωρ ἄγει. τινὲς δὲ φυρῶντες αὐτὴν μετὰ ἀλεύρου 2 ἐν καταποτίῳ διδόασι. μείγνυται δὲ καὶ ταῖς ὀφθαλμικαῖς δυνάμεσι, ξηραίνουσα τὰ ῥεύματα καὶ βλέφαρα τραχέα ἀποτήκουσα. 3 πλύνεται δὲ οὕτως· καθάρας τῆς ξηρᾶς λεπίδος ἡμιμναῖον βάλε εἰς θυίαν μεθʼ ὕδατος διαυγοῦς, καὶ συναναταράξας τῇ χειρὶ ἐπιμελῶς, ἄχρι ἂν ὑποστῇ ἡ λεπίς, ἀφαίρει τὰ ἐφεστῶτα, ἀποχέας τε τὸ ὕδωρ ἐπίχει ὀμβρίου ὕδατος κύαθον ἕνα, πλατείᾳ τε τῇ χειρὶ τρῖβε εὐτόνως πρὸς τῇ θυίᾳ οἱονεὶ ἀποψώχων. 4 ὅταν δὲ ἄρξηται ἀνιέναι τινὰ γλισχρότητα, κατὰ μικρὸν ὕδωρ προσεπίχει ἄχρι κυάθων ἓξ τρίβων συντόνως, ἀναλαβών τε τὴν λεπίδα τῇ χειρὶ ὡς πρὸς τὸ πλευρὸν τῆς θυίας τρῖβε εὐτόνως, καὶ ἐξιπώσας ἀνελοῦ τὸ ἀπορρυὲν εἰς πυξίδα ἐρυθροῦ χαλκοῦ· τοῦτο γάρ ἐστι τὸ ὥσπερ ἄνθος τῆς λεπίδος καὶ εὔτονον τῇ δυνάμει καὶ εὐθετοῦν εἰς τὰ ὀφθαλμικά, τὸ δὲ λοιπὸν ἄτονον. καὶ τὸ καταλειφθὲν δὲ ὁμοίως πλύνων ἀναιροῦ, ἄχρι ἂν μηδεμίαν γλισχρότητα ἀποκρίνῃ, τὸ δὲ λοιπὸν δεῖ σκεπάσαντα ὀθονίῳ ἐᾶσαι ἀκίνητον ἐπὶ δύο ἡμέρας, εἶτα ἀποχέαντα τὸ ἐφεστηκὸς ὕδωρ καὶ ξηράναντα ἀποτίθεσθαι εἰς πυξίδα. ἔνιοι δὲ καὶ ταύτην πλύνουσιν ὡς τὴν καδμείαν καὶ ἀποτίθενται. λεπίδος δὲ στομώματος δύναμίς ἐστιν ἡ αὐτὴ τῇ τοῦ χαλκοῦ λεπίδι, καὶ πλύσις καὶ ἀπόθεσις ὁμοία, ἐν μέντοι τῷ τὴν κοιλίαν καθαίρειν λείπεται τῆς τοῦ χαλκοῦ.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: DIOSC_DMM-5.79
TEXT:
ἰὸν δὲ τὸν ξυστὸν οὕτως σκευαστέον· εἰς πιθάκνην ἢ ἄλλο ὅμοιον ἀγγεῖον ἐγχέας δριμύτατον ὄξος ἐπικατάστρεψον χαλκοῦν ἀγγεῖον· καλὸν μέν, εἰ καμαροειδὲς εἴη, εἰ δὲ μή γε, ἰσόπεδον· ἔστω δὲ ἐσμηγμένον καὶ διαπνοὴν μηδεμίαν ἔχον· διὰ δὲ ἡμερῶν δέκα ἀναιρούμενος τὸ πῶμα ἀπόξυε τὸν ἐπιτρέχοντα ἰόν. ἢ λεπίδα ἀπὸ τοῦ αὐτοῦ ποιήσας χαλκοῦ ἐγκρέμασον εἰς τὸ αὐτὸ ἀγγεῖον, ἵνα μὴ ψαύσῃ τοῦ ὄξους, καὶ διὰ τῶν ἴσων ἡμερῶν ἀπόξυε. ἢ εἰς τὰ στέμφυλα μὴ πρόσφατα ὄντα, ὀξίζοντα 2 ἐγκρύψας μᾶζαν ἢ λεπίδα μίαν ἢ καὶ πλείονας ὡσαύτως ἀναστρέφου. ἔνεστι δὲ καὶ ἐκ ῥινημάτων ποιῆσαι ἢ λεπίδων, αἷς περιεχόμενα τὰ χρυσᾶ πέταλα ἐλαύνεται, ἐάν τις αὐτὰ ἐπιρραίνων ὄξει ἀνακινῇ τρὶς ἢ τετράκις τῆς ἡμέρας, ἄχρι ἂν παντελῶς ἰωθῇ. γεννᾶσθαι δέ φασιν ἰὸν καὶ ἐν τοῖς Κυπριακοῖς μετάλλοις, 3 τὸν μὲν λίθοις τισὶν ἐπανθοῦντα τῶν ἐχόντων τὸν χαλκόν, τὸν δέ ἔκ τινος σπηλαίου στάζοντα ἐν τοῖς ὑπὸ κύνα καύμασι· καὶ τὸν μὲν ὀλίγον τε καὶ κάλλιστον εἶναι, τὸν δὲ ἐκ τοῦ σπηλαίου δαψιλῆ μὲν ἐπιρρεῖν καὶ εὔχρουν, φαῦλον δὲ ὑπάρχειν διὰ τὸ πολλοῖς ἀναμεμεῖχθαι λιθώδεσι. 4 δολοῦται δὲ καὶ ἄλλοις πολλοῖς μισγομένοις, μᾶλλον δὲ τούτοις· τινὲς μὲν γὰρ κισήρει, οἱ δὲ μαρμάρῳ, ἄλλοι δὲ χαλκάνθῳ κυκῶσιν αὐτόν. καταλημψόμεθα δὲ τὴν μὲν κίσηριν καὶ τὸ μάρμαρον διὰ τοῦ νοτίσαι τὸν ἀντίχειρα τῆς εὐωνύμου χειρὸς καὶ τῷ ἑτέρῳ προστρίβειν τοῦ ἰοῦ τι μέρος· συμβαίνει γὰρ τὸν μὲν διαχεῖσθαι, τὸ δὲ ἀπὸ τῆς κισήρεως καὶ μαρμάρου μένειν ἀδιάχυτον καὶ τέλος ἀπολευκαίνεσθαι τῇ ἐπὶ πλεῖον παρατρίψει καὶ τῇ τοῦ ὑγροῦ παραπλοκῇ. 5 οὐ μὴν ἀλλὰ καὶ διὰ τῆς τῶν ὀδόντων ἐπερείσεως· λεῖον γὰρ ὑποπίπτει καὶ οὐ τραχὺ τὸ ἀμιγές. τὸ δὲ χαλκανθὲς ἀπελέγχεται τῷ πυρί· εἰ γάρ τις ἐμπάσας τὸν οὕτως δεδολωμένον ἰὸν ἐπὶ λεπίδα ὄστρακον, τούτων τὸ ἕτερον ἐπὶ θερμῆς τέφρας ἢ ἀνθρακιᾶς θείη, μεταβάλλει καὶ κατερυθραίνεται τὸ χαλκανθὲς διὰ τὸ φύσει καιόμενον αὐτὸ τοιαύτην ἔχειν χρόαν. 6 τοῦ δὲ λεγομένου σκώληκος ἰοῦ δισσὸν εἶδος ὑπάρχει· ὁ μὲν γὰρ ὀρυκτός ἐστιν, ὁ δὲ σκευάζεται οὕτως· εἰς θυίαν Κυπρίου χαλκοῦ, ἔχουσαν δὲ καὶ δοίδυκα ἀπὸ τῆς αὐτῆς πεποιημένον ἥλης, ἐγχέας ὄξους λευκοῦ καὶ δριμέος κοτύλης ἥμισυ τρῖβε, ἕως οὗ γλοιωθῇ, εἶτα ἔμβαλε στυπτηρίας στρογγύλης ⋖ δ´ καὶ ἁλὸς ὀρυκτοῦ διαφανοῦς ἢ θαλασσίου ὡς ὅτι λευκοτάτου καὶ στερεοῦ, εἰ δὲ μή γε, νίτρου τὸ ἴσον· εἶτα λέαινε ἐν ἡλίῳ ἐν τοῖς ὑπὸ κύνα καύμασιν, ἕως τῇ μὲν χρόᾳ ἰώδης, τῇ δὲ συστάσει ῥυσώδης γένηται, καὶ οὕτως ἀναπλάσας σκώληκας τοῖς Ῥοδιακοῖς ὁμοίους ἀποτίθεσο. ἐνεργὴς δὲ καὶ εὔχρους 7 γίνεται ἄγαν, ἐὰν ὄξους μὲν λάβῃ μέρος ἕν, οὔρου δὲ παιδίου μέρη δύο, τὰ δ᾿ ἄλλα ὡς προείρηται. τινὲς δὲ ἀποτετευγμένῳ τῷ ξυστῷ κόμι μείξαντες ἀναπλάσσουσι καὶ πωλοῦσιν, ὃν παραιτητέον ὡς φαῦλον. ἔστι δέ τις καὶ ὑπὸ τῶν χρυσοχόων γινόμενος ἰὸς διὰ θυίας καὶ δοίδυκος Κυπρίου χαλκοῦ, ἔτι δὲ οὔρου παιδίου, ᾧ τὸ χρυσίον κολλῶσιν. ἀναλογοῦσι δὲ κοινῶς 8 οἱ προειρημένοι ἰοὶ κεκαυμένῳ χαλκῷ, μᾶλλον δὲ ἐρρωμένοι περὶ τὴν ἐνέργειαν. ἰστέον δὲ ὅτι προέχει μὲν αὐτῶν ὁ ὀρυκτὸς σκώληξ· ἐχόμενος δ᾿ ἐστὶν ὁ ξυστός, εἶτα ὁ σκευαστός· δηκτικώτερος μέντοι καὶ μᾶλλον στύφων οὗτος ὑπάρχει, ὁ δὲ τῶν χρυσοχόων ἀνάλογος τῷ ξυστῷ. δύναται δὲ πᾶς ἰὸς στύφειν, θερμαίνειν, ἀποσμᾶν τὰς ἐν 9 ὀφθαλμοῖς οὐλὰς καὶ λεπτύνειν, δάκρυον ἄγειν, νομάς ἴσχειν, τραύματα ἀφλέγμαντα τηρεῖν, τὰ παλαιὰ ἀπουλοῦν ἕλκη σὺν ἐλαίῳ καὶ κηρῷ. σὺν μέλιτι δὲ ἑψηθέντες τύλους καὶ τὰ ῥυπαρὰ τῶν ἑλκῶν ἀνακαθαίρουσιν. 10 ἀμμωνιακῷ δὲ ἀναλημφθέντες εἰς κολλούρια σύριγγας καὶ τύλους ἐκτήκουσι, χρήσιμοι δὲ καὶ πρὸς ἐπουλίδας καὶ τὰς τῶν οὔλων ἐξοχάς. ἱκανῶς δὲ καὶ βλέφαρα λεπτύνουσι σὺν μέλιτι ἐγχριόμενοι· δεῖ δὲ πυριᾶν μετὰ τὴν ἔγχρισιν σπόγγῳ ἐξ ὕδατος θερμοῦ· ἀναλημφθέντες δὲ ῥητίνη τερεβινθίνῃ σὺν χαλκάνθῳ ἢ νίτρῳ λέπρας ἐξάγουσι. 11 καυστέον δὲ ὃν ἂν θέλῃς ἰὸν οὕτως· θλάσας αὐτὸν εἰς ὁλοσχερέστερα μέρη καὶ τηγάνῳ κεραμεῷ ἐπιθεὶς ἀπέρεισαι ἐπ᾿ ἀνθράκων διαπύρων, κίνει τε, ἕως ἂν μεταβάλῃ καὶ ὑποσποδίσῃ τῇ χρόᾳ· λοιπὸν δὲ ψύξας ἀποτίθεσο καὶ χρῶ. τινὲς δὲ ἐν ὠμῇ χύτρᾳ αὐτὸν καίουσιν ὡς προείρηται, οὐκ εἰς τὸ αὐτὸ δὲ πάντοτε καιόμενος μεταβάλλει χρῶμα.
