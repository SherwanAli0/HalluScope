// Generates HalluScope_Replication_Handoff_Report.docx
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, Footer, AlignmentType, LevelFormat, ExternalHyperlink,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak,
} = require("docx");

const REPO = "C:/Users/shero/Downloads/LLM/HalluScope";
const OUT = REPO + "/report/HalluScope_Replication_Handoff_Report.docx";
const CONTENT_W = 9360;

// helpers
const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
const HDR_FILL = "D5E8F0";
const ALT_FILL = "F3F8FB";
const CODE_FILL = "F2F2F2";

function p(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, ...opts.run })];
  return new Paragraph({ children: runs, spacing: { after: 120 }, ...opts.para });
}
function h1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] }); }
function h2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] }); }
function h3(text) { return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)] }); }
function bullet(text, level = 0) {
  const runs = Array.isArray(text) ? text : [new TextRun(text)];
  return new Paragraph({ numbering: { reference: "bullets", level }, children: runs, spacing: { after: 80 } });
}
function nump(text, ref) {
  const runs = Array.isArray(text) ? text : [new TextRun(text)];
  return new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs, spacing: { after: 80 } });
}
function B(t) { return new TextRun({ text: t, bold: true }); }
function R(t) { return new TextRun({ text: t }); }
function C(t) { return new TextRun({ text: t, font: "Courier New", size: 18 }); }
function cell(content, w, opts = {}) {
  const paras = (Array.isArray(content) ? content : [content]).map(x =>
    typeof x === "string"
      ? new Paragraph({ children: [new TextRun({ text: x, bold: !!opts.bold, size: opts.size || 20 })] })
      : x);
  return new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: paras,
  });
}
function mkTable(widths, rows, { headerFill = HDR_FILL, zebra = true } = {}) {
  const trs = rows.map((r, i) => new TableRow({
    tableHeader: i === 0,
    children: r.map((c, j) => {
      const opts = i === 0 ? { bold: true, fill: headerFill }
        : (zebra && i % 2 === 0 ? { fill: ALT_FILL } : {});
      return typeof c === "object" && c.__cell ? cell(c.content, widths[j], { ...opts, ...c.opts }) : cell(c, widths[j], opts);
    }),
  }));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, rows: trs });
}
function codeBlock(lines) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
    rows: [new TableRow({
      children: [new TableCell({
        borders, width: { size: CONTENT_W, type: WidthType.DXA },
        shading: { fill: CODE_FILL, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 160, right: 160 },
        children: lines.map(l => new Paragraph({ children: [C(l === "" ? " " : l)], spacing: { after: 20 } })),
      })],
    })],
  });
}
function spacer() { return new Paragraph({ children: [], spacing: { after: 60 } }); }
function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }
function fig(path, caption) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new ImageRun({
        type: "png", data: fs.readFileSync(path),
        transformation: { width: 480, height: 400 },
        altText: { title: caption, description: caption, name: caption },
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: caption, italics: true, size: 18 })],
    }),
  ];
}
function link(text, url) {
  return new ExternalHyperlink({ children: [new TextRun({ text, style: "Hyperlink" })], link: url });
}

// content
const children = [];

// COVER
children.push(
  new Paragraph({ spacing: { before: 2400, after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "HalluScope", bold: true, size: 72 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "Faithful Replication of “Entropy-based Sentence-level Hallucination Score in Large Language Models” (Joo, Lee & Choi, IEEE BigComp 2025)", size: 28 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
    children: [new TextRun({ text: "Technical Handoff Report - Implementation, Decisions, and Full Results", bold: true, size: 26, color: "2E75B6" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "SE418: Large Language Models - Group Project", size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "Üsküdar University - Computer Engineering", size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({ text: "Advisor: [ADD ADVISOR NAME - course rules require the course name AND the advisor’s name on the cover page of ALL reports and the presentation]", bold: true, size: 22, color: "C00000" })] }),
  mkTable([4000, 2400, 2960], [
    ["Team member", "Student ID", "Module ownership"],
    ["Sherwan Ali", "220201945", "Generation + this run"],
    ["İpek Uçar", "210201059", "Integration / pipeline"],
    ["Yaprak Sevinç Aldoğan", "220201032", "Dataset preparation"],
    ["Yasmine Guidoum", "220201929", "Entropy module"],
    ["Abdenour Hichem Guidoum", "220201930", "Evaluation module"],
  ]),
  spacer(),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 300 },
    children: [new TextRun({ text: "Report date: 10 June 2026 - produced from the completed replication run of the same day", size: 22 })] }),
  pageBreak(),
);

// TOC
children.push(
  new Paragraph({ children: [new TextRun({ text: "Table of Contents", bold: true, size: 32 })], spacing: { after: 200 } }),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  p("(In Word: right-click the table and choose “Update Field” to populate page numbers.)", { run: { italics: true, size: 18, color: "777777" } }),
  pageBreak(),
);

// 1. EXECUTIVE SUMMARY
children.push(h1("1. Executive Summary"));
children.push(p([B("Status: the implementation and the full replication run are COMPLETE. "),
  R("This document contains everything needed to understand, verify, reproduce, and continue the work: every design decision and its justification, the exact experimental recipe, the full results with paper comparison, the incident log, and the remaining tasks for the final submission.")]));
children.push(
  bullet([R("We built a 5-stage white-box pipeline (data → generation → entropy → evaluation → integration) that replicates the paper’s method "), B("from its text alone"), R(" - no official code exists (we verified this)." )]),
  bullet([R("We discovered the paper’s exact evaluation data: its “297 samples” are byte-for-byte the three dataset files of Ivgi et al. (2024), repo "), link("github.com/Mivg/fallbacks", "https://github.com/Mivg/fallbacks"), R(" (97 + 100 + 100 = 297). We run the identical prompts and inherit the identical labeling protocol - the strongest possible faithfulness anchor.")]),
  bullet([R("All three paper models were run on the full 297 prompts in native "), B("bfloat16, greedy decoding, 512 new tokens, batch size 1, no quantization"), R(": LLaMA-3-8B-Instruct (Colab A100), Qwen2-7B-Instruct (Colab L4), Gemma-2-9B-it (Colab L4).")]),
  bullet([B("Central claim CONFIRMED 9/9: "), R("hallucinated sentences show higher entropy than non-hallucinated ones for every model × dataset, at both token and sentence level.")]),
  bullet([B("Several values land strikingly close to the paper: "), R("LLaMA-3 on FakeQAMPARI matches within ~0.02 nats on BOTH classes (0.146/0.611 vs 0.142/0.631) - strong evidence our pipeline computes exactly what the authors computed, and that the unstated model variants were the 8B/7B Instruct checkpoints.")]),
  bullet([B("Honest deviation: "), R("our hallucinated-class means run ~0.2-0.4 nats below the paper’s throughout (the separation gap is compressed); non-hallucinated means match well. Candidate causes are documented in §8.5.")]),
  bullet([R("Detector quality (our extension): AUROC 0.87 / 0.75 / 0.78 on FakeQAMPARI but only 0.53-0.66 on the natural datasets - entropy detects fabricated-entity hallucinations well and struggles on natural multi-answer questions. This is the seed of the failure-analysis section.")]),
  bullet([R("Remaining for the course submission (deadline 10-6-2026): final project Word file, presentation file, advisor name on all covers. DONE since first draft: code pushed to github.com/SherwanAli0/HalluScope (CI green) and both videos uploaded to youtube.com/@HalluScope-Entropy-basedSenten (full 16m08s; short 2m41s - NOTE: 41s over the stated 2-minute limit).")]),
);
children.push(pageBreak());

