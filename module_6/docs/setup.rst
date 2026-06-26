Setup and Running the Application
=================================

Project layout
--------------

The Module 4 application is organized as follows::

   module_4/
   ├── src/
   ├── tests/
   ├── docs/
   ├── pytest.ini
   ├── requirements.txt
   ├── README.md
   └── coverage_summary.txt

The ``src`` folder contains the Flask app, scraping, loading, database, and
query code. The ``tests`` folder contains the full Pytest suite.

Install dependencies
--------------------

From the ``module_4`` folder, install dependencies with::

   py -m pip install -r requirements.txt

Environment variables
---------------------

The application uses ``DATABASE_URL`` to connect to PostgreSQL. Example local
test value::

   postgresql://postgres:postgres@localhost:5432/gradcafe_test

Do not commit real database passwords or local ``.env`` files.

Run the Flask app
-----------------

From the repository root, run::

   cd module_4
   py -m src.app

Then open the Flask development server in a browser.

Run tests
---------

Run the complete marked test suite with::

   py -m pytest -m "web or buttons or analysis or db or integration"

The Pytest configuration enforces 100 percent coverage for code under
``module_4/src``.