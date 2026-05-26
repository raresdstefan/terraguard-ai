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

logger = logging.getLogger("routes")
router = APIRouter()

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")


# ── Schema pentru datele trimise de ESP32 ──────────────────────────────────

class ESP32Payload(BaseModel):
    """
    Structura JSON pe care ESP32-ul tău o trimite prin HTTP POST.
    Toate câmpurile sunt opționale — dacă lipsesc, rămân NULL în DB.
    """
    field_id:    Optional[str]   = "field-001"
    # Senzor lumină (TSL2561)
    luminosity:  Optional[float] = None
    # Senzor sol 7-in-1 (Modbus)
    humidity:    Optional[float] = None
    temperature: Optional[float] = None
    ec:          Optional[float] = None   # Conductivitate — în Arduino e "Conductivitate"
    ph:          Optional[float] = None
    nitrogen:    Optional[float] = None   # N
    phosphorus:  Optional[float] = None   # P
    potassium:   Optional[float] = None   # K


# ── Helper: apel ML service ───────────────────────────────────────────────

def _call_ml(sensor_dict: dict) -> dict:
    """Apelează ml-service /predict și returnează predicția."""
    try:
        # Mapăm cheile interne pe schema ml-service (N, P, K, EC, ph)
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

@router.get("/sensor/live")
def get_live_data():
    """Returnează o citire simulată (fără ML, fără DB)."""
    return generate_fake_sensor_data()


@router.post("/sensor/ingest")
async def ingest_esp32_data(
    payload: ESP32Payload,
    db: AsyncSession = Depends(get_session)
):
    """
    ESP32-ul face POST la acest endpoint cu citirile senzorilor.
    Datele sunt salvate în PostgreSQL.

    Cod Arduino pentru a trimite datele (adaugă în loop()):
    ─────────────────────────────────────────────────────────
    #include <HTTPClient.h>
    #include <ArduinoJson.h>

    void sendToBackend(float hum, float temp, float ec, float ph,
                       float n, float p, float k, float lux) {
      HTTPClient http;
      http.begin("http://IP_SERVER:8000/sensor/ingest");
      http.addHeader("Content-Type", "application/json");

      StaticJsonDocument<256> doc;
      doc["field_id"]    = "field-001";
      doc["humidity"]    = hum;
      doc["temperature"] = temp;
      doc["ec"]          = ec;
      doc["ph"]          = ph;
      doc["nitrogen"]    = n;
      doc["phosphorus"]  = p;
      doc["potassium"]   = k;
      doc["luminosity"]  = lux;

      String body;
      serializeJson(doc, body);
      http.POST(body);
      http.end();
    }
    ─────────────────────────────────────────────────────────
    """
    sensor_dict = payload.dict()
    reading = await _save_reading(db, sensor_dict, source="esp32")
    return {"status": "saved", "id": reading.id, "timestamp": reading.timestamp}


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
