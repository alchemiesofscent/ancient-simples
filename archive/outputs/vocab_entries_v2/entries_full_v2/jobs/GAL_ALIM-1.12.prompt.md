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
CONTEXT_PREV_SOURCE_ID: GAL_ALIM-1.11
CONTEXT_PREV_TEXT:
Ἐκ τῶν νέων κριθῶν φρυγεισῶν συμμέτρως τὸ κάλλιστον ἄλφιτον γίγνεται· τούτων δ' ἀποροῦντες ἐνίοτε κἀκ τῶν ἄλλων αὐτὰ σκευάζομεν. εὐωδῶν δ' ὄντων ἁπάν|των, ὅσα καλῶς ἐσκευάσθη, μάλιστ' ἐστὶν εὐώδη τὰ ἐκ τῶν ἀρίστων καὶ νέων κριθῶν γιγνόμενα μὴ πάνυ ξηρὸν ἐχουσῶν τὸν στάχυν. ἐν ἔθει δ' ἐστὶ πολλοῖς τῶν ὑγιαινόντων ἐπιπάττειν αὐτὰ σιραίῳ καὶ οἴνῳ γλυκεῖ καὶ οἰνομέλιτι κεκραμένοις ἐν ὕδατι καί ποτε καὶ ὕδατι μόνῳ καὶ πίνειν ἐν τῷ θέρει πρὸ δυοῖν ἢ τριῶν ὡρῶν τοῦ λουτροῦ καί φασιν αἰσθάνεσθαι τοῦ πόματος ἀδίψου. δι' οἴνου γε μὴν αὐστηροῦ ποθέντα ξηραίνει γαστέρα. χρῶνται δ' ἀλφίτοις ἔν τισι τῶν ἐθνῶν ἐν ἄρτου χρείᾳ, καθάπερ ἐπὶ τῶν ἀγρῶν εἶδον ἐν Κύπρῳ, καίτοι πλεῖστον γεωργοῦσι σῖτον. οἱ παλαιοὶ δὲ καὶ τοῖς στρατευομένοις ἄλφιτα παρεσκεύαζον. ἀλλ' οὐ τό γε νῦν ἔτι τὸ Ῥωμαίων στρατιωτικὸν ἀλφίτοις χρῆται κατεγνωκὸς αὐτῶν ἀσθένειαν. ὀλίγην γὰρ τροφὴν δίδωσι τοῖς σώμασι, τοῖς μὲν ἰδιωτικῶς διακειμένοις καὶ ἀγυμνάστοις αὐτάρκη, τοῖς δ' ὁπωσοῦν γυμναζομένοις ἐνδεῆ. γίγνονται δ' ἐξ αὐτῶν ὑγρῷ φυραθέντων αἱ μᾶζαι, περὶ ὧν ἐφεξῆς ἐροῦμεν, ἐπειδὴ καὶ Φυλότιμος ἐπὶ πλέον ὑπὲρ | αὐτῶν διελθὼν ἐν τῷ πρώτῳ Περὶ τροφῆς ὅμως ἀδιόριστον εἴασε τὸ χρησιμώτατον ἐν αὐταῖς.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_ALIM-1.12
TEXT:
Τὴν δύναμιν ἑκάστου τῶν ἐδεσμάτων ἔνεστί σοι καὶ πρὸ τῆς διωρισμένης πείρας ἐκ τῆς φύσεως αὐτῶν τεκμήρασθαι. τίνι γὰρ οὐκ ἂν ἀνδρὶ συνετῷ τὸ μὲν ἀκριβῶς λεπτὸν καὶ λευκὸν καὶ καθαρὸν ἁπάσης πιτυρώδους οὐσίας ἄλευρον ἐνδείξαιτο καὶ κατὰ τὴν γαστέρα θᾶττόν τε καὶ μᾶλλον ἀλλοιοῦσθαι καὶ διὰ τοῦτο πέττεσθαί τε κάλλιον ἀναδίδοσθαί τε ῥᾷον ἑτοιμότερόν τε τρέφειν, ὡς ἂν ὅλον ἐξομοιούμενόν τε καὶ προστιθέμενον τοῖς τρεφομένοις σώμασιν, ὅσον δ' ἐν αὐτῷ πιτυρῶδές τ' ἐστὶ καὶ σκληρόν, ὥσπερ ἐκτὸς φαίνεται μὴ διαλυόμενον ὕδατι, κατὰ τὸν αὐτὸν λόγον οὐδ' ἐν τῇ γαστρὶ διαλύεσθαι βρεχόμενον, ἀλλὰ διαμένειν ὅλον ἀδιαίρετόν τε καὶ ἀκατέργαστον, ὁποῖον ἐλήφθη; τοῦτ' οὖν οὔτε πέττεσθαι δύναται καλῶς οὔτ' ἀναδίδοσθαι διὰ τὸ μηδ' ἐναρμόττειν ὅλως τοῖς στόμασι τῶν εἰς τὴν γαστέρα καὶ τὰ ἔντερα καθηκουσῶν φλεβῶν. οἷς ἐξ ἀνάγκης ἕπεται πλέον μὲν ἀπ' αὐτοῦ γίγνε|σθαι τὸ κοπρῶδες, ὑπιέναι δὲ θᾶττον αὐτῷ τε τῷ διὰ πλῆθος βάρει καὶ προσέτι τῷ ῥυπτικὴν ἔχειν ποιότητα τὸ πιτυρῶδες ἅπαν. εὔδηλον οὖν ἐστι τῷ ταῦτ' ἐννοήσαντι, τοσοῦτον ἀπολείπεσθαι μᾶζαν εἰς τροφὴν σώματος ἄρτων κριθίνων, ὅσον οὗτοι πυρίνων. ἐχούσης γὰρ ἤδη φύσει τῆς κριθῆς τὸ πιτυρῶδες οὐκ ὀλίγον ἡ φρυγεῖσα ξηρότερον μὲν καὶ αὐτὸ τοῦτο καὶ δυσθραυστότερον ἴσχει, ξηρότερον δὲ καὶ τὸ τούτου κρεῖττον, ἐξ οὗ τὴν τροφὴν ἐλάμβανε τὸ σῶμα. κατὰ τοῦτ' οὖν ἧττόν τε πέττεται τῶν κριθίνων ἄρτων ἡ μᾶζα καὶ φύσης μᾶλλον ἐμπίπλησι τὴν γαστέρα καὶ ἢν ἐπὶ πλέον ἐν αὐτῇ μείνῃ, ταραχὴν ἐργάζεται. μᾶλλον δὲ διαχωρεῖ κάτω φυραθεῖσα καὶ τριφθεῖσα μέχρι πλείονος. εἰ δὲ καὶ μέλι προσλάβοι, θᾶττον ἔτι καὶ διὰ τοῦτ' αὐτὸ παρορμήσει τὴν γαστέρα πρὸς ἔκκρισιν. Φυλότιμος μὲν οὖν οἴεται παχὺν καὶ κολλώδη καὶ ψυχρὸν ἐξ ἁπάσης μάζης γεννᾶσθαι χυμόν, ὃν αὐτός τε καὶ ὁ διδάσκαλος αὐτοῦ Πραξαγόρας «ὑαλώδη» καλοῦσι. τὸ δ' οὐχ οὕτως ἔχει, μήτε τὸ γλίσχρον ἐχόντων | τῶν ἀλφίτων, ὅπερ ἐν χόνδρῳ μάλιστ' ἐστί, μήτε τὸ τρόφιμον. ἐξαπατᾷ δ' αὐτὸν ἡ ἐπὶ πλέον ἐν οἴνῳ γλυκεῖ καὶ σιραίῳ φυραθεῖσα χρόνῳ πολλῷ μᾶζα. τριπτὴν δ' αὐτὴν ὀνομάζει καθάπερ Ἀθηναῖοι. τὸ γὰρ ἐκ ταύτης ἀνάλογον τῷ πυρίνῳ σταῖς γενόμενον ὅλκιμόν ἐστι καὶ κολλῶδες ἔκ τε τοῦ μεμαλάχθαι χρόνῳ πλείονι καὶ τοῦ μιχθέντος τοῖς ἀλφίτοις ὑγροῦ παχέος ὄντος. ὥσπερ δὲ τρῖψις πολλὴ μεθ' ὑγροῦ παχέος γενομένη γλίσχρον τῇ φαντασίᾳ τὸ τριφθὲν ἄλευρον ἐργάζεται, κἂν ἐκ κέγχρων ᾖ, κατὰ τὸν αὐτὸν λόγον ὁ χυλὸς τῆς πτισάνης φαίνεται γλίσχρος οὐδὲν ἔχων ἐν ἑαυτῷ κολλῶδες οὐδ' ἐμπλαστικόν, ἀλλὰ ῥυπτικόν τε καὶ τμητικόν, ὡς κἀπὶ τοῦ δέρματος ἡμῶν φαίνεται τὸν ῥύπον ἀφαιρῶν. εἰ δὲ καὶ ῥοφῆσαί τινι δοὺς αὐτὸν ὀλίγον ὕστερον ἐμέσαι ποιήσειας, ἀπορρύψει τε τὸ περιεχόμενον ἐν τῇ γαστρὶ φλέγμα καὶ συνεκβαλεῖ πᾶν ἅμ' ἑαυτῷ κατὰ τὸν ἔμετον.
