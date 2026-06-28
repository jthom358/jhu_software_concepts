""""
Module 2 GradCafe scraper

This file contains the scraping logic for collecting public
 GradCafe graduate admissions applicant data and saving it to applicant_data.json

 Current version:
 -Defines constants
 -Builds GradCafe URLs with urllib
 -checks robots.txt with urllib.robotparser
 """

import json
import random
import time
import re
import hashlib
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

from src.db.load_data import (
    get_watermark,
    insert_applicants_with_connection,
    update_watermark,
)

BASE_URL = "https://www.thegradcafe.com"
SURVEY_PATH = "/survey/"
ROBOTS_URL = urljoin(BASE_URL, "/robots.txt")

SRC_DIR = Path(__file__).resolve().parents[2]
OUTPUT_PATH = SRC_DIR / "data" / "new_applicant_data.json"

USER_AGENT = "jhu-software-concepts-student-scraper/1.0"
MIN_DELAY_SECONDS = 2
MAX_DELAY_SECONDS = 3
TARGET_RECORDS = 25

def _build_survey_url(page: int = 1, program: str | None = None) -> str:
    """
    Build a GradCafe survey URL using urllib.parse.urlencode

    Parameters:
    page: The survey results page number
    program: Optional program search term

    Returns:
    A complete GradCafe survey URL
    """
    query_params: dict[str, Any] = {}

    if page > 1:
        query_params["page"] = page

    if program:
        query_params["program"] = program

    query_string = urlencode(query_params)

    if query_string:
        return urljoin(BASE_URL, SURVEY_PATH) + "?" + query_string

    return urljoin(BASE_URL, SURVEY_PATH)

def _polite_delay() -> None:
    """
    Pause between page requests so the scraper does not make rapid repeated requests.
    """
    delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    print(f"Waiting {delay:.1f} seconds before next request...")
    time.sleep(delay)

def _load_robot_parser() -> RobotFileParser:
    """
    Load and parse GradCafe robots.txt using urllib.robotparser
    """
    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.read()
    return parser


def _can_fetch(url: str, parser: RobotFileParser) -> bool:
    """
    Check whether robots.txt permits this scraper to fetch the provided URL
    """
    return parser.can_fetch(USER_AGENT, url)

def _fetch_html_with_urllib(url: str, max_attempts: int = 3) -> str | None:
    """
    Fetch a public GradCafe page using urllib.request.

    Returns the HTML as a string if the request succeeds.
    Returns None if the request fails, is blocked, or is rate-limited.
    """
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    for attempt in range(1, max_attempts + 1):
        try:
            with urlopen(request, timeout=30) as response:
                status_code = response.status

                if status_code in {403, 429}:
                    print(f"Stopped: site returned status code {status_code}.")
                    return None

                raw_bytes = response.read()
                html = raw_bytes.decode("utf-8", errors="replace")

                return html

        except HTTPError as error:
            print(f"HTTP error while fetching {url}: {error.code}")

            if error.code in {403, 429}:
                print("Stopping because the site blocked or rate-limited the request.")
                return None

            return None

        except (URLError, TimeoutError) as error:
            print(f"URL or timeout error while fetching {url}: {error}")

            if attempt < max_attempts:
                wait_seconds = 10 * attempt
                print(f"Temporary fetch issue. Retrying in {wait_seconds} seconds...")
                time.sleep(wait_seconds)
            else:
                print("Stopping because all retry attempts failed.")
                return None

    return None

def _clean_text(text: str | None) -> str:
    """
    Normalize whitespace in scraped text.
    """
    if text is None:
        return ""

    return re.sub(r"\s+", " ", text).strip()


def _split_program_and_degree(program_text: str) -> tuple[str, str | None]:
    """
    Split a combined program/degree cell into program name and degree.

    Example:
        "Computer Science PhD" -> ("Computer Science", "PhD")
    """
    degree_options = ["PhD", "Masters", "PsyD", "EdD", "JD", "MBA", "MFA", "IND", "Other"]

    for degree in degree_options:
        pattern = rf"\b{re.escape(degree)}\b$"

        if re.search(pattern, program_text, flags=re.IGNORECASE):
            program_name = re.sub(pattern, "", program_text, flags=re.IGNORECASE).strip()
            return program_name, degree

    return program_text.strip(), None


