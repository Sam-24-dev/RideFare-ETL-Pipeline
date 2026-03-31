from pathlib import Path


def test_public_project_docs_exist() -> None:
    assert Path("README.md").exists()
    assert Path("docs/architecture/system-overview.md").exists()
    assert Path("docs/runbooks/local-development.md").exists()
