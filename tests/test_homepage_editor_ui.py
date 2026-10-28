"""Homepage editor removes legacy media selects and uses custom date controls."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "skin_cancer/webapp"


def test_homepage_intro_removed_but_save_retained():
    html = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
    assert "NỘI DUNG WEBSITE" not in html
    assert "Chỉnh sửa thông tin, hình ảnh và xem trước trước khi lưu." not in html
    assert 'id="hm-save"' in html


def test_media_selector_removed_but_upload_preview_kept():
    js = (ROOT / "static/js/homepage_management.js").read_text(encoding="utf-8")
    assert 'Chọn hình ảnh có sẵn' not in js
    assert 'data-hm-file=' in js
    assert 'data-hm-image=' in js
    assert 'state.files.get(path)?.file.name' in js


def test_custom_datetime_and_add_banner_button():
    js = (ROOT / "static/js/homepage_management.js").read_text(encoding="utf-8")
    css = (ROOT / "static/css/homepage-management.css").read_text(encoding="utf-8")
    assert "type:'datetime-local'" not in js
    assert 'data-hm-calendar' in js
    assert 'data-hm-day' in js
    assert 'data-hm-add' in js
    assert '.hm-add-banner' in css
    assert '.hm-calendar-popover' in css
