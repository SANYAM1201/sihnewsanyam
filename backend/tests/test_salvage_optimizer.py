import pytest
from app.services.salvage_optimizer import salvage_optimizer, haversine_distance_m


def test_haversine_distance():
    # Distance between Gateway of India and nearby point in Arabian Sea
    d = haversine_distance_m(18.9220, 72.8347, 18.9285, 72.8410)
    assert d > 0
    assert 500 < d < 2000  # approx ~980m


def test_salvage_route_optimization():
    detections = [
        {"id": "TRG-01", "class_label": "Ghost Net", "risk_level": "critical", "latitude": 18.9220, "longitude": 72.8347, "sadh_height_m": 2.1, "depth_m": 14.5},
        {"id": "TRG-02", "class_label": "Cylindrical Drum", "risk_level": "high", "latitude": 18.9285, "longitude": 72.8410, "sadh_height_m": 1.4, "depth_m": 16.2},
        {"id": "TRG-03", "class_label": "Sunken Wreck", "risk_level": "critical", "latitude": 18.9190, "longitude": 72.8490, "sadh_height_m": 4.8, "depth_m": 22.0},
    ]

    plan = salvage_optimizer.optimize_route(detections, vessel_origin=(18.9200, 72.8300))
    assert plan.total_waypoints == 3
    assert plan.total_distance_nm > 0.0
    assert plan.estimated_duration_hours > 0.0
    assert len(plan.waypoints) == 3
    assert plan.recovery_corridor_geojson["type"] == "FeatureCollection"
    assert len(plan.recovery_corridor_geojson["features"][0]["geometry"]["coordinates"]) == 4


def test_empty_salvage_route():
    plan = salvage_optimizer.optimize_route([])
    assert plan.total_waypoints == 0
    assert plan.total_distance_nm == 0.0
