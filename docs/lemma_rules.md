# Ancient Pharmacy Vocabulary Working Document (v1.0)

## 1. Purpose

This document defines a controlled vocabulary and extraction protocol for ancient pharmacy/science terms from Greek texts (often TEI). It specifies:

- what counts as a term,
- how terms are normalized and lemmatized,
- how terms are classified into a closed label set,
- how multiword expressions and composite notions (e.g., “mandrake root”) are represented,
- how “where applied” (application sites) is captured.

This is a working standard. Use it to guide human review and to constrain LLM extraction.

---

## 2. Core principles

1) **Separation of concerns**
- Vocabulary terms (what things are) are separate from relations (how things connect).
- Terms are controlled lists; relations are tables linking terms based on evidence.

2) **Evidence-first**
- No term or relation is “true” because it seems plausible. It enters the canonical vocabulary only because it appears in text and passes review.

3) **Stable keys**
- Every term must have:
  - a representative surface form (display),
  - a normalized form (matching key),
  - a lemma candidate (dedup key; treated as fallible).

4) **Closed label set**
- Every extracted term must fit exactly one label from the label set below.
- If it does not fit, exclude it.

---

## 3. Label set (authoritative)

The label set is operational: it exists to keep extraction consistent and reviewable.

### 3.1 SUBSTANCE
Definition: base medicinal materials, ingredients, and vehicles.

Examples (from Galenic/Dioscoridean style):
- μανδραγόρα (mandrake)
- ἑλλέβορος (hellebore)
- πέπερι (pepper)
- ὕδωρ (water)
- ὄξος (vinegar)
- ἅλμη (brine)
- θάλαττα (sea/seawater)
- ψιμμύθιον (white lead)
- καστορίον (castoreum)

Rule of thumb:
- If it can function as a headword in a materia medica list, it is SUBSTANCE.

Common edge cases:
- ἔλαιον: treat as SUBSTANCE in v1 (vehicle/material in medical use). Track “produced from olives” later as a relation if needed.
- οἶνος: SUBSTANCE when used as vehicle/ingredient.

---

### 3.2 PART
Definition: physical parts of a substance; not produced by a procedure.

Examples:
- ῥίζα (root)
- φύλλον (leaf)
- σπέρμα (seed)
- φλοιός (bark/peel)
- ἄνθος (flower, botanical sense)
- καρπός (fruit)

Example phrases (compositional):
- μανδραγόρου ῥίζα = SUBSTANCE(μανδραγόρα) + PART(ῥίζα)
- μανδραγόρου ῥίζης φλοιός often implies nested parts (root-bark); see 6.3.

Rule of thumb:
- Answers “which part of the substance?”

---

### 3.3 PREPARATION
Definition: products/forms produced by one or more procedures (outputs of processes).

Examples:
- ἀφέψημα (decoction)
- χυμός (juice/extract)
- τέφρα / σποδός (ash)
- κηρωτή (cerate)
- κατάπλασμα (poultice)
- ἔγχυμα / ἔκχυμα (infusion/extract; usage varies)

Rule of thumb:
- If you can ask “how was this made?” and the answer is a procedure sequence, it is PREPARATION.

Notes:
- “Preparation” is not “a part.” It is an output. It can have inputs, steps, and tools.

---

### 3.4 PROCESS
Definition: deliberate actions performed by practitioners on substances, preparations, bodies, or sites.

Examples (verbs or verbal nouns):
- μίγνυμι (mix)
- τήκω (melt)
- ἕψω (boil)
- διηθέω (filter/strain)
- καταθραύω (crush/grind)
- λειόω (grind smooth)
- ἐπιτίθημι (apply/place on)
- ἐπαλείφω (anoint)
- βρέχω (soak)
- καταντλέω (pour over)

Rule of thumb:
- What is being done (method action), not what is being used.

Exclusions:
- Generic discourse verbs (εἰμί, γίγνομαι, λέγω, δοκέω) are excluded unless part of fixed technical expressions.

---

### 3.5 TOOL_CONTAINER
Definition: tools, vessels, implements, cloths, and containers used in preparation/application.

Examples:
- ἀγγεῖον (vessel)
- κεράμιον (earthenware vessel)
- θυεία (small dish/bowl)
- σπόγγος (sponge)
- ἔριον (wool)
- (context-dependent) ὑφάσματα (cloths)

