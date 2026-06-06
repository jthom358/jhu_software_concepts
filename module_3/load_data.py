# load_data.py
# This file loads the cleaned GradCafe applicant data from Module 2
# into a PostgreSQL table called applicants.

import json
import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv


# Load database login information from module_3/.env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def clean_float(value):
    """Convert GPA values to floats when possible."""
    if value is None or value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def clean_gre(value, lowest, highest):
    """Convert GRE values to floats and remove obvious bad values."""
    score = clean_float(value)

    if score is None:
        return None

    if score < lowest or score > highest:
        return None

    return score


def clean_date(date_string):
    """Convert dates like 'May 29, 2026' into YYYY-MM-DD format."""
    if date_string is None or date_string == "":
        return None

    try:
        return datetime.strptime(date_string, "%b %d, %Y").date()
    except ValueError:
        return None


# Connect to the local PostgreSQL database
conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)

cur = conn.cursor()

# Recreate the applicants table so the script starts fresh each time.
# This matches the table structure required in the assignment.
cur.execute("""
    DROP TABLE IF EXISTS applicants;

    CREATE TABLE applicants (
        p_id INTEGER PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        gpa FLOAT,
        gre FLOAT,
        gre_v FLOAT,
        gre_aw FLOAT,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
""")

# Open the cleaned GradCafe data from Module 2
data_file = os.path.join(BASE_DIR, "data", "llm_extend_applicant_data.json")

with open(data_file, "r", encoding="utf-8") as file:
    applicants = json.load(file)

# Insert each applicant record into the PostgreSQL table
for i, applicant in enumerate(applicants, start=1):
    term = None
    if applicant.get("start_term") and applicant.get("start_year"):
        term = applicant.get("start_term") + " " + applicant.get("start_year")

    cur.execute("""
        INSERT INTO applicants (
            p_id,
            program,
            comments,
            date_added,
            url,
            status,
            term,
            us_or_international,
            gpa,
            gre,
            gre_v,
            gre_aw,
            degree,
            llm_generated_program,
            llm_generated_university
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        i,
        applicant.get("program"),
        applicant.get("comments"),
        clean_date(applicant.get("date_added")),
        applicant.get("entry_url"),
        applicant.get("applicant_status"),
        term,
        applicant.get("student_type"),
        clean_float(applicant.get("gpa")),
        clean_gre(applicant.get("gre_score"), 130, 170),
        clean_gre(applicant.get("gre_v_score"), 130, 170),
        clean_gre(applicant.get("gre_aw"), 0, 6),
        applicant.get("degree"),
        applicant.get("llm-generated-program"),
        applicant.get("llm-generated-university"),
    ))

conn.commit()

print(f"Loaded {len(applicants)} applicant records into the applicants table.")

cur.close()
conn.close()