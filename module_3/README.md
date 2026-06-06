# Module 3: GradCafe SQL and Flask Analysis

This module builds on the GradCafe scraping project from Module 2. The cleaned GradCafe applicant data is loaded into a local PostgreSQL database, queried with SQL, and displayed on a dynamic Flask webpage.

## Files

* `load_data.py`
  Loads the cleaned GradCafe JSON data into a PostgreSQL table called `applicants`.

* `query_data.py`
  Runs the required SQL analysis questions and prints the results to the console.

* `app.py`
  Runs the Flask webpage that displays the query results.

* `scrape.py`
  Copied and adapted from Module 2. It scrapes recent public GradCafe records.

* `pull_data.py`
  Used by the Flask “Pull Data” button. It calls the copied scraper, checks for likely duplicate records, and inserts new records into PostgreSQL.

* `templates/`
  Contains the HTML templates for the Flask webpage.

* `static/`
  Contains CSS styling for the Flask webpage.

* `data/`
  Contains the cleaned GradCafe JSON data used to initially load the database.

* `screenshots/`
  Contains screenshots of the console output and running Flask webpage.

## PostgreSQL Setup

This project uses a local PostgreSQL database.

Database used:

```text
Database name: gradcafe
User: postgres
Host: localhost
Port: 5432
```

The database password is stored locally in a `.env` file and is not included in GitHub.

The `.env` file should be placed inside `module_3` and should look like this:

```text
DB_NAME=gradcafe
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

## Install Requirements

From the main project folder:

```powershell
py -m pip install -r module_3\requirements.txt
```

## Load the Data

To create the `applicants` table and load the cleaned GradCafe data:

```powershell
py module_3\load_data.py
```

This script drops and recreates the `applicants` table, then inserts the cleaned applicant records from the JSON file.

## Run the SQL Queries

To print the required analysis questions and answers in the console:

```powershell
py module_3\query_data.py
```

The queries answer the assignment questions about Fall 2026 applications, international student percentages, GPA/GRE averages, acceptances, selected universities, and two additional original questions.

## Run the Flask Webpage

From the `module_3` folder:

```powershell
cd module_3
py app.py
```

Then open the webpage at:

```text
http://127.0.0.1:8080
```

The webpage displays the SQL query results dynamically from the PostgreSQL database.

## Pull Data Button

The “Pull Data” button checks GradCafe for recent applicant records using the copied Module 2 scraper. It then adds records to the PostgreSQL database only if they do not already appear to be stored.

The duplicate check uses a combination of fields such as program, date added, status, and degree because GradCafe does not provide a clean unique ID for each row.

Newly pulled records use the scraper-parsed program and university fields as fallback values for the LLM-generated columns.

## Update Analysis Button

The “Update Analysis” button refreshes the page and reruns the SQL queries so the displayed analysis uses the most recent database results.

If a Pull Data request is already running, the page warns the user and does not update the analysis until the data pull finishes.

## Notes

The data comes from anonymously submitted GradCafe entries, so the results should not be treated as official admissions statistics. The data may contain missing values, inconsistent formatting, repeated entries, or self-reporting bias.