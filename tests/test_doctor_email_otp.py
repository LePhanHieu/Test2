"""Doctor approval is one-time; later logins require an email-delivered OTP."""

import re
from datetime import timedelta

import pytest

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db, mail
from skin_cancer.webapp.models import DoctorApplication, SecuritySetting, User
from skin_cancer.webapp.models.base import utcnow


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        'SECRET_KEY': 'test-doctor-otp-secret',
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'otp.db'}",
        'RATELIMIT_ENABLED': False,
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'MAIL_SERVER': 'smtp.example.test',
        'MAIL_USERNAME': 'sender@example.test',
        'MAIL_PASSWORD': 'example-only',
        'MAIL_DEFAULT_SENDER': 'sender@example.test',
    })
    with application.app_context():
        db.create_all()
        admin = User(full_name='Administrator', email='admin@example.test',
                     role='ADMIN', is_active=True, email_verified=True)
        admin.set_password('StrongPassword123!')
        db.session.add(admin)
        db.session.add(SecuritySetting(id=1, require_admin_2fa=False))
        db.session.commit()
    yield application


def _create_and_approve_doctor(app, client, *, email_sent=True):
    reg = client.post('/api/auth/register', json={
        'full_name': 'Doctor Example', 'email': 'doctor.new@example.test',
        'password': 'StrongPassword123!', 'role': 'DOCTOR',
    })
    assert reg.status_code == 201, reg.get_json()
    assert reg.get_json()['verification_required'] is False
    with app.app_context():
        doctor = db.session.scalar(db.select(User).where(User.email == 'doctor.new@example.test'))
        assert doctor.email_verified is False
        application = db.session.scalar(db.select(DoctorApplication).where(DoctorApplication.user_id == doctor.id))
        application.certificate_path = 'certificates/doctor.pdf'
        application_id = application.id
        db.session.commit()

    # Unapproved doctors never receive a login OTP.
    blocked = client.post('/api/auth/login', json={
        'email': 'doctor.new@example.test', 'password': 'StrongPassword123!',
    })
    assert blocked.status_code == 401

    admin_login = client.post('/api/auth/login', json={
        'email': 'admin@example.test', 'password': 'StrongPassword123!',
    })
    assert admin_login.status_code == 200, admin_login.get_json()
    approval = client.patch(f'/api/admin/doctor-applications/{application_id}',
                            json={'decision': 'APPROVE'})
    assert approval.status_code == 200, approval.get_json()
    assert approval.get_json()['status'] == 'APPROVED'
    assert approval.get_json()['email_notification']['sent'] is email_sent
    assert client.patch(f'/api/admin/doctor-applications/{application_id}',
                        json={'decision': 'APPROVE'}).status_code == 404
    client.post('/api/auth/logout')
    return application_id


def _login_doctor(client):
    return client.post('/api/auth/login', json={
        'email': 'doctor.new@example.test', 'password': 'StrongPassword123!',
    })


def _code(email_message):
    return re.search(r'\b\d{6}\b', email_message.body).group(0)


def test_one_approval_then_email_otp_for_every_doctor_login(app, monkeypatch):
    sent = []
    monkeypatch.setattr(mail, 'send', lambda message: sent.append(message))
    client = app.test_client()
    application_id = _create_and_approve_doctor(app, client)

    assert len(sent) == 1
    assert sent[0].recipients == ['doctor.new@example.test']
    assert 'phê duyệt' in sent[0].subject.lower()
    assert 'Doctor Example' in sent[0].body
    assert 'Hồ sơ của bạn đã được phê duyệt' in sent[0].html
    assert 'Doctor Example' in sent[0].html
    assert '{{DOCTOR_NAME}}' not in sent[0].html

    challenge = _login_doctor(client)
    assert challenge.status_code == 200, challenge.get_json()
    assert challenge.get_json()['requires_2fa'] is True
    assert 'd***@example.test' in challenge.get_json()['message']
    assert len(sent) == 2
    assert sent[1].recipients == ['doctor.new@example.test']
    assert 'Mã Xác Thực Đăng Nhập' in sent[1].html
    assert _code(sent[1]) in sent[1].html
    assert '{{OTP_CODE}}' not in sent[1].html
    assert client.post('/api/auth/verify-2fa', json={'code': 'invalid'}).status_code == 401
    verified = client.post('/api/auth/verify-2fa', json={'code': _code(sent[-1])})
    assert verified.status_code == 200, verified.get_json()
    assert verified.get_json()['user']['role'] == 'DOCTOR'
    with app.app_context():
        doctor = db.session.scalar(db.select(User).where(User.email == 'doctor.new@example.test'))
        assert doctor.email_verified is True
        assert doctor.two_factor_code_hash is None
        assert db.session.get(DoctorApplication, application_id).status == 'APPROVED'

    client.post('/api/auth/logout')
    again = _login_doctor(client)
    assert again.status_code == 200
    assert again.get_json()['requires_2fa'] is True
    assert len(sent) == 3  # Approval email once, then one OTP per login.


