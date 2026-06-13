Operational Notes
=================

Busy state policy
-----------------

The application tracks whether a data pull is already in progress. While busy,
``POST /pull-data`` and ``POST /update-analysis`` return HTTP 409 with
``{"busy": true}``. This prevents overlapping pulls or analysis refreshes from
modifying shared state at the same time.

Idempotency strategy
--------------------

Database inserts use a uniqueness policy so repeated pulls with overlapping
records do not create duplicate applicant rows. Tests verify that multiple
pulls with overlapping fake records remain consistent.

Deterministic tests
-------------------

Tests use dependency injection and Flask's test client. They do not use live
internet calls, arbitrary sleep calls, or manual browser interaction.

Troubleshooting
---------------

If ``pytest`` is not recognized on Windows, run Pytest through Python instead::

   py -m pytest

If PostgreSQL's ``psql`` command is not on PATH, use the full executable path,
for example::

   & "C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe" --version

If database tests fail locally, confirm that ``DATABASE_URL`` points to an
available PostgreSQL database and that the database service is running.