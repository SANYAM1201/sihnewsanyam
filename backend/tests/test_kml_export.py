import pytest
from app.services.kml_service import kml_service


def test_kml_generation():
    detections = [
        {"id": "TRG-01", "class_label": "Ghost Net", "risk_level": "critical", "confidence": 0.95, "latitude": 18.9220, "longitude": 72.8347, "sadh_height_m": 2.1, "depth_m": 14.5},
        {"id": "TRG-02", "class_label": "Cylindrical Drum", "risk_level": "high", "confidence": 0.89, "latitude": 18.9285, "longitude": 72.8410, "sadh_height_m": 1.4, "depth_m": 16.2},
    ]

    kml_str = kml_service.generate_kml(detections, survey_title="Test Acoustic Survey")
    assert "<kml" in kml_str
    assert "</kml>" in kml_str
    assert "Test Acoustic Survey" in kml_str
    assert "Ghost Net" in kml_str
    assert "18.922000" in kml_str or "72.834700" in kml_str
    assert "Placemark" in kml_str
