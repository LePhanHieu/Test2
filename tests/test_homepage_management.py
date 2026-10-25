"""Website configuration uses site_settings/slides without new content tables."""
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from skin_cancer.webapp.database_app import create_app
from skin_cancer.webapp.extensions import db
from skin_cancer.webapp.models import SiteSetting, Slide, User
from skin_cancer.webapp.services.site_settings_service import SiteSettingsService


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        'SECRET_KEY': 'homepage-editor-tests',
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'homepage.db'}",
        'RATELIMIT_ENABLED': False, 'TESTING': True,
        'WTF_CSRF_ENABLED': False,
    })
    # Site uploads must remain isolated to a temporary instance directory.
    application.instance_path = str(tmp_path / 'instance')
    with application.app_context():
        db.create_all()
        admin = User(full_name='Website Admin', email='homepage-admin@example.test',
                     role='ADMIN', is_active=True, email_verified=True)
        admin.set_password('StrongPassword123!')
        db.session.add(admin)
        db.session.commit()
    return application


def _login(client):
    response = client.post('/api/auth/login', json={
        'email': 'homepage-admin@example.test', 'password': 'StrongPassword123!',
    })
    # An ADMIN may require terminal 2FA on production; tests use an authenticated session.
    if response.get_json().get('requires_2fa'):
        with client.session_transaction() as sess:
            sess.clear()
            sess['_user_id'] = '1'
            sess['_fresh'] = True
    else:
        assert response.status_code == 200


def test_homepage_json_is_validated_persisted_and_public(app):
    client = app.test_client()
    _login(client)
    data = SiteSettingsService.HOMEPAGE_DEFAULTS
    result = client.put('/api/admin/site-settings', json={
        'site_name': 'DermaScan Y tế',
        'homepage_config': data,
    })
    assert result.status_code == 200, result.get_json()
    assert result.get_json()['homepage_config']['vi']['features']['items'][0]['title'] == 'Mô hình EfficientNet-B0'
    public = client.get('/api/site-settings')
    assert public.status_code == 200
    assert public.get_json()['site_name'] == 'DermaScan Y tế'
    assert public.get_json()['homepage_config']['en']['features']['title']
    with app.app_context():
        assert db.session.get(SiteSetting, 1).homepage_config is not None


@pytest.mark.parametrize('invalid', [
    {'vi': {'features': {'items': []}}},
    {'social_links': {'github': 'javascript:alert(1)'}},
    {'vi': {'footer_extra': {'medical_notice': 'Bỏ hết lưu ý'}}},
    {'unknown': 'value'},
])
def test_rejects_malformed_or_unsafe_homepage_data(app, invalid):
    client = app.test_client()
    _login(client)
    response = client.put('/api/admin/site-settings', json={'homepage_config': invalid})
    assert response.status_code == 400


def _png_bytes():
    output = BytesIO()
    Image.new('RGB', (80, 48), '#2ba149').save(output, 'PNG')
    return output.getvalue()


def test_admin_can_upload_and_select_site_artwork(app):
    client = app.test_client()
    assert client.get('/api/admin/site-media').status_code == 401
    _login(client)
    response = client.post('/api/admin/site-media', data={
        'kind': 'banners', 'image': (BytesIO(_png_bytes()), 'new-banner.png'),
    }, content_type='multipart/form-data')
    assert response.status_code == 201, response.get_json()
    path = response.get_json()['path']
    assert path.startswith('site_media/banners/') and path.endswith('.png')
    listing = client.get('/api/admin/site-media')
    assert any(item['path'] == path for item in listing.get_json()['images'])
    assert client.get('/api/admin/site-media/image', query_string={'path': path}).status_code == 200
    assert client.get('/api/admin/site-media/image', query_string={'path': '../dermascan.db'}).status_code == 404


def test_invalid_image_rejected_without_storing(app):
    client = app.test_client()
    _login(client)
    response = client.post('/api/admin/site-media', data={
        'kind': 'logos', 'image': (BytesIO(b'not an image'), 'fake.png'),
    }, content_type='multipart/form-data')
    assert response.status_code == 400


def test_homepage_save_is_atomic_and_uploaded_banner_renders(app):
    client = app.test_client()
    _login(client)
    upload = client.post('/api/admin/site-media', data={
        'kind': 'banners', 'image': (BytesIO(_png_bytes()), 'fresh.png'),
    }, content_type='multipart/form-data')
    assert upload.status_code == 201
    image_path = upload.get_json()['path']
    payload = {
        'settings': {'site_name': 'Trang chủ thực',
                     'homepage_config': SiteSettingsService.HOMEPAGE_DEFAULTS},
        'slides': [{'title': 'Banner mới', 'subtitle': 'Nội dung thật',
                    'image_path': image_path, 'button_text': 'Bắt đầu',
                    'button_url': '/#analyze', 'is_active': True}],
    }
    created = client.post('/api/admin/homepage/save', json=payload)
    assert created.status_code == 200, created.get_json()
    banner_id = created.get_json()['slides'][0]['id']
    assert client.get(f'/api/slides/{banner_id}/image').status_code == 200
    assert client.get('/api/slides/active').get_json()['slides'][0]['title'] == 'Banner mới'

    invalid = {'settings': {'site_name': 'KHÔNG ĐƯỢC LƯU'},
               'slides': [{'id': banner_id, 'title': 'Banner sai',
                           'image_path': '../invalid.png'}]}
    rejected = client.post('/api/admin/homepage/save', json=invalid)
    assert rejected.status_code == 400
    assert client.get('/api/site-settings').get_json()['site_name'] == 'Trang chủ thực'
    with app.app_context():
        assert db.session.get(Slide, banner_id).title == 'Banner mới'


def test_homepage_save_removes_only_banner_rows_and_preserves_settings(app):
    client = app.test_client()
    _login(client)
    first = client.post('/api/admin/homepage/save', json={
        'settings': {'site_name': 'Giữ nguyên dữ liệu'}, 'slides': [],
    })
    assert first.status_code == 200, first.get_json()
    second = client.get('/api/site-settings').get_json()
    assert second['site_name'] == 'Giữ nguyên dữ liệu'
    assert second['homepage_config']['vi']['features']['items']


def test_admin_homepage_editor_and_live_public_configuration_are_wired(app):
    client = app.test_client()
    _login(client)
    admin = client.get('/admin')
    assert admin.status_code == 200
    source = admin.get_data(as_text=True)
    for element in ('module-homepage', 'data-hm-tab="branding"',
                    'data-hm-tab="banners"', 'data-hm-tab="content"',
                    'data-hm-tab="contact"', 'data-hm-tab="footer"',
                    'data-hm-device="desktop"', 'data-hm-device="mobile"',
                    'homepage_management.js'):
        assert element in source
    home_template = Path(__file__).resolve().parents[1] / 'skin_cancer/webapp/templates/index.html'
    assert 'applyConfiguredHomepage' in home_template.read_text(encoding='utf-8')
