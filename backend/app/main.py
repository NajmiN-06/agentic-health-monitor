from fastapi import FastAPI, status, Depends
from sqlmodel import Session, select
from typing import List
from dotenv import load_dotenv; load_dotenv()

from app.schemas import VitalsPayload, VitalsResponse
from app.models import VitalsRecord
from app.database import create_db_and_tables, get_session
from app.services.anomaly import anomaly_detector
from app.services.agent import generate_triage_note

app = FastAPI(
    title="Post-Op Telemetry Ingestion API",
    description="Full Agentic Clinical Guardrail Pipeline."
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def health_check():
    return {"status": "online", "system": "PostOp-Telemetry-Agentic-V2"}

# 1. Ingestion Pipeline: ML Score -> Conditional AI Triage -> DB Persistence
@app.post("/api/vitals", response_model=VitalsResponse, status_code=status.HTTP_201_CREATED)
def receive_vitals(payload: VitalsPayload, session: Session = Depends(get_session)):
    # Step A: Run ML Anomaly Detection
    is_anomaly, anomaly_score = anomaly_detector.predict(payload)
    
    triage_note = None
    
    # Step B: Trigger Agentic AI ONLY if an anomaly is detected
    if is_anomaly:
        # Fetch last 5 patient records for historical context & pattern tracking
        history_stmt = (
            select(VitalsRecord)
            .where(VitalsRecord.patient_id == payload.patient_id)
            .order_by(VitalsRecord.id.desc())
            .limit(5)
        )
        history = session.exec(history_stmt).all()
        
        # Build temp record object to pass to the agent prompt
        temp_record = VitalsRecord(**payload.model_dump())
        triage_note = generate_triage_note(temp_record, history)
        
        print(f"\n🚨 [CRITICAL ANOMALY ALERT] Patient: {payload.patient_id}")
        print(f"AI Triage Generated:\n{triage_note}\n")
    else:
        print(f"✅ [NORMAL] Patient: {payload.patient_id} | Score: {anomaly_score}")

    # Step C: Save enriched record to SQLite
    db_record = VitalsRecord(
        patient_id=payload.patient_id,
        heart_rate=payload.heart_rate,
        blood_pressure_sys=payload.blood_pressure_sys,
        blood_pressure_dia=payload.blood_pressure_dia,
        spo2=payload.spo2,
        temperature=payload.temperature,
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        triage_note=triage_note,
        acknowledged=False
    )
    
    session.add(db_record)
    session.commit()
    session.refresh(db_record)
    
    return VitalsResponse(
        status="acknowledged",
        record_id=db_record.id,
        patient_id=db_record.patient_id,
        is_anomaly=db_record.is_anomaly,
        anomaly_score=db_record.anomaly_score,
        triage_note=db_record.triage_note
    )

# 2. Get Recent Patient History (Chronological Order for Live Stream & Charts)
@app.get("/api/vitals/{patient_id}", response_model=List[VitalsRecord])
def get_patient_history(patient_id: str, limit: int = 30, session: Session = Depends(get_session)):
    statement = (
        select(VitalsRecord)
        .where(VitalsRecord.patient_id == patient_id)
        .order_by(VitalsRecord.id.desc())
        .limit(limit)
    )
    results = session.exec(statement).all()
    # Reverse list so chronological order flows left-to-right and latest tick is at index -1
    return results[::-1]

# 3. Get Active Critical Alerts Endpoint
@app.get("/api/alerts/{patient_id}", response_model=List[VitalsRecord])
def get_patient_alerts(patient_id: str, limit: int = 10, session: Session = Depends(get_session)):
    statement = (
        select(VitalsRecord)
        .where(VitalsRecord.patient_id == patient_id)
        .where(VitalsRecord.is_anomaly == True)
        .order_by(VitalsRecord.id.desc())
        .limit(limit)
    )
    return session.exec(statement).all()

# 4. Check if simulator should pause
@app.get("/api/simulation-gate/{patient_id}")
def check_simulation_gate(patient_id: str, session: Session = Depends(get_session)):
    statement = (
        select(VitalsRecord)
        .where(VitalsRecord.patient_id == patient_id)
        .where(VitalsRecord.is_anomaly == True)
        .where(VitalsRecord.acknowledged == False)
    )
    unacked = session.exec(statement).first()
    return {"pause": unacked is not None}

# 5. Acknowledge/Dismiss endpoint triggered by Streamlit dashboard
@app.post("/api/acknowledge/{patient_id}")
def acknowledge_alerts(patient_id: str, session: Session = Depends(get_session)):
    statement = (
        select(VitalsRecord)
        .where(VitalsRecord.patient_id == patient_id)
        .where(VitalsRecord.is_anomaly == True)
        .where(VitalsRecord.acknowledged == False)
    )
    records = session.exec(statement).all()
    for r in records:
        r.acknowledged = True
        session.add(r)
    session.commit()
    return {"status": "success", "acknowledged_count": len(records)}

# 6. Optional: Trigger variance directly on demand for demo/testing
@app.post("/api/trigger-variance/{patient_id}")
def trigger_variance(patient_id: str, session: Session = Depends(get_session)):
    payload = VitalsPayload(
        patient_id=patient_id,
        heart_rate=136.5,
        blood_pressure_sys=76.0,
        blood_pressure_dia=48.5,
        spo2=85.2,
        temperature=38.8
    )
    return receive_vitals(payload, session)

# 7. Optional: Reset telemetry history to start clean
@app.post("/api/reset/{patient_id}")
def reset_patient_telemetry(patient_id: str, session: Session = Depends(get_session)):
    statement = select(VitalsRecord).where(VitalsRecord.patient_id == patient_id)
    records = session.exec(statement).all()
    for r in records:
        session.delete(r)
    session.commit()
    return {"status": "success", "deleted_count": len(records)}