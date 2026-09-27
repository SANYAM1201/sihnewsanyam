"""In-memory LRU cache and hashing for Sonar DSP operations."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any

import numpy as np


def compute_image_hash(image: np.ndarray) -> str:
    """Computes quick SHA-256 fingerprint for caching DSP results."""
    return hashlib.sha256(image.tobytes()).hexdigest()[:16]


class DspPipelineCache:
    """Cache wrapper for DSP pipeline intermediate states."""

    def __init__(self, maxsize: int = 128) -> None:
        self.maxsize = maxsize
        self._store: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        if len(self._store) >= self.maxsize:
            # Drop earliest inserted key
            first_key = next(iter(self._store))
            del self._store[first_key]
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()


dsp_cache = DspPipelineCache()
