from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_ui_loads_and_reports_missing_key(tmp_path, monkeypatch):
    monkeypatch.setenv("DATALENS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=30).run()
    assert not app.exception
    assert len(app.dataframe) == 1
    analyze = next(b for b in app.button if "حلّل" in b.label)
    analyze.click().run()
    assert not app.exception
    assert any("GEMINI_API_KEY" in e.value for e in app.error)


def test_ui_renders_safe_results_and_evidence(tmp_path, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setenv("DATALENS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    trace = tmp_path / "trace.jsonl"
    trace.write_text('{"event":"complete"}\n', encoding="utf-8")
    result = SimpleNamespace(
        status="completed", turns=2, input_tokens=100, output_tokens=30,
        cost=0.0015, uncertain_cost=False,
        answer="## Findings\n- Honey: 300\n<script>alert(1)</script>",
        evidence={"E1": {"tool": "aggregate_data", "result": {
            "groups": [{"product": "Honey", "revenue": 300},
                       {"product": "Tea", "revenue": 80}],
            "total_groups": 2,
        }}},
        events=[{"event": "tool_result", "tool": "aggregate_data"}],
        trace_path=str(trace), task_id="test-task",
    )
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=30)
    app.session_state["run"] = result
    app.run()
    assert not app.exception
    assert len(app.dataframe) >= 2
    assert any("kpi-card" in m.value for m in app.markdown)
    assert any("&lt;script&gt;" in m.value for m in app.markdown)
