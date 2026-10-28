"""Deterministic measurement boundaries using generated dermoscopy-like shapes."""

from PIL import Image, ImageDraw

from skin_cancer.webapp.services.measurement_service import MeasurementService


def test_measurement_rejects_unreadable_image(tmp_path):
    result = MeasurementService().measure(tmp_path / "missing.png", tmp_path / "output")
    assert result.status == "FAILED"
    assert result.error_code == "IMAGE_READ_ERROR"


def test_measurement_returns_bounded_geometry_for_synthetic_lesion(tmp_path):
    image = Image.new("RGB", (128, 128), "white")
    ImageDraw.Draw(image).ellipse((36, 39, 92, 95), fill="black")
    source = tmp_path / "synthetic-lesion.png"
    image.save(source)

    result = MeasurementService().measure(source, tmp_path / "contours")

    assert result.status == "COMPLETED"
    assert 1500 <= result.lesion_area_px <= 3200
    assert 120 <= result.lesion_perimeter_px <= 250
    assert 0.05 <= result.lesion_ratio <= 0.25
    assert 25 <= result.bbox_x <= 45
    assert 25 <= result.bbox_y <= 48
    assert 45 <= result.bbox_width <= 70
    assert 45 <= result.bbox_height <= 70
