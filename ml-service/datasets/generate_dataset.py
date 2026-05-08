import pandas as pd
import random
from faker import Faker

fake = Faker()

records = []

for _ in range(50000):
    humidity = round(random.uniform(10, 95), 2)
    ph = round(random.uniform(4.0, 9.0), 2)
    light = random.randint(100, 1200)
    temperature = round(random.uniform(10, 40), 2)

    score = (
        humidity * 0.35 +
        (14 - abs(7 - ph)) * 5 +
        light * 0.01 +
        temperature * 0.5
    )

    if score > 55:
        quality = "Healthy"
    elif score > 40:
        quality = "Moderate"
    else:
        quality = "Poor"

    records.append({
        "humidity": humidity,
        "ph": ph,
        "light": light,
        "temperature": temperature,
        "soil_quality": quality
    })


df = pd.DataFrame(records)

output = "datasets/large_training_dataset.csv"
df.to_csv(output, index=False)

print(f"Dataset generated: {output}")
print(df.head())