from datalens.results_view import (
    chart_for_evidence,
    evidence_preview,
    key_facts,
    metric_card_html,
    render_answer_html,
)


def test_answer_renders_lists_table_heading_and_arabic():
    sample = (
        "## النتائج\n- **العسل**: 300\n- الشاي: 80\n\n"
        "| المنتج | الإيراد |\n| --- | --- |\n| العسل | 300 |\n"
    )
    markup = render_answer_html(sample)
    assert 'dir="rtl"' in markup
    assert "<h3>النتائج</h3>" in markup
    assert "<strong>العسل</strong>" in markup
    assert "<li>الشاي: 80</li>" in markup
    assert '<table class="answer-table">' in markup


def test_answer_escapes_remote_markup():
    danger = '<img src="https://evil.test/img" onerror="alert(1)">'
    content = render_answer_html(
        danger + "\n![](https://evil.test/img.png)\n[click](https://evil.test)", False
    )
    assert "<img" not in content
    assert "&lt;img" in content
    assert 'dir="ltr"' in content
    assert "<a " not in content
    assert "![](https://evil.test/img.png)" in content
    assert "<script" not in render_answer_html("<script>alert(1)</script>")


def test_metric_values_are_escaped():
    result = metric_card_html('<script>', "<img src=x>", "<", "invalid<script>")
    assert "<script>" not in result
    assert "<img " not in result
    assert "kpi-neutral" in result
    assert "&lt;script&gt;" in result


def test_tables_charts_and_facts_use_real_tool_results():
    evidence = {
        "E1": {"tool": "aggregate_data", "result": {
            "groups": [{"product": "Honey", "revenue": 300},
                       {"product": "Tea", "revenue": 80}],
            "total_groups": 2,
        }},
        "E2": {"tool": "check_data_quality", "result": {
            "rows": 6, "duplicate_rows": 1,
        }},
    }
    assert key_facts(evidence) == [
        ("المجموعات", 2), ("الصفوف", 6), ("الصفوف المكررة", 1),
    ]
    kind, table = evidence_preview(evidence["E1"]["result"])
    assert kind == "groups" and table["revenue"].sum() == 380
    chart = chart_for_evidence(evidence["E1"]["result"])
    assert list(chart.index) == ["Honey", "Tea"]
    assert list(chart["revenue"]) == [300, 80]


def test_missing_or_non_numeric_data_does_not_create_chart_or_facts():
    assert chart_for_evidence({"groups": [{"branch": "A", "value": "unknown"}]}) is None
    assert chart_for_evidence({"groups": [
        {"branch": "A", "value": "unknown"}, {"branch": "B", "value": "missing"},
    ]}) is None
    assert evidence_preview({"groups": [], "rows": "not a list"}) is None
    assert key_facts({"E1": {"result": {"error": "missing column"}}}) == []
