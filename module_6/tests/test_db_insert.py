"""Tests for PostgreSQL inserts, idempotency, and query outputs."""

import json

import pytest

import src.db.load_data as load_data
from src.db.db_utils import connect, get_database_url
from src.db.load_data import (
    build_program,
    clean_date,
    clean_float,
    clean_gre,
    create_applicants_table,
    insert_applicants,
    load_initial_data,
    load_json_records,
    normalize_record,
    get_watermark,
    insert_applicants_with_connection,
    update_watermark,
)
from src.worker.etl.query_data import get_analysis_results, get_expected_keys
from src.db.db_utils import connect


SAMPLE_RECORDS = [
    {
        "program_name_raw": "Computer Science",
        "university_raw": "Johns Hopkins University",
        "date_added": "May 29, 2026",
        "applicant_status": "Accepted",
        "start_term": "Fall",
        "start_year": "2026",
        "student_type": "International",
        "gpa": "3.80",
        "gre_score": "169",
        "gre_v_score": "165",
        "gre_aw": "5.0",
        "degree": "Masters",
        "comments": "sample",
        "entry_url": "https://example.com/1",
    },
    {
        "program_name_raw": "Computer Science",
        "university_raw": "Stanford University",
        "date_added": "May 30, 2026",
        "applicant_status": "Rejected",
        "start_term": "Fall",
        "start_year": "2026",
        "student_type": "American",
        "gpa": "3.40",
        "degree": "PhD",
        "entry_url": "https://example.com/2",
    },
]


@pytest.mark.db
def test_insert_on_pull_writes_required_non_null_fields(empty_database):
    inserted = insert_applicants(SAMPLE_RECORDS, empty_database)
    assert inserted == 2

    with connect(empty_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            assert cur.fetchone()[0] == 2
            cur.execute("SELECT p_id, program FROM applicants ORDER BY p_id LIMIT 1;")
            p_id, program = cur.fetchone()
            assert p_id == 1
            assert program == "Computer Science, Johns Hopkins University"


@pytest.mark.db
def test_duplicate_rows_do_not_create_duplicates(empty_database):
    assert insert_applicants(SAMPLE_RECORDS, empty_database) == 2
    assert insert_applicants(SAMPLE_RECORDS, empty_database) == 0

    with connect(empty_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            assert cur.fetchone()[0] == 2


@pytest.mark.db
def test_query_function_returns_expected_dictionary_keys(empty_database):
    insert_applicants(SAMPLE_RECORDS, empty_database)
    results = get_analysis_results(empty_database)
    assert results
    assert all(get_expected_keys().issubset(result.keys()) for result in results)
    assert any(result["answer"].endswith("%") for result in results)


@pytest.mark.db
def test_cleaning_and_normalization_helpers_cover_edge_cases():
    assert clean_float("") is None
    assert clean_float("bad") is None
    assert clean_float("3.25") == 3.25
    assert clean_gre("120", 130, 170) is None
    assert clean_gre("165", 130, 170) == 165
    assert clean_date("") is None
    assert clean_date("2026-05-29").isoformat() == "2026-05-29"
    assert clean_date("not a date") is None
    assert build_program({"program": "Existing Program"}) == "Existing Program"
    assert normalize_record({"comments": "missing program"}, 1) is None


@pytest.mark.db
def test_load_json_records_and_initial_load(tmp_path, empty_database):
    data_file = tmp_path / "records.json"
    data_file.write_text(json.dumps(SAMPLE_RECORDS), encoding="utf-8")
    assert len(load_json_records(str(data_file))) == 2
    assert load_initial_data(empty_database, str(data_file)) == 2


@pytest.mark.db
def test_database_url_resolution(monkeypatch):
    assert get_database_url("postgresql://direct/db") == "postgresql://direct/db"
    monkeypatch.setenv("DATABASE_URL", "postgresql://env/db")
    assert get_database_url() == "postgresql://env/db"
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv("DB_NAME", "gradcafe")
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "pw")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    assert get_database_url() == "postgresql://postgres:pw@localhost:5432/gradcafe"


def test_insert_with_existing_connection_requires_caller_commit(empty_database):
    """Connection-based inserts remain under caller transaction control."""
    with connect(empty_database) as conn:
        inserted = insert_applicants_with_connection(conn, SAMPLE_RECORDS)

        assert inserted == 2

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            assert cur.fetchone()[0] == 2

        conn.rollback()

    with connect(empty_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            assert cur.fetchone()[0] == 0


def test_watermark_round_trip(empty_database):
    """Watermarks are inserted and updated idempotently."""
    with connect(empty_database) as conn:
        assert get_watermark(conn, "gradcafe") is None

        update_watermark(conn, "gradcafe", "2026-06-01")
        assert get_watermark(conn, "gradcafe") == "2026-06-01"

        update_watermark(conn, "gradcafe", "2026-06-02")
        assert get_watermark(conn, "gradcafe") == "2026-06-02"

        conn.commit()


def test_insert_applicants_rolls_back_on_failure(monkeypatch):
    """A failed insert rolls back and propagates the original error."""

    class FakeConnection:
        """Minimal connection object for testing transaction behavior."""

        def __init__(self):
            self.rolled_back = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def commit(self):
            raise AssertionError("Commit must not occur after an insert failure.")

        def rollback(self):
            self.rolled_back = True

    fake_connection = FakeConnection()

    monkeypatch.setattr(
        load_data,
        "connect",
        lambda database_url=None: fake_connection,
    )

    def raise_insert_error(conn, records):
        del conn, records
        raise RuntimeError("simulated insert failure")

    monkeypatch.setattr(
        load_data,
        "insert_applicants_with_connection",
        raise_insert_error,
    )

    with pytest.raises(RuntimeError, match="simulated insert failure"):
        load_data.insert_applicants([], "postgresql://unused")

    assert fake_connection.rolled_back is True