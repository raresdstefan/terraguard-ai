"""
TerraGuard AI — ESP32 Serial/HTTP Bridge
=========================================
Două moduri de a primi date de la ESP32:

  1. HTTP (recomandat pentru producție):
     ESP32 face POST la /sensor/ingest cu JSON-ul citirilor.
     Activează cu: ESP32_MODE=http

  2. Serial USB (pentru debugging local):
     Backend-ul citește de pe portul serial /dev/ttyUSB0 sau COM3.
     Activează cu: ESP32_MODE=serial

Formatul JSON așteptat de la ESP32:
  {
    "field_id": "field-001",
    "humidity": 55.3,
    "temperature": 22.1,
    "ec": 1200,
    "ph": 6.8,
    "nitrogen": 145,
    "phosphorus": 52,
    "potassium": 178,
    "luminosity": 620.0
  }
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any

logger = logging.getLogger("esp32_service")

ESP32_MODE   = os.getenv("ESP32_MODE", "simulated")   # "http" | "serial" | "simulated"
SERIAL_PORT  = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")
SERIAL_BAUD  = int(os.getenv("SERIAL_BAUD", "115200"))


# ──────────────────────────────────────────────────────────────────────────
# Parser pentru output-ul Serial al ESP32
# Parsează formatul text din codul tău Arduino:
#   Umiditate:    55.3 %
#   Temperatura:  22.1 C
#   etc.
# ──────────────────────────────────────────────────────────────────────────

def parse_esp32_serial_output(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Parsează un bloc de text Serial de la ESP32 și returnează un dict
    cu valorile senzorilor, sau None dacă blocul e incomplet.

    ESP32-ul tău printează un bloc la fiecare 3 secunde delimitat de:
      =====================================
      [PARAMETRI SOL]
      ...
      [MEDIU EXTERN]
      Lumina: xxx lux
      =====================================
    """
    data: Dict[str, Any] = {}

    for line in raw_text.splitlines():
        line = line.strip()
        try:
            if line.startswith("Umiditate:"):
                data["humidity"]    = float(line.split(":")[1].strip().split()[0])
            elif line.startswith("Temperatura:"):
                data["temperature"] = float(line.split(":")[1].strip().split()[0])
            elif line.startswith("Conductivitate:"):
                data["ec"]          = float(line.split(":")[1].strip().split()[0])
            elif line.startswith("pH:"):
                data["ph"]          = float(line.split(":")[1].strip())
            elif line.startswith("Azot (N):"):
                data["nitrogen"]    = float(line.split(":")[1].strip().split()[0])
            elif line.startswith("Fosfor (P):"):
                data["phosphorus"]  = float(line.split(":")[1].strip().split()[0])
            elif line.startswith("Potasiu (K):"):
                data["potassium"]   = float(line.split(":")[1].strip().split()[0])
            elif line.startswith("Lumina:"):
                data["luminosity"]  = float(line.split(":")[1].strip().split()[0])
        except (ValueError, IndexError):
            continue

    # Verificăm că am primit cel puțin parametrii de sol
    required = {"humidity", "temperature", "ph", "nitrogen", "phosphorus", "potassium"}
    if not required.issubset(data.keys()):
        return None

    data.setdefault("luminosity", None)
    data.setdefault("ec", None)
    data["source"] = "esp32_serial"
    return data


async def read_from_serial_async():
    """
    Generator async care citește continuu de pe portul serial
    și yield-uiește dict-uri cu date de senzori.

    Necesită: pip install pyserial
    """
    try:
        import serial
        import serial.tools.list_ports
    except ImportError:
        logger.error("pyserial nu e instalat. Rulează: pip install pyserial")
        return

    logger.info(f"Conectare la serial {SERIAL_PORT} @ {SERIAL_BAUD} baud...")

    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=2)
    except serial.SerialException as e:
        logger.error(f"Nu pot deschide portul serial: {e}")
        return

    buffer = ""
    in_block = False

    while True:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                await asyncio.sleep(0.05)
                continue

            if "=====" in line and not in_block:
                in_block = True
                buffer = ""
                continue

            if "=====" in line and in_block:
                in_block = False
                parsed = parse_esp32_serial_output(buffer)
                if parsed:
                    yield parsed
                buffer = ""
                continue

            if in_block:
                buffer += line + "\n"

        except serial.SerialException as e:
            logger.error(f"Eroare serial: {e}")
            await asyncio.sleep(5)
