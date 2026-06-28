"""Tests for RabbitMQ worker message processing."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import src.worker.consumer as consumer


class FakeConnection:
    """Database connection that records transaction actions."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self):
        """Record a successful commit."""
        self.committed = True

    def rollback(self):
        """Record a rollback."""
        self.rolled_back = True

    def close(self):
        """Record connection closure."""
        self.closed = True


def test_process_message_commits_before_acknowledgement():
    """Successful tasks commit and are then acknowledged."""
    events = []
    connection = FakeConnection()
    channel = Mock()
    method = SimpleNamespace(delivery_tag=7)

    def handler(conn, payload):
        assert conn is connection
        assert payload == {"limit": 25}
        events.append("handled")

    def commit():
        events.append("committed")
        connection.committed = True

    connection.commit = commit

    def acknowledge(**kwargs):
        assert kwargs == {"delivery_tag": 7}
        events.append("acknowledged")

    channel.basic_ack.side_effect = acknowledge

    consumer.process_message(
        channel,
        method,
        None,
        json.dumps(
            {
                "kind": "scrape_new_data",
                "payload": {"limit": 25},
            }
        ).encode("utf-8"),
        handlers={"scrape_new_data": handler},
        connector=lambda database_url: connection,
    )

    assert events == ["handled", "committed", "acknowledged"]
    assert connection.rolled_back is False
    assert connection.closed is True
    channel.basic_nack.assert_not_called()


def test_process_message_rolls_back_and_nacks_failed_task():
    """Failed handlers roll back and reject without requeueing."""
    connection = FakeConnection()
    channel = Mock()
    method = SimpleNamespace(delivery_tag=11)

    def failing_handler(conn, payload):
        del conn, payload
        raise RuntimeError("task failed")

    consumer.process_message(
        channel,
        method,
        None,
        b'{"kind":"scrape_new_data","payload":{}}',
        handlers={"scrape_new_data": failing_handler},
        connector=lambda database_url: connection,
    )

    assert connection.committed is False
    assert connection.rolled_back is True
    assert connection.closed is True
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(
        delivery_tag=11,
        requeue=False,
    )


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        b'{"kind":"unknown","payload":{}}',
        b'{"kind":"known","payload":[]}',
    ],
)
def test_process_message_rejects_invalid_messages(body):
    """Malformed and unsupported messages are rejected permanently."""
    channel = Mock()
    method = SimpleNamespace(delivery_tag=20)

    consumer.process_message(
        channel,
        method,
        None,
        body,
        handlers={"known": Mock()},
        connector=Mock(),
    )

    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_called_once_with(
        delivery_tag=20,
        requeue=False,
    )


def test_open_channel_declares_durable_topology(monkeypatch):
    """The worker declares its exchange, queue, binding, and QoS."""
    channel = Mock()
    connection = Mock()
    connection.channel.return_value = channel

    blocking_connection = Mock(return_value=connection)
    monkeypatch.setattr(consumer.pika, "BlockingConnection", blocking_connection)
    monkeypatch.setenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@example:5672/%2F",
    )

    returned_connection, returned_channel = consumer.open_channel()

    assert returned_connection is connection
    assert returned_channel is channel

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
    channel.basic_qos.assert_called_once_with(prefetch_count=1)


def test_run_worker_registers_manual_ack_consumer(monkeypatch):
    """The worker registers its callback and closes when consumption ends."""
    connection = Mock()
    channel = Mock()
    monkeypatch.setattr(
        consumer,
        "open_channel",
        lambda: (connection, channel),
    )

    consumer.run_worker()

    channel.basic_consume.assert_called_once_with(
        queue="tasks_q",
        on_message_callback=consumer.process_message,
        auto_ack=False,
    )
    channel.start_consuming.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_run_worker_closes_connection_after_consumer_error(monkeypatch):
    """RabbitMQ connections close even if consumption exits with an error."""
    connection = Mock()
    channel = Mock()
    channel.start_consuming.side_effect = RuntimeError("consumer stopped")

    monkeypatch.setattr(
        consumer,
        "open_channel",
        lambda: (connection, channel),
    )

    with pytest.raises(RuntimeError, match="consumer stopped"):
        consumer.run_worker()

    connection.close.assert_called_once_with()