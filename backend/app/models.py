from pydantic import BaseModel, Field
from typing import Any, List, Optional


class ColumnInfo(BaseModel):
    name: str
    dtype: str = "object"
    nullable: bool = True
    description: str = ""
    role: str = "dimension"  # dimension | measure | id | date


class TablePreview(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    column_count: int
    row_count: int


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    file_name: str
    sheet_name: str
    column_count: int
    row_count: int
    columns: List[ColumnInfo]
    preview: TableInfo
    quality: dict
    notes: List[str]


class DashboardSuggestion(BaseModel):
    id: str
    title: str
    context: str
    purpose: str
    charts: List[str]
    difficulty: str = "medium"


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    answer: str
    sql: Optional[str] = None
    table: Optional[List[dict]] = None


class DashboardBuildRequest(BaseModel):
    suggestion_id: Optional[str] = None
    custom_scenario: Optional[str] = None
    title: Optional[str] = None


class ChatRequest(BaseModel):
    question: str


class DashboardSpecResponse(BaseModel):
    dashboard_id: str
    title: str
    summary: str
    layout: List[dict]