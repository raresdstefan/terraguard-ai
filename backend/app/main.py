from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.predictions import router as prediction_router

app = FastAPI(title="TerraGuard AI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)
app.include_router(prediction_router)

@app.get("/")
def root():
    return {
        "message": "TerraGuard AI Backend Running"
    }