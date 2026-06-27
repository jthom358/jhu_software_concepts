"""Tests for analysis labels and percentage formatting."""

import re

import pytest
from bs4 import BeautifulSoup

from src.worker.etl.query_data import format_answer


@pytest.mark.analysis
def test_format_answer_for_percentages_and_missing_values():
    assert format_answer(39.281, percentage=True) == "39.28%"
    assert format_answer(7, percentage=False) == "7"
    assert format_answer(3.5, percentage=False) == "3.50"
    assert format_answer(None, percentage=True) == "N/A"


@pytest.mark.analysis
def test_page_includes_answer_labels_and_two_decimal_percentages(client):
    response = client.get("/analysis")
    assert response.status_code == 200

    html = response.data.decode()
    soup = BeautifulSoup(html, "html.parser")
    result_cards = soup.select('[data-testid="analysis-result"]')
    assert result_cards
    assert all("Answer:" in card.get_text(" ") for card in result_cards)

    percentages = re.findall(r"\d+\.\d+%", html)
    assert percentages == ["50.00%"]
    assert all(re.fullmatch(r"\d+\.\d{2}%", value) for value in percentages)