Rule of thumb:
- Neither a material nor an action, but used to perform an action.

---

### 3.6 CONDITION
Definition: diseases, pathological states, clinical conditions, or treated states.

Examples:
- πυρετός (fever)
- φλεγμονή (inflammation)
- ἕλκος (ulcer)
- ἐρυσίπελας (erysipelas)
- ἄνθραξ (carbuncle; also “coal” elsewhere—use context)
- καῦμα (burn/heat injury)
- οἴδημα (swelling)

Rule of thumb:
- Something being treated/assessed medically.

---

### 3.7 QUALITY_PROPERTY
Definition: pharmacodynamic, sensory, or theoretical properties used to classify δράσεις/δυνάμεις.

Examples:
- θερμός / θερμότης (hot/heat)
- ψυχρός / ψυχρότης (cold/coldness)
- ξηρός / ξηρότης (dry/dryness)
- ὑγρός / ὑγρότης (moist/moisture)
- δύναμις (efficacy/power)
- κρᾶσις (mixture/temperament)
- λεπτομερής / παχυμερής (fine-/thick-parted; particle constitution)

Rule of thumb:
- Answers “how does it act / what is its quality?” rather than “what is it?”

---

### 3.8 APPLICATION_SITE
Definition: bodily target sites/regions where a substance/preparation is applied or where it acts as a target.

Examples:
- δέρμα (skin)
- γλῶττα (tongue)
- γαστήρ (stomach)
- ὑποχόνδρια (hypochondria)
- κνῆμαι (shins/legs)
- στόμα (mouth; only when bodily)
- φλέβες (veins) / ἀρτηρίαι (arteries) / πόροι (pores) when used as bodily targets

Contextual examples:
- ἐπὶ τοῦ δέρματος (onto the skin)
- κατὰ τῶν ὑποχονδρίων (over the hypochondria)
- εἰς τὴν γαστέρα (into the stomach)

Rule of thumb:
- “Where is it applied?” or “where in the body is it directed?”

Critical disambiguation:
- PART is for plants/animals/minerals; APPLICATION_SITE is for bodies.
- If ambiguous (στόμα), label as APPLICATION_SITE only when bodily context is clear.

---

## 4. Normalization and lemma requirements

### 4.1 Required fields per term
Every term record must carry:

- `display`: representative surface form as it appears in the text
- `normalized`: lowercase + strip accents/breathings only; preserve iota subscript; keep Greek script (no transliteration)
- `lemma_gr`: best lemma candidate (polytonic Greek), dictionary form
- `lemma_normalized`: normalization applied to lemma_gr

### 4.2 Lemma conventions
- Nouns/adjectives: nominative singular (appropriate gender; neuter when neuter)
- Verbs (PROCESS): use **present infinitive** when possible (e.g., θερμαίνειν, ψύχειν, μίγνυμι is not infinitive; preferred infinitive is μιγνύναι, but if uncertain, use dictionary headword μίγνυμι and mark lemma_confidence lower)

If lemmatization is uncertain, keep the surface form and set lemma_confidence < 0.75.

### 4.3 Deduplication keys
Within a chunk:
1) Deduplicate by `(label, lemma_normalized)` if lemma present
2) Else deduplicate by `(label, normalized)`

Across the corpus:
- canonical term IDs must be stable and created after review.

---

## 5. Multiword terms (MWEs)

Multiword expressions are common and often essential.

### 5.1 When to capture an MWE
Capture an MWE if:
- it is a stable technical expression (e.g., λευκὸς ἑλλέβορος),
- it disambiguates a substance (e.g., “Cnidian berry” style designations),
- it encodes an application-site phrase that matters (e.g., “κατὰ τῶν ὑποχονδρίων” as site phrase).

### 5.2 How to store MWEs
Store both:
- the phrase as a term candidate (with normalized surface),
- its internal head term(s) as separate terms.

Example:
- “λευκὸς ἑλλέβορος”
  - MWE term (SUBSTANCE, phrase)
  - headword term: ἑλλέβορος (SUBSTANCE)
  - modifier term: λευκός is not necessarily a standalone vocab term; treat as part of MWE unless it functions as QUALITY_PROPERTY in context.

