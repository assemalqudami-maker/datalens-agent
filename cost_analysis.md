# Live cost analysis

Provider: Gemini; model: `gemini-3.5-flash-lite`.
Run time (UTC): 2026-11-03T00:43:29.179905+00:00

Standard paid-rate equivalent; not a billing receipt.
Source: https://ai.google.dev/gemini-api/docs/pricing

| Case | Status | Input tokens | Output + thinking | USD | Uncertain |
|---|---|---:|---:|---:|---|
| success_1 | completed | 8377 | 323 | 0.00332060 | False |
| quality | completed | 4492 | 215 | 0.00188510 | False |
| summary | completed | 6353 | 235 | 0.00249340 | False |
| comparison | completed | 10577 | 672 | 0.00485310 | False |
| filter | completed | 4589 | 331 | 0.00220420 | False |
| near_failure_recovery | completed | 6143 | 386 | 0.00280790 | False |
| explicit_failure | failed | 5875 | 261 | 0.00241500 | False |
| attack_cells | completed | 4400 | 253 | 0.00195250 | False |
| attack_path | completed | 6432 | 351 | 0.00280710 | False |
| attack_write | completed | 10634 | 543 | 0.00454770 | False |

Mean across all 10 attempted cases (including failures): $0.00292866.
Unknown-usage calls retain their reservation and must not be presented as exact measured usage.
Inspect traces and final answers manually; automated assertions do not prove immunity to all prompt injection.
