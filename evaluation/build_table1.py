"""Stage 4b - Replication Table I + side-by-side comparison with the paper.

Aggregates labeled sentences into the base paper's Table I format:

  per (dataset, model):
    Non-hallucinate (Token)  - micro mean over all tokens of non-halluc sentences
    Non-hallucinate (Sentence) -  macro mean of sentence-level entropies
    Hallucinate (Token)      - same, for hallucinated sentences
    Hallucinate (Sentence)

"Token level" = mean over ALL tokens belonging to sentences of the class
(micro average); "sentence level" = mean of per-sentence means (macro
average). The paper does not define this precisely - this is the natural
reading and is documented as an interpretation.

Non-hallucinated class definitions (the paper is ambiguous; we report both):
  strict - sentences labeled C (contain a verified-correct answer)
  broad - all sentences NOT labeled H (C + R + unlabeled prose)
For fake_qampari every answer is a hallucination by construction, so the
strict class is empty there and the broad definition is the only possible
reading of the paper's reported "Non-hallucinate" column.

Claims verdicts:
  C1 - hallucinated entropy > non-hallucinated entropy (token AND sentence)
  C2 - sentence-level gap > token-level gap

Outputs:
  results/tables/replication_table1.csv  (full numbers, both definitions)
  results/tables/replication_table1.md   (human-readable, side-by-side paper)

Usage:
  py -3.11 evaluation/build_table1.py --aliases llama3-8b-instruct qwen2-7b-instruct gemma2-9b-it
"""

import argparse
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
LAB_DIR = HERE / "outputs"
TABLES = REPO / "results" / "tables"

# Table I of Joo, Lee & Choi (2025), transcribed from the paper.
# (dataset, paper_model) -> [NonH_token, NonH_sent, H_token, H_sent]
PAPER_TABLE1 = {
    ("trivia_facts", "LLaMa3"): [0.2301, 0.2203, 0.5886, 0.5944],
    ("trivia_facts", "Qwen2"):  [0.4513, 0.4239, 0.9602, 1.0027],
    ("trivia_facts", "Gemma2"): [0.1893, 0.1919, 0.6533, 0.6745],
    ("qampari", "LLaMa3"):      [0.2554, 0.2243, 0.4815, 0.4988],
    ("qampari", "Qwen2"):       [0.4316, 0.4125, 0.8286, 0.8114],
    ("qampari", "Gemma2"):      [0.1919, 0.1964, 0.5807, 0.6020],
    ("fake_qampari", "LLaMa3"): [0.1451, 0.1416, 0.5929, 0.6312],
    ("fake_qampari", "Qwen2"):  [0.4510, 0.4452, 0.9630, 1.0613],
    ("fake_qampari", "Gemma2"): [0.1635, 0.1454, 0.8184, 0.7789],
}

DATASET_ORDER = ["trivia_facts", "qampari", "fake_qampari"]


def paper_model_for(alias: str):
    a = alias.lower()
    if "llama" in a:
        return "LLaMa3"
    if "qwen" in a:
        return "Qwen2"
    if "gemma" in a:
        return "Gemma2"
    return None


