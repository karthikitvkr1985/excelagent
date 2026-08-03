"""Dataset storage: one DuckDB file + JSON metadata per dataset.

Layout (inside DATA_DIR):
  uploads/<id>.xlsx        original uploaded file
  refined/<id>.parquet     cleaned DataFrame
  db/<id>.duckdb           DuckDB file for SQL querying
  docs/<id>.json           knowledge/insights document
  docs/<id>_meta.json      dataset metadata + dashboard specs
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, List, Optional

import duckdb
import pandas as pd

from .config import ensure_data_dir


def _paths(dataset_id: str) -> dict:
    root = ensure_data_dir()
    return {
        "upload": root / "uploads" / f"{dataset_id}.xlsx",
        "parquet": root / "refined" / f"{dataset_id}.parquet",
        "db": root / "db" / f"{dataset_id}.duckdb",
        "doc": root / "docs" / f"{dataset_id}.json",
        "meta": root / "docs" / f"{dataset_id}_meta.json",
    }


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def save_upload(dataset_id: str, file_bytes: bytes) -> Path:
    p = _paths(dataset_id)["upload"]
    p.write_bytes(file_bytes)
    return p


def save_refined(dataset_id: str, df: pd.DataFrame) -> Path:
    p = _paths(dataset_id)["parquet"]
    df.to_parquet(p, index=False)
    _rebuild_db(dataset_id, df)
    return p


def _rebuild_db(dataset_id: str, df: pd.DataFrame):
    db_path = str(_paths(dataset_id)["db"])
    con = duckdb.connect(db_path)
    con.register("src", df)
    con.execute("CREATE OR REPLACE TABLE data AS SELECT * FROM src")
    con.close()


def load_refined(dataset_id: str) -> Optional[pd.DataFrame]:
    p = _paths(dataset_id)["parquet"]
    if not p.exists():
        return None
    return pd.read_parquet(p)


def save_doc(dataset_id: str, doc: dict):
    _paths(dataset_id)["doc"].write_text(json.dumps(doc, default=str, indent=2))


def load_doc(dataset_id: str) -> Optional[dict]:
    p = _paths(dataset_id)["doc"]
    if not p.exists():
        return None
    return json.loads(p.read_text())


def save_meta(dataset_id: str, meta: dict):
    _paths(dataset_id)["meta"].write_text(json.dumps(meta, default=str, indent=2))


def load_meta(dataset_id: str) -> Optional[dict]:
    p = _paths(dataset_id)["meta"]
    if not p.exists():
        return None
    return json.loads(p.read_text())


def run_sql(dataset_id: str, sql: str) -> Optional[pd.DataFrame]:
    """Execute a read-only query against the dataset's DuckDB file."""
    db_path = str(_paths(dataset_id)["db"])
    if not Path(db_path).exists():
        return None
    con = duckdb.connect(db_path, read_only=True)
    try:
        sql = sql.strip().rstrip(";")
        if not sql.lower().startswith(("select", "with", "show", "describe", "pragma")):
            raise ValueError("Only SELECT / WITH queries are allowed.")
        return con.execute(sql).df()
    finally:
        con.close()


def list_dataset_ids() -> List[str]:
    root = ensure_data_dir()
    return [p.stem for p in (root / "refined").glob("*.parquet")]