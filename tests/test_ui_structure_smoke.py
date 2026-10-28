"""Read-only template smoke contracts pending browser-based Playwright tests."""

from html.parser import HTMLParser
from pathlib import Path

import pytest


WEB = Path(__file__).resolve().parents[1] / "skin_cancer" / "webapp"


class ControlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.controls = []

    def handle_starttag(self, tag, attrs):
        if tag in {"input", "button", "select", "textarea", "dialog"}:
            self.controls.append((tag, dict(attrs)))


@pytest.mark.parametrize("template,required_ids", [
    ("index.html", {"doctorNav", "patientNav", "imageInput", "analyzeBtn", "hpAuthModal", "hpRegAgree"}),
    ("admin.html", {"sidebar", "profile-2fa", "doctor-rejection-dialog", "admin-case-modal"}),
])
def test_role_templates_keep_essential_dom_hooks(template, required_ids):
    source = (WEB / "templates" / template).read_text(encoding="utf-8")
    for element_id in required_ids:
        assert f'id="{element_id}"' in source


@pytest.mark.parametrize("template", ["index.html", "admin.html"])
def test_role_templates_retain_control_and_css_structure(template):
    source = (WEB / "templates" / template).read_text(encoding="utf-8")
    parser = ControlParser()
    parser.feed(source)
    tags = {tag for tag, _ in parser.controls}
    assert {"input", "button", "select"}.issubset(tags)
    assert "rel=\"stylesheet\"" in source
    assert "static', filename='js/" in source


def test_checkboxes_retain_explicit_identifiers_and_labels():
    index = (WEB / "templates" / "index.html").read_text(encoding="utf-8")
    admin = (WEB / "templates" / "admin.html").read_text(encoding="utf-8")
    assert 'type="checkbox" id="hpRegAgree"' in index
    assert 'for="profile-2fa"' in admin
    assert 'id="profile-2fa"' in admin


def test_existing_responsive_breakpoints_are_present():
    for name in ("style.css", "patient.css", "admin.css", "doctor-analysis-layout.css"):
        source = (WEB / "static" / "css" / name).read_text(encoding="utf-8")
        assert "@media" in source
