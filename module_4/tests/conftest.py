"""Shared pytest fixtures for Module 4 tests."""

from __future__ import annotations

import os

import pytest

from src.app import create_app
from src.load_data import create_applicants_table
from src.db_utils import connect


@pytest.fixture
def fake_results():
    return [
        {"question": "1. Analysis sample count?", "answer": "2", "sql": "SELECT 2;"},
        {"question": "2. What percent are accepted?", "answer": "50.00%", "sql": "SELECT 50.00;"},
    ]


@pytest.fixture
def web_app(fake_results):
    calls = {"pull": 0, "query": 0}

    def fake_pull(database_url=None):
        calls["pull"] += 1
        return {"pulled": 2, "inserted": 2}

    def fake_query(database_url=None):
        calls["query"] += 1
        return fake_results

    app = create_app(
        {"TESTING": True, "DATABASE_URL": "postgresql://example/test"},
        pull_func=fake_pull,
        query_func=fake_query,
    )
    app.test_calls = calls
    return app


@pytest.fixture
def client(web_app):
    return web_app.test_client()


@pytest.fixture
def database_url():
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gradcafe_test")


@pytest.fixture
def empty_database(database_url):
    create_applicants_table(database_url, drop_existing=True)
    yield database_url
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS applicants;")
        conn.commit()
