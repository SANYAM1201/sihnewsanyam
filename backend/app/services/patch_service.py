import os
import glob
import cv2
import numpy as np

def crop_anomaly_patch(swath_array: np.ndarray, bbox, swath_id: str, anomaly_id: str) -> tuple[str, str]:
    os.makedirs("outputs/patches", exist_ok=True)
    
    try:
        x, y, w, h = int(bbox.x), int(bbox.y), int(bbox.width), int(bbox.height)
        img_h, img_w = swath_array.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(img_w, x + w), min(img_h, y + h)
        
        if x2 <= x1 or y2 <= y1:
            return None, None
            
        crop = swath_array[y1:y2, x1:x2]
        
        if crop.dtype != np.uint8:
            if crop.max() <= 1.0:
                crop = (crop * 255).astype(np.uint8)
            else:
                crop = np.clip(crop, 0, 255).astype(np.uint8)
                
        patch_path = f"outputs/patches/{swath_id}_{anomaly_id}_patch.png"
        mask_path = f"outputs/patches/{swath_id}_{anomaly_id}_mask.png"
        
        cv2.imwrite(patch_path, crop)
        
        if len(crop.shape) == 3 and crop.shape[2] == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = crop
        
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        cv2.imwrite(mask_path, mask)
        
        return f"/api/anomaly/{anomaly_id}/patch", f"/api/anomaly/{anomaly_id}/mask"
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Failed to crop patch: %s", e)
        return None, None
