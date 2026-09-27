"""Forward-Azimuth WGS84 Geodesy Engine and Towfish Layback Engine.

Implements ellipsoidal geodesic projection with:
- Towfish heading azimuth & cable layback compensation
- Cross-track port/starboard offsets
- WGS84 ellipsoid parameters (semi-major axis, flattening)
- Ping index to geodetic coordinate mapping
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import logging

import numpy as np

logger = logging.getLogger(__name__)

# WGS84 ellipsoid parameters
WGS84_A = 6378137.0  # Semi-major axis (meters)
WGS84_F = 1 / 298.257223563  # Flattening
WGS84_E2 = 2 * WGS84_F - WGS84_F**2  # Square of eccentricity

try:
    import pyproj
    from pyproj import CRS, Geod, Transformer

    _GEOD = Geod(ellps="WGS84")
except ImportError:
    pyproj = None
    _GEOD = None


@dataclass
class GeodeticCoordinate:
    """Geodetic coordinate (latitude, longitude, altitude)."""

    lat: float  # Degrees
    lon: float  # Degrees
    alt: float = 0.0  # Meters (height above ellipsoid)


@dataclass
class ProjectedCoordinate:
    """Projected coordinate (easting, northing, altitude)."""

    easting: float  # Meters
    northing: float  # Meters
    alt: float = 0.0  # Meters


@dataclass
class SonarPing:
    """Sonar ping with navigation and acoustic geometry data."""

    ping_number: int
    timestamp: float = 0.0  # Seconds since midnight
    latitude: float = 0.0  # Degrees
    longitude: float = 0.0  # Degrees
    altitude: float = 10.0  # Towfish altitude (H_s) in meters
    heading: float = 0.0  # Vessel heading in degrees (0-360)
    speed: float = 5.0  # Vessel speed in knots
    beam_width: float = 40.0  # Beam width in degrees
    num_beams: int = 512  # Number of beams
    sample_rate: float = 100000.0  # Sample rate in Hz
    slant_range: float = 100.0  # Slant range (R_s) in meters
    frequency: float = 400000.0  # Frequency in Hz
    num_samples: int = 1000
    cross_track_offset: float = 0.0  # Cross-track offset in meters


class WGS84Geodesy:
    """WGS84 Geodesy Engine for Side-Scan Sonar.

    Implements forward-azimuth projection with ellipsoidal corrections.
    """

    def __init__(self):
        self.geod = _GEOD
        self.wgs84 = CRS.from_epsg(4326) if pyproj else None
        self.utm_crs: Optional[CRS] = None
        self.utm_zone: Optional[str] = None
        self.transformer: Optional[Transformer] = None
        self.ref_lat: float = 0.0
        self.ref_lon: float = 0.0
        self.towfish_offset: float = 0.0

    def set_reference_point(self, lat: float, lon: float) -> None:
        """Set reference point and configure UTM zone transformer."""
        self.ref_lat = lat
        self.ref_lon = lon
        zone = int((lon + 180) // 6) + 1
        if lon >= 0:
            self.utm_zone = f"326{zone:02d}"
        else:
            self.utm_zone = f"327{zone:02d}"

        if pyproj:
            self.utm_crs = CRS.from_string(f"EPSG:{self.utm_zone}")
            self.transformer = Transformer.from_crs(self.wgs84, self.utm_crs, always_xy=True)
        logger.info("Set reference point: (%f, %f), UTM zone: %s", lat, lon, self.utm_zone)

    def geodetic_to_utm(self, lat: float, lon: float) -> Tuple[float, float]:
        if self.transformer is None:
            self.set_reference_point(lat, lon)
        if self.transformer:
            return self.transformer.transform(lon, lat)
        return lon * 111320.0, lat * 111320.0

    def utm_to_geodetic(self, easting: float, northing: float) -> Tuple[float, float]:
        if self.transformer is None:
            raise ValueError("Reference point not set. Call set_reference_point() first.")
        lon, lat = self.transformer.itransform(easting, northing)
        return lat, lon

    def geodesic_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        if self.geod:
            _, _, distance = self.geod.inv(lon1, lat1, lon2, lat2)
            return distance
        meters_per_deg = 111320.0
        return math.hypot((lat2 - lat1) * meters_per_deg, (lon2 - lon1) * meters_per_deg * math.cos(math.radians(lat1)))

    def forward_azimuth(
        self, lat: float, lon: float, distance: float, azimuth: float, alt: float = 0.0
    ) -> Tuple[float, float, float]:
        if self.geod:
            new_lon, new_lat, _ = self.geod.fwd(lon, lat, azimuth, distance)
            return float(new_lat), float(new_lon), alt

        meters_per_deg_lat = 111320.0
        d_north = distance * math.cos(math.radians(azimuth))
        d_east = distance * math.sin(math.radians(azimuth))
        new_lat = lat + d_north / meters_per_deg_lat
        meters_per_deg_lon = meters_per_deg_lat * max(abs(math.cos(math.radians(lat))), 1e-6)
        new_lon = lon + d_east / meters_per_deg_lon
        return float(new_lat), float(new_lon), alt

    def calculate_ground_range(self, slant_range: float, altitude: float) -> float:
        return math.sqrt(max(0.0, slant_range**2 - altitude**2))

    def calculate_slant_range(self, ground_range: float, altitude: float) -> float:
        return math.sqrt(ground_range**2 + altitude**2)

    def ping_to_coordinates(
        self,
        reference: GeodeticCoordinate,
        ping: SonarPing,
        beam_index: int,
        sample_index: int,
        beam_angle: Optional[float] = None,
    ) -> GeodeticCoordinate:
        num_beams = max(1, getattr(ping, "num_beams", 512))
        num_samples = max(1, getattr(ping, "num_samples", 1000))
        altitude = getattr(ping, "altitude", 10.0)
        slant_range_max = getattr(ping, "slant_range", 100.0)
        heading = getattr(ping, "heading", 0.0)

        # Cross-track fraction from nadir (-1 port to +1 starboard)
        center_beam = num_beams / 2.0
        frac_across = (beam_index - center_beam) / max(center_beam, 1.0)
        ground_range_max = self.calculate_ground_range(slant_range_max, altitude)
        cross_track_m = frac_across * ground_range_max

        # Along-track from sample index (waterfall along-track)
        along_track_m = ((sample_index - num_samples / 2.0) / num_samples) * 50.0

        # Rotate relative to heading
        rad = math.radians(heading)
        eff_east = cross_track_m * math.cos(rad) + along_track_m * math.sin(rad)
        eff_north = -cross_track_m * math.sin(rad) + along_track_m * math.cos(rad)

        dist = math.hypot(eff_east, eff_north)
        if dist < 1e-4:
            return GeodeticCoordinate(lat=round(reference.lat, 7), lon=round(reference.lon, 7), alt=-altitude)

        azimuth = math.degrees(math.atan2(eff_east, eff_north)) % 360.0
        new_lat, new_lon, _ = self.forward_azimuth(reference.lat, reference.lon, dist, azimuth)
        return GeodeticCoordinate(lat=round(new_lat, 7), lon=round(new_lon, 7), alt=-altitude)

    def beam_to_coordinates(
        self, reference: GeodeticCoordinate, ping: SonarPing, beam_data: np.ndarray
    ) -> List[GeodeticCoordinate]:
        coordinates = []
        H, W = beam_data.shape
        for beam_idx in range(H):
            for sample_idx in range(W):
                if beam_data[beam_idx, sample_idx] > 0:
                    coordinates.append(self.ping_to_coordinates(reference, ping, beam_idx, sample_idx))
        return coordinates

    def offset_point(
        self, origin_lat: float, origin_lon: float, cross_track_m: float, along_track_m: float, heading: float
    ) -> Tuple[float, float]:
        rad = math.radians(heading)
        eff_east = cross_track_m * math.cos(rad) + along_track_m * math.sin(rad)
        eff_north = -cross_track_m * math.sin(rad) + along_track_m * math.cos(rad)
        dist = math.hypot(eff_east, eff_north)
        if dist < 1e-4:
            return round(origin_lat, 7), round(origin_lon, 7)
        azimuth = math.degrees(math.atan2(eff_east, eff_north)) % 360.0
        new_lat, new_lon, _ = self.forward_azimuth(origin_lat, origin_lon, dist, azimuth)
        return round(new_lat, 7), round(new_lon, 7)

    def compute_swath_bounds(
        self, center_lat: float, center_lon: float, heading: float, swath_width_m: float, track_length_m: float
    ) -> Dict[str, Any]:
        half_swath = swath_width_m / 2.0
        half_track = track_length_m / 2.0
        corners_local = [
            (-half_swath, half_track),
            (half_swath, half_track),
            (half_swath, -half_track),
            (-half_swath, -half_track),
        ]
        geo_corners = []
        for ct, at in corners_local:
            lat, lon = self.offset_point(center_lat, center_lon, ct, at, heading)
            geo_corners.append([lon, lat])
        geo_corners.append(geo_corners[0])

        lats = [c[1] for c in geo_corners]
        lons = [c[0] for c in geo_corners]
        return {
            "type": "Polygon",
            "coordinates": [geo_corners],
            "bbox": [min(lons), min(lats), max(lons), max(lats)],
            "center": [center_lon, center_lat],
            "swath_width_m": swath_width_m,
            "track_length_m": track_length_m,
        }

    def compute_towfish_position(
        self,
        vessel_lat: float,
        vessel_lon: float,
        vessel_heading: float,
        cable_out_m: float,
        towfish_depth_m: float,
        layback_offset_m: float = 0.0,
    ) -> Tuple[float, float, float]:
        if cable_out_m > towfish_depth_m:
            horizontal_layback = math.sqrt(cable_out_m**2 - towfish_depth_m**2) + layback_offset_m
        else:
            horizontal_layback = layback_offset_m

        if horizontal_layback <= 0.0:
            return round(vessel_lat, 7), round(vessel_lon, 7), 0.0

        trailing_azimuth = (vessel_heading + 180.0) % 360.0
        t_lat, t_lon, _ = self.forward_azimuth(vessel_lat, vessel_lon, horizontal_layback, trailing_azimuth)
        return round(t_lat, 7), round(t_lon, 7), round(horizontal_layback, 2)


# Alias for backward compatibility
GeodesyEngine = WGS84Geodesy
geodesy_engine = WGS84Geodesy()
