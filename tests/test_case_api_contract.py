"""Case ownership, patient-source and review contracts using synthetic data."""

import pytest

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Analysis, Case, CaseImage, DoctorReview, User


@pytest.fixture()
def case_context(isolated_storage, offline_runtime):
    app = create_app(isolated_storage["app_config"])
    with app.app_context():
        db.create_all()
        ids = {}
        for name, role in (("doctor_a", "DOCTOR"), ("doctor_b", "DOCTOR"), ("patient", "USER")):
            user = User(
                full_name=name, email=f"{name}@example.test", role=role,
                is_active=True, email_verified=True,
            )
            user.set_password("SyntheticPassword123!")
            db.session.add(user)
            db.session.flush()
            ids[name] = user.id
        case = Case(
            case_code="CASE-ISOLATED-01", doctor_id=ids["doctor_a"],
            patient_user_id=ids["patient"], status="CREATED",
        )
        db.session.add(case)
        db.session.flush()
        image = CaseImage(
            case_id=case.id, image_path="synthetic.png", original_filename="synthetic.png",
            mime_type="image/png", file_size=3, uploaded_by=ids["doctor_a"], status="UPLOADED",
        )
        db.session.add(image)
        db.session.flush()
        analysis = Analysis(case_id=case.id, case_image_id=image.id, status="PENDING")
        db.session.add(analysis)
        db.session.commit()
        ids["case"] = case.id
        ids["analysis"] = analysis.id
    return app, ids


def _client(app, user_id):
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
    return client


@pytest.mark.parametrize("payload", [
    {},
    {"patient_user_id": 999999},
    {"patient_user_id": 1, "temporary_patient": {"full_name": "Example"}},
    {"patient_user_id": "invalid"},
])
def test_create_case_rejects_invalid_patient_source(case_context, payload):
    app, ids = case_context
    client = _client(app, ids["doctor_a"])
    response = client.post("/api/cases", json=payload)
    assert response.status_code in (400, 404)
    with app.app_context():
        assert db.session.query(Case).count() == 1


def test_doctor_cannot_read_other_doctor_analysis_or_review(case_context):
    app, ids = case_context
    outsider = _client(app, ids["doctor_b"])
    assert outsider.get(f"/api/analyses/{ids['analysis']}").status_code == 404
    assert outsider.get(f"/api/analyses/{ids['analysis']}/review").status_code == 404
    assert outsider.post(
        f"/api/analyses/{ids['analysis']}/review",
        json={"doctor_conclusion": "Must not persist"},
    ).status_code == 404
    with app.app_context():
        assert db.session.query(DoctorReview).count() == 0


def test_review_draft_allows_missing_conclusion_but_final_requires_it(case_context):
    app, ids = case_context
    doctor = _client(app, ids["doctor_a"])
    path = f"/api/analyses/{ids['analysis']}/review"
    draft = doctor.post(path + "/draft", json={"clinical_note": "Synthetic note"})
    assert draft.status_code == 200
    assert draft.get_json()["review"]["review_status"] == "DRAFT"
    assert doctor.post(path, json={"clinical_note": "Synthetic note"}).status_code == 400
    with app.app_context():
        review = db.session.query(DoctorReview).one()
        assert review.review_status == "DRAFT"
        assert db.session.get(Case, ids["case"]).status == "CREATED"


def test_create_case_with_registered_patient_preserves_doctor_assignment(case_context):
    app, ids = case_context
    doctor = _client(app, ids["doctor_a"])
    response = doctor.post("/api/cases", json={"patient_user_id": ids["patient"]})
    assert response.status_code == 201
    with app.app_context():
        created = db.session.get(Case, response.get_json()["id"])
        assert created.doctor_id == ids["doctor_a"]
        assert created.patient_user_id == ids["patient"]
        assert created.status == "CREATED"


def test_final_review_requires_conclusion_and_marks_case_reviewed(case_context):
    app, ids = case_context
    doctor = _client(app, ids["doctor_a"])
    response = doctor.post(
        f"/api/analyses/{ids['analysis']}/review",
        json={"clinical_note": "Synthetic note", "doctor_conclusion": "Synthetic conclusion"},
    )
    assert response.status_code == 200
    assert response.get_json()["review"]["review_status"] == "REVIEWED"
    with app.app_context():
        assert db.session.query(DoctorReview).one().review_status == "REVIEWED"
        assert db.session.get(Case, ids["case"]).status == "REVIEWED"


def test_doctor_history_only_lists_completed_analyses(case_context):
    app, ids = case_context
    doctor = _client(app, ids["doctor_a"])
    response = doctor.get("/api/doctor/history")
    assert response.status_code == 200
    assert response.get_json() == {"records": []}
    outsider = _client(app, ids["doctor_b"])
    assert outsider.get(f"/api/cases/{ids['case']}").status_code == 404
