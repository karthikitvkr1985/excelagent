"""Dashboard suggestion and spec generation.

We generate dashboard *specs* (JSON describing charts/layout), never arbitrary
code. The frontend renders those specs with ECharts, which keeps generation
safe and controllable.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Optional

import pandas as pd

from . import storage
from .llm import llm_available, llm_json


def suggest_dashboards(dataset_id: str) -> dict:
    df = storage.load_refined(dataset_id)
    doc = storage.load_doc(dataset_id) or {}
    if df is None:
        raise ValueError("Dataset not found.")

    context = _context_columns(dataset_id, df, doc)

    if llm_available():
        payload = llm_json(_suggest_prompt(context), _DASHBOARD_SYSTEM)
        suggestions = payload.get("suggestions", []) if isinstance(payload, dict) else []
    else:
        suggestions = _heuristic_suggestions(_role_columns(df))

    out = []
    for i, s in enumerate(suggestions, start=1):
        out.append(
            {
                "id": f"sugg-{i}",
                "title": s.get("title", f"Dashboard {i}"),
                "context": s.get("context", ""),
                "purpose": s.get("purpose", ""),
                "charts": s.get("charts", []),
            }
        )
    return {"dataset_id": dataset_id, "suggestions": out}


_DASHBOARD_SYSTEM = (
    "You design business intelligence dashboards. You return structured JSON. "
    "You map available columns to appropriate chart types."
)


def _suggest_prompt(context: dict) -> str:
    return f"""Given the dataset and its insights, propose 4-6 distinct dashboards that would be valuable.
Return JSON: {{"suggestions":[{{"title":"...","context":"who uses this and why","purpose":"primary question it answers","charts":["chart type hints"]}}]}}
Base chart choices on the actual columns.
DATASET:
{json.dumps(context, default=str, indent=2)}
"""


def _context_columns(dataset_id: str, df: pd.DataFrame, doc: dict) -> dict:
    dims = [str(c) for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_datetime64_any_dtype(df[c])]
    measures = [str(c) for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    dates = [str(c) for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    return {
        "columns": list(map(str, df.columns)),
        "dimensions": dims,
        "measures": measures,
        "dates": dates,
        "selected_rows": df.head(4).to_dict("records"),
        "summary": (doc or {}).get("summary", ""),
    }


def _role_columns(df: pd.DataFrame) -> list:
    """Column metadata dicts (name/role) derived without the LLM."""
    from .excel_parser import summarize_columns

    return summarize_columns(df)


def _heuristic_suggestions(columns: list) -> list:
    dims = [c for c in columns if c["role"] == "dimension"]
    measures = [c for c in columns if c["role"] == "measure"]
    dates = [c for c in columns if c["role"] == "date"]
    suggestions = []
    if dates and measures:
        suggestions.append(
            {
                "title": "Trend Dashboard",
                "context": "Track how key metrics evolve over time.",
                "purpose": "Spot trends and seasonality of numeric measures against the date dimension.",
                "charts": ["line", "bar", "area"],
            }
        )
    if dims and measures:
        suggestions.append(
            {
                "title": "Breakdown Comparison",
                "context": "Compare measures across categorical dimensions.",
                "purpose": "See which categories drive the numbers.",
                "charts": ["bar", "pie", "radar"],
            }
        )
    if not suggestions:
        suggestions = [
            {
                "title": "Data Overview",
                "context": "General overview of the dataset.",
                "purpose": "Get a quick grasp of the data.",
                "charts": ["table", "bar"],
            }
        ]
    return suggestions


def build_dashboard(dataset_id: str, suggestion_id: str = None, custom_scenario: str = None, title: str = None) -> dict:
    df = storage.load_refined(dataset_id)
    doc = storage.load_doc(dataset_id) or {}
    if df is None:
        raise ValueError("Dataset not found.")

    scenario = custom_scenario or "Standard summary of the key trends in this data."
    if suggestion_id:
        # try to recover the suggestion for richer context
        pass

    spec = _build_spec(dataset_id, df, doc, scenario, title)
    dashboard_id = "dash-" + uuid.uuid4().hex[:8]
    spec["dashboard_id"] = dashboard_id
    spec["created_at"] = time.time()

    meta = storage.load_meta(dataset_id) or {}
    meta.setdefault("dashboards", []).append(spec)
    storage.save_meta(dataset_id, meta)
    return spec


def _build_spec(dataset_id, df, doc, scenario, title) -> dict:
    context = _context_columns(dataset_id, df, doc)
    context["scenario"] = scenario
    context["title"] = title or "Custom Dashboard"

    if llm_available():
        payload = llm_json(_spec_prompt(context), _SPEC_SYSTEM)
    else:
        payload = _fallback_spec(context)

    if not isinstance(payload, list):
        payload = payload.get("charts", []) if isinstance(payload, dict) else []

    charts = _sanitize_charts(df, payload)
    for chart in charts:
        chart["data"] = _chart_data(df, chart)

    return {
        "dashboard_id": "",
        "title": title or "Custom Dashboard",
        "summary": _spec_summary(payload, scenario, doc),
        "layouts": charts,
    }


def _chart_data(df: pd.DataFrame, chart: dict) -> dict:
    """Aggregate the refined table into ECharts-ready data for a chart spec."""
    x = chart.get("x")
    y = chart.get("y")
    agg = chart.get("aggregation") or "sum"
    ctype = chart.get("type")

    if x is None or x not in df.columns:
        return {"x_data": [], "series": []}

    if y is not None and y in df.columns and pd.api.types.is_numeric_dtype(df[y]):
        if agg == "mean":
            grp = df.groupby(x, as_index=False)[y].mean()
        elif agg == "count":
            grp = df.groupby(x, as_index=False)[y].count()
        else:
            grp = df.groupby(x, as_index=False)[y].sum()
        grp = grp.dropna()
    elif y is not None and y in df.columns:
        # string y with count -> value counts of y grouped by x (top 10)
        top = df.groupby(x)[y].count().sort_values(ascending=False).head(10)
        grp = top.reset_index()
        grp.columns = [x, y]
    else:
        grp = df[x].value_counts().head(10).reset_index()
        grp.columns = [x, "count"]
        y = "count"

    x_data = [str(v) for v in grp[x].tolist()]
    if ctype == "pie":
        return {
            "x_data": x_data,
            "series": [{"name": str(grp[x].iloc[i]), "value": _num(grp[y].iloc[i])} for i in range(len(grp))],
        }
    return {
        "x_data": x_data,
        "series": [{"name": y, "data": [_num(v) for v in grp[y].tolist()]}],
    }


def _num(v):
    try:
        f = float(v)
        if f != f:  # NaN
            return None
        return round(f, 2)
    except Exception:
        return str(v)


_SPEC_SYSTEM = (
    "You build ECharts dashboard specs. You output ONLY JSON. Use valid ECharts "
    "option objects with real field names from the provided data columns. Choose "
    "chart types: bar, line, pie, radar, scatter, area. Never invent columns."
)


def _spec_prompt(context: dict) -> str:
    return f"""User requested a dashboard for this scenario:
