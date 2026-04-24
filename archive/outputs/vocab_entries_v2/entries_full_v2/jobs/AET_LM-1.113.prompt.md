# Vocab extractor prompt

```prompt

## Prompt (paste into LLM system/user message as-is)

You are an extraction agent for the Ancient Simples Project. Read the input text (Ancient Greek, possibly with TEI tags) and extract candidate terms relevant to ancient pharmacy/science. Output must be strictly valid JSON (no commentary).

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
- Output requirement: set `substance_lemma_normalized` and `part_lemma_normalized` (both non-null) and set the generic `lemma_normalized` to "" (empty string).

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
CONTEXT_PREV_SOURCE_ID: AET_LM-1.112
CONTEXT_PREV_TEXT:
μήλινον σκευάζεται ἀπὸ τῶν κυδωνίων μήλων, γίγνεται δὲ καὶ ἐκ τῶν ἄλλων μήλων τῶν στρυφνότερον ἐχόντων τὸ δέρμα καὶ εὐωδέστερον. περιελόντες δὲ τὸ πρὸς τὴν ἔκφυσιν καὶ πρὸς τῷ πυθμένι κάρφος καὶ τὴν ἐντεριώνην σὺν τοῖς ἔνδον κόκκοις, εἶτα τέμνοντες προσκειμένου τοῦ δέρματος – ἐν αὐτῷ γὰρ ἡ εὐωδία καὶ ἡ στύψις ὑπάρχει – καὶ ποιήσαντες μικρὰ τεμάχη, ἐμβαλοῦμεν τῷ ξέστῃ τοῦ ὀμφακίνου ἐλαίου 𐆄 <γ> τῶν μήλων, καὶ ἡλιώσαντες ἡμέρας <μ> ἀποτιθέμεθα. δύναμις δὲ τοῦ μηλίνου μᾶλλον ἐπὶ τὸ ψυχρότερον νεύει, οὐ μὴν ἄγαν διὰ τὸ οἰνῶδες τοῦ μήλου. στύφει μέντοι γε ἱκανῶς καθάπερ τὸ σχίνινον καὶ μᾶλλον ᾠκείωται στομάχῳ, διὰ τὸ ἐκ τροφίμων ὑλῶν ἀμφοτέρων γίγνεσθαι τοῦ τε ἐλαίου καὶ τοῦ μήλου, ὥστε ἀκολούθως ἁρμόττει στομάχῳ φλεγμαίνοντι καὶ ἀτονοῦντι ἐμβρεχόμενον καὶ τοῖς ἐπιθέμασιν ἐμβαλλόμενον καὶ πινόμενον. χρησιμώτερον δὲ ἐστι τοῦ ῥοδίνου διὰ τὸ οἰκειότερον τοῦ μήλου· ἐντίθησι γὰρ τόνον τῷ στομάχῳ καὶ σφοδρότερον διωθεῖ τοὺς ἐγκειμένους ἐν τῇ γαστρὶ δριμεῖς χυμούς· ἐνίεται δὲ δι' ἕδρας καὶ τοῖς ὑπὸ δριμείας χολῆς δακνωμένοις τὸν κῶλον καὶ τὰ παχέα τῶν ἐντέρων. παραφυλακτέον δὲ καὶ τὴν αὐτοῦ προσαγωγὴν ἐπὶ τῶν ἀπὸ ψύξεως βλαβέντων, ἐπὶ γὰρ τούτων μᾶλλον ἁρμόζει τὸ ἔχον ἀψίνθιον συνεψόμενον.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: AET_LM-1.113
TEXT:
ἔλαιον ῥόδινον, κηρωτὴ ἡ ψύχουσα. Ῥόδινον σκευάζεται οὕτως· ῥόδων ἐρυθρῶν ἐξωνυχισμένων καὶ ἐψυγμένων ἡμέραν καὶ νύκτα 𐆄 <γ>, ἐλαίου ὀμφακίνου ξέστης ἰταλικὸς εἷς, ἐμβάλλοντα δὲ τὰ ῥόδα περισφίγγειν χρὴ τὸ στόμα τοῦ βίκου ἔσωθεν μὲν ὀθονίῳ, ἔξωθεν δὲ δέρματι διὰ τοὺς γιγνομένους ὄμβρους αἰφνίδιον καὶ ἡλιοῦν ἡμέρας <κ> καὶ οὕτως σειρώσαντα ἀποτίθεσθαι τοὺς βίκους ἐπὶ σανίδων ἐν οἴκοις εὐκράτοις. τινὲς δὲ ἕτερὰ τινα προσεμβάλλουσι τοῖς ῥόδοις. ἀρίστη δὲ ἐστιν ἡ διὰ τῶν ῥόδων μόνων καὶ ἐλαίου σκευασία. τινὲς δὲ οὐχ ἡλιοῦσιν, ἀλλ' ἀποκρημνοῦσι τὸν βίκον εἰς φρέαρ ὕδατος ψυχροῦ ἡμέρας <μ>. ἁρμόζει δὲ κεφαλῇ θερμανθείσῃ καὶ ξηρανθείσῃ ἢ ἐξ ἡλιώσεως ἢ ἐκ πυρετῶν ἤ τινος ἄλλης τοιαύτης προφάσεως. ὑγραίνει γὰρ καὶ παρηγορεῖ καὶ ὕπνον ἐπάγει. καὶ ἐπὶ σπλάγχνων δὲ ἐν πυρετοῖς ἐκθερμαινομένων ἁρμοδία ἡ κηρωτὴ δι' αὐτοῦ σκευαζομένη καὶ πλυνομένη δι' ὕδατος ψυχροῦ, καὶ πλειστάκις ἀλλασσομένου τοῦ ὕδατος ἐν θέρει καὶ ἐπιρραπτομένης τῆς κηρωτῆς τοῖς σπλάγχνοις. σκεύαζε δὲ οὕτως τὴν κηρωτήν· κηροῦ 𐆄 <ϛ> ῥοδίνου 𐆄 <δ>. τῆκε τὸν κηρὸν μετ' ὀλίγου ῥοδίνου ἐπὶ διπλώματος καὶ ἐπίχεε εἰς ὕδωρ ψυχροῦν καὶ ψυγέντα ἄρας τῆκε πάλιν καὶ ἐπίχεε καὶ μάλασσε ταῖς χερσὶν ἀποπλύνων τὸν κηρὸν τῷ ὕδατι καὶ πάλιν τὸ τρίτον τῆκε καὶ ἐπιχέας πλῦνε, εἶτα ἐπιβάλλων τὸ λοιπὸν τοῦ ῥοδίνου τῆκε καὶ ἄρας κινῶν ψῦχε καὶ ἐπίχεε ἐν θυίᾳ καὶ λείου ἐπιστάζων ὕδωρ ὅσον ἐπιδέχεται καὶ ἀνελόμενος ἀπόθου εἰς ψυχρὸν ὕδωρ ἀλλάσσων. εἰ δὲ ἀντὶ τοῦ ὕδατος ὄξος μίξῃς τῇ κηρωτῇ ἐπιρραίνων ἐν τῷ λειοῦσθαι αὐτὸ ἐν τῇ θυίᾳ, ἀγαθὸν φάρμακον ἐργάσῃ πρὸς ἐρυσιπέλατα καὶ ἕρπητας καὶ ἄνθρακας. κεῖται καλῶς ἡ κηρωτὴ ἐν τῷ <Ϟα> κεφαλαίῳ τοῦ <ε> λόγου. [πλυνομένη δι' ὕδατος ψυχροῦ πλειστάκις ἀλλασσομένου τοῦ ὕδατος ἐν θέρει καὶ ἐπιρριπτομένης τῆς κηρωτῆς τοῖς σπλάγχνοις
