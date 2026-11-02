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
