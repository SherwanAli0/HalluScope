"""Stage 4c - Threshold classifier on sentence entropy (EXTENSION, not replication).

The base paper only reports average entropies (Table I). This module goes
beyond it (HalluScope objective 4): treat sentence-level entropy as a score
for a binary hallucination classifier, sweep thresholds, and report
precision / recall / F1 / AUC-ROC per model and dataset, plus ROC curves.

Classes: positive = H sentences, negative = C sentences (strict).
For fake_qampari there are no C sentences by construction, so the negative
class falls back to all non-H sentences (broad) and is marked in the output.

Outputs:
  results/tables/classification_metrics.csv
  results/figures/roc_<alias>.png   (one figure per model, 3 dataset curves)

Usage:
  py -3.11 evaluation/classifier.py --aliases llama3-8b-instruct ...
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve, precision_recall_curve

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
LAB_DIR = HERE / "outputs"
TABLES = REPO / "results" / "tables"
FIGURES = REPO / "results" / "figures"


def collect(path):
    sents = [s for line in open(path, encoding="utf-8")
             for s in json.loads(line)["sentences"]]
    pos = [s["mean_entropy"] for s in sents if s["label"] == "H"]
    neg_strict = [s["mean_entropy"] for s in sents if s["label"] == "C"]
    neg_broad = [s["mean_entropy"] for s in sents if s["label"] != "H"]
    return pos, neg_strict, neg_broad


def best_f1(y, scores):
    prec, rec, thr = precision_recall_curve(y, scores)
    f1 = 2 * prec * rec / np.clip(prec + rec, 1e-12, None)
    i = int(np.nanargmax(f1[:-1])) if len(f1) > 1 else 0
    return f1[i], prec[i], rec[i], (thr[i] if i < len(thr) else float("nan"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aliases", nargs="+", required=True)
    ap.add_argument("--lab-dir", default=str(LAB_DIR))
    args = ap.parse_args()

    for alias in args.aliases:  # fail before touching results/ on a bad alias
        adir = Path(args.lab_dir) / alias
        if not adir.is_dir() or not any(adir.glob("*.jsonl")):
            sys.exit(f"[error] no labeled *.jsonl under {adir} - nothing to "
                     f"classify for alias '{alias}' (results/ left unchanged)")

    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    rows = []
    for alias in args.aliases:
        adir = Path(args.lab_dir) / alias
        fig, ax = plt.subplots(figsize=(6, 5))
        n_curves = 0
        for f in sorted(adir.glob("*.jsonl")):
            ds = f.stem
            pos, neg_strict, neg_broad = collect(f)
            neg, neg_def = (neg_strict, "strict") if neg_strict else (neg_broad, "broad")
            if not pos or not neg:
                print(f"[skip] {alias}/{ds}: pos={len(pos)} neg={len(neg)}")
                continue
            y = np.array([1] * len(pos) + [0] * len(neg))
            s = np.array(pos + neg)
            auroc = roc_auc_score(y, s)
            f1, p, r, thr = best_f1(y, s)
            rows.append({"model": alias, "dataset": ds, "neg_class": neg_def,
                         "n_pos": len(pos), "n_neg": len(neg),
                         "auroc": auroc, "best_f1": f1,
                         "precision": p, "recall": r, "threshold": thr})
            fpr, tpr, _ = roc_curve(y, s)
            ax.plot(fpr, tpr, label=f"{ds} (AUROC={auroc:.3f}, {neg_def})")
            n_curves += 1

        if n_curves == 0:  # nothing plottable: do not overwrite an existing figure
            plt.close(fig)
            print(f"[skip] {alias}: no dataset with both classes, no ROC figure written")
            continue

        ax.plot([0, 1], [0, 1], "k--", lw=0.8)
        ax.set_xlabel("False positive rate")
        ax.set_ylabel("True positive rate")
        ax.set_title(f"Sentence-entropy hallucination detection - {alias}")
        ax.legend(loc="lower right", fontsize=8)
        fig.tight_layout()
        fig.savefig(FIGURES / f"roc_{alias}.png", dpi=160)
        plt.close(fig)
        print(f"[ ok ] ROC figure -> {FIGURES / f'roc_{alias}.png'}")

    if not rows:
        sys.exit("[error] no dataset had both classes (H and a non-H class); "
                 "classification_metrics.csv left unchanged")
    df = pd.DataFrame(rows)
    out = TABLES / "classification_metrics.csv"
    df.to_csv(out, index=False)
    if not df.empty:
        print(df.to_string(index=False))
    print(f"[done] {out}")


if __name__ == "__main__":
    main()
