"""Characterize report email text and attachment before safe extraction."""

from skin_cancer.webapp.extensions import db, mail
from skin_cancer.webapp.models import Analysis, Case, User
from skin_cancer.webapp.services.email_service import EmailService
from skin_cancer.webapp.services.report_service import ReportService

from test_case_api_contract import case_context


def test_report_email_body_and_attachment_remain_unchanged(case_context, monkeypatch):
    app, ids = case_context
    app.config.update({
        "MAIL_SERVER": "smtp.example.test",
        "MAIL_USERNAME": "synthetic@example.test",
        "MAIL_PASSWORD": "synthetic-test-password",
        "MAIL_DEFAULT_SENDER": "synthetic@example.test",
        "MAIL_USE_TLS": False,
        "MAIL_USE_SSL": False,
    })
    messages = []
    monkeypatch.setattr(mail, "send", messages.append)
    with app.app_context():
        case = db.session.get(Case, ids["case"])
        analysis = db.session.get(Analysis, ids["analysis"])
        doctor = db.session.get(User, ids["doctor_a"])
        report = ReportService(app).generate(case, analysis, doctor)
        result = EmailService(app).send_report(report, doctor, recipient_email="recipient@example.test")

    assert result.ok is True
    assert len(messages) == 1
    message = messages[0]
    assert message.recipients == ["recipient@example.test"]
    assert message.body == (
        "Xin chào patient,\n\n"
        "Đính kèm email này là báo cáo phân tích tổn thương da của ca "
        "CASE-ISOLATED-01.\n\n"
        "Kết quả do hệ thống DermaScan AI cung cấp chỉ có giá trị hỗ trợ "
        "tham khảo và không thay thế chẩn đoán chuyên môn của bác sĩ.\n\n"
        "Trân trọng,\nDermaScan AI"
    )
    assert len(message.attachments) == 1
    assert message.attachments[0].content_type == "application/pdf"


def test_report_email_body_handles_missing_patient_name():
    body = EmailService._report_email_body("", "CASE-SYNTHETIC")
    assert body.startswith("Xin chào,\n\n")
    assert "của ca CASE-SYNTHETIC." in body
