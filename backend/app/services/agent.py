import os
from google import genai
from app.models import VitalsRecord

def get_genai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def generate_triage_note(current_vitals: VitalsRecord, history: list[VitalsRecord]) -> str:
    """
    Sends the anomalous vitals and recent history to Gemini to generate
    an executive clinical triage report.
    """
    client = get_genai_client()
    if not client:
        return "[AI TRIAGE UNAVAILABLE: GEMINI_API_KEY environment variable not set]"

    # Format recent history rows into text for context
    history_summary = ""
    for rec in history[:5]:  # Look at the last 5 ticks
        history_summary += f"- HR: {rec.heart_rate}, BP: {rec.blood_pressure_sys}/{rec.blood_pressure_dia}, SpO2: {rec.spo2}%, Temp: {rec.temperature}°C\n"

    prompt = f"""
    You are an expert Clinical AI Safety Assistant monitoring post-operative patients.
    
    PATIENT ID: {current_vitals.patient_id}
    
    CURRENT ANOMALOUS READINGS:
    - Heart Rate: {current_vitals.heart_rate} bpm
    - Blood Pressure: {current_vitals.blood_pressure_sys}/{current_vitals.blood_pressure_dia} mmHg
    - SpO2: {current_vitals.spo2}%
    - Temperature: {current_vitals.temperature} °C
    
    RECENT HISTORICAL BASELINE (Last 5 Ticks):
    {history_summary if history_summary else "No prior history available."}
    
    TASK:
    Generate a concise clinical triage note (maximum 3 bullet points):
    1. Primary Clinical Risk (e.g., Acute Tachycardia, Hypotensive Shock Risk).
    2. Comparison against baseline trend.
    3. Recommended Immediate Action for bedside nursing staff.
    
    Keep the tone professional, direct, and clinical.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"[AI TRIAGE ERROR: Failed to generate note - {str(e)}]"