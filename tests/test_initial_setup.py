"""Regression tests for the first-run, non-demo account provisioning flow."""

import pytest
from flask import current_app

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Case, Slide, SiteSetting, User
from skin_cancer.webapp.services.slide_service import SlideService


INITIAL_INPUT = (
    "Nguyen Quan Tri\nadmin@example.test\nStrongAdmin123!\nStrongAdmin123!\n"
    "Tran Bac Si\ndoctor@example.test\nStrongDoctor123!\nStrongDoctor123!\n"
    "Le Benh Nhan\npatient@example.test\nStrongPatient123!\nStrongPatient123!\n"
)


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "SECRET_KEY": "unit-test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'fresh.db'}",
        "RATELIMIT_ENABLED": False,
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    with application.app_context():
        db.create_all()
    yield application


def test_setup_creates_three_active_accounts_without_demo_cases(app):
    result = app.test_cli_runner().invoke(args=["setup-initial"], input=INITIAL_INPUT)
    assert result.exit_code == 0, result.output
    with app.app_context():
        users = db.session.scalars(db.select(User).order_by(User.role)).all()
        assert len(users) == 3
        assert {user.role for user in users} == {"ADMIN", "DOCTOR", "USER"}
        assert all(user.is_active and user.email_verified for user in users)
        assert db.session.scalar(db.select(db.func.count(Case.id))) == 0
        doctor = db.session.scalar(db.select(User).where(User.role == "DOCTOR"))
        assert doctor.check_password("StrongDoctor123!")
        assert doctor.password_hash != "StrongDoctor123!"
    assert "StrongDoctor123!" not in result.output


def test_setup_keeps_logo_and_two_banners_from_assets(app):
    result = app.test_cli_runner().invoke(args=["setup-initial"], input=INITIAL_INPUT)
    assert result.exit_code == 0, result.output
    with app.app_context():
        setting = db.session.get(SiteSetting, 1)
        assert setting.logo_path == "skin_cancer/webapp/assets/dermascan_logo.png"
        slides = db.session.scalars(db.select(Slide).order_by(Slide.display_order)).all()
        assert len(slides) == 2
        assert [slide.image_path for slide in slides] == [
            "skin_cancer/webapp/assets/demoslide1.png",
            "skin_cancer/webapp/assets/demoslide2.png",
        ]
        assert all(SlideService(current_app).resolve_image_path(slide).is_file() for slide in slides)


def test_rerun_does_not_replace_accounts(app):
    first = app.test_cli_runner().invoke(args=["setup-initial"], input=INITIAL_INPUT)
    assert first.exit_code == 0, first.output
    second = app.test_cli_runner().invoke(args=["setup-initial"], input="")
    assert second.exit_code == 0, second.output
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 3
        assert db.session.scalar(db.select(db.func.count(Slide.id))) == 2


def test_rerun_does_not_fail_when_a_provisioned_doctor_was_disabled(app):
    first = app.test_cli_runner().invoke(args=["setup-initial"], input=INITIAL_INPUT)
    assert first.exit_code == 0, first.output
    with app.app_context():
        doctor = db.session.scalar(db.select(User).where(User.role == "DOCTOR"))
        doctor.is_active = False
        db.session.commit()
    second = app.test_cli_runner().invoke(args=["setup-initial"], input="")
    assert second.exit_code == 0, second.output


def test_rerun_respects_banner_removal_by_admin(app):
    first = app.test_cli_runner().invoke(args=["setup-initial"], input=INITIAL_INPUT)
    assert first.exit_code == 0, first.output
    with app.app_context():
        for slide in db.session.scalars(db.select(Slide)).all():
            db.session.delete(slide)
        db.session.commit()
    second = app.test_cli_runner().invoke(args=["setup-initial"], input="")
    assert second.exit_code == 0, second.output
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Slide.id))) == 0


def test_duplicate_email_aborts_without_partial_accounts(app):
    attempted = INITIAL_INPUT.replace("doctor@example.test", "admin@example.test")
    result = app.test_cli_runner().invoke(args=["setup-initial"], input=attempted)
    assert result.exit_code != 0
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 0
        assert db.session.scalar(db.select(db.func.count(Slide.id))) == 0


def test_reserved_legacy_demo_email_is_rejected_before_provisioning(app):
    attempted = INITIAL_INPUT.replace("admin@example.test", "admin@dermascan.local")
    result = app.test_cli_runner().invoke(args=["setup-initial"], input=attempted)
    assert result.exit_code != 0
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 0


def test_existing_unrelated_accounts_are_never_overwritten(app):
    with app.app_context():
        user = User(full_name="Existing Account", email="existing@example.test", role="USER")
        user.set_password("OldPassword123!")
        db.session.add(user)
        db.session.commit()
    result = app.test_cli_runner().invoke(args=["setup-initial"], input=INITIAL_INPUT)
    assert result.exit_code != 0
    with app.app_context():
        users = db.session.scalars(db.select(User)).all()
        assert len(users) == 1
        assert users[0].check_password("OldPassword123!")


@pytest.mark.parametrize(
    ("email", "password", "role"),
    [
        ("doctor@example.test", "StrongDoctor123!", "DOCTOR"),
        ("patient@example.test", "StrongPatient123!", "USER"),
    ],
)
def test_initial_doctor_and_user_can_log_in_without_demo_seed(app, email, password, role):
    result = app.test_cli_runner().invoke(args=["setup-initial"], input=INITIAL_INPUT)
    assert result.exit_code == 0, result.output
    response = app.test_client().post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["role"] == role
