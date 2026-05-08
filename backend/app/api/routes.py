from fastapi import APIRouter
from app.services.sensor_service import generate_fake_sensor_data

router = APIRouter()

@router.get("/sensor/live")
def get_live_data():
    return generate_fake_sensor_data()