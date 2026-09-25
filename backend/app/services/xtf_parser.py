"""Pure-Python eXtended Triton Format (XTF) hydrographic parser.

Reads Triton XTF side-scan sonar files:
- 1024-byte Triton File Header (Magic 0xFACE / 0x7B)
- Ping packets (XTF_PING_HEADER): extracts ping number, time, altitude, depth,
  heading, latitude, longitude, and slant range
- Channel acoustic data: extracts Port and Starboard acoustic sweeps and
  reconstructs a calibrated waterfall sonogram.
"""

from __future__ import annotations

import io
import math
import struct
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class XtfPingTelemetry:
    ping_number: int
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    sensor_depth_m: float
    sensor_altitude_m: float
    sensor_heading_deg: float
    sensor_pitch_deg: float
    sensor_roll_deg: float
    latitude: float
    longitude: float
    slant_range_m: float
    num_samples_port: int
    num_samples_stbd: int


class XtfParseError(Exception):
    """Raised when an XTF file is corrupt or violates Triton specification."""


def parse_xtf_bytes(data: bytes) -> tuple[np.ndarray, dict[str, Any]]:
    """Parse raw bytes of an XTF file and reconstruct waterfall sonogram.

    Args:
        data: Raw binary content of an .xtf file.

    Returns:
        tuple (waterfall_image, metadata):
            waterfall_image: 2D uint8 numpy array of shape (N_pings, 2 * samples_per_channel)
            metadata: dictionary containing ping count, telemetry list, and summary navigation.
    """
    if len(data) < 1024:
        raise XtfParseError("File is smaller than 1024-byte XTF header")

    # Read File Header
    file_format = data[0]
    system_type = data[1]
    num_sonar_channels = struct.unpack_from("<H", data, 142)[0]

    if file_format != 0x7B and data[:2] != b"\xface":
        # Check Triton magic number
        magic = struct.unpack_from("<H", data, 0)[0]
        if magic != 0xFACE and file_format != 123:
            raise XtfParseError(f"Invalid XTF header signature (magic={magic:#x}, format={file_format})")

    port_pings: list[np.ndarray] = []
    stbd_pings: list[np.ndarray] = []
    telemetry: list[XtfPingTelemetry] = []

    offset = 1024
    total_len = len(data)

    while offset + 64 <= total_len:
        # Check packet header
        magic = struct.unpack_from("<H", data, offset)[0]
        if magic != 0xFACE:
            # Advance byte by byte if unsynchronized
            offset += 1
            continue

        header_type = data[offset + 2]
        num_bytes_record = struct.unpack_from("<I", data, offset + 4)[0]

        if num_bytes_record <= 0 or offset + num_bytes_record > total_len:
            break

        # HeaderType 0 = Sonar Ping Header
        if header_type == 0:
            ping_hdr_offset = offset
            # Unpack ping header fields
            try:
                (
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    second,
                    hsec,
                ) = struct.unpack_from("<HBBBBBB", data, ping_hdr_offset + 8)
                ping_num = struct.unpack_from("<I", data, ping_hdr_offset + 16)[0]
                sound_vel = struct.unpack_from("<f", data, ping_hdr_offset + 20)[0]
                sensor_depth = struct.unpack_from("<f", data, ping_hdr_offset + 32)[0]
                pitch = struct.unpack_from("<f", data, ping_hdr_offset + 36)[0]
                roll = struct.unpack_from("<f", data, ping_hdr_offset + 40)[0]
                heading = struct.unpack_from("<f", data, ping_hdr_offset + 44)[0]
                altitude = struct.unpack_from("<f", data, ping_hdr_offset + 52)[0]
                raw_y = struct.unpack_from("<d", data, ping_hdr_offset + 80)[0]  # Lat
                raw_x = struct.unpack_from("<d", data, ping_hdr_offset + 88)[0]  # Lon

                # Channel headers offset: ping header is 256 bytes
                chan_hdr_offset = ping_hdr_offset + 256
                # Channel 0: Port
                port_samples = struct.unpack_from("<I", data, chan_hdr_offset + 36)[0]
                port_slant_range = struct.unpack_from("<f", data, chan_hdr_offset + 12)[0]

                # Channel 1: Starboard
                chan1_offset = chan_hdr_offset + 64
                stbd_samples = struct.unpack_from("<I", data, chan1_offset + 36)[0]
                stbd_slant_range = struct.unpack_from("<f", data, chan1_offset + 12)[0]

                # Extract acoustic samples
                data_offset = ping_hdr_offset + 256 + (64 * 2)
                p_data = np.frombuffer(
                    data[data_offset : data_offset + port_samples], dtype=np.uint8
                )
                s_data = np.frombuffer(
                    data[data_offset + port_samples : data_offset + port_samples + stbd_samples],
                    dtype=np.uint8,
                )

                if len(p_data) == port_samples and len(s_data) == stbd_samples:
                    port_pings.append(p_data)
                    stbd_pings.append(s_data)
                    telemetry.append(
                        XtfPingTelemetry(
                            ping_number=ping_num,
                            year=year,
                            month=month,
                            day=day,
                            hour=hour,
                            minute=minute,
                            second=second,
                            sensor_depth_m=sensor_depth,
                            sensor_altitude_m=altitude,
                            sensor_heading_deg=heading,
                            sensor_pitch_deg=pitch,
                            sensor_roll_deg=roll,
                            latitude=raw_y,
                            longitude=raw_x,
                            slant_range_m=max(port_slant_range, stbd_slant_range),
                            num_samples_port=port_samples,
                            num_samples_stbd=stbd_samples,
                        )
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug("Skipping corrupt or unparseable ping record: %s", e)

        offset += num_bytes_record

    if not port_pings or not stbd_pings:
        raise XtfParseError("No valid sonar ping records found in XTF file")

    # Align ping lengths
    n_pings = len(port_pings)
    max_p = max(len(p) for p in port_pings)
    max_s = max(len(s) for s in stbd_pings)

    # Waterfall layout: Port swath is flipped so nadir meets at the center:
    # [Far Port <--- Nadir ---> Far Starboard]
    waterfall = np.zeros((n_pings, max_p + max_s), dtype=np.uint8)
    for i in range(n_pings):
        p_slice = np.flip(port_pings[i])  # flip port so nadir is at center
        s_slice = stbd_pings[i]
        waterfall[i, : len(p_slice)] = p_slice
        waterfall[i, max_p : max_p + len(s_slice)] = s_slice

    avg_lat = float(np.mean([t.latitude for t in telemetry])) if telemetry else 0.0
    avg_lon = float(np.mean([t.longitude for t in telemetry])) if telemetry else 0.0
    avg_heading = float(np.mean([t.sensor_heading_deg for t in telemetry])) if telemetry else 0.0
    avg_altitude = float(np.mean([t.sensor_altitude_m for t in telemetry])) if telemetry else 15.0
    avg_range = float(np.mean([t.slant_range_m for t in telemetry])) if telemetry else 50.0

    meta = {
        "num_pings": n_pings,
        "width_px": waterfall.shape[1],
        "height_px": waterfall.shape[0],
        "avg_latitude": avg_lat,
        "avg_longitude": avg_lon,
        "avg_heading_deg": avg_heading,
        "avg_altitude_m": avg_altitude,
        "avg_slant_range_m": avg_range,
        "pings": telemetry,
    }

    return waterfall, meta


def create_synthetic_xtf(
    num_pings: int = 128,
    samples_per_channel: int = 512,
    lat0: float = 12.9716,
    lon0: float = 80.2520,
    heading_deg: float = 45.0,
    altitude_m: float = 12.0,
    speed_knots: float = 4.0,
) -> bytes:
    """Generate a fully compliant Triton XTF file with simulated sonar pings."""
    buf = io.BytesIO()

    # 1. 1024-byte Triton File Header
    hdr = bytearray(1024)
    hdr[0] = 0x7B  # File format
    hdr[1] = 1  # Sonar
    hdr[2:10] = b"ISIS    "
    hdr[10:18] = b"7.00    "
    hdr[18:34] = b"SonarSentry SSS "
    struct.pack_into("<H", hdr, 34, 1)  # SonarType = 1 (Klein/Edgetech SSS)
    hdr[36:100] = b"Simulated Hydrographic Survey Trackline\x00"
    hdr[100:164] = b"survey_track_01.xtf\x00"
    struct.pack_into("<H", hdr, 142, 2)  # 2 Sonar channels (Port, Starboard)
    hdr[144] = 3  # NavUnits = Lat/Lon

    # Channel info: Port (chan 0)
    c0 = 146
    hdr[c0 : c0 + 16] = b"Port            "
    hdr[c0 + 16] = 1  # Type: Subbottom/Sidescan
    struct.pack_into("<H", hdr, c0 + 20, samples_per_channel)

    # Channel info: Starboard (chan 1)
    c1 = 146 + 128
    hdr[c1 : c1 + 16] = b"Starboard       "
    hdr[c1 + 16] = 2  # Type: Sidescan starboard
    struct.pack_into("<H", hdr, c1 + 20, samples_per_channel)

    buf.write(hdr)

    # 2. Ping Packets
    speed_mps = speed_knots * 0.514444
    dt_ping = 0.1  # 10 Hz ping rate

    for ping_idx in range(num_pings):
        # Navigation track progression
        dist_m = ping_idx * speed_mps * dt_ping
        rad = math.radians(heading_deg)
        d_lat = (dist_m * math.cos(rad)) / 111320.0
        d_lon = (dist_m * math.sin(rad)) / (111320.0 * math.cos(math.radians(lat0)))
        cur_lat = lat0 + d_lat
        cur_lon = lon0 + d_lon

        # Packet header (64 bytes)
        pkt_len = 256 + 128 + (samples_per_channel * 2)
        pkt_hdr = bytearray(256)
        struct.pack_into("<H", pkt_hdr, 0, 0xFACE)  # Magic
        pkt_hdr[2] = 0  # Sonar Ping Packet
        pkt_hdr[3] = 0  # Sub-channel
        struct.pack_into("<I", pkt_hdr, 4, pkt_len)  # NumBytesThisRecord
        struct.pack_into("<H", pkt_hdr, 8, 2026)  # Year
        pkt_hdr[10] = 9  # Month
        pkt_hdr[11] = 26  # Day
        pkt_hdr[12] = 12  # Hour
        pkt_hdr[13] = 0  # Min
        pkt_hdr[14] = int(ping_idx * dt_ping) % 60
        pkt_hdr[15] = int((ping_idx * dt_ping * 100) % 100)
        struct.pack_into("<I", pkt_hdr, 16, ping_idx + 1)  # PingNumber
        struct.pack_into("<f", pkt_hdr, 20, 1500.0)  # SoundVelocity m/s
        struct.pack_into("<f", pkt_hdr, 32, 5.0)  # SensorDepth m
        struct.pack_into("<f", pkt_hdr, 44, heading_deg)  # SensorHeading
        struct.pack_into("<f", pkt_hdr, 52, altitude_m)  # SensorAltitude
        struct.pack_into("<d", pkt_hdr, 80, cur_lat)  # RawSensorY
        struct.pack_into("<d", pkt_hdr, 88, cur_lon)  # RawSensorX

        # Channel 0 Ping Header (64 bytes)
        chan0_hdr = bytearray(64)
        struct.pack_into("<H", chan0_hdr, 0, 0)  # Channel 0
        struct.pack_into("<f", chan0_hdr, 12, 50.0)  # SlantRange 50m
        struct.pack_into("<I", chan0_hdr, 36, samples_per_channel)

        # Channel 1 Ping Header (64 bytes)
        chan1_hdr = bytearray(64)
        struct.pack_into("<H", chan1_hdr, 0, 1)  # Channel 1
        struct.pack_into("<f", chan1_hdr, 12, 50.0)  # SlantRange 50m
        struct.pack_into("<I", chan1_hdr, 36, samples_per_channel)

        # Acoustic Data: Backscatter + nadir blind zone + synthetic target
        # Port channel
        port_samples = np.random.randint(60, 95, size=samples_per_channel, dtype=np.uint8)
        # Water column blind zone near nadir (first 80 samples)
        blind_samples = int((altitude_m / 50.0) * samples_per_channel)
        port_samples[:blind_samples] = np.random.randint(5, 20, size=blind_samples, dtype=np.uint8)

        # Starboard channel
        stbd_samples = np.random.randint(60, 95, size=samples_per_channel, dtype=np.uint8)
        stbd_samples[:blind_samples] = np.random.randint(5, 20, size=blind_samples, dtype=np.uint8)

        # Inject synthetic marine debris signature on starboard around ping 60-70
        if 55 <= ping_idx <= 75:
            target_start = blind_samples + 120
            target_len = 25
            # Bright acoustic return
            stbd_samples[target_start : target_start + target_len] = np.random.randint(210, 255, size=target_len, dtype=np.uint8)
            # Acoustic shadow immediately behind it
            shadow_len = 40
            stbd_samples[target_start + target_len : target_start + target_len + shadow_len] = np.random.randint(2, 15, size=shadow_len, dtype=np.uint8)

        buf.write(pkt_hdr)
        buf.write(chan0_hdr)
        buf.write(chan1_hdr)
        buf.write(port_samples.tobytes())
        buf.write(stbd_samples.tobytes())

    return buf.getvalue()
