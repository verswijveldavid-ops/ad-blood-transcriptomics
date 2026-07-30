#!/usr/bin/env python3
"""Validate the two official GEO inputs used by the portfolio analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from gse249477 import load_raw_counts, parse_soft_metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("count_file", type=Path)
    parser.add_argument("soft_file", type=Path)
    args = parser.parse_args()

    metadata = parse_soft_metadata(args.soft_file)
    counts, _, diagnostics = load_raw_counts(args.count_file)
    sample_ids = counts.columns.tolist()

    print(f"Unique genes: {len(counts):,}")
    print(f"Count samples: {len(sample_ids)}")
    print(f"Metadata samples: {len(metadata)}")
    print("Conditions:", metadata["condition"].value_counts().to_dict())
    print("Missing count values:", int(counts.isna().sum().sum()))
    print("Negative count values:", int((counts < 0).sum().sum()))
    print("Parser diagnostics:", diagnostics)
    print(
        "Sample IDs match metadata:",
        set(sample_ids) == set(metadata["sample_id"]),
    )

    if set(sample_ids) != set(metadata["sample_id"]):
        print("Only in counts:", sorted(set(sample_ids) - set(metadata["sample_id"])))
        print("Only in metadata:", sorted(set(metadata["sample_id"]) - set(sample_ids)))


if __name__ == "__main__":
    main()
