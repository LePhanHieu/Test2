"""Protect JS script loading and dynamic DOM hooks before extraction."""

from pathlib import Path


WEB = Path(__file__).resolve().parents[1] / "skin_cancer" / "webapp"


def test_admin_scripts_load_in_existing_dependency_order():
    template = (WEB / "templates/admin.html").read_text(encoding="utf-8")
    ordered = ("js/admin.js", "js/admin_cases.js", "js/homepage_management.js")
    positions = [template.index(item) for item in ordered]
    assert positions == sorted(positions)
    for name in ordered:
        assert (WEB / "static" / name).is_file()


def test_doctor_patient_scripts_load_in_existing_dependency_order():
    template = (WEB / "templates/index.html").read_text(encoding="utf-8")
    ordered = ("js/focus_region.js", "js/timeline.js", "js/main.js", "js/patient.js")
    positions = [template.index(item) for item in ordered]
    assert positions == sorted(positions)
    for name in ordered:
        assert (WEB / "static" / name).is_file()


def test_dynamic_dom_hooks_remain_connected_to_consumers():
    cases_js = (WEB / "static/js/admin_cases.js").read_text(encoding="utf-8")
    admin_template = (WEB / "templates/admin.html").read_text(encoding="utf-8")
    for hook in ("case-search", "case-status", "case-doctor", "case-from", "case-to"):
        assert f'id="{hook}"' in admin_template
        assert f'#{hook}' in cases_js

    home_js = (WEB / "static/js/homepage_management.js").read_text(encoding="utf-8")
    assert "[data-hm-tab]" in home_js
    assert "data-hm-tab=" in admin_template
