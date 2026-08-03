import json
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import dashboard as dash_mod
from . import pipeline, qa, storage
from .config import settings

app = FastAPI(title="Excel Intelligence Agent", version="1.0.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_configured": bool(settings.gemini_api_key)}


@app.post("/api/datasets/upload")
async def upload(file: UploadFile = File(...), sheet_name: Optional[str] = None):
    if not file.filename.lower().endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Only .xlsx, .xls or .csv files are supported.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    try:
        return pipeline.process_upload(data, file.filename, sheet_name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse file: {e}")


@app.get("/api/datasets/{dataset_id}")
def dataset_info(dataset_id: str):
    df = storage.load_refined(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    meta = storage.load_meta(dataset_id) or {}
    return {
        "dataset_id": dataset_id,
        "file_name": meta.get("file_name"),
        "column_count": df.shape[1],
        "row_count": df.shape[0],
        "quality": meta.get("quality"),
        "notes": meta.get("notes", []),
    }


@app.get("/api/datasets/{dataset_id}/table")
def get_table(dataset_id: str, limit: int = 200, offset: int = 0):
    df = storage.load_refined(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    import pandas as pd

    total = len(df)
    page = df.iloc[offset : offset + limit]
    columns = [str(c) for c in page.columns]
    rows = page.where(pd.notna(page), None).values.tolist()
    return {"columns": columns, "rows": rows, "total": total, "offset": offset, "limit": limit}


@app.get("/api/datasets/{dataset_id}/download")
def download(dataset_id: str):
    df = storage.load_refined(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    buf = io_bytes(df)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{dataset_id}_refined.xlsx"'},
    )


def io_bytes(df):
    import io

    import pandas as pd

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf


@app.post("/api/datasets/{dataset_id}/insights")
def generate_insights(dataset_id: str, force: bool = False):
    try:
        return pipeline.build_knowledge_doc(dataset_id, force=force)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets/{dataset_id}/insights")
def get_insights(dataset_id: str):
    doc = storage.load_doc(dataset_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Insights not generated yet. POST /insights first.")
    return doc


@app.post("/api/datasets/{dataset_id}/dashboards/suggest")
def suggest(dataset_id: str):
    try:
        return dash_mod.suggest_dashboards(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/datasets/{dataset_id}/dashboards/build")
def build(req: dict, dataset_id: str):
    try:
        spec = dash_mod.build_dashboard(
            dataset_id,
            suggestion_id=req.get("suggestion_id"),
            custom_scenario=req.get("custom_scenario"),
            title=req.get("title"),
        )
        return spec
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/datasets/{dataset_id}/dashboards")
def list_dashboards(dataset_id: str):
    meta = storage.load_meta(dataset_id) or {}
    return {"dashboards": meta.get("dashboards", [])}


@app.post("/api/datasets/{dataset_id}/chat")
def chat(dataset_id: str, body: dict):
    question = (body.get("question") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    try:
        return qa.answer_question(dataset_id, question)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
