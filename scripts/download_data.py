#!/usr/bin/env python3
"""Download and checksum the two official GSE249477 source files."""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "raw"

FILES = {
    "GSE249477_raw_count_normalize_04-10-2025.csv.gz": {
        "url": (
            "https://www.ncbi.nlm.nih.gov/geo/download/"
            "?acc=GSE249477&file=GSE249477_raw_count_normalize_04-10-2025.csv.gz&format=file"
        ),
        "sha256": "4f8e0f8b75ebe4ec8aee6d88ce8e0a5a48f179f5fe7cb5981aafcae8701945cb",
    },
    "GSE249477_family.soft.gz": {
        "url": (
            "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE249nnn/"
            "GSE249477/soft/GSE249477_family.soft.gz"
        ),
        "sha256": "2bcd7b66d5959130dea5880a01713f8c1468197e0b6682214a89c503123f80de",
    },
}


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for filename, metadata in FILES.items():
        destination = DATA_DIR / filename
        if destination.exists() and checksum(destination) == metadata["sha256"]:
            print(f"Verified existing file: {filename}")
            continue

        temporary = destination.with_suffix(destination.suffix + ".part")
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(metadata["url"], temporary)
        observed = checksum(temporary)
        if observed != metadata["sha256"]:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(
                f"Checksum mismatch for {filename}: expected {metadata['sha256']}, got {observed}"
            )
        temporary.replace(destination)
        print(f"Verified: {filename}")


if __name__ == "__main__":
    main()
