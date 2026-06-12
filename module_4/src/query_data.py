"""SQL analysis queries for the GradCafe applicants table."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .db_utils import connect

EXPECTED_RESULT_KEYS = {"question", "answer", "sql"}


def run_query(cur: Any, question: str, sql: str, *, percentage: bool = False) -> dict[str, str]:
    """Run one SQL query and return a template-ready result dictionary."""
    cur.execute(sql)
    value = cur.fetchone()[0]
    return {"question": question, "answer": format_answer(value, percentage=percentage), "sql": sql.strip()}


def format_answer(value: Any, *, percentage: bool = False) -> str:
    """Format SQL answers, forcing percentages to use exactly two decimals."""
    if value is None:
        return "N/A"
    if percentage:
        return f"{float(value):.2f}%"
    if isinstance(value, (float, Decimal)):
        return f"{float(value):.2f}"
    return str(value)


def get_analysis_results(database_url: str | None = None) -> list[dict[str, str]]:
    """Run the Module 3 analysis queries and return results for the Flask template."""
    results: list[dict[str, str]] = []

    with connect(database_url) as conn:
        with conn.cursor() as cur:
            results.append(run_query(cur, "1. How many entries are in the database for Fall 2026?", """
                SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026';
            """))
            results.append(run_query(cur, "2. What percentage of entries are from international students, excluding American and Other?", """
                SELECT ROUND(100.0 * COUNT(*) FILTER (
                    WHERE us_or_international NOT ILIKE 'American'
                      AND us_or_international NOT ILIKE 'Other'
                      AND us_or_international IS NOT NULL
                ) / NULLIF(COUNT(*), 0), 2) FROM applicants;
            """, percentage=True))
            results.append(run_query(cur, "3. What is the average GPA of applicants who provided GPA?", """
                SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants WHERE gpa IS NOT NULL;
            """))
            results.append(run_query(cur, "3. What is the average GRE Quant score of applicants who provided it?", """
                SELECT ROUND(AVG(gre)::numeric, 2) FROM applicants WHERE gre IS NOT NULL;
            """))
            results.append(run_query(cur, "3. What is the average GRE Verbal score of applicants who provided it?", """
                SELECT ROUND(AVG(gre_v)::numeric, 2) FROM applicants WHERE gre_v IS NOT NULL;
            """))
            results.append(run_query(cur, "3. What is the average GRE Analytical Writing score of applicants who provided it?", """
                SELECT ROUND(AVG(gre_aw)::numeric, 2) FROM applicants WHERE gre_aw IS NOT NULL;
            """))
            results.append(run_query(cur, "4. What is the average GPA of American students in Fall 2026?", """
                SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants
                WHERE term = 'Fall 2026' AND us_or_international ILIKE 'American' AND gpa IS NOT NULL;
            """))
            results.append(run_query(cur, "5. What percent of Fall 2026 entries are acceptances?", """
                SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE status ILIKE '%accept%') / NULLIF(COUNT(*), 0), 2)
                FROM applicants WHERE term = 'Fall 2026';
            """, percentage=True))
            results.append(run_query(cur, "6. What is the average GPA of Fall 2026 applicants who were accepted?", """
                SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants
                WHERE term = 'Fall 2026' AND status ILIKE '%accept%' AND gpa IS NOT NULL;
            """))
            results.append(run_query(cur, "7. How many entries are JHU master's applicants in Computer Science?", """
                SELECT COUNT(*) FROM applicants
                WHERE degree ILIKE '%master%' AND program ILIKE '%computer science%'
                  AND (program ILIKE '%johns hopkins%' OR program ILIKE '%jhu%');
            """))
            results.append(run_query(cur, "8. How many 2026 acceptances are for Georgetown, MIT, Stanford, or CMU PhD Computer Science using downloaded fields?", """
                SELECT COUNT(*) FROM applicants
                WHERE term ILIKE '%2026%' AND status ILIKE '%accept%' AND degree ILIKE '%phd%'
                  AND program ILIKE '%computer science%'
                  AND (program ILIKE '%georgetown%' OR program ILIKE '%mit%'
                       OR program ILIKE '%massachusetts institute of technology%'
                       OR program ILIKE '%stanford%' OR program ILIKE '%carnegie mellon%' OR program ILIKE '%cmu%');
            """))
            results.append(run_query(cur, "9. Does the number change using LLM generated university and program fields?", """
                SELECT COUNT(*) FROM applicants
                WHERE term ILIKE '%2026%' AND status ILIKE '%accept%' AND degree ILIKE '%phd%'
                  AND llm_generated_program ILIKE '%computer science%'
                  AND (llm_generated_university ILIKE '%georgetown%' OR llm_generated_university ILIKE '%mit%'
                       OR llm_generated_university ILIKE '%massachusetts institute of technology%'
                       OR llm_generated_university ILIKE '%stanford%'
                       OR llm_generated_university ILIKE '%carnegie mellon%' OR llm_generated_university ILIKE '%cmu%');
            """))
            results.append(run_query(cur, "10. My question: What is the average GPA for PhD applicants?", """
                SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants WHERE degree ILIKE '%phd%' AND gpa IS NOT NULL;
            """))
            results.append(run_query(cur, "11. My question: How many Fall 2026 entries are waitlisted?", """
                SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026' AND status ILIKE '%wait%';
            """))

    return results


def get_expected_keys() -> set[str]:
    """Return the keys every analysis result dictionary should contain."""
    return EXPECTED_RESULT_KEYS


if __name__ == "__main__":
    for item in get_analysis_results():
        print(item["question"])
        print("Answer:", item["answer"])
        print()