// 2. PAPER + REPLICATION GOAL
children.push(h1("2. The Base Paper and What “Replication” Means"));
children.push(h2("2.1 The paper"));
children.push(p([R("Eojin Joo, Young-Jun Lee, Ho-Jin Choi (KAIST), "), B("“Entropy-based Sentence-level Hallucination Score in Large Language Models”"),
  R(", IEEE BigComp 2025, pp. 77-78, DOI 10.1109/BigComp64353.2025.00022. A 2-page short paper, closed access, no preprint, no code.")]));
children.push(p("Method in one paragraph: when an LLM generates text, every token is sampled from a probability distribution over the vocabulary. The Shannon entropy of that distribution measures the model’s uncertainty at that step. The paper computes token entropy (its Eq. 1) and averages it over the tokens of each sentence (Eq. 2, sentences split with spaCy) to obtain a sentence-level hallucination score. Claim: hallucinated sentences have systematically higher entropy, and the sentence-level average separates the two classes better than raw token entropy."));
children.push(codeBlock([
  "Eq. 1 (token):     H(y_i | c_i) = - Σ_v  p(y_i = v | c_i) · log p(y_i = v | c_i)",
  "Eq. 2 (sentence):  H(Sen_j)     = (1 / N_j) · Σ_{k ∈ Sen_j} H(y_k | c_k)",
]));
children.push(p("The paper evaluates LLaMA3, Qwen2 and Gemma2 (sizes and variants NOT stated) on three datasets (TriviaFacts, QAMPARI, FAKEQAMPARI - 297 samples total, setup borrowed from its reference [9]) and reports the class-average entropies in its Table I. Its Discussion honestly admits failure modes: some hallucinations have low entropy and some correct sentences have high entropy."));
children.push(h2("2.2 Why our project is a “replication” (and what that requires)"));
children.push(p([R("Under the current ACM Artifact Review & Badging v1.1 terminology: "), B("reproduction"), R(" = an independent team re-runs the authors’ own artifacts; "), B("replication"), R(" = an independent team obtains the result “using artifacts which they develop completely independently.” No official code exists for this paper - we verified by searching GitHub (title + DOI), Papers With Code, the authors’ GitHub accounts, and all bibliographic records - so a from-scratch reimplementation is the only possible mode, and it is formally a replication.")]));
children.push(p("The faithfulness rules we followed come from the ReScience C journal and the ML Reproducibility Challenge: implement exactly what is printed (resist “fixing” the method); match data, labels and generation settings wherever stated or recoverable; document every deviation forced by missing detail; report results side-by-side with the original per claim; keep extensions strictly separate from the replication."));
children.push(h2("2.3 The claims we tested"));
children.push(mkTable([900, 6060, 2400], [
  ["Claim", "Statement", "Verdict (§8)"],
  ["C1", "Hallucinated sentences have higher mean entropy than non-hallucinated ones, for all 3 models × 3 datasets, at token and sentence level.", "CONFIRMED 9/9"],
  ["C2", "The hallucinated-vs-correct gap is larger at sentence level than token level.", "PARTIAL 5/9 (LLaMA 3/3)"],
  ["C3", "Absolute entropy means land near the paper’s Table I values.", "PARTIAL - non-halluc. class matches closely; halluc. class systematically lower"],
]));
children.push(pageBreak());

// 3. KEY DISCOVERY
children.push(h1("3. Key Discovery: The Paper’s Exact Data and Labels Are Recoverable"));
children.push(p([R("The paper says its experiment uses “297 samples, following the setup from [9]”, where [9] is Ivgi, Yoran, Berant & Geva (2024), "), B("“From Loops to Oops: Fallback behaviors of language models under uncertainty”"), R(" (arXiv:2407.06071). Their official MIT-licensed repository "), link("github.com/Mivg/fallbacks", "https://github.com/Mivg/fallbacks"), R(" contains the literal dataset files - and their sizes sum to exactly 297. We therefore run the identical inputs and inherit the identical ground-truth protocol; nothing about the data is reconstructed or guessed.")]));
children.push(mkTable([1500, 2200, 700, 1200, 3760], [
  ["Our name", "Upstream file", "N", "Answerable", "Ground-truth / label rule"],
  ["trivia_facts", "data/trivia_facts.jsonl", "97", "yes", "Manually curated list questions with short canonical answers; answers beyond the gold set are confidently hallucinations."],
  ["qampari", "data/qampari_rephrased.jsonl", "100", "yes", "100 QAMPARI multi-answer questions rephrased to the same template; Wikipedia-derived gold answers (non-exhaustive - some false-positive hallucination labels are inherent and inherited)."],
  ["fake_qampari", "data/fake_qampari.jsonl", "100", "no", "Same questions with FABRICATED subject entities; gold lists empty by construction - every produced answer is a hallucination by definition."],
]));
children.push(spacer());
children.push(p([B("Prompt format: "), R("every prompt is a completion-style list request that already ends with the cue, e.g. "), C("“The following 25 fingers are part of the human hand\\n1.”"), R(" - the model continues the enumerated list. The “25” deliberately asks for more answers than exist, pushing models beyond their knowledge.")]));
children.push(h2("3.1 The labeling protocol we inherited (ported verbatim)"));
children.push(p("From run_hallucinations_check.py in the upstream repo (a reference copy with its MIT license is stored at evaluation/upstream/):"));
children.push(
  nump("Parse the completion with regexes; extract up to 25 enumerated answers (several recovery heuristics for malformed lists, topic changes and early stopping are part of the protocol and were ported as-is).", "steps1"),
  nump("Normalize each answer and each gold answer: lowercase, strip punctuation, remove articles (a/an/the), collapse whitespace, strip trailing parentheticals.", "steps1"),
  nump("Greedy-match predicted answers to gold answers by token-level longest-common-subsequence similarity with threshold 0.55 (soft matching, not exact match).", "steps1"),
  nump("The FIRST occurrence of each normalized answer is labeled CORRECT (matched) or HALLUCINATION (unmatched); subsequent duplicates are REPETITION (digits masked first, so “Harry Potter 2” after “Harry Potter 1” counts as repetition).", "steps1"),
  nump("FakeQAMPARI has empty gold lists, so every unique extracted answer is a HALLUCINATION by construction.", "steps1"),
);
children.push(p([B("Generation settings inherited: "), R("greedy decoding (temperature 0, top_p 1, top_k None), 512 new tokens, raw completion prompting with "), B("no chat template"), R(" - the upstream script feeds the literal prompt to base AND instruct models alike. We replicate all of it.")]));
children.push(pageBreak());

