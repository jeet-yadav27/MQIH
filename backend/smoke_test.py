"""End-to-end checks against a temporary SQLite file."""

from __future__ import annotations

import os
import tempfile
from io import BytesIO
from pathlib import Path

import openpyxl

TMP = Path(tempfile.mkdtemp(prefix="mqih-smoke-"))
os.environ["MQIH_DB"] = str(TMP / "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.schema_map import REQUIRED_COLUMNS  # noqa: E402


def must(response, code=200):
    if response.status_code != code:
        raise SystemExit(f"{response.request.method} {response.request.url} -> {response.status_code}\n{response.text}")
    return response.json() if response.content and "json" in response.headers.get("content-type", "") else response


def main() -> None:
    sample = Path(__file__).resolve().parents[1] / "sample_data" / "ftir_sample.csv"
    if not sample.exists():
        raise SystemExit("Sample CSV missing. Run make_sample.py first.")

    with TestClient(app) as client:
        health = must(client.get("/health"))
        assert health["records"] == 0

        missing = must(client.post("/upload", files={"file": ("bad.csv", b"foo,bar\n1,2\n", "text/csv")}), 400)
        assert "ftir_no" in missing["detail"]["missing_columns"]
        assert "foo" in missing["detail"]["unknown_columns"]

        header = ",".join(REQUIRED_COLUMNS + ["weird_col"])
        unknown = must(
            client.post(
                "/upload",
                files={"file": ("odd.csv", f"{header}\n1,2,3,4,5,6,7\n".encode(), "text/csv")},
            ),
            400,
        )
        assert unknown["detail"]["unknown_columns"] == ["weird_col"]

        only = "ftir_no,notes\nFT-1,hello\n"
        partial = must(client.post("/upload", files={"file": ("part.csv", only.encode(), "text/csv")}), 400)
        assert "ftir_report_date" in partial["detail"]["missing_columns"]
        assert "notes" in partial["detail"]["unknown_columns"]

        injected = must(
            client.post("/charts/custom", json={"chart_type": "bar", "x": "outbreak_country; drop table records", "agg": "count"}),
            400,
        )
        assert "not available" in injected["detail"]["message"]

        loaded = must(client.post("/upload", files={"file": ("ftir_sample.csv", sample.read_bytes(), "text/csv")}))
        assert loaded["inserted"] == 96, loaded
        assert loaded["rows_rejected"] == 0
        assert loaded["total_records"] == 96

        again = must(client.post("/upload", files={"file": ("ftir_sample.csv", sample.read_bytes(), "text/csv")}))
        assert again["inserted"] == 0
        assert again["duplicates_skipped"] == 96

        basic = must(client.get("/charts/basic"))
        assert basic["summary"]["record_count"] == 96
        assert basic["summary"]["measures"][0]["count"] > 0
        assert basic["summary"]["measures"][0]["median"] is not None
        kinds = {chart["kind"] for chart in basic["charts"]}
        assert "line" in kinds and "bar" in kinds
        assert any(chart["id"] == "reports_over_time" for chart in basic["charts"])

        country = must(
            client.post("/charts/custom", json={"chart_type": "bar", "x": "outbreak_country", "agg": "count"})
        )
        assert country["data"] and country["kind"] == "bar"

        trend = must(
            client.post("/charts/custom", json={"chart_type": "line", "x": "ftir_report_date", "agg": "count"})
        )
        assert trend["kind"] == "line" and len(trend["data"]) > 1

        pie = must(client.post("/charts/custom", json={"chart_type": "pie", "x": "rank", "agg": "count"}))
        assert pie["kind"] == "pie" and pie["data"]

        means = must(
            client.post(
                "/charts/custom",
                json={"chart_type": "bar", "x": "outbreak_country", "y": "days_used", "agg": "mean"},
            )
        )
        assert means["data"]

        scatter = must(
            client.post(
                "/charts/custom",
                json={"chart_type": "scatter", "x": "days_used", "y": "using_km_int", "agg": "mean"},
            )
        )
        assert scatter["kind"] == "scatter" and len(scatter["data"]) > 10

        bad_scatter = must(
            client.post("/charts/custom", json={"chart_type": "scatter", "x": "rank", "y": "status"}),
            400,
        )
        assert "numeric" in bad_scatter["detail"]["message"].lower()

        book = openpyxl.Workbook()
        sheet = book.active
        sheet.append(REQUIRED_COLUMNS)
        sheet.append(["FTIR-XLSX-1", "2025-03-01", "Open", "PM-210", "India", "Noise from the rear axle"])
        buffer = BytesIO()
        book.save(buffer)
        excel = must(client.post("/upload", files={"file": ("one.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}))
        assert excel["inserted"] == 1
        assert excel["sheet"]

        exported = client.get("/export")
        assert exported.status_code == 200
        assert "ftir_no" in exported.text.splitlines()[0]
        assert "FTIR-2024-0001" in exported.text

        blank = "ftir_no,ftir_report_date,status,product_model_code,outbreak_country,customer_complaint\n,,,,,Noise\n"
        rejected = must(client.post("/upload", files={"file": ("blank.csv", blank.encode(), "text/csv")}), 400)
        assert "FTIR number" in rejected["detail"]["message"]

    print("smoke ok")


if __name__ == "__main__":
    main()
