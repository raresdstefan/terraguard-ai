/**
 * TerraGuard AI — ESP32 Firmware
 * ================================
 * Citește:
 *   - Senzor sol 7-in-1 (NPK + pH + EC + Umiditate + Temperatură) via Modbus RS485
 *   - Senzor lumină TSL2561 via I2C
 *
 * Trimite datele:
 *   - Serial (USB) — pentru debugging și modul "serial" din backend
 *   - HTTP POST la backend TerraGuard — pentru modul "http" din backend
 *
 * CONFIGURARE: editează secțiunea "USER CONFIG" de mai jos.
 */

#include <Arduino.h>
#include <Wire.h>
#include <ModbusMaster.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_TSL2561_U.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ═══════════════════════════════════════════════════════════════
// USER CONFIG — modifică aceste valori
// ═══════════════════════════════════════════════════════════════

// WiFi
const char* WIFI_SSID     = "NumeleReteleiTale";
const char* WIFI_PASSWORD = "ParolaWifi";

// Backend TerraGuard
// Dacă rulezi Docker pe același PC: http://IP_PC:8000/sensor/ingest
// Dacă vrei și predicție ML: http://IP_PC:8000/predict/ingest
const char* BACKEND_URL   = "http://192.168.1.100:8000/sensor/ingest";

// Identificator câmp
const char* FIELD_ID      = "field-001";

// Interval între citiri (ms)
const unsigned long READ_INTERVAL = 10000;  // 10 secunde

// ═══════════════════════════════════════════════════════════════
// PINOUT
// ═══════════════════════════════════════════════════════════════

#define MAX485_RE_NEG  4
#define RX_PIN        16
#define TX_PIN        17
#define I2C_SDA_PIN   25
#define I2C_SCL_PIN   26

// ═══════════════════════════════════════════════════════════════
// OBIECTE GLOBALE
// ═══════════════════════════════════════════════════════════════

ModbusMaster node;
Adafruit_TSL2561_Unified tsl = Adafruit_TSL2561_Unified(TSL2561_ADDR_FLOAT, 12345);

bool wifiOK   = false;
bool tslOK    = false;

unsigned long lastReadTime = 0;

// ── RS485 callbacks ──────────────────────────────────────────
void preTransmission()  { digitalWrite(MAX485_RE_NEG, HIGH); }
void postTransmission() { digitalWrite(MAX485_RE_NEG, LOW);  }

// ═══════════════════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════════════════

void setup() {
  Serial.begin(115200);
  Serial.println("\n--- Initializare TerraGuard AI ---");

  // RS485 / Modbus
  pinMode(MAX485_RE_NEG, OUTPUT);
  digitalWrite(MAX485_RE_NEG, LOW);
  Serial2.begin(4800, SERIAL_8N1, RX_PIN, TX_PIN);
  node.begin(1, Serial2);
  node.preTransmission(preTransmission);
  node.postTransmission(postTransmission);
  Serial.println("-> Modbus RTU (Senzor Sol) ... OK");

  // I2C / TSL2561
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  if (!tsl.begin()) {
    Serial.println("-> EROARE: TSL2561 negasit! Verificati pinii SDA/SCL.");
    tslOK = false;
  } else {
    tsl.enableAutoRange(true);
    tsl.setIntegrationTime(TSL2561_INTEGRATIONTIME_101MS);
    Serial.println("-> TSL2561 (Lumina I2C) ... OK");
    tslOK = true;
  }

  // WiFi
  Serial.print("-> Conectare WiFi la ");
  Serial.print(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" OK");
    Serial.print("   IP: "); Serial.println(WiFi.localIP());
    wifiOK = true;
  } else {
    Serial.println(" FAIL — datele vor fi trimise doar pe Serial.");
    wifiOK = false;
  }

  Serial.println("Sistem pornit!\n");
  delay(2000);
}

// ═══════════════════════════════════════════════════════════════
// CITIRE SENZORI
// ═══════════════════════════════════════════════════════════════

struct SensorData {
  bool  soilOK = false;
  float humidity    = 0, temperature = 0, ec  = 0;
  float ph          = 0, nitrogen    = 0;
  float phosphorus  = 0, potassium   = 0;

