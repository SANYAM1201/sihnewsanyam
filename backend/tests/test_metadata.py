import io
import numpy as np
import pytest
import cv2

from app.services.metadata import embed_sonar_metadata, extract_sonar_metadata


@pytest.fixture
def sample_png_bytes():
    img = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def test_embed_and_extract_roundtrip(sample_png_bytes):
    meta = {"altitude": 25.0, "frequency_khz": 400, "sonar_type": "Side-Scan"}
    tagged_bytes = embed_sonar_metadata(sample_png_bytes, meta)
    extracted = extract_sonar_metadata(tagged_bytes)
    assert extracted is not None
    assert extracted["altitude"] == 25.0
    assert extracted["frequency_khz"] == 400


def test_extract_missing_returns_none(sample_png_bytes):
    extracted = extract_sonar_metadata(sample_png_bytes)
    assert extracted is None


def test_extract_invalid_bytes_returns_none():
    extracted = extract_sonar_metadata(b"not a png")
    assert extracted is None
