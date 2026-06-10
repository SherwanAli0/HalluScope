# Replication of "Entropy-based Sentence-level Hallucination Score in Large Language Models"

[![tests](https://github.com/SherwanAli0/HalluScope/actions/workflows/tests.yml/badge.svg)](https://github.com/SherwanAli0/HalluScope/actions/workflows/tests.yml)
[![License: MIT + CC-BY 4.0](https://img.shields.io/badge/license-MIT%20%2B%20CC--BY%204.0-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests passing](https://img.shields.io/badge/tests-12%20passing-brightgreen.svg)](tests/)
[![Paper](https://img.shields.io/badge/IEEE%20BigComp-10.1109%2FBigComp64353.2025.00022-darkblue.svg)](https://ieeexplore.ieee.org/document/10936832)

> **Original paper.** E. Joo, Y.-J. Lee, H.-J. Choi. *Entropy-based Sentence-level Hallucination Score in Large Language Models.* IEEE BigComp 2025, pp. 77 to 78. [DOI: 10.1109/BigComp64353.2025.00022](https://ieeexplore.ieee.org/document/10936832)

## Abstract

This repository is an independent paper-faithful replication of the entropy-based sentence-level hallucination score introduced by Joo et al. The method computes the Shannon entropy of the model's full-vocabulary token distribution at every generation step (paper Eq. 1) and averages it over the tokens of each spaCy-split sentence (Eq. 2); higher sentence entropy signals hallucination risk. We rebuilt the method from the paper text alone (no official code exists — we verified), recovered the paper's exact 297 evaluation prompts and labeling protocol from the upstream repository it cites (Ivgi et al. 2024, github.com/Mivg/fallbacks), and ran all three paper models — LLaMA-3-8B-Instruct, Qwen2-7B-Instruct, Gemma-2-9B-it — in native bf16, greedy, 512 new tokens, batch 1. The paper's central claim reproduces 9/9: hallucinated sentences carry higher entropy than non-hallucinated ones in every model x dataset cell, at both token and sentence level. On FakeQAMPARI, LLaMA-3 matches the paper's printed values to within ~0.02 nats on both classes (0.146/0.611 vs 0.142/0.631).

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
| Ipek Ucar (Team Leader) | [@ipekucr](https://github.com/ipekucr) | Uskudar University |
| Yaprak Sevinc Aldogan | [@YaprakSevincAldogan](https://github.com/YaprakSevincAldogan) | Uskudar University |
| Sherwan Ali | [@SherwanAli0](https://github.com/SherwanAli0) | Uskudar University |
| Yasmine Guidoum | [@Dandyyass](https://github.com/Dandyyass) | Uskudar University |
| Abdenour Hichem Guidoum | — | Uskudar University |

Per-contribution roles are listed in [CONTRIBUTORS.md](CONTRIBUTORS.md). University course project (SE418: Large Language Models), 2026.

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
├── data/                       Stage 1 — the paper's exact 297 prompts (Person: Yaprak)
│   ├── fetch_datasets.py       download + validate + unify
│   └── upstream/               byte-identical files from Mivg/fallbacks (MIT)
│
├── generation/                 Stage 2 — greedy generation + RAW logit entropy (Person: Sherwan)
│   └── generate.py             output_logits=True, fp32 nats, char spans, resumable
│
├── entropy/                    Stage 3 — spaCy sentences + Eq. 2 (Person: Yasmine)
│   └── sentence_entropy.py
│
├── evaluation/                 Stage 4 — labeling + tables + classifier (Person: Hichem)
│   ├── label.py                verbatim port of the upstream labeling protocol
│   ├── build_table1.py         ours-vs-paper Table I + C1/C2 verdicts
│   ├── classifier.py           AUROC / F1 / ROC curves (extension)
│   ├── upstream/               reference copy of the original script + its MIT license
│   └── outputs/                COMMITTED labeled per-sentence data (3 models x 3 datasets)
│
├── integration/                Stage 5 — orchestration (Person: Ipek)
│   ├── run_pipeline.py         one-command stage chaining
│   ├── config.yaml             canonical model set + run settings
│   ├── COLAB_GUIDE.md          click-by-click GPU run manual (zero experience assumed)
│   └── colab_replication.ipynb
│
├── tools/
│   └── validate_batching.py    batched-vs-single equivalence test (negative result)
│
├── results/
│   ├── tables/                 replication_table1.{csv,md}, classification_metrics.csv
│   └── figures/                roc_<model>.png (3 figures)
│
├── report/                     full technical handoff report (.docx) + generator
│
└── tests/                      12 sanity checks on the committed data + results
    └── test_sanity.py
```

Each stage folder has its own README documenting every decision taken inside it. The five stages hand off through files on disk (see `PIPELINE_CONTRACT.md`), so they can run on different machines — generation on a Colab GPU, everything else on a laptop.

## Requirements

- Python 3.10 to 3.13.
- Aggregation/tests only (no GPU): `pandas`, `numpy`, `scikit-learn`, `matplotlib`.
- Full generation additionally needs: `torch`, `transformers>=4.38,<5`, `accelerate`, `spacy` (+ `en_core_web_sm`). Pinned in `requirements.txt`.
  - `transformers` is capped `<5`: v5 requires a newer torch, and 4.38+ is required for `output_logits=True` (raw logits).
- Optional: `pytest` for the test suite.

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Data

The three evaluation datasets are committed under `data/upstream/` (tiny, MIT-licensed, from [Mivg/fallbacks](https://github.com/Mivg/fallbacks)) — the paper's "297 samples" exactly:

| Dataset | Prompts | Answerable | Hallucination ground truth |
|---|---|---|---|
| TriviaFacts | 97 | yes | unmatched answers vs curated gold list |
| QAMPARI | 100 | yes | unmatched answers vs Wikipedia-derived gold |
| FakeQAMPARI | 100 | **no** | everything is hallucination (fabricated subjects, empty gold) |

```bash
python data/fetch_datasets.py     # validates 97/100/100, writes data/processed/replication.jsonl
```

Counts, the `\n1.` completion cue, and empty FakeQAMPARI gold lists are enforced by `assert` statements.

**Model run outputs:** the labeled per-sentence data (`evaluation/outputs/`, ~11 MB) is committed, so all tables and figures can be regenerated without a GPU. The heavier per-token generation outputs (~37 MB) are not in git — regenerate them via `integration/COLAB_GUIDE.md`, or take them from the team's complete zip / Drive folder (`MyDrive/halluscope_out`).

## Reproduce the paper

```bash
# from the repository root — regenerates every table and figure from committed data (no GPU, seconds):
python run_all.py
python run_all.py --tests        # also run the 12-test sanity suite
```

Or with GNU Make:

```bash
make data          # validate + build the unified prompt file
make aggregate     # rebuild results/tables + results/figures from committed outputs
make tests         # run the sanity suite
make smoke         # optional: tiny end-to-end GPU/CPU pipeline test (downloads Qwen2-0.5B)
```

To regenerate the model runs themselves (GPU needed — free/Pro Colab works):

```bash
python integration/run_pipeline.py --model meta-llama/Meta-Llama-3-8B-Instruct --alias llama3-8b-instruct --dtype bfloat16
python integration/run_pipeline.py --model Qwen/Qwen2-7B-Instruct            --alias qwen2-7b-instruct  --dtype bfloat16
python integration/run_pipeline.py --model google/gemma-2-9b-it              --alias gemma2-9b-it       --dtype bfloat16
```

LLaMA-3 and Gemma-2 are gated on HuggingFace (accept the licenses + `HF_TOKEN`). Step-by-step instructions, including the disconnect-proof Google Drive setup: [`integration/COLAB_GUIDE.md`](integration/COLAB_GUIDE.md).

## Results

### Claim C1 — hallucinated > non-hallucinated entropy: CONFIRMED 9/9

Holds in every model x dataset cell, at both token and sentence level. Full table: [`results/tables/replication_table1.md`](results/tables/replication_table1.md).

### Claim C2 — sentence-level separates better than token-level: PARTIAL 5/9

Fully holds on LLaMA-3 (3/3) and on FakeQAMPARI for every model; fails on Qwen2/Gemma-2's natural-data cells. An honest nuance the 2-page paper could not surface.

### Detection quality (our extension — the paper reports only class means)

| Model | FakeQAMPARI AUROC | QAMPARI AUROC | TriviaFacts AUROC |
|---|---|---|---|
| LLaMA-3-8B | **0.872** | 0.631 | 0.663 |
| Qwen2-7B | 0.747 | 0.528 | 0.632 |
| Gemma-2-9B | 0.780 | 0.620 | 0.627 |

Entropy detects *fabricated-entity* hallucinations well and struggles on natural multi-answer questions — quantifying exactly where the paper's own "entropy alone is not enough" caveat bites. ROC curves: `results/figures/`.

## Replication notes

The faithful implementation reproduces the paper's *non-hallucinated* class means closely (several cells within 0.01–0.03 nats) while our *hallucinated* class means run ~0.2–0.4 nats below the paper's throughout — the separation gap is compressed, though never inverted. The main suspects, in order: (1) the paper never states how answer-level labels become *sentence*-level labels — our mapping rule is documented in `evaluation/README.md`; (2) inference precision is unstated in the paper (we use the checkpoints' native bf16); (3) "Gemma2" size is unstated (we use 9B; Gemma is our most deviant model). All seven forced assumptions are listed in the deviation ledger (`generation/README.md`, `report/`).

One negative result worth knowing: **batched greedy decoding is not deterministic** (batched-matmul rounding flips near-tie argmax choices; one of four test prompts diverged textually in bf16). All reported runs are batch-1; `tools/validate_batching.py` reproduces the finding.

## Reproducibility

- Decoding is greedy (`do_sample=False`) with batch size 1 — fully deterministic per model + prompt; no random seeds are involved anywhere in the replication path.
- Provenance: every run wrote `generation/outputs/<alias>/run_meta.json` (model id, dtype, GPU, library versions, timestamp). The three reported runs: LLaMA-3 on Colab A100-40GB, Qwen2 + Gemma-2 on Colab L4, all bf16, transformers 4.57.6.
- Wall-clock: ~17–28 s/prompt (512 new tokens) → ~1.5–2.5 h per model on Colab; aggregation from committed outputs takes seconds on any laptop.
- Tests: `python run_all.py --tests` runs 12 sanity assertions on the committed prompts and result CSVs (dataset integrity, C1 in all 9 cells, entropy ranges, AUROC bounds, near-match cells, figure presence). All 12 pass on the committed results.

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
  author = {Ucar, Ipek and Sevinc Aldogan, Yaprak and Ali, Sherwan and Guidoum, Yasmine and Guidoum, Abdenour Hichem},
  title  = {HalluScope: Faithful Replication of the Entropy-based Sentence-level Hallucination Score},
  year   = {2026},
  note   = {University course project (SE418), MIT-licensed},
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
