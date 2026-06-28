"""RabbitMQ consumer for background GradCafe tasks."""

# pylint: disable=duplicate-code

import json
import os
from collections.abc import Callable
from typing import Any

import pika

from src.db.db_utils import connect
from src.worker.etl.incremental_scraper import run_incremental_scrape
from src.worker.etl.query_data import get_analysis_results

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"

TaskHandler = Callable[[Any, dict[str, Any]], Any]


def handle_scrape_new_data(
    connection: Any,
    payload: dict[str, Any],
) -> dict[str, int]:
    """Run incremental GradCafe ingestion."""
    return run_incremental_scrape(connection, payload)


def handle_recompute_analytics(
    connection: Any,
    payload: dict[str, Any],
) -> list[dict[str, str]]:
    """Recompute all analytics using the active transaction."""
    requested_limit = payload.get("limit", 1)

    return get_analysis_results(
        requested_limit=requested_limit,
        connection=connection,
    )


TASK_HANDLERS: dict[str, TaskHandler] = {
    "scrape_new_data": handle_scrape_new_data,
    "recompute_analytics": handle_recompute_analytics,
}


def process_message(  # pylint: disable=too-many-arguments
    channel: Any,
    method: Any,
    properties: Any,
    body: bytes,
    *,
    handlers: dict[str, TaskHandler] | None = None,
    connector: Callable[..., Any] = connect,
) -> None:
    """Process one message in a dedicated database transaction."""
    del properties

    available_handlers = handlers if handlers is not None else TASK_HANDLERS
    database_url = os.getenv("DATABASE_URL")
    connection = None

    try:
        message = json.loads(body.decode("utf-8"))
        task_kind = message["kind"]
        payload = message.get("payload", {})

        if not isinstance(payload, dict):
            raise ValueError("Task payload must be a JSON object.")

        handler = available_handlers.get(task_kind)
        if handler is None:
            raise ValueError(f"Unknown task kind: {task_kind}")

        connection = connector(database_url)
        handler(connection, payload)
        connection.commit()
    except Exception:  # pylint: disable=broad-exception-caught
        if connection is not None:
            connection.rollback()

        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )
        return
    finally:
        if connection is not None:
            connection.close()

    channel.basic_ack(delivery_tag=method.delivery_tag)


def open_channel() -> tuple[Any, Any]:
    """Open RabbitMQ and declare the durable task topology."""
    rabbitmq_url = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/%2F",
    )
    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="direct",
        durable=True,
    )
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(
        exchange=EXCHANGE,
        queue=QUEUE,
        routing_key=ROUTING_KEY,
    )
    channel.basic_qos(prefetch_count=1)

    return connection, channel


def run_worker() -> None:
    """Consume task messages until the worker is stopped."""
    connection, channel = open_channel()

    channel.basic_consume(
        queue=QUEUE,
        on_message_callback=process_message,
        auto_ack=False,
    )

    try:
        channel.start_consuming()
    finally:
        connection.close()


if __name__ == "__main__":  # pragma: no cover
    run_worker()
