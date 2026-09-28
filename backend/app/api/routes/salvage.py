"""Naval Salvage Mission Planning & 3D Bathymetry API Endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import numpy as np

from app.database import get_db
from app.models.orm import Detection, Run
from app.services.salvage_optimizer import salvage_optimizer
from app.services.bathymetry_service import bathymetry_service

router = APIRouter(prefix="/api/salvage", tags=["salvage"])


@router.get("/route")
@router.get("/runs/{run_id}/route")
async def get_salvage_route(
    run_id: Optional[str] = None,
    cruising_speed: float = 8.0,
    db: Session = Depends(get_db),
) -> dict:
    """Generate risk-prioritized Naval Salvage Recovery Route across detected hazards."""
    query = db.query(Detection)
    if run_id:
        query = query.filter(Detection.run_id == run_id)
    
    dets = query.all()
    if not dets:
        # Provide sample tactical route if no detections stored yet
        sample_dets = [
            {"id": "TRG-01", "class_label": "Ghost Net", "risk_level": "critical", "latitude": 18.9220, "longitude": 72.8347, "sadh_height_m": 2.1, "depth_m": 14.5},
            {"id": "TRG-02", "class_label": "Cylindrical Drum", "risk_level": "high", "latitude": 18.9285, "longitude": 72.8410, "sadh_height_m": 1.4, "depth_m": 16.2},
            {"id": "TRG-03", "class_label": "Sunken Wreck", "risk_level": "critical", "latitude": 18.9190, "longitude": 72.8490, "sadh_height_m": 4.8, "depth_m": 22.0},
            {"id": "TRG-04", "class_label": "Subsea Pipeline Breach", "risk_level": "medium", "latitude": 18.9340, "longitude": 72.8310, "sadh_height_m": 1.2, "depth_m": 18.0},
        ]
        plan = salvage_optimizer.optimize_route(sample_dets, cruising_speed_knots=cruising_speed)
        return {
            "status": "success",
            "source": "simulated_tactical_scenario",
            "plan": plan.__dict__,
        }

    raw_items = [
        {
            "id": d.id,
            "class_label": d.class_label,
            "risk_level": d.risk_level,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "sadh_height_m": d.sadh_height_m,
            "depth_m": d.depth_m,
        }
        for d in dets
    ]

    plan = salvage_optimizer.optimize_route(raw_items, cruising_speed_knots=cruising_speed)
    return {
        "status": "success",
        "run_id": run_id,
        "plan": plan.__dict__,
    }


@router.get("/bathymetry/mesh")
@router.get("/runs/{run_id}/bathymetry")
async def get_bathymetry_mesh(
    run_id: Optional[str] = None,
    altitude: float = 12.0,
    depth: float = 25.0,
    swath_width: float = 100.0,
) -> dict:
    """Generate 3D seafloor bathymetric relief points for terrain contour visualization."""
    # Synthetic waterfall slice for rapid 3D reconstruction
    waterfall = np.random.randint(50, 220, (64, 128), dtype=np.uint8)
    mesh_data = bathymetry_service.compute_seabed_mesh(
        waterfall_array=waterfall,
        base_altitude_m=altitude,
        base_depth_m=depth,
        swath_width_m=swath_width,
    )
    return {
        "status": "success",
        "run_id": run_id,
        "bathymetry": mesh_data,
    }
