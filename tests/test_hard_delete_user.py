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


def test_approved_doctor_without_protected_records_can_be_deleted(app):
    doctor_id = _user(app, 'reviewed@example.test', 'DOCTOR')
    with app.app_context():
        db.session.add(DoctorApplication(user_id=doctor_id, status='APPROVED', reviewed_at=utcnow()))
        db.session.commit()
    client = app.test_client()
    _login_admin(client)
    result = client.delete(f'/api/admin/users/{doctor_id}')
    assert result.status_code == 200, result.get_json()
    with app.app_context():
        assert db.session.get(User, doctor_id) is None
        assert db.session.scalar(db.select(DoctorApplication).where(DoctorApplication.user_id == doctor_id)) is None


def test_rejected_doctor_without_protected_records_can_be_deleted(app):
    doctor_id = _user(app, 'rejected@example.test', 'DOCTOR')
    with app.app_context():
        db.session.add(DoctorApplication(user_id=doctor_id, status='REJECTED',
                                         reviewed_at=utcnow(), rejection_reason='Demo'))
        db.session.commit()
    client = app.test_client()
    _login_admin(client)
    result = client.delete(f'/api/admin/users/{doctor_id}')
    assert result.status_code == 200, result.get_json()
    with app.app_context():
        assert db.session.get(User, doctor_id) is None


def test_approved_doctor_with_case_is_still_protected(app):
    doctor_id = _user(app, 'reviewed-case@example.test', 'DOCTOR')
    with app.app_context():
        db.session.add(DoctorApplication(user_id=doctor_id, status='APPROVED', reviewed_at=utcnow()))
        db.session.add(Case(case_code='CASE-APPROVED-01', doctor_id=doctor_id,
                            patient_snapshot={'full_name': 'Patient'}))
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


def test_pending_doctor_registration_then_admin_delete_and_register_again(app, monkeypatch):
    client = app.test_client()
    created = client.post('/api/auth/register', json={
        'full_name': 'Pending Doctor', 'email': 'new.pending@example.test',
        'password': 'StrongPassword123!', 'role': 'DOCTOR',
    })
    assert created.status_code == 201
    user_id = created.get_json()['user']['id']
    with app.app_context():
        application = db.session.scalar(db.select(DoctorApplication).where(DoctorApplication.user_id == user_id))
        assert application.status == 'PENDING'
    _login_admin(client)
    deleted = client.delete(f'/api/admin/users/{user_id}')
    assert deleted.status_code == 200, deleted.get_json()
    with app.app_context():
        assert db.session.get(User, user_id) is None
        assert db.session.scalar(db.select(DoctorApplication).where(DoctorApplication.user_id == user_id)) is None
    client.post('/api/auth/logout')
    again = client.post('/api/auth/register', json={
        'full_name': 'Pending Doctor Again', 'email': 'new.pending@example.test',
        'password': 'StrongPassword123!', 'role': 'DOCTOR',
    })
    assert again.status_code == 201, again.get_json()


def test_pending_certificate_is_deleted_only_after_successful_admin_delete(app, tmp_path):
    from pathlib import Path
    from skin_cancer.webapp.services.user_deletion import cleanup_doctor_certificate
    account_id = _user(app, 'cert-pending@example.test', 'DOCTOR')
    filename = 'pending-test.pdf'
    with app.app_context():
        root = Path(app.config['UPLOAD_FOLDER']) / 'doctor-certificates'
        root.mkdir(parents=True, exist_ok=True)
        (root / filename).write_bytes(b'%PDF-1.4 test')
        db.session.add(DoctorApplication(user_id=account_id, status='PENDING', certificate_path=filename))
        db.session.commit()
    client = app.test_client()
    _login_admin(client)
    response = client.delete(f'/api/admin/users/{account_id}')
    assert response.status_code == 200, response.get_json()
    assert not (root / filename).exists()


def test_protected_case_prevents_certificate_deletion(app):
    from pathlib import Path
    account_id = _user(app, 'case-cert@example.test', 'DOCTOR')
    filename = 'protected-test.pdf'
    with app.app_context():
        root = Path(app.config['UPLOAD_FOLDER']) / 'doctor-certificates'
        root.mkdir(parents=True, exist_ok=True)
        (root / filename).write_bytes(b'%PDF-1.4 test')
        db.session.add(DoctorApplication(user_id=account_id, status='PENDING', certificate_path=filename))
        db.session.add(Case(case_code='CASE-HOLD-CERT', doctor_id=account_id,
                            patient_snapshot={'full_name': 'Patient'}))
        db.session.commit()
    client = app.test_client()
    _login_admin(client)
    response = client.delete(f'/api/admin/users/{account_id}')
    assert response.status_code == 409
    assert 'cases' in response.get_json()['message']
    assert (root / filename).exists()


def test_soft_deleted_approved_account_can_register_again(app):
    doctor_id = _user(app, 'soft-approved@example.test', 'DOCTOR')
    with app.app_context():
        doctor = db.session.get(User, doctor_id)
        doctor.deleted_at = utcnow()
        db.session.add(DoctorApplication(user_id=doctor_id, status='APPROVED', reviewed_at=utcnow()))
        db.session.commit()
    client = app.test_client()
    response = client.post('/api/auth/register', json={
        'full_name': 'Re-registered doctor', 'email': 'soft-approved@example.test',
        'password': 'StrongPassword123!', 'role': 'DOCTOR',
    })
    assert response.status_code == 201, response.get_json()
    with app.app_context():
        doctor = db.session.scalar(db.select(User).where(User.email == 'soft-approved@example.test'))
        assert doctor.full_name == 'Re-registered doctor'
        assert db.session.scalar(db.select(DoctorApplication.status).where(
            DoctorApplication.user_id == doctor.id)) == 'PENDING'
