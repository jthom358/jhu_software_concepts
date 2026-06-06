# pull_data.py
# This file supports the "Pull Data" button in the Flask app
# It reuses the copied Module 2 scraper to collect recent GradCafe records,
# checks which records are already in the PostgreSQL database, and inserts
# only records that appear to be new

import os
from datetime import datetime

import psycopg
from dotenv import load_dotenv

# scrape.py was copied from Module 2 into Module 3
# This import lets us reuse the same scraping function
from scrape import scrape_data


# Find the module_3 folder and load the private database settings.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def clean_float(value):
    """
    Convert GPA or score values into floats
    Missing or badly formatted values are stored as NULL in PostgreSQL
    """
    if value is None or value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def clean_gre(value, lowest, highest):
    """
    Convert GRE values and remove obvious invalid scores

    GRE Quant and Verbal should be between 130 and 170
    GRE Analytical Writing should be between 0 and 6
    """
    score = clean_float(value)

    if score is None:
        return None

    if score < lowest or score > highest:
        return None

    return score


def clean_date(date_string):
    """
    Convert GradCafe date strings like 'May 29, 2026'
    into a date format PostgreSQL can store
    """
    if date_string is None or date_string == "":
        return None

    try:
        return datetime.strptime(date_string, "%b %d, %Y").date()
    except ValueError:
        return None


def main():
    # Connect to the local PostgreSQL database created for this assignment
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )

    cur = conn.cursor()

    # Pull a small batch of recent GradCafe records.
    # This keeps the web button from launching a very long scrape
    records = scrape_data(target_records=25)

    # New records need new primary keys, so start after the current largest p_id
    cur.execute("SELECT COALESCE(MAX(p_id), 0) FROM applicants;")
    next_id = cur.fetchone()[0] + 1

    inserted = 0

    for applicant in records:
        # The database stores term as one field, such as "Fall 2026"
        term = None
        if applicant.get("start_term") and applicant.get("start_year"):
            term = applicant.get("start_term") + " " + applicant.get("start_year")

        date_added = clean_date(applicant.get("date_added"))

        program_name = applicant.get("program_name_raw")
        university = applicant.get("university_raw")

        if program_name and university:
            program = program_name + ", " + university
        elif program_name:
            program = program_name
        elif university:
            program = university
        else:
            program = None
        
        if program is None:
            print("Skipping record because no program or university was found.")
            continue

        # Check for a likely duplicate before inserting
        # GradCafe does not provide a clean unique ID, so this uses several
        # fields together to identify records that are probably already stored
        cur.execute("""
            SELECT COUNT(*)
            FROM applicants
            WHERE program = %s
              AND date_added = %s
              AND status = %s
              AND degree = %s;
        """, (
            program,
            date_added,
            applicant.get("applicant_status"),
            applicant.get("degree"),
        ))

        already_exists = cur.fetchone()[0] > 0

        if already_exists:
            continue

        # Insert the new applicant record into the same applicants table
        # used by load_data.py and query_data.py
        # For newly pulled data, the raw parsed program/university fields are
        # used as fallback values for the LLM-generated columns
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
            next_id,
            program,
            applicant.get("comments"),
            date_added,
            applicant.get("entry_url"),
            applicant.get("applicant_status"),
            term,
            applicant.get("student_type"),
            clean_float(applicant.get("gpa")),
            clean_gre(applicant.get("gre_score"), 130, 170),
            clean_gre(applicant.get("gre_v_score"), 130, 170),
            clean_gre(applicant.get("gre_aw"), 0, 6),
            applicant.get("degree"),
            applicant.get("program_name_raw"),
            applicant.get("university_raw"),
        ))

        next_id += 1
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"Pulled {len(records)} recent records.")
    print(f"Inserted {inserted} new records into the database.")


if __name__ == "__main__":
    lock_file = os.path.join(BASE_DIR, "scrape.lock")

    try:
        main()
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)