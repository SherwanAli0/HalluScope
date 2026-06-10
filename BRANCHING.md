# Branching model

This repository uses a simple integration-branch model sized for a five-person course team.

## Branches

| Branch | Purpose |
|---|---|
| `main` | The integration branch. Always green: all 12 sanity tests pass on every commit. The replication results published in README/results/ correspond to `main`. |
| `Ipek`, `Yaprak`, `Sherwan`, `Yasmine`, `Hichem` | Personal working branches, one per team member (created at project start). Use them for work-in-progress; merge into `main` via PR. |
| `<name>-<type>/<short-desc>` | Optional topic branches for focused changes, e.g. `sherwan-fix/span-alignment`, `ipek-docs/colab-guide`. |

## Rules

1. **Nothing lands on `main` without the tests passing.** Run `python run_all.py --tests` before merging; CI (`.github/workflows/tests.yml`) runs the same suite on every push/PR to `main` across 3 OSes x 3 Python versions.
2. **One logical change per PR.** Reference the issue it addresses. Use the PR template's faithfulness checklist.
3. **The replication path is frozen by default.** Changes to generation/entropy/labeling semantics need a paper-text justification (see CONTRIBUTING.md). Extension work (Part B datasets/models, Part C novelty scores) goes in topic branches and lands behind separate aliases/configs so the replication numbers stay untouched.
4. **Generated files stay out of git** except the two tracked artifact sets: `evaluation/outputs/` (labeled per-sentence data) and `results/` (tables + figures). If you regenerate results, commit the regenerated tables/figures in the same PR as the change that altered them, so reviewers see the numeric diff.
5. **No force-pushes to `main`.** Personal branches are yours to rebase as you like.

## Typical flow

```bash
git switch Sherwan                  # or a topic branch off main
# ...work...
python run_all.py --tests           # all 12 must pass
git push origin Sherwan
# open PR -> main, fill the template, get a review, merge
```

## History note

The initial scaffold (folder structure + README) was committed in April 2026; the full implementation, the three model runs, the results, and this governance layer landed in June 2026. See `CHANGELOG.md`.
