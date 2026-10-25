"""The public login form must not advertise a built-in demo account."""

from pathlib import Path

from flask import Flask, render_template


def test_login_form_does_not_prepopulate_demo_identity():
    templates = Path(__file__).resolve().parents[1] / "skin_cancer/webapp/templates"
    app = Flask(__name__, template_folder=str(templates))

    @app.get("/")
    def index():
        return render_template("index.html")

    response = app.test_client().get("/")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'value="doctor@dermascan.local"' not in page
    assert "Tài khoản bác sĩ mẫu:" not in page
