import { describe, expect, it } from "vitest";

import type { ModelLabPayload } from "../../lib/data/loaders";
import {
  buildScenarioExperience,
  findBaseScenario,
  findScenarioBySelection,
  hasPendingScenarioChanges,
  pickDefaultScenarioSelection,
  resolveScenarioDraft,
} from "../../components/scenarios/scenarios-derivations";

const payload: ModelLabPayload = {
  overview: {
    run_id: "scenario-run",
    generated_at: "2026-04-01T00:00:00+00:00",
    champion_model: "dummy_mean",
    explainability_model: "xgboost",
    row_count: 576,
    time_range: {
      min: "2024-03-31T00:00:00",
      max: "2024-03-31T23:00:00",
    },
    feature_columns: [
      "numeric__distance",
      "numeric__surge_multiplier",
      "numeric__temp",
      "numeric__ride_hour_of_day",
    ],
    holdout_rows: 144,
    development_rows: 432,
  },
  metrics: [],
  featureImportance: [
    { feature: "numeric__distance", importance: 0 },
    { feature: "numeric__surge_multiplier", importance: 0 },
    { feature: "numeric__temp", importance: 0 },
    { feature: "numeric__ride_hour_of_day", importance: 0 },
  ],
  shapSummary: {
    model_name: "xgboost",
    global_importance: [
      { feature: "numeric__distance", mean_abs_shap: 0 },
      { feature: "numeric__surge_multiplier", mean_abs_shap: 0 },
      { feature: "numeric__temp", mean_abs_shap: 0 },
      { feature: "numeric__ride_hour_of_day", mean_abs_shap: 0 },
    ],
    samples: [],
  },
  predictionSnapshot: [],
  runManifest: {
    run_id: "scenario-run",
    generated_at: "2026-04-01T00:00:00+00:00",
    dataset: {
      row_count: 576,
      feature_columns: [
        "numeric__distance",
        "numeric__surge_multiplier",
        "numeric__temp",
        "numeric__ride_hour_of_day",
      ],
      time_range: {
        min: "2024-03-31T00:00:00",
        max: "2024-03-31T23:00:00",
      },
    },
    split_plan: {
      holdout_rows: 144,
      development_rows: 432,
    },
  },
  simulator: {
    controls: {
      generated_at: "2026-04-01T00:00:00+00:00",
      model_name: "xgboost",
      simulator_mode: "model_direct",
      default_day_of_week: 0,
      sources: ["Beacon Hill", "North End"],
      destinations_by_source: {
        "Beacon Hill": ["Financial District", "North End"],
        "North End": ["Back Bay", "South Station"],
      },
      cab_types: ["Lyft", "Uber"],
      time_blocks: [
        { id: "madrugada", label: "Madrugada", hours: [0, 1, 2, 3, 4, 5], anchor_hour: 3 },
        { id: "manana", label: "Mañana", hours: [6, 7, 8, 9, 10, 11], anchor_hour: 9 },
        { id: "tarde", label: "Tarde", hours: [12, 13, 14, 15, 16, 17], anchor_hour: 15 },
        { id: "noche", label: "Noche", hours: [18, 19, 20, 21, 22, 23], anchor_hour: 21 },
      ],
      weather_profiles: [
        {
          id: "despejado",
          label: "Despejado",
          description: "Cielo estable y menor fricción climática.",
          values: { temp: 18, clouds: 10, pressure: 1012, rain: 0, humidity: 58, wind: 6 },
        },
        {
          id: "nublado",
          label: "Nublado",
          description: "Mayor cobertura y lectura más contenida.",
          values: { temp: 16, clouds: 72, pressure: 1010, rain: 0, humidity: 62, wind: 8 },
        },
        {
          id: "lluvia",
          label: "Lluvia",
          description: "La lluvia añade fricción y reduce la oferta visible.",
          values: { temp: 14, clouds: 85, pressure: 1006, rain: 2.2, humidity: 81, wind: 12 },
        },
        {
          id: "ventoso",
          label: "Ventoso",
          description: "Ráfagas y mayor incomodidad para trayectos expuestos.",
          values: { temp: 15, clouds: 32, pressure: 1008, rain: 0, humidity: 64, wind: 19 },
        },
      ],
      surge_levels: [1, 1.25, 1.5],
      distance_factors: [
        { id: "compacta", label: "Compacta", factor: 0.85 },
        { id: "referencia", label: "Referencia", factor: 1 },
        { id: "extendida", label: "Extendida", factor: 1.15 },
      ],
      route_catalog: [
        {
          source: "Beacon Hill",
          destination: "Financial District",
          cab_type: "Lyft",
          ride_name: "Beacon Hill → Financial District",
          median_distance: 5.8,
          total_rides: 12,
        },
        {
          source: "Beacon Hill",
          destination: "North End",
          cab_type: "Lyft",
          ride_name: "Beacon Hill → North End",
          median_distance: 1.9,
          total_rides: 8,
        },
        {
          source: "North End",
          destination: "Back Bay",
          cab_type: "Uber",
          ride_name: "North End → Back Bay",
          median_distance: 2.1,
          total_rides: 11,
        },
        {
          source: "North End",
          destination: "South Station",
          cab_type: "Uber",
          ride_name: "North End → South Station",
          median_distance: 3.4,
          total_rides: 9,
        },
      ],
    },
    grid: [
      {
        source: "Beacon Hill",
        destination: "Financial District",
        cab_type: "Lyft",
        ride_name: "Beacon Hill → Financial District",
        route_distance_median: 5.8,
        time_block: "tarde",
        weather_profile: "despejado",
        surge_multiplier: 1,
        distance_factor: 1,
        predicted_price: 25.25,
        price_band_low: 23.9,
        price_band_high: 27.1,
      },
      {
        source: "Beacon Hill",
        destination: "Financial District",
        cab_type: "Lyft",
        ride_name: "Beacon Hill → Financial District",
        route_distance_median: 5.8,
        time_block: "tarde",
        weather_profile: "nublado",
        surge_multiplier: 1.25,
        distance_factor: 1,
        predicted_price: 28.4,
        price_band_low: 26.1,
        price_band_high: 30.9,
      },
      {
        source: "Beacon Hill",
        destination: "Financial District",
        cab_type: "Lyft",
        ride_name: "Beacon Hill → Financial District",
        route_distance_median: 5.8,
        time_block: "tarde",
        weather_profile: "lluvia",
        surge_multiplier: 1.5,
        distance_factor: 1.15,
        predicted_price: 31.4,
        price_band_low: 28.9,
        price_band_high: 34.1,
      },
      {
        source: "Beacon Hill",
        destination: "North End",
        cab_type: "Lyft",
        ride_name: "Beacon Hill → North End",
        route_distance_median: 1.9,
        time_block: "madrugada",
        weather_profile: "despejado",
        surge_multiplier: 1,
        distance_factor: 1,
        predicted_price: 11.9,
        price_band_low: 10.4,
        price_band_high: 13.2,
      },
      {
        source: "North End",
        destination: "Back Bay",
        cab_type: "Uber",
        ride_name: "North End → Back Bay",
        route_distance_median: 2.1,
        time_block: "manana",
        weather_profile: "lluvia",
        surge_multiplier: 1.25,
        distance_factor: 1,
        predicted_price: 18,
        price_band_low: 15.8,
        price_band_high: 20.6,
      },
      {
        source: "North End",
        destination: "Back Bay",
        cab_type: "Uber",
        ride_name: "North End → Back Bay",
        route_distance_median: 2.1,
        time_block: "manana",
        weather_profile: "lluvia",
        surge_multiplier: 1,
        distance_factor: 1,
        predicted_price: 15.5,
        price_band_low: 14.1,
        price_band_high: 17.2,
      },
      {
        source: "North End",
        destination: "South Station",
        cab_type: "Uber",
        ride_name: "North End → South Station",
        route_distance_median: 3.4,
        time_block: "noche",
        weather_profile: "ventoso",
        surge_multiplier: 1.5,
        distance_factor: 1,
        predicted_price: 21.8,
        price_band_low: 18.9,
        price_band_high: 24.9,
      },
      {
        source: "North End",
        destination: "South Station",
        cab_type: "Uber",
        ride_name: "North End → South Station",
        route_distance_median: 3.4,
        time_block: "noche",
        weather_profile: "despejado",
        surge_multiplier: 1,
        distance_factor: 1,
        predicted_price: 18.9,
        price_band_low: 17.1,
        price_band_high: 20.4,
      },
    ],
  },
};

