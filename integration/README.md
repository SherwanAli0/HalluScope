# Stage 5 - Integration

**What this module does:** chains the file-based stages into one command,
holds the experiment configuration, and provides the Colab notebook used to
run the 7-9B replication models that don't fit local hardware.

## Files

| File | Role |
|---|---|
| `run_pipeline.py` | Runs data → generation → entropy → labeling for one model alias; `--aggregate` builds Table I + classifier metrics across aliases |
| `config.yaml` | Documentation of the experiment matrix: exact HF model ids, dtype/quantization, where each model runs, which are gated. Not read by any script. |
| `colab_replication.ipynb` | Self-contained Colab notebook for the three replication models (check its runtime/dtype cells against the matrix below before reusing it; `COLAB_GUIDE.md` describes the path actually used for the reported runs) |

## Execution matrix

| Model (paper name) | HF checkpoint | Where (reported run) | Why |
|---|---|---|---|
| LLaMa3 | `meta-llama/Meta-Llama-3-8B-Instruct` (gated) | Colab A100-40GB, bf16 | ~16 GB in bf16 - too big for a 4 GB local GPU or a T4 |
| Qwen2 | `Qwen/Qwen2-7B-Instruct` | Colab L4 24GB, bf16 | ~15 GB in bf16 |
| Gemma2 | `google/gemma-2-9b-it` (gated) | Colab L4 24GB, bf16 | fp16 is broken for Gemma-2; bf16 is not supported on a T4 |
| Gemma2 (fallback, not used) | `google/gemma-2-2b-it` | local RTX 2050, 4-bit | backup if Colab quota runs out (report as deviation, new alias) |

The reported runs used native bf16 with no quantization. The optional
`--load-4bit` path (NF4, double quant) was not used for reported results -
never mix quantized and unquantized runs in one comparison.

## Colab workflow

1. Open `colab_replication.ipynb` in Google Colab and pick a GPU that can hold the model in bf16 (A100 or L4; a T4 only works with the optional `--load-4bit` path, a different configuration).
2. Add your HF token as a Colab secret named `HF_TOKEN` (Llama-3 and Gemma-2
   are gated: accept both licenses on their HF model pages first).
3. Run all cells; each model takes roughly 1.5-3 h for 297 prompts × 512
   tokens. Generation **appends + flushes per prompt and resumes** after a
   disconnect - just re-run the cell.
4. The notebook zips `generation/outputs/` and saves it to Drive; download
   and unzip it into `generation/outputs/` locally, then run stages 3-4
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
