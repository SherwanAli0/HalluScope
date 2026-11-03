# Replication of "Entropy-based Sentence-level Hallucination Score in Large Language Models"

[![tests](https://github.com/SherwanAli0/HalluScope/actions/workflows/tests.yml/badge.svg)](https://github.com/SherwanAli0/HalluScope/actions/workflows/tests.yml)
[![License: MIT + CC-BY 4.0](https://img.shields.io/badge/license-MIT%20%2B%20CC--BY%204.0-yellow.svg)](LICENSE)
[![Python 3.10-3.12](https://img.shields.io/badge/python-3.10%20to%203.12%20(CI)-blue.svg)](.github/workflows/tests.yml)
[![Paper](https://img.shields.io/badge/IEEE%20BigComp-10.1109%2FBigComp64353.2025.00022-darkblue.svg)](https://ieeexplore.ieee.org/document/10936832)

> **Original paper.** E. Joo, Y.-J. Lee, H.-J. Choi. *Entropy-based Sentence-level Hallucination Score in Large Language Models.* IEEE BigComp 2025, pp. 77 to 78. [DOI: 10.1109/BigComp64353.2025.00022](https://ieeexplore.ieee.org/document/10936832)

## Abstract

This repository is an independent paper-faithful replication of the entropy-based sentence-level hallucination score introduced by Joo et al. The method computes the Shannon entropy of the model's full-vocabulary token distribution at every generation step (paper Eq. 1) and averages it over the tokens of each spaCy-split sentence (Eq. 2); higher sentence entropy is read as an uncertainty (hallucination-risk) signal, not as proof that a sentence is false (see [Scope and limits](#scope-and-limits)). We rebuilt the method from the paper text alone (no official code exists - we verified), recovered the paper's exact 297 evaluation prompts and labeling protocol from the upstream repository it cites (Ivgi et al. 2024, github.com/Mivg/fallbacks), and ran all three paper models - LLaMA-3-8B-Instruct, Qwen2-7B-Instruct, Gemma-2-9B-it - in native bf16, greedy, 512 new tokens, batch 1. The paper's central claim (C1) reproduces 9/9: sentences labeled hallucinated carry higher mean entropy than non-hallucinated ones in every model x dataset cell, at both token and sentence level, under the label and class definitions given below. Absolute values only partly match the paper (see [Replication notes](#replication-notes)). On FakeQAMPARI, LLaMA-3 matches the paper's printed values to within ~0.02 nats on both classes (0.146/0.611 vs 0.142/0.631).

## Headline result

Sentence-level entropy in nats (ours / paper Table I):

| Dataset | Model | Non-halluc. (ours/paper) | Halluc. (ours/paper) | Status |
|---|---|---|---|---|
| FakeQAMPARI | LLaMA-3-8B | **0.146 / 0.142** | **0.611 / 0.631** | matches to ~0.02 nats |
| FakeQAMPARI | Qwen2-7B | **0.435 / 0.445** | 0.898 / 1.061 | non-halluc. matches to 0.01 |
| TriviaFacts | LLaMA-3-8B | 0.244 / 0.220 | 0.395 / 0.594 | direction + non-halluc. match |
| TriviaFacts | Qwen2-7B | 0.449 / 0.424 | 0.610 / 1.003 | direction + non-halluc. match |
| QAMPARI | all three | higher H than non-H | higher H than non-H | direction reproduces |

Full 9-cell table with token-level columns: [`results/tables/replication_table1.md`](results/tables/replication_table1.md) and [Results](#results) below.

## Authors

| Name | GitHub | Affiliation |
|---|---|---|
| Sherwan Ali | [@SherwanAli0](https://github.com/SherwanAli0) | Uskudar University |
| Ipek Ucar | [@ipekucr](https://github.com/ipekucr) | Uskudar University |
| Yaprak Sevinc Aldogan | [@YaprakSevincAldogan](https://github.com/YaprakSevincAldogan) | Uskudar University |
| Yasmine Guidoum | [@Dandyyass](https://github.com/Dandyyass) | Uskudar University |
| Abdenour Hichem Guidoum | - | Uskudar University |

Per-contribution roles are listed in [CONTRIBUTORS.md](CONTRIBUTORS.md). University course project (SE418: Large Language Models), 2026.

## Presentation

Project presentation videos on the [HalluScope YouTube channel](https://www.youtube.com/@HalluScope-Entropy-basedSenten):

| Video | Length | Link |
|---|---|---|
| Full project presentation | 16m 08s | [LLM Presentation](https://www.youtube.com/watch?v=YVrVozSMKWI) |
| Short introduction | 2m 41s | [Introduction to the presentation of HalluScope](https://www.youtube.com/watch?v=QILSVvAm4g8) |

## Repository structure

```
.
├── README.md
├── LICENSE                     dual MIT (code) + CC-BY 4.0 (text/results)
├── CITATION.cff
├── CONTRIBUTORS.md             CRediT-style role attribution
├── PIPELINE_CONTRACT.md        binding JSONL interfaces between the 5 stages
├── RESULTS_SUMMARY.md          one-page results overview
├── requirements.txt
├── Makefile
├── run_all.py                  cross-platform single-command reproduction
├── Entropy-based_Sentence-level_Hallucination_Score.pdf
│
├── data/                       Stage 1 - the paper's exact 297 prompts (Person: Yaprak)
│   ├── fetch_datasets.py       download + validate + unify
│   └── upstream/               byte-identical files from Mivg/fallbacks (MIT)
│
├── generation/                 Stage 2 - greedy generation + RAW logit entropy (Person: Sherwan)
│   └── generate.py             output_logits=True, fp32 nats, char spans, resumable
│
├── entropy/                    Stage 3 - spaCy sentences + Eq. 2 (Person: Yasmine)
│   └── sentence_entropy.py
│
├── evaluation/                 Stage 4 - labeling + tables + classifier (Person: Hichem)
│   ├── label.py                verbatim port of the upstream labeling protocol
│   ├── build_table1.py         ours-vs-paper Table I + C1/C2 verdicts
│   ├── classifier.py           AUROC / F1 / ROC curves (extension)
│   ├── upstream/               reference copy of the original script + its MIT license
│   └── outputs/                COMMITTED labeled per-sentence data (3 models x 3 datasets)
│
├── integration/                Stage 5 - orchestration (Person: Ipek)
│   ├── run_pipeline.py         one-command stage chaining
│   ├── config.yaml             canonical model set + run settings
│   ├── COLAB_GUIDE.md          click-by-click GPU run manual (zero experience assumed)
│   └── colab_replication.ipynb
│
├── tools/
│   └── validate_batching.py    batched-vs-single equivalence test (negative result; batching study: Sherwan)
│
├── results/
│   ├── tables/                 replication_table1.{csv,md}, classification_metrics.csv
│   └── figures/                roc_<model>.png (3 figures)
│
├── report/                     full technical handoff report (.docx) + generator
│
└── tests/                      12 sanity checks on the committed data + results,
    ├── test_sanity.py          plus small synthetic fixtures for stage contracts
    └── test_stage_contracts.py
```

Each stage folder has its own README documenting every decision taken inside it. The five stages hand off through files on disk (see `PIPELINE_CONTRACT.md`), so they can run on different machines - generation on a Colab GPU, everything else on a laptop.

## Requirements

- **Aggregation and tests (no GPU, no model downloads):** Python 3.10-3.12 (the CI matrix: Ubuntu, Windows, macOS; Python 3.13 is not covered by CI). Needs `pandas`, `numpy`, `scikit-learn`, `matplotlib`; `pytest` for the tests (and `PyYAML` for the config check, which skips itself if absent). Checked for this README on Python 3.11.9 / pandas 3.1.0 / numpy 2.4.6 / scikit-learn 1.9.1 / matplotlib 3.11.2 / pytest 9.2.0 (Windows):

  ```bash
  pip install pandas numpy scikit-learn matplotlib pytest
  ```

- **Full generation (GPU, Stages 2-3):** additionally `torch` (install for your platform first), `transformers>=4.38,<5`, `accelerate`, `spacy` (+ `en_core_web_sm`), and `bitsandbytes` only for the optional `--load-4bit` path. Listed in `requirements.txt` as version *ranges* (only `transformers` carries a bound), not pins. The reported runs recorded `transformers 4.57.6` and `torch 2.11.0+cu128` in `run_meta.json`; the spaCy version used for the committed sentence segmentation was not recorded. The generation path is not exercised by CI.
  - `transformers` is capped `<5` as a compatibility cap (5.x was not tested here); 4.38+ is required for `output_logits=True` (raw logits).

```bash
pip install -r requirements.txt     # full generation stack; not needed for aggregation/tests
python -m spacy download en_core_web_sm
```

## Data

The three evaluation datasets are committed under `data/upstream/` (tiny, MIT-licensed, from [Mivg/fallbacks](https://github.com/Mivg/fallbacks)) - the paper's "297 samples" exactly:

| Dataset | Prompts | Answerable | Hallucination ground truth |
|---|---|---|---|
| TriviaFacts | 97 | yes | unmatched answers vs curated gold list |
| QAMPARI | 100 | yes | unmatched answers vs Wikipedia-derived gold |
| FakeQAMPARI | 100 | **no** | everything is hallucination (fabricated subjects, empty gold) |

```bash
python data/fetch_datasets.py     # validates 97/100/100, writes data/processed/replication.jsonl
```

Counts, the `\n1.` completion cue, and empty FakeQAMPARI gold lists are enforced by `assert` statements.

**Model run outputs:** the labeled per-sentence data (`evaluation/outputs/`, ~11 MB) is committed. It contains each sentence's text, label and per-token entropies, so the tables and figures in `results/` can be rebuilt without a GPU. It does **not** contain the raw completions or per-token generation records: the heavier Stage-2 outputs (~37 MB: completions, token ids, character spans) and Stage-3 outputs are git-ignored and are not in this repository. The team keeps a copy privately (zip / Google Drive); there is no public download, so anyone else must regenerate them with `integration/COLAB_GUIDE.md` (gated models, GPU) or ask the authors. Consequently Stages 2, 3 and the labeling step (`evaluation/label.py`) cannot be re-run from the committed files alone.

## Reproduce the paper

```bash
# from the repository root - regenerates every table and figure from committed data (no GPU, seconds):
python run_all.py
python run_all.py --only aggregate   # just rebuild results/ from the committed labeled outputs
python run_all.py --tests        # also run tests/ (12 sanity tests + stage-contract fixtures)
```

What this checks, and what it does not: `run_all.py` re-aggregates the **committed labeled sentences** (`evaluation/outputs/`) into `results/tables/*` and `results/figures/*`, and the tests check the committed prompts and result CSVs. It does **not** regenerate the raw model outputs, re-run labeling, or re-run any model. With the environment listed under [Requirements](#requirements) the rebuilt `replication_table1.csv/.md` and `classification_metrics.csv` were byte-identical to the committed ones; the three ROC PNGs differed byte-wise (cause not isolated; most likely the matplotlib version), so if you only wanted a check, discard the regenerated figures with `git checkout results/figures` rather than committing them. The script exits with an error (and leaves `results/` untouched) if `evaluation/outputs/` is missing, and warns if some of the three model aliases are absent.

Or with GNU Make:

```bash
make data          # validate + build the unified prompt file
make aggregate     # rebuild results/tables + results/figures from committed outputs
make tests         # run the sanity suite
make smoke         # optional: tiny end-to-end GPU/CPU pipeline test (downloads Qwen2-0.5B)
```

To regenerate the model runs themselves (GPU needed - free/Pro Colab works):

```bash
python integration/run_pipeline.py --model meta-llama/Meta-Llama-3-8B-Instruct --alias llama3-8b-instruct --dtype bfloat16
python integration/run_pipeline.py --model Qwen/Qwen2-7B-Instruct            --alias qwen2-7b-instruct  --dtype bfloat16
python integration/run_pipeline.py --model google/gemma-2-9b-it              --alias gemma2-9b-it       --dtype bfloat16
```

LLaMA-3 and Gemma-2 are gated on HuggingFace (accept the licenses + `HF_TOKEN`). Step-by-step instructions, including the disconnect-proof Google Drive setup: [`integration/COLAB_GUIDE.md`](integration/COLAB_GUIDE.md).

## Results

### Claim C1 - hallucinated > non-hallucinated entropy: CONFIRMED 9/9

Holds in every model x dataset cell, at both token and sentence level. The non-hallucinated class is `C` sentences (verified-correct answers); for FakeQAMPARI, which has no `C` sentences by construction, it is all non-`H` sentences (`R` repeats and unlabeled prose included), so those three cells compare against a broader class than the others. Full table: [`results/tables/replication_table1.md`](results/tables/replication_table1.md).

### Claim C2 - sentence-level separates better than token-level: PARTIAL 5/9

Fully holds on LLaMA-3 (3/3) and on FakeQAMPARI for every model; fails on Qwen2/Gemma-2's natural-data cells. Recomputed from the paper's printed Table I with the same rule, C2 holds in 8/9 cells (all but Gemma-2/FakeQAMPARI), so our 5/9 is a real divergence, not a property of the rule.

Definitions (our reading; the paper does not define them): there are no independent token-level hallucination labels. A token's class is the label of the sentence it belongs to; "token level" is the micro-average over all tokens of a class and "sentence level" is the macro-average of per-sentence mean entropies.

### Detection quality (our extension - the paper reports only class means)

| Model | FakeQAMPARI AUROC | QAMPARI AUROC | TriviaFacts AUROC |
|---|---|---|---|
| LLaMA-3-8B | **0.872** | 0.631 | 0.663 |
| Qwen2-7B | 0.747 | 0.528 | 0.632 |
| Gemma-2-9B | 0.780 | 0.620 | 0.627 |

Positive class = `H` sentences. The negative class differs by dataset: `C` sentences only for QAMPARI and TriviaFacts (n = 87-411), but all non-`H` sentences (`R` and unlabeled prose included; n = 794-1,275) for FakeQAMPARI, so the FakeQAMPARI column is not directly comparable with the other two (`neg_class` and `n_neg` are in `results/tables/classification_metrics.csv`). AUROC is a threshold-free ranking measure of how well sentence entropy separates these two groups of sentences; it says nothing about individual sentences being true or false. Qwen2/QAMPARI (0.528) is near chance. ROC curves: `results/figures/`.

## Scope and limits

- Sentence entropy is an **uncertainty/risk signal**: it measures how spread out the model's next-token distribution was while it wrote the sentence. In this study it is higher, on average, for sentences labeled hallucinated, under specific conditions: three open instruct models, raw-completion prompts (no chat template) that ask for lists of 25 items, greedy decoding, and the answer-matching labels below. It is **not** a factuality guarantee: AUROC ranges from 0.53 to 0.87 in the table above, and the paper itself notes that not all hallucinations occur in high-entropy sentences and some high-entropy sentences are accurate.
- Labels are a proxy. "Hallucinated" means a list item that did not match the dataset's gold answers (normalized token-LCS similarity >= 0.55); gold lists are finite, so a true answer missing from them is labeled `H`. A sentence takes the label of the answers it overlaps (our mapping, see `evaluation/README.md`). Between 23% (Gemma-2) and 38% (LLaMA-3) of generated sentences overlap no answer and are unlabeled.
- Scores need the raw per-step logits over the full vocabulary (`output_logits=True`, float32). The full-vocabulary entropy cannot be computed exactly from text alone or from an API that returns only the sampled token or top-k log-probabilities.
- The replication results cover the paper's 297 prompts and three models only; nothing here tests other tasks, prompt styles, languages or model families.

## Replication notes

Absolute values only partly match the paper (sentence level, ours vs. paper, from `results/tables/replication_table1.csv`):

- **Non-hallucinated class:** 4/9 cells are within 0.03 nats (LLaMA-3 and Qwen2, on both TriviaFacts and FakeQAMPARI; FakeQAMPARI uses the broad class). Ours is higher than the paper in 8/9 cells, by 0.10-0.29 nats on Gemma-2 (all three datasets) and on QAMPARI (all three models).
- **Hallucinated class:** ours is below the paper in 8/9 cells (by 0.02 to 0.39 nats; the largest shortfalls, 0.20-0.39, are on TriviaFacts) and above it in 1/9 (LLaMA-3/QAMPARI, +0.085). It is therefore not uniformly 0.2-0.4 nats lower.
- **Gap:** the hallucinated-minus-non-hallucinated gap is smaller than the paper's in 9/9 sentence-level cells and never inverted; on QAMPARI that comes mostly from a higher non-hallucinated mean rather than a lower hallucinated one.

The main suspects, in order: (1) the paper never states how answer-level labels become *sentence*-level labels - our mapping rule is documented in `evaluation/README.md`; (2) inference precision is unstated in the paper (we use the checkpoints' native bf16); (3) "Gemma2" size is unstated (we use 9B; Gemma-2 has the largest mean absolute deviation from the paper over the four Table I columns, 0.160, vs. 0.153 for Qwen2 and 0.082 for LLaMA-3). These are untested hypotheses. The deviation ledger is in `report/` (section 5.2) and `generation/README.md`.

One negative result worth knowing: **batched greedy decoding did not reproduce the batch-1 output** (batched-matmul rounding flips near-tie argmax choices; one of four test prompts diverged textually in bf16, per the authors' run of `tools/validate_batching.py`; that run's log is not committed). All reported runs are batch-1; `tools/validate_batching.py` reproduces the finding.

## Reproducibility

- Decoding is greedy (`do_sample=False`) with batch size 1, and no random seeds are involved in the replication path, so sampling randomness is removed. That is not a guarantee of bit-identical outputs on other hardware, drivers, library versions or dtypes: bf16 kernels can differ, and merely changing the batch size was observed to change near-tie argmax choices. The reported runs came from two different GPUs (A100 and L4); this repository contains no repeat run of the same configuration and no cross-device comparison, so exact repeatability of Stage 2 is not verified here. Aggregation from the committed labeled outputs is plain pandas/scikit-learn arithmetic (tables reproduced byte-for-byte in the environment above).
- Provenance: every run wrote `generation/outputs/<alias>/run_meta.json` (model id, dtype, GPU, library versions, timestamp). These files are git-ignored and not in this repository; the values below were read from the local git-ignored copies in the maintainer's checkout. The three reported runs: LLaMA-3 on Colab A100-40GB, Qwen2 + Gemma-2 on Colab L4, all bf16 (no quantization), transformers 4.57.6, torch 2.11.0+cu128.
- Wall-clock: ~17-28 s/prompt (512 new tokens) -> ~1.5-2.5 h per model on Colab (authors' estimate, not recorded in `run_meta.json`); aggregation from committed outputs takes seconds on any laptop.
- Tests: `python run_all.py --tests` runs `tests/`: 12 sanity assertions on the committed prompts and result CSVs (dataset integrity, C1 in all 9 cells, entropy ranges, AUROC bounds, near-match cells, figure presence) plus small synthetic fixtures for the stage contracts (`tests/test_stage_contracts.py`: Stage 3 token alignment and validation, Stage 4 labeling rules, missing-input handling, config.yaml parsing). They do not re-run any model.

## Citation

If you use this code or these results, please cite both the original paper and this replication:

```bibtex
@inproceedings{joo2025entropy,
  author    = {Joo, Eojin and Lee, Young-Jun and Choi, Ho-Jin},
  title     = {Entropy-based Sentence-level Hallucination Score in Large Language Models},
  booktitle = {2025 IEEE International Conference on Big Data and Smart Computing (BigComp)},
  pages     = {77--78},
  year      = {2025},
  doi       = {10.1109/BigComp64353.2025.00022}
}

@misc{halluscope2026,
  author = {Ali, Sherwan and Ucar, Ipek and Sevinc Aldogan, Yaprak and Guidoum, Yasmine and Guidoum, Abdenour Hichem},
  title  = {HalluScope: Faithful Replication of the Entropy-based Sentence-level Hallucination Score},
  year   = {2026},
  note   = {University course project (SE418); code MIT, documentation and results CC-BY 4.0},
  url    = {https://github.com/SherwanAli0/HalluScope}
}
```

A `CITATION.cff` is provided so GitHub renders a "Cite this repository" button automatically.

## License

This repository is dual-licensed:

- Source code (Python files, notebook, Makefile, configs): [MIT License](LICENSE).
- Documentation, results CSVs, figures, reports, and research notes: [CC-BY 4.0](LICENSE).
- The upstream datasets and reference script (`data/upstream/`, `evaluation/upstream/`) remain under the Ivgi et al. MIT license (`evaluation/upstream/LICENSE`).
- The original IEEE paper PDF is included for academic reference under fair-use quotation and is the copyright of its authors and IEEE; if the publisher requires its removal, open an issue and it will be replaced with a link.

## Contributing

Bug reports, replication-hypothesis additions, and test-coverage improvements are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Acknowledgements

- Joo, Lee, and Choi for the method specification we replicated.
- Ivgi, Yoran, Berant, and Geva for the datasets and labeling protocol (github.com/Mivg/fallbacks).
- Meta, Alibaba/Qwen, and Google for the open-weight models; HuggingFace for transformers.
- spaCy (Honnibal & Montani) for sentence segmentation.
