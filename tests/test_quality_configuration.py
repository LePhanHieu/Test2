"""CI must run the safe, isolated test suite and never the legacy E2E."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_quality_workflow_runs_only_safe_tests():
    workflow = (REPO_ROOT / ".github/workflows/quality.yml").read_text(
        encoding="utf-8"
    )

    assert "pytest tests/" in workflow
    assert "test_all_features_e2e.py" not in workflow
    assert "DATABASE_URL" in workflow
    assert "pytest-cov" in workflow or "--cov=" in workflow


def test_quality_workflow_has_separate_read_only_checks():
    workflow = (REPO_ROOT / ".github/workflows/quality.yml").read_text(
        encoding="utf-8"
    )

    assert "ruff check" in workflow
    assert "ruff format --check" in workflow
    assert "bandit -r" in workflow
    assert "--fix" not in workflow
