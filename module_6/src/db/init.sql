CREATE TABLE IF NOT EXISTS applicants (
    p_id INTEGER PRIMARY KEY,
    university TEXT,
    program TEXT,
    degree TEXT,
    status TEXT,
    date_added TEXT,
    decision_date TEXT,
    start_term TEXT,
    start_year INTEGER,
    student_type TEXT,
    gre_quantitative NUMERIC,
    gre_verbal NUMERIC,
    gre_analytical_writing NUMERIC,
    gpa NUMERIC,
    comments TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source TEXT PRIMARY KEY,
    last_seen TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);