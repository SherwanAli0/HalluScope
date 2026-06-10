# Stage 2 — Generation with Raw-Logit Capture

**What this module does:** runs each target model on the 297 replication
prompts and saves, for every generated token, the Shannon entropy of the
model's full-vocabulary predictive distribution — the white-box signal the
whole project is built on.

## Faithfulness decisions (and why)

| Decision | Value | Justification |
|---|---|---|
| Prompting | Raw completion text, **no chat template** | Matches the upstream generation script (`run_hallucinations_check.py`, Ivgi et al. 2024) that Joo et al.'s setup follows — it feeds the literal `"...\n1."` prompt to base *and* instruct models. |
| Decoding | **Greedy** (`do_sample=False`) | Upstream default (`temperature 0, top_p 1, top_k None`). Also makes runs deterministic. |
| Length | `max_new_tokens=512` | Upstream default (`--k 512`). |
| Logits | `output_logits=True` (raw), **not** `output_scores=True` | `scores` are *processed* logits; instruct models ship `do_sample=True` generation defaults whose warpers can silently distort them. Raw logits are exactly Eq. 1's p(y_i = v \| c_i) after softmax. Requires transformers ≥ 4.38 (asserted). |
| Entropy | Full-vocab, computed in **float32**, in **nats** | Half-precision softmax over 128k–256k vocabularies corrupts small-probability mass. Natural log matches the UQ literature the paper builds on. |
| Storage | Per-token scalars only, never logit tensors | 512 steps × 256k vocab per prompt would be GBs; the entropy scalar is all later stages need. |
| Gemma-2 | `attn_implementation="eager"` forced | Gemma-2's logit softcapping is incompatible with flash attention; fp16 is known-broken for Gemma-2 (use bf16/fp32/4-bit). |

## Token→character alignment

There is **no `offset_mapping` for generated ids**, so spans are computed by
cumulative-prefix decoding: token *i*'s span is the text added between
`decode(g[:i])` and `decode(g[:i+1])` (with `skip_special_tokens=True`,
`clean_up_tokenization_spaces=False`). Two edge cases:

- **Partial UTF-8** (byte-level BPE splits a multi-byte char): the prefix ends
  in `U+FFFD` → that token gets a zero-width span; the completing token's span
  covers the full character.
- **Special tokens** (EOS etc.): zero-width span + `"special": true` flag.
  They are **excluded from entropy averaging** downstream (documented choice;
  the paper does not state how EOS was handled).

## Extra captured signal (not part of the replication)

`logprob` (log-probability of the chosen token) is saved alongside entropy.
It costs nothing extra, is **not used** by the replication metric, and is kept
for the failure-analysis/extension stage.

## Outputs

`outputs/<alias>/<dataset>.jsonl` — one line per prompt:

```json
{"id": "qampari_007", "dataset": "qampari", "prompt": "...",
 "completion": "...", "tokens": [
   {"token_id": 123, "entropy": 0.4132, "logprob": -0.21,
    "span": [0, 4], "special": false}, ...]}
```

`outputs/<alias>/run_meta.json` — model id, dtype, quantization, library
versions, device, timestamp (provenance for the report).

Writing is **append + flush per prompt** and re-runs **resume** (already-done
ids are skipped) — this survives Colab runtime disconnects.

## How to run

```bash
# local smoke test (ungated tiny model)
py -3.11 generation/generate.py --model Qwen/Qwen2-0.5B-Instruct --alias smoke --limit 2 --max-new-tokens 64

# replication models (Colab T4, 4-bit NF4 — see integration/ notebook)
python generation/generate.py --model meta-llama/Meta-Llama-3-8B-Instruct --alias llama3-8b-instruct --load-4bit
python generation/generate.py --model Qwen/Qwen2-7B-Instruct            --alias qwen2-7b-instruct  --load-4bit
python generation/generate.py --model google/gemma-2-9b-it              --alias gemma2-9b-it       --load-4bit
```

Llama-3 and Gemma-2 are **gated** on HuggingFace: accept the license on the
model page and authenticate (`huggingface-cli login` or `HF_TOKEN`).

## Batching: available but OFF for the reported runs

`generate.py --batch-size N` (N>1) can generate N prompts at once for speed.
We validated it (`tools/validate_batching.py`) and **do not use it** for the
reported results: in bf16/4-bit, batched greedy decoding is **not
deterministic** — tiny batched-matmul rounding differences flip occasional
near-tie token choices, so a batched run diverges from the canonical
single-prompt greedy output (max per-token entropy diff ~1.5 nats on a
diverged sequence; completions textually differ). The token→sentence
*alignment* is correct (identical token counts, identical text on
non-diverging prompts) — the issue is pure numerical non-determinism inherent
to batched low-precision inference. All reported runs use **batch-1**
(`--batch-size 1`, the default), which is deterministic and reproducible.

## Documented deviations

1. The paper names "LLaMa3, Qwen2, Gemma2" **without sizes or variants**. We
   use the standard instruct checkpoints (8B / 7B / 9B); exact HF ids are in
   `run_meta.json`. This is a forced assumption — flagged in the report.
2. 7–9B models run in **4-bit NF4** (free Colab T4 cannot hold them in fp16).
   Quantization perturbs logits slightly; the quant config is identical across
   all models and is recorded. The `lm_head` stays unquantized by default,
   which preserves logit fidelity.
