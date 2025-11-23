# dashboard/components/alert_cards.py
import streamlit as st
from datetime import datetime
import requests

BACKEND_ALERT_URL = "http://127.0.0.1:8000/alerts/send"

SEVERITY_COLORS = {
    "normal": "#2ECC71",
    "warning": "#F1C40F",
    "critical": "#E74C3C"
}

def _pretty_issues(issues):
    if not issues:
        return "None"
    if isinstance(issues, list):
        return ", ".join(issues)
    return str(issues)

def _format_ts(ts):
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)

def send_alert_to_backend(item):
    # build payload
    if "anomaly" in item:
        ann = item.get("anomaly", {})
        severity = ann.get("severity", "normal")
        issues = ann.get("issues", [])
        score = ann.get("score", 0.0)
    else:
        severity = item.get("severity", "normal")
        issues = item.get("issues", [])
        score = item.get("score", 0.0)

    payload = {
        "timestamp": item.get("timestamp"),
        "satellite_id": item.get("satellite_id"),
        "severity": severity,
        "issues": issues,
        "score": score
    }
    try:
        resp = requests.post(BACKEND_ALERT_URL, json=payload, timeout=5)
        if resp.ok:
            return {"ok": True, "result": resp.json()}
        return {"ok": False, "result": resp.text}
    except Exception as e:
        return {"ok": False, "result": str(e)}

def render_alert_card(item, show_send_button=True):
    # support both latest format (nested anomaly) and flat history format
    if "anomaly" in item:
        ann = item.get("anomaly", {})
        severity = (ann.get("severity") or "normal").lower()
        issues = ann.get("issues", [])
        score = ann.get("score", 0.0)
    else:
        severity = (item.get("severity") or "normal").lower()
        issues = item.get("issues", [])
        score = item.get("score", 0.0)
        ann = {"severity": severity, "issues": issues, "score": score}

    color = SEVERITY_COLORS.get(severity, "#95A5A6")
    ts = _format_ts(item.get("timestamp", ""))

    # container card
    container = st.container()
    with container:
        cols = st.columns([3.5, 0.9])
        with cols[0]:
            st.markdown(
                f"""
                <div style="border-left:6px solid {color}; padding:10px; margin-bottom:8px; border-radius:8px; background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <strong style="font-size:14px;">Satellite: {item.get('satellite_id', 'unknown')}</strong><br>
                            <span class="small-muted">{ts}</span>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-weight:700; color:{color}; text-transform:uppercase;">{severity}</div>
                            <div style="font-size:13px;">Score: {round(float(score or 0),2)}</div>
                        </div>
                    </div>
                    <div style="margin-top:8px; color:rgba(230,238,243,0.85)"><strong>Issues:</strong> {_pretty_issues(issues)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            if show_send_button:
                btn_key = f"send_{item.get('timestamp')}_{item.get('satellite_id')}"
                if st.button("📣", key=btn_key):
                    with st.spinner("Sending alert..."):
                        resp = send_alert_to_backend(item)
                    if resp["ok"]:
                        st.success("Sent")
                    else:
                        st.error("Failed")
            else:
                st.write("")
