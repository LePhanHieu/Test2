"""Admin account deletion uses branded UI and refreshes stale CSRF tokens."""

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1] / "skin_cancer/webapp"


def test_delete_dialog_is_branded_and_has_error_feedback():
    html = (ROOT / "templates/admin.html").read_text(encoding="utf-8")
    js = (ROOT / "static/js/admin.js").read_text(encoding="utf-8")
    css = (ROOT / "static/css/admin-doctor-theme.css").read_text(encoding="utf-8")
    assert 'id="delete-account-modal"' in html
    assert 'id="delete-account-confirm"' in html
    assert 'id="delete-account-error"' in html
    assert 'confirm(`Xóa VĨNH VIỄN' not in js
    assert '.delete-account-modal' in css


def test_admin_api_recovers_only_from_expired_csrf():
    js = (ROOT / "static/js/admin.js").read_text(encoding="utf-8")
    assert "csrfToken = \"\";" in js
    assert "CSRF token thiếu hoặc hết hạn" in js
    assert "refreshCsrfToken" in js
    assert "attempt" in js


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js unavailable")
def test_admin_api_retries_once_on_csrf_error_but_not_other_errors():
    script = r"""
const fs = require('fs');
const assert = require('assert');
const source = fs.readFileSync(process.argv[1], 'utf8');
const fragment = source.slice(source.indexOf('async function refreshCsrfToken()'), source.indexOf('async function loadDashboard()'));
const factory = new Function('fetch', 'let csrfToken="stale"; const csrfMethods = new Set(["POST","PUT","PATCH","DELETE"]); ' + fragment + '; return api;');
const jsonResponse = (status, data) => ({ok:status>=200&&status<300,status,json:async()=>data});
(async () => {
  const calls=[];
  const api=factory(async (url,options) => {
    calls.push({url, token:options.headers['X-CSRFToken']});
    if(calls.length===1) return jsonResponse(400,{error:'CSRF token thiếu hoặc hết hạn'});
    if(calls.length===2) return jsonResponse(200,{csrf_token:'fresh'});
    return jsonResponse(200,{success:true});
  });
  assert.equal((await api('/api/admin/users/2',{method:'DELETE'})).success,true);
  assert.deepEqual(calls.map(call=>call.token),['stale',undefined,'fresh']);
  let otherCalls=0;
  const noRetry=factory(async () => {otherCalls++;return jsonResponse(400,{message:'Không thể xóa tài khoản đang đăng nhập.'});});
  await assert.rejects(noRetry('/api/admin/users/1',{method:'DELETE'}),/Không thể xóa/);
  assert.equal(otherCalls,1);
})().catch(error => {console.error(error);process.exit(1)});
"""
    result = subprocess.run(
        ["node", "-e", script, str(ROOT / "static/js/admin.js")],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
