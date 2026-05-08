import time
from app.services.sensor_service import generate_fake_sensor_data
from app.services.rabbitmq_service import publish_message

while True:
    data = generate_fake_sensor_data()
    print("Publishing:", data)
    publish_message(data)
    time.sleep(5)