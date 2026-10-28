"""Static keyboard/ARIA contracts pending isolated browser automation."""

from pathlib import Path


WEB = Path(__file__).resolve().parents[1] / "skin_cancer" / "webapp"


def test_homepage_management_tabs_have_accessible_selected_state():
    template = (WEB / "templates/admin.html").read_text(encoding="utf-8")
    script = (WEB / "static/js/homepage_management.js").read_text(encoding="utf-8")
    for name in ("branding", "banners", "content", "contact", "footer"):
        assert f'data-hm-tab="{name}" role="tab"' in template
    assert 'aria-selected="true"' in template
    assert "setAttribute('aria-selected'" in script


def test_auth_tabs_synchronize_aria_selection_and_modal_focus():
    template = (WEB / "templates/index.html").read_text(encoding="utf-8")
    assert 'data-view="login" role="tab" aria-selected="true"' in template
    assert 'data-view="register" role="tab" aria-selected="false"' in template
    assert 'tab.setAttribute("aria-selected"' in template
    assert "hpAuthPreviousFocus" in template
    assert "event.key === \"Tab\"" in template


def test_modal_keyboard_contract_keeps_escape_and_existing_hooks():
    template = (WEB / "templates/index.html").read_text(encoding="utf-8")
    for hook in ("hpAuthModal", "hpAuthCloseBtn", "hpAuthBackdrop"):
        assert f'"{hook}"' in template
    assert 'event.key === "Escape"' in template
