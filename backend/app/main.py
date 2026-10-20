from fastapi import FastAPI, status, Depends
from sqlmodel import Session, select
from typing import List

from app.schemas import VitalsPayload
from app.models import VitalsRecord
from app.database import create_db_and_tables, get_session

# Initialize FastAPI application
app = FastAPI(
    title="Post-Op Telemetry Ingestion API",
    description="Agnostic ingestion endpoint for real-time patient recovery vitals."
)

# Initialize database tables on server startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# 1. Health Check Endpoint
@app.get("/")
def health_check():
    return {"status": "online", "system": "PostOp-Telemetry-V1"}

# 2. Ingestion Endpoint (Validates payload AND saves to SQLite)
@app.post("/api/vitals", status_code=status.HTTP_201_CREATED)
def receive_vitals(payload: VitalsPayload, session: Session = Depends(get_session)):
    # Convert validated schema payload into a Database Record
    db_record = VitalsRecord(
        patient_id=payload.patient_id,
        heart_rate=payload.heart_rate,
        blood_pressure_sys=payload.blood_pressure_sys,
        blood_pressure_dia=payload.blood_pressure_dia,
        spo2=payload.spo2,
        temperature=payload.temperature
    )
    
    # Persist record into SQLite database
    session.add(db_record)
    session.commit()
    session.refresh(db_record)
    
    print(
        f"[SAVED TO DB] Record ID: {db_record.id} | Patient: {db_record.patient_id} | "
        f"HR: {db_record.heart_rate} | SpO2: {db_record.spo2}%"
    )
    
    return {
        "status": "acknowledged",
        "record_id": db_record.id,
        "patient_id": db_record.patient_id
    }

# 3. Retrieval Endpoint (Fetches recent vitals history for dashboard/ML)
@app.get("/api/vitals/{patient_id}", response_model=List[VitalsRecord])
def get_patient_history(
    patient_id: str, 
    limit: int = 20, 
    session: Session = Depends(get_session)
):
    # Query database for the latest readings for a given patient
    statement = (
        select(VitalsRecord)
        .where(VitalsRecord.patient_id == patient_id)
        .order_by(VitalsRecord.id.desc())
        .limit(limit)
    )
    results = session.exec(statement).all()
    return results