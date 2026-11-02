# ◈ DataLens Agent

[![Tests and MCP integration](https://github.com/assemalqudami-maker/datalens-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/assemalqudami-maker/datalens-agent/actions/workflows/ci.yml)

**اسأل بياناتك، وتابع كيف وصل الوكيل إلى الإجابة.**

A single-agent CSV analysis workspace for **LLM4Yemen · Track B · Week 5**. Arabic/English Streamlit interface, Gemini function calling, seven real MCP tools, SQLite memory, human approval for report writes, JSONL traces and token-based cost tracking.

## Current status

* Application, tests, GitHub workflows and deployment configuration are implemented.
* Real MCP calculations and enforcement tests run without a provider key, using a clearly labelled scripted model.
* **Live Gemini verification, the three final submission traces, and measured average cost are pending a valid API key.** A missing key produces an explicit configuration error, never fake AI results.
* Deployment URL/status will be added after Railway confirms a successful deployment.

## What it does

Upload a UTF-8 CSV (up to 5 MB), ask a question in Arabic or English, inspect the numerical evidence and cost, then approve or decline any proposed report save. Recover your previous task summaries after restarting using your private workspace key. Sample store data is synthetic and clearly labelled.

Examples:

* `رتّب المنتجات حسب إجمالي الإيرادات.`
* `Check missing values and duplicate rows.`
* `Compare branch revenues and prepare a report to save.`

The model picks tools; pandas computes the numbers. The application stops at a final answer, ten model turns, or the configured budget. Missing information is a valid explicit failure.

## Run locally (Python 3.12)

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux instead: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the displayed localhost URL. Enter your Gemini key in the password field, or copy `.env.example` to `.env` and set `GEMINI_API_KEY`. No source code needs editing. The key is never committed. Default model is `gemini-3.5-flash-lite`; if your account requires a different supported model, set `GEMINI_MODEL` with matching verified prices in `datalens/config.py`. A model being listed in documentation does not guarantee access for every account.

## GitHub Actions

**Tests and MCP integration** runs on pushes/PRs: lint, real MCP integration tests, permission/budget/memory tests, Streamlit test, and Docker startup health. It needs no secrets and does not claim live LLM connectivity.

**Live Gemini evaluation** is manually triggered:

1. Open [repository Actions secrets](https://github.com/assemalqudami-maker/datalens-agent/settings/secrets/actions).
2. Add `GEMINI_API_KEY` using **New repository secret**. Do not paste the key into an issue, README, or chat.
3. Open [Live Gemini evaluation](https://github.com/assemalqudami-maker/datalens-agent/actions/workflows/live.yml) → **Run workflow**.
4. Download `live-evidence`. It contains unchanged traces, per-case assertions and measured cost analysis. Missing credentials fail clearly. Review before copying the three required traces into `traces/`.

GitHub Actions secrets do **not** automatically become Railway variables. Set the deployment's `GEMINI_API_KEY` separately or use the UI's per-session key field. Optionally set `DATALENS_ACCESS_CODE` to restrict use of the deployment owner's key.

## Deployment

Railway builds the included Dockerfile from this repository. Mount a persistent volume at `/data` and set `DATALENS_DATA_DIR=/data`. The app binds to Railway's `PORT`; `/_stcore/health` is an application health check only. Use one replica with SQLite. Persistent storage is necessary for memory and budgets to survive container replacement. Hosting costs/quotas depend on your account and are separate from model token costs.

```bash
docker build -t datalens .
docker run --rm -p 8501:8501 -v datalens-data:/data --env-file .env datalens
```

## Tests and live evaluation

```bash
python -m pip install -r requirements-dev.txt
ruff check .
python -m pytest -q
python scripts/live_eval.py --output live-results
```

The last command requires a real key and may incur provider charges within the configured guard. It runs five success cases, recovery, missing-data failure, and three attacks. SDK retries are disabled; unknown usage keeps its reservation. A paused report requires actual user approval; automated evaluation declines writes.

## Project map

| Path | Purpose |
|---|---|
| `app.py` | Bilingual interface, approval and memory restore |
| `datalens/agent.py` | Bounded loop, permissions, evidence and cost |
| `datalens/provider.py` | Explicit Gemini adapter |
| `datalens/mcp_server.py` | Seven actual MCP tools |
| `datalens/storage.py` | SQLite memory, approvals, cost reservations, traces |
| `agent_spec.md` | Goal, tools, termination, budget, policy, examples |
| `cost_analysis.md` | Rates, formula, evidence status |
| `docs/architecture.md` | Architecture, privacy and practical limits |
| `docs/acceptance.md` | Requirement mapping and final submission steps |

## Privacy and limitations

CSV excerpts, tool results and recent memory snippets are sent to Gemini when analysis starts. Use authorized data. Workspace recovery keys grant access to that workspace's history; keep them private. API keys stay in session memory or server environment. Runtime files are ignored by Git. Host/server permissions restrict actions even if malicious data influences the model, but finite tests cannot establish immunity to every prompt injection.

This is a bounded capstone demo: no arbitrary code execution, multi-agent orchestration, Excel/OCR, automatic data cleanup, or large-scale multi-tenant authentication. Source data is not modified. Do not represent a deployment health check or scripted-model test as a live-provider success.

References: [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing), [Google Gen AI SDK](https://googleapis.github.io/python-genai/), [MCP Python SDK v1.30.0](https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0).