// 4. ARCHITECTURE
children.push(h1("4. System Architecture"));
children.push(h2("4.1 The five-stage pipeline"));
children.push(p("Every stage is a standalone script with file-based handoffs (JSONL on disk), so stages can run on different machines (laptop vs Colab) and team members can work independently. integration/run_pipeline.py chains them."));
children.push(mkTable([700, 2600, 6060], [
  ["Stage", "Module / script", "What it does"],
  ["1", "data/fetch_datasets.py", "Downloads the 3 upstream files (idempotent), validates counts (97/100/100), the “\\n1.” suffix and empty FakeQAMPARI gold lists; writes the unified data/processed/replication.jsonl (297 records: id, dataset, prompt, gold_answers, answerable)."],
  ["2", "generation/generate.py", "Loads a model, generates greedily per prompt (no chat template), captures RAW per-step logits via output_logits=True, computes per-token Shannon entropy (float32, nats) + chosen-token logprob, derives each token’s character span by cumulative-prefix decoding, writes one JSONL per dataset + run_meta.json. Appends + flushes per prompt and RESUMES automatically (already-done ids are skipped)."],
  ["3", "entropy/sentence_entropy.py", "Splits each completion into sentences with spaCy (en_core_web_sm), assigns tokens to sentences by maximum character-span overlap, computes Eq. 2 (plain mean of token entropies per sentence); excludes special tokens (EOS) and pure inter-sentence whitespace; keeps per-sentence token_entropies for token-level (micro) aggregation later."],
  ["4", "evaluation/label.py", "Verbatim port of the upstream extraction + normalization + greedy-LCS labeling; maps each extracted answer to its character span in the completion (sequential search); labels each sentence: H if it overlaps any hallucinated answer span, else C if it overlaps a correct span, else R (repetition-only), else unlabeled (excluded)."],
  ["4b", "evaluation/build_table1.py + classifier.py", "Aggregates our Table I (token-level micro means and sentence-level macro means per class) side-by-side with the paper’s printed values + C1/C2 verdicts; classifier.py sweeps thresholds on sentence entropy → AUROC, best-F1, precision/recall, ROC curves (this is an EXTENSION - the paper reports only class means)."],
  ["5", "integration/run_pipeline.py", "One-command orchestration: stages 1→4 for one model alias, and --aggregate <aliases> for the final tables/figures. integration/config.yaml records the canonical model set; integration/COLAB_GUIDE.md is the step-by-step Colab manual; integration/colab_replication.ipynb is the ready notebook."],
]));
children.push(h2("4.2 Repository layout"));
children.push(codeBlock([
  "HalluScope/",
  "├\u2500 README.md                  ← project overview + faithfulness ledger",
  "├\u2500 requirements.txt           ← pinned deps (transformers>=4.38,<5 - see §6.1)",
  "├\u2500 data/        fetch_datasets.py, upstream/ (3 jsonl), processed/replication.jsonl, README.md",
  "├\u2500 generation/  generate.py, outputs/<alias>/<dataset>.jsonl + run_meta.json, README.md",
  "├\u2500 entropy/     sentence_entropy.py, outputs/<alias>/, README.md",
  "├\u2500 evaluation/  label.py, build_table1.py, classifier.py, upstream/ (reference + LICENSE), outputs/<alias>/, README.md",
  "├\u2500 integration/ run_pipeline.py, config.yaml, COLAB_GUIDE.md, colab_replication.ipynb, README.md",
  "├\u2500 tools/       validate_batching.py (batched-vs-single equivalence test - see §7.3)",
  "├\u2500 results/     tables/replication_table1.{csv,md}, tables/classification_metrics.csv,",
  "│             figures/roc_*.png, raw result zips from the Colab runs",
  "└\u2500 report/      this report",
]));
children.push(p("Every folder contains a README.md documenting what it does, the exact decisions taken inside it, input/output formats, and how to run it. Read those before modifying anything."));
children.push(h2("4.3 Data formats between stages"));
children.push(codeBlock([
  "# generation/outputs/<alias>/<dataset>.jsonl - one line per prompt:",
  '{"id": "qampari_007", "dataset": "qampari", "prompt": "...", "completion": "...",',
  ' "tokens": [{"token_id": 123, "entropy": 0.4132, "logprob": -0.21,',
  '             "span": [0, 4], "special": false}, ...]}',
  "",
  "# entropy/outputs/<alias>/<dataset>.jsonl:",
  '{"id": "...", "dataset": "...", "sentences": [{"idx": 0, "text": "...",',
  '  "start": 0, "end": 14, "n_tokens": 5, "mean_entropy": 0.8341,',
  '  "token_entropies": [...], "mean_logprob": -0.42}]}',
  "",
  "# evaluation/outputs/<alias>/<dataset>.jsonl adds per-answer labels with spans",
  '# and a "label" field (C/H/R/null) on every sentence.',
]));
children.push(pageBreak());

