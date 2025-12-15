# lemmata.csv QC report

- Generated: `2025-12-15T20:45:17+00:00`
- Workbook: `Simples.xlsx`
- Total lemmata: **1154**
- Sent to review: **2**

## Normalization edge cases
- Headwords containing iota subscripts (preserved): **12**
- Headwords containing non-Greek letters/digits: **0**
- Multiword headwords (>=2 Greek tokens): **421**
- Normalized collisions (distinct headwords sharing same normalized form): **42**
  - `αστηρ αττικος`: `Ἀστὴρ Ἀττικός`, `ἀστὴρ Ἀττικὸς`, `ἀστὴρ ἀττικός`, `ἀστήρ ἀττικός`
  - `ακανθα αιγυπτια`: `ἄκανθα Αἰγυπτία`, `ἄκανθα αἰγυπτία`
  - `αργεμονη`: `Ἀργεμόνη`, `ἀργεμόνη`
  - `αρισαρον`: `Ἀρίσαρον`, `ἀρίσαρον`
  - `ασπληνον`: `Ἄσπληνον`, `ἄσπληνον`
  - `αστραγαλος`: `Ἀστράγαλος`, `ἀστράγαλος`
  - `αφακη`: `Ἀφάκη`, `ἀφάκη`
  - `βηχιον`: `βηχίον`, `Βηχίον`
  - `βολβος ημερος`: `βολβὸς ἥμερος`, `βολβός ἥμερος`
  - `γη σαμια`: `γῆ Σαμία`, `γῆ σαμία`
  - `γογγυλις`: `γογγυλίς`, `γογγυλίς`
  - `δολιχοι`: `δόλιχοι`, `δόλιχοι`
  - `ελαια`: `ἐλαία`, `ἐλαία`
  - `επιμηλις`: `ἐπιμηλίς`, `Ἐπιμηλίς`
  - `εφημερον`: `ἐφήμερον`, `Ἐφήμερον`
  - `θριδαξ`: `θρίδαξ`, `θρίδαξ`
  - `καππαρις`: `κάππαρις`, `κάππαρις`
  - `κινναρα`: `κιννάρα`, `κιννάρα`
  - `κισθος`: `κισθὸς`, `κισθός`
  - `κολοκυνθη`: `κολοκύνθη`, `κολοκύνθη`
  - _(more omitted)_

## Category (from column O)
- `plant`: **795**
- `mineral`: **184**
- `animal`: **174**
- `substance`: **1**
- Column O blank fallbacks to `substance`: **1**
- Sent to review for unmapped column O values: **0**

## Parent assignment
- Oil family (A) parent assignments: **30**
- Conservative prefix (D) parent assignments: **102**
