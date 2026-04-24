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
CONTEXT_PREV_SOURCE_ID: GAL_SMT-10.2.19
CONTEXT_PREV_TEXT:
ἐγὼ γοῦν οἶδα καὶ αὐτὸς θαυμαστῆς δυνάμεως πειραθεὶς ἀνθρωπείας τε καὶ κυνὸς κόπρου. λέξω δὲ σοι περὶ προτέρας τῆς κυνείας, ᾗ συνεχῶς ἐχρῆτὸ τις τῶν ἡμετέρων διδασκάλων, ὀστᾶ διδοὺς ἐσθίειν κυνὶ μόνα δυεῖν ἐφεξῆς ἡμερῶν, ἐξ ὧν σκληρὰ καὶ λευκὴ καὶ ἥκιστα δυσώδης ἡ κόπρος γίγνεται. ταύτην οὖν λαμβάνων ἐξήραινεν, ὡς ὕστερον ὁπότε βούληται χρῆσθαι λειοῦσθαι ῥᾳδίως. ἐχρῆτο δ' αὐτῇ πρός τε συνάγχας καὶ δυσεντερίας καὶ τὰ παλαιότατα τῶν ἑλκῶν. πρὸς μὲν οὖν συνάγχας, ἀναμιγνὺς τοῖς καὶ ἄλλως ἁρμόττουσιν πρὸς τὸ πάθος τοῦτο φαρμάκοις·ἐπὶ δὲ δυσεντερικῶν τῷ ἀφεψημένῳ γάλακτι, τῶν καλουμένων καχλήκων διαπύρων ἐμβεβλημένων, ἢ ὡς ὕστερον ἐγὼ διὰ τὸ εὐπόριστον ἐπὶ τὸν σίδηρον ἧκον, ἐμβάλλων τοῦτον διάπυρον τῷ γάλακτι καλῶς προαφεψημένῳ. καλοῦσι δ' ἔνιοι τῶν ἰατρῶν οὐκ οἶδ' ὅπως τὸ τοιοῦτον γάλα σχιστόν. ἐχρῆν γάρ οὐ τοῦτο καλεῖν οὕτως, ἀλλ' ἐφ' ὧν χωρίζομέν τε καὶ σχίζομεν ἀπὸ τοῦ τυρώδους τὸν ὀρρόν. ἀλλὰ τῆς κυνείας κόπρου ξηρᾶς λειώσας ὁ ἰατρὸς ἐνέβαλλε τῷ τοὺς κάχληκας ἐναπεσβεσμένους ἔχοντι γάλακτι λανθανόντως καὶ μόνους τοὺς γνησιωτάτους μαθητὰς ἐδίδαξε τοῦτο. τούτων μὲν οὖν τῶν δύο χρήσεων τῆς κυνείας κόπρου πάνυ πολλὴν ἔχω πεῖραν ὡς θαυμαστοῦ φαρμάκου, καθάπερ καὶ τῆς ἐπὶ τῶν κακοηθεστάτων ἑλκῶν. ἐμίγνυε γάρ οὖν κᾀπ' ἐκείνων τοῖς δοκίμοις φαρμάκοις τῆς κυνείας κόπρου βραχὺ, καὶ σαφῶς ἰσχυρότερον ἑαυτοῦ τὸ φάρμακον ἐγίγνετο, καὶ εἴ που διαφορῆσαὶ τι καὶ ξηράναι, κἀκείνοις τοῖς φαρμάκοις ἐμίγνυεν.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_SMT-10.2.20
TEXT:
τῆς ἀνθρωπείας κόπρου τοιάνδε τινὰ πεῖραν ἔχω. συνεχῶς τις ὑπὸ τῶν κατὰ τὴν φάρυγγα φλεγμονῶν ἠνωχλεῖτο σφοδρῶς, ὡς κινδυνεύειν ἀποπνιγῆναι, καὶ δὴ φλεβοτομεῖσθαι διὰ τὸν κίνδυνον τοῦτον ἠναγκάζετο. τούτῳ τις ἐντυχὼν ἐπηγγείλατο πεῖραν δώσειν φαρμάκου καὶ καλεῖν ἑαυτὸν ἠξίου πρὸ τῆς φλεβοτομίας, ὅταν αὖθίς ποτε φλεγμήνῃ τι τῶν κατὰ τὴν φάρυγγα μορίων αὐτοῦ. καὶ τοίνυν κληθεὶς, εἶτα διαχρίσας φαρμάκῳ ταχέως ἐθεράπευσε τὸν ἄνθρωπον. ὡς δὲ καὶ αὖθις ἤδη ἐνήργησεν, οὐκ ἐπὶ αὐτοῦ μόνου, ἀλλὰ καὶ ἐπ' ἄλλων τῶν ὁμοίως πασχόντων ἠξίου δοὺς μισθὸν ὁ συνεχῶς κινδυνεύων πνιγῆναι μαθεῖν τὸ φάρμακον. ἦν δ' ἅμα τε πλούσιος καὶ περὶ χρημάτων δαπάνην ἐλευθέριος. ὡς δὲ περὶ τοῦ μισθοῦ συνέβησαν, ὁ πιπράσκων τὴν γραφὴν ἀντιπαθείᾳ τινὶ τὴν ὠφέλειαν ἔφη τὸ φάρμακον ἔχειν. εἶναι δὲ τὴν ἀντιπάθειαν τὸ μὴ γνῶναι τὸν θεραπευόμενον ἐξ ὧν σύγκειται. ἐκέλευσεν οὖν ἄλλον ἀνθ' ἑαυτοῦ μαθησόμενον, ὅστις ἂν αὐτῷ πιστότατος εἶναι δοκῇ, καὶ τοῦτο αὐτὸν ὀμόσαι βουλόμενον μηδενὶ δοῦναι τὴν γραφὴν τοῦ φαρμάκου, μέχρις ἂν αὐτὸς ὁ ἀποδιδόμενος ζῇ. κατὰ τοῦτον μὲν δὴ μετὰ τὸν τοῦ δείξαντος θάνατον ὁ μαθὼν οὐ μόνον τὸν ἴδιον ἄνθρωπον, ἀλλὰ καὶ τοὺς ἄλλους ἰᾶται, κᾀμοῦ μηδ' αἰτήσαντος τοῦ φαρμάκου τὴν γραφὴν οὗτος ἔδωκεν ἑκών· ἦν δὲ κόπρος παιδίου ξηρὰ μετὰ μέλιτος Ἀττικοῦ λελειωμένη. διῃτᾶτο δὲ τὸ παιδίον, οὗ τὴν κόπρον ἔμελλον λήψεσθαι, καθάπερ αὐτὸς ὁ δοὺς τὸ φάρμακον ἔδειξεν, ἐπὶ θέρμων ἐδωδῇ. τούτων δὴ τῶν συνήθως ἐσθιομένων μετ' ἄρτου καλῶς ὠπτημένου κλιβανίτου συμμέτρων ἁλῶν τε καὶ ζύμης ἔχοντος. ἐδίδου δὲ καὶ οἶνον παλαιὸν πίνειν. ἅπαντα ταῦτα σύμμετρα κατὰ τὸν ὄγκον, ὡς ἀκριβῶς εὐπεπτῆσαι τὸ παιδίον. ἐπὶ μὲν δὴ τῆς πρώτης ἡμέρας τοιαύτῃ διαίτᾳ χρώμενος οὐδέπω κατὰ τὴν ὑστεραίαν ἀνῃρεῖτο τὴν κόπρον· ἐν ἐκείνῃ δ' αὖ πάλιν ὁμοίως διαιτήσας τὸ κατὰ τὴν τρίτην ἐκκριθὲν ἐλάμβανεν καὶ ξηραίνων ἐχρῆτο παραπλησίως τῇ κυνείᾳ κόπρῳ, καθότι προείρηται. ἔλεγε δὲ τὸν διδάξαντα διὰ τὴν δυσωδίαν τῶν ἄλλων ἐδεσμάτων φεύγοντα τοὺς θέρμους αἱρεῖσθαι, ἑαυτὸν δὲ ἕνεκα πείρας ὀρνιθείου κρέως καὶ περδικείου δι' ὕδατος ἢ λιτοῦ ζωμοῦ καλῶς ἑψημένου ἐδηδοκέναι πολλάκις, ἐνηργηκέναι δὲ τὸ φάρμακον οὐδὲν ἧττον. ἐγὼ μὲν δὴ σοι ταῦτα λέγειν ἔχω περὶ κυνείας τε καὶ ἀνθρωπείας κόπρου.
