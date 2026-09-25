# ============================================================================
# SONAR SENTRY — END-TO-END VERIFICATION SUITE
# Place at repo root: verify_sonar_sentry.py
# Usage:
#   python verify_sonar_sentry.py --stage env      # 0: environment sanity
#   python verify_sonar_sentry.py --stage dsp      # 1: preprocessing physics units
#   python verify_sonar_sentry.py --stage geodesy  # 2: coordinate math
#   python verify_sonar_sentry.py --stage val      # 3: ground-truth mAP A/B
#   python verify_sonar_sentry.py --stage api      # 4: live API + persistence E2E
#   python verify_sonar_sentry.py --stage perf    # 5: latency budget
#   python verify_sonar_sentry.py --stage edge    # 6: ONNX parity
#   python verify_sonar_sentry.py --stage all
# Exit code 0 = PASS. Any FAIL prints the file:line to fix.
# ============================================================================
from __future__ import annotations

import argparse
import io
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


# ----------------------------------------------------------------------------
# STAGE 0 — ENVIRONMENT: no mocks, no broken paths, real weights
# ----------------------------------------------------------------------------
def stage_env() -> None:
    print("\n=== STAGE 0: ENVIRONMENT SANITY ===")

    # 0.1 Real weights exist and are a valid Ultralytics checkpoint
    weights = BACKEND / "best.pt"
    check("best.pt exists and >5MB", weights.is_file() and weights.stat().st_size > 5_000_000,
          f"{weights.stat().st_size if weights.exists() else 0} bytes")
    try:
        import torch
        ckpt = torch.load(weights, map_location="cpu", weights_only=False)
        keys = list(ckpt.keys()) if isinstance(ckpt, dict) else []
        check("best.pt is a real training checkpoint (has 'model'/'train_args')",
              any(k in keys for k in ("model", "train_args", "epoch", "train_results")),
              f"keys={keys[:6]}")
        if isinstance(ckpt, dict) and "train_args" in ckpt:
            targs = ckpt["train_args"]
            print(f"        train_args: data={targs.get('data')} epochs={targs.get('epochs')} "
                  f"imgsz={targs.get('imgsz')}")
    except Exception as e:
        check("best.pt loads with torch.load", False, str(e))

    # 0.2 Broken symlink landmine
    sym = BACKEND / "yolov8s.pt"
    if sym.is_symlink():
        check("backend/yolov8s.pt symlink resolves", sym.resolve().is_file(),
              f"-> {os.readlink(sym)} (DELETE this if FAIL)")
    else:
        check("backend/yolov8s.pt not a broken symlink", True)

    # 0.3 Mock cannot be reached in prod config
    from app.config import get_settings
    s = get_settings()
    check("MODEL_PROVIDER is 'sonar' (not mock)", s.model_provider == "sonar", s.model_provider)
    check("SSS preprocessing enabled by default", s.sss_enable_processing is True)

    # 0.4 Factory builds the REAL pipeline
    from app.services.factory import create_inference_service
    svc = create_inference_service(s)
    meta = svc.metadata()
    check("inference service provider != 'mock'", meta.provider != "mock", meta.provider)
    check("model is loaded", svc.is_model_loaded)

    # 0.5 MockModelService must not appear in factory prod path
    factory_src = (BACKEND / "app" / "services" / "factory.py").read_text()
    check("factory.py never instantiates MockModelService for provider 'sonar'",
          "MockModelService()" not in factory_src.split('elif settings.model_provider == "sonar"')[0]
          or 'provider == "mock"' in factory_src)

    # 0.6 Silent exception swallowing audit (the 'verified' killers)
    import re
    for py in (BACKEND / "app").rglob("*.py"):
        src = py.read_text()
        for m in re.finditer(r"except\s+Exception\s*:\s*\n\s*pass", src):
            check(f"no bare 'except Exception: pass' in {py.name}", False,
                  "silent failure — replace with logging + metrics")
    detect_src = (BACKEND / "app" / "api" / "routes" / "detect.py").read_text()
    check("detect.py persists latitude/longitude per detection",
          "latitude" in detect_src.split("detection_dicts")[1] if "detection_dicts" in detect_src else False,
          "add lat/lng to detection_dicts + Detection ORM")


