import random
import joblib
import numpy as np

model = joblib.load("models/soil_quality_model.pkl")
encoder = joblib.load("models/label_encoder.pkl")


def get_crop_recommendation(humidity, ph, light):

    # Tomatoes
    if 60 <= humidity <= 80 and 6.0 <= ph <= 7.0:
        return {
            "crop": "Tomatoes 🍅",
            "description": (
                "The soil conditions are excellent for tomato growth. "
                "Balanced humidity and near-neutral pH support healthy roots."
            ),
            "recommendation": (
                "Maintain irrigation consistency and ensure proper sunlight exposure."
            )
        }

    # Potatoes
    elif 50 <= humidity <= 70 and 5.0 <= ph <= 6.5:
        return {
            "crop": "Potatoes 🥔",
            "description": (
                "The slightly acidic soil and moderate humidity are favorable for potatoes."
            ),
            "recommendation": (
                "Monitor soil drainage to avoid excess moisture accumulation."
            )
        }

    # Rice
    elif humidity > 80:
        return {
            "crop": "Rice 🌾",
            "description": (
                "High moisture levels make the soil suitable for water-intensive crops like rice."
            ),
            "recommendation": (
                "Maintain high irrigation levels and monitor nutrient balance."
            )
        }

    # Wheat
    elif 40 <= humidity <= 60 and 6.0 <= ph <= 7.5:
        return {
            "crop": "Wheat 🌱",
            "description": (
                "The soil has balanced conditions suitable for wheat cultivation."
            ),
            "recommendation": (
                "Ensure stable sunlight conditions for optimal yield."
            )
        }

    return {
        "crop": "No optimal crop detected",
        "description": (
            "Current soil conditions are unstable or unsuitable for common crops."
        ),
        "recommendation": (
            "Improve pH balance and irrigation before planting."
        )
    }


def predict_soil_quality(data):

    features = np.array([
        [
            data['humidity'],
            data['ph'],
            data['light'],
            data.get('temperature', 25)
        ]
    ])

    prediction = model.predict(features)[0]

    label = encoder.inverse_transform([prediction])[0]

    crop_data = get_crop_recommendation(
        data['humidity'],
        data['ph'],
        data['light']
    )

    return {
        "soil_quality": label,
        "confidence": "High",
        "recommended_crop": crop_data["crop"],
        "description": crop_data["description"],
        "recommendation": crop_data["recommendation"]
    }