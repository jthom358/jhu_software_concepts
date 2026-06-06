# query_data.py
# This file runs SQL queries on the GradCafe applicants table

import os

import psycopg
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Load local database settings from the private .env file.
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_connection():
    return psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def run_query(cur, question, sql):
    """Run one SQL query and return the answer."""
    cur.execute(sql)
    answer = cur.fetchone()[0]

    return {
        "question": question,
        "answer": answer,
        "sql": sql.strip()
    }

# Each query below answers one assignment question
# ILIKE is used for flexible text matching because GradCafe fields are messy
def get_analysis_results():
    """Run all required assignment queries."""
    results = []

    with get_connection() as conn:
        with conn.cursor() as cur:

            results.append(run_query(
                cur,
                "1. How many entries are in the database for Fall 2026?",
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026';
                """
            ))

            results.append(run_query(
                cur,
                "2. What percentage of entries are from international students, excluding American and Other?",
                """
                SELECT ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE us_or_international NOT ILIKE 'American'
                          AND us_or_international NOT ILIKE 'Other'
                          AND us_or_international IS NOT NULL
                    ) / COUNT(*),
                    2
                )
                FROM applicants;
                """
            ))

            results.append(run_query(
                cur,
                "3. What is the average GPA of applicants who provided GPA?",
                """
                SELECT ROUND(AVG(gpa)::numeric, 2)
                FROM applicants
                WHERE gpa IS NOT NULL;
                """
            ))

            results.append(run_query(
                cur,
                "3. What is the average GRE Quant score of applicants who provided it?",
                """
                SELECT ROUND(AVG(gre)::numeric, 2)
                FROM applicants
                WHERE gre IS NOT NULL;
                """
            ))

            results.append(run_query(
                cur,
                "3. What is the average GRE Verbal score of applicants who provided it?",
                """
                SELECT ROUND(AVG(gre_v)::numeric, 2)
                FROM applicants
                WHERE gre_v IS NOT NULL;
                """
            ))

            results.append(run_query(
                cur,
                "3. What is the average GRE Analytical Writing score of applicants who provided it?",
                """
                SELECT ROUND(AVG(gre_aw)::numeric, 2)
                FROM applicants
                WHERE gre_aw IS NOT NULL;
                """
            ))

            results.append(run_query(
                cur,
                "4. What is the average GPA of American students in Fall 2026?",
                """
                SELECT ROUND(AVG(gpa)::numeric, 2)
                FROM applicants
                WHERE term = 'Fall 2026'
                  AND us_or_international ILIKE 'American'
                  AND gpa IS NOT NULL;
                """
            ))

            results.append(run_query(
                cur,
                "5. What percent of Fall 2026 entries are acceptances?",
                """
                SELECT ROUND(
                    100.0 * COUNT(*) FILTER (WHERE status ILIKE '%accept%') / COUNT(*),
                    2
                )
                FROM applicants
                WHERE term = 'Fall 2026';
                """
            ))

            results.append(run_query(
                cur,
                "6. What is the average GPA of Fall 2026 applicants who were accepted?",
                """
                SELECT ROUND(AVG(gpa)::numeric, 2)
                FROM applicants
                WHERE term = 'Fall 2026'
                  AND status ILIKE '%accept%'
                  AND gpa IS NOT NULL;
                """
            ))

            results.append(run_query(
                cur,
                "7. How many entries are JHU master's applicants in Computer Science?",
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE degree ILIKE '%master%'
                  AND program ILIKE '%computer science%'
                  AND (
                      program ILIKE '%johns hopkins%'
                      OR program ILIKE '%jhu%'
                  );
                """
            ))

            results.append(run_query(
                cur,
                "8. How many 2026 acceptances are for Georgetown, MIT, Stanford, or CMU PhD Computer Science using downloaded fields?",
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term ILIKE '%2026%'
                  AND status ILIKE '%accept%'
                  AND degree ILIKE '%phd%'
                  AND program ILIKE '%computer science%'
                  AND (
                      program ILIKE '%georgetown%'
                      OR program ILIKE '%mit%'
                      OR program ILIKE '%massachusetts institute of technology%'
                      OR program ILIKE '%stanford%'
                      OR program ILIKE '%carnegie mellon%'
                      OR program ILIKE '%cmu%'
                  );
                """
            ))

            results.append(run_query(
                cur,
                "9. Does the number change using LLM generated university and program fields?",
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term ILIKE '%2026%'
                  AND status ILIKE '%accept%'
                  AND degree ILIKE '%phd%'
                  AND llm_generated_program ILIKE '%computer science%'
                  AND (
                      llm_generated_university ILIKE '%georgetown%'
                      OR llm_generated_university ILIKE '%mit%'
                      OR llm_generated_university ILIKE '%massachusetts institute of technology%'
                      OR llm_generated_university ILIKE '%stanford%'
                      OR llm_generated_university ILIKE '%carnegie mellon%'
                      OR llm_generated_university ILIKE '%cmu%'
                  );
                """
            ))

            results.append(run_query(
                cur,
                "10. My question: What is the average GPA for PhD applicants?",
                """
                SELECT ROUND(AVG(gpa)::numeric, 2)
                FROM applicants
                WHERE degree ILIKE '%phd%'
                  AND gpa IS NOT NULL;
                """
            ))

            results.append(run_query(
                cur,
                "11. My question: How many Fall 2026 entries are waitlisted?",
                """
                SELECT COUNT(*)
                FROM applicants
                WHERE term = 'Fall 2026'
                  AND status ILIKE '%wait%';
                """
            ))

    return results


if __name__ == "__main__":
    results = get_analysis_results()

    for item in results:
        print(item["question"])
        print("Answer:", item["answer"])
        print()