### 5.3 Nested parts
Example: μανδραγόρου ῥίζης φλοιός (bark of the root of mandrake)
Minimum v1 representation:
- SUBSTANCE: μανδραγόρα
- PART: ῥίζα
- PART: φλοιός
Evidence: store occurrence with surface phrase and mark `notes="nested: root-bark"`.

If you later want strict nesting:
- add an optional `part_parent_id` or a `nested_part_of` relation.

---

## 6. Relations (tables) we will maintain

Terms alone do not express “mandrake root,” “applied to skin,” or “decoction produced by boiling.” Relations do.

### 6.1 Substance–Part relation (composition)
Purpose: represent “mandrake has part root” and allow queries like “all root-uses”.

Table: `substance_parts`
- `substance_id`
- `part_id`
- `relation_type` (start with one value: `has_part`)

Evidence table (text-grounded): `substance_part_occurrences`
- `work_id`, `ref`, `segment_id`
- `substance_id`, `part_id`
- `surface`, `context`

### 6.2 Preparation as output of procedures (tracking outputs)
Purpose: treat preparations as outputs, so they can be linked to processes and inputs.

Option A (recommended minimal, review-friendly):
- `prep_events`: `prep_event_id`, `prep_type_id`, `work_id`, `ref`, `segment_id`, `context`
- `prep_inputs`: `prep_event_id`, `input_kind` (SUBSTANCE|SUBSTANCE_PART|PREPARATION), `input_id`
- `prep_steps`: `prep_event_id`, `step_i`, `process_id`, `tool_id?`, `notes`
- `prep_outputs`: `prep_event_id`, `prep_type_id` (often same as event type), `notes`

This supports:
- “Which processes produce cerates?”
- “Which inputs go into decoctions?”

### 6.3 Application relation (where applied)
Purpose: capture the applied thing + site, optionally with process.

Table: `applications`
- `work_id`, `ref`, `segment_id`
- `applied_kind` (SUBSTANCE|PREPARATION)
- `applied_id`
- `site_id` (APPLICATION_SITE)
- `process_id` (optional but preferred; e.g., ἐπιτίθημι / ἐπαλείφω / καταντλέω)
- `surface`, `context`

This supports:
- “Where is vinegar applied?”
- “Which substances are applied to skin vs stomach?”
- “Topical vs internal administration” (derive from site).

---

## 7. Extraction rules (for LLMs and humans)

### 7.1 What to extract
Extract terms that:
- are materials, parts, preparations, processes, tools/containers, conditions, qualities, or application sites,
- are relevant to pharmacy/science (broadly construed in medical texts).

### 7.2 What to exclude
Exclude:
- function words,
- most generic verbs and discourse verbs,
- personal names and places (unless part of a pharmaceutical designation),
- purely logical/metadiscursive vocabulary unless it is a technical term in the theory of qualities (e.g., κρᾶσις, δύναμις are included).

### 7.3 How to recognize APPLICATION_SITE reliably
Only classify as APPLICATION_SITE when:
- it occurs in a targeting frame (e.g., ἐπί/κατά/εἰς/πρός + bodily noun),
- or it is clearly a body region in therapeutic context.

Avoid turning the vocabulary into a general anatomy list.

---

## 8. Worked examples

### 8.1 “μανδραγόρου ῥίζης φλοιός … ψύχειν πέφυκε”
Extract:
- SUBSTANCE: μανδραγόρα
- PART: ῥίζα
- PART: φλοιός
- QUALITY_PROPERTY: ψυχρός / ψύχειν (if nominal/adjectival use; if verb used as pharmacodynamic predicate, keep QUALITY_PROPERTY only if expressed as quality term; otherwise keep PROCESS only if used as procedure—usually it is pharmacodynamic, so QUALITY_PROPERTY is acceptable with note)
Evidence:
- substance_part_occurrences:
  - (μανδραγόρα, ῥίζα)
  - (μανδραγόρα, φλοιός) with nested note

### 8.2 “σπόγγον ὄξει βρέξαντες ἐπιθήσομεν …”
Extract:
- TOOL_CONTAINER: σπόγγος
- SUBSTANCE: ὄξος
- PROCESS: βρέχω (soak)
- PROCESS: ἐπιτίθημι (apply)
- APPLICATION_SITE: depends on what follows (e.g., “ὁτῳδήποτε μορίῳ” is too generic; exclude unless named site appears)

