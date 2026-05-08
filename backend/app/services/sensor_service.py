from faker import Faker
import random

fake = Faker()

def generate_fake_sensor_data():
    return {
        "field_id": fake.uuid4(),
        "humidity": round(random.uniform(20, 90), 2),
        "ph": round(random.uniform(4.5, 8.5), 2),
        "light": random.randint(100, 1000)
    }