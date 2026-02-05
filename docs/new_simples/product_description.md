# Product statement (plain English)

This product is an internal scholarly database and web application that turns a set of TEI-encoded Greek medical texts into a queryable, citable, cross-linked corpus. It exists to let researchers reliably retrieve every passage (with full logical and physical references) that pertains to a single ingredient term or to a preparation formula (recipe), and to inspect how those ingredients and preparations are described across authors and recensions.

It does this by ingesting TEI as the canonical source for Greek base text and citation structure (book/chapter/section plus volume/page/line anchors), projecting that into a relational database for fast querying, and maintaining a curated linking layer (lemma identity, recipe identity, aliases, and evidence-backed assertions). The application then supports search, faceted queries, and comparison views that show reuse, reworking, and rearrangement of earlier materials through aligned passage views and “diff-like” highlighting grounded in stable identifiers and citations.

The intended deployment model is a single Next.js web application backed by Supabase/PostgreSQL, with offline scripts allowed for TEI indexing and exports.  

# What it serves

* A stable research substrate for “what does the corpus say about X?” where X is an ingredient (lemma) or a preparation (recipe/formula).
* A linking backbone that makes cross-author comparison tractable (Aëtius ↔ Galen ↔ Oribasius ↔ Paul ↔ Dioscorides), independent of differences in segmentation and editorial conventions.
* A citable evidence store: every retrieved claim or mention can be traced back to exact passages with both logical (book/chapter/section) and physical (edition volume/page/line) references.
* A controlled way to curate “how described” metadata (qualities, degrees, parts, processes, indications, etc.) with explicit evidence spans.

# What it does

Ingests and indexes TEI for base text and citations

* Reads TEI editions as the authority for Greek and citation spines.
* Extracts stable segments and their identifiers.
* Derives and stores:

  * logical refs (book/chapter/section or equivalent),
  * physical refs (volume/page/line where present),
  * token streams and normalized search fields for performance and anchoring.

Creates a queryable linking layer for ingredients and recipes

* Maintains a lemma registry (stable IDs) for ingredient identity, plus aliases for variant forms and spellings.
* Maintains a recipe/formula registry (stable IDs) representing preparations and their variants (when the same preparation appears with different steps/ingredients across authors).
* Links:

  * segments ↔ lemma IDs (aboutness and/or occurrence),
  * segments ↔ recipe IDs (membership and/or step evidence),
  * evidence spans ↔ structured assertions (qualities/parts/processes).

Supports the two primary query modes

* Ingredient queries: “show me all entries/passages related to absinth,” including:

  * “about” entries (curated links),
  * “mentions” (derived from token/alias matching),
  * and any associated assertions (e.g., qualities/degrees, uses, preparations), all with full references.
* Recipe queries: “show me all entries/passages related to formula X,” including:

  * all steps/members across works,
  * variants and rearrangements,
  * ingredients involved (lemmata),
  * processes used (boil, decoct, roast),
  * and the same citation completeness.

Enables “how described” queries (facet queries backed by evidence)

* Example classes of queries:

  * “all drugs that are hot, 3rd degree”
  * “all plant roots”
  * “all instances of boiling”
* Every returned result includes:

  * the cited passage,
  * the evidence span,
  * the exact logical + physical references.

Provides reuse/reworking analysis (“diff-like” views)

* Side-by-side aligned viewing of comparable passages, initially at segment level.
* “Diff-like” highlighting can be implemented as a staged capability:

  * early: segment alignment + similarity cues + manual notes,
  * later: finer-grained reuse/rearrangement views driven by derived tokens and optional heuristic alignment, clearly labeled as heuristic (not a definitive critical apparatus).

Exports citable datasets and interchange packages

* CSV/JSON exports for lemmata, recipes, links, assertions, and query results.
* Optional TEI standoff exports that point back to TEI segment/token anchors (export-only, no TEI editing in-app). 

---

