# Dioscorides vocab run QC summary

- Run dir: `outputs/vocab_entries_v3/entries_full_v3`
- Manifest: `outputs/vocab_entries_v3/entries_full_v3/manifest.json`
- Run id: `entries_full_v3`

## Completeness
- Expected jobs: 2135
- Result files present: 2135
- Valid result JSONs: 2120
- Missing results: 15
- Invalid JSON files: 0
- source_id mismatches: 0
- Error logs present: 1329
- Completeness OK: **False**

## Quality profile
- Total qualities: 2885
- Entries with >=1 quality: 1395
- Entries with degree != null: 419
- Qualities with explicit degree: 814
- Degree ratio: 0.282

### Axis counts
- COLD: 462
- DRY: 1119
- HOT: 1009
- WET: 295

### Intensity counts
- balanced: 114
- extreme: 22
- moderate: 167
- none: 2208
- strong: 224
- weak: 150

## Term profile
- ADMINISTRATION: 573
- APPLICATION_SITE: 1555
- CONDITION: 2744
- PART: 294
- PLACE: 296
- PREPARATION: 957
- PROCESS: 2568
- QUALITY_PROPERTY: 9960
- SUBSTANCE: 6884
- SUBSTANCE_PART: 1386
- TOOL_CONTAINER: 290

## Anomalies
- QUALITY_PROPERTY lemma_normalized in {δυναμις, ουσια}: 959
- SUBSTANCE_PART consistency anomalies: 0
- Normalization anomalies: 656

## Alerts
- High explicit-degree ratio for Dioscorides (>25%); check for over-quantification.
- Generic QUALITY_PROPERTY terms (δυναμις/ουσια) detected; spot-check context.
- Normalization anomalies detected; results may have bypassed runner post-validation.

## Missing result IDs (first 50)
- `AET_LM-1.7~1`
- `AET_LM-1.7~2`
- `AET_LM-1.77~1`
- `AET_LM-1.77~2`
- `AET_LM-1.209~1`
- `AET_LM-1.209~2`
- `AET_LM-1.241~1`
- `AET_LM-1.241~2`
- `AET_LM-1.241~3`
- `AET_LM-1.241~4`
- `AET_LM-1.318~1`
- `AET_LM-1.318~2`
- `AET_LM-1.318~3`
- `AET_LM-2.122~1`
- `AET_LM-2.122~2`
