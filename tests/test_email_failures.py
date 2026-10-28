"""Report mail failures persist audit state while external SMTP is blocked."""

from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Analysis, Case, EmailLog, User
from skin_cancer.webapp.services.email_service import EmailService, SMTP_SEND_FAILED
from skin_cancer.webapp.services.report_service import ReportService

from test_case_api_contract import case_context


def test_smtp_failure_persists_failed_email_log_and_safe_message(case_context):
    app, ids = case_context
    app.config.update({
        "MAIL_SERVER": "smtp.example.test",
        "MAIL_USERNAME": "synthetic@example.test",
        "MAIL_PASSWORD": "synthetic-not-a-secret",
        "MAIL_DEFAULT_SENDER": "synthetic@example.test",
        "MAIL_USE_TLS": False,
        "MAIL_USE_SSL": False,
    })
    with app.app_context():
        case = db.session.get(Case, ids["case"])
        analysis = db.session.get(Analysis, ids["analysis"])
        doctor = db.session.get(User, ids["doctor_a"])
        report = ReportService(app).generate(case, analysis, doctor)

        result = EmailService(app).send_report(
            report, doctor, recipient_email="recipient@example.test",
        )

        assert result.ok is False
        assert result.message == SMTP_SEND_FAILED
        assert db.session.get(EmailLog, result.log.id).status == "FAILED"
        assert db.session.get(EmailLog, result.log.id).sent_at is None


def test_invalid_recipient_is_recorded_without_smtp(case_context):
    app, ids = case_context
    with app.app_context():
        case = db.session.get(Case, ids["case"])
        analysis = db.session.get(Analysis, ids["analysis"])
        doctor = db.session.get(User, ids["doctor_a"])
        report = ReportService(app).generate(case, analysis, doctor)
        result = EmailService(app).send_report(
            report, doctor, recipient_email="not-an-email",
        )
        assert result.ok is False
        assert db.session.get(EmailLog, result.log.id).status == "FAILED"
