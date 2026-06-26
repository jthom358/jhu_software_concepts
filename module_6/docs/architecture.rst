Architecture
============

The application has three main layers.

Web layer
---------

The Flask web layer is implemented in ``src.app``. It exposes a
``create_app(...)`` factory so tests can construct a testable Flask app with
fake pull and query functions. The primary page is ``GET /analysis``.

The app also exposes button endpoints:

* ``POST /pull-data``
* ``POST /update-analysis``

The analysis template includes stable selectors:

* ``data-testid="pull-data-btn"``
* ``data-testid="update-analysis-btn"``

ETL layer
---------

The ETL layer includes scraping, pulling, normalization, and loading.

``src.scrape`` retrieves Grad Cafe data. Tests avoid live network calls by
injecting fake scraper and loader behavior.

``src.pull_data`` coordinates scraping recent records and inserting them into
PostgreSQL.

``src.load_data`` creates the required database schema, normalizes scraped
records into Module 3 fields, and inserts only unique rows.

Database and query layer
------------------------

``src.db_utils`` manages PostgreSQL connections through ``DATABASE_URL``.

``src.query_data`` computes the summary analysis displayed by the Flask
template. Query functions return dictionaries with stable keys so the template
and tests can rely on predictable output.