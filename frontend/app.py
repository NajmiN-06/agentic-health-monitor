import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Clinical Telemetry & AI Triage Monitor",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://127.0.0.1:8000"

# Inject modern ICU clinical telemetry CSS styling with cardiac pulse and heartbeat animations
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: radial-gradient(circle at 15% 15%, #0d1527 0%, #080c14 100%);
    color: #e2e8f0;
}

/* --- Cardiac Pulse & Heartbeat Keyframes --- */
@keyframes cardiacPulse {
    0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0, 240, 144, 0); }
    15% { transform: scale(1.035); box-shadow: 0 0 22px 3px rgba(0, 240, 144, 0.45); }
    30% { transform: scale(1); box-shadow: 0 0 8px 1px rgba(0, 240, 144, 0.2); }
    45% { transform: scale(1.05); box-shadow: 0 0 26px 4px rgba(0, 240, 144, 0.55); }
    70% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0, 240, 144, 0); }
    100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(0, 240, 144, 0); }
}

@keyframes heartIconPulse {
    0% { transform: scale(1); }
    14% { transform: scale(1.35); filter: drop-shadow(0 0 10px #ff3366); }
    28% { transform: scale(1.05); }
    42% { transform: scale(1.25); filter: drop-shadow(0 0 8px #ff3366); }
    70% { transform: scale(1); }
    100% { transform: scale(1); }
}

@keyframes criticalAlertPulse {
    0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 51, 102, 0.7); border-color: rgba(255, 51, 102, 0.9); }
    30% { transform: scale(1.03); box-shadow: 0 0 28px 8px rgba(255, 51, 102, 0.6); border-color: rgba(255, 51, 102, 1); }
    60% { transform: scale(1); box-shadow: 0 0 12px 2px rgba(255, 51, 102, 0.35); border-color: rgba(255, 51, 102, 0.7); }
    100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 51, 102, 0.7); border-color: rgba(255, 51, 102, 0.9); }
}

@keyframes liveStatusBlink {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(0.85); }
}

/* Glassmorphic Metric Card */
.vital-card {
    background: linear-gradient(145deg, rgba(17, 24, 39, 0.92) 0%, rgba(13, 19, 33, 0.96) 100%);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 14px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
    min-height: 165px;
}

.vital-card.beat-pulse {
    animation: cardiacPulse 1.2s cubic-bezier(0.25, 1, 0.5, 1);
    border-color: rgba(0, 240, 144, 0.8);
}

.vital-card.variance-alert {
    animation: criticalAlertPulse 1.5s infinite;
    background: linear-gradient(145deg, rgba(48, 16, 26, 0.92) 0%, rgba(26, 11, 18, 0.96) 100%);
    border-color: rgba(255, 51, 102, 0.9);
}

.card-top-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.card-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.1px;
    text-transform: uppercase;
    color: #94a3b8;
}

.heart-beat-icon {
    display: inline-block;
    font-size: 18px;
    animation: heartIconPulse 1.0s infinite ease-in-out;
}

.vital-reading-row {
    display: flex;
    align-items: baseline;
    gap: 6px;
    margin-bottom: 8px;
}

.vital-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 30px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.5px;
}

.vital-val.normal {
    color: #00f090;
    text-shadow: 0 0 12px rgba(0, 240, 144, 0.35);
}

.vital-val.abnormal {
    color: #ff3366;
    text-shadow: 0 0 16px rgba(255, 51, 102, 0.65);
}

.vital-units {
    font-size: 12px;
    font-weight: 600;
    color: #64748b;
}

.vital-badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 10.5px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 999px;
    letter-spacing: 0.4px;
}

.badge-stable {
    background: rgba(0, 240, 144, 0.12);
    border: 1px solid rgba(0, 240, 144, 0.35);
    color: #00f090;
}

.badge-variance {
    background: rgba(255, 51, 102, 0.18);
    border: 1px solid rgba(255, 51, 102, 0.5);
    color: #ff3366;
}

