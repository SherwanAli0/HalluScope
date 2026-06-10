"""Validate that batched generation matches the single-prompt path.

Batching is a speed optimization, not a method change - so it must produce the
same per-token entropies as batch-1 (up to floating-point noise from batched
matmuls and left padding). This script runs the SAME few prompts both ways on a
small model and reports the maximum entropy difference. If it's tiny
(< ~0.01 nats), the batched path is faithful and safe for the real runs.

Usage:
  py -3.11 tools/validate_batching.py --model google/gemma-2-2b-it --load-4bit --n 4 --max-new-tokens 96
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "generation"))

import generate as G  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

DATA = REPO / "data" / "processed" / "replication.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--dtype", default="auto")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    args = ap.parse_args()

    recs = [json.loads(l) for l in open(DATA, encoding="utf-8")][: args.n]
    prompts = [r["prompt"] for r in recs]

    tok = AutoTokenizer.from_pretrained(args.model)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = G.load_model(args.model, args.dtype, args.load_4bit)

    # single-prompt path (reference)
    single = [G.generate_one(model, tok, p, args.max_new_tokens) for p in prompts]
    # batched path (all n at once)
    batched = G.generate_batch(model, tok, prompts, args.max_new_tokens)

    max_ent_diff = 0.0
    max_text_mismatch = 0
    for i, ((c_s, t_s), (c_b, t_b)) in enumerate(zip(single, batched)):
        # compare entropies of the real (non-special) generated tokens
        es = [t["entropy"] for t in t_s if not t["special"]]
        eb = [t["entropy"] for t in t_b if not t["special"]]
        m = min(len(es), len(eb))
        for a, b in zip(es[:m], eb[:m]):
            max_ent_diff = max(max_ent_diff, abs(a - b))
        # the visible completions should be identical strings
        if c_s.strip() != c_b.strip():
            max_text_mismatch += 1
        print(f"prompt {i}: single {len(es)} real toks, batched {len(eb)} real "
              f"toks, text_match={c_s.strip() == c_b.strip()}")

    print(f"\nMAX per-token entropy difference (single vs batched): "
          f"{max_ent_diff:.6f} nats")
    print(f"completions textually mismatched: {max_text_mismatch}/{len(prompts)}")
    ok = max_ent_diff < 0.01 and max_text_mismatch == 0
    print("RESULT:", "PASS - batched path is faithful" if ok
          else "FAIL - investigate before using batching")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
