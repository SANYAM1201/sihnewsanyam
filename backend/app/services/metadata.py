"""Metadata embedding and extraction in PNG chunks for Sonar telemetry persistence."""

from __future__ import annotations

import io
import json
import zlib
from typing import Any

from PIL import Image, PngImagePlugin


def embed_sonar_metadata(image_bytes: bytes, metadata: dict[str, Any]) -> bytes:
    """Embeds telemetry dictionary into PNG as a compressed text chunk."""
    img = Image.open(io.BytesIO(image_bytes))
    meta_bytes = zlib.compress(json.dumps(metadata).encode("utf-8"))

    png_info = PngImagePlugin.PngInfo()
    png_info.add_text("sonar_telemetry", meta_bytes.hex())

    out_buf = io.BytesIO()
    img.save(out_buf, format="PNG", pnginfo=png_info)
    return out_buf.getvalue()


def extract_sonar_metadata(image_bytes: bytes) -> dict[str, Any] | None:
    """Extracts embedded sonar telemetry from PNG chunk if present."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        raw_hex = img.info.get("sonar_telemetry")
        if raw_hex:
            compressed = bytes.fromhex(raw_hex)
            decompressed = zlib.decompress(compressed).decode("utf-8")
            return json.loads(decompressed)
    except Exception:
        pass
    return None