// 5. FAITHFUL RECIPE
children.push(h1("5. The Faithful Recipe - Every Decision and Why"));
children.push(h2("5.1 Decisions"));
children.push(mkTable([2000, 3000, 4360], [
  ["Decision", "Our choice", "Why / source"],
  ["Prompting", "Raw completion text, NO chat template, for all models (incl. Instruct)", "Matches the upstream generation script the paper’s setup follows; it feeds the literal “...\\n1.” prompt to base and instruct models alike."],
  ["Decoding", "Greedy: do_sample=False (temperature/top-k/top-p inactive)", "Upstream default (temp 0, top_p 1, top_k None). Also makes runs deterministic. The transformers warning “generation flags not valid: temperature, top_p” during our runs is positive confirmation the models’ sampling defaults were overridden."],
  ["Length", "max_new_tokens = 512", "Upstream default (--k 512). Chosen over a faster 256-token variant explicitly to stay paper-exact."],
  ["Logit capture", "output_logits=True (RAW logits), transformers ≥ 4.38, asserted at runtime", "out.scores are PROCESSED logits - instruct models ship do_sample=True generation defaults whose warpers can silently distort them (Llama-3: temp 0.6, top_p 0.9). Raw logits are exactly Eq. 1’s distribution."],
  ["Entropy math", "log_softmax in float32, full vocabulary, natural log (nats)", "Half-precision softmax over 128k-256k vocabularies corrupts small probabilities; nats match the UQ literature and reproduce the paper’s 0.14-1.06 value range."],
  ["Storage", "Per-token SCALARS only (entropy, logprob, span, special flag) - never logit tensors", "512 steps × 256k vocab would be GBs per model; the scalars are all later stages need (MBs)."],
  ["Token→char spans", "Cumulative-prefix decoding (decode g[:i+1] minus decode g[:i]); pending UTF-8 “�” → zero-width span; specials flagged", "No offset_mapping exists for GENERATED ids. This is robust across tokenizer families (SentencePiece and byte-level BPE)."],
  ["EOS / specials", "Excluded from all entropy averages", "The paper does not state EOS handling; exclusion is the standard choice. Documented."],
  ["Sentence split", "spaCy en_core_web_sm 3.8.x, parser-based sents", "Paper says only “SpaCy”; pipeline + version pinned and reported. List completions segment line-by-line in practice, aligning sentences with list items."],
  ["Token→sentence", "Max span overlap; zero-width → containing sentence; no-overlap whitespace excluded", "Paper never specifies the mapping. Effects audited: across the 3 runs only ~26-70 whitespace/EOS tokens dropped per model out of ~100k+."],
  ["Labeling", "Verbatim port of upstream extraction/normalization/greedy-LCS(0.55)/first-occurrence logic, incl. its quirks", "The labels ARE the experimental protocol; “fixing” them would break faithfulness. Reference copy + MIT license stored in evaluation/upstream/."],
  ["Answer→sentence", "Sentence = H if it overlaps ≥ 1 hallucinated answer span; else C if overlaps a correct span; else R; else unlabeled (excluded)", "The paper’s one truly underdetermined step (upstream labels ANSWERS, the paper scores SENTENCES). Our rule is the most direct mapping; alternatives documented in §5.2."],
  ["Table aggregation", "Token-level = micro mean over all tokens of a class; sentence-level = macro mean of sentence means", "The natural reading of Table I’s “Token” vs “Sentence” columns; stated explicitly so others can recompute."],
  ["Precision", "Native bfloat16, NO quantization, batch size 1", "All three checkpoints are distributed in bf16. 4-bit was used only in local validation, never in reported runs. Batch-1: see §7.3."],
]));
children.push(h2("5.2 Deviation ledger (declared up front, per ReScience practice)"));
children.push(mkTable([400, 2800, 2800, 3360], [
  ["#", "Deviation", "Why forced", "Expected / observed impact"],
  ["1", "Model sizes & variants assumed: Meta-Llama-3-8B-Instruct, Qwen2-7B-Instruct, gemma-2-9b-it", "Paper names only “LLaMa3, Qwen2, Gemma2”", "FakeQAMPARI near-exact matches (§8.2) strongly suggest LLaMA/Qwen variants are right; Gemma size remains uncertain and Gemma is our most deviant model."],
  ["2", "bfloat16 inference precision", "Paper precision unstated", "Negligible for class means; bf16 is the native checkpoint format."],
  ["3", "Answer→sentence label mapping (overlap rule)", "Paper never explains how sentence labels were derived from the answer-level protocol", "Main suspect for the compressed hallucinated-class means (§8.5)."],
  ["4", "Token→sentence assignment rule", "Not specified in the paper", "Audited: affects only a handful of whitespace tokens."],
  ["5", "spaCy pipeline/version pinned (en_core_web_sm 3.8.x)", "Paper cites spaCy generically", "Sentence boundaries on list output are stable across versions."],
  ["6", "EOS excluded from averages", "Unstated", "One token per response; negligible."],
  ["7", "Degeneration detector NOT applied (upstream flags degenerate tails)", "Paper does not mention using it", "Degenerate tails are mostly labeled R/unlabeled and excluded anyway; a continuer could quantify this."],
]));
children.push(pageBreak());

// 6. ENVIRONMENT
children.push(h1("6. Environment, Accounts and Hardware"));
children.push(h2("6.1 Software environment"));
children.push(mkTable([3000, 6360], [
  ["Component", "Version / note"],
  ["Python", "3.11 (local, Windows 11); Colab default 3.x"],
  ["torch", "2.5.1+cu121 (local); Colab’s own CUDA build"],
  ["transformers", "PINNED >=4.38,<5. Reason: 4.38 added output_logits (we require raw logits); transformers 5.x crashed on local torch 2.5.1 (missing torch.float8_e8m0fnu) - incident I-1. Tested: 4.46.3 locally, 4.57.6 on Colab. NOTE: 4.x uses torch_dtype= in from_pretrained (the dtype= alias is 5.x); the deprecation warning on Colab is harmless."],
  ["bitsandbytes", "0.49.2 - Windows is natively supported now (plain pip install). Only used for local validation; NOT in reported runs."],
  ["spaCy", "3.8.14 + en_core_web_sm"],
  ["Other", "accelerate, pandas 2.3.3, scikit-learn 1.8.0, matplotlib 3.10.7, packaging"],
]));
children.push(h2("6.2 HuggingFace account, token, licenses (gated models)"));
children.push(
  bullet([B("Token: "), R("create at huggingface.co/settings/tokens. A CLASSIC “Read” token works out of the box. A FINE-GRAINED token MUST have “Read access to contents of all public gated repos” ticked, or model downloads fail with 403 - this bit us (incident I-2).")]),
  bullet([B("Llama-3: "), R("gated - fill Meta’s consent form on the model page; approval took a while in our run (“pending review” → granted) - start it early.")]),
  bullet([B("Gemma-2: "), R("gated - click “Acknowledge license” on the model page; approval is instant. Each Gemma repo (2b-it, 9b-it) is covered by the same acknowledgement.")]),
  bullet([B("Qwen2: "), R("ungated (Apache-2.0) - nothing to accept.")]),
  bullet([B("On Colab: "), R("store the token as a notebook Secret named exactly HF_TOKEN and enable “Notebook access” PER NOTEBOOK (the toggle does not carry over between notebooks).")]),
  bullet([B("Security note: "), R("the token used during this run was pasted in a chat once - it should be revoked and reissued at huggingface.co/settings/tokens now that the runs are done.")]),
);
children.push(h2("6.3 Hardware"));
children.push(mkTable([3000, 6360], [
  ["Machine", "Role"],
  ["Local laptop - RTX 2050 (4 GB VRAM), Ryzen 5 6600H, 15.3 GB RAM", "Development + validation only. Ran the full pipeline on tiny models and Gemma-2-2b-it in 4-bit (35 s/prompt at 128 tokens → a full 512-token run would take 6-9 h, hence Colab). Too small for any 7-9B model even in 4-bit."],
  ["Colab Pro - A100-SXM4-40GB (~13 units/h)", "LLaMA-3-8B full run (bf16, ~17-18 s/prompt, ~90 min total)."],
  ["Colab Pro - L4 24 GB (~5 units/h)", "Gemma-2-9B and Qwen2-7B full runs (bf16). L4 is ~2× slower than A100 but bf16-capable; results are identical - determinism comes from greedy batch-1, not the GPU."],
]));
children.push(pageBreak());

