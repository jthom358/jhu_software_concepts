"""Create and load the GradCafe PostgreSQL applicants table."""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any, Iterable

from src.db.db_utils import connect

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(BASE_DIR)
DATA_FILE = os.path.join(SRC_DIR, "data", "applicant_data.json")

REQUIRED_FIELDS = [
    "p_id",
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
]


def clean_float(value: Any) -> float | None:
    """Convert GPA and score values to floats when possible."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_gre(value: Any, lowest: float, highest: float) -> float | None:
    """Convert GRE values to floats and remove values outside the expected range."""
    score = clean_float(value)
    if score is None or score < lowest or score > highest:
        return None
    return score


def clean_date(date_string: Any) -> date | None:
    """Convert GradCafe date strings such as ``May 29, 2026`` to dates."""
    if isinstance(date_string, date):
        return date_string
    if date_string is None or date_string == "":
        return None
    for fmt in ("%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(date_string), fmt).date()
        except ValueError:
            continue
    return None


def build_term(record: dict[str, Any]) -> str | None:
    """Build a term string such as ``Fall 2026`` from a scraped record."""
    if record.get("term"):
        return record.get("term")
    if record.get("start_term") and record.get("start_year"):
        return f"{record.get('start_term')} {record.get('start_year')}"
    return None


def build_program(record: dict[str, Any]) -> str | None:
    """Build the Module 3 ``program`` field from cleaned or scraped values."""
    if record.get("program"):
        return record.get("program")

    program_name = record.get("program_name_raw") or record.get("llm-generated-program")
    university = record.get("university_raw") or record.get("llm-generated-university")

    if program_name and university:
        return f"{program_name}, {university}"
    if program_name:
        return program_name
    if university:
        return university
    return None


def normalize_record(
    record: dict[str, Any],
    p_id: int,
) -> dict[str, Any] | None:
    """Normalize one JSON/scraped record into the required applicants schema."""
    program = build_program(record)
    if not program:
        return None

    return {
        "p_id": p_id,
        "program": program,
        "comments": record.get("comments"),
        "date_added": clean_date(record.get("date_added")),
        "url": record.get("entry_url") or record.get("url"),
        "status": record.get("applicant_status") or record.get("status"),
        "term": build_term(record),
        "us_or_international": (
            record.get("student_type")
            or record.get("us_or_international")
        ),
        "gpa": clean_float(record.get("gpa")),
        "gre": clean_gre(
            record.get("gre_score") or record.get("gre"),
            130,
            170,
        ),
        "gre_v": clean_gre(
            record.get("gre_v_score") or record.get("gre_v"),
            130,
            170,
        ),
        "gre_aw": clean_gre(record.get("gre_aw"), 0, 6),
        "degree": record.get("degree"),
        "llm_generated_program": (
            record.get("llm-generated-program")
            or record.get("llm_generated_program")
            or record.get("program_name_raw")
        ),
        "llm_generated_university": (
            record.get("llm-generated-university")
            or record.get("llm_generated_university")
            or record.get("university_raw")
        ),
    }


def create_applicants_table(
    database_url: str | None = None,
    *,
    drop_existing: bool = False,
) -> None:
    """Create the applicants table and uniqueness index used by tests and the app."""
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            if drop_existing:
                cur.execute("DROP TABLE IF EXISTS ingestion_watermarks;")
                cur.execute("DROP TABLE IF EXISTS applicants;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS applicants (
                    p_id INTEGER PRIMARY KEY,
                    program TEXT NOT NULL,
                    comments TEXT,
                    date_added DATE,
                    url TEXT,
                    status TEXT,
                    term TEXT,
                    us_or_international TEXT,
                    gpa FLOAT,
                    gre FLOAT,
                    gre_v FLOAT,
                    gre_aw FLOAT,
                    degree TEXT,
                    llm_generated_program TEXT,
                    llm_generated_university TEXT
                );
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS applicants_unique_record_idx
                ON applicants (
                    COALESCE(program, ''),
                    COALESCE(date_added, DATE '1900-01-01'),
                    COALESCE(status, ''),
                    COALESCE(degree, '')
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ingestion_watermarks (
                    source TEXT PRIMARY KEY,
                    last_seen TEXT,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )


def next_applicant_id(cur: Any) -> int:
    """Return the next integer primary key for applicants."""
    cur.execute("SELECT COALESCE(MAX(p_id), 0) + 1 FROM applicants;")
    return int(cur.fetchone()[0])


def insert_applicants_with_connection(
    conn: Any,
    records: Iterable[dict[str, Any]],
) -> int:
    """Insert normalized applicants using an existing transaction."""
    inserted = 0

    with conn.cursor() as cur:
        p_id = next_applicant_id(cur)

        for source_record in records:
            record = normalize_record(source_record, p_id)
            if record is None:
                continue

            cur.execute(
                """
                INSERT INTO applicants (
                    p_id,
                    program,
                    comments,
                    date_added,
                    url,
                    status,
                    term,
                    us_or_international,
                    gpa,
                    gre,
                    gre_v,
                    gre_aw,
                    degree,
                    llm_generated_program,
                    llm_generated_university
                )
                VALUES (
                    %(p_id)s,
                    %(program)s,
                    %(comments)s,
                    %(date_added)s,
                    %(url)s,
                    %(status)s,
                    %(term)s,
                    %(us_or_international)s,
                    %(gpa)s,
                    %(gre)s,
                    %(gre_v)s,
                    %(gre_aw)s,
                    %(degree)s,
                    %(llm_generated_program)s,
                    %(llm_generated_university)s
                )
                ON CONFLICT DO NOTHING;
                """,
                record,
            )

            if cur.rowcount == 1:
                inserted += 1
                p_id += 1

    return inserted


def insert_applicants(
    records: Iterable[dict[str, Any]],
    database_url: str | None = None,
) -> int:
    """Insert records using a self-managed database transaction."""
    with connect(database_url) as conn:
        try:
            inserted = insert_applicants_with_connection(conn, records)
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return inserted


def load_json_records(data_file: str = DATA_FILE) -> list[dict[str, Any]]:
    """Read applicant records from a JSON file."""
    with open(data_file, "r", encoding="utf-8") as file:
        return json.load(file)


def load_initial_data(database_url: str | None = None, data_file: str = DATA_FILE) -> int:
    """Drop, recreate, and load the applicants table from the Module 3 JSON file."""
    create_applicants_table(database_url, drop_existing=True)
    return insert_applicants(load_json_records(data_file), database_url)


def get_watermark(conn: Any, source: str) -> str | None:
    """Return the last processed watermark for a source."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT last_seen
            FROM ingestion_watermarks
            WHERE source = %s
            LIMIT 1;
            """,
            (source,),
        )
        row = cur.fetchone()

    return row[0] if row else None


def update_watermark(conn: Any, source: str, last_seen: str) -> None:
    """Insert or advance the watermark within the current transaction."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_watermarks (
                source,
                last_seen,
                updated_at
            )
            VALUES (%s, %s, NOW())
            ON CONFLICT (source)
            DO UPDATE SET
                last_seen = EXCLUDED.last_seen,
                updated_at = NOW();
            """,
            (source, last_seen),
        )


if __name__ == "__main__":
    RECORD_COUNT = load_initial_data()
    print(f"Loaded {RECORD_COUNT} applicant records into the applicants table.")
