# Data provenance

The analysis uses two official files from GEO series GSE249477:

| File | Purpose |
|---|---|
| `GSE249477_raw_count_normalize_04-10-2025.csv.gz` | Author-deposited raw gene counts |
| `GSE249477_family.soft.gz` | Sample metadata and public accessions |

They are not tracked in Git because `scripts/download_data.py` retrieves the
exact files and verifies their SHA-256 checksums. Local copies belong in
`data/raw/`.

The main model uses the deposited integer `Total counts`; supplied normalized
columns are not used as differential-expression input. The parser explicitly
excludes 13 malformed gene rows with missing values rather than imputing them.

