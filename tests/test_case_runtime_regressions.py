"""Regression tests for errors observed in case API branches."""

from datetime import date
import sys
from types import ModuleType

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Analysis, AnalysisResult, Case, CaseImage, User
from skin_cancer.webapp.services import result_cache


def _doctor_client(isolated_storage):
    app = create_app(isolated_storage["app_config"])
    with app.app_context():
        db.create_all()
        doctor = User(
            full_name="Test Doctor", email="doctor-isolated@example.test",
            role="DOCTOR", is_active=True, email_verified=True,
        )
        doctor.set_password("TestPassword123!")
        db.session.add(doctor)
        db.session.commit()
        doctor_id = doctor.id

    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(doctor_id)
        session["_fresh"] = True
    return app, client, doctor_id


def test_doctor_statistics_empty_month_returns_zero_without_name_error(isolated_storage):
    _, client, _ = _doctor_client(isolated_storage)

    response = client.get("/api/doctor/statistics")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["metrics"]["total_analyses"] == 0
    assert payload["trends"] == [{
        "key": date.today().strftime("%Y-%m"),
        "label": f"Tháng {date.today().month}/{date.today().year}",
        "total": 0, "malignant": 0, "benign": 0,
    }]


def test_chatgpt_cache_failure_logs_warning_and_returns_consultation(
    isolated_storage, offline_runtime, monkeypatch, caplog,
):
    app, client, doctor_id = _doctor_client(isolated_storage)
    with app.app_context():
        case = Case(
            case_code="TEST-CASE-01", doctor_id=doctor_id,
            patient_snapshot={"full_name": "Synthetic Patient"}, status="CREATED",
        )
        db.session.add(case)
        db.session.flush()
        image = CaseImage(
            case_id=case.id, image_path="synthetic.png",
            original_filename="synthetic.png", mime_type="image/png",
            file_size=3, uploaded_by=doctor_id, status="UPLOADED",
        )
        db.session.add(image)
        db.session.flush()
        analysis = Analysis(case_id=case.id, case_image_id=image.id, status="COMPLETED")
        db.session.add(analysis)
        db.session.flush()
        db.session.add(AnalysisResult(
            analysis_id=analysis.id, model_name="synthetic-model",
            predicted_class="NV", binary_result=0,
            binary_probability=0.1, predicted_probability=0.9,
            class_probabilities={"NV": 0.9},
        ))
        db.session.commit()
        analysis_id = analysis.id

    fake_ai_app = ModuleType("skin_cancer.webapp.app")
    fake_ai_app.CLASS_INFO = {}
    monkeypatch.setitem(sys.modules, "skin_cancer.webapp.app", fake_ai_app)
    fake_consult = ModuleType("skin_cancer.webapp.services.chatgpt_service")
    fake_consult.generate_chatgpt_consultation = lambda **kwargs: {
        "headline": "Synthetic consultation", "summary": "Test result",
    }
    monkeypatch.setitem(
        sys.modules, "skin_cancer.webapp.services.chatgpt_service", fake_consult,
    )

    def fail_cache(_key):
        raise OSError("synthetic cache failure")

    monkeypatch.setattr(result_cache, "get_cached", fail_cache)
    response = client.post(f"/api/analyses/{analysis_id}/chatgpt-consult", json={})

    assert response.status_code == 200
    assert response.get_json()["consultation"]["headline"] == "Synthetic consultation"
    assert "Lỗi lưu cache chatgpt consult" in caplog.text
