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
CONTEXT_PREV_SOURCE_ID: GAL_SMT-8.24.2
CONTEXT_PREV_TEXT:
ὠκιμοειδές·ἔνιοι δὲ φιλεταίριον ὀνομάζουσιν· ἄχρηστος μὲν ἡ ῥίζα, τὸ δὲ σπέρμα λεπτομεροῦς τε καὶ ξηραντικῆς ἀδήκτως ὑπάρχει δυνάμεως.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_SMT-9.prooimion
TEXT:
Ὅσα μὲν τῶν φυτῶν ἐστι μόρια καὶ καρποὶ καὶ χυλοὶ καὶ ὀποὶ πρόσθεν εἴρηται· νυνὶ δὲ τῶν ὑπολοίπων φαρμάκων ὅσα μεταλλεύεται καὶ ὅσα τῆς γῆς αὐτῆς ἐστιν εἴδη πρόκειται διελθεῖν. ἐφεξῆς δ' αὐτῷ εἰρήσεταὶ τι καὶ περὶ τῶν ἐν τοῖς ζώοις μορίων, οἷς ἐν λόγῳ φαρμάκων χρώμεθα πρὸς τὰς ἰάσεις. κοινὸν δὲ τινα περὶ πάντων αὐτῶν λόγον ἄμεινον εἶναὶ μοι δοκεῖ προτάξαι σαφηνείας τε ἅμα καὶ τοῦ διηρθρωμένως ἀκούειν ἕνεκα τῶν εἰρημένων. ἐὰν γάρ ἕποιτὸ τις τὰ πάντα τοῖς γεγραφόσιν ἤτοι τὰς περὶ τῶν φαρμάκων πραγματείας ἢ τὰς περὶ ὕλης ἢ τὰς περὶ σκευασίας αὐτῶν, ἐν πολλοῖς σφαλήσεται μέγιστα καὶ παρακούσει τῶν ὑπ' ἐμοῦ διωρισμένως λεγομένων. δυοῖν δ' ὄντων κεφαλαίων τοῦ μέλλοντος λεχθήσεσθαι λόγου κοινοῦ, τὸ μὲν ἕτερόν ἐστιν εἰ τῶν αὐτοφυῶν φαρμάκων τὰ κεκαυμένα θερμότερα χρὴ νομίζειν ἢ ψυχρότερα, τὸ δ' ἕτερον ὑπὲρ τῶν στυφόντων φαρμάκων, ὧν ἐν εἴδει πρόσθεν ἐδείχθη τὰ αὐστηρὰ καὶ τὰ στρυφνά. λέλεκται μὲν οὖν ἤδη περὶ τούτων ἐν τῷ τετάρτῳ τῶνδε τῶν βιβλίων, ἀναμνῆσαι δὲ καὶ νῦν ἄμεινον ὡς ἐναντιωτάτη φαίνεται ποιότης καὶ δύναμις εἶναι τοῖς στύφουσι φαρμάκοις πρὸς τὰ δριμέα. στύφει μὲν γάρ ἀκακία καὶ βαλαύστιον, ὑπόκυστίς τε καὶ κύτινοι καὶ κηκὶς καὶ ῥῆον καὶ ῥοῦς, ὀμφάκιόν τε καὶ μέσπιλα, καὶ κρανία καὶ ῥοιᾶς λέμματα καὶ μύρτα. δριμέα δ' ἐστὶν εὐφόρβιον καὶ σκόροδα καὶ κρόμμυα καὶ πράσα καὶ νᾶπυ καὶ πέπερι καὶ γιγγίβερι καὶ σμύρνιον, ὀρίγανόν τε καὶ γλήχων, καὶ καλαμίνθη καὶ θύμος. χρὴ τοίνυν ἀναμνησθῆναι μόνον ἡμᾶς ὁποίαν αἴσθησιν ἔχομεν ἑκάστου τῶν εἰρημένων. ἀκολουθήσει γάρ εὐθέως ἡ διαφορὰ τῆς ποιότητος αὐτῶν, ἣν ἐν τῷ τετάρτῳ λόγῳ διῆλθον ἅμα ταῖς ἄλλαις γευσταῖς ἁπάσαις διαφοραῖς. συνάγει μὲν οὖν καὶ σφίγγει καὶ πιλεῖ τὴν οὐσίαν ἡμῶν τὰ στύφοντα, καὶ διὰ τοῦτο ἐπιτιθέμενα, καθ' ὅ τι ἂν ἐθελήσῃς μέλος ἔξωθεν, εὐθέως ἀποδείκνυσιν αὐτὸ ῥυσόν τε καὶ προσεσταλμένον. ἔμπαλιν δὲ τούτοις τὰ δριμέα κατὰ τοῦ δέρματος ἐπιτιθέμενα θερμαίνει τε σαφῶς αὐτὸ καὶ εἰς ὄγκον συναίρει σὺν ἐρυθρῷ χρώματι, καὶ εἰ χρονίσειεν, ἑλκοῖ. ταῦτα μὲν οὖν ἐναργῶς φαίνεται τέμνοντὰ τε καὶ θερμαίνοντα, καὶ διὰ τοῦθ' ἕλκοντα πρὸς ἑαυτὰ τὸ ἐκ τῶν πλησιαζόντων μορίων αἷμα. τὰ στύφοντα δ' ἀποκρουόμενα τὸ περιεχόμενον ἐν αὐτοῖς τῷ ψύχειν τε καὶ συνάγειν καὶ πιλεῖν πέφυκεν. ἡ δύναμίς τε οὖν ἐναντιωτάτη τοῖς στύφουσίν ἐστι πρὸς τὰ δριμέα, καὶ ἡ κατὰ τὴν γεῦσιν ποιότης οὐδὲν ὅμοιον ἔχουσα. πῶς οὖν ἔνιοι καὶ τὸ πέπερι καὶ τὰ σκόροδα καὶ πάντα τὰ δριμέα στύφειν λέγουσιν οὐδ' ἐπινοῆσαι δυνατόν. εἰ μὲν γάρ ὥσπερ ταῦτα στύφειν, οὕτω καὶ ῥοῦν καὶ βαλαύστιον ὀμφάκιόν τε καὶ μέσπιλον ὅσα τ' ἄλλα τοιαῦτα δριμέα προσηγόρευον, ὑπαλλάττοντες τὸ τῶν Ἑλλήνων ἔθος ἐν τοῖς ὀνόμασιν, ἀγνοεῖν μὲν ἂν αὐτοὺς ὑπολάβοιμεν τὰς φωνὰς τῶν Ἑλλήνων ἅμα τοῖς ὑπ' αὐτῶν σημαινομένοις, οὐ μὴν ἀναισθήτους γε κατὰ τὴν γευστικὴν εἶναι δύναμιν, ἢ τὴν ὀσφρητικήν· ἐπεὶ δ' ἑνὶ προσαγορεύουσιν ὀνόματι πράγματα δύο, καὶ τῇ κατὰ τὴν ὄσφρησιν αἰσθήσει καὶ τῇ κατὰ τὴν γεῦσιν, οἷς τε φαίνονται πράττοντα φύσιν ἐναντιωτάτην ἀλλήλοις ἔχοντα, θαυμάσαι προσήκει τοὺς ἀνθρώπους ἢ ἕνεκεν τῆς ἀναισθησίας ἢ τῆς ἀνοίας ἢ καὶ ἀμφοτέρου ἅμα. παραπλήσιον γάρ τοι ποιοῦσιν τῷ λέγοντι τὴν χιόνα τῷ πυρὶ τὴν αὐτὴν αἴσθησιν ἐργάζεσθαι, καὶ τις ὑπὸ συνήθειας τῆς εἰς τοσοῦτον ἀλλοκότου χρήσεως τῶν ὀνομάτων, ἔφη μοὶ ποτε μηδὲν κωλύειν φάναι τὴν αὐτὴν ἔχειν ποιότητὰ τε καὶ δύναμιν τῷ πυρὶ τὴν χιόνα· καὶ γάρ καὶ ταύτην ὦφθαι πολλάκις ἀποκαίουσαν τοὺς πόδας τῶν δι' αὐτῆς ἐπιπολὺ βαδισάντων· τῶν μὲν δὴ τοιούτων ἀνθρώπων οὐ σμικροῦ χρόνου χρεία τὸν ῥύπον ἀποκαθῆραι τῆς ψυχῆς. ὅσοι δ' οὐχ οὕτως ἠτύχησαν ὡς ἐν ἀμαθίᾳ τελέᾳ διαβιῶναι, προανεγνωκόσι τὸ τέταρτον τῶνδε τῶν ὑπομνημάτων, ἀρκεῖ τούτοις ἀναμνήσεως ἕνεκα τὰ μέχρι δεῦρο λελεγμένα, χάριν τοῦ διηρθρωμένως ἀκούειν τῶν ὀνομάτων ἐφ' ἑκάστου τῶν οἰκείων πραγμάτων, ὡς ἅπαντες Ἕλληνες εἰώθασιν χρῆσθαι. μεταβήσομαι δ' ἐπὶ τὸ δεύτερον ἤδη σκέμμα, μηκέθ' ὑπὲρ ὀνόματός τε καὶ τοῦ κατ' αὐτὸ σημαινομένου γιγνόμενον, ἀλλὰ περὶ φύσεως πράγματος οἱ μὲν γάρ πλεῖστοι νομίζουσι τὰ καυθέντα πάντα ψυχρότερα γίγνεσθαι σφῶν αὐτῶν, ἔνιοι δ' ἔμπαλιν αὐξάνεσθαι τὴν θερμασίαν οἴονται τῶν καυθέντων ἁπάντων, ἁμαρτάνοντες ἑκάτεροι. φανίονται γάρ ἐναργῶς ἔνια μὲν θερμότερα γινόμινα, κατὰ τε τὴν γεῦσιν καὶ τὴν ἁφὴν καὶ τὴν ἐν τῇ χρήσει θεωρουμένην δύναμιν, ὡς ἔμπροσθεν εἶπον ἐπὶ τε τῶν δριμέων καὶ τῶν στυφόντων, ἔνια δ' ἔμπαλιν ἧττον θερμὰ φαινόμενα μετὰ τὸ καυθῆναι· καὶ τοῦτο διαγινώσκομεν σαφῶς τῇ τε αἰσθήσει καὶ τῇ χρήσει. λέγω δὲ χρῆσιν, ὥσπερ ἐπὶ τῶν ἔμπροσθεν εἶπον, ὅταν ἐπιτιθέντα τῷ δέρματι τὰ μὲν ἐρυθρότερὰ τε καὶ θερμότερα αὐτὰ ποιῇ, τὰ δὲ ἄναιμὰ τε καὶ ψυχρὰ, καὶ τὰ μὲν εἰς ὄγκον ἐξαίρῃ, τὰ δὲ προστέλλῃ. τὰ μὲν οὖν δριμέα πολὺ τῆς θερμότητος ἀπόλλυσι καυθέντα, τὰ δὲ μὴ τοιαῦτα προσλαμβάνει, τελέως δὲ ψυχρὸν οὐδὲν τῶν καυθέντων ἐστίν. ἐγκαταλείπεται γάρ αὐτοῖς οἷον ἐμπύρευμὰ τι· καὶ γάρ προσηγόρευεν οὕτως Ἀριστοτέλης αὐτὸ, καὶ τοῦτ' ἔστι τὸ κατὰ τὰς πλύσεις ἀπορρυπτόμενον. ἔστι δὲ τὸ λεπτομερέστατον τῆς τῶν καυθέντων οὐσίας, οὗ συναπελθόντος τῷ ὕδατι τὸ λοιπὸν τοῦ καυθέντος οὐσία γεώδης ἐστί. τὸ μὲν γάρ ὑγρὸν ἅπαν ἡ καῦσις ἐκδαπανᾷ, τὸ δ' ὑπολειπόμενον γεῶδές ἐστιν ἅμα τῷ πρὸς Ἀριστοτέλους ἐμπυρεύματι κληθέντι. τοῦτ' οὖν ὅταν τις ἀφέληται καὶ χωρίσῃ τῇ πλύσει, τὸ μὲν ὕδωρ, ᾧ τὸ φάρμακον ἐπλύθη, θερμὴν δύναμιν ἐπεκτήσατο λεπτομερῆ, τὸ δ' ὑπόλοιπον γίνεται γεῶδες ψυχρὸν, ξηραίνειν ἀδήκτως δυνάμενον. εἴρηται μὲν οὖν μοι καὶ περὶ τούτων ἔμπροσθεν, ἀλλ' οὐδὲν χεῖρον ἀναμνῆσαι καὶ νῦν, ἵνα τις ὑπόγυον ἐσχηκὼς τὴν ἀνάμνησιν αὐτῶν ἕπηται τοῖς λεχθησομένοις ἀκριβέστερον.
