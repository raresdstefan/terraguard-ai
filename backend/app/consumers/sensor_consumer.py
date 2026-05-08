import pika
import json
import os
import requests

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
QUEUE = "soil_data"


def callback(ch, method, properties, body):
    data = json.loads(body)
    print("Received:", data)

    response = requests.post(
        "http://ml-service:8001/predict",
        json=data
    )

    print("Prediction:", response.json())


def start_consumer():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE)

    channel.basic_consume(
        queue=QUEUE,
        on_message_callback=callback,
        auto_ack=True
    )

    print("Waiting for messages...")
    channel.start_consuming()