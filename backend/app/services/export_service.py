"""Export detections as CSV, JSON, or Report."""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.models.orm import Detection, Run

logger = logging.getLogger(__name__)


class ExportService:
    HEADERS = [
        "id",
        "detection_id",
        "run_id",
        "class_label",
        "confidence",
        "risk_level",
        "bbox_x",
        "bbox_y",
        "bbox_width",
        "bbox_height",
        "depth_m",
        "area_m2",
        "latitude",
        "longitude",
        "sadh_height_m",
        "physics_confidence",
        "position_info",
        "created_at",
    ]

    def __init__(self, db: Session) -> None:
        self.db = db

    def _query(self, run_id: Optional[str] = None, limit: int = 1000, offset: int = 0) -> list[Detection]:
        q = self.db.query(Detection)
        if run_id:
            q = q.filter(Detection.run_id == run_id)
        return q.limit(limit).offset(offset).all()

    def to_dict(self, d: Detection) -> dict[str, Any]:
        return {h: getattr(d, h, None) for h in self.HEADERS}

    def to_csv(self, run_id: Optional[str] = None, limit: int = 1000, offset: int = 0) -> str:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(self.HEADERS)
        for d in self._query(run_id, limit, offset):
            row = self.to_dict(d)
            w.writerow([row.get(h) for h in self.HEADERS])
        return buf.getvalue()

    def to_json(self, run_id: Optional[str] = None, limit: int = 1000, offset: int = 0) -> str:
        return json.dumps([self.to_dict(d) for d in self._query(run_id, limit, offset)], indent=2, default=str)

    def to_geojson(self, run_id: Optional[str] = None, limit: int = 1000, offset: int = 0) -> dict[str, Any]:
        from app.services.pdf_report_service import NavalPDFReportService

        svc = NavalPDFReportService()
        dets = [
            {
                "id": d.id,
                "label": d.class_label,
                "confidence": d.confidence,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "height_m": d.sadh_height_m,
                "shadow_length_m": (d.bbox_height or 0.0) * 0.1,
                "physics_verified": (d.physics_confidence or 1.0) >= 0.6,
            }
            for d in self._query(run_id, limit, offset)
        ]
        return svc.export_detections_geojson(dets)

    def generate_dossier_pdf(self, run_id: Optional[str] = None) -> str:
        from app.services.pdf_report_service import NavalPDFReportService

        svc = NavalPDFReportService()
        run = self.db.query(Run).filter(Run.id == run_id).first() if run_id else None
        mission_info = {
            "mission_id": run.mission_id if run else "MSN-GLOBAL",
            "vessel": "INS Sandhayak (J18)",
            "area": "Indian Ocean Operations",
            "swath_width_m": 100.0,
            "altitude_m": 12.0,
        }
        dets = [
            {
                "id": d.id[:8],
                "label": d.class_label,
                "confidence": d.confidence,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "height_m": d.sadh_height_m or 1.2,
                "shadow_length_m": (d.bbox_height or 20.0) * 0.1,
                "physics_verified": (d.physics_confidence or 1.0) >= 0.6,
            }
            for d in self._query(run_id)
        ]
        pdf_path = svc.generate_salvage_dossier(mission_info, dets)
        return str(pdf_path)

    def run_report(self, run_id: str) -> dict[str, Any]:
        run = self.db.query(Run).filter(Run.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")
        dets = self._query(run_id)
        n = len(dets)
        return {
            "run": {
                "id": run.id,
                "mission_id": run.mission_id,
                "filename": run.filename,
                "created_at": str(run.created_at),
            },
            "stats": {
                "total": n,
                "avg_confidence": sum(d.confidence for d in dets) / n if n else 0,
                "by_class": {cls: sum(1 for d in dets if d.class_label == cls) for cls in set(d.class_label for d in dets)},
                "by_risk": {lvl: sum(1 for d in dets if d.risk_level == lvl) for lvl in set(d.risk_level for d in dets)},
            },
            "detections": [self.to_dict(d) for d in dets],
        }

