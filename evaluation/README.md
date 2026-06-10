# Stage 4 - Labeling & Evaluation

**What this module does:** labels every generated answer and sentence as
CORRECT / HALLUCINATION / REPETITION using the *exact protocol the base paper
inherited*, then builds the replication's headline artifact - our version of
the paper's Table I - plus classification metrics the paper doesn't report.

## Files

| File | Role |
|---|---|
| `label.py` | Verbatim port of the upstream labeling rules + sentence labeling |
| `build_table1.py` | Replication Table I, side-by-side with the paper's printed values, C1/C2 claim verdicts |
| `classifier.py` | **Extension** (objective 4): precision/recall/F1/AUC-ROC + ROC curves from sentence entropy |
| `upstream/run_hallucinations_check.py` | Reference copy of the original Ivgi et al. (2024) script the port follows (MIT, see `upstream/LICENSE`) |

## The labeling protocol (ported, not reinvented)

Joo et al. (2025) follow the setup of Ivgi et al. (2024). The functions in
`label.py` (`extract_answers`, `normalize_answer`, `greedy_match`, …) are
ported **verbatim** from the upstream `run_hallucinations_check.py` - quirks
included, because "fixing" them would change the ground truth labels:

1. Parse up to **25 enumerated answers** from the completion (regex; handles
   one-line lists, CSV-style lists, template divergence, `\n\n` cutoffs).
2. **Normalize**: lowercase → strip trailing parenthetical → remove
   punctuation → remove articles (a/an/the) → collapse whitespace.
3. **Greedy matching** of predictions to gold answers by token-level
   normalized LCS similarity, threshold **0.55** → matched = `CORRECT`.
4. First occurrence of an unmatched answer = `HALLUCINATION`; later
   duplicates of an already-seen normalized answer = `REPETITION`.
5. `fake_qampari` has empty gold lists (fabricated subjects) → every unique
   answer is `HALLUCINATION` **by construction**.

## Answer → sentence mapping (documented choice)

The upstream protocol labels *answers* (list items); the paper scores
*sentences*. The paper never states the mapping, so ours is explicit:

- each labeled answer is located in the completion (sequential string
  search; the mapped fraction is printed - unmapped answers just leave their
  sentences unlabeled);
- a sentence is **H** if it overlaps ≥1 hallucinated answer; else **C** if it
  overlaps ≥1 correct answer; else **R** if it overlaps only repetitions;
- sentences touching no labeled answer (prose, refusals, degenerate tails)
  stay **unlabeled**.

Since completions are enumerated lists and spaCy splits them per item, in
practice ≈1 answer ↔ 1 sentence.

## Table I definitions

- **Token level** = micro average (mean over all tokens of the class's
  sentences). **Sentence level** = macro average (mean of sentence means).
  The paper doesn't define this precisely; this is the natural reading and is
  flagged as an interpretation.
- **Non-hallucinated class**: `strict` = C sentences only. For
  `fake_qampari` no C sentences can exist, yet the paper still reports a
  Non-hallucinate column - the only consistent reading is `broad` = all
  non-H sentences, which we use there (marked `*` in the table). Both
  definitions are in the CSV.

## Claim verdicts produced

- **C1** - hallucinated sentences have higher entropy than non-hallucinated
  (token AND sentence level), per model × dataset.
- **C2** - the class gap is larger at sentence level than token level
  (the paper's headline argument for sentence-level scoring).

## How to run

```
py -3.11 evaluation/label.py        --alias <alias>
py -3.11 evaluation/build_table1.py --aliases <alias1> <alias2> ...
py -3.11 evaluation/classifier.py   --aliases <alias1> <alias2> ...
```

Outputs land in `evaluation/outputs/<alias>/`, `results/tables/`, and
`results/figures/`.
