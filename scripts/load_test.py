"""Async load test for /api/detect."""

import asyncio
import io
import json
import statistics
import time
import aiohttp
import cv2
import numpy as np

URL = "http://localhost:8000/api/detect"

arr = (np.random.rand(256, 256) * 255).astype(np.uint8)
ok, buf = cv2.imencode(".png", arr)
IMG_BYTES = buf.tobytes()


async def one_request(session, sem):
    async with sem:
        t0 = time.perf_counter()
        try:
            data = aiohttp.FormData()
            data.add_field("file", IMG_BYTES, filename="test.png", content_type="image/png")
            data.add_field("latitude", "12.9716")
            data.add_field("longitude", "80.2520")
            data.add_field("sonar_type", "Side-Scan")
            data.add_field("resolution", "0.1 m/px")
            data.add_field("depth_min", "0.0")
            data.add_field("depth_max", "30.0")
            async with session.post(URL, data=data, timeout=aiohttp.ClientTimeout(total=60)) as r:
                lat = time.perf_counter() - t0
                return {"ok": r.status < 400, "status": r.status, "lat": lat}
        except Exception as e:
            return {"ok": False, "status": 0, "lat": time.perf_counter() - t0, "err": str(e)}


async def run(n=20, c=5):
    sem = asyncio.Semaphore(c)
    async with aiohttp.ClientSession() as s:
        res = await asyncio.gather(*[one_request(s, sem) for _ in range(n)])

    ok = [r for r in res if r["ok"]]
    bad = [r for r in res if not r["ok"]]
    lats = [r["lat"] * 1000 for r in ok]

    print(f"\n  concurrency={c}  n={n}")
    print(f"  success={len(ok)}  errors={len(bad)}")
    if lats:
        lats.sort()
        print(
            f"  avg={statistics.mean(lats):.0f}ms  "
            f"p50={lats[len(lats)//2]:.0f}ms  "
            f"p95={lats[int(len(lats)*.95)]:.0f}ms  "
            f"max={max(lats):.0f}ms"
        )
    if bad:
        print(f"  first error: {bad[0]}")
    return {"n": n, "c": c, "ok": len(ok), "bad": len(bad), "p95": lats[int(len(lats) * .95)] if lats else None}


async def main():
    print("🚀 Load Test — backend should be running on :8000\n")
    results = {}
    for c in [1, 5, 10]:
        results[f"c{c}"] = await run(n=20, c=c)
        await asyncio.sleep(1)
    with open("load_test.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✅ Saved load_test.json")


if __name__ == "__main__":
    asyncio.run(main())
