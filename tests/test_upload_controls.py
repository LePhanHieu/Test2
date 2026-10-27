"""Admin uploads use styled, accessible file controls instead of native Choose File."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "skin_cancer/webapp/static"


def test_doctor_certificate_has_styled_label_and_selected_filename():
    script = (ROOT / "js/admin.js").read_text(encoding="utf-8")
    css = (ROOT / "css/admin-doctor-theme.css").read_text(encoding="utf-8")
    assert 'class="certificate-upload-button"' in script
    assert 'class="certificate-file-name"' in script
    assert 'input.closest(".certificate-upload")' in script
    assert '.certificate-upload input[type="file"]' in css


def test_homepage_media_picker_is_styled_and_displays_selection():
    script = (ROOT / "js/homepage_management.js").read_text(encoding="utf-8")
    css = (ROOT / "css/homepage-management.css").read_text(encoding="utf-8")
    assert 'class="hm-upload-button"' in script
    assert 'class="hm-file-name"' in script
    assert 'state.files.get(path)?.file.name' in script
    assert '.hm-file-picker input[type="file"]' in css
