"""Stage 4a - Hallucination labeling (faithful port of the upstream protocol).

The functions `extract_answers`, `normalize_answer`, `remove_trailing_parenthesis`,
`tokenize`, `longest_common_subsequence`, `compute_similarity`, `greedy_match`
and `get_correct_answers`, plus the CORRECT/HALLUCINATION/REPETITION ordering
rule, are ported VERBATIM (prints/comments removed; unused options dropped:
`return_before_after`, and `get_correct_answers(method=...)` other than the
default 'greedy') from:

    https://github.com/Mivg/fallbacks/blob/main/run_hallucinations_check.py
    Ivgi, Yoran, Berant, Geva (2024) "From Loops to Oops", MIT license
    (copy of the license in evaluation/upstream/LICENSE)

Joo et al. (2025) state their experiment follows this setup, so these rules
ARE the ground-truth protocol of the base paper. Quirks in the upstream code
are intentionally preserved - fixing them would change the labels.

Labeling protocol (answerable datasets: trivia_facts, qampari):
  1. parse up to 25 enumerated answers out of the completion;
  2. normalize (lowercase, strip punctuation/articles/trailing parentheses);
  3. greedy-match predictions to gold answers by normalized token-LCS
     similarity, threshold 0.55  ->  matched = CORRECT;
  4. first occurrence of an unmatched answer = HALLUCINATION;
     later duplicates of an already-seen normalized answer = REPETITION.
For fake_qampari the gold lists are empty (fabricated subjects), so every
unique answer is a HALLUCINATION by construction.

This script then maps each labeled answer to its character span in the
completion and labels each Stage 3 sentence:
  H - overlaps >=1 HALLUCINATION answer
  C - else, overlaps >=1 CORRECT answer
  R - else, overlaps >=1 REPETITION answer
  None - overlaps no labeled answer (prose, refusals, degenerate tails)

Output: outputs/<alias>/<dataset>.jsonl with per-sentence labels + entropy.

Usage:
  py -3.11 evaluation/label.py --alias smoke
"""

import argparse
import json
import re
import string
from enum import Enum
from itertools import product
from pathlib import Path
from typing import List, Tuple

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA_FILE = REPO / "data" / "processed" / "replication.jsonl"
GEN_DIR = REPO / "generation" / "outputs"
ENT_DIR = REPO / "entropy" / "outputs"
OUT_DIR = HERE / "outputs"

# ----------------------------------------------------------------------------
# Ported upstream code (Ivgi et al. 2024, MIT) - do not "fix"; quirks are part
# of the published protocol.
# ----------------------------------------------------------------------------

ENUM_ITEM_PATTERN = re.compile(r'^(\d+)\.\s*(.*)$')
NUMBER_PATTERN = re.compile(r'\d+')

CORRECT = 1
HALLUCINATION = 2
REPETITION = 3
BAD_FORMAT = 4
TOPIC_CHANGE = 5
EOS = 6

LABEL_NAME = {CORRECT: "C", HALLUCINATION: "H", REPETITION: "R"}

MINIMUM_ANSWERS = 3


class AnswerListStatus(Enum):
    FULL = -1
    BAD_FORMAT = BAD_FORMAT
    TOPIC_CHANGE = TOPIC_CHANGE
    EOS = EOS


