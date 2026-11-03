# Results

Final artifacts produced by Stage 4 aggregation (`evaluation/build_table1.py`
and `evaluation/classifier.py`). Everything here is **tracked in git**, as is
`evaluation/outputs/` (the labeled sentences these files are built from). The
heavier per-stage folders `generation/outputs/` and `entropy/outputs/` (and
`data/processed/`) are gitignored and are not in the repository.

## tables/

| File | Contents |
|---|---|
| `replication_table1.csv` | Our Table I numbers next to the paper's printed values, both non-hallucinated class definitions (strict/broad), sentence & token counts |
| `replication_table1.md` | Human-readable side-by-side table with per-cell C1/C2 claim verdicts - **the headline replication artifact**; paste-ready for the report |
| `classification_metrics.csv` | AUROC, best-F1, precision, recall, threshold per model × dataset (extension beyond the paper) |

## figures/

| File | Contents |
|---|---|
| `roc_<alias>.png` | ROC curves of sentence-entropy hallucination detection, one figure per model, one curve per dataset |

## How to regenerate

From the committed labeled outputs (CPU only, seconds; does not regenerate any
raw model output):

```
python run_all.py --only aggregate
```

(equivalently `python integration/run_pipeline.py --aggregate <alias1> <alias2> ...`
for chosen aliases). Re-running rewrites these files in place; the CSV/Markdown
tables reproduced exactly in a check with matplotlib 3.11.2, while the ROC PNGs differed
byte-wise (cause not isolated, most likely the matplotlib version), so keep the committed figures unless a figure actually changed.
If you generated your own aliases (stages 2-4), pass them to `run_pipeline.py --aggregate`.
