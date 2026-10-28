"""Smoke-test isolated PDF generation without comparing volatile PDF bytes."""

from pathlib import Path

from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import Analysis, Case, Report, User
from skin_cancer.webapp.services.report_service import ReportService

from test_case_api_contract import case_context


def test_report_generation_produces_valid_pdf_and_persists_version(case_context):
    app, ids = case_context
    with app.app_context():
        case = db.session.get(Case, ids["case"])
        analysis = db.session.get(Analysis, ids["analysis"])
        doctor = db.session.get(User, ids["doctor_a"])
        report = ReportService(app).generate(case, analysis, doctor)
        assert report.report_version == 1
        assert db.session.get(Report, report.id) is not None
        output = Path(app.config["REPORT_FOLDER"]) / report.pdf_path
        assert output.is_file()
        assert output.read_bytes().startswith(b"%PDF-")