# Clarifying questions to focus the product

These are the questions that materially change the schema, indexer contract, and UI scope. Answering them will let the work tree and MVP scope become crisp.

Ingredient identity and “related to”

* When you say “all entries related to a single ingredient term,” do you mean:

  * only passages whose *topic/heading* is that ingredient (“aboutness”), or
  * any passage that *mentions* the ingredient, or
  * both, with a way to separate them in results?
* Do you want “ingredient term” queries to be driven primarily by:

  * a curated lemma registry (preferred for stability),
  * a lexeme/string search (fast but noisy),
  * or a hybrid (curated lemma IDs + derived mention index from aliases)?

Recipe/formula identity and granularity

* What is the minimum unit of a “recipe/formula” you need for querying?

  * a named preparation concept (recipe ID),
  * a list of steps,
  * ingredients + processes only,
  * or fully modeled quantities/measurements?
* Do you need recipes to be stable across authors (one recipe ID with multiple attestations/variants), or is “recipe as it appears in one author” acceptable for the first build?
* Are recipes expected to live primarily:

  * in TEI (as standOff + step IDs) and projected to SQL, or
  * in SQL as canonical objects linked to TEI segments, with TEI as base text only?

“How described” facets (ontology) and curation load

* Which descriptive facets are “must have” for the first usable system (beyond your examples)?

  * qualities/degrees (hot/cold/dry/wet),
  * parts (root/leaf/seed),
  * processes (boil/decoct/roast),
  * indications/uses,
  * preparation forms (decoction, poultice, etc.),
  * dosage/measurement,
  * contraindications?
* For each facet, do you want:

  * fully curated assertions only (high accuracy, slower),
  * derived suggestions from token/alias cues feeding a review queue (faster, needs review UI),
  * or a mix (curate core, suggest the rest)?

Citation completeness expectations

* Is physical citation (volume/page/line) required for *all* indexed texts, or acceptable to be “present when the TEI provides it” with explicit “not available” handling?
* Are there multiple citation systems per work that must be supported simultaneously (e.g., different editions), or is one per TEI document sufficient for the first phase?

Segmentation for indexing and comparison

* What is the segment granularity you want as the default “entry”?

  * CTS section,
  * chapter,
  * smaller editorial units (e.g., recipe step),
  * or author-specific rules?
* Do you need the ability to compare across authors when one author splits content into multiple segments and another bundles it into one? If yes, do you want:

  * a lightweight “occurrence grouping” layer (clusters segments for comparison),
  * or is “show all linked segments; user interprets grouping” acceptable?

Reuse/reworking (“diffs”) expectations

* When you say “like diffs,” do you expect:

  * a true word-level diff output (high complexity, brittle across editions), or
  * a scholarly “reuse view” that highlights likely overlap and rearrangement heuristically, with citations and editorial notes?
* Do you want the system to assert directionality (“A copied B”), or just show similarity and let editors interpret?

Editorial workflow scope

* Is translation editing and commentary authoring in the web app required for the linking-first phase, or can it be minimal (store revised translation + notes) while linking/query features take priority?
* Who will do curation (how many editors, what roles), and do you need:

  * reviewer states (draft/reviewed/published),
  * audit trails,
  * disagreement/alternate assertions?

Success criteria for the first “linking happens” release

* What would count as success in the first release?

  * “For ingredient X, I can retrieve all relevant passages across Aëtius + comparator with complete citations”
  * “For recipe Y, I can retrieve all attestations and variants across authors”
  * “I can run the 4 canonical facet queries and export the results”
  * “I can see reuse patterns between two authors in a comparison view”

If you answer just the subset below, it will be enough to lock an MVP scope tightly:

* “related to” = aboutness vs mentions vs both
* recipe identity granularity (concept vs steps vs ingredients/processes/quantities)
* must-have facets for “how described”
* acceptable diff level (heuristic reuse view vs true word-level diff)
* required segment granularity for indexing
