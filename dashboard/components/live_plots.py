# dashboard/components/live_plots.py
import streamlit as st
import plotly.express as px
import pandas as pd

PLOTLY_DARK_TEMPLATE = "plotly_dark"

def _apply_common(fig, height=320):
    fig.update_layout(
        template=PLOTLY_DARK_TEMPLATE,
        plot_bgcolor="#000000",
        paper_bgcolor="#000000",
        font_color="#E6EEF3",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig

def render_score_trend(df_hist):
    if df_hist.empty:
        st.info("No historical anomaly scores to plot yet.")
        return

    df = df_hist.copy()
    if "timestamp" in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        x = df['timestamp']
    else:
        x = df.index

    # If multiple satellites, color by id, else single line
    try:
        fig = px.line(df, x=x, y="score", color="satellite_id",
                      title="Anomaly Score over Time",
                      labels={"score": "Score (0-1)", "timestamp": "Time"})
    except Exception:
        fig = px.line(df, x=x, y="score", title="Anomaly Score over Time", labels={"score": "Score (0-1)", "timestamp": "Time"})

    fig = _apply_common(fig, height=340)
    fig.update_traces(mode="lines+markers", marker=dict(size=6))
    st.plotly_chart(fig, use_container_width=True)

def render_issue_distribution(df_hist):
    if df_hist.empty:
        st.info("No issue data to show yet.")
        return

    df = df_hist.copy()
    if "issues" not in df.columns:
        st.info("No issue data available.")
        return

    df = df.explode("issues")
    df["issues"] = df["issues"].fillna("Unknown")
    counts = df['issues'].value_counts().reset_index()
    counts.columns = ["issue", "count"]
    fig = px.bar(counts, x="issue", y="count", text="count", title="Issue Frequency (Recent)")
    fig = _apply_common(fig, height=300)
    fig.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig, use_container_width=True)
