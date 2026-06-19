"""Pull recent GradCafe data and insert only new rows into PostgreSQL."""

from __future__ import annotations

from typing import Callable

from .load_data import insert_applicants
from .scrape import scrape_data


def pull_and_insert(
    database_url: str | None = None,
    *,
    scraper: Callable[..., list[dict]] = scrape_data,
    target_records: int = 25,
) -> dict[str, int]:
    """Scrape recent GradCafe records and insert new records into the database."""
    records = scraper(target_records=target_records)
    inserted = insert_applicants(records, database_url)
    return {"pulled": len(records), "inserted": inserted}


def main() -> None:
    """Run a small pull from the command line."""
    summary = pull_and_insert()
    print(f"Pulled {summary['pulled']} recent records.")
    print(f"Inserted {summary['inserted']} new records into the database.")


if __name__ == "__main__":
    main()
