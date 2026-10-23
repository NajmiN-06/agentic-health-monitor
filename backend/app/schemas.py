from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class VitalsPayload(BaseModel):
    patient_id: str = Field(..., example="PATIENT-POSTOP-102")
    heart_rate: float = Field(..., ge=30, le=220, description="Heart rate in BPM")
    blood_pressure_sys: float = Field(..., ge=50, le=250, description="Systolic BP in mmHg")
    blood_pressure_dia: float = Field(..., ge=30, le=150, description="Diastolic BP in mmHg")
    spo2: float = Field(..., ge=50, le=100, description="Blood oxygen saturation percentage")
    temperature: float = Field(..., ge=30.0, le=45.0, description="Body temperature in Celsius")

class VitalsResponse(BaseModel):
    status: str
    record_id: int
    patient_id: str
    is_anomaly: bool
    anomaly_score: float    
    triage_note: Optional[str] = None