def _parse_decision(decision_text: str) -> tuple[str | None, str | None]:
    """
    Parse decision text into status and decision date.

    Example:
        "Accepted on Apr 17" -> ("Accepted", "Apr 17")
    """
    text = _clean_text(decision_text)

    match = re.search(
        r"\b(Accepted|Rejected|Wait listed|Waitlisted|Interview)\s+on\s+(.+)$",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None, None

    status = match.group(1).title()

    if status == "Waitlisted":
        status = "Wait listed"

    decision_date = match.group(2).strip()

    return status, decision_date


def _extract_start_term_and_year(text: str) -> tuple[str | None, str | None]:
    """
    Extract start term and year from detail text.

    Example:
        "Accepted on Apr 17 Fall 2026 Other" -> ("Fall", "2026")
    """
    match = re.search(r"\b(Fall|Spring|Summer|Winter)\s+(20\d{2})\b", text, flags=re.IGNORECASE)

    if not match:
        return None, None

    return match.group(1).title(), match.group(2)


def _extract_student_type(text: str) -> str | None:
    """
    Extract applicant type when available.
    """
    lower_text = text.lower()

    if "international" in lower_text:
        return "International"

    if "american" in lower_text:
        return "American"

    if "other" in lower_text:
        return "Other"

    return None

def _extract_gpa(text: str) -> str | None:
    """
    Extract GPA from applicant detail text.

    Example:
        "Accepted on May 08 Fall 2026 International GPA 3.84" -> "3.84"
    """
    match = re.search(r"\bGPA\s+([0-4](?:\.\d{1,2})?)\b", text, flags=re.IGNORECASE)

    if not match:
        return None

    return match.group(1)

def _extract_gre_score(text: str) -> str | None:
    """
    Extract total GRE score when available.
    """
    match = re.search(r"\bGRE\s+(\d{3})\b", text, flags=re.IGNORECASE)

    if not match:
        return None

    return match.group(1)


def _extract_gre_v_score(text: str) -> str | None:
    """
    Extract GRE verbal score when available.
    """
    match = re.search(r"\bGRE\s*V\s+(\d{2,3})\b", text, flags=re.IGNORECASE)

    if not match:
        return None

    return match.group(1)


def _extract_gre_aw_score(text: str) -> str | None:
    """
    Extract GRE analytical writing score when available.
    """
    match = re.search(r"\bGRE\s*AW\s+([0-6](?:\.\d)?)\b", text, flags=re.IGNORECASE)

    if not match:
        return None

    return match.group(1)

def _is_main_applicant_row(cells: list[str]) -> bool:
    """
    Check whether a row looks like the main applicant row.
    """
    if len(cells) < 4:
        return False

    date_pattern = (
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"[a-z]*\s+\d{1,2},\s+20\d{2}\b"
    )
    has_added_date = re.search(date_pattern, cells[2]) is not None
    has_decision = " on " in cells[3].lower()

    return has_added_date and has_decision

def _build_applicant_record(
    cells: list[str],
    detail_text: str,
    page_url: str,
) -> dict[str, str | None]:
    """Build one normalized applicant record from parsed table cells."""
    program_name, degree = _split_program_and_degree(cells[1])
    status, decision_date = _parse_decision(cells[3])
    start_term, start_year = _extract_start_term_and_year(detail_text)

    return {
        "university_raw": cells[0],
        "program_name_raw": program_name,
        "degree": degree,
        "date_added": cells[2],
        "entry_url": page_url,
        "applicant_status": status,
        "acceptance_date": decision_date if status == "Accepted" else None,
        "rejection_date": decision_date if status == "Rejected" else None,
        "start_term": start_term,
        "start_year": start_year,
        "student_type": _extract_student_type(detail_text),
        "gre_score": _extract_gre_score(detail_text),
        "gre_v_score": _extract_gre_v_score(detail_text),
        "gre_aw": _extract_gre_aw_score(detail_text),
        "gpa": _extract_gpa(detail_text),
        "comments": cells[4] if len(cells) > 4 else None,
        "raw_listing_text": _clean_text(" ".join(cells + [detail_text])),
    }

def _parse_records_from_html(
    html: str,
    page_url: str,
) -> list[dict[str, str | None]]:
    """Parse all applicant records from one GradCafe results page."""
    soup = BeautifulSoup(html, "lxml")
    rows = soup.find_all("tr")
    records = []
    index = 0

    while index < len(rows):
        cells = [
            _clean_text(cell.get_text(" ", strip=True))
            for cell in rows[index].find_all("td")
        ]

        if not _is_main_applicant_row(cells):
            index += 1
            continue

        detail_text = ""

        if index + 1 < len(rows):
            next_cells = [
                _clean_text(cell.get_text(" ", strip=True))
                for cell in rows[index + 1].find_all("td")
            ]

            if len(next_cells) == 1:
                detail_text = next_cells[0]

        records.append(
            _build_applicant_record(
                cells,
                detail_text,
                page_url,
            )
        )
        index += 1

    return records


def scrape_data(target_records: int = TARGET_RECORDS) -> list[dict[str, str | None]]:
    """
    Scrape GradCafe applicant records from multiple public survey pages.
    Resumes from existing applicant_data.json if present.
    """
    parser = _load_robot_parser()
    records = []

    print("Checking recent GradCafe records starting from page 1.")

    # GradCafe currently shows 20 records per page.
    page = 1

    while len(records) < target_records:
        page_url = _build_survey_url(page=page)

        if not _can_fetch(page_url, parser):
            print(f"Stopping because robots.txt does not allow this URL: {page_url}")
            break

        print(f"\nFetching page {page}: {page_url}")

        html = _fetch_html_with_urllib(page_url)

        if html is None:
            print("Stopping because no HTML was fetched.")
            break

        page_records = _parse_records_from_html(html, page_url)

        if not page_records:
            print("Stopping because no records were found on this page.")
            break

        records.extend(page_records)

        print(f"Found {len(page_records)} records on page {page}.")
        print(f"Total records collected: {len(records)}")

        save_data(records)
        print(f"Checkpoint saved with {len(records)} records.")

        page += 1

        if len(records) < target_records:
            _polite_delay()

    return records[:target_records]

def save_data(data: list[dict[str, str | None]], path: Path = OUTPUT_PATH) -> None:
    """
    Save applicant records to a JSON file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_data(path: Path = OUTPUT_PATH) -> list[dict[str, str | None]]:
    """
    Load applicant records from a JSON file.
    """
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)

def _load_existing_records(path: Path = OUTPUT_PATH) -> list[dict[str, str | None]]:
    """
    Load existing records if applicant_data.json already exists.
    Otherwise return an empty list.
    """
    if not path.exists():
        return []

    return load_data(path)

def main() -> None:
    """
    Run a small multi-page scrape test and save the records to applicant_data.json.
    """
    records = scrape_data(target_records=TARGET_RECORDS)

    save_data(records)

    loaded_records = load_data()

    print(f"\nSaved and loaded {len(loaded_records)} records from {OUTPUT_PATH}.")

def record_watermark(record: dict[str, Any]) -> str:
    """Return a stable fingerprint for one scraped applicant record."""
    fields = {
        "university_raw": record.get("university_raw"),
        "program_name_raw": record.get("program_name_raw"),
        "date_added": record.get("date_added"),
        "applicant_status": record.get("applicant_status"),
        "degree": record.get("degree"),
    }

    serialized = json.dumps(
        fields,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def records_after_watermark(
    records: list[dict[str, Any]],
    last_seen: str | None,
) -> list[dict[str, Any]]:
    """Return records encountered before the previous newest record."""
    if last_seen is None:
        return records

    new_records = []

    for record in records:
        if record_watermark(record) == last_seen:
            break

        new_records.append(record)

    return new_records


def run_incremental_scrape(
    connection: Any,
    payload: dict[str, Any],
    *,
    scraper: Callable[..., list[dict[str, Any]]] = scrape_data,
) -> dict[str, int]:
    """Scrape and insert records using a transaction-owned connection."""
    requested_target = payload.get("target_records", TARGET_RECORDS)

    try:
        target_records = int(requested_target)
    except (TypeError, ValueError):
        target_records = TARGET_RECORDS

    target_records = max(1, min(target_records, 100))

    records = scraper(target_records=target_records)
    previous_watermark = get_watermark(connection, "gradcafe")
    new_records = records_after_watermark(records, previous_watermark)

    inserted = insert_applicants_with_connection(
        connection,
        new_records,
    )

    if records:
        update_watermark(
            connection,
            "gradcafe",
            record_watermark(records[0]),
        )

    return {
        "pulled": len(records),
        "new": len(new_records),
        "inserted": inserted,
    }

if __name__ == "__main__":
    main()
