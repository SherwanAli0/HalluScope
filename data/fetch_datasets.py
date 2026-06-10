"""Stage 1 — Dataset preparation (faithful replication).

Downloads the three evaluation datasets used by Joo et al. (2025) from the
official repository of their upstream setup, Ivgi et al. (2024) "From Loops to
Oops" (https://github.com/Mivg/fallbacks, MIT license), and converts them into
HalluScope's unified JSONL format.

The paper states: "we evaluated large language models using three datasets —
QAMPARI, FAKEQAMPARI, and TriviaFacts — comprising 297 samples, following the
setup from [9]".  297 = 97 (trivia_facts) + 100 (qampari_rephrased)
+ 100 (fake_qampari), which is exactly what these files contain.

Each line of the upstream files is {"<prompt>": [gold answers]} where the
prompt already ends with the completion cue "\n1." — it is fed to the model
verbatim, with NO chat template (this mirrors run_hallucinations_check.py in
the upstream repo).

Output: data/processed/replication.jsonl with one record per prompt:
    {"id": "qampari_007", "dataset": "qampari", "prompt": "...",
     "gold_answers": [...], "answerable": true}

Usage:
    py -3.11 data/fetch_datasets.py            # download (if needed) + convert
    py -3.11 data/fetch_datasets.py --force    # re-download
"""

import argparse
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM_DIR = HERE / "upstream"
PROCESSED_DIR = HERE / "processed"

BASE_URL = "https://raw.githubusercontent.com/Mivg/fallbacks/main/data"

# name -> (upstream filename, expected #prompts, answerable)
DATASETS = {
    "trivia_facts": ("trivia_facts.jsonl", 97, True),
    "qampari": ("qampari_rephrased.jsonl", 100, True),
    "fake_qampari": ("fake_qampari.jsonl", 100, False),
}

EXPECTED_TOTAL = 297  # as stated in Joo et al. (2025), Section III


def download(force: bool = False) -> None:
    UPSTREAM_DIR.mkdir(parents=True, exist_ok=True)
    for name, (fname, _, _) in DATASETS.items():
        dest = UPSTREAM_DIR / fname
        if dest.exists() and not force:
            print(f"[skip] {fname} already present")
            continue
        url = f"{BASE_URL}/{fname}"
        print(f"[get ] {url}")
        urllib.request.urlretrieve(url, dest)


def convert() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "replication.jsonl"
    total = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for name, (fname, expected_n, answerable) in DATASETS.items():
            src = UPSTREAM_DIR / fname
            records = []
            with open(src, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    (prompt, gold), = obj.items()  # exactly one key per line
                    records.append((prompt, gold))

            # --- validation against the published setup ---
            assert len(records) == expected_n, (
                f"{name}: expected {expected_n} prompts, got {len(records)}")
            for prompt, gold in records:
                assert prompt.endswith("\n1."), (
                    f"{name}: prompt missing completion cue: {prompt!r}")
                if not answerable:
                    assert gold == [], (
                        f"{name}: unanswerable prompt has gold answers")

            for i, (prompt, gold) in enumerate(records):
                rec = {
                    "id": f"{name}_{i:03d}",
                    "dataset": name,
                    "prompt": prompt,
                    "gold_answers": gold,
                    "answerable": answerable,
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total += 1
            print(f"[ ok ] {name}: {len(records)} prompts")

    assert total == EXPECTED_TOTAL, f"expected {EXPECTED_TOTAL} total, got {total}"
    print(f"[done] {total} prompts -> {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download upstream files")
    args = ap.parse_args()
    download(force=args.force)
    convert()
