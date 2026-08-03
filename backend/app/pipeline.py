"""End-to-end pipeline: upload -> parse -> clean -> insights -> knowledge doc."""
from __future__ import annotations

import json
import time
from typing import Optional

import pandas as pd

from . import excel_parser as xp
from . import storage
from .llm import llm_available, llm_json, llm_text


def process_upload(file_bytes: bytes, filename: str, sheet_name: Optional[str] = None) -> dict:
    dataset_id = storage.new_id()
    upload_path = storage.save_upload(dataset_id, file_bytes)

    sheets = xp.list_sheets(file_bytes, filename)
    if sheet_name is None:
        sheet_name = sheets[0]["name"] if sheets else "Sheet1"

    df, clean_notes = xp.clean_dataframe(xp.read_and_locate_header(str(upload_path), sheet_name))
    used_llm = False

    # Heuristic pass produced nothing usable -> ask the LLM to make sense of it.
    if (df is None or df.shape[0] == 0 or df.shape[1] == 0) and llm_available():
        llm_df = xp.llm_infer_structure(str(upload_path), sheet_name)
        if llm_df is not None and not llm_df.empty:
            df, clean_notes = xp.clean_dataframe(llm_df)
            used_llm = True

    if df is None or df.empty:
        raise ValueError("Could not extract any tabular data from the sheet. Try a sheet with clearer structure.")

    storage.save_refined(dataset_id, df)

    quality, quality_notes = xp.infer_quality(df)
    columns = xp.summarize_columns(df)

    meta = {
        "dataset_id": dataset_id,
        "file_name": filename,
        "sheet_name": sheet_name,
        "created_at": time.time(),
        "quality": quality,
        "notes": clean_notes + quality_notes,
        "used_llm": used_llm,
    }
    storage.save_meta(dataset_id, meta)

    return {
        "dataset_id": dataset_id,
        "file_name": filename,
        "sheet_name": sheet_name,
        "column_count": df.shape[1],
        "row_count": df.shape[0],
        "columns": columns,
        "preview": xp.preview_frame(df),
        "quality": quality,
        "notes": meta["notes"],
    }


def build_knowledge_doc(dataset_id: str, force: bool = False) -> dict:
    existing = storage.load_doc(dataset_id)
    if existing and not force:
        return existing

    df = storage.load_refined(dataset_id)
    meta = storage.load_meta(dataset_id) or {}
    if df is None:
        raise ValueError("Dataset not found.")

    stats = _build_stats(df)
    context = {
        "columns": xp.summarize_columns(df),
        "stats": stats,
        "sample": xp.preview_frame(df, limit=5),
        "quality": meta.get("quality"),
    }

    doc = {
        "dataset_id": dataset_id,
        "file_name": meta.get("file_name"),
        "generated_at": time.time(),
        "summary": "",
        "relationships": [],
        "insights": [],
        "anomalies": [],
        "business_context": "",
        "recommendations": [],
    }

    if llm_available():
        llm_doc = llm_json(_knowledge_prompt(context), _KNOWLEDGE_SYSTEM)
        if isinstance(llm_doc, dict):
            doc.update(llm_doc)
    else:
        # Deterministic fallback so the app is still useful without a key.
        doc["summary"] = f"Dataset has {df.shape[1]} columns and {df.shape[0]} rows."
        doc["insights"] = [
            {"title": k, "detail": str(v)} for k, v in list(stats.items())[:6]
        ]
        doc["relationships"] = _heuristic_relationships(context["columns"])

    storage.save_doc(dataset_id, doc)
    return doc


_KNOWLEDGE_SYSTEM = (
    "You are a senior data analyst and business consultant. You produce crisp, "
    "insightful, jargon-light analysis from tabular data summaries. You never invent "
    "numbers that are not in the provided stats."
)


def _knowledge_prompt(context: dict) -> str:
    return f"""Analyze the following dataset summary and produce a JSON document with EXACTLY these keys:

{{
  "summary": "2-4 sentence plain-English summary of what this data represents and its key takeaway.",
  "relationships": [{{"between": "colA → colB", "type": "1:many|many:many|one:one|derived|grouping|time-series", "meaning": "why/how the columns are related"}}],
  "insights": [{{"title": "short headline", "detail": "2-3 sentence explanation", "severity": "high|medium|low"}}],
  "anomalies": [{{"what": "what looks unusual", "detail": "explanation", "impact": "why it matters"}}],
  "business_context": "What business domain/questions this data could answer.",
  "recommendations": ["actionable suggestion 1", "actionable suggestion 2", ...]
}}

Only use the stats below. Do not fabricate numbers.

DATASET CONTEXT:
{json.dumps(context, default=str, indent=2)}
"""


def _build_stats(df: pd.DataFrame) -> dict:
    stats = {}
    for c in df.columns:
        s = df[c]
        entry: dict = {"type": str(s.dtype)}
        if pd.api.types.is_numeric_dtype(s):
            entry["min"] = float(s.min()) if not pd.isna(s.min()) else None
            entry["max"] = float(s.max()) if not pd.isna(s.max()) else None
            entry["mean"] = round(float(s.mean()), 2) if not pd.isna(s.mean()) else None
            entry["sum"] = round(float(s.sum()), 2) if not pd.isna(s.sum()) else None
            entry["nunique"] = int(s.nunique())
        elif pd.api.types.is_datetime64_any_dtype(s):
            entry["min"] = str(s.min()) if not pd.isna(s.min()) else None
            entry["max"] = str(s.max()) if not pd.isna(s.max()) else None
        else:
            top = s.dropna().value_counts().head(5)
            entry["top_values"] = [
                {"value": str(k), "count": int(v)} for k, v in top.items()
            ]
            entry["nunique"] = int(s.nunique())
        stats[c] = entry
    return stats


def _heuristic_relationships(columns: list) -> list:
    rels = []
    for c in columns:
        if c["role"] == "date":
            rels.append(
                {"between": c["name"] + " (date)", "type": "time-series", "meaning": "Time dimension for trend analysis."}
            )
    return rels