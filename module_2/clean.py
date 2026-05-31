"""
Module 2 GradCafe data cleaner.

This script prepares scraped GradCafe applicant data for the local LLM
standardization tool provided in module_2/llm_hosting.
"""

import html
import json
import re
from pathlib import Path


INPUT_PATH = Path("applicant_data.json")
OUTPUT_PATH = Path("cleaned_applicant_data.json")


def load_data(path: Path = INPUT_PATH) -> list[dict]:
    """
    Load applicant records from a JSON file.
    """
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _clean_text(value):
    """
    Remove HTML entities and normalize whitespace.
    """
    if value is None:
        return None

    value = html.unescape(str(value))
    value = re.sub(r"\s+", " ", value).strip()

    return value


def _make_llm_program_field(record: dict) -> str:
    """
    Create the 'program' field expected by the provided LLM standardizer.

    The LLM app expects one combined field that may contain both the program
    and university name.
    """
    program = record.get("program_name_raw") or ""
    university = record.get("university_raw") or ""

    if program and university:
        return f"{program}, {university}"

    if program:
        return program

    if university:
        return university

    return ""


def clean_data(records: list[dict]) -> list[dict]:
    """
    Clean text fields and add the LLM-compatible 'program' field.
    """
    cleaned_records = []

    for record in records:
        cleaned_record = {}

        for key, value in record.items():
            if isinstance(value, str):
                cleaned_record[key] = _clean_text(value)
            else:
                cleaned_record[key] = value

        cleaned_record["program"] = _make_llm_program_field(cleaned_record)

        cleaned_records.append(cleaned_record)

    return cleaned_records


def save_data(data: list[dict], path: Path = OUTPUT_PATH) -> None:
    """
    Save cleaned applicant records to a JSON file.
    """
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def main() -> None:
    """
    Load applicant_data.json, prepare rows for the local LLM, and save output.
    """
    records = load_data()
    cleaned_records = clean_data(records)
    save_data(cleaned_records)

    print(f"Prepared {len(cleaned_records)} records for LLM cleaning.")
    print(f"Saved cleaned records to {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()