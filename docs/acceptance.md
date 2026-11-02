# Acceptance and remaining submission work

| Requirement | Implementation | Evidence/status |
|---|---|---|
| Public GitHub repo | `assemalqudami-maker/datalens-agent` | Public repository |
| One-page specification | `agent_spec.md` | Written |
| Single agent/tool loop | `datalens/agent.py` | Scripted-provider loop tests; live provider pending |
| 5–10 tools | Seven MCP tools + final answer | Actual MCP discovery/integration tests |
| Five input tests | Parameterized integration tests | Five operations with actual CSV calculations |
| MCP server | `datalens/mcp_server.py` | Real stdio subprocess, MCP SDK pinned to 1.30.0 |
| SQLite memory | `datalens/storage.py` | Separate-process restart test |
| Permissions/audit/cost | Host and MCP checks | Approval, isolation, budget and redaction tests |
| Three hostile inputs | `sample_data/hostile.csv`, live evaluator | Enforcement tests passed; live LLM attacks pending |
| Streamlit | `app.py` | UI test; container health in CI |
| Public deployment | Railway configuration and persistent volume | See README for current deployment state |
| Success/recovery/failure traces | Live workflow creates them | Real provider evidence pending API key |
| Average cost | Formula and tracker implemented | No measured live average yet |

## Finalization after adding a real key

1. Run **Live Gemini evaluation** from GitHub Actions (default cap $0.10 per case, $1.00 total daily ledger).
2. Download `live-evidence`; inspect `evaluation.json` and all failed cases.
3. Confirm `success_1.jsonl` ends completed with correct numbers, `near_failure_recovery.jsonl` preserves a real tool error followed by correction, and `explicit_failure.jsonl` honestly ends failed for missing costs.
4. Copy those three unchanged traces to `traces/` and replace the pending root cost report with the measured report. Never rename an unrelated successful run as recovery.
5. If the model doesn't follow the recovery-test setup, retain that attempt, diagnose it and re-run; do not manufacture a tool error after the fact.
6. Exercise the deployed UI with a real request, a report approval and a memory restore. Record the screen if useful or if hosting becomes unavailable.
7. Email links in the body to `llm4yemen@gmail.com`, subject `Full Name - Track B - Week 5`, replacing Full Name with the student's actual name. State any remaining gaps. This repository does not send email automatically.
