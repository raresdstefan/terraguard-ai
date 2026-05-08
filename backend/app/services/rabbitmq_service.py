import pika
import json
import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
QUEUE = "soil_data"

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST)
)

channel = connection.channel()
channel.queue_declare(queue=QUEUE)


def publish_message(data):
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE,
        body=json.dumps(data)
    )