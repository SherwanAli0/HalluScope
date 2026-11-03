"""Stage 2 - Generation with raw-logit capture (faithful replication).

Runs a HuggingFace causal LM on every prompt from Stage 1, replicating the
generation setup of Joo et al. (2025), which follows Ivgi et al. (2024)
(run_hallucinations_check.py in https://github.com/Mivg/fallbacks):

  * raw completion prompting - NO chat template, for base AND instruct models
  * greedy decoding: do_sample=False (temperature/top-k/top-p inactive)
  * max_new_tokens = 512

For every generated token we store:
  * Shannon entropy of the FULL-VOCABULARY softmax of the RAW logits, in nats
    (the paper's Eq. 1).  We use `output_logits=True` (unprocessed scores),
    not `output_scores=True`, because processed scores can be silently warped
    by logits processors. Entropy is computed in float32 for numerical safety.
  * log-probability of the chosen token (cheap to keep; used later for
    failure analysis / extensions - NOT part of the replication metric).
  * the token's character span in the decoded completion, computed by
    cumulative-prefix decoding (there is no offset_mapping for generated
    ids). Special tokens get zero-width spans and are flagged.

Output: one JSONL per dataset under --out-dir/<alias>/, plus run_meta.json.
Each line:
  {"id", "dataset", "prompt", "completion",
   "tokens": [{"token_id", "entropy", "logprob", "span": [s,e], "special"}]}

Storage note: we deliberately save per-token SCALARS, not logit tensors
(GBs -> MBs), computing entropy during generation.

Usage (local smoke test):
  py -3.11 generation/generate.py --model Qwen/Qwen2-0.5B-Instruct --alias smoke \
      --limit 2 --max-new-tokens 64

Usage (real, on Colab T4):
  python generation/generate.py --model meta-llama/Meta-Llama-3-8B-Instruct \
      --alias llama3-8b-instruct --load-4bit
"""

import argparse
import json
import sys
import time
from pathlib import Path

import torch
from packaging import version

import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

assert version.parse(transformers.__version__) >= version.parse("4.38.0"), (
    "transformers >= 4.38 required for output_logits=True (raw logits)")

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_DATA = REPO / "data" / "processed" / "replication.jsonl"
DEFAULT_OUT = HERE / "outputs"


def load_model(model_id: str, dtype: str, load_4bit: bool):
    kwargs = {}
    if "gemma" in model_id.lower():
        # Gemma-2 logit softcapping is incompatible with flash/sdpa kernels;
        # eager attention is the recommended implementation.
        kwargs["attn_implementation"] = "eager"

    if load_4bit:
        from transformers import BitsAndBytesConfig
        compute = torch.bfloat16 if (dtype == "bfloat16" or (
            dtype == "auto" and torch.cuda.is_available()
            and torch.cuda.is_bf16_supported())) else torch.float16
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=compute,
        )
        kwargs["device_map"] = "auto"
    else:
        # transformers 4.x uses torch_dtype (the `dtype` alias is 5.x only)
        if dtype == "auto":
            if torch.cuda.is_available():
                kwargs["torch_dtype"] = (torch.bfloat16
                                         if torch.cuda.is_bf16_supported()
                                         else torch.float16)
            else:
                kwargs["torch_dtype"] = torch.float32
        else:
            kwargs["torch_dtype"] = getattr(torch, dtype)
        kwargs["device_map"] = "auto" if torch.cuda.is_available() else None

    model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
    model.eval()
    return model


def token_spans(tokenizer, gen_ids):
    """Character span of each generated token in the decoded completion.

    Cumulative-prefix decoding: token i's span is the text added between
    decode(g[:i]) and decode(g[:i+1]).  Incomplete UTF-8 sequences from
    byte-level BPE leave a trailing U+FFFD; those tokens get a zero-width
    span and the completing token's span covers the whole character.
    """
    spans = []
    prev = ""
    for i in range(len(gen_ids)):
        cur = tokenizer.decode(gen_ids[: i + 1], skip_special_tokens=True,
                               clean_up_tokenization_spaces=False)
        if cur.endswith("�"):
            spans.append((len(prev), len(prev)))  # pending multi-byte char
        else:
            spans.append((len(prev), len(cur)))
            prev = cur
    return spans, prev  # prev == full visible completion


