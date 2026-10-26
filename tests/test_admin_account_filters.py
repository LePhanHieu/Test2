"""Regression checks for the account-management filtering controls."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "skin_cancer" / "webapp"


def test_account_filters_have_reset_and_live_count():
    markup = (ROOT / "templates" / "admin.html").read_text(encoding="utf-8")
    assert 'id="user-reset-filters"' in markup
    assert 'id="users-count"' in markup
    assert 'aria-live="polite"' in markup


def test_account_controller_resets_initial_filters_and_empty_results():
    script = (ROOT / "static" / "js" / "admin.js").read_text(encoding="utf-8")
    assert 'function resetAccountFilters()' in script
    assert '$("#user-reset-filters").addEventListener("click"' in script
    assert '$("#users-count").textContent' in script
    assert 'Hãy thử xóa bộ lọc' in script
    assert 'accountListRequestId' in script
