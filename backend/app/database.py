"""SQLite connection helpers and schema bootstrap."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schema_refe.sql"
DEFAULT_DB = ROOT / "backend" / "data" / "mqih.db"


def db_path() -> Path:
    override = os.environ.get("MQIH_DB")
    return Path(override) if override else DEFAULT_DB


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    pragmas: list[str] = []
    body: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("PRAGMA"):
            pragmas.append(stripped.rstrip(";"))
        else:
            body.append(line)
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    try:
        for pragma in pragmas:
            conn.execute(pragma)
        conn.executescript("\n".join(body))
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_conn():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def refresh_materialized(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM mv_country_month")
    conn.execute(
        """
        INSERT INTO mv_country_month (outbreak_country, report_year, report_month, record_count)
        SELECT outbreak_country, report_year, report_month, COUNT(*)
        FROM records
        WHERE outbreak_country IS NOT NULL
          AND TRIM(outbreak_country) != ''
          AND report_year IS NOT NULL
          AND report_month IS NOT NULL
        GROUP BY outbreak_country, report_year, report_month
        """
    )
    conn.execute("DELETE FROM mv_trouble_codes")
    conn.execute(
        """
        INSERT INTO mv_trouble_codes (trouble_code, record_count)
        SELECT trouble_code_complaint, COUNT(*)
        FROM records
        WHERE trouble_code_complaint IS NOT NULL
          AND TRIM(trouble_code_complaint) != ''
        GROUP BY trouble_code_complaint
        """
    )
    conn.execute("DELETE FROM mv_dealer_summary")
    conn.execute(
        """
        INSERT INTO mv_dealer_summary (reported_company, record_count)
        SELECT reported_company, COUNT(*)
        FROM records
        WHERE reported_company IS NOT NULL
          AND TRIM(reported_company) != ''
        GROUP BY reported_company
        """
    )
    conn.execute("DELETE FROM mv_quality_dist")
    conn.execute(
        """
        INSERT INTO mv_quality_dist (quality, record_count)
        SELECT quality, COUNT(*)
        FROM records
        WHERE quality IS NOT NULL AND TRIM(quality) != ''
        GROUP BY quality
        """
    )