def micro_macro(sents):
    """(token-level micro mean, sentence-level macro mean, n_sent, n_tok)."""
    toks = [e for s in sents for e in s["token_entropies"]]
    if not sents or not toks:
        return None, None, len(sents), len(toks)
    micro = sum(toks) / len(toks)
    macro = sum(s["mean_entropy"] for s in sents) / len(sents)
    return micro, macro, len(sents), len(toks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aliases", nargs="+", required=True)
    ap.add_argument("--lab-dir", default=str(LAB_DIR))
    args = ap.parse_args()

    TABLES.mkdir(parents=True, exist_ok=True)
    rows = []
    for alias in args.aliases:
        adir = Path(args.lab_dir) / alias
        for f in sorted(adir.glob("*.jsonl")):
            ds = f.stem
            sents = [s for line in open(f, encoding="utf-8")
                     for s in json.loads(line)["sentences"]]
            h = [s for s in sents if s["label"] == "H"]
            strict = [s for s in sents if s["label"] == "C"]
            broad = [s for s in sents if s["label"] != "H"]

            h_tok, h_sent, n_h, _ = micro_macro(h)
            s_tok, s_sent, n_s, _ = micro_macro(strict)
            b_tok, b_sent, n_b, _ = micro_macro(broad)

            paper = PAPER_TABLE1.get((ds, paper_model_for(alias) or ""))
            rows.append({
                "dataset": ds, "model": alias,
                "nonh_token_strict": s_tok, "nonh_sent_strict": s_sent,
                "n_nonh_strict": n_s,
                "nonh_token_broad": b_tok, "nonh_sent_broad": b_sent,
                "n_nonh_broad": n_b,
                "h_token": h_tok, "h_sent": h_sent, "n_h": n_h,
                "paper_nonh_token": paper[0] if paper else None,
                "paper_nonh_sent": paper[1] if paper else None,
                "paper_h_token": paper[2] if paper else None,
                "paper_h_sent": paper[3] if paper else None,
            })

    df = pd.DataFrame(rows)
    df["dataset"] = pd.Categorical(df["dataset"], DATASET_ORDER, ordered=True)
    df = df.sort_values(["dataset", "model"])
    csv_path = TABLES / "replication_table1.csv"
    df.to_csv(csv_path, index=False)

    # human-readable markdown with claim verdicts -------------------------
    lines = ["# Replication of Table I - Joo, Lee & Choi (2025)", "",
             "Entropy in nats. `ours` = this replication; `paper` = Table I "
             "as printed. Non-hallucinated class: `strict` = C sentences; "
             "for fake_qampari the strict class is empty by construction, so "
             "`broad` (all non-H sentences) is shown there (marked *).", ""]
    header = ("| Dataset | Model | NonH tok (ours/paper) | NonH sent (ours/paper) "
              "| H tok (ours/paper) | H sent (ours/paper) | C1 | C2 |")
    lines += [header, "|" + "---|" * 8]

    def fmt(x):
        return " - " if x is None else f"{x:.4f}"

    c1_pass = c2_pass = total = 0
    for _, r in df.iterrows():
        use_broad = r["n_nonh_strict"] == 0
        nh_tok = r["nonh_token_broad"] if use_broad else r["nonh_token_strict"]
        nh_sent = r["nonh_sent_broad"] if use_broad else r["nonh_sent_strict"]
        star = "*" if use_broad else ""
        c1 = c2 = None
        if None not in (nh_tok, nh_sent, r["h_token"], r["h_sent"]):
            c1 = r["h_token"] > nh_tok and r["h_sent"] > nh_sent
            c2 = (r["h_sent"] - nh_sent) > (r["h_token"] - nh_tok)
            total += 1
            c1_pass += int(c1)
            c2_pass += int(c2)
        lines.append(
            f"| {r['dataset']} | {r['model']}{star} "
            f"| {fmt(nh_tok)} / {fmt(r['paper_nonh_token'])} "
            f"| {fmt(nh_sent)} / {fmt(r['paper_nonh_sent'])} "
            f"| {fmt(r['h_token'])} / {fmt(r['paper_h_token'])} "
            f"| {fmt(r['h_sent'])} / {fmt(r['paper_h_sent'])} "
            f"| {'✓' if c1 else '✗' if c1 is not None else ' - '} "
            f"| {'✓' if c2 else '✗' if c2 is not None else ' - '} |")

    lines += ["",
              f"**C1** (hallucinated > non-hallucinated, both levels): "
              f"{c1_pass}/{total} model×dataset cells",
              f"**C2** (sentence-level gap > token-level gap): "
              f"{c2_pass}/{total} cells", ""]
    md_path = TABLES / "replication_table1.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(df.to_string(index=False))
    print(f"\n[done] {csv_path}\n[done] {md_path}")


if __name__ == "__main__":
    main()
