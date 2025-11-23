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

st.set_page_config(page_title="🛰 Satellite Anomaly Detector", layout="wide", initial_sidebar_state="expanded")

# --- Theme CSS: pure black + soft blue accent (#3A8DFF) ---
st.markdown(
    """
    <style>
    :root {
        --accent: #3A8DFF;
        --panel: #0b0b0b;
        --muted: rgba(230,238,243,0.6);
        --panel-2: #101010;
    }
    /* app background */
    .stApp {
        background: #000000;
        color: #E6EEF3;
    }
    /* cards */
    .card {
        background: var(--panel-2);
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.04);
    }
    .side-card {
        background: var(--panel);
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.03);
    }
    .small-muted { color: var(--muted); font-size:12px; }
    .big-num { font-size: 34px; font-weight:700; color: #E6EEF3; }
    .metric-label { color: rgba(230,238,243,0.65); font-size:12px; }
    .accent { color: var(--accent); }
    /* sidebar background */
    .stSidebar .css-1d392kg { background: #070707; border-right: 1px solid rgba(255,255,255,0.02); }
    /* minimize streamer default bright boxes */
    .stButton>button { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.04); color: #E6EEF3; }
    /* small tweaks to headings */
    h1, .streamlit-expanderHeader { color: #E6EEF3; }
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

# dataframe for controls
df_hist = pd.DataFrame(history)
if not df_hist.empty:
    try:
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
    except Exception:
        pass
else:
    df_hist = pd.DataFrame(columns=["timestamp", "satellite_id", "severity", "issues", "score"])

# Controls in sidebar
with st.sidebar:
    st.header("Controls")
    sats = sorted(df_hist['satellite_id'].unique().tolist()) if not df_hist.empty else []
    selected_sat = st.selectbox("Filter satellite", options=["All"] + sats)
    play_toggle = st.checkbox("Play orbit animation", value=False)
    timestamps = sorted(df_hist['timestamp'].unique().tolist()) if not df_hist.empty else []
    slider_index = st.slider("Playback frame", 0, max(0, len(timestamps)-1), 0) if timestamps else 0
    st.markdown("---")
    st.write("Auto-refresh every ~4 seconds")
    st.markdown("<div class='small-muted'>Demo tips:</div>", unsafe_allow_html=True)
    st.write("- Start backend (uvicorn api.main:app --reload)")
    st.write("- Start simulator to stream telemetry")
    st.write("- Use Slack/email config in .env to enable push alerts")

# Tabs: Dashboard | Alerts | Satellites | Orbit | Predictions
tabs = st.tabs(["Dashboard", "Alerts", "Satellites", "Orbit", "System Health"])

# ---- DASHBOARD tab (summary + small plots) ----
with tabs[0]:
    left, right = st.columns([3, 1])
    with left:
        st.subheader("Overview")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        # Summary metrics (leveraging health panel functions)
        render_health_panel(df_hist, latest)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Recent score trend")
        render_score_trend(df_hist)
        st.markdown("---")
        st.markdown("### Issue frequency (recent)")
        render_issue_distribution(df_hist)

    with right:
        st.subheader("Quick Controls")
        st.markdown("<div class='side-card'>", unsafe_allow_html=True)
        st.write("Filter:", selected_sat)
        st.write("Frames:", len(timestamps))
        st.write("Play orbit:", play_toggle)
        st.markdown("</div>", unsafe_allow_html=True)

# ---- ALERTS tab ----
with tabs[1]:
    st.subheader("Live Alerts")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if not latest:
        st.info("No anomalies yet...")
    else:
        if selected_sat != "All":
            latest_filtered = [l for l in latest if l.get("satellite_id") == selected_sat]
        else:
            latest_filtered = latest

        for item in latest_filtered:
            render_alert_card(item, show_send_button=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### History (recent)")
    if df_hist.empty:
        st.info("No history available.")
    else:
        # show compact history - most recent 20
        history_recent = df_hist.sort_values("timestamp", ascending=False).head(20)
        for _, row in history_recent.iterrows():
            # convert to expected item shape for card renderer
            item = {
                "timestamp": row.get("timestamp"),
                "satellite_id": row.get("satellite_id"),
                "severity": row.get("severity"),
                "issues": row.get("issues"),
                "score": row.get("score")
            }
            render_alert_card(item, show_send_button=False)

# ---- SATELLITES tab ----
with tabs[2]:
    st.subheader("Satellite Data • Trends")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    # Plots already handle empty data
    render_score_trend(df_hist)
    render_issue_distribution(df_hist)
    st.markdown("</div>", unsafe_allow_html=True)

# ---- ORBIT tab ----
with tabs[3]:
    st.subheader("Orbit Visualizer")
    sel_sat = None if selected_sat == "All" else selected_sat
    render_orbit_visualizer(history, selected_satellite=sel_sat, play=play_toggle, slider_index=slider_index)

# ---- SYSTEM HEALTH tab ----
with tabs[4]:
    st.subheader("System Health")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    render_health_panel(df_hist, latest)
    st.markdown("</div>", unsafe_allow_html=True)

# small non-blocking refresh
if st.session_state.get("_auto_refresh", True):
    time.sleep(0.05)

