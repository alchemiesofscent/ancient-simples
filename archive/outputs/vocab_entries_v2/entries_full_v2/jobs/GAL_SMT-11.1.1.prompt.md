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
CONTEXT_PREV_SOURCE_ID: GAL_SMT-11.prooimion
CONTEXT_PREV_TEXT:
Τὰ πλεῖστα τῶν ἐν τοῖς ζώοις μορίων κοινὰ πᾶσιν αὐτοῖς ἐστιν, οὐδὲν μὴν οὕτω κοινὸν ὡς ἡ σάρξ. πᾶν γάρ ζῶον ἔχει ταύτην. ἔναιμον μὲν ἄνθρωπός τε καὶ τετράποδα πάντα καὶ ὄρνιθες, ὄφεις τε καὶ σαῦροι καὶ χελῶναι καὶ ἄλλα τοιαῦτα· χωρὶς δ' αἵματος τὰ τ' ὄστρεα πάντα καὶ τῶν ἐνύδρων οὐκ ὀλίγα, καθάπερ καὶ τῶν ἐν αὐτῇ τῇ γῇ. καὶ τὸ ἐσθιόμενον τῶν ζώων ἡ σάρξ ἐστι μάλιστα. καὶ γάρ καὶ τῶν σπλάγχνων ὁ πλεῖστος ὄγκος ἐκ τῶν κατ' αὐτὰς γίνεται σαρκῶν. ἔνιοι δὲ τῶν ἰατρῶν τὴν μὲν ἐν τούτοις σάρκα παρέγχυμα καλοῦσιν, διότι τῶν φλεβῶν ἐκχεόμενον τὸ αἷμα περιπήγνυται πᾶσι τοῖς ἀγγείοις, ὡς ἐκεῖνοι νομίζουσιν, τὴν δ' ἐν τοῖς μυσὶ μόνην ὀνομάζουσι σάρκα. περὶ μὲν δὴ τῶν ὀνομάτων, ὡς ἀεὶ φαμεν, ἐρίζειν οὐ χρὴ, τὴν δὲ τῶν πραγμάτων αὐτῶν ἐπιστήμην ἀσκητέον, ἧς καὶ ἡμεῖς ἀντιποιούμενοι διὰ παντὸς, ὅσα περὶ τῶν καθ' ἕκαστον ζῶον μορίων ἰδίων καὶ κοινῶν ἐπιστάμεθα, τὰ μὲν ἐκ τῆς πείρας, τὰ δ' ἐκ τοῦ λόγου διδαχθέντες, ἐφεξῆς ἐροῦμεν ἅπαντα τὴν ἀρχὴν ἀπὸ τῆς ἰδίως ὀνομαζομένης σαρκὸς ποιησάμενοι.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_SMT-11.1.1
TEXT:
οὐχ ἅπασαι τῶν ζώων αἱ σάρκες ἄνθρωπον τρέφουσιν, ἀλλ' ἐνίων εἰσὶ καὶ θανάσιμοι τῶν φαρμακωδῶν οὐδὲν ἧττον, ἃ καλοῦσι δηλητήρια, καὶ τῶν τρεφουσῶν δὲ ἡμᾶς σαρκῶν ἔνιαι μὲν αὐτὸ τοῦτο μόνον εἰσὶ τροφαὶ, τινὲς δὲ πρὸς τῷ τρέφειν ἔχουσι καὶ τὴν ὡς φαρμάκου δύναμιν, ἐπειδὴ κατὰ τὸ ξηραίνειν ἢ ὑγραίνειν καὶ θερμαίνειν ἢ ψύχειν, ἀλλοιοῦσι τὸ σῶμα. τὰς γοῦν τῶν ἐχιδνῶν θερμαινούσας τε καὶ ξηραινούσας ἐναργῶς ἔστιν ἰδεῖν ἀρτυομένας, ὥσπερ αἱ ἐγχέλεις ἐλαίῳ καὶ ἁλσὶ καὶ ἀνήθῳ καὶ πράσῳ καὶ ὕδατι δηλονότι μετὰ τοῦ συμμέτρου. ὅτι δὲ καθαίρουσιν διὰ τοῦ δέρματος ἅπαν τὸ σῶμα γνῶναὶ σοι πάρεστι κᾀξ ὧν ἐπειράθην ἐγὼ ἔτι νέος γενόμενος ἐπὶ τῆς ἡμετέρας Ἀσίας, ὧν ἕκαστον ἐφεξῆς ἤδη δίειμι. ἄνθρωπος νοσῶν τὸ καλούμενον πάθος ἐλέφαντα μέχρι μέν τινος ὁμοδίαιτος ἦν τοῖς συνήθεσιν, ἐπεὶ δ' ἐκ τῆς πρὸς αὐτὸν κοινωνίας τε καὶ ὁμιλίας ἐκοινώνησαν μὲν ἔνιοι τοῦ πάθους, αὐτὸς δὲ δυσώδης ἦν ἤδη καὶ εἰδεχθὴς, καλύβην αὐτῷ πηξάμενοι πλησίον τῆς κώμης ἐπὶ χθαμαλοῦ τοῦ λόφου παρὰ τινι πηγῇ ἱδρύουσιν ἐν αὐτῇ τὸν ἄνθρωπον φέροντες τροφὰς αὐτῷ ἐφ' ἡμέρας τοσαύτας ὅσον ἀποζῇν ἱκανῶς. περὶ δὲ κυνὸς ἐπιτολὴν θερισταῖς πλησίον αὐτοῦ θερίζουσιν ἐκομίσθη τις οἶνος ἐν κεραμίῳ μάλ' εὐώδης. ὁ μὲν κομίσας ἐγγὺς τῶν θεριζόντων καταθεὶς ἐχωρίσθη· τοῖς δ' ὡς ἧκεν ὁ καιρὸς τοῦ πίνειν, ἔθος μὲν ἦν αὐτοῖς ἐκχέουσι κρατῆρα μεθ' ὕδατος συμμέτρου κεραννύναι τὸν οἶνον, ὡς δὲ ἀνελομένου νεανίσκου τὸ κεράμιον, ἐξαιροῦντὰ τε τὸν οἶνον εἰς τὸν κρατῆρα, συνεξέπεσεν ἔχιδνα νεκρά. δείσαντες οὖν οἱ θερισταὶ μὴ τι πάθοιεν ἐκ τοῦ πόματος, αὐτοὶ μὲν ὕδατος ἔπιον, ὡς δ' ἀπηλλάττοντο, χαρίζονται δῆθεν ὑπὸ φιλανθρωπίας τῷ τὸν ἐλέφαντα νοσοῦντι τὸν ὅλον οἶνον, ἄμεινον αὐτῷ κρίναντες εἶναι τεθνάναι μᾶλλον ἢ ζῇν τοιούτῳ. ὁ δ' ἐκ τούτου πίνων ὑγιὴς ἐγένετο θαυμαστόν τινα τρόπον. ὅλον γάρ αὐτοῦ τὸ τοῦ δέρματος ὀχθῶδες ἀπέπεσεν ὡς τῶν μαλακοστράκων ζώων τὸ σκέπασμα. ὅσον δ' ὑπόλοιπον ἦν ἔτι μαλακὸν ἱκανῶς ἐφαίνετο καθάπερ τὸ τῶν καράβων τε καὶ καρκίνων, ὅταν ἀποπέσῃ τὸ πέριξ ὄστρακον. ἕτερον τοιοῦτον ἐξ ὁμοίας περιπτώσεως ἐγένετο κατὰ τὴν ἐν Ἀσίᾳ Μυσίαν, οὐ πόρρω τῆς ἡμετέρας πόλεως. ἄνθρωπος ἐλέφαντι κάμνων ἐπὶ χρῆσιν ὥρμησεν ὑδάτων θερμῶν αὐτοφυῶν ὠφελείας ἐλπίδι. παλλακὶς δ' ἦν αὐτῷ δούλη νέα τε καὶ καλὴ πολλοὺς ἐραστὰς ἔχουσα, ταύτῃ καὶ ἄλλα μέν τινα τῶν κατὰ τὴν οἰκίαν, ἀτάρ οὖν καὶ τὰ κατὰ τὸ ταμεῖον ἐπίστευεν ὁ κάμνων. ὡς δὲ καταχθέντων αὐτῶν, ἡνίκ' ἐχρῆτο τοῖς ὕδασιν, ἐν οἰκίᾳ παρακείμενον ἐχούσῃ χωρίον αὐχμηρὸν ἐχιδνῶν μεστὸν, ἐμπεσοῦσὰ τις αὐτῶν εἰς οἴνου κεράμιον ἀμελῶς κείμενον ἐναπέθανεν, ἕρμαιον ἡγησαμένη τὸ κατὰ τύχην ἐκβὰν ἡ παλλακὴ τῷ δεσπότῃ τὸν ποτὸν ἐκ τούτου προσέφερεν. ὁ δὲ πίνων αὐτὸ τῷ κατὰ τὴν καλύβην ὡσαύτως ὑγιάσθη. δύο μὲν ἤδη σοι ταῦτα διδάγματα τῆς κατὰ τὴν περίπτωσιν πείρας, ἕτερον δ' ἐπ' αὐτοῖς τρίτον ἐξ ἡμετέρας μιμήσεως. ἐπειδὴ γάρ τις νοσῶν τοῦτο τὸ νόσημα φιλοσοφώτερος ἢ κατὰ τοὺς πολλοὺς ἐδυσχέραινὲ τε δεινῶς καὶ τεθνάναι βέλτιον ἢ ζῇν ἔφασκεν εἶναι, διακειμένῳ οὕτως ἀθλίως ἐδήλωσα τὰς προειρημένας δύο περιπτώσεις αὐτῶν. ὁ δ', αὐτός τε γάρ ἦν ἔμπειρος οἰωνῶν ἐχρήσατὸ τε φίλῳ θαυμαστῶς κατορθοῦντι τὸ μάθημα, καθίσας ἐπ' ὄρνισιν ἅμ' ἐκείνῳ προὐτράπη τε μιμήσασθαι τὰ διὰ τῆς πείρας ἐγνωσμένα καὶ πίνων οἶνον οὕτω φαρμαχθέντα λεπρώδης ἐγένετο. χρόνῳ δ' ὕστερον ἰασάμεθα καὶ τὴν λέπραν αὐτοῦ τοῖς συνήθεσι φαρμάκοις. τέταρτος ἐπὶ τούτῳ τέχνην πεποιημένος ἐχίδνας ζώσας συλλαμβάνειν ἐν ἀρχῇ μὲν ἦν τοῦ πάθους ἐκείνου, προὔκειτο δ' ἡμῖν ὅπως ἰαθῇ τάχιστα. φλέβα τε οὖν αὐτοῦ τεμόντες καὶ καθήραντες φαρμάκῳ μέλαιναν κενοῦντι, χρήσασθαι ταῖς ἀγρευομέναις ἐχίδναις συνεβουλεύσαμεν, ἐν λοπάδι σκευάζοντι, καθάπερ τὰς ἐγχέλεις. οὗτος μὲν οὖν οὕτως ἐθεραπεύθη, διαπνεύσαντος αὐτῷ τοῦ πάθους. ἄλλος δὲ τις ἀνὴρ πλούσιος οὐχ ἡμεδαπὸς οὗτός γε, ἀλλ' ἐκ μέσης Θρᾴκης ἧκεν, ὀνείρατος προτρέψαντος αὐτὸν εἰς τὸ Πέργαμον, εἶτα τοῦ θεοῦ προστάξαντος ὄναρ αὐτῷ πίνειν τε τοῦ διὰ τῶν ἐχιδνῶν φαρμάκου καθ' ἑκάστην ἡμέραν καὶ χρίειν ἔξωθεν τὸ σῶμα, μετέπεσεν τὸ πάθος οὐ μετὰ πολλὰς ἡμέρας εἰς λέπραν, ἐθεραπεύθη τε πάλιν οἷς ὁ θεὸς ἐκέλευεν φαρμάκοις καὶ τοῦτο τὸ νόσημα. ἡ μὲν δὴ τῶν ἐχιδνῶν σάρξ εἰς τοσοῦτον ἥκει τῆς ξηραντικῆς δυνάμεως·ἐπεὶ δ' ἔνιοι τῶν φαγόντων αὐτὴν ἑάλωσαν δίψει σφοδροτάτῳ καὶ διὰ τοῦτο προσαγορεύουσι τὰς ἐχίδνας διψάδας. εἰσὶ δ' οἳ καὶ τοὺς δηχθέντας ὑπ' αὐτῶν φασιν οὐκ ἐμπίπλασθαι πίνοντας, ἀλλὰ διαρρήγνυσθαι πρότερον ἢ παύσασθαι διψῶντας. διὰ τοῦτο τῶν ἐν Ῥώμῃ τὰς ἐχίδνας θηρευόντων, οὓς ὀνομάζουσι Μαρσοὺς, ἐπυθόμην εἴ τι σημεῖον ἔχοιέν με διδάξαι διακριτικὸν ἑκατέρου τοῦ γένους τῶν ἐχιδνῶν· οἱ δ' οὐδὲν ὅλως ἔφασαν εἶναι γένος ἐχιδνῶν διψάδων, ἀλλὰ τὰς παρὰ θαλάττῃ καὶ τόποις ἁλμυρίδα πολλὴν ἔχουσι διαιτωμένας ἁλμυρὰν ἴσχειν τὴν σάρκα, διὸ καὶ κατὰ Λιβύην πολλὰς γίγνεσθαι τοιαύτας, ἐν Ἰταλίᾳ δ' οὐκ εἶναι διὰ τὴν ὑγρότητα τῆς χώρας. ταῦτα μὲν οὖν ἤκουσα τῶν Μαρσῶν λεγόντων, οὐ μὴν ἔχω βεβαίως εἰπεῖν εἴτ' ἀληθεύουσι τὸ σύμπαν εἴτε καὶ ψεύδονται κατὰ τι. τὸ μὲν γάρ ἐν οἷς εἰρήκασι χωρίοις γίνεσθαὶ τινας ἐχίδνας ἁλυκὴν ἐχούσας τὴν σάρκα πιθανώτατον εἶναὶ μοι δοκεῖ. συμμεταβαλλούσας γάρ οἶδα ταῖς τροφαῖς τὰς τῶν ζώων σάρκας, οὐ μὴν ὡς οὐδέν ἐστι γένος ἐχιδνῶν διψάδων ἀποφήνασθαι δύναμαι. τὸ δ' οὖν ἀσφαλέστατόν ἐστι φυλάττεσθαι τὰς ἐν τοῖς τοιούτοις χωρίοις ἐχίδνας θηρεύειν εἰς ἐδωδὴν ἢ φαρμάκου κατασκευὴν, ὁποῖόν ἐστι καὶ τουτὶ τὸ ἔνδοξον, ὃ καλοῦσιν ἅπαντες σχεδὸν ἰατροὶ θηριακήν. ἐπεὶ δ' ἔθος ἡμῖν ἐστιν, ὅταν τοὺς καλουμένους ἀρτίσκους θηριακοὺς σκευάζωμεν, ἀφαιρεῖν οὐ μόνον τὴν κεφαλὴν αὐτῶν, ἀλλὰ καὶ τὴν οὐράν, ἐνενόησα πολλάκις εὐλόγως ἴσως μὲν τὴν κεφαλὴν ὅλην, διὰ τὸν ἐν τῷ στόματι περιεχόμενον ἰὸν, ἀλόγως δὲ τὴν οὐρὰν ἀφαιρεῖσθαι. οὐδὲ γάρ τοῦτ' ἔστιν εἰπεῖν, ὅτι διὰ τὰ περιττώματα τῆς τροφῆς τὰ θ' ὑγρὰ καὶ τὰ ξηρὰ πρακτέον οὕτως ἐστίν. ἀποκτείναντες γάρ αὐτάς, εἶτ' ἐκδείραντές τε καὶ ἀναπτύξαντες, ἐξαιροῦμέν τε καὶ ἀπορρίπτομεν ἅπαντα τὰ ἔνδον, ὡς μόνην καταλείπεσθαι τὴν τῶν σαρκῶν οὐσίαν ἅμα ταῖς διαπεφυκυίαις αὐτῶν ἀρτηρίαις τε καὶ φλεψὶν, ἐλάχιστον ἐχούσαις ὄγκον ὡς πρὸς τὴν ὅλην σάρκα, καὶ μηδὲ φαινόμενον, ἐὰν μὴ πάνυ τις ἐπιμελῶς κατασκέψηται. τοὺς μὲν οὖν ἀρτίσκους, οὓς δὴ καὶ θηριακοὺς ὀνομάζουσι, σκευάζομεν οὕτως. κεκαθαρμένας αὐτὰς λαβόντες, εἶθ' ἕψοντες ἐν ὕδατι, μέχρις ἂν ἀκριβῶς ἡμῖν εἶναι δόξωσιν ἑφθαί. συνεμβάλλομεν δ' εὐθέως ἐξ ἀρχῆς ἀνήθου τῷ ὕδατι καὶ μετὰ τὴν ἕψησιν ἀπὸ τῶν σαρκῶν διακρίνομεν τὰς ἀκάνθας, εἶτα μίγνυμεν ἄρτῳ λελειωμένῳ τὴν σάρκα. τὸν δ' ἄρτον τοῦτον οὐ τὸν ἐπιτυχόντα λαμβάνομεν, ἀλλ' ὡς ἔνι μάλιστα καθαρώτατόν τε καὶ καλῶς ὠπτημένον ἐν κλιβάνῳ, συμμέτρων ἁλῶν ἔχοντα καὶ ζύμης. προαναξηραίνομεν δὲ αὐτὸν ἐν οἴκῳ ξηρῷ καὶ ἀνίκμῳ, μέχρις ἂν οὕτω γένηται ξηρὸς ὡς ἐν ὅλμῳ κοπῆναι δύνασθαι. οὐ μὴν κόπτοντές γε μίγνυμεν, ἀλλὰ διαβρέχοντες τῷ ὕδατι, καθὸ τὰς ἐχίδνας ἑψήσαμεν. αὐτὴν δὲ τὴν σάρκα πρὶν μιγνύναι τῷ ἄρτῳ, τρίβομεν ἐν θυίᾳ τῶν μαγείρων, ἄχρις ἂν ἀκριβῶς γένηται λεία. καὶ μετὰ ταῦτα μικροὺς ἀρτίσκους λεπτοὺς πλάσαντες, εἶτα ξηράναντες ἐν οἴκῳ θερμῷ καὶ ξηρῷ φυλάττομεν ἀποτιθέμενοι πάλιν ἐν οἴκῳ τοιούτῳ. τούτους μὲν οὖν εἰσβάλλοντος τοῦ θέρους σκευάζομεν, ἡνίκα μάλιστα βελτίστη τῶν ἐχιδνῶν ἐστιν ἡ σάρξ. χρώμεθα δ' ὕστερον κόπτοντές τε καὶ διάττοντες, εἶτ' αὖθις λειοῦντες ἀναμιγνύντες τε τοῖς ἐσκευασμένοις εἰς ἡδονὴν ἁλσὶν, ἐμβάλλομεν δ' αὐτῶν καὶ τῇ θηριακῇ. γίγνονται δὲ καὶ οἱ διὰ τῶν ὀπτηθεισῶν ἐχιδνῶν ἅλες ὑπὸ τὸν αὐτὸν καιρὸν εἰς χύτραν καινὴν ἐμβαλλόντων ἡμῶν τὰς ἐχίδνας ζώσας, ἅμα τοῖς ὑπεστορεσμένοις τε καὶ περικειμένοις αὐταῖς φαρμάκοις, ἃ λέγειν ἅπαντα νῦν οὐκ ἔστι τῆς ἐνεστώσης πραγματείας. ἴσως γάρ τις ἡμῖν εὐλόγως ἐγκαλέσει καὶ περὶ τῶν ἀρτίσκων τῆς κατασκευῆς ὡς οὐκ ἐν καιρῷ διελθοῦσιν. ἀλλὰ ταῦτα μὲν ἐπειδὴ φθάνει λελέχθαι, φυλαττέσθω, κᾂν δοκῇ μὴ πάνυ τι τῆς προκειμένης εἶναι πραγματείας ἴδια. τὰ δ' ἑξῆς κατὰ τὸ προσῆκον μέτρον λεγέσθω. προσῆκον δ' ἐστὶ περὶ τῆς καθόλου δυνάμεως ἀναμνῆσαι τὴν σάρκα τῶν ἐχιδνῶν, εἰπόντα εἶναι ξηραντικήν τε καὶ διαφορητικὴν ἰσχυρῶς, ἅμα τῷ θερμαίνειν μετρίως. ἐπείγεται δ', ὡς ἔοικεν, ἡ δύναμις αὐτῆς ἐπὶ τὸ δέρμα, διὰ τούτου κινοῦσα τὰ κατὰ τὸ σῶμα περιττώματα. φθειρῶν τε οὖν πλῆθος οὐκ ὀλίγον γεννᾶται τοῖς ἔχουσι κακοχυμίαν ἐν τοῖς σώμασι δαψιλῆ καὶ τοῦ δέρματος ἀφίσταταὶ τε καὶ ἀποπίπτει καθάπερ τι λέπος ἡ ἐπιδερμὶς ὀνομαζομένη, καθ' ἣν ἴσχονται μᾶλλον τῶν εἰς τὸ δέρμα φερομένων χυμῶν οἱ παχεῖς καὶ γεώδεις, ὑφ' ὧν αἵ τε ψῶραι καὶ αἱ λέπραι καὶ οἱ ἐλέφαντες γίνονται. ταῦτα μὲν οὖν εἶχόν σοι λέγειν περὶ τῶν τῆς ἐχίδνης σαρκῶν, ἐφεξῆς δὲ πάλιν ἀναλήψομαι τὸν λόγον. αἱ μὲν τῶν θερμοτέρων φύσει ζώων σάρκες οὐ μόνον τρέφουσιν ἡμᾶς, ἀλλὰ καὶ θερμαίνουσιν, αἱ δὲ τῶν ψυχροτέρων ψύχουσιν. οὕτως δὲ καὶ αἱ μὲν τῶν ξηροτέρων ξηραίνουσιν, αἱ δὲ τῶν ὑγροτέρων ὑγραίνουσιν. μεμνημένος οὖν ὧν ἔμαθες ἐν τοῖς περὶ κράσεων, ὅταν γνωρίσῃς τι τῶν ζώων εἶναι τῇ κράσει ξηρότερον, ὥσπερ εἰ τύχοι τὸν ἄγριον ὗν τοῦ ἡμέρου, γίνωσκε τούτου καὶ τὴν σάρκα ξηραντικωτέραν εἶναι καὶ κατὰ τὰς ἄλλας διαφορὰς τῶν κράσεων ὡσαύτως, οἷον ὅτι συὸς μὲν πρόβατον ξηρότερον, τούτου δ' αἲξ, τούτου δὲ βοῦς, καὶ τούτου λέων. οὕτω δὲ καὶ κατὰ θερμότητα λέων μὲν κυνὸς θερμότερος, κύων δὲ ταύρου, ταῦρος δὲ τοῦ τοὺς ὄρχεις ἐκτετμημένου βοός. ἀνάλογον οὖν τῇ κατὰ τὴν κρᾶσιν ὑπεροχῇ τῶν ἄλλων ζώων καὶ αἱ σάρκες αὐτῶν διοίσουσιν. καὶ διὰ τοῦτο ξηραίνειν μὲν ἐθέλων τὸ σῶμα τῶν ξηροτέρων τῇ κράσει ζώων δώσεις τὴν σάρκα, θερμαίνειν δὲ βουλόμενος τῶν θερμοτέρων, καὶ ψυχρότερον μὲν ἐπιχειρῶν ἐργάζεσθαι τῶν ψυχροτέρων, ὑγρότερον δὲ τῶν ὑγροτέρων. οὐ σμικρὰ δὲ διαφορὰ τῶν σαρκῶν ἐστι κᾀν τῷ τεταριχεῦσθαὶ τινας αὐτῶν. ὅλῳ γάρ παντὶ διαλλάττουσιν, ὡς πολλάκις ὑγροτάτου τῇ κράσει ζώου ταριχευθεῖσαν σάρκα ξηραντικωτέραν εἶναι μακρῷ τῆς φύσεως ξηρᾶς. ἀταριχεύτου καὶ ἡ ὀπτηθεῖσα δὲ ξηροτέρα τῆς ἑψηθείσης ἐστὶν ἐν ὕδατι. ἔγραψαν δὲ καὶ ἄλλων ζώων ἔνιοι σάρκας ὠφελεῖν ἐσθιομένας τε καὶ κατὰ πεπονθότων μερῶν ἐπιτιθεμένας, οἷον τὴν τοῦ χερσαίου ἐχίνου σκελετευθεῖσαν, εἰ ποθείη ἐλεφαντιῶσιν καὶ καχέκταις καὶ σπασμώδεσιν καὶ νεφριτικοῖς, ἔτι τε τοῖς τὸν ἀνασάρκα προσαγορευόμενον ὕδερον ἔχουσιν. εἰ δὲ ταῦτα ποιεῖν πέφυκεν, εἴη ἂν ἡ δύναμις αὐτῆς ἰσχυρῶς διαφορητικὴ τε καὶ ξηραντικὴ, ὥσπερ καὶ ἡ τῆς σκελετευθείσης γαλῆς, ἥπερ οὖν ὀνίνησι τοὺς ἐπιληπτικοὺς πινομένη. τῶν δὲ ταριχευθέντων αἰλούρων τὴν σάρκα λειωθεῖσαν ἐπιτιθεμένην ἐξάγειν σκόλοπὰς φασιν, ὡς ἑλκτικὴν ἔχουσαν δύναμιν δηλονότι, τῶν δὲ μυάκων ἁρμόττειν ἕλκεσιν ὑπὸ κυνὸς δάκνοντος γεγονόσιν. ἐγὼ δ' οὐδεμίαν ἐξαίρετον εὑρίσκω δύναμιν, ἧς δεῖται τὰ τοιαῦτα τῶν ἑλκῶν, ὥσπερ τὰ ὑπὸ τοῦ λυττῶντος κυνὸς δακόντος γενόμενα. καὶ ἡ τῶν κοχλιῶν δὲ σάρξ κοπεῖσα πρότερον ἐν ὅλμῳ καὶ μετὰ ταῦτα λειωθεῖσα ξηραντικωτάτη γίνεται πάντων τῶν ὑγρότητα περιττὴν ἐχόντων μορίων, ὥστε καὶ τοῖς ὑδερικοῖς ἁρμόττειν. ἡ δὲ ἐξ αὐτῶν ὑγρότης, μόνη καθ' ἑαυτὴν ἄνευ τῆς σαρκὸς λαμβανομένη, καλεῖται ὑπὸ τῶν πολλῶν μύξα κοχλίου, μιγνυμένη δὲ λιβανωτῷ ἢ ἀλόῃ ἢ σμύρνῃ ἤ τισι τούτων ἢ πᾶσιν ἄχρι τοῦ κηρωτῆς πάχος ἔχειν, ἐχέκολλόν τε γίνεται φάρμακον καὶ ξηραίνει καλῶς τοὺς ὑποπύους μύξους τῶν ὤτων. ἔστι δὲ καὶ ἀνακόλλημα ξηραντικὸν τῶν εἰς ὀφθαλμοὺς ῥευμάτων, ἐπιτιθεμένη κατὰ τὸ μέτωπον. ἔνιοι δὲ καὶ πρὸς σκόλοπας χρῶνται, λειοῦντες ὅλους μετὰ τῶν ὀστράκων, εἰσὶ δ' οἳ καὶ πρὸς καταμηνίων ἐπίσχεσιν. αὐτὰς δὲ τὰς σάρκας μόνας κᾀγώ ποτε κατ' ἀγρὸν ἐπὶ τραύματος ἅμα νεύρου τρώσει τε καὶ θλάσει γεγονότος ἐπέθηκα λειώσας, καὶ τὸ τε τραῦμα καλῶς ἐκολλήθη καὶ τὸ νεῦρον οὐκ ἐφλέγμηνε. ἦν δὲ σκληρὸς καὶ ἀγροῖκος ἄνθρωπος, ἔμιξὰ γε μὴν λειουμέναις αὐταῖς ἄχνην ἀλεύρου, λαβὼν ἀπὸ τοῦ πλησιάζοντος τῇ μύλῃ τοίχου. γεγράφασι δὲ τινες τῶν πρὸ ἡμῶν ἰατρῶν σμύρναν ἢ λιβανωτὸν μιγνύειν αὐτοῖς δεῖν ἐπὶ τῆς τοιαύτης χρήσεως, ἀλλ' οὐδετέραν εἶχον τούτων ἔξωθεν τῆς πόλεως ἐπὶ τῆς ἀγροικίας. δύναιτο δ' ἄν τις καὶ ῥητίνης φρικτῆς λείας μιγνύειν εἰ παρείη. ὁπόταν μέντοι πολὺ τῆς μύξης τῶν κοχλιῶν ἐθέλεις λαβεῖν μόνης, κατακέντησον αὐτῶν τὴν σάρκα γραφείῳ. χρὴ δὲ μὴ πρὸ πολλῶν ἡμερῶν αὐτοὺς θηρεῦσαι, καταξηραίνονται γάρ ἐν τῷ χρόνῳ. πρόσφατοι δ' ὄντες πολὺ τῆς γλίσχρας ὑγρότητος ἔχουσιν, ἣν κατακεντούμενοι τῷ γραφείῳ προϊᾶσιν. ἡ δ' ὑγρότης αὕτη καὶ τῶν ἐν τοῖς βλεφάροις τριχῶν παρὰ φύσιν ἀνακόλλημα γίνεται.
