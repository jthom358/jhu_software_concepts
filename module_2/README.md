# Module 2: GradCafe Web Scraping Assignment

## Name

Jonah Thomas
JHED ID: 21FC7C

## Module Info

Module 2
Assignment: GradCafe Web Scraping and Data Cleaning
Due Date: 5/31/26

## Overview

This project scrapes publicly available GradCafe graduate admissions applicant data, stores the scraped records in `applicant_data.json`, prepares the scraped data for local LLM standardization in `cleaned_applicant_data.json`, and includes LLM-standardized output in `llm_extend_applicant_data.json`.

The final scraped dataset contains 30,000 GradCafe applicant records.

## Repository Structure

```text
module_2/
├── scrape.py
├── clean.py
├── applicant_data.json
├── cleaned_applicant_data.json
├── llm_extend_applicant_data.json
├── llm_extend_applicant_data.jsonl
├── llm_extend_applicant_data_utf8.jsonl
├── cleaned_remaining.json
├── screenshot.jpg
├── README.md
├── requirements.txt
└── llm_hosting/
    ├── app.py
    ├── requirements.txt
    ├── README.md
    ├── sample_data.json
    ├── canon_programs.txt
    └── canon_universities.txt
```

Some intermediate JSONL/checkpoint files are included because the local LLM standardization step was long-running and checkpointed incrementally.

## Approach

I built the project as a reproducible scraping and cleaning pipeline.

First, I checked GradCafe's `robots.txt` manually in the browser and saved evidence as `screenshot.jpg`. I also implemented a programmatic `robots.txt` check in `scrape.py` using Python's `urllib.robotparser`.

The scraper uses `urllib.parse` to build paginated GradCafe survey URLs and `urllib.request` to request public survey result pages. After confirming that the public applicant rows were present in the returned HTML, I used BeautifulSoup to parse the table rows. I then used Python string methods and regular expressions to extract and normalize fields from the table cells and the associated detail rows.

Each applicant record is stored as a dictionary with descriptive keys. The scraper preserves the original raw applicant listing text for traceability and reproducibility.

The final scraper also includes checkpointing. After each page is scraped, the current records are saved to `applicant_data.json`. If the scrape is interrupted by a temporary network issue, the script can resume based on the number of records already saved.

## robots.txt Compliance

Before scraping GradCafe, I manually checked:

```text
https://www.thegradcafe.com/robots.txt
```

A screenshot of this check is included in `module_2` as `screenshot.jpg`.

The `robots.txt` file allowed general public access under `User-agent: *` while disallowing private/account-related paths such as:

```text
/signin
/register
/forgot-password
/reset-password
/confirm-password
/verify-email
/profile
```

My scraper avoids those disallowed paths and only requests publicly accessible GradCafe survey pages.

The scraper also checks `robots.txt` programmatically before requesting GradCafe URLs. It uses polite randomized delays between page requests and stops if the site blocks, rate-limits, rejects a request, or returns no usable HTML.

## Selenium Note

The assignment recommended Selenium when applicant results are dynamically rendered, paginated, or difficult to access through static `urllib` requests alone.

I first attempted a static `urllib` workflow because the assignment required `urllib` for URL construction, inspection, and page requests. The fetched GradCafe survey HTML contained the public applicant table rows directly, and BeautifulSoup was able to parse the rows and cells from the `urllib` response. Because the applicant data was accessible through static HTML, Selenium was not required for the final scraping workflow.

The final workflow uses:

```text
urllib → BeautifulSoup → regex/string parsing → JSON output
```

Selenium is included in `requirements.txt` as a possible fallback dependency, but the submitted scraper did not need browser rendering.

## Scraped Fields

The scraped records include the following fields when available:

```text
university_raw
program_name_raw
degree
date_added
entry_url
applicant_status
acceptance_date
rejection_date
start_term
start_year
student_type
gre_score
gre_v_score
gre_aw
gpa
comments
raw_listing_text
```

The `raw_listing_text` field preserves the original scraped row/detail text so that parsing choices can be audited later.

Missing or unavailable values are represented consistently as `None` / `null`.

## Scraping Details

The scraper handles pagination by building URLs such as:

```text
https://www.thegradcafe.com/survey/
https://www.thegradcafe.com/survey/?page=2
https://www.thegradcafe.com/survey/?page=3
```

