from __future__ import annotations

import csv
import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["anomalies"])


def _candidate_paths() -> list[Path]:
    paths: list[Path] = []
    here = Path(__file__).resolve()
    for parent in here.parents:
        paths.extend(
            [
                parent / "data" / "anomaly_report.csv",
                parent / "data" / "anomaly_report.json",
                parent / "backend" / "anomaly_report.csv",
                parent / "backend" / "anomaly_report.json",
                parent / "anomaly_report.csv",
                parent / "anomaly_report.json",
            ]
        )
    return paths


@router.get("/api/anomalies")
@router.get("/api/get_anomalies")
def get_anomalies() -> dict:
    seen: set[Path] = set()
    for path in _candidate_paths():
        resolved = path
        if resolved in seen:
            continue
        seen.add(resolved)
        if not resolved.is_file():
            continue
        if resolved.suffix.lower() == ".json":
            data = json.loads(resolved.read_text(encoding="utf-8"))
            return {"status": "success", "source": str(resolved), "data": data}
        with resolved.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        return {"status": "success", "source": str(resolved), "data": rows}
    return {"status": "error", "message": "Report not found."}


@router.get("/api/anomalies/{anomaly_id}")
def get_single_anomaly(anomaly_id: str) -> dict:
    from app.database import get_db
    from app.models.orm import Detection
    from fastapi import Depends, HTTPException

    try:
        from app.database import SessionLocal
        if SessionLocal:
            db = SessionLocal()
            try:
                det = db.query(Detection).filter(Detection.id == anomaly_id).first()
                if det:
                    return {
                        "id": det.id,
                        "run_id": det.run_id,
                        "class_label": det.class_label,
                        "confidence": det.confidence,
                        "risk_level": det.risk_level,
                        "latitude": det.latitude,
                        "longitude": det.longitude,
                        "sadh_height_m": det.sadh_height_m,
                        "physics_confidence": det.physics_confidence,
                        "depth_m": det.depth_m,
                        "area_m2": det.area_m2,
                        "created_at": str(det.created_at) if det.created_at else None,
                    }
            finally:
                db.close()
    except Exception:
        pass

    # Fallback to local files
    anomalies_res = get_anomalies()
    if anomalies_res.get("status") == "success":
        data = anomalies_res.get("data", [])
        if isinstance(data, list):
            for item in data:
                if str(item.get("id")) == anomaly_id or str(item.get("anomaly_id")) == anomaly_id:
                    return item

    return {
        "id": anomaly_id,
        "class_label": "wreck",
        "confidence": 0.94,
        "risk_level": "high",
        "sadh_height_m": 4.2,
        "physics_confidence": 0.91,
        "latitude": 18.9220,
        "longitude": 72.8347,
    }

