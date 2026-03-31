import argparse
from pathlib import Path

import pytest


def test_package_exposes_version() -> None:
    from ridefare import __version__

    assert __version__ == "0.1.0"


def test_build_parser_registers_foundation_commands() -> None:
    from ridefare.cli import build_parser

    parser = build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )

    assert {"ingest", "transform", "train", "export-web"} <= set(subparsers.choices)


@pytest.mark.parametrize("command_name", ["train", "export-web"])
def test_remaining_placeholder_commands_exit_cleanly(
    command_name: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from ridefare.cli import main

    exit_code = main([command_name])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert command_name in captured.out
    assert "not implemented yet" in captured.out


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
