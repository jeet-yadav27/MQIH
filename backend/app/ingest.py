"""Validate an uploaded table and insert it into ``records``."""

from __future__ import annotations

import hashlib
import math
import re
from io import BytesIO

import pandas as pd

from .database import get_conn, refresh_materialized
from .schema_map import (
    ALIASES,
    DATE_COLUMNS,
    HASH_FIELDS,
    INSERT_COLUMNS,
    KNOWN_UPLOAD_COLUMNS,
    REQUIRED_COLUMNS,
    SOURCE_COLUMNS,
)

_YES = {"yes", "y", "true", "1", "resolved", "solved", "closed", "complete", "completed"}
_PLACEHOLDERS = {"", "nan", "none", "null", "nat", "-"}


class SchemaError(Exception):
    def __init__(self, message: str, missing: list[str] | None = None, unknown: list[str] | None = None):
        super().__init__(message)
        self.message = message
        self.missing = missing or []
        self.unknown = unknown or []

    def as_dict(self) -> dict:
        return {
            "message": self.message,
            "missing_columns": self.missing,
            "unknown_columns": self.unknown,
        }


def _blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    try:
        if pd.isna(value):
            return True
    except TypeError:
        pass
    return str(value).strip().lower() in _PLACEHOLDERS


def _text(value) -> str | None:
    if _blank(value):
        return None
    return str(value).strip()


def _parse_int(value) -> int | None:
    if _blank(value):
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    if not match:
        return None
    try:
        return int(float(match.group()))
    except ValueError:
        return None


