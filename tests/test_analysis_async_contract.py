"""Safe polling contract for background analysis without loading AI weights."""

import pytest

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Analysis, Case, CaseImage, User


@pytest.fixture()
def analysis_client(isolated_storage, offline_runtime):
    app = create_app(isolated_storage["app_config"])
    with app.app_context():
        db.create_all()
        doctor = User(
            full_name="Async Doctor", email="async-doctor@example.test",
            role="DOCTOR", is_active=True, email_verified=True,
        )
        doctor.set_password("SyntheticPassword123!")
        db.session.add(doctor)
        db.session.flush()
        case = Case(
            case_code="ASYNC-SYNTHETIC-01", doctor_id=doctor.id,
            patient_snapshot={"full_name": "Synthetic Patient"}, status="CREATED",
        )
        db.session.add(case)
        db.session.flush()
        image = CaseImage(
            case_id=case.id, image_path="synthetic.png", original_filename="synthetic.png",
            mime_type="image/png", file_size=3, uploaded_by=doctor.id, status="UPLOADED",
        )
        db.session.add(image)
        db.session.flush()
        analyses = []
        for status in ("PENDING", "FAILED"):
            analysis = Analysis(case_id=case.id, case_image_id=image.id, status=status)
            if status == "FAILED":
                analysis.error_message = "synthetic failure"
            db.session.add(analysis)
            db.session.flush()
            analyses.append(analysis.id)
        db.session.commit()
        doctor_id = doctor.id
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(doctor_id)
        session["_fresh"] = True
    return client, analyses


def test_pending_analysis_remains_pending_in_poll(analysis_client):
    client, ids = analysis_client
    response = client.get(f"/api/analyses/{ids[0]}/status")
    assert response.status_code == 200
    assert response.get_json() == {"status": "PENDING"}


def test_failed_analysis_reports_existing_error(analysis_client):
    client, ids = analysis_client
    response = client.get(f"/api/analyses/{ids[1]}/status")
    assert response.status_code == 200
    assert response.get_json() == {"status": "FAILED", "error": "synthetic failure"}


def test_unknown_analysis_returns_not_found(analysis_client):
    client, _ = analysis_client
    response = client.get("/api/analyses/999999/status")
    assert response.status_code == 404
