import numpy as np
import pytest

from app.services.sadh_physics import (
    compute_physics_confidence,
    estimate_target_height,
    extract_sadh_from_bbox,
)


def test_estimate_target_height():
    # zero altitude or slant range
    assert estimate_target_height(10.0, 0.0, 50.0) == 0.0
    assert estimate_target_height(10.0, 15.0, 0.0) == 0.0
    assert estimate_target_height(-5.0, 15.0, 50.0) == 0.0

    # (L * H_s) / R_s = (10.0 * 15.0) / 50.0 = 3.0
    assert estimate_target_height(10.0, 15.0, 50.0) == 3.0


def test_compute_physics_confidence():
    # Elevated class with shadow and height
    conf_high = compute_physics_confidence("Shipwreck", 0.9, 2.5, has_shadow=True)
    assert 0.8 < conf_high <= 0.99

    # Elevated class without shadow -> penalized
    conf_low = compute_physics_confidence("Pipe", 0.9, 0.0, has_shadow=False)
    assert conf_low < 0.6

    # Non-elevated class (e.g. net or sediment)
    conf_net_shadow = compute_physics_confidence("Net", 0.8, 0.1, has_shadow=True)
    assert conf_net_shadow > 0.7

    conf_net_noshadow = compute_physics_confidence("Net", 0.8, 0.0, has_shadow=False)
    assert conf_net_noshadow > 0.6


def test_extract_sadh_from_bbox_with_mask():
    mask = np.zeros((100, 200), dtype=np.uint8)
    # Put shadow on starboard side of bbox
    mask[20:40, 140:170] = 255

    # Starboard bbox (center x > 0.5)
    shadow_len, has_shadow = extract_sadh_from_bbox(
        bbox_x=0.6,
        bbox_y=0.2,
        bbox_w=0.1,
        bbox_h=0.2,
        img_w=200,
        img_h=100,
        altitude_m=15.0,
        range_res_m=0.05,
        shadow_mask=mask,
    )
    assert has_shadow is True
    assert shadow_len > 0

    # Port bbox (center x < 0.5)
    mask_port = np.zeros((100, 200), dtype=np.uint8)
    mask_port[20:40, 10:40] = 255
    shadow_len_p, has_shadow_p = extract_sadh_from_bbox(
        bbox_x=0.25,
        bbox_y=0.2,
        bbox_w=0.1,
        bbox_h=0.2,
        img_w=200,
        img_h=100,
        altitude_m=15.0,
        range_res_m=0.05,
        shadow_mask=mask_port,
    )
    assert has_shadow_p is True
    assert shadow_len_p > 0


def test_extract_sadh_from_bbox_aspect_ratio_fallback():
    # Wide box (aspect ratio > 1.2) without mask
    shadow_len, has_shadow = extract_sadh_from_bbox(
        bbox_x=0.5,
        bbox_y=0.5,
        bbox_w=0.3,
        bbox_h=0.1,
        img_w=200,
        img_h=100,
        altitude_m=15.0,
        range_res_m=0.05,
    )
    assert has_shadow is True
    assert shadow_len > 0
