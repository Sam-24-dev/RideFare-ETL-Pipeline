import { z } from "zod";

const timeRangeSchema = z.object({
  min: z.string().nullable(),
  max: z.string().nullable(),
});

const metricSummarySchema = z.object({
  mae: z.number(),
  rmse: z.number(),
  r2: z.number(),
});

export const modelOverviewSchema = z.object({
  run_id: z.string(),
  generated_at: z.string(),
  champion_model: z.string(),
  explainability_model: z.string(),
  row_count: z.number(),
  time_range: timeRangeSchema,
  feature_columns: z.array(z.string()),
  holdout_rows: z.number(),
  development_rows: z.number(),
});

export const modelMetricsSchema = z.array(
  z.object({
    model_name: z.string(),
    holdout: metricSummarySchema,
    cross_validation: metricSummarySchema,
  }),
);

export const featureImportanceSchema = z.array(
  z.object({
    feature: z.string(),
    importance: z.number(),
  }),
);

export const shapSummarySchema = z.object({
  model_name: z.string(),
  global_importance: z.array(
    z.object({
      feature: z.string(),
      mean_abs_shap: z.number(),
    }),
  ),
  samples: z.array(
    z.object({
      ride_id: z.number(),
      ride_hour: z.string(),
      base_value: z.number().optional(),
      top_contributions: z
        .array(
          z.object({
            feature: z.string(),
            shap_value: z.number(),
          }),
        )
        .optional(),
    }),
  ),
});

export const predictionSnapshotSchema = z.array(
  z.object({
    ride_id: z.number(),
    ride_hour: z.string(),
    source: z.string(),
    destination: z.string(),
    cab_type: z.string(),
    ride_name: z.string(),
    distance: z.number(),
    surge_multiplier: z.number(),
    actual: z.number(),
    predicted: z.number(),
    residual: z.number(),
    model_name: z.string(),
  }),
);

export const runManifestSchema = z.object({
  run_id: z.string(),
  generated_at: z.string(),
  dataset: z.object({
    row_count: z.number(),
    feature_columns: z.array(z.string()),
    time_range: timeRangeSchema,
  }),
  split_plan: z.object({
    holdout_rows: z.number(),
    development_rows: z.number(),
  }),
});

export const scenarioControlsSchema = z.object({
  generated_at: z.string(),
  model_name: z.string(),
  default_day_of_week: z.number(),
  sources: z.array(z.string()),
  destinations_by_source: z.record(z.string(), z.array(z.string())),
  cab_types: z.array(z.string()),
  time_blocks: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      hours: z.array(z.number()),
      anchor_hour: z.number(),
    }),
  ),
  weather_profiles: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      description: z.string(),
      values: z.object({
        temp: z.number(),
        clouds: z.number(),
        pressure: z.number(),
        rain: z.number(),
        humidity: z.number(),
        wind: z.number(),
      }),
    }),
  ),
  surge_levels: z.array(z.number()),
  distance_factors: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      factor: z.number(),
    }),
  ),
  route_catalog: z.array(
    z.object({
      source: z.string(),
      destination: z.string(),
      cab_type: z.string(),
      ride_name: z.string(),
      median_distance: z.number(),
      total_rides: z.number(),
    }),
  ),
});

export const scenarioGridSchema = z.array(
  z.object({
    source: z.string(),
    destination: z.string(),
    cab_type: z.string(),
    ride_name: z.string(),
    route_distance_median: z.number(),
    time_block: z.string(),
    weather_profile: z.string(),
    surge_multiplier: z.number(),
    distance_factor: z.number(),
    predicted_price: z.number(),
    price_band_low: z.number(),
    price_band_high: z.number(),
  }),
);

export const dashboardOverviewSchema = z.object({
  generated_at: z.string(),
  time_range: timeRangeSchema,
  dimensions: z.object({
    sources: z.number(),
    destinations: z.number(),
    cab_types: z.number(),
  }),
  kpis: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      value: z.union([z.number(), z.string()]),
      format: z.enum(["integer", "currency", "multiplier", "text"]),
    }),
  ),
});

export const dashboardTimeseriesSchema = z.array(
  z.object({
    ride_date: z.string(),
    ride_hour: z.string(),
    source: z.string(),
    destination: z.string(),
    cab_type: z.string(),
    total_rides: z.number(),
    avg_price: z.number(),
    avg_surge_multiplier: z.number(),
  }),
);

export const dashboardRouteBreakdownSchema = z.array(
  z.object({
    source: z.string(),
    destination: z.string(),
    cab_type: z.string(),
    total_rides: z.number(),
    avg_price: z.number(),
    avg_distance: z.number(),
    avg_surge_multiplier: z.number(),
  }),
);

export const dashboardWeatherImpactSchema = z.array(
  z.object({
    ride_date: z.string(),
    ride_hour: z.string(),
    source: z.string(),
    destination: z.string(),
    cab_type: z.string(),
    total_rides: z.number(),
    avg_price: z.number(),
    avg_temp: z.number(),
    avg_clouds: z.number(),
    avg_humidity: z.number(),
  }),
);

export const dashboardFiltersSchema = z.object({
  sources: z.array(z.string()),
  destinations: z.array(z.string()),
  cab_types: z.array(z.string()),
  time_windows: z.array(
    z.object({
      id: z.string(),
      label: z.string(),
      hours: z.array(z.number()),
      anchor_hour: z.number(),
    }),
  ),
});

export type ModelOverview = z.infer<typeof modelOverviewSchema>;
export type ModelMetrics = z.infer<typeof modelMetricsSchema>;
export type FeatureImportance = z.infer<typeof featureImportanceSchema>;
export type ShapSummary = z.infer<typeof shapSummarySchema>;
export type PredictionSnapshot = z.infer<typeof predictionSnapshotSchema>;
export type RunManifest = z.infer<typeof runManifestSchema>;
export type ScenarioControls = z.infer<typeof scenarioControlsSchema>;
export type ScenarioGrid = z.infer<typeof scenarioGridSchema>;
export type DashboardOverview = z.infer<typeof dashboardOverviewSchema>;
export type DashboardTimeseries = z.infer<typeof dashboardTimeseriesSchema>;
export type DashboardRouteBreakdown = z.infer<typeof dashboardRouteBreakdownSchema>;
export type DashboardWeatherImpact = z.infer<typeof dashboardWeatherImpactSchema>;
export type DashboardFilters = z.infer<typeof dashboardFiltersSchema>;
