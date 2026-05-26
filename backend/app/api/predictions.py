"""
TerraGuard AI — Predictions API
=================================
GET  /predict/live    — date simulate + ML + salvare în DB
POST /predict/ingest  — date ESP32 + ML + salvare în DB
"""

import os
import logging
import requests
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sensor_service import generate_fake_sensor_data
from app.database import get_session, SensorReading

logger = logging.getLogger("predictions")
router = APIRouter()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")


def _call_ml(sensor_dict: dict) -> dict:
    try:
        payload = {
            "field_id":    sensor_dict.get("field_id"),
            "luminosity":  sensor_dict.get("luminosity", 400.0),
            "N":           sensor_dict.get("N") or sensor_dict.get("nitrogen", 100.0),
            "P":           sensor_dict.get("P") or sensor_dict.get("phosphorus", 50.0),
            "K":           sensor_dict.get("K") or sensor_dict.get("potassium", 120.0),
            "ph":          sensor_dict.get("ph", 6.5),
            "EC":          sensor_dict.get("EC") or sensor_dict.get("ec", 1.0),
            "humidity":    sensor_dict.get("humidity", 55.0),
            "temperature": sensor_dict.get("temperature", 22.0),
        }
        resp = requests.post(f"{ML_SERVICE_URL}/predict", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"ML service indisponibil: {e}")
        return {}


async def _save_reading(db, sensor, prediction=None, source="simulated"):
    reading = SensorReading(
        field_id    = sensor.get("field_id"),
        source      = source,
        luminosity  = sensor.get("luminosity"),
        humidity    = sensor.get("humidity"),
        temperature = sensor.get("temperature"),
        ec          = sensor.get("EC") or sensor.get("ec"),
        ph          = sensor.get("ph"),
        nitrogen    = sensor.get("N") or sensor.get("nitrogen"),
        phosphorus  = sensor.get("P") or sensor.get("phosphorus"),
        potassium   = sensor.get("K") or sensor.get("potassium"),
    )
    if prediction:
        reading.soil_quality     = prediction.get("soil_quality")
        reading.recommended_crop = prediction.get("recommended_crop")
        reading.confidence       = prediction.get("confidence")
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    return reading


@router.get("/predict/live")
async def predict_live(db: AsyncSession = Depends(get_session)):
    """
    Generează date simulate, rulează ML inference și salvează în PostgreSQL.
    """
    sensor_data = generate_fake_sensor_data()
    prediction  = _call_ml(sensor_data)
    reading     = await _save_reading(db, sensor_data, prediction, source="simulated")

    return {
        "sensor_data": sensor_data,
        "prediction":  prediction,
        "db_id":       reading.id,
    }


class ESP32PredictPayload(BaseModel):
    field_id:    Optional[str]   = "field-001"
    luminosity:  Optional[float] = None
    humidity:    Optional[float] = None
    temperature: Optional[float] = None
    ec:          Optional[float] = None
    ph:          Optional[float] = None
    nitrogen:    Optional[float] = None
    phosphorus:  Optional[float] = None
    potassium:   Optional[float] = None


@router.post("/predict/ingest")
async def predict_ingest(
    payload: ESP32PredictPayload,
    db: AsyncSession = Depends(get_session)
):
    """
    ESP32 trimite datele, obținem predicția ML și salvăm totul în PostgreSQL.
    Folosește acest endpoint dacă vrei atât predicție cât și stocare dintr-un singur apel.
    """
    sensor_dict = payload.dict()
    prediction  = _call_ml(sensor_dict)
    reading     = await _save_reading(db, sensor_dict, prediction, source="esp32")

    return {
        "sensor_data": sensor_dict,
        "prediction":  prediction,
        "db_id":       reading.id,
        "timestamp":   reading.timestamp,
    }
