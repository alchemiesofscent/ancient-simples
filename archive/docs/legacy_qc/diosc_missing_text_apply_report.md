# Dioscorides Missing-Text Apply Report

- Input CSV: `/home/seancoughlin/Projects/ancient-simples/data-workbench/diosc.csv`
- Patch CSV: `/home/seancoughlin/Projects/ancient-simples/data-workbench/diosc_missing_text_patch.csv`
- Output CSV: `/home/seancoughlin/Projects/ancient-simples/data-workbench/diosc.patched.csv`
- Source rows: **830**
- Output rows: **835**
- Inserted rows: **5**
- Missing `entry_en` rows after patch: **0**
- Sanity errors: **0**

## Operations
- Split embedded RV tails: **5**
- Inserted RV rows: **4**
- CLEAN 2.178_RV var_par_prod_gr (strip tab/quotes)
- FILL 2.178_RV lemma_en from patch
- REPLACE 3.73_RV entry_gr (strip RV prefix)
- FILL 3.73_RV missing fields (lemma_en/entry_en)
- REPLACE 4.58_RV entry_gr (strip RV prefix)
- FILL 4.58_RV missing fields (lemma_en/entry_en)
- SPLIT_HOST 3.63 -> removed [64] RV tail
- INSERT_AFTER 3.63 -> 3.64_RV
- SPLIT_HOST 4.15 -> removed [16] RV tail
- INSERT_AFTER 4.15 -> 4.16_RV
- SPLIT_HOST 4.127 -> removed [127] RV tail
- INSERT_AFTER 4.127 -> 4.127_RV
- SPLIT_HOST 4.137 -> removed [137] RV tail
- INSERT_AFTER 4.137 -> 4.137_RV
- SPLIT_HOST 4.189 -> removed [190] RV tail
- COPY 4.190_RV English -> 4.190 (restore Large heliotrope translation)
- REPLACE 4.190_RV payload -> Kunea
- INSERT_AFTER 4.190 -> 4.191 (Small heliotrope)