Each GradCafe survey page returned 20 applicant records. The final submitted `applicant_data.json` contains 30,000 records.

The scraper includes helper functions for:

```text
URL construction
robots.txt checking
HTML fetching
polite delays
text normalization
program/degree splitting
decision parsing
term/year extraction
student type extraction
GPA/GRE extraction
record parsing
JSON save/load
checkpoint/resume behavior
```

## Data Cleaning

The `clean.py` script loads `applicant_data.json`, normalizes whitespace and HTML entities, preserves the original scraped fields, and creates a combined `program` field in the format expected by the provided local LLM standardizer.

Example:

```text
program_name_raw: Public Policy
university_raw: University of Massachusetts
program: Public Policy, University of Massachusetts
```

The cleaned output is saved as:

```text
cleaned_applicant_data.json
```

This file contains the full 30,000 cleaned pre-LLM records.

## Local LLM Standardization

The provided local LLM files are included under:

```text
module_2/llm_hosting
```

I installed the provided LLM requirements and successfully ran the provided TinyLlama standardizer locally. The model downloaded through Hugging Face, and the standardizer worked on the provided `sample_data.json`.

The LLM app adds the following fields:

```text
llm-generated-program
llm-generated-university
```

I then prepared my scraped data for the LLM by using `clean.py` to create the combined `program` field expected by `llm_hosting/app.py`.

The full scraped dataset contains 30,000 records. The provided local LLM standardizer processes rows one at a time on CPU, so a complete 30,000-row LLM standardization pass was too slow to complete before the submission deadline. I began running the local LLM standardizer on the cleaned dataset and saved its incremental JSONL output. The final `llm_extend_applicant_data.json` file contains the LLM-standardized records completed before final submission.

The original full scraped dataset and full cleaned pre-LLM dataset are preserved in:

```text
applicant_data.json
cleaned_applicant_data.json
```

The LLM output can be extended by rerunning the provided app with the `--out` and `--append` options.

## Known LLM Cleaning Edge Cases

The LLM standardization output is not perfect. One systematic issue observed was fuzzy university matching. For example, a broad value such as `University of Massachusetts` may be mapped to a specific campus such as `University of Massachusetts Lowell`.

Because of this, the submitted files preserve the original scraped university/program fields alongside the LLM-generated fields. This makes the output auditable and allows future improvements to the canonical university/program lists.

## How to Run

Install the main project requirements from inside `module_2`:

```bash
pip install -r requirements.txt
```

Run the scraper:

```bash
python scrape.py
```

Run the cleaner:

```bash
python clean.py
```

Install the local LLM requirements:

```bash
cd llm_hosting
pip install -r requirements.txt
```

Test the provided LLM sample:

```bash
python app.py --file sample_data.json --out sample_out.jsonl
```

Run the local LLM standardizer on the cleaned applicant data:

```bash
python app.py --file ../cleaned_applicant_data.json --out ../llm_extend_applicant_data_utf8.jsonl
```

Resume/append a long-running LLM standardization job:

```bash
python app.py --file ../cleaned_remaining.json --out ../llm_extend_applicant_data_utf8.jsonl --append
```

Convert JSONL output to standard JSON:

```bash
python -c "import json; rows=[]; f=open('llm_extend_applicant_data_utf8.jsonl', encoding='utf-8'); [rows.append(json.loads(line)) for line in f if line.strip()]; json.dump(rows, open('llm_extend_applicant_data.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False); print(len(rows))"
```

## Known Bugs / Limitations

Some applicant rows do not include every optional field. Fields such as GRE, GRE V, GRE AW, GPA, and comments are only populated when visible in the scraped table/detail text.

Some comments appear only as a comment indicator such as `Total comments`, depending on what was exposed in the public table row.

The scraper stores the survey page URL as `entry_url`. If a more specific per-entry URL is not exposed in the parsed row, the page URL is preserved.

The local LLM standardization step was successfully run, but a complete 30,000-row LLM pass was limited by CPU runtime before the deadline. The submitted LLM output demonstrates the required local standardization workflow and can be extended by rerunning the included LLM app.

## Submission Notes

The GitHub repository is named:

```text
jhu_software_concepts
```

All assignment materials are placed under:

```text
module_2
```

The Canvas submission should include the zipped `module_2` folder and should match the final pushed GitHub version.
