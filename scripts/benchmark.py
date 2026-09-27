"""Benchmark inference, DSP, and memory usage."""

import json
import os
import sys
import time
import statistics
from pathlib import Path
import cv2
import numpy as np
import psutil

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


def bench(fn, n=20, warmup=3):
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return {
        "n": n,
        "avg_ms": round(statistics.mean(times) * 1000, 2),
        "min_ms": round(min(times) * 1000, 2),
        "max_ms": round(max(times) * 1000, 2),
        "std_ms": round(statistics.stdev(times) * 1000, 2),
        "fps": round(1.0 / statistics.mean(times), 1),
    }


img = (np.random.rand(640, 640, 3) * 255).astype(np.uint8)

# DSP Benchmark
try:
    from app.services.dsp import dynamic_bac
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dsp_r = bench(lambda: dynamic_bac(img_gray))
    print(f"DSP  avg={dsp_r['avg_ms']}ms  fps={dsp_r['fps']}")
except Exception as e:
    dsp_r = {"error": str(e)}
    print(f"DSP  ERROR: {e}")

# Inference Benchmark
try:
    from app.services.factory import create_inference_service
    from app.config import get_settings
    svc = create_inference_service(get_settings())
    ok, buf = cv2.imencode(".png", img)
    inf_r = bench(lambda: svc.predict(buf.tobytes()))
    print(f"Inference avg={inf_r['avg_ms']}ms  fps={inf_r['fps']}")
except Exception as e:
    inf_r = {"error": str(e)}
    print(f"Inference ERROR: {e}")

# Memory Benchmark
proc = psutil.Process(os.getpid())
mem = proc.memory_info()
mem_r = {"rss_mb": round(mem.rss / 1e6, 1), "vms_mb": round(mem.vms / 1e6, 1)}
print(f"MEM  rss={mem_r['rss_mb']}MB")

results = {"dsp": dsp_r, "inference": inf_r, "memory": mem_r}
with open("benchmarks.json", "w") as f:
    json.dump(results, f, indent=2)
print("\n✅ Saved benchmarks.json")