def test_resend_invalidates_previous_code_and_expiration_is_checked(app, monkeypatch):
    sent = []
    monkeypatch.setattr(mail, 'send', lambda message: sent.append(message))
    client = app.test_client()
    _create_and_approve_doctor(app, client)
    assert _login_doctor(client).status_code == 200
    old = _code(sent[-1])
    resend = client.post('/api/auth/resend-2fa', json={})
    assert resend.status_code == 200, resend.get_json()
    assert len(sent) == 3
    with app.app_context():
        doctor = db.session.scalar(db.select(User).where(User.email == 'doctor.new@example.test'))
        doctor.two_factor_code_expires_at = utcnow() - timedelta(minutes=1)
        db.session.commit()
    assert client.post('/api/auth/verify-2fa', json={'code': _code(sent[-1])}).status_code == 401
    assert len(old) == 6


def test_smtp_failure_is_not_a_successful_login(app, monkeypatch):
    def failed_send(_message):
        raise ConnectionError('SMTP unavailable')

    monkeypatch.setattr(mail, 'send', failed_send)
    client = app.test_client()
    _create_and_approve_doctor(app, client, email_sent=False)
    response = _login_doctor(client)
    assert response.status_code == 503
    assert response.get_json()['success'] is False
    with app.app_context():
        doctor = db.session.scalar(db.select(User).where(User.email == 'doctor.new@example.test'))
        assert doctor.two_factor_code_hash is None


def test_approval_persists_and_warns_admin_when_smtp_fails(app, monkeypatch):
    sent = []
    def fail_send(message):
        sent.append(message)
        raise ConnectionError('SMTP unavailable')
    monkeypatch.setattr(mail, 'send', fail_send)
    client = app.test_client()
    response = client.post('/api/auth/register', json={
        'full_name': 'Doctor Example', 'email': 'doctor.failed@example.test',
        'password': 'StrongPassword123!', 'role': 'DOCTOR',
    })
    assert response.status_code == 201
    with app.app_context():
        doctor = db.session.scalar(db.select(User).where(User.email == 'doctor.failed@example.test'))
        application = db.session.scalar(db.select(DoctorApplication).where(DoctorApplication.user_id == doctor.id))
        application.certificate_path = 'certificates/doctor.pdf'
        application_id = application.id
        db.session.commit()
    assert client.post('/api/auth/login', json={
        'email': 'admin@example.test', 'password': 'StrongPassword123!',
    }).status_code == 200
    approval = client.patch(f'/api/admin/doctor-applications/{application_id}', json={'decision': 'APPROVE'})
    assert approval.status_code == 200
    assert approval.get_json()['status'] == 'APPROVED'
    assert approval.get_json()['email_notification']['sent'] is False
    assert 'email' in approval.get_json()['email_notification']['message'].lower()
    assert len(sent) == 1
    with app.app_context():
        assert db.session.get(DoctorApplication, application_id).status == 'APPROVED'
        assert db.session.scalar(db.select(User).where(User.email == 'doctor.failed@example.test')).is_active is True


def test_sample_doctor_and_regular_user_do_not_require_email_otp(app, monkeypatch):
    sent = []
    monkeypatch.setattr(mail, 'send', lambda message: sent.append(message))
    with app.app_context():
        for email, role in [('doctor@dermascan.local', 'DOCTOR'), ('user@example.test', 'USER')]:
            person = User(full_name='Local Test User', email=email, role=role,
                          is_active=True, email_verified=True,
                          two_factor_enabled=email == 'doctor@dermascan.local')
            person.set_password('StrongPassword123!')
            db.session.add(person)
        db.session.commit()
    client = app.test_client()
    for email in ('doctor@dermascan.local', 'user@example.test'):
        result = client.post('/api/auth/login', json={
            'email': email, 'password': 'StrongPassword123!',
        })
        assert result.status_code == 200, result.get_json()
        assert result.get_json().get('requires_2fa') is not True
        client.post('/api/auth/logout')
    assert sent == []
