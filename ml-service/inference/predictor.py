import random


def predict_soil_quality(data):
    score = (
        data['humidity'] * 0.4 +
        (14 - abs(7 - data['ph'])) * 5 +
        data['light'] * 0.01
    )

    if score > 50:
        quality = "Healthy"
    elif score > 35:
        quality = "Moderate"
    else:
        quality = "Poor"

    return {
        "soil_quality": quality,
        "score": round(score, 2),
        "recommendation": random.choice([
            "Increase irrigation",
            "Reduce acidity",
            "Optimal conditions",
            "Monitor light exposure"
        ])
    }