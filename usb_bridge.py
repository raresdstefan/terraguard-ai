import serial
import json
import requests
import time

# --- CONFIGURARE ---
SERIAL_PORT = 'COM3'  
BAUD_RATE = 115200
# Endpoint-ul FastAPI din Docker
BACKEND_URL = 'http://localhost:8000/sensor/ingest' 
def start_bridge():
    try:
        # Ne conectam la cablul USB
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        print(f"[*] Conectat la {SERIAL_PORT}. Se asteapta date de la ESP32...")

        while True:
            if ser.in_waiting > 0:
                # Citim linia venita pe cablu
                line = ser.readline().decode('utf-8').strip()
                
                # Verificam daca pare a fi un JSON
                if line.startswith('{') and line.endswith('}'):
                    print(f"\n[USB] Date receptionate: {line}")
                    
                    try:
                        # Parsam si trimitem prin HTTP POST catre Docker (localhost nu e blocat de firewall!)
                        payload = json.loads(line)
                        response = requests.post(BACKEND_URL, json=payload, timeout=5)
                        print(f"[HTTP] Trimis la backend! Cod raspuns: {response.status_code}")
                    except json.JSONDecodeError:
                        print("[Eroare] JSON invalid primit pe USB.")
                    except requests.exceptions.RequestException as e:
                        print(f"[Eroare HTTP] Nu s-a putut trimite la server: {e}")

            time.sleep(0.1)

    except serial.SerialException as e:
        print(f"[Eroare] Nu se poate deschide portul {SERIAL_PORT}.")
        print("Asigura-te ca portul este corect si ca ai INCHIS Serial Monitor din Arduino IDE!")

if __name__ == "__main__":
    start_bridge()