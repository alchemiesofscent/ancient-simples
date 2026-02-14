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
CONTEXT_PREV_SOURCE_ID: GAL_ALIM-2.34
CONTEXT_PREV_TEXT:
Θαμνῶδες φυτόν ἐστιν ἡ κάππαρις ἐν Κύπρῳ πλείστη φυομένη. δύναμις δ' αὐτῆς ἐστι λεπτομερὴς ἱκανῶς καὶ διὰ τοῦτο τροφὴν ἐλαχίστην ἀναδίδωσιν εἰς τὸ τῶν ἐσθιόντων αὐτὴν σῶμα, καθάπερ καὶ τἄλλα πάνθ' ὅσα λεπτομερῆ. χρώμεθα δ' ὡς φαρμάκῳ μᾶλλον ἢ ὡς τροφῇ τῷ καρπῷ τοῦ φυτοῦ. κομίζεται γὰρ ὡς ἡμᾶς ἁλσὶ διαπασθεῖσα διὰ τὸ σήπεσθαι μόνην ἀποτιθεμένην. εὔδηλον οὖν, ὅτι χλωρὰ μὲν ἔτι πρὶν ταριχευθῆναι πλέον ἔχει τροφῆς. ἐκ δὲ τῆς ταριχείας ἀπόλλυσι πάμπολυ | καὶ γίγνεται χωρὶς μὲν τοῦ τοὺς ἅλας ἀποπλυθῆναι παντάπασιν ἄτροφος, ὑπακτικὴ δὲ γαστρός· ἀποπλυθεῖσα δὲ καὶ διαβραχεῖσα μέχρι τοῦ τελέως ἀποθέσθαι τὴν ἐκ τῶν ἁλῶν δύναμιν, ὡς ἔδεσμα μὲν ὀλιγοτροφώτατόν ἐστιν, ὡς ὄψον δὲ καὶ φάρμακον ἐπιτήδειον ἐπεγεῖραι καταπεπτωκυῖαν ὄρεξιν ἀπορρύψαι τε καὶ ὑπαγαγεῖν τὸ κατὰ τὴν γαστέρα φλέγμα καὶ τὰς κατὰ σπλῆνα καὶ ἧπαρ ἐμφράξεις ἐκκαθῆραι. χρῆσθαι δ' εἰς ταῦτα προσῆκεν αὐτῇ δι' ὀξυμέλιτος ἢ ὀξελαίου πρὸ τῶν ἄλλων ἁπάντων σιτίων. τοὺς δ' ἁπαλοὺς ἀκρέμονας καὶ τούτου τοῦ φυτοῦ παραπλησίως ἐσθίουσι τοῖς τῆς τερμίνθου καὶ χλωροὺς ἔτι καὶ συντιθέντες ὡς ἐκείνους ἐν ὀξάλμῃ τε καὶ ὄξει.


