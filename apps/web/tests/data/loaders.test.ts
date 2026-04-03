import { afterEach, describe, expect, it } from "vitest";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  loadDashboardPayload,
  loadHomeSnapshot,
  loadHowItWorksSnapshot,
  loadModelLabPayload,
} from "../../lib/data/loaders";

const tempRoots: string[] = [];

afterEach(() => {
  process.env.RIDEFARE_PROJECT_ROOT = undefined;
  for (const tempRoot of tempRoots.splice(0)) {
    rmSync(tempRoot, { recursive: true, force: true });
  }
});

describe("web data loaders", () => {
  it("returns guided missing states when exported artifacts do not exist", async () => {
    const tempRoot = mkdtempSync(join(tmpdir(), "ridefare-web-missing-"));
    tempRoots.push(tempRoot);
    process.env.RIDEFARE_PROJECT_ROOT = tempRoot;

    const dashboard = await loadDashboardPayload();
    const home = await loadHomeSnapshot();
    const howItWorks = await loadHowItWorksSnapshot();
    const modelLab = await loadModelLabPayload();

    expect(dashboard.status).toBe("missing");
    expect(home.status).toBe("missing");
    expect(howItWorks.status).toBe("missing");
    expect(modelLab.status).toBe("missing");
  });

  it("loads typed dashboard and model artifacts from generated JSON", async () => {
    const tempRoot = mkdtempSync(join(tmpdir(), "ridefare-web-ready-"));
    tempRoots.push(tempRoot);
    process.env.RIDEFARE_PROJECT_ROOT = tempRoot;

    const mlDir = join(tempRoot, "data", "processed", "ml", "web");
    const analyticsDir = join(tempRoot, "data", "processed", "analytics", "web");
    mkdirSync(mlDir, { recursive: true });
    mkdirSync(analyticsDir, { recursive: true });

    writeFileSync(
      join(mlDir, "model_overview.json"),
      JSON.stringify({
        run_id: "demo-run",
        generated_at: "2026-03-30T00:00:00+00:00",
        champion_model: "xgboost",
        explainability_model: "xgboost",
        row_count: 128,
        time_range: {
          min: "2024-01-01T00:00:00",
          max: "2024-01-03T00:00:00",
        },
        feature_columns: ["distance", "surge_multiplier", "source", "destination"],
        holdout_rows: 26,
        development_rows: 102,
      }),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "model_metrics.json"),
      JSON.stringify([
        {
          model_name: "xgboost",
          holdout: { mae: 2.1, rmse: 3.4, r2: 0.72 },
          cross_validation: { mae: 2.4, rmse: 3.8, r2: 0.68 },
        },
      ]),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "feature_importance.json"),
      JSON.stringify([{ feature: "distance", importance: 0.42 }]),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "shap_summary.json"),
      JSON.stringify({
        model_name: "xgboost",
        global_importance: [{ feature: "distance", mean_abs_shap: 1.24 }],
        samples: [],
      }),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "prediction_snapshot.json"),
      JSON.stringify([
        {
          ride_id: 1,
          ride_hour: "2024-01-01T09:00:00",
          source: "North End",
          destination: "Back Bay",
          cab_type: "UberX",
          ride_name: "UberX",
          distance: 2.3,
          surge_multiplier: 1.0,
          actual: 12.5,
          predicted: 12.2,
          residual: 0.3,
          model_name: "xgboost",
        },
      ]),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "run_manifest.json"),
      JSON.stringify({
        run_id: "demo-run",
        generated_at: "2026-03-30T00:00:00+00:00",
        dataset: {
          row_count: 128,
          feature_columns: ["distance", "surge_multiplier", "source", "destination"],
          time_range: { min: "2024-01-01T00:00:00", max: "2024-01-03T00:00:00" },
        },
        split_plan: { holdout_rows: 26, development_rows: 102 },
      }),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "scenario_controls.json"),
      JSON.stringify({
        generated_at: "2026-03-30T00:00:00+00:00",
        model_name: "xgboost",
        simulator_mode: "hybrid_fallback",
        default_day_of_week: 1,
        sources: ["North End"],
        destinations_by_source: { "North End": ["Back Bay"] },
        cab_types: ["UberX"],
        time_blocks: [{ id: "manana", label: "Mañana", hours: [6, 7, 8, 9, 10, 11], anchor_hour: 9 }],
        weather_profiles: [
          {
            id: "despejado",
            label: "Despejado",
            description: "Cielo despejado.",
            values: { temp: 17, clouds: 15, pressure: 1012, rain: 0, humidity: 58, wind: 6 },
          },
        ],
        surge_levels: [1, 1.25],
        distance_factors: [{ id: "referencia", label: "Referencia", factor: 1 }],
        route_catalog: [
          {
            source: "North End",
            destination: "Back Bay",
            cab_type: "UberX",
            ride_name: "UberX",
            median_distance: 2.3,
            total_rides: 12,
          },
        ],
      }),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "scenario_grid.json"),
      JSON.stringify([
        {
          source: "North End",
          destination: "Back Bay",
          cab_type: "UberX",
          ride_name: "UberX",
          route_distance_median: 2.3,
          time_block: "manana",
          weather_profile: "despejado",
          surge_multiplier: 1,
          distance_factor: 1,
          predicted_price: 12.2,
          price_band_low: 9.1,
          price_band_high: 15.3,
        },
      ]),
      "utf-8",
    );

    writeFileSync(
      join(analyticsDir, "dashboard_overview.json"),
      JSON.stringify({
        generated_at: "2026-03-30T00:00:00+00:00",
        time_range: { min: "2024-01-01T00:00:00", max: "2024-01-03T00:00:00" },
        dimensions: { sources: 1, destinations: 1, cab_types: 1 },
        kpis: [
          { id: "total_rides", label: "Viajes modelados", value: 128, format: "integer" },
          { id: "avg_price", label: "Tarifa media", value: 12.5, format: "currency" },
          {
            id: "avg_surge_multiplier",
            label: "Surge medio",
            value: 1.05,
            format: "multiplier",
          },
          {
            id: "dominant_route",
            label: "Ruta más activa",
            value: "North End → Back Bay",
            format: "text",
          },
        ],
      }),
      "utf-8",
    );
    writeFileSync(
      join(analyticsDir, "dashboard_timeseries.json"),
      JSON.stringify([
        {
          ride_date: "2024-01-01T00:00:00",
          ride_hour: "2024-01-01T09:00:00",
          source: "North End",
          destination: "Back Bay",
          cab_type: "UberX",
          total_rides: 12,
          avg_price: 12.5,
          avg_surge_multiplier: 1.05,
        },
      ]),
      "utf-8",
    );
    writeFileSync(
      join(analyticsDir, "dashboard_route_breakdown.json"),
      JSON.stringify([
        {
          source: "North End",
          destination: "Back Bay",
          cab_type: "UberX",
          total_rides: 12,
          avg_price: 12.5,
          avg_distance: 2.3,
          avg_surge_multiplier: 1.05,
        },
      ]),
      "utf-8",
    );
    writeFileSync(
      join(analyticsDir, "dashboard_weather_impact.json"),
      JSON.stringify([
        {
          ride_date: "2024-01-01T00:00:00",
          ride_hour: "2024-01-01T09:00:00",
          source: "North End",
          destination: "Back Bay",
          cab_type: "UberX",
          total_rides: 12,
          avg_price: 12.5,
          avg_temp: 17.2,
          avg_clouds: 20,
          avg_humidity: 58,
        },
      ]),
      "utf-8",
    );
    writeFileSync(
      join(analyticsDir, "dashboard_filters.json"),
      JSON.stringify({
        sources: ["North End"],
        destinations: ["Back Bay"],
        cab_types: ["UberX"],
        time_windows: [{ id: "manana", label: "Mañana", hours: [6, 7, 8, 9, 10, 11], anchor_hour: 9 }],
      }),
      "utf-8",
    );

    const dashboard = await loadDashboardPayload();
    const home = await loadHomeSnapshot();
    const howItWorks = await loadHowItWorksSnapshot();
    const modelLab = await loadModelLabPayload();

    expect(dashboard.status).toBe("ready");
    expect(home.status).toBe("ready");
    expect(howItWorks.status).toBe("ready");
    expect(modelLab.status).toBe("ready");

    if (dashboard.status === "ready") {
      expect(dashboard.data.overview.kpis[0]?.label).toBe("Viajes modelados");
    }

    if (home.status === "ready") {
      expect(home.data.championModel).toBe("xgboost");
      expect(home.data.explainabilityModel).toBe("xgboost");
      expect(home.data.rowCount).toBe(128);
      expect(home.data.totalRides).toBe(128);
      expect(home.data.avgPrice).toBe(12.5);
      expect(home.data.avgSurge).toBe(1.05);
      expect(home.data.dominantRoute).toBe("North End → Back Bay");
    }

    if (howItWorks.status === "ready") {
      expect(howItWorks.data.generatedAt).toBe("2026-03-30T00:00:00+00:00");
      expect(howItWorks.data.featureCount).toBe(4);
      expect(howItWorks.data.sourceCount).toBe(1);
      expect(howItWorks.data.destinationCount).toBe(1);
      expect(howItWorks.data.cabTypeCount).toBe(1);
      expect(howItWorks.data.championModel).toBe("xgboost");
      expect(howItWorks.data.explainabilityModel).toBe("xgboost");
      expect(howItWorks.data.hasTemporalSplit).toBe(true);
      expect(howItWorks.data.timeRange.max).toBe("2024-01-03T00:00:00");
      expect(howItWorks.data.topSignals[0]).toEqual({
        label: "Distancia",
        score: 0.42,
      });
    }

    if (modelLab.status === "ready") {
      expect(modelLab.data.simulator.controls.sources).toContain("North End");
      expect(modelLab.data.simulator.controls.simulator_mode).toBe("hybrid_fallback");
      expect(modelLab.data.featureImportance[0]?.feature).toBe("distance");
    }
  });

  it("falls back to shap importance when feature importance is missing", async () => {
    const tempRoot = mkdtempSync(join(tmpdir(), "ridefare-web-shap-fallback-"));
    tempRoots.push(tempRoot);
    process.env.RIDEFARE_PROJECT_ROOT = tempRoot;

    const mlDir = join(tempRoot, "data", "processed", "ml", "web");
    const analyticsDir = join(tempRoot, "data", "processed", "analytics", "web");
    mkdirSync(mlDir, { recursive: true });
    mkdirSync(analyticsDir, { recursive: true });

    writeFileSync(
      join(mlDir, "model_overview.json"),
      JSON.stringify({
        run_id: "demo-run",
        generated_at: "2026-03-30T00:00:00+00:00",
        champion_model: "xgboost",
        explainability_model: "xgboost",
        row_count: 128,
        time_range: {
          min: "2024-01-01T00:00:00",
          max: "2024-01-03T00:00:00",
        },
        feature_columns: ["distance", "surge_multiplier", "source", "destination"],
        holdout_rows: 26,
        development_rows: 102,
      }),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "run_manifest.json"),
      JSON.stringify({
        run_id: "demo-run",
        generated_at: "2026-03-30T00:00:00+00:00",
        dataset: {
          row_count: 128,
          feature_columns: ["distance", "surge_multiplier", "source", "destination"],
          time_range: { min: "2024-01-01T00:00:00", max: "2024-01-03T00:00:00" },
        },
        split_plan: { holdout_rows: 26, development_rows: 102 },
      }),
      "utf-8",
    );
    writeFileSync(
      join(mlDir, "shap_summary.json"),
      JSON.stringify({
        model_name: "xgboost",
        global_importance: [
          { feature: "numeric__surge_multiplier", mean_abs_shap: 0.66 },
          { feature: "numeric__distance", mean_abs_shap: 0.5 },
        ],
        samples: [],
      }),
      "utf-8",
    );
    writeFileSync(
      join(analyticsDir, "dashboard_overview.json"),
      JSON.stringify({
        generated_at: "2026-03-30T00:00:00+00:00",
        time_range: { min: "2024-01-01T00:00:00", max: "2024-01-03T00:00:00" },
        dimensions: { sources: 1, destinations: 1, cab_types: 1 },
        kpis: [],
      }),
      "utf-8",
    );

    const howItWorks = await loadHowItWorksSnapshot();

    expect(howItWorks.status).toBe("ready");

    if (howItWorks.status === "ready") {
      expect(howItWorks.data.topSignals[0]).toEqual({
        label: "Demanda",
        score: 0.66,
      });
      expect(howItWorks.data.topSignals[1]).toEqual({
        label: "Distancia",
        score: 0.5,
      });
    }
  });
});
