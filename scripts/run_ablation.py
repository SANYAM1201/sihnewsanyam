import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

from app.preprocessing.sonar_preprocessor import SonarPreprocessor
from ultralytics import YOLO

def create_ablation_split(name: str, preprocessor: SonarPreprocessor):
    src_ds = REPO / "datasets" / "screenshots_dev"
    target_ds = REPO / "datasets" / f"ablation_{name}_prep"
    if target_ds.exists():
        shutil.rmtree(target_ds)
    
    val_images_dst = target_ds / "images" / "val"
    val_images_dst.mkdir(parents=True, exist_ok=True)
    
    val_images_src = src_ds / "images" / "val"
    for img_file in sorted(val_images_src.glob("*.png")):
        img = np.array(Image.open(img_file).convert("RGB"))
        processed = preprocessor.process_array(img)
        if processed.ndim == 3 and processed.shape[0] in (1, 3):
            processed = np.transpose(processed, (1, 2, 0))
        if processed.dtype != np.uint8:
            processed = (np.clip(processed, 0, 1) * 255).astype(np.uint8) if processed.max() <= 1.05 else processed.astype(np.uint8)
        Image.fromarray(processed).save(val_images_dst / img_file.name)
        
    shutil.copytree(src_ds / "labels" / "val", target_ds / "labels" / "val", dirs_exist_ok=True)
    shutil.copytree(src_ds / "images" / "train", target_ds / "images" / "train", dirs_exist_ok=True)
    shutil.copytree(src_ds / "labels" / "train", target_ds / "labels" / "train", dirs_exist_ok=True)
    
    yaml_content = """train: images/train
val: images/val

names:
  0: shipwreck
  1: pipe
  2: cylinder
  3: net
"""
    (target_ds / "data.yaml").write_text(yaml_content)
    return target_ds

def run_eval(yaml_path: Path, output_json: Path):
    model = YOLO(str(REPO / "best.pt"))
    r = model.val(data=str(yaml_path), imgsz=640, conf=0.12, plots=False)
    metrics = {
        "mAP50": round(float(r.results_dict["metrics/mAP50(B)"]), 4),
        "mAP5095": round(float(r.results_dict["metrics/mAP50-95(B)"]), 4),
        "P": round(float(r.results_dict["metrics/precision(B)"]), 4),
        "R": round(float(r.results_dict["metrics/recall(B)"]), 4)
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(metrics, indent=2))
    return metrics

def main():
    conditions = {
        "raw": SonarPreprocessor(apply_sss_processing=False, apply_shadow_inpainting=False),
        "shadow_only": SonarPreprocessor(apply_sss_processing=False, apply_shadow_inpainting=True),
        "stripe_only": SonarPreprocessor(apply_sss_processing=True, apply_bac=False, apply_stripe_filter=True, apply_sharpening=False, apply_shadow_inpainting=False),
        "bac_only": SonarPreprocessor(apply_sss_processing=True, apply_bac=True, apply_stripe_filter=False, apply_sharpening=False, apply_shadow_inpainting=False),
        "homomorphic_only": SonarPreprocessor(apply_sss_processing=True, apply_bac=False, apply_stripe_filter=False, apply_sharpening=True, apply_shadow_inpainting=False),
        "full_pipeline": SonarPreprocessor(apply_sss_processing=True, apply_bac=True, apply_stripe_filter=True, apply_sharpening=True, apply_shadow_inpainting=True)
    }
    
    runs_dir = REPO / "runs" / "verify"
    runs_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    for name, prep in conditions.items():
        print(f"\n--- Running Ablation Condition: {name} ---")
        ds_dir = create_ablation_split(name, prep)
        out_file = runs_dir / f"ablation_{name}.json"
        res = run_eval(ds_dir / "data.yaml", out_file)
        results[name] = res
        print(f"Result for {name}: {res}")
        if ds_dir.exists():
            shutil.rmtree(ds_dir)
        
    summary_file = runs_dir / "ablation_summary.json"
    summary_file.write_text(json.dumps(results, indent=2))
    print(f"\nSaved all raw ablation JSONs to {runs_dir}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
