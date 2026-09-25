import pytest
import numpy as np
from app.services.sadh_physics import (
    estimate_target_height,
    compute_physics_confidence,
    extract_sadh_from_bbox,
)
from app.services.xtf_parser import (
    create_synthetic_xtf,
    parse_xtf_bytes,
    XtfParseError,
)


class TestSadhPhysics:
    def test_height_formula(self):
        # h_est = (L * H_s) / R_s
        # L = 10m, H_s = 15m, R_s = 50m -> h_est = 150 / 50 = 3.0m
        h = estimate_target_height(shadow_length_m=10.0, altitude_m=15.0, slant_range_m=50.0)
        assert abs(h - 3.0) < 1e-3

    def test_zero_or_negative_inputs(self):
        assert estimate_target_height(0, 15.0, 50.0) == 0.0
        assert estimate_target_height(10.0, 0.0, 50.0) == 0.0
        assert estimate_target_height(10.0, 15.0, 0.0) == 0.0

    def test_physics_confidence_elevated_with_shadow(self):
        conf = compute_physics_confidence(
            class_label="shipwreck",
            detection_conf=0.85,
            estimated_height_m=2.5,
            has_shadow=True,
        )
        assert conf >= 0.80

    def test_physics_confidence_elevated_missing_shadow_penalty(self):
        conf_with_shadow = compute_physics_confidence(
            class_label="shipwreck",
            detection_conf=0.85,
            estimated_height_m=2.5,
            has_shadow=True,
        )
        conf_no_shadow = compute_physics_confidence(
            class_label="shipwreck",
            detection_conf=0.85,
            estimated_height_m=0.0,
            has_shadow=False,
        )
        assert conf_no_shadow < conf_with_shadow
        assert conf_no_shadow <= 0.55


class TestXtfParser:
    def test_synthetic_xtf_generation_and_parsing(self):
        xtf_data = create_synthetic_xtf(num_pings=32, samples_per_channel=256)
        assert len(xtf_data) >= 1024

        waterfall, meta = parse_xtf_bytes(xtf_data)
        assert waterfall.ndim == 2
        assert waterfall.shape[0] == 31 or waterfall.shape[0] == 32
        assert waterfall.shape[1] == 512  # 256 port + 256 starboard
        assert meta["num_pings"] > 0
        assert "avg_latitude" in meta
        assert "avg_longitude" in meta
        assert "avg_heading_deg" in meta

    def test_corrupt_xtf_rejected(self):
        bad_xtf = b"FAKE_XTF_HEADER" + b"\x00" * 1024
        with pytest.raises(XtfParseError):
            parse_xtf_bytes(bad_xtf)
