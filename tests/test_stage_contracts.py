"""Stage-contract fixtures for the HalluScope replication.

Complements tests/test_sanity.py (which checks the committed datasets and
result CSVs). These tests use tiny SYNTHETIC fixtures and the committed
labeled outputs; they need no GPU, no model download and no spaCy. They guard
the interfaces documented in PIPELINE_CONTRACT.md:

  * Stage 3 token->sentence assignment and input validation;
  * Stage 4 labeling rules (C/H/R/unlabeled) and missing-input handling;
  * Stage 4b aggregation definitions (micro token vs macro sentence means,
    strict vs broad non-hallucinated class) and metric preconditions (no AUROC
    is produced when one class is absent);
  * the committed labeled artifacts satisfy the Stage 3/4 invariants;
  * run_all.py / build_table1.py / classifier.py fail loudly on a missing
    alias instead of overwriting committed results;
  * integration/config.yaml is valid YAML.
"""

import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ALIASES = ["llama3-8b-instruct", "qwen2-7b-instruct", "gemma2-9b-it"]
DATASET_SIZES = {"trivia_facts": 97, "qampari": 100, "fake_qampari": 100}


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- Stage 3

@pytest.fixture(scope="module")
def se():
    return _load("sentence_entropy", "entropy/sentence_entropy.py")


def _tok(span, ent=1.0, special=False):
    return {"token_id": 1, "entropy": ent, "logprob": -0.5,
            "span": list(span), "special": special}


def test_assign_tokens_overlap_zero_width_special_and_whitespace(se):
    sents = [(0, 10), (11, 20)]
    toks = [
        _tok((8, 12)),            # overlaps s0 by 2, s1 by 1 -> s0 (max overlap)
        _tok((15, 15)),           # zero-width inside s1 -> s1
        _tok((10, 10)),           # zero-width between sentences -> excluded
        _tok((10, 11)),           # pure inter-sentence whitespace -> excluded
        _tok((20, 20), special=True),  # special -> excluded
        _tok((12, 14)),           # inside s1 -> s1
    ]
    assert se.assign_tokens(sents, toks) == [0, 1, None, None, None, 1]


def test_check_record_accepts_valid_and_rejects_contract_violations(se):
    good = {"id": "x_000", "dataset": "x", "completion": "abcdef",
            "tokens": [_tok((0, 3)), _tok((3, 3)), _tok((3, 6)),
                       _tok((6, 6), special=True)]}
    se.check_record(good)  # must not raise

    def bad(**tok_overrides):
        rec = json.loads(json.dumps(good))
        rec["tokens"][2].update(tok_overrides)
        return rec

    with pytest.raises(ValueError, match="outside completion"):
        se.check_record(bad(span=[3, 99]))
    with pytest.raises(ValueError, match="overlaps or precedes"):
        se.check_record(bad(span=[1, 4]))
    with pytest.raises(ValueError, match="entropy"):
        se.check_record(bad(entropy=float("nan")))
    with pytest.raises(ValueError, match="entropy"):
        se.check_record(bad(entropy=-1.0))
    broken = json.loads(json.dumps(good))
    del broken["tokens"][0]["logprob"]
    with pytest.raises(ValueError, match="missing field"):
        se.check_record(broken)
    with pytest.raises(ValueError, match="missing field"):
        se.check_record({"id": "x_000", "dataset": "x", "completion": ""})


# ---------------------------------------------------------------- Stage 4a

@pytest.fixture(scope="module")
def lab():
    return _load("label_mod", "evaluation/label.py")


def test_label_answers_c_h_r_rules(lab):
    # first occurrence: matched -> C, unmatched -> H; later duplicate -> R
    order = lab.label_answers(["Heat", "Heat", "Unknown Manga"],
                              ["Heat", "Crying Freeman"])
    assert order == [lab.CORRECT, lab.REPETITION, lab.HALLUCINATION]
    # unanswerable dataset (gold None): every unique answer is H
    assert lab.label_answers(["A b", "C d", "A b"], None) == [
        lab.HALLUCINATION, lab.HALLUCINATION, lab.REPETITION]


def test_label_answers_does_not_mask_digits(lab):
    # PIPELINE_CONTRACT section 4: per-answer repetition uses the NORMALIZED
    # string only (as in the upstream `order` loop). Digit masking exists
    # upstream only in the aggregate counts, which this pipeline does not use.
    order = lab.label_answers(["Harry Potter 2", "Harry Potter 3"], ["Zebra"])
    assert order == [lab.HALLUCINATION, lab.HALLUCINATION]


