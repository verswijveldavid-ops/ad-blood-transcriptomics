#!/usr/bin/env python3
"""Validate the public RNA-seq repository and its headline results."""

from pathlib import Path
import re

import nbformat
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    ROOT / "notebooks" / "01_rnaseq_analysis.ipynb",
    ROOT / "notebooks" / "02_processing_and_QC.ipynb",
]

for path in NOTEBOOKS:
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    errors = [
        output
        for cell in code_cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    assert code_cells and all(cell.execution_count is not None for cell in code_cells)
    assert not errors

de = pd.read_csv(ROOT / "results" / "tables" / "deseq2_ad_vs_cn.csv")
gsea = pd.read_csv(ROOT / "results" / "tables" / "hallmark_preranked_gsea.csv")
assert len(de) == 9137
assert int((de["padj"] < 0.05).sum()) == 0
assert len(gsea) == 47
assert int((gsea["fdr"] < 0.05).sum()) == 0

required = [
    ROOT / "reports" / "01_rnaseq_analysis.html",
    ROOT / "reports" / "02_processing_and_QC.html",
    ROOT / "results" / "figures" / "01_input_qc.png",
    ROOT / "results" / "figures" / "02_pca.png",
    ROOT / "results" / "figures" / "03_de_overview.png",
    ROOT / "results" / "figures" / "04_top_genes_heatmap.png",
    ROOT / "results" / "figures" / "05_hallmark_gsea.png",
    ROOT / "resources" / "MSigDB_Hallmark_2020.gmt",
]
for path in required:
    assert path.exists() and path.stat().st_size > 0, path

forbidden = re.compile(
    r"/Users/|/home/|r0[0-9]{6}|student/task|projects_biomed|anonymous|submission",
    flags=re.IGNORECASE,
)
for path in ROOT.rglob("*"):
    if path.resolve() == Path(__file__).resolve():
        continue
    if path.is_file() and path.suffix.lower() in {".md", ".py", ".ipynb", ".txt", ".tsv"}:
        assert not forbidden.search(path.read_text(errors="replace")), path

print("PASS: 2 executed notebooks, 0 cell errors, 9,137 genes, 0 FDR-significant genes or Hallmark pathways.")
