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
from app.api.routes import LATEST_ESP32_DATA
from sqlalchemy import select, desc

logger = logging.getLogger("predictions")
router = APIRouter()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")


def _call_ml(sensor_dict: dict) -> dict:
    try:
        def val(key, alt_key=None, default=0.0):
            v = sensor_dict.get(key)
            if v is None and alt_key:
                v = sensor_dict.get(alt_key)
            return float(v) if v is not None else default

        payload = {
            "field_id":    sensor_dict.get("field_id"),
            "luminosity":  val("luminosity",  default=400.0),
            "N":           val("N",  "nitrogen",   default=100.0),
            "P":           val("P",  "phosphorus",  default=50.0),
            "K":           val("K",  "potassium",  default=120.0),
            "ph":          val("ph",              default=6.5),
            "EC":          val("EC", "ec",         default=1.0),
            "humidity":    val("humidity",         default=55.0),
            "temperature": val("temperature",      default=22.0),
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
    
    # Caută ultima citire reală de la ESP32 în DB
    stmt = (
        select(SensorReading)
        .where(SensorReading.source == "esp32")
        .order_by(desc(SensorReading.timestamp))
        .limit(1)
    )
    result = await db.execute(stmt)
    last_esp32 = result.scalar_one_or_none()

    if last_esp32:
        # Reconstituie dict-ul din înregistrarea din DB
        sensor_data = {
            "field_id":    last_esp32.field_id,
            "luminosity":  last_esp32.luminosity,
            "N":           last_esp32.nitrogen,
            "P":           last_esp32.phosphorus,
            "K":           last_esp32.potassium,
            "ph":          last_esp32.ph,
            "EC":          last_esp32.ec,
            "humidity":    last_esp32.humidity,
            "temperature": last_esp32.temperature,
        }
    else:
        # Nicio citire ESP32 în DB — fallback la simulate
        sensor_data = generate_fake_sensor_data()

    prediction = _call_ml(sensor_data)

    reading = await _save_reading(
        db, sensor_data, prediction,
        source="esp32" if last_esp32 else "simulated"
    )

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
