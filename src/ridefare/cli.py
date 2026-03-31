"""Foundation CLI entrypoints for the RideFare project."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from ridefare.config import RideFarePaths
from ridefare.exceptions import RideFareError
from ridefare.ingestion import run_ingest
from ridefare.transform import run_transform


def _run_placeholder(command_name: str) -> int:
    print(f"{command_name} is registered but not implemented yet.")
    return 0


def handle_ingest(args: argparse.Namespace) -> int:
    paths = RideFarePaths.defaults()
    config = paths.ingest_config(
        rides_path=args.rides_path,
        weather_path=args.weather_path,
        output_dir=args.output_dir,
    )
    run_ingest(config)
    print(f"Ingest completed. Interim artifacts written to {config.interim_dir}.")
    return 0


def handle_transform(args: argparse.Namespace) -> int:
    paths = RideFarePaths.defaults()
    config = paths.transform_config(
        duckdb_path=args.duckdb_path,
        profiles_dir=args.profiles_dir,
    )
    run_transform(config)
    print(f"Transform completed. DuckDB database available at {config.duckdb_path}.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ridefare",
        description="RideFare project command line interface.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest")
    ingest_parser.add_argument("--rides-path")
    ingest_parser.add_argument("--weather-path")
    ingest_parser.add_argument("--output-dir")
    ingest_parser.set_defaults(handler=handle_ingest)

    transform_parser = subparsers.add_parser("transform")
    transform_parser.add_argument("--duckdb-path")
    transform_parser.add_argument("--profiles-dir")
    transform_parser.set_defaults(handler=handle_transform)

    for command_name in ("train", "export-web"):
        command_parser = subparsers.add_parser(command_name)
        command_parser.set_defaults(handler=lambda _, name=command_name: _run_placeholder(name))

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    try:
        return handler(args)
    except RideFareError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def console_main() -> None:
    raise SystemExit(main())


def ingest_entrypoint() -> None:
    raise SystemExit(main(["ingest"]))


def transform_entrypoint() -> None:
    raise SystemExit(main(["transform"]))


def train_entrypoint() -> None:
    raise SystemExit(main(["train"]))


def export_web_entrypoint() -> None:
    raise SystemExit(main(["export-web"]))
