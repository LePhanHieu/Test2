"""Permanently delete only accounts with no protected related records."""

from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Case, DoctorApplication, User
from skin_cancer.webapp.models.base import utcnow

from test_doctor_email_otp import app


def _login_admin(client):
    result = client.post('/api/auth/login', json={
        'email': 'admin@example.test', 'password': 'StrongPassword123!',
    })
    assert result.status_code == 200


def _user(app, email, role='USER'):
    with app.app_context():
        user = User(full_name='Test Account', email=email, role=role, is_active=True)
        user.set_password('StrongPassword123!')
        db.session.add(user)
        db.session.commit()
        return user.id


def test_deleting_unrelated_account_removes_row_and_frees_email(app):
    account_id = _user(app, 'delete@example.test')
    client = app.test_client()
    _login_admin(client)
    result = client.delete(f'/api/admin/users/{account_id}')
    assert result.status_code == 200, result.get_json()
    with app.app_context():
        assert db.session.get(User, account_id) is None
    client.post('/api/auth/logout')
    registration = client.post('/api/auth/register', json={
        'full_name': 'New account', 'email': 'delete@example.test',
        'password': 'StrongPassword123!', 'role': 'USER',
    })
    assert registration.status_code == 201, registration.get_json()


def test_delete_blocked_for_doctor_with_cases(app):
    doctor_id = _user(app, 'cases@example.test', 'DOCTOR')
    with app.app_context():
        db.session.add(Case(case_code='CASE-PROTECTED-01', doctor_id=doctor_id,
                            patient_snapshot={'full_name': 'Patient'}))
        db.session.commit()
    client = app.test_client()
    _login_admin(client)
    result = client.delete(f'/api/admin/users/{doctor_id}')
    assert result.status_code == 409
    assert 'ca khám' in result.get_json()['message'].lower() or 'liên quan' in result.get_json()['message'].lower()
    with app.app_context():
        assert db.session.get(User, doctor_id) is not None
        assert db.session.scalar(db.select(Case).where(Case.doctor_id == doctor_id)) is not None


def test_reviewed_doctor_application_is_preserved(app):
    doctor_id = _user(app, 'reviewed@example.test', 'DOCTOR')
    with app.app_context():
        db.session.add(DoctorApplication(user_id=doctor_id, status='APPROVED', reviewed_at=utcnow()))
        db.session.commit()
    client = app.test_client()
    _login_admin(client)
    result = client.delete(f'/api/admin/users/{doctor_id}')
    assert result.status_code == 409
    with app.app_context():
        assert db.session.get(User, doctor_id) is not None


def test_unreviewed_doctor_application_can_be_removed_with_account(app):
    doctor_id = _user(app, 'pending@example.test', 'DOCTOR')
    with app.app_context():
        db.session.add(DoctorApplication(user_id=doctor_id, status='PENDING'))
        db.session.commit()
    client = app.test_client()
    _login_admin(client)
    result = client.delete(f'/api/admin/users/{doctor_id}')
    assert result.status_code == 200, result.get_json()
    with app.app_context():
        assert db.session.get(User, doctor_id) is None
        assert db.session.scalar(db.select(DoctorApplication).where(DoctorApplication.user_id == doctor_id)) is None


def test_self_delete_stays_blocked(app):
    client = app.test_client()
    _login_admin(client)
    with app.app_context():
        admin_id = db.session.scalar(db.select(User.id).where(User.email == 'admin@example.test'))
    result = client.delete(f'/api/admin/users/{admin_id}')
    assert result.status_code == 400


def test_previous_soft_deleted_account_can_reuse_email_if_safe(app):
    account_id = _user(app, 'old-deleted@example.test')
    with app.app_context():
        db.session.get(User, account_id).deleted_at = utcnow()
        db.session.commit()
    client = app.test_client()
    result = client.post('/api/auth/register', json={
        'full_name': 'Replacement', 'email': 'old-deleted@example.test',
        'password': 'StrongPassword123!', 'role': 'USER',
    })
    assert result.status_code == 201, result.get_json()
    with app.app_context():
        replacement = db.session.scalar(db.select(User).where(User.email == 'old-deleted@example.test'))
        assert replacement.full_name == 'Replacement'
        assert replacement.deleted_at is None


def test_previous_soft_deleted_with_cases_does_not_get_reclaimed(app):
    doctor_id = _user(app, 'old-linked@example.test', 'DOCTOR')
    with app.app_context():
        doctor = db.session.get(User, doctor_id)
        doctor.deleted_at = utcnow()
        db.session.add(Case(case_code='CASE-PROTECTED-02', doctor_id=doctor_id,
                            patient_snapshot={'full_name': 'Patient'}))
        db.session.commit()
    client = app.test_client()
    result = client.post('/api/auth/register', json={
        'full_name': 'Replacement', 'email': 'old-linked@example.test',
        'password': 'StrongPassword123!', 'role': 'USER',
    })
    assert result.status_code == 409
    with app.app_context():
        assert db.session.get(User, doctor_id) is not None
