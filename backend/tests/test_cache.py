import numpy as np
import pytest

from app.services.cache import DspPipelineCache, compute_image_hash, dsp_cache


@pytest.fixture
def sample_image():
    return (np.random.rand(128, 128, 3) * 255).astype(np.uint8)


def test_compute_image_hash(sample_image):
    h1 = compute_image_hash(sample_image)
    h2 = compute_image_hash(sample_image)
    assert h1 == h2
    assert isinstance(h1, str)
    assert len(h1) == 16


def test_cache_set_and_get(sample_image):
    cache = DspPipelineCache(maxsize=10)
    key = compute_image_hash(sample_image)
    cache.set(key, sample_image * 2)

    retrieved = cache.get(key)
    assert retrieved is not None
    assert np.array_equal(retrieved, sample_image * 2)


def test_cache_miss():
    cache = DspPipelineCache(maxsize=10)
    assert cache.get("nonexistent_key") is None


def test_cache_eviction():
    cache = DspPipelineCache(maxsize=2)
    cache.set("k1", "val1")
    cache.set("k2", "val2")
    cache.set("k3", "val3")

    assert cache.get("k1") is None
    assert cache.get("k2") == "val2"
    assert cache.get("k3") == "val3"


def test_cache_clear():
    cache = DspPipelineCache(maxsize=5)
    cache.set("k1", "v1")
    cache.clear()
    assert cache.get("k1") is None
