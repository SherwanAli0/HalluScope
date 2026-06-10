# Pipeline contract

The binding interfaces between the five stages. Every stage reads and writes ONLY these files, so stages can run on different machines (generation on a Colab GPU, everything else on a laptop) and team members can work independently. Changing any interface requires updating this document, the affected stage READMEs, and the tests in the same PR.

## §1 Stage 1 → Stage 2: the unified prompt file

`data/processed/replication.jsonl` — one JSON object per line, 297 lines exactly:

```json
{"id": "qampari_007",            // "<dataset>_<zero-padded index>"
 "dataset": "qampari",           // trivia_facts | qampari | fake_qampari
 "prompt": "The following 25 manga were drawn by Ryoichi Ikegami:\n1.",
 "gold_answers": ["Heat", "..."],// [] for fake_qampari (unanswerable)
 "answerable": true}
```

Invariants (enforced by `assert` in `fetch_datasets.py` and tests 1-4):
- counts: trivia_facts=97, qampari=100, fake_qampari=100 (total 297);
- every prompt ends with the completion cue `\n1.`;
- `fake_qampari` gold lists are all empty.

## §2 Stage 2 → Stage 3: generation outputs

`generation/outputs/<alias>/<dataset>.jsonl` — one line per prompt:

```json
{"id": "...", "dataset": "...", "prompt": "...", "completion": "...",
 "tokens": [{"token_id": 123,
             "entropy": 0.413200,   // Shannon entropy, FULL vocab, fp32, nats
             "logprob": -0.210000,  // log-prob of the chosen token (extension data)
             "span": [0, 4],        // char span in `completion` (zero-width allowed)
             "special": false}]}    // EOS/pad etc. — excluded downstream
```

plus `run_meta.json` (model id, dtype, quantization, batch size, decoding,
library versions, device, timestamp). Invariants:
- `completion` is the `skip_special_tokens=True` decode of the generated ids with `clean_up_tokenization_spaces=False`; all spans index into exactly this string;
- spans are non-overlapping and ordered; zero-width spans mark pending UTF-8 bytes and special tokens;
- one `tokens` entry per generated step (entropy computed from RAW logits, `output_logits=True` — never from processed `scores`);
- decoding for reported runs: greedy (`do_sample=False`), `max_new_tokens=512`, **batch size 1** (batched greedy is non-deterministic — see `tools/validate_batching.py`);
- writes are append + flush per prompt; re-runs skip ids already present (resume).

## §3 Stage 3 → Stage 4: sentence entropies

`entropy/outputs/<alias>/<dataset>.jsonl` — one line per prompt:

```json
{"id": "...", "dataset": "...", "sentences": [
  {"idx": 0, "text": "...", "start": 0, "end": 14,
   "n_tokens": 5,
   "mean_entropy": 0.834100,        // paper Eq. 2: plain mean of token entropies
   "token_entropies": [4.78, ...],  // kept for token-level (micro) aggregation
   "mean_logprob": -0.420000}]}
```

Invariants:
- sentences come from spaCy `en_core_web_sm` over `completion`; `start`/`end` are char offsets into that same string;
- token→sentence assignment: maximum span overlap; zero-width tokens by containing position; `special` tokens and zero-overlap whitespace tokens are excluded (counts printed for audit);
- `mean_entropy` is the unweighted mean of `token_entropies` (no filtering, no weighting — paper-faithful).

## §4 Stage 4: labeled sentences (the COMMITTED artifact)

`evaluation/outputs/<alias>/<dataset>.jsonl` — one line per prompt:

```json
{"id": "...", "dataset": "...",
 "answer_status": "EOS",            // upstream list-status (FULL/EOS/TOPIC_CHANGE/BAD_FORMAT)
 "answers": [{"text": "Thumb", "label": "C", "span": [1, 6]}, ...],
 "sentences": [{ ...all Stage-3 fields..., "label": "C" }]}
```

Label semantics (verbatim port of the upstream protocol — `evaluation/upstream/run_hallucinations_check.py`):
- per ANSWER: normalize → greedy-LCS match vs gold at threshold 0.55 → first occurrence `C` (matched) or `H` (unmatched); normalized duplicates (digits masked) → `R`; fake_qampari: every unique answer `H`;
- per SENTENCE (our documented mapping): `H` if it overlaps ≥1 H-answer span, else `C` if it overlaps a C-answer span, else `R` if only repetition spans, else `null` (unlabeled — excluded from class means).

## §5 Stage 4b: aggregated results

- `results/tables/replication_table1.csv` — 9 rows (3 models x 3 datasets), columns: `dataset, model, nonh_token_strict, nonh_sent_strict, n_nonh_strict, nonh_token_broad, nonh_sent_broad, n_nonh_broad, h_token, h_sent, n_h, paper_nonh_token, paper_nonh_sent, paper_h_token, paper_h_sent`. Token columns are micro-averages over all tokens of a class; sentence columns are macro-averages of sentence means. "strict" non-hallucinated = `C` sentences; "broad" = all non-`H`; FakeQAMPARI has no strict class by construction.
- `results/tables/classification_metrics.csv` — 9 rows, columns: `model, dataset, neg_class, n_pos, n_neg, auroc, best_f1, precision, recall, threshold` (positive class = `H`; threshold swept on sentence `mean_entropy`).
- `results/figures/roc_<alias>.png` — one ROC figure per model.

## §6 Aliases

Canonical aliases for the replication runs (used as folder names everywhere):
`llama3-8b-instruct` (meta-llama/Meta-Llama-3-8B-Instruct), `qwen2-7b-instruct` (Qwen/Qwen2-7B-Instruct), `gemma2-9b-it` (google/gemma-2-9b-it). Extension runs (Part B/C) must use NEW aliases — never overwrite a replication alias.

## §7 Pass-bands (guarded by tests/)

- C1: `h_sent > nonh_sent` and `h_token > nonh_token` in all 9 cells (ours AND the paper's printed values);
- all entropies in (0, 12.45) nats (ln of the largest vocab, Gemma-2's 256k);
- FakeQAMPARI AUROC > 0.70 for every model;
- LLaMA-3/FakeQAMPARI sentence means within 0.05 nats of the paper (the faithfulness anchor).
