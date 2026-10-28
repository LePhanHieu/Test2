"""Opt-in fixtures for tests touching storage or external services.

These fixtures deliberately do not run for the existing test suite unless
requested by name. Tests that import the heavy AI entrypoint must additionally
replace its hard-coded Grad-CAM path before invoking a worker.
"""

import socket

import pytest


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """Route Flask data, cache, images, reports and planned AI output to tmp."""
    from skin_cancer.webapp import config, database_app
    from skin_cancer.webapp.services import result_cache

    root = tmp_path.resolve()
    instance_dir = root / "instance"
    upload_dir = instance_dir / "uploads"
    report_dir = instance_dir / "reports"
    gradcam_dir = instance_dir / "gradcam"
    database = instance_dir / "test.db"
    cache_db = instance_dir / "cache.db"
    for directory in (instance_dir, upload_dir, report_dir, gradcam_dir):
        directory.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(config, "INSTANCE_DIR", instance_dir)
    monkeypatch.setattr(database_app, "INSTANCE_DIR", instance_dir)
    monkeypatch.setattr(result_cache, "CACHE_DB_PATH", cache_db)
    monkeypatch.setattr(result_cache, "_mem_cache", {})
    monkeypatch.setattr(result_cache, "_sqlite_initialized", False)
    monkeypatch.setattr(result_cache, "_client", None)
    monkeypatch.setattr(result_cache, "redis", None)

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    app_config = {
        "TESTING": True,
        "SECRET_KEY": "test-only-isolation-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.as_posix()}",
        "UPLOAD_FOLDER": str(upload_dir),
        "REPORT_FOLDER": str(report_dir),
        "RATELIMIT_ENABLED": False,
        "WTF_CSRF_ENABLED": False,
        "MAIL_SUPPRESS_SEND": True,
        "OPENAI_API_KEY": "",
    }

    def redirect_ai_worker_root(worker_webapp):
        """Call before `_run_analysis`: it uses webapp.PROJECT_ROOT for Grad-CAM.

        Importing `skin_cancer.webapp.app` itself may load real model weights,
        so the individual AI test must first supply its model/worker stubs.
        """
        monkeypatch.setattr(worker_webapp, "PROJECT_ROOT", root)

    yield {
        "root": root,
        "instance_dir": instance_dir,
        "database": database,
        "cache_db": cache_db,
        "upload_dir": upload_dir,
        "report_dir": report_dir,
        "gradcam_dir": gradcam_dir,
        "app_config": app_config,
        "redirect_ai_worker_root": redirect_ai_worker_root,
    }


@pytest.fixture
def offline_runtime(monkeypatch):
    """Fail closed on direct sockets and email in opt-in backend tests."""
    from skin_cancer.webapp.extensions import mail

    def block_connect(*_args, **_kwargs):
        raise RuntimeError("external network disabled in isolated tests")

    def block_mail(*_args, **_kwargs):
        raise RuntimeError("email disabled in isolated tests")

    monkeypatch.setattr(socket.socket, "connect", block_connect)
    monkeypatch.setattr(socket, "create_connection", block_connect)
    monkeypatch.setattr(mail, "send", block_mail)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    yield
