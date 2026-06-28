"""RabbitMQ consumer for background GradCafe tasks."""

# pylint: disable=duplicate-code

import json
import os
from collections.abc import Callable
from typing import Any

import pika

from src.db.db_utils import connect

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"

TaskHandler = Callable[[Any, dict[str, Any]], None]
TASK_HANDLERS: dict[str, TaskHandler] = {}


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
