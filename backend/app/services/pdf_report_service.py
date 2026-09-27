"""Naval Salvage & Clearance PDF Dossier Service.

Generates tactical mission reports for Indian Navy, Coast Guard, and Port Authorities.
Includes acoustic targets, shadow-dispersion physics validation, geodetic coordinates,
and salvage priority matrices.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger("sonar_pdf_service")


class NavalPDFReportService:
    """PDF Dossier and Geospatial Report Exporter."""

    def __init__(self, export_dir: Union[str, Path] = "backend/export/pdf"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def generate_salvage_dossier(
        self,
        mission_info: Dict[str, Any],
        detections: List[Dict[str, Any]],
        output_filename: Optional[str] = None,
    ) -> Path:
        """Generate high-authority PDF clearance dossier."""
        mission_id = mission_info.get("mission_id", f"MSN-{datetime.now().strftime('%Y%m%d-%H%M')}")
        if not output_filename:
            output_filename = f"NAV_SALVAGE_{mission_id}.pdf"

        file_path = self.export_dir / output_filename
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,  # Center
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "SubTitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#0284c7"),
            alignment=1,
            fontName="Helvetica-Bold",
        )
        header_meta = ParagraphStyle(
            "HeaderMeta",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
        )
        table_hdr_style = ParagraphStyle(
            "TableHdr",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName="Helvetica-Bold",
            alignment=1,
        )
        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#1e293b"),
        )
        table_cell_center = ParagraphStyle(
            "TableCellCenter",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#1e293b"),
            alignment=1,
        )

        story = []

        # Header Title
        story.append(Paragraph("SONAR SENTRY TACTICAL SALVAGE &amp; CLEARANCE DOSSIER", title_style))
        story.append(Paragraph("INDIAN NAVY &amp; COAST GUARD HYDROGRAPHIC RECONNAISSANCE UNIT", subtitle_style))
        story.append(Spacer(1, 0.15 * inch))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

        # Mission Metadata Grid
        vessel = mission_info.get("vessel", "INS Sandhayak (J18)")
        date_str = mission_info.get("date", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
        area = mission_info.get("area", "Arabian Sea Sector 4B")
        swath_w = mission_info.get("swath_width_m", 100.0)
        alt_m = mission_info.get("altitude_m", 12.5)

        meta_data = [
            [
                Paragraph(f"<b>Mission ID:</b> {mission_id}", header_meta),
                Paragraph(f"<b>Survey Vessel:</b> {vessel}", header_meta),
            ],
            [
                Paragraph(f"<b>Execution Date:</b> {date_str}", header_meta),
                Paragraph(f"<b>Survey Sector:</b> {area}", header_meta),
            ],
            [
                Paragraph(f"<b>Towfish Altitude:</b> {alt_m:.1f} m", header_meta),
                Paragraph(f"<b>Swath Width:</b> {swath_w:.1f} m", header_meta),
            ],
            [
                Paragraph(f"<b>Total Anomalies:</b> {len(detections)}", header_meta),
                Paragraph("<b>Classification:</b> RESTRICTED / OPERATIONAL", header_meta),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[3.75 * inch, 3.75 * inch])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(meta_table)
        story.append(Spacer(1, 0.2 * inch))

        # Anomaly Findings Section
        story.append(Paragraph("<b>TARGET DETECTION INVENTORY &amp; PHYSICS VALIDATION</b>", styles["Heading3"]))
        story.append(Spacer(1, 0.05 * inch))

        table_headers = [
            Paragraph("ID", table_hdr_style),
            Paragraph("Class", table_hdr_style),
            Paragraph("Conf", table_hdr_style),
            Paragraph("Height (m)", table_hdr_style),
            Paragraph("Shadow (m)", table_hdr_style),
            Paragraph("Physics", table_hdr_style),
            Paragraph("WGS84 Coordinates", table_hdr_style),
            Paragraph("Action Priority", table_hdr_style),
        ]
        det_rows = [table_headers]

        for idx, d in enumerate(detections, start=1):
            det_id = d.get("id", f"TGT-{idx:03d}")
            label = d.get("label", "unknown").replace("_", " ").title()
            conf = d.get("confidence", 0.0)
            h_m = d.get("height_m", 0.0)
            s_m = d.get("shadow_length_m", 0.0)
            phys_ok = d.get("physics_verified", True)
            lat = d.get("latitude")
            lng = d.get("longitude")
            coord_str = f"{lat:.5f}, {lng:.5f}" if lat and lng else "N/A"

            # Action Priority
            if label.lower() in ["ghost net", "shipwreck"] or conf > 0.85:
                prio = '<font color="#dc2626"><b>CRITICAL</b></font>'
            elif conf > 0.65:
                prio = '<font color="#d97706"><b>ELEVATED</b></font>'
            else:
                prio = '<font color="#16a34a"><b>ROUTINE</b></font>'

            phys_badge = '<font color="#16a34a">PASS</font>' if phys_ok else '<font color="#dc2626">FAIL</font>'

            row = [
                Paragraph(str(det_id), table_cell_center),
                Paragraph(label, table_cell_style),
                Paragraph(f"{conf * 100:.1f}%", table_cell_center),
                Paragraph(f"{h_m:.2f} m" if h_m else "N/A", table_cell_center),
                Paragraph(f"{s_m:.2f} m" if s_m else "N/A", table_cell_center),
                Paragraph(phys_badge, table_cell_center),
                Paragraph(coord_str, table_cell_style),
                Paragraph(prio, table_cell_center),
            ]
            det_rows.append(row)

        if len(det_rows) == 1:
            det_rows.append([Paragraph("No acoustic anomalies recorded in scan.", table_cell_style)] * 8)

        det_table = Table(
            det_rows,
            colWidths=[
                0.65 * inch,
                1.2 * inch,
                0.65 * inch,
                0.85 * inch,
                0.85 * inch,
                0.65 * inch,
                1.6 * inch,
                1.05 * inch,
            ],
        )
        det_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(det_table)
        story.append(Spacer(1, 0.25 * inch))

        # Salvage Action Recommendations
        story.append(Paragraph("<b>OPERATIONAL SALVAGE PROTOCOLS &amp; NAVAL DIRECTIVES</b>", styles["Heading3"]))
        recomms = (
            "1. Deploy Autonomous Underwater Vehicle (AUV) for optical inspection of Critical priority contacts.<br/>"
            "2. Ghost net anomalies represent severe hazard to submarine propulsion and marine biodiversity; prioritize immediate recovery.<br/>"
            "3. Coordinate with Maritime Rescue Coordination Centre (MRCC) Mumbai for maritime notice dissemination."
        )
        story.append(Paragraph(recomms, header_meta))

        doc.build(story)
        logger.info("Generated Naval Dossier PDF at: %s", file_path)
        return file_path

    def export_detections_geojson(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export detections as standardized GeoJSON FeatureCollection."""
        features = []
        for idx, d in enumerate(detections, start=1):
            lat = d.get("latitude")
            lng = d.get("longitude")
            if lat is None or lng is None:
                continue

            feature = {
                "type": "Feature",
                "id": d.get("id", f"feat_{idx}"),
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lng), float(lat)],
                },
                "properties": {
                    "label": d.get("label", "unknown"),
                    "confidence": d.get("confidence", 0.0),
                    "height_m": d.get("height_m"),
                    "shadow_length_m": d.get("shadow_length_m"),
                    "physics_verified": d.get("physics_verified", True),
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        }

    def export_detections_csv(self, detections: List[Dict[str, Any]]) -> str:
        """Export detections as CSV string."""
        output = io.StringIO()
        fieldnames = [
            "id",
            "label",
            "confidence",
            "latitude",
            "longitude",
            "height_m",
            "shadow_length_m",
            "physics_verified",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for idx, d in enumerate(detections, start=1):
            writer.writerow(
                {
                    "id": d.get("id", f"TGT-{idx:03d}"),
                    "label": d.get("label", "unknown"),
                    "confidence": round(d.get("confidence", 0.0), 4),
                    "latitude": d.get("latitude", ""),
                    "longitude": d.get("longitude", ""),
                    "height_m": d.get("height_m", ""),
                    "shadow_length_m": d.get("shadow_length_m", ""),
                    "physics_verified": d.get("physics_verified", True),
                }
            )
        return output.getvalue()

    def generate_dossier(
        self,
        run_id: str,
        detections: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        swath_image_path: Optional[Union[str, Path]] = None,
        vessel_track: Optional[List[Dict[str, Any]]] = None,
        output_path: Optional[Union[str, Path]] = None,
        include_geojson: bool = True,
    ) -> Dict[str, Path]:
        """Wrapper matching SIH-26057 Phase 2 interface."""
        mission_info = {
            "mission_id": run_id,
            "vessel": metadata.get("vessel_name", "INS Sandhayak (J18)"),
            "area": metadata.get("mission_name", "Arabian Sea Sector 4B"),
            "swath_width_m": metadata.get("swath_width_m", 100.0),
            "altitude_m": metadata.get("altitude_m", 12.5),
            "date": metadata.get("timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")),
        }
        filename = Path(output_path).name if output_path else f"NAV_SALVAGE_{run_id}.pdf"
        pdf_path = self.generate_salvage_dossier(mission_info, detections, filename)

        geojson_path = None
        if include_geojson:
            geojson_data = self.export_detections_geojson(detections)
            geojson_file = self.export_dir / f"dossier_{run_id}.geojson"
            with open(geojson_file, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=2)
            geojson_path = geojson_file

        return {"pdf": Path(pdf_path), "geojson": geojson_path}

    def generate_detection_pdf(
        self,
        detection: Dict[str, Any],
        sonar_image_path: Optional[Union[str, Path]] = None,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Generate tactical clearance sheet for a single target."""
        det_id = detection.get("id", "target")
        out_name = Path(output_path).name if output_path else f"detection_{det_id}.pdf"
        file_path = self.export_dir / out_name

        mission_info = {
            "mission_id": f"TGT-{det_id}",
            "vessel": "Inspection Vehicle",
            "area": f"Fix: {detection.get('latitude', 0):.5f}, {detection.get('longitude', 0):.5f}",
            "swath_width_m": 50.0,
            "altitude_m": detection.get("depth_m", 10.0),
        }
        return self.generate_salvage_dossier(mission_info, [detection], out_name)

    def generate_geojson(
        self,
        run_id: str,
        detections: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        vessel_track: Optional[List[Dict[str, Any]]] = None,
    ) -> Path:
        geojson_data = self.export_detections_geojson(detections)
        out_path = self.export_dir / f"dossier_{run_id}.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)
        return out_path


# Export aliases
PDFReportService = NavalPDFReportService
pdf_report_service = NavalPDFReportService()

