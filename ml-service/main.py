from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from inference.predictor import predict_soil_quality

app = FastAPI(title="TerraGuard ML Service")


class SensorData(BaseModel):
    field_id:    Optional[str]   = "field-001"
    # Luminosity sensor
    luminosity:  float           = 400.0
    # 7-in-1 soil sensor
    N:           float           = 100.0
    P:           float           = 50.0
    K:           float           = 120.0
    ph:          float           = 6.5
    EC:          float           = 1.0
    humidity:    float           = 55.0
    temperature: float           = 22.0


@app.post("/predict")
def predict(data: SensorData):
    result = predict_soil_quality(data.dict())
    return result


@app.get("/health")
def health():
    return {"status": "ok"}