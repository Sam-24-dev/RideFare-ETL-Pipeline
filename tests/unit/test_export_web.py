from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd


class IdentityPreprocessor:
    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        return frame.loc[:, ["distance"]].to_numpy()


class FlatEstimator:
    def load_model(self, path: Path) -> None:
        self.path = path

    def predict(self, transformed: np.ndarray) -> np.ndarray:
        return np.full((len(transformed),), 18.35, dtype=float)


def build_sample_snapshot() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ride_id": 1,
                "ride_hour": "2024-03-31T12:00:00",
                "distance": 2.1,
                "surge_multiplier": 1.0,
                "temp": 45.0,
                "clouds": 25.0,
                "pressure": 1012.0,
                "rain": 0.0,
                "humidity": 55.0,
                "wind": 9.1,
                "ride_hour_of_day": 12,
                "ride_day_of_week": 0,
                "source": "North End",
                "destination": "Back Bay",
                "cab_type": "Uber",
                "ride_name": "UberX",
                "price": 12.5,
            },
            {
                "ride_id": 2,
                "ride_hour": "2024-03-31T12:00:00",
                "distance": 5.8,
                "surge_multiplier": 1.25,
                "temp": 47.0,
                "clouds": 40.0,
                "pressure": 1011.0,
                "rain": 0.2,
                "humidity": 60.0,
                "wind": 8.3,
                "ride_hour_of_day": 12,
                "ride_day_of_week": 0,
                "source": "Beacon Hill",
                "destination": "Financial District",
                "cab_type": "Lyft",
                "ride_name": "Lyft XL",
                "price": 24.2,
            },
            {
                "ride_id": 3,
                "ride_hour": "2024-03-31T13:00:00",
                "distance": 3.4,
                "surge_multiplier": 1.5,
                "temp": 50.0,
                "clouds": 65.0,
                "pressure": 1009.0,
                "rain": 0.0,
                "humidity": 58.0,
                "wind": 10.4,
                "ride_hour_of_day": 13,
                "ride_day_of_week": 0,
                "source": "North End",
                "destination": "South Station",
                "cab_type": "Uber",
                "ride_name": "Uber Comfort",
                "price": 18.0,
            },
            {
                "ride_id": 4,
                "ride_hour": "2024-03-31T14:00:00",
                "distance": 1.9,
                "surge_multiplier": 1.0,
                "temp": 51.0,
                "clouds": 70.0,
                "pressure": 1008.0,
                "rain": 0.1,
                "humidity": 62.0,
                "wind": 11.2,
                "ride_hour_of_day": 14,
                "ride_day_of_week": 0,
                "source": "Beacon Hill",
                "destination": "North End",
                "cab_type": "Lyft",
                "ride_name": "Lyft",
                "price": 10.8,
            },
        ]
    )


def test_build_scenario_payload_uses_hybrid_fallback_for_flat_predictions(
    tmp_path: Path, monkeypatch
) -> None:
    from ridefare import export_web

    preprocessor_path = tmp_path / "preprocessor.pkl"
    preprocessor_path.write_bytes(pickle.dumps(IdentityPreprocessor()))
    model_path = tmp_path / "xgboost.json"
    model_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(export_web, "XGBRegressor", FlatEstimator)

    payload = export_web.build_scenario_payload(
        dataset_snapshot=build_sample_snapshot(),
        metrics={"models": {"xgboost": {"holdout": {"rmse": 7.55}}}},
        model_path=model_path,
        preprocessor_path=preprocessor_path,
    )

    rounded_prices = {round(float(row["predicted_price"]), 2) for row in payload["grid"]}
    rounded_bands = {
        (
            round(float(row["price_band_low"]), 2),
            round(float(row["price_band_high"]), 2),
        )
        for row in payload["grid"]
    }

    assert payload["controls"]["simulator_mode"] == "hybrid_fallback"
    assert len(rounded_prices) >= 4
    assert len(rounded_bands) > 1


def test_build_time_block_multipliers_covers_all_public_blocks() -> None:
    from ridefare.export_web import build_time_block_multipliers

    multipliers = build_time_block_multipliers(build_sample_snapshot())

    assert set(multipliers) == {"madrugada", "manana", "tarde", "noche"}
    assert len({round(value, 4) for value in multipliers.values()}) > 1


def test_build_weather_profile_multipliers_separate_clear_and_rainy_profiles() -> None:
    from ridefare.export_web import build_weather_profile_multipliers, build_weather_profiles

    snapshot = build_sample_snapshot()
    profiles = build_weather_profiles(snapshot)
    multipliers = build_weather_profile_multipliers(snapshot, profiles)

    assert multipliers["lluvia"] > multipliers["nublado"]
    assert multipliers["nublado"] >= multipliers["despejado"]
    assert multipliers["ventoso"] >= multipliers["despejado"]


def test_build_route_baselines_include_base_price_and_volatility() -> None:
    from ridefare.export_web import build_route_baselines

    baselines = build_route_baselines(build_sample_snapshot())
    beacon_financial = baselines[("Beacon Hill", "Financial District", "Lyft")]

    assert beacon_financial["base_price"] == 24.2
    assert beacon_financial["median_distance"] == 5.8
    assert beacon_financial["route_volatility"] > 0


def test_build_hybrid_scenario_grid_varies_relative_uplift_by_route() -> None:
    from ridefare.export_web import (
        build_hybrid_scenario_grid,
        build_route_baselines,
        build_route_catalog,
        build_surge_levels,
        build_time_block_multipliers,
        build_weather_profile_multipliers,
        build_weather_profiles,
    )

    snapshot = build_sample_snapshot()
    route_catalog = build_route_catalog(snapshot)
    route_baselines = build_route_baselines(snapshot)
    weather_profiles = build_weather_profiles(snapshot)
    grid = build_hybrid_scenario_grid(
        route_catalog=route_catalog,
        route_baselines=route_baselines,
        weather_profiles=weather_profiles,
        weather_multipliers=build_weather_profile_multipliers(snapshot, weather_profiles),
        surge_levels=build_surge_levels(snapshot),
        time_multipliers=build_time_block_multipliers(snapshot),
        model_rmse=7.55,
    )

    def get_price(
        source: str,
        destination: str,
        cab_type: str,
        time_block: str,
        weather_profile: str,
        surge_multiplier: float,
    ) -> float:
        return next(
            row["predicted_price"]
            for row in grid
            if row["source"] == source
            and row["destination"] == destination
            and row["cab_type"] == cab_type
            and row["time_block"] == time_block
            and row["weather_profile"] == weather_profile
            and row["surge_multiplier"] == surge_multiplier
            and row["distance_factor"] == 1.0
        )

    beacon_uplift = (
        get_price("Beacon Hill", "Financial District", "Lyft", "noche", "lluvia", 1.5)
        / get_price("Beacon Hill", "Financial District", "Lyft", "tarde", "despejado", 1.0)
        - 1
    )
    back_bay_uplift = (
        get_price("North End", "Back Bay", "Uber", "noche", "lluvia", 1.5)
        / get_price("North End", "Back Bay", "Uber", "tarde", "despejado", 1.0)
        - 1
    )

    assert round(beacon_uplift, 3) != round(back_bay_uplift, 3)
