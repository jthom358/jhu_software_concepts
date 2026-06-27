"""Tests for Flask app construction and analysis page rendering."""

import pytest
from bs4 import BeautifulSoup

from src.web.app import create_app


@pytest.mark.web
def test_create_app_has_required_routes(web_app):
    routes = {rule.rule for rule in web_app.url_map.iter_rules()}
    assert "/" in routes
    assert "/analysis" in routes
    assert "/pull-data" in routes
    assert "/update-analysis" in routes


@pytest.mark.web
def test_get_analysis_page_loads_with_required_components(client):
    response = client.get("/analysis")
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    page_text = soup.get_text(" ")

    assert "Analysis" in page_text
    assert "Answer:" in page_text
    assert soup.select_one('[data-testid="pull-data-btn"]').get_text(strip=True) == "Pull Data"
    assert soup.select_one('[data-testid="update-analysis-btn"]').get_text(strip=True) == "Update Analysis"


@pytest.mark.web
def test_root_renders_analysis_page(fake_results):
    app = create_app({"TESTING": True}, query_func=lambda database_url=None: fake_results)
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert b"GradCafe Data Analysis" in response.data
