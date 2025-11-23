import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import time

BASE_URL = "http://127.0.0.1:8000"
LATEST_ENDPOINT = f"{BASE_URL}/anomalies/latest"
HISTORY_ENDPOINT = f"{BASE_URL}/anomalies/history"
ALERTS_ENDPOINT = f"{BASE_URL}/alerts/send"
TELEMETRY_POSITIONS_ENDPOINT = f"{BASE_URL}/telemetry/positions"

st.set_page_config(
    page_title="🛰️ Satellite Anomaly Detector",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --primary: #3B82F6;
        --primary-dark: #2563EB;
        --success: #10B981;
        --warning: #F59E0B;
        --danger: #EF4444;
        --bg-dark: #000000;
        --bg-card: #0A0A0A;
        --bg-hover: #1A1A1A;
        --text-primary: #F1F5F9;
        --text-secondary: #94A3B8;
        --border: rgba(148, 163, 184, 0.1);
    }
    
    .stApp {
        background: #000000;
        color: var(--text-primary);
    }
    
    .main .block-container {
        background: #000000;
    }
    
    section[data-testid="stSidebar"] {
        background: #1E293B;
    }
    
    section[data-testid="stSidebar"] > div {
        background: #1E293B;
    }
    
    .css-1d392kg {
        background: #1E293B;
    }
    
    section[data-testid="stSidebar"] .block-container {
        background: #1E293B;
    }
    
    .stApp > header {
        background: #000000;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .metric-card {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid var(--border);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 8px 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .alert-card {
        background: var(--bg-card);
        border-radius: 10px;
        padding: 16px;
        margin: 12px 0;
        border-left: 4px solid;
        border-color: var(--primary);
    }
    
    .alert-critical {
        border-color: var(--danger);
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, var(--bg-card) 100%);
    }
    
    .alert-warning {
        border-color: var(--warning);
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.1) 0%, var(--bg-card) 100%);
    }
    
    .alert-normal {
        border-color: var(--success);
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, var(--bg-card) 100%);
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-online {
        background: rgba(16, 185, 129, 0.2);
        color: var(--success);
        border: 1px solid var(--success);
    }
    
    .status-offline {
        background: rgba(239, 68, 68, 0.2);
        color: var(--danger);
        border: 1px solid var(--danger);
    }
    
    .element-container {
        background: transparent;
    }
    
    .block-container {
        background: #000000;
    }
    
    h1, h2, h3 {
        color: var(--text-primary) !important;
    }
    
    .stButton>button {
        background: var(--primary);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background: var(--primary-dark);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3, show_spinner=False)
