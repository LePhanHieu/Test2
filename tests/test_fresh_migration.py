"""Smoke-test the real database migration followed by interactive setup."""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FLASK_ENTRY = "skin_cancer.webapp.database_app"


def test_fresh_migrations_then_setup_produce_only_initial_data(tmp_path):
    target = tmp_path / "dermascan_live.db"
    environ = dict(os.environ)
    environ.update({
        "SECRET_KEY": "isolated-migration-test-key",
        "DATABASE_URL": f"sqlite:///{target}",
    })
    migrate = subprocess.run(
        [sys.executable, "-m", "flask", "--app", FLASK_ENTRY, "db", "upgrade"],
        cwd=REPO_ROOT, env=environ, text=True, capture_output=True, check=False,
    )
    assert migrate.returncode == 0, migrate.stderr

    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0

    initial_input = (
        "Test Admin\nadmin@bootstrap.example\nAdminPassword123!\nAdminPassword123!\n"
        "Test Doctor\ndoctor@bootstrap.example\nDoctorPassword123!\nDoctorPassword123!\n"
        "Test Patient\npatient@bootstrap.example\nPatientPassword123!\nPatientPassword123!\n"
    )
    setup = subprocess.run(
        [sys.executable, "-m", "flask", "--app", FLASK_ENTRY, "setup-initial"],
        cwd=REPO_ROOT, env=environ, text=True, input=initial_input,
        capture_output=True, check=False,
    )
    assert setup.returncode == 0, setup.stderr + setup.stdout
    assert "AdminPassword123!" not in setup.stdout

    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM slides").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 0


def test_migrations_and_noninteractive_local_starter_accounts(tmp_path):
    target = tmp_path / "local_starters.db"
    environ = dict(os.environ)
    environ.update({
        "SECRET_KEY": "isolated-starter-test-key",
        "DATABASE_URL": f"sqlite:///{target}",
    })
    for args in [
        [sys.executable, "-m", "flask", "--app", FLASK_ENTRY, "db", "upgrade"],
        [sys.executable, "-m", "flask", "--app", FLASK_ENTRY, "setup-initial", "--local-starter-accounts"],
    ]:
        result = subprocess.run(args, cwd=REPO_ROOT, env=environ,
                                text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stderr + result.stdout
    with sqlite3.connect(target) as conn:
        assert set(conn.execute("SELECT email, role FROM users")) == {
            ("admin@dermascan.local", "ADMIN"),
            ("doctor@dermascan.local", "DOCTOR"),
            ("patient@dermascan.local", "USER"),
        }
        assert conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 0