def test_label_sentences_priority_h_over_c_over_r_else_none(lab):
    sents = [{"start": 0, "end": 10}, {"start": 10, "end": 20},
             {"start": 20, "end": 30}, {"start": 30, "end": 40}]
    spans = [(2, 5), (4, 8), (12, 15), (22, 25), (22, 24)]
    labels = [lab.CORRECT, lab.HALLUCINATION, lab.CORRECT,
              lab.REPETITION, lab.CORRECT]
    got = [s["label"] for s in lab.label_sentences(sents, spans, labels)]
    assert got == ["H", "C", "C", None]
    # an unmapped answer (span None) labels nothing
    assert lab.label_sentences([{"start": 0, "end": 5}], [None],
                               [lab.HALLUCINATION])[0]["label"] is None
    # R only when no H/C overlap
    assert lab.label_sentences([{"start": 0, "end": 5}], [(1, 3)],
                               [lab.REPETITION])[0]["label"] == "R"


def test_map_answer_spans_sequential_and_unmapped(lab):
    comp = " A1\n2. B2\n3. C3"
    spans = lab.map_answer_spans(comp, ["A1", "B2", "ZZZ"])
    assert spans[0] == (1, 3)
    assert comp[spans[1][0]:spans[1][1]] == "B2"
    assert spans[2] is None


def _label_main(lab, monkeypatch, tmp_path, ent_ids, gold_ids=("qampari_000",)):
    gold_file = tmp_path / "replication.jsonl"
    _write_jsonl(gold_file, [{"id": i, "dataset": "qampari", "prompt": "p\n1.",
                              "gold_answers": ["Heat", "Crying Freeman"],
                              "answerable": True} for i in gold_ids])
    comp = " Heat\n2. Crying Freeman\n3. Unknown Manga\n4. Unknown Manga"
    gen = tmp_path / "gen" / "t" / "qampari.jsonl"
    _write_jsonl(gen, [{"id": "qampari_000", "dataset": "qampari",
                        "prompt": "p\n1.", "completion": comp, "tokens": []}])
    sents = []
    for text in ["Heat", "2. Crying Freeman", "3. Unknown Manga", "4. Unknown Manga"]:
        a = comp.index(text)
        sents.append({"idx": len(sents), "text": text, "start": a,
                      "end": a + len(text), "n_tokens": 1, "mean_entropy": 1.0,
                      "token_entropies": [1.0], "mean_logprob": -1.0})
    _write_jsonl(tmp_path / "ent" / "t" / "qampari.jsonl",
                 [{"id": i, "dataset": "qampari", "sentences": sents}
                  for i in ent_ids])
    out_file = tmp_path / "out" / "t" / "qampari.jsonl"
    out_file.parent.mkdir(parents=True)
    out_file.write_text("PRE-EXISTING", encoding="utf-8")
    monkeypatch.setattr(lab, "DATA_FILE", gold_file)
    monkeypatch.setattr(sys, "argv", [
        "label.py", "--alias", "t", "--gen-dir", str(tmp_path / "gen"),
        "--ent-dir", str(tmp_path / "ent"), "--out-dir", str(tmp_path / "out")])
    return out_file


def test_label_main_labels_a_synthetic_completion(lab, monkeypatch, tmp_path):
    out_file = _label_main(lab, monkeypatch, tmp_path, ent_ids=["qampari_000"])
    lab.main()
    rec = json.loads(out_file.read_text(encoding="utf-8"))
    assert [a["label"] for a in rec["answers"]] == ["C", "C", "H", "R"]
    assert all(a["span"] is not None for a in rec["answers"])
    assert [s["label"] for s in rec["sentences"]] == ["C", "C", "H", "R"]


def test_label_main_missing_stage3_record_fails_before_touching_output(
        lab, monkeypatch, tmp_path):
    out_file = _label_main(lab, monkeypatch, tmp_path, ent_ids=["qampari_999"])
    with pytest.raises(SystemExit, match="no Stage-3 record"):
        lab.main()
    assert out_file.read_text(encoding="utf-8") == "PRE-EXISTING"


def test_label_main_unknown_prompt_id_fails_before_touching_output(
        lab, monkeypatch, tmp_path):
    out_file = _label_main(lab, monkeypatch, tmp_path, ent_ids=["qampari_000"],
                           gold_ids=("qampari_001",))
    with pytest.raises(SystemExit, match="not in replication.jsonl"):
        lab.main()
    assert out_file.read_text(encoding="utf-8") == "PRE-EXISTING"


# ---------------------------------------------------------------- Stage 4b