  bool  luxOK = false;
  float luminosity = 0;
};

SensorData readSensors() {
  SensorData d;

  // ── Sol (Modbus) ──────────────────────────────────────────
  uint8_t result = node.readHoldingRegisters(0x0000, 7);
  if (result == node.ku8MBSuccess) {
    d.soilOK      = true;
    d.humidity    = node.getResponseBuffer(0) / 10.0f;
    d.temperature = node.getResponseBuffer(1) / 10.0f;
    d.ec          = node.getResponseBuffer(2);           // us/cm
    d.ph          = node.getResponseBuffer(3) / 10.0f;
    d.nitrogen    = node.getResponseBuffer(4);
    d.phosphorus  = node.getResponseBuffer(5);
    d.potassium   = node.getResponseBuffer(6);
  }

  // ── Lumina (I2C) ─────────────────────────────────────────
  if (tslOK) {
    sensors_event_t event;
    tsl.getEvent(&event);
    if (event.light) {
      d.luxOK      = true;
      d.luminosity = event.light;
    }
  }

  return d;
}

// ═══════════════════════════════════════════════════════════════
// PRINT SERIAL (format text — compatibil cu parser-ul din backend)
// ═══════════════════════════════════════════════════════════════

void printSerial(const SensorData& d) {
  Serial.println("=====================================");

  if (d.soilOK) {
    Serial.println("[PARAMETRI SOL]");
    Serial.print("Umiditate:    ");    Serial.print(d.humidity);    Serial.println(" %");
    Serial.print("Temperatura:  ");   Serial.print(d.temperature);  Serial.println(" C");
    Serial.print("Conductivitate: "); Serial.print(d.ec);            Serial.println(" us/cm");
    Serial.print("pH:           ");   Serial.println(d.ph);
    Serial.print("Azot (N):     ");   Serial.print(d.nitrogen);     Serial.println(" mg/kg");
    Serial.print("Fosfor (P):   ");   Serial.print(d.phosphorus);   Serial.println(" mg/kg");
    Serial.print("Potasiu (K):  ");   Serial.print(d.potassium);    Serial.println(" mg/kg");
  } else {
    Serial.println("[PARAMETRI SOL] Eroare Modbus.");
  }

  Serial.println("-------------------------------------");

  if (d.luxOK) {
    Serial.println("[MEDIU EXTERN]");
    Serial.print("Lumina:       "); Serial.print(d.luminosity); Serial.println(" lux");
  } else {
    Serial.println("[MEDIU EXTERN] Senzor lumina indisponibil.");
  }

  Serial.println("=====================================\n");
}

// ═══════════════════════════════════════════════════════════════
// TRIMITERE HTTP POST LA BACKEND
// ═══════════════════════════════════════════════════════════════

void sendHTTP(const SensorData& d) {
  if (!wifiOK || WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] WiFi deconectat, skip.");
    return;
  }

  // Construiește JSON-ul
  StaticJsonDocument<384> doc;
  doc["field_id"] = FIELD_ID;

  if (d.soilOK) {
    doc["humidity"]    = d.humidity;
    doc["temperature"] = d.temperature;
    doc["ec"]          = d.ec;
    doc["ph"]          = d.ph;
    doc["nitrogen"]    = d.nitrogen;
    doc["phosphorus"]  = d.phosphorus;
    doc["potassium"]   = d.potassium;
  }
  if (d.luxOK) {
    doc["luminosity"] = d.luminosity;
  }

  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(BACKEND_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(8000);

  int httpCode = http.POST(body);
  if (httpCode == 200 || httpCode == 201) {
    Serial.print("[HTTP] Trimis OK → "); Serial.println(http.getString());
  } else {
    Serial.print("[HTTP] Eroare: "); Serial.println(httpCode);
  }
  http.end();
}

// ═══════════════════════════════════════════════════════════════
// LOOP
// ═══════════════════════════════════════════════════════════════

void loop() {
  unsigned long now = millis();
  if (now - lastReadTime < READ_INTERVAL) return;
  lastReadTime = now;

  SensorData data = readSensors();
  printSerial(data);   // Mereu pe Serial (pentru debugging)
  sendHTTP(data);      // HTTP POST la backend (dacă WiFi disponibil)
}
