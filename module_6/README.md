# Module 6: GradCafe Microservice Application

Module 6 refactors the GradCafe Flask and PostgreSQL application into a four-service Docker Compose architecture.

The system contains:

* A Flask web service
* A Python worker service
* A PostgreSQL database
* A RabbitMQ message broker

The Flask service publishes background jobs to RabbitMQ. The worker consumes those jobs, performs incremental GradCafe ingestion or analytics work, commits successful database transactions, and acknowledges messages only after the transaction completes.

## Architecture

```text
Browser
   |
   v
Flask Web Service
   |
   | publishes durable task messages
   v
RabbitMQ
   |
   | consumed with prefetch_count=1
   v
Python Worker
   |
   | transactional reads and inserts
   v
PostgreSQL
```

### Services

| Service    | Purpose                                                          |
| ---------- | ---------------------------------------------------------------- |
| `web`      | Serves the Flask analysis page and publishes background tasks    |
| `worker`   | Consumes RabbitMQ tasks, scrapes new records, and runs analytics |
| `db`       | Stores GradCafe applicant records and ingestion watermarks       |
| `rabbitmq` | Provides durable asynchronous task messaging                     |

## Project Structure

```text
module_6/
├── docker-compose.yml
├── README.md
├── setup.py
├── src/
│   ├── data/
│   │   └── applicant_data.json
│   ├── db/
│   │   ├── db_utils.py
│   │   ├── init.sql
│   │   └── load_data.py
│   ├── web/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── publisher.py
│   │   ├── run.py
│   │   └── app/
│   └── worker/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── consumer.py
│       └── etl/
│           ├── incremental_scraper.py
│           ├── pull_data.py
│           └── query_data.py
└── tests/
```

## Docker Hub Images

The two application images are published in the public Docker Hub repository:

```text
jthom358/module_6
```

Available tags:

```text
jthom358/module_6:web
jthom358/module_6:worker
```

The Compose file includes both `image` and `build` declarations. This allows the application images to be built locally or identified by their published Docker Hub tags.

## Requirements

* Docker Desktop
* Docker Compose
* Git
* Python 3.12 for local testing
* PostgreSQL for local database-backed tests

Docker Desktop should be running before using Docker Compose.

## Start the Application

From the `module_6` directory, build and start all four services:

```powershell
docker compose up -d --build
```

Check service status:

```powershell
docker compose ps
```

Expected status:

* `db` — healthy
* `rabbitmq` — healthy
* `web` — running
* `worker` — running

Open the Flask application:

```text
http://localhost:8080
```

Open the RabbitMQ management interface:

```text
http://localhost:15672
```

Development login:

```text
Username: guest
Password: guest
```

The development RabbitMQ credentials must not be reused in a production deployment.

## Stop the Application

Stop the containers while preserving the PostgreSQL volume:

```powershell
docker compose down
```

Stop the containers and delete the PostgreSQL volume:

```powershell
docker compose down -v
```

Deleting the volume causes the bundled applicant dataset to be loaded again during the next fresh startup.

## Initial Database Loading

The worker initializes the required database tables when it starts.

It then loads:

```text
src/data/applicant_data.json
```

inside the worker container through the read-only mount:

```text
/data/applicant_data.json
```

The initial load is idempotent. PostgreSQL uniqueness constraints and `ON CONFLICT DO NOTHING` prevent duplicate applicant records.

## Background Tasks

The Flask buttons publish the following task kinds:

```text
scrape_new_data
recompute_analytics
```

Messages are published through:

```text
Exchange: tasks
Exchange type: direct
Queue: tasks_q
Routing key: tasks
```

The exchange and queue are durable. Published messages use persistent delivery mode.

### Pull Data

The Pull Data button publishes a `scrape_new_data` task.

The worker:

1. Reads the current GradCafe ingestion watermark
2. Scrapes recent records
3. Stops when it reaches the previously processed watermark
4. Inserts only new records
5. Updates the watermark inside the same transaction
6. Commits the transaction
7. Acknowledges the RabbitMQ message

