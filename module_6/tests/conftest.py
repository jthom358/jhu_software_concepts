"""Shared pytest fixtures for Module 4 tests."""

from __future__ import annotations

import pytest
import os

from src.web.app import create_app
from src.db.load_data import create_applicants_table
from src.db.db_utils import connect, get_database_url


@pytest.fixture
def fake_results():
    return [
        {"question": "1. Analysis sample count?", "answer": "2", "sql": "SELECT 2;"},
        {"question": "2. What percent are accepted?", "answer": "50.00%", "sql": "SELECT 50.00;"},
    ]


@pytest.fixture
def web_app(fake_results, database_url):
    """Create a Flask test application with fake query and publisher functions."""
    calls = {
        "query": 0,
        "publish": [],
    }

    def fake_query(_database_url=None):
        calls["query"] += 1
        return fake_results

    def fake_publish(kind, payload=None, headers=None):
        calls["publish"].append(
            {
                "kind": kind,
                "payload": payload,
                "headers": headers,
            }
        )

    app = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": database_url,
        },
        query_func=fake_query,
        publish_func=fake_publish,
    )
    app.test_calls = calls
    return app


@pytest.fixture
def client(web_app):
    return web_app.test_client()


@pytest.fixture
def database_url():
    return os.getenv("TEST_DATABASE_URL") or get_database_url()


@pytest.fixture
def empty_database(database_url):
    create_applicants_table(database_url, drop_existing=True)
    yield database_url
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS applicants;")
        conn.commit()
