from __future__ import annotations

import math
import re

from app.schemas.detection import BoundingBox, DetectionItem

METERS_PER_DEGREE_LAT = 111_320.0
_DEFAULT_METERS_PER_PIXEL = 0.5


def parse_meters_per_pixel(resolution: str | None) -> float:
    if not resolution:
        return _DEFAULT_METERS_PER_PIXEL
    match = re.search(r"([0-9]*\.?[0-9]+)", str(resolution))
    if not match:
        return _DEFAULT_METERS_PER_PIXEL
    value = float(match.group(1))
    return value if value > 0 else _DEFAULT_METERS_PER_PIXEL


def georeference_offset(
    origin_lat: float,
    origin_lng: float,
    east_m: float,
    north_m: float,
    heading: float = 0.0,
) -> tuple[float, float]:
    """Calculate target WGS84 coordinate given origin, offsets, and vessel heading.

    Args:
        origin_lat: Origin latitude in degrees.
        origin_lng: Origin longitude in degrees.
        east_m: Cross-track / East offset in meters.
        north_m: Along-track / North offset in meters.
        heading: Vessel heading/azimuth in degrees clockwise from true north.
    """
    if heading != 0.0:
        rad = math.radians(heading)
        eff_east = east_m * math.cos(rad) + north_m * math.sin(rad)
        eff_north = -east_m * math.sin(rad) + north_m * math.cos(rad)
    else:
        eff_east = east_m
        eff_north = north_m

    try:
        import pyproj

        geod = pyproj.Geod(ellps="WGS84")
        dist = math.hypot(eff_east, eff_north)
        if dist < 1e-4:
            return round(origin_lat, 7), round(origin_lng, 7)
        azimuth = math.degrees(math.atan2(eff_east, eff_north)) % 360.0
        target_lon, target_lat, _ = geod.fwd(origin_lng, origin_lat, azimuth, dist)
        return round(float(target_lat), 7), round(float(target_lon), 7)
    except Exception:
        lat = origin_lat + eff_north / METERS_PER_DEGREE_LAT
        cos_lat = math.cos(math.radians(origin_lat))
        meters_per_deg_lng = METERS_PER_DEGREE_LAT * max(abs(cos_lat), 1e-6)
        lng = origin_lng + eff_east / meters_per_deg_lng
        return round(lat, 7), round(lng, 7)


def georeference_bbox(
    origin_lat: float | None,
    origin_lng: float | None,
    bbox: BoundingBox | None,
    resolution: str | None,
    heading: float = 0.0,
) -> tuple[float | None, float | None]:
    """Map a detection box to WGS84 using the scan origin as image (0, 0).

    Pixel +x is east, pixel +y (down the image) is south. The scan lat/lng is
    the vessel/georeference point, not a shared pin for every object.
    """
    if origin_lat is None or origin_lng is None:
        return None, None
    if bbox is None:
        return round(float(origin_lat), 7), round(float(origin_lng), 7)

    meters_per_px = parse_meters_per_pixel(resolution)
    center_x = bbox.x + bbox.width / 2.0
    center_y = bbox.y + bbox.height / 2.0
    east_m = center_x * meters_per_px
    north_m = -center_y * meters_per_px
    return georeference_offset(
        float(origin_lat), float(origin_lng), east_m, north_m, heading=heading
    )


def with_detection_coordinates(
    item: DetectionItem,
    origin_lat: float | None,
    origin_lng: float | None,
    resolution: str | None,
    heading: float = 0.0,
) -> DetectionItem:
    lat, lng = georeference_bbox(
        origin_lat, origin_lng, item.bbox, resolution, heading=heading
    )
    return item.model_copy(update={"latitude": lat, "longitude": lng})
