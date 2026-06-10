# Changelog

All notable changes to this repository are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/), and the project uses simple `MAJOR.MINOR.PATCH` versions.

## [1.0.0] — 2026-06-10

The complete faithful replication, implemented and run end-to-end in a single day.

### Added
- **Stage 1 (`data/`):** `fetch_datasets.py` — downloads and validates the paper's exact 297 prompts (97/100/100) from the upstream Mivg/fallbacks repository (MIT); byte-identical copies committed under `data/upstream/`.
- **Stage 2 (`generation/`):** `generate.py` — raw completion prompting (no chat template), greedy decoding, 512 new tokens, RAW per-step logits via `output_logits=True` (transformers >= 4.38 asserted), per-token Shannon entropy in float32 nats + chosen-token logprob, character spans via cumulative-prefix decoding, per-prompt append/flush with automatic resume, `run_meta.json` provenance.
- **Stage 3 (`entropy/`):** `sentence_entropy.py` — spaCy sentence segmentation, max-overlap token-to-sentence assignment, paper Eq. 2 (plain mean), EOS/whitespace exclusions with audit counters.
- **Stage 4 (`evaluation/`):** `label.py` — verbatim port of the upstream extraction/normalization/greedy-LCS(0.55)/first-occurrence labeling protocol with attribution; answer-span mapping (100% mapped in all runs); `build_table1.py` (ours-vs-paper Table I + C1/C2 verdicts); `classifier.py` (AUROC/F1/ROC extension).
- **Stage 5 (`integration/`):** `run_pipeline.py` orchestrator, `config.yaml`, `colab_replication.ipynb`, and `COLAB_GUIDE.md` (click-by-click GPU manual incl. gated-model licenses, Colab Secrets, and the Drive-symlink disconnect protection).
- **Results:** all three paper models run on the full 297 prompts in native bf16, batch 1 (LLaMA-3-8B-Instruct on A100; Qwen2-7B-Instruct and Gemma-2-9B-it on L4). Committed: labeled per-sentence outputs (`evaluation/outputs/`), `results/tables/replication_table1.{csv,md}`, `results/tables/classification_metrics.csv`, three ROC figures. Headline: C1 confirmed 9/9; LLaMA-3/FakeQAMPARI matches the paper within ~0.02 nats on both classes.
- **Tooling:** `tools/validate_batching.py` — batched-vs-single equivalence test that produced the negative result (batched greedy is non-deterministic; all reported runs batch-1).
- **Tests + CI:** 12-test sanity suite (`tests/test_sanity.py`) over committed datasets and result CSVs; GitHub Actions workflow on 3 OSes x Python 3.10-3.12.
- **Docs + governance:** per-stage READMEs with decision logs; root README in ours-vs-paper replication format; `PIPELINE_CONTRACT.md`; `RESULTS_SUMMARY.md`; full technical handoff report (`report/HalluScope_Replication_Handoff_Report.docx` + generator); dual MIT/CC-BY-4.0 `LICENSE`; `CITATION.cff`; `CONTRIBUTORS.md` (CRediT); `CONTRIBUTING.md`; `SECURITY.md`; `BRANCHING.md`; issue/PR templates; `CODEOWNERS`; `.editorconfig`.

### Fixed
- Pinned `transformers>=4.38,<5` (5.x requires a newer torch than the pinned 2.5.1; 4.38+ needed for raw logits).
- Gemma-2 fp16 breakage avoided via bf16 + eager attention (handled automatically in `generate.py`).

### Known limitations (documented, intentional)
- Hallucinated-class means run ~0.2-0.4 nats below the paper's (compressed gap; candidate causes in README "Replication notes" and report §8.5).
- The paper's model sizes/variants are unstated; ours are documented assumptions (deviation ledger).
- Per-token generation outputs (~37 MB) are not committed; regenerate via the Colab guide or use the team zip/Drive.

## [0.1.0] — 2026-04-18

### Added
- Initial repository scaffold: five-stage folder structure (`data/`, `generation/`, `entropy/`, `evaluation/`, `integration/`, `results/`, `report/`) with `.gitkeep` placeholders, initial README, and per-member branches (`Ipek`, `Yaprak`, `Sherwan`, `Yasmine`, `Hichem`).
