"""
TerraGuard AI — API Routes
===========================
Endpoint-uri:
  GET  /sensor/live        — citire live (simulată sau ESP32)
  POST /sensor/ingest      — ESP32 trimite date prin HTTP POST
  GET  /sensor/history     — ultimele N citiri din PostgreSQL
  GET  /predict/live       — citire + predicție ML
  POST /predict/ingest     — ingest ESP32 + predicție ML + salvare în DB
"""

import os
import requests
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.services.sensor_service import generate_fake_sensor_data
from app.database import get_session, SensorReading
LATEST_ESP32_DATA = None
logger = logging.getLogger("routes")
router = APIRouter()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")


# ── Schema pentru datele trimise de ESP32 ──────────────────────────────────

class ESP32Payload(BaseModel):
    field_id:    Optional[str]   = "field-001"
    luminosity:  Optional[float] = None
    humidity:    Optional[float] = None
    temperature: Optional[float] = None
    ph:          Optional[float] = None
    N:           Optional[float] = None
    P:           Optional[float] = None
    K:           Optional[float] = None
    EC:          Optional[float] = None
    nitrogen:    Optional[float] = None
    phosphorus:  Optional[float] = None
    potassium:   Optional[float] = None
    ec:          Optional[float] = None


# ── Helper: apel ML service ───────────────────────────────────────────────

def _call_ml(sensor_dict: dict) -> dict:
    """Apelează ml-service /predict și returnează predicția."""
    try:
        # Mapare strictă - asigură-te că orice valoare care lipsește devine un float default
        payload = {
            "field_id":    sensor_dict.get("field_id", "field-001"),
            "luminosity":  float(sensor_dict.get("luminosity") or 400.0),
            "N":           float(sensor_dict.get("N") or sensor_dict.get("nitrogen") or 100.0),
            "P":           float(sensor_dict.get("P") or sensor_dict.get("phosphorus") or 50.0),
            "K":           float(sensor_dict.get("K") or sensor_dict.get("potassium") or 120.0),
            "ph":          float(sensor_dict.get("ph") or 6.5),
            "EC":          float(sensor_dict.get("EC") or sensor_dict.get("ec") or 1.0),
            "humidity":    float(sensor_dict.get("humidity") or 55.0),
            "temperature": float(sensor_dict.get("temperature") or 22.0),
        }
        
        # Trimitem exact acest payload
        resp = requests.post(f"{ML_SERVICE_URL}/predict", json=payload, timeout=5)
        
        # Dacă eroarea persistă, logăm ce a plecat de la noi
        if resp.status_code == 422:
            logger.error(f"ML Service a respins payload-ul: {payload}")
            
        resp.raise_for_status()
        return resp.json()
        
    except Exception as e:
        logger.warning(f"ML service error: {e}")
        return {"error": "ML Unavailable"}


# ── Helper: salvare în PostgreSQL ─────────────────────────────────────────

async def _save_reading(
    db: AsyncSession,
    sensor: dict,
    prediction: dict = None,
    source: str = "simulated"
) -> SensorReading:
    """Salvează o citire (+ predicție opțională) în tabelul sensor_readings."""
    reading = SensorReading(
        field_id    = sensor.get("field_id"),
        source      = source,
        luminosity  = sensor.get("luminosity") or sensor.get("luminosity"),
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


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT-URI
# ══════════════════════════════════════════════════════════════════════════




@router.get("/sensor/history")
async def get_history(
    limit:    int = Query(default=50, le=500, description="Număr maxim de citiri"),
    field_id: Optional[str] = Query(default=None, description="Filtrare după field_id"),
    source:   Optional[str] = Query(default=None, description="esp32 | simulated"),
    db: AsyncSession = Depends(get_session)
):
    """
    Returnează ultimele `limit` citiri din PostgreSQL,
    ordonate descrescător după timestamp.
    """
    stmt = select(SensorReading).order_by(desc(SensorReading.timestamp)).limit(limit)
    if field_id:
        stmt = stmt.where(SensorReading.field_id == field_id)
    if source:
        stmt = stmt.where(SensorReading.source == source)

    result = await db.execute(stmt)
    readings = result.scalars().all()

    return [
        {
            "id":          r.id,
            "field_id":    r.field_id,
            "source":      r.source,
            "timestamp":   r.timestamp,
            "luminosity":  r.luminosity,
            "humidity":    r.humidity,
            "temperature": r.temperature,
            "ec":          r.ec,
            "ph":          r.ph,
            "nitrogen":    r.nitrogen,
            "phosphorus":  r.phosphorus,
            "potassium":   r.potassium,
            "soil_quality":     r.soil_quality,
            "recommended_crop": r.recommended_crop,
            "confidence":       r.confidence,
        }
        for r in readings
    ]

@router.post("/sensor/ingest")
async def ingest_esp32_data(payload: ESP32Payload, db: AsyncSession = Depends(get_session)):
    sensor_dict = payload.dict()

    # Normalizează: N→nitrogen, P→phosphorus, K→potassium, EC→ec
    sensor_dict["nitrogen"]   = sensor_dict.get("N")   or sensor_dict.get("nitrogen")
    sensor_dict["phosphorus"] = sensor_dict.get("P")   or sensor_dict.get("phosphorus")
    sensor_dict["potassium"]  = sensor_dict.get("K")   or sensor_dict.get("potassium")
    sensor_dict["ec"]         = sensor_dict.get("EC")  or sensor_dict.get("ec")

    reading = await _save_reading(db, sensor_dict, source="esp32")
    return {"status": "saved", "id": reading.id}

@router.get("/sensor/live")
def get_live_data():
    return generate_fake_sensor_data()


@router.get("/predict/live")
async def predict_live(db: AsyncSession = Depends(get_session)):
    stmt = (
        select(SensorReading)
        .where(SensorReading.source == "esp32")
        .order_by(desc(SensorReading.timestamp))
        .limit(1)
    )
    result = await db.execute(stmt)
    last_esp32 = result.scalar_one_or_none()

    if last_esp32:
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
        source = "esp32"
    else:
        sensor_data = generate_fake_sensor_data()
        source = "simulated"

    prediction = _call_ml(sensor_data)
    reading = await _save_reading(db, sensor_data, prediction, source=source)

    return {
        "sensor_data": sensor_data,
        "prediction":  prediction,
        "db_id":       reading.id,
    }