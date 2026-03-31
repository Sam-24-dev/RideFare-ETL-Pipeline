"""CLI entrypoints for the RideFare project."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from ridefare.config import RideFarePaths
from ridefare.exceptions import RideFareError
from ridefare.export_web import run_export_web
from ridefare.ingestion import run_ingest
from ridefare.ml_training import run_train
from ridefare.transform import run_transform


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


def handle_train(args: argparse.Namespace) -> int:
    paths = RideFarePaths.defaults()
    config = paths.train_config(
        duckdb_path=args.duckdb_path,
        artifacts_dir=args.artifacts_dir,
        run_id=args.run_id,
    )
    result = run_train(config)
    print(f"Train completed. ML artifacts written to {result.run_dir}.")
    return 0


def handle_export_web(args: argparse.Namespace) -> int:
    paths = RideFarePaths.defaults()
    config = paths.export_web_config(
        artifacts_dir=args.artifacts_dir,
        web_output_dir=args.web_output_dir,
        run_id=args.run_id,
    )
    result = run_export_web(config)
    print(f"Web export completed. Artifacts written to {result.web_output_dir}.")
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

    train_parser = subparsers.add_parser("train")
    train_parser.add_argument("--duckdb-path")
    train_parser.add_argument("--artifacts-dir")
    train_parser.add_argument("--run-id")
    train_parser.set_defaults(handler=handle_train)

    export_parser = subparsers.add_parser("export-web")
    export_parser.add_argument("--artifacts-dir")
    export_parser.add_argument("--web-output-dir")
    export_parser.add_argument("--run-id")
    export_parser.set_defaults(handler=handle_export_web)

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