Relation:
- applications:
  - applied=ὄξος, site=(if named), process=ἐπιτίθημι, with context

### 8.3 “κηρωτὴν … ἐπιθείης θερμῷ τινὶ παθήματι”
Extract:
- PREPARATION: κηρωτή (cerate)
- PROCESS: ἐπιτίθημι (apply)
- CONDITION: (if the πάθημα is specified elsewhere; “θερμῷ πάθηματι” may be too generic—capture QUALITY_PROPERTY θερμός but not necessarily CONDITION)

Relation:
- applications:
  - applied=κηρωτή, site=(if named), process=ἐπιτίθημι

---

## 9. Review and canonicalization rules

1) A term becomes canonical only after review.
- Candidates go to `term_candidates.csv`.
- Accepted terms go to the relevant controlled list (substances/parts/preparations/etc.).

2) Acceptance thresholds (pragmatic):
- Accept if:
  - it occurs in ≥2 distinct segments, or
  - it is a clearly standard technical term (e.g., κρᾶσις, δύναμις, πυρετός) with high confidence.
- Otherwise defer.

3) Prevent category drift:
- Do not let APPLICATION_SITE become an anatomy dump.
- Do not let PREPARATION absorb base materials (e.g., ὕδωρ is SUBSTANCE).

---

## 10. Prompt-ready label examples (compact)

SUBSTANCE: μανδραγόρα, ἑλλέβορος, πέπερι, ὕδωρ, ὄξος, ἅλμη, ψιμμύθιον  
PART: ῥίζα, φύλλον, σπέρμα, φλοιός, ἄνθος  
PREPARATION: ἀφέψημα, χυμός, τέφρα/σποδός, κηρωτή, κατάπλασμα  
PROCESS: μίγνυμι, τήκω, ἕψω, διηθέω, καταθραύω, ἐπιτίθημι, ἐπαλείφω  
TOOL_CONTAINER: ἀγγεῖον, κεράμιον, θυεία, σπόγγος, ἔριον  
CONDITION: πυρετός, φλεγμονή, ἕλκος, ἐρυσίπελας, οἴδημα  
QUALITY_PROPERTY: θερμός/θερμότης, ψυχρός/ψυχρότης, ξηρός/ξηρότης, ὑγρός/ὑγρότης, δύναμις, κρᾶσις  
APPLICATION_SITE: δέρμα, γλῶττα, γαστήρ, ὑποχόνδρια, κνῆμαι, στόμα (bodily)



# Borderline cases and adjudication rules (v1.0)

This appendix defines recurring ambiguous cases so review decisions stay consistent across texts and reviewers.

Use these rules when assigning labels, building aliases, and creating relations.

---

## A. SUBSTANCE vs PREPARATION

### A1. Vehicles and everyday materials (ὕδωρ, οἶνος, ὄξος, ἔλαιον, γάλα)
Default (v1):
- ὕδωρ, οἶνος, ὄξος, ἔλαιον, γάλα = **SUBSTANCE**

Reason:
- In medical discourse they function as materials/vehicles with pharmacodynamic properties.
- Treating them as PREPARATION forces you to model production pipelines (pressing/fermentation) that are usually not the focus of the therapeutic argument.

How to preserve “produced by” information:
- If the text explicitly discusses production (e.g., pressing olives, fermenting), capture it as a **PREPARATION_EVENT** relation later, but keep the base term in SUBSTANCE.

Example:
- “ἔλαιον” in an application context → SUBSTANCE
- “ἀμόργη δ’ ἐπ’ ἐλαίου” (dregs of oil) → see A3

---

### A2. Extracts, juices, decoctions, and pastes
Default:
- χυμός, ἀφέψημα, κατάπλασμα, κηρωτή = **PREPARATION**

Reason:
- These are explicitly procedural outputs and are meaningful as outputs-of-process relations.

Examples:
- “ἀφέψημα μανδραγόρας” → PREPARATION
- “χυμὸς ῥίζης” → PREPARATION

Relation expectation:
- For each attested PREPARATION, create (or queue) a prep-event linking:
  - input substance or substance+part
  - processes (boil, strain, press)
  - output preparation type

---

### A3. Residues, dregs, sediment (τρύξ, ἀμόργη, ἰλύς)
Default:
- Treat these as **PREPARATION** if they are explicitly described as separable products/residues.
- Treat as **SUBSTANCE** only if the text uses them as a stable material headword (rare).

