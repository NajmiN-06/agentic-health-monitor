import time
import requests
import random

API_URL = "http://127.0.0.1:8000/api/vitals"
GATE_URL = "http://127.0.0.1:8000/api/simulation-gate/PATIENT-POSTOP-102"
PATIENT_ID = "PATIENT-POSTOP-102"

def wait_for_acknowledgment():
    """Pauses telemetry streaming if an unacknowledged clinical alert is active on the dashboard."""
    # Give the backend a brief moment to ingest the anomaly before polling
    time.sleep(0.5)
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
        time.sleep(1)

def run_simulation():
    cycle = 0
    while True:
        cycle += 1
        print(f"\n==========================================")
        print(f"  Starting Clinical Telemetry Cycle {cycle}")
        print(f"==========================================")
        
        # Phase 1: Send 7 stable normal ticks
        print(f"🩺 [Cycle {cycle}] Phase 1: Streaming Normal Baseline Vitals...")
        for t in range(1, 8):
            wait_for_acknowledgment()
            payload = {
                "patient_id": PATIENT_ID,
                "heart_rate": round(random.uniform(70.0, 78.0), 1),
                "blood_pressure_sys": round(random.uniform(116.0, 122.0), 1),
                "blood_pressure_dia": round(random.uniform(74.0, 78.0), 1),
                "spo2": round(random.uniform(97.5, 99.0), 1),
                "temperature": round(random.uniform(36.6, 36.9), 1)
            }
            try:
                requests.post(API_URL, json=payload, timeout=3)
                print(f"  -> Stable tick {t}/7 sent. HR: {payload['heart_rate']} | BP: {payload['blood_pressure_sys']}/{payload['blood_pressure_dia']}")
            except Exception as e:
                print(f"Error sending stable tick: {e}")
            time.sleep(2.5)
            
        # Phase 2: Trigger Acute Physiological Variance Sequence
        print(f"\n🚨 [Cycle {cycle}] Phase 2: Triggering Acute Physiological Variance / Escalation...")
        payload = {
            "patient_id": PATIENT_ID,
            "heart_rate": round(random.uniform(134.0, 142.0), 1),
            "blood_pressure_sys": round(random.uniform(74.0, 80.0), 1),
            "blood_pressure_dia": round(random.uniform(46.0, 52.0), 1),
            "spo2": round(random.uniform(84.0, 87.0), 1),
            "temperature": round(random.uniform(38.6, 39.2), 1)
        }
        try:
            requests.post(API_URL, json=payload, timeout=5)
            print(f"  🚨 Acute variance anomaly sent! HR: {payload['heart_rate']} | BP: {payload['blood_pressure_sys']}/{payload['blood_pressure_dia']}")
            print("  ⏳ Telemetry paused at bedside. Waiting for clinician acknowledgment on dashboard...")
        except Exception as e:
            print(f"Error sending variance tick: {e}")

        # Wait until clinician acknowledges and dismisses on the dashboard
        wait_for_acknowledgment()
        print(f"✅ Alert acknowledged and dismissed by clinician!")
        print(f"🔄 Resetting physiological baseline. Initiating new normal vital cycle...\n")
        time.sleep(1.0)

if __name__ == "__main__":
    run_simulation()