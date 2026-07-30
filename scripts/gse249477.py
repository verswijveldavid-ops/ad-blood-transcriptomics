"""Data loading helpers for the GSE249477 portfolio analysis."""

from __future__ import annotations

import gzip
from pathlib import Path

import pandas as pd


TOTAL_COUNT_SUFFIX = " (GE) - Total counts"


def parse_soft_metadata(path: Path) -> pd.DataFrame:
    """Parse sample-level fields from a GEO family SOFT file."""
    samples: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line.startswith("^SAMPLE = "):
                if current:
                    samples.append(current)
                current = {"geo_accession": line.split(" = ", 1)[1]}
            elif current is None:
                continue
            elif line.startswith("!Sample_description = "):
                current["sample_id"] = line.split(" = ", 1)[1].strip()
            elif line.startswith("!Sample_characteristics_ch1 = "):
                value = line.split(" = ", 1)[1]
                key, _, item = value.partition(": ")
                current[key.lower()] = item.strip()
            elif line.startswith("!Sample_relation = SRA: "):
                current["sra_experiment"] = line.rsplit("=", 1)[-1]

    if current:
        samples.append(current)

    metadata = pd.DataFrame(samples)
    metadata["age"] = (
        metadata["age"].str.extract(r"(\d+)", expand=False).astype(int)
    )
    metadata["sex"] = metadata["sex"].str.lower()
    disease_map = {
        "Alzheimer's disease": "AD",
        "mild cognitive impairment due to Alzheimer's disease": "MCI",
        "cognitively normal control": "CN",
    }
    metadata["condition"] = metadata["disease state"].map(disease_map)
    return metadata[
        [
            "sample_id",
            "geo_accession",
            "sra_experiment",
            "condition",
            "age",
            "sex",
            "tissue",
        ]
    ]


def load_raw_counts(path: Path) -> tuple[pd.DataFrame, pd.Series, dict[str, int]]:
    """Load raw counts while isolating malformed source rows.

    GEO's CSV contains a handful of unescaped quotation marks in its long GO
    annotation fields. Pandas exposes these as 13 valid-looking gene rows with
    four missing samples plus 13 continuation rows. Those 13 genes are excluded
    explicitly rather than silently imputed; this is <0.1% of supplied genes.
    """
    source = pd.read_csv(path, low_memory=False)
    total_headers = [name for name in source.columns if name.endswith(" - Total counts")]
    if len(total_headers) != 62:
        raise ValueError(f"Expected 62 count columns, found {len(total_headers)}")
    sample_ids = [name.removesuffix(TOTAL_COUNT_SUFFIX) for name in total_headers]

    valid_identifier = source["Identifier"].astype(str).str.fullmatch(r"ENSG\d+")
    gene_rows = source.loc[valid_identifier, ["Name", "Identifier", *total_headers]].copy()
    affected = gene_rows[total_headers].isna().any(axis=1)
    clean = gene_rows.loc[~affected].copy()
    clean[total_headers] = clean[total_headers].astype(int)
    clean = clean.rename(columns={"Identifier": "ensembl_id", "Name": "symbol"})
    clean = clean.rename(columns=dict(zip(total_headers, sample_ids, strict=True)))

    duplicate_ids = int(clean["ensembl_id"].duplicated().sum())
    symbol_by_id = clean.groupby("ensembl_id", sort=False)["symbol"].first()
    counts = clean.drop(columns="symbol").groupby("ensembl_id", sort=False).sum()
    diagnostics = {
        "source_rows": len(source),
        "valid_gene_rows": len(gene_rows),
        "excluded_genes_with_missing_counts": int(affected.sum()),
        "unique_ensembl_ids": len(counts),
        "duplicate_ensembl_ids": duplicate_ids,
        "invalid_continuation_rows": int((~valid_identifier).sum()),
    }
    return counts, symbol_by_id, diagnostics