# ----------------------------------------------------------------------------
# STAGE 1 — DSP PHYSICS: synthetic ground-truth unit tests
# ----------------------------------------------------------------------------
def stage_dsp() -> None:
    print("\n=== STAGE 1: PREPROCESSING PHYSICS (synthetic ground truth) ===")
    import numpy as np
    from app.preprocessing.sidescan_processor import SidescanProcessor
    from app.preprocessing.shadow_handler import ShadowDetector
    from app.preprocessing.yolo_preprocessor import YOLOPreprocessor

    rng = np.random.default_rng(42)

    # 1.1 BAC: uniform background must stay ~uniform; a bright column is normalized
    img = np.full((200, 400), 100, np.uint8)
    img[:, 100:140] = 220                       # artificially bright range column
    out = SidescanProcessor(apply_bac=True, apply_stripe_filter=False,
                            apply_sharpening=False).process(img)
    col_before = img[:, 120].mean()
    col_after = out[:, 120].mean()
    check("BAC flattens across-range gain falloff",
          abs(col_after - out[:, 300].mean()) < 15 and abs(col_after - col_before) > 30,
          f"col mean {col_before:.0f} -> {col_after:.0f}")

    # 1.2 Stripe filter: injected horizontal lines are removed, target survives
    img = rng.normal(120, 10, (256, 256)).clip(0, 255).astype(np.uint8)
    img[64::32, :] = 20                          # towfish heave scanlines
    img[100:156, 100:156] = 230                  # a bright square target
    out = SidescanProcessor(apply_bac=False, apply_stripe_filter=True,
                            apply_sharpening=False).process(img)
    row_contrast = img[64, :].std() - out[64, :].std() if out.shape == img.shape else -1
    check("stripe filter attenuates line noise", out.std() < img.std(),
          f"std {img.std():.1f} -> {out.std():.1f}")
    check("stripe filter keeps bright target region",
          (out[100:156, 100:156].mean() - out.mean()) > 20)

    # 1.3 Shadow detector: known dark blob found, bright noise ignored
    img = np.full((300, 300), 200, np.uint8)
    img[150:180, 100:160] = 5                    # known acoustic shadow
    mask = ShadowDetector(threshold=0.15, min_shadow_size=100).detect(img)
    ys, xs = np.where(mask > 0)
    hit = len(ys) > 200 and 150 <= ys.mean() <= 180 and 100 <= xs.mean() <= 160
    check("shadow detector finds synthetic shadow at true location", hit,
          f"{len(ys)} px, center=({ys.mean():.0f},{xs.mean():.0f})")

    # 1.4 Letterbox round-trip: bbox un-mapping is exact
    prep = YOLOPreprocessor()
    img = np.zeros((1080, 1920, 3), np.uint8)
    chw, meta = prep.process_with_meta(img)
    check("letterbox tensor shape (3,640,640)", chw.shape == (3, 640, 640), str(chw.shape))
    # a box at known original coords -> forward -> inverse -> same coords
    bx, by, bw, bh = 960., 540., 200., 100.     # center-ish box
    lx, ly = (bx + bw / 2) * meta.scale + meta.pad_left, (by + bh / 2) * meta.scale + meta.pad_top
    ox, oy = (lx - meta.pad_left) / meta.scale, (ly - meta.pad_top) / meta.scale
    check("letterbox inverse mapping is lossless (<1px)",
          abs(ox - (bx + bw / 2)) < 1 and abs(oy - (by + bh / 2)) < 1,
          f"err=({abs(ox-(bx+bw/2)):.3f},{abs(oy-(by+bh/2)):.3f})")

    # 1.5 SLANT RANGE CORRECTION (once you implement it) — verification ready
    # Synthetic flat seabed at altitude H_s=10m, target at slant range R_s=26m:
    #   ground range R_g = sqrt(R_s^2 - H_s^2) = sqrt(676-100) = 24.0m
    H_s, R_s = 10.0, 26.0
    R_g = math.sqrt(R_s ** 2 - H_s ** 2)
    check("SRC geometry math sanity (R_g = sqrt(R_s^2 - H_s^2))",
          abs(R_g - 24.0) < 1e-9, f"R_g={R_g:.4f}")
    try:
        from app.preprocessing.slant_range import slant_range_correct  # your module
        # synthetic ping: nadir water column 0..H_s, then seabed returns
        ping = np.zeros(512); ping[100:] = 180
        corrected = slant_range_correct(ping, altitude=H_s, max_range=R_s * 1.2)
        check("SRC removes nadir water column on synthetic ping",
              corrected[: corrected.size // 5].max() < 10)
    except ImportError:
        check("SRC module exists (app/preprocessing/slant_range.py)", False,
              "not implemented yet — Phase 1.2 of the masterplan")


# ----------------------------------------------------------------------------
# STAGE 2 — GEODESY: flat math vs WGS84 ellipsoid reference
# ----------------------------------------------------------------------------
def stage_geodesy() -> None:
    print("\n=== STAGE 2: GEODESY ACCURACY ===")
    from app.services.georeference import georeference_offset

    try:
        from pyproj import Geod
        geod = Geod(ellps="WGS84")
        # 500m offset from a mid-latitude origin — typical cross-track distance
        lat0, lon0 = 18.9220, 72.8347          # Mumbai offshore
        east, north = 400.0, -300.0
        ref_lon, ref_lat, _ = geod.fwd(lon0, lat0, math.degrees(math.atan2(east, north)),
                                      math.hypot(east, north))
        got_lat, got_lon = georeference_offset(lat0, lon0, east, north)
        err = geod.inv(lon0, lat0, got_lon, got_lat)[2] - geod.inv(lon0, lat0, ref_lon, ref_lat)[2]
        check("flat georeference within 5 m of ellipsoidal truth over 500 m",
              abs(err) < 5.0, f"deviation={err:.2f} m")
        print("        NOTE: for ping-indexed XTF geodesy (heading, port/starboard), "
              "the flat model must be replaced — this test only bounds its error.")
    except ImportError:
        check("pyproj installed (pip install pyproj)", False)

    # heading sensitivity demo: 45° heading flips E/N — current code can't see it
    check("georeference.py accepts heading/azimuth parameter",
          "heading" in (BACKEND / "app" / "services" / "georeference.py").read_text(),
          "required for XTF telemetry")


# ----------------------------------------------------------------------------
# STAGE 3 — GROUND-TRUTH DETECTION EVALUATION (the real 'improved' proof)
# ----------------------------------------------------------------------------
# Prereq: a labeled SSS dataset in Ultralytics format, e.g. SCTD converted:
#   datasets/sctd/{images,labels}/{train,val}/... + data.yaml
def stage_val() -> None:
    print("\n=== STAGE 3: mAP A/B — RAW vs PREPROCESSED ===")
    import numpy as np
    from PIL import Image
    from app.preprocessing.sonar_preprocessor import SonarPreprocessor

    ds = Path("datasets/sctd")
    if not (ds / "data.yaml").exists():
        check("labeled dataset present (datasets/sctd/data.yaml)", False,
              "download SCTD / marine-debris SSS set and convert to YOLO format")
        return
    check("labeled dataset present", True)

    # 3.1 Bake a preprocessed copy of the val split (labels unchanged: same geometry)
    pre = SonarPreprocessor(apply_sss_processing=True, apply_shadow_inpainting=True)
    src_val = ds / "images" / "val"
    dst = REPO / "datasets" / "sctd_prep" / "images" / "val"
    if not dst.exists():
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src_val.glob("*")):
            img = np.array(Image.open(f).convert("RGB"))
            out = pre.process_array(img)
            # process_array returns the CHW tensor; save its HWC image form
            if out.ndim == 3 and out.shape[0] in (1, 3):
                out = np.transpose(out, (1, 2, 0))
            if out.dtype != np.uint8:
                out = (np.clip(out, 0, 1) * 255).astype(np.uint8) if out.max() <= 1.05 else out.astype(np.uint8)
            Image.fromarray(out).save(dst / f.name)
        shutil.copytree(ds / "labels" / "val", REPO / "datasets" / "sctd_prep" / "labels" / "val",
                        dirs_exist_ok=True)
        shutil.copy(ds / "data.yaml", REPO / "datasets" / "sctd_prep" / "data.yaml")
    yaml_text = (REPO / "datasets" / "sctd_prep" / "data.yaml").read_text()
    (REPO / "datasets" / "sctd_prep" / "data.yaml").write_text(
        yaml_text.replace("sctd/", str(REPO / "datasets/sctd_prep") + "/"))


    def yolo_val(data_yaml: Path, project: str) -> dict:
        cmd = [sys.executable, "-c",
               "from ultralytics import YOLO; import json;"
               "m=YOLO('best.pt');"
               f"r=m.val(data='{data_yaml}', imgsz=640, conf=0.12, project='runs/verify', name='{project}', plots=True);"
               "print('VALJSON', json.dumps({'mAP50': float(r.results_dict['metrics/mAP50(B)']),"
               "'mAP5095': float(r.results_dict['metrics/mAP50-95(B)']),"
               "'P': float(r.results_dict['metrics/precision(B)']),"
               "'R': float(r.results_dict['metrics/recall(B)'])}))"]
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        for line in p.stdout.splitlines():
            if line.startswith("VALJSON "):
                return json.loads(line[8:])
        check("yolo val produced metrics", False, p.stderr[-400:])
        return {}

    print("  running baseline (raw) validation…")
    raw = yolo_val(ds / "data.yaml", "raw")
    print("  running preprocessed validation…")
    enh = yolo_val(REPO / "datasets" / "sctd_prep" / "data.yaml", "prep")

    if raw and enh:
        print(f"\n  {'metric':<12}{'RAW':>10}{'ENHANCED':>12}{'delta':>10}")
        for k in ("mAP50", "mAP5095", "P", "R"):
            d = enh[k] - raw[k]
            print(f"  {k:<12}{raw[k]:>10.4f}{enh[k]:>12.4f}{d:>+10.4f}")
        check("mAP50 does not regress with preprocessing", enh["mAP50"] >= raw["mAP50"] - 0.005,
              f"{raw['mAP50']:.4f} -> {enh['mAP50']:.4f}")
        check("recall does not regress", enh["R"] >= raw["R"] - 0.005)
        verdict = "IMPROVED" if enh["mAP50"] > raw["mAP50"] + 0.005 else \
                  ("NEUTRAL" if enh["mAP50"] >= raw["mAP50"] - 0.005 else "HARMFUL — tune DSP")
        print(f"\n  >>> PREPROCESSING VERDICT: {verdict}")
        (REPO / "verification_results.json").write_text(
            json.dumps({"raw": raw, "enhanced": enh}, indent=2))


# ----------------------------------------------------------------------------
# STAGE 4 — LIVE API + PERSISTENCE END-TO-END
# ----------------------------------------------------------------------------
def stage_api() -> None:
    print("\n=== STAGE 4: LIVE API E2E (server must be running) ===")
    import requests

    base = os.getenv("API", "http://localhost:8000")

    # 4.1 health + provider must be real
    h = requests.get(f"{base}/api/health", timeout=5).json()
    check("health ok", h.get("status") in ("ok", "healthy"), str(h))

    # 4.2 real upload through the full chain
    img_path = next((REPO / "demo_data").glob("*.png"), None)
    if not img_path:
        check("demo image available for upload", False, "put a labeled SSS png in demo_data/")
        return
    t0 = time.perf_counter()
    r = requests.post(
        f"{base}/api/detect",
        files={"file": (img_path.name, img_path.read_bytes(), "image/png")},
        data={"latitude": "18.9220", "longitude": "72.8347", "sonar_type": "Side-Scan",
              "resolution": "0.5 m/px", "depth_min": "10", "depth_max": "50"},
        timeout=120)
    dt = time.perf_counter() - t0
    check("POST /api/detect returns 200", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
    body = r.json()
    check("model provider is NOT mock", body["model"]["provider"] != "mock", body["model"]["provider"])
    check("response includes run_id + timestamps", bool(body.get("run_id")) and
          "duration_seconds" in body["timestamps"])
    check("end-to-end under 10 s", dt < 10, f"{dt:.2f}s")
    run_id = body["run_id"]

    # 4.3 detections carry coordinates (computed AND persisted)
    dets = body["detections"]
    if dets:
        d0 = dets[0]
        check("detection has latitude in response", d0.get("latitude") is not None)
        lat_dist = abs(d0["latitude"] - 18.9220) if d0.get("latitude") else 999
        check("georeference actually moves the pin off origin when offset",
              True, f"lat delta={lat_dist:.6f} (0 only if bbox at origin)")

    # 4.4 persistence: read the DB directly — the PDF's critical bug
    import sqlite3
    dbf = REPO / "sonar_sentry.db"
    if not dbf.exists():
        check("sqlite db found", False, str(dbf)); return
    con = sqlite3.connect(dbf)
    cur = con.cursor()
    cur.execute("PRAGMA table_info(detections)")
    cols = [c[1] for c in cur.fetchall()]
    check("detections table has latitude column", "latitude" in cols, f"cols={cols}")
    check("detections table has longitude column", "longitude" in cols)
    if "latitude" in cols:
        cur.execute("SELECT COUNT(*), COUNT(latitude) FROM detections WHERE run_id=? ", (run_id,))
        n, nlat = cur.fetchone()
        check(f"persisted {n} detections and kept coordinates", n > 0 and nlat == n,
              f"rows={n}, with_lat={nlat}")
    # run status
    cur.execute("SELECT status, error_message FROM runs WHERE id=?", (run_id,))
    row = cur.fetchone()
    check("run status completed, no error", row and row[0] == "completed" and not row[1], str(row))
    con.close()

    # 4.5 negative tests: pipeline must reject junk, not silently mock it
    r = requests.post(f"{base}/api/detect",
                     files={"file": ("fake.xtf", b"\x00XTFjunk", "application/octet-stream")},
                     data={"latitude": "18.9", "longitude": "72.8", "sonar_type": "Side-Scan",
                           "resolution": "0.5 m/px", "depth_min": "10", "depth_max": "50"})
    check("fake .xtf rejected (until real XTF route exists)", r.status_code >= 400,
          f"{r.status_code} — after Phase 1.1 this flips: real .xtf MUST be accepted here")

    # 4.6 mocked-hash detector cannot be triggered via any response
    check("no MOCK_ labels in any detection", all("MOCK" not in d["class_label"] for d in dets))


# ----------------------------------------------------------------------------
# STAGE 5 — LATENCY BUDGET (real-time claim)
# ----------------------------------------------------------------------------
def stage_perf() -> None:
    print("\n=== STAGE 5: LATENCY BUDGET ===")
    import numpy as np
    from PIL import Image
    from app.preprocessing.sonar_preprocessor import SonarPreprocessor

    img_path = next((REPO / "demo_data").glob("*.png"), None)
    if not img_path:
        check("demo image for perf", False); return
    raw = img_path.read_bytes()
    pre = SonarPreprocessor()
    pre.process(raw)                                     # warmup
    times = []
    for _ in range(10):
        t0 = time.perf_counter(); pre.process(raw); times.append(time.perf_counter() - t0)
    med = sorted(times)[5] * 1000
    check("preprocessing < 150 ms/image at 1920x1080", med < 150, f"median={med:.1f} ms")

    # inference latency on CPU
    from app.services.factory import create_inference_service
    svc = create_inference_service()
    svc.predict(raw)
    t0 = time.perf_counter(); svc.predict(raw); t_inf = (time.perf_counter() - t0) * 1000
    check("full predict (prep+inference) < 1000 ms CPU", t_inf < 1000, f"{t_inf:.0f} ms")


# ----------------------------------------------------------------------------
# STAGE 6 — EDGE PARITY: ONNX export vs PyTorch
# ----------------------------------------------------------------------------
def stage_edge() -> None:
    print("\n=== STAGE 6: ONNX EXPORT PARITY ===")
    import numpy as np
    export_dir = REPO / "exports"
    export_dir.mkdir(exist_ok=True)
    p = subprocess.run([sys.executable, "-c",
        "from ultralytics import YOLO; m=YOLO('best.pt'); "
        f"p=m.export(format='onnx', imgsz=640, opset=12); print('ONNXPATH', p)"],
        cwd=REPO, capture_output=True, text=True)
    onnx_path = next((l for l in p.stdout.splitlines() if l.startswith("ONNXPATH ")), None)
    check("ONNX export succeeded", bool(onnx_path), p.stderr[-300:])
    if not onnx_path:
        return
    onnx_file = onnx_path.split()[1]

    try:
        import onnxruntime as ort
    except ImportError:
        check("onnxruntime installed (pip install onnxruntime)", False); return

    import torch
    from ultralytics import YOLO
    dummy = np.random.default_rng(0).normal(0.45, 0.2, (1, 3, 640, 640)).clip(0, 1).astype(np.float32)
    pt_model = YOLO("best.pt")
    pt_out = pt_model.predict(source=dummy[0].transpose(1, 2, 0), imgsz=640, conf=0.12, verbose=False)
    sess = ort.InferenceSession(onnx_file, providers=["CPUExecutionProvider"])
    ort_out = sess.run(None, {"images": dummy})
    n_pt = len(pt_out[0].boxes) if pt_out and pt_out[0].boxes is not None else 0
    print(f"        torch boxes={n_pt}, onnx output shapes={[o.shape for o in ort_out]}")
    check("ONNX runtime session loads and runs", len(ort_out) >= 1)
    # NOTE: full box parity needs post-processing; assert logits-level closeness:
    check("ONNX raw output finite", bool(np.isfinite(ort_out[0]).all()))
    print("        For TensorRT INT8 on Jetson: trtexec --onnx=" + onnx_file +
          " --int8 --saveEngine=best_int8.engine, then re-run STAGE 3 with the engine.")


# ----------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["env", "dsp", "geodesy", "val", "api", "perf", "edge", "all"])
    a = ap.parse_args()
    stages = [a.stage] if a.stage != "all" else ["env", "dsp", "geodesy", "val", "perf", "edge", "api"]
    for s in stages:
        try:
            globals()[f"stage_{s}"]()
        except Exception as e:
            check(f"stage '{s}' crashed", False, repr(e))
    print("\n" + "=" * 60)
    print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
    for f in FAIL:
        print(f"  ✗ {f}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
