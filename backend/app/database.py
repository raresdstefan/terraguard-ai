"""
TerraGuard AI — PostgreSQL Database Layer
==========================================
Folosește SQLAlchemy + asyncpg pentru conexiunea la PostgreSQL.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Float, String, DateTime, Integer
from datetime import datetime, timezone

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://terraguard:terraguard@postgres:5432/terraguard"
)

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


class SensorReading(Base):
    """
    Tabel principal: stochează fiecare citire de la senzori.
    Poate veni fie de la ESP32 real, fie din simulare.
    """
    __tablename__ = "sensor_readings"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    field_id    = Column(String, nullable=True, index=True)
    source      = Column(String, default="simulated")  # "esp32" sau "simulated"

    # Senzor lumina (TSL2561 / I2C)
    luminosity  = Column(Float, nullable=True)

    # Senzor sol 7-in-1 (Modbus RS485)
    humidity    = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    ec          = Column(Float, nullable=True)   # Conductivitate (us/cm)
    ph          = Column(Float, nullable=True)
    nitrogen    = Column(Float, nullable=True)   # N mg/kg
    phosphorus  = Column(Float, nullable=True)   # P mg/kg
    potassium   = Column(Float, nullable=True)   # K mg/kg

    # Predicție ML (opțional — se completează după inference)
    soil_quality     = Column(String, nullable=True)
    recommended_crop = Column(String, nullable=True)
    confidence       = Column(String, nullable=True)

    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


async def init_db():
    """Creează tabelele dacă nu există."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency FastAPI pentru injectarea sesiunii DB."""
    async with AsyncSessionLocal() as session:
        yield session
