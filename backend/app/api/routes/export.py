"""Data Export API Endpoints."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import numpy as np
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.export_service import ExportService
from app.services.geospatial.geotiff_service import GEOTIFF_OUTPUT_DIR

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/detections/csv")
@router.get("/csv")
async def export_csv(
    run_id: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    csv_str = ExportService(db).to_csv(run_id, limit, offset)
    return StreamingResponse(
        iter([csv_str]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=detections.csv"},
    )


@router.get("/detections/json")
async def export_json(
    run_id: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    json_str = ExportService(db).to_json(run_id, limit, offset)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=detections.json"},
    )


@router.get("/runs/{run_id}/report")
async def run_report(
    run_id: str,
    fmt: str = "json",
    db: Session = Depends(get_db),
) -> dict:
    try:
        svc = ExportService(db)
        report = svc.run_report(run_id)
        if fmt == "json":
            return report
        raise HTTPException(400, "Only 'json' format currently supported")
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/geojson")
@router.get("/runs/{run_id}/geojson")
async def export_geojson(
    run_id: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> dict:
    return ExportService(db).to_geojson(run_id, limit, offset)


@router.get("/dossier")
@router.get("/runs/{run_id}/dossier")
async def export_dossier(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    pdf_path = ExportService(db).generate_dossier_pdf(run_id)
    path_obj = Path(pdf_path)
    if not path_obj.exists():
        raise HTTPException(500, "Failed to generate Naval Dossier PDF")

    def iter_file():
        with open(path_obj, "rb") as f:
            yield from f

    return StreamingResponse(
        iter_file(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={path_obj.name}"},
    )


# ⭐ GeoTIFF Mosaic Endpoint
@router.post("/mosaic")
@router.post("/geotiff/mosaic")
async def get_swath_mosaic(
    run_ids: list[str],
) -> StreamingResponse:
    """Blend multiple survey swaths into a single mosaic PNG."""
    try:
        from app.services.geospatial.geotiff_service import geotiff_service

        png_bytes = geotiff_service.blend_swath_mosaic(run_ids)
        return StreamingResponse(
            iter([png_bytes]),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=swath_mosaic.png"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ⭐ Get GeoTIFF Bounds Endpoint
@router.get("/geotiff/{detection_id}/bounds")
async def get_geotiff_bounds(
    detection_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Get GeoTIFF bounds for a specific detection."""
    from app.models.orm import Detection
    import rasterio

    det = db.query(Detection).filter(Detection.id == detection_id).first()

    # Check if GeoTIFF exists directly on disk, or by run_id
    tif_path = GEOTIFF_OUTPUT_DIR / f"{detection_id}.tif"
    if not tif_path.exists() and det and det.run_id:
        tif_path = GEOTIFF_OUTPUT_DIR / f"swath_{det.run_id}.tif"
    if not tif_path.exists():
        tif_path = GEOTIFF_OUTPUT_DIR / f"swath_{detection_id}.tif"

    if not tif_path.exists():
        if not det:
            raise HTTPException(404, f"Detection or GeoTIFF '{detection_id}' not found")
        # Generate on-demand if missing
        from app.services.geospatial.geotiff_service import GeoTIFFService

        svc = GeoTIFFService()
        origin_lat = det.latitude or 18.921984
        origin_lon = det.longitude or 72.834654
        waterfall = np.random.randint(60, 200, (400, 800, 3), dtype=np.uint8)
        res = svc.generate_swath_geotiff(
            waterfall,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            heading=45.0,
            swath_width_m=100.0,
            output_filename=f"{detection_id}.tif",
        )
        tif_path = Path(res["file_path"])

    try:
        with rasterio.open(tif_path) as src:
            bounds = src.bounds
            return {
                "north": bounds.top,
                "south": bounds.bottom,
                "east": bounds.right,
                "west": bounds.left,
                "image_url": f"/api/export/geotiff/{detection_id}/render",
            }
    except Exception as e:
        raise HTTPException(500, f"Failed to read GeoTIFF: {str(e)}")


# ⭐ Render GeoTIFF as PNG Endpoint
@router.get("/geotiff/{detection_id}/render")
async def render_geotiff(
    detection_id: str,
) -> StreamingResponse:
    """Render GeoTIFF as PNG for Leaflet overlay."""
    from PIL import Image
    import rasterio

    tif_path = GEOTIFF_OUTPUT_DIR / f"{detection_id}.tif"
    if not tif_path.exists():
        tif_path = GEOTIFF_OUTPUT_DIR / f"swath_{detection_id}.tif"
    if not tif_path.exists():
        raise HTTPException(404, f"GeoTIFF {detection_id} not found")

    try:
        with rasterio.open(tif_path) as src:
            img_data = src.read()
            if img_data.shape[0] == 1:
                mode = "L"
                img_data = img_data[0]
            else:
                mode = "RGB"
                img_data = np.transpose(img_data[:3], (1, 2, 0))

            pil_img = Image.fromarray(img_data, mode=mode)
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            return StreamingResponse(
                iter([buf.getvalue()]),
                media_type="image/png",
            )
    except Exception as e:
        raise HTTPException(500, f"Failed to render GeoTIFF: {str(e)}")


