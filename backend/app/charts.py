"""Basic and custom chart payloads computed from ``records``."""

from __future__ import annotations

import math
import re

import pandas as pd

from .database import get_conn
from .ingest import SchemaError
from .schema_map import (
    ALLOWED_CHART_COLUMNS,
    CATEGORY_COLUMNS,
    DATE_COLUMNS,
    NUMERIC_COLUMNS,
    label_for,
)

_AGG = {"count", "mean", "sum", "median"}
_KINDS = {"bar", "line", "pie", "scatter"}


def _round(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return round(float(value), 2)


def _sort_key(label: str):
    text = str(label).replace("–", "-").replace(",", "")
    match = re.match(r"-?\d+(?:\.\d+)?", text)
    if match:
        return (0, float(match.group()))
    return (1, text)


def _short(text: str, limit: int = 22) -> str:
    text = "" if text is None else str(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _clean_text(series: pd.Series) -> pd.Series:
    text = series.dropna().astype(str).str.strip()
    return text[~text.str.lower().isin({"", "none", "nan", "null"})]


def _points_from_counts(counts: pd.Series, limit: int, other: bool) -> list[dict]:
    counts = counts.sort_values(ascending=False)
    if other and len(counts) > limit:
        head = counts.iloc[:limit]
        rest = int(counts.iloc[limit:].sum())
        rows = [_point(idx, val) for idx, val in head.items()]
        if rest:
            rows.append({"label": "Other", "short": "Other", "value": rest})
        return rows
    head = counts.iloc[:limit]
    return [_point(idx, val) for idx, val in head.items()]


def _point(label, value) -> dict:
    return {"label": str(label), "short": _short(label), "value": _round(value) if isinstance(value, float) else int(value) if float(value).is_integer() else _round(value)}


def _histogram(series: pd.Series, bins: int = 8) -> list[dict]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return []
    if values.nunique() == 1:
        only = float(values.iloc[0])
        label = str(int(only)) if only.is_integer() else str(round(only, 1))
        return [{"label": label, "short": label, "value": int(len(values))}]
    bucket_count = int(min(bins, max(int(values.nunique()), 1)))
    cats = pd.cut(values, bins=bucket_count, include_lowest=True)
    grouped = cats.value_counts(sort=False)
    rows = []
    for interval, count in grouped.items():
        if int(count) == 0:
            continue
        left = int(round(interval.left))
        right = int(round(interval.right))
        label = f"{left:,}–{right:,}"
        rows.append({"label": label, "short": label, "value": int(count)})
    return rows


def _measure(series: pd.Series, column: str) -> dict:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "column": column,
        "label": label_for(column),
        "count": int(values.shape[0]),
        "mean": _round(values.mean()) if not values.empty else None,
        "median": _round(values.median()) if not values.empty else None,
        "min": _round(values.min()) if not values.empty else None,
        "max": _round(values.max()) if not values.empty else None,
    }


def _category_chart(frame: pd.DataFrame, column: str, title: str, limit: int = 12) -> dict | None:
    if column not in frame.columns:
        return None
    counts = _clean_text(frame[column]).value_counts()
    if counts.empty:
        return None
    return {
        "id": column,
        "title": title,
        "subtitle": "Number of reports",
        "kind": "bar",
        "x_label": label_for(column),
        "y_label": "Reports",
        "data": _points_from_counts(counts, limit, other=True),
    }


def basic_charts() -> dict:
    with get_conn() as conn:
        frame = pd.read_sql_query("SELECT * FROM records", conn)
    count = int(len(frame))
    if count == 0:
        return {
            "summary": {
                "record_count": 0,
                "resolved_rate": None,
                "sbpr_rate": None,
                "measures": [
                    _measure(pd.Series(dtype=float), "days_used"),
                    _measure(pd.Series(dtype=float), "using_km_int"),
                ],
            },
            "charts": [],
            "message": "No records yet. Upload a CSV or Excel extract to build the overview.",
        }

    charts: list[dict] = []
    dates = pd.to_datetime(frame["ftir_report_date"], errors="coerce")
    monthly = dates.dt.to_period("M").dropna().astype(str).value_counts().sort_index()
    if not monthly.empty:
        charts.append(
            {
                "id": "reports_over_time",
                "title": "Reports over time",
                "subtitle": "Count by FTIR report month",
                "kind": "line",
                "x_label": "Month",
                "y_label": "Reports",
                "data": [_point(idx, val) for idx, val in monthly.items()],
            }
        )

    for column, title in (
        ("outbreak_country", "Outbreak country"),
        ("product_model_code", "Product model"),
        ("rank", "Severity rank"),
        ("status", "Status"),
        ("quality", "Quality"),
        ("segmentation", "Segmentation"),
        ("repair_status", "Repair status"),
        ("trouble_code_complaint", "Trouble codes"),
    ):
        chart = _category_chart(frame, column, title, limit=10 if column == "trouble_code_complaint" else 12)
        if chart:
            charts.append(chart)

    days_hist = _histogram(frame["days_used"]) if "days_used" in frame else []
    if days_hist:
        charts.append(
            {
                "id": "days_used_hist",
                "title": "Days used",
                "subtitle": "How long vehicles were in service before the incident",
                "kind": "bar",
                "x_label": "Days used",
                "y_label": "Reports",
                "data": days_hist,
            }
        )
    km_hist = _histogram(frame["using_km_int"]) if "using_km_int" in frame else []
    if km_hist:
        charts.append(
            {
                "id": "km_hist",
                "title": "Usage (km)",
                "subtitle": "Odometer reading at the time of the incident",
                "kind": "bar",
                "x_label": "Kilometres",
                "y_label": "Reports",
                "data": km_hist,
            }
        )

    resolved = pd.to_numeric(frame["is_resolved"], errors="coerce")
    sbpr = pd.to_numeric(frame["has_sbpr"], errors="coerce")
    return {
        "summary": {
            "record_count": count,
            "resolved_rate": _round(resolved.mean()) if resolved.notna().any() else None,
            "sbpr_rate": _round(sbpr.mean()) if sbpr.notna().any() else None,
            "measures": [
                _measure(frame["days_used"], "days_used"),
                _measure(frame["using_km_int"], "using_km_int"),
            ],
        },
        "charts": charts,
        "message": None,
    }


def _ensure_column(name: str) -> str:
    if not name or not re.fullmatch(r"[a-z_][a-z0-9_]*", name) or name not in ALLOWED_CHART_COLUMNS:
        raise SchemaError(f"Column '{name}' is not available for charting.")
    return name


def _axis_labels(series: pd.Series, column: str, kind: str) -> pd.Series:
    if column in DATE_COLUMNS:
        parsed = pd.to_datetime(series, errors="coerce")
        if parsed.notna().mean() > 0.5:
            if kind == "line" or parsed.dt.normalize().nunique(dropna=True) > 18:
                return parsed.dt.to_period("M").astype(str)
            return parsed.dt.strftime("%Y-%m-%d")
    if column in NUMERIC_COLUMNS and kind != "scatter":
        numeric = pd.to_numeric(series, errors="coerce")
        valid = numeric.dropna()
        if valid.empty:
            return pd.Series([pd.NA] * len(series), index=series.index)
        if valid.nunique() <= 8 and kind != "line":
            return valid.round(0).astype("Int64").astype(str)
        bucket_count = int(min(8, max(int(valid.nunique()), 1)))
        cats = pd.cut(numeric, bins=bucket_count, include_lowest=True)
        return cats.map(lambda iv: None if pd.isna(iv) else f"{int(round(iv.left)):,}–{int(round(iv.right)):,}")
    return series


def custom_chart(chart_type: str, x: str, y: str | None, agg: str) -> dict:
    if chart_type not in _KINDS:
        raise SchemaError("Chart type must be bar, line, pie, or scatter.")
    if agg not in _AGG:
        raise SchemaError("Aggregation must be count, mean, sum, or median.")
    x = _ensure_column(x)
    if chart_type == "scatter":
        if not y:
            raise SchemaError("A scatter plot needs both an X column and a Y column.")
        y = _ensure_column(y)
        if x not in NUMERIC_COLUMNS or y not in NUMERIC_COLUMNS:
            raise SchemaError("Scatter plots use numeric columns such as days used and usage (km).")
        agg = "none"
    elif chart_type == "pie":
        agg = "count"
        y = None
    elif agg == "count":
        y = None
    else:
        if not y:
            raise SchemaError(f"Choose a numeric column to {agg}.")
        y = _ensure_column(y)
        if y not in NUMERIC_COLUMNS:
            raise SchemaError(f"'{label_for(y)}' is not numeric. Pick a measure such as days used or usage (km).")

    columns = [x] if y is None else [x, y]
    with get_conn() as conn:
        sql = "SELECT " + ", ".join(f'"{col}"' for col in columns) + " FROM records"
        frame = pd.read_sql_query(sql, conn)

    title = _title(chart_type, x, y, agg)
    y_label = "Reports" if agg in {"count", "none"} and chart_type != "scatter" else f"{agg.title()} of {label_for(y)}" if y else "Reports"
    if chart_type == "scatter":
        y_label = label_for(y)

    if frame.empty:
        return _empty(chart_type, title, label_for(x), y_label, "No records yet. Upload data before building a chart.")

    if chart_type == "scatter":
        plot = frame[[x, y]].copy()
        plot[x] = pd.to_numeric(plot[x], errors="coerce")
        plot[y] = pd.to_numeric(plot[y], errors="coerce")
        plot = plot.dropna().head(3000)
        data = [{"x": _round(a), "y": _round(b)} for a, b in plot.itertuples(index=False, name=None)]
        return {
            "id": "custom",
            "title": title,
            "subtitle": f"{len(data)} vehicles",
            "kind": "scatter",
            "x_label": label_for(x),
            "y_label": y_label,
            "data": data,
            "message": None if data else "Those columns have no numeric values to plot.",
            "point_count": len(data),
        }

    work = frame.copy()
    work["_x"] = _axis_labels(work[x], x, chart_type)
    if y is None:
        if x in NUMERIC_COLUMNS:
            labels = work["_x"].dropna().astype(str)
        else:
            labels = _clean_text(work["_x"])
        labels = labels[labels.astype(str).str.strip() != ""]
        if labels.empty:
            return _empty(chart_type, title, label_for(x), y_label, f"{label_for(x)} has no values.")
        counts = labels.value_counts()
        if x in DATE_COLUMNS or x in NUMERIC_COLUMNS:
            ordered = sorted(counts.index, key=_sort_key)
            data = [_point(lab, counts[lab]) for lab in ordered]
        elif chart_type == "line":
            data = [_point(lab, counts[lab]) for lab in sorted(counts.index, key=_sort_key)]
        else:
            limit = 8 if chart_type == "pie" else 15
            data = _points_from_counts(counts, limit, other=True)
        return _payload(chart_type, title, label_for(x), y_label, data, f"{int(counts.sum())} reports")

    work["_y"] = pd.to_numeric(work[y], errors="coerce")
    work = work.dropna(subset=["_y"])
    work["_x"] = work["_x"].astype(str)
    work = work[work["_x"].str.strip().ne("") & work["_x"].ne("None") & work["_x"].ne("nan")]
    if work.empty:
        return _empty(chart_type, title, label_for(x), y_label, "No rows have both a category and a numeric value.")
    grouped = work.groupby("_x", dropna=True)["_y"].agg(agg)
    if x in DATE_COLUMNS or x in NUMERIC_COLUMNS or chart_type == "line":
        grouped = grouped.reindex(sorted(grouped.index, key=_sort_key))
    elif chart_type == "pie":
        grouped = grouped.sort_values(ascending=False).head(8)
    else:
        grouped = grouped.sort_values(ascending=False).head(15)
    data = [_point(idx, val) for idx, val in grouped.items()]
    return _payload(chart_type, title, label_for(x), y_label, data, f"{agg.title()} of {label_for(y)}")


def _title(kind: str, x: str, y: str | None, agg: str) -> str:
    if kind == "scatter":
        return f"{label_for(y)} vs {label_for(x)}"
    if agg == "count" or y is None:
        return f"{label_for(x)}"
    return f"{agg.title()} of {label_for(y)} by {label_for(x)}"


def _payload(kind, title, x_label, y_label, data, subtitle) -> dict:
    return {
        "id": "custom",
        "title": title,
        "subtitle": subtitle,
        "kind": kind,
        "x_label": x_label,
        "y_label": y_label,
        "data": data,
        "message": None if data else "Nothing to plot for that selection.",
        "point_count": len(data),
    }


def _empty(kind, title, x_label, y_label, message) -> dict:
    return _payload(kind, title, x_label, y_label, [], message) | {"message": message, "subtitle": message}
