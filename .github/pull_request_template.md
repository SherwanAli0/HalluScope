<!--
  Thanks for contributing! Please fill in this template so reviewers
  understand the change quickly.
-->

## What

<!-- One sentence describing the change. -->

## Why

<!-- The motivation. Link to an issue if one exists: "Closes #12" -->

## How

<!-- The approach. Mention any trade-offs or alternatives considered. -->

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature / capability
- [ ] Documentation update
- [ ] New replication hypothesis / failure-analysis addition
- [ ] Test addition or improvement
- [ ] Refactor (no functional change)
- [ ] Build / CI / tooling change

## Faithfulness check (replication path only)

- [ ] No change to the replication semantics (greedy batch-1 decoding, raw-logit entropy in fp32 nats, the ported labeling protocol, Eq. 2 plain-mean aggregation), OR the change is justified by a specific paper/upstream-protocol reference cited in this PR.
- [ ] The C1 sanity checks still pass in all 9 cells (`python -m pytest tests/ -v`).
- [ ] No extension/novelty (new scores, new datasets, new models) was mixed into the replication path — extensions live behind separate aliases/configs and are labeled as extensions.

## Tested

- [ ] All 12 sanity tests pass (`python run_all.py --tests` or `make tests`)
- [ ] If generation code changed: ran the smoke test (`make smoke`) and spot-checked entropy magnitudes (~0.05-1.5 nats sentence means)
- [ ] If aggregation changed: regenerated `results/` and diffed against the committed tables

## Reviewer checklist

- [ ] Branch follows the convention in BRANCHING.md
- [ ] No `__pycache__/`, stage outputs, or other generated files committed (only `evaluation/outputs/` and `results/` are tracked)
- [ ] No hardcoded local paths, no tokens/secrets
- [ ] Any new algorithmic code cites its source (paper equation, upstream script line, or library docs)