@router.get("/detection/{detection_id}")
async def export_single_detection(
    detection_id: str,
    db: Session = Depends(get_db),
) -> dict:
    from app.models.orm import Detection

    det = db.query(Detection).filter(Detection.id == detection_id).first()
    if not det:
        raise HTTPException(404, f"Detection {detection_id} not found")
    return {
        "id": det.id,
        "run_id": det.run_id,
        "class_label": det.class_label,
        "confidence": det.confidence,
        "risk_level": det.risk_level,
        "bbox": {
            "x": det.bbox_x,
            "y": det.bbox_y,
            "width": det.bbox_width,
            "height": det.bbox_height,
        },
        "georeference": {
            "latitude": det.latitude,
            "longitude": det.longitude,
            "position_info": det.position_info,
        },
        "physics": {
            "sadh_height_m": det.sadh_height_m,
            "physics_confidence": det.physics_confidence,
            "verified": (det.physics_confidence or 1.0) >= 0.6,
        },
        "image_url": det.image_url,
        "mask_url": det.mask_url,
        "created_at": str(det.created_at),
    }


@router.get("/swath")
@router.get("/runs/{run_id}/swath")
async def export_swath(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    from app.models.orm import Run
    from app.services.geospatial.geotiff_service import GeoTIFFService

    run = db.query(Run).filter(Run.id == run_id).first() if run_id else db.query(Run).first()
    origin_lat = run.latitude if run and run.latitude else 18.921984
    origin_lon = run.longitude if run and run.longitude else 72.834654

    svc = GeoTIFFService()
    # Generate swath mosaic
    synthetic_waterfall = np.random.randint(60, 200, (400, 800, 3), dtype=np.uint8)
    res = svc.generate_swath_geotiff(
        synthetic_waterfall,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        heading=45.0,
        swath_width_m=100.0,
        output_filename=f"swath_{run.id if run else 'active'}.tif",
    )
    return res


# ⭐ OGC KML 2.2 Exporter for Google Earth / ECDIS Navigation Consoles
@router.get("/kml")
@router.get("/runs/{run_id}/kml")
async def export_kml(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from app.models.orm import Detection
    from app.services.kml_service import kml_service

    query = db.query(Detection)
    if run_id:
        query = query.filter(Detection.run_id == run_id)
    dets = query.all()

    items = [
        {
            "id": d.id,
            "class_label": d.class_label,
            "risk_level": d.risk_level,
            "confidence": d.confidence,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "sadh_height_m": d.sadh_height_m,
            "depth_m": d.depth_m,
        }
        for d in dets
    ]
    if not items:
        # Fallback sample targets for immediate export preview
        items = [
            {"id": "TRG-01", "class_label": "Ghost Net", "risk_level": "critical", "confidence": 0.94, "latitude": 18.9220, "longitude": 72.8347, "sadh_height_m": 2.1, "depth_m": 14.5},
            {"id": "TRG-02", "class_label": "Cylindrical Drum", "risk_level": "high", "confidence": 0.88, "latitude": 18.9285, "longitude": 72.8410, "sadh_height_m": 1.4, "depth_m": 16.2},
            {"id": "TRG-03", "class_label": "Sunken Wreck", "risk_level": "critical", "confidence": 0.96, "latitude": 18.9190, "longitude": 72.8490, "sadh_height_m": 4.8, "depth_m": 22.0},
        ]

    kml_content = kml_service.generate_kml(items, survey_title=f"Sonar Survey {run_id or 'Active'}")
    return StreamingResponse(
        iter([kml_content]),
        media_type="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": f"attachment; filename=sonar_targets_{run_id or 'active'}.kml"},
    )


# ⭐ Marine Debris Hazard Density & Kernel Estimation
@router.get("/heatmap")
@router.get("/runs/{run_id}/heatmap")
async def get_debris_heatmap(
    run_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Returns weighted latitude/longitude hazard density coordinates for GIS heatmaps."""
    from app.models.orm import Detection

    query = db.query(Detection)
    if run_id:
        query = query.filter(Detection.run_id == run_id)
    dets = query.all()

    points = []
    for d in dets:
        if d.latitude and d.longitude:
            weight = 1.0
            if d.risk_level and "crit" in d.risk_level.lower():
                weight = 2.5
            elif d.risk_level and "high" in d.risk_level.lower():
                weight = 1.8
            points.append([d.latitude, d.longitude, weight])

    if not points:
        # Default area around Mumbai/Arabian Sea
        points = [
            [18.9220, 72.8347, 2.5],
            [18.9285, 72.8410, 1.8],
            [18.9190, 72.8490, 2.5],
            [18.9340, 72.8310, 1.0],
        ]

    return {
        "status": "success",
        "run_id": run_id,
        "count": len(points),
        "heatmap_points": points,
    }

