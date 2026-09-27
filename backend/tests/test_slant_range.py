import numpy as np
import pytest

from app.preprocessing.slant_range import (
    SlantRangeCorrector,
    ground_range_to_slant_range,
    slant_range_correct,
    slant_range_to_ground_range,
)


def test_conversions():
    # R_g = sqrt(R_s^2 - H_s^2)
    # 5, 3 -> 4
    assert slant_range_to_ground_range(5.0, 3.0) == 4.0
    # when slant_range < altitude -> 0.0
    assert slant_range_to_ground_range(2.0, 3.0) == 0.0

    # R_s = sqrt(R_g^2 + H_s^2)
    # 4, 3 -> 5
    assert ground_range_to_slant_range(4.0, 3.0) == 5.0


def test_slant_range_correct_1d():
    ping = np.ones(100, dtype=np.float32)
    # altitude <= 0 or max_range <= 0 returns copy
    res_noop = slant_range_correct(ping, altitude=0, max_range=50)
    assert np.array_equal(res_noop, ping)

    # 1D unilateral
    res = slant_range_correct(ping, altitude=10, max_range=50, bilateral=False)
    # 10/50 = 0.2 -> first 20 samples zeroed
    assert np.all(res[:20] == 0)
    assert np.all(res[20:] == 1)

    # 1D bilateral
    res_bi = slant_range_correct(ping, altitude=10, max_range=50, bilateral=True)
    # nadir_samples = 20, half = 10, mid = 50 -> [40:60] zeroed
    assert np.all(res_bi[40:60] == 0)
    assert np.all(res_bi[:40] == 1)
    assert np.all(res_bi[60:] == 1)

    # 1D with resample_ground_range
    res_resample = slant_range_correct(ping, altitude=10, max_range=50, resample_ground_range=True)
    assert len(res_resample) == 100


def test_slant_range_correct_2d():
    img = np.ones((50, 100), dtype=np.float32)
    # 2D unilateral
    res = slant_range_correct(img, altitude=10, max_range=50, bilateral=False)
    assert np.all(res[:, :20] == 0)
    assert np.all(res[:, 20:] == 1)

    # 2D bilateral
    res_bi = slant_range_correct(img, altitude=10, max_range=50, bilateral=True)
    assert np.all(res_bi[:, 40:60] == 0)
    assert np.all(res_bi[:, :40] == 1)
    assert np.all(res_bi[:, 60:] == 1)


def test_slant_range_corrector_class():
    corrector = SlantRangeCorrector(default_altitude=10.0, default_max_range=50.0, bilateral=False)
    img = np.ones((10, 100), dtype=np.float32)
    out = corrector.process(img)
    assert out.shape == img.shape
    assert np.all(out[:, :20] == 0)

    # override params
    out_override = corrector.process(img, altitude=20.0, max_range=50.0)
    assert np.all(out_override[:, :40] == 0)
