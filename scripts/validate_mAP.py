"""Validate mAP across IoU thresholds and report softening."""

import json
import logging
import pathlib
import sys
from ultralytics import YOLO

logger = logging.getLogger(__name__)

MODEL_PATH = "models/best.pt"
DATA_PATH = "datasets/screenshots_dev"

if not pathlib.Path(MODEL_PATH).exists():
    print(f"⚠️  Model {MODEL_PATH} not found. Skipping validation.")
    sys.exit(0)

data_yaml = pathlib.Path(DATA_PATH) / "data.yaml"

if not data_yaml.exists():
    print(f"⚠️  No data.yaml at {data_yaml} — place your val dataset there and re-run.")
    sys.exit(0)

model = YOLO(MODEL_PATH)
results = model.val(data=str(data_yaml), split="val", plots=False, save_json=True)
rd = results.results_dict

map50 = rd.get("metrics/mAP50", rd.get("mAP_50", 0.0))
map95 = rd.get("metrics/mAP50-95", rd.get("mAP_50-95", 0.0))
soft = map50 - map95
pct = (soft / map50 * 100) if map50 > 0 else 0

print(f"\n📊 mAP@0.50      : {map50:.4f}")
print(f"📊 mAP@0.50:0.95 : {map95:.4f}")
print(f"📊 Softening     : {soft:.4f}  ({pct:.1f}%)")

if pct > 5:
    print("\n⚠️  Softening >5% — increase edge_preservation in adaptive_beam_angle_correction")
    print("   Edit backend/app/services/dsp.py → edge_preservation=0.9")
else:
    print("\n✅ Softening within acceptable range (<5%)")

with open("mAP_results.json", "w") as f:
    json.dump({"map50": map50, "map95": map95, "softening": soft, "pct": pct}, f, indent=2)
print("📄 Saved mAP_results.json")