---

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_ALIM-2.40
TEXT:
Προὔκριναν πολλοὶ τῶν ἰατρῶν τὸ λάχανον τοῦτο τῶν ἄλλων ἁπάντων, ὥσπερ τὰ σῦκα τῆς ὀπώρας· εὐχυμότερον γάρ ἐστιν αὐτῶν. ὃ δὲ μέμφονταί τινες αὐτοῦ, μέγιστον ἔπαινον ἔχει. καὶ εἴπερ ὄντως ἀληθὲς ἦν, οὐ μόνον λαχάνων, ἀλλὰ καὶ τῶν εὐχυμοτάτων τε καὶ τροφιμωτάτων ἐδεσμάτων οὐδενὸς ἂν ἦν δεύ|τερον· αἷμα γὰρ αὐτήν φασι γεννᾶν. ἔνιοι δ' οὐχ ἁπλῶς αἷμα λέγουσιν, ἀλλὰ καὶ τὸ πολὺ προστιθέασι, πολὺ γεννᾶν αἷμα φάσκοντες τὴν θριδακίνην. ἀλλ' οὗτοι, κἂν εἰ φρονιμώτερον ἐγκαλοῦσι, μείζονά γε ψεύδονται τῶν ἑτέρων· καίτοι καὶ αὐτὸ τὸ πολὺ γεννᾶν αἷμα μόνον λεγόμενον οὐκ ἄν τις εὐλόγως μέμψαιτο. δῆλον γάρ, ὅτι τὸ τοιοῦτον πάντων ἂν εἴη τῶν ἐδεσμάτων εὐχυμότατον, εἴ γε πλεῖστον μὲν αἷμα, τῶν δ' ἄλλων χυμῶν οὐδένα γεννᾶν πέφυκεν. εἰ δὲ πλῆθος μὲν ἀθροίζεσθαι φήσουσιν ἐκ τῆς θριδακίνης καὶ κατὰ τοῦτο μέμφοιντο, ῥᾷστον ἐπανορθώσασθαι τὸ ἔγκλημα, δυναμένων γε δὴ τῶν ἐσθιόντων αὐτὰς διαπονεῖσθαι μὲν πλείω, προσφέρεσθαι δ' ὀλίγας. ταῦτα μὲν οὖν ἀπόχρη λελέχθαι πρὸς τοὺς ψέγοντας οὐκ ὀρθῶς τὸ λάχανον τοῦτο. γιγνώσκειν δὲ χρή, πάντων τῶν λαχάνων ὀλίγιστόν τε καὶ κακόχυμον αἷμα γεννώντων, ἐκ τῆς θριδακίνης οὐ πολὺ μὲν οὐδὲ κακόχυμον, οὐ μὴν εὔχυμόν γε τελέως αἷμα γίγνεσθαι. ἐσθίουσι δ' αὐτὴν ὡς τὰ πολλὰ μὲν ὠμήν· ὅταν δ' εἰς σπέρματος γένεσιν ἐξορμᾶν ὑπάρξη|ται θέρους ὥρᾳ, προεψήσαντες ἐν ὕδατι γλυκεῖ προσφέρονται δι' ἐλαίου καὶ γάρου καὶ ὄξους ἢ διά τινος τῶν ὑποτριμμάτων, καὶ μάλισθ' ὅσα διὰ τυροῦ σκευάζεται. χρῶνται δ' αὐτῇ καὶ πρὶν εἰς καυλὸν ἐξορμῆσαι πολλοὶ δι' ὕδατος ἕψοντες, ὥσπερ κἀγὼ νῦν ἠρξάμην, ἀφ' οὗ τῶν ὀδόντων ἔχω φαύλως. εἰδὼς γάρ τις τῶν ἑταίρων ἐν ἔθει μὲν ὂν ἐκ πολλοῦ μοι τὸ λάχανον, ἐπίπονον δὲ νῦν ἔχον τὴν μάσησιν, εἰσηγήσατο τὴν ἕψησιν. ἐχρώμην δὲ θριδακίναις ἐν νεότητι μὲν ἐκχολουμένης μοι συνεχῶς τῆς ἄνω γαστρὸς ἐμψύξεως ἕνεκεν, ὁπότε δ' εἰς τὴν καθεστηκυῖαν ἡλικίαν ἦλθον, ἄκος ἦν μοι μόνον τὸ λάχανον τοῦτο τῆς ἀγρυπνίας, ἔμπαλιν ἢ ὡς ὅτε μειράκιον ἦν ἐσπουδακότι περὶ τὸν ὕπνον. εἰθισμένος τε γὰρ ἑκουσίως ἀγρυπνεῖν ἐπὶ νεότητος ἅμα τε καὶ τῆς τῶν παρακμαζόντων ἡλικίας ἀγρυπνητικῆς οὔσης, ἀκουσίως ἀγρυπνῶν ἐδυςφόρουν, καί μοι μόνον ἀλεξιφάρμακον ἀγρυπνίας ἦν ἑσπέρας ἐσθιομένη θριδακίνη. λέγω δ' οὐκ ἄλλο τι θριδακίνην ἢ ὃ πάντες οἱ νῦν ἄνθρωποι καλοῦσι θρίδακα, ἐπεί τοι | παρ' ἡμῖν ἕτερόν τι λάχανον ἄγριον ὀνομάζεται θριδακίνη, πάμπολυ παρά τε τὰς ὁδοὺς φυόμενον ἐπί τε τοῖς ὑψηλοῖς τῶν τάφρων ἔτι τε κατὰ τὰς καλουμένας λιβάδας καὶ πολλὰς τῶν ἀσπόρων χωρῶν. ἔστι δὲ μικρὸν ἐκεῖνο τὸ λάχανον, οἷόνπερ ἡ ἄρτι φυομένη θρῖδαξ ἡ κηπευομένη, καί τι βραχὺ πικρότητος ἐμφαίνει, καὶ μᾶλλον ἔτι κατὰ τὴν αὔξησιν, ἐκκαυλῆσαν δὲ καὶ πάνυ σαφῆ τὸν πικρὸν ἔχει χυμόν. ὅμοιον δέ τι λάχανον ἄγριον τῇ θριδακίνῃ τῇδε καὶ ἣν ὀνομάζουσι χονδρίλην ἐστὶ καὶ θᾶττον εἰς καυλὸν ἐξορμᾷ, πικρότητα σαφεστέραν ἔχον καί τινα γλίσχρον τε καὶ λευκὸν ὀπόν, οἷόσπερ ὁ τῶν τιθυμάλλων ἐστίν, ἀλλ' οὐ δριμὺν ὡς ἐκεῖνος, ᾧ πρὸς ἀνακόλλησιν ἐνίοτε χρώμεθα τῶν ἐν τοῖς βλεφάροις τριχῶν. ταῦτα μὲν οὖν ἄγρια καλεῖται λάχανα πρὸς διορισμὸν τῶν κηπευομένων, εἴρηται δὲ μικρὸν ἔμπροσθεν ὑπὲρ αὐτῶν κοινῇ. περὶ δὲ τῆς κηπευομένης θριδακίνης τῆς ἅπασι συνήθως ἐσθιομένης τε καὶ καλουμένης θρίδακος ἐν κεφαλαίῳ πάλιν ἀναλαβὼν ἐρῶ μνήμης ἕνεκεν, ὡς ὑγρὸν μὲν ἔχει καὶ ψυχρὸν τὸν χυλόν, οὐ | μὴν κακόχυμός γ' ἐστί. διὰ τοῦτ' οὖν οὐδ' ἀπεπτεῖται τοῖς ἄλλοις λαχάνοις ὁμοίως οὐδ' ἐπέχει τὴν διαχώρησιν, ὥσπερ οὐδὲ προτρέπει. καὶ τοῦτ' εἰκότως αὐτῇ συμβέβηκε μήτ' αὐστηρὸν ἐχούσῃ τι μήτε στρυφνόν, ὑφ' ὧν ἴσχεται τοὐπίπαν ἡ γαστήρ, ὥσπερ ὑπὸ τῶν ἁλυκῶν τε καὶ δριμέων καὶ ὅλως ῥυπτικὸν ἐχόντων τι προτρέπεται πρὸς ἔκκρισιν, ὧν οὐδ' αὐτῶν ὑπάρχει τι τῇ θριδακίνῃ.
