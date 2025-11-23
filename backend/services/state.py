# backend/services/state.py
from collections import deque

LATEST_ANOMALIES = deque(maxlen=200)
LATEST_TELEMETRY = deque(maxlen=500)  # Store telemetry with positions

def add_anomaly_record(record: dict):
    LATEST_ANOMALIES.append(record)

def get_latest_anomalies():
    # newest first
    return list(LATEST_ANOMALIES)[::-1]

def add_telemetry_record(record: dict):
    """Store full telemetry record with position data."""
    LATEST_TELEMETRY.append(record)

def get_latest_telemetry(limit: int = 500):
    """Get latest telemetry records with positions (newest first)."""
    return list(LATEST_TELEMETRY)[-limit:][::-1]
