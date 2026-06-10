---
name: Bug report
about: Report something that's broken or producing wrong numbers
title: "[BUG] "
labels: bug
assignees: ''
---

## What happened

<!-- A clear description of what went wrong. -->

## What you expected

<!-- What should have happened instead. Reference the paper section / Table I cell or the PIPELINE_CONTRACT.md interface if relevant. -->

## To reproduce

Steps to reproduce the behaviour:
1. Run `...`
2. Observe output `...`
3. Compare to expected `...`

## Error output / log

```
<paste any traceback or unexpected numbers here>
```

## Environment

- OS: <Windows / macOS / Linux / Colab>
- GPU (if generation): <none / T4 / L4 / A100 / local>
- Python version: <output of `python --version`>
- Repo commit: <output of `git rev-parse HEAD`>
- Pip freeze for the relevant packages:
  ```
  torch==
  transformers==
  spacy==
  pandas==
  ```

## Has a sanity test failed?

- [ ] `python -m pytest tests/` produces failures (paste below if yes)
- [ ] C1 (hallucinated > non-hallucinated entropy) broke in some cell
- [ ] Entropy values fall outside the sane range (~0.05 to 1.5 nats sentence means under greedy decoding)
- [ ] None of the above; this is a new failure mode
