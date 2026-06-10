# Stage 1 - Dataset Preparation

**What this module does:** downloads and validates the exact 297 evaluation
prompts used by the base paper, and converts them to HalluScope's unified
format.

## Why these datasets

Joo et al. (2025) write that their experiment uses *"three datasets - QAMPARI,
FAKEQAMPARI, and TriviaFacts - comprising 297 samples, following the setup
from [9]"*, where [9] is Ivgi et al. (2024), *From Loops to Oops* (arXiv:2407.06071).
The official repository of that paper - <https://github.com/Mivg/fallbacks>
(MIT license) - contains the literal dataset files, and their sizes add up
exactly:

| Upstream file | Our name | Prompts | Answerable? |
|---|---|---|---|
| `data/trivia_facts.jsonl` | `trivia_facts` | 97 | yes |
| `data/qampari_rephrased.jsonl` | `qampari` | 100 | yes |
| `data/fake_qampari.jsonl` | `fake_qampari` | 100 | **no** (gold lists empty by construction - subjects are fabricated entities, so every produced answer is a hallucination) |
| | | **297** | |

Using the identical files means our replication runs on **the same inputs and
the same ground-truth protocol** as the base paper - not a reconstruction.

## Format details (important for faithfulness)

- Every prompt is a completion-style list request, e.g.
  `"The following 25 fingers are part of the human hand\n1."` - the `\n1.`
  cue is **part of the prompt** and the model continues the list.
- Prompts are fed to the model **verbatim, with no chat template**, matching
  the upstream generation script (`run_hallucinations_check.py`), which uses
  raw text-completion for base *and* instruct models.
- The "25" in every prompt is deliberate upstream design: it asks for more
  answers than truly exist, pushing models beyond their knowledge.

## Files

- `fetch_datasets.py` - downloads upstream files into `upstream/`, validates
  counts (97/100/100), the `\n1.` suffix, and empty gold lists for
  `fake_qampari`, then writes the unified file.
- `upstream/` - byte-identical copies of the three upstream dataset files.
- `processed/replication.jsonl` - unified format, one record per prompt:

```json
{"id": "qampari_007", "dataset": "qampari", "prompt": "...\n1.",
 "gold_answers": ["..."], "answerable": true}
```

## How to run

```
py -3.11 data/fetch_datasets.py          # idempotent; --force re-downloads
```

Run from the repository root. Output lands in `data/processed/replication.jsonl`
(297 lines). All downstream stages read only that file.
