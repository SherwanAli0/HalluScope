# Running the big models on Google Colab - complete beginner guide

Your laptop GPU (4 GB) can run **Gemma-2-2B** but **not** LLaMA-3-8B or
Qwen2-7B - those need ~16 GB. Google Colab gives you a bigger GPU in the
browser. With **Colab Pro**, pick an **A100 (40 GB)** and run every model in
its native **bf16** precision (no quantization) - this is both the fastest
option and the *most faithful* (no 4-bit deviation, fully deterministic). This
guide assumes **zero** prior Colab experience. Follow it top to bottom.

You will run **all three replication models** on Colab:
`LLaMA-3-8B-Instruct`, `Qwen2-7B-Instruct`, and `gemma-2-9b-it`.

---

## What you need before you start

- A Google account (the same one you use for Gmail) - Colab is free.
- Your Hugging Face account (`SherwanAli`) and the token you already made.
- The file `HalluScope_for_colab.zip` (in your `Downloads\LLM` folder).
- About **3 hours total**, but mostly hands-off waiting. Do one model, let
  it run, come back.

---

## STEP 0 - Accept the two gated licenses NOW (do this first, it can take time)

Two of the three models are "gated" - you must accept their licence before you
can download them. Do both now, before anything else, so they're ready by the
time you run the models.

**LLaMA-3** (Meta must approve you; usually minutes, occasionally longer):
1. Make sure you are logged in to Hugging Face as **SherwanAli**.
2. Open <https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct>
3. Near the top is a box asking you to share your info and agree to Meta's
   license. Fill the short form (name, country, etc.) and click agree / submit.
4. You'll see "Your request to access this model is pending" - that's fine,
   keep going. It usually flips to "granted" within a few minutes (you get an
   email).

**Gemma-2-9B** (instant approval, same as the 2B you already did):
5. Open <https://huggingface.co/google/gemma-2-9b-it>
6. Click **Acknowledge license** in the "Access Gemma" box. Approved
   immediately.

> Qwen2-7B is **not** gated - nothing to accept for it.
> Your existing `HF_TOKEN` already has gated access enabled, so no token change
> is needed.

---

## STEP 1 - Open Colab and create a notebook

1. Go to <https://colab.research.google.com>
2. If asked, sign in with your Google account.
3. A pop-up titled "Open notebook" may appear → click **New notebook**
   (bottom-left). If no pop-up, click **File → New notebook**.
4. You now have an empty notebook: a page with one empty grey box (a "cell")
   and a ▶ play button on its left. You type code in a cell and press the ▶
   button (or Shift+Enter) to run it.

---

## STEP 2 - Turn on the A100 GPU (very important)

Without this, the models will not run.

1. Menu bar → **Runtime** → **Change runtime type**.
2. A small window opens. Under **Hardware accelerator**, choose **A100 GPU**.
   (If A100 isn't offered, choose **L4** - also 24 GB and bf16-capable, just a
   bit slower. Avoid plain T4 here: 16 GB is too small for Gemma-2-9B in bf16.)
3. Click **Save**.

To confirm it worked, type this into the first cell and press ▶:

```
!nvidia-smi
```

You should see a table mentioning **A100-SXM4-40GB** (or **L4**) and a large
memory figure (40960 / 23034 MiB). If instead you see "command not found", the
GPU isn't on - redo this step.

> A100 costs ~13 Pro compute units/hour; all three models together use roughly
> **30-50 of your 100 units**. Plenty of margin.
> If A100s are momentarily unavailable, L4 works fine - same commands.

---

## STEP 3 - Give Colab your Hugging Face token (the safe way)

Colab has a "Secrets" feature so you don't paste your token into a code cell.

1. On the **left edge** of the screen there's a vertical strip of icons. Click
   the **key icon** 🔑 ("Secrets").
2. Click **+ Add new secret**.
3. In **Name** type exactly: `HF_TOKEN`
4. In **Value** paste your Hugging Face token (the `hf_...` string).
5. Turn **ON** the toggle **"Notebook access"** next to it.

That's it - the notebook can now read your token by the name `HF_TOKEN`.

---

## STEP 4 - Upload the code ZIP

1. On the left edge, click the **folder icon** 📁 ("Files").
2. A panel opens. Click the **upload icon** (a page with an up-arrow) at the
   top of that panel - OR just drag `HalluScope_for_colab.zip` from your
   Downloads folder into the panel.
