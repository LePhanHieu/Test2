"""UI token and control contracts; browser screenshots remain a separate gate."""

from pathlib import Path

import pytest


WEB = Path(__file__).resolve().parents[1] / "skin_cancer" / "webapp"


def test_shared_ui_tokens_preserve_approved_palette():
    tokens = (WEB / "static/css/tokens.css").read_text(encoding="utf-8")
    assert "--ds-primary: #2ba149" in tokens
    assert "--ds-accent: #fd8624" in tokens
    for spacing in (4, 8, 12, 16, 24, 32):
        assert f"--ds-space-{spacing}: {spacing}px" in tokens


@pytest.mark.parametrize("template", ["index.html", "admin.html"])
def test_shared_control_styles_load_after_legacy_role_styles(template):
    markup = (WEB / "templates" / template).read_text(encoding="utf-8")
    token_link = "filename='css/tokens.css'"
    component_link = "filename='css/components.css'"
    assert token_link in markup and component_link in markup
    assert markup.index(token_link) < markup.index(component_link)
    if template == "index.html":
        assert markup.index("filename='css/patient.css'") < markup.index(component_link)
    else:
        assert markup.index("filename='css/admin-doctor-theme.css'") < markup.index(component_link)


def test_control_styles_scope_focus_and_disabled_states():
    css = (WEB / "static/css/components.css").read_text(encoding="utf-8")
    assert ":focus-visible" in css
    assert ":disabled" in css
    assert "--ds-focus-ring" in css
    assert ".hp-check" in css
    assert ".switch" in css
