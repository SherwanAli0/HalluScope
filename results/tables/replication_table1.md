# Replication of Table I - Joo, Lee & Choi (2025)

Entropy in nats. `ours` = this replication; `paper` = Table I as printed. Non-hallucinated class: `strict` = C sentences; for fake_qampari the strict class is empty by construction, so `broad` (all non-H sentences) is shown there (marked *).

| Dataset | Model | NonH tok (ours/paper) | NonH sent (ours/paper) | H tok (ours/paper) | H sent (ours/paper) | C1 | C2 |
|---|---|---|---|---|---|---|---|
| trivia_facts | gemma2-9b-it | 0.3056 / 0.1893 | 0.2989 / 0.1919 | 0.4197 / 0.6533 | 0.4095 / 0.6745 | ✓ | ✗ |
| trivia_facts | llama3-8b-instruct | 0.2457 / 0.2301 | 0.2436 / 0.2203 | 0.3674 / 0.5886 | 0.3946 / 0.5944 | ✓ | ✓ |
| trivia_facts | qwen2-7b-instruct | 0.4619 / 0.4513 | 0.4494 / 0.4239 | 0.6568 / 0.9602 | 0.6098 / 1.0027 | ✓ | ✗ |
| qampari | gemma2-9b-it | 0.3803 / 0.1919 | 0.4043 / 0.1964 | 0.5385 / 0.5807 | 0.5488 / 0.6020 | ✓ | ✗ |
| qampari | llama3-8b-instruct | 0.3623 / 0.2554 | 0.3907 / 0.2243 | 0.5214 / 0.4815 | 0.5834 / 0.4988 | ✓ | ✓ |
| qampari | qwen2-7b-instruct | 0.6488 / 0.4316 | 0.7016 / 0.4125 | 0.7212 / 0.8286 | 0.7627 / 0.8114 | ✓ | ✗ |
| fake_qampari | gemma2-9b-it* | 0.5077 / 0.1635 | 0.2992 / 0.1454 | 0.6757 / 0.8184 | 0.7189 / 0.7789 | ✓ | ✓ |
| fake_qampari | llama3-8b-instruct* | 0.2424 / 0.1451 | 0.1460 / 0.1416 | 0.5828 / 0.5929 | 0.6109 / 0.6312 | ✓ | ✓ |
| fake_qampari | qwen2-7b-instruct* | 0.6524 / 0.4510 | 0.4355 / 0.4452 | 0.8914 / 0.9630 | 0.8980 / 1.0613 | ✓ | ✓ |

**C1** (hallucinated > non-hallucinated, both levels): 9/9 model×dataset cells
**C2** (sentence-level gap > token-level gap): 5/9 cells