"{context['scenario']}"

Build a JSON array of chart specs that best serve this scenario. Each element:
{{"type":"bar|line|pie|radar|scatter","title":"...","x":"column","y":"column|sum(count)","aggregation":"sum|count|mean|none","series_columns":["col"...] optional}}

Available columns:
dimensions: {context['dimensions']}
measures: {context['measures']}
dates: {context['dates']}

Sample rows: {json.dumps(context['selected_rows'], default=str)[:2000]}

Also include a short kickoff chart that summarizes the data. Use only available columns.
"""


def _fallback_spec(context: dict) -> list:
    charts = []
    dims, measures, dates = context["dimensions"], context["measures"], context["dates"]
    if dates and measures:
        charts.append({"type": "line", "x": dates[0], "y": measures[0], "aggregation": "sum", "title": f"{measures[0]} over {dates[0]}"})
    if dims and measures:
        charts.append({"type": "bar", "x": dims[0], "y": measures[0], "aggregation": "sum", "title": f"{measures[0]} by {dims[0]}"})
    if measures:
        charts.append({"type": "pie", "x": dims[0] if dims else measures[0], "y": measures[0], "title": f"Share by {dims[0] if dims else 'measure'}"})
    return charts


def _spec_summary(payload, scenario, doc) -> str:
    if isinstance(doc, dict) and doc.get("summary"):
        return doc["summary"]
    return f"Dashboard built for scenario: {scenario}"


def _sanitize_charts(df: pd.DataFrame, charts: list) -> list:
    """Validate chart specs against real columns, drop invalid ones, insert computed series."""
    valid_cols = set(map(str, df.columns))
    out = []
    for c in charts:
        if not isinstance(c, dict) or c.get("type") not in {"bar", "line", "pie", "radar", "scatter", "area"}:
            continue
        x = c.get("x")
        y = c.get("y")
        if x not in valid_cols and c["type"] not in {"pie"}:
            continue
        if c["type"] == "pie" and y not in valid_cols:
            if not (x in valid_cols and y in valid_cols):
                continue
        chart = {
            "type": c["type"],
            "title": c.get("title", y or ""),
            "x": x,
            "y": y,
            "aggregation": c.get("aggregation", "sum" if y else "count"),
            "series_columns": c.get("series_columns", []),
        }
        out.append(chart)
    return out