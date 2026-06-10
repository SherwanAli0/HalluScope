# Stage 3 - Sentence-Level Entropy (Eq. 2)

**What this module does:** turns Stage 2's per-token entropies into the
paper's sentence-level hallucination score.

## The formulas being replicated

Token-level (paper Eq. 1, computed in Stage 2 from raw logits):

```
H(y_i | c_i) = − Σ_v  p(y_i = v | c_i) · log p(y_i = v | c_i)      [nats]
```

Sentence-level (paper Eq. 2, computed here):

```
H(Sen_j) = (1 / N_j) · Σ_{k ∈ Sen_j}  H(y_k | c_k)
```

i.e. the **plain mean** of token entropies within the sentence - no
weighting, no filtering. That is exactly what this module computes.

## Sentence splitting

spaCy `en_core_web_sm` (the paper says only "SpaCy", so the pipeline/version
is pinned here and reported: see root `requirements.txt`). The completions
are enumerated lists ("1. X\n2. Y"), which spaCy segments line-by-line in
practice - each list item becomes its own sentence, which is what makes
per-item hallucination labels (Stage 4) line up with sentences.

## Token→sentence assignment (documented choice)

The paper never specifies how generated *tokens* map to spaCy *sentences*.
Our rule, applied to the character spans produced in Stage 2:

1. token → the sentence its span **overlaps most**;
2. zero-width tokens (partial UTF-8 bytes) → sentence containing their position;
3. **special tokens (EOS) excluded** from all averages;
4. tokens overlapping **no** sentence (pure inter-sentence whitespace, e.g.
   the lone `\n` between list items) are excluded - Eq. 2 sums over tokens
   *"within a sentence"*.

The script prints how many tokens each rule dropped, so the effect is
auditable (typically only whitespace/EOS tokens).

## Outputs

`outputs/<alias>/<dataset>.jsonl` - one line per prompt:

```json
{"id": "qampari_007", "dataset": "qampari", "sentences": [
  {"idx": 0, "text": "Crying Freeman", "start": 0, "end": 14,
   "n_tokens": 5, "mean_entropy": 0.8341,
   "token_entropies": [..], "mean_logprob": -0.42}]}
```

`token_entropies` is kept per sentence so Stage 4 can compute the paper's
**token-level** Table I columns (micro-average over all tokens of a class)
alongside the **sentence-level** columns (macro-average of sentence means).
`mean_logprob` is extra signal for failure analysis - not used in the
replication tables.

## How to run

```
py -3.11 entropy/sentence_entropy.py --alias <alias>
```

Reads `generation/outputs/<alias>/*.jsonl`, writes `entropy/outputs/<alias>/`.
