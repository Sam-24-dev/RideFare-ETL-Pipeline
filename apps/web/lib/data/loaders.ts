import path from "node:path";

import {
  dashboardFiltersSchema,
  dashboardOverviewSchema,
  dashboardRouteBreakdownSchema,
  dashboardTimeseriesSchema,
  dashboardWeatherImpactSchema,
  featureImportanceSchema,
  modelMetricsSchema,
  modelOverviewSchema,
  predictionSnapshotSchema,
  runManifestSchema,
  scenarioControlsSchema,
  scenarioGridSchema,
  shapSummarySchema,
  type DashboardFilters,
  type DashboardOverview,
  type DashboardRouteBreakdown,
  type DashboardTimeseries,
  type DashboardWeatherImpact,
  type FeatureImportance,
  type ModelMetrics,
  type ModelOverview,
  type PredictionSnapshot,
  type RunManifest,
  type ScenarioControls,
  type ScenarioGrid,
  type ShapSummary,
} from "./contracts";
import { fileExists, type LoadState, readJsonFile, resolveProjectRoot } from "./filesystem";

export type HomeSnapshot = {
  championModel: string;
  explainabilityModel: string;
  rowCount: number;
  timeRange: ModelOverview["time_range"];
  featureCount: number;
  generatedAt: string;
  totalRides: number;
  avgPrice: number;
  avgSurge: number;
  dominantRoute: string;
  dimensions: DashboardOverview["dimensions"];
};

export type HowItWorksSnapshot = {
  generatedAt: string;
  featureCount: number;
  timeRange: ModelOverview["time_range"];
  sourceCount: number;
  destinationCount: number;
  cabTypeCount: number;
  championModel: string;
  explainabilityModel: string;
  hasTemporalSplit: boolean;
  topSignals: Array<{
    label: string;
    score: number;
  }>;
};

export type DashboardPayload = {
  overview: DashboardOverview;
  timeseries: DashboardTimeseries;
  routeBreakdown: DashboardRouteBreakdown;
  weatherImpact: DashboardWeatherImpact;
  filters: DashboardFilters;
};

export type ModelLabPayload = {
  overview: ModelOverview;
  metrics: ModelMetrics;
  featureImportance: FeatureImportance;
  shapSummary: ShapSummary;
  predictionSnapshot: PredictionSnapshot;
  runManifest: RunManifest;
  simulator: {
    controls: ScenarioControls;
    grid: ScenarioGrid;
  };
};

export async function loadHomeSnapshot(): Promise<LoadState<HomeSnapshot>> {
  const modelOverviewState = await loadModelOverview();
  if (modelOverviewState.status === "missing") {
    return modelOverviewState;
  }

  const dashboardOverviewState = await loadDashboardOverview();
  if (dashboardOverviewState.status === "missing") {
    return dashboardOverviewState;
  }

  const overview = modelOverviewState.data;
  const dashboardOverview = dashboardOverviewState.data;
  return {
    status: "ready",
    data: {
      championModel: overview.champion_model,
      explainabilityModel: overview.explainability_model,
      rowCount: overview.row_count,
      timeRange: overview.time_range,
      featureCount: overview.feature_columns.length,
      generatedAt: overview.generated_at,
      totalRides: getNumericKpiValue(dashboardOverview, "total_rides"),
      avgPrice: getNumericKpiValue(dashboardOverview, "avg_price"),
      avgSurge: getNumericKpiValue(dashboardOverview, "avg_surge_multiplier"),
      dominantRoute: getTextKpiValue(dashboardOverview, "dominant_route"),
      dimensions: dashboardOverview.dimensions,
    },
  };
}

export async function loadDashboardPayload(): Promise<LoadState<DashboardPayload>> {
  const projectRoot = resolveProjectRoot();
  const analyticsDir = path.join(projectRoot, "data", "processed", "analytics", "web");
  const required = {
    overview: path.join(analyticsDir, "dashboard_overview.json"),
    timeseries: path.join(analyticsDir, "dashboard_timeseries.json"),
    routeBreakdown: path.join(analyticsDir, "dashboard_route_breakdown.json"),
    weatherImpact: path.join(analyticsDir, "dashboard_weather_impact.json"),
    filters: path.join(analyticsDir, "dashboard_filters.json"),
  };

  for (const [key, filePath] of Object.entries(required)) {
    if (!(await fileExists(filePath))) {
      return missingState(
        `Falta el artefacto analítico "${key}". Ejecuta ridefare export-web antes de abrir el dashboard.`,
      );
    }
  }

  const [overview, timeseries, routeBreakdown, weatherImpact, filters] = await Promise.all([
    parseJson(required.overview, dashboardOverviewSchema),
    parseJson(required.timeseries, dashboardTimeseriesSchema),
    parseJson(required.routeBreakdown, dashboardRouteBreakdownSchema),
    parseJson(required.weatherImpact, dashboardWeatherImpactSchema),
    parseJson(required.filters, dashboardFiltersSchema),
  ]);

  return {
    status: "ready",
    data: {
      overview,
      timeseries,
      routeBreakdown,
      weatherImpact,
      filters,
    },
  };
}