def _sent(label, ents):
    return {"label": label, "mean_entropy": sum(ents) / len(ents),
            "token_entropies": ents}


def _lab_fixture(root):
    rec = lambda i, ds, ss: {"id": f"{ds}_{i:03d}", "dataset": ds, "sentences": ss}
    _write_jsonl(root / "m-llama" / "trivia_facts.jsonl", [rec(0, "trivia_facts", [
        _sent("H", [1.0, 3.0]), _sent("H", [5.0]), _sent("C", [0.5]),
        _sent("R", [9.0, 9.0]), _sent(None, [2.0])])])
    _write_jsonl(root / "m-llama" / "fake_qampari.jsonl", [rec(0, "fake_qampari", [
        _sent("H", [2.0, 2.0]), _sent("R", [1.0]), _sent(None, [0.5])])])


def test_table1_micro_token_macro_sentence_and_strict_vs_broad(tmp_path, monkeypatch):
    pd = pytest.importorskip("pandas")
    b1 = _load("build_table1_mod", "evaluation/build_table1.py")
    lab_dir = tmp_path / "lab"
    _lab_fixture(lab_dir)
    monkeypatch.setattr(b1, "TABLES", tmp_path / "tables")
    monkeypatch.setattr(sys, "argv", ["build_table1.py", "--aliases", "m-llama",
                                      "--lab-dir", str(lab_dir)])
    b1.main()
    df = pd.read_csv(tmp_path / "tables" / "replication_table1.csv")
    t = df[df.dataset == "trivia_facts"].iloc[0]
    # H: tokens [1,3,5] -> micro 3.0; sentence means [2,5] -> macro 3.5
    assert t.h_token == pytest.approx(3.0) and t.h_sent == pytest.approx(3.5)
    # strict = C only; broad = everything not H (C, R, unlabeled)
    assert t.n_nonh_strict == 1 and t.nonh_sent_strict == pytest.approx(0.5)
    assert t.n_nonh_broad == 3
    assert t.nonh_token_broad == pytest.approx((0.5 + 9 + 9 + 2) / 4)
    assert t.nonh_sent_broad == pytest.approx((0.5 + 9 + 2) / 3)
    f = df[df.dataset == "fake_qampari"].iloc[0]
    assert f.n_nonh_strict == 0 and math.isnan(f.nonh_sent_strict)
    assert f.n_nonh_broad == 2
    md = (tmp_path / "tables" / "replication_table1.md").read_text(encoding="utf-8")
    assert "m-llama*" in md  # fake_qampari row flagged as using the broad class


def test_classifier_never_invents_auroc_for_single_class(tmp_path, monkeypatch):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("sklearn")
    pytest.importorskip("matplotlib")
    cl = _load("classifier_mod", "evaluation/classifier.py")
    lab_dir = tmp_path / "lab"
    rec = lambda ds, ss: [{"id": f"{ds}_000", "dataset": ds, "sentences": ss}]
    # a: both classes, perfectly separable by entropy -> AUROC 1.0 (strict)
    _write_jsonl(lab_dir / "m" / "a.jsonl", rec("a", [
        _sent("H", [3.0]), _sent("H", [4.0]), _sent("C", [0.1]), _sent("C", [0.2])]))
    # b: only H sentences -> no AUROC may be produced
    _write_jsonl(lab_dir / "m" / "b.jsonl", rec("b", [_sent("H", [1.0]), _sent("H", [2.0])]))
    # c: no C sentences but non-H prose exists -> falls back to the broad class
    _write_jsonl(lab_dir / "m" / "c.jsonl", rec("c", [
        _sent("H", [3.0]), _sent("R", [0.1]), _sent(None, [0.2])]))
    monkeypatch.setattr(cl, "TABLES", tmp_path / "tables")
    monkeypatch.setattr(cl, "FIGURES", tmp_path / "figures")
    monkeypatch.setattr(sys, "argv", ["classifier.py", "--aliases", "m",
                                      "--lab-dir", str(lab_dir)])
    cl.main()
    df = pd.read_csv(tmp_path / "tables" / "classification_metrics.csv")
    assert sorted(df.dataset) == ["a", "c"]          # b skipped, not scored
    a = df[df.dataset == "a"].iloc[0]
    assert a.neg_class == "strict" and a.auroc == pytest.approx(1.0)
    c = df[df.dataset == "c"].iloc[0]
    assert c.neg_class == "broad" and c.n_neg == 2


