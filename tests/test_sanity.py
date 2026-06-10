"""12-test sanity suite for the HalluScope replication.

Runs against the COMMITTED artifacts only — the upstream datasets and the
result CSVs/figures under results/ — so it needs no GPU and no model
downloads (deps: pandas, pytest). It guards three things:

  1. dataset integrity (tests 1-4): the inputs are still byte-faithful to the
     paper's 297-prompt setup;
  2. the replication's central claims (tests 5-9): C1 holds in all 9 cells for
     OUR numbers and for the paper's printed numbers;
  3. result hygiene (tests 10-12): metric bounds, figure presence, and the
     headline LLaMA-3/FakeQAMPARI near-match that anchors faithfulness.

If a code change breaks any of these, it is a regression on the replication
and must be justified against the paper text (see CONTRIBUTING.md).
"""

import json
import math
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
UPSTREAM = REPO / "data" / "upstream"
TABLE1 = REPO / "results" / "tables" / "replication_table1.csv"
CLS = REPO / "results" / "tables" / "classification_metrics.csv"
FIGS = REPO / "results" / "figures"

EXPECTED_COUNTS = {"trivia_facts.jsonl": 97,
                   "qampari_rephrased.jsonl": 100,
                   "fake_qampari.jsonl": 100}
ALIASES = {"llama3-8b-instruct", "qwen2-7b-instruct", "gemma2-9b-it"}
LN_VOCAB_MAX = 12.45  # ln(256k), Gemma-2 — theoretical entropy ceiling


def _lines(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def _nonh_sent(row):
    """Strict (CORRECT sentences) where it exists, else broad — same rule
    build_table1 uses for FakeQAMPARI, which has no CORRECT class."""
    v = row["nonh_sent_strict"]
    return row["nonh_sent_broad"] if (isinstance(v, float) and math.isnan(v)) else v


def _nonh_tok(row):
    v = row["nonh_token_strict"]
    return row["nonh_token_broad"] if (isinstance(v, float) and math.isnan(v)) else v


# ---------- 1-4: dataset integrity ----------

def test_01_upstream_files_present_with_paper_counts():
    for fname, n in EXPECTED_COUNTS.items():
        path = UPSTREAM / fname
        assert path.exists(), f"missing upstream dataset: {fname}"
        assert len(_lines(path)) == n, f"{fname}: expected {n} prompts"


def test_02_every_prompt_ends_with_completion_cue():
    for fname in EXPECTED_COUNTS:
        for obj in _lines(UPSTREAM / fname):
            (prompt, _), = obj.items()
            assert prompt.endswith("\n1."), f"{fname}: prompt lost its cue"


def test_03_fake_qampari_gold_lists_all_empty():
    for obj in _lines(UPSTREAM / "fake_qampari.jsonl"):
        (_, gold), = obj.items()
        assert gold == [], "FakeQAMPARI must be unanswerable by construction"


def test_04_fetch_datasets_builds_exactly_297():
    subprocess.run([sys.executable, str(REPO / "data" / "fetch_datasets.py")],
                   check=True, cwd=REPO, capture_output=True)
    out = REPO / "data" / "processed" / "replication.jsonl"
    assert len(_lines(out)) == 297


# ---------- 5-9: the replication's claims ----------

@pytest.fixture(scope="module")
def table1():
    assert TABLE1.exists(), "results/tables/replication_table1.csv missing"
    df = pd.read_csv(TABLE1)
    assert len(df) == 9, "expected 3 models x 3 datasets = 9 rows"
    assert set(df["model"]) == ALIASES
    return df


def test_05_table1_has_ours_and_paper_columns(table1):
    needed = {"dataset", "model", "h_token", "h_sent",
              "nonh_token_strict", "nonh_sent_strict",
              "nonh_token_broad", "nonh_sent_broad",
              "paper_nonh_sent", "paper_h_sent",
              "paper_nonh_token", "paper_h_token"}
    assert needed.issubset(table1.columns)


def test_06_c1_sentence_level_holds_in_all_9_cells(table1):
    for _, r in table1.iterrows():
        assert r["h_sent"] > _nonh_sent(r), \
            f"C1 (sentence) fails: {r['model']}/{r['dataset']}"


def test_07_c1_token_level_holds_in_all_9_cells(table1):
    for _, r in table1.iterrows():
        assert r["h_token"] > _nonh_tok(r), \
            f"C1 (token) fails: {r['model']}/{r['dataset']}"


def test_08_entropies_within_theoretical_range(table1):
    cols = ["h_token", "h_sent", "nonh_token_broad", "nonh_sent_broad"]
    vals = table1[cols].to_numpy().ravel()
    assert ((vals > 0) & (vals < LN_VOCAB_MAX)).all(), \
        "entropy outside (0, ln|V|) — wrong axis / scores-vs-logits bug?"


def test_09_c1_also_holds_for_the_papers_printed_values(table1):
    for _, r in table1.iterrows():
        assert r["paper_h_sent"] > r["paper_nonh_sent"]
        assert r["paper_h_token"] > r["paper_nonh_token"]


# ---------- 10-12: result hygiene + headline anchor ----------

def test_10_classification_metrics_bounded_and_figures_present():
    assert CLS.exists(), "results/tables/classification_metrics.csv missing"
    df = pd.read_csv(CLS)
    assert len(df) == 9 and set(df["model"]) == ALIASES
    for col in ["auroc", "best_f1", "precision", "recall"]:
        assert df[col].between(0, 1).all(), f"{col} out of [0,1]"
    for alias in ALIASES:
        assert (FIGS / f"roc_{alias}.png").exists(), f"missing ROC figure {alias}"


def test_11_fakeqampari_auroc_above_chance_for_every_model():
    df = pd.read_csv(CLS)
    fake = df[df["dataset"] == "fake_qampari"]
    assert len(fake) == 3
    assert (fake["auroc"] > 0.70).all(), \
        "fabricated-entity detection regressed below the reported 0.75-0.87 band"


def test_12_llama_fakeqampari_matches_paper_within_5_hundredths(table1):
    r = table1[(table1["model"] == "llama3-8b-instruct")
               & (table1["dataset"] == "fake_qampari")].iloc[0]
    assert abs(r["nonh_sent_broad"] - r["paper_nonh_sent"]) < 0.05, \
        "headline near-match (non-halluc.) lost"
    assert abs(r["h_sent"] - r["paper_h_sent"]) < 0.05, \
        "headline near-match (halluc.) lost"
