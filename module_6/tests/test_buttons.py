"""Tests for asynchronous Flask button endpoints."""

import pytest

from src.web.app import create_app


@pytest.mark.buttons
def test_post_pull_data_queues_scrape_task(web_app):
    """Pull Data queues the scrape task and redirects to analysis."""
    response = web_app.test_client().post("/pull-data")

    assert response.status_code == 303
    assert response.headers["Location"].endswith("/analysis")
    assert web_app.test_calls["publish"] == [
        {
            "kind": "scrape_new_data",
            "payload": {},
            "headers": None,
        }
    ]


@pytest.mark.buttons
def test_post_update_analysis_queues_recompute_task(web_app):
    """Update Analysis queues the analytics task and redirects to analysis."""
    response = web_app.test_client().post("/update-analysis")

    assert response.status_code == 303
    assert response.headers["Location"].endswith("/analysis")
    assert web_app.test_calls["publish"] == [
        {
            "kind": "recompute_analytics",
            "payload": {},
            "headers": None,
        }
    ]


@pytest.mark.buttons
def test_pull_data_returns_503_when_queue_is_unavailable(fake_results):
    """Pull Data returns 503 when RabbitMQ publishing fails."""

    def broken_publish(_kind, _payload=None, _headers=None):
        raise RuntimeError("RabbitMQ unavailable")

    app = create_app(
        {"TESTING": True},
        query_func=lambda _database_url=None: fake_results,
        publish_func=broken_publish,
    )

    response = app.test_client().post("/pull-data")

    assert response.status_code == 503
    assert response.get_json() == {
        "ok": False,
        "queued": False,
        "message": "Task queue unavailable.",
    }


@pytest.mark.buttons
def test_update_analysis_returns_503_when_queue_is_unavailable(fake_results):
    """Update Analysis returns 503 when RabbitMQ publishing fails."""

    def broken_publish(_kind, _payload=None, _headers=None):
        raise RuntimeError("RabbitMQ unavailable")

    app = create_app(
        {"TESTING": True},
        query_func=lambda _database_url=None: fake_results,
        publish_func=broken_publish,
    )

    response = app.test_client().post("/update-analysis")

    assert response.status_code == 503
    assert response.get_json() == {
        "ok": False,
        "queued": False,
        "message": "Task queue unavailable.",
    }