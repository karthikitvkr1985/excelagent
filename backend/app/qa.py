"""Q&A: answer natural-language questions about the dataset.

Strategy: build a compact schema summary, ask the LLM for a read-only SQL query
against the dataset's DuckDB file, execute it safely, then have the LLM craft a
plain-English answer from the results (or answer directly from context for
non-SQL questions).
"""
from __future__ import annotations

import json

import pandas as pd

from . import storage
from .llm import llm_available, llm_json, llm_text


def answer_question(dataset_id: str, question: str) -> dict:
    df = storage.load_refined(dataset_id)
    doc = storage.load_doc(dataset_id) or {}
    if df is None:
        raise ValueError("Dataset not found.")

    schema = _schema_summary(df)
    sql = None
    table = None
    answer = ""

    if llm_available():
        sql = _ask_sql(question, schema)
        if sql:
            try:
                result_df = storage.run_sql(dataset_id, sql)
                if result_df is not None and not result_df.empty:
                    table = result_df.head(50).to_dict("records")
                    answer = _explain_result(question, sql, result_df, schema)
                else:
                    answer = "That question returned no matching data."
            except Exception as e:
                answer = f"Could not run the query for that question: {e}"
        else:
            answer = _answer_from_context(question, schema, doc)

    if not llm_available():
        answer = _heuristic_answer(question, schema, df)

    return {"answer": answer, "sql": sql, "table": table}


def _schema_summary(df: pd.DataFrame) -> dict:
    cols = []
    for c in df.columns:
        s = df[c]
        entry = {"name": str(c), "type": str(s.dtype)}
        if pd.api.types.is_numeric_dtype(s):
            entry.update(min=float(s.min()), max=float(s.max()), mean=float(s.mean()))
        elif pd.api.types.is_datetime64_any_dtype(s):
            entry.update(min=str(s.min()), max=str(s.max()))
        else:
            top = s.dropna().value_counts().head(5)
            entry["sample_values"] = [str(v) for v in top.index]
        cols.append(entry)
    return {"columns": cols, "rows": len(df), "sample_rows": df.head(3).to_dict("records")}


def _ask_sql(question: str, schema: dict) -> str:
    prompt = f"""Translate this user question into a single read-only SQL query
against a DuckDB table named `data`.

RULES:
- Use ONLY columns in the schema. Never invent columns.
- Output ONLY the SQL text, no markdown, no explanations.
- Use standard SQL (aggregations: COUNT, SUM, AVG, GROUP BY, ORDER BY, WHERE).

SCHEMA:
{json.dumps(schema, default=str, indent=2)}

QUESTION: {question}
"""
    try:
        text = llm_text(prompt)
        text = text.strip()
        # strip code fences
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return text
    except Exception:
        return None


def _explain_result(question: str, sql: str, df: pd.DataFrame, schema: dict) -> str:
    prompt = f"""The user asked: "{question}"
The SQL executed was: {sql}
It returned this table (first {min(len(df), 20)} rows):
{df.head(20).to_string()}

Write a clear, concise 2-5 sentence answer in plain English for a business user,
highlighting the key numbers. Do not fabricate numbers not in the table.
"""
    try:
        return llm_text(prompt)
    except Exception:
        return f"Query returned {len(df)} row(s)."


def _answer_from_context(question: str, schema: dict, doc: dict) -> str:
    prompt = f"""Answer this question about a dataset. Use the schema and the 
pre-computed insights below. If the question needs calculations, note what data 
would be needed. Keep it to 3-6 sentences.

SCHEMA:
{json.dumps(schema, default=str, indent=2)}

INSIGHTS DOC:
{json.dumps(doc, default=str)[:3000]}

QUESTION: {question}
"""
    try:
        return llm_text(prompt)
    except Exception:
        return "I could not answer that question right now."


def _heuristic_answer(question: str, schema: dict, df: pd.DataFrame) -> str:
    """Offline fallback when no LLM key is set."""
    q = question.lower()
    cols = [c["name"] for c in schema["columns"]]
    measures = [c["name"] for c in schema["columns"] if c["type"].startswith(("int", "float"))]
    if "column" in q or "columns" in q:
        return "Columns: " + ", ".join(cols)
    if "row" in q and ("how many" in q or "count" in q):
        return f"The dataset has {len(df)} rows."
    if measures and ("sum" in q or "total" in q):
        return f"Totals: " + "; ".join(f"{m} = {df[m].sum():,.2f}" for m in measures[:4])
    if "missing" in q or "null" in q:
        miss = df.isna().sum().sum()
        return f"Total missing cells: {int(miss)}."
    return "Add a GEMINI_API_KEY to enable natural-language Q&A. Meanwhile, ask about columns, row counts, totals, or missing values."