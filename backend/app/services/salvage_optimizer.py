"""Naval Salvage Mission Planner & Autonomous Route Optimizer.

Calculates risk-prioritized recovery paths, transit nautical miles, fuel/battery expenditure,
and clearance sequencing for maritime operations (Indian Navy, Coast Guard, Salvage Operators).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two WGS-84 coordinates in meters."""
    r = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


RISK_WEIGHTS = {
    "critical": 1.0,
    "high": 0.8,
    "medium": 0.5,
    "low": 0.2,
}


@dataclass
class SalvageWaypoint:
    target_id: str
    class_label: str
    risk_level: str
    latitude: float
    longitude: float
    target_height_m: float
    depth_m: float
    priority_rank: int = 0
    distance_from_prev_nm: float = 0.0
    est_clearance_time_mins: int = 30


@dataclass
class SalvageMissionPlan:
    mission_id: str
    origin_coords: Tuple[float, float]
    total_waypoints: int
    total_distance_nm: float
    estimated_duration_hours: float
    highest_threat_class: str
    waypoints: List[Dict[str, Any]] = field(default_factory=list)
    recovery_corridor_geojson: Dict[str, Any] = field(default_factory=dict)


class SalvageRouteOptimizer:
    """Autonomous route planning and risk-ranked recovery scheduler."""

    def optimize_route(
        self,
        detections: List[Dict[str, Any]],
        vessel_origin: Optional[Tuple[float, float]] = None,
        cruising_speed_knots: float = 8.0,
    ) -> SalvageMissionPlan:
        if not detections:
            return SalvageMissionPlan(
                mission_id="MSN-SALVAGE-EMPTY",
                origin_coords=vessel_origin or (18.9220, 72.8347),
                total_waypoints=0,
                total_distance_nm=0.0,
                estimated_duration_hours=0.0,
                highest_threat_class="None",
            )

        valid_targets = []
        for d in detections:
            lat = d.get("latitude")
            lon = d.get("longitude")
            if lat is not None and lon is not None:
                valid_targets.append(d)

        if not valid_targets:
            valid_targets = detections

        # Default origin to first target or Mumbai Naval Base
        origin_lat = vessel_origin[0] if vessel_origin else float(valid_targets[0].get("latitude", 18.9220))
        origin_lon = vessel_origin[1] if vessel_origin else float(valid_targets[0].get("longitude", 72.8347))

        # Sort targets by combined heuristic: Risk Urgency + Proximity (Greedy TSP with Risk Bias)
        unvisited = list(valid_targets)
        current_lat, current_lon = origin_lat, origin_lon
        ordered_waypoints: List[SalvageWaypoint] = []
        total_dist_m = 0.0

        step = 1
        while unvisited:
            best_idx = 0
            best_score = float("inf")
            best_dist = 0.0

            for i, target in enumerate(unvisited):
                t_lat = float(target.get("latitude", current_lat))
                t_lon = float(target.get("longitude", current_lon))
                dist_m = haversine_distance_m(current_lat, current_lon, t_lat, t_lon)

                risk = str(target.get("risk_level", "medium")).lower()
                weight = RISK_WEIGHTS.get(risk, 0.5)

                # Score combines distance with priority (lower is chosen first)
                # High risk heavily discounts distance, pulling urgent targets earlier
                score = dist_m / (1.0 + weight * 2.0)

                if score < best_score:
                    best_score = score
                    best_idx = i
                    best_dist = dist_m

            chosen = unvisited.pop(best_idx)
            t_lat = float(chosen.get("latitude", current_lat))
            t_lon = float(chosen.get("longitude", current_lon))
            total_dist_m += best_dist

            dist_nm = best_dist / 1852.0  # meters to nautical miles

            # Estimate salvage time based on class & height
            cls_name = str(chosen.get("class_label", "Debris")).lower()
            h_m = float(chosen.get("sadh_height_m", 1.0) or 1.0)
            if "net" in cls_name:
                clearance_time = 45
            elif "wreck" in cls_name:
                clearance_time = 90
            elif "cylinder" in cls_name or "pipe" in cls_name:
                clearance_time = 60
            else:
                clearance_time = max(20, int(h_m * 25))

            ordered_waypoints.append(
                SalvageWaypoint(
                    target_id=str(chosen.get("id", f"TRG-{step:02d}")),
                    class_label=str(chosen.get("class_label", "Marine Debris")),
                    risk_level=str(chosen.get("risk_level", "HIGH")).upper(),
                    latitude=t_lat,
                    longitude=t_lon,
                    target_height_m=round(h_m, 2),
                    depth_m=round(float(chosen.get("depth_m", 15.0) or 15.0), 1),
                    priority_rank=step,
                    distance_from_prev_nm=round(dist_nm, 3),
                    est_clearance_time_mins=clearance_time,
                )
            )

            current_lat, current_lon = t_lat, t_lon
            step += 1

        total_nm = total_dist_m / 1852.0
        transit_hours = total_nm / max(cruising_speed_knots, 1.0)
        total_clearance_hours = sum(w.est_clearance_time_mins for w in ordered_waypoints) / 60.0
        est_duration = round(transit_hours + total_clearance_hours, 2)

        # Build GeoJSON navigation line
        coordinates = [[origin_lon, origin_lat]] + [
            [w.longitude, w.latitude] for w in ordered_waypoints
        ]

        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                    "properties": {
                        "name": "Naval Salvage Recovery Trajectory",
                        "total_distance_nm": round(total_nm, 2),
                        "estimated_duration_hrs": est_duration,
                    },
                }
            ],
        }

        # Threat breakdown
        risk_counts = {}
        for w in ordered_waypoints:
            risk_counts[w.risk_level] = risk_counts.get(w.risk_level, 0) + 1
        highest_threat = "CRITICAL" if "CRITICAL" in risk_counts else ("HIGH" if "HIGH" in risk_counts else "MEDIUM")

        return SalvageMissionPlan(
            mission_id=f"MSN-SALV-{len(ordered_waypoints)}TGT",
            origin_coords=(origin_lat, origin_lon),
            total_waypoints=len(ordered_waypoints),
            total_distance_nm=round(total_nm, 2),
            estimated_duration_hours=est_duration,
            highest_threat_class=highest_threat,
            waypoints=[w.__dict__ for w in ordered_waypoints],
            recovery_corridor_geojson=geojson,
        )


salvage_optimizer = SalvageRouteOptimizer()
