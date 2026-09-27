# Sonar Sentry — REST & WebSocket API Reference

Base URL (Local): `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`  
WebSocket Stream: `ws://localhost:8000/ws/waterfall`

---

## Endpoints

### 1. Ingest Sonar Scan (Images & Hydrographic Files)
- **POST** `/api/detect`
- **POST** `/api/detect/xtf` (Convenience route for Triton XTF files)
- **Content-Type**: `multipart/form-data`

#### Parameters:
- `file`: File upload (`.png`, `.jpg`, `.tif`, `.tiff`, `.xtf`)
- `latitude`: Float (e.g. `13.0628`)
- `longitude`: Float (e.g. `80.3582`)
- `sonar_type`: String (`Side-Scan`, `Multibeam`, `Synthetic Aperture`, `SSS-Dual`)
- `resolution`: String (`0.1 m/px`, `0.5 m/px`, `1 m/px`, `1024x768`)
- `depth_min`: Float (e.g. `4.0`)
- `depth_max`: Float (e.g. `38.0`)
- `confidence_threshold`: Integer (0-95, default `20`)

#### Response:
```json
{
  "success": true,
  "run_id": "7bf3b0f5-56ee-4df6-8051-2485fa1b8ebc",
  "mission_id": "MSN-A1F2",
  "status": "completed",
  "waterfall_url": "/api/waterfall/7bf3b0f5-56ee-4df6-8051-2485fa1b8ebc",
  "detections": [
    {
      "detection_id": "d-90124",
      "class_label": "debris",
      "confidence": 0.88,
      "risk_level": "high",
      "sadh_height_m": 2.45,
      "physics_confidence": 0.82,
      "depth_m": 18.2,
      "area_m2": 4.5,
      "latitude": 13.0629,
      "longitude": 80.3584,
      "bbox": { "x": 0.32, "y": 0.45, "width": 0.08, "height": 0.12 }
    }
  ]
}
```

---

### 2. Waterfall Preview
- **GET** `/api/waterfall/{run_id}`
- **GET** `/api/runs/{run_id}/file`
- **Response**: Image (`image/png` or original image mime)

---

### 3. All Detections Query
- **GET** `/api/detections?limit=100`
- **Response**: List of detections with SADH height and physics confidence.

---

### 4. Real-Time Acoustic Streaming
- **WebSocket** `/ws/waterfall`
- **Protocol**: JSON or Binary chunks
```json
{
  "type": "ping",
  "ping_number": 42,
  "waterfall_chunk": [120, 122, ...],
  "detections": [],
  "timestamp": "2026-09-27T00:55:00Z"
}
```