3. Wait until the file `HalluScope_for_colab.zip` appears in the list. (A
   warning may say files are deleted when the runtime ends - that's normal.)

---

## STEP 5 - Run the setup cells

Now paste each block below into a **new cell** and press ▶, one at a time,
waiting for each to finish (the ▶ spinner stops and a number appears) before
the next. To add a new cell, click **+ Code** in the toolbar.

**5a - install the libraries** (takes ~2-3 minutes):

```
!pip install -q "transformers>=4.38,<5" accelerate bitsandbytes spacy packaging pandas scikit-learn matplotlib
!python -m spacy download en_core_web_sm -q
```

**5b - unzip the code and enter the folder:**

```
!unzip -o HalluScope_for_colab.zip -d /content/
%cd /content/HalluScope
```

You should see a list of files ending in the folder being entered.

**5c - log in to Hugging Face using your secret:**

```
from google.colab import userdata
from huggingface_hub import login
login(token=userdata.get("HF_TOKEN"))
print("logged in OK")
```

If it prints `logged in OK`, you're set. (If it errors about the secret,
re-check STEP 3 - the name must be exactly `HF_TOKEN` and "Notebook access"
must be on.)

**5d - build the dataset file:**

```
!python data/fetch_datasets.py
```

Should end with `[done] 297 prompts`.

---

## STEP 6 - Run the models (the long part)

Run these **one at a time**. Each prints progress like
`[50/297] ... mean H=0.43 nats (12s/prompt, ~50 min left)` so you can see it
working and how long is left.

Run order below puts the two **already-approved** models first, so you can
start immediately while LLaMA-3 waits on Meta.

**6a - Qwen2-7B** (no license needed - start here):

```
!python integration/run_pipeline.py --model Qwen/Qwen2-7B-Instruct --alias qwen2-7b-instruct --dtype bfloat16
```

**6b - Gemma-2-9B** (already approved):

```
!python integration/run_pipeline.py --model google/gemma-2-9b-it --alias gemma2-9b-it --dtype bfloat16
```

**6c - LLaMA-3-8B** (run once Meta approves you - otherwise it errors with
"gated"/"awaiting a review"):

```
!python integration/run_pipeline.py --model meta-llama/Meta-Llama-3-8B-Instruct --alias llama3-8b-instruct --dtype bfloat16
```

`--dtype bfloat16` runs the model in its native precision (no quantization) - 
fastest and most faithful. Each model takes roughly **40-75 min** on an A100
(downloads first ~5-10 min, then generates all 297 prompts at 512 tokens).
About **2-3 hours total** for all three, mostly unattended.

> **Want it faster?** You can run models in parallel: open a **second** Colab
> notebook (File → New notebook), repeat STEPS 1-5 in it, and run a *different*
> model there at the same time. Two A100 sessions ≈ half the wall-clock. Each
> session still uses batch-1, so results stay identical and faithful. (Uses
> units faster - fine within your 100.)

### If Colab disconnects partway (this is normal on the free tier)

The script **saves after every prompt and resumes**. If you get disconnected
or the cell stops:
1. Reconnect (top-right **Reconnect**, or **Runtime → Reconnect**).
2. If the runtime fully reset, re-run cells **5a, 5b, 5c** first (the uploaded
   ZIP survives a reconnect but not a full reset - if the ZIP is gone, re-upload
   it in STEP 4).
3. Re-run the same model cell (6a or 6b). It will say "X already done,
   skipping" and continue from where it stopped.

---

## STEP 7 - Download your results

After all three models finish, run this to package and download the outputs:

```
import os
os.chdir("/content/HalluScope")
!zip -qr /content/halluscope_outputs.zip generation/outputs entropy/outputs evaluation/outputs
from google.colab import files
files.download("/content/halluscope_outputs.zip")
```

Your browser downloads `halluscope_outputs.zip`. Move it into your
`Downloads\LLM\HalluScope` folder. Then tell me - I'll unzip it and build the
final Table I (side-by-side with the paper) and ROC curves from all three
models.

> Tip: you don't have to wait for all three. After each model finishes you can
> run STEP 7 to download what's done so far - the zip just includes whichever
> aliases exist. Good insurance against a late disconnect.

---

## Quick troubleshooting

| Symptom | Fix |
|---|---|
| `!nvidia-smi` errors / "no GPU" | STEP 2 not done, or no free GPU right now - set T4 and/or retry later |
| LLaMA cell: "gated"/"awaiting review"/403 | Meta hasn't approved STEP 0 yet - wait for the email, then re-run |
| "Cannot access gated repo ... token permissions" | Your token lacks gated access - fix at huggingface.co/settings/tokens (enable "read public gated repos"), update the `HF_TOKEN` secret |
| Cell about `HF_TOKEN` / `userdata` errors | Secret name must be exactly `HF_TOKEN` and "Notebook access" toggled on (STEP 3) |
| Runtime disconnected | Normal - see "If Colab disconnects" under STEP 6; just reconnect and re-run |
| "CUDA out of memory" | Very rare for bf16 batch-1 on a 40 GB A100. Re-run the cell; if it persists, **Runtime → Restart runtime**, re-run 5a-5c, then the model. On a smaller L4, restart between models so each starts with a clean GPU. |
| Lost everything after closing the tab | Colab wipes files when the runtime ends - re-upload the ZIP (STEP 4) and re-run from 5a. Already-downloaded results on your PC are safe. |