def extract_answers(result, require_max_answers=False, require_enumerated_answers=False,
                    max_answers=500, max_words_for_eos=150):
    topic_change = eos = trimmed = False
    before = after = None
    n_words = len(result.split())

    first_line = result.split('\n')[0]
    answers = None
    if len(enumerators := re.findall(r'(\d+)\.\s?\w', first_line)) >= MINIMUM_ANSWERS:
        if all(int(enumerators[i]) == i + 2 for i in range(len(enumerators))):
            answers = re.split(r'\d+\.\s?', first_line)
            answers = [f'{i}. {ans.strip()}' for i, ans in enumerate(answers, 2)]
            topic_change = len(answers) <= max_answers
            eos = len([l for l in result.split('\n') if len(l.strip()) > 0]) == 1
            trimmed = True
    elif len(parts := first_line.split(',')) >= MINIMUM_ANSWERS:
        if len(re.findall(r'(\d+)\.\s*\w', result)) >= MINIMUM_ANSWERS:
            pass  # enumeration later on, not a csv
        else:
            answers = [f'{i}. {ans.strip()}' for i, ans in enumerate(parts, 2)]
            topic_change = len(answers) <= max_answers
            eos = len([l for l in result.split('\n') if len(l.strip()) > 0]) == 1
            trimmed = True

    if answers is None:
        pattern = r'\n(\d+)\.\s(?=\D)+'
        replacement = r'\n\1. '
        result_ = re.sub(pattern, replacement, result)
        if result_ != result:
            result = result_

        if '\nThe following ' in result:
            after = result[result.index('\nThe following '):]
            before = result = result.split('\nThe following ')[0]
            trimmed = True
            topic_change = True
            eos = False
        if '\n\n' in result:
            before = result_up_to_newlines = result[:result.index('\n\n')]
            after = result[result.index('\n\n'):]
            if result_up_to_newlines.split('\n')[-1].startswith(f'{max_answers}.'):
                topic_change = True
                eos = len(result[result.index('\n\n'):].strip()) == 0
                trimmed = not eos
                result = result_up_to_newlines
            else:
                probably_divergence = True
                for i, line in enumerate(result_up_to_newlines.split('\n')[1:], 2):
                    match = ENUM_ITEM_PATTERN.match(line)
                    if match is None or int(match.group(1)) != i:
                        probably_divergence = False
                if probably_divergence and len(result_up_to_newlines.split('\n')) >= MINIMUM_ANSWERS:
                    topic_change = True
                    eos = len(result[result.index('\n\n'):].strip()) == 0
                    trimmed = not eos
                    result = result_up_to_newlines

        answers = [l for l in result.lstrip().split('\n') if len(l) > 0]

        if len(answers) < max_answers:
            if require_max_answers:
                raise ValueError(f'Found only {len(answers)} answers instead of {max_answers}')

    answers_list = []
    for i, ans in enumerate(answers, 1):
        match = ENUM_ITEM_PATTERN.match(ans)
        if require_enumerated_answers:
            assert match is not None, f'answer without a number: {ans}'
            assert int(match.group(1)) == i, f'answer with wrong number: {ans}'
        if match is not None:
            answers_list.append(match.group(2))
        else:
            if re.match(r'^\d+\.?\s?$', ans) is not None and i == len(answers):
                eos = False
                continue
            answers_list.append(ans)

    topic_change = topic_change or len(answers) <= max_answers
    eos = eos or (not trimmed and len(answers) <= max_answers)
    if eos and n_words > max_words_for_eos:
        topic_change = eos = False

    if max_answers is not None and len(answers_list) > max_answers:
        answers_list = answers_list[:max_answers]

    topic_change = topic_change and len(answers_list) >= MINIMUM_ANSWERS
    if len(answers_list) < max_answers:
        if not topic_change:
            answer_status = AnswerListStatus.BAD_FORMAT
        elif eos:
            answer_status = AnswerListStatus.EOS
        else:
            answer_status = AnswerListStatus.TOPIC_CHANGE
    else:
        answer_status = AnswerListStatus.FULL if not topic_change else AnswerListStatus.TOPIC_CHANGE
    return answers_list, answer_status


def remove_trailing_parenthesis(s):
    return re.sub(r'(.+)\([^)]+\)$', r'\1', s).strip()


