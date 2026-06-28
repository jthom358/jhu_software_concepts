"""Secure SQL analysis queries for the GradCafe applicants table."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Sequence

from psycopg import sql

from src.db.db_utils import connect

EXPECTED_RESULT_KEYS = {"question", "answer", "sql"}
APPLICANTS_TABLE = "applicants"
DEFAULT_QUERY_LIMIT = 1
MAX_QUERY_LIMIT = 100


def clamp_limit(value: Any) -> int:
    """Return a query limit constrained to the allowed range."""
    try:
        requested_limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_QUERY_LIMIT

    return max(1, min(requested_limit, MAX_QUERY_LIMIT))


def build_statement(query_text: str) -> sql.Composed:
    """Build a safely composed SQL statement for the applicants table."""
    return sql.SQL(query_text).format(
        applicants=sql.Identifier(APPLICANTS_TABLE),
    )


def run_query(
    cur: Any,
    question: str,
    statement: sql.Composable,
    params: Sequence[Any] = (),
    *,
    percentage: bool = False,
) -> dict[str, str]:
    """Execute one parameterized SQL statement and format its result."""
    cur.execute(statement, params)
    row = cur.fetchone()
    value = row[0] if row else None

    return {
        "question": question,
        "answer": format_answer(value, percentage=percentage),
        "sql": statement.as_string(cur.connection).strip(),
    }


def format_answer(value: Any, *, percentage: bool = False) -> str:
    """Format SQL answers, forcing percentages to use two decimals."""
    if value is None:
        return "N/A"
    if percentage:
        return f"{float(value):.2f}%"
    if isinstance(value, (float, Decimal)):
        return f"{float(value):.2f}"
    return str(value)


def get_analysis_results(
    database_url: str | None = None,
    requested_limit: Any = DEFAULT_QUERY_LIMIT,
    *,
    connection: Any | None = None,
) -> list[dict[str, str]]:
    """Run the analysis queries using safe SQL and a bounded limit."""
    limit = clamp_limit(requested_limit)

    query_specs = [
        (
            "1. How many entries are in the database for Fall 2026?",
            """
            SELECT COUNT(*)
            FROM {applicants}
            WHERE term = %s
            LIMIT %s;
            """,
            ("Fall 2026", limit),
            False,
        ),
        (
            (
                "2. What percentage of entries are from international "
                "students, excluding American and Other?"
            ),
            """
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE us_or_international NOT ILIKE %s
                      AND us_or_international NOT ILIKE %s
                      AND us_or_international IS NOT NULL
                ) / NULLIF(COUNT(*), 0),
                2
            )
            FROM {applicants}
            LIMIT %s;
            """,
            ("American", "Other", limit),
            True,
        ),
        (
            "3. What is the average GPA of applicants who provided GPA?",
            """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM {applicants}
            WHERE gpa IS NOT NULL
            LIMIT %s;
            """,
            (limit,),
            False,
        ),
        (
            (
                "3. What is the average GRE Quant score of applicants "
                "who provided it?"
            ),
            """
            SELECT ROUND(AVG(gre)::numeric, 2)
            FROM {applicants}
            WHERE gre IS NOT NULL
            LIMIT %s;
            """,
            (limit,),
            False,
        ),
        (
            (
                "3. What is the average GRE Verbal score of applicants "
                "who provided it?"
            ),
            """
            SELECT ROUND(AVG(gre_v)::numeric, 2)
            FROM {applicants}
            WHERE gre_v IS NOT NULL
            LIMIT %s;
            """,
            (limit,),
            False,
        ),
        (
            (
                "3. What is the average GRE Analytical Writing score "
                "of applicants who provided it?"
            ),
            """
            SELECT ROUND(AVG(gre_aw)::numeric, 2)
            FROM {applicants}
            WHERE gre_aw IS NOT NULL
            LIMIT %s;
            """,
            (limit,),
            False,
        ),
        (
            "4. What is the average GPA of American students in Fall 2026?",
            """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM {applicants}
            WHERE term = %s
              AND us_or_international ILIKE %s
              AND gpa IS NOT NULL
            LIMIT %s;
            """,
            ("Fall 2026", "American", limit),
            False,
        ),
        (
            "5. What percent of Fall 2026 entries are acceptances?",
            """
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status ILIKE %s
                ) / NULLIF(COUNT(*), 0),
                2
            )
            FROM {applicants}
            WHERE term = %s
            LIMIT %s;
            """,
            ("%accept%", "Fall 2026", limit),
            True,
        ),
        (
            (
                "6. What is the average GPA of Fall 2026 applicants "
                "who were accepted?"
            ),
            """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM {applicants}
            WHERE term = %s
              AND status ILIKE %s
              AND gpa IS NOT NULL
            LIMIT %s;
            """,
            ("Fall 2026", "%accept%", limit),
            False,
        ),
        (
            (
                "7. How many entries are JHU master's applicants "
                "in Computer Science?"
            ),
            """
            SELECT COUNT(*)
            FROM {applicants}
            WHERE degree ILIKE %s
              AND program ILIKE %s
              AND (
                  program ILIKE %s
                  OR program ILIKE %s
              )
            LIMIT %s;
            """,
            (
                "%master%",
                "%computer science%",
                "%johns hopkins%",
                "%jhu%",
                limit,
            ),
            False,
        ),
        (
            (
                "8. How many 2026 acceptances are for Georgetown, MIT, "
                "Stanford, or CMU PhD Computer Science using downloaded fields?"
            ),
            """
            SELECT COUNT(*)
            FROM {applicants}
            WHERE term ILIKE %s
              AND status ILIKE %s
              AND degree ILIKE %s
              AND program ILIKE %s
              AND (
                  program ILIKE %s
                  OR program ILIKE %s
                  OR program ILIKE %s
                  OR program ILIKE %s
                  OR program ILIKE %s
                  OR program ILIKE %s
              )
            LIMIT %s;
            """,
            (
                "%2026%",
                "%accept%",
                "%phd%",
                "%computer science%",
                "%georgetown%",
                "%mit%",
                "%massachusetts institute of technology%",
                "%stanford%",
                "%carnegie mellon%",
                "%cmu%",
                limit,
            ),
            False,
        ),
        (
            (
                "9. Does the number change using LLM generated "
                "university and program fields?"
            ),
            """
            SELECT COUNT(*)
            FROM {applicants}
            WHERE term ILIKE %s
              AND status ILIKE %s
              AND degree ILIKE %s
              AND llm_generated_program ILIKE %s
              AND (
                  llm_generated_university ILIKE %s
                  OR llm_generated_university ILIKE %s
                  OR llm_generated_university ILIKE %s
                  OR llm_generated_university ILIKE %s
                  OR llm_generated_university ILIKE %s
                  OR llm_generated_university ILIKE %s
              )
            LIMIT %s;
            """,
            (
                "%2026%",
                "%accept%",
                "%phd%",
                "%computer science%",
                "%georgetown%",
                "%mit%",
                "%massachusetts institute of technology%",
                "%stanford%",
                "%carnegie mellon%",
                "%cmu%",
                limit,
            ),
            False,
        ),
        (
            "10. My question: What is the average GPA for PhD applicants?",
            """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM {applicants}
            WHERE degree ILIKE %s
              AND gpa IS NOT NULL
            LIMIT %s;
            """,
            ("%phd%", limit),
            False,
        ),
        (
            "11. My question: How many Fall 2026 entries are waitlisted?",
            """
            SELECT COUNT(*)
            FROM {applicants}
            WHERE term = %s
              AND status ILIKE %s
            LIMIT %s;
            """,
            ("Fall 2026", "%wait%", limit),
            False,
        ),
    ]

    def execute_queries(active_connection: Any) -> list[dict[str, str]]:
        """Execute all analysis queries using the supplied connection."""
        results: list[dict[str, str]] = []

        with active_connection.cursor() as cursor:
            for question, query_text, params, percentage in query_specs:
                statement = build_statement(query_text)
                results.append(
                    run_query(
                        cursor,
                        question,
                        statement,
                        params,
                        percentage=percentage,
                    )
                )

        return results

    if connection is not None:
        return execute_queries(connection)

    with connect(database_url) as managed_connection:
        return execute_queries(managed_connection)


def get_expected_keys() -> set[str]:
    """Return the keys every analysis result dictionary should contain."""
    return EXPECTED_RESULT_KEYS


if __name__ == "__main__":
    for item in get_analysis_results():
        print(item["question"])
        print("Answer:", item["answer"])
        print()
