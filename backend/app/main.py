from fastapi import FastAPI
from app.api.routes import router
from app.consumers.sensor_consumer import start_consumer
import threading

app = FastAPI(title="TerraGuard AI")

app.include_router(router)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=start_consumer)
    thread.daemon = True
    thread.start()

@app.get("/")
def root():
    return {"message": "TerraGuard AI Backend Running"}