### Update Analysis

The Update Analysis button publishes a `recompute_analytics` task.

The worker runs the application analytics queries through the active message transaction and acknowledges the task only after a successful commit.

## RabbitMQ Reliability

The worker uses:

```text
prefetch_count=1
auto_ack=False
```

For successful tasks:

1. The handler completes
2. PostgreSQL commits
3. RabbitMQ receives `basic_ack`

For failed tasks:

1. PostgreSQL rolls back
2. RabbitMQ receives `basic_nack`
3. `requeue=False` prevents a permanently failing task from looping forever

The worker also retries its initial RabbitMQ connection to handle short startup timing differences between containers.

## PostgreSQL Persistence

PostgreSQL data is stored in the named volume:

```text
postgres_data
```

The database therefore survives ordinary container recreation and `docker compose down`.

The data is removed only when the volume is explicitly deleted, such as with:

```powershell
docker compose down -v
```

## Health Checks

The database health check uses:

```text
pg_isready
```

The RabbitMQ health check verifies:

```text
rabbitmq-diagnostics ping
rabbitmq-diagnostics check_port_connectivity
```

The web and worker services wait for PostgreSQL and RabbitMQ to become healthy before starting.

## Verify the Database

Check the number of applicant records:

```powershell
docker compose exec db psql -P pager=off `
    -U gradcafe_app `
    -d gradcafe `
    -c "SELECT COUNT(*) FROM applicants;"
```

Inspect the ingestion watermark:

```powershell
docker compose exec db psql -P pager=off `
    -U gradcafe_app `
    -d gradcafe `
    -c "SELECT * FROM ingestion_watermarks;"
```

## Verify RabbitMQ

Check queue state:

```powershell
docker compose exec rabbitmq rabbitmqctl list_queues `
    name messages_ready messages_unacknowledged consumers
```

A healthy idle system should show approximately:

```text
tasks_q    0    0    1
```

This means:

* No messages are waiting
* No messages are currently unacknowledged
* One worker consumer is connected

## View Logs

View worker logs:

```powershell
docker compose logs worker --tail=100
```

View web logs:

```powershell
docker compose logs web --tail=100
```

Follow all service logs:

```powershell
docker compose logs -f
```

## Local Python Environment

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install the local project requirements according to the repository configuration.

## Run Tests

The database-backed tests require a separate PostgreSQL test database.

Set the test connection string:

```powershell
$env:TEST_DATABASE_URL = "postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/gradcafe_test"
```

Run the complete test suite:

```powershell
python -m pytest
```

The submitted project currently contains 50 passing tests and enforces 100 percent source-code coverage.

## Run Pylint

Run Pylint on the application source:

```powershell
python -m pylint src
```

The submitted source achieves:

```text
Your code has been rated at 10.00/10
```

## Security and Data Integrity

The application includes the following safeguards:

* Parameterized PostgreSQL queries
* Safe `psycopg.sql` composition
* Validated and bounded query limits
* Durable RabbitMQ exchange and queue declarations
* Persistent task messages
* Manual acknowledgements
* Commit-before-ack behavior
* Rollback and non-requeued rejection on failure
* Idempotent applicant insertion
* Incremental ingestion watermarks
* Read-only container data mount
* Non-root web and worker containers
* Docker health checks
* PostgreSQL named-volume persistence

## Docker Image Users

Both custom Docker images create and run as a non-root application user with UID and GID `1000`.

The images use Python 3.11 slim and pinned service dependencies.

## Development Credentials

The Compose configuration contains development-only credentials so the complete assignment stack can run reproducibly.

These credentials are not suitable for production. A production deployment should use secret management, unique credentials, restricted RabbitMQ users, and encrypted network connections.

## Published Documentation

The project’s existing Sphinx documentation is available through Read the Docs:

```text
https://jthom358-jhu-software-concepts.readthedocs.io/en/latest/
```
