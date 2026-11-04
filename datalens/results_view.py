"""Safe presentational helpers: model text and CSV cells never become executable HTML."""
import html
import math
import re
from collections.abc import Mapping

import pandas as pd


def _inline(value: str) -> str:
    text = html.escape(value, quote=True)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    return re.sub(r"\x60([^\x60]+)\x60", r"<code>\1</code>", text)


def _cells(line: str) -> list[str] | None:
    value = line.strip().strip("|")
    parts = [part.strip() for part in value.split("|")]
    return parts if "|" in line and len(parts) > 1 else None


def _separator(cells: list[str] | None) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", p) for p in cells)


def render_answer_html(answer: str, arabic: bool = True) -> str:
    """Render readable headings, lists and tables using escaped text, never Markdown HTML."""
    direction = "rtl" if arabic else "ltr"
    chunks = [f'<div class="answer-card" dir="{direction}">',
              '<div class="answer-card-accent" aria-hidden="true"></div>']
    lines = str(answer).splitlines()
    active_list = ""
    i = 0

    def close_list():
        nonlocal active_list
        if active_list:
            chunks.append(f"</{active_list}>")
            active_list = ""

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            close_list()
            i += 1
            continue
        headers = _cells(line)
        divider = _cells(lines[i + 1]) if i + 1 < len(lines) else None
        if headers and divider and len(headers) == len(divider) and _separator(divider):
            close_list()
            chunks.append('<div class="answer-table-scroll"><table class="answer-table"><thead><tr>')
            for cell in headers:
                chunks.append("<th>" + _inline(cell) + "</th>")
            chunks.append("</tr></thead><tbody>")
            i += 2
            while i < len(lines):
                cells = _cells(lines[i])
                if not cells or len(cells) != len(headers):
                    break
                chunks.append("<tr>")
                for cell in cells:
                    chunks.append("<td>" + _inline(cell) + "</td>")
                chunks.append("</tr>")
                i += 1
            chunks.append("</tbody></table></div>")
            continue
        heading = re.match(r"^#{1,4}\s+(.+)$", line)
        if heading:
            close_list()
            chunks.append("<h3>" + _inline(heading.group(1)) + "</h3>")
            i += 1
            continue
        bullet = re.match(r"^[-*•]\s+(.+)$", line)
        numbered = re.match(r"^\d{1,3}[.)]\s+(.+)$", line)
        kind = "ul" if bullet else "ol" if numbered else ""
        if kind:
            if active_list != kind:
                close_list()
                chunks.append(f"<{kind}>")
                active_list = kind
            item = bullet.group(1) if bullet else numbered.group(1)
            chunks.append("<li>" + _inline(item) + "</li>")
        else:
            close_list()
            chunks.append("<p>" + _inline(line) + "</p>")
        i += 1
    close_list()
    return "".join(chunks) + "</div>"


def metric_card_html(label: str, value: object, icon: str, tone: str = "") -> str:
    tone = tone if tone in {"main", "soft", "deep", "neutral"} else "neutral"
    return (
        f'<div class="kpi-card kpi-{tone}">'
        f'<div class="kpi-top"><span class="kpi-label">{html.escape(label)}</span>'
        f'<span class="kpi-icon" aria-hidden="true">{html.escape(icon)}</span></div>'
        f'<div class="kpi-value">{html.escape(str(value))}</div></div>'
    )


def evidence_preview(result: Mapping) -> tuple[str, pd.DataFrame] | None:
    """Return a table only when it was supplied by the MCP tool result."""
    for name in ("groups", "statistics", "rows", "sample"):
        rows = result.get(name)
        if isinstance(rows, list) and rows and all(isinstance(row, dict) for row in rows):
            return name, pd.DataFrame(rows)
    return None


def chart_for_evidence(result: Mapping) -> pd.DataFrame | None:
    """Use original group labels and finite numeric values from real MCP evidence."""
    rows = result.get("groups")
    if not isinstance(rows, list) or not 2 <= len(rows) <= 30:
        return None
    if not all(isinstance(row, dict) for row in rows):
        return None
    keys = list(rows[0])
    if len(keys) < 2 or any(set(row) != set(keys) for row in rows):
        return None
    label_key = next(
        (key for key in keys if all(isinstance(row[key], (str, type(None))) for row in rows)),
        keys[0],
    )
    value_key = next(
        (key for key in ["sum"] + [key for key in keys if key != label_key]
         if key != label_key and all(
             isinstance(row[key], (int, float)) and not isinstance(row[key], bool)
             and math.isfinite(row[key]) for row in rows)),
        None,
    )
    if value_key is None:
        return None
    return pd.DataFrame({
        label_key: [str(row[label_key]) for row in rows[:12]],
        value_key: [row[value_key] for row in rows[:12]],
    }).set_index(label_key)


_FACTS = {
    "rows": ("الصفوف", "Rows"),
    "duplicate_rows": ("الصفوف المكررة", "Duplicate rows"),
    "total_groups": ("المجموعات", "Groups"),
    "matching_rows": ("الصفوف المطابقة", "Matching rows"),
}


def key_facts(evidence: Mapping, arabic: bool = True) -> list[tuple[str, int]]:
    """Show at most three actual integer tool facts, never inferred currency or totals."""
    facts, seen = [], set()
    for entry in evidence.values():
        result = entry.get("result", {})
        if not isinstance(result, dict):
            continue
        for key, labels in _FACTS.items():
            value = result.get(key)
            if key not in seen and isinstance(value, int) and not isinstance(value, bool):
                facts.append((labels[0] if arabic else labels[1], value))
                seen.add(key)
            if len(facts) == 3:
                return facts
    return facts
