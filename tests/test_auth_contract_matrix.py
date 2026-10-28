"""Characterize login and role boundaries without contacting external services."""

import pytest

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import User


@pytest.fixture()
def auth_client(isolated_storage):
    app = create_app(isolated_storage["app_config"])
    with app.app_context():
        db.create_all()
        for role in ("ADMIN", "DOCTOR", "USER"):
            user = User(
                full_name=f"Synthetic {role}",
                email=f"{role.lower()}@example.test",
                role=role,
                is_active=True,
                email_verified=True,
            )
            user.set_password("ValidPassword123!")
            db.session.add(user)
        db.session.commit()
    return app.test_client()


@pytest.mark.parametrize("role", ["ADMIN", "DOCTOR", "USER"])
def test_invalid_password_rejected_for_every_role(auth_client, role):
    response = auth_client.post("/api/auth/login", json={
        "email": f"{role.lower()}@example.test", "password": "incorrect",
    })
    assert response.status_code == 401
    assert response.get_json()["success"] is False


@pytest.mark.parametrize("payload", [None, [], {"email": 1, "password": "abc"}])
def test_login_rejects_invalid_request_shape(auth_client, payload):
    response = auth_client.post("/api/auth/login", json=payload)
    assert response.status_code == 400


def test_user_cannot_read_doctor_statistics(auth_client):
    login = auth_client.post("/api/auth/login", json={
        "email": "user@example.test", "password": "ValidPassword123!",
    })
    assert login.status_code == 200
    response = auth_client.get("/api/doctor/statistics")
    assert response.status_code == 403


def test_anonymous_cannot_read_doctor_statistics(auth_client):
    response = auth_client.get("/api/doctor/statistics")
    assert response.status_code == 401
