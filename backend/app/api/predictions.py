from fastapi import APIRouter
import requests

from app.services.sensor_service import generate_fake_sensor_data

router = APIRouter()

@router.get("/predict/live")
def predict_live():

    sensor_data = generate_fake_sensor_data()

    response = requests.post(
        "http://ml-service:8001/predict",
        json=sensor_data
    )

    prediction = response.json()

    return {
        "sensor_data": sensor_data,
        "prediction": prediction
    }