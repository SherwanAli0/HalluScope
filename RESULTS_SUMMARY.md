# Results summary

One-page overview of the replication results. Full numbers: [`results/tables/replication_table1.md`](results/tables/replication_table1.md) and [`results/tables/classification_metrics.csv`](results/tables/classification_metrics.csv). Full analysis: `report/HalluScope_Replication_Handoff_Report.docx` §8.

**Setup.** 3 models (LLaMA-3-8B-Instruct, Qwen2-7B-Instruct, Gemma-2-9B-it) x 3 datasets (TriviaFacts 97, QAMPARI 100, FakeQAMPARI 100 - the paper's exact 297 prompts) x 512 greedy tokens, native bf16, batch 1. Sentence score = mean token entropy (paper Eq. 2), in nats.

## Table I replication (sentence-level, ours / paper)

| Dataset | Model | Non-halluc. | Halluc. | C1 |
|---|---|---|---|---|
| TriviaFacts | LLaMA-3-8B | 0.2436 / 0.2203 | 0.3946 / 0.5944 | ✓ |
| TriviaFacts | Qwen2-7B | 0.4494 / 0.4239 | 0.6098 / 1.0027 | ✓ |
| TriviaFacts | Gemma-2-9B | 0.2989 / 0.1919 | 0.4095 / 0.6745 | ✓ |
| QAMPARI | LLaMA-3-8B | 0.3907 / 0.2243 | 0.5834 / 0.4988 | ✓ |
| QAMPARI | Qwen2-7B | 0.7016 / 0.4125 | 0.7627 / 0.8114 | ✓ |
| QAMPARI | Gemma-2-9B | 0.4043 / 0.1964 | 0.5488 / 0.6020 | ✓ |
| FakeQAMPARI* | LLaMA-3-8B | **0.1460 / 0.1416** | **0.6109 / 0.6312** | ✓ |
| FakeQAMPARI* | Qwen2-7B | **0.4355 / 0.4452** | 0.8980 / 1.0613 | ✓ |
| FakeQAMPARI* | Gemma-2-9B | 0.2992 / 0.1454 | 0.7189 / 0.7789 | ✓ |

\* FakeQAMPARI has no CORRECT sentences by construction; non-hallucinated = all non-H sentences (broad). Bold = near-exact match to the paper.

## Verdicts

- **C1 (hallucinated > non-hallucinated): CONFIRMED 9/9** - at sentence AND token level, ours and the paper's printed values alike.
- **C2 (sentence gap > token gap): PARTIAL 5/9** - LLaMA-3 3/3, FakeQAMPARI 3/3; fails on Qwen2/Gemma-2 natural-data cells.
- **C3 (absolute values): PARTIAL** - non-hallucinated class matches closely (several cells within 0.01-0.03 nats); hallucinated class runs ~0.2-0.4 nats below the paper everywhere (compressed gap, never inverted). Candidate causes: the paper's unstated answer→sentence label mapping; unstated inference precision; unstated "Gemma2" size.

## Detection quality (extension - AUROC, positive class = hallucinated)

| Model | FakeQAMPARI | QAMPARI | TriviaFacts |
|---|---|---|---|
| LLaMA-3-8B | **0.872** | 0.631 | 0.663 |
| Qwen2-7B | 0.747 | 0.528 | 0.632 |
| Gemma-2-9B | 0.780 | 0.620 | 0.627 |

Entropy detects fabricated-entity hallucinations well; on natural multi-answer questions many hallucinations are produced confidently - quantifying the paper's own "entropy alone is not enough" caveat. (F1 values in the CSV are inflated by class imbalance; AUROC is the meaningful number. Qwen2/QAMPARI rests on only 87 strict-correct sentences.)

## Run statistics

| Model | GPU | Sentences | C | H | R | unlabeled | answer spans mapped |
|---|---|---|---|---|---|---|---|
| LLaMA-3-8B | A100 40GB | 9,881 | 533 | 4,392 | 1,154 | 3,802 | 6,656/6,656 (100%) |
| Qwen2-7B | L4 24GB | 8,381 | 455 | 4,738 | 667 | 2,521 | 100% |
| Gemma-2-9B | L4 24GB | 8,853 | 624 | 5,858 | 330 | 2,041 | 100% |

Negative result worth remembering: batched greedy decoding is **non-deterministic** (near-tie argmax flips under batched-matmul rounding) - all reported runs are batch-1 (`tools/validate_batching.py`).
