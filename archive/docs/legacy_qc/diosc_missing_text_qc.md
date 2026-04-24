# Dioscorides Missing-Text QC

- Review file: `/home/seancoughlin/Projects/ancient-simples/data-workbench/diosc_alignment_review_text.csv`
- Exists: **True**
- Data rows: **69**
- Action counts: `{'KEEP': 30, 'UPDATE': 14, 'INSERT': 25}`
- Invalid action rows: **39**
- Rows with Greek in `revised_lemma_en` but empty `revised_entry_gr`: **6**
- INSERT rows missing `insert_after_line_no`: **0**

## Assessment
- `diosc_alignment_review_text.csv` is not directly apply-compatible for deterministic patching.
- Action vocabulary and payload placement require rebuild from authoritative recovered chapter texts.
