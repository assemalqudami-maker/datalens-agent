# DataLens Agent — specification

**Goal:** Answer a user's CSV analysis question end to end using verifiable calculations, then optionally save an explicitly approved report.

**Domain:** Data analysis. **Architecture:** One Gemini agent; Python 3.12, Streamlit, pandas, a real MCP stdio server, SQLite. No multi-agent system. Arabic and English supported. Default model: `gemini-3.5-flash-lite` (configurable only with verified pricing).

## Allowed tools (8)

| Tool | Permission | Purpose |
|---|---|---|
| `inspect_dataset` | auto | Schema, types, row count, bounded sample |
| `check_data_quality` | auto | Missing values and duplicate counts |
| `summarize_numeric` | auto | Numeric count/sum/mean/min/max |
| `aggregate_data` | auto | Group and aggregate a selected column |
| `filter_rows` | auto | Literal/numeric filtering; no eval or SQL |
| `compare_groups` | auto | Compare numeric distributions by group |
| `save_report` | ask_on_write | Save a report after exact-content approval |
| `final_answer` | auto | Host-side terminal response with evidence IDs |

Seven data/report tools are discovered over MCP; the host adds `final_answer`. Tools never receive the model API key. Only the selected dataset in the current workspace is authorized.

## Termination and budget

All three controls are enforced simultaneously: `max_turns=10`, `budget=$0.10/task`, and a valid `final_answer`. Stop when **any** termination condition occurs. No unbounded retry; at most eight tool calls per model turn. Context limit: 24,000 tokens; output limit: 2,048 tokens. Shared daily application guard: $1.00. Before each generation, count input tokens including tools/system, reserve an overhead margin plus bounded output, and refuse calls exceeding the remaining budget. Settle using returned input and output+thinking usage. Missing usage or ambiguous failures retain their reservation and stop. This is an application guard, not a guarantee about external billing.

## Permissions, memory and data

Policy: **ask_on_write**. CSV analysis is automatic; saving a report pauses for a human decision. Approval is exact-content, one-use and expires after 10 minutes; enforced again by the MCP server. Internal audit/memory/cost bookkeeping is automatic. JSON schemas, dataset allowlisting and bounded tools enforce restrictions independently of model obedience. SQLite stores task summaries, approval grants and atomic cost reservations. A random workspace recovery key isolates memory; knowledge of this key grants access. Uploaded data is untrusted. Source files are not edited; no arbitrary code, shell, network, or filesystem tool exists.

## Three input → output success examples

Using the explicitly synthetic `sample_data/sales.csv`:

1. **“Rank products by total revenue.”** → Honey 300, Coffee 150, Tea 80, with tool evidence.
2. **“Check missing values and duplicates.”** → One missing `customer_note`, zero duplicate rows.
3. **“Compare branches and save a report.”** → Aden 320, Sanaa 210; preview → explicit approval → saved report ID. Declining creates no report.

**Explicit failure:** Exact profit requested for `missing_costs.csv` → explain that costs are absent; do not invent profit. **Recovery case:** Wrong `total_sales` column → retain the error in JSONL → inspect schema → use `revenue` → total 530. Live-provider outcomes must be captured, not fabricated.
