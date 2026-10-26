import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time

st.set_page_config(
    page_title="Clinical Telemetry & AI Triage Monitor",
    layout="wide"
)

API_BASE_URL = "http://127.0.0.1:8000"

# Initialize local session state for instant UI dismissal using alert IDs
if 'dismissed_alert_ids' not in st.session_state:
    st.session_state.dismissed_alert_ids = set()

st.sidebar.title("Telemetry Controls")
patient_id = st.sidebar.text_input("Patient ID", value="PATIENT-POSTOP-102")
auto_refresh = st.sidebar.checkbox("Enable Live Stream", value=True)
refresh_rate = st.sidebar.slider("Refresh Interval (Seconds)", 2, 10, 3)

st.title("Post-Operative Patient Telemetry & Clinical Intelligence")
st.markdown(f"**Active Stream Identifier:** `{patient_id}` | **System Status:** Operational")
st.markdown("---")

def fetch_patient_history(pat_id):
    try:
        response = requests.get(f"{API_BASE_URL}/api/vitals/{pat_id}?limit=30", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data:
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df.sort_values('timestamp')
    except Exception:
        pass
    return pd.DataFrame()

def fetch_patient_alerts(pat_id):
    try:
        response = requests.get(f"{API_BASE_URL}/api/alerts/{pat_id}?limit=10", timeout=3)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

df = fetch_patient_history(patient_id)
alerts_data = fetch_patient_alerts(patient_id)

if df.empty:
    st.warning(f"No telemetry data found for patient `{patient_id}`. Verify that the simulator service is running.")
else:
    latest = df.iloc[-1]

    # Prune dismissed IDs that the backend has already acknowledged (keeps the set small)
    backend_acked_ids = {a['id'] for a in alerts_data if a.get('acknowledged', False)}
    st.session_state.dismissed_alert_ids -= backend_acked_ids

    # Find alerts that are unacked on the backend AND not locally dismissed
    unacked_alerts = [
        a for a in alerts_data
        if not a.get('acknowledged', False) and a['id'] not in st.session_state.dismissed_alert_ids
    ]
    has_active_alert = len(unacked_alerts) > 0

    show_alert_banner = has_active_alert

    # --- 1. SAFETY ALERT BANNER ---
    if show_alert_banner:
        current_alert = unacked_alerts[0]
        alert_id = current_alert['id']
        alert_ts = str(current_alert.get('timestamp'))

        st.error("CRITICAL CLINICAL ALERT: ACUTE PHYSIOLOGICAL VARIANCE / ESCALATION DETECTED")

        col_alert_1, col_alert_2 = st.columns([1, 2])
        with col_alert_1:
            st.markdown("**Triggering Measurement Snapshot:**")
            st.text(f"Timestamp: {alert_ts}\nHeart Rate: {current_alert['heart_rate']:.1f} bpm\nBlood Pressure: {current_alert['blood_pressure_sys']:.1f}/{current_alert['blood_pressure_dia']:.1f} mmHg\nSpO2: {current_alert['spo2']:.1f}%\nTemperature: {current_alert['temperature']:.1f} °C")
        with col_alert_2:
            st.markdown("**Autonomous AI Triage Assessment & Sequential Pattern Report:**")
            triage_val = current_alert.get('triage_note')
            triage_text = str(triage_val) if triage_val is not None and pd.notna(triage_val) else "Standard clinical guardrails active: Recommend immediate bedside nursing review and physician notification."
            st.info(triage_text)

            if st.button("Acknowledge & Dismiss Alert", key=f"dismiss_alert_{alert_id}", type="primary"):
                # Immediately mark this specific alert as locally dismissed
                st.session_state.dismissed_alert_ids.add(alert_id)
                # Fire-and-forget: tell the backend to persist the acknowledgment
                try:
                    requests.post(f"{API_BASE_URL}/api/acknowledge/{patient_id}", timeout=3)
                except:
                    pass
                st.rerun()
        st.markdown("---")

    # --- 2. REAL-TIME TELEMETRY METRICS ---
    st.subheader("Real-Time Telemetry Metrics")
    kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)
    
    with kpi_1:
        st.metric("Heart Rate", f"{latest['heart_rate']:.1f} bpm")
    with kpi_2:
        st.metric("Blood Pressure", f"{latest['blood_pressure_sys']:.1f}/{latest['blood_pressure_dia']:.1f}")
    with kpi_3:
        st.metric("Oxygen Saturation", f"{latest['spo2']:.1f}%")
    with kpi_4:
        st.metric("Core Temperature", f"{latest['temperature']:.1f} °C")
    with kpi_5:
        # Clinical status is VARIANCE only if the alert banner is actively shown
        is_var = show_alert_banner
        status_text = "VARIANCE" if is_var else "STABLE"
        color_code = "#ff4b4b" if is_var else "#2ecc71"
        st.markdown(
            f"""
            <div style="padding: 0px; border-radius: 5px;">
                <p style="color: rgb(150, 150, 150); font-size: 14px; margin-bottom: 2px;">Clinical Status</p>
                <p style="color: {color_code}; font-size: 24px; font-weight: bold; margin-top: 0px;">{status_text}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- 3. WORKSPACE (Analytics & Triage History) ---
    workspace_left, workspace_right = st.columns([2, 1])

    with workspace_left:
        st.subheader("Physiological Trend Analysis")
        
        fig_cardio = px.line(
            df, x='timestamp', y=['heart_rate', 'blood_pressure_sys', 'blood_pressure_dia'],
            labels={'value': 'Value', 'timestamp': 'Time', 'variable': 'Parameter'},
            title="Cardiovascular Parameters Over Time"
        )
        fig_cardio.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)
        st.plotly_chart(fig_cardio, use_container_width=True)

        fig_spo2 = px.line(
            df, x='timestamp', y='spo2',
            title="Oxygen Saturation (SpO2 %)",
            color_discrete_sequence=['#2ecc71']
        )
        fig_spo2.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=250)
        st.plotly_chart(fig_spo2, use_container_width=True)

    with workspace_right:
        st.subheader("AI Triage History Log")
        
        if not alerts_data:
            st.success("No physiological variance events recorded.")
        else:
            for alert in alerts_data[:4]:
                event_time = str(alert['timestamp'])[11:19]
                with st.expander(f"Variance Event | {event_time} (Score: {alert['anomaly_score']:.2f})"):
                    st.text(f"HR: {alert['heart_rate']} | BP: {alert['blood_pressure_sys']}/{alert['blood_pressure_dia']}")
                    note_val = alert.get('triage_note')
                    st.caption(str(note_val) if note_val is not None and pd.notna(note_val) else "No triage note recorded.")

    st.markdown("---")

    # --- 4. AUDIT TRAIL TABLE ---
    st.subheader("Telemetry Audit Trail")
    st.dataframe(
        df[['timestamp', 'heart_rate', 'blood_pressure_sys', 'blood_pressure_dia', 'spo2', 'temperature', 'is_anomaly', 'anomaly_score', 'acknowledged']],
        use_container_width=True,
        height=220
    )

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()