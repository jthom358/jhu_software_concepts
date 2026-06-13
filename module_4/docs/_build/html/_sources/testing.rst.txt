Testing Guide
=============

Test organization
-----------------

All tests live under ``module_4/tests``. The required test files are:

* ``test_flask_page.py``
* ``test_buttons.py``
* ``test_analysis_format.py``
* ``test_db_insert.py``
* ``test_integration_end_to_end.py``
* ``test_coverage_edges.py``

Markers
-------

Every test is marked with one or more of the required Pytest markers:

* ``web`` for Flask route and page tests
* ``buttons`` for Pull Data and Update Analysis behavior
* ``analysis`` for formatting and rounding checks
* ``db`` for schema, inserts, and query tests
* ``integration`` for end-to-end flows

Run the full marked suite with::

   py -m pytest -m "web or buttons or analysis or db or integration"

Coverage
--------

``pytest.ini`` enables ``pytest-cov`` and requires 100 percent coverage for
``module_4/src``. The coverage proof is stored in
``module_4/coverage_summary.txt``.

Fixtures and test doubles
-------------------------

The suite uses Flask's test client rather than manual browser interaction.
Tests inject fake pull and query functions through the app factory so tests do
not depend on live Grad Cafe network calls or long-running scrapes.

Database tests use PostgreSQL through ``DATABASE_URL`` and create isolated test
state before inserting or querying rows.

Expected selectors
------------------

The UI tests depend on these stable selectors:

* ``data-testid="pull-data-btn"``
* ``data-testid="update-analysis-btn"``

Formatting expectations
-----------------------

Rendered analysis items use ``Answer:`` labels. Percentage values are rendered
with exactly two decimal places, such as ``39.28%``.