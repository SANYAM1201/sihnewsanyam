"""Domain-specific Side-Scan Sonar (SSS) processing operations.

Implements acoustic corrections inspired by SidescanTools / SonarSuite:
1. Column-wise Beam Angle Correction (BAC) gain normalization
2. 2D-FFT horizontal stripe noise filtration
3. Homomorphic edge sharpening
"""

from __future__ import annotations

import logging

import cv2
import numpy as np
from scipy import fft

logger = logging.getLogger(__name__)


class SidescanProcessor:
    """Preprocesses raw side-scan sonar image arrays with acoustic corrections."""

    def __init__(
        self,
        apply_bac: bool = True,
        apply_stripe_filter: bool = True,
        apply_sharpening: bool = True,
        apply_bld: bool = False,
    ) -> None:
        self.apply_bac = apply_bac
        self.apply_stripe_filter = apply_stripe_filter
        self.apply_sharpening = apply_sharpening
        self.apply_bld = apply_bld
        self.last_bottom_line: np.ndarray | None = None

    def process(self, image: np.ndarray) -> np.ndarray:
        """Apply configured SSS corrections to input image.

        Args:
            image: uint8 NumPy array of shape (H, W) or (H, W, 3).

        Returns:
            Processed uint8 NumPy array with same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError("Input image must be a numpy.ndarray")
        if image.size == 0:
            raise ValueError("Input image array is empty")

        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

        result = image.copy()

        # Step 1: Column-wise Beam Angle Correction (Gain Normalization)
        if self.apply_bac:
            try:
                result = self._apply_bac(result)
            except Exception as e:
                logger.warning(f"BAC normalization failed: {e}. Skipping stage.")

        # Step 2: 2D-FFT Stripe Noise Filter (Towfish heave / horizontal line noise)
        if self.apply_stripe_filter:
            try:
                result = self._apply_stripe_filter(result)
            except Exception as e:
                logger.warning(f"Stripe noise filter failed: {e}. Skipping stage.")

        # Step 3: Homomorphic Sharpening (Separates acoustic illumination & reflectance)
        if self.apply_sharpening:
            try:
                result = self._apply_homomorphic(result)
            except Exception as e:
                logger.warning(f"Homomorphic sharpening failed: {e}. Skipping stage.")

        # Step 4: Bottom-Line Detection (BLD) if enabled
        if self.apply_bld:
            try:
                self.last_bottom_line = self.detect_bottom_line(result)
            except Exception as e:
                logger.warning(f"BLD detection failed: {e}. Skipping stage.")

        return result

    def get_bottom_line(self) -> np.ndarray | None:
        """Return the most recently detected bottom line array, or None."""
        return self.last_bottom_line

    def _apply_bac(self, image: np.ndarray) -> np.ndarray:
        """Column-wise Beam Angle Correction (BAC).

        Acoustic energy drops as grazing angle flattens across range columns.
        Normalizes each range column by its mean intensity profile.
        """
        is_color = len(image.shape) == 3 and image.shape[2] == 3

        if is_color:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
        else:
            gray = image.astype(np.float32)

        # Compute column means across pings (axis 0)
        col_means = np.mean(gray, axis=0, keepdims=True)
        global_mean = float(np.mean(col_means))
        if global_mean <= 1e-3:
            return image

        # Avoid zero-division on completely black columns (e.g. padding/blind zone)
        col_means = np.where(col_means < 1.0, 1.0, col_means)

        # Scale each column so its mean equals the global average
        scale_factor = global_mean / col_means

        if is_color:
            # Broadcast across all 3 channels
            scaled = image.astype(np.float32) * scale_factor[:, :, np.newaxis]
        else:
            scaled = gray * scale_factor

        return np.clip(scaled, 0, 255).astype(np.uint8)

    def _apply_stripe_filter(self, image: np.ndarray, notch_width: int = 4) -> np.ndarray:
        """2D-FFT horizontal stripe removal.

        Towfish heave, acoustic ping interference, or electrical noise creates
        horizontal scanlines across SSS waterfall records. In 2D frequency
        space, horizontal lines concentrate along the vertical frequency axis
        (u ~ 0, v != 0). A notch filter attenuates these frequencies.

        Optimized for performance: processes single-channel luminance in YCrCb
        and uses 2x downsampling for large imagery (>640px) to achieve <15ms execution.
        """
        h, w = image.shape[:2]
        if h < 8 or w < 8:
            return image

        is_color = len(image.shape) == 3 and image.shape[2] == 3

        if is_color:
            # Check if all 3 channels are identical (common for grayscale RGB)
            if np.array_equal(image[..., 0], image[..., 1]) and np.array_equal(image[..., 0], image[..., 2]):
                filtered_ch = self._apply_single_channel_stripe_filter(image[..., 0], notch_width=notch_width)
                return np.repeat(filtered_ch[..., np.newaxis], 3, axis=-1)

            # In acoustic sonar, acoustic backscatter is encoded in Luminance (Y).
            # Filtering Y in YCrCb avoids chromatic distortion and gives 3x speedup.
            ycrcb = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
            ycrcb[..., 0] = self._apply_single_channel_stripe_filter(ycrcb[..., 0], notch_width=notch_width)
            return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)

        return self._apply_single_channel_stripe_filter(image, notch_width=notch_width)

    def _apply_single_channel_stripe_filter(
        self, channel: np.ndarray, notch_width: int = 4
    ) -> np.ndarray:
        h, w = channel.shape[:2]
        if h < 8 or w < 8:
            return channel

        # Downsample large images (>640px) for 2D FFT to achieve ~10x speedup
        downsample = (h > 640 or w > 640)
        if downsample:
            target_h = max(64, h // 2)
            target_w = max(64, w // 2)
            proc_img = cv2.resize(channel, (target_w, target_h), interpolation=cv2.INTER_AREA)
        else:
            proc_img = channel

        fh, fw = proc_img.shape[:2]
        img_float = proc_img.astype(np.float32)

        # 2D Fast Fourier Transform
        fft_img = fft.fft2(img_float)
        fft_shifted = fft.fftshift(fft_img)

        # Create notch filter along center column (u == 0 axis)
        crow, ccol = fh // 2, fw // 2
        mask = np.ones((fh, fw), dtype=np.float32)

        # Notch along the horizontal line frequency axis (u == 0)
        half_w = max(0, (notch_width - 1) // 2)
        mask[:, max(0, ccol - half_w) : min(fw, ccol + half_w + 1)] = 0.35
        # Restore DC neighborhood so overall image brightness is preserved
        dc_rad = 3
        mask[
            max(0, crow - dc_rad) : min(fh, crow + dc_rad + 1),
            max(0, ccol - dc_rad) : min(fw, ccol + dc_rad + 1),
        ] = 1.0

        fft_filtered = fft_shifted * mask
        fft_inv_shifted = fft.ifftshift(fft_filtered)
        filtered = np.real(fft.ifft2(fft_inv_shifted))
        norm_uint8 = np.clip(filtered, 0, 255).astype(np.uint8)

        if downsample:
            return cv2.resize(norm_uint8, (w, h), interpolation=cv2.INTER_LINEAR)
        return norm_uint8

    def _apply_homomorphic(self, image: np.ndarray) -> np.ndarray:
        """Simplified homomorphic filtering for acoustic images.

        Separates illumination (low frequency) from reflectance / structural
        target edges (high frequency) via log transform and high-pass unsharp mask.
        Optimized with YCrCb color space and physical scale preservation.
        """
        is_color = len(image.shape) == 3 and image.shape[2] == 3

        if is_color:
            ycrcb = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
            lum_channel = ycrcb[..., 0].astype(np.float32)
        else:
            lum_channel = image.astype(np.float32)

        # Log transform
        log_l = np.log1p(lum_channel)

        # Low-pass estimation of illumination via Gaussian blur
        ksize = 25
        blurred = cv2.GaussianBlur(log_l, (ksize, ksize), sigmaX=8)

        # High-pass amplification of reflectance
        sharpened_log = 0.9 * blurred + 1.12 * (log_l - blurred)

        # Inverse exponential transform
        result_l = np.expm1(sharpened_log)
        norm_l = np.clip(result_l, 0, 255).astype(np.uint8)

        if is_color:
            ycrcb[..., 0] = norm_l
            return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)

        return norm_l

    def detect_bottom_line(
        self, image: np.ndarray, threshold_factor: float = 2.0
    ) -> np.ndarray:
        """Detect the Bottom Line (first seafloor contact / water column boundary).

        In side-scan sonar waterfall records, the water column directly beneath
        the towfish has very low backscatter (acoustic shadow / blind zone).
        The seafloor appears as the first strong return signal.

        Args:
            image: uint8 NumPy array of shape (H, W) or (H, W, 3).
            threshold_factor: Multiplier above water-column noise floor for seafloor contact.

        Returns:
            1D array of length W containing the detected row index of the seafloor
            for each column across range.
        """
        return self._detect_bottom_line(image, threshold_factor=threshold_factor)

    def _detect_bottom_line(
        self, image: np.ndarray, threshold_factor: float = 2.0
    ) -> np.ndarray:
        """Internal implementation of Bottom-Line Detection (BLD)."""
        if len(image.shape) == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        elif len(image.shape) == 2:
            gray = image
        else:
            gray = image[..., 0]

        h, w = gray.shape[:2]
        if h < 4 or w < 4:
            return np.zeros(w, dtype=np.int32)

        # Light vertical smoothing to reduce ping speckle without excessive edge blur
        ksize_y = min(5, max(3, (h // 20) | 1))
        smoothed = cv2.GaussianBlur(gray, (1, ksize_y), sigmaX=0, sigmaY=1)

        # Estimate water column noise floor from the first 5% of rows
        noise_rows = max(2, int(h * 0.05))
        noise_floor = np.mean(smoothed[:noise_rows, :], axis=0) + 1e-3

        thresholds = np.clip(noise_floor * threshold_factor, 15.0, 200.0)

        bottom_line = np.zeros(w, dtype=np.int32)
        for col in range(w):
            col_vals = smoothed[:, col]
            # Find first index where return exceeds threshold
            hits = np.where(col_vals > thresholds[col])[0]
            if len(hits) > 0 and hits[0] >= noise_rows:
                bottom_line[col] = int(hits[0])
            else:
                # Fallback: find maximum gradient along column
                grad = np.gradient(col_vals.astype(np.float32))
                bottom_line[col] = int(np.argmax(grad[noise_rows:])) + noise_rows

        return bottom_line
