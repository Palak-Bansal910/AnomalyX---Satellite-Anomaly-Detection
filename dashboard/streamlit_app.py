# dashboard/streamlit_app.py
# dashboard/streamlit_app.py
import time
import requests
import pandas as pd
import streamlit as st

from components.alert_cards import render_alert_card
from components.health_panel import render_health_panel
from components.live_plots import render_score_trend, render_issue_distribution
from components.orbit_visualizer import render_orbit_visualizer

BASE_URL = "http://127.0.0.1:8000"
LATEST_ENDPOINT = f"{BASE_URL}/anomalies/latest"
HISTORY_ENDPOINT = f"{BASE_URL}/anomalies/history?limit=500"

st.set_page_config(page_title="🛰 Satellite Anomaly Detector", layout="wide")

# --- Custom minimal CSS for nicer look ---
st.markdown(
    """
    <style>
    /* page background + card background */
    .stApp {
        background: linear-gradient(180deg, #0f1724 0%, #07122a 100%);
        color: #E6EEF3;
    }
    .card {
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 12px;
        box-shadow: 0 4px 10px rgba(2,6,23,0.6);
        border: 1px solid rgba(255,255,255,0.03);
    }
    .side-card {
        background: rgba(255,255,255,0.02);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.03);
    }
    .small-muted { color: rgba(230,238,243,0.6); font-size:12px; }
    .big-num { font-size: 36px; font-weight:700; color: #E6EEF3; }
    .metric-label { color: rgba(230,238,243,0.65); font-size:12px; }
    /* override streamlit default backgrounds for sidebar */
    .css-1d392kg { background: transparent; }
    .stSidebar .css-1d392kg { background: rgba(255,255,255,0.02); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛰 Satellite Anomaly Detector — Mission Dashboard")
st.markdown("<div class='small-muted'>Live telemetry → anomaly pipeline. Use controls on the left to filter/playback.</div>", unsafe_allow_html=True)

# fetch functions
@st.cache_data(ttl=3)
def fetch_latest():
    try:
        r = requests.get(LATEST_ENDPOINT, timeout=2)
        return r.json().get("data", []) if r.ok else []
    except Exception:
        return []

@st.cache_data(ttl=5)
def fetch_history():
    try:
        r = requests.get(HISTORY_ENDPOINT, timeout=4)
        data = r.json().get("data", []) if r.ok else []
        # normalize issues as lists
        for item in data:
            if isinstance(item.get("issues"), str):
                item["issues"] = item["issues"].split(",") if item["issues"] else []
        return data
    except Exception:
        return []

latest = fetch_latest()
history = fetch_history()

# build dataframe for UI controls
df_hist = pd.DataFrame(history)
if not df_hist.empty:
    try:
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
    except Exception:
        pass
else:
    df_hist = pd.DataFrame(columns=["timestamp", "satellite_id", "severity", "issues", "score"])

# LEFT: control panel (moved to left for ergonomics)
with st.sidebar:
    st.header("Controls")
    sats = sorted(df_hist['satellite_id'].unique().tolist()) if not df_hist.empty else []
    selected_sat = st.selectbox("Filter satellite", options=["All"] + sats)
    play_toggle = st.checkbox("Play animation", value=False)
    # slider for manual frame selection
    timestamps = sorted(df_hist['timestamp'].unique().tolist()) if not df_hist.empty else []
    if timestamps:
        slider_index = st.slider("Playback frame", 0, max(0, len(timestamps)-1), 0)
    else:
        slider_index = 0
    st.markdown("---")
    st.write("Auto-refresh every ~4 seconds")
    st.markdown("<div class='small-muted'>Demo tips:</div>", unsafe_allow_html=True)
    st.write("- Start backend (uvicorn api.main:app --reload)")
    st.write("- Start simulator to stream telemetry")
    st.write("- Use Slack/email config in .env to enable push alerts")

# MAIN layout: wider left area for cards + visualizations, right side for health
left_col, right_col = st.columns([3.2, 1])

with left_col:
    st.subheader("Live Alerts")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if not latest:
        st.info("No anomalies yet...")
    else:
        # apply satellite filter to latest
        if selected_sat != "All":
            latest_filtered = [l for l in latest if l.get("satellite_id") == selected_sat]
        else:
            latest_filtered = latest

        # compact grid: two columns for alert cards (adjust per item)
        for item in latest_filtered:
            render_alert_card(item, show_send_button=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Anomaly Score Trend")
    with st.container():
        render_score_trend(df_hist)

    st.markdown("---")
    st.subheader("Issue Frequency (Recent)")
    with st.container():
        render_issue_distribution(df_hist)

    st.markdown("---")
    st.subheader("Orbit Visualizer")
    sel_sat = None if selected_sat == "All" else selected_sat
    render_orbit_visualizer(history, selected_satellite=sel_sat, play=play_toggle, slider_index=slider_index)

with right_col:
    st.subheader("System Health")
    st.markdown("<div class='side-card'>", unsafe_allow_html=True)
    render_health_panel(df_hist, latest)
    st.markdown("</div>", unsafe_allow_html=True)

# auto refresh (non-blocking)
if st.session_state.get("_auto_refresh", True):
    time.sleep(0.1)