/* Critical Alert Banner */
.clinical-alert-banner {
    background: linear-gradient(135deg, rgba(60, 10, 22, 0.95) 0%, rgba(30, 8, 14, 0.98) 100%);
    border: 2px solid #ff3366;
    box-shadow: 0 0 30px rgba(255, 51, 102, 0.45);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 20px;
    animation: criticalAlertPulse 1.8s infinite;
}

.alert-header-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid rgba(255, 51, 102, 0.3);
    padding-bottom: 8px;
}

.alert-beacon-icon {
    font-size: 26px;
    animation: liveStatusBlink 1s infinite;
}

.alert-heading-title {
    font-size: 16px;
    font-weight: 800;
    color: #ff3366;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

.alert-heading-sub {
    font-size: 12px;
    color: #fca5a5;
    margin-top: 2px;
}

.snapshot-box {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 51, 102, 0.3);
    border-radius: 10px;
    padding: 14px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    color: #e2e8f0;
    line-height: 1.8;
}

.triage-report-box {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 10px;
    padding: 16px 20px;
    color: #e2e8f0;
    font-size: 13.5px;
    line-height: 1.6;
}

/* Pulsing Status Dot */
.live-status-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-right: 6px;
    animation: liveStatusBlink 1.4s infinite;
}
.dot-green { background-color: #00f090; box-shadow: 0 0 8px #00f090; }
.dot-red { background-color: #ff3366; box-shadow: 0 0 10px #ff3366; }
</style>
""", unsafe_allow_html=True)

# --- Session State Setup ---
if 'dismissed_alert_ids' not in st.session_state:
    st.session_state.dismissed_alert_ids = set()

if 'last_seen_ts' not in st.session_state:
    st.session_state.last_seen_ts = None

if 'beat_tick' not in st.session_state:
    st.session_state.beat_tick = 0

# --- Sidebar Controls ---
st.sidebar.markdown("### 🎛️ Telemetry Controls")
patient_id = st.sidebar.text_input("Active Patient ID", value="PATIENT-POSTOP-102")
auto_refresh = st.sidebar.checkbox("Enable Live Telemetry Stream", value=True)
refresh_rate = st.sidebar.slider("Refresh Interval (Seconds)", min_value=2, max_value=8, value=2)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Clinical Simulator Actions")

# Trigger on-demand variance for instant testing
if st.sidebar.button("🚨 Simulate Critical Variance Now", use_container_width=True, type="secondary"):
    try:
        res = requests.post(f"{API_BASE_URL}/api/trigger-variance/{patient_id}", timeout=5)
        if res.status_code == 201:
            st.sidebar.success("Acute physiological variance event injected!")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Failed to trigger variance: {e}")

# Reset patient telemetry
if st.sidebar.button("🔄 Reset Patient History & Alerts", use_container_width=True):
    try:
        res = requests.post(f"{API_BASE_URL}/api/reset/{patient_id}", timeout=5)
        if res.status_code == 200:
            st.session_state.dismissed_alert_ids.clear()
            st.sidebar.success("Telemetry history reset!")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Reset failed: {e}")

st.sidebar.markdown("---")
# Backend connectivity status check
backend_online = False
try:
    health_res = requests.get(f"{API_BASE_URL}/", timeout=2)
    backend_online = (health_res.status_code == 200)
except Exception:
    backend_online = False

status_dot_class = "dot-green" if backend_online else "dot-red"
status_text = "Ingestion Pipeline Connected" if backend_online else "Backend Offline (Port 8000)"
st.sidebar.markdown(f'<span class="live-status-dot {status_dot_class}"></span>**Backend:** {status_text}', unsafe_allow_html=True)


# --- Header ---
st.title("Post-Operative Clinical Telemetry & Autonomous AI Guardrail")
st.markdown(f"**Patient Stream:** `{patient_id}` &nbsp;|&nbsp; **Architecture:** ML Isolation Forest + Gemini Agentic Triage")
st.markdown("---")


# --- API Fetch Helpers ---
def fetch_patient_history(pat_id):
    try:
        response = requests.get(f"{API_BASE_URL}/api/vitals/{pat_id}?limit=35", timeout=3)
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
        response = requests.get(f"{API_BASE_URL}/api/alerts/{pat_id}?limit=15", timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []


# --- Streamlit Fragment for Clean Live Updates Without Ghost Duplicates ---
@st.fragment(run_every=f"{refresh_rate}s" if auto_refresh else None)
def render_live_telemetry():
    df = fetch_patient_history(patient_id)
    alerts_data = fetch_patient_alerts(patient_id)

    if df.empty:
        st.info(f"⏳ Telemetry stream active for patient `{patient_id}`. Waiting for initial readings from simulator...")
        st.caption("Ensure `simulator.py` is running in your terminal (`python backend/app/services/simulator.py`).")
        return

    latest = df.iloc[-1]
    current_ts_str = str(latest['timestamp'])

    # Track beat animation trigger
    if current_ts_str != st.session_state.last_seen_ts:
        st.session_state.last_seen_ts = current_ts_str
        st.session_state.beat_tick += 1
        is_beat = True
    else:
        is_beat = False

    beat_class = "beat-pulse" if is_beat else ""

    # Prune locally dismissed alerts that the backend has already marked acknowledged
    backend_acked_ids = {a['id'] for a in alerts_data if a.get('acknowledged', False)}
    st.session_state.dismissed_alert_ids -= backend_acked_ids

    # An active alert exists if it is unacknowledged on backend AND not in our dismissed set
    unacked_alerts = [
        a for a in alerts_data
        if not a.get('acknowledged', False) and a['id'] not in st.session_state.dismissed_alert_ids
    ]
    has_active_alert = len(unacked_alerts) > 0

    # ==========================================
    # 1. EMERGENCY CLINICAL ALERT BANNER
    # ==========================================
    if has_active_alert:
        active_alert = unacked_alerts[0]
        alert_id = active_alert['id']
        alert_ts = str(active_alert.get('timestamp'))

        alert_banner_html = (
            '<div class="clinical-alert-banner">'
            '<div class="alert-header-row">'
            '<div class="alert-beacon-icon">🚨</div>'
            '<div>'
            '<div class="alert-heading-title">CRITICAL CLINICAL ALERT: ACUTE PHYSIOLOGICAL ESCALATION DETECTED</div>'
            f'<div class="alert-heading-sub">Automated Clinical Guardrail Triggered &bull; Timestamp: {alert_ts} &bull; Score: {active_alert.get("anomaly_score", 0):.4f}</div>'
            '</div>'
            '</div>'
            '</div>'
        )
        st.markdown(alert_banner_html, unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.markdown("##### 📌 Triggering Snapshot")
            snapshot_html = (
                '<div class="snapshot-box">'
                f'<b>Heart Rate:</b> <span style="color:#ff3366; font-weight:700;">{active_alert["heart_rate"]:.1f} bpm</span> [TACHYCARDIA]<br>'
                f'<b>Blood Pressure:</b> <span style="color:#ff3366; font-weight:700;">{active_alert["blood_pressure_sys"]:.1f}/{active_alert["blood_pressure_dia"]:.1f} mmHg</span> [HYPOTENSIVE]<br>'
                f'<b>Oxygen Saturation:</b> <span style="color:#ff3366; font-weight:700;">{active_alert["spo2"]:.1f}%</span> [DESATURATION]<br>'
                f'<b>Core Temperature:</b> <span style="color:#ff3366; font-weight:700;">{active_alert["temperature"]:.1f} °C</span> [PYREXIA]<br>'
                '<b>Isolation Forest Anomaly:</b> TRUE'
                '</div>'
            )
            st.markdown(snapshot_html, unsafe_allow_html=True)

        with col_right:
            st.markdown("##### 🩺 Autonomous AI Triage Evaluation & Bedside Protocols")
            triage_text = active_alert.get('triage_note')
            if not triage_text or pd.isna(triage_text):
                triage_text = "Standard clinical guardrail triggered: Immediate bedside nursing review recommended. Continuous hemodynamic monitoring required."
            
            triage_box_html = f'<div class="triage-report-box">{triage_text}</div>'
            st.markdown(triage_box_html, unsafe_allow_html=True)

            st.write("")
            # Acknowledge and dismiss button: Clears alert and unpauses simulator for next normal cycle!
            if st.button("✅ Acknowledge & Dismiss Alert (Start New Normal Vital Cycle)", key=f"btn_dismiss_{alert_id}", type="primary", use_container_width=True):
                # 1. Immediately record in session state so alert vanishes from UI
                st.session_state.dismissed_alert_ids.add(alert_id)
                # 2. Tell backend to mark acknowledged so simulator unpauses and resumes normal vitals
                try:
                    requests.post(f"{API_BASE_URL}/api/acknowledge/{patient_id}", timeout=3)
                except Exception as err:
                    print("Dismiss post error:", err)
                # 3. Rerun fragment immediately for instantaneous dismissal
                st.rerun(scope="fragment")

        st.markdown("---")

    # ==========================================
    # 2. REAL-TIME TELEMETRY METRICS (BEAT EFFECT)
    # ==========================================
    st.subheader("Real-Time Telemetry & Cardiac Hemodynamics")

    hr = latest['heart_rate']
    bp_sys = latest['blood_pressure_sys']
    bp_dia = latest['blood_pressure_dia']
    spo2 = latest['spo2']
    temp = latest['temperature']

    # Dynamic status colors and badges
    hr_status = "Tachycardia" if hr > 100 else ("Bradycardia" if hr < 60 else "Normal Sinus")
    hr_color = "abnormal" if (hr > 100 or hr < 60) else "normal"

    bp_status = "Hypotensive" if bp_sys < 90 else ("Hypertensive" if bp_sys > 140 else "Normotensive")
    bp_color = "abnormal" if (bp_sys < 90 or bp_sys > 140) else "normal"

    spo2_status = "Hypoxic" if spo2 < 90 else "Adequate Perfusion"
    spo2_color = "abnormal" if spo2 < 90 else "normal"

    temp_status = "Pyrexia" if temp > 38.0 else ("Hypothermic" if temp < 35.5 else "Normothermic")
    temp_color = "abnormal" if (temp > 38.0 or temp < 35.5) else "normal"

    clin_status_text = "CRITICAL VARIANCE" if has_active_alert else "STABLE"
    clin_badge_class = "badge-variance" if has_active_alert else "badge-stable"
    clin_card_class = "vital-card variance-alert" if has_active_alert else f"vital-card {beat_class}"
    status_dot = "dot-red" if has_active_alert else "dot-green"

    # SVG ECG rhythm line representation
    ecg_stroke = "#ff3366" if has_active_alert else "#00f090"
    ecg_svg = (
        f'<svg width="100%" height="22" viewBox="0 0 140 22" style="margin-top: 6px; opacity: 0.9;">'
        f'<path d="M0,11 L32,11 L38,11 L41,3 L45,19 L49,1 L53,21 L56,11 L62,11 L67,14 L72,11 L140,11" '
        f'fill="none" stroke="{ecg_stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )

    card1, card2, card3, card4, card5 = st.columns(5)

    with card1:
        hr_html = (
            f'<div class="vital-card {beat_class}">'
            '<div class="card-top-row">'
            '<span class="card-label">Heart Rate</span>'
            '<span class="heart-beat-icon">❤️</span>'
            '</div>'
            '<div class="vital-reading-row">'
            f'<span class="vital-val {hr_color}">{hr:.1f}</span>'
            '<span class="vital-units">BPM</span>'
            '</div>'
            f'<div class="vital-badge-pill {("badge-variance" if hr_color == "abnormal" else "badge-stable")}">'
            f'{hr_status}'
            '</div>'
            f'{ecg_svg}'
            '</div>'
        )
        st.markdown(hr_html, unsafe_allow_html=True)

    with card2:
        bp_html = (
            f'<div class="vital-card {beat_class}">'
            '<div class="card-top-row">'
            '<span class="card-label">Blood Pressure</span>'
            '<span style="font-size: 16px;">🩺</span>'
            '</div>'
            '<div class="vital-reading-row">'
            f'<span class="vital-val {bp_color}">{bp_sys:.0f}/{bp_dia:.0f}</span>'
            '<span class="vital-units">mmHg</span>'
            '</div>'
            f'<div class="vital-badge-pill {("badge-variance" if bp_color == "abnormal" else "badge-stable")}">'
            f'{bp_status}'
            '</div>'
            f'<div style="font-size: 11px; color: #64748b; margin-top: 10px;">Mean MAP: {((bp_sys + 2*bp_dia)/3):.1f} mmHg</div>'
            '</div>'
        )
        st.markdown(bp_html, unsafe_allow_html=True)

    with card3:
        spo2_html = (
            f'<div class="vital-card {beat_class}">'
            '<div class="card-top-row">'
            '<span class="card-label">Pulse Oximetry</span>'
            '<span style="font-size: 16px;">🫁</span>'
            '</div>'
            '<div class="vital-reading-row">'
            f'<span class="vital-val {spo2_color}">{spo2:.1f}</span>'
            '<span class="vital-units">% SpO2</span>'
            '</div>'
            f'<div class="vital-badge-pill {("badge-variance" if spo2_color == "abnormal" else "badge-stable")}">'
            f'{spo2_status}'
            '</div>'
            '<div style="font-size: 11px; color: #64748b; margin-top: 10px;">Plethysmograph: Continuous</div>'
            '</div>'
        )
        st.markdown(spo2_html, unsafe_allow_html=True)

    with card4:
        temp_html = (
            f'<div class="vital-card {beat_class}">'
            '<div class="card-top-row">'
            '<span class="card-label">Core Temperature</span>'
            '<span style="font-size: 16px;">🌡️</span>'
            '</div>'
            '<div class="vital-reading-row">'
            f'<span class="vital-val {temp_color}">{temp:.1f}</span>'
            '<span class="vital-units">°C</span>'
            '</div>'
            f'<div class="vital-badge-pill {("badge-variance" if temp_color == "abnormal" else "badge-stable")}">'
            f'{temp_status}'
            '</div>'
            '<div style="font-size: 11px; color: #64748b; margin-top: 10px;">Thermistor probe active</div>'
            '</div>'
        )
        st.markdown(temp_html, unsafe_allow_html=True)

    with card5:
        clin_html = (
            f'<div class="{clin_card_class}">'
            '<div class="card-top-row">'
            '<span class="card-label">Clinical State</span>'
            f'<span class="live-status-dot {status_dot}"></span>'
            '</div>'
            '<div class="vital-reading-row">'
            f'<span class="vital-val {"abnormal" if has_active_alert else "normal"}" style="font-size: 20px;">'
            f'{clin_status_text}'
            '</span>'
            '</div>'
            f'<div class="vital-badge-pill {clin_badge_class}">'
            f'{"AI Guardrail Warning" if has_active_alert else "Sinus Baseline Nominal"}'
            '</div>'
            f'<div style="font-size: 11px; color: #64748b; margin-top: 10px;">Tick #{st.session_state.beat_tick} &bull; Synced</div>'
            '</div>'
        )
        st.markdown(clin_html, unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================
    # 3. WORKSPACE: PHYSIOLOGICAL TRENDS & AI HISTORY
    # ==========================================
    col_trend, col_triage_log = st.columns([2, 1])

    with col_trend:
        st.subheader("Physiological Trend Analysis")

        # Cardio chart
        fig_cardio = px.line(
            df,
            x='timestamp',
            y=['heart_rate', 'blood_pressure_sys', 'blood_pressure_dia'],
            labels={'value': 'Measurement', 'timestamp': 'Time', 'variable': 'Vital Parameter'},
            title="Cardiovascular Telemetry Trends (HR & Arterial BP)"
        )
        fig_cardio.update_layout(
            paper_bgcolor='rgba(13, 19, 33, 0.7)',
            plot_bgcolor='rgba(13, 19, 33, 0.7)',
            font=dict(color='#cbd5e1', family='Inter'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20),
            height=280
        )
        fig_cardio.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.06)')
        fig_cardio.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.06)')
        st.plotly_chart(fig_cardio, use_container_width=True, key="fig_cardio_chart")

        # SpO2 chart
        fig_spo2 = px.line(
            df,
            x='timestamp',
            y='spo2',
            labels={'spo2': 'SpO2 %', 'timestamp': 'Time'},
            title="Oxygen Saturation (SpO2 %)",
            color_discrete_sequence=['#00f090']
        )
        fig_spo2.add_hline(y=90.0, line_dash="dash", line_color="#ff3366", annotation_text="Hypoxia Threshold (90%)", annotation_position="bottom right")
        fig_spo2.update_layout(
            paper_bgcolor='rgba(13, 19, 33, 0.7)',
            plot_bgcolor='rgba(13, 19, 33, 0.7)',
            font=dict(color='#cbd5e1', family='Inter'),
            margin=dict(l=20, r=20, t=40, b=20),
            height=230
        )
        fig_spo2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.06)')
        fig_spo2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.06)')
        st.plotly_chart(fig_spo2, use_container_width=True, key="fig_spo2_chart")

    with col_triage_log:
        st.subheader("AI Triage History Log")
        
        if not alerts_data:
            st.success("✅ No physiological variance events recorded.")
        else:
            for alert in alerts_data[:5]:
                event_time = str(alert['timestamp'])[11:19]
                ack_status = "Acknowledged" if alert.get('acknowledged', False) else "UNACKNOWLEDGED"
                score = alert.get('anomaly_score', 0.0)
                
                with st.expander(f"⚠️ Event at {event_time} | Score: {score:.2f} [{ack_status}]"):
                    st.markdown(f"**Vitals:** HR `{alert['heart_rate']:.1f}` | BP `{alert['blood_pressure_sys']:.1f}/{alert['blood_pressure_dia']:.1f}` | SpO2 `{alert['spo2']:.1f}%`")
                    note = alert.get('triage_note')
                    if note and pd.notna(note):
                        st.caption(str(note))
                    else:
                        st.caption("Standard guardrail triage applied.")

    st.markdown("---")

    # ==========================================
    # 4. AUDIT TRAIL TABLE (SINGLE CLEAN INSTANCE)
    # ==========================================
    st.subheader("Telemetry Audit Trail")
    
    # Format dataframe cleanly with human-readable numbers and timestamps
    audit_df = df.copy()
    audit_df['Time'] = audit_df['timestamp'].dt.strftime('%H:%M:%S')
    audit_df['HR (bpm)'] = audit_df['heart_rate'].round(1)
    audit_df['BP (mmHg)'] = audit_df['blood_pressure_sys'].round(1).astype(str) + " / " + audit_df['blood_pressure_dia'].round(1).astype(str)
    audit_df['SpO2 (%)'] = audit_df['spo2'].round(1)
    audit_df['Temp (°C)'] = audit_df['temperature'].round(1)
    audit_df['Anomaly?'] = audit_df['is_anomaly'].apply(lambda x: "🚨 ANOMALY" if x else "✅ Normal")
    audit_df['Score'] = audit_df['anomaly_score'].round(4)
    audit_df['Acknowledged'] = audit_df['acknowledged'].apply(lambda x: "Yes" if x else "No")

    display_cols = ['Time', 'HR (bpm)', 'BP (mmHg)', 'SpO2 (%)', 'Temp (°C)', 'Anomaly?', 'Score', 'Acknowledged']
    
    # Explicit unique key prevents Streamlit from creating duplicate dataframe nodes
    st.dataframe(
        audit_df[display_cols].sort_index(ascending=False),
        use_container_width=True,
        height=240,
        key="telemetry_audit_table"
    )

# Render the self-updating telemetry view cleanly
render_live_telemetry()