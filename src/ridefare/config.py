"""Path and runtime configuration for the RideFare data platform."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _resolve_candidate(project_root: Path, candidate: str | Path | None, default: Path) -> Path:
    if candidate is None:
        return default

    path = Path(candidate)
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


@dataclass(frozen=True)
class IngestConfig:
    """Resolved configuration for the ingest command."""

    project_root: Path
    rides_path: Path
    weather_path: Path
    interim_dir: Path
    manifest_path: Path


@dataclass(frozen=True)
class TransformConfig:
    """Resolved configuration for the transform command."""

    project_root: Path
    interim_dir: Path
    duckdb_path: Path
    dbt_project_dir: Path
    dbt_profiles_dir: Path


@dataclass(frozen=True)
class RideFarePaths:
    """Canonical project locations for RideFare."""

    project_root: Path
    rides_raw_path: Path
    weather_raw_path: Path
    interim_dir: Path
    processed_dir: Path
    duckdb_path: Path
    dbt_project_dir: Path
    dbt_profiles_dir: Path
    samples_dir: Path

    @classmethod
    def defaults(cls, project_root: Path | None = None) -> RideFarePaths:
        root = (project_root or Path.cwd()).resolve()
        data_dir = root / "data"
        return cls(
            project_root=root,
            rides_raw_path=data_dir / "raw" / "PFDA_rides.csv",
            weather_raw_path=data_dir / "raw" / "PFDA_weather.csv",
            interim_dir=data_dir / "interim",
            processed_dir=data_dir / "processed",
            duckdb_path=data_dir / "processed" / "ridefare.duckdb",
            dbt_project_dir=root / "dbt",
            dbt_profiles_dir=data_dir / "processed" / "dbt_profiles",
            samples_dir=data_dir / "samples",
        )

    def ingest_config(
        self,
        rides_path: str | Path | None = None,
        weather_path: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> IngestConfig:
        resolved_output_dir = _resolve_candidate(
            self.project_root,
            output_dir,
            self.interim_dir,
        )
        return IngestConfig(
            project_root=self.project_root,
            rides_path=_resolve_candidate(self.project_root, rides_path, self.rides_raw_path),
            weather_path=_resolve_candidate(self.project_root, weather_path, self.weather_raw_path),
            interim_dir=resolved_output_dir,
            manifest_path=resolved_output_dir / "run_manifest.json",
        )

    def transform_config(
        self,
        duckdb_path: str | Path | None = None,
        profiles_dir: str | Path | None = None,
    ) -> TransformConfig:
        return TransformConfig(
            project_root=self.project_root,
            interim_dir=self.interim_dir,
            duckdb_path=_resolve_candidate(self.project_root, duckdb_path, self.duckdb_path),
            dbt_project_dir=self.dbt_project_dir,
            dbt_profiles_dir=_resolve_candidate(
                self.project_root,
                profiles_dir,
                self.dbt_profiles_dir,
            ),
        )
