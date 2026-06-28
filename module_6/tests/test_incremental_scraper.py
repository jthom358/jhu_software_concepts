"""Tests for incremental GradCafe ingestion."""

from unittest.mock import Mock

from src.worker.etl.incremental_scraper import (
    record_watermark,
    records_after_watermark,
    run_incremental_scrape,
)


RECORDS = [
    {
        "university_raw": "Johns Hopkins University",
        "program_name_raw": "Computer Science",
        "date_added": "June 28, 2026",
        "applicant_status": "Accepted",
        "degree": "Masters",
    },
    {
        "university_raw": "Stanford University",
        "program_name_raw": "Computer Science",
        "date_added": "June 27, 2026",
        "applicant_status": "Rejected",
        "degree": "PhD",
    },
]


def test_record_watermark_is_stable():
    """Identical records produce identical fingerprints."""
    assert record_watermark(RECORDS[0]) == record_watermark(
        dict(RECORDS[0])
    )


def test_records_after_watermark_stops_at_previous_record():
    """Only records newer than the watermark are returned."""
    watermark = record_watermark(RECORDS[1])

    assert records_after_watermark(RECORDS, watermark) == [RECORDS[0]]


def test_records_after_missing_watermark_returns_all_records():
    """The first ingestion treats every scraped record as new."""
    assert records_after_watermark(RECORDS, None) == RECORDS


def test_incremental_scrape_inserts_and_advances_watermark(monkeypatch):
    """The task filters, inserts, and updates its watermark."""
    connection = Mock()
    previous_watermark = record_watermark(RECORDS[1])

    monkeypatch.setattr(
        "src.worker.etl.incremental_scraper.get_watermark",
        lambda conn, source: previous_watermark,
    )

    insert_mock = Mock(return_value=1)
    monkeypatch.setattr(
        "src.worker.etl.incremental_scraper."
        "insert_applicants_with_connection",
        insert_mock,
    )

    update_mock = Mock()
    monkeypatch.setattr(
        "src.worker.etl.incremental_scraper.update_watermark",
        update_mock,
    )

    summary = run_incremental_scrape(
        connection,
        {"target_records": 25},
        scraper=lambda target_records: RECORDS,
    )

    assert summary == {
        "pulled": 2,
        "new": 1,
        "inserted": 1,
    }

    insert_mock.assert_called_once_with(
        connection,
        [RECORDS[0]],
    )

    update_mock.assert_called_once_with(
        connection,
        "gradcafe",
        record_watermark(RECORDS[0]),
    )


def test_incremental_scrape_handles_empty_result(monkeypatch):
    """An empty scrape does not replace the watermark."""
    connection = Mock()

    monkeypatch.setattr(
        "src.worker.etl.incremental_scraper.get_watermark",
        lambda conn, source: None,
    )

    insert_mock = Mock(return_value=0)
    monkeypatch.setattr(
        "src.worker.etl.incremental_scraper."
        "insert_applicants_with_connection",
        insert_mock,
    )

    update_mock = Mock()
    monkeypatch.setattr(
        "src.worker.etl.incremental_scraper.update_watermark",
        update_mock,
    )

    summary = run_incremental_scrape(
        connection,
        {},
        scraper=lambda target_records: [],
    )

    assert summary == {
        "pulled": 0,
        "new": 0,
        "inserted": 0,
    }

    update_mock.assert_not_called()


def test_incremental_scrape_clamps_invalid_target(monkeypatch):
    """Invalid task limits fall back to the configured default."""
    connection = Mock()
    observed_targets = []

    monkeypatch.setattr(
        "src.worker.etl.incremental_scraper.get_watermark",
        lambda conn, source: None,
    )
    monkeypatch.setattr(
        "src.worker.etl.incremental_scraper."
        "insert_applicants_with_connection",
        lambda conn, records: 0,
    )

    def scraper(*, target_records):
        observed_targets.append(target_records)
        return []

    run_incremental_scrape(
        connection,
        {"target_records": "invalid"},
        scraper=scraper,
    )

    assert observed_targets == [25]