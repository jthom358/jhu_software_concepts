"""""
Module 2 GradCafe scraper

This file contains the scraping logic for collecting public
 GradCafe graduate admissions applicant data and saving it to applicant_data.json

 Current version:
 -Defines constants
 -Builds GradCafe URLs with urllib
 -checks robots.txt with urllib.robotparser
 """

import json
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

BASE_URL = "https://www.thegradcafe.com"
SURVEY_PATH = "/survey/"
ROBOTS_URL = urljoin(BASE_URL, "/robots.txt")

OUTPUT_PATH = Path("applicant_data.json")

USER_AGENT = "jhu-software-concepts-student-scraper/1.0"

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

def _fetch_html_with_urllib(url: str) -> str | None:
    """
    Fetch a public GradCafe page using urllib.request.

    Returns the HTML as a string if the request succeeds.
    Returns None if the request fails, is blocked, or is rate limited
    """
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )

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

    except URLError as error:
        print(f"URL error while fetching {url}: {error}")
        return None
    
def _inspect_html_for_applicant_text(html: str) -> None:
    """
    Use BeautifulSoup to inspect whether the fetched HTML appears to contain
    applicant result information
    """
    soup = BeautifulSoup(html, "lxml")
    page_text = soup.get_text(" ", strip=True)

    search_terms = ["Accepted", "Rejected", "Waitlisted", "GPA", "GRE", "PhD", "Masters"]

    print("\nHTML inspection:")
    print(f"Total visible text length: {len(page_text)} characters")

    for term in search_terms:
        count = page_text.count(term)
        print(f"Occurrences of '{term}': {count}")

    print("\nSample text around applicant-related terms:")

    for term in search_terms:
        index = page_text.find(term)

        if index != -1:
            start = max(index - 150, 0)
            end = min(index + 350, len(page_text))
            snippet = page_text[start:end]
            print(f"\n--- Around '{term}' ---")
            print(snippet)
            break

def _inspect_possible_result_blocks(html: str) -> None:
    """
    Print likely applicant result blocks so we can understand the page structure
    before writing the parser.
    """
    soup = BeautifulSoup(html, "lxml")

    possible_blocks = soup.find_all(["div", "tr", "article", "li"])

    print("\nPossible applicant result blocks:")

    count = 0

    for block in possible_blocks:
        text = block.get_text(" ", strip=True)

        if not text:
            continue

        lower_text = text.lower()

        # Skip search/filter panel text.
        if "select a degree type" in lower_text or "apply filters" in lower_text:
            continue

        has_decision = (
            "accepted on" in lower_text
            or "rejected on" in lower_text
            or "wait listed on" in lower_text
            or "waitlisted on" in lower_text
            or "interview" in lower_text
        )

        has_degree = (
            " phd " in f" {lower_text} "
            or " masters " in f" {lower_text} "
            or " psyd " in f" {lower_text} "
            or " edd " in f" {lower_text} "
            or " mba " in f" {lower_text} "
            or " mfa " in f" {lower_text} "
            or " jd " in f" {lower_text} "
        )

        has_date = re.search(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2}\b",
            text,
        )

        reasonable_length = 40 <= len(text) <= 800

        if has_decision and has_degree and has_date and reasonable_length:
            count += 1
            print(f"\n--- Possible block {count} ---")
            print(f"Tag: {block.name}")
            print(f"Class: {block.get('class')}")
            print(f"Text: {text[:1000]}")

        if count >= 10:
            break

    print(f"\nPrinted {count} possible result blocks.")