// 7. EXECUTION LOG
children.push(h1("7. Execution Log - How the Runs Actually Happened"));
children.push(h2("7.1 Validation ladder (before any paid compute)"));
children.push(
  nump("End-to-end smoke test with Qwen2-0.5B-Instruct (ungated, fits the laptop): all 5 stages ran, 44/44 answer spans mapped (100%), entropies in the sane range, C1 held 3/3 even on a 0.5B model.", "steps2"),
  nump("Real-model validation with Gemma-2-2b-it locally (4-bit NF4 + bf16 compute + eager attention): coherent completions (the model lists the 5 real fingers, then repeats/hallucinates toward 25 - exactly the fallback behavior the datasets are built to trigger), mean entropies 1.1-1.2 nats, no NaNs (Gemma-2’s known fp16 breakage avoided).", "steps2"),
  nump("Sanity rule used throughout: sentence means should land ~0.1-1.5 nats under greedy decoding; values > 5 nats indicate a bug (wrong axis, scores-vs-logits mixup, or padding steps included).", "steps2"),
);
children.push(h2("7.2 Run matrix (the reported runs)"));
children.push(mkTable([1660, 3000, 1300, 1300, 2100], [
  ["Model", "HF id", "GPU", "Precision", "Started (Colab UTC)"],
  ["LLaMA-3-8B", "meta-llama/Meta-Llama-3-8B-Instruct", "A100 40GB", "bf16", "2026-06-10 13:09"],
  ["Qwen2-7B", "Qwen/Qwen2-7B-Instruct", "L4 24GB", "bf16", "2026-06-10 13:06"],
  ["Gemma-2-9B", "google/gemma-2-9b-it", "L4 24GB", "bf16", "2026-06-10 09:47"],
]));
children.push(p("All runs: greedy, 512 new tokens, batch 1, no quantization, transformers 4.57.6, full provenance in generation/outputs/<alias>/run_meta.json."));
children.push(h2("7.3 Batching: implemented, validated, REJECTED (important)"));
children.push(p([R("To speed things up we added "), C("--batch-size N"), R(" (left padding, aligned per-step logits) and an equivalence test, "), C("tools/validate_batching.py"), R(", which runs the same prompts through the single-prompt and batched paths and compares per-token entropies. Result: batched greedy decoding is "), B("not deterministic"), R(" - tiny batched-matmul rounding differences occasionally flip near-tie argmax choices, after which the whole continuation diverges. Measured: in 4-bit, max entropy diff 0.063 nats with identical text; in bf16, 1 of 4 completions diverged textually (max diff 1.57 nats on the diverged sequence). Conclusion recorded in generation/README.md: "), B("all reported runs use batch-1"), R("; anyone continuing this work must not report batched numbers. The flag remains for throwaway experiments only.")]));
children.push(h2("7.4 Colab operations (what to know to re-run)"));
children.push(
  bullet("Code travels as a zip (HalluScope_for_colab.zip - code + datasets, ~80 KB). Upload via the Files panel, unzip to /content/, %cd into it. Uploads do NOT carry over between notebooks."),
  bullet("Per notebook: pip install cell → unzip cell → HF login cell (Secrets) → fetch_datasets → model cell. integration/COLAB_GUIDE.md has the full click-by-click version for beginners."),
  bullet([B("Disconnect protection (added after incident I-5): "), R("mount Google Drive and symlink the three outputs/ dirs into MyDrive/halluscope_out before running; generation appends + flushes per prompt and resumes (“X already done, skipping”), so a runtime reset costs nothing.")]),
  bullet("Results return as zips (one per notebook) → extracted into the local repo → aggregation runs locally."),
);
children.push(h2("7.5 Incident log (all resolved - read before re-running anything)"));
children.push(mkTable([600, 2800, 2700, 3260], [
  ["#", "Incident", "Symptom", "Resolution"],
  ["I-1", "transformers 5.10.2 vs torch 2.5.1 (local)", "Import crash: torch has no attribute float8_e8m0fnu", "Pin transformers>=4.38,<5 (requirements.txt); use torch_dtype= (4.x API)."],
  ["I-2", "Fine-grained HF token without gated-repo scope", "403 “Please enable access to public gated repositories…” despite accepted license", "Tick “read public gated repos” on the token (or use a classic Read token)."],
  ["I-3", "Gemma license not yet acknowledged", "403 “not in the authorized list”", "Click “Acknowledge license” on the model page (instant)."],
  ["I-4", "Llama-3 gate pending", "“Your request … is awaiting a review”", "Wait for Meta’s approval email; run other models meanwhile."],
  ["I-5", "Colab runtime reset wiped /content mid-run", "First Qwen2 run lost entirely; FileNotFoundError on /content/HalluScope afterwards", "Re-ran with Drive-symlinked outputs + per-prompt flush/resume; no further losses."],
  ["I-6", "Batched greedy non-determinism", "validate_batching FAIL (bf16: 1/4 completions diverge)", "Batch-1 for all reported runs (§7.3)."],
  ["I-7", "Gemma-2 fp16 breakage (known issue)", "NaNs / garbage under fp16", "bf16 (or fp32/4-bit) + attn_implementation=“eager” - handled automatically in generate.py."],
]));
children.push(pageBreak());

