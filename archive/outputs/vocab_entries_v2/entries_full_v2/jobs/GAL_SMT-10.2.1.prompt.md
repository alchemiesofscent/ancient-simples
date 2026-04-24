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
CONTEXT_PREV_SOURCE_ID: GAL_SMT-10.1.0
CONTEXT_PREV_TEXT:
Οὐδὲν τῶν νῦν λεχθησομένων τοῖς ἀγνοοῦσι τὰ κατὰ τὴν ἀρχὴν τῆς πραγματείας ἐν τοῖς πρώτοις πέντε βιβλίοις εἰρημένα μεγάλην ὠφέλειαν οἴσει, τινὰ δ' ἴσως καὶ βλάψει τὸν χρησόμενον τοῖς ἐν αὐτῷ γεγραμμένοις φαρμάκοις, οὐκ ἔχοντα μέθοδον. ὡς οὖν ἐκεῖνα μεμαθηκότι σοι διαλέξομαι, τὸ κεφάλαιον ἀναμνήσας ὅλης τῆς πραγματείας. ἐδείχθη τὰ φάρμακα κατὰ μὲν τὰς δραστικὰς ὀνομαζομένας ποιότητας ἐνεργοῦντα θερμότητα καὶ ψυχρότητα καὶ ξηρότητα καὶ ὑγρότητα, τῇ δὲ τούτων κράσει στρυφνὰ καὶ αὐστηρὰ καὶ ἁλμυρὰ καὶ ἁλυκὰ καὶ πικρὰ καὶ δριμέα καὶ γλυκέα γιγνόμενα, καὶ τὰ μὲν ῥυπτικὰ, τὰ δὲ ἀποκρουστικὰ, τὰ δὲ ἑλκτικὰ, τὰ δὲ μαλακτικὰ, τὰ δὲ καυστικὰ, τὰ δὲ σηπτικὰ, τὰ δὲ ἐσχαρωτικὰ, καὶ πρός γε τούτοις ἔτι κατ' ἄλλας ἰδικωτέρας ἐνεργείας, σαρκωτικὰ τε καὶ συνουλωτικὰ καὶ κολλητικὰ συρίγγων ἢ ἑλκῶν, ἢ καθαιρετικὰ τῶν ὑπεραυξανομένον σαρκῶν. ἐδείχθη δὲ καὶ ὡς ἡ καθόλου δύναμις ἐκ πείρας μιᾶς ἐνδεικτικῶς εὑρίσκοιτο, καὶ οὐ τῆς τυχούσης γε πείρας, ἀλλὰ μετὰ τῶν εἰρημένων διορισμῶν γιγνομένης· εὑρεθείσης δ' ἅπαξ τῆς καθόλου δυνάμεως οὐδεμιᾶς ἔτι πείρας εἶναι χρείαν εἴς γε τὰς κατὰ μέρος ἐνεργείας, ὅτι μὴ πρὸς βεβαίωσιν μόνην ὧν ὁ λόγος εὗρεν. οὕτως οὖν καὶ νῦν ποιησαίμεθα τὴν κρίσιν τῆς προκειμένης ὕλης, αὕτη δ' ἐστὶν ἡ ἐκ τῶν ζώων. ἐν μὲν γάρ τοῖς μετὰ τὸ πέμπτον ἐφεξῆς τρισὶ βιβλίοις, ἕκτω καὶ ἑβδόμῳ καὶ ὀγδόω, τὴν περὶ τὰ φυτὰ διήλθομεν ὕλην, οὐ πᾶσαν δηλονότι τὴν καθ' ὅλην τὴν οἰκουμένην, ἀλλ' ὅσης ἡμεῖς ἔχομεν πεῖραν. ἐν δὲ τῷ πρὸ τοῦδε, τῆς δ' ὅλης πραγματείας ἐννάτῳ, τὴν περὶ τὰ γεώδη τε καὶ λιθώδη σώματα. λείπεται δ' ἡμῖν ἔτι τὴν περὶ τὰ ζῶα διελεῖν ὕλην· εἶτ' ἔτι τῶν ἐν θαλάττῃ καὶ λίμναις ἢ ὅλως ἐν ὕδατι γεννωμένων ἐστὶν ὑπόλοιπον, ἃ μήτε φυτὰ μήτε γῆ μήτε λίθος ἐστὶ μήτε ζῶον. ὀλίγιστα δὲ τὰ τοιαῦτα παντάπασίν ἐστι καὶ γεγράψεται τελευταῖα, μετὰ τὸ διελθεῖν ἡμᾶς τὰ κατὰ τὰ σώματα τῶν ζώων. ἔσται δὲ καὶ τούτων ἡ τάξις τῆς διδασκαλίας κατὰ τὴν τῶν πρώτων γραμμάτων τάξιν ἐν ταῖς προσηγορίαις αὐτῶν. ὥσπερ δ' ἐν τῇ τῶν φυτῶν ὕλῃ καὶ περὶ τῶν ἐξ αὐτῶν γινομένων χυμῶν τὸν λόγον ἐποιησάμην, οὕτως καὶ νῦν οὐ μόνον τῶν στερεῶν μορίων ἐν τοῖς ζώοις ἡ διδασκαλία τῆς δυνάμεως, ἀλλὰ καὶ τῶν ἐν αὐτοῖς περιεχομίνων ἔσται, φλέγματος, χολῆς, αἵματος, οὔρου, κόπρου καὶ τῶν ὁμοίων. ἐν μὲν οὖν τοῖς ἔμπροσθεν εἰρημένοις οὐ πολλὰ τῶν κατὰ μέρος ἐν ταῖς ὑπὸ τῶν ἰατρῶν γεγραμμέναις ὕλαις ἄγνωστὰ μοι γέγονεν, ἀλλ' αὐτὸς ἐσπούδασα διὰ τῆς πείρας γνῶναι τὰς δυνάμεις αὐτῶν, εἴ τινος δ' οὐκ ἔγνων, οὐδ' ἔγραψα περὶ τούτου τὴν ἀρχὴν, οὐκ ἀξιῶν ἄλλοις πιστεύειν οὐδὲ περὶ ἑνὸς τοιούτου, διὰ τὸ καταμαθεῖν ἐνίους πολλὰ ψευδομένους. ἐπὶ δὲ τῆς νῦν προκειμένης ὕλης οὐχ οὕτως ἔχει. πάμπολλα ὁμολογῶ μορίων τε καὶ ὑγρῶν ἐν τοῖς τῶν ζώων σώμασι περιεχομένων, ὧν οὐδεμίαν αὐτὸς ἔσχηκα τοιαύτην πεῖραν, ὁποίαν ἔγραψὰν τινες·ἔνια μὲν γάρ αὐτῶν ἀσελγῆ τέ ἐστι καὶ βδελυρὰ, τινὰ δὲ καὶ πρὸς τῶν νόμων ἀπηγορευμένα, περὶ ὧν οὐκ οἶδα πῶς ἔγραψεν ὁ Ξενοκράτης, ἄνθρωπος οὐ πάλαι γεγονὼς, ἀλλὰ κατὰ τοὺς πάππους ἡμῶν, τῆς Ῥωμαϊκῆς βασιλείας ἀπηγορευκυίας ἀνθρώπους ἐσθίειν, ἀλλ' ἐκεῖνός γε ὡς αὐτὸς πεπειραμένος ἀξιοπίστως πάνυ γράφει τίνα πάθη θεραπεύειν πέφυκεν ἐγκέφαλος ἐσθιόμενος ἢ σάρκες ἢ ἧπαρ ἀνθρώπου, τίνα δὲ τὰ τῆς κεφαλῆς ἢ κνήμης ἢ δακτύλων ὀστᾶ τὰ μὲν καυθέντα, τὰ δ' ἄκαυστα πινόμενα, τίνα δ' αὐτὸ τὸ αἷμα. ταῦτα μὲν οὖν εἰ καὶ παρὰ τοὺς νόμους, ἀλλ' οὐκ ἀσελγῆ γε. πόσις δ' ἱδρῶτός τε καὶ οὔρου καὶ καταμηνίου γυναικὸς ἀσελγῆ καὶ βδελυρὰ, καὶ τούτων οὐδὲν ἧττον ἡ κόπρος, ἣν διαχριομένην τε τοῖς κατὰ τὸ στόμα καὶ τὴν φάρυγγα μορίοις εἴς τε τὴν γαστέρα καταπινομένην ἔγραψεν ὁ Ξενοκράτης ὅ τὶ ποτε ποιεῖν δύναται· γέγραφε δὲ καὶ περὶ τοῦ κατὰ τὰ ὦτα ῥύπου καταπινομένου. ἐγὼ μὲν οὖν οὐδὲ τοῦτον ἂν ὑπέμεινα καταπιεῖν, ἐφ' ᾧ γε μηδέποτε νοσῆσαι. πολὺ δ' αὐτοῦ βδελυρώτερον ἡγοῦμαι τὴν κόπρον εἶναι. καὶ μεῖζόν γε ὄνειδός ἐστιν ἀνθρώπῳ σωφρονοῦντι κοπροφάγον ἀκούειν ἢ αἰσχρουργὸν ἢ κίναιδον, ἀλλὰ καὶ τῶν αἰσχρουργῶν μᾶλλον βδελυττόμεθα τοὺς φοινικίζοντας τῶν λεσβιαζόντων, ᾧ φαίνεταὶ μοι παραπλήσιόν τι πάσχειν ὁ καὶ καταμηνίου πίνων. οὔτ' οὖν τούτων ὑπομείναι τις ἂν εἰς πεῖραν ἐλθεῖν ἄνθρωπος κατὰ φύσιν ἔχων οὔθ' ὅσα μετριώτερα μὲν τούτων, ἔτι δ' ἀσελγῆ, κόπρῳ καταχρίεσθαὶ τι τοῦ σώματος μέρος, ἕνεκα τοῦ κατ' αὐτὸ πάθους, ἢ ἀνθρώπου σπέρματος. γόνον δὲ αὐτὸ καλεῖν εἴωθεν ὁ Ξενοκράτης, καὶ διορίζεταὶ γε μετὰ πάσης ἐπιμελείας τίνα μὲν αὐτὸς ὁ γόνος μόνος ὠφελεῖν πέφυκε καταχριόμενος, τίνα δὲ μετὰ τὴν ὁμιλίαν ἀνδρὸς καὶ γυναικὸς, ὅταν ἐκπέσῃ τοῦ γυναικείου κόλπου. μεγάλην γάρ τινα δεῖ γενέσθαι βοηθημάτων πενίαν, ἵνα τις χίμεθλα θεραπεύσῃ ὑπερχύσας ἀνδρὸς σπέρμα μὴ μεῖναν ἔνδον, ἀλλ' ἐκρυὲν τῆς γυναικὸς ἐπὶ τῇ συνουσίᾳ. πολὺ μὲν δὴ καὶ τὸ τοιοῦτο τῆς ὕλης εἶδός ἐστιν ἐν τοῖς περὶ τῆς ἀπὸ τῶν ζώων ὠφελείας ὑπ' αὐτοῦ γεγραμμένοις. οὐ γάρ ἀνθρώπου δηλονότι, τίνα δύναμιν ἔχει πινόμενον οὖρον ἢ καταπινομένοις τε καὶ διαχριομένοις τοῖς ἐν τὸ στόματι μέρεσι κόπρος, ἀλλὰ καὶ τῶν ἄλλων ζώων ἑκάστου διηγεῖται, πολὺ δ' ἄλλο τῶν δυσπορίστων, οἷον ὅταν ἐλέφαντος ἢ ἵππου Νειλώου μνημονεύῃ. βασιλίσκον μὲν γάρ τὸ θηρίον οὐδὲ εἶδον οὐδέποτε, καὶ εἰ ἀληθῆ τὰ λεγόμενα περὶ αὐτοῦ, κινδυνῶδές ἐστι καὶ τὸ πλησίον ἀφικέσθαι τῷ ζώῳ τούτῳ. παραπλήσια δὲ τῷ Ξενακράτει καὶ ἄλλοι τινὲς ἔγραψαν περὶ ζώων, ἐξ ὧν καὶ αὐτὸς ὁ Ξενοκράτης ἐξεγράψατο τὰ πλεῖστα. πόθεν γάρ ἂν ηὐπόρησε τοσούτων τε καὶ τοιούτων πραγμάτων αὐτὸς πειραθῆναι; ὁ γοῦν ἡμέτερος γενόμενός ποτε βασιλεὺς Ἄτταλος ἐλάττονα φαίνεται γράφων, καίτοι φιλοτιμότατα σχὼν περὶ τὴν τῶν τοιούτων πεῖραν. ἐπαινῶν δὲ τις Ἀτευρίστου τὴν αὐτὴν πραγματείαν, ἔδωκὲ μοι καὶ αὐτὴν διελθεῖν, ὥς γε ἐμοὶ δοκεῖ, χωρὶς αὐτοψίας ἰδίας τοῦ γράψαντος αὐτὴν γεγονυῖαν. ἐγὼ τοίνυν οὔτε βασιλίσκων οὔτε ἐλεφάντων οὔθ' ἵππων Νειλώων οὔτ' ἄλλου τινὸς οὗ μὴ πεῖραν αὐτὸς ἔχω μνημονεύσω, τῶν δὲ καλουμένων φίλτρων, ἀγωγίμων, ὀνειροπομπῶν τε καὶ μισήτρων, αὐτοῖς γάρ τοῖς ἐκείνων ὀνόμασιν ἐξεπίτηδες χρῶμαι, τὴν ἀρχὴν ἂν, οὐδ' εἰ πεῖραν ἱκανὴν εἶχον, ἐμνημόνευσα διὰ γραμμάτων, ὥσπερ οὐδὲ τῶν θανασίμων φαρμάκων ἢ τῶν ὡς αὐτοὶ καλοῦσιν παθοποιῶν. ἐκεῖνα μὲν γάρ αὐτῶν καὶ γελοῖα, καταδῆσαι τοὺς ἀντιδίκους, ὡς μηδὲν ἐπὶ τοῦ δικανικοῦ δυνηθῆναι φθέγξασθαι, ἢ ἐκτρῶσαι ποιῆσαι τὴν κύουσαν, ἢ μηδέποτε συλλαβεῖν, ὅσα τ' ἄλλα τοιαῦτα. τὰ μέν γε πλεῖστα εἶναι τούτων ἐστὶ καὶ πρὸς τῆς πείρας ἀδύνατα ὑπάρχειν, ἔνια δὲ εἰ καὶ δυνατὰ, βλαβερὰ γοῦν γ' ἐστὶ τῷ βίῳ τῶν ἀνθρώπων, ὥστ' ἐγὼ νὴ τοὺς θεοὺς θαυμάζω κατὰ τίνα τὴν ἔννοιαν ἧκον ἐπὶ τὸ γράφειν αὐτὰ τινες. ἃ γάρ καὶ τοῖς ζῶσιν ἀδοξίαν φέρει γνωσθέντα, πῶς ταῦτα μετὰ θάνατον εὐδοξίαν οἴσειν αὑτοῖς ἤλπισαν; εἰ μὲν οὖν βασιλεῖς ὄντες ἐν ἀνθρώποις ἐπὶ θανάτῳ κατακεκριμένοις ἐποιήσαντο τὴν τεῖραν αὐτῶν, οὐδὲν ἔπραξαν δεινόν. ἐπεὶ δ' ἰδιῶται τοιαύτης ἐξουσίας ἐν ὅλῳ τῷ βίῳ γεγονότες ἐπὶ τὸ γράφειν ἧκον αὐτὰ, δυοῖν θάτερον, ἢ μὴ πειραθέντες αὐτοὶ γράφουσιν ὑπὲρ ὧν οὐκ ἴσασιν, ἢ εἴπερ ἐπειράθησαν, ἀσεβέστατοι πάντων ἀνθρώπων εἰσὶν, ἕνεκα πείρας ὀλέθρια δόντες φάρμακα τοῖς οὐδὲν ἠδικηκόσιν, ἐνίοτε δὲ καὶ καλοῖς τε καὶ ἀγαθοῖς ἀνδράσιν. ἰατροὺς γοῦν τις ἑστῶτας ἐπὶ ῥωποπώλαις θεασάμενος δύο, προσεκόμισεν αὐτοῖς μέλι πιπράσκων δῆθεν. οἱ δὲ ἐγεύσαντὸ τε καὶ περὶ τῆς τιμῆς διελέγοντο καὶ ὡς ὀλίγον αὐτῶν διδόντων, ὁ μὲν σπεύσας ἐχωρήθη, τῶν δ' ἰατρῶν οὐδέτερος ἐσώθη. τὰ τοιαῦτ' οὖν ἅπαντα τῶν πραξάντων τοὺς γράψαντας οὐχ ἧττον, ἀλλὰ καὶ μᾶλλον ἄξιον μισεῖν, ὅσῳ καὶ μεῖόν ἐστιν ἀδίκημα μόνον τι ποιῆσαι κακὸν ἢ μετὰ πολλῶν. καὶ τῷ μὲν πράξαντι συναπέθανεν ἡ τῶν κακῶν θεωρημάτων ἐμπειρία, τῶν δὲ γραψάντων πάντων ἀθάνατός ἐστιν τοῖς πονηροῖς ὅπλα τῆς κακουργίας παρασκευάζουσα. λέγωμεν οὖν ἡμεῖς ἤδη περὶ τῶν χρησίμων ἀνθρώποις πραγμάτων, ὅσων πεῖραν ἔχομεν. Περὶ τῶν ἐν τοῖς ζώοις ὑγρῶν.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_SMT-10.2.1
TEXT:
αἷμα, προσυπακούειν δηλονότι χρὴ τοῦ κατὰ φύσιν ἔχοντος ζώου, τοῦτο γάρ καὶ ὄντως ἐστὶν αἷμα. τὸ δὲ μελαγχολικὸν ἢ πικρόχολον ἢ φλεγματῶδες ἢ ὀρρῶδες ἢ σηπεδονῶδες αἷμα μικτόν ἐστιν ἔκ τε τοῦ κατ' ἀλήθειαν αἵματος καὶ τοῦ μεμιγμένου χυμοῦ τε καὶ ἰχῶρος αὐτῷ. καὶ αὐτοῦ δὲ τοῦ κατὰ φύσιν αἵματος ἐν ἑκάστῳ ζώῳ τὸ μὲν ὑγρότερόν ἐστι, τὸ δὲ ξηρότερον, καὶ τὸ μὲν μᾶλλον, τὸ δὲ ἧττον θερμὸν, ψυχρὸν γάρ οὐδέν ἐστιν αἷμα.
