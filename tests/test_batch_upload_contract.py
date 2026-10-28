"""Batch-upload API characterization with synthetic, isolated images."""

import io

import pytest
from PIL import Image

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Case, CaseImage, UploadBatch, User


@pytest.fixture()
def batch_client(isolated_storage, offline_runtime):
    app = create_app(isolated_storage["app_config"])
    with app.app_context():
        db.create_all()
        doctor = User(
            full_name="Synthetic Doctor", email="batch-doctor@example.test",
            role="DOCTOR", is_active=True, email_verified=True,
        )
        doctor.set_password("SyntheticPassword123!")
        db.session.add(doctor)
        db.session.flush()
        case = Case(
            case_code="BATCH-SYNTHETIC-01", doctor_id=doctor.id,
            patient_snapshot={"full_name": "Synthetic Patient"}, status="CREATED",
        )
        db.session.add(case)
        db.session.commit()
        doctor_id, case_id = doctor.id, case.id
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(doctor_id)
        session["_fresh"] = True
    return app, client, case_id, isolated_storage


def _png(color):
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def test_mixed_batch_preserves_valid_image_and_reports_partial(batch_client):
    app, client, case_id, storage = batch_client
    response = client.post(
        f"/api/cases/{case_id}/upload-batch",
        data={"images": [
            (_png("green"), "valid.png", "image/png"),
            (io.BytesIO(b"not a PNG"), "broken.png", "image/png"),
        ]},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    body = response.get_json()
    assert (body["total_images"], body["success_count"], body["failed_count"]) == (2, 1, 1)
    assert body["status"] == "PARTIAL"
    assert sorted(item["status"] for item in body["items"]) == ["FAILED", "UPLOADED"]
    assert body["csv_path"] == "private"
    with app.app_context():
        batch = db.session.get(UploadBatch, body["batch_id"])
        assert batch.status == "PARTIAL"
        assert db.session.query(CaseImage).filter_by(batch_id=batch.id).count() == 2
    assert len(list((storage["upload_dir"] / "images").glob("*.png"))) == 1


def test_batch_rejects_missing_images_without_creating_batch(batch_client):
    app, client, case_id, _ = batch_client
    response = client.post(f"/api/cases/{case_id}/upload-batch", data={})
    assert response.status_code == 400
    with app.app_context():
        assert db.session.query(UploadBatch).count() == 0


def test_batch_rejects_more_than_configured_limit(batch_client):
    app, client, case_id, _ = batch_client
    app.config["BATCH_MAX_IMAGES"] = 1
    response = client.post(
        f"/api/cases/{case_id}/upload-batch",
        data={"images": [(_png("green"), "first.png"), (_png("red"), "second.png")]},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    with app.app_context():
        assert db.session.query(UploadBatch).count() == 0
