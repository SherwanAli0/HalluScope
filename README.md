# HalluScope

**SE418: Large Language Models — Group Project**
Üsküdar University, Computer Engineering

A benchmarking framework that measures hallucination rates across open-source LLMs using entropy-based detection. Reproduces and extends Joo, Lee & Choi (2025) *"Entropy-based Sentence-level Hallucination Score in Large Language Models"* (IEEE BigComp 2025).

---

## Research Question

> Does sentence-level entropy-based hallucination detection generalize across open-source LLMs and domains?

---

## Models Evaluated

| Model | Size | Source |
|---|---|---|
| LLaMA-3 | 8B | Meta / HuggingFace |
| Mistral | 7B | Mistral AI / HuggingFace |
| Gemma | 2B | Google / HuggingFace |
| Phi-3 | ~3.8B | Microsoft / HuggingFace |

---

## Datasets

| Dataset | Type |
|---|---|
| TruthfulQA | General knowledge, factual Q&A |
| HaluEval | Labeled hallucination examples |

---

## Pipeline

```
Stage 1 — Data Preparation   →   data/
Stage 2 — Generation          →   generation/
Stage 3 — Entropy Scoring     →   entropy/
Stage 4 — Evaluation          →   evaluation/
Stage 5 — Integration         →   integration/
```

Each stage reads from and writes to disk so team members can work in parallel.

---

## Repository Structure

```
HalluScope/
├── data/               # Dataset loading and formatting (Person 1)
├── generation/         # Model inference + logit saving (Person 2)
├── entropy/            # Entropy computation module (Person 3)
├── evaluation/         # Classifier, metrics, plots (Person 4)
├── integration/        # Pipeline runner + failure analysis (Person 5)
├── results/
│   ├── figures/        # ROC curves, entropy plots
│   └── tables/         # Comparison tables (CSV)
└── report/             # Final written report
```

---

## Core Formula

Token-level entropy for predicted token `y_i` given context `c_i`:

```
H(y_i | c_i) = - Σ  p(y_i = v | c_i) · log p(y_i = v | c_i)
```

Sentence-level entropy (average over all tokens in sentence `Sen_j` of length `N_j`):

```
H(Sen_j) = (1 / N_j) · Σ  H(y_k | c_k)
```

Higher entropy → greater model uncertainty → higher hallucination risk.

---

## Extensions Beyond the Base Paper

- 4 models (base paper tested 3: LLaMA-3, Qwen2, Gemma2)
- Different datasets: TruthfulQA + HaluEval (base paper used QAMPARI, FAKEQAMPARI, TriviaFacts)
- Full classification metrics: precision, recall, F1, AUC-ROC (base paper reports averages only)
- Systematic failure analysis: cases where entropy-based detection succeeds and fails
- Cross-model comparison of detection performance

---

## Team

| Role | Responsibility |
|---|---|
| Person 1 — Dataset Lead | Download TruthfulQA + HaluEval, unified JSON format |
| Person 2 — Generation Lead | Run all 4 models with `output_scores=True`, save logits |
| Person 3 — Entropy Module | Implement token + sentence entropy from logits |
| Person 4 — Evaluation Module | Threshold classifier, F1, AUC-ROC, plots |
| Person 5 — Integration | Pipeline runner, failure analysis, final report, GitHub |

---

## Base Paper

> Eojin Joo, Young-Jun Lee, Ho-Jin Choi.
> *Entropy-based Sentence-level Hallucination Score in Large Language Models.*
> IEEE BigComp 2025. DOI: 10.1109/BigComp64353.2025.00022
