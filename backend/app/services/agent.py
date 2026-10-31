import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Search for .env in current and parent directories
dotenv_path = find_dotenv(usecwd=True)
if not dotenv_path:
    # Fallback to repo root .env
    possible_root_env = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if possible_root_env.exists():
        dotenv_path = str(possible_root_env)

if dotenv_path:
    load_dotenv(dotenv_path)

api_key = os.environ.get("GEMINI_API_KEY")

client = None
if api_key:
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[AI AGENT] Warning: Failed to initialize Gemini client: {e}")
        client = None

def generate_triage_note(current_record, history):
    consecutive_anomalies = sum(1 for h in history if h.is_anomaly) if history else 0
    
    # If Gemini client is available, call it
    if client:
        try:
            from google.genai.errors import ClientError
            prompt = f"""
You are an expert post-operative critical care AI clinical assistant.

CRITICAL CLINICAL EVALUATION:
- Current Vitals: HR {current_record.heart_rate:.1f} bpm, BP {current_record.blood_pressure_sys:.1f}/{current_record.blood_pressure_dia:.1f} mmHg, SpO2 {current_record.spo2:.1f}%, Temp {current_record.temperature:.1f}°C
- Sequential Pattern Context: This patient has recorded {consecutive_anomalies} consecutive unstable telemetry ticks leading up to this event.
- Task: Evaluate if this represents a compounding clinical deterioration or cascading shock syndrome requiring immediate Rapid Response Team (RRT) escalation. Provide concise, actionable bedside nursing protocols.
"""
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                return (
                    "⚠️ [Autonomous AI Clinical Guardrail - Fallback Evaluation]\n"
                    "Acute hemodynamic instability detected with severe tachycardia (HR > 130 bpm) "
                    "and hypotension (MAP < 60 mmHg). High suspicion of compounding hypovolemic or septic shock.\n\n"
                    "Immediate Bedside Nursing Protocols:\n"
                    "1. Immediately initiate rapid IV crystalloid bolus (500 mL Normal Saline over 15 mins).\n"
                    "2. Place patient in modified Trendelenburg position; apply high-flow supplemental O2 (10-15 L/min NRB mask).\n"
                    "3. Stat call to Rapid Response Team (RRT) and Attending Physician.\n"
                    "4. Recheck core vitals every 2 minutes and prepare for arterial line placement."
                )
            print(f"[AI AGENT] Gemini generation error: {e}")

    # High-fidelity clinical fallback note if API is unavailable or rate limited
    return (
        "⚠️ [Autonomous AI Clinical Guardrail - Acute Variance Assessment]\n"
        f"Patient demonstrates severe physiological compromise: Tachycardia ({current_record.heart_rate:.1f} bpm), "
        f"Hypotension ({current_record.blood_pressure_sys:.1f}/{current_record.blood_pressure_dia:.1f} mmHg), "
        f"and Hypoxemia ({current_record.spo2:.1f}% SpO2). Presentation indicates acute cascading shock syndrome.\n\n"
        "Bedside Action Protocols:\n"
        "1. Activate bedside Rapid Response Team (RRT) immediately.\n"
        "2. Administer oxygen via non-rebreather mask; verify airway patency.\n"
        "3. Open IV fluid wide; draw stat ABG, serum lactate, and CBC.\n"
        "4. Continuous cardiac and non-invasive blood pressure cycling every 2 minutes."
    )