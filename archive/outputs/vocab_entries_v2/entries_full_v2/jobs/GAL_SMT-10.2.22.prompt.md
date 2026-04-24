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
CONTEXT_PREV_SOURCE_ID: GAL_SMT-10.2.21
CONTEXT_PREV_TEXT:
τὴν δὲ τῶν λύκων ἐπότιζὲ τις κωλικοὺς οὐ μόνον ἐν τοῖς παροξυσμοῖς, ἀλλὰ καὶ τοῖς διαλείμμασιν, ὅσοι γε χωρὶς φλεγμονῆς ἔπασχον. εἶδον δὲ τινας αὐτῶν οὐκέθ' ἁλόντας τῷ παθήματι καὶ τοὺς ἁλόντας οὐκέτ' οὐδέποτ' αὖθις ἰσχυρῶς παθόντας, ἀλλ' οὐδὲ μετ' ὀλίγον χρόνον. ἐλάμβανε δὲ κᾀκεῖνος τὴν λευκοτέραν κόπρον τῶν λύκων μᾶλλον, ἥτις ὀστᾶ φαγόντων αὐτῶν ἀποκρίνεται. ἐθαύμασα δ' ἐπ' αὐτῷ, ὅτι καὶ περιαπτόμενον πολλάκις ἐναργῶς ὠφέλησεν. ἐλάμβανεν οὖν οὗτος τὴν κόπρον οὐδὲ πεπτωκυῖαν ἐπὶ τὴν γῆν, οὐ χαλεπῶς δὲ γίνεται τοῦτο. φύσιν γάρ ἔχει ἐκεῖνο τὸ ζῶον, καθάπερ ὁ κύων, ἐπαίρων τὸ ἕτερον τῶν ὀπισθίων σκελῶν ἐνουρεῖν καὶ ἀποπατεῖν πρός τι τῶν ἐξεχόντων τῆς γῆς. ἐπ' ἀκάνθαις τε οὖν πολλάκις εὑρίσκεται θέρους ἐν ὥρᾳ λυκεία κόπρος ἐπὶ τε θάμνοις τισὶ καὶ κλείθροις καὶ βοτάναις εὐαυξέσιν. εὑρίσκεται δὲ ἐν ταῖς κόπροις αὐτῶν καὶ αὐτῶν τῶν ὀστῶν τι τοῦ καταβεβρωμένου ζώου διαπεφευγότος, ὥσπερ τὴν μάσησιν, οὕτω καὶ τὴν πέψιν, ὃ καὶ αὐτὸ κόπτων καὶ λειῶν ἐδίδου πίνειν τοῖς κωλικοῖς. καὶ εἰ καθαρότητος ἄνθρωπος εἴη καὶ ἁλῶν καὶ πεπέρεως ἤ τινος τῶν τοιούτων, ἐμίγνυεν. ἐδίδου δὲ τοὐπίπαν μὲν δι' οἴνου λεπτοῦ κατὰ τὴν σύστασιν, ἔστι δ' ὅτε καὶ δι' ὕδατος. τὸ δ' οὖν περιαπτόμενον τῆς κόπρου ταῖς λαγόσι τοῦ πάσχοντος ἐκέλευσεν ἔχειν ἄρτημα, μάλιστα μὲν ἐξ ἐρίου γεγονὸς οὐ τοῦ τυχόντος προβάτου. πολὺ γάρ εἶναι βέλτιον ὑπὸ τοῦ λύκου διεσπασμένου ἐπὶ τὸ πρὸς τὴν τοιαύτην χρείαν ἐπιτήδειον ἐσόμενον. εἰ δὲ μὴ παρείη τὸ τοιοῦτον ἔριον, ἐκ δέρματος ἐλαφείου τὸν ἱμάντα τὸν περιελιττόμενον ταῖς λαγόσι καὶ αὐτὸ τὸ περιέξον τὴν κόπρον ἐκέλευσεν εἶναι. ἡμεῖς δὲ καὶ εἰς χυτρίδιον τηλικοῦτον, ἡλίκος ἐστὶν ὁ μέγιστος κύαμος, ἐμβάλλοντες τῆς κόπρου περιήψαμεν ἐνίοις ἕνεκα πείρας, ἐθαυμάσαμέν τε φανερῶς ὠφεληθέντας ἰδόντες τοὺς πλείστους αὐτῶν. ἐποιοῦμεν δὲ τῷ χυτριδίῳ δύο τινὰ καθάπερ ὦτα, δι' ὧν ὁ ἱμὰς διεβάλετο. τοῦτο μὲν δὴ κατὰ τὸ πάρεργον, εἰ μέλλει τις καὶ τοῖς οὕτω περιαπτομένοις πιστεύειν, λέγω δ' οὕτως, ὥστ' οὐσίαν εἶναι τὴν περιαπτομένην, οὐκ ὀνόματα βάρβαρα, καθάπερ εἰώθασιν ἔνιοι τῶν γοήτων, ἐπείτοι καὶ ἄλλων οὐσιῶν ἐπειράθην ὁμοίως ἐνεργουσῶν ἐπ' ἄλλων παθῶν. ἀλλ' οὐ νῦν καιρὸς ὑπὲρ αὐτῶν λέγειν, ἴωμεν οὖν αὖθις ἐπὶ τὸ προκείμενον.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_SMT-10.2.22
TEXT:
ἀνθρωπείας μὲν γάρ καὶ κυνείας καὶ λυκείας ἐμνημόνευσα κόπρου, τῶν δ' ἄλλων οὐδέπω, καίτοι πλείους ἔτι τῶν εἰρημένων ὑπολείπονται, τινὲς μὲν καὶ πάνυ συνεχῆ τὴν χρείαν παρέχουσαι, τινὲς δὲ σπανιωτέραν. συνεχέστατα μὲν οὖν χρώμεθα ταῖς τῶν αἰγῶν κόπροις, σπύραθοι δ' ἰδίως ὀνομάζονται δριμείας καὶ διαφορητικῆς οὖσαι δυνάμεως, ὡς καὶ τοῖς σκιρρουμένοις ὄγκοις ἁρμόττειν οὐ σπληνὸς μόνον, ἐφ' ὧν συνεχέστατα χρῶνται πολλοὶ τῶν ἰατρῶν ταῖς τοιαύταις κόπροις, ἀλλὰ καὶ ἄλλων μερῶν. ἔγωγ' οὖν ἐπὶ γόνατος ἔχοντος ὄγκον χρόνιον δύσλυτον ἐχρησάμην αὐτῇ δι' ὀξυκράτου καταπλάττεσθαι κελεύσας ἄλευρον κρίθινον ἐπιβαλλομένης τῆς κόπρου, καὶ θαυμαστῶς ὁ ἄνθρωπος ὤνητο. τῶν δ' ἀγροίκων τις ἦν, ἐφ' ᾧ τοῦτο ἐπράχθη. καὶ οὕτως ἤδη καὶ ἄλλος ἀγροῖκος ἐφ' ὁμοίων ὄγκων οὐ κατὰ γόνατος μόνον, ἀλλὰ καὶ κατ' ἄλλων μορίων ὁμοίως χρησάμενος ὠφελήθη. δριμύτερον γάρ ἐστι τὸ φάρμακον ἢ ὥστε γυναῖκας ἀστυκὰς ἢ παιδία θεραπεύειν, ἢ ὅλως τοὺς μαλακοσάρκους. ἀλλὰ περὶ μὲν τῆς κατὰ μέρος χρήσεως ἁπάντων φαρμάκων ἐν τῷ περὶ συνθέσεως αὐτῶν εἰρήσεται. καὶ ἐπὶ τῶν ὑδερικῶν τε καὶ σπληνικῶν τῇ αἰγείᾳ κόπρῳ πολυειδῶς χρώμεθα. καὶ μέντοι καὶ καυθεῖσα λεπτομερεστέρα μὲν, οὐ μὴν δριμυτέρα γε σαφῶς γίνεται. διὸ καὶ πρὸς ἀλωπεκίας ἁρμόττει καὶ πάνθ' ὅσα τῶν ῥυπτόντων δεῖται φαρμάκων, οἷον λέπρας τε καὶ ψώρας καὶ λειχῆνας, ὅσα τ' ἄλλα τοιαῦτα. μίγνυται δὲ καὶ τοῖς διαφορητικοῖς καταπλάσμασιν, οἷα τὰ τῶν παρωτίδων ἐστὶ καὶ τῶν βουβώνων κεχρονικότων. ἔστι γάρ ἡ δύναμις αὐτῆς ἀκαύστου καὶ κικαυμένης ῥυπτικὴ τε καὶ διαφορητικὴ, καὶ οὐ βραχὺ γε τὸ διαφορητικὸν ἔχει. πρὸς γοῦν τὰ τῶν ἐχιδνῶν δήγματα καὶ πολὺ δὴ μᾶλλον ἔτι τὰ τῶν ἄλλων θηρίων ἰατρός τις τῶν ἐν ἀγροῖς τε καὶ κώμαις ἰατρευόντων ἐχρῆτο δι' ὄξους αὐτῇ καὶ διέσωσε πάνυ πολλούς. ὁ δ' αὐτὸς οὗτος ἰατρὸς καὶ τοῖς ἰκτερικοῖς ἐδίδου τὰς σπυράθους δι' οἴνου πίνειν καὶ πρὸς ῥοῦν γυναικεῖον ἐχρῆτο, σὺν λιβανωτῷ προστιθείς. καὶ χρὴ γινώσκειν μὲν ἅπαντα τὰ τοιαῦτα τὸν ἄριστον ἰατρὸν, ἐκλέγεσθαι δὲ τὰ βελτίω, καὶ μάλιστ' ἐπὶ τῶν ἀστυκῶν τε καὶ ἀξιολόγων ἀνδρῶν, ἐφ' ὧν οὐκ ἄν ποτ' ἐχρησάμην ἐγὼ τοιούτῳ φαρμάκῳ παμπόλλων ἀμεινόνων εὐπορῶν. ὅμως δ' οὖν γίγνεταὶ ποτε καὶ τῶν τοιούτων ἡ χρεία κατὰ τὰς ὁδοιπορίας καὶ τὰ κυνηγέσια καὶ τὴν ἐν ἀγρῷ διατριβὴν, ὅταν τι μὴ παρῇ τῶν βελτιόνων, ἢ καὶ σκληρόσαρκος ὁ ἀγροῖκος ἄνθρωπος ᾖ, παραπλήσιος ὄνῳ. πολλοὶ γάρ τῶν τοιούτων κατὰ τοὺς ἀγροὺς εἰσὶν ἄξιοι τοῦ πίνειν σπύραθα. ὅπερ δὲ κᾀν τοῖς ἔμπροσθεν ἐπ' οὔρων τε καὶ χολῶν καὶ σιάλων ἐρρέθη, τοῦτο καὶ νῦν μέμνησο, τὴν μὲν καθόλου καὶ κοινὴν δύναμιν ἁπάσαις εἶναι τὴν αὐτὴν, ἐξηλλάχθαι δὲ κατὰ τὰς τῶν ζώων κράσεις. τῶν μὲν γάρ ξηροτέρων τῇ κράσει ζώων καὶ ἡ κόπρος ἐστὶ ξηραντικωτέρα, καθάπερ γε καὶ τῶν θερμοτέρων θερμαντικωτέρα, ψύχει δ' οὐδεμία, καθάπερ οὐδ' ὑγραίνει. πολλὰ δ' ἂν εἴη καὶ παρὰ τὴν φύσιν τῶν ἐδηδεσμένων αὐτῶν ἡ διαφορὰ, καὶ διὰ τοῦτ' ἐπ' ἀνθρώπων μᾶλλον ἢ τῶν ἄλλων ζώων μείζων ἐστὶν, ὅτι ποικιλωτάτης τῆς τροφῆς χρῆται τὸ ζῶον τοῦτο. τὶ γάρ ὅμοιον ἔχει σκόροδὰ τε καὶ κρόμμυα φαγόντες ἢ κολοκύνθην, εἰ οὕτως ἔτυχεν; αἰγὸς δὲ σπύραθοι βραχὺ μὲν ἄν τι διαφέροιεν ἀλλήλων παρὰ τὰς νομάς, οὐ μὴν τοσοῦτόν γε ὅσον αἱ τῶν ἀνθρώπων.
