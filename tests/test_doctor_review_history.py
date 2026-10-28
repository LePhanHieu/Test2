"""Doctor review history, rejection reason and mail notification."""

from skin_cancer.webapp.extensions import db, mail
from skin_cancer.webapp.models import DoctorApplication, User

from test_doctor_email_otp import app  # shared isolated SQLite fixture


def _application(app, email):
    with app.app_context():
        doctor = User(full_name='Bác sĩ Lê Minh', email=email, role='DOCTOR', is_active=False)
        doctor.set_password('StrongPassword123!')
        db.session.add(doctor)
        db.session.flush()
        application = DoctorApplication(user_id=doctor.id, certificate_path='certificates/example.pdf')
        db.session.add(application)
        db.session.commit()
        return application.id


def _admin(client):
    response = client.post('/api/auth/login', json={
        'email': 'admin@example.test', 'password': 'StrongPassword123!',
    })
    assert response.status_code == 200


def test_rejection_requires_reason_and_appears_in_review_history(app, monkeypatch):
    sent = []
    monkeypatch.setattr(mail, 'send', lambda message: sent.append(message))
    application_id = _application(app, 'rejected@example.test')
    client = app.test_client()
    _admin(client)

    empty = client.patch(f'/api/admin/doctor-applications/{application_id}', json={
        'decision': 'REJECT', 'reason': ' ',
    })
    assert empty.status_code == 400

    result = client.patch(f'/api/admin/doctor-applications/{application_id}', json={
        'decision': 'REJECT', 'reason': 'Chứng chỉ chưa hợp lệ',
    })
    assert result.status_code == 200
    assert result.get_json()['status'] == 'REJECTED'
    assert result.get_json()['email_notification']['sent'] is True
    assert len(sent) == 1
    assert 'Chứng chỉ chưa hợp lệ' in sent[0].body

    history = client.get('/api/admin/doctor-applications/history?status=REJECTED')
    assert history.status_code == 200
    records = history.get_json()['applications']
    assert len(records) == 1
    assert records[0]['rejection_reason'] == 'Chứng chỉ chưa hợp lệ'
    assert records[0]['reviewer_name'] == 'Administrator'
    assert records[0]['reviewed_at']
    assert records[0]['certificate_path'] == 'certificates/example.pdf'
    assert records[0]['email_status'] == 'SENT'
    assert client.patch(f'/api/admin/doctor-applications/{application_id}', json={
        'decision': 'APPROVE',
    }).status_code == 404  # rejected applications cannot resubmit


def test_rejection_status_persists_when_email_fails(app, monkeypatch):
    monkeypatch.setattr(mail, 'send', lambda _message: (_ for _ in ()).throw(ConnectionError('SMTP down')))
    application_id = _application(app, 'mail-failed@example.test')
    client = app.test_client()
    _admin(client)
    response = client.patch(f'/api/admin/doctor-applications/{application_id}', json={
        'decision': 'REJECT', 'reason': 'Thiếu chứng chỉ',
    })
    assert response.status_code == 200
    assert response.get_json()['email_notification']['sent'] is False
    with app.app_context():
        record = db.session.get(DoctorApplication, application_id)
        assert record.status == 'REJECTED'
        assert record.rejection_reason == 'Thiếu chứng chỉ'
        assert record.email_notification_status == 'FAILED'
        assert record.user.is_active is False


def test_approval_included_and_searchable_in_history(app, monkeypatch):
    monkeypatch.setattr(mail, 'send', lambda _message: None)
    application_id = _application(app, 'approved@example.test')
    client = app.test_client()
    _admin(client)
    assert client.patch(f'/api/admin/doctor-applications/{application_id}', json={'decision': 'APPROVE'}).status_code == 200
    history = client.get('/api/admin/doctor-applications/history?status=APPROVED&search=approved@example.test')
    assert history.status_code == 200
    assert [item['id'] for item in history.get_json()['applications']] == [application_id]


def test_review_history_ui_and_calendar_overlay_are_present():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / 'skin_cancer/webapp'
    template = (root / 'templates/admin.html').read_text(encoding='utf-8')
    javascript = (root / 'static/js/admin.js').read_text(encoding='utf-8')
    css = (root / 'static/css/homepage-management.css').read_text(encoding='utf-8')
    assert 'id="doctor-review-history"' in template
    assert 'data-review-tab="history"' in template
    assert 'doctor-applications/history' in javascript
    assert 'position:absolute' in css[css.index('.hm-calendar-popover'):css.index('.hm-calendar-header')]