def test_classifier_all_single_class_keeps_existing_csv(tmp_path, monkeypatch):
    pytest.importorskip("pandas")
    pytest.importorskip("sklearn")
    pytest.importorskip("matplotlib")
    cl = _load("classifier_mod2", "evaluation/classifier.py")
    _write_jsonl(tmp_path / "lab" / "m" / "b.jsonl", [
        {"id": "b_000", "dataset": "b", "sentences": [_sent("H", [1.0])]}])
    tables = tmp_path / "tables"
    tables.mkdir()
    (tables / "classification_metrics.csv").write_text("KEEP", encoding="utf-8")
    monkeypatch.setattr(cl, "TABLES", tables)
    monkeypatch.setattr(cl, "FIGURES", tmp_path / "figures")
    monkeypatch.setattr(sys, "argv", ["classifier.py", "--aliases", "m",
                                      "--lab-dir", str(tmp_path / "lab")])
    with pytest.raises(SystemExit, match="no dataset had both classes"):
        cl.main()
    assert (tables / "classification_metrics.csv").read_text() == "KEEP"
    assert not list((tmp_path / "figures").glob("*.png"))


# ------------------------------------------------- committed artifacts

def test_committed_labeled_outputs_follow_stage3_and_stage4_contract():
    allowed = {"C", "H", "R", None}
    for alias in ALIASES:
        for ds, n in DATASET_SIZES.items():
            path = REPO / "evaluation" / "outputs" / alias / f"{ds}.jsonl"
            recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
            assert [r["id"] for r in recs] == [f"{ds}_{i:03d}" for i in range(n)], \
                f"{alias}/{ds}: ids are not the unified prompt ids, in order"
            for r in recs:
                assert r["answer_status"] in {"FULL", "EOS", "TOPIC_CHANGE", "BAD_FORMAT"}
                prev_end, prev_idx = 0, -1
                for s in r["sentences"]:
                    where = f"{alias}/{r['id']}/sentence {s['idx']}"
                    assert s["label"] in allowed, where
                    assert s["n_tokens"] == len(s["token_entropies"]) > 0, where
                    assert s["mean_entropy"] == pytest.approx(
                        sum(s["token_entropies"]) / s["n_tokens"], abs=1e-9), where
                    assert 0 <= s["start"] < s["end"], where
                    assert s["start"] >= prev_end and s["idx"] > prev_idx, where
                    prev_end, prev_idx = s["end"], s["idx"]
                if ds == "fake_qampari":
                    assert all(a["label"] != "C" for a in r["answers"])
                    assert all(s["label"] != "C" for s in r["sentences"])


# ------------------------------------------- scripts: missing-input paths

RESULT_FILES = ["results/tables/replication_table1.csv",
                "results/tables/replication_table1.md",
                "results/tables/classification_metrics.csv"] + \
               [f"results/figures/roc_{a}.png" for a in ALIASES]


@pytest.mark.parametrize("script", ["evaluation/build_table1.py",
                                    "evaluation/classifier.py"])
def test_aggregators_reject_missing_alias_and_leave_results_untouched(script):
    pytest.importorskip("pandas")
    if "classifier" in script:
        pytest.importorskip("sklearn")
        pytest.importorskip("matplotlib")
    before = {f: _sha(REPO / f) for f in RESULT_FILES}
    proc = subprocess.run([sys.executable, str(REPO / script),
                           "--aliases", "no-such-alias"],
                          cwd=REPO, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "no labeled *.jsonl" in proc.stderr
    assert {f: _sha(REPO / f) for f in RESULT_FILES} == before
    assert not (REPO / "results" / "figures" / "roc_no-such-alias.png").exists()


def test_run_all_aggregate_errors_when_no_labeled_outputs(tmp_path):
    # a copy of run_all.py in an empty directory has no evaluation/outputs/
    import shutil
    shutil.copy(REPO / "run_all.py", tmp_path / "run_all.py")
    proc = subprocess.run([sys.executable, str(tmp_path / "run_all.py"),
                           "--only", "aggregate"],
                          cwd=tmp_path, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "NOT rebuilt" in proc.stderr
    assert "run_all complete" not in proc.stdout


# ------------------------------------------------------------- config

def test_integration_config_is_valid_yaml_and_matches_reported_runs():
    yaml = pytest.importorskip("yaml")
    cfg = yaml.safe_load(open(REPO / "integration" / "config.yaml", encoding="utf-8"))
    assert [m["alias"] for m in cfg["models"]] == ALIASES
    assert cfg["max_new_tokens"] == 512 and cfg["batch_size"] == 1
    # the reported runs were native bf16, not 4-bit (see run_meta.json notes)
    assert all(m["load_4bit"] is False and m["dtype"] == "bfloat16"
               for m in cfg["models"])