def fetch_latest_anomalies():
    try:
        response = requests.get(LATEST_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    except Exception:
        return []

@st.cache_data(ttl=5, show_spinner=False)
def fetch_anomaly_history(limit=500):
    try:
        response = requests.get(HISTORY_ENDPOINT, params={"limit": limit}, timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            for item in data:
                if isinstance(item.get("issues"), str):
                    item["issues"] = item["issues"].split(",") if item["issues"] else []
            return data
        return []
    except Exception:
        return []

def check_backend_health():
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return response.status_code == 200
    except Exception:
        return False

def send_alert(alert_data):
    try:
        response = requests.post(ALERTS_ENDPOINT, json=alert_data, timeout=5)
        return response.status_code in [200, 503]
    except Exception:
        return False

@st.cache_data(ttl=5, show_spinner=False)
def fetch_telemetry_positions(limit=500):
    try:
        response = requests.get(f"{TELEMETRY_POSITIONS_ENDPOINT}?limit={limit}", timeout=5)
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    except Exception:
        return []

def normalize_anomaly_data(item):
    if "anomaly" in item:
        ann = item.get("anomaly", {})
        return {
            "timestamp": item.get("timestamp"),
            "satellite_id": item.get("satellite_id"),
            "severity": ann.get("severity", "normal"),
            "issues": ann.get("issues", []),
            "score": float(ann.get("score", 0.0))
        }
    else:
        return {
            "timestamp": item.get("timestamp"),
            "satellite_id": item.get("satellite_id"),
            "severity": item.get("severity", "normal"),
            "issues": item.get("issues", []),
            "score": float(item.get("score", 0.0))
        }

def combine_anomaly_data(latest, history):
    combined = []
    
    if latest:
        for item in latest:
            combined.append(normalize_anomaly_data(item))
    
    if history:
        latest_timestamps = {item.get("timestamp") for item in combined}
        for item in history:
            ts = item.get("timestamp")
            if not ts or ts not in latest_timestamps:
                combined.append(normalize_anomaly_data(item))
    
    return combined

def create_severity_gauge(severity_counts):
    total = sum(severity_counts.values())
    if total == 0:
        return None
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = severity_counts.get("critical", 0),
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Critical Anomalies", 'font': {'size': 20}},
        delta = {'reference': total * 0.1},
        gauge = {
            'axis': {'range': [None, total]},
            'bar': {'color': "#EF4444"},
            'steps': [
                {'range': [0, total * 0.3], 'color': "rgba(16, 185, 129, 0.2)"},
                {'range': [total * 0.3, total * 0.7], 'color': "rgba(245, 158, 11, 0.2)"},
                {'range': [total * 0.7, total], 'color': "rgba(239, 68, 68, 0.2)"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': total * 0.9
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font={'color': "#F1F5F9"},
        height=300
    )
    return fig

def create_timeline_chart(df):
    if df.empty:
        return None
    
    fig = go.Figure()
    
    for satellite in df['satellite_id'].unique():
        sat_df = df[df['satellite_id'] == satellite].sort_values('timestamp')
        fig.add_trace(go.Scatter(
            x=sat_df['timestamp'],
            y=sat_df['score'],
            mode='lines+markers',
            name=satellite,
            line=dict(width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        title="Anomaly Score Timeline",
        xaxis_title="Time",
        yaxis_title="Anomaly Score",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font={'color': "#F1F5F9"},
        legend=dict(bgcolor="#000000"),
        height=400,
        hovermode='x unified'
    )
    return fig

def create_severity_pie(severity_counts):
    if sum(severity_counts.values()) == 0:
        return None
    
    colors = {
        "critical": "#EF4444",
        "warning": "#F59E0B",
        "normal": "#10B981"
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=list(severity_counts.keys()),
        values=list(severity_counts.values()),
        hole=0.4,
        marker_colors=[colors.get(k, "#64748B") for k in severity_counts.keys()]
    )])
    
    fig.update_layout(
        title="Severity Distribution",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font={'color': "#F1F5F9"},
        height=350,
        showlegend=True
    )
    return fig

def create_issue_bar_chart(df):
    if df.empty or "issues" not in df.columns:
        return None
    
    df_exploded = df.explode("issues")
    df_exploded = df_exploded[df_exploded["issues"].notna()]
    
    if df_exploded.empty:
        return None
    
    issue_counts = df_exploded["issues"].value_counts().head(10)
    
    fig = go.Figure(data=[go.Bar(
        x=issue_counts.index,
        y=issue_counts.values,
        marker_color="#3B82F6",
        text=issue_counts.values,
        textposition='outside'
    )])
    
    fig.update_layout(
        title="Top Issues Detected",
        xaxis_title="Issue Type",
        yaxis_title="Count",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font={'color': "#F1F5F9"},
        height=400,
        xaxis_tickangle=-45
    )
    return fig

def main():
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("🛰️ Satellite Anomaly Detector")
        st.markdown("**Real-time monitoring dashboard for satellite telemetry and anomaly detection**")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        backend_status = check_backend_health()
        if backend_status:
            st.markdown('<span class="status-badge status-online">● Online</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge status-offline">● Offline</span>', unsafe_allow_html=True)
            st.error("Backend not connected. Start with: `scripts\\start_backend.bat`")
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    with st.spinner("Loading anomaly data..."):
        latest = fetch_latest_anomalies()
        history = fetch_anomaly_history(limit=500)
    
    all_anomalies = combine_anomaly_data(latest, history)
    
    if all_anomalies:
        df = pd.DataFrame(all_anomalies)
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception:
            pass
    else:
        df = pd.DataFrame(columns=["timestamp", "satellite_id", "severity", "issues", "score"])

    with st.sidebar:
        st.header("⚙️ Controls")
        
        satellites = sorted(df['satellite_id'].unique().tolist()) if not df.empty else []
        selected_satellite = st.selectbox(
            "📡 Filter Satellite",
            options=["All"] + satellites,
            index=0
        )
        
        st.markdown("---")
        
        if not df.empty and 'timestamp' in df.columns:
            try:
                min_time = df['timestamp'].min()
                max_time = df['timestamp'].max()
                if pd.notna(min_time) and pd.notna(max_time):
                    min_time_dt = min_time.to_pydatetime() if hasattr(min_time, 'to_pydatetime') else datetime.fromisoformat(str(min_time))
                    max_time_dt = max_time.to_pydatetime() if hasattr(max_time, 'to_pydatetime') else datetime.fromisoformat(str(max_time))
                else:
                    min_time_dt = datetime.now() - timedelta(hours=1)
                    max_time_dt = datetime.now()
                
                time_range = st.slider(
                    "⏱️ Time Range",
                    min_value=min_time_dt,
                    max_value=max_time_dt,
                    value=(min_time_dt, max_time_dt),
                    format="MM/DD HH:mm"
                )
            except Exception as e:
                st.warning(f"Time range filter unavailable: {str(e)}")
                time_range = None
        else:
            time_range = None

        st.markdown("---")
        
        st.subheader("📊 Quick Stats")
        st.metric("Total Anomalies", len(df))
        if not df.empty:
            st.metric("Active Satellites", df['satellite_id'].nunique())
            critical_count = len(df[df['severity'] == 'critical'])
            st.metric("Critical", critical_count, delta=f"{critical_count} active" if critical_count > 0 else None)
        
        st.markdown("---")
        
        auto_refresh = st.checkbox("🔄 Auto-refresh (5s)", value=False)
        if auto_refresh:
            placeholder = st.empty()
            placeholder.info("🔄 Auto-refresh is enabled. Dashboard will refresh every 5 seconds.")
            time.sleep(5)
            placeholder.empty()
            st.rerun()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🚨 Alerts", "📈 Analytics", "🌍 Orbit View"])
    
    with tab1:
        st.subheader("📊 Key Metrics")
        
        if df.empty:
            st.info("📭 No anomaly data available. Start the simulator to generate telemetry data.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total = len(df)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total Anomalies</div>
                    <div class="metric-value">{total}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                critical = len(df[df['severity'] == 'critical']) if not df.empty else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Critical</div>
                    <div class="metric-value" style="color: #EF4444;">{critical}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                warning = len(df[df['severity'] == 'warning']) if not df.empty else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Warnings</div>
                    <div class="metric-value" style="color: #F59E0B;">{warning}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                active_sats = df['satellite_id'].nunique() if not df.empty else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Active Satellites</div>
                    <div class="metric-value" style="color: #3B82F6;">{active_sats}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not df.empty:
                    severity_counts = {
                        "critical": len(df[df['severity'] == 'critical']),
                        "warning": len(df[df['severity'] == 'warning']),
                        "normal": len(df[df['severity'] == 'normal'])
                    }
                    pie_fig = create_severity_pie(severity_counts)
                    if pie_fig:
                        st.plotly_chart(pie_fig, use_container_width=True, key="severity_pie_chart")
            
            with col2:
                if not df.empty and 'timestamp' in df.columns:
                    timeline_fig = create_timeline_chart(df)
                    if timeline_fig:
                        st.plotly_chart(timeline_fig, use_container_width=True, key="timeline_chart")
            
            if not df.empty:
                issue_fig = create_issue_bar_chart(df)
                if issue_fig:
                    st.plotly_chart(issue_fig, use_container_width=True, key="issue_bar_chart")
    
    with tab2:
        st.subheader("🚨 Live Alerts")
        
        if latest:
            filtered_latest = latest
            if selected_satellite != "All":
                filtered_latest = [item for item in latest if item.get("satellite_id") == selected_satellite]
            
            for item in filtered_latest:
                normalized = normalize_anomaly_data(item)
                severity = normalized.get("severity", "normal").lower()
                issues = normalized.get("issues", [])
                
                alert_class = f"alert-{severity}" if severity in ["critical", "warning", "normal"] else "alert-card"
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div class="alert-card {alert_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h3 style="margin: 0; color: var(--text-primary);">{normalized.get('satellite_id', 'Unknown')}</h3>
                                <p style="margin: 4px 0; color: var(--text-secondary); font-size: 12px;">{normalized.get('timestamp', 'N/A')}</p>
                            </div>
                            <div style="text-align: right;">
                                <span class="status-badge status-{severity}" style="font-size: 14px; padding: 6px 14px;">
                                    {severity.upper()}
                                </span>
                            </div>
                        </div>
                        <div style="margin-top: 12px;">
                            <strong>Score:</strong> {normalized.get('score', 0.0):.2f} | 
                            <strong>Issues:</strong> {', '.join(issues) if issues else 'None'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("📤 Send Alert", key=f"send_{normalized.get('timestamp')}_{normalized.get('satellite_id')}"):
                        alert_payload = {
                            "timestamp": normalized.get("timestamp"),
                            "satellite_id": normalized.get("satellite_id"),
                            "severity": normalized.get("severity"),
                            "issues": normalized.get("issues", []),
                            "score": normalized.get("score", 0.0)
                        }
                        if send_alert(alert_payload):
                            st.success("Alert sent!")
                        else:
                            st.warning("Alert service not configured")
        else:
            st.info("📭 No active alerts. All systems normal.")
        
        st.markdown("---")
        st.subheader("📜 Alert History")
        
        if not df.empty:
            display_df = df
            if selected_satellite != "All":
                display_df = df[df['satellite_id'] == selected_satellite]
            
            st.dataframe(
                display_df.sort_values('timestamp', ascending=False).head(50)[
                    ['timestamp', 'satellite_id', 'severity', 'score', 'issues']
                ],
                use_container_width=True,
                height=400
            )
        else:
            st.info("No alert history available.")
    
    with tab3:
        st.subheader("📈 Analytics & Insights")
        
        if df.empty:
            st.info("No data available for analytics.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Severity Trends")
                if 'timestamp' in df.columns and not df.empty:
                    df_trends = df.copy()
                    
                    if not pd.api.types.is_datetime64_any_dtype(df_trends['timestamp']):
                        df_trends['timestamp'] = pd.to_datetime(df_trends['timestamp'], errors='coerce')
                    
                    df_trends = df_trends.dropna(subset=['timestamp'])
                    
                    if not df_trends.empty:
                        time_min = df_trends['timestamp'].min()
                        time_max = df_trends['timestamp'].max()
                        time_span_hours = (time_max - time_min).total_seconds() / 3600
                        
                        if time_span_hours <= 24:
                            df_trends['time_group'] = df_trends['timestamp'].dt.floor('5T')
                            x_col = 'time_group'
                        elif time_span_hours <= 168:
                            df_trends['time_group'] = df_trends['timestamp'].dt.floor('H')
                            x_col = 'time_group'
                        else:
                            df_trends['time_group'] = df_trends['timestamp'].dt.date
                            x_col = 'time_group'
                        
                        severity_trends = df_trends.groupby([x_col, 'severity']).size().reset_index(name='count')
                        severity_trends = severity_trends.sort_values(x_col)
                        
                        if not severity_trends.empty:
                            fig = px.line(
                                severity_trends,
                                x=x_col,
                                y='count',
                                color='severity',
                                title="Anomaly Trends Over Time",
                                color_discrete_map={
                                    "critical": "#EF4444",
                                    "warning": "#F59E0B",
                                    "normal": "#10B981"
                                }
                            )
                            fig.update_layout(
                                paper_bgcolor="#000000",
                                plot_bgcolor="#000000",
                                font={'color': "#F1F5F9"},
                                height=400,
                                xaxis_title="Time",
                                yaxis_title="Count",
                                hovermode='x unified'
                            )
                            st.plotly_chart(fig, use_container_width=True, key="severity_trends_chart")
                        else:
                            st.info("No severity trend data available after grouping.")
                    else:
                        st.info("No valid timestamp data available.")
                else:
                    st.info("Timestamp data not available for trends.")
            
            with col2:
                st.markdown("### Satellite Performance")
                if 'satellite_id' in df.columns:
                    sat_performance = df.groupby('satellite_id').agg({
                        'score': 'mean',
                        'severity': lambda x: (x == 'critical').sum()
                    }).reset_index()
                    sat_performance.columns = ['Satellite', 'Avg Score', 'Critical Count']
                    
                    fig = px.bar(
                        sat_performance,
                        x='Satellite',
                        y='Avg Score',
                        color='Critical Count',
                        title="Average Anomaly Score by Satellite",
                        color_continuous_scale="Reds"
                    )
                    fig.update_layout(
                        paper_bgcolor="#000000",
                        plot_bgcolor="#000000",
                        font={'color': "#F1F5F9"},
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True, key="satellite_performance_chart")
    
    with tab4:
        st.subheader("🌍 Orbit Visualization")
        
        with st.spinner("Loading orbit data..."):
            telemetry_positions = fetch_telemetry_positions(limit=500)
        
        if telemetry_positions:
            pos_df = pd.DataFrame(telemetry_positions)
            
            if not pos_df.empty and all(col in pos_df.columns for col in ['position_x', 'position_y', 'position_z', 'satellite_id', 'timestamp']):
                try:
                    pos_df['timestamp'] = pd.to_datetime(pos_df['timestamp'])
                except Exception:
                    pass
                
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    available_sats = sorted(pos_df['satellite_id'].unique().tolist())
                    selected_sat = st.selectbox(
                        "📡 Select Satellite",
                        options=["All"] + available_sats,
                        index=0,
                        key="orbit_sat_select"
                    )
                
                with col2:
                    view_mode = st.selectbox(
                        "🎥 View Mode",
                        options=["3D Interactive", "2D Orbit Path", "Real-time Animation"],
                        index=0,
                        key="orbit_view_mode"
                    )
                
                with col3:
                    show_velocity = st.checkbox("Show Velocity", value=False, key="show_velocity")
                
                display_df = pos_df if selected_sat == "All" else pos_df[pos_df['satellite_id'] == selected_sat]
                
                if not display_df.empty:
                    if view_mode == "3D Interactive":
                        fig = go.Figure()
                        
                        for sat_id in display_df['satellite_id'].unique():
                            sat_df = display_df[display_df['satellite_id'] == sat_id].sort_values('timestamp')
                            
                            fig.add_trace(go.Scatter3d(
                                x=sat_df['position_x'],
                                y=sat_df['position_y'],
                                z=sat_df['position_z'],
                                mode='lines',
                                name=f'{sat_id} Orbit',
                                line=dict(color='#3A8DFF', width=3),
                                showlegend=True
                            ))
                            
                            latest = sat_df.iloc[-1]
                            fig.add_trace(go.Scatter3d(
                                x=[latest['position_x']],
                                y=[latest['position_y']],
                                z=[latest['position_z']],
                                mode='markers',
                                name=f'{sat_id} Current',
                                marker=dict(
                                    size=12,
                                    color='#EF4444',
                                    symbol='diamond'
                                ),
                                showlegend=True
                            ))
                            
                            if show_velocity and all(col in sat_df.columns for col in ['velocity_x', 'velocity_y', 'velocity_z']):
                                latest = sat_df.iloc[-1]
                                fig.add_trace(go.Cone(
                                    x=[latest['position_x']],
                                    y=[latest['position_y']],
                                    z=[latest['position_z']],
                                    u=[latest['velocity_x']],
                                    v=[latest['velocity_y']],
                                    w=[latest['velocity_z']],
                                    name=f'{sat_id} Velocity',
                                    colorscale='Viridis',
                                    showscale=False,
                                    sizemode="absolute",
                                    sizeref=50
                                ))
                        
                        u = np.linspace(0, 2 * np.pi, 50)
                        v = np.linspace(0, np.pi, 50)
                        earth_radius = 6371
                        x_earth = earth_radius * np.outer(np.cos(u), np.sin(v))
                        y_earth = earth_radius * np.outer(np.sin(u), np.sin(v))
                        z_earth = earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))
                        
                        fig.add_trace(go.Surface(
                            x=x_earth,
                            y=y_earth,
                            z=z_earth,
                            colorscale='Blues',
                            showscale=False,
                            opacity=0.3,
                            name='Earth'
                        ))
                        
                        fig.update_layout(
                            title="🌍 3D Satellite Orbit Visualization",
                            scene=dict(
                                xaxis_title="X (km)",
                                yaxis_title="Y (km)",
                                zaxis_title="Z (km)",
                                aspectmode="data",
                                bgcolor="#000000",
                                xaxis=dict(backgroundcolor="#000000", gridcolor="#333333"),
                                yaxis=dict(backgroundcolor="#000000", gridcolor="#333333"),
                                zaxis=dict(backgroundcolor="#000000", gridcolor="#333333"),
                            ),
                            paper_bgcolor="#000000",
                            plot_bgcolor="#000000",
                            font={'color': "#F1F5F9"},
                            height=700,
                            margin=dict(l=0, r=0, t=50, b=0)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, key="orbit_3d_view")
                    
                    elif view_mode == "2D Orbit Path":
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_xy = go.Figure()
                            for sat_id in display_df['satellite_id'].unique():
                                sat_df = display_df[display_df['satellite_id'] == sat_id].sort_values('timestamp')
                                fig_xy.add_trace(go.Scatter(
                                    x=sat_df['position_x'],
                                    y=sat_df['position_y'],
                                    mode='lines+markers',
                                    name=sat_id,
                                    line=dict(width=2),
                                    marker=dict(size=6)
                                ))
                            
                            fig_xy.update_layout(
                                title="XY Plane (Top View)",
                                xaxis_title="X (km)",
                                yaxis_title="Y (km)",
                                paper_bgcolor="#000000",
                                plot_bgcolor="#000000",
                                font={'color': "#F1F5F9"},
                                height=400
                            )
                            st.plotly_chart(fig_xy, use_container_width=True, key="orbit_xy_view")
                        
                        with col2:
                            fig_xz = go.Figure()
                            for sat_id in display_df['satellite_id'].unique():
                                sat_df = display_df[display_df['satellite_id'] == sat_id].sort_values('timestamp')
                                fig_xz.add_trace(go.Scatter(
                                    x=sat_df['position_x'],
                                    y=sat_df['position_z'],
                                    mode='lines+markers',
                                    name=sat_id,
                                    line=dict(width=2),
                                    marker=dict(size=6)
                                ))
                            
                            fig_xz.update_layout(
                                title="XZ Plane (Side View)",
                                xaxis_title="X (km)",
                                yaxis_title="Z (km)",
                                paper_bgcolor="#000000",
                                plot_bgcolor="#000000",
                                font={'color': "#F1F5F9"},
                                height=400
                            )
                            st.plotly_chart(fig_xz, use_container_width=True, key="orbit_xz_view")
                    
                    else:
                        st.info("Real-time animation mode - shows orbit evolution over time")
                        
                        timestamps = sorted(display_df['timestamp'].unique())
                        frames = []
                        
                        for ts in timestamps:
                            frame_data = display_df[display_df['timestamp'] == ts]
                            traces = []
                            for sat_id in frame_data['satellite_id'].unique():
                                sat_data = frame_data[frame_data['satellite_id'] == sat_id]
                                traces.append(go.Scatter3d(
                                    x=sat_data['position_x'],
                                    y=sat_data['position_y'],
                                    z=sat_data['position_z'],
                                    mode='markers',
                                    name=sat_id,
                                    marker=dict(size=10, color='#3A8DFF')
                                ))
                            frames.append(go.Frame(data=traces, name=str(ts)))
                        
                        fig_anim = go.Figure(
                            data=frames[0].data if frames else [],
                            frames=frames
                        )
                        
                        fig_anim.update_layout(
                            title="🌍 Animated Orbit View",
                            scene=dict(
                                xaxis_title="X (km)",
                                yaxis_title="Y (km)",
                                zaxis_title="Z (km)",
                                aspectmode="data"
                            ),
                            updatemenus=[dict(
                                type="buttons",
                                showactive=False,
                                buttons=[dict(
                                    label="▶ Play",
                                    method="animate",
                                    args=[None, {
                                        "frame": {"duration": 200, "redraw": True},
                                        "fromcurrent": True
                                    }]
                                )]
                            )],
                            paper_bgcolor="#000000",
                            plot_bgcolor="#000000",
                            font={'color': "#F1F5F9"},
                            height=600
                        )
                        
                        st.plotly_chart(fig_anim, use_container_width=True, key="orbit_animation_view")
                    
                    st.markdown("---")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Positions", len(display_df))
                    with col2:
                        avg_x = display_df['position_x'].mean()
                        st.metric("Avg X Position", f"{avg_x:.1f} km")
                    with col3:
                        avg_y = display_df['position_y'].mean()
                        st.metric("Avg Y Position", f"{avg_y:.1f} km")
                    with col4:
                        avg_z = display_df['position_z'].mean()
                        st.metric("Avg Z Position", f"{avg_z:.1f} km")
                        
                else:
                    st.warning(f"No position data available for {selected_sat}")
            else:
                st.warning("Position data incomplete. Missing required fields (position_x, position_y, position_z).")
        else:
            st.info("📡 No orbit data available. Start the simulator to generate telemetry with position data.")

if __name__ == "__main__":
    main()