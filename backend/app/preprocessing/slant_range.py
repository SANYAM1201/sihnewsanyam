from __future__ import annotations

import math
import numpy as np


def slant_range_to_ground_range(slant_range: float, altitude: float) -> float:
    """Calculate horizontal ground range from slant range and towfish altitude.

    Formula: R_g = sqrt(R_s^2 - H_s^2) for R_s >= H_s
    """
    if slant_range < altitude:
        return 0.0
    return math.sqrt(slant_range**2 - altitude**2)


def ground_range_to_slant_range(ground_range: float, altitude: float) -> float:
    """Calculate slant range from ground range and towfish altitude.

    Formula: R_s = sqrt(R_g^2 + H_s^2)
    """
    return math.sqrt(ground_range**2 + altitude**2)


def slant_range_correct(
    ping: np.ndarray,
    altitude: float,
    max_range: float,
    bilateral: bool = False,
    resample_ground_range: bool = False,
) -> np.ndarray:
    """Apply Slant-Range Correction (SRC) to a sonar ping or 2D waterfall image.

    Removes nadir water-column backscatter where R_s < altitude (transducer height
    above seabed), eliminating water-column reverberation and geometric distortion.

    Args:
        ping: 1D array of backscatter samples or 2D image (height, width).
        altitude: Towfish altitude in meters (H_s).
        max_range: Maximum slant range in meters (R_s,max).
        bilateral: True if nadir is in the center (port + stbd), False if at edge.
        resample_ground_range: If True, geometrically resamples R_s -> R_g.

    Returns:
        np.ndarray: Corrected ping or waterfall matrix.
    """
    arr = np.array(ping, copy=True)
    if altitude <= 0 or max_range <= 0:
        return arr

    if arr.ndim == 1:
        n_samples = arr.shape[0]
        nadir_samples = int(n_samples * min(1.0, altitude / max_range))

        if bilateral:
            mid = n_samples // 2
            half_nadir = nadir_samples // 2
            arr[max(0, mid - half_nadir) : min(n_samples, mid + half_nadir)] = 0
        else:
            # Water column occupies index 0 up to nadir arrival
            arr[:nadir_samples] = 0

        if resample_ground_range and altitude < max_range:
            max_rg = math.sqrt(max_range**2 - altitude**2)
            rg_indices = np.linspace(0, max_rg, n_samples)
            rs_indices = np.sqrt(rg_indices**2 + altitude**2)
            sample_coords = (rs_indices / max_range) * (n_samples - 1)
            arr = np.interp(sample_coords, np.arange(n_samples), arr)

    elif arr.ndim == 2:
        h, w = arr.shape
        nadir_samples = int(w * min(1.0, altitude / max_range))

        if bilateral:
            mid = w // 2
            half_nadir = nadir_samples // 2
            arr[:, max(0, mid - half_nadir) : min(w, mid + half_nadir)] = 0
        else:
            arr[:, :nadir_samples] = 0

    return arr


class SlantRangeCorrector:
    """Configurable Slant-Range Correction processor."""

    def __init__(
        self,
        default_altitude: float = 10.0,
        default_max_range: float = 50.0,
        bilateral: bool = False,
    ) -> None:
        self.default_altitude = default_altitude
        self.default_max_range = default_max_range
        self.bilateral = bilateral

    def process(
        self,
        image: np.ndarray,
        altitude: float | None = None,
        max_range: float | None = None,
    ) -> np.ndarray:
        alt = altitude if altitude is not None else self.default_altitude
        rng = max_range if max_range is not None else self.default_max_range
        return slant_range_correct(
            image,
            altitude=alt,
            max_range=rng,
            bilateral=self.bilateral,
        )
