# lemmata.csv QC report

- Generated: `2026-01-20T21:39:37+00:00`
- Workbook: `simples.xlsx`
- Total lemmata: **1285**
- Sent to review: **8**

## Normalization edge cases
- Headwords containing iota subscripts (preserved): **12**
- Headwords containing non-Greek letters/digits: **0**
- Multiword headwords (>=2 Greek tokens): **427**
- Normalized collisions (distinct headwords sharing same normalized form): **55**
  - `αστηρ αττικος`: `Ἀστὴρ Ἀττικός`, `ἀστὴρ Ἀττικὸς`, `ἀστὴρ ἀττικός`, `ἀστήρ ἀττικός`
  - `κισθος`: `κισθὸς`, `κίσθος`, `κισθός`
  - `αιρα`: `αἶρα`, `αἴρα`
  - `ακανθα αιγυπτια`: `ἄκανθα Αἰγυπτία`, `ἄκανθα αἰγυπτία`
  - `αλιμον`: `ἅλιμον`, `ἄλιμον`
  - `αμπελος αγρια`: `ἄμπελος ἄγρια`, `ἄμπελος ἀγρία`
  - `αρισαρον`: `Ἀρίσαρον`, `ἀρίσαρον`
  - `αστραγαλος`: `Ἀστράγαλος`, `ἀστράγαλος`
  - `αφακη`: `Ἀφάκη`, `ἀφάκη`
  - `βηχιον`: `βηχίον`, `βήχιον`
  - `γη σαμια`: `γῆ Σαμία`, `γῆ σαμία`
  - `γογγυλις`: `γογγυλίς`, `γογγυλίς`
  - `δολιχοι`: `δόλιχοι`, `δόλιχοι`
  - `ελαια`: `ἐλαία`, `ἐλαία`
  - `ελενιον`: `ἑλενιον`, `ἑλένιον`
  - `θριδαξ`: `θρίδαξ`, `θρίδαξ`
  - `ιδαια ριζα`: `Ἰδαία ῥίζα`, `ἰδαία ῥίζα`
  - `ισοπυρον`: `Ἰσόπυρον`, `ἰσόπυρον`
  - `καππαρις`: `κάππαρις`, `κάππαρις`
  - `κερασος`: `κέρασος`, `κεράσος`
  - _(more omitted)_

## Category (from workbook category column)
- `vegetable`: **898**
- `animal`: **220**
- `mineral`: **167**
- Blank/`substance` category fallbacks (defaulted to `vegetable`): **14**
- Sent to review for unmapped column O values: **0**

## Parent assignment
- Oil family (A) parent assignments: **30**
- Conservative prefix (D) parent assignments: **137**
