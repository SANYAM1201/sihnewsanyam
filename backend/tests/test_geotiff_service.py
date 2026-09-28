import pytest
import numpy as np
from pathlib import Path

try:
    import rasterio
    from rasterio.transform import from_bounds
except ImportError:
    rasterio = None

from backend.app.services.geospatial.geotiff_service import GeoTIFFService


def make_synthetic_swath(bbox, file_path):
    if rasterio is None:
        return
    data = np.random.randint(50, 200, (3, 100, 100), dtype=np.uint8)
    transform = from_bounds(*bbox, 100, 100)
    with rasterio.open(
        file_path,
        "w",
        driver="GTiff",
        height=100,
        width=100,
        count=3,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data)


@pytest.mark.skipif(rasterio is None, reason="rasterio is not installed")
def test_overlapping_raster_merge_no_crash(tmp_path):
    """Two synthetic swaths with 30% geographic overlap must blend without error."""
    service = GeoTIFFService(export_dir=tmp_path)
    
    run_a = "swath_run_a"
    run_b = "swath_run_b"
    file_a = tmp_path / f"{run_a}.tif"
    file_b = tmp_path / f"{run_b}.tif"
    
    make_synthetic_swath((80.0, 12.0, 81.0, 13.0), file_a)
    make_synthetic_swath((80.7, 12.0, 81.7, 13.0), file_b)  # 30% overlap on longitude
    
    result = service.blend_swath_mosaic([run_a, run_b])
    assert result is not None
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result.startswith(b"\x89PNG")
