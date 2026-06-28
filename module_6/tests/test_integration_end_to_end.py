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
    """Queue tasks, simulate worker insertion, and verify rendered analytics."""
    published_tasks = []

    def fake_publish(kind, payload=None, headers=None):
        published_tasks.append(
            {
                "kind": kind,
                "payload": payload,
                "headers": headers,
            }
        )

    app = create_app(
        {"TESTING": True, "DATABASE_URL": empty_database},
        publish_func=fake_publish,
        query_func=get_analysis_results,
    )
    client = app.test_client()

    pull_response = client.post("/pull-data")
    assert pull_response.status_code == 202
    assert pull_response.get_json()["queued"] is True
    assert published_tasks[-1]["kind"] == "scrape_new_data"

    # Simulate the worker processing the queued scrape task.
    inserted = insert_applicants(SAMPLE_RECORDS, empty_database)
    assert inserted == 2

    update_response = client.post("/update-analysis")
    assert update_response.status_code == 202
    assert update_response.get_json()["queued"] is True
    assert published_tasks[-1]["kind"] == "recompute_analytics"

    page = client.get("/analysis")
    html = page.data.decode()

    assert page.status_code == 200
    assert "Answer:" in html
    assert re.search(r"\d+\.\d{2}%", html)


@pytest.mark.integration
def test_multiple_pulls_with_overlapping_data_remain_consistent(empty_database):
    """Repeated worker processing does not create duplicate applicants."""
    published_tasks = []

    def fake_publish(kind, payload=None, headers=None):
        published_tasks.append(
            {
                "kind": kind,
                "payload": payload,
                "headers": headers,
            }
        )

    app = create_app(
        {"TESTING": True, "DATABASE_URL": empty_database},
        publish_func=fake_publish,
        query_func=get_analysis_results,
    )
    client = app.test_client()

    first_response = client.post("/pull-data")
    assert first_response.status_code == 202

    first_inserted = insert_applicants(SAMPLE_RECORDS, empty_database)
    assert first_inserted == 2

    second_response = client.post("/pull-data")
    assert second_response.status_code == 202

    second_inserted = insert_applicants(SAMPLE_RECORDS, empty_database)
    assert second_inserted == 0

    assert [task["kind"] for task in published_tasks] == [
        "scrape_new_data",
        "scrape_new_data",
    ]

    with connect(empty_database) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            assert cur.fetchone()[0] == 2
