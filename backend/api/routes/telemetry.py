# backend/api/routes/telemetry.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from fastapi import Query
from backend.services.preprocess import preprocess_telemetry
from backend.services.anomaly_engine import compute_anomaly
from backend.services.state import add_anomaly_record, add_telemetry_record, get_latest_telemetry
from backend.core.database import SessionLocal     # adjust name if your file is database.py
from backend.core.models import AnomalyEvent
from ...core.logger import logger

router = APIRouter(tags=["Telemetry"])

# Define Pydantic schema inline or import from api/schemas.py if you prefer
class TelemetrySchema(BaseModel):
    timestamp: str
    satellite_id: str
    position_x: float
    position_y: float
    position_z: float
    velocity_x: float
    velocity_y: float
    velocity_z: float
    temp_payload: float
    temp_battery: float
    temp_bus: float
    sensor1_value: float
    sensor2_value: float
    sensor3_value: float
    comms_rssi: float
    comms_snr: float
    comms_packet_loss: float

@router.post("/", status_code=200)
async def receive_telemetry(data: TelemetrySchema):
    try:
        logger.info(f"Received telemetry for {data.satellite_id} at {data.timestamp}")
        features = preprocess_telemetry(data.dict())
        anomaly = compute_anomaly(features)

        record = {
            "timestamp": data.timestamp,
            "satellite_id": data.satellite_id,
            "anomaly": anomaly
        }

        # add to in-memory
        add_anomaly_record(record)
        
        # Store full telemetry with positions for orbit visualization
        telemetry_record = data.dict()
        telemetry_record["timestamp"] = data.timestamp
        add_telemetry_record(telemetry_record)

        # persist to DB
        db = SessionLocal()
        try:
            if isinstance(data.timestamp, str):
                timestamp_dt = datetime.fromisoformat(data.timestamp.replace('Z', '+00:00'))
            else:
                timestamp_dt = data.timestamp
            
            db_event = AnomalyEvent(
                timestamp=timestamp_dt,
                satellite_id=data.satellite_id,
                severity=anomaly.get("severity", "normal"),
                issue=",".join(anomaly.get("issues", [])), 
                score=float(anomaly.get("score", 0.0))
            )
            db.add(db_event)
            db.commit()
        finally:
            db.close()

        return {"status": "ok", **record}
    except Exception as e:
        logger.error(f"Error in /telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
def get_telemetry_positions(limit: int = Query(500, ge=1, le=1000)):
    """Get recent telemetry records with position data for orbit visualization."""
    try:
        telemetry_records = get_latest_telemetry(limit=limit)
        # Format for frontend - only include position and essential data
        result = []
        for record in telemetry_records:
            result.append({
                "timestamp": record.get("timestamp"),
                "satellite_id": record.get("satellite_id"),
                "position_x": record.get("position_x"),
                "position_y": record.get("position_y"),
                "position_z": record.get("position_z"),
                "velocity_x": record.get("velocity_x"),
                "velocity_y": record.get("velocity_y"),
                "velocity_z": record.get("velocity_z"),
            })
        return {"data": result}
    except Exception as e:
        logger.error(f"Error in /telemetry/positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
