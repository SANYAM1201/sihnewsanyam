"""XTF Telemetry Service - Native Triton binary ingestion engine."""

from __future__ import annotations

from typing import Any, Dict, Tuple
import numpy as np

from app.services.xtf_parser import (
    XtfParseError,
    parse_xtf_bytes,
    parse_xtf_file,
    XTFPing,
    XTFPingHeader,
)

__all__ = [
    "XtfParseError",
    "parse_xtf_bytes",
    "parse_xtf_file",
    "XTFPing",
    "XTFPingHeader",
    "XtfService",
]


class XtfService:
    """Service wrapper for decoding, validating, and slicing XTF sidescan records."""

    @staticmethod
    def parse_bytes(data: bytes) -> Tuple[np.ndarray, Dict[str, Any]]:
        return parse_xtf_bytes(data)

    @staticmethod
    def parse_file(path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        return parse_xtf_file(path)