def generate_one(model, tokenizer, prompt: str, max_new_tokens: int):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    input_len = inputs["input_ids"].shape[1]

    with torch.no_grad():
        out = model.generate(
            **inputs,
            do_sample=False,            # greedy - overrides instruct defaults
            max_new_tokens=max_new_tokens,
            return_dict_in_generate=True,
            output_logits=True,         # RAW logits, not processed scores
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )

    gen_ids = out.sequences[0, input_len:].tolist()
    assert len(out.logits) == len(gen_ids)

    special_ids = set(tokenizer.all_special_ids)
    spans, completion = token_spans(tokenizer, gen_ids)

    # Compute entropy + chosen-token logprob on-GPU and transfer ONCE per
    # prompt. Per-token .item() would force a GPU->CPU sync every step
    # (hundreds per prompt) and dominates runtime on a weak GPU.
    ent_t, lp_t = [], []
    for tid, step_logits in zip(gen_ids, out.logits):
        logp = torch.log_softmax(step_logits[0].float(), dim=-1)
        ent_t.append(-(logp.exp() * logp).sum())          # nats, GPU scalar
        lp_t.append(logp[tid])
    ents = torch.stack(ent_t).cpu().tolist()
    lps = torch.stack(lp_t).cpu().tolist()
    del out

    tokens = [{
        "token_id": tid,
        "entropy": round(ents[i], 6),
        "logprob": round(lps[i], 6),
        "span": list(spans[i]),
        "special": tid in special_ids,
    } for i, tid in enumerate(gen_ids)]
    return completion, tokens