def _parse_date(value) -> str | None:
    if _blank(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce", dayfirst=False)
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    canons: list[str | None] = []
    seen: dict[str, str] = {}
    for original in df.columns:
        raw = str(original).replace("\ufeff", "").strip()
        key = re.sub(r"[\s/\-]+", "_", raw.lower())
        key = re.sub(r"[^a-z0-9_]", "", key)
        key = re.sub(r"_+", "_", key).strip("_")
        if not key or key.startswith("unnamed"):
            canons.append(None)
            continue
        canon = ALIASES.get(key, key)
        if canon in seen:
            raise SchemaError(
                f"Columns '{seen[canon]}' and '{raw}' both map to '{canon}'. Keep only one."
            )
        seen[canon] = raw
        canons.append(canon)
    renamed = df.copy()
    renamed.columns = [c if c is not None else f"__drop_{i}" for i, c in enumerate(canons)]
    drop_cols = [c for c in renamed.columns if str(c).startswith("__drop_")]
    if drop_cols:
        renamed = renamed.drop(columns=drop_cols)
    return renamed


def _read_frame(raw: bytes, filename: str) -> tuple[pd.DataFrame, str | None]:
    lower = filename.lower()
    if lower.endswith(".csv"):
        last_error: Exception | None = None
        for encoding in ("utf-8-sig", "utf-8", "cp1252"):
            try:
                frame = pd.read_csv(BytesIO(raw), dtype=str, encoding=encoding)
                return frame, None
            except UnicodeDecodeError as exc:
                last_error = exc
        raise SchemaError(
            "Could not decode this CSV. Save it as UTF-8 and try again."
        ) from last_error
    if lower.endswith(".xlsx"):
        try:
            book = pd.ExcelFile(BytesIO(raw))
        except Exception as exc:
            raise SchemaError("Could not read this Excel file. Use a valid .xlsx workbook.") from exc
        if not book.sheet_names:
            raise SchemaError("The workbook has no sheets.")
        sheet = book.sheet_names[0]
        return book.parse(sheet), sheet
    raise SchemaError("Upload a .csv or .xlsx file.")


def _validate_columns(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    frame = _normalize_columns(frame)
    present = list(frame.columns)
    unknown = sorted({c for c in present if c not in KNOWN_UPLOAD_COLUMNS})
    missing = [c for c in REQUIRED_COLUMNS if c not in present]
    if unknown or missing:
        parts = ["This file does not match the FTIR records schema."]
        if missing:
            parts.append("Required columns are missing.")
        if unknown:
            parts.append("Columns are not in the schema.")
        raise SchemaError(" ".join(parts), missing=missing, unknown=unknown)
    omitted = [c for c in SOURCE_COLUMNS if c not in present and c != "file_name"]
    return frame, omitted


def _resolved(problem_solved: str | None, repair_status: str | None, fallback: int | None) -> int:
    blob = " ".join(filter(None, [problem_solved, repair_status])).lower()
    if any(token in blob.split() or token in blob for token in ("yes", "resolved", "solved", "completed", "closed")):
        if problem_solved and problem_solved.lower() in _YES:
            return 1
        if repair_status and any(word in repair_status.lower() for word in ("resolv", "complet", "closed")):
            return 1
    if problem_solved and problem_solved.lower() in {"no", "n", "open", "pending"}:
        return 0
    if fallback is not None:
        return 1 if fallback else 0
    return 0


def _hash_row(values: dict) -> str:
    payload = "|".join("" if values.get(col) is None else str(values.get(col)) for col in HASH_FIELDS)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def _build_record(row: pd.Series, filename: str) -> tuple[dict | None, str | None]:
    ftir_no = _text(row.get("ftir_no"))
    if ftir_no is None:
        return None, "Missing FTIR number"
    values: dict = {col: _text(row.get(col)) for col in SOURCE_COLUMNS}
    values["ftir_no"] = ftir_no
    values["file_name"] = filename
    for col in DATE_COLUMNS:
        if col in row.index or True:
            values[col] = _parse_date(row.get(col)) if col in row.index else values.get(col)
            if col in row.index:
                values[col] = _parse_date(row.get(col))

    days = _parse_int(row.get("days_used")) if "days_used" in row.index else None
    if days is None:
        registered = values.get("date_registered")
        incident = values.get("date_of_incident")
        if registered and incident:
            delta = pd.to_datetime(incident) - pd.to_datetime(registered)
            if pd.notna(delta):
                days = max(int(delta.days), 0)
    values["days_used"] = days

    km = _parse_int(row.get("using_time_km")) if "using_time_km" in row.index else None
    if km is None and "using_km_int" in row.index:
        km = _parse_int(row.get("using_km_int"))
    report_date = values.get("ftir_report_date")
    year = month = None
    if report_date:
        stamp = pd.to_datetime(report_date)
        year = int(stamp.year)
        month = int(stamp.month)
    else:
        year = _parse_int(row.get("report_year")) if "report_year" in row.index else None
        month = _parse_int(row.get("report_month")) if "report_month" in row.index else None

    summary = _text(row.get("summary")) if "summary" in row.index else None
    root = _text(row.get("root_cause")) if "root_cause" in row.index else None
    fallback_resolved = _parse_int(row.get("is_resolved")) if "is_resolved" in row.index else None
    record = {
        **{col: values.get(col) for col in SOURCE_COLUMNS},
        "file_name": filename,
        "row_hash": _hash_row(values),
        "using_km_int": km,
        "report_year": year,
        "report_month": month,
        "is_resolved": _resolved(values.get("problem_solved"), values.get("repair_status"), fallback_resolved),
        "has_sbpr": 1 if values.get("sbpr_no") else 0,
        "summary": summary,
        "root_cause": root,
    }
    # days_used lives in SOURCE_COLUMNS and was set on values.
    record["days_used"] = days
    return record, None


def ingest_bytes(raw: bytes, filename: str) -> dict:
    if not raw:
        raise SchemaError("The file is empty.")
    if len(raw) > 25 * 1024 * 1024:
        raise SchemaError("File is larger than 25 MB.")
    try:
        frame, sheet = _read_frame(raw, filename)
    except SchemaError:
        raise
    except Exception as exc:
        raise SchemaError("Could not read this file. Check that it is a valid CSV or Excel workbook.") from exc

    if frame.shape[1] == 0:
        raise SchemaError("No columns were found. Include a header row that matches the FTIR schema.")
    frame, omitted = _validate_columns(frame)
    if frame.empty:
        raise SchemaError("The file has headers but no data rows.")

    records: list[dict] = []
    rejected: list[dict] = []
    for index, row in frame.iterrows():
        record, reason = _build_record(row, filename)
        if record is None:
            if len(rejected) < 8:
                rejected.append({"row": int(index) + 2, "reason": reason or "Rejected"})
            else:
                rejected.append({"row": int(index) + 2, "reason": reason or "Rejected"})
            continue
        records.append(record)

    rejected_count = len(rejected)
    if not records:
        raise SchemaError(
            "Every row was rejected because FTIR number is missing.",
            missing=["ftir_no"],
        )

    placeholders = ", ".join(["?"] * len(INSERT_COLUMNS))
    columns_sql = ", ".join(INSERT_COLUMNS)
    sql = f"INSERT OR IGNORE INTO records ({columns_sql}) VALUES ({placeholders})"
    tuples = [tuple(rec.get(col) for col in INSERT_COLUMNS) for rec in records]

    with get_conn() as conn:
        before = conn.total_changes
        conn.executemany(sql, tuples)
        inserted = conn.total_changes - before
        refresh_materialized(conn)
        total = conn.execute("SELECT COUNT(*) AS n FROM records").fetchone()["n"]

    duplicates = len(records) - inserted
    message = f"Uploaded {inserted} record{'s' if inserted != 1 else ''} into the FTIR database."
    if duplicates:
        message += f" Skipped {duplicates} duplicate{'s' if duplicates != 1 else ''}."
    if rejected_count:
        message += f" Rejected {rejected_count} row{'s' if rejected_count != 1 else ''} without an FTIR number."
    return {
        "ok": True,
        "filename": filename,
        "sheet": sheet,
        "rows_read": int(len(frame)),
        "inserted": int(inserted),
        "duplicates_skipped": int(duplicates),
        "rows_rejected": int(rejected_count),
        "rejected_preview": rejected[:8],
        "optional_columns_omitted": omitted,
        "total_records": int(total),
        "message": message,
    }
