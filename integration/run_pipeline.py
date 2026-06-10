"""Stage 5 - Pipeline runner.

Chains the four stages for one model alias:

  data/fetch_datasets.py  ->  generation/generate.py  ->
  entropy/sentence_entropy.py  ->  evaluation/label.py

and (optionally, once several models are done) the aggregation:

  evaluation/build_table1.py + evaluation/classifier.py

Every stage is a separate script with file-based handoffs, so any stage can
also be run by hand (see each folder's README). This runner just removes the
copy-paste.

Usage:
  # full run for one model (example: local smoke test)
  py -3.11 integration/run_pipeline.py --model Qwen/Qwen2-0.5B-Instruct \
      --alias smoke --limit 2 --max-new-tokens 64

  # real replication model on Colab
  python integration/run_pipeline.py --model meta-llama/Meta-Llama-3-8B-Instruct \
      --alias llama3-8b-instruct --load-4bit

  # aggregation only (after all models are generated)
  py -3.11 integration/run_pipeline.py --aggregate llama3-8b-instruct qwen2-7b-instruct gemma2-9b-it
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def run(script, *args):
    cmd = [sys.executable, str(REPO / script), *args]
    print(f"\n=== {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=REPO)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--alias")
    ap.add_argument("--max-new-tokens", type=int, default=512)
    ap.add_argument("--load-4bit", action="store_true")
    ap.add_argument("--dtype", default="auto")
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--datasets", nargs="*", default=None)
    ap.add_argument("--aggregate", nargs="*", default=None,
                    help="aliases to aggregate into Table I + classifier metrics")
    args = ap.parse_args()

    if args.model or args.alias:
        assert args.model and args.alias, "--model and --alias go together"
        run("data/fetch_datasets.py")
        gen = ["--model", args.model, "--alias", args.alias,
               "--max-new-tokens", str(args.max_new_tokens),
               "--dtype", args.dtype,
               "--batch-size", str(args.batch_size)]
        if args.load_4bit:
            gen.append("--load-4bit")
        if args.limit:
            gen += ["--limit", str(args.limit)]
        if args.datasets:
            gen += ["--datasets", *args.datasets]
        run("generation/generate.py", *gen)
        run("entropy/sentence_entropy.py", "--alias", args.alias)
        run("evaluation/label.py", "--alias", args.alias)

    if args.aggregate:
        run("evaluation/build_table1.py", "--aliases", *args.aggregate)
        run("evaluation/classifier.py", "--aliases", *args.aggregate)

    print("\npipeline complete.")


if __name__ == "__main__":
    main()
