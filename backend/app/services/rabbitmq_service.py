import pika
import json
import os
import time

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
QUEUE = "soil_data"

_channel = None


def _get_channel():
    global _channel

    if _channel and _channel.is_open:
        return _channel

    retries = 10
    for attempt in range(1, retries + 1):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
            _channel = connection.channel()
            _channel.queue_declare(queue=QUEUE)
            print(f"RabbitMQ connected on attempt {attempt}")
            return _channel
        except pika.exceptions.AMQPConnectionError as e:
            print(f"RabbitMQ not ready (attempt {attempt}/{retries}), retrying in 3s...")
            time.sleep(3)

    raise RuntimeError("Could not connect to RabbitMQ after multiple retries")


def publish_message(data):
    channel = _get_channel()
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE,
        body=json.dumps(data)
    )
