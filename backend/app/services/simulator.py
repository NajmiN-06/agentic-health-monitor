import time
import random
import httpx

API_URL = "http://127.0.0.1:8000/api/vitals"
PATIENT_ID = "PATIENT-POSTOP-102"

def generate_vitals(is_anomaly: bool = False) -> dict:
    if not is_anomaly:
        return{
        "patient_id": PATIENT_ID,
            "heart_rate": round(random.gauss(72, 3), 1),        
            "blood_pressure_sys": round(random.gauss(118, 4), 1),
            "blood_pressure_dia": round(random.gauss(76, 3), 1), 
            "spo2": round(random.gauss(98, 0.5), 1),            
            "temperature": round(random.gauss(36.7, 0.1), 1)
    }
    else:

        return {
            "patient_id": PATIENT_ID,
            "heart_rate": round(random.gauss(138, 6), 1),       
            "blood_pressure_sys": round(random.gauss(82, 4), 1),
            "blood_pressure_dia": round(random.gauss(52, 3), 1),
            "spo2": round(random.gauss(87, 1.5), 1),           
            "temperature": round(random.gauss(39.1, 0.2), 1)   
        }

def start_stream(interval_seconds: int = 2, anomaly_interval: int = 8):
    """
    Streams live telemetry to the backend.
    Injects an anomaly every `anomaly_interval` ticks to simulate a sudden clinical event.
    """
    tick = 0
    with httpx.Client() as client:
        print(f"--- Starting Post-Op Telemetry Stream for {PATIENT_ID} ---")
        while True:
            tick += 1
            # Inject a sudden anomaly spike every 8th reading
            trigger_anomaly = (tick % anomaly_interval == 0)
            state_label = "CRITICAL_ANOMALY" if trigger_anomaly else "POSTOP_STABLE"
            
            vitals = generate_vitals(is_anomaly=trigger_anomaly)
            
            try:
                response = client.post(API_URL, json=vitals)
                print(f"[Tick {tick:02d}] State: {state_label} | Status: {response.status_code}")
            except Exception as e:
                print(f"[Tick {tick:02d}] Transmission Error: {e}")
                
            time.sleep(interval_seconds)

if __name__ == "__main__":
    start_stream()