import pytest
import numpy as np
from app.services.bathymetry_service import bathymetry_service


def test_compute_seabed_mesh():
    raw_waterfall = np.random.randint(60, 200, (64, 128), dtype=np.uint8)
    mesh = bathymetry_service.compute_seabed_mesh(
        waterfall_array=raw_waterfall,
        base_altitude_m=12.0,
        base_depth_m=25.0,
        swath_width_m=100.0,
        grid_resolution=16,
    )

    assert "grid_size" in mesh
    assert "point_cloud_3d" in mesh
    assert "wireframe_indices" in mesh
    assert len(mesh["point_cloud_3d"]) > 0
    assert mesh["swath_width_m"] == 100.0
    assert mesh["min_depth_m"] <= mesh["max_depth_m"]