def generate_batch(model, tokenizer, prompts, max_new_tokens):
    """Greedy-generate a batch of prompts at once and return one
    (completion, tokens) pair per prompt.

    Uses LEFT padding so every sequence's generated tokens start at the same
    absolute position, which keeps out.logits[t][b] aligned with sequence b's
    t-th generated token. The token->logit ALIGNMENT is correct, but batched
    matmul rounding can flip near-tie argmax choices, so the output is NOT
    guaranteed to equal the single-prompt path (tools/validate_batching.py
    found such a divergence in bf16). Do not use it for reported results. Padding/EOS
    tokens that trail a finished sequence are flagged `special` and excluded
    from entropy downstream, exactly as the lone EOS is in the batch-1 path.
    """
    enc = tokenizer(prompts, return_tensors="pt", padding=True,
                    return_attention_mask=True).to(model.device)
    input_len = enc["input_ids"].shape[1]

    with torch.no_grad():
        out = model.generate(
            **enc,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            return_dict_in_generate=True,
            output_logits=True,
            pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
        )

    n_steps = len(out.logits)
    seqs = out.sequences[:, input_len:input_len + n_steps]      # [B, n_steps]

    # entropy + chosen-token logprob for the whole batch, one transfer total
    ent_steps, lp_steps = [], []
    for t in range(n_steps):
        logp = torch.log_softmax(out.logits[t].float(), dim=-1)  # [B, vocab]
        ent_steps.append(-(logp.exp() * logp).sum(-1))           # [B]
        lp_steps.append(logp.gather(1, seqs[:, t:t + 1]).squeeze(1))
    ent = torch.stack(ent_steps, dim=1).cpu().tolist()           # [B, n_steps]
    lp = torch.stack(lp_steps, dim=1).cpu().tolist()
    gen_all = seqs.cpu().tolist()
    del out

    special_ids = set(tokenizer.all_special_ids)
    results = []
    for b in range(len(prompts)):
        gen_ids = gen_all[b]
        spans, completion = token_spans(tokenizer, gen_ids)
        tokens = [{
            "token_id": tid,
            "entropy": round(ent[b][i], 6),
            "logprob": round(lp[b][i], 6),
            "span": list(spans[i]),
            "special": tid in special_ids,
        } for i, tid in enumerate(gen_ids)]
        results.append((completion, tokens))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="HF model id")
    ap.add_argument("--alias", required=True, help="short name for output folder")
    ap.add_argument("--data", default=str(DEFAULT_DATA))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--max-new-tokens", type=int, default=512)
    ap.add_argument("--dtype", default="auto",
                    choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--batch-size", type=int, default=1,
                    help="prompts generated at once; >1 needs spare VRAM "
                         "(e.g. 8-16 on an A100). batch-1 is the reference path.")
    ap.add_argument("--datasets", nargs="*", default=None,
                    help="subset of datasets to run (default: all)")
    ap.add_argument("--limit", type=int, default=None,
                    help="max prompts per dataset (smoke tests)")
    args = ap.parse_args()

    records = [json.loads(l) for l in open(args.data, encoding="utf-8")]
    if args.datasets:
        records = [r for r in records if r["dataset"] in args.datasets]
    if args.limit:
        per = {}
        kept = []
        for r in records:
            per.setdefault(r["dataset"], 0)
            if per[r["dataset"]] < args.limit:
                kept.append(r)
                per[r["dataset"]] += 1
        records = kept

    out_dir = Path(args.out_dir) / args.alias
    out_dir.mkdir(parents=True, exist_ok=True)

    # resume: skip ids already generated
    done = set()
    for f in out_dir.glob("*.jsonl"):
        for line in open(f, encoding="utf-8"):
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass
    todo = [r for r in records if r["id"] not in done]
    print(f"{len(records)} prompts requested, {len(done)} already done, "
          f"{len(todo)} to generate")
    if not todo:
        return

    print(f"loading {args.model} (4bit={args.load_4bit}, dtype={args.dtype}, "
          f"batch_size={args.batch_size})")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    # left padding is required for correct batched decoder-only generation
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = load_model(args.model, args.dtype, args.load_4bit)

    meta = {
        "model_id": args.model,
        "alias": args.alias,
        "max_new_tokens": args.max_new_tokens,
        "dtype": args.dtype,
        "load_4bit": args.load_4bit,
        "batch_size": args.batch_size,
        "decoding": "greedy (do_sample=False)",
        "chat_template": False,
        "transformers": transformers.__version__,
        "torch": torch.__version__,
        "device": (torch.cuda.get_device_name(0)
                   if torch.cuda.is_available() else "cpu"),
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2))

    handles = {}
    t0 = time.time()
    bs = max(1, args.batch_size)
    n = 0
    for start in range(0, len(todo), bs):
        chunk = todo[start:start + bs]
        if bs == 1:
            completion, tokens = generate_one(model, tokenizer,
                                              chunk[0]["prompt"],
                                              args.max_new_tokens)
            batch_out = [(completion, tokens)]
        else:
            # batch by identical-length prompts is unnecessary here; left
            # padding handles mixed lengths within the chunk.
            batch_out = generate_batch(model, tokenizer,
                                       [r["prompt"] for r in chunk],
                                       args.max_new_tokens)

        for rec, (completion, tokens) in zip(chunk, batch_out):
            n += 1
            ds = rec["dataset"]
            if ds not in handles:
                handles[ds] = open(out_dir / f"{ds}.jsonl", "a", encoding="utf-8")
            handles[ds].write(json.dumps({
                "id": rec["id"], "dataset": ds, "prompt": rec["prompt"],
                "completion": completion, "tokens": tokens,
            }, ensure_ascii=False) + "\n")
            handles[ds].flush()  # survive Colab disconnects

        ents = [t["entropy"] for t in batch_out[-1][1] if not t["special"]]
        mean_e = sum(ents) / len(ents) if ents else float("nan")
        rate = (time.time() - t0) / n
        print(f"[{n}/{len(todo)}] {chunk[-1]['id']}  "
              f"mean H={mean_e:.3f} nats  "
              f"({rate:.2f}s/prompt, ~{rate*(len(todo)-n)/60:.0f} min left)",
              flush=True)

    for h in handles.values():
        h.close()
    print("done.")


if __name__ == "__main__":
    main()
