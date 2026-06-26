"""Tests for button endpoints and busy-state behavior."""

import pytest


@pytest.mark.buttons
def test_post_pull_data_returns_ok_and_triggers_loader(web_app):
    response = web_app.test_client().post("/pull-data")
    assert response.status_code == 200
    assert response.get_json() == {"ok": True, "pulled": 2, "inserted": 2}
    assert web_app.test_calls["pull"] == 1


@pytest.mark.buttons
def test_post_update_analysis_returns_ok_when_not_busy(web_app):
    response = web_app.test_client().post("/update-analysis")
    assert response.status_code == 200
    assert response.get_json() == {"ok": True, "count": 2}
    assert web_app.test_calls["query"] == 1


@pytest.mark.buttons
def test_update_analysis_returns_409_and_does_not_update_when_busy(web_app):
    web_app.config["PULL_IN_PROGRESS"] = True
    response = web_app.test_client().post("/update-analysis")
    assert response.status_code == 409
    assert response.get_json() == {"ok": False, "busy": True}
    assert web_app.test_calls["query"] == 0


@pytest.mark.buttons
def test_pull_data_returns_409_when_busy(web_app):
    web_app.config["PULL_IN_PROGRESS"] = True
    response = web_app.test_client().post("/pull-data")
    assert response.status_code == 409
    assert response.get_json() == {"ok": False, "busy": True}
    assert web_app.test_calls["pull"] == 0


@pytest.mark.buttons
def test_pull_data_clears_busy_flag_after_loader_error(fake_results):
    def broken_pull(database_url=None):
        raise ValueError("loader failed")

    from src.app import create_app

    app = create_app({"TESTING": True}, pull_func=broken_pull, query_func=lambda database_url=None: fake_results)
    with pytest.raises(ValueError):
        app.test_client().post("/pull-data")
    assert app.config["PULL_IN_PROGRESS"] is False
