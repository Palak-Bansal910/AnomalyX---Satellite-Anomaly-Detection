# dashboard/components/orbit_visualizer.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# soft blue accent used for markers
ACCENT = "#3A8DFF"
MARKER_COLOR = "#9FB7FF"

def build_frames(df, sat_list):
    frames = []
    timestamps = sorted(df['timestamp'].unique())
    for t in timestamps:
        sub = df[df['timestamp'] == t]
        data = []
        for sat in sat_list:
            sat_sub = sub[sub['satellite_id'] == sat]
            if not sat_sub.empty:
                data.append(go.Scatter(x=sat_sub['position_x'], y=sat_sub['position_y'],
                                       mode='markers',
                                       marker=dict(size=8, color=ACCENT),
                                       name=sat, showlegend=False))
        frames.append(go.Frame(data=data, name=str(t)))
    return frames, timestamps

def render_orbit_visualizer(history_records, selected_satellite=None, play=False, slider_index=0):
    # assemble DataFrame with positions
    rows = []
    for r in history_records:
        px = r.get("position_x") or r.get("pos_x") or r.get("x")
        py = r.get("position_y") or r.get("pos_y") or r.get("y")
        if px is None or py is None:
            continue
        try:
            rows.append({
                "timestamp": pd.to_datetime(r.get("timestamp")),
                "satellite_id": r.get("satellite_id") or "SAT-UNK",
                "position_x": float(px),
                "position_y": float(py)
            })
        except Exception:
            continue

    if len(rows) == 0:
        st.info("Position data unavailable from backend. Showing placeholder.")
        return

    df = pd.DataFrame(rows).sort_values("timestamp")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    sat_list = sorted(df['satellite_id'].unique())

    # if a particular satellite selected, only show that one in static view
    frames, timestamps = build_frames(df, sat_list)

    # base figure (dark)
    fig = go.Figure()
    first_t = timestamps[0]
    first_df = df[df['timestamp'] == first_t]

    for sat in sat_list:
        sat_df = first_df[first_df['satellite_id'] == sat]
        fig.add_trace(go.Scatter(
            x=sat_df['position_x'],
            y=sat_df['position_y'],
            mode='markers',
            marker=dict(size=8, color=MARKER_COLOR),
            name=sat,
            showlegend=True
        ))

    # layout
    fig.update_layout(
        plot_bgcolor="#000000",
        paper_bgcolor="#000000",
        font=dict(color="#E6EEF3"),
        title=f"Orbit positions over time (frames: {len(timestamps)})",
        xaxis=dict(title="X (km)", gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(title="Y (km)", gridcolor="rgba(255,255,255,0.04)"),
        height=520,
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=1,
            x=1.12,
            xanchor="right",
            yanchor="top",
            buttons=[dict(label="Play",
                          method="animate",
                          args=[None, {"frame": {"duration": 400, "redraw": True},
                                       "fromcurrent": True, "transition": {"duration": 200}}])])]
    )

    fig.frames = frames

    # render according to play flag
    if not play:
        # static frame at slider_index (if available)
        idx = max(0, min(slider_index, len(timestamps)-1))
        ts = timestamps[idx]
        sub = df[df['timestamp'] == ts]
        fig2 = go.Figure()
        for sat in sat_list:
            if selected_satellite and sat != selected_satellite:
                continue
            sat_sub = sub[sub['satellite_id'] == sat]
            fig2.add_trace(go.Scatter(x=sat_sub['position_x'], y=sat_sub['position_y'], mode='markers', marker=dict(size=8, color=ACCENT), name=sat))
        fig2.update_layout(plot_bgcolor="#000000", paper_bgcolor="#000000", font=dict(color="#E6EEF3"), title=f"Positions at {ts}", xaxis_title="X (km)", yaxis_title="Y (km)", height=520)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.plotly_chart(fig, use_container_width=True)
