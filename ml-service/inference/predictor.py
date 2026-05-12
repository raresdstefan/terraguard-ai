"""
TerraGuard AI — Inference
==========================
Accepts all 8 sensor parameters:
  Luminosity sensor : luminosity (lux)
  7-in-1 soil sensor: N, P, K, ph, EC, humidity, temperature
"""

import joblib
import numpy as np

model   = joblib.load("models/soil_quality_model.pkl")
encoder = joblib.load("models/label_encoder.pkl")

FEATURES = ["luminosity", "N", "P", "K", "ph", "EC", "humidity", "temperature"]


# ─────────────────────────────────────────────
#  Crop recommendation engine (8-parameter)
# ─────────────────────────────────────────────

def get_crop_recommendation(data):
    hum  = data["humidity"]
    ph   = data["ph"]
    n    = data["N"]
    p    = data["P"]
    k    = data["K"]
    ec   = data["EC"]
    temp = data["temperature"]
    lux  = data["luminosity"]

    # Tomatoes — warm, moderate humidity, balanced NPK, good light
    if 60 <= hum <= 80 and 6.0 <= ph <= 7.0 and temp >= 18 and lux >= 400:
        return {
            "crop": "Tomatoes 🍅",
            "description": "Balanced humidity, near-neutral pH, warm temperature, and adequate light create ideal tomato conditions.",
            "recommendation": "Maintain consistent irrigation; ensure K levels stay above 120 mg/kg for fruit quality.",
        }

    # Potatoes — slightly acidic, moderate humidity, high K
    if 50 <= hum <= 70 and 5.0 <= ph <= 6.5 and k >= 100:
        return {
            "crop": "Potatoes 🥔",
            "description": "Slightly acidic soil with moderate humidity and good potassium levels favour potato tuber development.",
            "recommendation": "Monitor drainage to prevent waterlogging; maintain EC below 1.5 dS/m.",
        }

    # Rice — high humidity, flooded conditions
    if hum > 80 and ph <= 7.5:
        return {
            "crop": "Rice 🌾",
            "description": "High soil moisture content and near-neutral pH are well-suited to paddy rice cultivation.",
            "recommendation": "Maintain high irrigation and monitor nitrogen levels; target N > 80 mg/kg.",
        }

    # Wheat — moderate humidity, good N, balanced EC
    if 40 <= hum <= 65 and 6.0 <= ph <= 7.5 and n >= 80 and ec <= 1.8:
        return {
            "crop": "Wheat 🌱",
            "description": "Moderate moisture, ample nitrogen, and balanced salinity support healthy wheat growth.",
            "recommendation": "Ensure stable sunlight (> 300 lux) and top-dress with P if levels fall below 30 mg/kg.",
        }

    # Sunflower — dry-tolerant, high light, moderate fertility
    if hum < 45 and lux >= 500 and ph <= 7.5:
        return {
            "crop": "Sunflower 🌻",
            "description": "Lower humidity with strong light levels and moderate soil fertility suit drought-tolerant sunflowers.",
            "recommendation": "Minimal irrigation required; maintain pH below 7.5 and K above 80 mg/kg.",
        }

    # Maize — warm, high N demand, moderate-high humidity
    if temp >= 20 and n >= 120 and 50 <= hum <= 80:
        return {
            "crop": "Maize 🌽",
            "description": "Warm temperatures and high nitrogen availability combined with good soil moisture create optimal maize conditions.",
            "recommendation": "Split nitrogen applications across the growing season; target K > 100 mg/kg.",
        }

    return {
        "crop": "No optimal crop detected",
        "description": "Current soil conditions do not match standard agronomic profiles for common crops.",
        "recommendation": "Adjust pH toward 6.0–7.0, improve drainage if humidity > 85 %, and enrich NPK levels.",
    }


# ─────────────────────────────────────────────
#  Main prediction function
# ─────────────────────────────────────────────

def predict_soil_quality(data):
    features = np.array([[
        data.get("luminosity",  400),
        data.get("N",           100),
        data.get("P",            50),
        data.get("K",           120),
        data.get("ph",          6.5),
        data.get("EC",          1.0),
        data.get("humidity",     55),
        data.get("temperature",  22),
    ]])

    prediction   = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    confidence_pct = round(float(probabilities.max()) * 100, 1)

    if confidence_pct >= 85:
        confidence_label = "High"
    elif confidence_pct >= 65:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"

    label     = encoder.inverse_transform([prediction])[0]
    crop_data = get_crop_recommendation(data)

    return {
        "soil_quality":     label,
        "confidence":       confidence_label,
        "confidence_pct":   confidence_pct,
        "recommended_crop": crop_data["crop"],
        "description":      crop_data["description"],
        "recommendation":   crop_data["recommendation"],
    }