export async function loadHowItWorksSnapshot(): Promise<LoadState<HowItWorksSnapshot>> {
  const modelOverviewState = await loadModelOverview();
  if (modelOverviewState.status === "missing") {
    return modelOverviewState;
  }

  const dashboardOverviewState = await loadDashboardOverview();
  if (dashboardOverviewState.status === "missing") {
    return dashboardOverviewState;
  }

  const runManifestState = await loadRunManifest();
  if (runManifestState.status === "missing") {
    return runManifestState;
  }

  const overview = modelOverviewState.data;
  const dashboardOverview = dashboardOverviewState.data;
  const runManifest = runManifestState.data;
  const topSignals = await loadHowItWorksSignals();

  return {
    status: "ready",
    data: {
      generatedAt: runManifest.generated_at,
      featureCount: overview.feature_columns.length,
      timeRange: runManifest.dataset.time_range,
      sourceCount: dashboardOverview.dimensions.sources,
      destinationCount: dashboardOverview.dimensions.destinations,
      cabTypeCount: dashboardOverview.dimensions.cab_types,
      championModel: overview.champion_model,
      explainabilityModel: overview.explainability_model,
      hasTemporalSplit: overview.holdout_rows > 0 || runManifest.split_plan.holdout_rows > 0,
      topSignals,
    },
  };
}

export async function loadModelLabPayload(): Promise<LoadState<ModelLabPayload>> {
  const modelOverviewState = await loadModelOverview();
  if (modelOverviewState.status === "missing") {
    return modelOverviewState;
  }

  const projectRoot = resolveProjectRoot();
  const mlWebDir = path.join(projectRoot, "data", "processed", "ml", "web");
  const required = {
    metrics: path.join(mlWebDir, "model_metrics.json"),
    featureImportance: path.join(mlWebDir, "feature_importance.json"),
    shapSummary: path.join(mlWebDir, "shap_summary.json"),
    predictionSnapshot: path.join(mlWebDir, "prediction_snapshot.json"),
    runManifest: path.join(mlWebDir, "run_manifest.json"),
    scenarioControls: path.join(mlWebDir, "scenario_controls.json"),
    scenarioGrid: path.join(mlWebDir, "scenario_grid.json"),
  };

  for (const [key, filePath] of Object.entries(required)) {
    if (!(await fileExists(filePath))) {
      return missingState(
        `Falta el artefacto de modelo "${key}". Ejecuta ridefare train y ridefare export-web para poblar el laboratorio.`,
      );
    }
  }

  const [metrics, featureImportance, shapSummary, predictionSnapshot, runManifest, controls, grid] =
    await Promise.all([
      parseJson(required.metrics, modelMetricsSchema),
      parseJson(required.featureImportance, featureImportanceSchema),
      parseJson(required.shapSummary, shapSummarySchema),
      parseJson(required.predictionSnapshot, predictionSnapshotSchema),
      parseJson(required.runManifest, runManifestSchema),
      parseJson(required.scenarioControls, scenarioControlsSchema),
      parseJson(required.scenarioGrid, scenarioGridSchema),
    ]);

  return {
    status: "ready",
    data: {
      overview: modelOverviewState.data,
      metrics,
      featureImportance,
      shapSummary,
      predictionSnapshot,
      runManifest,
      simulator: {
        controls,
        grid,
      },
    },
  };
}

async function loadModelOverview(): Promise<LoadState<ModelOverview>> {
  const projectRoot = resolveProjectRoot();
  const filePath = path.join(projectRoot, "data", "processed", "ml", "web", "model_overview.json");

  if (!(await fileExists(filePath))) {
    return missingState(
      "Todavía no hay artefactos ML exportados. Ejecuta ridefare train y ridefare export-web para poblar la app pública.",
    );
  }

  return {
    status: "ready",
    data: await parseJson(filePath, modelOverviewSchema),
  };
}

async function loadDashboardOverview(): Promise<LoadState<DashboardOverview>> {
  const projectRoot = resolveProjectRoot();
  const filePath = path.join(
    projectRoot,
    "data",
    "processed",
    "analytics",
    "web",
    "dashboard_overview.json",
  );

  if (!(await fileExists(filePath))) {
    return missingState(
      "Todavía no hay artefactos analíticos exportados. Ejecuta ridefare export-web para poblar la home pública.",
    );
  }

  return {
    status: "ready",
    data: await parseJson(filePath, dashboardOverviewSchema),
  };
}