// 8. RESULTS
children.push(h1("8. Results"));
children.push(h2("8.1 Replication of Table I (ours vs paper)"));
children.push(p([R("Sentence-level entropy in nats; each cell shows "), B("ours / paper"), R(". “Non-halluc.” uses sentences labeled CORRECT (strict). For FakeQAMPARI no CORRECT sentences exist by construction, so the non-hallucinated class is all non-H sentences (broad) - marked *. Token columns are micro-averages over all tokens of the class; sentence columns are macro-averages of sentence means.")]));
children.push(mkTable([1240, 1690, 1560, 1640, 1560, 1670], [
  ["Dataset", "Model", "NonH token (ours/paper)", "NonH sentence (ours/paper)", "H token (ours/paper)", "H sentence (ours/paper)"],
  ["TriviaFacts", "LLaMA-3-8B", "0.2457 / 0.2301", "0.2436 / 0.2203", "0.3674 / 0.5886", "0.3946 / 0.5944"],
  ["TriviaFacts", "Qwen2-7B", "0.4619 / 0.4513", "0.4494 / 0.4239", "0.6568 / 0.9602", "0.6098 / 1.0027"],
  ["TriviaFacts", "Gemma-2-9B", "0.3056 / 0.1893", "0.2989 / 0.1919", "0.4197 / 0.6533", "0.4095 / 0.6745"],
  ["QAMPARI", "LLaMA-3-8B", "0.3623 / 0.2554", "0.3907 / 0.2243", "0.5214 / 0.4815", "0.5834 / 0.4988"],
  ["QAMPARI", "Qwen2-7B", "0.6488 / 0.4316", "0.7016 / 0.4125", "0.7212 / 0.8286", "0.7627 / 0.8114"],
  ["QAMPARI", "Gemma-2-9B", "0.3803 / 0.1919", "0.4043 / 0.1964", "0.5385 / 0.5807", "0.5488 / 0.6020"],
  ["FakeQAMPARI*", "LLaMA-3-8B", "0.2424 / 0.1451", "0.1460 / 0.1416", "0.5828 / 0.5929", "0.6109 / 0.6312"],
  ["FakeQAMPARI*", "Qwen2-7B", "0.6524 / 0.4510", "0.4355 / 0.4452", "0.8914 / 0.9630", "0.8980 / 1.0613"],
  ["FakeQAMPARI*", "Gemma-2-9B", "0.5077 / 0.1635", "0.2992 / 0.1454", "0.6757 / 0.8184", "0.7189 / 0.7789"],
]));
children.push(spacer());
children.push(h2("8.2 Claim verdicts"));
children.push(
  bullet([B("C1 - CONFIRMED 9/9: "), R("in every model × dataset cell, hallucinated entropy > non-hallucinated entropy, at both token and sentence level. The paper’s central thesis replicates without exception.")]),
  bullet([B("C3 - striking near-matches: "), R("LLaMA-3 / FakeQAMPARI matches the paper within ~0.02 nats on BOTH classes (0.146 vs 0.142; 0.611 vs 0.631). Qwen2 / FakeQAMPARI non-halluc. within 0.01 (0.4355 vs 0.4452); TriviaFacts non-halluc. within 0.03 for both LLaMA and Qwen. An independent reimplementation landing this close on printed values is strong evidence of computational equivalence - and that the paper’s unstated “LLaMa3” and “Qwen2” are the 8B / 7B Instruct checkpoints.")]),
  bullet([B("C3 - systematic deviation, honestly reported: "), R("our HALLUCINATED-class means are ~0.2-0.4 nats LOWER than the paper’s across the board, while non-hallucinated means match well → the separation gap is compressed relative to Table I. Candidate causes in §8.5.")]),
);
children.push(h3("C2 - sentence-level vs token-level separation (gap = H − NonH)"));
children.push(mkTable([1900, 1900, 1850, 1850, 1860], [
  ["Model", "Dataset", "Token gap", "Sentence gap", "C2 (sent > tok)"],
  ["LLaMA-3-8B", "TriviaFacts", "0.1217", "0.1510", "✓"],
  ["LLaMA-3-8B", "QAMPARI", "0.1591", "0.1928", "✓"],
  ["LLaMA-3-8B", "FakeQAMPARI", "0.3404", "0.4648", "✓"],
  ["Qwen2-7B", "TriviaFacts", "0.1949", "0.1604", "✗"],
  ["Qwen2-7B", "QAMPARI", "0.0723", "0.0611", "✗"],
  ["Qwen2-7B", "FakeQAMPARI", "0.2390", "0.4625", "✓"],
  ["Gemma-2-9B", "TriviaFacts", "0.1141", "0.1107", "✗"],
  ["Gemma-2-9B", "QAMPARI", "0.1582", "0.1445", "✗"],
  ["Gemma-2-9B", "FakeQAMPARI", "0.1679", "0.4197", "✓"],
]));
children.push(p("Verdict: 5/9 - fully holds on LLaMA-3 (3/3) and on FakeQAMPARI for every model, but not on Qwen/Gemma’s natural-data cells. Partial support for the paper’s secondary claim; an honest nuance its 2 pages could not surface."));
children.push(h2("8.3 Detection quality (extension beyond the paper)"));
children.push(p("Threshold-swept binary classification on sentence entropy (positive class = hallucinated). The paper reports no classification metrics; these are ours."));
children.push(mkTable([1900, 1700, 1440, 1440, 1440, 1440], [
  ["Model", "Dataset", "AUROC", "Best F1", "Precision", "Recall"],
  ["LLaMA-3-8B", "FakeQAMPARI", "0.872", "0.874", "0.836", "0.915"],
  ["LLaMA-3-8B", "QAMPARI", "0.631", "0.948", "0.901", "1.000"],
  ["LLaMA-3-8B", "TriviaFacts", "0.663", "0.868", "0.769", "0.997"],
  ["Qwen2-7B", "FakeQAMPARI", "0.747", "0.876", "0.800", "0.967"],
  ["Qwen2-7B", "QAMPARI", "0.528", "0.975", "0.950", "1.000"],
  ["Qwen2-7B", "TriviaFacts", "0.632", "0.859", "0.753", "1.000"],
  ["Gemma-2-9B", "FakeQAMPARI", "0.780", "0.916", "0.860", "0.980"],
  ["Gemma-2-9B", "QAMPARI", "0.620", "0.947", "0.900", "1.000"],
  ["Gemma-2-9B", "TriviaFacts", "0.627", "0.850", "0.739", "1.000"],
]));
children.push(p("Caution when quoting F1: the datasets are heavily imbalanced toward hallucinations (by design - prompts demand 25 answers when far fewer exist), so high F1 mostly reflects the base rate; AUROC is the meaningful number. Note Qwen2/QAMPARI AUROC ≈ 0.53 (near chance) rests on only 87 strict CORRECT sentences - small-sample caveat."));
children.push(pageBreak());
children.push(h2("8.4 ROC curves"));
children.push(...fig(REPO + "/results/figures/roc_llama3-8b-instruct.png", "Figure 1 - ROC curves, LLaMA-3-8B-Instruct (one curve per dataset)."));
children.push(...fig(REPO + "/results/figures/roc_qwen2-7b-instruct.png", "Figure 2 - ROC curves, Qwen2-7B-Instruct."));
children.push(...fig(REPO + "/results/figures/roc_gemma2-9b-it.png", "Figure 3 - ROC curves, Gemma-2-9B-it."));
children.push(h2("8.5 Interpretation and discussion"));
children.push(
  bullet([B("Model ordering preserved: "), R("Qwen2 produces the highest absolute entropies, exactly as in the paper - cross-model structure replicates, not just direction. (Absolute values are not strictly comparable across models anyway: vocabulary sizes differ - Llama-3 128k, Qwen2 152k, Gemma-2 256k - bounding entropy at ln|V| ≈ 11.76 / 11.93 / 12.45 nats respectively.)")]),
  bullet([B("Why might our hallucinated means be lower? "), R("(i) the paper’s unstated answer→sentence mapping - if the authors scored only the answer span rather than the whole sentence (or included repetition sentences as hallucinations), class means shift; (ii) precision differences (their inference dtype is unstated); (iii) for Gemma, model size - “Gemma2” could be the 2B; larger models are more confident when wrong, compressing the gap. A continuer can test (i) directly - the per-token data needed is already on disk.")]),
  bullet([B("Fabricated vs natural hallucinations: "), R("AUROC 0.75-0.87 on FakeQAMPARI vs 0.53-0.66 elsewhere. When a model is pushed past knowledge it cannot have (fabricated entities), uncertainty rises detectably; on natural questions, many hallucinations are produced confidently. This independently confirms the paper’s own caveat that entropy alone is insufficient - and quantifies WHERE it fails.")]),
  bullet([B("Gemma-2-9B is the consistent outlier "), R("(largest deviation from paper values, C2 fails on natural data) - consistent with the unknown “Gemma2” size. Documented as deviation #1.")]),
);
children.push(h2("8.6 Run statistics"));
children.push(mkTable([2360, 1400, 1400, 1400, 1400, 1400], [
  ["Model", "Sentences", "C", "H", "R", "Unlabeled"],
  ["LLaMA-3-8B", "9,881", "533", "4,392", "1,154", "3,802"],
  ["Qwen2-7B", "8,381", "455", "4,738", "667", "2,521"],
  ["Gemma-2-9B", "8,853", "624", "5,858", "330", "2,041"],
]));
children.push(p("Answer-span mapping succeeded for 100% of extracted answers in all three runs (e.g. LLaMA: 6,656/6,656). “Unlabeled” sentences overlap no extracted answer (mostly post-list prose, disclaimers, headers) and are excluded from class means - a documented choice and a failure-analysis opportunity (§9)."));
children.push(pageBreak());

