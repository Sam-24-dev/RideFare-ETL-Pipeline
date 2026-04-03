"""Path and runtime configuration for the RideFare data platform."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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
class TrainConfig:
    """Resolved configuration for the train command."""

    project_root: Path
    duckdb_path: Path
    artifacts_dir: Path
    run_id: str
    run_dir: Path
    latest_dir: Path


@dataclass(frozen=True)
class ExportWebConfig:
    """Resolved configuration for the export-web command."""

    project_root: Path
    duckdb_path: Path
    artifacts_dir: Path
    analytics_output_dir: Path
    run_id: str
    selected_run_dir: Path
    web_output_dir: Path


def _default_run_id() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")


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
    ml_artifacts_dir: Path
    analytics_artifacts_dir: Path
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
            ml_artifacts_dir=data_dir / "processed" / "ml",
            analytics_artifacts_dir=data_dir / "processed" / "analytics",
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

    def train_config(
        self,
        duckdb_path: str | Path | None = None,
        artifacts_dir: str | Path | None = None,
        run_id: str | None = None,
    ) -> TrainConfig:
        resolved_artifacts_dir = _resolve_candidate(
            self.project_root,
            artifacts_dir,
            self.ml_artifacts_dir,
        )
        selected_run_id = run_id or _default_run_id()
        return TrainConfig(
            project_root=self.project_root,
            duckdb_path=_resolve_candidate(self.project_root, duckdb_path, self.duckdb_path),
            artifacts_dir=resolved_artifacts_dir,
            run_id=selected_run_id,
            run_dir=resolved_artifacts_dir / "runs" / selected_run_id,
            latest_dir=resolved_artifacts_dir / "latest",
        )

    def export_web_config(
        self,
        artifacts_dir: str | Path | None = None,
        web_output_dir: str | Path | None = None,
        run_id: str | None = None,
    ) -> ExportWebConfig:
        resolved_artifacts_dir = _resolve_candidate(
            self.project_root,
            artifacts_dir,
            self.ml_artifacts_dir,
        )
        if run_id in (None, "latest"):
            selected_run_id = "latest"
            selected_run_dir = resolved_artifacts_dir / "latest"
        else:
            selected_run_id = run_id
            selected_run_dir = resolved_artifacts_dir / "runs" / selected_run_id
        return ExportWebConfig(
            project_root=self.project_root,
            duckdb_path=self.duckdb_path,
            artifacts_dir=resolved_artifacts_dir,
            analytics_output_dir=self.analytics_artifacts_dir / "web",
            run_id=selected_run_id,
            selected_run_dir=selected_run_dir,
            web_output_dir=_resolve_candidate(
                self.project_root,
                web_output_dir,
                resolved_artifacts_dir / "web",
            ),
        )
