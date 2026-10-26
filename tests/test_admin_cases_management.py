"""Admin case management must be read-only and scoped to administrators."""

from pathlib import Path

import pytest

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Case, SecuritySetting, User


ROOT = Path(__file__).resolve().parents[1] / "skin_cancer" / "webapp"


def test_admin_cases_endpoints_are_read_only_and_protected():
    routes = (ROOT / "routes" / "admin.py").read_text(encoding="utf-8")
    assert '@bp.get("/api/admin/cases")' in routes
    assert '@bp.get("/api/admin/cases/<int:case_id>")' in routes
    assert '@bp.get("/api/admin/cases/<int:case_id>/images/<int:image_id>/<kind>")' in routes
    assert "@require_roles(\"ADMIN\")" in routes


def test_admin_cases_ui_has_list_filters_pagination_and_details():
    html = (ROOT / "templates" / "admin.html").read_text(encoding="utf-8")
    js = (ROOT / "static" / "js" / "admin_cases.js").read_text(encoding="utf-8")
    for element in ("case-search", "case-status", "case-doctor", "case-from", "case-to", "admin-cases-table", "admin-case-detail", "case-next", "case-prev"):
        assert f'id="{element}"' in html
    assert '/api/admin/cases?' in js
    assert "async function loadAdminCases()" in js


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "SECRET_KEY": "admin-cases-test", "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'cases.db'}",
        "RATELIMIT_ENABLED": False, "WTF_CSRF_ENABLED": False,
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "MEASUREMENT_FOLDER": str(tmp_path / "measurements"),
    })
    with application.app_context():
        db.create_all()
        admin = User(full_name="Admin", email="admin-cases@example.test", role="ADMIN", is_active=True, email_verified=True)
        admin.set_password("StrongPassword123!")
        doctor = User(full_name="Bác sĩ An", email="doctor-cases@example.test", role="DOCTOR", is_active=True, email_verified=True)
        doctor.set_password("StrongPassword123!")
        db.session.add_all([admin, doctor])
        db.session.flush()
        db.session.add(Case(case_code="CASE-001", doctor_id=doctor.id,
                            patient_snapshot={"full_name": "Bệnh nhân Minh"}, status="COMPLETED"))
        db.session.add(SecuritySetting(id=1, require_admin_2fa=False))
        db.session.commit()
    return application


def test_admin_cases_list_search_detail_and_access_control(app):
    client = app.test_client()
    assert client.get("/api/admin/cases").status_code == 401
    response = client.post("/api/auth/login", json={"email": "admin-cases@example.test", "password": "StrongPassword123!"})
    assert response.status_code == 200, response.get_json()
    found = client.get("/api/admin/cases?search=Minh")
    assert found.status_code == 200, found.get_json()
    body = found.get_json()
    assert body["total"] == 1
    assert body["metrics"]["completed"] == 1
    case_id = body["cases"][0]["id"]
    assert client.get(f"/api/admin/cases/{case_id}").get_json()["patient"] == "Bệnh nhân Minh"
    assert client.get("/api/admin/cases?status=INVALID").status_code == 400
    assert client.get("/api/admin/cases?start=2026-12-30&end=2026-01-01").status_code == 400
    assert client.post("/api/admin/cases", json={}).status_code == 405
    assert client.patch(f"/api/admin/cases/{case_id}", json={}).status_code == 405
    assert client.delete(f"/api/admin/cases/{case_id}").status_code == 405
    assert client.get(f"/api/admin/cases/{case_id}/images/999/original").status_code == 404
    assert client.get("/api/admin/cases?search=NotFound").get_json()["total"] == 0
    assert client.get("/api/admin/cases?status=CREATED").get_json()["total"] == 0
    assert client.get("/api/admin/cases?doctor=invalid").status_code == 400
    client.post("/api/auth/logout")
    # A doctor can view their own cases through doctor APIs, but never the admin listing.
    with client.session_transaction() as session:
        session["_user_id"] = "2"
        session["_fresh"] = True
    assert client.get("/api/admin/cases").status_code == 403
    assert client.get(f"/api/admin/cases/{case_id}").status_code == 403
    assert client.get(f"/api/admin/cases/{case_id}/images/999/original").status_code == 403