Examples:
- τρύξ (wine lees) → PREPARATION
- ἀμόργη (oil dregs) → PREPARATION
- ἰλύς (mud/silt) in “τοῦ Νείλου ἰλυῶδες ὕδωρ” context: the water is SUBSTANCE; ἰλύς is not necessarily a canonical PREPARATION unless used as a therapeutic ingredient.

Rule:
- If it is “the leftover matter after separation,” label PREPARATION (product of a process: settling/straining/pressing).

---

## B. SUBSTANCE vs PART

### B1. “Mandrake root” (μανδραγόρα + ῥίζα)
Canonical model:
- μανδραγόρα = SUBSTANCE
- ῥίζα = PART
- “μανδραγόρου ῥίζα” is represented by a relation:
  - `substance_part_occurrence(substance=μανδραγόρα, part=ῥίζα)`

Do not create a separate SUBSTANCE entry “μανδραγόρου ῥίζα” as canonical.
Instead:
- store it as a **surface alias** or a **phrase record** for matching and evidence, but canonical identity remains compositional.

Reason:
- Prevents combinatorial explosion (every plant part as new substance).

---

### B2. Plant exudates and natural products (ῥητίνη, πίσσα, ἄσφαλτος)
Default:
- If treated as a standalone material: **SUBSTANCE**
- If explicitly framed as “from part of X” and functioning as “a part”: still **SUBSTANCE** (not PART), because exudates behave like materials, not anatomical parts.

Examples:
- ῥητίνη (resin) → SUBSTANCE
- πίσσα (pitch) → SUBSTANCE
- ἄσφαλτος (bitumen) → SUBSTANCE

Rule:
- PART is for anatomical/botanical parts (root/leaf/bark/seed), not for products (resin/pitch), even if “comes from” the plant.

Capture “derived from” later as a relation if needed.

---

### B3. Powders and “ground” forms
Default:
- If “powder” is expressed as a generic state (e.g., χνοῦς, κονιορτός) and used as a resulting product, treat as **PREPARATION** only when the text treats it as an output form.
- Otherwise treat as a descriptive state and do not canonize.

Examples:
- “ὡς χνοῶδες γενέσθαι” (become downy/fine) describes particle state; do not turn χνοῦς into a canonical PREPARATION unless it becomes an ingredient class.

Rule:
- Avoid canonizing generic physical descriptors unless used as stable medical materials.

---

## C. PART vs APPLICATION_SITE

### C1. “Parts” of bodies are NOT PART
PART is only “part of a substance.”

Body targets are APPLICATION_SITE.
Examples:
- δέρμα, γλῶττα, γαστήρ, ὑποχόνδρια, κνῆμαι → APPLICATION_SITE

Rule:
- If it belongs to anatomy, it is APPLICATION_SITE only when used as an application target, otherwise exclude (to avoid anatomy drift).

---

### C2. Ambiguous nouns (στόμα, φλοιός)
στόμα:
- APPLICATION_SITE when bodily (mouth; orifice of wound) in therapeutic context.
- Exclude when used as “opening” in non-bodily sense unless the context is clearly medicinal and the target is bodily.

φλοιός:
- PART when botanical (bark/peel).
- Exclude if it is used metaphorically without substance reference.

Rule:
- If the term attaches to a known SUBSTANCE in genitive, prefer PART (e.g., “ῥίζης φλοιός”).
- If it attaches to a body context, prefer APPLICATION_SITE.

---

## D. QUALITY_PROPERTY vs PROCESS

### D1. Pharmacodynamic predicates (θερμαίνειν, ψύχειν, ξηραίνειν, ὑγραίνειν)
These can look like verbs (PROCESS) but often function as “what property it has.”

Default for v1:
- When used as a pharmacodynamic classification (the text is stating what a drug does by nature): label as **QUALITY_PROPERTY** (or include both with notes if you must, but prefer one for dedup).
- When used as a practical instruction (“cool it by doing X”): label as **PROCESS**.

Examples:
- “τὸ φάρμακον ψύχει” (drug cools) → QUALITY_PROPERTY
- “ψῦξον τὸ σῶμα” (cool the body) → PROCESS

