from pathlib import Path


def test_public_project_docs_exist() -> None:
    assert Path("README.md").exists()
    assert Path("docs/architecture/system-overview.md").exists()
    assert Path("docs/runbooks/local-development.md").exists()
    assert Path("docs/runbooks/deployment.md").exists()
    assert Path("docs/runbooks/release-process.md").exists()
    assert Path("docs/ml/model-card.md").exists()
    assert Path("docs/ml/evaluation-protocol.md").exists()
    assert Path("docs/ml/modeling-strategy.md").exists()
    assert Path("docs/ui/design-system.md").exists()


def test_phase_6_visual_assets_exist() -> None:
    assert Path("apps/web/app/icon.svg").exists()
    assert Path("apps/web/app/apple-icon.tsx").exists()
    assert Path("apps/web/app/opengraph-image.tsx").exists()
    assert Path("apps/web/app/twitter-image.tsx").exists()
    assert Path("docs/ui/screenshots/phase-6/home-desktop.png").exists()
    assert Path("docs/ui/screenshots/phase-6/dashboard-desktop.png").exists()
    assert Path("docs/ui/screenshots/phase-6/como-funciona-desktop.png").exists()
    assert Path("docs/ui/screenshots/phase-6/escenarios-desktop.png").exists()
    assert Path("docs/ui/screenshots/phase-6/dashboard-mobile.png").exists()
    assert Path("docs/ui/screenshots/phase-6/escenarios-mobile.png").exists()
