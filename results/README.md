# Results

Final artifacts produced by Stage 4 aggregation (`evaluation/build_table1.py`
and `evaluation/classifier.py`). Everything here is **tracked in git** (unlike
the per-stage `outputs/` folders, which are regenerable and gitignored).

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

```
py -3.11 integration/run_pipeline.py --aggregate <alias1> <alias2> ...
```

after stages 2-4 have produced outputs for those aliases.
