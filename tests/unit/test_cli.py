import argparse
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


def test_package_exposes_version() -> None:
    from ridefare import __version__

    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert __version__ == pyproject["project"]["version"]


def test_build_parser_registers_foundation_commands() -> None:
    from ridefare.cli import build_parser

    parser = build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )

    assert {"ingest", "transform", "train", "export-web"} <= set(subparsers.choices)


def test_ingest_reports_missing_default_raw_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ridefare.cli import main

    monkeypatch.chdir(tmp_path)

    exit_code = main(["ingest"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "PFDA_rides.csv" in captured.err
    assert "PFDA_weather.csv" in captured.err


def test_transform_reports_missing_interim_parquet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ridefare.cli import main

    (tmp_path / "dbt").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    exit_code = main(["transform"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "rides.parquet" in captured.err
    assert "weather.parquet" in captured.err


def test_train_reports_missing_default_duckdb_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ridefare.cli import main

    monkeypatch.chdir(tmp_path)

    exit_code = main(["train"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "ridefare.duckdb" in captured.err


def test_export_web_reports_missing_latest_run_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ridefare.cli import main

    monkeypatch.chdir(tmp_path)

    exit_code = main(["export-web"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "latest" in captured.err


def test_cli_import_does_not_eagerly_load_ml_dependencies() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import ridefare.cli; "
                "print('xgboost' in sys.modules); print('shap' in sys.modules)"
            ),
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout.splitlines()[-2:] == ["False", "False"]
