from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

# This model defines the database table structure for storing incoming vitals
class VitalsRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    heart_rate: float
    blood_pressure_sys: float
    blood_pressure_dia: float
    spo2: float
    temperature: float
    is_anomaly: bool = Field(default=False)
    anomaly_score: float = Field(default=0.0)
    triage_note: Optional[str] = Field(default=None)    