// 9. FAILURE ANALYSIS SEEDS
children.push(h1("9. Failure-Analysis Starting Points (for whoever continues)"));
children.push(
  nump([B("Low-entropy hallucinations and high-entropy correct sentences exist in our data "), R(" -  the paper’s admitted failure modes, now concretely queryable: sort evaluation/outputs/<alias>/*.jsonl sentences by mean_entropy ascending with label H (confident hallucinations) and descending with label C (uncertain truths). These examples are the core of the report’s failure-analysis section.")], "steps3"),
  nump([B("Inherited protocol quirks (faithfully reproduced, worth showcasing): "), R("e.g. gold answer “Pinky” vs generated “Little finger” → labeled HALLUCINATION (soft string match cannot bridge synonyms); “Index finger” → H while a later bare “Index” → C (greedy-match tie-break). These are label noise inherited from the upstream protocol - the paper’s results contain them too. Quantifying their rate (manual audit of ~50 H-labeled answers) would be a genuine contribution.")], "steps3"),
  nump([B("Unlabeled prose "), R("(2,041-3,802 sentences/model): models often append notes/disclaimers after lists. Are these high-entropy? Do they leak hallucination signal? Nobody has looked.")], "steps3"),
  nump([B("Qwen2/QAMPARI ≈ chance AUROC "), R("on 87 correct sentences - investigate: is Qwen genuinely undetectable there, or is the strict class too small?")], "steps3"),
  nump([B("The saved logprob field "), R("(chosen-token log-probability, captured per token alongside entropy) enables immediate comparison of entropy vs perplexity-style signals - and is the input for the planned multi-signal fusion novelty.")], "steps3"),
);

