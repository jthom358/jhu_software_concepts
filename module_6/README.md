````powershell
@'
# Module 5: Secure GradCafe Flask and PostgreSQL Application

This project builds on the previous GradCafe data-analysis modules by adding software-assurance controls, reproducible packaging, static analysis, dependency scanning, database hardening, and continuous integration. The application loads and collects GradCafe applicant data, stores it in PostgreSQL, analyzes the records with safely composed SQL queries, and displays the results through a Flask web interface.

## Project Structure

- `src/` — Flask application, database utilities, scraper, loader, and analysis queries
- `tests/` — unit, integration, database, page, and button tests
- `.github/workflows/ci.yml` — submission copy of the Module 5 CI workflow
- `dependency.svg` — Python dependency graph generated with pydeps and Graphviz
- `setup.py` — installable Python package configuration
- `requirements.txt` — runtime, testing, documentation, linting, and analysis dependencies
- `.env.example` — example environment-variable configuration
- `snyk-analysis.png` — required Snyk dependency-scan evidence
- `snyk-code-analysis.png` — Snyk Code static-analysis evidence
- `coverage_summary.txt` — Pytest and coverage results
- `pylint_summary.txt` — Pylint results

## Requirements

- Python 3.12 or compatible Python 3.10+
- PostgreSQL
- Graphviz for regenerating the dependency graph
- Snyk CLI for local security scanning
- Git

## Environment Variables

Copy `.env.example` to `.env` and replace the placeholders with local database credentials.

```powershell
Copy-Item .env.example .env
````

Required variables:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gradcafe_test
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

The real `.env` file is excluded from version control. Do not commit passwords or other credentials.

For destructive database tests, define a separate administrative test connection:

```powershell
$env:TEST_DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/gradcafe_test"
```

The application itself should continue using the least-privilege account from `.env`.

## Fresh Install with pip and venv

Create and activate a clean virtual environment:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install the project and all required tools:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pip check
```

The editable installation makes package imports consistent for local execution, testing, and CI.

## Fresh Install with uv

Create a clean environment using uv:

```powershell
uv venv .venv --python 3.12
```

Install the declared dependencies and project package:

```powershell
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt
uv pip install --python .\.venv\Scripts\python.exe -e .
uv pip check --python .\.venv\Scripts\python.exe
```

Activate the environment when needed:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Database Initialization

The database schema can be created and populated with the bundled applicant data by running:

```powershell
python -m src.load_data
```

The application uses environment variables to create its PostgreSQL connection.

## Running the Flask Application

From `module_5`, run:

```powershell
python -m src.app
```

Open the local address displayed in the terminal. The analysis page displays the PostgreSQL query results and includes controls for pulling recent data and updating the analysis.

Flask debug mode is disabled in the submitted application configuration.

## Running Tests

Set the administrative test database URL before running database and integration tests:

```powershell
$env:TEST_DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/gradcafe_test"
python -m pytest
```

The final test suite contains 23 passing tests and enforces 100 percent code coverage through `pytest.ini`.

## Pylint

Run Pylint only on the Python source files:

```powershell
python -m pylint .\src --fail-under=10
```

The final source code achieves a score of:

```text
Your code has been rated at 10.00/10
```

## SQL Injection Defenses

User-provided values are never concatenated, formatted, or inserted directly into SQL strings. Dynamic identifiers are composed with `psycopg.sql.SQL` and `sql.Identifier`, while values are passed separately through `%s` placeholders and parameter collections. SQL statement construction is kept separate from query execution. Query limits are validated and clamped between 1 and 100 to prevent oversized requests. Tests exercise invalid and malicious values to confirm that the application does not expose unintended records or execute injected SQL.

## Least-Privilege Database Configuration

The normal application account is not a PostgreSQL superuser and does not own the `applicants` table. It is granted only the permissions required by the application:

```sql
GRANT SELECT, INSERT ON TABLE applicants TO gradcafe_app;
REVOKE UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
ON TABLE applicants FROM gradcafe_app;
REVOKE CREATE ON SCHEMA public FROM gradcafe_app;
```

The account can read and insert applicant records but cannot drop or alter the table. Administrative credentials are reserved for schema creation and test setup.

## Dependency Graph

The dependency graph can be regenerated with:

```powershell
python -m pydeps .\src `
    --noshow `
    -T svg `
    -o dependency.svg `
    --exclude flask flask.* `
    --max-bacon 2 `
    --rankdir LR
```

Graphviz must be installed and its `dot` executable must be available on the system path.

## Security Scanning

Run the required dependency scan with:

```powershell
snyk test --file=requirements.txt --package-manager=pip
```

The submitted dependency scan tested 51 dependencies and reported no vulnerable paths.

Run the optional Snyk Code static-analysis scan with:

```powershell
snyk code test src
```

The final source-only Snyk Code scan reported zero issues. The scan is limited to `src` so that third-party packages installed inside `.venv` are not incorrectly treated as project source code.

## Continuous Integration

The root repository workflow is located at:

```text
.github/workflows/module5-ci.yml
```

A matching submission copy is located at:

```text
module_5/.github/workflows/ci.yml
```

The workflow runs on pushes and pull requests affecting Module 5 and contains four separate jobs:

1. Pylint with `--fail-under=10`
2. Dependency-graph generation and validation
3. Snyk dependency scanning
4. PostgreSQL-backed Pytest execution with 100 percent coverage enforcement

The PostgreSQL test database runs as a GitHub Actions service container. The Snyk credential is stored as an encrypted GitHub Actions secret named `SNYK_TOKEN` and is never committed to the repository.

## Published Documentation

The project’s Sphinx documentation remains available through Read the Docs:

https://jthom358-jhu-software-concepts.readthedocs.io/en/latest/

## Security Evidence

The submission contains:

* `Pylint-and-Pytest-Perfect-Evidence.png`
* `pylint_summary.txt`
* `coverage_summary.txt`
* `snyk-analysis.png`
* `snyk-code-analysis.png`
* `github-actions-success.png`
* `dependency.svg`
  '@ | Set-Content .\README.md -Encoding utf8

```
```
