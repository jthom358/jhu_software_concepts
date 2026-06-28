CREATE TABLE IF NOT EXISTS applicants (
    p_id INTEGER PRIMARY KEY,
    program TEXT NOT NULL,
    comments TEXT,
    date_added DATE,
    url TEXT,
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa DOUBLE PRECISION,
    gre DOUBLE PRECISION,
    gre_v DOUBLE PRECISION,
    gre_aw DOUBLE PRECISION,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS applicants_unique_record_idx
ON applicants (
    COALESCE(program, ''),
    COALESCE(date_added, DATE '1900-01-01'),
    COALESCE(status, ''),
    COALESCE(degree, '')
);

CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source TEXT PRIMARY KEY,
    last_seen TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);