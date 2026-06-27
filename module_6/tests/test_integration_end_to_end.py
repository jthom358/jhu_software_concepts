"""End-to-end tests for pull, update, render, and repeated pulls."""

import re

import pytest

from src.web.app import create_app
from src.db.load_data import insert_applicants
from src.worker.etl.query_data import get_analysis_results
from tests.test_db_insert import SAMPLE_RECORDS
from src.db.db_utils import connect


@pytest.mark.integration
def test_end_to_end_pull_update_render(empty_database):
    def fake_pull(database_url=None):
        inserted = insert_applicants(SAMPLE_RECORDS, database_url)
        return {"pulled": len(SAMPLE_RECORDS), "inserted": inserted}

    app = create_app(
        {"TESTING": True, "DATABASE_URL": empty_database},
        pull_func=fake_pull,
        query_func=get_analysis_results,
    )
    client = app.test_client()

    pull_response = client.post("/pull-data")
    assert pull_response.status_code == 200
    assert pull_response.get_json()["inserted"] == 2

    update_response = client.post("/update-analysis")
    assert update_response.status_code == 200
    assert update_response.get_json()["ok"] is True

    page = client.get("/analysis")
    html = page.data.decode()
    assert page.status_code == 200
    assert "Answer:" in html
    assert re.search(r"\d+\.\d{2}%", html)


@pytest.mark.integration
def test_multiple_pulls_with_overlapping_data_remain_consistent(empty_database):
    def fake_pull(database_url=None):
        inserted = insert_applicants(SAMPLE_RECORDS, database_url)
        return {"pulled": len(SAMPLE_RECORDS), "inserted": inserted}

    app = create_app({"TESTING": True, "DATABASE_URL": empty_database}, pull_func=fake_pull, query_func=get_analysis_results)
    client = app.test_client()

    assert client.post("/pull-data").get_json()["inserted"] == 2
    assert client.post("/pull-data").get_json()["inserted"] == 0

    with connect(empty_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            assert cur.fetchone()[0] == 2