Practical rule for extractors:
- If the subject is a SUBSTANCE and the verb describes its effect, treat as QUALITY_PROPERTY.
- If the subject is a practitioner implied and the verb is an instruction, treat as PROCESS.

---

### D2. Theoretical terms (δύναμις, κρᾶσις, οὐσία, στοιχεῖον)
Default:
- δύναμις, κρᾶσις, θερμότης/ψυχρότης/… = QUALITY_PROPERTY
- οὐσία, στοιχεῖον: include only when they are part of explicit medical-physical theory in scope; otherwise exclude as too general.

Example:
- “ἡ δὲ δύναμις αἰτία τις ἐστιν δραστική” → include δύναμις (QUALITY_PROPERTY)
- “περὶ στοιχείων” in a pharmacological context → include στοιχεῖον only if it is functioning as a technical medical concept in that chunk.

Rule:
- Keep the vocabulary pharmacy/science-focused, not generic metaphysics.

---

## E. CONDITION vs QUALITY_PROPERTY

### E1. “Hot disease” and adjectival modifiers
- πυρετός is CONDITION.
- θερμός is QUALITY_PROPERTY.
- “θερμὰ νοσήματα” (hot diseases) yields:
  - CONDITION: νόσημα only if it is a specific clinical term in that context (often too generic)
  - QUALITY_PROPERTY: θερμός
Better:
- keep the specific disease nouns (πυρετός, φλεγμονή, ἐρυσίπελας, ἕλκος)
- avoid canonizing generic “νόσημα” unless your research requires it.

Rule:
- Prefer specific nosological lexemes; avoid generic containers.

---

## F. TOOL_CONTAINER vs APPLICATION_SITE vs OTHER

### F1. Materials used as implements (σπόγγος, ἔριον)
Even though they are “materials,” in therapeutic practice they behave as implements.
Default:
- σπόγγος, ἔριον = TOOL_CONTAINER

Reason:
- Their role is instrumental; you need them to reconstruct application procedures.

---

## G. Multiword expressions (MWEs)

### G1. Adjective + substance (λευκὸς ἑλλέβορος)
Default:
- Create an MWE record as SUBSTANCE (phrase), because it disambiguates.
- Also keep the headword SUBSTANCE (ἑλλέβορος).

Do not create λευκός as a standalone term unless it is used as a general QUALITY_PROPERTY in context.

---

### G2. Substance + part phrases (μανδραγόρου ῥίζα)
Default:
- Do NOT canonize as SUBSTANCE.
- Represent via SUBSTANCE + PART + occurrence relation.
- Keep the phrase as an alias for matching.

---

## H. Canonicalization thresholds (borderline enforcement)

### H1. Prevent “vocabulary bloat”
A candidate becomes canonical only if:
- it appears in ≥2 segments, OR
- it is an established technical term (high confidence), OR
- it is required for a relation you are extracting (e.g., a recurring APPLICATION_SITE).

Otherwise:
- DEFER (store in candidates), not ACCEPT.

### H2. APPLICATION_SITE discipline
Do not build a general anatomy lexicon.
Canonize application sites only when:
- they appear in an application frame (ἐπί/κατά/εἰς + site; or near apply/anoint/pour verbs),
- and recur or are clinically central.

---

## I. Worked borderline examples

### I1. “μανδραγόραν … κατὰ τῆς γλώττης ἐπιβαλλόμενον”
Extract:
- SUBSTANCE: μανδραγόρα
- APPLICATION_SITE: γλῶττα
- PROCESS: ἐπιβάλλω / ἐπιτίθημι (apply/place) if it is procedural instruction; otherwise capture as relation evidence
Relation:
- application(applied=μανδραγόρα, site=γλῶττα, process=apply)

### I2. “κηρωτὴν … διὰ ὕδατος ψυχροῦ μαλάξας”
Extract:
- PREPARATION: κηρωτή
- SUBSTANCE: ὕδωρ
- QUALITY_PROPERTY: ψυχρός
- PROCESS: μαλάσσω (soften), ἀναδεύω (stir) if present

### I3. “τρὺξ μὲν ἐπὶ τῶν οἴνων…”
Extract:
- PREPARATION: τρύξ
- SUBSTANCE: οἶνος
Optional relation:
- preparation_output_of(settling/fermentation) only if explicitly described; otherwise keep as PREPARATION term.

