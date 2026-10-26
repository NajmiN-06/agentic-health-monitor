import time
import requests
import random

API_URL = "http://127.0.0.1:8000/api/vitals"
GATE_URL = "http://127.0.0.1:8000/api/simulation-gate/PATIENT-POSTOP-102"
PATIENT_ID = "PATIENT-POSTOP-102"

def wait_for_acknowledgment():
    """Pauses telemetry streaming if an unacknowledged clinical alert is active on the dashboard."""
    while True:
        try:
            res = requests.get(GATE_URL, timeout=2)
            if res.status_code == 200:
                data = res.json()
                if not data.get("pause", False):
                    break
                else:
                    print("⏸️ Clinical alert active. Simulator paused waiting for clinician dismissal...")
        except Exception as e:
            print(f"Gate check error: {e}")
        time.sleep(3)

def run_simulation():
    cycle = 0
    while True:
        cycle += 1
        print(f"\n--- Starting Monitoring Cycle {cycle} ---")
        
        # Phase 1: Send 7 stable normal ticks
        for t in range(1, 8):
            wait_for_acknowledgment()
            payload = {
                "patient_id": PATIENT_ID,
                "heart_rate": random.uniform(70.0, 80.0),
                "blood_pressure_sys": random.uniform(115.0, 125.0),
                "blood_pressure_dia": random.uniform(72.0, 80.0),
                "spo2": random.uniform(97.0, 99.0),
                "temperature": random.uniform(36.6, 37.0)
            }
            try:
                requests.post(API_URL, json=payload)
                print(f"Stable tick {t}/7 sent.")
            except Exception as e:
                print(f"Error sending stable tick: {e}")
            time.sleep(2.5)
            
        # Phase 2: Send consecutive escalating variance/anomaly ticks
        print("🚨 Triggering Acute Physiological Variance Sequence...")
        for variance_tick in range(1, 4):
            wait_for_acknowledgment()
            payload = {
                "patient_id": PATIENT_ID,
                "heart_rate": random.uniform(130.0 + variance_tick * 3, 145.0),
                "blood_pressure_sys": random.uniform(80.0 - variance_tick * 5, 85.0),
                "blood_pressure_dia": random.uniform(48.0, 55.0),
                "spo2": random.uniform(84.0 - variance_tick * 2, 88.0),
                "temperature": random.uniform(38.5, 39.4)
            }
            try:
                requests.post(API_URL, json=payload)
                print(f"Variance escalation tick {variance_tick}/3 sent.")
            except Exception as e:
                print(f"Error sending variance tick: {e}")
            time.sleep(2.5)

if __name__ == "__main__":
    run_simulation()