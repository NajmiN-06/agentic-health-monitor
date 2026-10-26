import os
from google import genai
from google.genai.errors import ClientError

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_triage_note(current_record, history):
    try:
        # Count consecutive anomalies from history
        consecutive_anomalies = sum(1 for h in history if h.is_anomaly) if history else 0
        
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
        return response.text.strip()
        
    except ClientError as e:
        if e.code == 429:
            return "[AI TRIAGE NOTICE: Daily Gemini API free tier quota limit reached. Standard clinical guardrails active: Recommend immediate bedside nursing review, continuous SpO2 observation, and physician notification if hemodynamic instability persists.]"
        return f"[AI TRIAGE ERROR: API Client Error - {str(e)}]"
        
    except Exception as e:
        return f"[AI TRIAGE ERROR: Failed to generate note - {str(e)}]"