describe("scenarios derivations", () => {
  it("selects the most expressive exported scenario while keeping the reference distance hidden", () => {
    const selection = pickDefaultScenarioSelection(payload);
    const experience = buildScenarioExperience(payload, selection);

    expect(selection).toEqual({
      source: "Beacon Hill",
      destination: "Financial District",
      cabType: "Lyft",
      timeBlock: "tarde",
      weatherProfile: "nublado",
      surgeMultiplier: 1.25,
    });
    expect(experience.referenceDistanceFactor).toBe(1);
    expect(experience.selectedScenario?.distance_factor).toBe(1);
    expect(experience.deltaAbs).toBeCloseTo(3.15, 2);
    expect(experience.deltaPct).toBeCloseTo(0.1248, 3);
  });

  it("normalizes dependent controls when the source changes and invalid values remain selected", () => {
    const draft = resolveScenarioDraft(payload, {
      source: "North End",
      destination: "Financial District",
      cabType: "Lyft",
      timeBlock: "tarde",
      weatherProfile: "nublado",
      surgeMultiplier: 1.25,
    });

    expect(draft.selection.source).toBe("North End");
    expect(draft.options.destinations).toEqual(["Back Bay", "South Station"]);
    expect(draft.selection.destination).toBe("Back Bay");
    expect(draft.selection.cabType).toBe("Uber");
    expect(draft.selection.timeBlock).toBe("manana");
    expect(draft.selection.weatherProfile).toBe("lluvia");
    expect(draft.selection.surgeMultiplier).toBe(1.25);
  });

  it("detects pending draft changes before the scenario is applied", () => {
    const initialSelection = pickDefaultScenarioSelection(payload);

    expect(hasPendingScenarioChanges(initialSelection, initialSelection)).toBe(false);
    expect(
      hasPendingScenarioChanges(initialSelection, {
        ...initialSelection,
        weatherProfile: "lluvia",
      }),
    ).toBe(true);
  });

  it("falls back to the same weather with base demand when a clean baseline is not exported", () => {
    const selection = {
      source: "North End",
      destination: "Back Bay",
      cabType: "Uber",
      timeBlock: "manana",
      weatherProfile: "lluvia",
      surgeMultiplier: 1.25,
    };

    const baseScenario = findBaseScenario(payload, selection);
    const experience = buildScenarioExperience(payload, selection);

    expect(baseScenario?.weather_profile).toBe("lluvia");
    expect(baseScenario?.surge_multiplier).toBe(1);
    expect(experience.deltaAbs).toBeCloseTo(2.5, 2);
    expect(experience.deltaPct).toBeCloseTo(0.161, 2);
  });

  it("returns null for combinations that do not exist in the exported grid", () => {
    const scenario = findScenarioBySelection(payload, {
      source: "Beacon Hill",
      destination: "Financial District",
      cabType: "Lyft",
      timeBlock: "noche",
      weatherProfile: "lluvia",
      surgeMultiplier: 1.5,
    });

    expect(scenario).toBeNull();
  });

  it("builds public influence cards and an editorial reading without ML jargon", () => {
    const experience = buildScenarioExperience(payload, {
      source: "Beacon Hill",
      destination: "Financial District",
      cabType: "Lyft",
      timeBlock: "tarde",
      weatherProfile: "nublado",
      surgeMultiplier: 1.25,
    });

    expect(experience.factors.map((factor) => factor.title)).toEqual([
      "Distancia",
      "Demanda",
      "Clima",
      "Hora y ritmo urbano",
    ]);
    expect(experience.factors[0]?.body).toContain("5.8 mi");
    expect(experience.factors[1]?.body).toContain("alta");
    expect(experience.factors[2]?.body).toContain("Nublado");
    expect(experience.editorial.heading).toBe("Cómo leer este escenario");
    expect(experience.editorial.columns[0]).toContain("Beacon Hill");
    expect(experience.editorial.columns[0]).toContain("Tarde");
    expect(experience.editorial.columns[1]).toContain("margen esperado");
  });

  it("reorders the visible factors when the applied scenario changes materially", () => {
    const expressiveExperience = buildScenarioExperience(payload, {
      source: "North End",
      destination: "South Station",
      cabType: "Uber",
      timeBlock: "noche",
      weatherProfile: "ventoso",
      surgeMultiplier: 1.5,
    });

    expect(expressiveExperience.factors[0]?.title).not.toBe("Distancia");
    expect(["Demanda", "Clima", "Hora y ritmo urbano"]).toContain(
      expressiveExperience.factors[0]?.title,
    );
    expect(expressiveExperience.editorial.columns[1]).toContain("margen esperado");
  });
});
