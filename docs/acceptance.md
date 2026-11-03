# Acceptance and submission status

| Requirement | Implementation | Evidence/status |
|---|---|---|
| Public GitHub repo | `assemalqudami-maker/datalens-agent` | Public repository |
| One-page specification | `agent_spec.md` | Written |
| Single agent/tool loop | `datalens/agent.py` | Scripted tests + successful live Gemini evaluation |
| 5–10 tools | Seven MCP tools + final answer | Actual MCP discovery/integration tests |
| Five input tests | Parameterized integration tests | Five operations with actual CSV calculations |
| MCP server | `datalens/mcp_server.py` | Real stdio subprocess, MCP SDK pinned to 1.30.0 |
| SQLite memory | `datalens/storage.py` | Separate-process restart test |
| Permissions/audit/cost | Host and MCP checks | Approval, isolation, budget and redaction tests |
| Three hostile inputs | `sample_data/hostile.csv`, live evaluator | All three live hostile-input assertions passed |
| Streamlit | `app.py` | UI test; container health in CI |
| Public deployment | Railway + persistent `/data` volume | Live: `https://datalens-agent-production.up.railway.app`; latest deployment SUCCESS |
| Success/recovery/failure traces | `traces/*.jsonl` | Three verified live Gemini traces committed |
| Average cost | Provider usage metadata + tracker | Measured mean: $0.00292866 across 10 attempted cases |

## Remaining manual submission checks

1. Exercise the deployed UI once with a real request, a report approval, and a memory restore.
2. Record the required demonstration video/screenshots if requested by the course.
3. Email the repository and public deployment links to `llm4yemen@gmail.com` with subject `Full Name - Track B - Week 5`, replacing Full Name with the student's actual name. This repository does not send email automatically.
