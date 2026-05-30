"""""
Module 2 GradCafe scraper

This file contains the scraping logic for collecting public
 GradCafe graduate admissions applicant data and saving it to applicant_data.json

 Current version:
 -Defines constants
 -Builds GradCafe URLs with urllib
 -checks robots.txt with urllib.robotparser
 """

from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin
from urllib.robotparser import RobotFileParser

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
    A complete GradCafe survey URL.
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
    Load and parse GradCafe robots.txt using urllib.robotparser.
    """
    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.read()
    return parser


def _can_fetch(url: str, parser: RobotFileParser) -> bool:
    """
    Check whether robots.txt permits this scraper to fetch the provided URL.
    """
    return parser.can_fetch(USER_AGENT, url)


def main() -> None:
    """
    Small test to confirm that URL building and robots.txt checking work.
    """
    parser = _load_robot_parser()

    test_url = _build_survey_url(page=1)

    print(f"Robots URL: {ROBOTS_URL}")
    print(f"Test survey URL: {test_url}")
    print(f"Allowed by robots.txt: {_can_fetch(test_url, parser)}")


if __name__ == "__main__":
    main()