"""Multi-stage image loader with comprehensive fallbacks.

Decodes raw image bytes into RGB numpy arrays.
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
import threading
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)
_PIL_LOCK = threading.Lock()  # PIL is not thread-safe for open()


def safe_load_image(
    image_data: bytes,
    target_size: Optional[Tuple[int, int]] = None,
    fallback_to_blank: bool = False,
) -> np.ndarray:
    """Load image bytes into a numpy array.

    Priority:
      1. PIL via BytesIO (fastest, handles most formats)
      2. OpenCV decode (handles JPEG artifacts PIL can't)
      3. PIL via temp file (last resort for truncated files)
      4. Blank 512x512 fallback array if fallback_to_blank is True

    Args:
        image_data: Raw image bytes (PNG, TIFF, JPEG, GeoTIFF...)
        target_size: Optional (width, height) to resize output.
        fallback_to_blank: If True, returns uint8 blank array on decoding failure instead of raising ValueError.

    Returns:
        np.ndarray dtype=uint8, shape (H, W, 3) or (H, W)
    """
    if image_data is None or len(image_data) == 0:
        if fallback_to_blank:
            logger.warning("Empty image data provided — returning blank fallback array")
            img_array = np.zeros((512, 512, 3), dtype=np.uint8)
            if target_size is not None:
                img_array = cv2.resize(img_array, target_size)
            return img_array
        raise ValueError("Empty image data")

    img_array: Optional[np.ndarray] = None

    # Stage 1: PIL with BytesIO
    try:
        from PIL import Image

        with _PIL_LOCK:
            img = Image.open(io.BytesIO(image_data))
            img.load()  # force decode
            img_array = np.array(img)
            if img_array.size == 0:
                img_array = None
    except Exception as e:
        logger.debug(f"Stage 1 (PIL/BytesIO) failed: {e}")

    # Stage 2: OpenCV
    if img_array is None:
        try:
            buf = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
            if img is not None and img.size > 0:
                if len(img.shape) == 2:
                    img_array = img
                elif img.shape[2] == 4:
                    img_array = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                else:
                    img_array = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except Exception as e:
            logger.debug(f"Stage 2 (OpenCV) failed: {e}")

    # Stage 3: PIL via temp file
    if img_array is None:
        try:
            from PIL import Image

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(image_data)
                fname = f.name
            with _PIL_LOCK:
                img = Image.open(fname)
                img.load()
                img_array = np.array(img)
            os.unlink(fname)
            if img_array is not None and img_array.size == 0:
                img_array = None
        except Exception as e:
            logger.debug(f"Stage 3 (PIL/tempfile) failed: {e}")

    # Stage 4: Blank fallback or raise
    if img_array is None:
        if fallback_to_blank:
            logger.warning("All image-loading stages failed — returning blank 512x512 fallback array")
            img_array = np.zeros((512, 512, 3), dtype=np.uint8)
        else:
            logger.error("All image-loading stages failed to decode image bytes")
            raise ValueError("Could not load image: decoding failed across all stages")

    # Optional resize
    if target_size is not None:
        try:
            img_array = cv2.resize(img_array, target_size, interpolation=cv2.INTER_LINEAR)
        except Exception:
            pass

    return img_array.astype(np.uint8)
