# Security Policy

This is a research-replication repository, not a production system. There is no exposed network service, no authentication layer, and no sensitive data committed. The risk surface is low.

That said, if you discover a security-relevant issue (for example: a path-traversal bug in the dataset loaders, unsafe handling of downloaded files, or a leaked credential anywhere in the history), please report it responsibly.

## How to report

1. **Do NOT open a public issue** that describes the vulnerability.
2. Instead, contact one of the authors listed in `CITATION.cff` privately.
3. Include:
  - A description of the issue
  - The minimal reproducing input
  - The version (commit hash) where you observed the issue
4. We will acknowledge within 7 days and aim to release a fix within 30 days for verified issues.

## Credentials note

Running the gated models requires a personal HuggingFace token. Tokens must only ever live in Colab Secrets (`HF_TOKEN`) or the local HF credential cache - never in code, notebooks, configs, or commit history. If you accidentally commit one, revoke it at huggingface.co/settings/tokens immediately and report it as above.

## Out of scope

The following are not considered security issues for this project:

- Numerical differences between our results and the paper (documented in README "Replication notes" and the report in `report/`)
- Performance issues (slow generation runs)
- Compatibility issues with Python versions outside the supported range
- Use of permissive licenses (MIT / CC-BY 4.0) that allow commercial reuse
