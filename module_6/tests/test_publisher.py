"""Unit tests for the RabbitMQ task publisher."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.web import publisher


def test_open_channel_declares_durable_entities(monkeypatch):
    """The publisher declares the required durable AMQP entities."""
    monkeypatch.setenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")

    connection = MagicMock()
    channel = connection.channel.return_value

    with patch.object(
        publisher.pika,
        "BlockingConnection",
        return_value=connection,
    ) as blocking_connection:
        returned_connection, returned_channel = publisher._open_channel()

    assert returned_connection is connection
    assert returned_channel is channel

    blocking_connection.assert_called_once()
    channel.exchange_declare.assert_called_once_with(
        exchange="tasks",
        exchange_type="direct",
        durable=True,
    )
    channel.queue_declare.assert_called_once_with(
        queue="tasks_q",
        durable=True,
    )
    channel.queue_bind.assert_called_once_with(
        exchange="tasks",
        queue="tasks_q",
        routing_key="tasks",
    )


def test_publish_task_sends_persistent_compact_json():
    """Publishing sends the required JSON structure and persistent metadata."""
    connection = MagicMock()
    channel = MagicMock()

    with patch.object(
        publisher,
        "_open_channel",
        return_value=(connection, channel),
    ):
        publisher.publish_task(
            "scrape_new_data",
            payload={"since": "123"},
            headers={"request_id": "abc"},
        )

    channel.basic_publish.assert_called_once()
    arguments = channel.basic_publish.call_args.kwargs

    assert arguments["exchange"] == "tasks"
    assert arguments["routing_key"] == "tasks"
    assert arguments["mandatory"] is False

    message = json.loads(arguments["body"].decode("utf-8"))
    assert message["kind"] == "scrape_new_data"
    assert message["payload"] == {"since": "123"}
    assert "ts" in message

    properties = arguments["properties"]
    assert properties.delivery_mode == 2
    assert properties.headers == {"request_id": "abc"}

    connection.close.assert_called_once_with()


def test_publish_task_uses_defaults():
    """Missing payload and headers become empty dictionaries."""
    connection = MagicMock()
    channel = MagicMock()

    with patch.object(
        publisher,
        "_open_channel",
        return_value=(connection, channel),
    ):
        publisher.publish_task("recompute_analytics")

    arguments = channel.basic_publish.call_args.kwargs
    message = json.loads(arguments["body"].decode("utf-8"))

    assert message["payload"] == {}
    assert arguments["properties"].headers == {}
    connection.close.assert_called_once_with()


def test_publish_task_closes_connection_after_publish_error():
    """The connection closes while the publish exception remains visible."""
    connection = MagicMock()
    channel = MagicMock()
    channel.basic_publish.side_effect = RuntimeError("publish failed")

    with patch.object(
        publisher,
        "_open_channel",
        return_value=(connection, channel),
    ):
        with pytest.raises(RuntimeError, match="publish failed"):
            publisher.publish_task("scrape_new_data")

    connection.close.assert_called_once_with()