async function loadRunManifest(): Promise<LoadState<RunManifest>> {
  const projectRoot = resolveProjectRoot();
  const filePath = path.join(projectRoot, "data", "processed", "ml", "web", "run_manifest.json");

  if (!(await fileExists(filePath))) {
    return missingState(
      "TodavÃ­a no hay manifiesto de ejecuciÃ³n exportado. Ejecuta ridefare train y ridefare export-web para documentar el proceso pÃºblico.",
    );
  }

  return {
    status: "ready",
    data: await parseJson(filePath, runManifestSchema),
  };
}

async function loadHowItWorksSignals(): Promise<HowItWorksSnapshot["topSignals"]> {
  const projectRoot = resolveProjectRoot();
  const mlDir = path.join(projectRoot, "data", "processed", "ml", "web");
  const featureImportancePath = path.join(mlDir, "feature_importance.json");
  const shapSummaryPath = path.join(mlDir, "shap_summary.json");

  const [featureImportance, shapSummary] = await Promise.all([
    (async () => {
      if (!(await fileExists(featureImportancePath))) {
        return null;
      }
      return parseJson(featureImportancePath, featureImportanceSchema);
    })(),
    (async () => {
      if (!(await fileExists(shapSummaryPath))) {
        return null;
      }
      return parseJson(shapSummaryPath, shapSummarySchema);
    })(),
  ]);

  return buildHowItWorksTopSignals(featureImportance, shapSummary);
}

function buildHowItWorksTopSignals(
  featureImportance: FeatureImportance | null,
  shapSummary: ShapSummary | null,
): HowItWorksSnapshot["topSignals"] {
  const preferredImportance = featureImportance?.filter((entry) => entry.importance > 0) ?? [];
  const preferredShap =
    shapSummary?.global_importance.filter((entry) => entry.mean_abs_shap > 0) ?? [];

  const rawSignals =
    preferredImportance.length > 0
      ? preferredImportance.map((entry) => ({
          feature: entry.feature,
          score: entry.importance,
        }))
      : preferredShap.length > 0
        ? preferredShap.map((entry) => ({
            feature: entry.feature,
            score: entry.mean_abs_shap,
          }))
        : (featureImportance ?? shapSummary?.global_importance ?? []).map((entry) => ({
            feature: entry.feature,
            score: "importance" in entry ? entry.importance : entry.mean_abs_shap,
          }));

  const groupedScores = new Map<string, number>();

  for (const signal of rawSignals) {
    const label = mapSignalLabel(signal.feature);
    groupedScores.set(label, (groupedScores.get(label) ?? 0) + signal.score);
  }

  const rankedSignals = Array.from(groupedScores.entries())
    .sort(
      (left, right) =>
        right[1] - left[1] ||
        getSignalSortOrder(left[0]) - getSignalSortOrder(right[0]) ||
        left[0].localeCompare(right[0]),
    )
    .slice(0, 4)
    .map(([label, score]) => ({ label, score }));

  if (rankedSignals.length > 0) {
    return rankedSignals;
  }

  return [
    { label: "Distancia", score: 0 },
    { label: "Demanda", score: 0 },
    { label: "Clima", score: 0 },
    { label: "Tráfico y hora", score: 0 },
  ];
}

function mapSignalLabel(feature: string): string {
  const normalizedFeature = feature.toLowerCase();

  if (normalizedFeature.includes("distance") || normalizedFeature.includes("base_fare")) {
    return "Distancia";
  }

  if (normalizedFeature.includes("surge") || normalizedFeature.includes("demand")) {
    return "Demanda";
  }

  if (
    normalizedFeature.includes("temp") ||
    normalizedFeature.includes("cloud") ||
    normalizedFeature.includes("pressure") ||
    normalizedFeature.includes("rain") ||
    normalizedFeature.includes("humidity") ||
    normalizedFeature.includes("wind") ||
    normalizedFeature.includes("weather")
  ) {
    return "Clima";
  }

  if (
    normalizedFeature.includes("hour") ||
    normalizedFeature.includes("day_of_week") ||
    normalizedFeature.includes("traffic") ||
    normalizedFeature.includes("congestion")
  ) {
    return "Tráfico y hora";
  }

  return "Contexto";
}

function getSignalSortOrder(label: string): number {
  const preferredOrder = ["Distancia", "Demanda", "Clima", "Tráfico y hora", "Contexto"];
  const index = preferredOrder.indexOf(label);

  return index === -1 ? preferredOrder.length : index;
}

async function parseJson<T>(filePath: string, schema: { parse: (value: unknown) => T }): Promise<T> {
  const payload = await readJsonFile<unknown>(filePath);
  return schema.parse(payload);
}

function getNumericKpiValue(overview: DashboardOverview, id: string): number {
  const match = overview.kpis.find((kpi) => kpi.id === id);
  return typeof match?.value === "number" ? match.value : 0;
}

function getTextKpiValue(overview: DashboardOverview, id: string): string {
  const match = overview.kpis.find((kpi) => kpi.id === id);
  return typeof match?.value === "string" ? match.value : "Sin lectura destacada";
}

function missingState(message: string): LoadState<never> {
  return {
    status: "missing",
    message,
  };
}
