"""Cross-platform single-command reproduction for the HalluScope replication.

Regenerates every table and figure in results/ from the committed labeled
data (evaluation/outputs/) — no GPU needed, takes seconds:

    python run_all.py             # fetch+validate data, rebuild tables+figures
    python run_all.py --tests     # additionally run the 12-test sanity suite
    python run_all.py --only data         # just validate/build the datasets
    python run_all.py --only aggregate    # just rebuild results/

Regenerating the MODEL RUNS themselves (GPU, ~2h/model) is a separate path —
see integration/COLAB_GUIDE.md and integration/run_pipeline.py.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
ALIASES = ["llama3-8b-instruct", "qwen2-7b-instruct", "gemma2-9b-it"]


def run(script, *args):
    cmd = [sys.executable, str(REPO / script), *args]
    print(f"\n=== {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=REPO)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", action="store_true", help="run the sanity suite")
    ap.add_argument("--only", choices=["data", "aggregate"], default=None)
    args = ap.parse_args()

    if args.only in (None, "data"):
        run("data/fetch_datasets.py")

    if args.only in (None, "aggregate"):
        present = [a for a in ALIASES
                   if (REPO / "evaluation" / "outputs" / a).is_dir()]
        if not present:
            print("\n[skip] no evaluation/outputs/<alias>/ found — nothing to "
                  "aggregate. (Did you clone without the committed outputs, "
                  "or are you mid-regeneration?)")
        else:
            print(f"\naggregating aliases: {present}")
            run("evaluation/build_table1.py", "--aliases", *present)
            run("evaluation/classifier.py", "--aliases", *present)

    if args.tests:
        print("\n=== sanity suite (12 tests)")
        rc = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"],
                            cwd=REPO).returncode
        sys.exit(rc)

    print("\nrun_all complete.")


if __name__ == "__main__":
    main()
