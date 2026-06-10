# Contributing

Thanks for your interest in this paper-replication repository. This is a course-project artefact, but contributions that improve reproducibility, documentation, or test coverage are welcome.

## Ground rules

1. **Faithfulness to the paper is paramount.** The replication path (greedy batch-1 decoding, raw-logit entropy in float32 nats, the verbatim-ported labeling protocol, Eq. 2 plain-mean aggregation) implements only what the paper and its upstream protocol specify. Hypotheses, tweaks, and "what if" experiments belong in separate scripts/aliases clearly labeled as extensions.
2. **C1 is the algorithm-correctness check.** Any change after which hallucinated sentences no longer carry higher entropy than non-hallucinated ones in all 9 model x dataset cells (`tests/test_sanity.py`) is a regression and will be rejected.
3. **Batch-1 is non-negotiable for reported numbers.** Batched greedy decoding is non-deterministic (see `tools/validate_batching.py` and README "Replication notes"). `--batch-size > 1` is for throwaway experiments only.
4. **Source-citation rule.** Every algorithmic block must cite its source: the paper's equation number (e.g. `paper Eq. 2`), the upstream script (`run_hallucinations_check.py`, kept at `evaluation/upstream/`), or library docs. The labeling port must stay verbatim — including its quirks; "fixing" upstream behaviour breaks faithfulness.

## How to propose a change

1. **Open an issue first.** Describe the problem, paste the smallest reproducible example, and reference the paper section / equation or contract interface (`PIPELINE_CONTRACT.md`) that motivates the change.
2. **Branch + PR.** Branch off `main` (see `BRANCHING.md`), keep one logical change per PR. Reference the issue.
3. **Run the tests.** Before opening a PR, run `python run_all.py --tests` (or `make tests`). All 12 assertions must pass.
4. **Update the stage README** if the change affects decisions documented there, and `PIPELINE_CONTRACT.md` if an interface changes.

## What we accept

- Documentation fixes (typos, broken links, clarifications).
- Failure-analysis additions (e.g. quantifying label noise in the inherited protocol, analyzing the unlabeled-prose sentences).
- Test cases that strengthen the sanity-check coverage.
- Cross-platform fixes (Linux, macOS, Windows, Colab compatibility).
- Performance improvements that produce identical numbers (verified by tests — and remember the batching lesson).

## What we do NOT accept

- Changes to the replication semantics without a paper-text justification.
- Novelty extensions (content-weighted entropy, multi-signal fusion, new datasets/models) merged into the replication path — these are planned as clearly-separated Part B / Part C work; keep them behind their own aliases, configs, and result files.
- Edits to `data/upstream/` or `evaluation/upstream/` — these are byte-faithful copies of the published protocol.

## Code style

- Python 3.10+ syntax. Type hints where useful, not mandatory.
- Docstrings cite paper equations (`paper Eq. 1`) or upstream sources as URLs/filenames.
- One concept per function; no "kitchen-sink" helpers.
- 4-space indent, no tabs. UTF-8 encoded files. LF line endings (see `.editorconfig`).

## Questions?

Open an issue or contact the authors listed in `CITATION.cff`.