def normalize_answer(s, should_remove_year=False):
    """Lower text and remove punctuation, articles and extra whitespace."""

    def remove_articles(text):
        return re.sub(r"\b(a|an|the)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    def remove_year(text):
        return re.sub(r"\(\d{4}\)", "", text).strip()

    if should_remove_year:
        s = remove_year(s)

    return white_space_fix(remove_articles(remove_punc(remove_trailing_parenthesis(lower(s).strip()))))


def tokenize(s: str) -> List[str]:
    return s.split()


def longest_common_subsequence(s1: List[str], s2: List[str]) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 or j == 0:
                dp[i][j] = 0
            elif s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def compute_similarity(refernce: str, prediction: str) -> float:
    tokens1 = tokenize(refernce)
    tokens2 = tokenize(prediction)
    lcs_length = longest_common_subsequence(tokens1, tokens2)
    return lcs_length / len(tokens1) if tokens1 else 0


def greedy_match(set1: List[str], set2: List[str], threshold: float = 0.5) -> List[Tuple[str, str, float]]:
    similarities = [(s1, s2, compute_similarity(s1, s2)) for s1, s2 in product(set1, set2)]
    similarities = sorted(similarities, key=lambda x: (-x[-1], x[1].count(' '), x[0].count(' ')))
    matched = set()
    matches = []
    for s1, s2, sim in similarities:
        if sim >= threshold and s1 not in matched and s2 not in matched:
            matches.append((s1, s2, sim))
            matched.add(s1)
            matched.add(s2)
    return matches


def get_correct_answers(answers, correct_answers):
    clean_answers_list = [normalize_answer(ans) for ans in answers]
    clean_answers = set(clean_answers_list)
    clean_correct_answers_list = [normalize_answer(ans) for ans in correct_answers]
    clean_correct_answers = set(clean_correct_answers_list)
    greedy_matches = greedy_match(list(clean_correct_answers), list(clean_answers), threshold=0.55)
    return {gm[1] for gm in greedy_matches}, clean_answers_list


def label_answers(answers, gold_answers):
    """First occurrence = CORRECT (matched) or HALLUCINATION; repeats = REPETITION.

    Verbatim ordering rule from upstream `_analyze_results`. `gold_answers`
    is None for the unanswerable dataset (fake_qampari): nothing can match,
    so every unique answer is a HALLUCINATION by construction.
    """
    if gold_answers is not None:
        correct_predictions, clean_answers_list = get_correct_answers(answers, gold_answers)
    else:
        clean_answers_list = [normalize_answer(ans) for ans in answers]
        correct_predictions = {}
    saw = set()
    order = []
    for p in clean_answers_list:
        if p in saw:
            order.append(REPETITION)
        elif p in correct_predictions:
            order.append(CORRECT)
            saw.add(p)
        else:
            order.append(HALLUCINATION)
            saw.add(p)
    return order

# ----------------------------------------------------------------------------
# HalluScope additions: answer -> char span -> sentence label
# ----------------------------------------------------------------------------


def map_answer_spans(completion: str, answers: List[str]):
    """Locate each extracted answer in the completion (sequential search).

    extract_answers may have lightly rewritten/trimmed its working copy, so a
    small number of answers can fail to map; they are returned as None and
    counted (sentences they would label simply stay unlabeled).
    """
    spans = []
    cursor = 0
    for ans in answers:
        cand = ans.strip()
        idx = completion.find(ans, cursor)
        if idx < 0 and cand:
            idx = completion.find(cand, cursor)
            ans = cand if idx >= 0 else ans
        if idx < 0 and cand:
            idx = completion.find(cand)  # out-of-order fallback
            ans = cand if idx >= 0 else ans
        if idx < 0:
            spans.append(None)
        else:
            spans.append((idx, idx + len(ans)))
            cursor = idx + len(ans)
    return spans


def label_sentences(sentences, answer_spans, answer_labels):
    """H beats C beats R; sentences touching no labeled answer stay None."""
    out = []
    for s in sentences:
        ss, se = s["start"], s["end"]
        hit = set()
        for span, lab in zip(answer_spans, answer_labels):
            if span is None:
                continue
            if max(0, min(se, span[1]) - max(ss, span[0])) > 0:
                hit.add(lab)
        if HALLUCINATION in hit:
            label = "H"
        elif CORRECT in hit:
            label = "C"
        elif REPETITION in hit:
            label = "R"
        else:
            label = None
        out.append({**s, "label": label})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alias", required=True)
    ap.add_argument("--gen-dir", default=str(GEN_DIR))
    ap.add_argument("--ent-dir", default=str(ENT_DIR))
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    args = ap.parse_args()

    gold = {json.loads(l)["id"]: json.loads(l)
            for l in open(DATA_FILE, encoding="utf-8")}

    gen_dir = Path(args.gen_dir) / args.alias
    ent_dir = Path(args.ent_dir) / args.alias
    out_dir = Path(args.out_dir) / args.alias
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(gen_dir.glob("*.jsonl"))
    assert files, f"no generation outputs under {gen_dir}"

    totals = {"C": 0, "H": 0, "R": 0, None: 0}
    unmapped = mapped = 0
    for f in files:
        ent_path = ent_dir / f.name
        assert ent_path.exists(), f"missing entropy output {ent_path} - run Stage 3 first"
        ent_by_id = {json.loads(l)["id"]: json.loads(l)["sentences"]
                     for l in open(ent_path, encoding="utf-8")}

        # validate inputs BEFORE opening (and truncating) the output file
        for line in open(f, encoding="utf-8"):
            rid = json.loads(line)["id"]
            if rid not in gold:
                raise SystemExit(
                    f"[error] {f.name}: id {rid!r} is not in {DATA_FILE.name} "
                    "- regenerate it with data/fetch_datasets.py (Stage 1)")
            if rid not in ent_by_id:
                raise SystemExit(
                    f"[error] {f.name}: id {rid!r} has generation output but no "
                    f"Stage-3 record in {ent_path} - re-run "
                    "entropy/sentence_entropy.py for this alias")

        out_path = out_dir / f.name
        with open(f, encoding="utf-8") as fin, \
             open(out_path, "w", encoding="utf-8") as fout:
            for line in fin:
                rec = json.loads(line)
                grec = gold[rec["id"]]
                answers, status = extract_answers(rec["completion"], max_answers=25)
                labels = label_answers(
                    answers, grec["gold_answers"] if grec["answerable"] else None)
                spans = map_answer_spans(rec["completion"], answers)
                unmapped += sum(1 for s in spans if s is None)
                mapped += sum(1 for s in spans if s is not None)

                sentences = label_sentences(ent_by_id[rec["id"]], spans, labels)
                for s in sentences:
                    totals[s["label"]] = totals.get(s["label"], 0) + 1

                fout.write(json.dumps({
                    "id": rec["id"], "dataset": rec["dataset"],
                    "answer_status": status.name,
                    "answers": [
                        {"text": a, "label": LABEL_NAME[l],
                         "span": list(sp) if sp else None}
                        for a, l, sp in zip(answers, labels, spans)],
                    "sentences": sentences,
                }, ensure_ascii=False) + "\n")
        print(f"[ ok ] {f.name} -> {out_path}")

    total_ans = mapped + unmapped
    print(f"[stats] answer spans mapped: {mapped}/{total_ans} "
          f"({100*mapped/max(total_ans,1):.1f}%)")
    print(f"[stats] sentence labels: C={totals.get('C',0)} H={totals.get('H',0)} "
          f"R={totals.get('R',0)} unlabeled={totals.get(None,0)}")


if __name__ == "__main__":
    main()