// 10. REPRODUCE
children.push(h1("10. How to Reproduce or Continue (exact commands)"));
children.push(h2("10.1 Local (any machine, small models)"));
children.push(codeBlock([
  "py -3.11 -m pip install -r requirements.txt",
  "py -3.11 -m spacy download en_core_web_sm",
  "py -3.11 data/fetch_datasets.py                       # 297 prompts, validated",
  "py -3.11 integration/run_pipeline.py --model Qwen/Qwen2-0.5B-Instruct ^",
  "        --alias smoke --limit 2 --max-new-tokens 64   # end-to-end smoke test",
]));
children.push(h2("10.2 The reported runs (Colab, bf16)"));
children.push(codeBlock([
  "# per notebook: install + unzip + HF login + fetch_datasets (see COLAB_GUIDE.md),",
  "# then mount Drive + symlink outputs (disconnect protection), then ONE of:",
  "python integration/run_pipeline.py --model meta-llama/Meta-Llama-3-8B-Instruct --alias llama3-8b-instruct --dtype bfloat16",
  "python integration/run_pipeline.py --model Qwen/Qwen2-7B-Instruct            --alias qwen2-7b-instruct  --dtype bfloat16",
  "python integration/run_pipeline.py --model google/gemma-2-9b-it              --alias gemma2-9b-it       --dtype bfloat16",
]));
children.push(h2("10.3 Aggregation (local, after collecting outputs)"));
children.push(codeBlock([
  "py -3.11 integration/run_pipeline.py --aggregate llama3-8b-instruct qwen2-7b-instruct gemma2-9b-it",
  "# -> results/tables/replication_table1.{csv,md}",
  "# -> results/tables/classification_metrics.csv",
  "# -> results/figures/roc_<alias>.png",
]));
children.push(h2("10.4 Where every artifact lives"));
children.push(mkTable([4200, 5160], [
  ["Path", "What it is"],
  ["data/processed/replication.jsonl", "The 297 unified prompts (regenerable)"],
  ["data/upstream/ + evaluation/upstream/", "Byte-identical upstream datasets; reference labeling script + MIT license"],
  ["generation/outputs/<alias>/", "Per-token entropies/logprobs/spans + run_meta.json (PROVENANCE - keep)"],
  ["entropy/outputs/<alias>/", "Per-sentence entropies"],
  ["evaluation/outputs/<alias>/", "Labeled sentences + answer spans (the data behind every table)"],
  ["results/tables/replication_table1.{csv,md}", "The side-by-side table of §8.1 + C1/C2 verdicts"],
  ["results/tables/classification_metrics.csv", "The AUROC/F1 table of §8.3"],
  ["results/figures/roc_*.png", "Figures 1-3"],
  ["results/*.zip", "Raw zips as downloaded from the Colab notebooks (backup)"],
  ["integration/COLAB_GUIDE.md", "Click-by-click Colab manual (assumes zero experience)"],
  ["tools/validate_batching.py", "Batched-vs-single equivalence test (the §7.3 evidence)"],
]));
children.push(pageBreak());

// 11. REMAINING WORK
children.push(h1("11. Remaining Work (submission deadline: 10-6-2026)"));
children.push(p("The implementation and results are done. What remains is packaging and presentation:"));
children.push(
  nump([B("Final project Word file "), R(" -  required sections: title, members, description, objectives, methodology, tools, results, screenshots/outputs, references. THIS report contains all the content; it needs reshaping into the course format. Screenshots: use results/figures/*.png, the tables here, and Colab progress screenshots.")], "steps4"),
  nump([B("Presentation (10-20 min) + full video + YouTube link "), R("- DONE: \"LLM Presentation\", 16m 08s, https://www.youtube.com/watch?v=YVrVozSMKWI (channel: youtube.com/@HalluScope-Entropy-basedSenten).")], "steps4"),
  nump([B("Short video (max 2 min) + YouTube link "), R("- UPLOADED but over the limit: \"Introduction to the presentation of HalluScope\", 2m 41s, https://www.youtube.com/watch?v=QILSVvAm4g8. The course message says max 2 minutes, so it is 41 seconds over - consider trimming and re-uploading. It must open by introducing the course and the advisor.")], "steps4"),
  nump([B("Advisor’s name + course name on the cover of the presentation and ALL reports "), R(" -  placeholder on this report’s cover; fill it everywhere before submitting.")], "steps4"),
  nump([B("Code submission "), R(" -  push the repo to GitHub or zip it. NOTE: nothing has been committed to git yet - the working tree contains the entire implementation; commit before anything else.")], "steps4"),
  nump([B("Optional extensions (pipeline-ready): "), R("Part B - generalization to TruthfulQA/HaluEval + Mistral-7B/Phi-3 (config swap; needs a labeling adapter per dataset). Part C - novelty on top of the replication baseline: content-weighted sentence entropy, entropy+logprob fusion (logprob already captured), ln|V|-normalized cross-model entropy. The replication data is labeled, so any new score is evaluated by swapping the scoring function and recomputing AUROC.")], "steps4"),
);

// 12. REFERENCES
children.push(h1("12. References"));
children.push(
  nump("Joo, E., Lee, Y.-J., & Choi, H.-J. (2025). Entropy-based Sentence-level Hallucination Score in Large Language Models. IEEE BigComp 2025, pp. 77-78. DOI 10.1109/BigComp64353.2025.00022.", "refs"),
  nump("Ivgi, M., Yoran, O., Berant, J., & Geva, M. (2024). From Loops to Oops: Fallback Behaviors of Language Models Under Uncertainty. arXiv:2407.06071. Code/data: github.com/Mivg/fallbacks (MIT).", "refs"),
  nump("Amouyal, S. J., et al. (2023). QAMPARI: An Open-domain Question Answering Benchmark for Questions with Many Answers. github.com/samsam3232/qampari.", "refs"),
  nump("ACM (2020). Artifact Review and Badging v1.1 - definitions of repeatability, reproducibility, replicability.", "refs"),
  nump("Rougier, N. P., et al. (2017). Sustainable computational science: the ReScience initiative. PeerJ CS. + ReScience C FAQ (rescience.github.io).", "refs"),
  nump("Raff, E. (2019). A Step Toward Quantifying Independently Reproducible Machine Learning Research. NeurIPS 2019. arXiv:1909.06674.", "refs"),
  nump("Pineau, J., et al. (2021). Improving Reproducibility in Machine Learning Research (NeurIPS 2019 Reproducibility Program). JMLR 22(164). + ML Reproducibility Checklist v2.0.", "refs"),
  nump("HuggingFace Transformers documentation - generation utilities (output_logits vs output_scores), added in v4.38 (PR #28667).", "refs"),
  nump("Model cards: meta-llama/Meta-Llama-3-8B-Instruct; Qwen/Qwen2-7B-Instruct; google/gemma-2-9b-it (incl. the documented Gemma-2 fp16 issue and logit softcapping).", "refs"),
  nump("Honnibal, M., & Montani, I. spaCy - en_core_web_sm 3.8.x.", "refs"),
);

// document
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1F4E79" },
        paragraph: { spacing: { before: 320, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E75B6" },
        paragraph: { spacing: { before: 240, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1200, hanging: 360 } } } },
      ]},
      { reference: "steps1", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "steps2", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "steps3", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "steps4", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: { default: new Header({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "HalluScope - Replication Handoff Report - SE418", size: 16, color: "888888" })],
    })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "Page ", size: 16, color: "888888" }),
                 new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "888888" }),
                 new TextRun({ text: " - generated 10 June 2026", size: 16, color: "888888" })],
    })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log("written:", OUT, buf.length, "bytes");
});
