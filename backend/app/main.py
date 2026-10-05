"""MQIH field-quality API."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .charts import basic_charts, custom_chart
from .database import ROOT, get_conn, init_db
from .ingest import SchemaError, ingest_bytes
from .schema_map import (
    CATEGORY_COLUMNS,
    DATE_COLUMNS,
    NUMERIC_COLUMNS,
    REQUIRED_COLUMNS,
    SOURCE_COLUMNS,
    column_meta,
)

app = FastAPI(title="MQIH Field Quality", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_PATH = ROOT / "sample_data" / "ftir_sample.csv"


@app.on_event("startup")
def _startup() -> None:
    init_db()


class CustomChartRequest(BaseModel):
    chart_type: Literal["bar", "line", "pie", "scatter"]
    x: str = Field(min_length=1)
    y: str | None = None
    agg: Literal["count", "mean", "sum", "median"] = "count"


def _schema_error(exc: SchemaError) -> HTTPException:
    return HTTPException(status_code=400, detail=exc.as_dict())


@app.get("/health")
def health():
    with get_conn() as conn:
        records = conn.execute("SELECT COUNT(*) AS n FROM records").fetchone()["n"]
    return {"status": "ok", "records": records}


@app.get("/meta")
def meta():
    optional = [c for c in SOURCE_COLUMNS if c not in REQUIRED_COLUMNS]
    return {
        "required": column_meta(REQUIRED_COLUMNS),
        "optional": column_meta(optional),
        "categorical": column_meta(CATEGORY_COLUMNS),
        "numeric": column_meta(NUMERIC_COLUMNS),
        "date": column_meta(sorted(DATE_COLUMNS)),
    }


@app.get("/meta/template")
def template():
    header = ",".join(SOURCE_COLUMNS) + "\n"
    return Response(
        content=header,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ftir_template.csv"'},
    )


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    filename = file.filename or "upload.csv"
    raw = await file.read()
    try:
        return ingest_bytes(raw, filename)
    except SchemaError as exc:
        raise _schema_error(exc) from exc


@app.post("/upload/sample")
def upload_sample():
    if not SAMPLE_PATH.exists():
        raise HTTPException(status_code=404, detail={"message": "Sample file is not on the server."})
    try:
        return ingest_bytes(SAMPLE_PATH.read_bytes(), SAMPLE_PATH.name)
    except SchemaError as exc:
        raise _schema_error(exc) from exc


@app.get("/charts/basic")
def charts_basic():
    return basic_charts()


@app.post("/charts/custom")
def charts_custom(body: CustomChartRequest):
    try:
        return custom_chart(body.chart_type, body.x, body.y, body.agg)
    except SchemaError as exc:
        raise _schema_error(exc) from exc


@app.get("/export")
def export_records():
    with get_conn() as conn:
        frame = pd.read_sql_query("SELECT * FROM records ORDER BY id", conn)
    if "row_hash" in frame.columns:
        frame = frame.drop(columns=["row_hash"])
    payload = frame.to_csv(index=False)
    return Response(
        content=payload,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ftir_records.csv"'},
    )
