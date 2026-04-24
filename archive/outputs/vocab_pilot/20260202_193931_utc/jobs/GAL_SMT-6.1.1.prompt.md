# Vocab extractor prompt

```prompt

## Prompt (paste into LLM system/user message as-is)

You are an extraction agent for the Ancient Simples Project. Read the input text (Ancient Greek, possibly with TEI tags) and extract candidate terms relevant to ancient pharmacy/science. Output must be strictly valid JSON (no commentary).

### Labels (choose exactly one per term)
- SUBSTANCE
- PART
- PREPARATION
- PROCESS
- TOOL_CONTAINER
- CONDITION
- QUALITY_PROPERTY
- APPLICATION_SITE
- ADMINISTRATION

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

PART (physical parts of a substance; not produced by a procedure)
- Examples: ῥίζα, φύλλον, σπέρμα, φλοιός, ἄνθος (botanical), καρπός, βλαστός
- Rule: answers “which part of the substance?”

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

Disambiguation reminders:
- PART ≠ APPLICATION_SITE (ῥίζα is PART; δέρμα/κεφαλή are APPLICATION_SITE)
- SUBSTANCE ≠ PREPARATION (μανδραγόρα is SUBSTANCE; ἀφέψημα μανδραγόρας is PREPARATION)
- Adjectives are usually QUALITY_PROPERTY unless they clearly denote a CONDITION (e.g., κεφαλαλγής in therapeutic context).

### Galenic degree tracking (mandatory)
Additionally, extract Galenic degree statements for the four primary qualities:
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

Hedges:
- If the degree phrase contains “που” or similar approximation cues, record hedge="που" and lower confidence slightly.

Axis assignment:
- If “θερμ-” terms occur in the same clause/window as the degree phrase, record axis=HOT.
- If “ψυχ-” terms occur, axis=COLD.
- If “ξηρ- / ξηραντ-” terms occur, axis=DRY.
- If “ὑγρ-” terms occur, axis=WET.
If multiple axes are explicitly coordinated (e.g., “θερμὸς … καὶ ξηραντικὸς κατὰ τὴν τρίτην…”), output one record per axis with the same degree.

Applies-to linking:
- If the subject is clearly a SUBSTANCE/PREPARATION (e.g., “ἄγνος… θερμὸς…”) set `applies_to` to that term’s lemma_normalized.
- If unclear, set applies_to.kind="UNSPECIFIED".

Do NOT treat degree ordinals as separate terms.

### Deduplication (hard)
- Deduplicate within the chunk by (label, lemma_normalized). If lemma_normalized is empty, deduplicate by (label, normalized).
- Do not output the same lemma_normalized more than once under the same label.
- Do not output the same lemma_normalized under multiple labels unless unavoidable; if unavoidable, choose the best label and lower confidence.

### Output format (strict JSON only)
{
  "source_id": "<SOURCE_ID>",
  "terms": [
    {
      "label": "SUBSTANCE|PART|PREPARATION|PROCESS|TOOL_CONTAINER|CONDITION|QUALITY_PROPERTY|APPLICATION_SITE|ADMINISTRATION",
      "display": "<GREEK_SURFACE>",
      "normalized": "<NORMALIZED_SURFACE>",
      "lemma_gr": "<GREEK_LEMMA_OR_EMPTY>",
      "lemma_normalized": "<NORMALIZED_LEMMA_OR_EMPTY>",
      "is_multiword": true|false,
      "confidence": 0.0-1.0,
      "lemma_confidence": 0.0-1.0
    }
  ],
  "qualities": [
    {
      "axis": "HOT|COLD|DRY|WET",
      "degree": 1|2|3|4|null,
      "hedge": "none|που|approx",
      "evidence_display": "<short Greek snippet>",
      "evidence_normalized": "<normalized snippet>",
      "applies_to": {
        "kind": "SUBSTANCE|PART|PREPARATION|UNSPECIFIED",
        "lemma_normalized": "<lemma key or empty>"
      },
      "confidence": 0.0-1.0
    }
  ]
}

Sorting:
- Sort `terms` by label, then lemma_normalized (or normalized if lemma missing).
- Sort `qualities` by axis, then degree.

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

## INPUT (authoritative)
Use the following SOURCE_ID and TEXT (ignore any placeholders above).

SOURCE_ID: GAL_SMT-6.1.1
TEXT:
ἀβροτόνου ταύτης τῆς πόας οὔτε τὴν ἰδέαν χρὴ γράφειν ἐπὶ τοσούτοις τε καὶ τοιούτοις ἀνδράσιν οὔτε τὰς κατὰ μέρος ἐνεργείας ὡς ἐκεῖνοι, κᾂν εἰ μὴ διωρισμένως, ἀλλὰ σαφῶς γοῦν ἐδήλωσαν. εἰρήσεται δὲ καὶ ἡμῖν ἐπιπλέον ὑπὲρ αὐτῶν ἐν τῇ περὶ συνθέσεως φαρμάκων πραγματείᾳ καὶ τῇ τῶν εὐπορίστων, ἔστι δ' ὅτε κᾀν τοῖς τῆς θεραπευτικῆς μεθόδου γράμμασιν, ὅταν ἡ χρεία καλῇ. μόνον δὲ, ὅπερ ἐξ ἀρχῆς πρόκειται, τὰς καθόλου δυνάμεις ἁπάντων τῶν φαρμάκων ἐπισκέψασθαι, τοῦτο κᾀπὶ τῶν ἄλλων μὲν ἕπεται, καὶ νῦν δὲ ἤδη ποιητέον αὐτὸ καὶ λεκτέον ὡς θερμόν τέ ἐστι καὶ ξηρὸν τὴν δύναμιν τὸ ἀβρότονον, ἐν τρίτῃ που τάξει καὶ ἀποστάσει μετὰ τὰς συμμετρίας τεταγμένον, διαφορητικήν τὲ τινα καὶ τμητικὴν ἔχον δύναμιν. τῆς αὐτῆς δ' ἐστὶ δυνάμεως καὶ ἡ τρίψις αὐτοῦ εἰληφυῖα, ὥσπερ τὸ σαρκωτικόν τε καὶ δακνῶδες. ὅτι δὲ καὶ ὡς πρὸς τὴν εὔκρατον φύσιν ἡ τοιαύτη τάξις ἐξετάζεται πρόσθεν εἴρηται πολλάκις. ἐξεύρομεν δ' αὐτοῦ τὴν κρᾶσιν οὐχ ἥκιστα μὲν καὶ τῇ γεύσει τεκμηράμενοι, πικρὸν γάρ ἱκανῶς ἐστιν. ὁ δὲ τοιοῦτος χυμὸς ἐδείκνυτο γεώδης μὲν ὢν τὴν οὐσίαν, ὑπὸ θερμότητος δαψιλοῦς λεπτύνεσθαι, ὥστε καὶ θερμαίνειν καὶ ξηραίνειν οὐκ ἀγεννῶς. οὐ μὴν ἀλλὰ καὶ τῇ διωρισμένῃ πείρᾳ, περὶ ἧς ἔμπροσθεν εἴρηται πολλάκις, ἀκριβῶς βασανίσαντες ἐκ τῆς αὐτῆς εὕρομεν τὸ φάρμακον τοῦτο κράσεως. εἴτε γάρ κόψας τὴν κόμην ἅμα τοῖς ἄνθεσιν, ἄχρηστον γάρ αὐτοῦ τὸ λοιπὸν κάρφος, ἐπιπάττοις ἕλκει καθαρῷ, δακνῶδές τε καὶ ἐρεθιστικὸν φαίνεται, εἴτε ἀποβρέξας ἐν ἐλαίῳ καταντλεῖν ἐθελήσαις ἤτοι κεφαλὴν ἢ γαστέρα, θερμαῖνον σφοδρῶς εὑρεθήσεται. καὶ μὲν δὴ καὶ ὅσοι κατὰ περιόδους ἁλίσκονται ῥίγεσιν, εἰ καὶ τούτους ἀνατρίβοις πρὸ τῆς εἰσβολῆς, ἧττον ῥιγῶσιν, ἀλλ' οὐδὲ τὴν αἴσθησιν εὐθὺς ἅμα τῷ προσφέρεσθαι λανθάνει θερμαῖνον. ὅτι δὲ ἕλμινθας ἀναιρεῖν εἰκός ἐστι πικρὸν ὑπάρχον αὐτὸ καὶ πρὸ τῆς πείρας εὔδηλον, εἴ τι μεμνήμεθα τῶν ἐν τῷ τετάρτῳ τῶνδε τῶν ὑπομνημάτων εἰρημένων ὑπὲρ τοῦ πικροῦ χυμοῦ τῆς φύσεως. εἰδήσεις δ' εὐθὺς ὡς καὶ διαφορητικήν τινα καὶ τμητικὴν ἔχει δύναμιν. ἀλλὰ καὶ ὡς μᾶλλον ἀψινθίου τοῦτο ὑπάρχειν ἀναγκαῖον αὐτῷ συλλογίσασθαὶ σοι παρέσται πρῶτον μὲν ἐκ τῆς γεύσεως. ἐλαχίστης γάρ τινος μετέχει στρυφνότητος τὸ ἀβρότονον, ἀψίνθιον δὲ οὐκ ὀλίγης·ἔπειτα δὲ κᾀκ τοῦ κακοστόμαχον εἶναι τὸ ἀβρότονον, ὥσπερ οὖν καὶ τὸ σέριφον, εὐστόμαχον δὲ τὸ ἀψίνθιον. ἐδείχθη γάρ καὶ περὶ τούτων πρόσθεν ὡς τὸ μὲν πικρὸν αὐτὸ καθ' αὑτὸ παντελῶς εἴη κακοστόμαχον, τὸ δὲ αὐστηρὸν ἢ στρυφνὸν ἢ ὅλως στῦφον εὐστόμαχον. ἐπιμιγνυμένων δὲ τῶν ποιοτήτων ἀλλήλαις ἡ σφοδροτέρα ἂν ἐπικρατοίη. ταῦτ' οὖν ἀρκεῖ σοι γινώσκειν ἐν τῇδε τῇ πραγματείᾳ. δειχθήσεται γάρ ἐν τοῖς τῆς θεραπευτικῆς μεθόδου γράμμασιν ὡς ἄν τις τοιούτῳ φαρμάκῳ κάλλιστα χρῷτο. καὶ διὰ τοῦτο μηκέτι ἐπιζήτει ἀκούειν μήθ' ὅτι σὺν ἑφθῷ μήλῳ κυδονίῳ καταπλασθὲν ἢ ἄρτῳ φλεγμονὰς ὀφθαλμῶν ἰᾶται, μήθ' ὅτι διαφορεῖ φύματα σὺν ὠμηλύσει λεῖον ἑψηθέν. οὐδὲ γάρ τούτων οὐδέτερον οὔτε τῶν ἄλλων οὐδὲν τῆς νῦν πραγματείας ἴδιόν ἐστιν, ἀλλὰ τοῖς μὲν ἐμπειρικὴν διδασκαλίαν ποιουμένοις ἐν τοῖς εὐπορίστοις γράφεται φαρμάκοις, ὅσοι δὲ λογικῶς ἀσκῆσαι τὴν τέχνην βούλονται, τῆς θεραπευτικῆς ἐστι χρεία τούτοις μεθόδου. τὰ τε γάρ ἄλλα καὶ βλαβείη τις ἂν μᾶλλον ἢ ὠφεληθείη πρὸς τῆς τοιαύτης ἱστορίας. Ἱπποκράτει μὲν οὖν ἐν ἀφορισμοῖς γράφοντι, ὀδύνας ὀφθαλμῶν ἀκρατοποσίη ἢ λουτρὸν ἢ πυρίη ἢ φλεβοτομίη ἢ φαρμακείη λύει· μὴ μέντοι προστιθέντι, ποίας μὲν οὖν ὀδύνας ἀκρατοποσία, ποίας δὲ λουτρὸν, καὶ τίνας μὲν πυρία, τίνας δὲ φλεβοτομία, τίνας δὲ φαρμακεία, συγχωρήσειεν ἄν τις, οἶμαι, διὰ τρεῖς αἰτίας. καὶ γάρ ἀφοριστικὴν ἐποιεῖτο διδασκαλίαν, ἐν ᾗ διὰ τὸ σύντομον οὕτω λέγεσθαι συγκεχώρηκε τὰ πολλὰ, καὶ πάντα τὰ ἰατικὰ τῶν ὀδυνῶν ἔγραψεν, εἰ καὶ μὴ διωρίσατο πρὸς ὁποίαν ὀδύνην ποῖον αὐτῶν ἁρμόττει, ἢ καὶ πολλαχόθι τῶν ἄλλων συγγραμμάτων ἀφορμὰς ἡμῖν ἔδωκε τῶν ἐν τοῖς οὕτω ῥηθεῖσι διορισμῶν. ὅσοι δὲ μήτ' ἐν ἑτέροις βιβλίοις ἔγραψαν ὑπὲρ τῶν τοιούτων ἀφορισμῶν μήτε ἐν διεξοδικῇ τε καὶ μακρᾷ πραγματείᾳ, γράφουσιν ἀφοριστικῶς τε καὶ βραχέως, εἴτε τὸ πρὸς τούτοις ἓν ἐκ πολλῶν δηλοῦσιν, εἰς πλείω δὲ βλάπτουσιν ἡμᾶς ἢ ὠφελοῦσι. πολλῶν γάρ οὐσῶν διαφορῶν ἐν ταῖς ὀφθαλμίαις, καὶ μιᾶς μὲν ἐξ αὐτῶν χρῃζούσης τοῦ προειρημένου καταπλάσματος, τῶν δ' ἄλλων βλαπτομένων, ὁ χρώμενος ἐπὶ πασῶν ἀδιορίστως πολὺ πλείους βλάψει ἢ ὠφελήσει. κατὰ τοῦτον οὖν τὸν τρόπον οὐ περὶ ἀβροτόνου μόνον, ἀλλὰ καὶ περὶ τῶν ἄλλων ἁπάντων γραπτέον ἡμῖν ἐστι, τὰς μὲν κατὰ τὸ θερμαίνειν καὶ ψύχειν ἢ ὑγραίνειν ἢ ξηραίνειν δυνάμεις ἐξ ὧν πολλάκις εἴρηκα μεθόδων εὑρίσκουσιν, ὅσα δὲ κατὰ τὴν ἰδιότητα τῆς ὅλης οὐσίας ἀποτελοῦνται τῇ πείρᾳ μόνῃ. δέδεικται καὶ περὶ τῶν τοιούτων ὡς δηλητήριοὶ τὲ εἰσι καὶ δηλητηρίων ἀλεξητήριοι καὶ καθαρτικοί. τούτων γάρ οὐχ οἷόν τε λογικὴν ποιήσασθαι τὴν εὕρεσιν, ἀλλ' ἢ μόνον ὑπόνοιὰν τινα πιθανὴν ἔστιν εὑρεῖν ἐπὶ τινων· οὐ γάρ δὴ ἐπὶ πάντων γε, καθάπερ καὶ αὐτὸ τοῦτο δεδήλωται διὰ τῶν ἔμπροσθεν. ἀλλὰ περὶ μὲν τῶν οὕτως εὑρισκομένων δυνάμεων ἰδίᾳ ποιήσομαι τὸν λόγον ἐν τοῖς ἐφεξῆς, ἐπειδὰν πρότερον ὑπὲρ τῶν κατὰ τὸ θερμαίνειν καὶ ψύχειν, ὑγραίνειν τε καὶ ξηραίνειν, καὶ ὅσα ταύταις ἕπονται διέλθω καθ' ἕκαστον εἶδος φαρμάκου. τοσόνδε μέντοι προσθεὶς ἔτι περὶ ἀβροτόνου καταπαύσω τὸν λόγον, ὡς ὁ θαυμασιώτατος Πάμφιλος, καίτοι ταύτην πρώτην πόαν γράφων καὶ τάχ' ἂν εἰ μηδενὸς τῶν ἐφεξῆς, ἀλλὰ ταύτης γοῦν ἐθελήσας αὐτόπτης γενέσθαι, ὅμως ἔσφαλται μέγιστα, νομίζων ὑπὸ Ῥωμαίων σαντόνικον ὀνομάζεσθαι τὴν βοτάνην. διαφέρει γάρ ἀβρότονον σαντονίκου, καθότι καὶ Διοσκουρίδης ἔγραψεν ἐν τῷ τρίτῳ περὶ ὕλης ἀκριβέστατα, καὶ πάντες ἴσασι τοῦτὸ γε ἰατροὶ καὶ ῥωποπῶλαι. τοῦ μὲν γάρ ἀβροτόνου δύο ἐστὶν εἴδη, τὸ μὲν ἄρρεν, τὸ δὲ θῆλυ νομιζόμενον, ὡς καὶ τοῦτο διώρισται παρὰ τῷ Διοσκουρίδῃ τε καὶ τῷ Παμφίλῳ καὶ ἄλλοις μυρίοις. ἕτερον δὲ ἐστιν αὐτοῦ τὸ ἀψίνθιον, οὗ πάλιν εἴδη χρὴ τίθεσθαι καὶ αὐτὰ τριττὰ, ὧν τὸ μὲν τῷ γένει ὁμωνύμως προσαγορεύονται ἀψίνθιον, ὁποῖον μάλιστὰ ἐστι τὸ Ποντικὸν, τὸ δὲ σέριφον, τὸ δὲ σαντόνικον. εἰ δ' ἄλλο μὲν ἀψίνθιον, ἄλλο δὲ σέριφον, ἄλλο δὲ σαντόνικον λέγοι, οὐδὲν εἰς τὰ παρόντα διαφέρει. οὐδὲ γάρ ὄνομα διαιρήσοντες ἥκομεν, ἀλλ' ὑπὲρ αὐτῶν τῶν πραγμάτων σπουδάζομεν. ἐπεὶ τοίνυν καὶ ταῦτα καὶ ταῖς ἰδέαις καὶ ταῖς γεύσεσι καὶ ταῖς δυνάμεσιν ἕτερα σαφῶς ἀλλήλων ἐστὶν, ὀνομαζέτω μὲν, εἰ βούλοιτὸ τις, ἅπαντα διὰ μιᾶς προσηγορίας, ἐκδιδασκέτω δὲ ἀκριβῶς τὰς δυνάμεις. ἡμεῖς οὖν τὰς μὲν ἰδέας αὐτάρκως ἔφαμεν εἰρῆσθαι Διοσκουρίδῃ τε καὶ ἄλλοις οὐκ ὀλίγοις, ὥστ' οὐ χρὴ γράφειν αὖθις ὅσα τοῖς πρόσθεν ὀρθῶς εἴρηται. εἴ τι δ' ἐν ταῖς τούτου δυνάμεσιν ἀδιόριστον ἐκεῖνοι παρέλιπον, οὗ δὴ χάριν ἐπὶ τήνδε τὴν ἔξοδον ἀφικόμην, ἐγὼ προσθεῖναι πειράσομαι. τὸ μὲν ἀψίνθιον ἧττόν ἐστιν τῶν εἰρημένων θερμὸν, ὡς ἂν πλείστης μετέχων τῆς στύψεως. εἰ δὲ καὶ τοῦτο λεπτομερὲς ἧττον ἐκείνων, καὶ λεπτυντικὸν δὴ κατὰ τὸν αὐτὸν τρόπον ἧττον ἐκείνων, οὐ μὴν ἧττόν γε ξηραντικόν. τῶν δ' ἄλλων τὸ μὲν σαντόνικον ἀπὸ Σαντονείας χώρας, ἐν ᾗ φύεται, τὴν προσηγορίαν ἔχον ἐγγυτάτω τὴν δύναμίν ἐστι τοῦ σερίφου, βραχεῖ τινι λειπόμενον ἐν τῷ λεπτύνειν τε καὶ θερμαίνειν καὶ ξηραίνειν. αὐτὸ δὲ τὸ σέριφον ἧττον μὲν θερμὸν τοῦ ἀβροτόνου, θερμότερον δὲ ἀψινθίου, κακοστόμαχον δὲ ἱκανῶς καὶ ὡς ἂν ἁλμυρίδα τινὰ σὺν πικρότητι ἀποφαῖνον, ἔτι τε τῆς στρυφνότητος ὀλίγον μετέχον. οὕτω δὲ καὶ ἀβρότονον καὶ σαντόνικον ἱκανῶς ἐστι κακοστόμαχον. μόνον γάρ ἐν αὐτοῖς τὸ ἀψίνθιον καὶ μάλιστα τὸ Ποντικὸν εὐστόμαχόν ἐστιν ὅτι πλείστης μετέχει στύψεως. ἀβρότονον δὲ κεκαυμένον θερμὸν καὶ ξηρόν ἐστι τὴν δύναμιν, ἔτι μᾶλλον κολοκύνθης ξηρᾶς κεκαυμένης καὶ ἀνήθου ῥίζης. ἐκεῖνα γάρ ἕλκεσιν ὑγροῖς τε ἅμα καὶ χωρὶς φλεγμονῆς τετυλωμένοις ἁρμόττει, καὶ διὰ τοῦτο μάλιστα τοῖς ἐπὶ πόσθαις αἰδοίου συμπεφωνηκέναι δοκεῖ. τοῦ δὲ ἀβροτόνου ἡ τέφρα δακνώδης ἅπασιν ἕλκεσιν ὑπάρχει. καὶ διὰ τοῦτο καὶ πρὸς ἀλωπεκίας ἁρμόττει σὺν ἐλαίῳ λεπτομερεῖ, κικίνῳ δηλονότι ἢ ῥαφανίνῳ ἢ Σικυωνίῳ ἢ παλαιῷ, καὶ μάλιστα τῷ Σαβίνῳ. καὶ γένεια δὲ βραδέως ἀνιόντα προκαλεῖται μετὰ τινος τῶν εἰρημένων ἐλαίων ὅτου δὴ, καὶ οὐδὲν δ' ἧττον ἐκείνων σχινίνῳ δευόμενον. ἀραιωτικὸν γάρ ἐστι πρὸς τῷ λεπτομερὲς εἶναι καὶ δακνῶδες καὶ θερμὸν, ἃς δὴ καὶ μάλιστα χρὴ γινώσκειν τὰς δυνάμεις αὐτοῦ καὶ μηδὲν ἔτι τῶν κατὰ μέρος ἐν τῇδε τῇ πραγμανείᾳ δεῖσθαι.
