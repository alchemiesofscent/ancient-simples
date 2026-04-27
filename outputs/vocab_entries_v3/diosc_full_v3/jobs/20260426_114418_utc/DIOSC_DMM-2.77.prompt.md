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
CONTEXT_PREV_SOURCE_ID: DIOSC_DMM-2.76
CONTEXT_PREV_TEXT:
στέαρ πρὸς μὲν τὰ περὶ μήτραν ἁρμόζει τὸ νεαρὸν χήνειον ἢ ὀρνίθειον καὶ δίχα ἁλῶν τεθεραπευμένον, πολέμιον δὲ ὑστέρᾳ τὸ ἡλισμένον καὶ τὸ τῷ χρόνῳ μεταβεβληκὸς εἰς δριμύτητα. πρόσφατον δὲ τούτων λαβών τι καὶ ἐξυμενίσας ἔμβαλε εἰς λοπάδα καινὴν κεραμεᾶν, δὶς τοσοῦτον χωροῦσαν ἢ ὅσον ἐστὶ τὸ μέλλον θεραπεύεσθαι, εἶτα θεὶς εἰς ὀξύτατον ἥλιον τὸ ἀγγεῖον κεκαλυμμένον ἐπιμελῶς, ὑπὸ χεῖρα τὸ ἀποτηκόμενον ἀπήθει εἰς ἕτερον ἀγγεῖον ὀστράκινον, ἕως ἂν ἅπαν δαπανήσῃ τοῦτο δὲ εἰς κατάψυχρον τόπον ἀποτίθεσο καὶ χρῶ. τινὲς δὲ 2 ἀντὶ τοῦ ἡλίου ὑπὲρ ὕδατος θερμοῦ ἐπερείδονται τὴν λοπάδα ἢ ἐπὶ λεπτῆς καὶ μαλακῆς ἀνθρακιᾶς. ἐστι δὲ καὶ ἄλλος τρόπος θεραπείας τοιοῦτος μετὰ τὸ ἐξυμενισθῆναι τὸ στέαρ λεαίνεται καὶ εἰς λοπάδα ἐμβληθὲν τήκεται, ἁλὸς ὀλίγου καὶ λεπτοῦ προσεμπασθέντος, εἶτα διὰ ῥάκους λινοῦ ὑλισθὲν ἀποτίθεται. ἁρμόζει δὲ τὸ τοιοῦτον εἰς τὰ ἄκοπα. ὔειον δὲ καὶ ἄρκειον θεραπεύεται οὕτως· λαβὼν τὸ πρόσφατον καὶ καταπίμελον, οἷόν ἐστι τὸ νεφριαῖον, ἔμβαλε 8 εἰς ὕδωρ δαψιλὲς ὄμβριον ὡς ὅτι ψυχρότατον καὶ ἐξυμένισον καὶ τρῖβε ταῖς χερσὶν ἐπιμελῶς, ἀνατρίβων αὐτὸ καὶ οἱονεὶ ἀποψήχων· 3 εἶτα ἑτέρῳ ὕδατι πολλάκις ἀποκλύσας δὸς εἰς χύτραν κεράμεᾶν τὸ διπλάσιον χωροῦσαν, ἐπιχέας τε ὕδωρ, ὡς ὑπερέχειν τοῦ στέατος, θὲς ἐπὶ κούφης ἀνθρακιᾶς καὶ κίνει σπάθῃ. ὅταν δὲ τακῇ, διηθήσας αὐτὸ διʼ ἡθμοῦ εἰς ὕδωρ, καὶ ἐάσας ψυγῆναι πάλιν ἐστραγγισμένον ἐπιμελῶς ἀπόδος εἰς τὴν χύτραν προπεπλυμένην , ἐπιχέας τε ὕδωρ τῆξον πραέως, καὶ καθελὼν μικρόν τε ἐάσας τὴν τρύγα ὑποστῆναι κατάχεον εἰς θυίαν νενοτισμένην σπόγγῳ. ὅταν δὲ παγῇ, ἀνελόμενος καὶ τὴν πρὸς τῷ πυθμένι ἀκαθαρσίαν ἀφελὼν τῆξον ἐκ τρίτου χωρὶς ὕδατος, καὶ κατεράσας εἰς θυίαν καθαρίσας τε ἔμβαλε εἰς κεραμεοῦν ἀγγεῖον καὶ πωμάσας ἀπόθου εἰς κατάψυχρον τόπον. 4 τράγειον δὲ καὶ προβάτειον, ἔτι δὲ καὶ ἐλάφειον θεραπεύεται οὕτως. λαβών, σἶον προείρηται, στέαρ οἰουτινοσοῦν αὐτῶν καὶ πλύνας ἐξυμενίσας τε, ὡς προείρηται ἐπὶ τοῦ ὑείου, δὸς εἰς θυίαν μαλάττειν καὶ τρῖβε, κατʼ ὀλίγον ὕδωρ ἐπιχέων, ἄχρι ἂν μήτε αἱμάλωψ ἐκκρίνηται μήτε λάμπη ἐπιπλέῃ λαμπρόν τε γένηται. λοιπὸν ἐμβαλὼν αὐτὸ εἰς κεραμεᾶν χύτραν καὶ προσεπιδούς ὕδωρ ὥστε ὑπερέχειν θὲς ἐπὶ κούφης ἀνθρακιᾶς καὶ κίνει. ὅταν δὲ τακῇ ἅπαν, κατεράσας αὐτὸ εἰς ὕδωρ καὶ ψύξας πλύνας τε τὴν χύτραν ἐκ δευτέρου τῆκε καὶ τὰ αὐτὰ ποίει τοῖς προειρημένοις. 5 τὸ δὲ τρίτον χωρὶς ὕδατος τήξας εἰς νενοτισμένην θυΐαν ἀπήθησον καὶ ψυγὲν ἀποτίθεσο, ὡς ἐλέγετο ἐπὶ τοῦ ὑείου. καὶ τοῦ βοείου δὲ στέατος ἐξυμενιστέον τὸ νεφριαῖον καὶ θαλάττῃ πελαγίᾳ πλυτέον, εἶτα εἰς ὅλμον ἐμβλητέον καὶ κοπτέον ἐπιμελῶς, ἐπιρραινομένης τῆς θαλάττης. ὅταν δὲ διαλυθῇ ἅπαν, εἰσβλητέον αὐτὸ εἰς χύτραν κεραμεᾶν καὶ θάλασσαν ἐπιχυτέον, ὡς ὑπερέχειν μὴ ἦττον σπιθαμῆς, ἑψητέον τε, ἄχρι τὴν ἰδίαν ὀσμὴν ἀποβάλῃ· εἶτα πρὸς μίαν μνᾶν τοῦ στέατος 6 Ἀττικὴν κηροῦ Τυρρηνικοῦ ὁλκὰς τέτταρας ἐμβλητέον καὶ διηθητέον, ἀφαιρετέον τε τὴν προσκαθημένην ἐν τῳ πυθμένι ἀκαθαρσίαν καὶ εἰς λοπάδα καινὴν ἀποθετέον· εἶτα εἰς ἥλιον καθ᾿ ἡμέραν κομιστέον περιεσκεπασμένον, ὅπως ἀπολευκανθῇ καὶ τὴν δυσωδίαν ἀποβάλῃ. τὸ δὲ ταύρειον θεραπευτέον οὕτως· λαβὼν καὶ τούτου τὸ πρόσφατον καὶ νεφριαῖον ἔκπλυνον ποταμίῳ ῥεύματι, ἐξυμενίσας τε δὸς εἰς χύτραν κεραμεᾶν καινήν, ἁλὸς ὀλίγον προσεμπάσας, καὶ τῆκε· εἶτα εἰς ὕδωρ διαυγὲς ἀπηθήσας, ὅταν ἀρχὴν λαμβάνῃ 7 πήξεως, ταῖς χερσὶ πάλιν ἔκπλυνον σφοδρῶς τρίβων. τοῦ μὲν ἀποχεομένου ὕδατος τοῦ δὲ ἐπιχεομένου, ἄχρι ἂν πλυθῇ καλῶς, καὶ πάλιν εἰς χύτραν ἐμβαλών ἕψε μετʼ οἴνου ἴσου εὐώδους. ὡς δ᾿ ἂν ζέσῃ δίς, ἄρας ἀπὸ τοῦ πυρὸς τὴν χύτραν ἔασον ἐννυκτερεῦσαι τὸ στέαρ ἐνθάδε· τῇ δ᾿ ἐχομένη ἐάν τι τῆς δυσωδίας ὑπολείπηται, ἀνελόμενος τὸ προειρημένον εἰς ἑτέραν χύτραν καινὴν προσεπίχεον οἶνον εὐώδη καὶ τὰ αὐτὰ τοῖς προειρημένοις ποίει, ἕως ἂν ἅπασαν τὴν δυσωδίαν ἀποβάλῃ. τήκετοι 8 δὲ καὶ χωρὶς ἀλῶν ἐπ᾿ ἐνίαις διαθέσεσιν, ἐν αἶς οὗτοι ἐναντιοῦνται· γίνεται μέντοι τὸ οὕτως σκευασθὲν οὐκ ἄγαν λευκόν, ὡσαύτως δὲ καὶ παρδάλειον σκευαστέον καὶ λεόντειον συάγρειόν τε καὶ καμήλεον καὶ ἵππειον καὶ τὰ ὅμοια. ἀρωματιστέο΄ν δὲ στέαρ μόσχειον καὶ ταύρειον, ἔτι δὲ ἐλάφειον καὶ μυελὸν τοῦδε τοῦ ζῴου τὸν τρόπον τοῦτον· ἐξυμενίσας τὸ μέλλον εὐωδιάζεσθαι καὶ πλύνας, ὡς προείρηται, σύζεσον οἴνῳ ἀθαλάσσῳ τε καὶ εὐώδει, εἶτα ἀνελόμενος καὶ ἐννυκτερεῦσαι ἀφφὶς ἕτερον οἶνον ἀπὸ τοῦ αὐτοῦ γένους ἐπίχεε τῷ πλήθει τοσοῦτον, ὅσον ἦν ὁ ἔμπροσθεν δοθείς, καὶ τήξας ἀποκογχίσας τε ἐπιμελῶς, πρὸς ἐννέα κοτύλας τοῦ στέατος ἔμβολε 9 σχοίνου Ἀραβικῆς ὁλκὰς ἑπτά· ἐὰν δὲ εὐωδέστερον ποιῆσαι θέλῃς, τοῦ ἄνθους ὁλκὰς τεσσαράκοντα, προσαπόδος δὲ καὶ φοίνικος καὶ καλάμου τὰς ἴσας ὁλκάς, ἀσπαλάθου τε καὶ ξυλοβαλσάμου ἀνὰ ὁλκὴν μίαν μεῖξον δὲ καὶ καρδαμώμου καὶ νάρδου καὶ κασσίας καὶ κιναμώμου ἀνὰ οὐγγίαν μίαν — πάντα δὲ ἔστω ὁλοσχερέστερον κεκομμένα — εἶτα ἐπιδούς οἶνον εὐώδη ἀπέρεισαι ἐπ ἀνθράκων πεπωμασμένον τὸ ἀγγεῖον καὶ σύζεσον τρίς, ἄρας τε ἀπὸ τοῦ πυρὸς ἔασον ἐννυκτερεῦσαι αὐτό· τῇ δ᾿ ἐχομένῃ ἀπόχεε τὸν οἶνον καὶ ἄλλον ἐπιδοὺς τοῦ αὐτοῦ γένους σύζεσον ὁμοίως ἔτι τρὶς καὶ ἄφες. 10 πρωὶ δὲ ἀνελόμενος τὸ στέαρ ἀπόχεε τὸν οἶνον, ἐκπλύνας τε τὸ ἀγγεῖον καὶ καθάρας τὸ πρὸς τῳ πυθμένι καὶ τήξας διυλίσας τε αὐτὸ ἀπόθου καὶ χρῶ. ἀρωματίζεται δὲ καὶ τὸ τεθεραπευμένον τὸν αὐτὸν τρόπον. προστύφεται δὲ τὰ προειρημένα στέατα πρὸς τὸ ῥᾳδίως δέξασθαι τὴν τῶν ἀρωμάτων δύναμιν ρὕτως· λαβὼν αὐτῶν ὅ τι ἂν αἱρῇ ζέσον ἅμα οἴνῳ, συγκαθεὶς μυρσίνης κλάδον ἕρπυλλόν τε καὶ κύπερον, ἔτι δὲ ἀσπάλαθον ὁλοσχερέστερον συγκοπέντα· τινὲς δὲ ἐνὶ τούτων ἀρκοῦνται. ὅταν δὲ τὸ τρίτον ἀναζέσῃ, ἀνελόμενος πραέως καὶ δι᾿ ὀθόνης ὑλίσας ἀρωμάτιζε, ὡς δεδήλωται. ἔτι δὲ καὶ οὕτως πρόστυφε τὰ στέατα κόψας ὅ τι ἂν 11 αὐτῶν θέλῃς — πρόσφατον δὲ καὶ ἀμιγὲς αἵματος τά τε ἄλλα ἔχον, ἃ πολλάκις εἴρηται — καὶ ἐμβαλὼν εἰς λοπάδα καινὴν ἐπιχέας τε οἶνον παλαιὸν λευκὸν εὐώδη, ὡς ὑπερέχειν δακτύλους ὀκτώ, σύζεσον ἐλαφρῷ χρώμενος πυρί, ἕως τὴν σύμφυτον ὀσμὴν ὀποβάλῃ καὶ μᾶλλον οἰνίζῃ. εἶτα καθελὼν τὸ ἀγγεῖον καὶ ψύξας ἀνελοῦ τοῦ στέατος μνᾶς δύο καὶ ἐμβαλών εἰς λοπάδα προσεπιδούς τε τοῦ αὐτοῦ οἴνου κοτύλας τέσσαρας καὶ λωτίνου καρποῦ, οὖ τοῖς ξύλοις οἱ αὐλοποιοὶ χρῶνται, κεκομμένου μνᾶς τέσσαρας ἕψε πυρὶ κούφῳ διηνεκῶς κινῶν. ὅταν 12 δὲ τὴν στεατώδη ἀποφοράν ἀποβάλῃ πᾶσαν, διυλίσας αὐτὸ ψῦχε, καὶ λαβὼν ἀσπαλάθου κεκομμένου μνᾶν μίαν, ἀμαρακίνου δὲ ἄνθους μνᾶς τέσσαρας οἴνῳ φύρασον παλαιῷ καὶ ἔασον μίαν νύκτα συμπιεῖν τῇ δ᾿ ἐχομένη εἰς χύτραν κεραμεᾶν τριχουνιαίαν καινὴν κάθες ταῦτα καὶ τὸ στέαρ, προσαπόδος δὲ καὶ οἴνου χοέως ἥμισυ καὶ σύζεσον ἅπαντα ὁμοῦ· ὅταν δὲ πάντων τῶν στυμμάτων τὴν δύναμιν καὶ τὴν ὀσμὴν ἀπολάβῃ τὸ στέαρ, καθελὼν αὐτὸ καὶ διυλίσας πῆξον ἀπόθου τε. ἐὰν δὲ εὐωδέστερον ποιῆσαι θέλῃς, μίσγε σμύρνης τῆς λιπαρωτάτης ὀκτὼ ὁλκὰς οἴνῳ διειμένας πολυετεῖ. 13 τὸ δὲ ὀρνίθειον καὶ χήνειον στέαρ οὔτως ἂν εὐωδια\σθείη· σθείη· λαβὼν οἵουτινος αὐτῶν τεθεραπευμένου κοτύλας τέσσαρας καὶ καθεὶς εἰς ὀστρακίνην χύτραν πρόσμειξον ἐρυσισκήπτρου καὶ ξυλοβαλσάμου, ἔτι δὲ φοίνικος ἐλάτης καὶ καλάμου ὁλοσχερῶνς κεκομμένων ἀνὰ δραχμάς δεκαδύο, ἐπιδούς τε οἴνου Λεσβίου παλαιοῦ κύαθον ἕνα θὲς ἐπ᾿ ἀνθρακιᾶς καὶ σύζεσον τρίς· εἶτα ἀνελόμενος ἀπὸ τοῦ πυρὸς τὸ ἀγγεῖον καὶ ἐάσας ψυγῆναι τὰ ἐν αὐτῷ ἡμέραν καὶ νύκτα, τῇ ἐχομένη τῆξον αὐτά, καὶ διὰ ῥάκους λινοῦ καὶ καθαροῦ ὕλισον εἰς ἀργυροῦν ἀγγεῖον. 14 ὅταν δὲ παγῇ, ἀνελόμενος κόγχῳ τὸ προειρημένον εἰς κεραμεοῦν ἀγγεῖον βάλε καὶ πωμάσας στεγανῶς ἀπόθου ἐν καταψύχρῳ τόπῳ· χειμῶνος δὲ ταῦτα δραστέον, ἐν γάρ θέρει οὐ πήγνυται. τινὲς δὲ πρὸς τὴν σύστασιν αὐτοῦ καὶ τὴν πῆξιν βραχύ κηροῦ Τυρρηνικοῦ μίσγουσιν. τῳ δὲ αὐτῷ τρόπῳ ἀρωματιστέον καὶ τὸ ὕειον καὶ ἄρκειον καὶ τά ὅμοια. σαμψουχίζεται δὲ στέαρ οὕτως· λαβών τοῦ καλῶς τεθεραπευμένου ὅσον μνᾶν μίαν — ἔστω δὲ μᾶλλον ταύρειον — καὶ σαμψούχου ὡρίμου τεθλασμένου ἐπιμελῶς μνᾶν μίαν ἥμισυ μεῖξον καὶ μαγίδας ἀνάπλασον ἐπιχέας δαψιλέστερον οἶνον, εἶτα ἀποθέμενος αὐτὰς εἰς ἀγγεῖον καὶ σκεπάσας ἔασον ἐννυκτερεῦσαι. 15 πρωὶ δὲ εἰς χύτραν κεραμεᾶν ἐμβαλὼν καὶ ὕδωρ ἐπιχέας ἕψε κούφως. ὅταν δὲ τὴν ἰδίαν ὀσμὴν ἀποβάλῃ τὸ στέαρ, διυλίσας αὐτὸ καὶ ἐάσας μεῖναι ὅλην τὴν νύκτα πεπωμασμένον καλῶς, τῇ ἐπιούσῃ ἀνελόμενος τὸν τροχίσκον καὶ προσαποξύσας τὴν ἐν τῳ πυθμένι ῥυπαρίαν μεῖξον πάλιν σαμψούχου κεκομμένου, ὡς εἴρηται, ἄλλην μνᾶν μίαν ἥμισυ καὶ ὡσαύτως ἀναστρέφου, μαγίδας τε ποιῶν καὶ τὰ ἄλλα τὰ προειρημένα ἐπὶ πᾶσι δὲ ἑψήσας καὶ διυλίσας ἀφελών τε, εἴ τις πρὸς τῷ πυθμένι ῥυπαρία ὑπάρχοι, ἀπόθου ἐν καταψύχρῳ τόπῳ. εἰ δὲ ἀθεράπευτον στέαρ χήνειον ἢ ἀρνίθειον ἢ μόσχειον 16 θέλοι τις ἄσηπτον διατηρῆσαι, οὕτως ποιητέον αὐτό· λαβὼν πρόσφατον, ὁποῖον ἂν αἱρῇ, ἔκπλυνον ἐπιμελῶς καὶ διαψύξας ἐπὶ κοσκίνου ἐν σκιᾷ, μετὰ τὸ ξηρανθῆναι ἔμβαλε εἰς ὀθόνην καὶ ἐκπίεσον ταῖς χερσὶν ἐρρωμένως, εἶτα λίνῳ διείρας κρέμασον ἐν τόπῳ σκιερῷ· μετὰ δὲ ἡμέρας πολλὰς καινῷ ἀποδήσας χαριῃ ἀποτίθεσο ἐν καταψύχρῳ τόπῳ. ἄσηπτα δὲ διαμένει καὶ ἐν μέλιτι ἀποτεθέντα. δύναμιν δὲ ἔχει τὰ στέατα πάντα θερμαντικήν. τὸ μέντοι 17 ταύρειον στύφει ποσῶς καὶ τὸ βόειον καὶ τὸ μόσχειον, καὶ τὸ λεόντειον δὲ ἀναλογεῖ τούτοις· φασὶ δὲ καὶ ἀντιφάρμακον αὐτὸ τοῖς ἐπιβουλεύουσιν εἶναι. τὸ δὲ ἐλεφάντειον καὶ ἐλάφειον ἑρπετὰ διώκει καταχριόμενον τὸ δὲ αἴγειον στυπτικώτερον, ὅθεν δυσεντερικοῖς δίδοται σύν ἀλφίτῳ καὶ τυρῷ, καὶ ἑψόμενον ἐγκλύζεται μετὰ πτισάνης χυλοῦ. εὐθετεῖ δὲ καὶ φθισικοῖς ἐν ῥοφήμασιν ὁ ἐξ αὐτῶν ζωμός, καὶ τοῖς κανθαρίδας πεπωκόσιν ὠφελίμως δίδοται. τὸ δὲ τράγειον, διαλυτικώτερον ὄν, βοηθεῖ 18 ποδαγρικοῖς φυραθὲν σὺν αἰγὸς σπυράθοις καὶ κρόκῳ καὶ ἐπιτιθέμενον, καὶ τὸ προβάτειον δὲ ἀναλογεῖ τούτῳ. ὕειον δὲ [ἀναλογεῖ] τοῖς περὶ ὑστέραν καὶ ἕδραν καὶ πυρικαύτοις ἁρμόζει· τὸ δὲ ταριχηρὸν ὕειον ὡς ὅτι παλαιότατον θερμαίνει, μαλάσσει, οἴνῳ δὲ πλυθὲν ἁρμόζει πλευριτικοῖς, σὺν τέφρᾳ ἢ ἀσβέστῳ ἀναλημφθέν, καὶ πρὸς οἰδήματα καὶ φλεγμονάς. τὸ δὲ ὄνειόν φασιν οὐλάς ὁμόχρους ποιεῖν, χήνειον δᾶ καὶ ὀρνίθειον πρός τε τὰ γυναικεῖα καὶ ἐπιρρήξεις χειλῶν καὶ προσώπων ἐπιμέλειαν καὶ ὠταλγίας ἁρμόζει, τὸ δὲ ἄρκειον δοκεῖ τριχοφυὲς εἶναι ἀλωπεκιῶν καὶ χιμετλιῶσιν ἁρμόζει. 19 τὸ δὲ τῆς ἀλώπεκος στέαρ ποιεῖ πρὸς ὠταλγίας, τὸ δὲ τῶν ποταμίων ἰχθύων ὀξυδερκὲς ἐγχριόμενον, ἀποτακὲν ἐν ἡλίῳ καὶ μέλιτι μιγέν, τὸ δὲ τῆς ἐχίδνης πρὸς ἀμβλυωπίας, ἔτι δὲ ὑποχύσεις ἐνεργεῖ. μιγὲν κεδρίᾳ καὶ μέλιτι Ἀττικῷ καὶ ἐλαίῳ παλαιῷ ἴσον, ἐκτιλθείσας δὲ τὰς ἐν μασχάλη τρίχας πρὸς ταῖς ῥίζαις καταρισθὲν καθʼ ἑαυτὸ πρόσφατον ἐξιτήλους ποιεῖ.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: DIOSC_DMM-2.77
TEXT:
μυε λῶν δὲ κράτιστός ἐστιν ὁ ἐλάφειος, εἶτα μόσχειος καὶ μετὰ τοῦτον ταύρειος, εἶτα αἴγειος καὶ προβάτειος. συνίσταται δὲ θέρους τοῦ συνεγγίζοντος τῷ φθινοπώρῳ· ἐν γὰρ τοῖς ἄλλοις καιροῖς αἱμαλωπιᾷ καὶ οἱονεὶ σάρξ εὔθρυπτος ἐν τοῖς ἀστέοις εὑρίσκεται. ἐστι δὲ δύσγνωστος, ἐὰν μή τις αὐτὸν ἐξοστείσας ἴδῃ καὶ ἀποθῆται. ἄπαντες δέ εἰσι μαλακτικοί, ἀραιωτικοί, θερμαντικοί, πληρυμωτικοὶ ἑλκῶν· ὁ δὲ ἐλάφειος περιχρισθεὶς καὶ θηρία διώκει. 2 θεραπεύεται δὲ ὁ πρόσφ ατος μαλαχθεὶς ὡς στέαρ, παραχεομένου ὕδατος, ἐκλεγομένων τῶν ὀστέων, εἶτα διʼ ὀθόνης ὑλισθεὶς καὶ ὡσαύτως πλυθείς, ἄχρι ἂν οὗ τὸ ὕδωρ καθαρὸν γένηται· ἔπεινα ἐν διπλώματι τακείς, ὑπαναλημφθείσης πτερῷ τῆς ἐπινηχομένης ῥυπαρίας, καὶ διυλισθεὶς εἰς θυίαν, μετὰ τὸ παγῆναι ἀποτίθεται ἐν ἀστρακίνῳ ἀγγείῳ καινῷ, ἀπεξυσμένης ἐπιμελῶς τῆς ὑποστάθμης. εἰ δʼ ἀθεράπευτον ἀποτίθεσθαι βούλει, ποίει πάντα, ὡς ἐπὶ τοῦ ὀρνιθείου καὶ χηνείου στέατος ὑπεδείξαμεν (II 76).
