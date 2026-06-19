from datetime import date

import pytest

from src import pull_data
from src.load_data import (
    build_program,
    build_term,
    clean_date,
    insert_applicants,
)

from src.query_data import clamp_limit

@pytest.mark.db
def test_load_data_helper_edge_cases():
    """Cover helper branches used by database normalization."""
    existing_date = date(2026, 5, 29)
    assert clean_date(existing_date) == existing_date

    assert build_program({"program_name_raw": "Computer Science"}) == "Computer Science"
    assert build_program({"university_raw": "Johns Hopkins University"}) == "Johns Hopkins University"
    
    assert build_term({"term": "Spring 2027"}) == "Spring 2027"
    assert build_term({}) is None


@pytest.mark.db
def test_insert_applicants_skips_invalid_records(database_url):
    """Invalid records normalize to None and should not be inserted."""
    inserted = insert_applicants([{}], database_url)
    assert inserted == 0

@pytest.mark.buttons
def test_pull_and_insert_uses_scraper_and_loader(monkeypatch):
    """The pull helper should scrape records and pass them to the loader."""
    fake_records = [{"program_name_raw": "AI", "university_raw": "JHU"}]

    def fake_scraper(target_records):
        assert target_records == 7
        return fake_records

    def fake_insert(records, database_url):
        assert records == fake_records
        assert database_url == "postgresql://example"
        return 1

    monkeypatch.setattr(pull_data, "insert_applicants", fake_insert)

    summary = pull_data.pull_and_insert(
        "postgresql://example",
        scraper=fake_scraper,
        target_records=7,
    )

    assert summary == {"pulled": 1, "inserted": 1}


@pytest.mark.buttons
def test_pull_data_main_prints_summary(monkeypatch, capsys):
    """The CLI wrapper prints the pull summary."""
    monkeypatch.setattr(
        pull_data,
        "pull_and_insert",
        lambda: {"pulled": 2, "inserted": 1},
    )

    pull_data.main()

    output = capsys.readouterr().out
    assert "Pulled 2 recent records." in output
    assert "Inserted 1 new records into the database." in output

def test_clamp_limit_handles_invalid_and_out_of_range_values():
    """Query limits should remain within the safe allowed range."""
    assert clamp_limit("invalid") == 1
    assert clamp_limit(None) == 1
    assert clamp_limit(0) == 1
    assert clamp_limit(-50) == 1
    assert clamp_limit(50) == 50
    assert clamp_limit(1000) == 100