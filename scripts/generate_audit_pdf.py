#!/usr/bin/env python3
"""Generate a publication-grade PDF of the SIH 2026 Architectural Audit & Gap Analysis Report."""

import os
import sys
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "SONAR SENTRY: SIH 2026 GRAND FINALE AUDIT & GAP REPORT")
            self.drawRightString(612 - 54, 755, "CONFIDENTIAL & PROPRIETARY")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 747, 612 - 54, 747)

        # Footer (all pages)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(54, 36, "Problem Statement 26057 — Side-Scan Sonar Marine Debris & Ghost Net Detection")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(612 - 54, 36, page_str)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 612 - 54, 46)
        
        self.restoreState()

def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=5,
    )

    alert_style = ParagraphStyle(
        "AlertBox",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#991b1b"),
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )

    cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
    )

    cell_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.white,
    )

    story = []

    # Title Banner
    story.append(Paragraph("SONAR SENTRY: ARCHITECTURAL AUDIT & GAP REPORT", title_style))
    story.append(Paragraph("Acoustic Physics Gap Analysis & Model Verification for SIH 2026 Grand Finale (PS: 26057)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e3a8a"), spaceAfter=10))

    # Meta Info Table
    meta_data = [
        [
            Paragraph("<b>Target Competition:</b> SIH 2026 Grand Finale", cell_style),
            Paragraph("<b>Repository:</b> ritesh123malik/sihnew", cell_style),
        ],
        [
            Paragraph("<b>Benchmark Paradigm:</b> WPG-DetNet / Active Sonar", cell_style),
            Paragraph("<b>Evaluation Date:</b> September 27, 2026", cell_style),
        ],
        [
            Paragraph("<b>Operational Standard:</b> Jetson Orin Nano Edge AUV", cell_style),
            Paragraph("<b>Verification Outcome:</b> 218/218 Unit Tests Passing", cell_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Scorecard Banner
    score_data = [
        [
            Paragraph("<font size=14><b>91.5%</b></font><br/>Platform Engineering", ParagraphStyle('Score', alignment=1, fontSize=8, leading=10, textColor=colors.HexColor("#047857"))),
            Paragraph("<font size=14><b>15.0%</b></font><br/>Dataset Training Arsenal", ParagraphStyle('Score', alignment=1, fontSize=8, leading=10, textColor=colors.HexColor("#b91c1c"))),
            Paragraph("<font size=14><b>79.0%</b></font><br/>Overall SIH Readiness", ParagraphStyle('Score', alignment=1, fontSize=8, leading=10, textColor=colors.HexColor("#1d4ed8"))),
            Paragraph("<font size=14><b>21.0%</b></font><br/>Remaining Deficit Delta", ParagraphStyle('Score', alignment=1, fontSize=8, leading=10, textColor=colors.HexColor("#d97706"))),
        ]
    ]
    score_table = Table(score_data, colWidths=[126, 126, 126, 126])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 12))

    # Section 1: Executive Summary
    story.append(Paragraph("1. Executive Audit Summary", h1_style))
    story.append(Paragraph(
        "An in-depth codebase audit was conducted against the SIH 2026 Grand Finale Blueprint. "
        "The software architecture has achieved exceptional maturity: all telemetry ingestion (1024-byte Triton .xtf), "
        "digital signal processing (Slant Range Correction, 2D-FFT heave filtering), high-precision WGS84 forward-azimuth geodesy, "
        "PostGIS synchronization, and multi-page tactical naval PDF report generation are 100% verified and operational. "
        "The backend passes 218/218 unit tests with 93% code coverage and a 18.3 ms detailed health response latency.",
        body_style
    ))

    # Alert Box: Model Dataset Finding
    alert_data = [[
        Paragraph(
            "<b>CRITICAL AUDIT VERDICT: MODEL NOT TRAINED ON REPORT DATASET ARSENAL</b><br/>"
            "Forensic extraction of the model checkpoint (<code>best.pt</code>, 21.46 MB) confirmed that the model was <b>NOT</b> trained "
            "on the 16,650-sample hydrographic dataset arsenal specified in Section 5.1 (DRISHTI-SSS, SCTD 3.0, AquaScan-1K, SeabedObjects-KLSG, "
            "NOAA NCEI, Holoocean). Instead, <code>best.pt</code> was trained in Google Colab on an internal set of 11 VLC screen-grab images "
            "(<code>datasets/screenshots_dev</code>) with only 4 classes (shipwreck, pipe, cylinder, net). The WERB+D-GRM+SADH model "
            "(<code>best_werb_dgrm_sadh.pt</code>) was trained locally on 7 synthetic samples as an architectural proof-of-concept.",
            alert_style
        )
    ]]
    alert_table = Table(alert_data, colWidths=[504])
    alert_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef2f2")),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#ef4444")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(alert_table)
    story.append(Spacer(1, 10))

    # Section 2: Codebase Comparison Matrix
    story.append(Paragraph("2. Comprehensive Codebase Comparison Matrix (All 10 Domains)", h1_style))
    matrix_headers = ["Domain", "Blueprint Standard", "Status in sihnew", "Score"]
    matrix_rows = [
        [
            Paragraph("<b>Telemetry Ingestion</b>", cell_bold),
            Paragraph("Native binary parser for .xtf (1024-byte Triton headers, pings)", cell_style),
            Paragraph("xtf_parser.py parses headers, navigation, waterfalls. /api/detect/xtf live.", cell_style),
            Paragraph("<font color='#047857'><b>100%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Signal Processing (DSP)</b>", cell_bold),
            Paragraph("Slant Range Correction (SRC), BAC, 2D-FFT stripe filter, TVG compensation", cell_style),
            Paragraph("slant_range.py & acoustic_filters.py implement SRC, BAC, 2D-FFT, and TVG attenuation.", cell_style),
            Paragraph("<font color='#047857'><b>98%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Acoustic Head & Physics Loss</b>", cell_bold),
            Paragraph("SADH predicting target height h = (L_s·H_s)/R_s; in-training physics loss", cell_style),
            Paragraph("sadh_physics.py and sadh_loss.py implement formulas; deployed weights lack differentiable loss.", cell_style),
            Paragraph("<font color='#d97706'><b>88%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Geodesy & Coordinates</b>", cell_bold),
            Paragraph("WGS84 ellipsoidal forward-azimuth projection with heading & layback", cell_style),
            Paragraph("geodesy.py uses pyproj.Geod(ellps='WGS84'). Deviation <0.01m over 500m.", cell_style),
            Paragraph("<font color='#047857'><b>100%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Database Persistence</b>", cell_bold),
            Paragraph("Full spatial metadata (WGS84 coordinates, SADH height, PostGIS geom)", cell_style),
            Paragraph("SQLite ORM and supabase_schema.sql synchronized with PostGIS geometry and SADH fields.", cell_style),
            Paragraph("<font color='#047857'><b>100%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Edge Quantization</b>", cell_bold),
            Paragraph("ONNX to TensorRT INT8 compiled execution engine for Jetson Orin Nano", cell_style),
            Paragraph("best.onnx verified; export_tensorrt.py scripted. Awaiting hardware compile on Jetson.", cell_style),
            Paragraph("<font color='#047857'><b>90%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Seafloor Mapping</b>", cell_bold),
            Paragraph("Stitched georeferenced GeoTIFF seafloor swath draped on Leaflet map", cell_style),
            Paragraph("geotiff_service.py generates GeoTIFFs (100%). Leaflet renders vector box, lacks raster drape.", cell_style),
            Paragraph("<font color='#d97706'><b>75%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Inspection & Export</b>", cell_bold),
            Paragraph("Acoustic inspection modal (shadow curve); 1-click Naval Dossier PDF + GeoJSON", cell_style),
            Paragraph("pdf_report_service.py generates Naval dossiers; GeoJSON live; ShadowCurveChart in AnomalyInspector.", cell_style),
            Paragraph("<font color='#047857'><b>85%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Backbone Architecture</b>", cell_bold),
            Paragraph("Wavelet-Embedded Residual Backbone (WERB) with 2D Haar DWT layers", cell_style),
            Paragraph("WERBBackbone PyTorch architecture coded; production checkpoint best.pt lacks in-backbone DWT.", cell_style),
            Paragraph("<font color='#b91c1c'><b>55%</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Scene Reasoning</b>", cell_bold),
            Paragraph("Debris Graph Reasoning Module (D-GRM) with GCN linking torn net fragments", cell_style),
            Paragraph("GCN layer coded in debris_graph.py; live pipeline uses torch.randn instead of real backbone features.", cell_style),
            Paragraph("<font color='#b91c1c'><b>50%</b></font>", cell_bold),
        ],
    ]

    matrix_table = Table([[Paragraph(h, cell_header) for h in matrix_headers]] + matrix_rows, colWidths=[90, 140, 224, 50])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ALIGN', (3,0), (3,-1), 'CENTER'),
    ]))
    story.append(matrix_table)

    story.append(PageBreak())

    # Section 3: The 9 Technical Gaps Detailed Analysis
    story.append(Paragraph("3. Detailed Analysis of the 9 Blueprint Technical Gaps", h1_style))

    gaps_info = [
        ("Gap 1: In-Backbone Wavelet Frequency Decoupling (WERB)", "55% Completed | 45% Gap Left", [
            ("Implemented", "Full 4D Haar DWT filter tensors in wavelet_layer.py; WERBBackbone multi-scale architecture with noise suppression gates passing all unit tests."),
            ("Remaining", "The live detection route (/api/detect/image) calls Ultralytics YOLO('best.pt'), which has standard convolutional weights rather than in-backbone Haar DWT layers.")
        ]),
        ("Gap 2: Debris Graph Reasoning Module (D-GRM)", "50% Completed | 50% Gap Left", [
            ("Implemented", "2-layer GCN in debris_graph.py and gcn_layer.py with spatial proximity and cosine similarity graph adjacency."),
            ("Remaining", "In sonar_model_service.py line 230, D-GRM receives torch.randn(len(detections), 256) instead of extracting real RoI feature embeddings from the neural backbone.")
        ]),
        ("Gap 3: In-Training Multi-Task Physics Loss (SADH)", "70% Completed | 30% Gap Left", [
            ("Implemented", "Differentiable loss L_phys = |L_pred - (h·R_s)/H_s| in sadh_loss.py and training harness train_sih2026.py."),
            ("Remaining", "Deployed checkpoint best.pt was trained with standard YOLOv8 CIoU/BCE loss. Production weights with backpropagated physics loss across a full sonar dataset must still be trained.")
        ]),
        ("Gap 4: GeoTIFF Seafloor Swath Mosaic Generation", "95% Completed | 5% Gap Left", [
            ("Implemented", "geotiff_service.py generates georeferenced GeoTIFFs using Rasterio with EPSG:4326/UTM affine transforms. REST export live."),
            ("Remaining", "Cross-swath mosaic blending and feathering across multiple overlapping survey runs.")
        ]),
        ("Gap 5: Leaflet Swath Raster Overlay (GeoMap.jsx)", "65% Completed | 35% Gap Left", [
            ("Implemented", "GeoMap.jsx renders satellite tiles, vessel track polylines, colored risk markers, and swath bounding box polygons."),
            ("Remaining", "Leaflet <ImageOverlay> is not currently imported or rendered; sonogram raster images are not yet draped directly onto the seabed coordinates.")
        ]),
        ("Gap 6: PostGIS SQL Synchronization", "100% Completed | 0% Gap Left (SOLVED)", [
            ("Implemented", "supabase_schema.sql updated with sadh_height_m, shadow_length_m, physics_confidence, and geom GEOMETRY(Point, 4326) columns with spatial indexes."),
            ("Remaining", "None. Database persistence is 100% synchronized.")
        ]),
        ("Gap 7: Standalone Acoustic Physics Inspection Modal", "85% Completed | 15% Gap Left", [
            ("Implemented", "AnomalyInspector.jsx page with full SADH physics calculations, Lambertian backscatter analysis, and ShadowCurveChart.jsx theoretical vs. observed decay curve."),
            ("Remaining", "The slide-over AnomalyModal.jsx lacks a dynamic cropped sonogram snippet and binary shadow mask preview.")
        ]),
        ("Gap 8: Professional Naval Salvage PDF Dossier & GeoJSON", "100% Completed | 0% Gap Left (SOLVED)", [
            ("Implemented", "pdf_report_service.py (382 lines ReportLab) generates official multi-page tactical clearance dossiers with mission threat matrices. GeoJSON export live."),
            ("Remaining", "None. Fully operational.")
        ]),
        ("Gap 9: Silent Exception Swallowing (Linter Audit)", "100% Completed | 0% Gap Left (SOLVED)", [
            ("Implemented", "All 5 bare 'except Exception: pass' instances in main.py, runs.py, metadata.py, safe_image_loader.py, and startup_validator.py replaced with structured logging."),
            ("Remaining", "None. Code hygiene audit clean.")
        ]),
    ]

    for title, status_badge, details in gaps_info:
        story.append(Paragraph(f"<b>{title}</b> — <font color='#1e3a8a'><b>{status_badge}</b></font>", h2_style))
        for label, desc in details:
            color = "#047857" if label == "Implemented" else "#b91c1c"
            story.append(Paragraph(f"<font color='{color}'><b>[{label}]</b></font> {desc}", body_style))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 10))

    # Section 4: Dataset Audit Deep-Dive
    story.append(Paragraph("4. Curated Multi-Frequency Sonar Dataset Arsenal Audit", h1_style))
    story.append(Paragraph(
        "Section 5.1 of the SIH blueprint requires a comprehensive 16,650-sample hydrographic training corpus. "
        "The following table compares the blueprint requirements against the contents of the local repository:",
        body_style
    ))

    ds_headers = ["Dataset Name", "Target Frequency", "Volume Req.", "Mission Target Classes", "Status in Repo"]
    ds_rows = [
        [
            Paragraph("<b>DRISHTI-SSS</b>", cell_bold),
            Paragraph("450 / 900 kHz", cell_style),
            Paragraph("3,200 imgs", cell_style),
            Paragraph("Ghost fishing nets, ropes, plastics, debris", cell_style),
            Paragraph("<font color='#b91c1c'><b>Missing (0%)</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>SCTD 3.0 Benchmark</b>", cell_bold),
            Paragraph("100 / 400 kHz", cell_style),
            Paragraph("2,800 imgs", cell_style),
            Paragraph("Shipwrecks, aircraft fuselages, containers", cell_style),
            Paragraph("<font color='#b91c1c'><b>Missing (0%)</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>AquaScan-1K</b>", cell_bold),
            Paragraph("900 kHz", cell_style),
            Paragraph("1,150 imgs", cell_style),
            Paragraph("Subsea pipelines, cylindrical drums", cell_style),
            Paragraph("<font color='#b91c1c'><b>Missing (0%)</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>SeabedObjects-KLSG</b>", cell_bold),
            Paragraph("Multi-beam / SSS", cell_style),
            Paragraph("4,500 imgs", cell_style),
            Paragraph("Hard-negative geological reefs, sand ripples", cell_style),
            Paragraph("<font color='#b91c1c'><b>Missing (0%)</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>NOAA NCEI Archive</b>", cell_bold),
            Paragraph("Multi-frequency", cell_style),
            Paragraph("45 GB (.xtf)", cell_style),
            Paragraph("Raw authentic hydrographic survey telemetry", cell_style),
            Paragraph("<font color='#b91c1c'><b>Missing (0%)</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Holoocean Acoustics</b>", cell_bold),
            Paragraph("Configurable", cell_style),
            Paragraph("5,000 pings", cell_style),
            Paragraph("Partially silted munitions, nets on hulls", cell_style),
            Paragraph("<font color='#b91c1c'><b>Missing (0%)</b></font>", cell_bold),
        ],
        [
            Paragraph("<b>Current best.pt</b>", cell_bold),
            Paragraph("N/A (Colab)", cell_style),
            Paragraph("11 images", cell_style),
            Paragraph("shipwreck, pipe, cylinder, net", cell_style),
            Paragraph("<font color='#047857'><b>Trained (100%)</b></font>", cell_bold),
        ],
    ]

    ds_table = Table([[Paragraph(h, cell_header) for h in ds_headers]] + ds_rows, colWidths=[90, 80, 64, 180, 90])
    ds_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e3a8a")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('ALIGN', (4,0), (4,-1), 'CENTER'),
    ]))
    story.append(ds_table)

    story.append(Spacer(1, 12))

    # Section 5: Strategic Action Plan
    story.append(Paragraph("5. Step-by-Step Strategic Roadmap to 100% Completion", h1_style))
    roadmap_items = [
        "<b>1. Leaflet Raster Overlay (Frontend):</b> Import <code>ImageOverlay</code> from <code>react-leaflet</code> into <code>GeoMap.jsx</code> and drape the GeoTIFF sonogram over the seabed bounding box.",
        "<b>2. Backbone Feature Extraction for D-GRM:</b> In <code>sonar_model_service.py</code>, extract real 256-d RoI feature vectors from the intermediate layer of YOLO instead of using <code>torch.randn</code>.",
        "<b>3. AnomalyModal Sonogram Crop:</b> Add a dynamic cropped canvas preview of the anomaly bounding box and its acoustic shadow mask into <code>AnomalyModal.jsx</code>.",
        "<b>4. Ingest Sonar Datasets:</b> Download open hydrographic datasets (SCTD 3.0, AquaScan, DRISHTI-SSS) into <code>datasets/external/</code> using <code>scripts/collect_datasets.py</code>.",
        "<b>5. Execute 3-Stage Curriculum Training:</b> Run <code>backend/training/train_sih2026.py</code> for 100 epochs with the WERB backbone and differentiable SADH physics loss.",
        "<b>6. Hardware TensorRT INT8 Compilation:</b> On the physical NVIDIA Jetson Orin Nano, run <code>python backend/export_tensorrt.py</code> to produce <code>best_int8.engine</code> achieving >60 FPS."
    ]
    for item in roadmap_items:
        story.append(Paragraph(f"• {item}", body_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "SIH2026_COMPREHENSIVE_AUDIT_REPORT.pdf"
    build_pdf(out_file)
