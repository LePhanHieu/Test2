"""The default launcher must select new operational storage, not the demo DB."""

from pathlib import Path

from skin_cancer.webapp.config import INSTANCE_DIR, database_config


def test_default_database_is_a_new_clean_file(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    uri = database_config()["SQLALCHEMY_DATABASE_URI"]
    assert uri == "sqlite:///" + (INSTANCE_DIR / "dermascan_live.db").as_posix()


def test_database_url_override_still_works(monkeypatch, tmp_path):
    custom = f"sqlite:///{tmp_path / 'custom.db'}"
    monkeypatch.setenv("DATABASE_URL", custom)
    assert database_config()["SQLALCHEMY_DATABASE_URI"] == custom
