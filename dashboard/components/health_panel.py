# dashboard/components/health_panel.py
import streamlit as st
import pandas as pd

SEVERITY_ORDER = ["critical", "warning", "normal"]
SEVERITY_COLORS = {
    "normal": "#2ECC71",
    "warning": "#F1C40F",
    "critical": "#E74C3C"
}

def render_count_metric(label, value, color=None, help_text=None):
    color_style = f"color:{color};" if color else ""
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
            <div style="flex:1">
                <div class="metric-label">{label}</div>
                <div class="big-num" style="{color_style}">{value}</div>
                {"<div class='small-muted'>"+help_text+"</div>" if help_text else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_health_panel(df_history: pd.DataFrame, latest: list):
    if df_history is None or df_history.empty:
        total_anomalies = 0
        counts = {"critical": 0, "warning": 0, "normal": 0}
    else:
        total_anomalies = len(df_history)
        counts = {}
        for s in SEVERITY_ORDER:
            counts[s] = int((df_history['severity'].fillna("normal").str.lower() == s).sum())

    latest_severity = "N/A"
    if latest and isinstance(latest, list) and len(latest) > 0:
        sev_map = {"critical": 3, "warning": 2, "normal": 1}
        top = ("normal", 0)
        for item in latest:
            if "anomaly" in item:
                s = item.get("anomaly", {}).get("severity", "normal")
            else:
                s = item.get("severity", "normal")
            s = (s or "normal").lower()
            if sev_map.get(s, 1) > sev_map.get(top[0], 1):
                top = (s, sev_map.get(s))
        latest_severity = top[0]

    color = SEVERITY_COLORS.get(latest_severity, "#95A5A6")
    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center;'>", unsafe_allow_html=True)
    st.markdown(f"<div><div class='metric-label'>Latest Severity</div><div class='big-num' style='color:{color}; text-transform:uppercase;'>{latest_severity}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div><div class='metric-label'>Total logged</div><div class='big-num'>{total_anomalies}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    cols = st.columns(3)
    for i, s in enumerate(["critical", "warning", "normal"]):
        with cols[i]:
            c = counts.get(s, 0)
            render_count_metric(s.capitalize(), c, color=SEVERITY_COLORS.get(s))

    st.markdown("---")
    st.markdown("<div class='metric-label'>Recent anomalies (compact)</div>", unsafe_allow_html=True)
    if df_history is None or df_history.empty:
        st.write("No history available.")
    else:
        recent = df_history.sort_values("timestamp", ascending=False).head(5)
        for _, row in recent.iterrows():
            sid = row.get("satellite_id", "unknown")
            sev = str(row.get("severity", "normal")).upper()
            score = row.get("score", 0)
            ts = row.get("timestamp")
            st.markdown(f"<div style='padding:6px 8px; margin-bottom:6px; border-radius:6px; background:#070707'><strong>{sid}</strong> <span style='float:right'>{sev} • {round(float(score or 0),2)}</span><br><small class='small-muted'>{ts}</small></div>", unsafe_allow_html=True)
