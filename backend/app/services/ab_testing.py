"""Lightweight A/B framework — assigns variants by hashed session ID."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ABTest:
    name: str
    variants: dict[str, dict[str, Any]]
    weights: dict[str, float]
    active: bool = True


_TESTS: dict[str, ABTest] = {
    "detection_model": ABTest(
        name="detection_model",
        variants={
            "default": {"model": "default"},
            "400khz": {"model": "400khz"},
        },
        weights={"default": 0.8, "400khz": 0.2},
    ),
    "dsp_pipeline": ABTest(
        name="dsp_pipeline",
        variants={
            "standard": {"bac": True, "tvg": True, "src": False},
            "enhanced": {"bac": True, "tvg": True, "src": True},
        },
        weights={"standard": 0.6, "enhanced": 0.4},
    ),
}


def get_variant(test: str, session_id: str = "anon") -> Optional[str]:
    t = _TESTS.get(test)
    if not t or not t.active:
        return None
    bucket = abs(hash(f"{test}:{session_id}")) % 1000
    cum = 0.0
    for name, w in t.weights.items():
        cum += w * 1000
        if bucket < cum:
            return name
    return list(t.variants)[0]


def get_config(test: str, session_id: str = "anon") -> Optional[dict[str, Any]]:
    v = get_variant(test, session_id)
    return _TESTS[test].variants.get(v) if v and test in _TESTS else None


def record(test: str, variant: str, metrics: dict[str, Any]) -> None:
    logger.info(f"📊 AB {test}/{variant}: {metrics}")


def list_tests() -> dict[str, Any]:
    return {k: {"variants": list(v.variants), "active": v.active} for k, v in _TESTS.items()}
