"""""
Module 2 GradCafe scraper

This file contains the scraping logic for collecting public
 GradCafe graduate admissions applicant data and saving it to applicant_data.json

 Current version:
 -Defines constants
 -Builds GradCafe URLs with urllib
 -checks robots.txt with urllib.robotparser
 """

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

if __name__ == "__main__":
    main()