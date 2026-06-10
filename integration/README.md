# Stage 5 — Integration

**What this module does:** chains the file-based stages into one command,
holds the experiment configuration, and provides the Colab notebook used to
run the 7–9B replication models that don't fit local hardware.

## Files

| File | Role |
|---|---|
| `run_pipeline.py` | Runs data → generation → entropy → labeling for one model alias; `--aggregate` builds Table I + classifier metrics across aliases |
| `config.yaml` | The replication's experiment matrix: exact HF model ids, quantization, where each model runs, which are gated |
| `colab_replication.ipynb` | Self-contained Colab notebook (free T4) for the three replication models |

## Execution matrix

| Model (paper name) | HF checkpoint | Where | Why |
|---|---|---|---|
| LLaMa3 | `meta-llama/Meta-Llama-3-8B-Instruct` | Colab T4, 4-bit NF4 | ~16 GB fp16 — exceeds both local 4 GB and T4 fp16 |
| Qwen2 | `Qwen/Qwen2-7B-Instruct` | Colab T4, 4-bit NF4 | ~15 GB fp16 |
| Gemma2 | `google/gemma-2-9b-it` | Colab T4, 4-bit NF4 | fp16 is broken for Gemma-2; bf16 unsupported on T4 |
| Gemma2 (fallback) | `google/gemma-2-2b-it` | local RTX 2050, 4-bit | backup if Colab quota runs out (report as deviation) |

Identical 4-bit config for every model (NF4, double quant) — never mix
quantized and unquantized runs in one comparison.

## Colab workflow

1. Open `colab_replication.ipynb` in Google Colab, set runtime → T4 GPU.
2. Add your HF token as a Colab secret named `HF_TOKEN` (Llama-3 and Gemma-2
   are gated: accept both licenses on their HF model pages first).
3. Run all cells; each model takes roughly 1.5–3 h for 297 prompts × 512
   tokens. Generation **appends + flushes per prompt and resumes** after a
   disconnect — just re-run the cell.
4. The notebook zips `generation/outputs/` and saves it to Drive; download
   and unzip it into `generation/outputs/` locally, then run stages 3–4
   locally:

```
py -3.11 entropy/sentence_entropy.py --alias llama3-8b-instruct
py -3.11 evaluation/label.py        --alias llama3-8b-instruct
...
py -3.11 integration/run_pipeline.py --aggregate llama3-8b-instruct qwen2-7b-instruct gemma2-9b-it
```

## Smoke test (validates the whole pipeline in ~2 min, no gated access)

```
py -3.11 integration/run_pipeline.py --model Qwen/Qwen2-0.5B-Instruct --alias smoke --limit 2 --max-new-tokens 64
py -3.11 integration/run_pipeline.py --aggregate smoke
```
