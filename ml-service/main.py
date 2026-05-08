from fastapi import FastAPI
from pydantic import BaseModel
from inference.predictor import predict_soil_quality

app = FastAPI(title="ML Service")

class SensorData(BaseModel):
    humidity: float
    ph: float
    light: int

@app.post("/predict")
def predict(data: SensorData):
    result = predict_soil_quality(data.dict())
    return result