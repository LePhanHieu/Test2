"""Safeguards for future AI/API tests that must not touch live state."""

import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from skin_cancer.webapp.services import result_cache


def test_isolated_storage_writes_cache_only_inside_tmp_path(isolated_storage):
    paths = isolated_storage
    result_cache.save_cached("isolation-probe", {"result": "synthetic"})

    assert result_cache.get_cached("isolation-probe") == {"result": "synthetic"}
    assert result_cache.CACHE_DB_PATH == paths["cache_db"]
    assert paths["cache_db"].is_file()
    assert paths["cache_db"].is_relative_to(paths["root"])
    assert paths["upload_dir"].is_relative_to(paths["root"])
    assert paths["report_dir"].is_relative_to(paths["root"])
    assert paths["gradcam_dir"].is_relative_to(paths["root"])


def test_isolated_storage_configures_flask_instance_and_database(isolated_storage):
    from skin_cancer.webapp.database_app import create_app

    paths = isolated_storage
    app = create_app(paths["app_config"])

    assert Path(app.instance_path) == paths["instance_dir"]
    assert app.config["SQLALCHEMY_DATABASE_URI"] == (
        "sqlite:///" + paths["database"].as_posix()
    )
    assert Path(app.config["UPLOAD_FOLDER"]) == paths["upload_dir"]
    assert Path(app.config["REPORT_FOLDER"]) == paths["report_dir"]


def test_offline_runtime_rejects_outbound_sockets_and_mail(offline_runtime):
    from skin_cancer.webapp.extensions import mail

    with pytest.raises(RuntimeError, match="external network disabled"):
        socket.socket().connect(("198.51.100.1", 443))

    with pytest.raises(RuntimeError, match="email disabled"):
        mail.send(object())


def test_isolated_storage_redirects_hardcoded_gradcam_worker_root(isolated_storage):
    paths = isolated_storage
    worker_webapp = SimpleNamespace(PROJECT_ROOT=Path("/outside-test"))

    paths["redirect_ai_worker_root"](worker_webapp)

    assert worker_webapp.PROJECT_ROOT / "instance" / "gradcam" == paths["gradcam_dir"]