def _inspect_table_cells(html: str) -> None:
    """
    Print the individual cells from likely applicant table rows.
    This helps us understand whether the row data is already separated by <td> tags.
    """
    soup = BeautifulSoup(html, "lxml")
    rows = soup.find_all("tr")

    print("\nInspecting table cells from applicant rows:")

    printed_count = 0

    for row in rows:
        cells = row.find_all(["td", "th"])

        if not cells:
            continue

        cell_texts = [cell.get_text(" ", strip=True) for cell in cells]
        row_text = " ".join(cell_texts)
        lower_text = row_text.lower()

        # Skip table headers or filter-related rows.
        if "select a degree type" in lower_text or "apply filters" in lower_text:
            continue

        has_decision = (
            "accepted on" in lower_text
            or "rejected on" in lower_text
            or "wait listed on" in lower_text
            or "waitlisted on" in lower_text
            or "interview" in lower_text
        )

        if not has_decision:
            continue

        printed_count += 1
        print(f"\n--- Row {printed_count} ---")

        for index, text in enumerate(cell_texts):
            print(f"Cell {index}: {text}")

        if printed_count >= 5:
            break

    print(f"\nPrinted {printed_count} applicant rows with cells.")

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

def _is_main_applicant_row(cells: list[str]) -> bool:
    """
    Check whether a row looks like the main applicant row.
    """
    if len(cells) < 4:
        return False

    date_pattern = r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2}\b"
    has_added_date = re.search(date_pattern, cells[2]) is not None
    has_decision = " on " in cells[3].lower()

    return has_added_date and has_decision

def _parse_records_from_html(html: str, page_url: str) -> list[dict[str, str | None]]:
    """
    Parse all applicant records from one GradCafe results page.
    """
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

        university = cells[0]
        program_name, degree = _split_program_and_degree(cells[1])
        date_added = cells[2]
        status, decision_date = _parse_decision(cells[3])
        comments = cells[4] if len(cells) > 4 else None

        detail_text = ""

        if index + 1 < len(rows):
            next_cells = [
                _clean_text(cell.get_text(" ", strip=True))
                for cell in rows[index + 1].find_all("td")
            ]

            if len(next_cells) == 1:
                detail_text = next_cells[0]

        start_term, start_year = _extract_start_term_and_year(detail_text)
        student_type = _extract_student_type(detail_text)
        gpa = _extract_gpa(detail_text)

        record = {
            "university_raw": university,
            "program_name_raw": program_name,
            "degree": degree,
            "date_added": date_added,
            "entry_url": page_url,
            "applicant_status": status,
            "acceptance_date": decision_date if status == "Accepted" else None,
            "rejection_date": decision_date if status == "Rejected" else None,
            "start_term": start_term,
            "start_year": start_year,
            "student_type": student_type,
            "gre_score": None,
            "gre_v_score": None,
            "gre_aw": None,
            "gpa": gpa,
            "comments": comments,
            "raw_listing_text": _clean_text(" ".join(cells + [detail_text])),
        }

        records.append(record)
        index += 1

    return records
def save_data(data: list[dict[str, str | None]], path: Path = OUTPUT_PATH) -> None:
    """
    Save applicant records to a JSON file.
    """
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_data(path: Path = OUTPUT_PATH) -> list[dict[str, str | None]]:
    """
    Load applicant records from a JSON file.
    """
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
    
def main() -> None:
    """
    Small test to confirm that URL building, robots.txt checking,
    and one safe urllib page request work
    """
    parser = _load_robot_parser()

    test_url = _build_survey_url(page=1)

    print(f"Robots URL: {ROBOTS_URL}")
    print(f"Test survey URL: {test_url}")
    print(f"Allowed by robots.txt: {_can_fetch(test_url, parser)}")

    if not _can_fetch(test_url, parser):
        print("Stopping because robots.txt does not allow this URL.")
        return

    html = _fetch_html_with_urllib(test_url)

    if html is None:
        print("No HTML was fetched.")
        return

    print(f"Fetched HTML length: {len(html)} characters")
    print("First 500 characters:")
    print(html[:500])

    _inspect_html_for_applicant_text(html)
    _inspect_possible_result_blocks(html)
    _inspect_table_cells(html)

    page_records = _parse_records_from_html(html, test_url)

    print(f"\nParsed {len(page_records)} records from this page.")

    print("\nFirst 5 parsed records:")
    for record in page_records[:5]:
        print(record)
    
    save_data(page_records)

    loaded_records = load_data()

    print(f"\nSaved and loaded {len(loaded_records)} records from {OUTPUT_PATH}.")

if __name__ == "__main__":
    main()