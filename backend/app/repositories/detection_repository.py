from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.orm import Detection


class DetectionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, **kwargs) -> Detection:
        detection = Detection(**kwargs)
        self._db.add(detection)
        self._db.commit()
        self._db.refresh(detection)
        return detection

    def create_many(self, detections: list[dict]) -> list[Detection]:
        objects = [Detection(**d) for d in detections]
        self._db.add_all(objects)
        self._db.commit()
        for obj in objects:
            self._db.refresh(obj)
        return objects

    def get(self, detection_id: str) -> Detection | None:
        return self._db.query(Detection).filter(Detection.id == detection_id).first()

    def list_by_run(self, run_id: str) -> list[Detection]:
        return (
            self._db.query(Detection)
            .filter(Detection.run_id == run_id)
            .order_by(Detection.created_at.desc())
            .all()
        )

    def count_by_run(self, run_id: str) -> int:
        return self._db.query(Detection).filter(Detection.run_id == run_id).count()

    def list_all(self, limit: int = 200) -> list[Detection]:
        return (
            self._db.query(Detection)
            .order_by(Detection.created_at.desc())
            .limit(limit)
            .all()
        )

