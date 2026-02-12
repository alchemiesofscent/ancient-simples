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
CONTEXT_PREV_SOURCE_ID: GAL_ALIM-2.10
CONTEXT_PREV_TEXT:
Τὸν αὐτὸν λόγον ἔχουσι πρὸς τὰς σταφυλὰς αἱ σταφίδες, ὃν αἱ ἰσχάδες πρὸς τὰ σῦκα. γίγνονται δὲ γλυκεῖαι μὲν πολλαί, στρυφναὶ δὲ παντάπασιν ὀλίγαι, μικταὶ δ' ἔκ τε γλυκείας καὶ αὐστηρᾶς ποιότητος αἱ πλεῖσται. μέτεστί γε μὴν καὶ ταῖς γλυκείαις ἀμυδρᾶς ποιότητος αὐστηρᾶς καὶ ταῖς αὐστηραῖς τῆς γλυκείας. αἱ μὲν οὖν αὐστηραὶ ψυχρότεραι τὴν κρᾶσίν εἰσιν, ὥσπερ αἱ γλυκεῖαι θερμότεραι. καὶ τὸν μὲν στόμαχον ῥωννύουσι καὶ τὴν γαστέρα στεγνοῦσιν αἱ αὐστηραί, καὶ δῆλον ὅτι μᾶλλον αὐτῶν αἱ στρυφναί. μέσην δέ πως κατάστασιν ἐν αὐταῖς αἱ γλυκεῖαι ποιοῦσι, μήτ' ἐκλύουσαι σαφῶς τὸν στόμαχον μήθ' | ὑπάγουσαι τὴν γαστέρα. τό γε μὴν ἐπικεραστικὸν ὑπάρχει ταῖς γλυκείαις ἀεί, καθάπερ γε καὶ τὸ μετρίως ῥυπτικόν, ὥστ' ἐξ ἀμφοτέρων τῶν δυνάμεων τὰς μικρὰς κατὰ τὸ στόμα τῆς κοιλίας, ὃ δὴ καὶ στόμαχον ὀνομάζουσιν, ἀμβλύνουσι δήξεις, ὡς αἵ γε μείζους τῶν δήξεων εὔδηλον ὅτι γενναιοτέρων χρῄζουσι βοηθημάτων. ἀμείνους δ' ἐν ταῖς σταφίσιν εἰσὶν αἱ λιπαρώτεραί τε καὶ τὸν οἷον φλοιὸν ἔχουσαι λεπτόν. ἔνιοι δὲ καλῶς ποιοῦντες ἐκ τῶν γλυκειῶν τῶν μεγάλων, οἷαίπέρ εἰσιν αἱ Σκυβελίτιδες, πρὶν ἐσθίειν ἐξαιροῦσι τὰ γίγαρτα. χρονισθεῖσαι δ' οὖν καὶ αὗται σκληρὸν ἔχουσι καὶ παχὺ τὸ δέρμα, καὶ χρὴ προδιαβρέχειν αὐτὰς ἐν ὕδατι· καὶ γὰρ καὶ τὸ γίγαρτον ἑτοιμότερον οὕτως ἐξαιρεῖται. ἔμπαλιν δὲ ταύταις ἕτεραί τινές εἰσιν αὐστηραὶ καὶ βραχεῖαι, γίγαρτον ὅλως οὐδὲν ἔχουσαι. γεννῶνται δ' αὗται μὲν ἐν Κιλικίᾳ, τὴν χρόαν ὑπόξανθοι, κατὰ δὲ τὴν Παμφυλίαν αἵ τε Σκυβελίτιδες καὶ αἱ μέλαιναι τὸ χρῶμα. μέγισται μὲν οὖν, ὡς ἔφην, αὗται, σμικρόταται δ' αἱ κιρραὶ ἐν Κιλικίᾳ, γεννωμένων γε καὶ ἄλλων ἐν Κιλικίᾳ γλυκειῶν θ' ἅμα καὶ μελαινῶν σταφίδων μέσων τὸ μέγεθος, | ὥσπερ καὶ κατ' ἄλλα πολλὰ τῶν ἐθνῶν, καὶ μάλιστ' ἐν τῇ Λιβύῃ. κατὰ δὲ τὴν Ἀσίαν ποικίλον εἶδος σταφίδων γεννᾶται· καὶ γὰρ ὑπόξανθοι καὶ μέλαιναι καὶ γλυκεῖαι καὶ ὑπαυστηροὶ γίγνονται. κατὰ μέντοι τὰς ψυχρὰς χώρας οὐδ' αἱ σταφυλαὶ τελέως πεπαίνονται, μήτι γε δὴ τῶν σταφίδων τινές, διόπερ ἐπεμβάλλουσι τοῖς οἴνοις ῥητίνης, ὅπως μὴ ταχέως ὀξυνθῶσιν. ἡ μὲν οὖν κατὰ χρόαν διαφορὰ τῶν σταφίδων ὡς πρὸς τὴν δύναμιν αὐτῶν οὐδὲν συντελεῖ, καθάπερ οὐδ' ἡ κατὰ μέγεθος· ἡ δὲ κατὰ τὴν γευστὴν ποιότητα τὸ σύμπαν δύναται, καὶ ταύτῃ μόνῃ προσέχων τὸν νοῦν, ἐπὶ τίνων τε δεῖ χρῆσθαι καὶ καθ' ὅντινα καιρόν, εὑρήσεις, ὡς προείρηται. τροφὴ δ' ἐκ τῶν σταφίδων ἀναδίδοται τῷ σώματι παραπλησία κατὰ τὴν ποιότητα ταῖς σταφυλαῖς αὐταῖς, γλυκεῖα μὲν ἐκ τῶν γλυκειῶν, αὐστηρὰ δ' ἐκ τῶν αὐστηρῶν, μεικτὴ δ' ἐκ τῶν ἀμφοτέρας ἐχουσῶν τὰς ποιότητας· τῇ δὲ ποσότητι πλείων μὲν ἐκ τῶν λιπαρῶν τε καὶ γλυκειῶν, ἐλάττων δ' ἐκ τῶν αὐστηρῶν τε καὶ ἀλιπῶν. εἰ δὲ τὸν ἴσον ὄγκον σταφίδος λιπαρᾶς γλυκείας ἐκγεγιγαρτισμένης πα|ραβάλλοις ὄγκῳ ῥαγῶν ἴσῳ, τροφιμωτέρας εὑρήσεις τὰς σταφίδας. ἧττον μὲν οὖν ἰσχάδων αἱ τοιαῦται τό θ' ὑπακτικὸν ἔχουσι καὶ τὸ ῥυπτικόν, εὐστομαχώτεραι δ' εἰσὶ τῶν ἰσχάδων.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_ALIM-2.11
TEXT:
Οὐ τοῖς ἀττικίζειν τῇ φωνῇ προῃρημένοις γράφεται ταῦτα (τάχα γὰρ οὐδ' ἀναγνῶναί τις αὐτὰ βουλήσεται καταφρονῶν ὑγιείας σώματος, ὥσπερ καὶ ψυχῆς), ἀλλ' ἰατροῖς μὲν μάλιστα, μὴ πάνυ τι φροντίζουσιν ἀττικίσεων, ἤδη δὲ καὶ τοῖς ἄλλοις, ὅσοι ζῶσιν ὡς λογικὰ ζῷα, πρὸ τιμῆς καὶ δόξης καὶ πλούτου καὶ δυνάμεως πολιτικῆς ἐπιμελεῖσθαι προῃρημένοις σώματος καὶ ψυχῆς. οὗτοι γὰρ εὖ οἶδ' ὅτι τὴν μὲν τῶν Ἀθηναίων φωνὴν οὐδὲν ἡγοῦνται τιμιωτέραν εἶναι φύσει τῆς τῶν ἄλλων ἀνθρώπων, ὑγίειαν δὲ σώματος ἀξιολογώτατόν τι πρᾶγμα εἶναι νομίζουσι τῷ κατὰ φύσιν βιοῦν ἐσπουδακότι. τούτοις οὖν εἰδὼς ὠφελιμώτερον ἔσεσθαι τὸν σαφέστερον λόγον, ἃ γιγνώσκουσιν ὀνόματα γράφω, κἂν μὴ τοῖς παλαιοῖς Ἕλλησιν ᾖ συνήθη. τὸ μὲν οὖν τῶν | μόρων ὄνομα γνώριμόν πώς ἐστι τοῖς πολλοῖς, εἰ καὶ διὰ μηδὲν ἄλλο, διὰ γοῦν τὸ στοματικὸν φάρμακον, ὃ διὰ μόρων ὀνομάζεται, χυλὸν ἔχον αὐτῶν· ἐνίας δὲ τῶν ἐφεξῆς εἰρησομένων ὀπωρῶν ἀγνοοῦσιν οἱ πολλοὶ τῶν ἀνθρώπων ὅπως ὠνόμαζον οἱ πρὸ ἑξακοσίων ἐτῶν Ἀθηναῖοι. τοὺς μὲν γὰρ νῦν ὁρῶσιν οὐδέν τι διαφορώτερον τῶν ἄλλων Ἑλλήνων ἕκαστον τῶν καρπῶν ὀνομάζοντας, ἀλλὰ καὶ τὰ μόρα συκάμινα καλοῦντας οὐδὲν ἧττον ἢ μόρα καὶ τὰ περσικὰ καὶ τὰ κάρυα καὶ τὰ πραικόκκια καὶ τἄλλ' ἁπλῶς, ὡς ἔθος ἐστὶ τοῖς ἄλλοις Ἕλλησιν. οὐδὲ γὰρ οὐδὲ βλαβήσονταί τι, εἰ τὰς παλαιὰς προσηγορίας ἀγνοοῦντες γιγνώσκουσι τὰς δυνάμεις αὐτῶν. ἄμεινον γάρ ἐστιν ἐπίστασθαι τῶν ἐπὶ τὴν διαχώρησιν ὁρμώντων ἐδεσμάτων ὕστερα μὲν χρῆναι τὰ βραδυπόρα λαμβάνειν, ἁπάντων δὲ πρῶτα τὰ διεξερχόμενα μὲν ταχέως, διαφθειρόμενα δ', εἰ χρονίσειεν ἐν τῇ γαστρί, τοῦ τὰς προσηγορίας αὐτῶν ἐγνωκέναι. οὐ μὴν | οὐδ' ἀγνοεῖν μοι δοκοῦσι παντάπασιν οἱ ἄνθρωποι τὴν τάξιν τῶν ἐσθιομένων ἑαυτοῖς· θεώμεθα γοῦν αὐτοὺς ἐπὶ τῶν πλείστων ἐδεσμάτων φυλάττοντας αὐτήν. προλαμβάνουσί γέ τοι ῥαφανίδας ἐλαίας τε καὶ τῆλιν ἐκ γάρου, καὶ μετὰ ταῦτα μαλάχας τε καὶ τεῦτλα καὶ ἄλλα τοιαῦτα λάχανα μετ' ἐλαίου καὶ γάρου. τῶν μὲν γὰρ ὁσημέραι παρασκευαζομένων εἰς ἐδωδὴν αὐτοῖς ἡ μακρὰ πεῖρα διδάσκαλος γίγνεται τῆς δυνάμεως, εἰ καὶ σμικρὸν ἔχοιεν φρενῶν· ὅσα δὲ διὰ χρόνου πλείονος εἰς πεῖραν ἔρχεται, μόνοις τοῖς ἐπιμελέσι παραφυλάττεται καὶ μνημονεύεται. τὰ τοίνυν συκάμινα καθαρᾷ μὲν ἐμπεσόντα γαστρὶ καὶ πρῶτα ληφθέντα διεξέρχεται τάχιστα καὶ τοῖς ἄλλοις σιτίοις ὑφηγεῖται· δεύτερα δ' ἐφ' ἑτέροις ἢ καὶ χυμὸν εὑρόντα μοχθηρὸν ἐν αὐτῇ διαφθείρεται τάχιστα, διαφθορὰν ἀλλόκοτόν τινα καὶ οὐ ῥητὴν ἴσχοντα ταῖς κολοκύνθαις ὁμοίως. ἀβλαβέστατα γὰρ ὄντα ταῦτα τῶν ὡραίων ἐδεσμάτων, ὅταν μὴ πεφθέντα ταχέως ὑποχωρήσῃ, μοχθηρὰν ἴσχει | διαφθορὰν ὁμοίως τοῖς πέποσι, καίτοι κἀκεῖνοι ταχέως ὑπελθόντες οὐδὲν μέγα βλάπτουσι. καιρὸς δὲ τῆς χρήσεως, ὥσπερ τοῖς πέποσιν, οὕτω καὶ τοῖς μόροις, ὅταν αὐχμηρὸν καὶ θερμὸν γένηται τὸ τῆς γαστρὸς σῶμα· τοιοῦτον γάρ πως ἀναγκαῖόν ἐστι τηνικαῦτα καὶ τὸ ἧπαρ εἶναι. τῇ μὲν οὖν κολοκύνθῃ καὶ τῷ σικύῳ τῷ τ' ἤδη πέπονι καὶ πρὶν πεπανθῆναι, σὺν αὐτοῖς δὲ καὶ μηλοπέπονι στυφούσης οὐ μέτεστι ποιότητος· ἐν δὲ τοῖς συκαμίνοις, καὶ μάλισθ' ὅταν ᾖ μὴ πάνυ πέπειρα, σαφής ἐστιν ἡ τοιαύτη ποιότης, ἀωροτέροις δ' οὖσιν ἔτι καὶ ἡ ὀξεῖα. καί τινες αὐτὰ καθαιροῦντες ἀπὸ τῶν δένδρων καὶ ξηραίνοντες ἀποτίθενται φάρμακον αὐτοῖς ἐσόμενον ἀγαθὸν εἰς δυσεντερίας τε καὶ διαῤῥοίας χρονίας ἴασιν. ἀλλ' οὐ πρόκειται νῦν ἡμῖν περὶ φαρμάκων δυνάμεως διεξέρχεσθαι. πάλιν οὖν ὅσα τοῖς συκαμίνοις ὡς τροφῇ δρᾶν ὑπάρχει λέγωμεν. ὅτι μὲν ὑπέρχεται ῥᾳδίως, εἴρηται, τάχα μὲν τῷ τῆς οὐσίας ὑγρῷ τε καὶ ὀλισθηρῷ μόνῳ, τάχα δὲ καί τινος ἐπιμιξίᾳ ποιότητος δριμυτέρας ἐρεθίζειν εἰς ἔκκρισιν | ἱκανῆς, ὡς ἥ γε στύφουσα ποιότης οὐ μόνον οὐδὲν ὀνίνησιν εἰς ὑποχώρησιν, ἀλλὰ καὶ στεγνοῦν πέφυκεν. ὅτι δ' ἐναντίων δυνάμεων οὐκ ὀλίγα μετέσχηκε σώματα, μεμάθηκας ἐν τοῖς Περὶ τῆς τῶν ἁπλῶν φαρμάκων δυνάμεως ὑπομνήμασι. τεκμαίρομαι τοίνυν τὰ μόρα δύναμιν ἔχειν ἐν ἑαυτοῖς τοιαύτην βραχεῖαν, ὁποία τοῖς καθαρτικοῖς ὑπάρχει μεγάλη, δι' ἣν οὐ μόνον ὑποχωρεῖ ῥᾳδίως, ἀλλὰ καὶ διαφθείρεται χρονίσαντα κατὰ τὴν γαστέρα. μὴ διαφθαρέντα δ', ὡς ἔφην, ὑγραίνει μὲν πάντως, ψύχει δ' οὐ πάντως, εἰ μὴ ψυχρὰ ληφθείη. τροφὴν δ' ἐλαχίστην δίδωσι τῷ σώματι παραπλησίως τοῖς πέποσιν, οὐ μὴν ἐμετικόν γέ τι πρόσεστιν αὐτοῖς οὐδὲ κακοστόμαχον, ὡς ἐκείνοις.
