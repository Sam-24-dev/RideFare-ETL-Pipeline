def test_project_root_guides_exist() -> None:
    from pathlib import Path

    assert Path("AGENTS.md").exists()
    assert Path("ROADMAP.md").exists()
