from pathlib import Path


def test_runtime_dependencies_do_not_use_github_urls():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "git+https://" not in pyproject
    assert "github.com" not in pyproject
    assert "lemonade-store>=0.1.0" in pyproject
