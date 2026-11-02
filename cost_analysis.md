# Cost analysis — live measurement pending

**Provider:** Google Gemini Developer API. **Default model:** `gemini-3.5-flash-lite`.
**Pricing checked:** 2026-11-03. [Official pricing](https://ai.google.dev/gemini-api/docs/pricing).

| Standard text pricing | USD per 1 million tokens |
|---|---:|
| Input | 0.30 |
| Output, including thinking | 2.50 |

The optional legacy `gemini-2.5-flash-lite` profile uses $0.10 input and $0.40 output per million, but availability depends on the account. Model selection never silently falls back. Verify access and rates before changing models.

## Calculation

`cost_usd = input_tokens × input_rate / 1,000,000 + (candidate_tokens + thinking_tokens) × output_rate / 1,000,000`

Every generation is recorded separately and summed per task, including failed attempts. Repeated prompt/context tokens are charged again. Cached input is conservatively counted at the standard input rate; no caching discount is assumed. No grounding/search APIs are used. Provider free-tier billing may be $0 even when this paid-rate equivalent is positive. Hosting is separate.

**Illustration only, not a measurement:** 2,000 input tokens and 500 output tokens at the default rates equal $0.00185.

## Budget enforcement

Default cap is $0.10/task and $1.00/day across the application. `count_tokens` includes system instructions and function declarations. Each generation reserves 115% of the counted input plus 512 input tokens and twice the configured output maximum. Atomic SQLite reservations prevent concurrent tasks from separately spending the same daily allowance. SDK retries are disabled. A timed-out call may still have incurred a provider charge: retain its reservation, mark cost uncertain, and stop. Missing usage metadata also stops the task. A process crash leaves its reservation intact. Guards rely on the configured rates and provider behavior; configure provider-side spending limits as well if required.

## Current measured results

**Live calls completed during initial build: 0. Average real task cost: unavailable.** No API key was available in the build environment. Tests use an explicitly labelled scripted model and a real MCP subprocess; their simulated token counts are not Gemini measurements. Do not use them to claim a real average cost or successful live-provider integration.

Run **Actions → Live Gemini evaluation** after adding the `GEMINI_API_KEY` repository secret. The workflow preserves all original JSONL traces, per-case tokens, failures and a generated `cost_analysis.md` in its `live-evidence` artifact. Review that evidence and replace this pending report with the real table before submission. The mean includes all attempted cases, not just successful ones; uncertain reservations are clearly marked.
