"""
TerraGuard AI — Sensor Service
================================
Simulates readings from:
  - Luminosity sensor  (1 parameter)
  - 7-in-1 soil sensor (N, P, K, pH, EC, humidity, temperature)
"""

from faker import Faker
import random

fake = Faker()


def generate_fake_sensor_data():
    """
    Generate a realistic simulated sensor reading.
    Ranges are based on agronomic plausibility rules from Stage 2/3 datasets.
    """
    # Soft correlation: healthy-ish soil more likely
    soil_type = random.choices(
        ["healthy", "moderate", "poor"],
        weights=[0.40, 0.40, 0.20]
    )[0]

    if soil_type == "healthy":
        humidity    = round(random.uniform(45, 80),  2)
        ph          = round(random.uniform(5.8, 7.2), 2)
        N           = round(random.uniform(100, 200), 1)
        P           = round(random.uniform(35, 90),   1)
        K           = round(random.uniform(120, 260), 1)
        EC          = round(random.uniform(0.7, 1.8), 2)
        temperature = round(random.uniform(15, 28),   2)
        luminosity  = round(random.uniform(400, 1100), 1)

    elif soil_type == "moderate":
        humidity    = round(random.uniform(20, 65),  2)
        ph          = round(random.uniform(4.8, 8.2), 2)
        N           = round(random.uniform(50, 140),  1)
        P           = round(random.uniform(15, 65),   1)
        K           = round(random.uniform(60, 160),  1)
        EC          = round(random.uniform(0.4, 2.5), 2)
        temperature = round(random.uniform(10, 36),   2)
        luminosity  = round(random.uniform(200, 800), 1)

    else:  # poor
        humidity    = round(random.uniform(5, 40),   2)
        ph          = round(random.uniform(3.8, 5.2), 2)
        N           = round(random.uniform(5, 50),    1)
        P           = round(random.uniform(2, 25),    1)
        K           = round(random.uniform(10, 80),   1)
        EC          = round(random.uniform(2.5, 4.0), 2)
        temperature = round(random.uniform(8, 42),    2)
        luminosity  = round(random.uniform(50, 400),  1)

    return {
        "field_id":    fake.uuid4(),
        # Luminosity sensor
        "luminosity":  luminosity,
        # 7-in-1 soil sensor
        "N":           N,
        "P":           P,
        "K":           K,
        "ph":          ph,
        "EC":          EC,
        "humidity":    humidity,
        "temperature": temperature,
    }
